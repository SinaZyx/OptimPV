#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core modules pour le système de cartographie de prospection OptimPV.

Ce package contient les modules principaux utilisés par l'application :
- data_handler : Gestion des données Enedis et géocodage
- ui : Interface utilisateur Streamlit
- map_visualizer_robust : Visualisation cartographique
- cadastre_analyzer : Analyse cadastrale et enrichissement
- Utilitaires divers (tooltips, satellite, etc.)
"""

# Imports principaux pour faciliter l'utilisation
# NOTE: Imports conditionnels pour éviter les erreurs de dépendances
try:
    from .data_handler import (
        load_and_process_data,
        enrich_single_building_on_demand,
        get_closest_communes_to_mougins
    )
    DATA_HANDLER_AVAILABLE = True
except ImportError:
    DATA_HANDLER_AVAILABLE = False

# UI est dans le dossier parent, pas dans core/
# from .ui import show_prospect_map_ui  # SUPPRIMÉ - UI pas dans core/

__version__ = "2.0.0"
__author__ = "OptimPV Team"

# Modules disponibles
__all__ = [
    'data_handler',
    'map_visualizer_robust',
    'cadastre_analyzer',
]

# Ajouter les fonctions seulement si disponibles
if DATA_HANDLER_AVAILABLE:
    __all__.extend([
        'load_and_process_data',
        'enrich_single_building_on_demand', 
        'get_closest_communes_to_mougins'
    ])