"""
Système de navigation unifié et contextuel pour OptimPV
Gère la navigation adaptative selon le profil utilisateur
"""
import streamlit as st
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from .user_profile_manager import profile_manager, UserType

@dataclass
class NavigationItem:
    """Élément de navigation"""
    key: str
    title: str
    icon: str
    page_function: Optional[Callable] = None
    requires_data: bool = False
    children: Optional[Dict[str, 'NavigationItem']] = None
    
class UnifiedNavigationSystem:
    """Système de navigation centralisé et adaptatif"""
    
    def __init__(self):
        """Initialise le système de navigation"""
        self.profile_manager = profile_manager
        self._init_navigation_state()
        
    def _init_navigation_state(self):
        """Initialise l'état de navigation"""
        if 'navigation_history' not in st.session_state:
            st.session_state.navigation_history = []
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "Accueil"
        if 'breadcrumbs' not in st.session_state:
            st.session_state.breadcrumbs = []
            
    def render_navigation(self) -> None:
        """Affiche la navigation adaptée au profil utilisateur"""
        user_type = self.profile_manager.get_user_type()
        
        if user_type == UserType.CLIENT:
            self._render_client_navigation()
        elif user_type == UserType.INVESTOR:
            self._render_investor_navigation()
        elif user_type == UserType.ADMIN:
            self._render_admin_navigation()
        else:
            self._render_guest_navigation()
            
    def _render_client_navigation(self):
        """Navigation simplifiée pour les clients"""
        st.sidebar.markdown("### 🏠 Mon Espace Client")
        
        nav_items = [
            ("Tableau de Bord", "📊", "client_dashboard"),
            ("Mes Économies", "💰", "client_savings"),
            ("Ma Consommation", "⚡", "client_energy"),
            ("Comparaison Factures", "📄", "client_bills"),
            ("Questions Fréquentes", "❓", "client_faq")
        ]
        
        for title, icon, key in nav_items:
            if self._render_nav_button(title, icon, key):
                st.session_state.current_page = key
                self._update_breadcrumbs(title)
                st.rerun()
                
    def _render_investor_navigation(self):
        """Navigation complète pour les investisseurs"""
        st.sidebar.markdown("### 💼 Espace Investisseur")
        
        # Navigation principale
        main_sections = {
            "Vue d'ensemble": {
                "icon": "📈",
                "items": [
                    ("Dashboard Financier", "💹", "investor_dashboard"),
                    ("Indicateurs Clés", "🎯", "investor_kpis"),
                    ("Synthèse Exécutive", "📋", "investor_summary")
                ]
            },
            "Analyse Approfondie": {
                "icon": "🔍",
                "items": [
                    ("Cash-flow Détaillé", "💵", "investor_cashflow"),
                    ("Analyse de Sensibilité", "📊", "investor_sensitivity"),
                    ("Monte Carlo", "🎲", "investor_monte_carlo"),
                    ("Optimisation Prix", "🎯", "investor_optimization")
                ]
            },
            "Gestion des Risques": {
                "icon": "⚠️",
                "items": [
                    ("Matrice des Risques", "🔲", "investor_risk_matrix"),
                    ("Scénarios de Stress", "📉", "investor_stress_test"),
                    ("Couverture (DSCR)", "🛡️", "investor_dscr")
                ]
            },
            "Rapports & Export": {
                "icon": "📑",
                "items": [
                    ("Générer Rapport", "📄", "investor_report"),
                    ("Export Excel", "📊", "investor_excel"),
                    ("Export PowerBI", "📈", "investor_powerbi")
                ]
            }
        }
        
        for section, config in main_sections.items():
            with st.sidebar.expander(f"{config['icon']} {section}"):
                for title, icon, key in config['items']:
                    if self._render_nav_button(title, icon, key, compact=True):
                        st.session_state.current_page = key
                        self._update_breadcrumbs(section, title)
                        st.rerun()
                        
    def _render_admin_navigation(self):
        """Navigation complète pour les administrateurs"""
        st.sidebar.markdown("### ⚙️ Administration")
        
        # Sélecteur de vue rapide
        view_mode = st.sidebar.radio(
            "Mode de vue",
            ["Admin", "Client", "Investisseur"],
            horizontal=True
        )
        
        if view_mode == "Client":
            self._render_client_navigation()
        elif view_mode == "Investisseur":
            self._render_investor_navigation()
        else:
            # Navigation admin spécifique
            nav_items = [
                ("Configuration Globale", "⚙️", "admin_config"),
                ("Gestion Utilisateurs", "👥", "admin_users"),
                ("Import/Export Données", "📤", "admin_data"),
                ("Logs & Monitoring", "📊", "admin_logs"),
                ("Paramètres Système", "🔧", "admin_system")
            ]
            
            for title, icon, key in nav_items:
                if self._render_nav_button(title, icon, key):
                    st.session_state.current_page = key
                    self._update_breadcrumbs(title)
                    st.rerun()
                    
    def _render_guest_navigation(self):
        """Navigation limitée pour les visiteurs"""
        st.sidebar.markdown("### 👁️ Mode Découverte")
        
        nav_items = [
            ("Accueil", "🏠", "home"),
            ("Démonstration", "🎮", "demo"),
            ("Fonctionnalités", "✨", "features"),
            ("Tarifs", "💰", "pricing"),
            ("Contact", "📧", "contact")
        ]
        
        for title, icon, key in nav_items:
            if self._render_nav_button(title, icon, key):
                st.session_state.current_page = key
                self._update_breadcrumbs(title)
                st.rerun()
                
        # Call to action pour s'identifier
        st.sidebar.markdown("---")
        st.sidebar.info("💡 Connectez-vous pour accéder à toutes les fonctionnalités")
        
    def _render_nav_button(self, title: str, icon: str, key: str, 
                          compact: bool = False, disabled: bool = False) -> bool:
        """Affiche un bouton de navigation"""
        # Vérifier si la page nécessite des données
        requires_data = key in ["client_savings", "client_energy", "investor_dashboard", 
                               "investor_cashflow", "investor_optimization"]
        
        if requires_data and not st.session_state.get('data_imported', False):
            disabled = True
            
        # Style du bouton selon l'état
        is_current = st.session_state.current_page == key
        button_type = "primary" if is_current else "secondary"
        
        # Rendu compact ou normal
        if compact:
            label = f"{icon} {title[:20]}..." if len(title) > 20 else f"{icon} {title}"
        else:
            label = f"{icon} {title}"
            
        return st.sidebar.button(
            label,
            key=f"nav_{key}",
            disabled=disabled,
            type=button_type,
            use_container_width=True,
            help=f"Données requises" if disabled and requires_data else None
        )
        
    def _update_breadcrumbs(self, *items):
        """Met à jour le fil d'Ariane"""
        st.session_state.breadcrumbs = ["Accueil"] + list(items)
        
    def render_breadcrumbs(self):
        """Affiche le fil d'Ariane"""
        if len(st.session_state.breadcrumbs) > 1:
            breadcrumb_text = " > ".join(st.session_state.breadcrumbs)
            st.markdown(f"<small>📍 {breadcrumb_text}</small>", unsafe_allow_html=True)
            
    def render_page_header(self, title: str, subtitle: Optional[str] = None):
        """Affiche l'en-tête de page avec breadcrumbs"""
        self.render_breadcrumbs()
        
        # Titre adapté au profil
        user_profile = self.profile_manager.get_current_profile()
        if user_profile and user_profile.complexity_level == "simple":
            st.markdown(f"# {title}")
            if subtitle:
                st.markdown(f"*{subtitle}*")
        else:
            st.markdown(f"<h1 class='main-header'>{title}</h1>", unsafe_allow_html=True)
            if subtitle:
                st.markdown(f"<p class='subtitle'>{subtitle}</p>", unsafe_allow_html=True)
                
    def get_quick_actions(self) -> List[Tuple[str, str, Callable]]:
        """Retourne les actions rapides selon le profil"""
        user_type = self.profile_manager.get_user_type()
        
        if user_type == UserType.CLIENT:
            return [
                ("💰 Voir mes économies", "client_savings", None),
                ("📊 Mon tableau de bord", "client_dashboard", None),
                ("❓ Aide", "client_help", None)
            ]
        elif user_type == UserType.INVESTOR:
            return [
                ("📈 Analyse rapide", "investor_quick_analysis", None),
                ("💾 Export Excel", "investor_export", None),
                ("🎯 Optimiser", "investor_optimize", None)
            ]
        else:
            return [
                ("🎮 Démo", "demo", None),
                ("📧 Contact", "contact", None)
            ]
            
    def render_mobile_navigation(self):
        """Affiche la navigation optimisée mobile (bottom bar)"""
        # CSS pour la bottom navigation
        st.markdown("""
        <style>
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
            padding: 0.5rem;
            z-index: 999;
        }
        .bottom-nav-item {
            display: inline-block;
            width: 20%;
            text-align: center;
            padding: 0.5rem;
        }
        @media (min-width: 768px) {
            .bottom-nav { display: none; }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Navigation items pour mobile
        user_type = self.profile_manager.get_user_type()
        if user_type == UserType.CLIENT:
            nav_items = [
                ("🏠", "Accueil"),
                ("💰", "Économies"),
                ("⚡", "Conso"),
                ("📊", "Stats"),
                ("❓", "Aide")
            ]
        else:
            nav_items = [
                ("🏠", "Accueil"),
                ("📈", "Analyse"),
                ("💼", "Finance"),
                ("📑", "Rapports"),
                ("⚙️", "Plus")
            ]
            
        # Rendu de la navigation mobile
        cols = st.columns(len(nav_items))
        for idx, (icon, label) in enumerate(nav_items):
            with cols[idx]:
                if st.button(icon, key=f"mobile_nav_{idx}", help=label):
                    # Navigation logic
                    pass

# Instance globale
navigation = UnifiedNavigationSystem()