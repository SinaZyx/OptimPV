#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitaires d'import pour OptimPV
=================================

Ce module gère les imports dynamiques pour éviter les problèmes
avec les noms de dossiers contenant des espaces.
"""

import os
import sys
import importlib.util
from pathlib import Path


def import_launcher_module(interface_path=None):
    """
    Import dynamique du module launcher pour éviter les problèmes avec les espaces
    
    Args:
        interface_path: Chemin vers le dossier Interface serveur
        
    Returns:
        StreamlitServerManager: Classe du gestionnaire de serveur Streamlit
    """
    if interface_path is None:
        # Détecter automatiquement le chemin
        current_dir = Path(__file__).parent
        interface_path = current_dir / "Interface serveur"
    
    interface_path = str(interface_path)
    
    # Ajouter le chemin au sys.path
    if interface_path not in sys.path:
        sys.path.insert(0, interface_path)
    
    try:
        # Essayer d'abord l'import normal après avoir ajouté le chemin
        import importlib
        importlib.invalidate_caches()  # Forcer le rechargement du cache
        import launcher  # type: ignore
        return launcher.StreamlitServerManager
    except ImportError:
        # Fallback avec import dynamique
        launcher_path = os.path.join(interface_path, "launcher.py")
        if os.path.exists(launcher_path):
            spec = importlib.util.spec_from_file_location("launcher", launcher_path)
            launcher_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(launcher_module)
            return launcher_module.StreamlitServerManager
        else:
            raise ImportError(f"Module launcher introuvable dans {launcher_path}")


def safe_import_cx_freeze():
    """Import sécurisé de cx_Freeze"""
    try:
        import cx_Freeze
        return cx_Freeze
    except ImportError:
        return None


def safe_import_pyinstaller():
    """Import sécurisé de PyInstaller"""
    try:
        import PyInstaller
        return PyInstaller
    except ImportError:
        return None


def safe_import_nuitka():
    """Import sécurisé de Nuitka"""
    try:
        import nuitka
        return nuitka
    except ImportError:
        return None 