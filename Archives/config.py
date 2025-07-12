import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import time

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
        st.session_state.config = {
            # Paramètres du projet
            "nom_projet": "Projet Photovoltaïque",
            "localisation": "Marseille, France",
            "puissance_kwc": 500,  # en kWc
            "opex_method": "auto",  # "auto", "percent", "kwc", "custom"
            "opex_percent": 1.5,    # % du CAPEX par an (valeur par défaut: 1.5%)
            "opex_per_kwc": 20.0,   # €/kWc/an (valeur par défaut: 20€/kWc/an)
            "opex_onduleur_provision": True,  # Inclure provision pour remplacement onduleurs
            "opex_onduleur_cost": 130.0,      # €/kWc pour remplacement onduleurs
            "opex_onduleur_lifetime": 14,     # Durée de vie estimée des onduleurs (années)
            "date_debut_ppa": "2023-01-01",
            "duree_ppa": 240,  # en mois
            "duree_construction": 12,  # en mois
            
            # Paramètres économiques
            "capex": 85000.0,  # en €
            "opex": 4500.0,  # en €/an
            "prix_vente_initial": 0.17,  # en €/kWh
            "taux_inflation": 2.0,  # en % par an
            "tarif_edf_reference": 0.21,  # en €/kWh
            
            # Paramètres financiers
            "taux_imposition": 25.0,  # en %
            "taux_interet_dette": 4.0,  # en %
            "cout_fonds_propres": 8.0,  # en %
            "target_dscr": 1.2,
            "debt_ratio": 0.80,  # 80% dette, 20% fonds propres
            "debt_term_years": 15,  # Durée du prêt en années
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
            "prix_min_revente": 0.15,  # en €/kWh
            "prix_max_revente": 0.21,  # en €/kWh
            "pas_optimisation": 0.01,  # en €/kWh
            
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
                        value=config.get("debt_term_years", 15), # Utilise .get()
                        step=1,
                        help="Durée du prêt bancaire en années"
                    )

                with col4:
                    # --- DÉBUT DU BLOC CORRIGÉ pour Ratio Dette/Total ---
                    # Récupérer la valeur stockée de manière sûre, avec 0.80 comme défaut
                    stored_ratio = config.get("debt_ratio", 0.80)

                    # Vérifier si la valeur stockée semble être un pourcentage incorrect (ex: > 1)
                    if stored_ratio > 1.0:
                        # Si oui, supposer que c'était un pourcentage et le reconvertir en ratio décimal
                        stored_ratio = stored_ratio / 100.0
                        # Optionnel : Clamper la valeur corrigée pour qu'elle soit dans les limites attendues (0.1 à 0.9)
                        stored_ratio = max(0.1, min(0.9, stored_ratio)) 
                        # Note : On ne modifie pas st.session_state ici directement pour éviter des boucles infinies

                    # Calculer la valeur à afficher dans le slider (en pourcentage)
                    # Assurer la conversion en float
                    slider_value = float(stored_ratio * 100)

                    # S'assurer que la valeur à afficher est DANS les limites min/max du slider
                    slider_value = max(10.0, min(90.0, slider_value))

                    # Créer le slider avec la valeur corrigée et contrôlée
                    st.session_state.config["debt_ratio"] = st.slider(
                        "Ratio Dette/Total (%)",
                        min_value=10.0,
                        max_value=90.0,
                        value=slider_value, # Utilise la valeur calculée et vérifiée
                        step=5.0,
                        help="Pourcentage du projet financé par dette bancaire"
                    ) / 100.0 # Re-convertir en ratio décimal pour le stockage
                    # --- FIN DU BLOC CORRIGÉ ---

                # Paramètres SHL dans une nouvelle ligne
                # CORRECTION: Utilisation de .get() et float()
                st.session_state.config["taux_interet_shl"] = st.number_input(
                    "Taux d'intérêt SHL (%)",
                    min_value=0.0,
                    max_value=15.0,
                    value=float(config.get("taux_interet_shl", 4.0)), # Utilise .get() et float()
                    step=0.1,
                    help="Taux d'intérêt des prêts actionnaires (SHL) en pourcentage"
                )
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
            
            st.markdown("<h3 class='sub-header'>Contraintes d'Optimisation</h3>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            # Récupérer les valeurs limites de manière sûre une seule fois
            tarif_edf_ref_val = config.get("tarif_edf_reference", 0.21)
            prix_min_revente_val = config.get("prix_min_revente", 0.15)

            with col1:
                # CORRECTION: Utilisation de .get() et float()
                st.session_state.config["tarif_edf_reference"] = st.number_input(
                    "Tarif EDF de référence (€/kWh)",
                    min_value=0.05,
                    max_value=0.50,
                    value=float(tarif_edf_ref_val), # Utilise la variable locale sûre et float()
                    step=0.01,
                    help="Tarif EDF actuel servant de référence pour la compétitivité"
                )

                # CORRECTION: Utilisation de .get(), float(), et max_value sécurisé
                st.session_state.config["prix_min_revente"] = st.number_input(
                    "Prix minimum de revente (€/kWh)",
                    min_value=0.05,
                    max_value=float(config.get("tarif_edf_reference", 0.21)), # Utilise .get() et float() pour max_value
                    value=float(prix_min_revente_val), # Utilise la variable locale sûre et float()
                    step=0.01,
                    help="Prix minimum de revente à considérer dans l'optimisation"
                )

                # CORRECTION: Utilisation de .get(), float(), et min/max_value sécurisés
                st.session_state.config["prix_max_revente"] = st.number_input(
                    "Prix maximum de revente (€/kWh)",
                    min_value=float(config.get("prix_min_revente", 0.15)), # Utilise .get() et float() pour min_value
                    max_value=float(config.get("tarif_edf_reference", 0.21)), # Utilise .get() et float() pour max_value
                    value=float(config.get("prix_max_revente", 0.21)), # Utilise .get() et float() pour value
                    step=0.01,
                    help="Prix maximum de revente à considérer dans l'optimisation (généralement le tarif EDF)"
                )

            with col2:
                # CORRECTION: Utilisation de .get() et float()
                st.session_state.config["pas_optimisation"] = st.number_input(
                    "Pas d'optimisation (€/kWh)",
                    min_value=0.001,
                    max_value=0.05,
                    value=float(config.get("pas_optimisation", 0.01)), # Utilise .get() et float()
                    step=0.001,
                    help="Incrément entre chaque prix testé dans l'optimisation"
                )

                # CORRECTION: Utilisation de .get() (int, pas besoin de float ici)
                st.session_state.config["nb_iterations_monte_carlo"] = st.number_input(
                    "Nombre d'itérations Monte Carlo",
                    min_value=100,
                    max_value=10000,
                    value=config.get("nb_iterations_monte_carlo", 1000), # Utilise .get()
                    step=100,
                    help="Nombre d'itérations pour la simulation Monte Carlo"
                )

                col_a, col_b = st.columns(2)
                with col_a:
                    # CORRECTION: Utilisation de .get() et float()
                    st.session_state.config["ecart_type_production"] = st.number_input(
                        "Écart-type production (%)",
                        min_value=1.0,
                        max_value=30.0,
                        value=float(config.get("ecart_type_production", 10.0)), # Utilise .get() et float()
                        step=1.0,
                        help="Écart-type de la variabilité de production pour Monte Carlo"
                    )

                with col_b:
                    # CORRECTION: Utilisation de .get() et float()
                    st.session_state.config["ecart_type_consommation"] = st.number_input(
                        "Écart-type consommation (%)",
                        min_value=1.0,
                        max_value=30.0,
                        value=float(config.get("ecart_type_consommation", 5.0)), # Utilise .get() et float()
                        step=1.0,
                        help="Écart-type de la variabilité de consommation pour Monte Carlo"
                    )
        
        with tab2:
            st.markdown("<h3 class='sub-header'>Données du Projet (Général)</h3>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                # CORRECTION: Utilisation de .get() et float() (déjà corrigé)
                st.session_state.config["capex"] = st.number_input(
                    "CAPEX (€)",
                    max_value=20000000.0,
                    value=float(config.get("capex", 85000.0)), # Utilise .get() et float()
                    step=100000.0,
                    help="Coût d'investissement initial du projet"
                )
                
            with col2:
                # CORRECTION: Utilisation de .get() (int)
                st.session_state.config["duree_construction"] = st.number_input(
                    "Durée de construction (mois)",
                    max_value=24,
                    value=config.get("duree_construction", 12), # Utilise .get()
                    step=1,
                    help="Durée de la phase de construction avant mise en service"
                )
                
                # CORRECTION: Utilisation de .get() et float() pour la value avant * 100
                # Contrôle de la valeur pour éviter StreamlitValueAboveMaxError
                degradation_percent = min(float(config.get("degradation_rate", 0.005)) * 100, 2.0)
                st.session_state.config["degradation_rate"] = st.number_input(
                    "Taux de dégradation annuel des panneaux (%)",
                    min_value=0.1,
                    max_value=2.0,
                    value=degradation_percent, # Utilise la valeur contrôlée
                    step=0.1,
                    help="Taux de dégradation annuel des performances des panneaux PV en pourcentage"
                ) / 100  # Re-conversion en décimal pour stockage
            
            # Ajout du calculateur d'OPEX
            st.markdown("#### Calculateur d'OPEX")
        
            col1, col2 = st.columns(2)
            with col1:
                # CORRECTION: Utilisation de .get() et float()
                puissance_kwc = st.number_input(
                    "Puissance installée (kWc)",
                    min_value=1.0,
                    max_value=10000.0,
                    value=float(config.get("puissance_kwc", 500.0)), # Utilise .get() et float()
                    step=1.0,
                    help="Puissance crête de l'installation PV en kWc"
                )
                st.session_state.config["puissance_kwc"] = puissance_kwc
                
                # CORRECTION: Utilisation de .get() pour l'index
                opex_method = st.radio(
                    "Méthode de calcul OPEX",
                    options=["auto", "percent", "kwc", "custom"],
                    format_func=lambda x: {
                        "auto": "Automatique (recommandé)",
                        "percent": "% du CAPEX",
                        "kwc": "Coût par kWc",
                        "custom": "Personnalisé"
                    }[x],
                    index=["auto", "percent", "kwc", "custom"].index(config.get("opex_method", "auto")), # Utilise .get()
                    help="Méthode pour calculer l'OPEX annuel"
                )
                st.session_state.config["opex_method"] = opex_method

            with col2:
                capex = config.get("capex", 85000.0) # Utilise .get() pour le calcul
                
                if opex_method == "percent":
                    # CORRECTION: Utilisation de .get() et float() pour la valeur du slider
                    opex_percent = st.slider(
                        "OPEX en % du CAPEX",
                        min_value=0.5,
                        max_value=5.0,
                        value=float(config.get("opex_percent", 1.5)), # Utilise .get() et float()
                        step=0.1,
                        help="Pourcentage du CAPEX utilisé pour l'OPEX annuel"
                    )
                    st.session_state.config["opex_percent"] = opex_percent
                    calculated_opex = capex * (opex_percent / 100.0)
                    st.info(f"OPEX calculé : {calculated_opex:.2f} €/an ({opex_percent:.1f}% du CAPEX)")
                
                elif opex_method == "kwc":
                     # CORRECTION: Utilisation de .get() et float() pour la valeur du slider
                    opex_per_kwc = st.slider(
                        "OPEX en €/kWc/an",
                        min_value=5.0,
                        max_value=100.0,
                        value=float(config.get("opex_per_kwc", 20.0)), # Utilise .get() et float()
                        step=1.0,
                        help="Coût annuel de l'OPEX par kWc installé"
                    )
                    st.session_state.config["opex_per_kwc"] = opex_per_kwc
                    calculated_opex = puissance_kwc * opex_per_kwc
                    st.info(f"OPEX calculé : {calculated_opex:.2f} €/an ({opex_per_kwc:.1f} €/kWc/an)")
                
                elif opex_method == "auto":
                    opex_by_percent = capex * 0.015
                    opex_by_kwc = puissance_kwc * 20
                    calculated_opex = (opex_by_percent + opex_by_kwc) / 2
                    st.info(f"""OPEX calculé : {calculated_opex:.2f} €/an
                    - Basé sur CAPEX ({capex:,.2f} €) : {opex_by_percent:.2f} €/an (1.5%)
                    - Basé sur puissance ({puissance_kwc:.1f} kWc) : {opex_by_kwc:.2f} €/an (20 €/kWc)"""
                    )
                
                else:  # custom
                    # CORRECTION: Utiliser .get() pour lire la valeur existante avant l'input
                    calculated_opex = config.get("opex", 4500.0)
                    st.info(f"OPEX personnalisé : {calculated_opex:.2f} €/an")

            # Provision pour onduleurs
             # CORRECTION: Utilisation de .get() pour value
            opex_onduleur_provision = st.checkbox(
                "Inclure provision pour remplacement onduleurs",
                value=config.get("opex_onduleur_provision", True), # Utilise .get()
                help="Ajoute une provision annuelle pour le remplacement futur des onduleurs"
            )
            st.session_state.config["opex_onduleur_provision"] = opex_onduleur_provision

            if opex_onduleur_provision:
                col1, col2 = st.columns(2)
                with col1:
                     # CORRECTION: Utilisation de .get() et float()
                    opex_onduleur_cost = st.number_input(
                        "Coût onduleurs (€/kWc)",
                        min_value=50.0,
                        max_value=300.0,
                        value=float(config.get("opex_onduleur_cost", 130.0)), # Utilise .get() et float()
                        step=10.0,
                        help="Coût de remplacement des onduleurs en €/kWc"
                    )
                    st.session_state.config["opex_onduleur_cost"] = opex_onduleur_cost

                with col2:
                    # CORRECTION: Utilisation de .get() (int)
                    opex_onduleur_lifetime = st.number_input(
                        "Durée de vie onduleurs (années)",
                        min_value=8,
                        max_value=20,
                        value=config.get("opex_onduleur_lifetime", 14), # Utilise .get()
                        step=1,
                        help="Durée de vie estimée des onduleurs avant remplacement"
                    )
                    st.session_state.config["opex_onduleur_lifetime"] = opex_onduleur_lifetime

                # Assurer que lifetime n'est pas zéro pour éviter DivisionByZeroError
                safe_lifetime = opex_onduleur_lifetime if opex_onduleur_lifetime > 0 else 1
                onduleur_provision = (puissance_kwc * opex_onduleur_cost) / safe_lifetime
                st.info(f"Provision onduleurs : {onduleur_provision:.2f} €/an ({puissance_kwc:.1f} kWc × {opex_onduleur_cost:.1f} €/kWc ÷ {safe_lifetime} ans)")

                if opex_method != "custom":
                    total_opex = calculated_opex + onduleur_provision
                    st.success(f"OPEX total (avec provision) : {total_opex:.2f} €/an")
                    st.session_state.config["opex"] = total_opex
            else:
                # S'il n'y a pas de provision et que la méthode n'est pas custom, on utilise l'opex calculé sans provision
                if opex_method != "custom":
                    st.session_state.config["opex"] = calculated_opex


            # Pour le mode personnalisé, proposer un champ de saisie directe
            if opex_method == "custom":
                 # CORRECTION: Utilisation de .get() et float()
                opex_custom = st.number_input(
                    "OPEX annuel personnalisé (€/an)",
                    min_value=0.0,
                    max_value=100000.0,
                    value=float(config.get("opex", 4500.0)), # Utilise .get() et float()
                    step=100.0,
                    help="Montant personnalisé pour l'OPEX annuel"
                )
                # Si la provision est activée en mode custom, on l'ajoute à la valeur custom
                if opex_onduleur_provision:
                     st.session_state.config["opex"] = opex_custom + onduleur_provision
                     st.success(f"OPEX total (personnalisé + provision) : {st.session_state.config['opex']:.2f} €/an")
                else:
                     st.session_state.config["opex"] = opex_custom
        
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
                st.write(f"Taux d'intérêt SHL: {st.session_state.config.get('taux_interet_shl', 4.0)}%")
            st.write(f"Taux d'inflation: {st.session_state.config['taux_inflation']}%")
            st.write(f"Taux d'imposition: {st.session_state.config['taux_imposition']}%")
            
            # Paramètres du projet
            st.markdown("#### Paramètres du Projet")
            st.write(f"CAPEX: {st.session_state.config['capex']:,.2f} €")
            st.write(f"OPEX: {st.session_state.config['opex']:,.2f} €/an")
            
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
            st.write(f"Tarif EDF de référence: {st.session_state.config['tarif_edf_reference']} €/kWh")
            st.write(f"Prix min de revente: {st.session_state.config['prix_min_revente']} €/kWh")
            st.write(f"Prix max de revente: {st.session_state.config['prix_max_revente']} €/kWh")
            st.write(f"Pas d'optimisation: {st.session_state.config['pas_optimisation']} €/kWh")
            st.write(f"Nombre d'itérations Monte Carlo: {st.session_state.config['nb_iterations_monte_carlo']}")
            st.write(f"Écart-type production: {st.session_state.config['ecart_type_production']}%")
            st.write(f"Écart-type consommation: {st.session_state.config['ecart_type_consommation']}%")

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
        """Assure que toutes les valeurs par défaut sont présentes dans la configuration."""
        defaults = {
            # Paramètres économiques
            "taux_actualisation": 4.0,
            "taux_inflation": 2.0,
            "taux_augmentation_electricite": 3.5,
            "duree_etude": 25,
            "prix_min_revente": 0.15,
            "prix_max_revente": 0.21,
            "tarif_remuneration_surplus": 0.13,
            
            # Paramètres d'optimisation
            "pas_optimisation": 0.01,
            "nb_iterations_monte_carlo": 1000,
            "ecart_type_production": 10.0,
            "ecart_type_consommation": 5.0,
            
            # Paramètres du projet
            "capex": 85000.0,
            "puissance_installee": 100.0,
            "subvention": 0.0,
            "methode_opex": "pourcentage",
            "opex_pourcentage": 1.5,
            "opex_manuel": 1275.0,
            
            # Provisions pour onduleurs
            "inclure_provisions_onduleurs": True,
            "cout_onduleurs": 150.0,
            "duree_vie_onduleurs": 10,
            
            # Paramètres PVSOL
            "pvs_feed_in_tariff": 0.1108,
            "pvs_avoided_cost_tariff": 0.2218
        }
        
        for key, value in defaults.items():
            if key not in st.session_state.config:
                st.session_state.config[key] = value