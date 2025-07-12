# modules/optimisation_analyse/ui_page.py (Extraits Modifiés)

import streamlit as st
import pandas as pd
import numpy as np
import time # Pour clés uniques

try:
    from modules.analysis_engine import AnalysisEngine
    from modules.optimisation_analyse.logique_optimisation import OptimizationLogic
    from modules.optimisation_analyse.visualisation_prix import create_price_benefit_figure, create_autoconsommation_surplus_pie_chart
    from modules.financial_summary_table import display_financial_summary_table
except ImportError as e:
    st.error(f"Erreur importation module : {e}")
    # Définir une fonction vide pour éviter les erreurs si l'import échoue
    def display_financial_summary_table(results: dict | None):
        st.warning("Module d'affichage du tableau financier non chargé.")
    # Ajouter une fonction vide pour le pie chart aussi en cas d'erreur
    def create_autoconsommation_surplus_pie_chart(autoconso_kwh: float, surplus_kwh: float):
        st.warning("Module d'affichage du pie chart non chargé.")
        return None # ou une figure vide
    # Optionnel: arrêter si le module est critique?
    # st.stop() 

def display_analysis_optimisation_section(scenario_name: str):
    st.header(f"Analyse Détaillée et Optimisation : Scénario '{scenario_name}'")
    st.markdown("---")

    # --- Vérifications Préliminaires ---
    required_state = ['config', 'scenarios', 'processed_data']
    # ... (idem qu'avant) ...
    if 'config' not in st.session_state or 'scenarios' not in st.session_state or 'processed_data' not in st.session_state:
         st.error("Données ou configuration manquantes.")
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
    try:
        analysis_engine = AnalysisEngine(
             config=st.session_state.config,
             scenarios=st.session_state.scenarios,
             sites_data=st.session_state.sites_data
        )
        # --- COMMENTER L'INSTANCIATION INITIALE ICI ---
        # optimizer = OptimizationLogic(
        #      config=st.session_state.config,
        #      analysis_engine=analysis_engine
        # )
        # --- FIN COMMENTAIRE ---
    except Exception as e:
         st.error(f"Erreur initialisation moteurs : {e}")
         return

    key_suffix = f"_{scenario_name}" # Pour clés uniques des widgets

    # --- Définition des Onglets --- 
    tab1, tab2 = st.tabs(["📊 Analyse & Visualisation", "📋 Synthèse Financière"])

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
                            # Recréer l'engine avec les données actuelles
                            sites_cfg_local = st.session_state.get('sites_config', {}) # Récupérer sites_config
                            analysis_engine_local = AnalysisEngine(
                                config=st.session_state.config,
                                scenarios=st.session_state.scenarios,
                                sites_data=st.session_state.sites_data
                            )
                            floor_res = analysis_engine_local.simulate_selling_price(
                                scenario_name,
                                target_npv=0,
                                override_source_prix_autoconso="prix_initial",
                                sites_config=sites_cfg_local # <-- Passer sites_config ICI
                            )
                            if floor_res and isinstance(floor_res, dict):
                                 lcoe_val = floor_res.get('lcoe_associated') or floor_res.get('lcoe') # Tentatives
                                 floor_res['lcoe_for_ui'] = lcoe_val
                                 floor_res['edf_ref_for_ui'] = st.session_state.config.get('tarif_edf_reference')
                            st.session_state.floor_price_results[scenario_name] = floor_res
                            st.session_state.thresholds_calculated[scenario_name] = True 
                        except Exception as e:
                            st.error(f"Erreur calcul seuils: {e}")
                            st.session_state.floor_price_results[scenario_name] = {'error': str(e)}
                            st.session_state.thresholds_calculated[scenario_name] = False
                    st.rerun()

                # Affichage des seuils...
                floor_data = st.session_state.floor_price_results.get(scenario_name)
                if isinstance(floor_data, dict) and 'error' not in floor_data:
                     p_plancher = floor_data.get('prix_revente_optimal_pour_cible')
                     lcoe_ui = floor_data.get('lcoe_for_ui')
                     edf_ui = floor_data.get('edf_ref_for_ui')
                     col_s1, col_s2, col_s3 = st.columns(3)
                     with col_s1: st.metric("Prix Plancher Prod.", f"{p_plancher:.4f} €" if p_plancher is not None else "N/A")
                     with col_s2: st.metric("LCOE", f"{lcoe_ui:.4f} €" if lcoe_ui is not None else "N/A")
                     with col_s3: st.metric("Tarif EDF Réf.", f"{edf_ui:.4f} €" if edf_ui is not None else "N/A")
                elif isinstance(floor_data, dict) and 'error' in floor_data:
                     st.error(f"Erreur calcul seuils: {floor_data['error']}")
                # else: st.caption("Cliquez pour calculer.")

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
                                # Recréer les instances AVANT l'appel
                                analysis_engine = AnalysisEngine(
                                    config=st.session_state.config, 
                                    scenarios=st.session_state.scenarios,
                                    sites_data=st.session_state.sites_data
                                )
                                optimizer = OptimizationLogic(
                                     config=st.session_state.config,
                                     analysis_engine=analysis_engine
                                )
                                # <-- AJOUT: Récupérer sites_config ici -->
                                sites_cfg_local = st.session_state.get('sites_config', {})
                                # Passer les contraintes lues ET sites_config
                                optim_res = optimizer.find_optimal_price_constrained(
                                    scenario_name=scenario_name,
                                    tri_projet_min_pct_constraint=constraints_to_use['min_irr_pct'],
                                    sites_config=sites_cfg_local # <-- AJOUTER CECI
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
            prix_optimal_const_trouve = None # Initialisation

            if isinstance(optim_data, dict):
                 # --- Section 1 : Indicateurs Clés --- 
                 st.markdown("---")
                 st.subheader("📈 Indicateurs Clés au Prix Optimal")
                 if 'error' in optim_data:
                     st.error(f"Erreur optimisation: {optim_data['error']}")
                 elif 'prix_optimal_const' in optim_data:
                     prix_optimal_const_trouve = optim_data['prix_optimal_const']
                     st.metric("Prix Optimal Recommandé (sous Contraintes)",
                               f"{prix_optimal_const_trouve:.4f} €/kWh",
                               help="Meilleur prix maximisant la NPV Equity tout en respectant les contraintes définies.")
                     # Affichage Contraintes
                     constraints_used = optim_data.get('contraintes_appliquees', {})
                     indic_opt = optim_data.get('indicateurs_au_prix_optimal', {})
                     min_proj_irr_target_disp = constraints_used.get('min_irr_pct', 'N/A')
                     edf_ref_res = optim_data.get('tarif_edf_reference')
                     gain_pct_res = ((edf_ref_res - prix_optimal_const_trouve) / edf_ref_res * 100) if (edf_ref_res and edf_ref_res > 0 and prix_optimal_const_trouve is not None) else 0
                     st.caption(f"Contraintes visées: TRI **Projet** ≥ {min_proj_irr_target_disp} %, "
                                f"Payback Equity ≤ {constraints_used.get('max_payback', 'N/A')} ans, "
                                f"Gain Client ≥ {constraints_used.get('min_consumer_gain_pct', 'N/A')} %")
                     # Métriques KPIs
                     npv_eq = indic_opt.get('npv')
                     irr_eq = indic_opt.get('irr')
                     payback_eq = indic_opt.get('payback_period')
                     dscr_res = indic_opt.get('avg_dscr')
                     irr_proj = indic_opt.get('irr_project')
                     payback_proj = indic_opt.get('payback_project')
                     col_eq1, col_eq2 = st.columns(2)
                     with col_eq1:
                         st.metric("VAN Fonds Propres (€)", f"{npv_eq:,.0f}" if npv_eq is not None else "N/A")
                         st.metric("TRI Fonds Propres (%)", f"{irr_eq*100:.1f}" if irr_eq is not None else "N/A",
                                    delta=f"{(irr_eq*100) - float(min_proj_irr_target_disp):.1f}% vs cible" if irr_eq is not None and isinstance(min_proj_irr_target_disp, (int, float)) else None,
                                    delta_color="normal", help="Taux de Rentabilité Interne sur les fonds propres investis.")
                     with col_eq2:
                          st.metric("Payback Fonds Propres (ans)", f"{payback_eq:.1f}" if payback_eq is not None else "N/A",
                                     delta=f"{(payback_eq - constraints_used.get('max_payback', 0)):.1f} vs cible" if payback_eq is not None and constraints_used.get('max_payback') is not None else None,
                                     delta_color="inverse", help="Temps pour récupérer l'investissement initial en fonds propres.")
                          st.metric("DSCR Moyen", f"{dscr_res:.2f}" if dscr_res is not None else "N/A",
                                     help="Ratio de couverture du service de la dette moyen sur la durée du prêt.")
                     st.markdown("---")
                     st.markdown("**Indicateurs Projet (avant financement)**")
                     col_proj1, col_proj2 = st.columns(2)
                     with col_proj1:
                         st.metric("TRI Projet (%)", f"{irr_proj*100:.1f}" if irr_proj is not None else "N/A",
                                    help="Taux de Rentabilité Interne du projet basé sur l'investissement total et les flux opérationnels.")
                     with col_proj2:
                         st.metric("Payback Projet (ans)", f"{payback_proj:.1f}" if payback_proj is not None else "N/A",
                                    help="Temps pour récupérer l'investissement total (CAPEX) par les flux opérationnels.")
                     # Gain Client
                     st.metric("Gain Client", f"{gain_pct_res:.1f}%" if edf_ref_res else "N/A",
                               delta=f"{(gain_pct_res - constraints_used.get('min_consumer_gain_pct', 0)):.1f}% vs cible" if edf_ref_res is not None and constraints_used.get('min_consumer_gain_pct') is not None else None,
                               delta_color="normal")
                 else:
                      st.info("Optimisation effectuée mais prix non trouvé ou erreur.")

                 # --- Section 2 : Monte Carlo --- 
                 if prix_optimal_const_trouve is not None:
                     st.markdown("---")
                     st.subheader("🎲 Évaluation de la Robustesse (Monte Carlo)")
                     with st.container(border=True):
                          st.caption("Lancez une simulation Monte Carlo pour évaluer l'impact des aléas au prix optimal.")
                          if st.button(f"Lancer Simulation Monte Carlo{key_suffix}", key=f"btn_mc{key_suffix}_tab1"):
                                with st.spinner("Simulation Monte Carlo..."):
                                    try:
                                        # S'assurer que l'optimizer existe (ou le recréer)
                                        if 'optimizer' not in locals() or optimizer is None:
                                            st.warning("Réinstanciation Optimizer avant Monte Carlo...")
                                            analysis_engine = AnalysisEngine(
                                                config=st.session_state.config,
                                                scenarios=st.session_state.scenarios,
                                                sites_data=st.session_state.sites_data
                                            )
                                            optimizer = OptimizationLogic(
                                                config=st.session_state.config,
                                                analysis_engine=analysis_engine
                                            )
                                        # --- AJOUT: Récupération sites_config ---
                                        sites_cfg_local = st.session_state.get('sites_config', {})
                                        # --- FIN AJOUT ---
                                        mc_res = optimizer.run_monte_carlo_simulation(
                                            scenario_name,
                                            prix_revente=prix_optimal_const_trouve,
                                            sites_config=sites_cfg_local # <--- AJOUT DE L'ARGUMENT
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
                             elif 'probabilities' in mc_data:
                                 st.markdown("**Probabilités de succès (Monte Carlo) :**")
                                 probs = mc_data['probabilities']; stats_mc = mc_data['statistics']; cons_mc = mc_data['contraintes_mc']
                                 prob_dscr = probs.get('avg_dscr', 0)*100; prob_payback = probs.get('payback_period', 0)*100; prob_global = probs.get('global', 0)*100
                                 col_p1, col_p2, col_p3 = st.columns(3)
                                 with col_p1: st.metric(f"P(DSCR ≥ {cons_mc.get('dscr_min', 'N/A')})", f"{prob_dscr:.1f}%")
                                 with col_p2: st.metric(f"P(Payback Equity ≤ {cons_mc.get('payback_max', 'N/A')} ans)", f"{prob_payback:.1f}%")
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
            st.subheader("📊 Visualisations Interactives") # Titre pour la colonne

            # --- Graphe Prix/Bénéfice --- 
            st.markdown("**Analyse de la courbe Prix / Bénéfice**")
            if st.button(f"Afficher/Actualiser le Graphique{key_suffix}", key=f"btn_show_graph_constrained{key_suffix}_tab1"):
                if not st.session_state.thresholds_calculated.get(scenario_name, False):
                    st.warning("Veuillez d'abord calculer les seuils (colonne de gauche).")
                else:
                    with st.spinner("Génération des données du graphique..."):
                        try:
                            # Recalculer les seuils pour le graphique
                            floor_data_graph = st.session_state.floor_price_results.get(scenario_name, {})
                            lcoe_graph = floor_data_graph.get('lcoe_for_ui', 0.05)
                            prix_plancher_graph = floor_data_graph.get('prix_revente_optimal_pour_cible')
                            prix_min_graph = max(lcoe_graph, prix_plancher_graph) if prix_plancher_graph is not None else lcoe_graph
                            prix_edf_ref_graph = floor_data_graph.get('edf_ref_for_ui', 0.30)
                            prix_max_graph = max(prix_min_graph + 0.01, prix_edf_ref_graph)
                            # Générer points
                            num_points = 100
                            if abs(prix_max_graph - prix_min_graph) < 1e-4:
                                prix_a_tester_graph = np.linspace(prix_min_graph, prix_max_graph, num_points)
                            else:
                                pas_graph = (prix_max_graph - prix_min_graph) / num_points
                                prix_a_tester_graph = np.arange(prix_min_graph, prix_max_graph + pas_graph, pas_graph)
                            # Calculer l'autoconso annuelle
                            param_autoconso_annuel_graph = 0
                            if 'sites_data' in st.session_state and st.session_state.sites_data:
                                try:
                                    # Logique d'agrégation simplifiée pour le graphique
                                    aggregated_data_vis = pd.concat(st.session_state.sites_data.values()).groupby('Temps')[['production_kwh', 'consumption_kwh']].sum()
                                    aggregated_data_vis['year'] = aggregated_data_vis.index.year
                                    ref_year_vis = aggregated_data_vis['year'].min()
                                    ref_data_vis = aggregated_data_vis[aggregated_data_vis['year'] == ref_year_vis]
                                    param_autoconso_annuel_graph = np.sum(np.minimum(ref_data_vis['production_kwh'], ref_data_vis['consumption_kwh']))
                                except Exception as e_agg:
                                     st.warning(f"Erreur agrégation pour graphique : {e_agg}")
                            # Calculer données courbe
                            data_curve = []
                            for p_vente in prix_a_tester_graph:
                                benefice_client = param_autoconso_annuel_graph * (prix_edf_ref_graph - p_vente)
                                pct_economie = ((prix_edf_ref_graph - p_vente) / prix_edf_ref_graph) * 100 if prix_edf_ref_graph > 0 else 0
                                data_curve.append({'PrixVente': p_vente, 'BeneficeClient': benefice_client, 'PctEconomie': pct_economie})
                            
                            if data_curve:
                                st.session_state[curve_data_key] = pd.DataFrame(data_curve).sort_values(by='PrixVente')
                            else:
                                st.session_state[curve_data_key] = None
                        except Exception as e_graph:
                            st.error(f"Erreur génération données graphique: {e_graph}")
                            st.session_state[curve_data_key] = None
                    st.rerun()

            # Affichage du Graphique
            df_curve = st.session_state.get(curve_data_key)
            if df_curve is None or df_curve.empty:
                st.info("Cliquez sur 'Afficher/Actualiser le Graphique'.")
            else:
                try:
                    # Récupérer données pour le graphique
                    floor_data_viz = st.session_state.floor_price_results.get(scenario_name, {})
                    cout_prod_viz = floor_data_viz.get('lcoe_for_ui', df_curve['PrixVente'].min())
                    prix_edf_viz = floor_data_viz.get('edf_ref_for_ui', df_curve['PrixVente'].max())
                    optim_results_viz = st.session_state.constrained_optim_results.get(scenario_name, {})
                    prix_optimal_viz = optim_results_viz.get('prix_optimal_const')
                    # Slider
                    slider_min_viz = df_curve['PrixVente'].min(); slider_max_viz = df_curve['PrixVente'].max()
                    default_slider_val_viz = prix_optimal_viz if (prix_optimal_viz is not None and slider_min_viz <= prix_optimal_viz <= slider_max_viz) else (slider_min_viz + slider_max_viz) / 2
                    selected_price_explore_viz = st.slider(
                        "Explorer un Prix (€/kWh):", min_value=float(slider_min_viz), max_value=float(slider_max_viz),
                        value=float(default_slider_val_viz), step=max(1e-5, (slider_max_viz - slider_min_viz)/1000),
                        format="%.4f €/kWh", key=f"ui_viz_slider_constrained_{scenario_name}"
                    )
                    # Création figure
                    fig = create_price_benefit_figure(
                        df_data=df_curve, cout_prod=cout_prod_viz, prix_edf=prix_edf_viz,
                        selected_price=selected_price_explore_viz, optimal_price=prix_optimal_viz
                    )
                    if fig: st.plotly_chart(fig, use_container_width=True)
                    # Détails sous le graphe
                    param_autoconso_annuel_details_local = 0 # Fallback
                    if 'param_autoconso_annuel_graph' in locals() or 'param_autoconso_annuel_graph' in globals(): # Réutiliser si calculé plus haut
                         param_autoconso_annuel_details_local = param_autoconso_annuel_graph
                    elif 'sites_data' in st.session_state and st.session_state.sites_data: # Recalculer si besoin
                         try:
                              aggregated_data_det = pd.concat(st.session_state.sites_data.values()).groupby('Temps')[['production_kwh', 'consumption_kwh']].sum()
                              aggregated_data_det['year'] = aggregated_data_det.index.year
                              ref_year_det = aggregated_data_det['year'].min()
                              ref_data_details = aggregated_data_det[aggregated_data_det['year'] == ref_year_det]
                              param_autoconso_annuel_details_local = np.sum(np.minimum(ref_data_details['production_kwh'], ref_data_details['consumption_kwh']))
                         except Exception as e_det:
                              print(f"WARN: Erreur recalc autoconso pour détails: {e_det}")
                    
                    final_benefice = param_autoconso_annuel_details_local * (prix_edf_viz - selected_price_explore_viz)
                    final_pct_eco = ((prix_edf_viz - selected_price_explore_viz) / prix_edf_viz) * 100 if prix_edf_viz > 0 else 0
                    st.markdown(f"**Pour `{selected_price_explore_viz:.4f} €/kWh` (curseur):**")
                    det_col1, det_col2 = st.columns(2)
                    with det_col1: st.metric("Bénéfice Client", f"{final_benefice:,.0f} €/an")
                    with det_col2: st.metric("Économie Client", f"{final_pct_eco:.1f}%")
                except Exception as e_viz:
                    st.error("Erreur affichage visualisation:"); st.exception(e_viz)

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

    with tab2:
        st.subheader("📊 Synthèse Financière Annuelle (au Prix Optimal)")

        # Récupérer les résultats nécessaires pour le tableau
        optim_data_tab2 = st.session_state.constrained_optim_results.get(scenario_name)
        financial_results_dict_tab2 = None
        if isinstance(optim_data_tab2, dict) and 'indicateurs_au_prix_optimal' in optim_data_tab2:
             financial_results_dict_tab2 = optim_data_tab2.get('indicateurs_au_prix_optimal')

        # Appeler la fonction d'affichage du tableau SI les données sont prêtes
        if financial_results_dict_tab2 and isinstance(financial_results_dict_tab2, dict):
             display_financial_summary_table(financial_results_dict_tab2)
        else:
             st.info("Lancez l'optimisation dans l'onglet 'Analyse & Visualisation' pour afficher ce tableau.")

# --- Fin fonction UI ---