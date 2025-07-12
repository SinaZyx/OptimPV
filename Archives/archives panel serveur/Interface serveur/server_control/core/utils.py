#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OptimPV - Utilitaires Communs
=============================

Fonctions utilitaires partagées entre les modules.
"""

import streamlit as st
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional, Any


def normalize_mac_address(mac_str):
    """
    Normalise une adresse MAC vers le format standard XX:XX:XX:XX:XX:XX
    
    Args:
        mac_str (str): Adresse MAC dans différents formats
        
    Returns:
        str: Adresse MAC normalisée ou None si invalide
    """
    if not mac_str:
        return None
    
    # Supprimer les espaces et convertir en minuscules
    mac_clean = mac_str.strip().lower()
    
    # Supprimer tous les séparateurs possibles
    mac_clean = mac_clean.replace(':', '').replace('-', '').replace('.', '').replace(' ', '')
    
    # Vérifier que c'est bien 12 caractères hexadécimaux
    if len(mac_clean) != 12:
        return None
    
    try:
        # Vérifier que tous les caractères sont hexadécimaux
        int(mac_clean, 16)
    except ValueError:
        return None
    
    # Reformater avec des deux-points
    formatted_mac = ':'.join([mac_clean[i:i+2] for i in range(0, 12, 2)])
    
    # Convertir en majuscules pour la cohérence
    return formatted_mac.upper()


def setup_project_paths():
    """Configure les chemins du projet pour les imports"""
    project_root = Path(__file__).parent.parent.parent.parent
    interface_serveur_path = project_root / "Interface serveur"
    
    if str(interface_serveur_path) not in sys.path:
        sys.path.insert(0, str(interface_serveur_path))
    
    return project_root, interface_serveur_path


def load_protection_module() -> Tuple[bool, Optional[Any], Optional[Any]]:
    """Charge le module de protection hardware de manière sécurisée"""
    try:
        security_path = os.path.join(os.path.dirname(__file__), '..', '..', 'security')
        if security_path not in sys.path:
            sys.path.append(security_path)
        
        # Import conditionnel avec gestion d'erreur
        import hardware_protection  # type: ignore
        return True, hardware_protection.require_license, hardware_protection.LicenseManager
    except ImportError:
        return False, None, None


def check_usb_access_realtime() -> Tuple[bool, str]:
    """Vérification en temps réel de l'accès USB"""
    protection_enabled, _, LicenseManager = load_protection_module()
    
    if not protection_enabled:
        return True, "Protection désactivée"
    
    if LicenseManager is None:
        return False, "Module de protection non disponible"
    
    try:
        license_manager = LicenseManager()
        check_usb_method = getattr(license_manager, 'check_usb_token', None)
        if check_usb_method:
            usb_valid, usb_message = check_usb_method()
            return usb_valid, usb_message
        return False, "Méthode USB non disponible"
    except Exception as e:
        return False, f"Erreur: {str(e)}"


def apply_custom_css():
    """Applique les styles CSS personnalisés"""
    st.markdown("""
    <style>
    .server-status-running {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .server-status-stopped {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .metric-container {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)


def show_page_header(title="OptimPV - Server Control Panel", subtitle="Interface de gestion du serveur d'optimisation photovoltaïque"):
    """Affiche l'en-tête de page standardisé"""
    st.markdown(f"""
    <h1 style='text-align: center; color: #2E8B57;'>
        🌞 {title}
    </h1>
    <p style='text-align: center; font-size: 1.2em; color: #555;'>
        {subtitle}
    </p>
    """, unsafe_allow_html=True)


def log_message(message, log_file=None):
    """Ajoute une entrée au log"""
    if log_file is None:
        # Utiliser AppData par défaut
        appdata_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'OptimPV')
        os.makedirs(appdata_dir, exist_ok=True)
        log_file = os.path.join(appdata_dir, "optimpv_server.log")
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}\n"
    
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception:
        pass  # Ignore les erreurs de log


def get_logs(log_file=None, lines=50):
    """Récupère les dernières lignes de log"""
    if log_file is None:
        # Utiliser AppData par défaut
        appdata_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'OptimPV')
        log_file = os.path.join(appdata_dir, "optimpv_server.log")
    
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                log_lines = f.readlines()
            return log_lines[-lines:] if len(log_lines) > lines else log_lines
        else:
            return ["Aucun log disponible"]
    except Exception as e:
        return [f"Erreur lecture logs: {str(e)}"]


@st.cache_data(ttl=30)
def load_network_config():
    """Charge la configuration réseau avec cache"""
    try:
        setup_project_paths()
        from admin_config import NetworkAdminConfig  # type: ignore
        admin_config = NetworkAdminConfig()
        return admin_config.get_network_config()
    except:
        return {
            "ip": "127.0.0.1",
            "port": 8502,
            "external_access": False
        }


def check_admin_module_available():
    """Vérifie si le module d'administration est disponible"""
    try:
        setup_project_paths()
        from admin_config import NetworkAdminConfig  # type: ignore
        return True, NetworkAdminConfig
    except ImportError:
        return False, None


def cleanup_duplicate_configs():
    """Nettoie les fichiers de configuration dupliqués"""
    import json
    from pathlib import Path
    
    # Fichier de référence (racine du projet)
    project_root, _ = setup_project_paths()
    main_config = project_root.parent / "network_admin_config.json"
    
    if not main_config.exists():
        return False, "Fichier de configuration principal non trouvé"
    
    # Lire la configuration de référence
    try:
        with open(main_config, 'r', encoding='utf-8') as f:
            reference_config = json.load(f)
    except Exception as e:
        return False, f"Erreur lecture config principale: {e}"
    
    # Fichiers à synchroniser
    config_locations = [
        project_root / "network_admin_config.json",
        project_root / "server_control" / "launchers" / "network_admin_config.json"
    ]
    
    synchronized = 0
    errors = []
    
    for config_file in config_locations:
        if config_file.exists():
            try:
                # Lire le fichier existant
                with open(config_file, 'r', encoding='utf-8') as f:
                    current_config = json.load(f)
                
                # Comparer et synchroniser si différent
                if current_config != reference_config:
                    with open(config_file, 'w', encoding='utf-8') as f:
                        json.dump(reference_config, f, indent=2, ensure_ascii=False)
                    synchronized += 1
                    
            except Exception as e:
                errors.append(f"{config_file.name}: {e}")
    
    if errors:
        return False, f"Erreurs: {'; '.join(errors)}"
    
    return True, f"{synchronized} fichier(s) synchronisé(s)"


def validate_server_ports():
    """Valide la cohérence des ports de configuration"""
    try:
        network_config = load_network_config()
        configured_port = network_config.get('port', 8501)
        
        # Vérifier si un serveur tourne sur un port différent
        import psutil
        for conn in psutil.net_connections():
            if conn.status == 'LISTEN' and hasattr(conn, 'laddr') and conn.laddr:
                port = conn.laddr.port if hasattr(conn.laddr, 'port') else None
                if port and port in [8501, 8502, 8503, 8504]:
                    if port != configured_port:
                        return False, f"Serveur détecté sur port {port}, configuré pour {configured_port}"
        
        return True, f"Configuration port cohérente: {configured_port}"
        
    except Exception as e:
        return False, f"Erreur validation ports: {e}" 