"""
Gestionnaire de thèmes pour l'application avec support Dark/Light mode
"""
import streamlit as st
from typing import Dict, Any, Optional
import json
from dataclasses import dataclass, asdict

@dataclass
class ColorPalette:
    """Palette de couleurs pour un thème"""
    # Couleurs principales
    primary: str
    primary_hover: str
    secondary: str
    secondary_hover: str
    accent: str
    
    # Couleurs de fond
    background: str
    surface: str
    surface_hover: str
    
    # Couleurs de texte
    text_primary: str
    text_secondary: str
    text_disabled: str
    
    # Couleurs d'état
    success: str
    warning: str
    error: str
    info: str
    
    # Couleurs de graphiques
    chart_colors: list
    
    # Gradients
    gradient_start: str
    gradient_end: str
    
    # Bordures et ombres
    border: str
    shadow: str

class ThemeManager:
    """Gestionnaire de thèmes avec persistence des préférences"""
    
    # Définition des thèmes
    THEMES = {
        'light': ColorPalette(
            # Couleurs principales
            primary='#1E88E5',
            primary_hover='#1976D2',
            secondary='#43A047',
            secondary_hover='#388E3C',
            accent='#FF6F00',
            
            # Couleurs de fond
            background='#FFFFFF',
            surface='#F5F7FA',
            surface_hover='#E8EBF0',
            
            # Couleurs de texte
            text_primary='#1A202C',
            text_secondary='#4A5568',
            text_disabled='#A0AEC0',
            
            # Couleurs d'état
            success='#48BB78',
            warning='#F6AD55',
            error='#F56565',
            info='#4299E1',
            
            # Couleurs de graphiques
            chart_colors=[
                '#1E88E5', '#43A047', '#FF6F00', '#E53935', '#8E24AA',
                '#00ACC1', '#FFB300', '#5E35B1', '#039BE5', '#C0CA33'
            ],
            
            # Gradients
            gradient_start='#1E88E5',
            gradient_end='#43A047',
            
            # Bordures et ombres
            border='#E2E8F0',
            shadow='rgba(0, 0, 0, 0.1)'
        ),
        
        'dark': ColorPalette(
            # Couleurs principales
            primary='#4FC3F7',
            primary_hover='#29B6F6',
            secondary='#81C784',
            secondary_hover='#66BB6A',
            accent='#FFB74D',
            
            # Couleurs de fond
            background='#0F172A',
            surface='#1E293B',
            surface_hover='#334155',
            
            # Couleurs de texte
            text_primary='#F1F5F9',
            text_secondary='#CBD5E1',
            text_disabled='#64748B',
            
            # Couleurs d'état
            success='#4ADE80',
            warning='#FBBF24',
            error='#F87171',
            info='#60A5FA',
            
            # Couleurs de graphiques
            chart_colors=[
                '#4FC3F7', '#81C784', '#FFB74D', '#FF8A80', '#BA68C8',
                '#4DD0E1', '#FFD54F', '#9575CD', '#4FC3F7', '#DCE775'
            ],
            
            # Gradients
            gradient_start='#4FC3F7',
            gradient_end='#81C784',
            
            # Bordures et ombres
            border='#334155',
            shadow='rgba(0, 0, 0, 0.3)'
        ),
        
        'corporate': ColorPalette(
            # Thème professionnel corporate
            primary='#2C3E50',
            primary_hover='#34495E',
            secondary='#27AE60',
            secondary_hover='#229954',
            accent='#E74C3C',
            
            background='#FAFAFA',
            surface='#FFFFFF',
            surface_hover='#F5F5F5',
            
            text_primary='#2C3E50',
            text_secondary='#7F8C8D',
            text_disabled='#BDC3C7',
            
            success='#27AE60',
            warning='#F39C12',
            error='#E74C3C',
            info='#3498DB',
            
            chart_colors=[
                '#2C3E50', '#27AE60', '#E74C3C', '#3498DB', '#9B59B6',
                '#1ABC9C', '#F39C12', '#34495E', '#16A085', '#8E44AD'
            ],
            
            gradient_start='#2C3E50',
            gradient_end='#3498DB',
            
            border='#ECF0F1',
            shadow='rgba(52, 73, 94, 0.1)'
        )
    }
    
    def __init__(self):
        """Initialise le gestionnaire de thèmes"""
        if 'theme' not in st.session_state:
            st.session_state.theme = self._load_saved_theme() or 'light'
            
        if 'theme_colors' not in st.session_state:
            st.session_state.theme_colors = asdict(self.THEMES[st.session_state.theme])
    
    def _load_saved_theme(self) -> Optional[str]:
        """Charge le thème sauvegardé depuis le localStorage"""
        try:
            # Dans une vraie app, on utiliserait le localStorage du navigateur
            # Pour Streamlit, on peut utiliser un cookie ou un fichier de config
            return 'light'  # Par défaut
        except:
            return None
    
    def get_current_theme(self) -> str:
        """Retourne le thème actuel"""
        return st.session_state.theme
    
    def get_colors(self) -> Dict[str, Any]:
        """Retourne les couleurs du thème actuel"""
        return st.session_state.theme_colors
    
    def switch_theme(self, theme_name: str):
        """Change le thème actuel"""
        if theme_name in self.THEMES:
            st.session_state.theme = theme_name
            st.session_state.theme_colors = asdict(self.THEMES[theme_name])
            # Sauvegarder la préférence
            self._save_theme_preference(theme_name)
            return True
        return False
    
    def _save_theme_preference(self, theme_name: str):
        """Sauvegarde la préférence de thème"""
        # Dans une vraie app, on sauvegarderait dans le localStorage
        pass
    
    def apply_theme_css(self):
        """Applique le CSS du thème actuel"""
        colors = self.get_colors()
        
        css = f"""
        <style>
        /* Variables CSS globales */
        :root {{
            --primary: {colors['primary']};
            --primary-hover: {colors['primary_hover']};
            --secondary: {colors['secondary']};
            --secondary-hover: {colors['secondary_hover']};
            --accent: {colors['accent']};
            
            --bg: {colors['background']};
            --surface: {colors['surface']};
            --surface-hover: {colors['surface_hover']};
            
            --text-primary: {colors['text_primary']};
            --text-secondary: {colors['text_secondary']};
            --text-disabled: {colors['text_disabled']};
            
            --success: {colors['success']};
            --warning: {colors['warning']};
            --error: {colors['error']};
            --info: {colors['info']};
            
            --border: {colors['border']};
            --shadow: {colors['shadow']};
            
            --gradient: linear-gradient(135deg, {colors['gradient_start']}, {colors['gradient_end']});
        }}
        
        /* Application globale du thème */
        .stApp {{
            background-color: var(--bg);
            color: var(--text-primary);
        }}
        
        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: var(--surface);
            border-right: 1px solid var(--border);
        }}
        
        /* Cards et surfaces */
        .element-container {{
            background-color: var(--surface);
            border-radius: 12px;
            padding: 1rem;
            transition: all 0.3s ease;
        }}
        
        .element-container:hover {{
            background-color: var(--surface-hover);
            box-shadow: 0 4px 12px var(--shadow);
        }}
        
        /* Boutons personnalisés */
        .stButton > button {{
            background-color: var(--primary);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px var(--shadow);
        }}
        
        .stButton > button:hover {{
            background-color: var(--primary-hover);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px var(--shadow);
        }}
        
        /* Métriques avec style moderne */
        [data-testid="metric-container"] {{
            background: var(--gradient);
            padding: 1.5rem;
            border-radius: 16px;
            color: white;
            box-shadow: 0 4px 12px var(--shadow);
            transition: transform 0.3s ease;
        }}
        
        [data-testid="metric-container"]:hover {{
            transform: scale(1.02);
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .fade-in {{
            animation: fadeIn 0.5s ease-out;
        }}
        
        /* Glassmorphism effect */
        .glass {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 16px;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .element-container {{
                padding: 0.75rem;
            }}
        }}
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    def get_plotly_theme(self) -> Dict[str, Any]:
        """Retourne la configuration Plotly pour le thème actuel"""
        colors = self.get_colors()
        
        return {
            'layout': {
                'paper_bgcolor': colors['surface'],
                'plot_bgcolor': colors['background'],
                'font': {
                    'color': colors['text_primary'],
                    'family': 'Inter, system-ui, sans-serif'
                },
                'colorway': colors['chart_colors'],
                'hovermode': 'x unified',
                'hoverlabel': {
                    'bgcolor': colors['surface'],
                    'font_color': colors['text_primary'],
                    'bordercolor': colors['border']
                },
                'xaxis': {
                    'gridcolor': colors['border'],
                    'linecolor': colors['border'],
                    'tickfont': {'color': colors['text_secondary']}
                },
                'yaxis': {
                    'gridcolor': colors['border'],
                    'linecolor': colors['border'],
                    'tickfont': {'color': colors['text_secondary']}
                }
            }
        }

# Instance globale
theme_manager = ThemeManager()