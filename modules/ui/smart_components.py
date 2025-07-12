"""
Composants UI intelligents et contextuels pour OptimPV
Adaptation automatique selon le profil utilisateur
"""
import streamlit as st
import plotly.graph_objects as go
from typing import Any, Dict, List, Optional, Union, Callable
import pandas as pd
from datetime import datetime
from .user_profile_manager import profile_manager, UserType

class SmartComponents:
    """Composants UI qui s'adaptent au contexte utilisateur"""
    
    @staticmethod
    def render_contextual_metric(
        metric_key: str,
        value: Union[float, int, str],
        previous_value: Optional[Union[float, int]] = None,
        format_type: str = "number",
        help_text: Optional[str] = None,
        **kwargs
    ):
        """
        Affiche une métrique adaptée au profil utilisateur
        
        Args:
            metric_key: Clé de la métrique (npv, tri, etc.)
            value: Valeur à afficher
            previous_value: Valeur précédente pour delta
            format_type: Type de formatage (number, currency, percentage)
            help_text: Texte d'aide contextuel
        """
        # Obtenir la terminologie adaptée
        label = profile_manager.get_terminology(metric_key)
        user_type = profile_manager.get_user_type()
        
        # Formatage selon le type
        if format_type == "currency":
            if isinstance(value, (int, float)):
                formatted_value = f"{value:,.0f} €"
            else:
                formatted_value = value
        elif format_type == "percentage":
            if isinstance(value, (int, float)):
                formatted_value = f"{value:.1f}%"
            else:
                formatted_value = value
        else:
            if isinstance(value, (int, float)):
                formatted_value = f"{value:,.0f}"
            else:
                formatted_value = value
                
        # Calcul du delta si valeur précédente fournie
        delta = None
        delta_color = "normal"
        if previous_value is not None and isinstance(value, (int, float)):
            delta_val = value - previous_value
            if format_type == "currency":
                delta = f"{delta_val:+,.0f} €"
            elif format_type == "percentage":
                delta = f"{delta_val:+.1f}%"
            else:
                delta = f"{delta_val:+,.0f}"
            delta_color = "normal" if delta_val >= 0 else "inverse"
            
        # Adaptation du help text selon le profil
        if not help_text:
            help_texts = {
                UserType.CLIENT: {
                    "npv": "Vos gains totaux sur la durée du projet",
                    "tri": "La rentabilité de votre investissement",
                    "payback": "Le temps nécessaire pour récupérer votre investissement",
                    "economie_mensuelle": "Vos économies moyennes chaque mois"
                },
                UserType.INVESTOR: {
                    "npv": "Valeur Actualisée Nette du projet",
                    "tri": "Taux de Rendement Interne attendu",
                    "payback": "Période de récupération du capital investi",
                    "lcoe": "Coût actualisé de l'énergie produite"
                }
            }
            
            if user_type in help_texts and metric_key in help_texts[user_type]:
                help_text = help_texts[user_type][metric_key]
                
        # Rendu de la métrique
        st.metric(
            label=label,
            value=formatted_value,
            delta=delta,
            delta_color=delta_color,
            help=help_text,
            **kwargs
        )
        
    @staticmethod
    def render_responsive_chart(
        chart_func: Callable,
        data: pd.DataFrame,
        title: str,
        chart_type: str = "line",
        height: Optional[int] = None,
        **kwargs
    ):
        """
        Affiche un graphique responsive adapté au device
        
        Args:
            chart_func: Fonction de création du graphique
            data: Données du graphique
            title: Titre du graphique
            chart_type: Type de graphique
            height: Hauteur (auto-adaptée si None)
        """
        # Détection du mode mobile (approximatif)
        is_mobile = st.session_state.get('is_mobile', False)
        
        # Adapter la hauteur
        if height is None:
            height = 300 if is_mobile else 450
            
        # Adapter le titre selon le profil
        user_type = profile_manager.get_user_type()
        if user_type == UserType.CLIENT:
            # Titre plus simple pour les clients
            title = title.replace("Cash-flow", "Économies mensuelles")
            title = title.replace("NPV", "Gains totaux")
            
        # Container avec options d'export contextuelles
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.subheader(title)
                
            with col2:
                # Options d'export selon le profil
                if profile_manager.should_show_advanced_features():
                    export_format = st.selectbox(
                        "Export",
                        ["PNG", "SVG", "Excel", "CSV"],
                        key=f"export_{title}",
                        label_visibility="collapsed"
                    )
                else:
                    if st.button("📥", key=f"export_{title}", help="Exporter"):
                        st.info("Export en PNG")
                        
            # Affichage du graphique
            fig = chart_func(data, **kwargs)
            
            # Configuration responsive
            fig.update_layout(
                height=height,
                margin=dict(l=20, r=20, t=40, b=20) if is_mobile else dict(l=50, r=50, t=50, b=50),
                showlegend=not is_mobile or chart_type != "line",
                title_font_size=14 if is_mobile else 16
            )
            
            # Mode sombre si préférence
            if st.session_state.get('theme_preference') == 'dark':
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
            st.plotly_chart(fig, use_container_width=True)
            
    @staticmethod
    def render_guided_empty_state(
        context: str,
        user_type: Optional[UserType] = None
    ):
        """
        Affiche un état vide avec guidage utilisateur
        
        Args:
            context: Contexte de l'état vide (no_data, no_analysis, etc.)
            user_type: Type d'utilisateur (auto-détecté si None)
        """
        if user_type is None:
            user_type = profile_manager.get_user_type()
            
        # Configurations par contexte et type d'utilisateur
        empty_states = {
            "no_data": {
                UserType.CLIENT: {
                    "icon": "📊",
                    "title": "Aucune donnée disponible",
                    "message": "Pour voir vos économies, nous avons besoin de vos données de consommation.",
                    "actions": [
                        ("📤 Importer mes données", "data_import"),
                        ("🎮 Voir une démo", "demo")
                    ]
                },
                UserType.INVESTOR: {
                    "icon": "📈",
                    "title": "Données requises",
                    "message": "Importez les données de production et consommation pour l'analyse financière.",
                    "actions": [
                        ("📤 Import Excel/CSV", "data_import"),
                        ("📋 Utiliser template", "template"),
                        ("🎲 Données exemple", "sample_data")
                    ]
                }
            },
            "no_analysis": {
                UserType.CLIENT: {
                    "icon": "🔍",
                    "title": "Analyse non effectuée",
                    "message": "Lancez l'analyse pour découvrir vos économies potentielles.",
                    "actions": [
                        ("🚀 Lancer l'analyse", "run_analysis"),
                        ("❓ Comment ça marche ?", "help")
                    ]
                },
                UserType.INVESTOR: {
                    "icon": "💡",
                    "title": "Optimisation requise",
                    "message": "Exécutez l'optimisation pour obtenir les indicateurs financiers.",
                    "actions": [
                        ("🎯 Optimiser", "optimize"),
                        ("⚙️ Configurer paramètres", "config"),
                        ("📊 Analyse rapide", "quick_analysis")
                    ]
                }
            }
        }
        
        # Obtenir la configuration
        config = empty_states.get(context, {}).get(user_type, {
            "icon": "ℹ️",
            "title": "Information",
            "message": "Cette section nécessite une action.",
            "actions": []
        })
        
        # Rendu de l'état vide
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 2rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">
                    {config['icon']}
                </div>
                <h3>{config['title']}</h3>
                <p style="color: #666; margin-bottom: 2rem;">
                    {config['message']}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Actions suggérées
            if config['actions']:
                cols = st.columns(len(config['actions']))
                for idx, (label, action_key) in enumerate(config['actions']):
                    with cols[idx]:
                        if st.button(
                            label,
                            key=f"empty_action_{action_key}",
                            use_container_width=True,
                            type="primary" if idx == 0 else "secondary"
                        ):
                            # Handler pour l'action
                            SmartComponents._handle_empty_state_action(action_key)
                            
    @staticmethod
    def _handle_empty_state_action(action_key: str):
        """Gère les actions des états vides"""
        action_handlers = {
            "data_import": lambda: st.session_state.update({"current_page": "Importation Données"}),
            "demo": lambda: st.session_state.update({"current_page": "demo"}),
            "run_analysis": lambda: st.session_state.update({"current_page": "Analyse & Optimisation"}),
            "optimize": lambda: st.session_state.update({"run_optimization": True}),
            "help": lambda: st.session_state.update({"show_help": True})
        }
        
        if action_key in action_handlers:
            action_handlers[action_key]()
            st.rerun()
            
    @staticmethod
    def render_info_tooltip(
        text: str,
        tooltip: str,
        user_type: Optional[UserType] = None
    ):
        """
        Affiche un texte avec tooltip adapté au niveau utilisateur
        
        Args:
            text: Texte principal
            tooltip: Texte du tooltip
            user_type: Type d'utilisateur
        """
        if user_type is None:
            user_type = profile_manager.get_user_type()
            
        # Adapter le tooltip selon le profil
        if user_type == UserType.CLIENT:
            # Simplifier les termes techniques
            tooltip = tooltip.replace("NPV", "gains totaux")
            tooltip = tooltip.replace("TRI", "rentabilité")
            tooltip = tooltip.replace("LCOE", "coût de l'énergie")
            
        # Utilisation du help de Streamlit
        st.markdown(f"{text} ℹ️", help=tooltip)
        
    @staticmethod
    def render_comparison_selector(
        scenarios: List[str],
        default_selection: Optional[List[str]] = None,
        max_selection: int = 3
    ):
        """
        Sélecteur de scénarios pour comparaison
        
        Args:
            scenarios: Liste des scénarios disponibles
            default_selection: Sélection par défaut
            max_selection: Nombre max de sélections
        """
        user_type = profile_manager.get_user_type()
        
        if user_type == UserType.CLIENT:
            # Interface simplifiée pour les clients
            st.markdown("### 📊 Comparer les options")
            
            selected = st.multiselect(
                "Sélectionnez les options à comparer :",
                scenarios,
                default=default_selection or scenarios[:2],
                max_selections=max_selection,
                help="Comparez jusqu'à 3 options différentes"
            )
        else:
            # Interface avancée pour investisseurs
            col1, col2 = st.columns([3, 1])
            
            with col1:
                selected = st.multiselect(
                    "Scénarios à comparer :",
                    scenarios,
                    default=default_selection or scenarios[:3],
                    max_selections=max_selection
                )
                
            with col2:
                # Options de comparaison avancées
                comparison_mode = st.radio(
                    "Mode",
                    ["Absolu", "Relatif", "Delta"],
                    help="Mode de comparaison des valeurs"
                )
                
        return selected
        
    @staticmethod
    def render_period_selector(
        default_period: str = "year",
        show_custom: bool = True
    ):
        """
        Sélecteur de période adapté au profil
        
        Args:
            default_period: Période par défaut
            show_custom: Afficher l'option personnalisée
        """
        user_type = profile_manager.get_user_type()
        
        if user_type == UserType.CLIENT:
            # Options simplifiées
            period = st.select_slider(
                "Période :",
                options=["Mois", "Année", "Total"],
                value="Année"
            )
            
            period_map = {"Mois": "month", "Année": "year", "Total": "total"}
            return period_map[period]
        else:
            # Options avancées
            col1, col2 = st.columns([2, 1])
            
            with col1:
                period = st.selectbox(
                    "Période d'analyse :",
                    ["Journalier", "Mensuel", "Trimestriel", "Annuel", "Total"] + 
                    (["Personnalisé"] if show_custom else []),
                    index=3  # Annuel par défaut
                )
                
            with col2:
                if period == "Personnalisé":
                    date_range = st.date_input(
                        "Plage de dates",
                        value=(datetime.now().date(), datetime.now().date()),
                        key="custom_period"
                    )
                    
            return period.lower()

# Instance globale
smart_components = SmartComponents()