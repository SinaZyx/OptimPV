# Dans modules/visualization/main_visualization_ui.py
import streamlit as st
import pandas as pd
# ... autres imports nécessaires pour la classe elle-même ...

try:
    from .client_charts import (
        create_price_comparison_chart,
        create_annual_savings_chart,
        create_energy_distribution_pie,
        create_facture_comparison_chart,
        create_cumulative_savings_chart
    )
    from .producer_charts import (
        create_financial_indicators_chart,
        create_waterfall_cashflow_chart,
        create_debt_balance_chart,
        create_annual_revenue_breakdown_chart,
        create_monte_carlo_results_chart,
        create_monte_carlo_boxplot
        # create_sensitivity_tornado_chart, # si vous le mettez ici
        # display_sensitivity_analysis     # si vous le mettez ici
    )
    # Adaptez cet import pour le profil journalier et le LCOE
    from .lcoe_analysis_charts import display_lcoe_analysis_section # Fonction UI pour le LCOE
    from .producer_charts import create_daily_pattern_chart # Ou depuis lcoe_analysis_charts.py

except ImportError as e:
    st.error(f"Erreur d'importation des modules de graphiques : {e}")
    # Définir des fonctions factices pour éviter les plantages
    def create_price_comparison_chart(*args, **kwargs): return None
    # ... etc. pour toutes les fonctions importées ...
    def display_lcoe_analysis_section(*args, **kwargs): st.warning("Section LCOE non chargée.")
    def create_daily_pattern_chart(*args, **kwargs): return None, None


class VisualizationModule:
    def __init__(self):
        # ... (inchangé) ...
        pass #

    def initialize_default_dashboard(self): #
        # ... (inchangé) ...
        pass

    # Les méthodes de création de graphiques sont maintenant dans des fichiers séparés.
    # La méthode show_ui appellera ces fonctions importées.

    def show_ui(self):
        st.markdown("<h1 class='main-header'>Visualisation des Résultats</h1>", unsafe_allow_html=True)

        if not hasattr(st.session_state, 'constrained_optim_results') or not st.session_state.constrained_optim_results:
            st.warning("Pour accéder aux visualisations, lancez d'abord l'optimisation.")
            return

        available_scenarios = list(st.session_state.constrained_optim_results.keys())
        if not available_scenarios:
            st.warning("Aucun résultat d'optimisation trouvé.")
            return

        selected_scenario_idx = 0
        if 'selected_scenario_visu' in st.session_state and st.session_state.selected_scenario_visu in available_scenarios:
            selected_scenario_idx = available_scenarios.index(st.session_state.selected_scenario_visu)

        selected_scenario = st.selectbox(
            "Sélectionner un scénario à visualiser",
            options=available_scenarios,
            index=selected_scenario_idx,
            key="viz_scenario_select_main_ui" # Clé modifiée pour éviter conflit potentiel
        )
        st.session_state.selected_scenario_visu = selected_scenario

        optim_results = st.session_state.constrained_optim_results.get(selected_scenario, {})
        results_data = optim_results.get('indicateurs_au_prix_optimal')

        if not results_data or not isinstance(results_data, dict) or 'monthly_data' not in results_data:
            st.warning(f"Données détaillées manquantes pour le scénario '{selected_scenario}'.")
            return

        mc_results = st.session_state.get('monte_carlo_results', {}).get(selected_scenario)

        client_tab, producer_tab = st.tabs(["📊 Synthèse Client", "📈 Analyse Producteur/Investisseur"])

        with client_tab:
            st.markdown("<h2 class='sub-header'>Synthèse pour le Client Final</h2>", unsafe_allow_html=True)
            col1_1, col1_2 = st.columns(2)
            with col1_1:
                fig = create_price_comparison_chart(results_data, st.session_state.config)
                if fig: st.plotly_chart(fig, use_container_width=True)
            with col1_2:
                fig = create_annual_savings_chart(results_data, st.session_state.config)
                if fig: st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                fig = create_energy_distribution_pie(results_data)
                if fig: st.plotly_chart(fig, use_container_width=True)
            with col2_2:
                fig = create_facture_comparison_chart(results_data, st.session_state.config)
                if fig: st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            col3_1, _ = st.columns([2,1]) # Ajuster si besoin
            with col3_1:
                fig = create_cumulative_savings_chart(results_data, st.session_state.config)
                if fig: st.plotly_chart(fig, use_container_width=True)

        with producer_tab:
            st.markdown("<h2 class='sub-header'>Analyse pour le Producteur/Investisseur</h2>", unsafe_allow_html=True)

            flux_tab, revenus_tab, dette_tab, profils_tab, lcoe_size_tab, mc_tab = st.tabs([
                "Flux Financiers", "Revenus", "Dette", "Profils Énergétiques", 
                "Analyse LCOE par Taille", "Monte Carlo"
            ])

            with flux_tab:
                fig = create_financial_indicators_chart(results_data)
                if fig: st.plotly_chart(fig, use_container_width=True)

                years_available = len(results_data.get('monthly_data', pd.DataFrame()).resample('YE').count().index)
                if years_available > 0:
                    year_index = st.slider("Sélectionner l'année pour la cascade", 1, years_available, min(5, years_available), key="waterfall_year_slider_main_ui") - 1
                    fig = create_waterfall_cashflow_chart(results_data, year_index)
                    if fig: st.plotly_chart(fig, use_container_width=True)

            with revenus_tab:
                fig = create_annual_revenue_breakdown_chart(results_data)
                if fig: st.plotly_chart(fig, use_container_width=True)

            with dette_tab:
                fig = create_debt_balance_chart(results_data)
                if fig: st.plotly_chart(fig, use_container_width=True)

            with profils_tab:
                fig, suggestions = create_daily_pattern_chart(results=results_data)
                if fig: st.plotly_chart(fig, use_container_width=True)
                if suggestions:
                    st.markdown("---")
                    st.subheader("📊 Analyse du Profil et Suggestions :")
                    for suggestion_text in suggestions:
                        st.markdown(f"* {suggestion_text}")

            with lcoe_size_tab:
                if 'analysis_engine_instance' in st.session_state:
                     # Note: analysis_engine_instance, config, sites_config, scenarios
                     # doivent être disponibles dans st.session_state ou passés à show_ui
                     display_lcoe_analysis_section(
                         st.session_state.analysis_engine_instance,
                         st.session_state.config,
                         st.session_state.sites_config, # La config par site agrégée
                         st.session_state.scenarios
                     )
                else:
                     st.warning("L'instance du moteur d'analyse (analysis_engine_instance) doit être initialisée et stockée dans st.session_state pour cette analyse.")

            with mc_tab:
                if mc_results and isinstance(mc_results, dict) and 'statistics' in mc_results:
                    fig = create_monte_carlo_results_chart(mc_results)
                    if fig: st.plotly_chart(fig, use_container_width=True)
                    fig_box = create_monte_carlo_boxplot(mc_results)
                    if fig_box: st.plotly_chart(fig_box, use_container_width=True)
                else:
                    st.info("Aucun résultat Monte Carlo disponible.")