# -*- coding: utf-8 -*-
"""
Module de sécurité OptimPV
==========================

Ce module contient les fonctionnalités de protection hardware et de gestion des licences.
"""

# Import des classes principales pour faciliter l'utilisation
try:
    from .hardware_protection import HardwareProtection, LicenseManager, require_license
    __all__ = ['HardwareProtection', 'LicenseManager', 'require_license']
except ImportError:
    # Si le module hardware_protection n'est pas disponible
    __all__ = [] 