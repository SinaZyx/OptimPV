# modules/optimisation_analyse/ui_page.py (Extraits Modifiés)

import streamlit as st
import pandas as pd
import numpy as np
import time # Pour clés uniques

try:
    from modules.analysis_engine import AnalysisEngine
    from modules.optimisation_analyse.logique_optimisation import OptimizationLogic
    from modules.optimisation_analyse.visualisation_prix import create_price_benefit_figure
    from modules.financial_summary_table import display_financial_summary_table
except ImportError as e:
    st.error(f"Erreur importation module : {e}")
    # Définir une fonction vide pour éviter les erreurs si l'import échoue
    def display_financial_summary_table(results: dict | None):
        st.warning("Module d'affichage du tableau financier non chargé.")
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
             processed_data=st.session_state.processed_data
        )
        optimizer = OptimizationLogic(
             config=st.session_state.config,
             analysis_engine=analysis_engine
        )
    except Exception as e:
         st.error(f"Erreur initialisation moteurs : {e}")
         return

    key_suffix = f"_{scenario_name}" # Pour clés uniques des widgets

    # --- Layout ---
    left_col, right_col = st.columns([1, 1]) # Deux colonnes

    with left_col:
        st.subheader("📈 Optimisation & Robustesse")

        # --- Étape 1: Calcul des Seuils (Prix Plancher / LCOE) ---
        with st.container(border=True):
            st.markdown("**1. Calculer les Seuils Indispensables**")
            st.caption("Calcul du prix plancher (VAN=0) et du LCOE pour définir les bornes.")
            # ... (Code identique à l'exemple précédent pour calculer et afficher le prix plancher, LCOE et EDF) ...
            if st.button(f"Calculer Prix Plancher (VAN=0) & LCOE{key_suffix}", key=f"btn_floor{key_suffix}"):
                 # ... (logique de calcul floor_res comme avant) ...
                 with st.spinner("Calcul des seuils..."):
                    try:
                        floor_res = analysis_engine.simulate_selling_price(
                            scenario_name, target_npv=0, override_source_prix_autoconso="prix_initial"
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
                 # Afficher les métriques... (comme dans l'exemple précédent)
                 st.metric("Prix Plancher Prod.", f"{p_plancher:.4f} €" if p_plancher is not None else "N/A")
                 st.metric("LCOE", f"{lcoe_ui:.4f} €" if lcoe_ui is not None else "N/A")
                 st.metric("Tarif EDF Réf.", f"{edf_ui:.4f} €" if edf_ui is not None else "N/A")
            elif isinstance(floor_data, dict) and 'error' in floor_data:
                 st.error(f"Erreur calcul seuils: {floor_data['error']}")
            # else: st.caption("Cliquez pour calculer.")

        # --- Étape 2: Définir les Contraintes & Lancer l'Optimisation ---
        with st.container(border=True):
            st.markdown("**2. Optimiser le Prix sous Contraintes**")

            if not st.session_state.thresholds_calculated.get(scenario_name, False):
                st.warning("Veuillez d'abord calculer les seuils (étape 1).")
            else:
                st.markdown("Définissez vos exigences minimales :")
                current_config = st.session_state.config

                # --- DEBUT MODIFICATION: Remplacer DSCR par TRI ---
                default_min_irr = float(current_config.get('constraint_min_irr_pct', 8.0)) # Lire la nouvelle config
                default_max_payback = float(current_config.get('constraint_max_payback', 18.0))
                default_min_gain = float(current_config.get('constraint_min_consumer_gain_pct', 5.0))

                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1:
                    # Remplacer le number_input du DSCR par celui du TRI
                    min_irr_input = st.number_input(
                        "TRI Minimum (%)", min_value=0.0, max_value=50.0, # Ajuster max si besoin
                        value=default_min_irr, step=0.5, format="%.1f", # <-- CORRIGÉ: Juste le format du nombre
                        key=f"constraint_irr{key_suffix}", help="Taux de Rentabilité Interne (IRR) minimum visé pour le projet."
                    )
                    st.session_state.config['constraint_min_irr_pct'] = min_irr_input # Sauvegarder la valeur en %
                # --- FIN MODIFICATION ---
                with col_c2:
                    max_payback_input = st.number_input(
                        "Payback Maximum (ans)", min_value=5.0, max_value=30.0,
                        value=default_max_payback, step=1.0, format="%.1f",
                        key=f"constraint_payback{key_suffix}", help="Durée maximale de retour sur investissement."
                    )
                    st.session_state.config['constraint_max_payback'] = max_payback_input
                with col_c3:
                    min_gain_input = st.slider(
                        "Gain Client Minimum (%)", min_value=0, max_value=50,
                        value=int(default_min_gain), step=1, format="%d%%",
                        key=f"constraint_gain{key_suffix}", help="Pourcentage minimum d'économie pour le client par rapport au tarif EDF."
                    )
                    st.session_state.config['constraint_min_consumer_gain_pct'] = float(min_gain_input)

                # Bouton pour lancer l'optimisation (inchangé)
                if st.button(f"Trouver le Prix Optimal (sous Contraintes){key_suffix}", key=f"btn_constrained_optim{key_suffix}"):
                    with st.spinner("Optimisation sous contraintes en cours..."):
                        try:
                            # La logique lit les contraintes depuis config
                            optim_res = optimizer.find_optimal_price_constrained(scenario_name)
                            st.session_state.constrained_optim_results[scenario_name] = optim_res

                            if optim_res and 'error' not in optim_res and 'prix_optimal_const' in optim_res:
                                st.session_state['analyse_optimisation_terminee'] = True
                                print("DEBUG UI: Flag 'analyse_optimisation_terminee' mis à True.")
                            
                            if scenario_name in st.session_state.monte_carlo_results:
                                 del st.session_state.monte_carlo_results[scenario_name]
                        except Exception as e:
                            st.error(f"Erreur lors de l'optimisation: {e}")
                            st.session_state.constrained_optim_results[scenario_name] = {'error': str(e)}
                    st.rerun()

            # Affichage du résultat de l'optimisation contrainte
            optim_data = st.session_state.constrained_optim_results.get(scenario_name)
            prix_optimal_const_trouve = None
            if isinstance(optim_data, dict):
                if 'error' in optim_data:
                    st.error(f"Erreur optimisation: {optim_data['error']}")
                elif 'prix_optimal_const' in optim_data:
                    prix_optimal_const_trouve = optim_data['prix_optimal_const']
                    st.metric("Prix Optimal Recommandé (sous Contraintes)",
                              f"{prix_optimal_const_trouve:.4f} €/kWh",
                              help="Meilleur prix maximisant la NPV tout en respectant les contraintes définies.")
                    
                    constraints_used = optim_data.get('contraintes_appliquees', {})
                    indic_opt = optim_data.get('indicateurs_au_prix_optimal', {})
                    min_irr_target_disp = constraints_used.get('min_irr_pct', 'N/A')
                    payback_res = indic_opt.get('payback_period')
                    edf_ref_res = optim_data.get('tarif_edf_reference')
                    gain_pct_res = ((edf_ref_res - prix_optimal_const_trouve) / edf_ref_res * 100) if (edf_ref_res and edf_ref_res > 0 and prix_optimal_const_trouve is not None) else 0

                    st.caption(f"Contraintes visées: TRI ≥ {min_irr_target_disp} %, " 
                               f"Payback ≤ {constraints_used.get('max_payback', 'N/A')} ans, "
                               f"Gain Client ≥ {constraints_used.get('min_consumer_gain_pct', 'N/A')} %")

                    npv_opt = indic_opt.get('npv')
                    irr_opt = indic_opt.get('irr')
                    roi_opt = indic_opt.get('roi')
                    dscr_res = indic_opt.get('avg_dscr')

                    col_r1, col_r2, col_r3 = st.columns(3)
                    with col_r1:
                         st.metric("NPV Projet", f"{npv_opt:,.0f} €" if npv_opt is not None else "N/A")
                         st.metric("IRR Projet", f"{irr_opt*100:.1f}%" if irr_opt is not None else "N/A",
                                   delta=f"{(irr_opt*100) - float(min_irr_target_disp):.1f}% vs cible" if irr_opt is not None and isinstance(min_irr_target_disp, (int, float)) else None,
                                   delta_color="normal")
                    with col_r2:
                         st.metric("ROI", f"{roi_opt*100:.1f}%" if roi_opt is not None else "N/A")
                         st.metric("Payback", f"{payback_res:.1f} ans" if payback_res is not None else "N/A",
                                   delta=f"{payback_res - constraints_used.get('max_payback', 0):.1f} vs cible" if payback_res is not None and constraints_used.get('max_payback') is not None else None,
                                   delta_color="inverse")
                    with col_r3:
                         st.metric("DSCR Moyen", f"{dscr_res:.2f}" if dscr_res is not None else "N/A")
                         st.metric("Gain Client", f"{gain_pct_res:.1f}%" if edf_ref_res else "N/A",
                                   delta=f"{gain_pct_res - constraints_used.get('min_consumer_gain_pct', 0):.1f}% vs cible" if edf_ref_res is not None and constraints_used.get('min_consumer_gain_pct') is not None else None,
                                   delta_color="normal")


                    # --- MODIFICATION : Affichage du Tableau Financier dans un conteneur dédié ---
                    # Le st.markdown("---") peut être avant ou après le conteneur selon préférence visuelle
                    st.markdown("---")
                    with st.container(border=True): # Crée une boîte visuelle pour la section
                        st.subheader("📊 Synthèse Financière Annuelle (Prix Optimal)") # Titre de la section

                        financial_results_dict = optim_data.get('indicateurs_au_prix_optimal')
                        if financial_results_dict and isinstance(financial_results_dict, dict):
                            # Appeler la fonction à l'intérieur du conteneur
                            display_financial_summary_table(financial_results_dict)
                        else:
                            # Afficher le message d'attente à l'intérieur du conteneur
                            st.info("Le tableau de synthèse financière s'affichera ici une fois l'optimisation réussie.")
                    # --- FIN MODIFICATION ---
                else:
                    st.info("Optimisation effectuée mais prix non trouvé.")
            # else: st.caption("Ajustez les contraintes et cliquez pour optimiser.")

        # --- Étape 3: (Optionnel) Analyse de Robustesse Monte Carlo ---
        if prix_optimal_const_trouve is not None: # N'afficher que si un prix optimal a été trouvé
            with st.container(border=True):
                 st.markdown("**3. Évaluer la Robustesse du Prix Optimal**")
                 st.caption("Lancez une simulation Monte Carlo pour voir comment les aléas (production, consommation) affectent les résultats au prix optimal trouvé.")

                 if st.button(f"Lancer Simulation Monte Carlo{key_suffix}", key=f"btn_mc{key_suffix}"):
                      with st.spinner("Simulation Monte Carlo en cours..."):
                           try:
                                mc_res = optimizer.run_monte_carlo_simulation(
                                     scenario_name,
                                     prix_revente=prix_optimal_const_trouve # Utiliser le prix optimal trouvé
                                )
                                st.session_state.monte_carlo_results[scenario_name] = mc_res
                           except Exception as e:
                                st.error(f"Erreur lors de la simulation Monte Carlo: {e}")
                                st.session_state.monte_carlo_results[scenario_name] = {'error': str(e)}
                      st.rerun()
                 # Affichage des résultats Monte Carlo
                 mc_data = st.session_state.monte_carlo_results.get(scenario_name)
                 if isinstance(mc_data, dict):
                    if 'error' in mc_data:
                        st.error(f"Erreur Monte Carlo: {mc_data['error']}")
                    elif 'probabilities' in mc_data:
                        st.markdown("**Probabilités de succès (Monte Carlo) :**")
                        probs = mc_data['probabilities']
                        stats_mc = mc_data['statistics']
                        cons_mc = mc_data['contraintes_mc']

                        # NOTE: La probabilité DSCR est toujours calculée et affichée,
                        # même si elle n'est plus une contrainte principale ici.
                        # Pour ajouter la probabilité TRI, il faudrait modifier
                        # run_monte_carlo_simulation et les résultats retournés.
                        prob_dscr = probs.get('avg_dscr', 0) * 100 
                        prob_payback = probs.get('payback_period', 0) * 100
                        prob_global = probs.get('global', 0) * 100

                        col_p1, col_p2, col_p3 = st.columns(3)
                        with col_p1:
                            st.metric(f"P(DSCR ≥ {cons_mc.get('dscr_min', 'N/A')})", f"{prob_dscr:.1f}%") # Affichage DSCR MC conservé
                        with col_p2:
                            st.metric(f"P(Payback ≤ {cons_mc.get('payback_max', 'N/A')} ans)", f"{prob_payback:.1f}%")
                        with col_p3:
                            st.metric("P(Succès Global)", f"{prob_global:.1f}%")

                        with st.expander("Voir statistiques détaillées de Monte Carlo"):
                           # Afficher les moyennes, std, percentiles...
                           for k, v in stats_mc.items():
                               st.write(f"**{k.upper()}**: Moyenne={v['mean']:.2f}, Ecart-type={v['std']:.2f}, Médiane={v['p'][2]:.2f}")
                    else: st.info("Simulation Monte Carlo effectuée mais données de probabilités manquantes.")


    with right_col:
        st.subheader("📊 Visualisation Interactive")
        st.markdown("**Analyse de la courbe Prix / Bénéfice**")

        if st.button(f"Afficher/Actualiser le Graphique{key_suffix}", key=f"btn_show_graph_constrained{key_suffix}"):
            if not st.session_state.thresholds_calculated.get(scenario_name, False):
                st.warning("Veuillez d'abord calculer les seuils (Étape 1 à gauche).")
            else:
                with st.spinner("Génération des données du graphique..."):
                    try:
                        floor_data_graph = st.session_state.floor_price_results.get(scenario_name, {})
                        prix_min_graph = floor_data_graph.get('prix_revente_optimal_pour_cible', 0.05)
                        prix_edf_ref_graph = floor_data_graph.get('edf_ref_for_ui', 0.30)
                        prix_max_graph = max(prix_min_graph + 0.01, prix_edf_ref_graph)
                        num_points = 100 if (prix_max_graph - prix_min_graph) > 0.01 else 50
                        pas_graph = max(1e-5, (prix_max_graph - prix_min_graph) / num_points)
                        prix_a_tester_graph = np.arange(prix_min_graph, prix_max_graph + pas_graph, pas_graph)


                        data_curve = []
                        config = st.session_state.config
                        param_cout_prod = floor_data_graph.get('lcoe_for_ui', 0.10) # LCOE reste nécessaire pour référence
                        param_prix_edf = floor_data_graph.get('edf_ref_for_ui', 0.22)

                        # Récupérer l'autoconso annuelle (identique)
                        ref_data_loop = st.session_state.processed_data[st.session_state.processed_data['Temps'].dt.year == st.session_state.processed_data['Temps'].dt.year.min()]
                        autoconso_annuel_loop = ref_data_loop.apply(lambda row: min(row['production_kwh'], row['consumption_kwh']), axis=1).sum()

                        for p_vente in prix_a_tester_graph:
                            benefice_client = autoconso_annuel_loop * (param_prix_edf - p_vente)
                            pct_economie = ((param_prix_edf - p_vente) / param_prix_edf) * 100 if param_prix_edf > 0 else 0

                            data_curve.append({
                                'PrixVente': p_vente,
                                'BeneficeClient': benefice_client,
                                'PctEconomie': pct_economie,
                            })
                        if data_curve:
                            st.session_state[curve_data_key] = pd.DataFrame(data_curve).sort_values(by='PrixVente')
                        else: st.session_state[curve_data_key] = None
                    except Exception as e:
                        st.error(f"Erreur génération données graphique: {e}")
                        st.session_state[curve_data_key] = None
                st.rerun()


        # --- Affichage du Graphique (si données prêtes) ---
        df_curve = st.session_state.get(curve_data_key)

        if df_curve is None or df_curve.empty:
            st.info("Cliquez sur 'Afficher/Actualiser le Graphique' pour générer la courbe.")
        else:
            try:
                floor_data_viz = st.session_state.floor_price_results.get(scenario_name, {})
                cout_prod_viz = floor_data_viz.get('lcoe_for_ui', df_curve['PrixVente'].min())
                prix_edf_viz = floor_data_viz.get('edf_ref_for_ui', df_curve['PrixVente'].max())
                prix_optimal_viz = st.session_state.constrained_optim_results.get(scenario_name, {}).get('prix_optimal_const')


                # Slider (identique)
                slider_min_viz = df_curve['PrixVente'].min()
                slider_max_viz = df_curve['PrixVente'].max()
                default_slider_val_viz = prix_optimal_viz if (prix_optimal_viz is not None and slider_min_viz <= prix_optimal_viz <= slider_max_viz) else (slider_min_viz + slider_max_viz) / 2
                selected_price_explore_viz = st.slider(
                    "Explorer un Prix sur la Courbe (€/kWh):",
                    min_value=float(slider_min_viz), max_value=float(slider_max_viz),
                    value=float(default_slider_val_viz), step=max(1e-5, (slider_max_viz - slider_min_viz)/1000),
                    format="%.4f €/kWh",
                    key=f"ui_viz_slider_explore_constrained_{scenario_name}"
                )


                # Création de la figure (appel identique)
                fig = create_price_benefit_figure(
                    df_data=df_curve,
                    cout_prod=cout_prod_viz,
                    prix_edf=prix_edf_viz,
                    selected_price=selected_price_explore_viz,
                    optimal_price=prix_optimal_viz
                )

                if fig:
                    st.plotly_chart(fig, use_container_width=True)

                    # Calculs pour les détails sous le graphique
                    try:
                        ref_data_details = st.session_state.processed_data[st.session_state.processed_data['Temps'].dt.year == st.session_state.processed_data['Temps'].dt.year.min()]
                        param_autoconso_annuel_details_local = ref_data_details.apply(lambda row: min(row['production_kwh'], row['consumption_kwh']), axis=1).sum()
                    except Exception as e_autoconso:
                        st.error(f"Erreur calcul autoconso annuelle pour détails: {e_autoconso}")
                        param_autoconso_annuel_details_local = 0 # Fallback

                    # Affichage des détails pour le point exploré
                    final_benefice = param_autoconso_annuel_details_local * (prix_edf_viz - selected_price_explore_viz)
                    final_pct_eco = ((prix_edf_viz - selected_price_explore_viz) / prix_edf_viz) * 100 if prix_edf_viz > 0 else 0

                    st.markdown(f"**Pour `{selected_price_explore_viz:.4f} €/kWh` (curseur):**")
                    det_col1, det_col2 = st.columns(2) # Deux colonnes suffisent
                    with det_col1: st.metric("Bénéfice Client", f"{final_benefice:,.0f} €/an")
                    with det_col2: st.metric("Économie Client", f"{final_pct_eco:.1f}%")

                else:
                    st.error("Impossible de générer le graphique.")

            except Exception as e:
                st.error("Erreur affichage visualisation:")
                st.exception(e) # Afficher la trace pour debug
# --- Fin fonction UI ---