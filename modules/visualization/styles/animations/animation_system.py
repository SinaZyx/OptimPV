"""
Système d'animations et transitions fluides pour l'interface
"""
import streamlit as st
from typing import Optional, List, Dict, Any, Literal
import random

class AnimationSystem:
    """Gestionnaire d'animations pour l'interface"""
    
    # Bibliothèque d'animations prédéfinies
    ANIMATIONS = {
        # Entrées
        'fadeIn': """
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
        """,
        
        'fadeInUp': """
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        """,
        
        'fadeInDown': """
            @keyframes fadeInDown {
                from {
                    opacity: 0;
                    transform: translateY(-30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        """,
        
        'fadeInLeft': """
            @keyframes fadeInLeft {
                from {
                    opacity: 0;
                    transform: translateX(-30px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
        """,
        
        'fadeInRight': """
            @keyframes fadeInRight {
                from {
                    opacity: 0;
                    transform: translateX(30px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
        """,
        
        'scaleIn': """
            @keyframes scaleIn {
                from {
                    opacity: 0;
                    transform: scale(0.8);
                }
                to {
                    opacity: 1;
                    transform: scale(1);
                }
            }
        """,
        
        'rotateIn': """
            @keyframes rotateIn {
                from {
                    opacity: 0;
                    transform: rotate(-90deg);
                }
                to {
                    opacity: 1;
                    transform: rotate(0);
                }
            }
        """,
        
        # Attention
        'pulse': """
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
        """,
        
        'shake': """
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
                20%, 40%, 60%, 80% { transform: translateX(10px); }
            }
        """,
        
        'bounce': """
            @keyframes bounce {
                0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
                40% { transform: translateY(-30px); }
                60% { transform: translateY(-15px); }
            }
        """,
        
        'glow': """
            @keyframes glow {
                0%, 100% { 
                    box-shadow: 0 0 5px rgba(30, 136, 229, 0.5);
                }
                50% { 
                    box-shadow: 0 0 20px rgba(30, 136, 229, 0.8);
                }
            }
        """,
        
        # Slides
        'slideInUp': """
            @keyframes slideInUp {
                from {
                    transform: translateY(100%);
                }
                to {
                    transform: translateY(0);
                }
            }
        """,
        
        'slideInDown': """
            @keyframes slideInDown {
                from {
                    transform: translateY(-100%);
                }
                to {
                    transform: translateY(0);
                }
            }
        """,
        
        'slideInLeft': """
            @keyframes slideInLeft {
                from {
                    transform: translateX(-100%);
                }
                to {
                    transform: translateX(0);
                }
            }
        """,
        
        'slideInRight': """
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                }
                to {
                    transform: translateX(0);
                }
            }
        """,
        
        # Spéciaux
        'gradient': """
            @keyframes gradient {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
        """,
        
        'float': """
            @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-20px); }
            }
        """,
        
        'spin': """
            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
        """,
        
        'wave': """
            @keyframes wave {
                0%, 100% { transform: rotate(0deg); }
                10%, 30%, 50%, 70%, 90% { transform: rotate(-10deg); }
                20%, 40%, 60%, 80% { transform: rotate(10deg); }
            }
        """
    }
    
    def __init__(self):
        """Initialise le système d'animations"""
        if 'animations_loaded' not in st.session_state:
            st.session_state.animations_loaded = set()
    
    def load_animations(self, animations: List[str]):
        """
        Charge les animations spécifiées
        
        Args:
            animations: Liste des noms d'animations à charger
        """
        new_animations = set(animations) - st.session_state.animations_loaded
        
        if new_animations:
            css = "<style>\n"
            for anim in new_animations:
                if anim in self.ANIMATIONS:
                    css += self.ANIMATIONS[anim] + "\n"
                    st.session_state.animations_loaded.add(anim)
            css += "</style>"
            
            st.markdown(css, unsafe_allow_html=True)
    
    def animate_element(
        self,
        element_class: str,
        animation: str,
        duration: float = 1.0,
        delay: float = 0,
        easing: str = "ease",
        iteration: int = 1,
        direction: Literal["normal", "reverse", "alternate", "alternate-reverse"] = "normal",
        fill_mode: Literal["none", "forwards", "backwards", "both"] = "both"
    ):
        """
        Applique une animation à un élément
        
        Args:
            element_class: Classe CSS de l'élément
            animation: Nom de l'animation
            duration: Durée en secondes
            delay: Délai avant le début
            easing: Fonction d'easing
            iteration: Nombre d'itérations (ou 'infinite')
            direction: Direction de l'animation
            fill_mode: Mode de remplissage
        """
        # Charger l'animation si nécessaire
        self.load_animations([animation])
        
        # Générer le CSS
        iteration_str = 'infinite' if iteration == -1 else str(iteration)
        
        css = f"""
        <style>
        .{element_class} {{
            animation: {animation} {duration}s {easing} {delay}s {iteration_str} {direction} {fill_mode};
        }}
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    def stagger_animation(
        self,
        parent_class: str,
        child_selector: str,
        animation: str,
        duration: float = 0.5,
        stagger_delay: float = 0.1,
        base_delay: float = 0
    ):
        """
        Applique une animation décalée aux enfants d'un élément
        
        Args:
            parent_class: Classe du parent
            child_selector: Sélecteur des enfants
            animation: Animation à appliquer
            duration: Durée de chaque animation
            stagger_delay: Délai entre chaque enfant
            base_delay: Délai de base
        """
        # Charger l'animation
        self.load_animations([animation])
        
        # CSS pour l'animation décalée
        css = f"""
        <style>
        .{parent_class} {child_selector} {{
            opacity: 0;
            animation: {animation} {duration}s ease-out forwards;
        }}
        """
        
        # Ajouter les délais pour chaque enfant
        for i in range(1, 21):  # Support jusqu'à 20 enfants
            delay = base_delay + (i - 1) * stagger_delay
            css += f"""
        .{parent_class} {child_selector}:nth-child({i}) {{
            animation-delay: {delay}s;
        }}
        """
        
        css += "</style>"
        st.markdown(css, unsafe_allow_html=True)
    
    def create_transition_classes(self):
        """Crée les classes CSS pour les transitions standards"""
        css = """
        <style>
        /* Transitions de base */
        .transition-all {
            transition: all 0.3s ease;
        }
        
        .transition-transform {
            transition: transform 0.3s ease;
        }
        
        .transition-opacity {
            transition: opacity 0.3s ease;
        }
        
        .transition-colors {
            transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
        }
        
        /* Hover effects */
        .hover-scale:hover {
            transform: scale(1.05);
        }
        
        .hover-lift:hover {
            transform: translateY(-4px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .hover-glow:hover {
            box-shadow: 0 0 20px rgba(30, 136, 229, 0.5);
        }
        
        .hover-rotate:hover {
            transform: rotate(5deg);
        }
        
        /* Click effects */
        .click-scale:active {
            transform: scale(0.95);
        }
        
        .click-pulse:active {
            animation: pulse 0.3s ease-out;
        }
        
        /* Loading states */
        .loading {
            position: relative;
            pointer-events: none;
            opacity: 0.7;
        }
        
        .loading::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 20px;
            height: 20px;
            margin: -10px 0 0 -10px;
            border: 2px solid var(--primary);
            border-radius: 50%;
            border-top-color: transparent;
            animation: spin 0.8s linear infinite;
        }
        
        /* Skeleton loading */
        .skeleton {
            background: linear-gradient(
                90deg,
                var(--surface) 25%,
                var(--surface-hover) 50%,
                var(--surface) 75%
            );
            background-size: 200% 100%;
            animation: skeleton-loading 1.5s ease-in-out infinite;
        }
        
        @keyframes skeleton-loading {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        
        /* Smooth scroll */
        .smooth-scroll {
            scroll-behavior: smooth;
        }
        
        /* Page transitions */
        .page-enter {
            animation: fadeInUp 0.5s ease-out;
        }
        
        .page-exit {
            animation: fadeOut 0.3s ease-in;
        }
        
        /* Card animations */
        .card-enter {
            animation: scaleIn 0.3s ease-out;
        }
        
        .card-hover {
            transition: all 0.3s ease;
        }
        
        .card-hover:hover {
            transform: translateY(-8px);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
        }
        
        /* Parallax effect */
        .parallax {
            transform: translateZ(0);
            will-change: transform;
        }
        
        /* Glassmorphism animation */
        .glass-animate {
            backdrop-filter: blur(0px);
            animation: glass-in 0.5s ease-out forwards;
        }
        
        @keyframes glass-in {
            to {
                backdrop-filter: blur(10px);
            }
        }
        
        /* Number counter animation */
        .number-animate {
            display: inline-block;
            animation: number-pop 0.5s ease-out;
        }
        
        @keyframes number-pop {
            0% {
                transform: scale(0.5);
                opacity: 0;
            }
            50% {
                transform: scale(1.2);
            }
            100% {
                transform: scale(1);
                opacity: 1;
            }
        }
        
        /* Success animation */
        .success-animate {
            animation: success-check 0.5s ease-out;
        }
        
        @keyframes success-check {
            0% {
                transform: scale(0) rotate(45deg);
                opacity: 0;
            }
            50% {
                transform: scale(1.2) rotate(45deg);
            }
            100% {
                transform: scale(1) rotate(45deg);
                opacity: 1;
            }
        }
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    def animate_number(
        self,
        start: float,
        end: float,
        duration: float = 2.0,
        element_id: str = None,
        format_func: Optional[callable] = None
    ):
        """
        Anime un compteur de nombre
        
        Args:
            start: Valeur de départ
            end: Valeur finale
            duration: Durée de l'animation
            element_id: ID de l'élément à animer
            format_func: Fonction de formatage
        """
        if not element_id:
            element_id = f"counter_{random.randint(1000, 9999)}"
        
        if not format_func:
            format_func = lambda x: f"{x:,.0f}"
        
        # JavaScript pour l'animation du compteur
        js = f"""
        <div id="{element_id}" class="number-animate">{format_func(start)}</div>
        <script>
        (function() {{
            const element = document.getElementById('{element_id}');
            const start = {start};
            const end = {end};
            const duration = {duration * 1000};
            const startTime = Date.now();
            
            function updateCounter() {{
                const now = Date.now();
                const progress = Math.min((now - startTime) / duration, 1);
                
                // Easing function
                const easeOutQuart = 1 - Math.pow(1 - progress, 4);
                
                const current = start + (end - start) * easeOutQuart;
                element.textContent = '{format_func("PLACEHOLDER")}'.replace('PLACEHOLDER', current.toFixed(0));
                
                if (progress < 1) {{
                    requestAnimationFrame(updateCounter);
                }}
            }}
            
            updateCounter();
        }})();
        </script>
        """
        
        st.markdown(js, unsafe_allow_html=True)
    
    def create_loading_animation(
        self,
        type: Literal["spinner", "dots", "bars", "pulse"] = "spinner",
        color: str = "var(--primary)",
        size: str = "medium"
    ):
        """
        Crée une animation de chargement
        
        Args:
            type: Type d'animation
            color: Couleur de l'animation
            size: Taille (small, medium, large)
        """
        sizes = {
            "small": "20px",
            "medium": "40px",
            "large": "60px"
        }
        
        size_value = sizes.get(size, sizes["medium"])
        
        if type == "spinner":
            html = f"""
            <div class="loading-spinner" style="
                width: {size_value};
                height: {size_value};
                border: 3px solid rgba(0, 0, 0, 0.1);
                border-top-color: {color};
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
                margin: 20px auto;
            "></div>
            """
        
        elif type == "dots":
            html = f"""
            <div class="loading-dots" style="
                display: flex;
                justify-content: center;
                gap: 8px;
                margin: 20px auto;
            ">
                <div style="
                    width: 12px;
                    height: 12px;
                    background: {color};
                    border-radius: 50%;
                    animation: pulse 1.4s ease-in-out infinite;
                "></div>
                <div style="
                    width: 12px;
                    height: 12px;
                    background: {color};
                    border-radius: 50%;
                    animation: pulse 1.4s ease-in-out 0.2s infinite;
                "></div>
                <div style="
                    width: 12px;
                    height: 12px;
                    background: {color};
                    border-radius: 50%;
                    animation: pulse 1.4s ease-in-out 0.4s infinite;
                "></div>
            </div>
            """
        
        elif type == "bars":
            html = f"""
            <div class="loading-bars" style="
                display: flex;
                justify-content: center;
                gap: 4px;
                margin: 20px auto;
                height: {size_value};
            ">
                <div style="
                    width: 4px;
                    background: {color};
                    animation: stretch 1.2s ease-in-out infinite;
                "></div>
                <div style="
                    width: 4px;
                    background: {color};
                    animation: stretch 1.2s ease-in-out 0.1s infinite;
                "></div>
                <div style="
                    width: 4px;
                    background: {color};
                    animation: stretch 1.2s ease-in-out 0.2s infinite;
                "></div>
                <div style="
                    width: 4px;
                    background: {color};
                    animation: stretch 1.2s ease-in-out 0.3s infinite;
                "></div>
                <div style="
                    width: 4px;
                    background: {color};
                    animation: stretch 1.2s ease-in-out 0.4s infinite;
                "></div>
            </div>
            <style>
            @keyframes stretch {
                0%, 40%, 100% { transform: scaleY(0.4); }
                20% { transform: scaleY(1); }
            }
            </style>
            """
        
        elif type == "pulse":
            html = f"""
            <div style="
                width: {size_value};
                height: {size_value};
                background: {color};
                border-radius: 50%;
                margin: 20px auto;
                animation: pulse 1.5s ease-in-out infinite;
            "></div>
            """
        
        st.markdown(html, unsafe_allow_html=True)

# Instance globale
animation_system = AnimationSystem()