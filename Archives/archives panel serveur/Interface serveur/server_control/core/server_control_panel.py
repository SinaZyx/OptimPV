#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OptimPV - Panneau de Contrôle Serveur (Version Modulaire)
=========================================================

Interface de contrôle simplifiée utilisant des modules séparés.
"""

import streamlit as st
import time
import sys
import os
from pathlib import Path
import threading

# Ajouter le chemin du projet pour les imports
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Ajouter le chemin Interface serveur pour les imports
interface_serveur_path = project_root / "Interface serveur"
if str(interface_serveur_path) not in sys.path:
    sys.path.insert(0, str(interface_serveur_path))

# Ajouter le chemin pour les modules de sécurité
security_modules_path = project_root / "Interface serveur" / "server_control" / "security"
if str(security_modules_path) not in sys.path:
    sys.path.insert(0, str(security_modules_path))

# Fonction d'import robuste
def safe_import_module(module_name, function_names=None):
    """Importe un module de manière sécurisée avec plusieurs fallbacks"""
    # Essayer d'abord l'import direct depuis le dossier core
    try:
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        module = __import__(module_name, fromlist=function_names or [])
        return module
    except ImportError:
        pass
    
    # Essayer import depuis server_control.core
    try:
        module = __import__(f"server_control.core.{module_name}", fromlist=function_names or [])
        return module
    except ImportError:
        pass
    
    # Essayer import relatif seulement si on est dans un contexte de package
    try:
        # Vérifier si on peut faire un import relatif
        current_module = globals().get('__name__', '')
        if current_module and current_module != "__main__" and "." in current_module:
            module = __import__(f".{module_name}", fromlist=function_names or [], level=1)
            return module
    except (ImportError, ValueError, KeyError):
        pass
    
    # Dernier fallback - charger le fichier directement avec importlib
    try:
        import importlib.util
        module_path = current_dir / f"{module_name}.py"
        if module_path.exists():
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
    except Exception:
        pass
    
    return None

# Imports avec gestion robuste
utils_module = safe_import_module("utils", ["apply_custom_css", "show_page_header", "check_usb_access_realtime", "load_protection_module", "check_admin_module_available"])
server_manager_module = safe_import_module("server_manager", ["OptimPVServerManager", "show_server_control_tab"])

if utils_module:
    apply_custom_css = utils_module.apply_custom_css
    show_page_header = utils_module.show_page_header
    check_usb_access_realtime = utils_module.check_usb_access_realtime
    load_protection_module = utils_module.load_protection_module
    check_admin_module_available = utils_module.check_admin_module_available
else:
    st.error("❌ Impossible de charger le module utils")
    st.stop()

if server_manager_module:
    OptimPVServerManager = server_manager_module.OptimPVServerManager
    show_server_control_tab = server_manager_module.show_server_control_tab
else:
    st.error("❌ Impossible de charger le module server_manager")
    st.stop()

# Importer le module d'actions de lockdown
try:
    import lockdown_actions
    LOCKDOWN_ACTIONS_AVAILABLE = True
except ImportError:
    LOCKDOWN_ACTIONS_AVAILABLE = False
    # Fallback: tenter un import relatif si server_control_panel est exécuté comme partie d'un package plus grand
    try:
        from ..security import lockdown_actions # Si core et security sont des sous-packages
        LOCKDOWN_ACTIONS_AVAILABLE = True
    except (ImportError, ValueError):
        print("WARN: Impossible de charger lockdown_actions directement ou relativement.")
        # Essayer d'ajouter le chemin explicitement et retenter
        # Cela est déjà fait plus haut, donc si ça échoue ici, c'est un problème plus profond.
        pass 

# Configuration de la page
try:
    st.set_page_config(
        page_title="OptimPV - Server Control Panel",
        page_icon="🌞",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except Exception:
    # Page déjà configurée
    pass

def check_security_access():
    """Vérifie l'accès sécurisé (USB + licence)"""
    protection_enabled, _, LicenseManager = load_protection_module()
    
    if not protection_enabled:
        return True, "Protection désactivée", False
    
    if LicenseManager is None:
        return False, "Module de protection non disponible", False
    
    try:
        license_manager = LicenseManager()
        
        # Vérifier d'abord le token USB (priorité)
        check_usb_method = getattr(license_manager, 'check_usb_token', None)
        if check_usb_method:
            usb_valid, usb_message = check_usb_method()
            if usb_valid:
                return True, f"🔑 {usb_message}", True  # Accès complet + USB
        
        # Vérifier ensuite la licence classique
        authorized, message = license_manager.check_license()
        return authorized, f"✅ {message}" if authorized else f"❌ {message}", False
        
    except Exception as e:
        return False, f"❌ Erreur: {str(e)}", False

def show_simple_interface():
    """Interface simple pour utilisateurs sans accès complet"""
    
    show_page_header()
    apply_custom_css()
    
    # CSS pour cacher la sidebar en mode restreint
    st.markdown("""
    <style>
    .css-1d391kg {display: none !important;}
    .css-1rs6os {display: none !important;}
    .css-17eq0hr {display: none !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    .css-1lcbmhc {margin-left: 0rem !important;}
    .css-1outpf7 {margin-left: 0rem !important;}
    </style>
    """, unsafe_allow_html=True)
    
    # Interface restreinte - Aucun accès administrateur sans token USB
    
    # Gestionnaire de serveur
    server_manager = OptimPVServerManager()
    server_running = server_manager.is_server_running()
    
    # Informations d'état en haut de page (interface simple et propre)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 📊 État du Système")
        if server_running:
            st.success("🟢 Serveur OptimPV Actif")
        else:
            st.error("🔴 Serveur OptimPV Inactif")
    
    # Interface de contrôle serveur simple
    show_server_control_tab(server_manager, server_running)

def show_full_interface(has_usb_access, license_status):
    """Interface complète avec tous les onglets"""
    
    show_page_header("OptimPV - Server Control Panel (Mode Complet)")
    apply_custom_css()
    
    if has_usb_access:
        st.success(f"🔓 Accès complet autorisé - {license_status}")
    else:
        st.warning(f"🔐 Accès administrateur par mot de passe - {license_status}")
    
    # Initialisation du gestionnaire de serveur
    server_manager = OptimPVServerManager()
    server_running = server_manager.is_server_running()

    # Sidebar avec informations système
    with st.sidebar:
        st.header("📊 État du Système")
        
        if server_running:
            st.success("🟢 Serveur OptimPV Actif")
        else:
            st.error("🔴 Serveur OptimPV Inactif")

        # Informations sur la licence
        st.markdown("---")
        st.subheader("🔐 Statut d'Accès")
        
        if has_usb_access:
            st.success("✅ Accès complet")
        else:
            st.warning("⚠️ Accès limité")
        
        st.caption(license_status)
        
        # Bouton de vérification USB en temps réel
        st.markdown("---")
        st.subheader("🔑 Vérification USB")
        
        # Information sur le fonctionnement
        st.info("""
        💡 **Fonctionnement :**
        - Cliquez sur "Vérifier USB" pour détecter votre clé administrateur
        - Si détectée, cliquez sur "Actualiser" pour accéder aux fonctions avancées
        - Aucune vérification automatique (pas de refresh permanent)
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Vérifier USB", use_container_width=True, key="main_verify_usb"):
                usb_valid, usb_message = check_usb_access_realtime()
                if usb_valid:
                    st.success(f"✅ {usb_message}")
                    if not has_usb_access:
                        st.success("🔄 Clé USB détectée ! Actualisez la page pour accéder aux fonctions avancées.")
                        if st.button("🔄 Actualiser maintenant", key="usb_detected_refresh"):
                            st.rerun()
                else:
                    st.error(f"❌ {usb_message}")
                    if has_usb_access:
                        st.warning("⚠️ Clé USB non détectée. Actualisez la page si vous l'avez débranchée.")
        
        with col2:
            if st.button("🔄 Actualiser Page", use_container_width=True, key="main_refresh"):
                st.info("Page actualisée")
                st.rerun()

        # Statut USB
        if has_usb_access:
            st.success(f"🔑 USB: Connectée au démarrage")
        else:
            st.info(f"🔒 USB: Non détectée au démarrage")

        # Bouton de déconnexion forcée si pas d'USB (pour test)
        if not has_usb_access:
            st.markdown("---")
            st.subheader("🚪 Session")
            st.caption("Mode: Accès par mot de passe")
            if st.button("🚪 Se Déconnecter", use_container_width=True, key="logout_button", type="secondary"):
                # Retirer l'autorisation d'accès complet
                st.session_state.allow_full_access = False
                st.session_state.panel_authenticated = False
                st.success("✅ Déconnexion réussie")
                st.info("🔄 Redirection vers l'interface restreinte...")
                time.sleep(1)
                st.rerun()

        st.markdown("---")
        st.info("""
        **OptimPV Server Control Panel**
        
        Interface de gestion du serveur d'optimisation photovoltaïque.
        
        🔧 Contrôle du serveur
        📜 Monitoring des logs
        🔧 Administration réseau
        """)

    # Interface principale avec onglets conditionnels
    # Cacher l'onglet Administration si accès par mot de passe uniquement (sans USB)
    if has_usb_access:
        # Accès complet avec USB - tous les onglets disponibles
        tab1, tab2, tab3, tab4 = st.tabs([
            "🖥️ Contrôle Serveur", 
            "📜 Logs & Monitoring", 
            "🔧 Administration",
            "🔐 Licence"
        ])
        
        with tab1:
            show_server_control_tab(server_manager, server_running)
        
        with tab2:
            # Import paresseux du module de logs
            logs_module = safe_import_module("logs_monitoring", ["show_logs_monitoring_tab"])
            if logs_module and hasattr(logs_module, 'show_logs_monitoring_tab'):
                logs_module.show_logs_monitoring_tab(server_manager)
            else:
                st.error("Module de monitoring non disponible")
                st.info("Le module `logs_monitoring.py` est requis pour cette fonctionnalité.")
        
        with tab3:
            # Import paresseux du module d'administration
            admin_module = safe_import_module("admin_interface", ["show_admin_tab"])
            if admin_module and hasattr(admin_module, 'show_admin_tab'):
                admin_module.show_admin_tab()
            else:
                st.error("Module d'administration non disponible")
                st.info("Le module `admin_interface.py` est requis pour cette fonctionnalité.")
            
        with tab4:
            # Import paresseux du module de licence
            license_module = safe_import_module("license_manager_ui", ["show_license_tab"])
            if license_module and hasattr(license_module, 'show_license_tab'):
                license_module.show_license_tab()
            else:
                st.error("Module de licence non disponible")
                st.info("Le module `license_manager_ui.py` est requis pour cette fonctionnalité.")
    else:
        # Accès par mot de passe uniquement (MAC) - onglet Administration masqué
        tab1, tab2, tab3 = st.tabs([
            "🖥️ Contrôle Serveur", 
            "📜 Logs & Monitoring", 
            "🔐 Licence"
        ])
        
        with tab1:
            show_server_control_tab(server_manager, server_running)
        
        with tab2:
            # Import paresseux du module de logs
            logs_module = safe_import_module("logs_monitoring", ["show_logs_monitoring_tab"])
            if logs_module and hasattr(logs_module, 'show_logs_monitoring_tab'):
                logs_module.show_logs_monitoring_tab(server_manager)
            else:
                st.error("Module de monitoring non disponible")
                st.info("Le module `logs_monitoring.py` est requis pour cette fonctionnalité.")
            
        with tab3:
            # Import paresseux du module de licence
            license_module = safe_import_module("license_manager_ui", ["show_license_tab"])
            if license_module and hasattr(license_module, 'show_license_tab'):
                license_module.show_license_tab()
            else:
                st.error("Module de licence non disponible")
                st.info("Le module `license_manager_ui.py` est requis pour cette fonctionnalité.")
        
        # Message informatif sur les fonctions restreintes
        st.info("🔒 **Accès restreint** : L'onglet Administration nécessite la présence du token USB pour des raisons de sécurité.")

def main_control_panel():
    """Point d'entrée principal du panneau de contrôle"""
    
    # Initialiser st.session_state si nécessaire
    if 'access_level' not in st.session_state:
        st.session_state.access_level = "unknown"
    if 'reason_for_restriction' not in st.session_state:
        st.session_state.reason_for_restriction = ""
    if 'initial_auth_type' not in st.session_state:
        st.session_state.initial_auth_type = "unknown"

    # Vérifier le niveau d'accès dynamique défini par la surveillance USB
    access_mode = st.session_state.get('access_level')
    reason_for_restriction = st.session_state.get('reason_for_restriction', "")

    if access_mode == "lockdown":
        show_page_header("OptimPV - SÉCURITÉ ACTIVÉE")
        apply_custom_css()
        st.error("🚨 ALERTE DE SÉCURITÉ 🚨")
        st.error(f"Verrouillage du système activé. Raison: {reason_for_restriction}")
        st.warning("L'application est en cours de fermeture ou a été neutralisée.")
        if LOCKDOWN_ACTIONS_AVAILABLE:
            lockdown_actions.log_action(f"PANEL: Access mode 'lockdown'. Raison: {reason_for_restriction}. Arrêt de l'interface.")
        st.stop()

    if access_mode == "mac_restricted":
        show_simple_interface() 
        st.sidebar.info(reason_for_restriction or "Mode restreint activé suite au retrait de l'USB.")
        return

    # Vérifications de sécurité initiales
    has_full_access, license_status, has_usb_access = check_security_access()
    
    # LOGIQUE SIMPLIFIÉE : Plus d'authentification par mot de passe
    # Si USB présent = accès complet
    # Si MAC autorisée sans USB = mode restreint (pas d'élévation possible)
    # Si rien = accès refusé
    
    if has_usb_access:
        # Accès complet avec USB
        show_full_interface(has_usb_access, license_status)
    elif has_full_access and not has_usb_access:
        # MAC autorisée mais pas d'USB = mode restreint définitif
        show_simple_interface()
        st.sidebar.warning("🔒 Accès restreint (MAC uniquement). Token USB requis pour les fonctions avancées.")
    elif not has_full_access:
        # Aucun accès autorisé
        show_page_header("OptimPV - ACCÈS REFUSÉ")
        apply_custom_css()
        st.error("🚫 ACCÈS REFUSÉ AU PANNEAU DE CONTRÔLE")
        st.error(license_status)
        st.warning("Veuillez vérifier votre clé USB ou votre licence MAC.")
        
        if LOCKDOWN_ACTIONS_AVAILABLE:
            st.error("🔴 Licence invalide. Fermeture de l'application.")
            lockdown_actions.log_action(f"PANEL: Accès refusé: {license_status}. Fermeture.")
            st.session_state.access_level = "lockdown"
            st.session_state.reason_for_restriction = f"Accès refusé: {license_status}"
            
            # Fermeture immédiate sans lockdown destructeur
            thread_close = threading.Thread(target=lambda: (time.sleep(2), os._exit(1)), daemon=True)
            thread_close.start()
            st.warning("Fermeture de l'application...")
        else:
            st.error("ERREUR: Module de sécurité non disponible.")
        st.stop()
    else:
        show_page_header("OptimPV - ERREUR D'ACCÈS")
        apply_custom_css()
        st.error("Une erreur s'est produite lors de la vérification de l'accès.")
        st.stop()

if __name__ == "__main__":
    main_control_panel() 