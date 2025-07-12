"""
Storage Legacy - Redirection vers la nouvelle structure modulaire

Ce fichier maintient la compatibilité descendante en redirigeant vers 
la nouvelle structure modulaire du système de stockage OptimPV 2.0.

DEPRECATED: Utilisez 'from modules.storage import StorageModule' à la place.
"""

import warnings
from .storage.migration import show_migration_warning
from .storage import StorageModule, show_storage_ui

# Afficher l'avertissement de migration
show_migration_warning()

# Exporter les classes principales pour compatibilité descendante
__all__ = ['StorageModule', 'show_storage_ui']

# Message de migration
def __getattr__(name):
    if name in ['StorageModule', 'show_storage_ui']:
        warnings.warn(
            f"Importing {name} from modules.storage_legacy is deprecated. "
            f"Use 'from modules.storage import {name}' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return globals()[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")