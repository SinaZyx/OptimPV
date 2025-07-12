#!/usr/bin/env python3
"""
OptimPV - Intégration Protection EXE
===================================

Module d'intégration pour la protection de sécurité dans l'EXE OptimPV.
Gère l'authentification USB, la surveillance et les mesures de sécurité.
"""

import sys
import os
import time
import threading
import logging
from pathlib import Path

# Configuration du logger pour ce module
logger = logging.getLogger(__name__)

# Ajouter le répertoire de sécurité au path si nécessaire
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Import des modules de sécurité avec gestion d'erreur
try:
    from hardware_protection import HardwareProtection
    from usb_surveillance_exe import USBSurveillanceEXE
    from lockdown_actions import execute_full_lockdown
    logger.info("Modules de sécurité chargés avec succès")
except ImportError as e:
    logger.error(f"Modules de sécurité non disponibles: {e}")
    HardwareProtection = None
    USBSurveillanceEXE = None
    execute_full_lockdown = None

def check_initial_authorization():
    """Vérifie l'autorisation dès le démarrage - Lockdown immédiat si refusé"""
    if not getattr(sys, 'frozen', False):
        logger.info("Mode développement - Sécurité désactivée")
        return True
    
    if not HardwareProtection:
        return True
    
    try:
        hw_protection = HardwareProtection()
        
        # Vérification USB
        usb_valid, usb_message = hw_protection.verify_usb_token()
        if usb_valid:
            logger.info(f"[CLE] Accès autorisé par clé USB: {usb_message}")
            return True
        
        # Si pas d'USB, vérifier MAC
        mac_valid, mac_message = hw_protection.verify_machine_license()
        if mac_valid:
            # MAC autorisée mais pas d'USB = mode restreint (pas de lockdown)
            logger.info(f"[OK] Accès autorisé par licence: {mac_message}")
            return True
        
        # Ni USB ni MAC autorisée = LOCKDOWN IMMÉDIAT
        logger.critical("[CRITIQUE] Accès refusé - MAC non autorisée et pas d'USB")
        logger.critical("[LOCKDOWN] Déclenchement immédiat du lockdown complet")
        
        # Déclencher le lockdown immédiatement
        if execute_full_lockdown:
            try:
                execute_full_lockdown()
            except Exception as e:
                logger.error(f"[ERREUR] Erreur lockdown: {e}")
                # Fallback: fermeture brutale
                os._exit(1)
        else:
            logger.warning("Module lockdown non disponible - Fermeture")
            os._exit(1)
        
        return False
        
    except Exception as e:
        logger.error(f"[ERREUR] Erreur vérification autorisation: {e}")
        return False

def start_usb_surveillance():
    """Démarre la surveillance USB en arrière-plan"""
    if not USBSurveillanceEXE or not getattr(sys, 'frozen', False):
        return None
    
    try:
        logger.info("[SECURITE] Initialisation de la surveillance USB avancée...")
        surveillance = USBSurveillanceEXE()
        surveillance.start_monitoring()
        logger.info("[OK] Surveillance USB active - Protection anti-copie activée")
        return surveillance
    except Exception as e:
        logger.warning(f"[ATTENTION] Erreur initialisation surveillance USB: {e}")
        return None

def start_secure_control_panel():
    """Démarre le panneau de contrôle avec protection de sécurité"""
    try:
        # Import du launcher du panneau de contrôle
        sys.path.insert(0, str(Path(__file__).parent.parent / "launchers"))
        
        logger.info("[SECURITE] Démarrage du panneau de contrôle sécurisé...")
        
        # Essayer d'importer et démarrer le launcher EXE
        try:
            from exe_control_panel_launcher import start_control_panel_exe
            
            # Démarrer le serveur
            server_info = start_control_panel_exe()
            
            if server_info and server_info.get('success'):
                url = server_info.get('url', 'http://127.0.0.1:8504')
                port = server_info.get('port', 8504)
                
                logger.info(f"[OK] Panneau de contrôle disponible: {url}")
                
                # Ouvrir dans le navigateur
                import webbrowser
                try:
                    webbrowser.open(url)
                except Exception:
                    pass
                
                return {
                    'success': True,
                    'url': url,
                    'port': port,
                    'server_info': server_info
                }
            else:
                logger.error("[ERREUR] Impossible de démarrer le serveur")
                return {'success': False, 'error': 'Échec démarrage serveur'}
                
        except ImportError as e:
            logger.error(f"[ERREUR] Erreur d'import du serveur: {e}")
            
            # Fallback vers le launcher simple
            try:
                panel_file = Path(__file__).parent.parent / "core" / "server_control_panel.py"
                if not panel_file.exists():
                    logger.error(f"[ERREUR] Fichier panneau non trouvé: {panel_file}")
                    return {'success': False, 'error': 'Fichier panneau manquant'}
                
            except Exception as e2:
                logger.error(f"[ERREUR] Erreur fallback: {e2}")
                return {'success': False, 'error': str(e2)}
        
        # Si on arrive ici, essayer le démarrage direct
        try:
            from smart_control_panel_launcher import launch_smart_control_panel
            result = launch_smart_control_panel()
            
            if result and result.get('success'):
                url = result.get('url', 'http://127.0.0.1:8504')
                logger.info(f"[OK] Panneau de contrôle disponible: {url}")
                
                # Ouvrir dans le navigateur
                import webbrowser
                try:
                    webbrowser.open(url)
                except Exception:
                    pass
                
                return result
            else:
                logger.error("[ERREUR] Impossible de démarrer le serveur")
                return {'success': False, 'error': 'Échec démarrage serveur smart launcher'}
                
        except ImportError as e:
            logger.error(f"[ERREUR] Erreur d'import en mode développement: {e}")
            return {'success': False, 'error': str(e)}
            
    except Exception as e:
        logger.error(f"[ERREUR] Erreur lors du démarrage du panneau: {e}")
        return {'success': False, 'error': str(e)}

def start_persistent_server():
    """Démarre un serveur persistant avec protection"""
    try:
        # Démarrer le panneau de contrôle
        result = start_secure_control_panel()
        
        if result and result.get('success'):
            logger.warning("[ATTENTION] Le serveur tournera en continu avec protection active")
            
            # Boucle de maintien du serveur
            try:
                while True:
                    time.sleep(10)
                    # Ici on pourrait ajouter des vérifications périodiques
                    
            except KeyboardInterrupt:
                logger.info("\n[INFO] Arrêt demandé par l'utilisateur")
                return True
                
        else:
            logger.error("[ERREUR] Impossible de démarrer le serveur persistant")
            return False
            
    except Exception as e:
        logger.error(f"[ERREUR] Erreur serveur persistant: {e}")
        return False

def start_simple_server():
    """Démarre un serveur Streamlit simple"""
    try:
        # Import de l'application principale
        app_path = Path(__file__).parent.parent.parent.parent / "app.py"
        
        if app_path.exists():
            import subprocess
            import socket
            
            # Trouver un port disponible
            def find_free_port():
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', 0))
                    return s.getsockname()[1]
            
            port = find_free_port()
            url = f"http://127.0.0.1:{port}"
            
            logger.info(f"[OK] Serveur démarré: {url}")
            
            # Ouvrir dans le navigateur
            import webbrowser
            try:
                webbrowser.open(url)
            except Exception:
                pass
            
            # Démarrer Streamlit
            cmd = [
                sys.executable, "-m", "streamlit", "run", 
                str(app_path), "--server.port", str(port),
                "--server.headless", "true"
            ]
            
            subprocess.run(cmd)
            return True
            
        else:
            logger.error("[ERREUR] Impossible de démarrer le serveur")
            return False
            
    except Exception as e:
        logger.error(f"[ERREUR] Erreur serveur: {e}")
        return False

def trigger_lockdown_if_unauthorized():
    """Déclenche le lockdown si l'accès n'est pas autorisé"""
    if not getattr(sys, 'frozen', False):
        return
    
    if not HardwareProtection:
        return
    
    try:
        hw_protection = HardwareProtection()
        
        # Vérifier l'autorisation
        usb_valid, usb_message = hw_protection.verify_usb_token()
        mac_valid, mac_message = hw_protection.verify_machine_license()
        
        if not usb_valid and not mac_valid:
            logger.warning("[ALERTE] DÉCLENCHEMENT DU LOCKDOWN COMPLET")
            logger.warning("[VERROUILLAGE] MAC non autorisée - Suppression de l'application")
            
            if execute_full_lockdown:
                execute_full_lockdown()
            else:
                os._exit(1)
                
    except Exception as e:
        logger.error(f"[ERREUR] Erreur lors du lockdown: {e}")
        if execute_full_lockdown:
            execute_full_lockdown()
        else:
            os._exit(1)
    
    if not execute_full_lockdown:
        logger.warning("[ATTENTION] Module de sécurité non disponible - Fermeture simple")
        os._exit(1)

def apply_streamlit_metadata_patch():
    """Applique le patch pour les métadonnées Streamlit en mode EXE"""
    if getattr(sys, 'frozen', False):
        logger.info("[MOBILE] Mode EXE détecté")
        
        # Patch pour les métadonnées Streamlit
        try:
            import importlib.metadata
            original_metadata = importlib.metadata.metadata
            
            def patched_metadata(package_name):
                if package_name == 'streamlit':
                    # Retourner des métadonnées factices pour Streamlit
                    from email.message import EmailMessage
                    msg = EmailMessage()
                    msg['Name'] = 'streamlit'
                    msg['Version'] = '1.28.0'
                    return msg
                return original_metadata(package_name)
            
            importlib.metadata.metadata = patched_metadata
            logger.info("[OK] Patch métadonnées Streamlit appliqué")
        except Exception as e:
            logger.warning(f"[ATTENTION] Erreur patch métadonnées: {e}")
    else:
        logger.info("[OUTILS] Mode développement")

def show_security_status(security_protection_instance=None):
    """Affiche le statut de sécurité détaillé"""
    logger.info("\n[SECURITE] STATUT DE SÉCURITÉ:")
    logger.info(f"   • Protection active: {'[OK]' if security_protection_instance else '[NON]'}")
    logger.info(f"   • USB surveillée: {'[OK]' if security_protection_instance and hasattr(security_protection_instance, 'monitoring') else '[NON]'}")
    logger.info(f"   • Token présent: {'[OK]' if security_protection_instance and getattr(security_protection_instance, 'usb_present', False) else '[NON]'}")

def main():
    """Point d'entrée principal avec gestion des arguments"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--panel":
            start_secure_control_panel()
        elif sys.argv[1] == "--server":
            start_persistent_server()
        elif sys.argv[1] == "--status":
            show_security_status()
        else:
            logger.error(f"[ERREUR] Option inconnue: {sys.argv[1]}")
            sys.exit(1)
    else:
        start_optimpv_with_protection()

def show_main_menu_console(security_protection_instance=None):
    """Affiche le menu principal en mode console"""
    try:
        while True:
            logger.info("\n[CIBLE] OPTIMPV - MENU PRINCIPAL SÉCURISÉ")
            logger.info("=" * 50)
            
            # Afficher le statut de sécurité
            if security_protection_instance and HardwareProtection:
                hw_protection = HardwareProtection()
                usb_valid, _ = hw_protection.verify_usb_token()
                usb_status = "[OK]" if usb_valid else "[NON]"
                monitoring_status = "[ACTIF]" if hasattr(security_protection_instance, 'monitoring') else "[INACTIF]"
                logger.info(f"[SECURITE] SÉCURITÉ - USB: {usb_status} | Surveillance: {monitoring_status}")
            
            logger.info("\nOptions disponibles:")
            logger.info("1  Panneau de Contrôle Sécurisé")
            logger.info("2  Serveur Persistant avec Protection")
            logger.info("3  Vérifier le Statut de Sécurité")
            logger.info("0  Quitter")
            logger.info("")
            
            try:
                choice = input("Votre choix: ").strip()
                
                if choice == "1":
                    logger.info("[SECURITE] Démarrage du panneau de contrôle sécurisé...")
                    start_secure_control_panel()
                elif choice == "2":
                    start_persistent_server()
                elif choice == "3":
                    show_security_status(security_protection_instance)
                elif choice == "0":
                    break
                else:
                    logger.error("[ERREUR] Choix invalide. Veuillez sélectionner 0, 1, 2 ou 3.")
                    
            except KeyboardInterrupt:
                logger.info("\n[INFO] Arrêt demandé")
                break
                
    except Exception as e:
        logger.error(f"[ERREUR] Erreur dans le menu: {e}")

def show_security_status(security_protection_instance=None):
    """Affiche un rapport de sécurité détaillé"""
    logger.info("\n[RECHERCHE] RAPPORT DE SÉCURITÉ DÉTAILLÉ")
    logger.info("=" * 50)
    
    if not HardwareProtection:
        logger.warning("[ATTENTION] Modules de sécurité non disponibles")
        return
    
    try:
        hw_protection = HardwareProtection()
        
        # Informations machine
        machine_info = hw_protection.get_machine_info()
        logger.info("[PC] INFORMATIONS MACHINE:")
        logger.info(f"   • ID Machine: {machine_info['machine_id']}")
        logger.info(f"   • Processeur: {machine_info['processor']}")
        logger.info(f"   • Mode EXE: {'[OK]' if machine_info['is_exe'] else '[NON]'}")
        
        # Vérifications de sécurité
        logger.info("\n[VERIFICATIONS] VÉRIFICATIONS DE SÉCURITÉ:")
        
        # USB
        usb_valid, usb_message = hw_protection.verify_usb_token()
        logger.info(f"   • Token USB: {'[OK]' if usb_valid else '[NON]'} {usb_message}")
        
        # MAC
        mac_valid, mac_message = hw_protection.verify_machine_license()
        logger.info(f"   • Licence MAC: {'[OK]' if mac_valid else '[NON]'} {mac_message}")
        
        # Statut global
        overall_valid = usb_valid or mac_valid
        logger.info(f"   • Accès global: {'[OK] AUTORISÉ' if overall_valid else '[NON] REFUSÉ'}")
        
        # Surveillance active
        if security_protection_instance:
            logger.info("\n[SECURITE] SURVEILLANCE ACTIVE:")
            status = getattr(security_protection_instance, 'get_status', lambda: {})()
            logger.info(f"   • Protection active: {'[OK]' if status.get('protection_active') else '[NON]'}")
            logger.info(f"   • Surveillance USB: {'[OK]' if status.get('monitoring') else '[NON]'}")
            logger.info(f"   • Token présent: {'[OK]' if status.get('usb_present') else '[NON]'}")
            
            # Alertes de sécurité
            if status.get('protection_triggered'):
                logger.warning("   • [ATTENTION] PROTECTION DÉCLENCHÉE!")
                logger.warning("     - Une violation de sécurité a été détectée")
                logger.warning("     - Surveillance renforcée activée")
                logger.warning("     - Vérifiez la présence de votre token USB")
            
            if status.get('usb_removed_detected'):
                logger.warning("   • [ALERTE] RETRAIT USB DÉTECTÉ!")
                logger.warning("     - Le token USB a été retiré")
                logger.warning("     - Mode de protection activé")
                logger.warning("     - Réinsérez le token pour restaurer l'accès complet")
        
        # Recommandations
        if overall_valid:
            logger.info("   • [OK] Configuration de sécurité optimale")
        else:
            logger.warning("   • [ATTENTION] Accès non autorisé - Vérifiez votre token USB ou licence")
            
    except Exception as e:
        logger.error(f"[ERREUR] Erreur lors de l'affichage du statut: {e}")

def start_optimpv_with_protection():
    """Point d'entrée principal avec protection de sécurité complète"""
    # Appliquer les patches nécessaires
    apply_streamlit_metadata_patch()
    
    # Vérification d'autorisation initiale - LOCKDOWN IMMÉDIAT si refusé
    if not check_initial_authorization():
        # Si on arrive ici, c'est que le lockdown a échoué
        # Déclencher un lockdown de secours
        logger.warning("[ALERTE] DÉCLENCHEMENT DU LOCKDOWN COMPLET")
        logger.warning("[VERROUILLAGE] MAC non autorisée - Suppression de l'application")
        
        if execute_full_lockdown:
            try:
                execute_full_lockdown()
            except Exception as e:
                logger.error(f"[ERREUR] Erreur lors du lockdown: {e}")
                os._exit(1)
        else:
            logger.warning("[ATTENTION] Module de sécurité non disponible - Fermeture simple")
            os._exit(1)
        return
    
    # Démarrer la surveillance USB
    security_protection_instance = start_usb_surveillance()
    
    # Afficher le menu principal
    show_main_menu_console(security_protection_instance)

if __name__ == "__main__":
    main()