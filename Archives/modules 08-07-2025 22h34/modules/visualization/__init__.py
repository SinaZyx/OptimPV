"""
Module de visualisation restructure pour OptimPV
"""
from .main_visualization_ui import VisualizationModule

# Exports pour compatibilite
from .client import *
from .investor import *
from .shared import *

__all__ = [
    'VisualizationModule'
]