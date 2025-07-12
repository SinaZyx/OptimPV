import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import time

def default_tarif_oa(p_kwc: float) -> float:
    """
    Renvoie le tarif OA SUGGÉRÉ en €/kWh selon la puissance, 
    en utilisant les valeurs de base DÉFINIES DANS LA CONFIGURATION.
    """
    # Lire les tarifs de base depuis la configuration actuelle (avec valeurs par défaut robustes)
    config = st.session_state.get("config", {}) # Lire la config actuelle
    t_le9 = float(config.get("tarif_oa_bracket_le9", 0.0761))  # Exemple de défaut si clé manque
    t_le100 = float(config.get("tarif_oa_bracket_le100", 0.0761)) # Exemple de défaut
    t_gt100 = float(config.get("tarif_oa_bracket_gt100", 0.0600)) # Exemple de défaut
    
    p_kwc = float(p_kwc) 
    if p_kwc <= 9:
        return t_le9 
    elif p_kwc <= 100:
        return t_le100
    else: # > 100 kWc
        return t_gt100

class ConfigModule:
    def __init__(self):
        # Initialiser les configurations par défaut si elles n'existent pas
        if 'config' not in st.session_state:
            self.initialize_default_config()
        
        # Initialiser les scénarios
        if 'scenarios' not in st.session_state:
            self.initialize_default_scenarios()
    
    def initialize_default_config(self):
        """Initialise la configuration par défaut"""
        # Calculer la puissance par défaut une fois
        default_power = 20.0 # MODIFIÉ: Exemple de puissance par défaut
        # Définir les tarifs par défaut des paliers ICI
        default_oa_le9 = 0.0400   # Exemple pour surplus <= 9 kWc (À VÉRIFIER/ADAPTER !)
        default_oa_le100 = 0.0761 # Exemple pour surplus <= 100 kWc (À VÉRIFIER/ADAPTER !)
        default_oa_gt100 = 0.0600 # Exemple pour surplus > 100 kWc (À VÉRIFIER/ADAPTER !)
        
        # Définir les barèmes de subvention par défaut (€/kWc) - EXEMPLES À ADAPTER !
        # Basé sur structure française fréquente (mais vérifier les montants exacts !)
        default_sub_rate_le3 = 100.0 # Exemple pour <= 3 kWc (AJOUTÉ)
        default_sub_rate_le9 = 80.0   # Exemple pour <= 9 kWc
        default_sub_rate_le36 = 190.0  # Exemple pour > 9 et <= 36 kWc
        default_sub_rate_le100 = 100.0 # Exemple pour > 36 et <= 100 kWc
        default_sub_rate_le500 = 0.0  # Exemple pour > 100 et <= 500 kWc 
        default_sub_rate_gt100 = 0.0 # Exemple pour > 100 kWc (AJOUTÉ, souvent 0 mais à vérifier)
        # (Adapter/ajouter/supprimer les paliers selon la réglementation visée)
        
        st.session_state.config = {
            # Paramètres du projet
            "nom_projet": "Projet Photovoltaïque",
            "localisation": "Marseille, France",
            "puissance_kwc": default_power,  # en kWc
            
            # --- AJOUTER/MODIFIER CES LIGNES ---
            "tarif_oa_bracket_le9": default_oa_le9,        # Stocke le tarif du palier <= 9 kWc
            "tarif_oa_bracket_le100": default_oa_le100,    # Stocke le tarif du palier <= 100 kWc
            "tarif_oa_bracket_gt100": default_oa_gt100,    # Stocke le tarif du palier > 100 kWc
            # Initialise tarif_oa basé sur la puissance ET les paliers par défaut
            "tarif_oa": default_tarif_oa(default_power), 
            "tarif_oa_indexe_inflation": True, # MODIFIÉ: Default = True
            "taux_inflation_tarif_oa": 1.89, # Taux spécifique pour l'OA (en %)
            # --- FIN AJOUT ---
            
            # --- AJOUTER CES LIGNES --- 
            "subvention_rate_le3": default_sub_rate_le3, # AJOUTÉ
            "subvention_rate_le9": default_sub_rate_le9,
            "subvention_rate_le36": default_sub_rate_le36,
            "subvention_rate_le100": default_sub_rate_le100,
            "subvention_rate_le500": default_sub_rate_le500, # Ou autre palier max pertinent
            "subvention_rate_gt100": default_sub_rate_gt100, # AJOUTÉ (utilisé si > 100kWc)
            "subvention_calculee": 0.0, # Sera calculé dans show_ui
            # --- FIN AJOUT ---
            
            "opex_method": "auto",  # "auto", "percent", "kwc", "custom"
            "opex_percent": 1.5,    # % du CAPEX par an (valeur par défaut: 1.5%)
            "opex_per_kwc": 20.0,   # €/kWc/an (valeur par défaut: 20€/kWc/an)
            "opex_onduleur_provision": True,  # Inclure provision pour remplacement onduleurs
            "opex_onduleur_cost": 130.0,      # €/kWc pour remplacement onduleurs
            "opex_onduleur_lifetime": 15,     # Durée de vie estimée des onduleurs (années)
            "date_debut_ppa": datetime.now().date().isoformat(),
            "duree_ppa": 240,  # en mois
            "duree_construction": 12,  # en mois
            
            # --- AJOUT DES CLES MANQUANTES ICI ---
            "amortissement_duree": 15,         # Durée d'amortissement comptable (années)
            "valeur_residuelle_pct": 0.0,      # Valeur résiduelle en % du CAPEX net subvention
            "cout_demantelement_pct": 0.05,    # CORRIGÉ: Coût de démantèlement en % du CAPEX initial (ratio décimal)
            "source_prix_autoconso": "prix_initial", # MODIFIÉ: Default = Prix de vente initial
            # --- FIN AJOUT ---
            
            # Paramètres économiques
            "capex": 85000.0,  # en €
            "opex": 4500.0,  # en €/an
            "prix_vente_initial": 0.17,  # en €/kWh
            "taux_inflation": 2.0,  # en % par an
            "tarif_edf_reference": 0.21,  # en €/kWh
            
            # Paramètres financiers
            "taux_imposition": 25.0,  # en %
            "taux_interet_dette": 4.0,  # en %
            "cout_fonds_propres": 8.0,  # MODIFIÉ: Exemple 8%
            "target_dscr": 1.2, # <-- RAJOUTÉ (avec sa valeur par défaut)
            "debt_ratio": 0.80,  # 80% dette, 20% fonds propres
            "debt_term_years": 20,  # MODIFIÉ: Exemple 20 ans
            "with_loan": True,  # True = avec prêt, False = 100% fonds propres
            
            # Paramètres techniques
            "degradation_rate": 0.005,  # Taux de dégradation annuel (0.5% par an)
            
            # Paramètres PVSOL
            "pvs_feed_in_tariff": 0.1108,  # Prix de vente fixe (€/kWh)
            "pvs_avoided_cost_tariff": 0.2218,  # Coût évité initial (€/kWh)
            
            # Paramètres de simulation
            "taux_interet_shl": 4.0,  # en %
            
            # Périodes de blocage
            "shl_blocage_period": 60,  # en mois
            "dividends_blocage_period": 60,  # en mois
            
            # Contraintes d'optimisation
            "constraint_min_irr_pct": 8.0,  # AJOUTÉ: TRI minimum en % (exemple: 8%)
            "constraint_max_payback": 18.0, # Conservé
            "constraint_min_consumer_gain_pct": 5.0, # Conservé
            "prix_min_revente": 0.05,  # MODIFIÉ: Exemple 0.05
            "prix_max_revente": 0.40,  # MODIFIÉ: Exemple 0.40
            "pas_optimisation": 0.001, # MODIFIÉ: Exemple 0.001
            
            # Paramètres Monte Carlo
            "nb_iterations_monte_carlo": 1000,
            "ecart_type_production": 10.0,  # en %
            "ecart_type_consommation": 5.0,  # en %
        }
    
    def initialize_default_scenarios(self):
        """Initialise les scénarios par défaut"""
        st.session_state.scenarios = {
            "Base": {
                "description": "Scénario de référence",
                "production_modifier": 1.0,  # multiplicateur
                "opex_modifier": 1.0,  # multiplicateur
                "capex_modifier": 1.0,  # multiplicateur
                "inflation_modifier": 1.0,  # multiplicateur
            },
            "P90": {
                "description": "Production réduite de 5%",
                "production_modifier": 0.95,
                "opex_modifier": 1.0,
                "capex_modifier": 1.0,
                "inflation_modifier": 1.0,
            },
            "OPEX +10%": {
                "description": "Augmentation des coûts d'exploitation de 10%",
                "production_modifier": 1.0,
                "opex_modifier": 1.1,
                "capex_modifier": 1.0,
                "inflation_modifier": 1.0,
            },
            "CAPEX +10%": {
                "description": "Augmentation de l'investissement initial de 10%",
                "production_modifier": 1.0,
                "opex_modifier": 1.0,
                "capex_modifier": 1.1,
                "inflation_modifier": 1.0,
            },
            "Inflation Modifiée": {
                "description": "Inflation à 1.5% au lieu de 2%",
                "production_modifier": 1.0,
                "opex_modifier": 1.0,
                "capex_modifier": 1.0,
                "inflation_modifier": 0.75,  # 1.5/2.0
            }
        }
    
    def save_config(self, config_name):
        """Sauvegarde la configuration actuelle"""
        if not os.path.exists('saved_configs'):
            os.makedirs('saved_configs')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"saved_configs/config_{config_name}_{timestamp}.json"
        
        # Construire le dictionnaire de configuration complet
        config_to_save = {
            "config": st.session_state.config,
            "scenarios": st.session_state.scenarios,
            "metadata": {
                "date_creation": datetime.now().isoformat(),
                "nom": config_name
            }
        }
        
        # Enregistrer au format JSON
        with open(filename, 'w') as f:
            json.dump(config_to_save, f, indent=4)
        
        return filename
    
    def load_config(self, filename):
        """Charge une configuration existante"""
        try:
            with open(filename, 'r') as f:
                loaded_config = json.load(f)
            
            # Mettre à jour la configuration dans la session
            if 'config' in loaded_config:
                st.session_state.config = loaded_config['config']
            
            if 'scenarios' in loaded_config:
                st.session_state.scenarios = loaded_config['scenarios']
            
            return True
        except Exception as e:
            st.error(f"Erreur lors du chargement de la configuration: {e}")
            return False
    
    def get_available_configs(self):
        """Récupère la liste des configurations sauvegardées"""
        if not os.path.exists('saved_configs'):
            return []
        
        configs = []
        for filename in os.listdir('saved_configs'):
            if filename.endswith('.json'):
                configs.append(filename)
        
        return configs
    
    def show_ui(self):
        """Affiche l'interface utilisateur du module de configuration"""
        st.markdown("<h1 class='main-header'>Configuration du Projet</h1>", unsafe_allow_html=True)

        # Récupérer la config pour accès plus facile (mais on écrira toujours dans st.session_state)
        config = st.session_state.config

        # Créer des onglets pour organiser l'interface
        tab1, tab2, tab3, tab4 = st.tabs(["Paramètres Économiques", "Paramètres du Projet", "Scénarios", "Sauvegarde/Chargement"])

        with tab1:
            st.markdown("<h3 class='sub-header'>Paramètres Macro-économiques</h3>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                # CORRECTION: Utilisation de .get() et float()
                st.session_state.config["taux_inflation"] = st.number_input(
                    "Taux d'inflation (%)",
                    min_value=0.0,
                    max_value=10.0,
                    value=float(config.get("taux_inflation", 2.0)), # Utilise .get() et float()
                    step=0.1,
                    help="Taux d'inflation annuel en pourcentage"
                )

            with col2:
                # CORRECTION: Utilisation de .get() et float()
                st.session_state.config["taux_imposition"] = st.number_input(
                    "Taux d'imposition (%)",
                    min_value=0.0,
                    max_value=50.0,
                    value=float(config.get("taux_imposition", 25.0)), # Utilise .get() et float()
                    step=0.1,
                    help="Taux d'imposition des bénéfices en pourcentage"
                )
                
            # Ajouter la section pour contrôler l'indexation du tarif OA
            st.markdown("#### Tarifs de référence et indexation")
            
            col1, col2 = st.columns(2)
            with col1:
                # CORRECTION: Utilisation de .get() et float()
                st.session_state.config["tarif_edf_reference"] = st.number_input(
                    "Tarif EDF de référence (€/kWh)",
                    min_value=0.05,
                    max_value=0.50,
                    value=float(config.get("tarif_edf_reference", 0.21)),
                    step=0.01,
                    help="Tarif EDF actuel servant de référence pour la compétitivité",
                    key="config_tarif_edf_ref"
                )

                # Ajouter les contrôles d'indexation du tarif OA ici
                # --- Case à cocher pour indexation ---
                index_oa_checkbox = st.checkbox( 
                    "Indexer le Tarif OA sur Inflation ?",
                    value=config.get("tarif_oa_indexe_inflation", True), 
                    key="tarif_oa_index_check",
                    help="Si coché, le tarif OA augmentera chaque année."
                )
                st.session_state.config["tarif_oa_indexe_inflation"] = index_oa_checkbox

                # --- Champ Conditionnel pour le Taux Spécifique ---
                if index_oa_checkbox: # Afficher seulement si la case est cochée
                    # Utiliser .get() et float()
                    st.session_state.config["taux_inflation_tarif_oa"] = st.number_input(
                        "-> Taux d'inflation pour Tarif OA (%)", # La flèche indique que c'est conditionnel
                        min_value=0.0, max_value=10.0,
                        value=float(config.get("taux_inflation_tarif_oa", 1.89)), 
                        step=0.1,
                        help="Taux annuel spécifique utilisé SEULEMENT pour indexer le tarif OA.",
                        key="inflation_oa_rate"
                    )
                # --- FIN Bloc Conditionnel ---
                
                # --- AJOUTER CET EXPANDER ---
                st.markdown("---") # Séparateur
                with st.expander("🔧 Configuration des Barèmes Tarif OA par Défaut"):
                     st.warning("Modifiez ici les tarifs utilisés par défaut lors de l'auto-remplissage du 'Tarif OA - Rachat Surplus' en fonction de la puissance. Ces valeurs doivent refléter les tarifs réglementaires en vigueur.")
                     
                     # Utiliser .get() et float() pour robustesse
                     val_le9 = float(config.get("tarif_oa_bracket_le9", 0.0761))
                     val_le100 = float(config.get("tarif_oa_bracket_le100", 0.0761))
                     val_gt100 = float(config.get("tarif_oa_bracket_gt100", 0.0600))
                     
                     st.session_state.config["tarif_oa_bracket_le9"] = st.number_input(
                          "Tarif OA par défaut si Puissance <= 9 kWc (€/kWh)",
                          min_value=0.0, max_value=0.5, value=val_le9, step=0.0001, format="%.4f",
                          key="conf_oa_le9"
                     )
                     st.session_state.config["tarif_oa_bracket_le100"] = st.number_input(
                          "Tarif OA par défaut si 9 < Puissance <= 100 kWc (€/kWh)",
                          min_value=0.0, max_value=0.5, value=val_le100, step=0.0001, format="%.4f",
                          key="conf_oa_le100"
                     )
                     st.session_state.config["tarif_oa_bracket_gt100"] = st.number_input(
                          "Tarif OA par défaut si Puissance > 100 kWc (€/kWh)",
                          min_value=0.0, max_value=0.5, value=val_gt100, step=0.0001, format="%.4f",
                          key="conf_oa_gt100"
                     )
                # --- FIN EXPANDER ---

            st.markdown("<h3 class='sub-header'>Paramètres Financiers</h3>", unsafe_allow_html=True)

            # Ajouter la case à cocher pour le mode de financement
            # CORRECTION: Utilisation de .get()
            st.session_state.config["with_loan"] = st.checkbox(
                "Financement avec prêt bancaire",
                value=config.get("with_loan", True), # Utilise .get()
                help="Décochez pour simuler un projet financé à 100% par fonds propres"
            )

            # Conditionnellement afficher les paramètres de prêt uniquement si "with_loan" est True
            if st.session_state.config["with_loan"]:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    # CORRECTION: Utilisation de .get() et float()
                    st.session_state.config["target_dscr"] = st.number_input(
                        "Target DSCR",
                        min_value=1.0,
                        max_value=2.0,
                        value=float(config.get("target_dscr", 1.2)), # Utilise .get() et float()
                        step=0.01,
                        help="Ratio de couverture du service de la dette cible"
                    )

                with col2:
                    # CORRECTION: Utilisation de .get() et float()
                    st.session_state.config["taux_interet_dette"] = st.number_input(
                        "Taux d'intérêt de la dette (%)",
                        min_value=0.0,
                        max_value=10.0,
                        value=float(config.get("taux_interet_dette", 4.0)), # Utilise .get() et float()
                        step=0.1,
                        help="Taux d'intérêt annuel de la dette en pourcentage"
                    )

                with col3:
                    # CORRECTION: Utilisation de .get() (int, pas besoin de float ici car step=1)
                    st.session_state.config["debt_term_years"] = st.number_input(
                        "Durée du prêt (années)",
                        min_value=5,
                        max_value=30,
                        value=config.get("debt_term_years", 20), # Utilise .get()
                        step=1,
                        help="Durée du prêt bancaire en années"
                    )

                with col4:
                    # --- DÉBUT DU BLOC CORRIGÉ pour Ratio Dette/Total ---
                    # Récupérer la valeur stockée de manière sûre, avec 0.80 comme défaut
                    stored_ratio = config.get("debt_ratio", 0.80)

                    # Vérifier si la valeur stockée semble être un pourcentage incorrect (ex: > 1)
                    if stored_ratio > 1.0:
                        stored_ratio = stored_ratio / 100.0
                        stored_ratio = max(0.1, min(1.0, stored_ratio)) # Clamper entre 0.1 et 1.0 (10% à 100%)

                    slider_value = float(stored_ratio * 100)
                    # S'assurer que la valeur à afficher est DANS les limites min/max du slider (maintenant 10% à 100%)
                    slider_value = max(10.0, min(100.0, slider_value))

                    # Créer le slider avec la valeur corrigée et contrôlée
                    st.session_state.config["debt_ratio"] = st.slider(
                        "Ratio Dette/Total (%)",
                        min_value=10.0,
                        max_value=100.0, # <-- MODIFIÉ: Autoriser jusqu'à 100%
                        value=slider_value, # Utilise la valeur calculée et vérifiée
                        step=5.0,
                        help="Pourcentage du projet financé par dette bancaire"
                    ) / 100.0 # Re-convertir en ratio décimal pour le stockage
                    # --- FIN DU BLOC CORRIGÉ ---

                # Paramètres SHL dans une nouvelle ligne
                # CORRECTION: Utilisation de .get() et float()
                # --- SUPPRESSION DU CHAMP DE SAISIE SHL ---
                # st.session_state.config["taux_interet_shl"] = st.number_input(
                #     "Taux d'intérêt SHL (%)",
                #     min_value=0.0,
                #     max_value=15.0,
                #     value=float(config.get("taux_interet_shl", 4.0)), # Utilise .get() et float()
                #     step=0.1,
                #     help="Taux d'intérêt des prêts actionnaires (SHL) en pourcentage"
                # )
                # --- FIN SUPPRESSION ---
            else:
                # Si sans prêt, afficher uniquement le coût des fonds propres
                # CORRECTION: Utilisation de .get() et float()
                st.session_state.config["cout_fonds_propres"] = st.number_input(
                    "Coût des fonds propres (%)",
                    min_value=0.0,
                    max_value=20.0,
                    value=float(config.get("cout_fonds_propres", 8.0)), # Utilise .get() et float()
                    step=0.5,
                    help="Taux de rendement exigé par les investisseurs"
                )

                # Force le ratio de dette à 0 et met les autres paramètres de prêt à des valeurs par défaut
                st.session_state.config["debt_ratio"] = 0.0
                st.session_state.config["target_dscr"] = 1.0 # Mettre une valeur par défaut cohérente
                st.session_state.config["debt_term_years"] = 15 # Mettre une valeur par défaut cohérente
                st.session_state.config["taux_interet_dette"] = 0.0 # Mettre une valeur par défaut cohérente
            
            # --- L'ANCIENNE SECTION "Contraintes d'Optimisation" EST VIDE MAINTENANT --- 
            
            # --- SUPPRESSION DE L'EN-TÊTE ET DES WIDGETS MONTE CARLO --- 
            # st.markdown("<h3 class='sub-header'>Paramètres Monte Carlo</h3>", unsafe_allow_html=True)
            # col_mc1, col_mc2 = st.columns(2) # Deux colonnes pour les params MC
            # with col_mc1:
            #      # Nombre d'itérations MC
            #      st.session_state.config["nb_iterations_monte_carlo"] = st.number_input(
            #         "Nombre d'itérations Monte Carlo",
            #         min_value=100,
            #         max_value=10000,
            #         value=config.get("nb_iterations_monte_carlo", 1000), # Utilise .get()
            #         step=100,
            #         help="Nombre d'itérations pour la simulation Monte Carlo"
            #     )
            #          
            # with col_mc2:
            #     # Écarts-types MC
            #     col_a, col_b = st.columns(2)
            #     with col_a:
            #         st.session_state.config["ecart_type_production"] = st.number_input(
            #             "Écart-type production (%)",
            #             min_value=1.0,
            #             max_value=30.0,
            #             value=float(config.get("ecart_type_production", 10.0)), # Utilise .get() et float()
            #             step=1.0,
            #             help="Écart-type de la variabilité de production pour Monte Carlo"
            #         )
            #     
            #     with col_b:
            #         st.session_state.config["ecart_type_consommation"] = st.number_input(
            #             "Écart-type consommation (%)",
            #             min_value=1.0,
            #             max_value=30.0,
            #             value=float(config.get("ecart_type_consommation", 5.0)), # Utilise .get() et float()
            #             step=1.0,
            #             help="Écart-type de la variabilité de consommation pour Monte Carlo"
            #         )
            # --- FIN SUPPRESSION ---
        
        with tab2:
            st.markdown("<h3 class='sub-header'>Données du Projet (Général)</h3>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                # CAPEX 
                st.session_state.config["capex"] = st.number_input(
                    "CAPEX (€)", max_value=20000000.0,
                    value=float(config.get("capex", 85000.0)), step=100000.0, 
                    help="Coût d'investissement initial du projet"
                 )
                # Puissance (Nécessaire avant Tarif OA)
                puissance_kwc = st.number_input(
                    "Puissance installée (kWc)", min_value=1.0, max_value=10000.0,
                    value=float(config.get("puissance_kwc", 20.0)), step=1.0, 
                    help="Puissance crête de l'installation PV en kWc",
                    key="puissance_kwc_input_tab2" # Clé unique
                )
                st.session_state.config["puissance_kwc"] = puissance_kwc
                 
                # Durée PPA (en mois)
                st.session_state.config["duree_ppa"] = st.number_input(
                    "Durée PPA (mois)", min_value=12, max_value=360, 
                    value=config.get("duree_ppa", 240), step=12, 
                    help="Durée du contrat d'achat d'électricité en mois"
                )

                # --- AJOUT: Durée d'amortissement ---
                st.session_state.config["amortissement_duree"] = st.number_input(
                    "Durée d'amortissement (années)",
                    min_value=5, max_value=40,
                    value=int(config.get("amortissement_duree", 15)), step=1,
                    help="Durée sur laquelle l'investissement est amorti comptablement.",
                    key="amort_duree_input"
                )
                # --- FIN AJOUT ---

            with col2:
                # Taux Dégradation 
                degradation_percent = min(float(config.get("degradation_rate", 0.005)) * 100, 2.0)
                st.session_state.config["degradation_rate"] = st.number_input(
                    "Taux de dégradation annuel (%)", min_value=0.1, max_value=2.0,
                    value=degradation_percent, step=0.1, 
                    help="Taux de dégradation annuel des panneaux PV (%)"
                ) / 100.0 
                
                # Date début PPA
                try:
                    current_date_str = str(config.get("date_debut_ppa", "2023-01-01"))
                    default_date = datetime.fromisoformat(current_date_str).date()
                except ValueError:
                    default_date = datetime.now().date() 
                selected_date = st.date_input(
                     "Date de début du PPA", value=default_date,
                     min_value=datetime(2020, 1, 1).date(), max_value=datetime(2040, 12, 31).date(),
                     key="date_debut_ppa_input_tab2" # Clé unique
                 )
                st.session_state.config["date_debut_ppa"] = selected_date.isoformat()

                # --- AJOUT: Valeur Résiduelle et Coût Démantèlement ---
                st.session_state.config["valeur_residuelle_pct"] = st.number_input(
                    "Valeur résiduelle (% CAPEX net sub.)",
                    min_value=0.0, max_value=50.0,
                    value=float(config.get("valeur_residuelle_pct", 0.0)) * 100.0, step=1.0,
                    help="Valeur estimée de l'installation à la fin de l'amortissement, en % du CAPEX net de subvention.",
                    key="val_res_pct_input"
                ) / 100.0 # Convertir en décimal pour stockage

                st.session_state.config["cout_demantelement_pct"] = st.number_input(
                    "Coût démantèlement (% CAPEX brut)",
                    min_value=0.0, max_value=20.0, # max_value est bien en %
                    value=float(config.get("cout_demantelement_pct", 0.05)) * 100.0, step=1.0, # CORRIGÉ: défaut get à 0.05, multiplié par 100
                    help="Coût estimé pour démanteler l'installation en fin de vie, en % du CAPEX initial.",
                    key="cout_demant_pct_input"
                ) / 100.0 # Re-convertir en décimal pour stockage
                # --- FIN AJOUT ---

            # --- AJOUT: Source Prix Autoconsommation ---
            st.markdown("---")
            st.markdown("#### Valorisation de l'Autoconsommation")
            source_options = {
                "prix_initial": "Prix de vente initial (configuré)",
                "tarif_edf": "Tarif EDF de référence",
                "tarif_oa": "Tarif d'Obligation d'Achat (OA)"
            }
            source_prix_selection = st.selectbox(
                "Comment valoriser l'énergie autoconsommée ?",
                options=list(source_options.keys()),
                format_func=lambda x: source_options[x],
                index=list(source_options.keys()).index(config.get("source_prix_autoconso", "prix_initial")),
                help="Détermine le prix utilisé pour calculer les 'économies' générées par l'autoconsommation.",
                key="source_prix_auto_select"
            )
            st.session_state.config["source_prix_autoconso"] = source_prix_selection
            # Afficher une info sur le choix
            if source_prix_selection == 'prix_initial':
                st.caption(f"Utilisera {config.get('prix_vente_initial', 0.17):.4f} €/kWh (indexé sur inflation générale)")
            elif source_prix_selection == 'tarif_edf':
                st.caption(f"Utilisera {config.get('tarif_edf_reference', 0.21):.4f} €/kWh (indexé sur inflation générale)")
            elif source_prix_selection == 'tarif_oa':
                oa_val = config.get('tarif_oa', 0.0)
                oa_index_txt = " (indexé)" if config.get('tarif_oa_indexe_inflation', True) else " (non indexé)"
                st.caption(f"Utilisera {oa_val:.4f} €/kWh{oa_index_txt}")
            # --- FIN AJOUT ---
            
            # --- AJOUT: Section pour configurer les barèmes de subvention ---
            st.markdown("---")
            with st.expander("🔧 Configuration Barème Prime à l'Investissement (€/kWc)"):
                st.caption("Modifiez ici les taux de subvention par kWc pour chaque palier de puissance. Ces taux serviront à calculer automatiquement le montant total de la prime.")

                col_sub1, col_sub2 = st.columns(2)
                with col_sub1:
                    st.session_state.config["subvention_rate_le9"] = st.number_input(
                        "Taux Subvention (P <= 9 kWc) [€/kWc]", min_value=0.0, 
                        value=float(config.get("subvention_rate_le9", 80.0)), step=1.0, 
                        key="conf_sub_le9", format="%.1f"
                    )
                    st.session_state.config["subvention_rate_le36"] = st.number_input(
                        "Taux Subvention (9 < P <= 36 kWc) [€/kWc]", min_value=0.0, 
                        value=float(config.get("subvention_rate_le36", 190.0)), step=1.0, 
                        key="conf_sub_le36", format="%.1f"
                    )
                with col_sub2:
                    st.session_state.config["subvention_rate_le100"] = st.number_input(
                        "Taux Subvention (36 < P <= 100 kWc) [€/kWc]", min_value=0.0, 
                        value=float(config.get("subvention_rate_le100", 100.0)), step=1.0, 
                        key="conf_sub_le100", format="%.1f"
                    )
                    st.session_state.config["subvention_rate_le500"] = st.number_input(
                        "Taux Subvention (100 < P <= 500 kWc) [€/kWc]", min_value=0.0, 
                        value=float(config.get("subvention_rate_le500", 0.0)), step=1.0, 
                        key="conf_sub_le500", format="%.1f"
                    )
                st.caption("*Adaptez les paliers et taux selon la réglementation applicable.*")
            # --- FIN EXPANDER SUBVENTION ---

            # --- AJOUT: Calcul et affichage de la subvention totale ---
            # Lire la puissance configurée
            puissance_actuelle = float(config.get("puissance_kwc", 0.0))
            # Lire les taux des barèmes configurés
            rate_le9 = float(config.get("subvention_rate_le9", 0.0))
            rate_le36 = float(config.get("subvention_rate_le36", 0.0))
            rate_le100 = float(config.get("subvention_rate_le100", 0.0))
            rate_le500 = float(config.get("subvention_rate_le500", 0.0))
            # Déterminer le taux applicable
            applicable_rate = 0.0
            if puissance_actuelle <= 9: applicable_rate = rate_le9
            elif puissance_actuelle <= 36: applicable_rate = rate_le36
            elif puissance_actuelle <= 100: applicable_rate = rate_le100
            elif puissance_actuelle <= 500: applicable_rate = rate_le500
            # (Ajouter d'autres paliers ou une logique pour > 500 si nécessaire)

            # Calculer et sauvegarder le total
            total_subvention_calculee = applicable_rate * puissance_actuelle
            st.session_state.config["subvention_calculee"] = total_subvention_calculee

            # Afficher le résultat (par exemple près du CAPEX)
            st.info(f"Prime à l'investissement calculée : **{total_subvention_calculee:,.2f} €** ({applicable_rate:.1f} €/kWc appliqué à {puissance_actuelle:.1f} kWc)")
            # --- FIN CALCUL ET AFFICHAGE SUBVENTION ---
                 
            # Calculateur d'OPEX (Reste dans tab2 mais après les paramètres généraux)
            st.markdown("---") # Séparateur visuel
            st.markdown("#### Calculateur d'OPEX Annuel")
            
            # Utiliser des noms de variables différents pour les colonnes ici pour éviter conflits
            col1_opex, col2_opex = st.columns(2) 
            with col1_opex:
                opex_method = st.radio(
                    "Méthode de calcul OPEX", options=["auto", "percent", "kwc", "custom"],
                    format_func=lambda x: {"auto": "Automatique", "percent": "% CAPEX", "kwc": "€/kWc", "custom": "Personnalisé"}[x],
                    index=["auto", "percent", "kwc", "custom"].index(config.get("opex_method", "auto")), 
                    key="opex_method_radio_tab2" # Clé unique
                )
                st.session_state.config["opex_method"] = opex_method
                
                opex_onduleur_provision = st.checkbox(
                    "Inclure provision onduleurs", value=config.get("opex_onduleur_provision", True),
                    help="Ajoute une provision annuelle pour le remplacement futur des onduleurs",
                    key="opex_onduleur_check_tab2" # Clé unique
                )
                st.session_state.config["opex_onduleur_provision"] = opex_onduleur_provision
                
                if opex_onduleur_provision:
                     opex_onduleur_cost = st.number_input(
                        "Coût onduleurs (€/kWc)", min_value=50.0, max_value=300.0,
                        value=float(config.get("opex_onduleur_cost", 130.0)), step=10.0, 
                        help="Coût de remplacement des onduleurs en €/kWc",
                        key="opex_onduleur_cost_tab2" # Clé unique
                     )
                     st.session_state.config["opex_onduleur_cost"] = opex_onduleur_cost

            with col2_opex:
                # Calcul de l'opex basé sur la méthode choisie
                capex_val = config.get("capex", 85000.0) 
                puissance_val = config.get("puissance_kwc", 20.0)
                calculated_opex = config.get("opex", 4500.0) # Valeur par défaut si custom ou erreur

                if opex_method == "percent":
                    opex_percent = st.slider(
                        "OPEX en % du CAPEX", min_value=0.5, max_value=5.0,
                        value=float(config.get("opex_percent", 1.5)), step=0.1, 
                        key="opex_percent_slider_tab2" # Clé unique
                    )
                    st.session_state.config["opex_percent"] = opex_percent
                    calculated_opex = capex_val * (opex_percent / 100.0)
                    st.info(f"OPEX de base calculé : {calculated_opex:.2f} €/an")
                
                elif opex_method == "kwc":
                    opex_per_kwc = st.slider(
                        "OPEX en €/kWc/an", min_value=5.0, max_value=100.0,
                        value=float(config.get("opex_per_kwc", 20.0)), step=1.0, 
                        key="opex_per_kwc_slider_tab2" # Clé unique
                    )
                    st.session_state.config["opex_per_kwc"] = opex_per_kwc
                    calculated_opex = puissance_val * opex_per_kwc
                    st.info(f"OPEX de base calculé : {calculated_opex:.2f} €/an")
                
                elif opex_method == "auto":
                    opex_by_percent = capex_val * 0.015
                    opex_by_kwc = puissance_val * 20 
                    calculated_opex = (opex_by_percent + opex_by_kwc) / 2
                    st.info(f"OPEX de base calculé : {calculated_opex:.2f} €/an (auto)")
                
                # Champ pour OPEX custom (s'affiche seulement si méthode = custom)
                if opex_method == "custom":
                    opex_custom_input = st.number_input(
                        "OPEX annuel personnalisé (€/an)", min_value=0.0, max_value=100000.0,
                        value=float(config.get("opex", 4500.0)), step=100.0, 
                        key="opex_custom_input_tab2" # Clé unique
                    )
                    st.session_state.config["opex"] = opex_custom_input # Si custom, c'est la valeur de base
                    calculated_opex = opex_custom_input # Pour le calcul de la provision ci-dessous
                
                # Calcul et affichage de la provision onduleur
                if opex_onduleur_provision:
                     opex_onduleur_lifetime = st.number_input(
                        "Durée de vie onduleurs (années)", min_value=8, max_value=20,
                        value=config.get("opex_onduleur_lifetime", 15), step=1, 
                        key="opex_lifetime_input_tab2" # Clé unique
                     )
                     st.session_state.config["opex_onduleur_lifetime"] = opex_onduleur_lifetime
                     opex_onduleur_cost_val = config.get("opex_onduleur_cost", 130.0)
                     safe_lifetime = opex_onduleur_lifetime if opex_onduleur_lifetime > 0 else 1
                     onduleur_provision_val = (puissance_val * opex_onduleur_cost_val) / safe_lifetime
                     st.info(f"Provision onduleurs : + {onduleur_provision_val:.2f} €/an")
                     # Ajouter la provision à l'OPEX final (sauf si custom, où on l'ajoute à la valeur custom saisie)
                     if opex_method != "custom":
                          st.session_state.config["opex"] = calculated_opex + onduleur_provision_val
                     else:
                           # On a déjà mis opex_custom dans config["opex"]
                           st.session_state.config["opex"] = st.session_state.config["opex"] + onduleur_provision_val 
                     st.success(f"OPEX total utilisé : {st.session_state.config['opex']:.2f} €/an")

                else: # Si pas de provision et pas custom, on sauvegarde l'opex calculé
                     if opex_method != "custom":
                          st.session_state.config["opex"] = calculated_opex
                          st.info(f"OPEX total utilisé : {calculated_opex:.2f} €/an")
        
        with tab3:
            st.markdown("<h3 class='sub-header'>Scénarios d'Analyse</h3>", unsafe_allow_html=True)
            
            # Afficher les scénarios existants et permettre leur modification
            for scenario_name, scenario in st.session_state.scenarios.items():
                with st.expander(f"Scénario: {scenario_name}"):
                    st.text_input("Description", value=scenario["description"], key=f"desc_{scenario_name}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.session_state.scenarios[scenario_name]["production_modifier"] = st.number_input(
                            "Modificateur de production",
                            min_value=0.5,
                            max_value=1.5,
                            value=scenario["production_modifier"],
                            step=0.01,
                            key=f"prod_mod_{scenario_name}",
                            help="Facteur multiplicatif appliqué à la production"
                        )
                        
                        st.session_state.scenarios[scenario_name]["opex_modifier"] = st.number_input(
                            "Modificateur OPEX",
                            min_value=0.5,
                            max_value=1.5,
                            value=scenario["opex_modifier"],
                            step=0.01,
                            key=f"opex_mod_{scenario_name}",
                            help="Facteur multiplicatif appliqué aux OPEX"
                        )
                    
                    with col2:
                        st.session_state.scenarios[scenario_name]["capex_modifier"] = st.number_input(
                            "Modificateur CAPEX",
                            min_value=0.5,
                            max_value=1.5,
                            value=scenario["capex_modifier"],
                            step=0.01,
                            key=f"capex_mod_{scenario_name}",
                            help="Facteur multiplicatif appliqué au CAPEX"
                        )
                        
                        st.session_state.scenarios[scenario_name]["inflation_modifier"] = st.number_input(
                            "Modificateur Inflation",
                            min_value=0.5,
                            max_value=1.5,
                            value=scenario["inflation_modifier"],
                            step=0.01,
                            key=f"inf_mod_{scenario_name}",
                            help="Facteur multiplicatif appliqué au taux d'inflation"
                        )
            
            # Ajouter un nouveau scénario
            st.markdown("---")
            with st.expander("Ajouter un nouveau scénario"):
                new_scenario_name = st.text_input("Nom du nouveau scénario")
                new_scenario_desc = st.text_input("Description")
                
                col1, col2 = st.columns(2)
                with col1:
                    new_prod_mod = st.number_input(
                        "Modificateur de production",
                        min_value=0.5,
                        max_value=1.5,
                        value=1.0,
                        step=0.01,
                        key="new_prod_mod"
                    )
                    
                    new_opex_mod = st.number_input(
                        "Modificateur OPEX",
                        min_value=0.5,
                        max_value=1.5,
                        value=1.0,
                        step=0.01,
                        key="new_opex_mod"
                    )
                
                with col2:
                    new_capex_mod = st.number_input(
                        "Modificateur CAPEX",
                        min_value=0.5,
                        max_value=1.5,
                        value=1.0,
                        step=0.01,
                        key="new_capex_mod"
                    )
                    
                    new_inflation_mod = st.number_input(
                        "Modificateur Inflation",
                        min_value=0.5,
                        max_value=1.5,
                        value=1.0,
                        step=0.01,
                        key="new_inflation_mod"
                    )
                
                if st.button("Ajouter le scénario") and new_scenario_name:
                    # Vérifier que le nom n'existe pas déjà
                    if new_scenario_name in st.session_state.scenarios:
                        st.error("Un scénario avec ce nom existe déjà !")
                    else:
                        # Ajouter le nouveau scénario
                        st.session_state.scenarios[new_scenario_name] = {
                            "description": new_scenario_desc,
                            "production_modifier": new_prod_mod,
                            "opex_modifier": new_opex_mod,
                            "capex_modifier": new_capex_mod,
                            "inflation_modifier": new_inflation_mod
                        }
                        st.success(f"Scénario '{new_scenario_name}' ajouté avec succès !")
                        st.rerun()
                        
            # Paramètres Spécifiques pour Comparaison PVSOL
            st.markdown("---")
            st.markdown("<h3 class='sub-header'>Paramètres Spécifiques pour Comparaison PVSOL</h3>", unsafe_allow_html=True)
            
            st.info("Ces paramètres sont utilisés pour reproduire les calculs de cash flow du PDF importé depuis PVSOL.")
            
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.config["pvs_feed_in_tariff"] = float(st.number_input(
                    "Tarif de revente PVSOL (€/kWh)",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(st.session_state.config.get("pvs_feed_in_tariff", 0.1108)),
                    step=0.0001,
                    format="%.4f"
                ))
            
            with col2:
                st.session_state.config["pvs_avoided_cost_tariff"] = float(st.number_input(
                    "Prix travail initial PVSOL (€/kWh)",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(st.session_state.config.get("pvs_avoided_cost_tariff", 0.2218)),
                    step=0.0001,
                    format="%.4f"
                ))
                
            st.warning("Pour correspondre aux spécifications du PDF, veuillez régler le 'Taux d'inflation' à 2.0% et 'OPEX annuel' à 0.0 €.")
        
        with tab4:
            st.markdown("<h3 class='sub-header'>Sauvegarde et Chargement</h3>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Sauvegarde de la configuration")
                config_name = st.text_input("Nom de la configuration", value="Config_Projet")
                
                if st.button("Sauvegarder la configuration"):
                    filename = self.save_config(config_name)
                    st.success(f"Configuration sauvegardée avec succès dans le fichier : {filename}")
            
            with col2:
                st.markdown("#### Chargement d'une configuration")
                available_configs = self.get_available_configs()
                
                if available_configs:
                    selected_config = st.selectbox("Sélectionner une configuration", available_configs)
                    
                    if st.button("Charger la configuration"):
                        if self.load_config(f"saved_configs/{selected_config}"):
                            st.success(f"Configuration '{selected_config}' chargée avec succès !")
                            st.rerun()
                else:
                    st.info("Aucune configuration sauvegardée disponible.")
        
        # Afficher un récapitulatif des paramètres
        st.markdown("---")
        st.markdown("<h3 class='sub-header'>Récapitulatif des Paramètres</h3>", unsafe_allow_html=True)
        
        with st.expander("Afficher le récapitulatif des paramètres"):
            # Paramètres économiques
            st.markdown("#### Paramètres Économiques")
            st.write(f"Mode de financement: {'Avec prêt bancaire' if st.session_state.config.get('with_loan', True) else '100% fonds propres'}")
            if st.session_state.config.get('with_loan', True):
                st.write(f"Ratio Dette/Fonds propres: {st.session_state.config.get('debt_ratio', 0.80)*100:.0f}% / {(1-st.session_state.config.get('debt_ratio', 0.80))*100:.0f}%")
                st.write(f"Target DSCR: {st.session_state.config.get('target_dscr', 1.2)}")
                st.write(f"Taux d'intérêt de la dette: {st.session_state.config.get('taux_interet_dette', 4.0)}%")
                st.write(f"Durée du prêt: {st.session_state.config.get('debt_term_years', 15)} ans")
            st.write(f"Taux d'inflation: {st.session_state.config.get('taux_inflation', 2.0)}%")
            st.write(f"Taux d'imposition: {st.session_state.config.get('taux_imposition', 25.0)}%")
            
            # Paramètres du projet
            st.markdown("#### Paramètres du Projet")
            st.write(f"CAPEX: {st.session_state.config.get('capex', 0.0):,.2f} €")
            st.write(f"OPEX: {st.session_state.config.get('opex', 0.0):,.2f} €/an")
            
            method_names = {
                "auto": "Automatique",
                "percent": f"{st.session_state.config.get('opex_percent', 1.5):.1f}% du CAPEX",
                "kwc": f"{st.session_state.config.get('opex_per_kwc', 20.0):.1f} €/kWc/an",
                "custom": "Personnalisé"
            }

            st.write(f"Méthode calcul OPEX: {method_names.get(st.session_state.config.get('opex_method', 'auto'))}")
            if st.session_state.config.get("opex_onduleur_provision", True):
                # Vérifier que les clés nécessaires existent et ont des valeurs non nulles avant le calcul
                puissance = st.session_state.config.get("puissance_kwc", 0)
                cost = st.session_state.config.get("opex_onduleur_cost", 0)
                lifetime = st.session_state.config.get("opex_onduleur_lifetime", 1) # Eviter division par zéro
                if puissance > 0 and cost > 0 and lifetime > 0:
                     onduleur_provision = (puissance * cost) / lifetime
                     st.write(f"Provision onduleurs: {onduleur_provision:,.2f} €/an incluse")
                else:
                     st.write("Provision onduleurs: (Paramètres manquants ou nuls)")
            
            st.write(f"Durée de construction: {st.session_state.config.get('duree_construction', 12)} mois")
            st.write(f"Date de début du PPA: {st.session_state.config.get('date_debut_ppa', '2023-01-01')} ") # Espace ajouté pour éviter conflit potentiel
            
            # Périodes de blocage
            st.write(f"Période de blocage SHL: {st.session_state.config.get('shl_blocage_period', 60)} mois")
            st.write(f"Période de blocage des dividendes: {st.session_state.config.get('dividends_blocage_period', 60)} mois")
            
            # Contraintes d'optimisation
            st.markdown("#### Contraintes d'Optimisation")
            st.write(f"Tarif EDF de référence: {st.session_state.config.get('tarif_edf_reference', 0.21)} €/kWh")
            st.write(f"Prix min de revente: {st.session_state.config.get('prix_min_revente', 0.05)} €/kWh")
            st.write(f"Prix max de revente: {st.session_state.config.get('prix_max_revente', 0.40)} €/kWh")
            st.write(f"Pas d'optimisation: {st.session_state.config.get('pas_optimisation', 0.001)} €/kWh")
            st.write(f"Nombre d'itérations Monte Carlo: {st.session_state.config.get('nb_iterations_monte_carlo', 1000)}")
            st.write(f"Écart-type production: {st.session_state.config.get('ecart_type_production', 10.0)}%")
            st.write(f"Écart-type consommation: {st.session_state.config.get('ecart_type_consommation', 5.0)}%")

        # Bouton pour enregistrer les modifications de configuration
        st.markdown("---")
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Enregistrer les paramètres", type="primary"):
                st.session_state.config_saved = True
                st.success("Paramètres enregistrés avec succès!")
                # self.update_config(st.session_state.config)
                time.sleep(1)
                st.rerun()
        
        with col2:
            st.info("Cliquez sur ce bouton pour sauvegarder tous les paramètres ci-dessus et actualiser la page.")
            
    def ensure_config_defaults(self):
        """
        Assure que toutes les clés définies dans initialize_default_config 
        existent dans la config actuellement en session (st.session_state.config),
        en ajoutant les clés manquantes avec leur valeur par défaut.
        """
        print("DEBUG CONFIG: Vérification des clés de config après chargement...")
        if 'config' not in st.session_state:
            # Si pas de config du tout, l'initialisation par défaut devrait déjà avoir eu lieu
            print("DEBUG CONFIG: Pas de config en session - rien à vérifier.")
            # S'assurer qu'elle est appelée au cas où
            if 'config_module' in st.session_state:
                 st.session_state.config_module.initialize_default_config()
            else:
                 ConfigModule().initialize_default_config() # Fallback
            return

        # --- Dictionnaire des valeurs par défaut ---
        # IMPORTANT : MAINTENIR CE DICTIONNAIRE SYNCHRONISÉ AVEC initialize_default_config !!!
        default_power = 20.0 # Même valeur que dans init
        default_config_dict = { 
             "nom_projet": "Projet Photovoltaïque", "localisation": "Marseille, France", 
             "puissance_kwc": default_power, 
             "tarif_oa_bracket_le9": 0.0400,
             "tarif_oa_bracket_le100": 0.0761,
             "tarif_oa_bracket_gt100": 0.0600,
             "tarif_oa": 0.0761, # Valeur par défaut simple, sera recalculée
             "tarif_oa_indexe_inflation": True, # MODIFIÉ: Default = True
             "taux_inflation_tarif_oa": 1.89,
             "subvention_rate_le3": 100.0,
             "subvention_rate_le9": 80.0,
             "subvention_rate_le36": 190.0,
             "subvention_rate_le100": 100.0,
             "subvention_rate_le500": 0.0,
             "subvention_rate_gt100": 0.0,
             "subvention_calculee": 0.0,
             "opex_method": "auto", "opex_percent": 1.5, "opex_per_kwc": 20.0, 
             "opex_onduleur_provision": True, "opex_onduleur_cost": 130.0, 
             "opex_onduleur_lifetime": 15,
             "date_debut_ppa": datetime.now().date().isoformat(),
             "duree_ppa": 240, "duree_construction": 12, 
             
             "amortissement_duree": 15,
             "valeur_residuelle_pct": 0.0,
             "cout_demantelement_pct": 0.05,
             "source_prix_autoconso": "prix_initial", # MODIFIÉ: Default = Prix de vente initial
             # Paramètres économiques
             "capex": 85000.0,
             "opex": 4500.0,
             "prix_vente_initial": 0.17,
             "taux_inflation": 2.0,
             "tarif_edf_reference": 0.21,
             
             # Paramètres financiers
             "taux_imposition": 25.0,
             "taux_interet_dette": 4.0,
             "cout_fonds_propres": 8.0,
             "target_dscr": 1.2, # <-- RAJOUTÉ
             "debt_ratio": 0.80,
             "debt_term_years": 20,
             "with_loan": True,
             
             # Paramètres techniques
             "degradation_rate": 0.005,
             
             # Paramètres PVSOL
             "pvs_feed_in_tariff": 0.1108,
             "pvs_avoided_cost_tariff": 0.2218,
             
             # Paramètres de simulation
             "taux_interet_shl": 4.0,
             
             # Périodes de blocage
             "shl_blocage_period": 60,
             "dividends_blocage_period": 60,
             
             # Contraintes d'optimisation
             "constraint_min_irr_pct": 8.0, # AJOUTÉ
             "constraint_max_payback": 18.0,
             "constraint_min_consumer_gain_pct": 5.0,
             "prix_min_revente": 0.05,  # MODIFIÉ
             "prix_max_revente": 0.40,  # MODIFIÉ
             "pas_optimisation": 0.001, # MODIFIÉ
             
             # Paramètres Monte Carlo
             "nb_iterations_monte_carlo": 1000,
             "ecart_type_production": 10.0,
             "ecart_type_consommation": 5.0,
        }
        # --- Fin Dictionnaire des défauts ---

        config_changed = False
        current_config = st.session_state.config
        for key, default_value in default_config_dict.items():
            if key not in current_config:
                current_config[key] = default_value # Ajouter la clé manquante
                config_changed = True
                print(f"CONFIG: Ajout clé manquante '{key}' avec valeur par défaut lors du chargement.")
        
        if config_changed:
            st.toast("Certaines clés de configuration manquantes ont été ajoutées avec leurs valeurs par défaut.", icon="ℹ️")
            print("DEBUG CONFIG: ensure_config_defaults a ajouté des clés.")