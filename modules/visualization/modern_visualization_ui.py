"""
Interface de visualisation moderne avec tous les nouveaux composants
"""
import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import plotly.graph_objects as go

# Import des nouveaux composants
from .styles.themes.theme_manager import theme_manager
from .ui.theme_selector import render_theme_selector, render_theme_toggle_mini
from .ui.cards.modern_cards import (
    render_metric_card, 
    render_info_card,
    render_stat_cards_row,
    render_chart_card
)
from .ui.buttons.animated_buttons import (
    render_animated_button,
    render_button_group,
    render_floating_action_button
)
from .charts.interactive.advanced_charts import (
    InteractiveChartManager,
    create_animated_time_series,
    create_realtime_chart_placeholder
)
from .charts.advanced.energy_flow_charts import (
    create_energy_sankey_diagram,
    create_consumption_heatmap,
    create_3d_surface_analysis,
    create_radar_comparison_chart,
    create_gantt_installation_chart,
    create_network_energy_flow
)
from .components.dashboard.customizable_dashboard import (
    CustomizableDashboard,
    WidgetType,
    WidgetConfig
)
from .styles.animations.animation_system import animation_system

# Import des modules existants pour compatibilité
from .main_visualization_ui import VisualizationModule

class ModernVisualizationUI:
    """Interface de visualisation moderne avec fonctionnalités avancées
    
    N'hérite plus de VisualizationModule pour éviter les conflits de sidebar
    """
    
    def __init__(self):
        """Initialise l'interface moderne"""
        # Plus d'appel à super() car on n'hérite plus de VisualizationModule
        
        # Marquer cette instance comme interface moderne
        self.is_modern_ui = True
        
        # Initialiser les attributs de données
        self.config = {}
        self.scenarios = {}
        self.sites_data = {}
        self.economic_results = {}
        self.optimization_results = {}
        self.monte_carlo_results = {}
        self.floor_price_results = {}
        
        # Initialiser le thème
        theme_manager.apply_theme_css()
        
        # Initialiser les animations
        animation_system.create_transition_classes()
        
        # État pour le mode moderne
        if 'modern_ui_enabled' not in st.session_state:
            st.session_state.modern_ui_enabled = True
            
        # Dashboard personnalisable
        self.dashboard = None
        
        # Instance de l'ancienne interface pour réutiliser certains composants
        self._classic_module = VisualizationModule()
    
    def show_ui(self, **kwargs):
        """Interface principale modernisée
        
        Args:
            **kwargs: Paramètres optionnels incluant:
                - config: Configuration du projet
                - scenarios: Scénarios disponibles
                - sites_data: Données des sites
                - economic_results: Résultats économiques
                - optimization_results: Résultats d'optimisation
                - monte_carlo_results: Résultats Monte Carlo
                - floor_price_results: Résultats prix plancher
        """
        # Stocker les données passées en paramètres
        self.config = kwargs.get('config', st.session_state.get('config', {}))
        self.scenarios = kwargs.get('scenarios', st.session_state.get('scenarios', {}))
        self.sites_data = kwargs.get('sites_data', st.session_state.get('sites_data', {}))
        self.economic_results = kwargs.get('economic_results', st.session_state.get('economic_results', {}))
        self.optimization_results = kwargs.get('optimization_results', st.session_state.get('optimization_results', {}))
        self.monte_carlo_results = kwargs.get('monte_carlo_results', st.session_state.get('monte_carlo_results', {}))
        self.floor_price_results = kwargs.get('floor_price_results', st.session_state.get('floor_price_results', {}))
        
        # Header moderne avec animations
        self._render_modern_header()
        
        # Navigation et filtres directement dans la page principale
        st.markdown("---")
        
        # Navigation en tabs horizontaux
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("📊 Dashboard", use_container_width=True, type="primary" if st.session_state.get('view_mode', 'dashboard') == 'dashboard' else "secondary"):
                st.session_state.view_mode = 'dashboard'
                st.rerun()
        with col2:
            if st.button("📈 Analytics", use_container_width=True, type="primary" if st.session_state.get('view_mode', 'dashboard') == 'analytics' else "secondary"):
                st.session_state.view_mode = 'analytics'
                st.rerun()
        with col3:
            if st.button("📑 Rapports", use_container_width=True, type="primary" if st.session_state.get('view_mode', 'dashboard') == 'reports' else "secondary"):
                st.session_state.view_mode = 'reports'
                st.rerun()
        with col4:
            if st.button("🔧 Classique", use_container_width=True, type="primary" if st.session_state.get('view_mode', 'dashboard') == 'classic' else "secondary"):
                st.session_state.view_mode = 'classic'
                st.rerun()
        
        # Filtres en ligne sous la navigation
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            
            with col1:
                # Sélection du scénario
                if hasattr(st.session_state, 'scenarios') and st.session_state.scenarios:
                    st.selectbox(
                        "📊 Scénario",
                        options=list(st.session_state.scenarios.keys()),
                        key="selected_scenario_visu"
                    )
            
            with col2:
                # Type d'utilisateur
                st.radio(
                    "👤 Type d'utilisateur",
                    options=['Client', 'Investisseur'],
                    horizontal=True,
                    key="user_type_visu"
                )
            
            with col3:
                # Période simplifiée
                st.selectbox(
                    "📅 Période",
                    options=['Toute la durée', 'Dernière année', 'Derniers 6 mois', 'Dernier mois'],
                    key="period_filter"
                )
            
            with col4:
                # Sélecteur de thème
                render_theme_toggle_mini()
        
        st.markdown("---")
        
        # Initialiser view_mode si nécessaire
        if 'view_mode' not in st.session_state:
            st.session_state.view_mode = 'dashboard'
        
        # Vérification des données
        if not self._check_data_availability():
            self._render_empty_state()
            return
        
        # Mode d'affichage
        if st.session_state.view_mode == 'dashboard':
            self._render_modern_dashboard()
        elif st.session_state.view_mode == 'analytics':
            self._render_advanced_analytics()
        elif st.session_state.view_mode == 'reports':
            self._render_reports_section()
        else:
            # Mode classique - NE PAS appeler super().show_ui() pour éviter la double sidebar
            self._render_classic_mode()
    
    def _render_modern_header(self):
        """Affiche le header moderne avec animations"""
        # Container avec animation
        header_container = st.container()
        
        with header_container:
            # Animation d'entrée
            animation_system.animate_element(
                "header-main",
                "fadeInDown",
                duration=0.8
            )
            
            # Layout du header
            col1, col2, col3 = st.columns([2, 5, 1])
            
            with col1:
                # Logo/Titre avec gradient
                st.markdown("""
                <div class="header-main">
                    <h1 style="
                        background: var(--gradient);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        font-size: 2.5rem;
                        font-weight: 800;
                        margin: 0;
                    ">
                        OptimPV Pro
                    </h1>
                    <p style="color: var(--text-secondary); margin: 0;">
                        Visualisation Avancée
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Métriques principales avec animation
                if hasattr(st.session_state, 'constrained_optim_results'):
                    self._render_header_metrics()
            
            with col3:
                # Actions rapides
                render_animated_button(
                    "🔄",
                    on_click=st.rerun,
                    variant="ghost",
                    size="small",
                    tooltip="Actualiser",
                    animate=True
                )
    
    def _render_header_metrics(self):
        """Affiche les métriques principales dans le header"""
        # Récupérer les données du scénario actuel
        if not hasattr(st.session_state, 'selected_scenario_visu'):
            return
            
        scenario = st.session_state.selected_scenario_visu
        results = st.session_state.constrained_optim_results.get(scenario, {})
        indicators = results.get('indicateurs_au_prix_optimal', {})
        
        # Métriques à afficher
        metrics = [
            {
                'title': 'NPV',
                'value': f"{indicators.get('npv', 0):,.0f}€",
                'delta': f"+{indicators.get('npv', 0)/1000:.0f}k€",
                'icon': '💰',
                'gradient': True,
                'size': 'small'
            },
            {
                'title': 'TRI',
                'value': f"{indicators.get('tri', 0):.1%}",
                'delta': 'Excellent' if indicators.get('tri', 0) > 0.1 else 'Bon',
                'delta_color': 'normal',
                'icon': '📈',
                'gradient': True,
                'size': 'small'
            },
            {
                'title': 'LCOE',
                'value': f"{indicators.get('lcoe', 0):.3f}€/kWh",
                'icon': '⚡',
                'gradient': True,
                'size': 'small'
            }
        ]
        
        # Afficher en ligne avec animation décalée
        cols = st.columns(len(metrics))
        animation_system.stagger_animation(
            "header-metrics",
            ".metric-card",
            "fadeInUp",
            duration=0.5,
            stagger_delay=0.1
        )
        
        st.markdown('<div class="header-metrics" style="display: contents;">', unsafe_allow_html=True)
        
        for col, metric in zip(cols, metrics):
            with col:
                render_metric_card(**metric)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_modern_navigation(self):
        """Navigation moderne avec icônes et animations"""
        st.markdown("### 🧭 Navigation")
        
        # Options de navigation avec icônes
        nav_options = [
            ("dashboard", "📊 Tableau de Bord", "Vue d'ensemble interactive"),
            ("analytics", "📈 Analyses Avancées", "Graphiques et insights détaillés"),
            ("reports", "📄 Rapports", "Génération de rapports"),
            ("settings", "⚙️ Paramètres", "Configuration et personnalisation")
        ]
        
        # Rendu des boutons de navigation
        for key, label, help_text in nav_options:
            if render_animated_button(
                label,
                variant="ghost" if st.session_state.view_mode != key else "primary",
                full_width=True,
                icon_position="left",
                animate=True,
                key=f"nav_{key}"
            ):
                st.session_state.view_mode = key
                st.rerun()
    
    def _render_modern_dashboard(self):
        """Affiche le dashboard moderne personnalisable"""
        # Initialiser le dashboard si nécessaire
        if not self.dashboard:
            self.dashboard = CustomizableDashboard(
                "main_dashboard",
                default_layout=self._get_default_dashboard_layout()
            )
        
        # Sélection du scénario avec style moderne
        scenario = self._render_scenario_selector()
        
        if not scenario:
            return
        
        # Récupérer les données
        results_data = self._get_scenario_data(scenario)
        
        if not results_data:
            st.warning("Aucune donnée disponible pour ce scénario")
            return
        
        # Définir les renderers pour chaque type de widget
        widget_renderers = {
            "metric": lambda config: self._render_metric_widget(config, results_data),
            "chart": lambda config: self._render_chart_widget(config, results_data),
            "table": lambda config: self._render_table_widget(config, results_data),
            "text": lambda config: self._render_text_widget(config),
            "custom": lambda config: self._render_custom_widget(config, results_data)
        }
        
        # Afficher le dashboard
        self.dashboard.render(widget_renderers)
    
    def _render_advanced_analytics(self):
        """Section analyses avancées avec nouveaux graphiques"""
        st.markdown("## 📊 Analyses Avancées")
        
        # Tabs pour différentes analyses
        tabs = st.tabs([
            "🌊 Flux Énergétiques",
            "🌡️ Heatmaps",
            "📊 Analyses 3D",
            "🎯 Comparaisons",
            "📅 Planning",
            "🔗 Réseau"
        ])
        
        # Récupérer les données
        scenario = st.session_state.get('selected_scenario_visu')
        if not scenario:
            st.warning("Sélectionnez un scénario")
            return
            
        results_data = self._get_scenario_data(scenario)
        
        with tabs[0]:  # Flux Énergétiques
            self._render_energy_flow_analysis(results_data)
            
        with tabs[1]:  # Heatmaps
            self._render_heatmap_analysis(results_data)
            
        with tabs[2]:  # Analyses 3D
            self._render_3d_analysis(results_data)
            
        with tabs[3]:  # Comparaisons
            self._render_comparison_analysis()
            
        with tabs[4]:  # Planning
            self._render_gantt_planning()
            
        with tabs[5]:  # Réseau
            self._render_network_analysis(results_data)
    
    def _render_energy_flow_analysis(self, results_data: Dict[str, Any]):
        """Analyse des flux énergétiques avec Sankey"""
        st.markdown("### 🌊 Flux Énergétiques")
        
        # Préparer les données pour le Sankey
        monthly_data = results_data.get('monthly_data', pd.DataFrame())
        
        if not monthly_data.empty:
            # Calculer les flux annuels
            total_production = monthly_data['production_kWh'].sum()
            total_autoconso = monthly_data['autoconsommation_kWh'].sum()
            total_injection = monthly_data['injection_reseau_kWh'].sum()
            total_soutirage = monthly_data['soutirage_reseau_kWh'].sum()
            total_conso = monthly_data['consommation_totale_kWh'].sum()
            
            # Créer le diagramme Sankey
            energy_flows = {
                'source': [0, 1, 0, 2, 3],  # Production PV, Réseau, PV, Autoconso, Soutirage
                'target': [2, 3, 4, 5, 5],  # Autoconso, Soutirage, Injection, Consommation
                'value': [
                    total_autoconso,
                    total_soutirage,
                    total_injection,
                    total_autoconso,
                    total_soutirage
                ],
                'labels': [
                    'Production PV',
                    'Réseau',
                    'Autoconsommation',
                    'Soutirage réseau',
                    'Injection réseau',
                    'Consommation totale'
                ]
            }
            
            fig = create_energy_sankey_diagram(
                energy_flows,
                title="Flux Énergétiques Annuels",
                height=600
            )
            
            render_chart_card(
                "Diagramme de Sankey",
                fig,
                "Visualisation des flux d'énergie entre production, consommation et réseau",
                glass=True
            )
    
    def _render_heatmap_analysis(self, results_data: Dict[str, Any]):
        """Analyse avec heatmaps temporelles"""
        st.markdown("### 🌡️ Cartes de Chaleur Temporelles")
        
        monthly_data = results_data.get('monthly_data', pd.DataFrame())
        
        if not monthly_data.empty:
            # Sélection du type de heatmap
            heatmap_type = st.selectbox(
                "Type d'analyse",
                ["Consommation horaire", "Production journalière", "Autoconsommation hebdomadaire"]
            )
            
            # Créer des données simulées pour la démo (à remplacer par vraies données)
            if 'timestamp' not in monthly_data.columns:
                monthly_data['timestamp'] = pd.date_range(
                    start='2024-01-01',
                    periods=len(monthly_data),
                    freq='h'
                )
            
            if heatmap_type == "Consommation horaire":
                fig = create_consumption_heatmap(
                    monthly_data,
                    'timestamp',
                    'consommation_totale_kWh',
                    title="Profil de Consommation Horaire",
                    aggregation="hourly"
                )
            elif heatmap_type == "Production journalière":
                fig = create_consumption_heatmap(
                    monthly_data,
                    'timestamp',
                    'production_kWh',
                    title="Production PV par Jour",
                    aggregation="daily",
                    colorscale="Viridis"
                )
            else:
                fig = create_consumption_heatmap(
                    monthly_data,
                    'timestamp',
                    'autoconsommation_kWh',
                    title="Autoconsommation Hebdomadaire",
                    aggregation="weekly",
                    colorscale="Blues"
                )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_3d_analysis(self, results_data: Dict[str, Any]):
        """Analyses 3D multi-paramètres"""
        st.markdown("### 📊 Analyses 3D Multi-Paramètres")
        
        # Créer des données d'exemple pour la surface 3D
        # (À remplacer par les vraies données d'optimisation)
        x = np.linspace(10, 100, 20)  # Puissance kWc
        y = np.linspace(0.1, 0.3, 20)  # Prix kWh
        X, Y = np.meshgrid(x, y)
        Z = 50000 * X * Y - 1000 * X  # NPV simulée
        
        # Créer DataFrame
        data_3d = []
        for i in range(len(x)):
            for j in range(len(y)):
                data_3d.append({
                    'Puissance_kWc': X[j, i],
                    'Prix_kWh': Y[j, i],
                    'NPV': Z[j, i]
                })
        
        df_3d = pd.DataFrame(data_3d)
        
        fig = create_3d_surface_analysis(
            df_3d,
            'Puissance_kWc',
            'Prix_kWh',
            'NPV',
            title="Surface d'Optimisation NPV",
            colorscale="RdYlGn"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_comparison_analysis(self):
        """Comparaisons multi-critères avec radar charts"""
        st.markdown("### 🎯 Comparaisons Multi-Critères")
        
        # Sélection des scénarios à comparer
        available_scenarios = list(st.session_state.constrained_optim_results.keys())
        
        selected_scenarios = st.multiselect(
            "Scénarios à comparer",
            available_scenarios,
            default=available_scenarios[:2] if len(available_scenarios) >= 2 else available_scenarios
        )
        
        if len(selected_scenarios) >= 2:
            # Préparer les données pour le radar
            categories = ['Rentabilité', 'Autonomie', 'Impact CO2', 'Résilience', 'Performance']
            datasets = []
            
            for scenario in selected_scenarios:
                results = st.session_state.constrained_optim_results[scenario]
                indicators = results.get('indicateurs_au_prix_optimal', {})
                
                # Normaliser les valeurs entre 0 et 100
                values = [
                    min(100, indicators.get('tri', 0) * 500),  # TRI
                    indicators.get('taux_autoconsommation', 0) * 100,  # Autonomie
                    min(100, indicators.get('emissions_evitees_tonnes', 0) * 10),  # CO2
                    min(100, indicators.get('dscr_moyen', 1) * 50),  # Résilience
                    min(100, indicators.get('lcoe', 0.2) * 200)  # Performance (inversé)
                ]
                
                datasets.append({
                    'name': scenario,
                    'values': values
                })
            
            fig = create_radar_comparison_chart(
                categories,
                datasets,
                title="Comparaison Multi-Critères des Scénarios"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_gantt_planning(self):
        """Planning d'installation avec Gantt"""
        st.markdown("### 📅 Planning d'Installation")
        
        # Tâches d'exemple pour le Gantt
        tasks = [
            {
                'name': 'Étude de faisabilité',
                'start': '2024-01-15',
                'end': '2024-02-01',
                'resource': 'Technicien'
            },
            {
                'name': 'Obtention permis',
                'start': '2024-02-01',
                'end': '2024-03-15',
                'resource': 'Autre'
            },
            {
                'name': 'Installation structure',
                'start': '2024-03-15',
                'end': '2024-03-25',
                'resource': 'Installateur'
            },
            {
                'name': 'Pose panneaux',
                'start': '2024-03-25',
                'end': '2024-04-05',
                'resource': 'Installateur'
            },
            {
                'name': 'Raccordement électrique',
                'start': '2024-04-05',
                'end': '2024-04-15',
                'resource': 'Électricien'
            },
            {
                'name': 'Mise en service',
                'start': '2024-04-15',
                'end': '2024-04-20',
                'resource': 'Technicien'
            }
        ]
        
        fig = create_gantt_installation_chart(
            tasks,
            title="Planning Prévisionnel d'Installation"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_network_analysis(self, results_data: Dict[str, Any]):
        """Analyse du réseau de distribution"""
        st.markdown("### 🔗 Réseau de Distribution Énergétique")
        
        # Créer un réseau d'exemple
        nodes = [
            {'id': 'pv', 'label': 'Panneaux PV', 'x': 0, 'y': 1, 'type': 'source', 'size': 30},
            {'id': 'onduleur', 'label': 'Onduleur', 'x': 1, 'y': 1, 'type': 'grid', 'size': 25},
            {'id': 'batterie', 'label': 'Batterie', 'x': 1, 'y': 0, 'type': 'storage', 'size': 20},
            {'id': 'reseau', 'label': 'Réseau', 'x': 2, 'y': 2, 'type': 'grid', 'size': 25},
            {'id': 'maison', 'label': 'Habitation', 'x': 2, 'y': 1, 'type': 'consumer', 'size': 30},
            {'id': 'ev', 'label': 'Véhicule électrique', 'x': 2, 'y': 0, 'type': 'consumer', 'size': 20}
        ]
        
        # Flux d'énergie
        edges = [
            {'source': 'pv', 'target': 'onduleur', 'value': 5000},
            {'source': 'onduleur', 'target': 'maison', 'value': 3000},
            {'source': 'onduleur', 'target': 'batterie', 'value': 1000},
            {'source': 'onduleur', 'target': 'reseau', 'value': 1000},
            {'source': 'batterie', 'target': 'maison', 'value': 500},
            {'source': 'batterie', 'target': 'ev', 'value': 300},
            {'source': 'reseau', 'target': 'maison', 'value': 1500}
        ]
        
        fig = create_network_energy_flow(
            nodes,
            edges,
            title="Réseau de Distribution en Temps Réel"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Méthodes utilitaires
    def _check_data_availability(self) -> bool:
        """Vérifie la disponibilité des données"""
        return (
            hasattr(st.session_state, 'constrained_optim_results') and 
            st.session_state.constrained_optim_results
        )
    
    def _render_empty_state(self):
        """Affiche l'état vide avec call-to-action"""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style="
                text-align: center;
                padding: 4rem 2rem;
                background: var(--surface);
                border-radius: 16px;
                margin-top: 2rem;
            ">
                <h2 style="color: var(--text-primary); margin-bottom: 1rem;">
                    📊 Aucune donnée disponible
                </h2>
                <p style="color: var(--text-secondary); margin-bottom: 2rem;">
                    Lancez d'abord une optimisation pour accéder aux visualisations
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if render_animated_button(
                "🚀 Lancer l'optimisation",
                variant="gradient",
                size="large",
                full_width=True,
                animate=True,
                glow=True
            ):
                st.session_state.page = "optimization"  # Rediriger vers la page d'optimisation
                st.rerun()
    
    def _render_scenario_selector(self) -> Optional[str]:
        """Sélecteur de scénario moderne"""
        available_scenarios = list(st.session_state.constrained_optim_results.keys())
        
        if not available_scenarios:
            return None
        
        # Container avec style
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                selected_scenario = st.selectbox(
                    "📊 Scénario",
                    options=available_scenarios,
                    index=available_scenarios.index(st.session_state.get('selected_scenario_visu', available_scenarios[0])),
                    key="modern_scenario_select"
                )
                st.session_state.selected_scenario_visu = selected_scenario
            
            with col2:
                render_animated_button(
                    "Comparer",
                    icon="⚖️",
                    variant="secondary",
                    size="small",
                    full_width=True
                )
            
            with col3:
                render_animated_button(
                    "Exporter",
                    icon="📤",
                    variant="secondary",
                    size="small",
                    full_width=True
                )
        
        return selected_scenario
    
    def _get_scenario_data(self, scenario: str) -> Optional[Dict[str, Any]]:
        """Récupère les données d'un scénario"""
        optim_results = st.session_state.constrained_optim_results.get(scenario, {})
        return optim_results.get('indicateurs_au_prix_optimal')
    
    def _get_default_dashboard_layout(self) -> List[WidgetConfig]:
        """Retourne le layout par défaut du dashboard"""
        return [
            WidgetConfig(
                id="metric_npv",
                type=WidgetType.METRIC,
                title="NPV",
                position={"x": 1, "y": 1, "w": 3, "h": 2},
                config={"metric": "npv", "format": "currency"}
            ),
            WidgetConfig(
                id="metric_tri",
                type=WidgetType.METRIC,
                title="TRI",
                position={"x": 4, "y": 1, "w": 3, "h": 2},
                config={"metric": "tri", "format": "percentage"}
            ),
            WidgetConfig(
                id="metric_lcoe",
                type=WidgetType.METRIC,
                title="LCOE",
                position={"x": 7, "y": 1, "w": 3, "h": 2},
                config={"metric": "lcoe", "format": "currency_per_unit"}
            ),
            WidgetConfig(
                id="metric_payback",
                type=WidgetType.METRIC,
                title="Payback",
                position={"x": 10, "y": 1, "w": 3, "h": 2},
                config={"metric": "payback", "format": "years"}
            ),
            WidgetConfig(
                id="chart_production",
                type=WidgetType.CHART,
                title="Production & Consommation",
                position={"x": 1, "y": 3, "w": 6, "h": 4},
                config={"chart_type": "line", "series": ["production", "consommation"]}
            ),
            WidgetConfig(
                id="chart_financial",
                type=WidgetType.CHART,
                title="Flux Financiers",
                position={"x": 7, "y": 3, "w": 6, "h": 4},
                config={"chart_type": "waterfall", "metric": "cashflow"}
            )
        ]
    
    # Méthodes de rendu des widgets
    def _render_metric_widget(self, config: WidgetConfig, data: Dict[str, Any]):
        """Rendu d'un widget métrique"""
        metric_key = config.config.get('metric')
        format_type = config.config.get('format', 'number')
        
        value = data.get(metric_key, 0)
        
        # Formatage selon le type
        if format_type == 'currency':
            formatted_value = f"{value:,.0f}€"
        elif format_type == 'percentage':
            formatted_value = f"{value:.1%}"
        elif format_type == 'currency_per_unit':
            formatted_value = f"{value:.3f}€/kWh"
        elif format_type == 'years':
            formatted_value = f"{value:.1f} ans"
        else:
            formatted_value = f"{value:,.0f}"
        
        render_metric_card(
            title=config.title,
            value=formatted_value,
            gradient=True,
            animate=True
        )
    
    def _render_chart_widget(self, config: WidgetConfig, data: Dict[str, Any]):
        """Rendu d'un widget graphique"""
        chart_type = config.config.get('chart_type', 'line')
        
        # Créer un graphique selon le type
        # (Implémentation simplifiée, à étendre selon les besoins)
        fig = go.Figure()
        
        if chart_type == 'line' and 'monthly_data' in data:
            monthly_data = data['monthly_data']
            for series in config.config.get('series', []):
                if series in monthly_data.columns:
                    fig.add_trace(go.Scatter(
                        x=monthly_data.index,
                        y=monthly_data[series],
                        name=series,
                        mode='lines'
                    ))
        
        # Appliquer le thème
        theme = theme_manager.get_plotly_theme()
        fig.update_layout(**theme['layout'])
        
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{config.id}")
    
    def _render_table_widget(self, config: WidgetConfig, data: Dict[str, Any]):
        """Rendu d'un widget tableau"""
        st.dataframe(
            data.get('monthly_data', pd.DataFrame()).head(10),
            use_container_width=True
        )
    
    def _render_text_widget(self, config: WidgetConfig):
        """Rendu d'un widget texte"""
        content = config.config.get('content', '')
        st.markdown(content)
    
    def _render_custom_widget(self, config: WidgetConfig, data: Dict[str, Any]):
        """Rendu d'un widget personnalisé"""
        st.info(f"Widget personnalisé: {config.title}")
    
    def _check_data_availability(self) -> bool:
        """Vérifie si des données sont disponibles pour l'affichage"""
        # Vérifier si nous avons des données dans la session
        has_data = (
            hasattr(st.session_state, 'constrained_optim_results') and 
            st.session_state.constrained_optim_results
        ) or (
            self.economic_results or 
            self.optimization_results
        )
        return has_data
    
    def _render_empty_state(self):
        """Affiche un état vide quand aucune donnée n'est disponible"""
        st.markdown("""
        <div style="text-align: center; padding: 50px;">
            <h2>📊 Aucune donnée à visualiser</h2>
            <p>Veuillez d'abord exécuter une analyse depuis l'onglet "Analyse & Optimisation"</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Ces méthodes ne sont plus nécessaires car tout est intégré dans show_ui()
    
    def _render_classic_mode(self):
        """Affiche l'interface classique en utilisant l'instance de VisualizationModule"""
        try:
            # Passer les données à l'instance classique
            self._classic_module.config = self.config
            self._classic_module.scenarios = self.scenarios
            self._classic_module.sites_data = self.sites_data
            self._classic_module.economic_results = self.economic_results
            self._classic_module.optimization_results = self.optimization_results
            self._classic_module.monte_carlo_results = self.monte_carlo_results
            self._classic_module.floor_price_results = self.floor_price_results
            
            # Appeler directement les méthodes de rendu sans la sidebar
            if hasattr(st.session_state, 'constrained_optim_results') and st.session_state.constrained_optim_results:
                # Mode investisseur par défaut pour l'interface classique
                from .investor.dashboard import display_investor_dashboard
                display_investor_dashboard()
            else:
                from .client.dashboard import display_client_dashboard
                display_client_dashboard()
        except Exception as e:
            st.error(f"Erreur lors du chargement de l'interface classique: {str(e)}")
            st.info("Essayez de sélectionner un autre mode d'affichage.")

# Export de la classe principale
__all__ = ['ModernVisualizationUI']