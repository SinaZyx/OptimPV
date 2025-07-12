"""
UI Themes and Styling for PMO Billing System
Modern themes with dark/light mode support and OptimPV corporate branding
"""

import streamlit as st
from typing import Dict, Any, Optional
import json


class UIThemes:
    """Theme management system for the billing interface"""
    
    def __init__(self):
        self.themes = self._load_themes()
        self.current_theme = st.session_state.get('current_theme', 'OptimPV Corporate')
    
    def _load_themes(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined themes"""
        return {
            "OptimPV Corporate": {
                "primary_color": "#2E7D32",  # Green
                "secondary_color": "#81C784",
                "accent_color": "#4CAF50",
                "background_color": "#FAFAFA",
                "text_color": "#212121",
                "sidebar_color": "#E8F5E9",
                "card_color": "#FFFFFF",
                "border_color": "#E0E0E0",
                "success_color": "#4CAF50",
                "warning_color": "#FF9800",
                "error_color": "#F44336",
                "info_color": "#2196F3",
                "font_family": "Roboto, sans-serif",
                "description": "Thème corporate OptimPV avec couleurs vertes"
            },
            "Mode Sombre": {
                "primary_color": "#BB86FC",
                "secondary_color": "#03DAC6",
                "accent_color": "#CF6679",
                "background_color": "#121212",
                "text_color": "#FFFFFF",
                "sidebar_color": "#1E1E1E",
                "card_color": "#1E1E1E",
                "border_color": "#333333",
                "success_color": "#4CAF50",
                "warning_color": "#FF9800",
                "error_color": "#CF6679",
                "info_color": "#03DAC6",
                "font_family": "Roboto, sans-serif",
                "description": "Thème sombre moderne pour un confort visuel"
            },
            "Mode Clair": {
                "primary_color": "#1976D2",
                "secondary_color": "#42A5F5",
                "accent_color": "#FFC107",
                "background_color": "#FFFFFF",
                "text_color": "#212121",
                "sidebar_color": "#F5F5F5",
                "card_color": "#FFFFFF",
                "border_color": "#E0E0E0",
                "success_color": "#4CAF50",
                "warning_color": "#FF9800",
                "error_color": "#F44336",
                "info_color": "#2196F3",
                "font_family": "Inter, sans-serif",
                "description": "Thème clair et lumineux pour une visibilité optimale"
            },
            "Personnalisé": {
                "primary_color": "#6366F1",
                "secondary_color": "#8B5CF6",
                "accent_color": "#EC4899",
                "background_color": "#F8FAFC",
                "text_color": "#1E293B",
                "sidebar_color": "#F1F5F9",
                "card_color": "#FFFFFF",
                "border_color": "#E2E8F0",
                "success_color": "#10B981",
                "warning_color": "#F59E0B",
                "error_color": "#EF4444",
                "info_color": "#3B82F6",
                "font_family": "Inter, sans-serif",
                "description": "Thème personnalisable avec couleurs modernes"
            }
        }
    
    def apply_theme(self, theme_name: Optional[str] = None):
        """Apply selected theme to the interface"""
        if theme_name:
            self.current_theme = theme_name
            st.session_state.current_theme = theme_name
        
        theme = self.themes.get(self.current_theme, self.themes["OptimPV Corporate"])
        
        # Generate CSS
        css = self._generate_theme_css(theme)
        
        # Apply CSS
        st.markdown(css, unsafe_allow_html=True)
        
        # Store theme in session state for consistency
        st.session_state.theme_config = theme
    
    def _generate_theme_css(self, theme: Dict[str, Any]) -> str:
        """Generate CSS from theme configuration"""
        
        css = f"""
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Root variables */
        :root {{
            --primary-color: {theme['primary_color']};
            --secondary-color: {theme['secondary_color']};
            --accent-color: {theme['accent_color']};
            --background-color: {theme['background_color']};
            --text-color: {theme['text_color']};
            --sidebar-color: {theme['sidebar_color']};
            --card-color: {theme['card_color']};
            --border-color: {theme['border_color']};
            --success-color: {theme['success_color']};
            --warning-color: {theme['warning_color']};
            --error-color: {theme['error_color']};
            --info-color: {theme['info_color']};
            --font-family: {theme['font_family']};
        }}
        
        /* Main container styling */
        .main > div {{
            background-color: var(--background-color);
            color: var(--text-color);
            font-family: var(--font-family);
        }}
        
        /* Header styling */
        .main h1 {{
            color: var(--primary-color);
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        
        .main h2 {{
            color: var(--primary-color);
            font-weight: 600;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }}
        
        .main h3 {{
            color: var(--secondary-color);
            font-weight: 500;
            margin-top: 1.5rem;
            margin-bottom: 0.8rem;
        }}
        
        .main h4 {{
            color: var(--text-color);
            font-weight: 500;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }}
        
        /* Sidebar styling */
        .css-1d391kg {{
            background-color: var(--sidebar-color);
            border-right: 1px solid var(--border-color);
        }}
        
        .css-1d391kg .css-1v0mbdj {{
            color: var(--text-color);
        }}
        
        /* Button styling */
        .stButton > button {{
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 500;
            font-family: var(--font-family);
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .stButton > button:hover {{
            background-color: var(--secondary-color);
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        
        .stButton > button:active {{
            transform: translateY(0px);
        }}
        
        /* Primary button styling */
        .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            font-weight: 600;
        }}
        
        .stButton > button[kind="primary"]:hover {{
            background: linear-gradient(135deg, var(--secondary-color), var(--primary-color));
        }}
        
        /* Secondary button styling */
        .stButton > button[kind="secondary"] {{
            background-color: transparent;
            color: var(--primary-color);
            border: 2px solid var(--primary-color);
        }}
        
        .stButton > button[kind="secondary"]:hover {{
            background-color: var(--primary-color);
            color: white;
        }}
        
        /* Metric styling */
        .css-1xarl3l {{
            background-color: var(--card-color);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }}
        
        .css-1xarl3l:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }}
        
        /* Metric label styling */
        .css-1wivap2 {{
            color: var(--text-color);
            font-weight: 500;
            font-size: 0.9rem;
        }}
        
        /* Metric value styling */
        .css-1wivap2 + div {{
            color: var(--primary-color);
            font-weight: 700;
            font-size: 1.8rem;
        }}
        
        /* Success metric delta */
        .css-1wivap2 + div + div[data-testid="metric-delta"] {{
            color: var(--success-color);
        }}
        
        /* Warning metric delta */
        .css-1wivap2 + div + div[data-testid="metric-delta"].negative {{
            color: var(--error-color);
        }}
        
        /* Dataframe styling */
        .stDataFrame {{
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .stDataFrame table {{
            background-color: var(--card-color);
            color: var(--text-color);
        }}
        
        .stDataFrame th {{
            background-color: var(--primary-color);
            color: white;
            font-weight: 600;
            text-align: left;
            padding: 12px;
        }}
        
        .stDataFrame td {{
            padding: 10px 12px;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .stDataFrame tr:hover {{
            background-color: rgba(46, 125, 50, 0.05);
        }}
        
        /* Input styling */
        .stTextInput > div > div > input {{
            background-color: var(--card-color);
            color: var(--text-color);
            border: 2px solid var(--border-color);
            border-radius: 8px;
            font-family: var(--font-family);
            transition: border-color 0.3s ease;
        }}
        
        .stTextInput > div > div > input:focus {{
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(46, 125, 50, 0.1);
        }}
        
        .stSelectbox > div > div > select {{
            background-color: var(--card-color);
            color: var(--text-color);
            border: 2px solid var(--border-color);
            border-radius: 8px;
            font-family: var(--font-family);
        }}
        
        .stNumberInput > div > div > input {{
            background-color: var(--card-color);
            color: var(--text-color);
            border: 2px solid var(--border-color);
            border-radius: 8px;
            font-family: var(--font-family);
        }}
        
        /* Textarea styling */
        .stTextArea > div > div > textarea {{
            background-color: var(--card-color);
            color: var(--text-color);
            border: 2px solid var(--border-color);
            border-radius: 8px;
            font-family: var(--font-family);
        }}
        
        /* Progress bar styling */
        .stProgress > div > div {{
            background-color: var(--border-color);
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .stProgress > div > div > div {{
            background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
            border-radius: 10px;
        }}
        
        /* Success message styling */
        .stSuccess {{
            background-color: rgba(76, 175, 80, 0.1);
            border-left: 4px solid var(--success-color);
            border-radius: 0 8px 8px 0;
            color: var(--success-color);
            font-weight: 500;
        }}
        
        /* Warning message styling */
        .stWarning {{
            background-color: rgba(255, 152, 0, 0.1);
            border-left: 4px solid var(--warning-color);
            border-radius: 0 8px 8px 0;
            color: var(--warning-color);
            font-weight: 500;
        }}
        
        /* Error message styling */
        .stError {{
            background-color: rgba(244, 67, 54, 0.1);
            border-left: 4px solid var(--error-color);
            border-radius: 0 8px 8px 0;
            color: var(--error-color);
            font-weight: 500;
        }}
        
        /* Info message styling */
        .stInfo {{
            background-color: rgba(33, 150, 243, 0.1);
            border-left: 4px solid var(--info-color);
            border-radius: 0 8px 8px 0;
            color: var(--info-color);
            font-weight: 500;
        }}
        
        /* Tab styling */
        .stTabs > div > div > div > div {{
            background-color: var(--card-color);
            border: 1px solid var(--border-color);
            border-radius: 8px 8px 0 0;
            color: var(--text-color);
            font-weight: 500;
            padding: 12px 20px;
            margin-right: 4px;
            transition: all 0.3s ease;
        }}
        
        .stTabs > div > div > div > div:hover {{
            background-color: var(--primary-color);
            color: white;
        }}
        
        .stTabs > div > div > div > div[aria-selected="true"] {{
            background-color: var(--primary-color);
            color: white;
            border-bottom: none;
        }}
        
        /* Expander styling */
        .streamlit-expanderHeader {{
            background-color: var(--card-color);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-color);
            font-weight: 500;
            transition: all 0.3s ease;
        }}
        
        .streamlit-expanderHeader:hover {{
            background-color: var(--primary-color);
            color: white;
        }}
        
        .streamlit-expanderContent {{
            background-color: var(--card-color);
            border: 1px solid var(--border-color);
            border-top: none;
            border-radius: 0 0 8px 8px;
            color: var(--text-color);
        }}
        
        /* Container styling */
        .element-container {{
            background-color: var(--background-color);
        }}
        
        /* Plotly chart styling */
        .js-plotly-plot {{
            background-color: var(--card-color);
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        /* File uploader styling */
        .stFileUploader > div {{
            background-color: var(--card-color);
            border: 2px dashed var(--border-color);
            border-radius: 8px;
            transition: border-color 0.3s ease;
        }}
        
        .stFileUploader > div:hover {{
            border-color: var(--primary-color);
        }}
        
        /* Slider styling */
        .stSlider > div > div > div {{
            background-color: var(--border-color);
        }}
        
        .stSlider > div > div > div > div {{
            background-color: var(--primary-color);
        }}
        
        /* Checkbox styling */
        .stCheckbox > label {{
            color: var(--text-color);
            font-weight: 500;
        }}
        
        /* Radio button styling */
        .stRadio > label {{
            color: var(--text-color);
            font-weight: 500;
        }}
        
        /* Date input styling */
        .stDateInput > div > div > input {{
            background-color: var(--card-color);
            color: var(--text-color);
            border: 2px solid var(--border-color);
            border-radius: 8px;
            font-family: var(--font-family);
        }}
        
        /* Form styling */
        .stForm {{
            background-color: var(--card-color);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }}
        
        /* Divider styling */
        hr {{
            border: none;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--border-color), transparent);
            margin: 2rem 0;
        }}
        
        /* Status component styling */
        .stStatus {{
            background-color: var(--card-color);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        /* Spinner styling */
        .stSpinner > div {{
            border-color: var(--primary-color);
        }}
        
        /* Balloons animation styling */
        .stBalloons {{
            color: var(--primary-color);
        }}
        
        /* Custom card styling */
        .custom-card {{
            background: var(--card-color);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
        }}
        
        .custom-card:hover {{
            box-shadow: 0 4px 16px rgba(0,0,0,0.12);
            transform: translateY(-2px);
        }}
        
        /* KPI card styling */
        .kpi-card {{
            background: linear-gradient(135deg, var(--card-color), rgba(46, 125, 50, 0.02));
            border: 2px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            transition: all 0.3s ease;
        }}
        
        .kpi-card:hover {{
            border-color: var(--primary-color);
            box-shadow: 0 8px 24px rgba(46, 125, 50, 0.1);
        }}
        
        /* Notification styling */
        .notification {{
            background-color: var(--card-color);
            border-left: 4px solid var(--info-color);
            border-radius: 0 8px 8px 0;
            padding: 16px;
            margin: 8px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            animation: slideIn 0.3s ease;
        }}
        
        @keyframes slideIn {{
            from {{
                transform: translateX(-100%);
                opacity: 0;
            }}
            to {{
                transform: translateX(0);
                opacity: 1;
            }}
        }}
        
        /* Responsive design */
        @media (max-width: 768px) {{
            .main h1 {{
                font-size: 1.8rem;
            }}
            
            .main h2 {{
                font-size: 1.5rem;
            }}
            
            .custom-card {{
                padding: 16px;
                margin: 8px 0;
            }}
            
            .kpi-card {{
                padding: 16px;
            }}
        }}
        
        /* Dark mode specific adjustments */
        {self._generate_dark_mode_adjustments() if theme.get('background_color') == '#121212' else ''}
        
        </style>
        """
        
        return css
    
    def _generate_dark_mode_adjustments(self) -> str:
        """Generate additional CSS adjustments for dark mode"""
        return """
        /* Dark mode specific styles */
        .stDataFrame table th {
            background-color: #333333;
        }
        
        .stDataFrame tr:hover {
            background-color: rgba(255, 255, 255, 0.05);
        }
        
        .stTabs > div > div > div > div:hover {
            background-color: #333333;
        }
        
        .streamlit-expanderHeader:hover {
            background-color: #333333;
        }
        
        /* Plotly dark mode */
        .js-plotly-plot .plotly {
            background-color: #1E1E1E !important;
        }
        """
    
    def set_theme(self, theme_name: str):
        """Set the current theme"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            st.session_state.current_theme = theme_name
            self.apply_theme()
    
    def get_current_theme(self) -> Dict[str, Any]:
        """Get current theme configuration"""
        return self.themes.get(self.current_theme, self.themes["OptimPV Corporate"])
    
    def customize_theme(self, custom_colors: Dict[str, str]) -> Dict[str, Any]:
        """Customize the current theme with new colors"""
        current_theme = self.get_current_theme().copy()
        current_theme.update(custom_colors)
        
        # Save custom theme
        self.themes["Personnalisé"] = current_theme
        
        return current_theme
    
    def create_theme_selector(self):
        """Create a theme selector widget"""
        st.markdown("#### 🎨 Personnalisation du Thème")
        
        # Theme selection
        col1, col2 = st.columns(2)
        
        with col1:
            selected_theme = st.selectbox(
                "Choisir un thème",
                list(self.themes.keys()),
                index=list(self.themes.keys()).index(self.current_theme),
                help="Sélectionnez un thème prédéfini"
            )
            
            if selected_theme != self.current_theme:
                self.set_theme(selected_theme)
                st.rerun()
        
        with col2:
            if st.button("🔄 Appliquer", help="Appliquer le thème sélectionné"):
                self.apply_theme()
                st.success("✅ Thème appliqué avec succès!")
        
        # Theme description
        current_theme = self.get_current_theme()
        st.info(f"**{self.current_theme}:** {current_theme.get('description', 'Aucune description disponible')}")
        
        # Preview colors
        st.markdown("##### 🎨 Aperçu des Couleurs")
        
        color_cols = st.columns(4)
        color_items = [
            ("Primaire", current_theme["primary_color"]),
            ("Secondaire", current_theme["secondary_color"]),
            ("Accent", current_theme["accent_color"]),
            ("Succès", current_theme["success_color"])
        ]
        
        for i, (name, color) in enumerate(color_items):
            with color_cols[i]:
                st.markdown(
                    f"""
                    <div style="
                        background-color: {color};
                        height: 40px;
                        border-radius: 8px;
                        margin-bottom: 5px;
                        border: 1px solid #ddd;
                    "></div>
                    <small style="color: #666;">{name}</small><br>
                    <small style="color: #999; font-family: monospace;">{color}</small>
                    """,
                    unsafe_allow_html=True
                )
        
        # Custom color picker (for Personnalisé theme)
        if self.current_theme == "Personnalisé":
            st.markdown("---")
            st.markdown("##### 🎛️ Personnalisation Avancée")
            
            with st.expander("Modifier les couleurs"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    primary = st.color_picker(
                        "Couleur Primaire",
                        current_theme["primary_color"],
                        help="Couleur principale de l'interface"
                    )
                    
                    secondary = st.color_picker(
                        "Couleur Secondaire",
                        current_theme["secondary_color"],
                        help="Couleur secondaire pour les éléments"
                    )
                
                with col2:
                    accent = st.color_picker(
                        "Couleur d'Accent",
                        current_theme["accent_color"],
                        help="Couleur d'accent pour les highlights"
                    )
                    
                    success = st.color_picker(
                        "Couleur de Succès",
                        current_theme["success_color"],
                        help="Couleur pour les messages de succès"
                    )
                
                with col3:
                    warning = st.color_picker(
                        "Couleur d'Avertissement",
                        current_theme["warning_color"],
                        help="Couleur pour les avertissements"
                    )
                    
                    error = st.color_picker(
                        "Couleur d'Erreur",
                        current_theme["error_color"],
                        help="Couleur pour les messages d'erreur"
                    )
                
                if st.button("💾 Sauvegarder les Modifications", type="primary"):
                    custom_colors = {
                        "primary_color": primary,
                        "secondary_color": secondary,
                        "accent_color": accent,
                        "success_color": success,
                        "warning_color": warning,
                        "error_color": error
                    }
                    
                    self.customize_theme(custom_colors)
                    self.apply_theme()
                    st.success("✅ Thème personnalisé sauvegardé!")
                    st.rerun()
    
    def export_theme(self, theme_name: Optional[str] = None) -> str:
        """Export theme configuration as JSON"""
        theme = self.themes.get(theme_name or self.current_theme)
        return json.dumps(theme, indent=2)
    
    def import_theme(self, theme_json: str, theme_name: str = "Importé"):
        """Import theme configuration from JSON"""
        try:
            theme_config = json.loads(theme_json)
            self.themes[theme_name] = theme_config
            return True
        except json.JSONDecodeError:
            return False
    
    def create_theme_preview(self, theme_name: str):
        """Create a preview of a specific theme"""
        theme = self.themes.get(theme_name)
        if not theme:
            st.error(f"Thème '{theme_name}' non trouvé")
            return
        
        st.markdown(f"#### 👀 Aperçu: {theme_name}")
        
        # Create preview elements
        preview_html = f"""
        <div style="
            background: {theme['background_color']};
            color: {theme['text_color']};
            padding: 20px;
            border-radius: 12px;
            border: 1px solid {theme['border_color']};
            font-family: {theme['font_family']};
            margin: 10px 0;
        ">
            <h3 style="color: {theme['primary_color']}; margin-top: 0;">
                Exemple de Titre
            </h3>
            
            <div style="
                background: {theme['card_color']};
                padding: 15px;
                border-radius: 8px;
                border: 1px solid {theme['border_color']};
                margin: 10px 0;
            ">
                <p>Exemple de contenu dans une carte</p>
                
                <button style="
                    background: {theme['primary_color']};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    margin-right: 10px;
                ">Bouton Principal</button>
                
                <button style="
                    background: transparent;
                    color: {theme['primary_color']};
                    border: 2px solid {theme['primary_color']};
                    padding: 6px 14px;
                    border-radius: 6px;
                ">Bouton Secondaire</button>
            </div>
            
            <div style="
                background: {theme['success_color']};
                color: white;
                padding: 10px;
                border-radius: 6px;
                margin: 5px 0;
                opacity: 0.9;
            ">✅ Message de succès</div>
            
            <div style="
                background: {theme['warning_color']};
                color: white;
                padding: 10px;
                border-radius: 6px;
                margin: 5px 0;
                opacity: 0.9;
            ">⚠️ Message d'avertissement</div>
            
            <div style="
                background: {theme['info_color']};
                color: white;
                padding: 10px;
                border-radius: 6px;
                margin: 5px 0;
                opacity: 0.9;
            ">ℹ️ Message d'information</div>
        </div>
        """
        
        st.markdown(preview_html, unsafe_allow_html=True)
    
    def get_theme_colors(self) -> Dict[str, str]:
        """Get current theme colors for use in components"""
        theme = self.get_current_theme()
        return {
            "primary": theme["primary_color"],
            "secondary": theme["secondary_color"],
            "accent": theme["accent_color"],
            "success": theme["success_color"],
            "warning": theme["warning_color"],
            "error": theme["error_color"],
            "info": theme["info_color"]
        }