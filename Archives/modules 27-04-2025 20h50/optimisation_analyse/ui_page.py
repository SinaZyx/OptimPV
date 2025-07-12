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
                        "TRI Projet Minimum (%)",
                        min_value=0.0, max_value=50.0,
                        value=float(current_config.get('constraint_min_irr_pct', 8.0)),
                        step=0.5, format="%.1f",
                        key=f"constraint_project_irr{key_suffix}",
                        help="Taux de Rentabilité Interne (TRI) minimum visé pour le **projet global (avant financement)**."
                    )
                    st.session_state.config['constraint_min_irr_pct'] = min_irr_input
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
                            # --- Section de debug/synchro (gardez-la pour l'instant) ---
                            widget_key = f"constraint_project_irr{key_suffix}" # Clé du widget st.number_input
                            if widget_key in st.session_state:
                                current_constraint_val = st.session_state[widget_key]
                                # Assurer que la config est synchronisée JUSTE AVANT l'optimisation
                                try:
                                    st.session_state.config['constraint_min_irr_pct'] = float(current_constraint_val)
                                    print(f"DEBUG UI (via clé): Lancement optimisation avec TRI Projet Min = {current_constraint_val}%")
                                    # Utiliser st.info pour une visibilité claire dans l'UI
                                    st.info(f"DEBUG UI (via clé): Lancement optimisation avec TRI Projet Min = {current_constraint_val}%") 
                                except (ValueError, TypeError):
                                     st.error(f"DEBUG UI: Impossible de convertir la valeur {current_constraint_val} du widget en float.")
                                     # Ne pas continuer si la valeur n'est pas valide
                                     raise ValueError("Valeur de contrainte TRI invalide.")
                            else:
                                # Fallback si la clé n'existe pas (ne devrait pas arriver)
                                current_constraint_val = st.session_state.config.get('constraint_min_irr_pct', 'ERREUR CLE')
                                print(f"DEBUG UI (via config fallback - ERREUR CLE WIDGET): Lancement optimisation avec TRI Projet Min = {current_constraint_val}%")
                                st.warning(f"DEBUG UI (via config fallback - ERREUR CLE WIDGET): Lancement optimisation avec TRI Projet Min = {current_constraint_val}%")
                                # Tenter de forcer la conversion float ici aussi pour le fallback
                                try:
                                     st.session_state.config['constraint_min_irr_pct'] = float(current_constraint_val)
                                except (ValueError, TypeError):
                                     st.error(f"DEBUG UI: Impossible de convertir la valeur fallback {current_constraint_val} en float.")
                                     raise ValueError("Valeur de contrainte TRI fallback invalide.")
                            # --- FIN Section Debug/Synchro ---
                            
                            # --- AJOUT : Instancier l'Optimizer ICI ---
                            # Assurez-vous que 'analysis_engine' est bien défini avant ce bloc
                            try:
                                 optimizer = OptimizationLogic(
                                      config=st.session_state.config, # Utilise la config mise à jour
                                      analysis_engine=analysis_engine # analysis_engine est créé plus haut
                                 )
                            except Exception as e_init:
                                 st.error(f"Erreur lors de la ré-initialisation de l'Optimizer : {e_init}")
                                 st.stop() # Arrêter si l'optimizer ne peut être créé
                            # --- FIN AJOUT ---
                            
                            # --- MODIFIER L'APPEL : Passer la contrainte comme argument ---
                            optim_res = optimizer.find_optimal_price_constrained(
                                scenario_name=scenario_name,
                                tri_projet_min_pct_constraint=current_constraint_val # <-- Passer la valeur lue
                            )
                            # --- FIN MODIFICATION APPEL ---

                            # Traitement des résultats
                            if optim_res and isinstance(optim_res, dict): 
                                st.session_state.constrained_optim_results[scenario_name] = optim_res
                                if 'error' not in optim_res and 'prix_optimal_const' in optim_res:
                                    st.session_state['analyse_optimisation_terminee'] = True
                                    print("DEBUG UI: Flag 'analyse_optimisation_terminee' mis à True.")
                            else:
                                # Gérer le cas où optim_res n'est pas un dictionnaire attendu
                                st.error("Erreur: Le résultat de l'optimisation n'est pas dans le format attendu.")
                                st.session_state.constrained_optim_results[scenario_name] = {'error': 'Format de résultat inattendu.'}
                            
                            # Supprimer les résultats MC si nouvelle optimisation
                            if scenario_name in st.session_state.monte_carlo_results:
                                 del st.session_state.monte_carlo_results[scenario_name]

                        except Exception as e:
                            st.error(f"Erreur lors de l'optimisation: {e}")
                            st.session_state.constrained_optim_results[scenario_name] = {'error': str(e)}
                    st.rerun()

            # Affichage du résultat de l'optimisation contrainte
            # --- DÉBUT MODIFICATION : Affichage résultats optimisation et tableau dans des onglets ---
            optim_data = st.session_state.constrained_optim_results.get(scenario_name)
            prix_optimal_const_trouve = None # Initialisation

            # Créer les onglets ICI, après avoir potentiellement trouvé le prix optimal
            tab_results1, tab_results2 = st.tabs(["📈 Indicateurs Clés & Robustesse", "📊 Synthèse Financière"])

            with tab_results1:
                # --- Placer les métriques et Monte Carlo dans le premier onglet ---
                st.subheader("Indicateurs au Prix Optimal") # Ajouter un sous-titre

                if isinstance(optim_data, dict):
                    if 'error' in optim_data:
                        st.error(f"Erreur optimisation: {optim_data['error']}")
                    elif 'prix_optimal_const' in optim_data:
                        prix_optimal_const_trouve = optim_data['prix_optimal_const'] # Récupérer le prix ici aussi
                        st.metric("Prix Optimal Recommandé (sous Contraintes)",
                                  f"{prix_optimal_const_trouve:.4f} €/kWh",
                                  help="Meilleur prix maximisant la NPV Equity tout en respectant les contraintes définies.")

                        # Affichage des st.caption pour les contraintes visées
                        constraints_used = optim_data.get('contraintes_appliquees', {})
                        indic_opt = optim_data.get('indicateurs_au_prix_optimal', {}) # Récupérer une seule fois
                        min_proj_irr_target_disp = constraints_used.get('min_irr_pct', 'N/A')
                        edf_ref_res = optim_data.get('tarif_edf_reference')
                        gain_pct_res = ((edf_ref_res - prix_optimal_const_trouve) / edf_ref_res * 100) if (edf_ref_res and edf_ref_res > 0 and prix_optimal_const_trouve is not None) else 0

                        st.caption(f"Contraintes visées: TRI **Projet** ≥ {min_proj_irr_target_disp} %, "
                                   f"Payback Equity ≤ {constraints_used.get('max_payback', 'N/A')} ans, "
                                   f"Gain Client ≥ {constraints_used.get('min_consumer_gain_pct', 'N/A')} %")

                        # Récupération des indicateurs depuis indic_opt
                        npv_eq = indic_opt.get('npv')
                        irr_eq = indic_opt.get('irr')
                        payback_eq = indic_opt.get('payback_period')
                        dscr_res = indic_opt.get('avg_dscr')
                        irr_proj = indic_opt.get('irr_project')
                        payback_proj = indic_opt.get('payback_project')

                        # Affichage de TOUTES les métriques comme avant
                        col_eq1, col_eq2 = st.columns(2)
                        with col_eq1:
                            st.metric("VAN Fonds Propres (€)", f"{npv_eq:,.0f}" if npv_eq is not None else "N/A")
                            st.metric("TRI Fonds Propres (%)", f"{irr_eq*100:.1f}" if irr_eq is not None else "N/A",
                                       delta=f"{(irr_eq*100) - float(min_proj_irr_target_disp):.1f}% vs cible" if irr_eq is not None and isinstance(min_proj_irr_target_disp, (int, float)) else None,
                                       delta_color="normal", help="Taux de Rentabilité Interne sur les fonds propres investis.")
                        with col_eq2:
                             st.metric("Payback Fonds Propres (ans)", f"{payback_eq:.1f}" if payback_eq is not None else "N/A",
                                       delta=f"{payback_eq - constraints_used.get('max_payback', 0):.1f} vs cible" if payback_eq is not None and constraints_used.get('max_payback') is not None else None,
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

                        # Affichage Gain Client
                        st.metric("Gain Client", f"{gain_pct_res:.1f}%" if edf_ref_res else "N/A",
                                  delta=f"{gain_pct_res - constraints_used.get('min_consumer_gain_pct', 0):.1f}% vs cible" if edf_ref_res is not None and constraints_used.get('min_consumer_gain_pct') is not None else None,
                                  delta_color="normal")

                        st.markdown("---") # Séparateur avant Monte Carlo

                        # --- Placer la section Monte Carlo ici aussi ---
                        # Note: La condition `if prix_optimal_const_trouve is not None:` est déjà implicitement vraie ici
                        with st.container(border=True): # Garder un container pour MC
                             st.markdown("**3. Évaluer la Robustesse (Monte Carlo)**")
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

                                    prob_dscr = probs.get('avg_dscr', 0) * 100
                                    prob_payback = probs.get('payback_period', 0) * 100
                                    prob_global = probs.get('global', 0) * 100

                                    col_p1, col_p2, col_p3 = st.columns(3)
                                    with col_p1:
                                        st.metric(f"P(DSCR ≥ {cons_mc.get('dscr_min', 'N/A')})", f"{prob_dscr:.1f}%")
                                    with col_p2:
                                        st.metric(f"P(Payback Equity ≤ {cons_mc.get('payback_max', 'N/A')} ans)", f"{prob_payback:.1f}%") # Préciser Equity
                                    with col_p3:
                                        st.metric("P(Succès Global)", f"{prob_global:.1f}%")

                                    with st.expander("Voir statistiques détaillées de Monte Carlo"):
                                       for k, v in stats_mc.items():
                                           st.write(f"**{k.upper()}**: Moyenne={v['mean']:.2f}, Ecart-type={v['std']:.2f}, Médiane={v['p'][2]:.2f}")
                                else: st.info("Simulation Monte Carlo effectuée mais données de probabilités manquantes.")
                    # Fin de la condition elif 'prix_optimal_const'
                    else:
                        st.info("Optimisation effectuée mais prix non trouvé.")
                else:
                     st.info("Résultats de l'optimisation non disponibles. Lancez l'optimisation ci-dessus.")
                # --- Fin du premier onglet ---

            with tab_results2:
                # --- Placer le tableau financier dans le second onglet ---
                st.subheader("Synthèse Financière Annuelle (au Prix Optimal)") # Titre spécifique pour l'onglet

                # Récupérer à nouveau les indicateurs si nécessaire
                # Utiliser 'indic_opt' qui a déjà été récupéré si possible
                financial_results_dict = None
                if isinstance(optim_data, dict) and 'indicateurs_au_prix_optimal' in optim_data:
                     financial_results_dict = optim_data.get('indicateurs_au_prix_optimal')

                if financial_results_dict and isinstance(financial_results_dict, dict):
                     # Appeler la fonction d'affichage du tableau
                     display_financial_summary_table(financial_results_dict)
                else:
                    st.info("Lancez l'optimisation (Étape 2) pour afficher la synthèse financière annuelle.")
                # --- Fin du second onglet ---
            # --- FIN MODIFICATION : Fin des onglets ---

            # ATTENTION: L'ancien bloc 'with st.container(border=True):' pour le tableau financier
            # qui était ici (vers ligne 235-245) est maintenant SUPPRIMÉ car intégré dans tab_results2.

        # --- Étape 3: (Optionnel) Analyse de Robustesse Monte Carlo ---
        # Cette section est maintenant DANS le premier onglet (tab_results1),
        # donc le code original qui était ici est supprimé.
        # if prix_optimal_const_trouve is not None: ...

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
                        # Utiliser LCOE comme prix min si prix plancher non dispo ou trop bas
                        lcoe_graph = floor_data_graph.get('lcoe_for_ui', 0.05)
                        prix_plancher_graph = floor_data_graph.get('prix_revente_optimal_pour_cible')
                        # Prendre le LCOE comme minimum absolu pour la courbe, ou le prix plancher si plus élevé
                        prix_min_graph = max(lcoe_graph, prix_plancher_graph) if prix_plancher_graph is not None else lcoe_graph

                        prix_edf_ref_graph = floor_data_graph.get('edf_ref_for_ui', 0.30)
                        # Assurer que max > min, même si prix EDF < LCOE
                        prix_max_graph = max(prix_min_graph + 0.01, prix_edf_ref_graph)

                        # Générer les points pour la courbe
                        num_points = 100
                        # Gérer le cas où min et max sont très proches
                        if abs(prix_max_graph - prix_min_graph) < 1e-4:
                            prix_a_tester_graph = np.linspace(prix_min_graph, prix_max_graph, num_points)
                        else:
                            pas_graph = (prix_max_graph - prix_min_graph) / num_points
                            prix_a_tester_graph = np.arange(prix_min_graph, prix_max_graph + pas_graph, pas_graph)


                        # --- NOUVEAU : Calculer l'autoconsommation annuelle agrégée --- 
                        # Refaire l'agrégation ici spécifiquement pour la visualisation
                        if 'sites_data' not in st.session_state or not st.session_state.sites_data:
                            st.error("Aucune donnée de site trouvée pour générer le graphique.")
                            st.session_state[curve_data_key] = None
                        else:
                            # Logique d'agrégation (similaire à analysis_engine)
                            first_site_id = list(st.session_state.sites_data.keys())[0]
                            # Initialiser avec l'index du premier site pour couvrir la plage temporelle
                            aggregated_data_vis = pd.DataFrame(index=st.session_state.sites_data[first_site_id]['Temps'].drop_duplicates().sort_values())
                            aggregated_data_vis['production_kwh'] = 0.0
                            aggregated_data_vis['consumption_kwh'] = 0.0
                            aggregated_data_vis.index = pd.to_datetime(aggregated_data_vis.index) # Assurer DatetimeIndex

                            for site_id, df_site in st.session_state.sites_data.items():
                                 # Préparer le DF pour l'ajout
                                 df_to_add = df_site.set_index('Temps')[['production_kwh', 'consumption_kwh']]
                                 if df_to_add.index.has_duplicates: # Gérer doublons éventuels
                                     print(f"WARN UI Graphique: Doublons temporels pour {site_id}, agrégation par somme.")
                                     df_to_add = df_to_add.groupby(df_to_add.index).sum()
                                 # Utiliser .add avec fill_value=0 pour sommer en alignant les index
                                 aggregated_data_vis = aggregated_data_vis.add(df_to_add, fill_value=0)
                            
                            # Remplacer les NaN potentiels introduits par .add si des index manquaient
                            aggregated_data_vis.fillna(0, inplace=True)

                            # Utiliser les données agrégées pour calculer l'autoconsommation de référence
                            aggregated_data_vis['year'] = aggregated_data_vis.index.year
                            ref_year_vis = aggregated_data_vis['year'].min()
                            ref_data_vis = aggregated_data_vis[aggregated_data_vis['year'] == ref_year_vis]

                            # Calculer l'autoconsommation sur l'année de référence agrégée
                            # Note: Ne pas appliquer de dégradation ici, on veut juste le volume de base
                            param_autoconso_annuel_graph = np.sum(np.minimum(ref_data_vis['production_kwh'], ref_data_vis['consumption_kwh']))
                            # --- FIN NOUVEAU CALCUL AUTOCONSO --- 

                            # Utiliser cette valeur dans la boucle
                            data_curve = []
                            param_cout_prod = lcoe_graph # Utiliser LCOE comme référence coût
                            param_prix_edf = prix_edf_ref_graph

                            for p_vente in prix_a_tester_graph:
                                # Le bénéfice client est l'économie réalisée sur le volume autoconsommé
                                benefice_client = param_autoconso_annuel_graph * (param_prix_edf - p_vente)
                                pct_economie = ((param_prix_edf - p_vente) / param_prix_edf) * 100 if param_prix_edf > 0 else 0

                                data_curve.append({
                                    'PrixVente': p_vente,
                                    'BeneficeClient': benefice_client,
                                    'PctEconomie': pct_economie,
                                })

                            if data_curve:
                                st.session_state[curve_data_key] = pd.DataFrame(data_curve).sort_values(by='PrixVente')
                            else:
                                st.session_state[curve_data_key] = None
                    except Exception as e:
                        st.error(f"Erreur génération données graphique: {e}")
                        # Afficher la trace complète dans la console pour aider au débogage
                        import traceback
                        print("Traceback Erreur Graphique:")
                        print(traceback.format_exc())
                        st.session_state[curve_data_key] = None
                    # --- FIN CODE REMPLACÉ --- 
                st.rerun() # Assure le rafraichissement de l'UI après calcul


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

                    # --- BLOC MODIFIÉ POUR LES DÉTAILS SOUS LE GRAPHIQUE --- 
                    param_autoconso_annuel_details_local = 0 # Initialiser avec une valeur par défaut
                    try:
                        # --- NOUVEAU CALCUL BASÉ SUR DONNÉES AGRÉGÉES --- 
                        if 'sites_data' in st.session_state and st.session_state.sites_data:
                            # Utiliser les données agrégées déjà calculées pour le graphique si possible,
                            # Sinon, refaire l'agrégation ici. Assumons qu'on la refait pour être sûr :
                            first_site_id_det = list(st.session_state.sites_data.keys())[0]
                            aggregated_data_det = pd.DataFrame(index=st.session_state.sites_data[first_site_id_det]['Temps'].drop_duplicates().sort_values())
                            aggregated_data_det['production_kwh'] = 0.0
                            aggregated_data_det['consumption_kwh'] = 0.0
                            aggregated_data_det.index = pd.to_datetime(aggregated_data_det.index)

                            for site_id_det, df_site_det in st.session_state.sites_data.items():
                                df_to_add_det = df_site_det.set_index('Temps')[['production_kwh', 'consumption_kwh']]
                                if df_to_add_det.index.has_duplicates:
                                    df_to_add_det = df_to_add_det.groupby(df_to_add_det.index).sum()
                                aggregated_data_det = aggregated_data_det.add(df_to_add_det, fill_value=0)
                            
                            # Remplacer les NaN potentiels introduits par .add
                            aggregated_data_det.fillna(0, inplace=True)
                            
                            aggregated_data_det['year'] = aggregated_data_det.index.year
                            ref_year_det = aggregated_data_det['year'].min()
                            ref_data_details = aggregated_data_det[aggregated_data_det['year'] == ref_year_det] # Utiliser les données agrégées filtrées

                            # Calculer l'autoconsommation sur l'année de référence agrégée
                            param_autoconso_annuel_details_local = np.sum(np.minimum(ref_data_details['production_kwh'], ref_data_details['consumption_kwh']))
                        else:
                            st.warning("Données de site non trouvées pour calculer les détails sous le graphique.")
                        # --- FIN NOUVEAU CALCUL --- 

                    except Exception as e_autoconso:
                        st.error(f"Erreur calcul autoconso annuelle pour détails: {e_autoconso}")
                        import traceback
                        print("Traceback Erreur Détails Graphique:")
                        print(traceback.format_exc())
                        # param_autoconso_annuel_details_local reste à 0 (fallback)
                    # --- FIN BLOC MODIFIÉ --- 

                    # Affichage des détails pour le point exploré
                    # Utiliser prix_edf_viz déjà calculé pour le graphique
                    final_benefice = param_autoconso_annuel_details_local * (prix_edf_viz - selected_price_explore_viz)
                    final_pct_eco = ((prix_edf_viz - selected_price_explore_viz) / prix_edf_viz) * 100 if prix_edf_viz > 0 else 0

                    st.markdown(f"**Pour `{selected_price_explore_viz:.4f} €/kWh` (curseur):**")
                    det_col1, det_col2 = st.columns(2)
                    with det_col1: st.metric("Bénéfice Client", f"{final_benefice:,.0f} €/an")
                    with det_col2: st.metric("Économie Client", f"{final_pct_eco:.1f}%")

                    # --- DÉBUT DU CODE POUR LE CAMEMBERT --- 
                    st.markdown("---") # Ajoute une ligne de séparation
                    st.markdown("**Répartition Annuelle Moyenne de l'Énergie Produite**")

                    # Récupérer les données nécessaires à partir des résultats d'optimisation
                    # (qui sont dans optim_data, calculés dans la colonne de gauche)
                    optim_data = st.session_state.constrained_optim_results.get(scenario_name, {})
                    results_dict = optim_data.get('indicateurs_au_prix_optimal', {})

                    if results_dict: # Vérifie si les indicateurs existent
                        # Calculer les totaux (ou moyennes annuelles si pertinent)
                        # Ici on somme sur toutes les années de la simulation
                        total_auto = sum(results_dict.get('annual_autoconsumption', [0]))
                        total_surp = sum(results_dict.get('annual_surplus', [0]))
                        total_prod = sum(results_dict.get('annual_production', [0])) # Optionnel: pour vérification

                        # Vérifier si la production totale est positive pour éviter division par zéro ou camembert vide
                        if total_prod > 1e-6:
                            # Appeler la fonction importée pour créer le camembert
                            pie_fig = create_autoconsommation_surplus_pie_chart(total_auto, total_surp)
                            if pie_fig: # S'assurer que la fonction a retourné une figure
                                st.plotly_chart(pie_fig, use_container_width=True)
                            # else: # La fonction placeholder gère déjà l'avertissement si import échoue
                            #     pass 
                        else:
                            st.caption("Production nulle ou non calculée, impossible d'afficher la répartition.")
                    else:
                        # Afficher un message si les résultats d'optimisation ne sont pas encore disponibles
                        st.caption("Lancez l'optimisation (colonne de gauche) pour voir la répartition.")
                    # --- FIN DU CODE À AJOUTER POUR LE CAMEMBERT ---

                else:
                    st.error("Impossible de générer le graphique.")

            except Exception as e:
                st.error("Erreur affichage visualisation (right_col):")
                st.exception(e) # Afficher la trace pour debug
# --- Fin fonction UI ---