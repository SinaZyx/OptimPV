"""
Module de stockage OptimPV - Version 2.0 modulaire
=====================================

Ce module fournit un système complet de gestion de projets avec :
- Sauvegarde et chargement de projets
- Comparaison intelligente entre projets  
- Interface utilisateur intuitive
- Visualisations avancées

Usage:
    from modules.storage import StorageModule
    
    storage = StorageModule()
    storage.show_ui()
"""

from .core import StorageModule
from .project_manager import ProjectManager
from .comparison import ProjectComparison
from .data_utils import DataUtils
from .visualization import ComparisonVisualization
from .ui_components import UIComponents

# Fonction principale pour compatibilité descendante
def show_storage_ui():
    """Affiche l'interface utilisateur de stockage"""
    storage = StorageModule()
    storage.show_ui()

__all__ = [
    'StorageModule',
    'ProjectManager', 
    'ProjectComparison',
    'DataUtils',
    'ComparisonVisualization',
    'UIComponents',
    'show_storage_ui'
]

__version__ = "2.0.0"