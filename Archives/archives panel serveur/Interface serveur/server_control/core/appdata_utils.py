#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OptimPV - Utilitaires AppData
============================

Fonctions utilitaires pour gérer les chemins AppData de manière centralisée.
"""

import os
from pathlib import Path


def get_optimpv_appdata_dir():
    """Retourne le répertoire AppData pour OptimPV"""
    appdata_base = os.environ.get('APPDATA', os.path.expanduser('~'))
    appdata_dir = os.path.join(appdata_base, 'OptimPV')
    os.makedirs(appdata_dir, exist_ok=True)
    return appdata_dir


def get_config_dir():
    """Retourne le répertoire de configuration dans AppData"""
    config_dir = os.path.join(get_optimpv_appdata_dir(), 'config')
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def get_logs_dir():
    """Retourne le répertoire des logs dans AppData"""
    logs_dir = os.path.join(get_optimpv_appdata_dir(), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir


def get_network_config_path():
    """Retourne le chemin complet du fichier de configuration réseau"""
    return os.path.join(get_optimpv_appdata_dir(), 'network_admin_config.json')


def get_panel_password_path():
    """Retourne le chemin complet du fichier de mot de passe du panneau"""
    return os.path.join(get_config_dir(), 'panel_password.json')


def get_server_log_path():
    """Retourne le chemin complet du fichier de log du serveur"""
    return os.path.join(get_logs_dir(), 'optimpv_server.log')


def get_launcher_log_path():
    """Retourne le chemin complet du fichier de log du launcher"""
    return os.path.join(get_logs_dir(), 'optimpv_launcher.log')


def show_appdata_info():
    """Affiche les informations sur l'emplacement des fichiers AppData"""
    appdata_dir = get_optimpv_appdata_dir()
    
    print(f"📁 Répertoire OptimPV AppData: {appdata_dir}")
    print(f"📁 Configuration: {get_config_dir()}")
    print(f"📁 Logs: {get_logs_dir()}")
    print(f"📄 Config réseau: {get_network_config_path()}")
    print(f"📄 Mot de passe: {get_panel_password_path()}")
    print(f"📄 Log serveur: {get_server_log_path()}")
    print(f"📄 Log launcher: {get_launcher_log_path()}")


def cleanup_old_files():
    """Nettoie les anciens fichiers de configuration dans le répertoire de l'exe"""
    old_files = [
        'network_admin_config.json',
        'optimpv_server.log',
        'optimpv_launcher.log',
        'config/panel_password.json'
    ]
    
    cleaned = []
    for old_file in old_files:
        if os.path.exists(old_file):
            try:
                os.remove(old_file)
                cleaned.append(old_file)
            except Exception as e:
                print(f"Impossible de supprimer {old_file}: {e}")
    
    # Supprimer le dossier config s'il est vide
    if os.path.exists('config') and not os.listdir('config'):
        try:
            os.rmdir('config')
            cleaned.append('config/')
        except Exception:
            pass
    
    return cleaned 