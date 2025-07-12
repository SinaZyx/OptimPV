"""Module ERP pour la gestion des clients OptimPV.

Ce module centralise toutes les fonctionnalités de gestion clients:
- Gestion des fiches clients
- Autoconsommation collective
- Gestion des prix personnalisés
- Intégration cartographique
- Connexion avec le module de facturation
"""

__version__ = "1.0.0"
__author__ = "OptimPV Team"

# Import de l'interface principale uniquement
from .ui.main_interface import render_erp_module

__all__ = [
    "render_erp_module"
]