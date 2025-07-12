"""
Module UI unifié pour OptimPV
Composants intelligents et adaptatifs selon le profil utilisateur
"""

from .user_profile_manager import (
    UserProfileManager,
    UserType,
    UserProfile,
    profile_manager
)

from .unified_navigation import (
    UnifiedNavigationSystem,
    NavigationItem,
    navigation
)

from .smart_components import (
    SmartComponents,
    smart_components
)

__all__ = [
    # Gestionnaire de profils
    'UserProfileManager',
    'UserType', 
    'UserProfile',
    'profile_manager',
    
    # Navigation unifiée
    'UnifiedNavigationSystem',
    'NavigationItem',
    'navigation',
    
    # Composants intelligents
    'SmartComponents',
    'smart_components'
]

# Version du module UI
__version__ = "2.0.0"