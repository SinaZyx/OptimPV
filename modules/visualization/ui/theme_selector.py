"""
Composant UI pour la sélection et le switch de thème
"""
import streamlit as st
from typing import Optional
from ...styles.themes.theme_manager import theme_manager

def render_theme_selector(position: str = 'sidebar', key: Optional[str] = None):
    """
    Affiche le sélecteur de thème avec preview
    
    Args:
        position: 'sidebar', 'main', ou 'floating'
        key: Clé unique pour le composant
    """
    current_theme = theme_manager.get_current_theme()
    
    if position == 'floating':
        # Bouton flottant en bas à droite
        st.markdown("""
        <style>
        .theme-toggle {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 999;
            background: var(--surface);
            border-radius: 50%;
            width: 56px;
            height: 56px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px var(--shadow);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .theme-toggle:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 20px var(--shadow);
        }
        </style>
        <div class="theme-toggle" onclick="toggleTheme()">
            <span style="font-size: 24px;">{'🌙' if current_theme == 'light' else '☀️'}</span>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        # Interface standard
        container = st.sidebar if position == 'sidebar' else st
        
        with container:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Sélecteur de thème avec preview
                selected_theme = st.selectbox(
                    "🎨 Thème",
                    options=['light', 'dark', 'corporate'],
                    format_func=lambda x: {
                        'light': '☀️ Clair',
                        'dark': '🌙 Sombre',
                        'corporate': '🏢 Corporate'
                    }.get(x, x),
                    index=['light', 'dark', 'corporate'].index(current_theme),
                    key=key or 'theme_selector'
                )
            
            with col2:
                # Bouton de preview
                if st.button("👁️", help="Preview du thème", key=f"{key}_preview" if key else "theme_preview"):
                    show_theme_preview()
            
            # Appliquer le changement
            if selected_theme != current_theme:
                theme_manager.switch_theme(selected_theme)
                st.rerun()

def show_theme_preview():
    """Affiche un aperçu du thème actuel"""
    colors = theme_manager.get_colors()
    
    with st.expander("🎨 Aperçu du thème", expanded=True):
        # Couleurs principales
        st.markdown("**Couleurs principales**")
        cols = st.columns(5)
        color_items = [
            ('Primary', colors['primary']),
            ('Secondary', colors['secondary']),
            ('Accent', colors['accent']),
            ('Success', colors['success']),
            ('Error', colors['error'])
        ]
        
        for i, (name, color) in enumerate(color_items):
            with cols[i]:
                st.markdown(f"""
                <div style="
                    background-color: {color};
                    height: 60px;
                    border-radius: 8px;
                    margin-bottom: 4px;
                "></div>
                <small style="color: var(--text-secondary);">{name}</small>
                """, unsafe_allow_html=True)
        
        # Exemple de composants
        st.markdown("**Composants**")
        
        # Card exemple
        st.markdown(f"""
        <div style="
            background: var(--surface);
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid var(--border);
            margin: 1rem 0;
        ">
            <h4 style="color: var(--text-primary); margin: 0;">Exemple de Card</h4>
            <p style="color: var(--text-secondary); margin: 0.5rem 0;">
                Ceci est un exemple de card avec le thème actuel.
            </p>
            <button style="
                background: var(--primary);
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 6px;
                cursor: pointer;
                margin-top: 0.5rem;
            ">Action</button>
        </div>
        """, unsafe_allow_html=True)
        
        # Gradient exemple
        st.markdown(f"""
        <div style="
            background: {f"linear-gradient(135deg, {colors['gradient_start']}, {colors['gradient_end']})"}; 
            height: 80px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            margin: 1rem 0;
        ">
            Gradient Example
        </div>
        """, unsafe_allow_html=True)

def render_theme_toggle_mini():
    """Affiche un toggle minimaliste pour le thème"""
    current = theme_manager.get_current_theme()
    
    # CSS pour le toggle switch
    st.markdown("""
    <style>
    .theme-switch {
        position: relative;
        display: inline-block;
        width: 60px;
        height: 30px;
    }
    
    .theme-switch input {
        opacity: 0;
        width: 0;
        height: 0;
    }
    
    .slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #ccc;
        transition: .4s;
        border-radius: 34px;
    }
    
    .slider:before {
        position: absolute;
        content: "";
        height: 22px;
        width: 22px;
        left: 4px;
        bottom: 4px;
        background-color: white;
        transition: .4s;
        border-radius: 50%;
    }
    
    input:checked + .slider {
        background-color: var(--primary);
    }
    
    input:checked + .slider:before {
        transform: translateX(30px);
    }
    
    .theme-icons {
        position: absolute;
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 8px;
        pointer-events: none;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Toggle switch
    is_dark = current == 'dark'
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        toggle = st.checkbox(
            "",
            value=is_dark,
            key="theme_toggle_mini",
            label_visibility="collapsed"
        )
        
        if toggle != is_dark:
            new_theme = 'dark' if toggle else 'light'
            theme_manager.switch_theme(new_theme)
            st.rerun()