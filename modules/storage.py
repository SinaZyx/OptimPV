"""
Module de compatibilité pour l'import de StorageModule

Ce fichier assure la compatibilité avec l'ancienne structure d'import.
"""

# Import depuis le nouveau package storage
from .storage.core import StorageModule
from .storage import (
    ProjectManager,
    ProjectComparison,
    DataUtils,
    ComparisonVisualization,
    UIComponents,
    show_storage_ui
)

# Export pour compatibilité
__all__ = [
    'StorageModule',
    'ProjectManager', 
    'ProjectComparison',
    'DataUtils',
    'ComparisonVisualization',
    'UIComponents',
    'show_storage_ui'
]