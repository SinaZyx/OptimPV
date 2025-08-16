"""
Simple UI Components for PMO Billing System
Uses native Streamlit components without custom CSS
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union
import time


class UIComponents:
    """Simple UI components for the billing system using native Streamlit"""
    
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
        """Create sidebar metrics using native Streamlit"""
        st.sidebar.markdown("### 📊 Aperçu Rapide")
        
        for label, value in metrics.items():
            if isinstance(value, (int, float)):
                delta = self._calculate_metric_delta(label, value)
                st.sidebar.metric(label, value, delta=delta)
            else:
                st.sidebar.metric(label, value)
    
    def _calculate_metric_delta(self, label: str, current_value: Union[int, float]) -> Optional[str]:
        """Calculate metric delta based on historical data"""
        if "CA" in label:
            return "+12.5%" if current_value > 10000 else "-5.2%"
        elif "Factures" in label:
            return f"-{max(0, current_value - 10)}" if current_value > 10 else None
        elif "Participants" in label:
            return f"+{max(0, current_value - 5)}" if current_value > 5 else None
        return None
    
    def create_enhanced_navigation(self, options: Dict[str, Dict[str, Any]]) -> str:
        """Create enhanced navigation using native Streamlit selectbox"""
        # Create option labels with badges
        enhanced_options = []
        for option, config in options.items():
            label = option
            if config.get('count', 0) > 0:
                label += f" ({config['count']})"
            if config.get('badge'):
                label += f" - {config['badge']}"
            enhanced_options.append(label)
        
        # Get current page from session state
        original_options = list(options.keys())
        current_page = st.session_state.get('current_page', original_options[0])
        
        # Find index of current page
        try:
            default_index = original_options.index(current_page)
        except ValueError:
            default_index = 0
        
        # Create selectbox with default value
        selected_index = st.sidebar.selectbox(
            "Navigation",
            range(len(enhanced_options)),
            format_func=lambda x: enhanced_options[x],
            index=default_index,
            key="navigation_select"
        )
        
        return original_options[selected_index]
    
    def create_modern_card(self, title: str, content: str, icon: str = "📊", 
                          color: str = "blue", action_button: Optional[Dict] = None):
        """Create a card using native Streamlit components"""
        # Create container
        with st.container():
            # Title with icon
            st.subheader(f"{icon} {title}")
            
            # Content
            if color == "green":
                st.success(content)
            elif color == "red" or color == "orange":
                st.warning(content)
            elif color == "blue" or color == "purple":
                st.info(content)
            else:
                st.write(content)
            
            # Action button if provided
            if action_button:
                if st.button(
                    action_button.get('label', 'Action'),
                    key=action_button.get('key', None),
                    type=action_button.get('type', 'secondary')
                ):
                    if 'callback' in action_button:
                        action_button['callback']()
    
    def create_data_table_with_actions(self, 
                                     data: pd.DataFrame,
                                     key: str = "data_table",
                                     actions: Optional[List[Dict]] = None,
                                     selection_mode: str = "single",
                                     height: int = 400) -> Dict[str, Any]:
        """Create data table with action buttons using native Streamlit"""
        result = {
            "selected_rows": [],
            "action_triggered": None
        }
        
        # Display dataframe
        st.dataframe(
            data,
            use_container_width=True,
            height=height,
            key=f"{key}_display"
        )
        
        # Action buttons
        if actions:
            cols = st.columns(len(actions))
            for i, action in enumerate(actions):
                with cols[i]:
                    if st.button(
                        action.get('label', 'Action'),
                        key=f"{key}_action_{i}",
                        type=action.get('type', 'secondary'),
                        disabled=action.get('disabled', False),
                        use_container_width=True
                    ):
                        result["action_triggered"] = action['name']
                        if 'callback' in action:
                            action['callback']()
        
        return result
    
    def create_progress_tracker(self, steps: List[Dict[str, Any]], current_step: int = 0):
        """Create progress tracker using native Streamlit"""
        # Progress bar
        progress = (current_step + 1) / len(steps) if steps else 0
        st.progress(progress)
        
        # Display steps
        cols = st.columns(len(steps))
        for i, (step, col) in enumerate(zip(steps, cols)):
            with col:
                if i < current_step:
                    st.success(f"✓ {step['title']}")
                elif i == current_step:
                    st.info(f"→ {step['title']}")
                else:
                    st.text(f"○ {step['title']}")
        
        # Current step info
        if current_step < len(steps):
            current_step_info = steps[current_step]
            st.info(f"**Étape actuelle:** {current_step_info['title']}")
            if 'description' in current_step_info:
                st.write(current_step_info['description'])
    
    def create_notification_center(self):
        """Create notification center using native Streamlit"""
        if st.session_state.notifications:
            st.markdown("#### 🔔 Notifications")
            
            for notification in st.session_state.notifications:
                notification_type = notification.get('type', 'info')
                message = notification.get('message', '')
                
                if notification_type == 'success':
                    st.success(message)
                elif notification_type == 'error':
                    st.error(message)
                elif notification_type == 'warning':
                    st.warning(message)
                else:
                    st.info(message)
            
            # Clear notifications button
            if st.button("Effacer les notifications", key="clear_notifications"):
                st.session_state.notifications = []
                st.rerun()
    
    def show_notification(self, message: str, type: str = "info"):
        """Add a notification"""
        st.session_state.notifications.append({
            'message': message,
            'type': type,
            'timestamp': datetime.now()
        })
    
    def create_dashboard_grid(self, metrics: List[Dict[str, Any]], cols: int = 4):
        """Create dashboard grid using native Streamlit columns"""
        # Create columns
        columns = st.columns(cols)
        
        # Display metrics
        for i, metric in enumerate(metrics):
            col_index = i % cols
            with columns[col_index]:
                value = metric.get('value', 0)
                delta = metric.get('delta', None)
                
                st.metric(
                    label=metric.get('label', 'Metric'),
                    value=value,
                    delta=delta,
                    help=metric.get('help', None)
                )
    
    def create_search_bar(self, placeholder: str = "Rechercher...", key: str = "search") -> str:
        """Create search bar using native Streamlit"""
        return st.text_input(
            "🔍 Recherche",
            placeholder=placeholder,
            key=key
        )
    
    def create_date_range_picker(self, key: str = "date_range") -> tuple:
        """Create date range picker using native Streamlit"""
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Date de début",
                value=date.today() - timedelta(days=30),
                key=f"{key}_start"
            )
        
        with col2:
            end_date = st.date_input(
                "Date de fin",
                value=date.today(),
                key=f"{key}_end"
            )
        
        return start_date, end_date
    
    def create_filter_sidebar(self, filters: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Create filter sidebar using native Streamlit"""
        st.sidebar.markdown("### 🔧 Filtres")
        
        filter_values = {}
        
        for filter_name, filter_config in filters.items():
            filter_type = filter_config.get('type', 'select')
            
            if filter_type == 'select':
                filter_values[filter_name] = st.sidebar.selectbox(
                    filter_config.get('label', filter_name),
                    filter_config.get('options', []),
                    key=f"filter_{filter_name}"
                )
            elif filter_type == 'multiselect':
                filter_values[filter_name] = st.sidebar.multiselect(
                    filter_config.get('label', filter_name),
                    filter_config.get('options', []),
                    default=filter_config.get('default', []),
                    key=f"filter_{filter_name}"
                )
            elif filter_type == 'slider':
                filter_values[filter_name] = st.sidebar.slider(
                    filter_config.get('label', filter_name),
                    min_value=filter_config.get('min', 0),
                    max_value=filter_config.get('max', 100),
                    value=filter_config.get('default', 50),
                    key=f"filter_{filter_name}"
                )
            elif filter_type == 'date':
                filter_values[filter_name] = st.sidebar.date_input(
                    filter_config.get('label', filter_name),
                    value=filter_config.get('default', date.today()),
                    key=f"filter_{filter_name}"
                )
        
        return filter_values
    
    def create_loading_placeholder(self, message: str = "Chargement..."):
        """Create loading placeholder using native Streamlit"""
        with st.spinner(message):
            time.sleep(0.5)  # Simulated loading
    
    def create_empty_state(self, 
                          title: str = "Aucune donnée",
                          message: str = "Il n'y a pas encore de données à afficher.",
                          action_label: str = None,
                          action_callback: callable = None):
        """Create empty state using native Streamlit"""
        st.info(f"### {title}\n\n{message}")
        
        if action_label and action_callback:
            if st.button(action_label, type="primary"):
                action_callback()
    
    def create_confirmation_dialog(self, 
                                 title: str,
                                 message: str,
                                 confirm_label: str = "Confirmer",
                                 cancel_label: str = "Annuler") -> bool:
        """Create confirmation dialog using native Streamlit"""
        st.warning(f"### {title}\n\n{message}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(confirm_label, type="primary", key="confirm_btn"):
                return True
        
        with col2:
            if st.button(cancel_label, key="cancel_btn"):
                return False
        
        return False
    
    def create_tour_guide(self, steps: List[Dict[str, str]], key: str = "tour"):
        """Create tour guide using native Streamlit"""
        if f"{key}_active" not in st.session_state:
            st.session_state[f"{key}_active"] = False
            st.session_state[f"{key}_step"] = 0
        
        if not st.session_state[f"{key}_active"]:
            if st.button("🎯 Démarrer le tour guidé", key=f"{key}_start"):
                st.session_state[f"{key}_active"] = True
                st.session_state[f"{key}_step"] = 0
                st.rerun()
        else:
            current_step = st.session_state[f"{key}_step"]
            
            if current_step < len(steps):
                step = steps[current_step]
                
                with st.container():
                    st.info(f"**Étape {current_step + 1}/{len(steps)}: {step['title']}**\n\n{step['content']}")
                    
                    col1, col2, col3 = st.columns([1, 1, 2])
                    
                    with col1:
                        if current_step > 0:
                            if st.button("← Précédent", key=f"{key}_prev"):
                                st.session_state[f"{key}_step"] -= 1
                                st.rerun()
                    
                    with col2:
                        if current_step < len(steps) - 1:
                            if st.button("Suivant →", key=f"{key}_next"):
                                st.session_state[f"{key}_step"] += 1
                                st.rerun()
                        else:
                            if st.button("Terminer ✓", key=f"{key}_finish"):
                                st.session_state[f"{key}_active"] = False
                                st.session_state[f"{key}_step"] = 0
                                st.rerun()
                    
                    with col3:
                        if st.button("Quitter ✕", key=f"{key}_quit"):
                            st.session_state[f"{key}_active"] = False
                            st.session_state[f"{key}_step"] = 0
                            st.rerun()