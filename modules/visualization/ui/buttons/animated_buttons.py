"""
Composants de boutons modernes avec animations et effets visuels
"""
import streamlit as st
from typing import Optional, Callable, Dict, Any, Literal
import uuid

def render_animated_button(
    label: str,
    on_click: Optional[Callable] = None,
    variant: Literal["primary", "secondary", "success", "danger", "ghost", "gradient"] = "primary",
    size: Literal["small", "medium", "large"] = "medium",
    icon: Optional[str] = None,
    icon_position: Literal["left", "right"] = "left",
    full_width: bool = False,
    disabled: bool = False,
    loading: bool = False,
    tooltip: Optional[str] = None,
    animate: bool = True,
    glow: bool = False,
    key: Optional[str] = None
) -> bool:
    """
    Bouton moderne avec animations et effets visuels
    
    Args:
        label: Texte du bouton
        on_click: Callback à exécuter au clic
        variant: Style du bouton
        size: Taille du bouton
        icon: Emoji ou symbole
        icon_position: Position de l'icône
        full_width: Prendre toute la largeur
        disabled: Désactiver le bouton
        loading: Afficher un état de chargement
        tooltip: Infobulle au survol
        animate: Activer les animations
        glow: Effet de lueur
        key: Clé unique Streamlit
        
    Returns:
        bool: True si cliqué
    """
    # Générer une clé unique si non fournie
    if not key:
        key = f"animated_btn_{uuid.uuid4().hex[:8]}"
    
    # Configuration des tailles
    sizes = {
        "small": {"padding": "0.375rem 0.75rem", "font": "0.875rem", "icon": "1rem"},
        "medium": {"padding": "0.5rem 1rem", "font": "1rem", "icon": "1.25rem"},
        "large": {"padding": "0.75rem 1.5rem", "font": "1.125rem", "icon": "1.5rem"}
    }
    
    size_config = sizes[size]
    
    # CSS pour les variantes
    st.markdown(f"""
    <style>
    .animated-btn-{key} {{
        position: relative;
        padding: {size_config['padding']};
        font-size: {size_config['font']};
        font-weight: 600;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        width: {'100%' if full_width else 'auto'};
        user-select: none;
        overflow: hidden;
    }}
    
    .animated-btn-{key}.primary {{
        background: var(--primary);
        color: white;
        box-shadow: 0 2px 8px rgba(30, 136, 229, 0.3);
    }}
    
    .animated-btn-{key}.primary:hover:not(:disabled) {{
        background: var(--primary-hover);
        box-shadow: 0 4px 12px rgba(30, 136, 229, 0.4);
        transform: translateY(-2px);
    }}
    
    .animated-btn-{key}.secondary {{
        background: var(--surface);
        color: var(--text-primary);
        border: 2px solid var(--border);
    }}
    
    .animated-btn-{key}.secondary:hover:not(:disabled) {{
        background: var(--surface-hover);
        border-color: var(--primary);
        color: var(--primary);
    }}
    
    .animated-btn-{key}.success {{
        background: var(--success);
        color: white;
        box-shadow: 0 2px 8px rgba(72, 187, 120, 0.3);
    }}
    
    .animated-btn-{key}.success:hover:not(:disabled) {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(72, 187, 120, 0.4);
        filter: brightness(1.1);
    }}
    
    .animated-btn-{key}.danger {{
        background: var(--error);
        color: white;
        box-shadow: 0 2px 8px rgba(245, 101, 101, 0.3);
    }}
    
    .animated-btn-{key}.danger:hover:not(:disabled) {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(245, 101, 101, 0.4);
        filter: brightness(1.1);
    }}
    
    .animated-btn-{key}.ghost {{
        background: transparent;
        color: var(--primary);
        border: none;
        padding: {size_config['padding']};
    }}
    
    .animated-btn-{key}.ghost:hover:not(:disabled) {{
        background: rgba(30, 136, 229, 0.1);
    }}
    
    .animated-btn-{key}.gradient {{
        background: var(--gradient);
        color: white;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }}
    
    .animated-btn-{key}.gradient:hover:not(:disabled) {{
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        filter: brightness(1.1);
    }}
    
    .animated-btn-{key}:disabled {{
        opacity: 0.5;
        cursor: not-allowed;
        transform: none !important;
    }}
    
    .animated-btn-{key}:active:not(:disabled) {{
        transform: translateY(0);
        box-shadow: 0 1px 4px var(--shadow);
    }}
    
    /* Effet de ripple au clic */
    .animated-btn-{key}::before {{
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        transform: translate(-50%, -50%);
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.5);
        transition: width 0.6s, height 0.6s;
    }}
    
    .animated-btn-{key}:active::before {{
        width: 300px;
        height: 300px;
    }}
    
    /* Animation de chargement */
    @keyframes spin {{
        to {{ transform: rotate(360deg); }}
    }}
    
    .btn-loading {{
        position: relative;
        color: transparent !important;
    }}
    
    .btn-loading::after {{
        content: '';
        position: absolute;
        width: 1rem;
        height: 1rem;
        top: 50%;
        left: 50%;
        margin-left: -0.5rem;
        margin-top: -0.5rem;
        border: 2px solid white;
        border-top-color: transparent;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }}
    
    /* Effet de lueur */
    .btn-glow {{
        animation: glow 2s ease-in-out infinite;
    }}
    
    @keyframes glow {{
        0%, 100% {{
            box-shadow: 0 0 20px rgba(30, 136, 229, 0.6);
        }}
        50% {{
            box-shadow: 0 0 30px rgba(30, 136, 229, 0.8);
        }}
    }}
    
    /* Animation d'entrée */
    @keyframes fadeInUp {{
        from {{
            opacity: 0;
            transform: translateY(10px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    .animate-in {{
        animation: fadeInUp 0.4s ease-out;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Classes du bouton
    classes = [f"animated-btn-{key}", variant]
    if loading:
        classes.append("btn-loading")
    if glow and not disabled:
        classes.append("btn-glow")
    if animate:
        classes.append("animate-in")
    
    # Contenu du bouton
    if loading:
        btn_content = ""
    else:
        icon_html = f'<span style="font-size: {size_config["icon"]};">{icon}</span>' if icon else ""
        
        if icon and icon_position == "right":
            btn_content = f'{label} {icon_html}'
        elif icon:
            btn_content = f'{icon_html} {label}'
        else:
            btn_content = label
    
    # Utiliser le bouton Streamlit avec style custom
    clicked = st.button(
        btn_content if not loading else "⠀" * len(label),  # Espace pour maintenir la taille
        key=key,
        help=tooltip,
        disabled=disabled or loading,
        use_container_width=full_width
    )
    
    if clicked and on_click:
        on_click()
    
    return clicked

def render_button_group(
    buttons: list[Dict[str, Any]],
    variant: str = "primary",
    size: str = "medium",
    orientation: Literal["horizontal", "vertical"] = "horizontal",
    spacing: str = "0.5rem",
    key: Optional[str] = None
):
    """
    Groupe de boutons avec style unifié
    
    Args:
        buttons: Liste de configs de boutons
        variant: Variante par défaut
        size: Taille par défaut
        orientation: Disposition des boutons
        spacing: Espacement entre boutons
        key: Clé unique
    """
    if not buttons:
        return
    
    # CSS pour le groupe
    group_key = key or f"btn_group_{uuid.uuid4().hex[:8]}"
    
    st.markdown(f"""
    <style>
    .button-group-{group_key} {{
        display: flex;
        flex-direction: {'column' if orientation == 'vertical' else 'row'};
        gap: {spacing};
        margin: 1rem 0;
        {'align-items: stretch;' if orientation == 'vertical' else 'flex-wrap: wrap;'}
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Container pour le groupe
    if orientation == "horizontal":
        cols = st.columns(len(buttons))
        for i, btn_config in enumerate(buttons):
            with cols[i]:
                render_animated_button(
                    variant=btn_config.get('variant', variant),
                    size=btn_config.get('size', size),
                    full_width=True,
                    **{k: v for k, v in btn_config.items() if k not in ['variant', 'size']}
                )
    else:
        for btn_config in buttons:
            render_animated_button(
                variant=btn_config.get('variant', variant),
                size=btn_config.get('size', size),
                full_width=True,
                **{k: v for k, v in btn_config.items() if k not in ['variant', 'size']}
            )

def render_floating_action_button(
    icon: str,
    on_click: Optional[Callable] = None,
    position: Literal["bottom-right", "bottom-left", "top-right", "top-left"] = "bottom-right",
    color: str = "primary",
    tooltip: Optional[str] = None,
    key: Optional[str] = None
) -> bool:
    """
    Bouton d'action flottant (FAB) avec animation
    
    Args:
        icon: Icône du bouton
        on_click: Callback au clic
        position: Position sur l'écran
        color: Couleur du bouton
        tooltip: Texte au survol
        key: Clé unique
        
    Returns:
        bool: True si cliqué
    """
    fab_key = key or f"fab_{uuid.uuid4().hex[:8]}"
    
    # Positions CSS
    positions = {
        "bottom-right": "bottom: 2rem; right: 2rem;",
        "bottom-left": "bottom: 2rem; left: 2rem;",
        "top-right": "top: 2rem; right: 2rem;",
        "top-left": "top: 2rem; left: 2rem;"
    }
    
    # CSS du FAB
    st.markdown(f"""
    <style>
    .fab-{fab_key} {{
        position: fixed;
        {positions[position]}
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: var(--{color});
        color: white;
        border: none;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transition: all 0.3s ease;
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    
    .fab-{fab_key}:hover {{
        transform: scale(1.1) rotate(15deg);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
    }}
    
    .fab-{fab_key}:active {{
        transform: scale(0.95);
    }}
    
    @keyframes fabEntrance {{
        from {{
            transform: scale(0) rotate(180deg);
            opacity: 0;
        }}
        to {{
            transform: scale(1) rotate(0);
            opacity: 1;
        }}
    }}
    
    .fab-{fab_key} {{
        animation: fabEntrance 0.5s ease-out;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Placeholder pour le FAB
    fab_placeholder = st.empty()
    
    # Bouton invisible pour la fonctionnalité
    clicked = st.button(
        icon,
        key=fab_key,
        help=tooltip,
        use_container_width=False
    )
    
    # HTML du FAB
    fab_html = f"""
    <button class="fab-{fab_key}" title="{tooltip or ''}" onclick="document.querySelector('[data-testid="baseButton-{fab_key}"]').click()">
        {icon}
    </button>
    """
    
    fab_placeholder.markdown(fab_html, unsafe_allow_html=True)
    
    if clicked and on_click:
        on_click()
    
    return clicked