"""
Gestionnaire de profils utilisateurs pour OptimPV
Permet de différencier l'expérience selon le type d'utilisateur
"""
import streamlit as st
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class UserType(Enum):
    """Types d'utilisateurs supportés"""
    CLIENT = "client"
    INVESTOR = "investor"
    ADMIN = "admin"
    GUEST = "guest"

@dataclass
class UserProfile:
    """Configuration d'un profil utilisateur"""
    type: UserType
    name: str
    icon: str
    default_view: str
    allowed_pages: List[str]
    metrics_focus: List[str]
    theme_preference: str
    complexity_level: str  # simple, intermediate, advanced
    language: str = "fr"
    
class UserProfileManager:
    """Gestionnaire centralisé des profils utilisateurs"""
    
    # Configuration des profils
    PROFILES = {
        UserType.CLIENT: UserProfile(
            type=UserType.CLIENT,
            name="Client",
            icon="👤",
            default_view="client_dashboard",
            allowed_pages=[
                "Accueil",
                "Mon Tableau de Bord",
                "Mes Économies", 
                "Ma Consommation",
                "Mes Factures",
                "Support"
            ],
            metrics_focus=[
                "economie_mensuelle",
                "economie_totale", 
                "taux_autoconsommation",
                "reduction_facture",
                "temps_retour_simple"
            ],
            theme_preference="light",
            complexity_level="simple"
        ),
        
        UserType.INVESTOR: UserProfile(
            type=UserType.INVESTOR,
            name="Investisseur",
            icon="💼",
            default_view="investor_dashboard",
            allowed_pages=[
                "Accueil",
                "Vue Financière",
                "Analyse Détaillée",
                "Gestion des Risques",
                "Optimisation",
                "Rapports",
                "Export Données"
            ],
            metrics_focus=[
                "npv_projet",
                "tri_projet",
                "lcoe",
                "payback",
                "dscr_moyen",
                "cashflow_cumule"
            ],
            theme_preference="professional",
            complexity_level="advanced"
        ),
        
        UserType.ADMIN: UserProfile(
            type=UserType.ADMIN,
            name="Administrateur",
            icon="⚙️",
            default_view="admin_overview",
            allowed_pages="ALL",  # Accès à tout
            metrics_focus="ALL",
            theme_preference="system",
            complexity_level="expert"
        ),
        
        UserType.GUEST: UserProfile(
            type=UserType.GUEST,
            name="Visiteur",
            icon="👁️",
            default_view="demo",
            allowed_pages=[
                "Accueil",
                "Démonstration",
                "À Propos"
            ],
            metrics_focus=[
                "exemple_economie",
                "exemple_production"
            ],
            theme_preference="light",
            complexity_level="simple"
        )
    }
    
    def __init__(self):
        """Initialise le gestionnaire de profils"""
        if 'user_profile' not in st.session_state:
            st.session_state.user_profile = None
        if 'user_type' not in st.session_state:
            st.session_state.user_type = UserType.GUEST
            
    def set_user_type(self, user_type: UserType) -> None:
        """Définit le type d'utilisateur actuel"""
        st.session_state.user_type = user_type
        st.session_state.user_profile = self.PROFILES[user_type]
        
        # Appliquer les préférences
        self._apply_user_preferences()
        
    def get_current_profile(self) -> Optional[UserProfile]:
        """Retourne le profil utilisateur actuel"""
        return st.session_state.get('user_profile')
    
    def get_user_type(self) -> UserType:
        """Retourne le type d'utilisateur actuel"""
        return st.session_state.get('user_type', UserType.GUEST)
    
    def is_page_allowed(self, page_name: str) -> bool:
        """Vérifie si l'utilisateur a accès à une page"""
        profile = self.get_current_profile()
        if not profile:
            return False
            
        if profile.allowed_pages == "ALL":
            return True
            
        return page_name in profile.allowed_pages
    
    def get_allowed_pages(self) -> List[str]:
        """Retourne la liste des pages autorisées"""
        profile = self.get_current_profile()
        if not profile:
            return []
            
        if profile.allowed_pages == "ALL":
            # Retourner toutes les pages disponibles
            return [
                "Accueil", "Configuration", "Importation Données",
                "Analyse & Optimisation", "Carte de Prospection",
                "Facturation PMO", "Visualisation", "Rapports",
                "Historique", "Serveur"
            ]
            
        return profile.allowed_pages
    
    def get_focused_metrics(self) -> List[str]:
        """Retourne les métriques pertinentes pour l'utilisateur"""
        profile = self.get_current_profile()
        if not profile:
            return []
            
        if profile.metrics_focus == "ALL":
            return []  # Toutes les métriques
            
        return profile.metrics_focus
    
    def should_show_advanced_features(self) -> bool:
        """Détermine si les fonctionnalités avancées doivent être affichées"""
        profile = self.get_current_profile()
        if not profile:
            return False
            
        return profile.complexity_level in ["advanced", "expert"]
    
    def get_terminology(self, key: str) -> str:
        """Retourne la terminologie adaptée au profil"""
        terminology_map = {
            UserType.CLIENT: {
                "npv": "Gains totaux",
                "tri": "Rentabilité",
                "lcoe": "Coût de l'énergie",
                "payback": "Temps de retour",
                "cashflow": "Économies mensuelles",
                "dscr": "Sécurité financière"
            },
            UserType.INVESTOR: {
                "npv": "VAN (Valeur Actualisée Nette)",
                "tri": "TRI (Taux de Rendement Interne)",
                "lcoe": "LCOE (Levelized Cost of Energy)",
                "payback": "Période de récupération",
                "cashflow": "Flux de trésorerie",
                "dscr": "DSCR (Debt Service Coverage Ratio)"
            }
        }
        
        user_type = self.get_user_type()
        if user_type in terminology_map and key in terminology_map[user_type]:
            return terminology_map[user_type][key]
        return key
    
    def _apply_user_preferences(self) -> None:
        """Applique les préférences utilisateur"""
        profile = self.get_current_profile()
        if not profile:
            return
            
        # Stocker les préférences dans session_state
        st.session_state.theme_preference = profile.theme_preference
        st.session_state.complexity_level = profile.complexity_level
        st.session_state.user_language = profile.language
        
    def render_profile_selector(self) -> None:
        """Affiche le sélecteur de profil utilisateur"""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("### 👥 Sélectionnez votre profil")
            
            # Options de profil
            profile_options = {
                "👤 Client": UserType.CLIENT,
                "💼 Investisseur": UserType.INVESTOR,
                "👁️ Visiteur": UserType.GUEST
            }
            
            # Affichage en colonnes
            cols = st.columns(len(profile_options))
            
            for idx, (label, user_type) in enumerate(profile_options.items()):
                with cols[idx]:
                    if st.button(
                        label,
                        key=f"profile_{user_type.value}",
                        use_container_width=True,
                        type="primary" if self.get_user_type() == user_type else "secondary"
                    ):
                        self.set_user_type(user_type)
                        st.rerun()
                        
            # Description du profil sélectionné
            current_profile = self.get_current_profile()
            if current_profile and current_profile.type != UserType.GUEST:
                st.info(f"""
                **Profil {current_profile.name}** {current_profile.icon}
                
                • Accès : {', '.join(current_profile.allowed_pages[:3])}...
                • Niveau : {current_profile.complexity_level}
                • Focus : {', '.join(self.get_terminology(m) for m in current_profile.metrics_focus[:3])}...
                """)
    
    def get_navigation_config(self) -> Dict[str, Any]:
        """Retourne la configuration de navigation adaptée"""
        profile = self.get_current_profile()
        if not profile:
            return {}
            
        # Mapping des pages selon le profil
        if profile.type == UserType.CLIENT:
            return {
                "Mon Tableau de Bord": ("📊", "client_dashboard"),
                "Mes Économies": ("💰", "client_savings"),
                "Ma Consommation": ("⚡", "client_energy"),
                "Mes Factures": ("📄", "client_bills"),
                "Support": ("💬", "support")
            }
        elif profile.type == UserType.INVESTOR:
            return {
                "Vue Financière": ("💼", "investor_financial"),
                "Analyse Détaillée": ("📈", "investor_analysis"),
                "Gestion des Risques": ("⚠️", "investor_risks"),
                "Optimisation": ("🎯", "optimization"),
                "Rapports": ("📑", "reports"),
                "Export Données": ("💾", "export")
            }
        else:
            return {
                "Accueil": ("🏠", "home"),
                "Démonstration": ("🎮", "demo"),
                "À Propos": ("ℹ️", "about")
            }

# Instance globale
profile_manager = UserProfileManager()