"""
Modern UI Components for PMO Billing System
Reusable components with modern styling and interactive features
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union
import json
import time


class UIComponents:
    """Modern UI components for the billing system"""
    
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize session state variables"""
        if 'notifications' not in st.session_state:
            st.session_state.notifications = []
        if 'loading_states' not in st.session_state:
            st.session_state.loading_states = {}
        if 'auto_save_data' not in st.session_state:
            st.session_state.auto_save_data = {}
    
    def create_sidebar_metrics(self, metrics: Dict[str, Union[str, int, float]]):
        """Create enhanced sidebar metrics with modern styling"""
        st.sidebar.markdown("### 📊 Aperçu Rapide")
        
        for label, value in metrics.items():
            # Create metric with custom styling
            if isinstance(value, (int, float)):
                delta = self._calculate_metric_delta(label, value)
                st.sidebar.metric(
                    label, 
                    value, 
                    delta=delta,
                    help=f"Métrique: {label}"
                )
            else:
                st.sidebar.metric(label, value)
    
    def _calculate_metric_delta(self, label: str, current_value: Union[int, float]) -> Optional[str]:
        """Calculate delta for metrics based on historical data"""
        # Simulate historical comparison (in real implementation, use actual data)
        if "Projets" in label:
            return "+1" if current_value > 0 else None
        elif "Participants" in label:
            return f"+{max(0, current_value - 5)}" if current_value > 5 else None
        elif "Statut" in label:
            return None
        return None
    
    def create_enhanced_navigation(self, options: Dict[str, Dict[str, Any]]) -> str:
        """Create enhanced navigation with badges and counters"""
        navigation_html = """
        <style>
        .nav-badge {
            background: #FF6B6B;
            color: white;
            border-radius: 10px;
            padding: 2px 6px;
            font-size: 10px;
            margin-left: 5px;
        }
        .nav-count {
            background: #4ECDC4;
            color: white;
            border-radius: 10px;
            padding: 2px 6px;
            font-size: 10px;
            margin-left: 5px;
        }
        .nav-new {
            background: #45B7D1;
            color: white;
            border-radius: 10px;
            padding: 2px 6px;
            font-size: 10px;
            margin-left: 5px;
        }
        </style>
        """
        st.sidebar.markdown(navigation_html, unsafe_allow_html=True)
        
        # Create option labels with badges
        enhanced_options = []
        for option, config in options.items():
            label = option
            
            if config.get('count', 0) > 0:
                label += f" <span class='nav-count'>{config['count']}</span>"
            
            if config.get('badge'):
                badge_class = {
                    'NEW': 'nav-new',
                    'BETA': 'nav-badge',
                    'SYNC': 'nav-count',
                    'INFO': 'nav-count'
                }.get(config['badge'], 'nav-badge')
                label += f" <span class='{badge_class}'>{config['badge']}</span>"
            
            enhanced_options.append(label)
        
        # Display selection with HTML formatting
        selected_index = st.sidebar.selectbox(
            "Choisir une section",
            range(len(enhanced_options)),
            format_func=lambda x: enhanced_options[x].replace('<span', '').split('>')[0].strip(),
            key="nav_selection"
        )
        
        return list(options.keys())[selected_index]
    
    def create_modern_card(self, title: str, content: str, icon: str = "📊", 
                          color: str = "blue", action_button: Optional[Dict] = None):
        """Create a modern card component"""
        # Color mapping
        color_map = {
            "blue": {"bg": "#E3F2FD", "border": "#2196F3", "text": "#0D47A1"},
            "green": {"bg": "#E8F5E8", "border": "#4CAF50", "text": "#1B5E20"},
            "orange": {"bg": "#FFF3E0", "border": "#FF9800", "text": "#E65100"},
            "red": {"bg": "#FFEBEE", "border": "#F44336", "text": "#B71C1C"},
            "purple": {"bg": "#F3E5F5", "border": "#9C27B0", "text": "#4A148C"}
        }
        
        colors = color_map.get(color, color_map["blue"])
        
        card_html = f"""
        <div style="
            background: {colors['bg']};
            border-left: 4px solid {colors['border']};
            padding: 1rem;
            border-radius: 8px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <h4 style="color: {colors['text']}; margin: 0 0 10px 0;">
                {icon} {title}
            </h4>
            <p style="color: {colors['text']}; margin: 0;">
                {content}
            </p>
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)
        
        if action_button:
            if st.button(action_button['label'], key=action_button.get('key')):
                return action_button.get('action', lambda: None)()
    
    def create_kpi_widget(self, title: str, value: Union[str, int, float], 
                         delta: Optional[str] = None, delta_color: str = "normal",
                         icon: str = "📊", help_text: Optional[str] = None,
                         trend_data: Optional[List[float]] = None):
        """Create an enhanced KPI widget with trend visualization"""
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.metric(
                label=f"{icon} {title}",
                value=value,
                delta=delta,
                delta_color=delta_color,
                help=help_text
            )
        
        with col2:
            if trend_data:
                # Create mini trend chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    y=trend_data,
                    mode='lines',
                    line=dict(color='#4ECDC4', width=2),
                    showlegend=False
                ))
                fig.update_layout(
                    height=60,
                    margin=dict(l=0, r=0, t=0, b=0),
                    xaxis=dict(showgrid=False, showticklabels=False),
                    yaxis=dict(showgrid=False, showticklabels=False),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def create_data_table_with_actions(self, data: pd.DataFrame, 
                                     actions: List[Dict[str, Any]] = None,
                                     selection_mode: str = "single",
                                     search_columns: List[str] = None) -> Dict[str, Any]:
        """Create an enhanced data table with search, filters, and actions"""
        
        result = {"selected_rows": [], "action_triggered": None}
        
        if data.empty:
            st.info("📝 Aucune donnée à afficher")
            return result
        
        # Search functionality
        if search_columns:
            col1, col2 = st.columns([2, 1])
            with col1:
                search_term = st.text_input("🔍 Rechercher", key="table_search")
            with col2:
                if st.button("🗑️ Effacer", key="clear_search"):
                    st.rerun()
            
            if search_term:
                mask = data[search_columns].astype(str).apply(
                    lambda x: x.str.contains(search_term, case=False, na=False)
                ).any(axis=1)
                data = data[mask]
        
        # Enhanced data editor
        if selection_mode == "multiple":
            # Add selection column
            data_with_selection = data.copy()
            data_with_selection.insert(0, "Sélectionner", False)
            
            edited_df = st.data_editor(
                data_with_selection,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Sélectionner": st.column_config.CheckboxColumn(
                        "Sélectionner",
                        help="Cocher pour sélectionner cette ligne",
                        default=False,
                    )
                },
                disabled=[col for col in data_with_selection.columns if col != "Sélectionner"]
            )
            
            # Get selected rows
            result["selected_rows"] = edited_df[edited_df["Sélectionner"]].index.tolist()
        else:
            st.dataframe(data, use_container_width=True)
        
        # Action buttons
        if actions:
            st.markdown("#### ⚡ Actions Disponibles")
            action_cols = st.columns(len(actions))
            
            for i, action in enumerate(actions):
                with action_cols[i]:
                    if st.button(
                        action['label'], 
                        key=action.get('key', f"action_{i}"),
                        type=action.get('type', 'secondary'),
                        disabled=action.get('disabled', False),
                        use_container_width=True
                    ):
                        result["action_triggered"] = action['name']
                        if 'callback' in action:
                            action['callback'](result["selected_rows"])
        
        return result
    
    def create_progress_tracker(self, steps: List[Dict[str, Any]], current_step: int = 0):
        """Create a progress tracker for multi-step processes"""
        
        progress_html = """
        <style>
        .progress-container {
            display: flex;
            align-items: center;
            margin: 20px 0;
        }
        .progress-step {
            display: flex;
            flex-direction: column;
            align-items: center;
            flex: 1;
            position: relative;
        }
        .progress-circle {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .progress-line {
            height: 2px;
            flex: 1;
            margin: 0 10px;
            position: absolute;
            top: 20px;
            left: 50%;
            right: -50%;
        }
        .step-completed {
            background: #4CAF50;
            color: white;
        }
        .step-current {
            background: #2196F3;
            color: white;
        }
        .step-pending {
            background: #E0E0E0;
            color: #757575;
        }
        .line-completed {
            background: #4CAF50;
        }
        .line-pending {
            background: #E0E0E0;
        }
        </style>
        """
        
        st.markdown(progress_html, unsafe_allow_html=True)
        
        # Create progress HTML
        progress_steps_html = '<div class="progress-container">'
        
        for i, step in enumerate(steps):
            if i < current_step:
                circle_class = "step-completed"
                icon = "✓"
            elif i == current_step:
                circle_class = "step-current"
                icon = str(i + 1)
            else:
                circle_class = "step-pending"
                icon = str(i + 1)
            
            progress_steps_html += f"""
            <div class="progress-step">
                <div class="progress-circle {circle_class}">
                    {icon}
                </div>
                <span style="font-size: 12px; text-align: center;">{step['title']}</span>
            """
            
            if i < len(steps) - 1:
                line_class = "line-completed" if i < current_step else "line-pending"
                progress_steps_html += f'<div class="progress-line {line_class}"></div>'
            
            progress_steps_html += '</div>'
        
        progress_steps_html += '</div>'
        
        st.markdown(progress_steps_html, unsafe_allow_html=True)
        
        # Display current step description
        if current_step < len(steps):
            current_step_info = steps[current_step]
            st.info(f"**Étape actuelle:** {current_step_info['title']}\n\n{current_step_info.get('description', '')}")
    
    def create_notification_center(self):
        """Create a notification center for user feedback"""
        
        if st.session_state.notifications:
            st.markdown("#### 🔔 Notifications")
            
            for i, notification in enumerate(st.session_state.notifications):
                notification_type = notification.get('type', 'info')
                message = notification.get('message', '')
                timestamp = notification.get('timestamp', datetime.now())
                
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    if notification_type == 'success':
                        st.success(f"✅ {message}")
                    elif notification_type == 'warning':
                        st.warning(f"⚠️ {message}")
                    elif notification_type == 'error':
                        st.error(f"❌ {message}")
                    else:
                        st.info(f"ℹ️ {message}")
                
                with col2:
                    if st.button("Supprimer", key=f"notif_{i}"):
                        st.session_state.notifications.pop(i)
                        st.rerun()
            
            # Clear all button
            if len(st.session_state.notifications) > 1:
                if st.button("🗑️ Tout supprimer"):
                    st.session_state.notifications.clear()
                    st.rerun()
    
    def add_notification(self, message: str, notification_type: str = 'info'):
        """Add a notification to the notification center"""
        notification = {
            'message': message,
            'type': notification_type,
            'timestamp': datetime.now()
        }
        st.session_state.notifications.append(notification)
    
    def create_interactive_chart(self, data: pd.DataFrame, chart_type: str = "line",
                                title: str = "Graphique", x_col: str = None, 
                                y_col: str = None, color_col: str = None) -> go.Figure:
        """Create interactive charts with Plotly"""
        
        if data.empty:
            st.warning("Aucune donnée disponible pour le graphique")
            return None
        
        fig = None
        
        if chart_type == "line":
            fig = px.line(
                data, 
                x=x_col, 
                y=y_col, 
                color=color_col,
                title=title,
                template="plotly_white"
            )
        elif chart_type == "bar":
            fig = px.bar(
                data, 
                x=x_col, 
                y=y_col, 
                color=color_col,
                title=title,
                template="plotly_white"
            )
        elif chart_type == "pie":
            fig = px.pie(
                data, 
                values=y_col, 
                names=x_col,
                title=title,
                template="plotly_white"
            )
        elif chart_type == "scatter":
            fig = px.scatter(
                data, 
                x=x_col, 
                y=y_col, 
                color=color_col,
                title=title,
                template="plotly_white"
            )
        
        if fig:
            # Enhance chart appearance
            fig.update_layout(
                font=dict(family="Arial, sans-serif", size=12),
                title_font=dict(size=16, color="#2E86AB"),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Add hover customization
            fig.update_traces(
                hovertemplate="<b>%{x}</b><br>%{y}<extra></extra>"
            )
        
        return fig
    
    def create_modal_dialog(self, title: str, content: str, 
                          buttons: List[Dict[str, Any]] = None) -> str:
        """Create a modal-like dialog using Streamlit components"""
        
        st.markdown(f"### 🔔 {title}")
        st.markdown("---")
        st.markdown(content)
        st.markdown("---")
        
        if buttons:
            button_cols = st.columns(len(buttons))
            
            for i, button in enumerate(buttons):
                with button_cols[i]:
                    if st.button(
                        button['label'], 
                        key=button.get('key', f"modal_btn_{i}"),
                        type=button.get('type', 'secondary'),
                        use_container_width=True
                    ):
                        return button['action']
        
        return None
    
    def create_file_uploader_with_preview(self, accepted_types: List[str] = None,
                                        max_size_mb: int = 10) -> Dict[str, Any]:
        """Create an enhanced file uploader with preview capabilities"""
        
        result = {"file": None, "preview": None, "valid": False}
        
        if accepted_types is None:
            accepted_types = ["csv", "xlsx", "pdf", "json"]
        
        st.markdown("#### 📁 Upload de Fichier")
        
        uploaded_file = st.file_uploader(
            "Choisir un fichier",
            type=accepted_types,
            help=f"Types acceptés: {', '.join(accepted_types)}. Taille max: {max_size_mb}MB"
        )
        
        if uploaded_file:
            # Check file size
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            
            if file_size_mb > max_size_mb:
                st.error(f"❌ Fichier trop volumineux ({file_size_mb:.1f}MB). Maximum autorisé: {max_size_mb}MB")
                return result
            
            result["file"] = uploaded_file
            result["valid"] = True
            
            # File info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Nom", uploaded_file.name)
            with col2:
                st.metric("Taille", f"{file_size_mb:.1f} MB")
            with col3:
                st.metric("Type", uploaded_file.type)
            
            # Preview based on file type
            if uploaded_file.type == "text/csv":
                try:
                    df = pd.read_csv(uploaded_file)
                    st.markdown("##### 👀 Aperçu du CSV")
                    st.dataframe(df.head(10))
                    result["preview"] = df
                except Exception as e:
                    st.error(f"Erreur lors de la lecture du CSV: {e}")
            
            elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
                try:
                    df = pd.read_excel(uploaded_file)
                    st.markdown("##### 👀 Aperçu de l'Excel")
                    st.dataframe(df.head(10))
                    result["preview"] = df
                except Exception as e:
                    st.error(f"Erreur lors de la lecture de l'Excel: {e}")
            
            elif uploaded_file.type == "application/json":
                try:
                    json_content = json.loads(uploaded_file.getvalue().decode("utf-8"))
                    st.markdown("##### 👀 Aperçu du JSON")
                    st.json(json_content)
                    result["preview"] = json_content
                except Exception as e:
                    st.error(f"Erreur lors de la lecture du JSON: {e}")
            
            else:
                st.info("👁️ Aperçu non disponible pour ce type de fichier")
        
        return result
    
    def create_auto_save_form(self, form_key: str, form_data: Dict[str, Any]):
        """Create a form with auto-save functionality"""
        
        # Initialize auto-save data
        if form_key not in st.session_state.auto_save_data:
            st.session_state.auto_save_data[form_key] = {}
        
        # Auto-save indicator
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("#### 💾 Sauvegarde Automatique Activée")
        with col2:
            last_save = st.session_state.auto_save_data[form_key].get('last_save')
            if last_save:
                st.caption(f"Dernier save: {last_save.strftime('%H:%M:%S')}")
        
        # Update auto-save data
        current_time = datetime.now()
        if (not last_save or 
            (current_time - last_save).seconds > 30):  # Auto-save every 30 seconds
            
            st.session_state.auto_save_data[form_key].update({
                'data': form_data,
                'last_save': current_time
            })
            
            if last_save:  # Don't show on first save
                st.success("💾 Données sauvegardées automatiquement")
    
    def create_loading_state(self, key: str, message: str = "Chargement..."):
        """Create and manage loading states"""
        
        if key not in st.session_state.loading_states:
            st.session_state.loading_states[key] = False
        
        if st.session_state.loading_states[key]:
            return st.spinner(message)
        
        return None
    
    def set_loading_state(self, key: str, is_loading: bool):
        """Set loading state for a specific component"""
        st.session_state.loading_states[key] = is_loading
    
    def create_keyboard_shortcuts_help(self):
        """Display keyboard shortcuts help"""
        
        with st.expander("⌨️ Raccourcis Clavier"):
            shortcuts = {
                "Ctrl + R": "Actualiser la page",
                "Ctrl + S": "Sauvegarder (auto-save activé)",
                "Esc": "Fermer les modales",
                "Tab": "Navigation entre les champs",
                "Ctrl + F": "Rechercher dans les tableaux",
                "Ctrl + A": "Sélectionner tout",
                "Ctrl + Z": "Annuler (quand disponible)"
            }
            
            for shortcut, description in shortcuts.items():
                st.write(f"**{shortcut}** - {description}")
    
    def create_tour_guide(self, steps: List[Dict[str, str]]):
        """Create a guided tour for new users"""
        
        if 'tour_completed' not in st.session_state:
            st.session_state.tour_completed = False
        
        if 'current_tour_step' not in st.session_state:
            st.session_state.current_tour_step = 0
        
        if not st.session_state.tour_completed:
            st.info("🎯 **Bienvenue !** Voulez-vous faire le tour guidé de l'interface ?")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✅ Commencer le tour"):
                    st.session_state.current_tour_step = 0
                    self._show_tour_step(steps)
            
            with col2:
                if st.button("⏭️ Passer"):
                    st.session_state.tour_completed = True
                    st.rerun()
            
            with col3:
                if st.button("❌ Ne plus afficher"):
                    st.session_state.tour_completed = True
                    st.rerun()
    
    def _show_tour_step(self, steps: List[Dict[str, str]]):
        """Show current tour step"""
        
        current_step = st.session_state.current_tour_step
        
        if current_step < len(steps):
            step = steps[current_step]
            
            st.markdown(f"### 🎯 Tour Guidé - Étape {current_step + 1}/{len(steps)}")
            st.markdown(f"**{step['title']}**")
            st.markdown(step['description'])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if current_step > 0:
                    if st.button("⬅️ Précédent"):
                        st.session_state.current_tour_step -= 1
                        st.rerun()
            
            with col2:
                if st.button("⏭️ Passer le tour"):
                    st.session_state.tour_completed = True
                    st.rerun()
            
            with col3:
                if current_step < len(steps) - 1:
                    if st.button("➡️ Suivant"):
                        st.session_state.current_tour_step += 1
                        st.rerun()
                else:
                    if st.button("🎉 Terminer"):
                        st.session_state.tour_completed = True
                        st.balloons()
                        st.rerun()
        
        # Progress bar
        progress = (current_step + 1) / len(steps)
        st.progress(progress)