"""
Migration - Aide à la transition vers la structure modulaire
"""

import logging
import warnings

logger = logging.getLogger(__name__)

def show_migration_warning():
    """Affiche un avertissement sur la migration"""
    warnings.warn(
        "Le fichier storage.py a été décomposé en modules séparés. "
        "Utilisez 'from modules.storage import StorageModule' à la place.",
        DeprecationWarning,
        stacklevel=2
    )
    logger.info("Migration vers la structure modulaire détectée")

# Mapping des anciennes classes/fonctions vers les nouvelles
MIGRATION_MAP = {
    'StorageModule': 'modules.storage.StorageModule',
    'show_storage_ui': 'modules.storage.show_storage_ui'
}

def get_migration_info():
    """Retourne les informations de migration"""
    return {
        'version': '2.0.0',
        'modules': {
            'core': 'modules.storage.core',
            'project_manager': 'modules.storage.project_manager', 
            'comparison': 'modules.storage.comparison',
            'data_utils': 'modules.storage.data_utils',
            'ui_components': 'modules.storage.ui_components',
            'visualization': 'modules.storage.visualization'
        },
        'migration_notes': [
            "Le fichier storage.py a été décomposé en 6 modules spécialisés",
            "La classe StorageModule est maintenant dans modules.storage.core",
            "Utilisez 'from modules.storage import StorageModule' pour la compatibilité",
            "Toutes les fonctionnalités existantes sont préservées",
            "Performance améliorée grâce à la modularité"
        ]
    }