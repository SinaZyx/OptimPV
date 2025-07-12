"""
Composants de cards modernes avec effets visuels avancés
"""
import streamlit as st
from typing import Optional, Dict, Any, List
import plotly.graph_objects as go

def render_metric_card(
    title: str,
    value: str,
    delta: Optional[str] = None,
    delta_color: str = "normal",
    icon: Optional[str] = None,
    gradient: bool = True,
    glass: bool = False,
    animate: bool = True,
    size: str = "medium",
    custom_style: Optional[Dict[str, str]] = None
):
    """
    Affiche une carte métrique moderne avec effets visuels
    
    Args:
        title: Titre de la métrique
        value: Valeur principale
        delta: Changement/variation
        delta_color: 'normal', 'inverse', 'off'
        icon: Emoji ou icône
        gradient: Appliquer un gradient de fond
        glass: Effect glassmorphism
        animate: Animations au hover
        size: 'small', 'medium', 'large'
        custom_style: Styles CSS personnalisés
    """
    # Définir les tailles
    sizes = {
        'small': {'padding': '1rem', 'font_value': '1.5rem', 'font_title': '0.875rem'},
        'medium': {'padding': '1.5rem', 'font_value': '2rem', 'font_title': '1rem'},
        'large': {'padding': '2rem', 'font_value': '2.5rem', 'font_title': '1.125rem'}
    }
    size_config = sizes.get(size, sizes['medium'])
    
    # Classes CSS
    classes = ['metric-card']
    if gradient:
        classes.append('gradient-bg')
    if glass:
        classes.append('glass-effect')
    if animate:
        classes.append('animate-hover')
    
    # Style de base
    base_style = {
        'padding': size_config['padding'],
        'border-radius': '16px',
        'position': 'relative',
        'overflow': 'hidden',
        'transition': 'all 0.3s ease',
        'box-shadow': '0 4px 12px var(--shadow)'
    }
    
    # Fusionner avec le style personnalisé
    if custom_style:
        base_style.update(custom_style)
    
    style_str = '; '.join([f"{k}: {v}" for k, v in base_style.items()])
    
    # CSS spécifique
    st.markdown(f"""
    <style>
    .metric-card {{
        background: var(--surface);
        color: var(--text-primary);
    }}
    
    .gradient-bg {{
        background: var(--gradient) !important;
        color: white !important;
    }}
    
    .glass-effect {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    
    .animate-hover:hover {{
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 8px 24px var(--shadow);
    }}
    
    .metric-icon {{
        position: absolute;
        top: {size_config['padding']};
        right: {size_config['padding']};
        font-size: 2rem;
        opacity: 0.7;
    }}
    
    .metric-value {{
        font-size: {size_config['font_value']};
        font-weight: 700;
        margin: 0.5rem 0;
        font-variant-numeric: tabular-nums;
    }}
    
    .metric-title {{
        font-size: {size_config['font_title']};
        opacity: 0.8;
        font-weight: 500;
    }}
    
    .metric-delta {{
        font-size: 0.875rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        margin-top: 0.5rem;
    }}
    
    .delta-positive {{
        color: var(--success);
    }}
    
    .delta-negative {{
        color: var(--error);
    }}
    
    @keyframes slideInUp {{
        from {{
            opacity: 0;
            transform: translateY(20px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    .animate-in {{
        animation: slideInUp 0.5s ease-out;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Déterminer la couleur et l'icône du delta
    delta_html = ""
    if delta:
        delta_value = delta.replace('%', '').replace('+', '').replace('-', '')
        try:
            delta_num = float(delta_value)
            is_positive = delta_num > 0
            
            if delta_color == "inverse":
                is_positive = not is_positive
            
            delta_class = "delta-positive" if is_positive else "delta-negative"
            delta_icon = "↑" if is_positive else "↓"
            
            if delta_color != "off":
                delta_html = f"""
                <div class="metric-delta {delta_class}">
                    <span>{delta_icon}</span>
                    <span>{delta}</span>
                </div>
                """
        except:
            delta_html = f'<div class="metric-delta">{delta}</div>'
    
    # HTML de la carte
    card_html = f"""
    <div class="{' '.join(classes)} animate-in" style="{style_str}">
        {f'<div class="metric-icon">{icon}</div>' if icon else ''}
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

def render_info_card(
    title: str,
    content: str,
    icon: Optional[str] = None,
    color_scheme: str = "primary",
    expandable: bool = False,
    actions: Optional[List[Dict[str, Any]]] = None,
    glass: bool = False
):
    """
    Carte d'information moderne avec contenu riche
    
    Args:
        title: Titre de la carte
        content: Contenu (peut être du markdown)
        icon: Icône ou emoji
        color_scheme: 'primary', 'secondary', 'success', 'warning', 'error', 'info'
        expandable: Si True, le contenu peut être étendu/réduit
        actions: Liste d'actions [{label, callback, icon}]
        glass: Effect glassmorphism
    """
    # CSS pour la carte info
    st.markdown(f"""
    <style>
    .info-card {{
        background: var(--surface);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid var(--{color_scheme});
        transition: all 0.3s ease;
        position: relative;
    }}
    
    .info-card:hover {{
        box-shadow: 0 6px 20px var(--shadow);
        transform: translateX(4px);
    }}
    
    .info-card-header {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }}
    
    .info-card-icon {{
        font-size: 1.5rem;
        color: var(--{color_scheme});
    }}
    
    .info-card-title {{
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
    }}
    
    .info-card-content {{
        color: var(--text-secondary);
        line-height: 1.6;
    }}
    
    .info-card-actions {{
        display: flex;
        gap: 0.5rem;
        margin-top: 1rem;
        flex-wrap: wrap;
    }}
    
    .info-card-action {{
        padding: 0.375rem 0.75rem;
        border-radius: 6px;
        background: var(--{color_scheme});
        color: white;
        font-size: 0.875rem;
        font-weight: 500;
        border: none;
        cursor: pointer;
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
    }}
    
    .info-card-action:hover {{
        transform: translateY(-2px);
        box-shadow: 0 2px 8px var(--shadow);
        filter: brightness(1.1);
    }}
    
    .glass-info-card {{
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Générer un ID unique pour l'expandable
    import uuid
    card_id = str(uuid.uuid4())[:8]
    
    if expandable:
        with st.expander(f"{icon} {title}" if icon else title, expanded=False):
            st.markdown(content)
            
            if actions:
                cols = st.columns(len(actions))
                for i, action in enumerate(actions):
                    with cols[i]:
                        if st.button(
                            action.get('label', 'Action'),
                            key=f"action_{card_id}_{i}",
                            use_container_width=True
                        ):
                            if 'callback' in action:
                                action['callback']()
    else:
        # Card HTML non-expandable
        actions_html = ""
        if actions:
            action_buttons = []
            for action in actions:
                action_icon = action.get('icon', '')
                action_label = action.get('label', 'Action')
                action_buttons.append(f"""
                <button class="info-card-action">
                    {f'<span>{action_icon}</span>' if action_icon else ''}
                    <span>{action_label}</span>
                </button>
                """)
            actions_html = f'<div class="info-card-actions">{"".join(action_buttons)}</div>'
        
        card_classes = "info-card"
        if glass:
            card_classes += " glass-info-card"
        
        card_html = f"""
        <div class="{card_classes}">
            <div class="info-card-header">
                {f'<div class="info-card-icon">{icon}</div>' if icon else ''}
                <h3 class="info-card-title">{title}</h3>
            </div>
            <div class="info-card-content">
                {content}
            </div>
            {actions_html}
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)

def render_stat_cards_row(stats: List[Dict[str, Any]], columns: Optional[int] = None):
    """
    Affiche une rangée de cartes statistiques
    
    Args:
        stats: Liste de dictionnaires avec les propriétés des cartes
        columns: Nombre de colonnes (auto si None)
    """
    if not stats:
        return
    
    # Déterminer le nombre de colonnes
    if columns is None:
        columns = min(len(stats), 4)
    
    # CSS pour la grille
    st.markdown("""
    <style>
    .stats-grid {
        display: grid;
        gap: 1rem;
        margin: 1rem 0;
    }
    
    @media (min-width: 768px) {
        .stats-grid-2 { grid-template-columns: repeat(2, 1fr); }
        .stats-grid-3 { grid-template-columns: repeat(3, 1fr); }
        .stats-grid-4 { grid-template-columns: repeat(4, 1fr); }
    }
    
    @media (max-width: 767px) {
        .stats-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Créer les colonnes
    cols = st.columns(columns)
    
    for i, stat in enumerate(stats):
        col_index = i % columns
        with cols[col_index]:
            render_metric_card(**stat)

def render_chart_card(
    title: str,
    chart_figure: go.Figure,
    description: Optional[str] = None,
    height: int = 400,
    actions: Optional[List[Dict[str, Any]]] = None,
    glass: bool = False
):
    """
    Carte contenant un graphique avec header et actions
    
    Args:
        title: Titre du graphique
        chart_figure: Figure Plotly
        description: Description optionnelle
        height: Hauteur du graphique
        actions: Actions disponibles
        glass: Effet glassmorphism
    """
    # Container avec style
    with st.container():
        # Header
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"### {title}")
            if description:
                st.caption(description)
        
        with col2:
            if actions:
                # Menu d'actions
                action_choice = st.selectbox(
                    "",
                    options=[a['label'] for a in actions],
                    key=f"chart_actions_{title}",
                    label_visibility="collapsed"
                )
                
                # Exécuter l'action sélectionnée
                for action in actions:
                    if action['label'] == action_choice and 'callback' in action:
                        action['callback']()
        
        # Graphique avec style
        st.plotly_chart(
            chart_figure,
            use_container_width=True,
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': title.replace(' ', '_').lower(),
                    'height': height * 2,
                    'width': None,
                    'scale': 2
                }
            }
        )