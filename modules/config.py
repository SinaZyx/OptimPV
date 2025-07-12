import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import time

# Tarifs TURPE 6 (Fév 2025) pour ACOC Producteur
TURPE_PROD_RATES = {
    "BT<=36kVA": {
        "CG": {"Unique": 21.60, "CARD": 22.80}, # p.19
        "CC": {"Linky": 22.44}                 # p.20 (on suppose Linky)
    },
    "BT>36kVA": {
        "CG": {"Unique": 285.96, "CARD": 318.00},# p.15
        "CC": {"Mensuelle": 288.84}             # p.16 (on suppose transmission mensuelle)
    },
    "HTA": {
        "CG": {"Unique": 725.16, "CARD": 725.16}, # Approximation
        "CC": {"Mensuelle": 383.76}             # p.11
    }
}

def default_tarif_oa(p_kwc: float) -> float:
    """
    Renvoie le tarif OA SUGGÉRÉ en €/kWh selon la puissance,
    en utilisant les valeurs de base DÉFINIES DANS LA CONFIGURATION GLOBALE.
    """
    config = st.session_state.get("config", {})
    t_le9 = float(config.get("tarif_oa_bracket_le9", 0.0761))
    t_le100 = float(config.get("tarif_oa_bracket_le100", 0.0761))
    t_gt100 = float(config.get("tarif_oa_bracket_gt100", 0.0600))

    p_kwc = float(p_kwc)
    if p_kwc <= 9: return t_le9
    elif p_kwc <= 100: return t_le100
    else: return t_gt100

class ConfigModule:
    def __init__(self):
        # Initialiser la config globale si elle n'existe pas
        if 'config' not in st.session_state:
            self.initialize_default_config()
        # Initialiser la config par site si elle n'existe pas
        if 'sites_config' not in st.session_state:
            st.session_state.sites_config = {}
        # Initialiser les scénarios s'ils n'existent pas
        if 'scenarios' not in st.session_state:
            self.initialize_default_scenarios()

    def initialize_default_config(self):
        """Initialise la configuration GLOBALE par défaut"""
        # Note: CAPEX/OPEX/Puissance ne sont plus ici comme paramètres principaux,
        # mais on garde les defaults pour les barèmes etc.
        default_power = 20.0 # Utilisé pour le tarif OA par défaut initial
        default_oa_le9 = 0.0400
        default_oa_le100 = 0.0761
        default_oa_gt100 = 0.0600
        default_sub_rate_le3 = 100.0
        default_sub_rate_le9 = 80.0
        default_sub_rate_le36 = 190.0
        default_sub_rate_le100 = 100.0
        default_sub_rate_le500 = 0.0
        default_sub_rate_gt100 = 0.0

        st.session_state.config = {
            # --- Infos Projet Générales ---
            "nom_projet": "Projet Photovoltaïque ACOC",
            "localisation": "France",
            "date_debut_ppa": datetime.now().date().isoformat(),
            "duree_ppa": 240,  # en mois
            "duree_construction": 12,  # en mois
            "amortissement_duree": 15,
            "valeur_residuelle_pct": 0.0,
            "cout_demantelement_pct": 0.0,
            "degradation_rate": 0.005,

             # --- Paramètres Économiques Globaux ---
            "taux_inflation": 2.0,
            "taux_imposition": 25.0,
            "tarif_edf_reference": 0.21,
            "source_prix_autoconso": "prix_initial",

            # --- Barèmes et Options Tarifaires / Subvention (Globaux) ---
            "tarif_oa_bracket_le9": default_oa_le9,
            "tarif_oa_bracket_le100": default_oa_le100,
            "tarif_oa_bracket_gt100": default_oa_gt100,
            "tarif_oa": default_tarif_oa(default_power), # Initialisé, mais sera recalculé
            "tarif_oa_indexe_inflation": True,
            "taux_inflation_tarif_oa": 1.89,
            "subvention_rate_le3": default_sub_rate_le3,
            "subvention_rate_le9": default_sub_rate_le9,
            "subvention_rate_le36": default_sub_rate_le36,
            "subvention_rate_le100": default_sub_rate_le100,
            "subvention_rate_le500": default_sub_rate_le500,
            "subvention_rate_gt100": default_sub_rate_gt100,
            "subvention_calculee": 0.0, # Sera recalculé globalement

            # --- TURPE (Global) ---
            "turpe_prod_tension": "BT<=36kVA",
            "turpe_prod_contrat": "Unique",
            "turpe_prod_calculee": 0.0, # Sera recalculé globalement
            "turpe_indexe_inflation": True,

            # --- Paramètres Financiers Globaux ---
            "cout_fonds_propres": 8.0,
            "with_loan": True,
            "debt_ratio": 0.80,
            "taux_interet_dette": 4.0,
            "debt_term_years": 20,
            "target_dscr": 1.2,
            "taux_interet_shl": 4.0, # Gardé ici pour l'instant
            "shl_blocage_period": 60,
            "dividends_blocage_period": 60,
            "capitalize_construction_interest": True, # Capitalisation EN PLUS du paiement (intérêts toujours payés)

            # --- Valeurs OPEX par défaut (pour pré-remplir config par site) ---
            "opex_method": "auto", # Méthode par défaut suggérée pour les sites
            "opex_percent": 1.5,
            "opex_per_kwc": 20.0,
            "opex_onduleur_provision": True, # Option globale pour l'instant
            "opex_onduleur_cost": 130.0,
            "opex_onduleur_lifetime": 15,
            # Note: Les CAPEX et OPEX globaux ne sont plus définis ici comme inputs principaux

            # --- Paramètres Comparaison PVSOL (Globaux) ---
            "pvs_feed_in_tariff": 0.1108,
            "pvs_avoided_cost_tariff": 0.2218,

            # --- Paramètres Optimisation & MC (Globaux) ---
            "constraint_min_project_irr_pct": 8.0,
            "constraint_max_payback": 18.0,
            "constraint_min_consumer_gain_pct": 5.0,
            "prix_min_revente": 0.05,
            "prix_max_revente": 0.40,
            "pas_optimisation": 0.001,
            "nb_iterations_monte_carlo": 1000,
            "ecart_type_production": 10.0,
            "ecart_type_consommation": 5.0,

            # --- Paramètres Gestion de Trésorerie et Placements (SIMPLIFIÉ) ---
            "placement_tresorerie_active": False,  # Activer la gestion des placements
            "placement_tva_capex": True,  # Placer le remboursement TVA CAPEX initial
            "placement_tva_exploitation": True,  # Placer les crédits TVA mensuels d'exploitation
            "seuil_tva_capex": 5000.0,  # Seuil pour identifier la TVA CAPEX (€)
            "pourcentage_tva_capex_a_placer": 80.0,  # % à placer pour TVA CAPEX
            "pourcentage_tva_exploitation_a_placer": 50.0,  # % à placer pour TVA exploitation
            "taux_placement_provision_onduleur": 2.5,  # Taux annuel pour provision onduleur (%)
            "taux_placement_exces_tva": 1.5,  # Taux annuel pour TVA placée (%)
            "seuil_remboursement_tva": 50.0,  # Seuil minimum pour placer les remboursements TVA (€)
        }
        # Assurer que sites_config existe aussi
        if 'sites_config' not in st.session_state:
            st.session_state.sites_config = {}

    def initialize_default_scenarios(self):
        """Initialise les scénarios par défaut"""
        # (Cette fonction reste inchangée par rapport à votre code précédent)
        st.session_state.scenarios = {
            "Base": {"description": "Scénario de référence", "production_modifier": 1.0, "opex_modifier": 1.0, "capex_modifier": 0.0, "inflation_modifier": 1.0,},
            "P90": {"description": "Production réduite de 5%", "production_modifier": 0.95, "opex_modifier": 1.0, "capex_modifier": 1.0, "inflation_modifier": 1.0,},
            "OPEX +10%": {"description": "Augmentation des coûts d'exploitation de 10%", "production_modifier": 1.0, "opex_modifier": 1.1, "capex_modifier": 1.0, "inflation_modifier": 1.0,},
            "CAPEX +10%": {"description": "Augmentation de l'investissement initial de 10%", "production_modifier": 1.0, "opex_modifier": 1.0, "capex_modifier": 1.1, "inflation_modifier": 1.0,},
            "Inflation Modifiée": {"description": "Inflation à 1.5% au lieu de 2%", "production_modifier": 1.0, "opex_modifier": 1.0, "capex_modifier": 1.0, "inflation_modifier": 0.75,},
        }

    def save_config(self, config_name):
        """Sauvegarde la configuration actuelle (globale + sites + scénarios)"""
        if not os.path.exists('saved_configs'):
            os.makedirs('saved_configs')

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"saved_configs/config_{config_name}_{timestamp}.json"

        # Construire le dictionnaire de configuration complet
        config_to_save = {
            "config": st.session_state.config, # Config globale
            "sites_config": st.session_state.sites_config, # NOUVEAU: Config par site
            "scenarios": st.session_state.scenarios, # Scénarios
            "metadata": {
                "date_creation": datetime.now().isoformat(),
                "nom": config_name
            }
        }
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)
            return filename
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde de la configuration : {e}")
            return None

    def load_config(self, filename):
        """Charge une configuration existante (globale + sites + scénarios)"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            # Mettre à jour la configuration globale
            if 'config' in loaded_data:
                st.session_state.config = loaded_data['config']
                # Optionnel: Appeler ensure_config_defaults ici pour ajouter clés manquantes si ancien format
                self.ensure_config_defaults()
            else:
                 self.initialize_default_config() # Fallback si section config manque

            # Mettre à jour la configuration par site (NOUVEAU)
            if 'sites_config' in loaded_data:
                st.session_state.sites_config = loaded_data['sites_config']
            else:
                st.session_state.sites_config = {} # Initialiser si manque

            # Mettre à jour les scénarios
            if 'scenarios' in loaded_data:
                st.session_state.scenarios = loaded_data['scenarios']
            else:
                self.initialize_default_scenarios() # Fallback

            st.success(f"Configuration '{filename}' chargée.")
            return True
        except FileNotFoundError:
            st.error(f"Fichier de configuration introuvable : {filename}")
            return False
        except json.JSONDecodeError as e:
            st.error(f"Erreur de format JSON dans {filename}: {e}")
            return False
        except Exception as e:
            st.error(f"Erreur lors du chargement de la configuration depuis {filename}: {e}")
            return False

    def get_available_configs(self):
        """Récupère la liste des configurations sauvegardées"""
        # (Cette fonction reste inchangée)
        if not os.path.exists('saved_configs'): return []
        configs = [f for f in os.listdir('saved_configs') if f.endswith('.json')]
        return configs

    # --- MÉTHODE SHOW_UI MODIFIÉE ---
    def show_ui(self):
        """Affiche l'interface utilisateur du module de configuration (MODIFIÉE pour config par site)."""
        st.markdown("<h1 class='main-header'>Configuration du Projet</h1>", unsafe_allow_html=True)

        # Récupérer la config globale pour accès facile
        config = st.session_state.config
        # Récupérer la config par site (setdefault initialise si n'existe pas)
        sites_config = st.session_state.setdefault('sites_config', {})

        # Définir les onglets
        tab_titles = [
            "Économie & Tarifs",         # Onglet 1 (Eco + Tarifs)
            "Projet & Technique",        # Onglet 2 (Projet Global + Technique)
            "Financement",               # Onglet 3
            "Configuration par Site",    # Onglet 4 (NOUVEAU)
            "⚖️ Clés de Répartition",    # Onglet 5 (NOUVEAU)
            "Scénarios",                 # Onglet 6
            "Sauvegarde/Chargement"      # Onglet 7
        ]
        tab_eco, tab_proj, tab_fin, tab_sites, tab_repartition, tab_scen, tab_save = st.tabs(tab_titles)

        # --- Onglet 1: Économie & Tarifs (Global) ---
        with tab_eco:
            st.markdown("<h3 class='sub-header'>Paramètres Macro-économiques & Tarifs</h3>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.config["taux_inflation"] = st.number_input("Taux d'inflation Général (%)", min_value=0.0, max_value=10.0, value=float(config.get("taux_inflation", 2.0)), step=0.1, help="Inflation annuelle pour OPEX, TURPE (si indexé), prix EDF, etc.")
                st.session_state.config["taux_imposition"] = st.number_input(
                    "Taux d'imposition Standard (%)",
                    min_value=0.0,
                    max_value=50.0,
                    value=float(config.get("taux_imposition", 25.0)),
                    step=0.1,
                    help="Taux standard (normalement 25%) appliqué sur la part du bénéfice imposable annuel excédant 42 500€. Le taux réduit PME (15% sur les premiers 42 500€) est appliqué automatiquement par le moteur de calcul. Ce champ permet d'ajuster le taux standard si besoin."
                )

            with col2:
                st.session_state.config["tarif_edf_reference"] = st.number_input("Tarif EDF de référence (€/kWh)", min_value=0.05, max_value=0.50, value=float(config.get("tarif_edf_reference", 0.21)), step=0.01, format="%.4f", help="Tarif de comparaison pour le gain client")
                # Placeholder pour peut-être d'autres paramètres éco

            st.markdown("---")
            st.markdown("#### Tarif d'Achat Surplus (OA)")
            col_oa1, col_oa2 = st.columns(2)
            with col_oa1:
                # Le champ 'tarif_oa' est maintenant informatif, il sera recalculé
                # avant l'analyse basé sur la puissance totale et les barèmes.
                # On peut afficher la valeur actuellement stockée ou une valeur indicative.
                current_total_power = sum(cfg.get('puissance_kwc', 0) for cfg in sites_config.values()) # Calcul puissance totale actuelle
                calculated_oa = default_tarif_oa(current_total_power) if current_total_power > 0 else 0.0
                st.metric("Tarif OA Applicable (calculé)", f"{calculated_oa:.4f} €/kWh", help=f"Basé sur P_totale={current_total_power:.1f} kWc et barèmes ci-dessous.")
            with col_oa2:
                index_oa_checkbox = st.checkbox("Indexer le Tarif OA sur Inflation Spécifique?", value=config.get("tarif_oa_indexe_inflation", True), key="tarif_oa_index_check_config")
                st.session_state.config["tarif_oa_indexe_inflation"] = index_oa_checkbox
                if index_oa_checkbox:
                     st.session_state.config["taux_inflation_tarif_oa"] = st.number_input("-> Taux Inflation OA (%)", min_value=0.0, max_value=10.0, value=float(config.get("taux_inflation_tarif_oa", 1.89)), step=0.1, key="inflation_oa_rate_config")

            with st.expander("🔧 Configuration Barèmes Tarif OA"):
                 st.session_state.config["tarif_oa_bracket_le9"] = st.number_input("Barème si P <= 9 kWc (€/kWh)", min_value=0.0, value=float(config.get("tarif_oa_bracket_le9", 0.0400)), step=0.0001, format="%.4f")
                 st.session_state.config["tarif_oa_bracket_le100"] = st.number_input("Barème si 9 < P <= 100 kWc (€/kWh)", min_value=0.0, value=float(config.get("tarif_oa_bracket_le100", 0.0761)), step=0.0001, format="%.4f")
                 st.session_state.config["tarif_oa_bracket_gt100"] = st.number_input("Barème si P > 100 kWc (€/kWh)", min_value=0.0, value=float(config.get("tarif_oa_bracket_gt100", 0.0600)), step=0.0001, format="%.4f")

            st.markdown("---")
            st.markdown("#### Valorisation de l'Autoconsommation")
            source_options = {"prix_initial": "Prix de vente optimisé (indexé inflation gén.)", "tarif_edf": "Tarif EDF de référence (indexé inflation gén.)", "tarif_oa": "Tarif d'Obligation d'Achat (selon son indexation)"}
            source_prix_selection = st.selectbox("Source pour valoriser l'énergie autoconsommée", options=list(source_options.keys()), format_func=lambda x: source_options[x], index=list(source_options.keys()).index(config.get("source_prix_autoconso", "prix_initial")), key="source_prix_auto_select_configtab")
            st.session_state.config["source_prix_autoconso"] = source_prix_selection

        # --- Onglet 2: Projet & Technique (Global) ---
        with tab_proj:
            st.markdown("<h3 class='sub-header'>Paramètres Généraux Projet & Techniques</h3>", unsafe_allow_html=True)
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.session_state.config['duree_ppa'] = st.number_input("Durée Simulation (mois)", min_value=12, max_value=480, value=config.get("duree_ppa", 240), step=12)
                st.session_state.config['duree_construction'] = st.number_input("Durée Construction (mois)", min_value=0, max_value=36, value=int(config.get('duree_construction', 12)), step=1)
                st.session_state.config["amortissement_duree"] = st.number_input("Durée Amortissement Comptable (années)", min_value=5, max_value=40, value=int(config.get("amortissement_duree", 15)), step=1)

            with col_p2:
                 try: default_date = datetime.fromisoformat(str(config.get("date_debut_ppa"))).date()
                 except: default_date = datetime.now().date()
                 selected_date = st.date_input("Date Début Exploitation (après construction)", value=default_date, key="date_debut_ppa_input_configtab")
                 st.session_state.config["date_debut_ppa"] = selected_date.isoformat()
                 st.session_state.config["degradation_rate"] = st.number_input("Taux Dégradation Annuel (%)", min_value=0.0, max_value=5.0, value=float(config.get("degradation_rate", 0.005)) * 100, step=0.1, help="Perte de production annuelle des panneaux") / 100.0
                 st.session_state.config["valeur_residuelle_pct"] = st.number_input("Valeur Résiduelle Actifs (% CAPEX Net)", min_value=-50.0, max_value=50.0, value=float(config.get("valeur_residuelle_pct", 0.0)) * 100.0, step=1.0, help="Valeur en fin d'amortissement") / 100.0
                 st.session_state.config["cout_demantelement_pct"] = st.number_input("Coût Démantèlement (% CAPEX Brut)", min_value=-50.0, max_value=50.0, value=float(config.get("cout_demantelement_pct", 0.0)) * 100.0, step=1.0, help="Coût (ou gain si négatif) en fin de projet") / 100.0

            st.markdown("---")
            st.markdown("#### Paramètres TURPE (Calcul Global)")
            # Le calcul utilise la puissance TOTALE des sites
            total_power_for_turpe = sum(cfg.get('puissance_kwc', 0) for cfg in sites_config.values())
            # Déterminer la tranche de tension basée sur la puissance totale (exemple simple)
            if total_power_for_turpe <= 36: default_tension = "BT<=36kVA"
            elif total_power_for_turpe <= 250: default_tension = "BT>36kVA" # Hypothèse pour la tranche suivante
            else: default_tension = "HTA" # Au-delà, on suppose HTA

            # Recalculer TURPE ici basé sur puissance totale et sélections
            selected_tension = config.get("turpe_prod_tension", default_tension)
            selected_contrat = config.get("turpe_prod_contrat", "Unique")
            cg_rate = TURPE_PROD_RATES.get(selected_tension, {}).get("CG", {}).get(selected_contrat, 0.0)
            cc_keys = list(TURPE_PROD_RATES.get(selected_tension, {}).get("CC", {}).keys())
            cc_key = cc_keys[0] if cc_keys else None
            cc_rate = TURPE_PROD_RATES.get(selected_tension, {}).get("CC", {}).get(cc_key, 0.0) if cc_key else 0.0
            turpe_glob_calc = cg_rate + cc_rate
            st.session_state.config["turpe_prod_calculee"] = turpe_glob_calc # Mettre à jour dans la config

            st.metric("TURPE Producteur Globale Calculée (€ HT/an)", f"{turpe_glob_calc:.2f}", help=f"Basé sur P_totale={total_power_for_turpe:.1f} kWc et options ci-dessous.")
            with st.expander("🔧 Modifier Options Calcul TURPE Global"):
                 col_t1, col_t2 = st.columns(2)
                 with col_t1:
                      tension_options = list(TURPE_PROD_RATES.keys())
                      current_tension_val = config.get("turpe_prod_tension", default_tension)
                      try: current_tension_idx = tension_options.index(current_tension_val)
                      except ValueError: current_tension_idx = 0; st.session_state.config["turpe_prod_tension"] = tension_options[0]
                      selected_tension_exp = st.selectbox("Niveau Tension (basé sur P Totale)", options=tension_options, index=current_tension_idx, key="turpe_tension_select_glob")
                      st.session_state.config["turpe_prod_tension"] = selected_tension_exp
                 with col_t2:
                      contrat_options = ["Unique", "CARD"]
                      current_contrat_val = config.get("turpe_prod_contrat", "Unique")
                      try: current_contrat_idx = contrat_options.index(current_contrat_val)
                      except ValueError: current_contrat_idx = 0; st.session_state.config["turpe_prod_contrat"] = contrat_options[0]
                      selected_contrat_exp = st.selectbox("Type Contrat TURPE", options=contrat_options, index=current_contrat_idx, key="turpe_contrat_select_glob", help="Contrat Unique ou CARD direct avec Enedis.")
                      st.session_state.config["turpe_prod_contrat"] = selected_contrat_exp

                 st.session_state.config["turpe_indexe_inflation"] = st.checkbox("Indexer TURPE sur Inflation Générale?", value=config.get("turpe_indexe_inflation", True), key="turpe_index_check_glob")

            st.markdown("---")
            st.markdown("#### Barèmes Subvention (Prime Investissement)")
            with st.expander("🔧 Configuration Barèmes Subvention Globale"):
                 # ... (Inputs pour subvention_rate_le9, le36, le100, le500 etc. comme avant) ...
                 st.session_state.config["subvention_rate_le9"] = st.number_input(
                     "Taux si P <= 9 kWc (€/kWc)",
                     value=float(config.get("subvention_rate_le9", 80.0)),
                     key="sub_rate_le9", # Utiliser des clés uniques
                     step=1.0, format="%.1f"
                 )
                 st.session_state.config["subvention_rate_le36"] = st.number_input(
                     "Taux si 9 < P <= 36 kWc (€/kWc)",
                     value=float(config.get("subvention_rate_le36", 190.0)), # Valeur par défaut indicative
                     key="sub_rate_le36",
                     step=1.0, format="%.1f"
                 )
                 st.session_state.config["subvention_rate_le100"] = st.number_input(
                     "Taux si 36 < P <= 100 kWc (€/kWc)",
                     value=float(config.get("subvention_rate_le100", 100.0)), # Valeur par défaut indicative
                     key="sub_rate_le100",
                     step=1.0, format="%.1f"
                 )
                 st.session_state.config["subvention_rate_le500"] = st.number_input(
                     "Taux si 100 < P <= 500 kWc (€/kWc)",
                     value=float(config.get("subvention_rate_le500", 0.0)), # Valeur par défaut indicative
                     key="sub_rate_le500",
                     step=1.0, format="%.1f"
                 )
                 # ... autres paliers (supprimé car redondant avec les ajouts)
            # Calculer et afficher subvention globale
            total_power_for_sub = sum(cfg.get('puissance_kwc', 0) for cfg in sites_config.values())
            rate_le9 = float(config.get("subvention_rate_le9", 0.0))
            rate_le36 = float(config.get("subvention_rate_le36", 0.0))
            rate_le100 = float(config.get("subvention_rate_le100", 0.0))
            rate_le500 = float(config.get("subvention_rate_le500", 0.0))
            applicable_rate = 0.0 # Placeholder - Ajouter la logique if/elif basée sur total_power_for_sub
            if total_power_for_sub <= 9: applicable_rate = rate_le9
            elif total_power_for_sub <= 36: applicable_rate = rate_le36
            elif total_power_for_sub <= 100: applicable_rate = rate_le100
            elif total_power_for_sub <= 500: applicable_rate = rate_le500
            total_subvention_glob = applicable_rate * total_power_for_sub
            st.session_state.config["subvention_calculee"] = total_subvention_glob
            st.metric("Subvention Totale Projet Calculée (€)", f"{total_subvention_glob:,.2f}", help=f"Basé sur P_totale={total_power_for_sub:.1f} kWc et barèmes ci-dessus.")


        # --- Onglet 3: Financement (Global) ---
        with tab_fin:
            st.markdown("<h3 class='sub-header'>Paramètres de Financement</h3>", unsafe_allow_html=True)
            # (Copier ici la logique de la section financement globale: checkbox prêt, ratio dette, taux, durée, blocages etc.)
            st.session_state.config["with_loan"] = st.checkbox("Financement avec prêt bancaire", value=config.get("with_loan", True), key="fin_with_loan")
            if st.session_state.config["with_loan"]:
                 # ... (debt_ratio, taux_interet_dette, debt_term_years, target_dscr) ...
                 col_f1, col_f2 = st.columns(2)
                 with col_f1:
                      st.session_state.config["debt_ratio"] = st.slider("Ratio Dette/Total (%)", min_value=0.0, max_value=100.0, value=float(config.get("debt_ratio", 0.8))*100, step=5.0, key="fin_debt_ratio") / 100.0
                      # MODIFICATION: S'assurer que la valeur est au moins égale au minimum requis
                      current_debt_term = int(config.get("debt_term_years", 20))
                      value_for_widget_debt_term = max(1, current_debt_term)
                      st.session_state.config["debt_term_years"] = st.number_input("Durée Prêt (ans)", min_value=1, value=value_for_widget_debt_term, step=1, key="fin_debt_term")
                 with col_f2:
                      st.session_state.config["taux_interet_dette"] = st.number_input("Taux Intérêt Dette Annuel (%)", min_value=0.0, value=float(config.get("taux_interet_dette", 4.0)), step=0.1, key="fin_debt_rate")
                      st.session_state.config["target_dscr"] = st.number_input("DSCR Cible Minimum", min_value=1.0, value=float(config.get("target_dscr", 1.2)), step=0.05, key="fin_dscr")

                 st.markdown("---")
                 st.markdown("#### Gestion des Intérêts de Construction")
                 st.session_state.config["capitalize_construction_interest"] = st.checkbox(
                     "Capitaliser les intérêts de construction",
                     value=config.get("capitalize_construction_interest", True),
                     key="fin_capitalize_interest",
                     help="Si coché: les intérêts pendant la construction sont payés ET ajoutés au capital du prêt. Si décoché: les intérêts sont uniquement payés mensuellement pendant la construction."
                 )
                 if st.session_state.config["capitalize_construction_interest"]:
                     st.info("💡 **Mode actuel**: Les intérêts de construction sont payés chaque mois ET capitalisés (ajoutés au capital du prêt)")
                 else:
                     st.info("💡 **Mode actuel**: Les intérêts de construction sont uniquement payés mensuellement (pas de capitalisation)")
                 
                 st.markdown("---")
                 st.markdown("#### Périodes de Blocage")
                 # ... (shl_blocage_period, dividends_blocage_period) ...
                 col_b1, col_b2 = st.columns(2)
                 with col_b1: st.session_state.config["shl_blocage_period"] = st.number_input("Blocage Remb. SHL (mois)", min_value=0, value=int(config.get("shl_blocage_period", 60)), step=12)
                 with col_b2: st.session_state.config["dividends_blocage_period"] = st.number_input("Blocage Dividendes (mois)", min_value=0, value=int(config.get("dividends_blocage_period", 60)), step=12)

                 # Section simplifiée
                 st.markdown("---")
                 st.markdown("#### 💰 Gestion des Placements de Trésorerie")

                 st.info("""
                 **Objectif** : Optimiser uniquement :
                 - 🔧 **Provision Onduleur** : Placement automatique long terme (15 ans)
                 - 💶 **Remboursements TVA** : Placement du remboursement TVA initial
                 - ✅ **Revenus d'exploitation** : Restent en trésorerie disponible
                 """)

                 placement_active = st.checkbox(
                     "Activer les placements automatiques",
                     value=config.get("placement_tresorerie_active", False),
                     help="Place automatiquement la provision onduleur et une partie du remboursement TVA"
                 )
                 st.session_state.config["placement_tresorerie_active"] = placement_active

                 if placement_active:
                     col1, col2 = st.columns(2)
                     
                     with col1:
                         st.markdown("**Paramètres TVA**")
                         pct_tva = st.slider(
                             "% du remboursement TVA à placer",
                             min_value=0.0,
                             max_value=100.0,
                             value=float(config.get("pourcentage_tva_a_placer", 80.0)),
                             step=5.0,
                             help="Pourcentage du remboursement TVA à placer (garder une partie pour le BFR)"
                         )
                         st.session_state.config["pourcentage_tva_a_placer"] = pct_tva
                         
                     with col2:
                         st.markdown("**Taux de Placement Annuels**")
                         taux_prov = st.number_input(
                             "Provision Onduleur (%/an)",
                             min_value=0.0,
                             max_value=10.0,
                             value=float(config.get("taux_placement_provision_onduleur", 2.5)),
                             step=0.1,
                             format="%.1f"
                         )
                         st.session_state.config["taux_placement_provision_onduleur"] = taux_prov
                         
                         taux_tva = st.number_input(
                             "TVA placée (%/an)",
                             min_value=0.0,
                             max_value=10.0,
                             value=float(config.get("taux_placement_exces_tva", 1.5)),
                             step=0.1,
                             format="%.1f"
                         )
                         st.session_state.config["taux_placement_exces_tva"] = taux_tva
                 else:
                     st.info("💡 La gestion des placements est désactivée. La trésorerie restera non rémunérée.")
            else:
                 st.session_state.config["cout_fonds_propres"] = st.number_input("Coût des Fonds Propres Annuel (%)", min_value=0.0, max_value=25.0, value=float(config.get("cout_fonds_propres", 8.0)), step=0.5, key="fin_equity_cost")
                 # Forcer les valeurs liées au prêt à 0 si pas de prêt
                 st.session_state.config["debt_ratio"] = 0.0
                 st.session_state.config["taux_interet_dette"] = 0.0
                 st.session_state.config["debt_term_years"] = 0
                 st.session_state.config["target_dscr"] = 1.0 # Ou une autre valeur neutre
                 st.session_state.config["capitalize_construction_interest"] = True # Pas d'effet sans prêt


        # --- Onglet 4: Configuration par Site (NOUVEAU & DYNAMIQUE) ---
        with tab_sites:
            st.markdown("<h3 class='sub-header'>Configuration Spécifique par Site</h3>", unsafe_allow_html=True)

            # Vérifier si des données de site ont été chargées
            # Utiliser .get pour éviter KeyError si sites_data n'existe pas encore
            sites_data_dict = st.session_state.get('sites_data', {})
            if sites_data_dict:
                site_ids = sorted(list(sites_data_dict.keys()))
                st.info(f"Configurez les paramètres financiers pour chacun des **{len(site_ids)}** site(s) importé(s). Ces valeurs seront utilisées pour calculer les totaux CAPEX/OPEX/Puissance du projet.")

                for site_id in site_ids:
                    # Récupérer la config existante ou un dict vide pour ce site
                    # Utiliser setdefault pour créer l'entrée si elle manque dans sites_config
                    site_cfg = sites_config.setdefault(site_id, {})
                    original_filename = site_cfg.get('nom_fichier', site_id)

                    with st.expander(f"Site : {original_filename} (ID: `{site_id}`)"):
                        # --- AJOUT: Type de Site ---
                        site_type = st.selectbox(
                            "Type de Site",
                            options=["Producteur", "Consommateur Pur"],
                            # Index par défaut basé sur puissance actuelle ou type stocké
                            index=0 if site_cfg.get('site_type', 'Producteur' if site_cfg.get('puissance_kwc', 0.0) > 0 else 'Consommateur Pur') == 'Producteur' else 1,
                            key=f"cfg_type_{site_id}",
                            help="Choisir 'Consommateur Pur' désactive les champs liés à la production (Puissance, CAPEX, OPEX)."
                        )
                        site_cfg['site_type'] = site_type # Stocker le type
                        is_consumer = (site_type == "Consommateur Pur")
                        # is_producer est l'inverse, utiliser is_consumer rend le code plus clair
                        # is_producer = not is_consumer # On peut utiliser is_consumer directement

                        col_s1, col_s2, col_s3 = st.columns(3)
                        # -- Puissance --
                        with col_s1:
                            # Lire valeur existante ou proposer 0 comme défaut
                            current_power = float(site_cfg.get('puissance_kwc', 0.0))
                            # Valeur à afficher: 0 si conso, sinon la valeur stockée
                            value_power_widget = 0.0 if is_consumer else current_power
                            site_power_input = st.number_input(
                                f"Puissance (kWc)",
                                min_value=0.0,
                                value=value_power_widget, # Afficher 0 si conso
                                step=0.1,
                                key=f"cfg_power_{site_id}",
                                help="Puissance crête de l'installation PV. Forcée à 0 et grisée si le type est 'Consommateur Pur'.",
                                disabled=is_consumer # Griser si conso
                            )
                            # Sauvegarder 0 si conso, sinon la valeur saisie
                            site_cfg['puissance_kwc'] = 0.0 if is_consumer else site_power_input
                            # Mettre à jour la variable pour les calculs OPEX/CAPEX suivants
                            effective_power = site_cfg['puissance_kwc']

                        # -- CAPEX --
                        with col_s2:
                            # Proposer défaut 0 si conso pur, sinon basé sur puissance * 1000
                            default_capex = effective_power * 1000 if not is_consumer else 0.0
                            current_capex = float(site_cfg.get('capex', default_capex))
                            # Valeur à afficher: 0 si conso, sinon la valeur stockée
                            value_capex_widget = 0.0 if is_consumer else current_capex
                            site_capex_input = st.number_input(
                                f"CAPEX (€)",
                                min_value=0.0,
                                value=value_capex_widget, # Afficher 0 si conso
                                step=100.0,
                                format="%.0f",
                                key=f"cfg_capex_{site_id}",
                                help="Investissement initial pour ce site. Forcé à 0 et grisé si 'Consommateur Pur'.",
                                disabled=is_consumer # Griser si conso
                            )
                            # Sauvegarder 0 si conso, sinon la valeur saisie
                            site_cfg['capex'] = 0.0 if is_consumer else site_capex_input
                            # Mettre à jour la variable pour les calculs OPEX suivants
                            effective_capex = site_cfg['capex']

                        # --- NOUVELLE SECTION OPEX DÉTAILLÉE --- 
                        st.markdown("---") # Séparateur avant la nouvelle section OPEX détaillée
                        st.markdown("**OPEX Annuel de Base (avant inflation et provision onduleur)**")

                        # Utiliser is_consumer défini plus haut basé sur le Type de Site
                        # is_consumer = (site_cfg.get('site_type') == "Consommateur Pur")

                        col_o1, col_o2, col_o3 = st.columns(3) # Ou plus de colonnes si besoin

                        with col_o1:
                            # --- Entretien / Nettoyage ---
                            default_opex_maint = 0.0 # Mettre un défaut si pertinent
                            current_opex_maint = float(site_cfg.get("opex_maintenance", default_opex_maint))
                            opex_maint_input = st.number_input(
                                "Entretien/Nettoyage (€/an)",
                                min_value=0.0,
                                # Afficher 0 et désactiver si consommateur
                                value=0.0 if is_consumer else current_opex_maint,
                                step=10.0,
                                format="%.0f",
                                key=f"cfg_opex_maint_{site_id}",
                                help="Coût annuel estimé pour l'entretien et le nettoyage.",
                                disabled=is_consumer
                            )
                            # Sauvegarder 0 si conso, sinon la valeur saisie
                            site_cfg['opex_maintenance'] = 0.0 if is_consumer else opex_maint_input

                        with col_o2:
                            # --- Assurance ---
                            default_opex_insu = 0.0
                            current_opex_insu = float(site_cfg.get("opex_insurance", default_opex_insu))
                            opex_insu_input = st.number_input(
                                "Assurance (€/an)",
                                min_value=0.0,
                                value=0.0 if is_consumer else current_opex_insu,
                                step=10.0,
                                format="%.0f",
                                key=f"cfg_opex_insu_{site_id}",
                                help="Coût annuel estimé pour l'assurance.",
                                disabled=is_consumer
                            )
                            site_cfg['opex_insurance'] = 0.0 if is_consumer else opex_insu_input

                        with col_o3:
                            # --- Gestion Admin/Exploitation ---
                            default_opex_admin = 0.0
                            current_opex_admin = float(site_cfg.get("opex_admin", default_opex_admin))
                            opex_admin_input = st.number_input(
                                "Gestion Admin/Exploit. (€/an)",
                                min_value=0.0,
                                value=0.0 if is_consumer else current_opex_admin,
                                step=10.0,
                                format="%.0f",
                                key=f"cfg_opex_admin_{site_id}",
                                help="Coût annuel estimé pour la gestion administrative, suivi, etc.",
                                disabled=is_consumer
                            )
                            site_cfg['opex_admin'] = 0.0 if is_consumer else opex_admin_input

                        # Supprimer les anciennes clés OPEX globales si elles existent dans site_cfg
                        site_cfg.pop('opex_method', None)
                        site_cfg.pop('opex_value', None)

                        # --- La section Provision Onduleur reste après ---
                        st.markdown("---"); st.markdown("**Provision Remplacement Onduleur**")
                        prov_cols = st.columns([1,2,2])

                        with prov_cols[0]:
                            current_prov_enabled = site_cfg.get("opex_onduleur_provision_site", False)
                            # Activer seulement si producteur
                            site_prov_enabled_input = st.checkbox("Activer?", value=current_prov_enabled if not is_consumer else False, key=f"cfg_prov_ond_{site_id}", disabled=is_consumer)
                            # Sauvegarder True/False si producteur, False si consommateur
                            site_cfg['opex_onduleur_provision_site'] = site_prov_enabled_input if not is_consumer else False
                            # Utiliser la valeur effective pour les champs suivants
                            effective_prov_enabled = site_cfg['opex_onduleur_provision_site']

                        with prov_cols[1]: # Colonne pour le coût
                            default_total_cost = 500.0 # Coût total par défaut raisonnable
                            # Lire la valeur existante avec la NOUVELLE clé
                            current_total_cost = float(site_cfg.get("opex_onduleur_total_cost_site", default_total_cost))
                            value_cost_widget = max(0.0, current_total_cost)

                            site_total_cost_input = st.number_input(
                                "Coût Remplacement Total (€)", # <-- NOUVEAU LABEL
                                min_value=0.0,
                                value=value_cost_widget,
                                step=50.0, # Pas ajusté
                                format="%.0f", # Format euros entiers
                                key=f"cfg_prov_total_cost_{site_id}", # <-- NOUVELLE CLE
                                disabled=not effective_prov_enabled,
                                help="Coût total estimé (non indexé) pour remplacer l'onduleur de ce site."
                            )
                            # Sauvegarder la valeur sous la NOUVELLE clé
                            site_cfg['opex_onduleur_total_cost_site'] = site_total_cost_input if effective_prov_enabled else 0.0
                            # Optionnel: supprimer l'ancienne clé (bonne pratique si elle existe)
                            if 'opex_onduleur_cost_site' in site_cfg:
                                del site_cfg['opex_onduleur_cost_site']

                        with prov_cols[2]: # Colonne pour la durée de vie (inchangée)
                            default_life = 15 # Default lifetime
                            current_life_from_cfg = int(site_cfg.get("opex_onduleur_lifetime_site", default_life))
                            value_life_widget = max(1, current_life_from_cfg)
                            site_life_input = st.number_input("Durée Vie (ans)",
                                                        min_value=1,
                                                        value=value_life_widget,
                                                        step=1,
                                                        key=f"cfg_prov_life_{site_id}",
                                                        disabled=not effective_prov_enabled) # Désactiver si checkbox décochée OU si conso
                            # Sauvegarder la valeur si activé, sinon 0
                            site_cfg['opex_onduleur_lifetime_site'] = site_life_input if effective_prov_enabled else 0

                        st.session_state.sites_config[site_id] = site_cfg

            else:
                st.warning("Aucun site importé. Veuillez d'abord importer des données via l'onglet/section 'Importation Données'.")
                st.info("Après l'import, revenez sur cet onglet pour configurer chaque site.")

        # --- Onglet 5: Clés de Répartition ---
        with tab_repartition:
            st.markdown("<h3 class='sub-header'>⚖️ Gestion des Clés de Répartition</h3>", unsafe_allow_html=True)
            
            # Vérifier si des sites sont configurés
            if sites_config:
                # Importer le manager et l'interface améliorée
                try:
                    from .repartition_keys import RepartitionKeyManager
                    from .repartition_keys.key_ui_enhanced import render_enhanced_repartition_ui
                    
                    # Initialiser le manager si nécessaire
                    if 'repartition_manager' not in st.session_state:
                        st.session_state.repartition_manager = RepartitionKeyManager(sites_config)
                    else:
                        # Vérifier si le manager a la méthode update_sites_config
                        if hasattr(st.session_state.repartition_manager, 'update_sites_config'):
                            # Mettre à jour le manager avec les nouveaux sites
                            st.session_state.repartition_manager.update_sites_config(sites_config)
                        else:
                            # Recréer le manager si l'ancienne version n'a pas la méthode
                            st.session_state.repartition_manager = RepartitionKeyManager(sites_config)
                    
                    # Afficher l'interface de répartition améliorée
                    render_enhanced_repartition_ui(st.session_state.repartition_manager)
                    
                except ImportError as e:
                    st.error(f"Le module de gestion des clés de répartition n'est pas disponible : {e}")
                    st.info("Veuillez vérifier que le module 'repartition_keys' est correctement installé dans le dossier 'modules'.")
            else:
                st.warning("Aucun site configuré. Veuillez d'abord configurer des sites dans l'onglet 'Configuration par Site'.")
                st.info("Les clés de répartition permettent de définir comment l'énergie produite est distribuée entre les participants.")

        # --- Onglet 6: Scénarios ---
        with tab_scen:
            st.markdown("<h3 class='sub-header'>Gestion des Scénarios</h3>", unsafe_allow_html=True)
            # Afficher les scénarios existants et permettre leur modification/suppression
            if not st.session_state.scenarios:
                 st.info("Aucun scénario défini.")
            else:
                 # Utiliser une copie pour itérer et supprimer sans risque
                 scenarios_copy = st.session_state.scenarios.copy()
                 for scenario_name in scenarios_copy:
                      # Ne pas permettre la modification/suppression du scénario 'Base'
                      is_base = scenario_name == "Base"
                      with st.expander(f"Scénario: {scenario_name}{' (Référence)' if is_base else ''}"):
                           scenario = st.session_state.scenarios[scenario_name] # Lire la dernière version
                           new_desc = st.text_input("Description", value=scenario["description"], key=f"desc_{scenario_name}", disabled=is_base)
                           if not is_base: st.session_state.scenarios[scenario_name]["description"] = new_desc

                           col1, col2 = st.columns(2)
                           with col1:
                               new_prod_mod = st.number_input("Modif. Production", value=scenario["production_modifier"], step=0.01, key=f"prod_mod_{scenario_name}", disabled=is_base, format="%.2f")
                               new_opex_mod = st.number_input("Modif. OPEX", value=scenario["opex_modifier"], step=0.01, key=f"opex_mod_{scenario_name}", disabled=is_base, format="%.2f")
                           with col2:
                               new_capex_mod = st.number_input("Modif. CAPEX", value=scenario["capex_modifier"], step=0.01, key=f"capex_mod_{scenario_name}", disabled=is_base, format="%.2f")
                               new_inf_mod = st.number_input("Modif. Inflation", value=scenario["inflation_modifier"], step=0.01, key=f"inf_mod_{scenario_name}", disabled=is_base, format="%.2f")

                           # Mettre à jour seulement si ce n'est pas le scénario de base
                           if not is_base:
                               st.session_state.scenarios[scenario_name]["production_modifier"] = new_prod_mod
                               st.session_state.scenarios[scenario_name]["opex_modifier"] = new_opex_mod
                               st.session_state.scenarios[scenario_name]["capex_modifier"] = new_capex_mod
                               st.session_state.scenarios[scenario_name]["inflation_modifier"] = new_inf_mod

                               if st.button("Supprimer ce Scénario", key=f"del_{scenario_name}"):
                                    del st.session_state.scenarios[scenario_name]
                                    st.rerun()

            # Ajouter un nouveau scénario
            st.markdown("---")
            with st.expander("Ajouter un nouveau scénario"):
                # ... (Logique d'ajout de scénario inchangée) ...
                new_scenario_name = st.text_input("Nom du nouveau scénario", key="new_scen_name")
                new_scenario_desc = st.text_input("Description", key="new_scen_desc")
                col1, col2 = st.columns(2)
                # ... (Inputs pour modificateurs avec clés uniques) ...
                with col1:
                     new_prod_mod = st.number_input("Modif. Production", value=1.0, step=0.01, key="new_prod_mod")
                     new_opex_mod = st.number_input("Modif. OPEX", value=1.0, step=0.01, key="new_opex_mod")
                with col2:
                     new_capex_mod = st.number_input("Modif. CAPEX", value=1.0, step=0.01, key="new_capex_mod")
                     new_inflation_mod = st.number_input("Modif. Inflation", value=1.0, step=0.01, key="new_inflation_mod")

                if st.button("Ajouter le scénario", key="add_new_scen") and new_scenario_name:
                    if new_scenario_name in st.session_state.scenarios:
                        st.error("Un scénario avec ce nom existe déjà !")
                    elif new_scenario_name == "Base":
                         st.error("Le nom 'Base' est réservé.")
                    else:
                        st.session_state.scenarios[new_scenario_name] = {
                            "description": new_scenario_desc, "production_modifier": new_prod_mod,
                            "opex_modifier": new_opex_mod, "capex_modifier": new_capex_mod,
                            "inflation_modifier": new_inflation_mod
                        }
                        st.success(f"Scénario '{new_scenario_name}' ajouté.")
                        st.rerun()


        # --- Onglet 7: Sauvegarde/Chargement ---
        with tab_save:
            st.markdown("<h3 class='sub-header'>Sauvegarde et Chargement de la Configuration Complète</h3>", unsafe_allow_html=True)
            st.info("Sauvegarde la configuration globale, la configuration par site et les scénarios.")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Sauvegarder")
                config_name_save = st.text_input("Nom pour la sauvegarde", value="Config_Projet_MultiSite")
                if st.button("Sauvegarder Configuration Complète", key="save_all_config"):
                    filename = self.save_config(config_name_save) # save_config gère maintenant sites_config
                    if filename:
                         st.success(f"Configuration sauvegardée: {filename}")
                    else:
                         st.error("Échec de la sauvegarde.")
            with col2:
                st.markdown("#### Charger")
                available_configs = self.get_available_configs()
                if available_configs:
                    selected_config_load = st.selectbox("Choisir configuration à charger", available_configs, key="select_load_config")
                    if st.button("Charger Configuration Complète", key="load_all_config"):
                        if self.load_config(f"saved_configs/{selected_config_load}"): # load_config gère maintenant sites_config
                            st.success(f"Configuration '{selected_config_load}' chargée.")
                            time.sleep(1) # Laisser le temps à l'utilisateur de voir le message
                            st.rerun() # Recharger l'app pour refléter partout
                        # else: l'erreur est gérée dans load_config
                else:
                    st.info("Aucune configuration sauvegardée.")

        # Récapitulatif : Simplifié pour éviter redondance excessive
        st.markdown("---")
        # Remplacer l'expander récap par un bouton qui enregistre et force le recalcul
        # (Le récapitulatif détaillé est moins utile maintenant que les params sont par site)

        if st.button("Appliquer et Sauvegarder Tous les Paramètres Modifiés", type="primary", key="save_all_params_button"):
            # L'enregistrement se fait au fil de l'eau dans st.session_state
            # Ce bouton sert surtout à confirmer et potentiellement déclencher des recalculs ailleurs
            st.success("Paramètres de configuration (globaux et par site) mis à jour dans la session.")
            # On pourrait ajouter un appel pour forcer le recalcul de la subvention/TURPE/OA globaux ici
            # self.recalculate_global_aggregates() # Fonction à créer si besoin
            st.toast("Paramètres appliqués.", icon="✅")
            time.sleep(1)
            # Pas forcément besoin de rerun ici, sauf si des calculs dépendants doivent être rafraîchis immédiatement
            # st.rerun()


    # --- ensure_config_defaults reste utile ---
    def ensure_config_defaults(self):
        """Vérifie et complète la config GLOBALE avec les valeurs par défaut."""
        # (Garder cette fonction telle quelle, elle ne gère que st.session_state.config)
        print("DEBUG CONFIG: Vérification des clés de config globale...")
        if 'config' not in st.session_state:
            print("DEBUG CONFIG: Pas de config globale en session.")
            self.initialize_default_config()
            return

        # Dictionnaire des valeurs par défaut GLOBALES (copié de votre code)
        default_config_dict = {
             "nom_projet": "Projet Photovoltaïque ACOC", "localisation": "France",
             "date_debut_ppa": datetime.now().date().isoformat(), "duree_ppa": 240, "duree_construction": 12,
             "amortissement_duree": 15, "valeur_residuelle_pct": 0.0, "cout_demantelement_pct": 0.0,
             "degradation_rate": 0.005, "taux_inflation": 2.0, "taux_imposition": 25.0,
             "tarif_edf_reference": 0.21, "source_prix_autoconso": "prix_initial",
             "tarif_oa_bracket_le9": 0.0400, "tarif_oa_bracket_le100": 0.0761, "tarif_oa_bracket_gt100": 0.0600,
             "tarif_oa": 0.0761, "tarif_oa_indexe_inflation": True, "taux_inflation_tarif_oa": 1.89,
             "subvention_rate_le3": 100.0, "subvention_rate_le9": 80.0, "subvention_rate_le36": 190.0,
             "subvention_rate_le100": 100.0, "subvention_rate_le500": 0.0, "subvention_rate_gt100": 0.0,
             "subvention_calculee": 0.0, "turpe_prod_tension": "BT<=36kVA", "turpe_prod_contrat": "Unique",
             "turpe_prod_calculee": 0.0, "turpe_indexe_inflation": True, "cout_fonds_propres": 8.0,
             "with_loan": True, "debt_ratio": 0.80, "taux_interet_dette": 4.0, "debt_term_years": 20,
             "target_dscr": 1.2, "taux_interet_shl": 4.0, "shl_blocage_period": 60,
             "dividends_blocage_period": 60, "capitalize_construction_interest": True,
             "opex_method": "auto", "opex_percent": 1.5,
             "opex_per_kwc": 20.0,
             "pvs_feed_in_tariff": 0.1108, "pvs_avoided_cost_tariff": 0.2218,
             "constraint_min_project_irr_pct": 8.0, "constraint_max_payback": 18.0,
             "constraint_min_consumer_gain_pct": 5.0, "prix_min_revente": 0.05, "prix_max_revente": 0.40,
             "pas_optimisation": 0.001, "nb_iterations_monte_carlo": 1000, "ecart_type_production": 10.0,
             "ecart_type_consommation": 5.0,
        }

        config_changed = False
        current_config = st.session_state.config
        for key, default_value in default_config_dict.items():
            if key not in current_config:
                current_config[key] = default_value
                config_changed = True
                print(f"CONFIG GLOBALE: Ajout clé manquante '{key}'")

        # S'assurer que la config par site existe aussi
        if 'sites_config' not in st.session_state:
             st.session_state.sites_config = {}

        if config_changed:
            st.toast("Certaines clés de configuration globale manquantes ont été ajoutées.", icon="ℹ️")

# Fin de la classe ConfigModule