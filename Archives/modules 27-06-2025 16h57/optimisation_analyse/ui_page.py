# modules/optimisation_analyse/ui_page.py (Extraits Modifiés)

import streamlit as st
import pandas as pd
import numpy as np
import time # Pour clés uniques
import traceback
# import datetime # Maintenu si utilisé ailleurs, sinon peut être enlevé si non requis

try:
    from modules.engine_module.core_analyzer import AnalysisEngine
    from modules.optimisation_analyse.logique_optimisation import OptimizationLogic
    from modules.optimisation_analyse.visualisation_prix import create_price_benefit_figure, create_autoconsommation_surplus_pie_chart
    
    # NOUVEAUX IMPORTS
    from ..table_finance.financial_display_utils import load_table_map
    from ..table_finance.annual_summary_display import display_project_summary, display_annual_detailed_summary
    from ..table_finance.monthly_cash_flow_display import display_cash_flow_statement_restructured

except ImportError as e:
    st.error(f"Erreur importation module dans ui_page.py : {e}")
    # Définitions factices pour permettre à l'UI de se charger partiellement
    def display_project_summary(*args, **kwargs): st.warning("Module display_project_summary non chargé.")
    def display_annual_detailed_summary(*args, **kwargs): st.warning("Module display_annual_detailed_summary non chargé.")
    def display_cash_flow_statement_restructured(*args, **kwargs): st.warning("Module display_cash_flow_statement_restructured non chargé.")
    def create_autoconsommation_surplus_pie_chart(*args, **kwargs): st.warning("Module pie chart non chargé."); return None
    def create_price_benefit_figure(*args, **kwargs): st.warning("Module graph prix/bénéfice non chargé."); return None
    # st.stop() # Peut être utile si les imports sont critiques

def display_analysis_optimisation_section(scenario_name: str):
    st.header(f"Analyse Détaillée et Optimisation : Scénario '{scenario_name}'")
    st.markdown("---")

    # --- Vérifications Préliminaires ---
    if 'config' not in st.session_state or 'scenarios' not in st.session_state or 'sites_data' not in st.session_state:
         st.error("Données ('sites_data') ou configuration manquantes pour l'analyse.")
         return

    # --- Instanciation Moteur d'Analyse et Stockage en Session ---
    try:
        # Créer/Mettre à jour l'instance dans st.session_state
        # pour qu'elle soit disponible pour la page de Visualisation
        st.session_state['analysis_engine_instance'] = AnalysisEngine(
            config=st.session_state.config,
            scenarios=st.session_state.scenarios,
            sites_data=st.session_state.sites_data
        )
    except Exception as e:
        st.error(f"Erreur lors de l'initialisation du moteur d'analyse : {e}")
        # Afficher la trace de l'erreur pour le débogage
        st.exception(traceback.format_exc())
        return

    # --- Initialisation Session State spécifique à la page ---
    if 'floor_price_results' not in st.session_state: st.session_state.floor_price_results = {}
    # Nouveaux états pour optimisation contrainte et MC
    if 'constrained_optim_results' not in st.session_state: st.session_state.constrained_optim_results = {}
    if 'monte_carlo_results' not in st.session_state: st.session_state.monte_carlo_results = {}
    curve_data_key = f"optim_curve_data_{scenario_name}"
    if curve_data_key not in st.session_state: st.session_state[curve_data_key] = None
    if 'thresholds_calculated' not in st.session_state: st.session_state.thresholds_calculated = {}
    if scenario_name not in st.session_state.thresholds_calculated: st.session_state.thresholds_calculated[scenario_name] = False

    # --- Instanciation Moteurs ---
    # SUPPRIMÉ : L'instanciation initiale n'est plus nécessaire car analysis_engine est déjà stocké
    # dans st.session_state['analysis_engine_instance']

    # Récupération du taux de TVA pour les revenus (doit être dans la config globale)
    # Assurez-vous que 'taux_tva_operations_pct' est bien la clé dans votre st.session_state.config
    taux_tva_revenus_pct = float(st.session_state.config.get('taux_tva_operations_pct', 20.0)) # Ex: 20.0 pour 20%
    taux_tva_revenus_decimal = taux_tva_revenus_pct / 100.0

    key_suffix = f"_{scenario_name}" # Pour clés uniques des widgets

    # --- Définition des Onglets --- 
    tab1, tab2 = st.tabs(["📊 Analyse & Visualisation", "📄 Rapports Financiers Détaillés"])

    with tab1:
        # --- TOUT LE CONTENU ACTUEL DES COLONNES GAUCHE ET DROITE IRA ICI ---

        # Layout à deux colonnes à l'intérieur du premier onglet
        left_col_tab1, right_col_tab1 = st.columns([1, 1]) # Ratio peut être ajusté

        with left_col_tab1:
            st.subheader("⚙️ Configuration & Résultats") # Titre pour la colonne

            # --- Étape 1: Calcul des Seuils --- 
            with st.container(border=True):
                st.markdown("**1. Calculer les Seuils Indispensables**")
                st.caption("Calcul du prix plancher (VAN=0) et du LCOE pour définir les bornes.")
                
                if st.button(f"Calculer Prix Plancher (VAN=0) & LCOE{key_suffix}", key=f"btn_floor{key_suffix}_tab1"):
                    with st.spinner("Calcul des seuils..."):
                        try:
                            # MODIFIÉ : Utiliser l'instance de session_state au lieu d'en créer une nouvelle
                            sites_cfg_local = st.session_state.get('sites_config', {})
                            # S'assurer que l'instance est à jour avant utilisation
                            st.session_state['analysis_engine_instance'] = AnalysisEngine(
                                config=st.session_state.config,
                                scenarios=st.session_state.scenarios,
                                sites_data=st.session_state.sites_data
                            )
                            floor_res = st.session_state['analysis_engine_instance'].simulate_selling_price(
                                scenario_name,
                                target_npv=0,
                                override_source_prix_autoconso="prix_initial",
                                sites_config=sites_cfg_local
                            )
                            if floor_res and isinstance(floor_res, dict):
                                 lcoe_val = floor_res.get('lcoe_associated') or floor_res.get('lcoe') # Tentatives
                                 floor_res['lcoe_for_ui'] = lcoe_val
                                 # On s'assure que la clé est bien 'edf_ref_for_ui_ttc' pour la sauvegarde
                                 edf_ref_ttc = st.session_state.config.get('tarif_edf_reference') 
                                 floor_res['edf_ref_for_ui_ttc'] = edf_ref_ttc # Utilisation de la clé standardisée et explicite
                            st.session_state.floor_price_results[scenario_name] = floor_res
                            st.session_state.thresholds_calculated[scenario_name] = True 
                        except Exception as e:
                            st.error(f"Erreur calcul seuils: {e}")
                            st.session_state.floor_price_results[scenario_name] = {'error': str(e)}
                            st.session_state.thresholds_calculated[scenario_name] = False
                    st.rerun()

                # Affichage des seuils...
                floor_data = st.session_state.floor_price_results.get(scenario_name)
                if isinstance(floor_data, dict) and 'error' not in floor_data and floor_data.get('prix_revente_optimal_pour_cible') is not None:
                     p_plancher_ht = floor_data.get('prix_revente_optimal_pour_cible')
                     lcoe_ht = floor_data.get('lcoe_for_ui') # Supposé HT (LCOE engineering)
                     edf_ref_ttc_ui = floor_data.get('edf_ref_for_ui_ttc') # Confirmé TTC par vous

                     col_s1, col_s2, col_s3 = st.columns(3)
                     with col_s1: 
                         st.metric("Prix Plancher Prod. (HT)", 
                                   f"{p_plancher_ht:.4f} €/kWh" if p_plancher_ht is not None else "N/A",
                                   help="Prix de vente HT qui annule la VAN Projet.")
                     with col_s2: 
                         st.metric("LCOE (HT)", 
                                   f"{lcoe_ht:.4f} €/kWh" if lcoe_ht is not None else "N/A",
                                   help="Coût actualisé de l'énergie (engineering), typiquement HT.")
                     with col_s3: 
                         st.metric("Tarif EDF Réf. (TTC)", 
                                   f"{edf_ref_ttc_ui:.4f} €/kWh" if edf_ref_ttc_ui is not None else "N/A",
                                   help="Tarif de comparaison client, toutes taxes comprises.")
                elif isinstance(floor_data, dict) and 'error' in floor_data:
                     st.error(f"Erreur lors du calcul des seuils: {floor_data['error']}")
                # else: st.caption("Cliquez pour calculer.") # Décommenter si vous voulez ce message par défaut

            # --- Étape 2: Définir Contraintes & Lancer Optimisation --- 
            with st.container(border=True):
                st.markdown("**2. Optimiser le Prix sous Contraintes**")
                
                if not st.session_state.thresholds_calculated.get(scenario_name, False):
                    st.warning("Veuillez d'abord calculer les seuils (étape 1).")
                else:
                    st.markdown("Définissez vos exigences minimales :")
                    current_config = st.session_state.config
                    
                    # Utilisation des clés de config pour les contraintes
                    default_min_irr = float(current_config.get('constraint_min_irr_pct', 8.0))
                    default_max_payback = float(current_config.get('constraint_max_payback', 18.0))
                    default_min_gain = float(current_config.get('constraint_min_consumer_gain_pct', 5.0))

                    col_c1, col_c2, col_c3 = st.columns(3)
                    with col_c1:
                        min_irr_input = st.number_input(
                            "TRI Projet Minimum (%)", min_value=0.0, max_value=50.0,
                            value=default_min_irr, step=0.5, format="%.1f",
                            key=f"constraint_project_irr{key_suffix}", 
                            help="Taux de Rentabilité Interne (TRI) minimum visé pour le **projet global (avant financement)**."
                        )
                        # Synchronisation immédiate avec la config (peut être redondant si lu au clic)
                        # st.session_state.config['constraint_min_irr_pct'] = min_irr_input
                    with col_c2:
                        max_payback_input = st.number_input(
                            "Payback Maximum (ans)", min_value=5.0, max_value=30.0,
                            value=default_max_payback, step=1.0, format="%.1f",
                            key=f"constraint_payback{key_suffix}", help="Durée maximale de retour sur investissement pour les fonds propres."
                        )
                        # st.session_state.config['constraint_max_payback'] = max_payback_input
                    with col_c3:
                        min_gain_input = st.slider(
                            "Gain Client Minimum (%)", min_value=0, max_value=50,
                            value=int(default_min_gain), step=1, format="%d%%",
                            key=f"constraint_gain{key_suffix}", help="Pourcentage minimum d'économie pour le client par rapport au tarif EDF."
                        )
                        # st.session_state.config['constraint_min_consumer_gain_pct'] = float(min_gain_input)

                    if st.button(f"Trouver le Prix Optimal (sous Contraintes){key_suffix}", key=f"btn_constrained_optim{key_suffix}_tab1"):
                        # --- Lire les valeurs des widgets AU MOMENT DU CLIC --- 
                        constraints_to_use = {
                            'min_irr_pct': st.session_state[f"constraint_project_irr{key_suffix}"],
                            'max_payback': st.session_state[f"constraint_payback{key_suffix}"],
                            'min_consumer_gain_pct': st.session_state[f"constraint_gain{key_suffix}"]
                        }
                        # --- Mettre à jour la config JUSTE AVANT --- 
                        st.session_state.config['constraint_min_irr_pct'] = float(constraints_to_use['min_irr_pct'])
                        st.session_state.config['constraint_max_payback'] = float(constraints_to_use['max_payback'])
                        st.session_state.config['constraint_min_consumer_gain_pct'] = float(constraints_to_use['min_consumer_gain_pct'])
                        st.info(f"Optimisation lancée avec: TRI Projet Min={constraints_to_use['min_irr_pct']}%, Payback Max={constraints_to_use['max_payback']} ans, Gain Client Min={constraints_to_use['min_consumer_gain_pct']}%" ) # Feedback UI

                        with st.spinner("Optimisation sous contraintes en cours..."):
                            try:
                                # MODIFIÉ : S'assurer que analysis_engine_instance est à jour avant d'instancier Optimizer
                                st.session_state['analysis_engine_instance'] = AnalysisEngine(
                                    config=st.session_state.config, 
                                    scenarios=st.session_state.scenarios,
                                    sites_data=st.session_state.sites_data
                                )
                                # Instancier Optimizer avec l'instance de session_state
                                optimizer = OptimizationLogic(
                                     config=st.session_state.config,
                                     analysis_engine=st.session_state['analysis_engine_instance']
                                )
                                # Récupérer sites_config
                                sites_cfg_local = st.session_state.get('sites_config', {})
                                # Passer les contraintes lues ET sites_config
                                optim_res = optimizer.find_optimal_price_constrained(
                                    scenario_name=scenario_name,
                                    tri_projet_min_pct_constraint=constraints_to_use['min_irr_pct'],
                                    sites_config=sites_cfg_local
                                )
                                if optim_res and isinstance(optim_res, dict): 
                                    st.session_state.constrained_optim_results[scenario_name] = optim_res
                                    if 'error' not in optim_res and 'prix_optimal_const' in optim_res:
                                        st.session_state['analyse_optimisation_terminee'] = True
                                else:
                                    st.error("Format de résultat d'optimisation inattendu.")
                                    st.session_state.constrained_optim_results[scenario_name] = {'error': 'Format inattendu.'}
                                # Supprimer les résultats MC si nouvelle optimisation
                                if scenario_name in st.session_state.monte_carlo_results: del st.session_state.monte_carlo_results[scenario_name]
                            except Exception as e:
                                st.error(f"Erreur lors de l'optimisation: {e}")
                                st.session_state.constrained_optim_results[scenario_name] = {'error': str(e)}
                        st.rerun()

            # --- Affichage des Résultats (KPIs & Monte Carlo) --- 
            optim_data = st.session_state.constrained_optim_results.get(scenario_name)
            prix_optimal_ht_trouve = None # MODIFIÉ: Renommé pour clarté et cohérence

            if isinstance(optim_data, dict):
                 # --- Section 1 : Indicateurs Clés --- 
                 st.markdown("---")
                 st.subheader("📈 Indicateurs Clés au Prix Optimal")
                 if 'error' in optim_data:
                     st.error(f"Erreur optimisation: {optim_data['error']}")
                     if 'details' in optim_data : st.error(f"Détails: {optim_data['details']}")
                 elif 'prix_optimal_const' in optim_data and optim_data['prix_optimal_const'] is not None:
                     prix_optimal_ht_trouve = optim_data['prix_optimal_const'] # MODIFIÉ: Renommé pour clarté et cohérence
                     # Calcul du prix TTC basé sur le prix HT optimal et le taux de TVA des revenus
                     prix_optimal_ttc_calc = prix_optimal_ht_trouve * (1 + taux_tva_revenus_decimal)

                     indic_at_optimal = optim_data.get('indicateurs_au_prix_optimal', {})
                     npv_eq = indic_at_optimal.get('npv')
                     irr_eq = indic_at_optimal.get('irr')
                     payback_eq = indic_at_optimal.get('payback_period')
                     npv_proj = indic_at_optimal.get('npv_project')
                     irr_proj = indic_at_optimal.get('irr_project')
                     payback_proj = indic_at_optimal.get('payback_project')
                     lcoe = indic_at_optimal.get('lcoe')
                     avg_dscr = indic_at_optimal.get('avg_dscr')
                     autoconsumption_rate = indic_at_optimal.get('autoconsumption_rate')
                     autoproduction_rate = indic_at_optimal.get('autoproduction_rate')

                     net_equity_investment_value = float(indic_at_optimal.get('net_equity_investment', 0.0))
                     EQUITY_DISPLAY_THRESHOLD = 1.0 
                     is_equity_display_negligible = abs(net_equity_investment_value) < EQUITY_DISPLAY_THRESHOLD

                     col_prix_opt1, col_prix_opt2 = st.columns(2)
                     with col_prix_opt1:
                         st.metric("Prix Optimal Recommandé (HT)",
                                   f"{prix_optimal_ht_trouve:.4f} €/kWh",
                                   help="Prix de vente HT optimisé sous contraintes.")
                     with col_prix_opt2:
                         st.metric("Prix Optimal Recommandé (TTC)",
                                   f"{prix_optimal_ttc_calc:.4f} €/kWh",
                                   help=f"Prix HT majoré de la TVA à {taux_tva_revenus_pct:.1f}%. C'est le prix payé par un client final non assujetti à la TVA.")

                     constraints_applied = optim_data.get('contraintes_appliquees', {})
                     # Tarif EDF de référence TTC utilisé pour la contrainte Gain Client
                     edf_ref_ttc_for_gain_calc = constraints_applied.get('tarif_edf_ref_ttc_config_utilise', 
                                                                      st.session_state.config.get('tarif_edf_reference', 0))
                     
                     # --- AJOUTEZ LE CALCUL DE gain_client_ttc_reel_pct ICI ---
                     gain_client_ttc_reel_pct = 0.0 # Initialisation par défaut
                     # S'assurer que edf_ref_ttc_for_gain_calc est un nombre avant la division
                     if isinstance(edf_ref_ttc_for_gain_calc, (int, float)) and edf_ref_ttc_for_gain_calc > 1e-6:
                         # S'assurer que prix_optimal_ttc_calc est un nombre
                         if isinstance(prix_optimal_ttc_calc, (int, float)):
                             gain_client_ttc_reel_pct = ((edf_ref_ttc_for_gain_calc - prix_optimal_ttc_calc) / edf_ref_ttc_for_gain_calc) * 100
                         else:
                             st.warning("prix_optimal_ttc_calc n'est pas numérique, calcul du gain client impossible.")
                     elif isinstance(edf_ref_ttc_for_gain_calc, (int, float)) and edf_ref_ttc_for_gain_calc <= 1e-6 :
                         st.warning("Tarif EDF de référence (edf_ref_ttc_for_gain_calc) est nul ou trop faible, calcul du gain client impossible.")
                     else:
                         st.warning("Tarif EDF de référence (edf_ref_ttc_for_gain_calc) n'est pas numérique, calcul du gain client impossible.")
                     # --- FIN DE L'AJOUT ---

                     min_proj_irr_target_disp = constraints_applied.get('min_irr_projet_pct_cible', 'N/A')
                     gain_client_cible_ttc_disp = constraints_applied.get('min_consumer_gain_pct_cible_ttc', 'N/A')
                     payback_equity_cible_disp = constraints_applied.get('max_payback_equity_annees_cible', 'N/A')

                     st.caption(f"Contraintes visées lors de l'optimisation: "
                                f"TRI Projet ≥ {min_proj_irr_target_disp}% ; "
                                f"Payback Equity ≤ {payback_equity_cible_disp} ans ; "
                                f"Gain Client (vs EDF TTC) ≥ {gain_client_cible_ttc_disp}%")
                     
                     # Détection du financement 100% dette pour masquer la section fonds propres
                     debt_ratio = float(st.session_state.config.get('debt_ratio', 0.8))
                     is_full_debt_financing = debt_ratio >= 0.99  # 99% pour gérer les arrondis
                     
                     if not is_full_debt_financing:
                         st.markdown("<h6>Indicateurs Fonds Propres :</h6>", unsafe_allow_html=True)
                         col_eq1, col_eq2, col_eq3 = st.columns(3)
                         with col_eq1:
                             van_fp_help_text = "Valeur Actuelle Nette des flux de trésorerie disponibles pour les actionnaires."
                             if is_equity_display_negligible:
                                 van_fp_help_text += " Représente le surplus de valeur généré sans apport significatif en fonds propres."
                             st.metric("VAN Fonds Propres (€)", 
                                       f"{npv_eq:,.0f}" if pd.notna(npv_eq) else "N/A", 
                                       help=van_fp_help_text)
                         with col_eq2:
                             if is_equity_display_negligible:
                                 st.metric("TRI Fonds Propres (%)", 
                                           "N/A (FP nuls/négligeables)", 
                                           help="Non applicable ou infini car l'investissement initial en fonds propres est nul ou négligeable.")
                             else:
                                 # Récupération de l'avertissement TRI depuis les résultats
                                 irr_equity_warning = indic_at_optimal.get('irr_equity_warning')
                                 
                                 if irr_equity_warning:
                                     # Cas d'avertissement TRI
                                     st.metric("TRI Fonds Propres (%)", 
                                               "N/A*",
                                               help=f"{irr_equity_warning}. La VAN reste l'indicateur le plus fiable dans ce cas.")
                                 elif pd.isna(irr_eq) or not np.isfinite(irr_eq):
                                     st.metric("TRI Fonds Propres (%)", 
                                               "Calcul impossible",
                                               help="Taux de Rentabilité Interne non calculable - flux de trésorerie atypiques.")
                                 elif irr_eq < -0.5:  # Si TRI < -50%
                                     st.metric("TRI Fonds Propres (%)", 
                                               "< -50%*",
                                               help="TRI très négatif : structure de financement atypique avec prime élevée. La VAN reste l'indicateur le plus fiable.")
                                 else:
                                     st.metric("TRI Fonds Propres (%)", 
                                               f"{irr_eq*100:.1f}%",
                                               help="Taux de Rentabilité Interne sur les fonds propres investis.")

                         with col_eq3:
                             payback_equity_cible_disp = constraints_applied.get('max_payback_equity_annees_cible', 'N/A') 

                             if is_equity_display_negligible:
                                 st.metric("Payback Fonds Propres (ans)", 
                                           "N/A (FP nuls/négligeables)", 
                                           help="Non applicable car l'investissement initial en fonds propres est nul ou négligeable.")
                             else:
                                 payback_display_value = "N/A"
                                 delta_text_payback = None
                                 if pd.notna(payback_eq) and np.isfinite(payback_eq):
                                     if payback_eq == 0.0:
                                         payback_display_value = "Immédiat (<1 an)"
                                     else:
                                         payback_display_value = f"{payback_eq:.1f}"
                                     
                                     if isinstance(payback_equity_cible_disp, (int, float)) and pd.notna(payback_equity_cible_disp):
                                         delta_text_payback = f"{(payback_eq - payback_equity_cible_disp):.1f} vs cible"
                                 elif pd.notna(payback_eq): 
                                      payback_display_value = "Jamais récupéré"

                                 st.metric("Payback Fonds Propres (ans)", 
                                           payback_display_value,
                                           delta=delta_text_payback if payback_display_value not in ["N/A", "Jamais récupéré"] else None,
                                           delta_color="inverse", 
                                           help="Temps pour récupérer l'investissement initial en fonds propres.")
                     else:
                         # Message informatif pour financement 100% dette
                         st.info("💡 **Financement 100% dette** : Les indicateurs Fonds Propres ne s'appliquent pas car aucun apport en capital n'est requis.")

                     # Note explicative pour faible apport de fonds propres (seulement si pas 100% dette)
                     if not is_full_debt_financing:
                         net_equity_investment = indic_at_optimal.get('net_equity_investment', 0)
                         capex_total = indic_at_optimal.get('capex_scenario_final_utilise', 0)
                         subvention_montant = indic_at_optimal.get('total_subvention', 0)
                         
                         if net_equity_investment and capex_total and net_equity_investment < capex_total * 0.15:  # Si FP < 15% du CAPEX
                             st.info(
                                 f"**Note :** Avec un apport en fonds propres net de {net_equity_investment:,.0f}€ "
                                 f"(après déduction de la prime de {subvention_montant:,.0f}€), certains indicateurs "
                                 f"comme le TRI peuvent être mathématiquement instables. "
                                 f"La VAN reste l'indicateur le plus fiable dans ce cas."
                             )

                     # Diagnostic détaillé du TRI Fonds Propres (seulement si pas 100% dette)
                     if not is_full_debt_financing:
                         equity_details = indic_at_optimal.get('equity_calculation_details', {})
                         fcfe_details = indic_at_optimal.get('fcfe_calculation_details', [])
                         irr_method = indic_at_optimal.get('irr_calculation_method', 'Standard')
                         coherence_errors = indic_at_optimal.get('equity_coherence_errors', [])
                         
                         # Si des erreurs de cohérence sont détectées
                         if coherence_errors:
                             st.error("⚠️ **Incohérences détectées dans les calculs Fonds Propres**")
                             for error in coherence_errors:
                                 st.write(f"• {error}")
                             
                             # Proposer de voir le détail
                             if st.button("🔍 Voir le détail des calculs"):
                                 try:
                                     import json
                                     with open('debug_equity_calculations.json', 'r') as f:
                                         debug_data = json.load(f)
                                     st.json(debug_data)
                                 except:
                                     st.error("Fichier de debug non trouvé")
                         
                         if equity_details or fcfe_details:
                             with st.expander("📊 Analyse détaillée du TRI Fonds Propres"):
                                 # Afficher le calcul de l'investissement
                                 if equity_details:
                                     st.markdown("**Calcul de l'investissement net en fonds propres :**")
                                     col1, col2, col3 = st.columns(3)
                                     with col1:
                                         st.metric("CAPEX Total", f"{equity_details.get('capex_total', 0):,.0f} €")
                                         st.metric("- Dette", f"{equity_details.get('debt_amount', 0):,.0f} €")
                                     with col2:
                                         st.metric("= FP Bruts", f"{equity_details.get('gross_equity', 0):,.0f} €")
                                         st.metric("- Subvention", f"{equity_details.get('subvention', 0):,.0f} €")
                                     with col3:
                                         st.metric("= FP Nets", f"{equity_details.get('net_equity_investment', 0):,.0f} €")
                                         st.caption(f"*Méthode : {equity_details.get('method', 'Standard')}*")
                                 
                                 # Alerte si flux exceptionnels détectés
                                 exceptional_months = [d for d in fcfe_details if d.get('exceptional_vat', 0) > 0 or d.get('prime_excluded', 0) > 0]
                                 if exceptional_months:
                                     st.warning(
                                         f"⚠️ {len(exceptional_months)} mois avec flux exceptionnels détectés et isolés du calcul TRI."
                                     )
                                     
                                     # Détail des flux exceptionnels
                                     total_exceptional_vat = sum(d.get('exceptional_vat', 0) for d in exceptional_months)
                                     total_prime_excluded = sum(d.get('prime_excluded', 0) for d in exceptional_months)
                                     
                                     if total_exceptional_vat > 0:
                                         st.info(f"💰 TVA exceptionnelle isolée : {total_exceptional_vat:,.0f} €")
                                     if total_prime_excluded > 0:
                                         st.info(f"🎁 Prime autoconso retirée des flux : {total_prime_excluded:,.0f} €")
                                 
                                 # Afficher la méthode de calcul utilisée
                                 if irr_method == 'MIRR':
                                     st.info(
                                         "ℹ️ **TRI Modifié (MIRR) utilisé** car les flux de trésorerie "
                                         "présentent une structure atypique. Le MIRR est plus représentatif "
                                         "de la rentabilité réelle dans ce cas."
                                     )
                                 elif irr_method == 'IRR':
                                     st.success("✅ **TRI Standard** utilisé avec succès.")
                                 elif irr_method in ['N/A', 'ERROR']:
                                     st.error(f"❌ Calcul TRI impossible : {irr_method}")

                     st.markdown("<h6>Indicateurs Projet Global :</h6>", unsafe_allow_html=True)
                     col_proj1, col_proj2, col_proj_res3 = st.columns(3) # Ajout d'une colonne pour le gain client
                     with col_proj1:
                         st.metric("TRI Projet (%)", f"{irr_proj*100:.1f}%" if irr_proj is not None else "N/A",
                                    delta=f"{(irr_proj*100 - min_proj_irr_target_disp):.1f}% vs cible" if irr_proj is not None and min_proj_irr_target_disp != 'N/A' else None,
                                    delta_color="normal",
                                    help="Taux de Rentabilité Interne du projet basé sur l'investissement total et les flux opérationnels après IS.")
                     with col_proj2:
                         st.metric("Payback Projet (ans)", f"{payback_proj:.1f}" if payback_proj is not None else "N/A",
                                    help="Temps pour récupérer l'investissement total (CAPEX net) par les flux opérationnels après IS.")
                     with col_proj_res3: # Affichage du Gain Client TTC Réel
                         # La variable gain_client_ttc_reel_pct est maintenant définie
                         delta_gain_client_val = 0.0 # Valeur par défaut pour le calcul du delta
                         if gain_client_cible_ttc_disp != 'N/A':
                             try:
                                 # S'assurer que gain_client_cible_ttc_disp peut être converti en float
                                 delta_gain_client_val = gain_client_ttc_reel_pct - float(gain_client_cible_ttc_disp)
                             except ValueError:
                                 st.warning(f"gain_client_cible_ttc_disp ('{gain_client_cible_ttc_disp}') n'est pas un nombre valide pour le calcul du delta.")
                                 # delta_gain_client_val reste à 0.0, ou vous pouvez choisir de mettre delta_text à None

                         delta_text_gain_client = f"{delta_gain_client_val:.1f}% vs cible" if gain_client_cible_ttc_disp != 'N/A' else None

                         st.metric("Gain Client Réel (vs EDF TTC)", f"{gain_client_ttc_reel_pct:.1f}%",
                                   delta=delta_text_gain_client, 
                                   delta_color="normal",
                                   help="Gain effectif pour le client final comparant le prix de vente TTC au tarif EDF TTC de référence.")
                 else:
                      st.info("Optimisation effectuée mais prix non trouvé ou erreur.")

                 # --- Section 2 : Monte Carlo --- 
                 if prix_optimal_ht_trouve is not None:
                     st.markdown("---")
                     st.subheader("🎲 Évaluation de la Robustesse (Monte Carlo)")
                     with st.container(border=True):
                          st.caption("Lancez une simulation Monte Carlo pour évaluer l'impact des aléas au prix optimal.")
                          
                          # Nouveau: Contrôle du nombre d'itérations
                          col_mc1, col_mc2 = st.columns([1, 2])
                          with col_mc1:
                              n_iterations_mc_ui = st.slider(
                                  "Nombre d'itérations:", 
                                  min_value=50, 
                                  max_value=1000, 
                                  value=int(st.session_state.config.get('nb_iterations_monte_carlo', 200)),
                                  step=50,
                                  key=f"mc_iterations_slider_{scenario_name}"
                              )
                          with col_mc2:
                              st.caption("⚠️ **Note**: Un nombre élevé d'itérations améliore la précision mais augmente considérablement le temps de calcul.")
                              
                          if st.button(f"Lancer Simulation Monte Carlo{key_suffix}", key=f"btn_mc{key_suffix}_tab1"):
                                with st.spinner("Simulation Monte Carlo..."):
                                    try:
                                        # MODIFIÉ : S'assurer que analysis_engine_instance est à jour
                                        st.session_state['analysis_engine_instance'] = AnalysisEngine(
                                            config=st.session_state.config,
                                            scenarios=st.session_state.scenarios,
                                            sites_data=st.session_state.sites_data
                                        )
                                        
                                        # Utiliser le nombre d'itérations choisi par l'utilisateur
                                        config_mc_custom = st.session_state.config.copy()
                                        config_mc_custom['nb_iterations_monte_carlo'] = n_iterations_mc_ui
                                        
                                        # Instancier Optimizer avec l'instance de session_state et la config modifiée
                                        optimizer = OptimizationLogic(
                                            config=config_mc_custom,
                                            analysis_engine=st.session_state['analysis_engine_instance']
                                        )
                                        # Récupérer sites_config
                                        sites_cfg_local = st.session_state.get('sites_config', {})
                                        mc_res = optimizer.run_monte_carlo_simulation(
                                            scenario_name,
                                            prix_revente=prix_optimal_ht_trouve,
                                            sites_config=sites_cfg_local
                                        )
                                        st.session_state.monte_carlo_results[scenario_name] = mc_res
                                    except Exception as e_mc:
                                        st.error(f"Erreur Monte Carlo: {e_mc}")
                                        st.session_state.monte_carlo_results[scenario_name] = {'error': str(e_mc)}
                                st.rerun()
                          # Affichage résultats MC
                          mc_data = st.session_state.monte_carlo_results.get(scenario_name)
                          if isinstance(mc_data, dict):
                             if 'error' in mc_data: st.error(f"Erreur Monte Carlo: {mc_data['error']}")
                             elif 'probabilities' in mc_data and 'statistics' in mc_data: # S'assurer que statistics est aussi là
                                 st.markdown("**Probabilités de succès (Monte Carlo) :**")
                                 probs = mc_data['probabilities'] 
                                 stats_mc = mc_data['statistics']
                                 # MODIFIÉ : Utiliser la bonne clé et .get() avec un fallback
                                 cons_mc = mc_data.get('contraintes_mc_cibles_appliquees', mc_data.get('contraintes_mc', {}))
                                 
                                 prob_dscr = probs.get('avg_dscr', 0)*100
                                 prob_payback = probs.get('payback_period', 0)*100
                                 prob_global = probs.get('global', 0)*100
                                 
                                 col_p1, col_p2, col_p3 = st.columns(3)
                                 
                                 # MODIFIÉ : Utiliser les bonnes sous-clés pour les contraintes
                                 dscr_cible_val = cons_mc.get('dscr_moyen_min', 'N/A')
                                 payback_cible_val = cons_mc.get('payback_max_equity_annees', 'N/A')

                                 with col_p1: st.metric(f"P(DSCR ≥ {dscr_cible_val})", f"{prob_dscr:.1f}%")
                                 with col_p2: st.metric(f"P(Payback Equity ≤ {payback_cible_val} ans)", f"{prob_payback:.1f}%")
                                 with col_p3: st.metric("P(Succès Global)", f"{prob_global:.1f}%")

                                 with st.expander("Voir statistiques détaillées"):
                                    for k, v in stats_mc.items():
                                         mean_val=v.get('mean',np.nan); std_val=v.get('std',np.nan); median_val=v.get('p',[np.nan]*5)[2]
                                         mean_str=f"{mean_val:.2f}" if pd.notna(mean_val) else "N/A"; std_str=f"{std_val:.2f}" if pd.notna(std_val) else "N/A"; median_str=f"{median_val:.2f}" if pd.notna(median_val) else "N/A"
                                         st.write(f"**{k.upper()}**: Moyenne={mean_str}, Ecart-type={std_str}, Médiane={median_str}")
                             else: st.info("Résultats Monte Carlo non disponibles.")
                 else:
                      st.info("Lancez l'optimisation et obtenez un prix optimal valide pour exécuter Monte Carlo.")
            else:
                 st.info("Résultats de l'optimisation non disponibles. Lancez l'optimisation (Étape 2 ci-dessus).")
            # --- Fin Affichage Résultats Séquentiels ---

        # --- Fin Colonne Gauche Onglet 1 ---

        with right_col_tab1:
            st.subheader("📊 Visualisations Interactives")

            st.markdown("**Analyse de la courbe Prix de Vente HT / Bénéfice Client Annuel (vs EDF TTC)**")
            
            floor_data_viz = st.session_state.floor_price_results.get(scenario_name, {})
            lcoe_ht_viz = floor_data_viz.get('lcoe_for_ui') 
            prix_edf_ref_ttc_viz = floor_data_viz.get('edf_ref_for_ui_ttc', st.session_state.config.get('tarif_edf_reference', 0.21))

            if st.button(f"Afficher/Actualiser le Graphique Prix/Bénéfice{key_suffix}", key=f"btn_show_graph_constrained{key_suffix}_tab1"):
                if not st.session_state.thresholds_calculated.get(scenario_name, False) or lcoe_ht_viz is None:
                    st.warning("Veuillez d'abord calculer les seuils (Prix Plancher HT & LCOE HT) dans la colonne de gauche.")
                else:
                    with st.spinner("Génération des données du graphique..."):
                        try:
                            # Borne inférieure pour l'axe X du graphe (prix HT)
                            prix_min_graph_ht = lcoe_ht_viz * 0.8 
                            # Borne supérieure HT : ne doit pas dépasser le prix qui annulerait le gain client TTC.
                            # (Tarif EDF TTC * (1 - 0% gain)) / (1+TVA) = Tarif EDF HT équivalent
                            # Ou plus simplement, le tarif EDF TTC lui-même comme une sorte de "limite psychologique" pour le prix HT
                            # ou utiliser prix_max_ht_selon_gain_client calculé dans logique_optimisation.
                            # Pour le graphique, on peut prendre une plage autour du LCOE et du prix optimal.
                            optim_data_viz = st.session_state.constrained_optim_results.get(scenario_name, {})
                            prix_optimal_ht_viz_graph = optim_data_viz.get('prix_optimal_const')
                            
                            if prix_optimal_ht_viz_graph:
                                prix_max_graph_ht = max(prix_optimal_ht_viz_graph * 1.2, prix_edf_ref_ttc_viz / (1+taux_tva_revenus_decimal) * 1.1)
                                prix_min_graph_ht = min(lcoe_ht_viz * 0.9, prix_optimal_ht_viz_graph * 0.8)
                            else: # Fallback si pas de prix optimal
                                prix_max_graph_ht = prix_edf_ref_ttc_viz # Limite indicative
                            
                            prix_max_graph_ht = max(prix_max_graph_ht, prix_min_graph_ht + 0.02) # Assurer un intervalle minimal

                            num_points_graph = 100
                            prix_ht_a_tester_graph = np.linspace(prix_min_graph_ht, prix_max_graph_ht, num_points_graph)
                            
                            # Récupérer l'autoconso annuelle (devrait venir des résultats d'un calcul AnalysisEngine)
                            # Idéalement, on la prend des 'indicateurs_au_prix_optimal' du run d'optimisation
                            # ou du run de calcul des seuils.
                            param_autoconso_annuel_graph = 0
                            indic_for_graph = optim_data_viz.get('indicateurs_au_prix_optimal') if optim_data_viz else floor_data_viz
                            if indic_for_graph and indic_for_graph.get('monthly_data') is not None:
                                df_monthly_graph = indic_for_graph['monthly_data']
                                if 'Autoconsommation_kWh' in df_monthly_graph:
                                     # Prendre la moyenne sur les années si plusieurs, ou la somme de la première année
                                     unique_years_graph = df_monthly_graph['Sim_Year_Operational'].unique()
                                     if len(unique_years_graph) > 0:
                                         param_autoconso_annuel_graph = df_monthly_graph.groupby('Sim_Year_Operational')['Autoconsommation_kWh'].sum().mean()
                                     else: # Fallback si pas d'années
                                         param_autoconso_annuel_graph = df_monthly_graph['Autoconsommation_kWh'].sum()


                            if param_autoconso_annuel_graph == 0 and 'sites_data' in st.session_state and st.session_state.sites_data:
                                 # Fallback très simplifié si non trouvé dans les résultats
                                 try: # Tentative de ré-agrégation rapide (moins précis)
                                     # MODIFIÉ : Utiliser l'instance stockée dans session_state plutôt que d'en créer une nouvelle
                                     if 'analysis_engine_instance' in st.session_state:
                                         temp_engine_graph = st.session_state['analysis_engine_instance']
                                     else:
                                         temp_engine_graph = AnalysisEngine(st.session_state.config, st.session_state.scenarios, st.session_state.sites_data)
                                     # Utiliser les données agrégées par le moteur si possible
                                     # Pour l'instant, on ne peut pas facilement obtenir l'autoconso annuelle sans un run complet.
                                     # On va la laisser à 0 si non trouvée dans les résultats, avec un message d'alerte.
                                     if hasattr(temp_engine_graph, 'hourly_data_to_return'): # Si analysis_engine a cette variable (nécessite un run)
                                         # Ce calcul est une approximation, il faudrait les résultats d'un vrai run
                                         df_agg_graph = temp_engine_graph.hourly_data_to_return 
                                         if not df_agg_graph.empty:
                                             df_agg_graph['year'] = pd.to_datetime(df_agg_graph['Temps']).dt.year
                                             ref_year_graph = df_agg_graph['year'].min()
                                             ref_data_graph = df_agg_graph[df_agg_graph['year'] == ref_year_graph]
                                             param_autoconso_annuel_graph = np.sum(np.minimum(ref_data_graph['production_kwh'], ref_data_graph['consumption_kwh']))

                                 except Exception as e_agg_graph:
                                     st.warning(f"Erreur estimation autoconso pour graphique: {e_agg_graph}.")
                            
                            if param_autoconso_annuel_graph < 1e-3 : # Si toujours nul ou quasi-nul
                                st.warning("Volume d'autoconsommation annuel de référence non trouvé ou nul. Le graphique de bénéfice client pourrait être plat ou incorrect.")
                                param_autoconso_annuel_graph = 0 # S'assurer que c'est bien 0 pour éviter erreurs

                            data_curve_list = []
                            for p_vente_ht_iter in prix_ht_a_tester_graph:
                                p_vente_ttc_iter = p_vente_ht_iter * (1 + taux_tva_revenus_decimal)
                                # Bénéfice client calculé TTC vs TTC
                                benefice_client_annuel_ttc = param_autoconso_annuel_graph * (prix_edf_ref_ttc_viz - p_vente_ttc_iter)
                                # Pourcentage d'économie TTC vs TTC
                                pct_economie_ttc = ((prix_edf_ref_ttc_viz - p_vente_ttc_iter) / prix_edf_ref_ttc_viz) * 100 if prix_edf_ref_ttc_viz > 1e-6 else 0
                                data_curve_list.append({
                                    'PrixVenteHT': p_vente_ht_iter, 
                                    'BeneficeClient': benefice_client_annuel_ttc, 
                                    'PctEconomie': pct_economie_ttc 
                                })
                            
                            st.session_state[curve_data_key] = pd.DataFrame(data_curve_list).sort_values(by='PrixVenteHT') if data_curve_list else None
                        except Exception as e_graph_gen:
                            st.error(f"Erreur génération données graphique: {e_graph_gen}"); traceback.print_exc()
                            st.session_state[curve_data_key] = None
                    st.rerun()

            df_curve_viz = st.session_state.get(curve_data_key)
            if df_curve_viz is not None and not df_curve_viz.empty:
                try:
                    cout_prod_ht_for_viz = lcoe_ht_viz if lcoe_ht_viz is not None else df_curve_viz['PrixVenteHT'].min()
                    optim_results_for_viz_graph = st.session_state.constrained_optim_results.get(scenario_name, {})
                    prix_optimal_ht_for_viz = optim_results_for_viz_graph.get('prix_optimal_const')
                    
                    slider_min_ht_viz = float(df_curve_viz['PrixVenteHT'].min())
                    slider_max_ht_viz = float(df_curve_viz['PrixVenteHT'].max())
                    # S'assurer que default_slider_val_ht_viz est dans les bornes du slider
                    default_slider_val_ht_viz = prix_optimal_ht_for_viz if (prix_optimal_ht_for_viz is not None and slider_min_ht_viz <= prix_optimal_ht_for_viz <= slider_max_ht_viz) else np.clip((slider_min_ht_viz + slider_max_ht_viz) / 2.0, slider_min_ht_viz, slider_max_ht_viz)
                    
                    selected_price_ht_explore_viz = st.slider(
                        "Explorer un Prix de Vente (HT) (€/kWh):", 
                        min_value=slider_min_ht_viz, max_value=slider_max_ht_viz,
                        value=float(default_slider_val_ht_viz), 
                        step=max(1e-5, (slider_max_ht_viz - slider_min_ht_viz)/200.0), 
                        format="%.4f €/kWh", key=f"ui_viz_slider_constrained_{scenario_name}"
                    )
                    
                    figure_prix_benef = create_price_benefit_figure(
                        df_data=df_curve_viz, 
                        cout_prod_ht=cout_prod_ht_for_viz, 
                        prix_edf_ref_ttc=prix_edf_ref_ttc_viz, 
                        selected_price_ht=selected_price_ht_explore_viz, 
                        optimal_price_ht=prix_optimal_ht_for_viz,
                        taux_tva=taux_tva_revenus_decimal 
                    )
                    if figure_prix_benef: st.plotly_chart(figure_prix_benef, use_container_width=True)
                    
                    selected_price_ttc_explore_viz = selected_price_ht_explore_viz * (1 + taux_tva_revenus_decimal)
                    
                    # Récupérer l'autoconso annuelle utilisée pour le graphique
                    # Pour la cohérence de l'affichage sous le graphe.
                    # Le calcul est fait dans le bloc "Afficher/Actualiser", on le réutilise ou on le stocke en session.
                    # Ici, on prend la valeur calculée lors de la génération du df_curve_viz
                    autoconso_annuelle_pour_details = 0
                    if 'param_autoconso_annuel_graph' in locals() and param_autoconso_annuel_graph > 0:
                        autoconso_annuelle_pour_details = param_autoconso_annuel_graph
                    elif df_curve_viz is not None and not df_curve_viz.empty and 'BeneficeClient' in df_curve_viz.columns and prix_edf_ref_ttc_viz > 1e-6:
                        # Tentative de rétro-calculer l'autoconso à partir du premier point du graphe (approximation)
                        # Benefice = Autoconso * (PrixEDF_TTC - PrixVente_TTC)
                        # Autoconso = Benefice / (PrixEDF_TTC - PrixVente_TTC)
                        first_p_vente_ht = df_curve_viz['PrixVenteHT'].iloc[0]
                        first_p_vente_ttc = first_p_vente_ht * (1 + taux_tva_revenus_decimal)
                        first_benefice = df_curve_viz['BeneficeClient'].iloc[0]
                        if abs(prix_edf_ref_ttc_viz - first_p_vente_ttc) > 1e-6:
                            autoconso_annuelle_pour_details = first_benefice / (prix_edf_ref_ttc_viz - first_p_vente_ttc)

                    final_benefice_ttc_details = autoconso_annuelle_pour_details * (prix_edf_ref_ttc_viz - selected_price_ttc_explore_viz)
                    final_pct_eco_ttc_details = ((prix_edf_ref_ttc_viz - selected_price_ttc_explore_viz) / prix_edf_ref_ttc_viz) * 100 if prix_edf_ref_ttc_viz > 1e-6 else 0
                    
                    st.markdown(f"**Pour un prix de vente de `{selected_price_ht_explore_viz:.4f} €/kWh HT` (soit `{selected_price_ttc_explore_viz:.4f} €/kWh TTC`) :**")
                    details_col1, details_col2 = st.columns(2)
                    with details_col1: st.metric("Bénéfice Client Annuel (vs EDF TTC)", f"{final_benefice_ttc_details:,.0f} €")
                    with details_col2: st.metric("Économie Client (vs EDF TTC)", f"{final_pct_eco_ttc_details:.1f}%")

                except Exception as e_visualisation:
                    st.error(f"Erreur lors de l'affichage de la visualisation: {e_visualisation}"); traceback.print_exc()

            # --- Graphe Camembert Autoconso/Surplus --- 
            st.markdown("---")
            st.markdown("**Répartition Annuelle Moyenne Énergie Produite**")
            results_dict_pie = st.session_state.constrained_optim_results.get(scenario_name, {}).get('indicateurs_au_prix_optimal', {})
            if results_dict_pie:
                total_auto=0.0; total_surp=0.0; total_prod=0.0
                monthly_df_pie = results_dict_pie.get('monthly_data')
                if isinstance(monthly_df_pie, pd.DataFrame) and not monthly_df_pie.empty:
                    if 'Autoconsommation_kWh' in monthly_df_pie.columns: total_auto = monthly_df_pie['Autoconsommation_kWh'].sum()
                    if 'Surplus_kWh' in monthly_df_pie.columns: total_surp = monthly_df_pie['Surplus_kWh'].sum()
                    total_prod = total_auto + total_surp
                    if total_prod < 1e-6 and 'Production_kWh' in monthly_df_pie.columns: # Fallback si les deux sont nuls
                         total_prod = monthly_df_pie['Production_kWh'].sum()
                
                if total_prod > 1e-6:
                    pie_fig = create_autoconsommation_surplus_pie_chart(total_auto, total_surp)
                    if pie_fig: st.plotly_chart(pie_fig, use_container_width=True)
                else: st.caption("Production nulle ou non calculée.")
            else:
                 st.caption("Lancez l'optimisation pour voir la répartition.")
            # --- Fin Graphe Camembert --- 

        # --- Fin Colonne Droite Onglet 1 ---

    # --- Fin Onglet 1 ---

    with tab2: # Onglet "Synthèse Financière Détaillée"
        st.subheader("📄 Rapports Financiers Détaillés") # Ou un titre similaire

        # Récupérer les résultats financiers pour les rapports
        # (Cette logique de récupération des résultats semble correcte d'après votre code précédent)
        optim_data_tab2 = st.session_state.constrained_optim_results.get(scenario_name)
        financial_results_dict_for_reports = None

        if isinstance(optim_data_tab2, dict) and \
           'indicateurs_au_prix_optimal' in optim_data_tab2 and \
           isinstance(optim_data_tab2['indicateurs_au_prix_optimal'], dict) and \
           "error" not in optim_data_tab2['indicateurs_au_prix_optimal']:
            financial_results_dict_for_reports = optim_data_tab2.get('indicateurs_au_prix_optimal')
        elif isinstance(optim_data_tab2, dict) and 'error' in optim_data_tab2: # Erreur de l'optimisation elle-même
            st.error(f"Erreur dans les résultats d'optimisation : {optim_data_tab2['error']}")
        elif isinstance(st.session_state.floor_price_results.get(scenario_name), dict) and \
             st.session_state.floor_price_results[scenario_name].get('indicateurs_au_prix_optimal') is not None and \
             "error" not in st.session_state.floor_price_results[scenario_name]:
            st.info("Affichage des indicateurs au prix plancher (VAN Projet=0) car l'optimisation sous contraintes n'a pas été lancée ou a échoué.")
            financial_results_dict_for_reports = st.session_state.floor_price_results[scenario_name].get('indicateurs_au_prix_optimal')
        
        if financial_results_dict_for_reports:
            # Afficher le récapitulatif global du projet en premier
            # display_project_summary vient de annual_summary_display.py
            display_project_summary(financial_results_dict_for_reports) 
            st.markdown("---")

            # Créer des sous-onglets ou des sections pour la synthèse annuelle et les flux mensuels
            sub_tab_annual_report, sub_tab_monthly_cfs_report = st.tabs([
                "📈 Synthèse Annuelle (Tableau Détaillé)", 
                "🏦 Flux de Trésorerie Mensuels (par Année)"
            ])

            with sub_tab_annual_report:
                table_map_data_ui = load_table_map() # De financial_display_utils.py
                if table_map_data_ui:
                    # Assurer que scenario_name_for_key est bien passé
                    display_annual_detailed_summary(
                        financial_results_dict_for_reports, 
                        table_map_data_ui,
                        scenario_name_for_key=scenario_name # Ajout/Confirmation du paramètre
                    )
                else:
                    st.error("Impossible d'afficher la synthèse annuelle détaillée : échec du chargement de financial_table_map.json.")
            
            with sub_tab_monthly_cfs_report:
                available_years_for_cfs_report = []
                monthly_df_for_cfs_report = financial_results_dict_for_reports.get('monthly_data')
                
                # Assurer que l'index est datetime et extraire les années
                if isinstance(monthly_df_for_cfs_report, pd.DataFrame) and not monthly_df_for_cfs_report.empty:
                    df_temp_cfs = monthly_df_for_cfs_report.copy() # Travailler sur une copie
                    if not isinstance(df_temp_cfs.index, pd.DatetimeIndex):
                        try: 
                            df_temp_cfs.index = pd.to_datetime(df_temp_cfs.index)
                        except Exception: # Si la conversion échoue, available_years restera vide
                            st.error("Format d'index des données mensuelles incorrect pour la sélection de l'année.")
                            df_temp_cfs = pd.DataFrame() # Réinitialiser pour éviter d'autres erreurs

                    if isinstance(df_temp_cfs.index, pd.DatetimeIndex) and not df_temp_cfs.empty:
                        available_years_for_cfs_report = sorted(list(df_temp_cfs.index.year.unique()))
                
                if available_years_for_cfs_report:
                    # Utiliser une clé unique pour le selectbox pour éviter les conflits entre scénarios
                    selectbox_key_cfs = f"year_select_cfs_report_ui_{scenario_name}"
                    selected_year_cfs_report = st.selectbox(
                        "Choisir l'année pour les Flux de Trésorerie :", 
                        available_years_for_cfs_report, 
                        index=0, 
                        key=selectbox_key_cfs
                    )
                    # Appel à la fonction du nouveau module monthly_cash_flow_display.py
                    display_cash_flow_statement_restructured(financial_results_dict_for_reports, selected_year_cfs_report)
                elif isinstance(monthly_df_for_cfs_report, pd.DataFrame) and monthly_df_for_cfs_report.empty:
                    st.info("Aucune donnée mensuelle à afficher pour les flux de trésorerie (DataFrame vide).")
                else: # Si available_years est vide pour d'autres raisons
                    st.info("Aucune année disponible pour sélectionner les flux de trésorerie.")
        else:
             # Gestion améliorée de l'affichage si financial_results_dict_for_reports est None
             error_msg_display_reports = "Résultats financiers non disponibles pour le scénario."
             if isinstance(optim_data_tab2, dict) and 'error' in optim_data_tab2:
                 error_msg_display_reports = f"Erreur dans les résultats d'optimisation: {optim_data_tab2['error']}"
             
             st.warning(f"Lancez ou corrigez l'optimisation (ou le calcul des seuils) dans l'onglet 'Analyse & Visualisation' pour afficher les rapports financiers. Message: {error_msg_display_reports}")

# --- Fin fonction UI ---