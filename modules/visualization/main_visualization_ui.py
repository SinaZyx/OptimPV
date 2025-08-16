# Module principal de visualisation avec navigation améliorée
import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

# Imports depuis la nouvelle structure
try:
    # Client modules
    from .client import (
        create_price_comparison_chart,
        create_annual_savings_chart,
        create_energy_distribution_pie,
        create_facture_comparison_chart,
        create_cumulative_savings_chart
    )
    from .client.dashboard import display_client_dashboard
    
    # Investor modules
    from .investor import (
        create_financial_indicators_chart,
        create_waterfall_cashflow_chart,
        create_debt_balance_chart,
        create_annual_revenue_breakdown_chart,
        create_daily_pattern_chart,
        create_monte_carlo_results_chart,
        create_monte_carlo_boxplot,
        create_sensitivity_tornado_chart,
        display_sensitivity_analysis_section
    )
    from .investor.dashboard import display_investor_dashboard
    
    # Shared modules
    from .shared import (
        display_breakeven_analysis_ui,
        prepare_chart_for_export,
        COLORS
    )
    
    # LCOE analysis
    from .lcoe_analysis_charts import display_lcoe_analysis_section
    
    imports_successful = True
    
except ImportError as e:
    st.error(f"Erreur d'importation des modules de graphiques : {e}")
    imports_successful = False
    # Définir des fonctions factices pour éviter les plantages
    def create_price_comparison_chart(*args, **kwargs): return None
    def display_lcoe_analysis_section(*args, **kwargs): st.warning("Section LCOE non chargée.")
    def create_daily_pattern_chart(*args, **kwargs): return None, None
    def display_client_dashboard(*args, **kwargs): st.warning("Dashboard client non chargé.")
    def display_investor_dashboard(*args, **kwargs): st.warning("Dashboard investisseur non chargé.")


class VisualizationModule:
    def __init__(self):
        # Initialisation des états
        if 'view_mode' not in st.session_state:
            st.session_state.view_mode = 'dashboard'  # dashboard, detailed, analysis
        if 'user_type' not in st.session_state:
            st.session_state.user_type = 'client'  # client, investor
        if 'show_export_options' not in st.session_state:
            st.session_state.show_export_options = False
            
    def initialize_default_dashboard(self):
        """Initialise les paramètres par défaut du dashboard"""
        if 'dashboard_settings' not in st.session_state:
            st.session_state.dashboard_settings = {
                'theme': 'light',
                'auto_refresh': False,
                'export_format': 'pdf'
            }

    def show_ui(self):
        """Interface principale avec navigation améliorée"""
        
        # Sidebar pour la navigation
        with st.sidebar:
            st.markdown("### 🧭 Navigation")
            
            # Sélection du type d'utilisateur
            user_type = st.radio(
                "Type d'utilisateur",
                options=['client', 'investor'],
                format_func=lambda x: "👥 Client" if x == 'client' else "💼 Investisseur",
                key="user_type_selector"
            )
            st.session_state.user_type = user_type
            
            # Mode de vue
            view_mode = st.radio(
                "Mode d'affichage",
                options=['dashboard', 'detailed', 'analysis'],
                format_func=lambda x: {
                    'dashboard': "📊 Tableau de Bord",
                    'detailed': "📈 Vue Détaillée",
                    'analysis': "🔍 Analyses Avancées"
                }.get(x, x),
                key="view_mode_selector"
            )
            st.session_state.view_mode = view_mode
            
            # Filtres persistants
            with st.expander("⚙️ Filtres", expanded=True):
                # Période d'analyse
                period_filter = st.selectbox(
                    "Période",
                    options=['all', '1y', '5y', '10y', '20y'],
                    format_func=lambda x: {
                        'all': "Toute la durée",
                        '1y': "1 an",
                        '5y': "5 ans",
                        '10y': "10 ans",
                        '20y': "20 ans"
                    }.get(x, x)
                )
                
                # Options d'export
                st.markdown("### 📤 Export")
                export_format = st.selectbox(
                    "Format",
                    options=['pdf', 'png', 'xlsx'],
                    format_func=lambda x: {
                        'pdf': "📄 PDF",
                        'png': "🖼️ PNG",
                        'xlsx': "📊 Excel"
                    }.get(x, x)
                )
                
                if st.button("🚀 Exporter", use_container_width=True):
                    st.session_state.show_export_options = True
        
        # Titre principal adapté au contexte
        if st.session_state.user_type == 'client':
            st.markdown("<h1 class='main-header'>🏠 Espace Client - Visualisation</h1>", unsafe_allow_html=True)
        else:
            st.markdown("<h1 class='main-header'>💼 Espace Investisseur - Visualisation</h1>", unsafe_allow_html=True)
        
        # Vérification des données
        if not hasattr(st.session_state, 'constrained_optim_results') or not st.session_state.constrained_optim_results:
            st.warning("Pour accéder aux visualisations, lancez d'abord l'optimisation.")
            return

        available_scenarios = list(st.session_state.constrained_optim_results.keys())
        if not available_scenarios:
            st.warning("Aucun résultat d'optimisation trouvé.")
            return

        # Sélection du scénario
        selected_scenario_idx = 0
        if 'selected_scenario_visu' in st.session_state and st.session_state.selected_scenario_visu in available_scenarios:
            selected_scenario_idx = available_scenarios.index(st.session_state.selected_scenario_visu)

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            selected_scenario = st.selectbox(
                "📊 Scénario à visualiser",
                options=available_scenarios,
                index=selected_scenario_idx,
                key="viz_scenario_select_main_ui"
            )
        with col2:
            if st.button("🔄 Actualiser", use_container_width=True):
                st.rerun()
        with col3:
            if st.button("⚙️ Paramètres", use_container_width=True):
                st.session_state.show_settings = True
                
        st.session_state.selected_scenario_visu = selected_scenario

        optim_results = st.session_state.constrained_optim_results.get(selected_scenario, {})
        results_data = optim_results.get('indicateurs_au_prix_optimal')

        if not results_data or not isinstance(results_data, dict) or 'monthly_data' not in results_data:
            st.warning(f"Données détaillées manquantes pour le scénario '{selected_scenario}'.")
            return

        mc_results = st.session_state.get('monte_carlo_results', {}).get(selected_scenario)
        
        # Affichage selon le mode et le type d'utilisateur
        if st.session_state.view_mode == 'dashboard':
            self._show_dashboard_view(results_data, mc_results)
        elif st.session_state.view_mode == 'detailed':
            self._show_detailed_view(results_data, mc_results)
        elif st.session_state.view_mode == 'analysis':
            self._show_analysis_view(results_data, mc_results)

    def _show_dashboard_view(self, results_data: Dict[str, Any], mc_results: Optional[Dict[str, Any]]):
        """Affiche la vue dashboard selon le type d'utilisateur"""
        if st.session_state.user_type == 'client':
            display_client_dashboard(results_data, st.session_state.config)
        else:
            display_investor_dashboard(results_data, st.session_state.config, mc_results)
    
    def _show_detailed_view(self, results_data: Dict[str, Any], mc_results: Optional[Dict[str, Any]]):
        """Affiche la vue détaillée avec tous les graphiques"""
        
        if st.session_state.user_type == 'client':
            # Vue détaillée client
            tabs = st.tabs(["💰 Économies", "⚡ Énergie", "📊 Comparaisons", "📈 Projections"])
            
            with tabs[0]:  # Économies
                col1, col2 = st.columns(2)
                with col1:
                    fig = create_annual_savings_chart(results_data, st.session_state.config)
                    if fig: st.plotly_chart(fig, use_container_width=True)
                with col2:
                    fig = create_cumulative_savings_chart(results_data, st.session_state.config)
                    if fig: st.plotly_chart(fig, use_container_width=True)
                    
            with tabs[1]:  # Énergie
                col1, col2 = st.columns(2)
                with col1:
                    fig = create_energy_distribution_pie(results_data)
                    if fig: st.plotly_chart(fig, use_container_width=True)
                with col2:
                    fig, suggestions = create_daily_pattern_chart(results=results_data)
                    if fig: st.plotly_chart(fig, use_container_width=True)
                    
            with tabs[2]:  # Comparaisons
                col1, col2 = st.columns(2)
                with col1:
                    fig = create_price_comparison_chart(results_data, st.session_state.config)
                    if fig: st.plotly_chart(fig, use_container_width=True)
                with col2:
                    fig = create_facture_comparison_chart(results_data, st.session_state.config)
                    if fig: st.plotly_chart(fig, use_container_width=True)
                    
            with tabs[3]:  # Projections
                display_breakeven_analysis_ui(
                    results_data, 
                    st.session_state.config,
                    st.session_state.get('analysis_engine_instance')
                )
                
        else:
            # Vue détaillée investisseur
            tabs = st.tabs([
                "💰 Flux Financiers", "📈 Revenus", "💳 Dette", 
                "⚡ Profils", "📊 LCOE", "🎲 Monte Carlo", "🔍 Sensibilité"
            ])
            
            with tabs[0]:  # Flux Financiers
                fig = create_financial_indicators_chart(results_data)
                if fig: st.plotly_chart(fig, use_container_width=True)
                
                years_available = len(results_data.get('monthly_data', pd.DataFrame()).resample('Y').count().index)
                if years_available > 0:
                    year_index = st.slider(
                        "Sélectionner l'année pour la cascade", 
                        1, years_available, 
                        min(5, years_available), 
                        key="waterfall_year_slider"
                    ) - 1
                    fig = create_waterfall_cashflow_chart(results_data, year_index)
                    if fig: st.plotly_chart(fig, use_container_width=True)
                    
            with tabs[1]:  # Revenus
                fig = create_annual_revenue_breakdown_chart(results_data)
                if fig: st.plotly_chart(fig, use_container_width=True)
                
            with tabs[2]:  # Dette
                fig = create_debt_balance_chart(results_data)
                if fig: st.plotly_chart(fig, use_container_width=True)
                
            with tabs[3]:  # Profils
                fig, suggestions = create_daily_pattern_chart(results=results_data)
                if fig: st.plotly_chart(fig, use_container_width=True)
                if suggestions:
                    st.markdown("### 💡 Suggestions")
                    for s in suggestions:
                        st.markdown(f"- {s}")
                        
            with tabs[4]:  # LCOE
                if 'analysis_engine_instance' in st.session_state:
                    display_lcoe_analysis_section(
                        st.session_state.analysis_engine_instance,
                        st.session_state.config,
                        st.session_state.get('sites_config', {}),
                        st.session_state.get('scenarios', [])
                    )
                else:
                    st.warning("Moteur d'analyse non disponible pour l'analyse LCOE.")
                    
            with tabs[5]:  # Monte Carlo
                if mc_results:
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        fig = create_monte_carlo_results_chart(mc_results)
                        if fig: st.plotly_chart(fig, use_container_width=True)
                    with col2:
                        fig = create_monte_carlo_boxplot(mc_results)
                        if fig: st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Aucun résultat Monte Carlo disponible.")
                    
            with tabs[6]:  # Sensibilité
                display_sensitivity_analysis_section(st.session_state.selected_scenario_visu)
    
    def _show_analysis_view(self, results_data: Dict[str, Any], mc_results: Optional[Dict[str, Any]]):
        """Affiche la vue analyses avancées"""
        
        st.markdown("### 🔍 Analyses Avancées")
        
        analysis_type = st.selectbox(
            "Type d'analyse",
            options=['breakeven', 'sensitivity', 'scenario_comparison', 'optimization'],
            format_func=lambda x: {
                'breakeven': "🎯 Analyse Breakeven",
                'sensitivity': "📊 Analyse de Sensibilité",
                'scenario_comparison': "⚖️ Comparaison de Scénarios",
                'optimization': "🎛️ Optimisation Avancée"
            }.get(x, x)
        )
        
        if analysis_type == 'breakeven':
            display_breakeven_analysis_ui(
                results_data,
                st.session_state.config,
                st.session_state.get('analysis_engine_instance')
            )
            
        elif analysis_type == 'sensitivity':
            # Interface de sensibilité avancée
            st.markdown("#### Paramètres de Sensibilité")
            
            col1, col2 = st.columns(2)
            with col1:
                params_to_test = st.multiselect(
                    "Paramètres à tester",
                    options=['capex', 'opex', 'tarif_achat', 'taux_actualisation', 'prix_elec'],
                    default=['capex', 'tarif_achat']
                )
                
            with col2:
                variation_range = st.slider(
                    "Plage de variation (%)",
                    min_value=10,
                    max_value=50,
                    value=20,
                    step=5
                )
                
            if st.button("Lancer l'analyse", type="primary"):
                # TODO: Implémenter l'analyse de sensibilité
                st.info("Analyse de sensibilité en cours de développement...")
                
        elif analysis_type == 'scenario_comparison':
            # Comparaison multi-scénarios
            available_scenarios = list(st.session_state.constrained_optim_results.keys())
            
            scenarios_to_compare = st.multiselect(
                "Scénarios à comparer",
                options=available_scenarios,
                default=available_scenarios[:2] if len(available_scenarios) >= 2 else available_scenarios
            )
            
            if len(scenarios_to_compare) >= 2:
                # TODO: Implémenter la comparaison
                st.info("Comparaison de scénarios en cours de développement...")
            else:
                st.warning("Sélectionnez au moins 2 scénarios pour la comparaison.")
                
        elif analysis_type == 'optimization':
            st.info("Module d'optimisation avancée en cours de développement...")