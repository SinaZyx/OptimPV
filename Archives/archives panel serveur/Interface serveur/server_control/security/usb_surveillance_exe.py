#!/usr/bin/env python3
"""
OptimPV - Surveillance USB en Temps Réel pour EXE
================================================

Module de surveillance continue du token USB avec protection anti-copie
"""

import threading
import time
import os
import sys
import subprocess
import psutil
from typing import Optional, Callable
from hardware_protection import LicenseManager
import streamlit as st
# Import du nouveau module d'actions de lockdown
import lockdown_actions
from pathlib import Path

class USBWatchdog:
    """
    Chien de garde USB - Surveille la présence du token USB en continu
    
    Analogie: C'est comme un gardien de sécurité qui vérifie toutes les 2 secondes
    que votre badge d'accès est toujours présent. S'il disparaît -> ALERTE !
    """
    
    def __init__(self, drive_letter: str = "G", token_file: str = "sys.dat", 
                 check_interval: float = 2.0):
        self.drive_letter = drive_letter
        self.token_file = token_file
        self.check_interval = check_interval
        self.license_manager = LicenseManager()
        
        # État de surveillance
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.last_usb_status = False
        self.consecutive_failures = 0
        self.max_failures = 3  # Tolérance pour éviter les faux positifs
        
        # Callbacks
        self.on_usb_removed: Optional[Callable] = None
        self.on_usb_inserted: Optional[Callable] = None
        
        print(f"[SECURITE] Surveillance USB initialisée - Lecteur: {drive_letter}:")
    
    def set_callbacks(self, on_removed: Callable = None, on_inserted: Callable = None):
        """Définit les fonctions à appeler lors des événements USB"""
        self.on_usb_removed = on_removed
        self.on_usb_inserted = on_inserted
    
    def adaptive_check_interval(self):
        """Ajuste l'intervalle selon l'activité"""
        current_interval = self.check_interval
        if self.consecutive_failures > 5:
            # Ralentir si échecs répétés, jusqu'à un maximum de 30s ou 5x l'intervalle initial
            new_interval = min(max(30, current_interval * 5), current_interval * 1.5) 
            print(f"[SURVEILLANCE] Intervalle adapté à {new_interval:.2f}s (échecs: {self.consecutive_failures})")
            return new_interval
        # Si moins de 5 échecs, ou si la clé est présente, revenir à l'intervalle normal ou un peu plus rapide
        # On peut aussi envisager de réduire l'intervalle si la clé est présente et stable.
        # Pour l'instant, on retourne l'intervalle de base ou celui augmenté.
        print(f"[SURVEILLANCE] Intervalle de base utilisé: {current_interval:.2f}s")
        return current_interval

    def check_usb_windows_robust(self) -> bool: # Renommé pour refléter la spécificité Windows
        """Version robuste de détection USB pour Windows utilisant WMI et fallback."""
        # Méthode 1: WMI (plus robuste)
        try:
            import wmi # Import local pour éviter erreur si non dispo sur non-Windows
            # Tentative de logger l'utilisation de WMI
            try: from optimpv_main import logger; logger.write("[USBWatchdog] Using WMI for USB check.")
            except: print("[USBWatchdog] Using WMI for USB check (local print).")

            c = wmi.WMI()
            # Requête WMI plus stable
            # DriveType=2 signifie disque amovible
            target_device_id = f"{self.drive_letter}:"
            for disk in c.Win32_LogicalDisk(DriveType=2):
                if disk.DeviceID == target_device_id:
                    token_path = Path(disk.DeviceID) / self.token_file
                    # Tentative de logger le chemin vérifié
                    try: from optimpv_main import logger; logger.write(f"[USBWatchdog] WMI Check: Checking for {token_path}")
                    except: print(f"[USBWatchdog] WMI Check: Checking for {token_path} (local print).")
                    return token_path.exists()
            # Tentative de logger si le disque n'est pas trouvé via WMI
            try: from optimpv_main import logger; logger.write(f"[USBWatchdog] WMI Check: Drive {target_device_id} not found among removable drives.")
            except: print(f"[USBWatchdog] WMI Check: Drive {target_device_id} not found among removable drives (local print).")
            return False # Disque non trouvé ou n'est pas un disque amovible
        except ImportError:
            # Tentative de logger l'échec d'import de WMI
            try: from optimpv_main import logger; logger.write("[USBWatchdog] WMI module not found. Falling back to basic path check.")
            except: print("[USBWatchdog] WMI module not found. Falling back to basic path check (local print).")
            # Fallback sur méthode basique si wmi n'est pas installé ou échec
            return self._basic_path_check()
        except Exception as e:
            # Tentative de logger l'erreur WMI
            try: from optimpv_main import logger; logger.write(f"[USBWatchdog] WMI error: {e}. Falling back to basic path check.")
            except: print(f"[USBWatchdog] WMI error: {e}. Falling back to basic path check (local print).")
            # Fallback sur méthode basique en cas d'autre erreur WMI
            return self._basic_path_check()

    def _basic_path_check(self) -> bool:
        """Vérification basique par chemin direct."""
        token_path = Path(f"{self.drive_letter}:") / self.token_file
        # Tentative de logger le chemin vérifié en fallback
        try: from optimpv_main import logger; logger.write(f"[USBWatchdog] Basic Check: Checking for {token_path}")
        except: print(f"[USBWatchdog] Basic Check: Checking for {token_path} (local print).")
        return token_path.exists()
    
    def check_usb_token(self) -> bool: # Reste la méthode principale appelée, qui délègue
        """Vérification du token USB, utilisant la méthode robuste pour Windows."""
        if sys.platform == "win32":
            # Tentative de logger l'utilisation de la méthode Windows
            try: from optimpv_main import logger; logger.write("[USBWatchdog] Using Windows-specific USB check.")
            except: print("[USBWatchdog] Using Windows-specific USB check (local print).")
            return self.check_usb_windows_robust()
        else:
            # Pour les autres OS, utiliser la méthode basique ou une autre spécifique si développée
            # Tentative de logger l'utilisation de la méthode basique pour non-Windows
            try: from optimpv_main import logger; logger.write("[USBWatchdog] Using basic path check for non-Windows OS.")
            except: print("[USBWatchdog] Using basic path check for non-Windows OS (local print).")
            return self._basic_path_check() # Ou self.license_manager.check_usb_token si c'est différent
    
    def start_monitoring(self):
        """Démarre la surveillance USB en arrière-plan"""
        if self.is_monitoring:
            print("[ATTENTION] Surveillance déjà active")
            return
        
        print(f"[SURVEILLANCE] Démarrage de la surveillance USB...")
        
        # Vérifier l'état initial
        initial_status = self.check_usb_token()
        self.last_usb_status = initial_status
        
        if initial_status:
            print(f"[OK] Token USB détecté au démarrage sur {self.drive_letter}:")
        else:
            print(f"[ATTENTION] Token USB non détecté sur {self.drive_letter}: au démarrage")
        
        # Démarrer le thread de surveillance
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        print("[OK] Surveillance USB active")
    
    def stop_monitoring(self):
        """Arrête la surveillance USB"""
        if self.is_monitoring:
            print("[OK] Surveillance USB arrêtée")
            self.is_monitoring = False
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=1)
    
    def _monitor_loop(self):
        """Boucle de surveillance principale (thread séparé)"""
        # Utilisation du logger global s'il est disponible
        try:
            from optimpv_main import logger
            logger.write(f"[SURVEILLANCE] Thread de surveillance démarré (intervalle initial: {self.check_interval}s)")
        except ImportError:
            print(f"[SURVEILLANCE] Thread de surveillance démarré (intervalle initial: {self.check_interval}s) - Logger global non trouvé.")

        while self.is_monitoring:
            current_check_interval = self.adaptive_check_interval()
            try:
                current_status = self.check_usb_token() # Utilise la méthode mise à jour
                
                # Détecter les changements d'état
                if current_status != self.last_usb_status:
                    if current_status:
                        # USB réinsérée
                        print(f"[OK] Token USB détecté sur {self.drive_letter}:")
                        self.consecutive_failures = 0
                        if self.on_usb_inserted:
                            self.on_usb_inserted()
                    else:
                        # USB retirée - incrémenter le compteur d'échecs
                        self.consecutive_failures += 1
                        print(f"[ATTENTION] Token USB non détecté ({self.consecutive_failures}/{self.max_failures})")
                        
                        # Déclencher la protection seulement après plusieurs échecs
                        if self.consecutive_failures >= self.max_failures:
                            print(f"[ALERTE] ALERTE: Token USB retiré définitivement!")
                            if self.on_usb_removed:
                                self.on_usb_removed()
                            # Arrêter la surveillance après déclenchement
                            self.is_monitoring = False
                            break
                
                else:
                    # État inchangé
                    if current_status:
                        # USB toujours présente - reset du compteur
                        self.consecutive_failures = 0
                    else:
                        # USB toujours absente - incrémenter si on était en état "présent" avant
                        if self.last_usb_status:
                            self.consecutive_failures += 1
                
                self.last_usb_status = current_status
                
            except Exception as e:
                print(f"[ERREUR] Erreur surveillance USB: {e}")
                self.consecutive_failures += 1
            
            # Attendre avant la prochaine vérification
            # time.sleep(self.check_interval) # Ancienne méthode
            time.sleep(current_check_interval) # Nouvelle méthode avec intervalle adaptatif
        
        try:
            from optimpv_main import logger
            logger.write("[SURVEILLANCE] Thread de surveillance terminé")
        except ImportError:
            print("[SURVEILLANCE] Thread de surveillance terminé - Logger global non trouvé.")
    
    def get_status(self) -> dict:
        """Retourne l'état actuel de la surveillance"""
        return {
            "monitoring": self.is_monitoring,
            "usb_present": self.last_usb_status,
            "consecutive_failures": self.consecutive_failures,
            "drive_letter": self.drive_letter,
            "token_file": self.token_file
        }


class SecurityProtection:
    """
    Protection de sécurité avancée pour EXE
    
    Analogie: C'est le système d'alarme complet de votre voiture.
    Si quelqu'un essaie de voler la voiture (retirer la clé USB),
    l'alarme se déclenche et active toutes les protections.
    """
    
    def __init__(self):
        self.usb_watchdog = None
        self.protection_triggered = False
        self.mac_restricted_mode = False
    
    def initialize_protection(self, drive_letter: str = "G", token_file: str = "sys.dat"):
        """Initialise la protection USB"""
        print("[SECURITE] Initialisation de la protection de sécurité...")
        
        self.usb_watchdog = USBWatchdog(drive_letter, token_file)
        
        self.usb_watchdog.set_callbacks(
            on_removed=self.handle_usb_removal,
            on_inserted=self.on_usb_reinserted
        )
        
        self.usb_watchdog.start_monitoring()
        
        print("[OK] Protection de sécurité active")
    
    def on_usb_reinserted(self):
        """Appelé quand la clé USB est réinsérée"""
        print("[OK] Mode complet restauré avec USB")
        # Réactiver le mode complet si l'USB revient
        self.mac_restricted_mode = False
        self.protection_triggered = False
        if hasattr(st, 'session_state'):
            st.session_state.access_level = "full"
            st.session_state.reason_for_restriction = ""
            # Forcer le rafraîchissement de l'interface
            try:
                st.rerun()
            except:
                pass
    
    def handle_usb_removal(self):
        print("[CLE] USB retirée. Vérification de l'autorisation MAC...")
        try:
            license_manager = LicenseManager()
            mac_authorized, mac_message = license_manager.check_license()

            if mac_authorized:
                print(f"[OK] MAC autorisée ({mac_message}). Passage en mode restreint.")
                self.mac_restricted_mode = True
                if hasattr(st, 'session_state'):
                    st.session_state.access_level = "mac_restricted"
                    st.session_state.reason_for_restriction = "USB retirée, accès par MAC."
                    # Forcer le rafraîchissement de l'interface
                    try:
                        st.rerun()
                    except:
                        pass
                else:
                    print("[ATTENTION] Contexte Streamlit (st.session_state) non disponible directement ici.")

                # NE PAS arrêter la surveillance - continuer à surveiller pour la réinsertion
                print("[OK] Surveillance USB maintenue pour détecter la réinsertion")
                self.protection_triggered = False
            else:
                print("[ERREUR] MAC non autorisée. Déclenchement du verrouillage de sécurité !")
                self.trigger_security_lockdown_actual()

        except Exception as e:
            print(f"[ERREUR] Erreur lors de la gestion du retrait de l'USB : {e}")
            self.trigger_security_lockdown_actual()
    
    def trigger_security_lockdown_actual(self):
        if self.protection_triggered:
            return
        self.protection_triggered = True
        print("[ALERTE] DÉCLENCHEMENT DE LA PROTECTION DE SÉCURITÉ (ACTUAL)!")
        print("[VERROUILLAGE] ACCÈS NON AUTORISÉ DÉTECTÉ - ACTIVATION DES CONTRE-MESURES")
        
        protection_thread = threading.Thread(target=self._execute_protection, daemon=True)
        protection_thread.start()
    
    def _execute_protection(self):
        """Exécute les mesures de protection en utilisant le module centralisé."""
        try:
            lockdown_actions.log_action("LOCKDOWN (usb_surveillance): Appel à execute_full_lockdown.")
            lockdown_actions.execute_full_lockdown() 
            lockdown_actions.log_action("LOCKDOWN (usb_surveillance): execute_full_lockdown terminé.")
            
        except Exception as e:
            # En cas d'erreur même dans l'appel à execute_full_lockdown, logguer et tenter de fermer.
            lockdown_actions.log_action(f"ERREUR CRITIQUE (usb_surveillance): Échec de execute_full_lockdown: {e}")
        finally:
            # Forcer la fermeture de l'application après avoir tenté toutes les mesures.
            # Ceci est une mesure de dernier recours.
            lockdown_actions.log_action("LOCKDOWN (usb_surveillance): Tentative de fermeture finale du processus (os._exit).")
            try:
                os._exit(1) # Quitte immédiatement sans nettoyage.
            except:
                sys.exit(1) # Fallback plus standard.
    
    def _kill_all_browsers(self):
        """Ferme tous les navigateurs (y compris headless)"""
        # DÉPRÉCIÉ - Maintenant géré par lockdown_actions.py
        lockdown_actions.log_action("_kill_all_browsers (DEPRECATED) appelé dans usb_surveillance_exe. Utiliser lockdown_actions.")
        # Pourrait appeler la nouvelle fonction pour compatibilité si nécessaire, mais idéalement non utilisé.
        # lockdown_actions.kill_all_browsers()
        pass # Laisser vide ou supprimer
    
    def _kill_python_processes(self):
        """Ferme tous les processus Python/Streamlit (sauf le processus actuel)"""
        # DÉPRÉCIÉ - Maintenant géré par lockdown_actions.py
        lockdown_actions.log_action("_kill_python_processes (DEPRECATED) appelé dans usb_surveillance_exe. Utiliser lockdown_actions.")
        pass # Laisser vide ou supprimer
    
    def _delete_exe(self):
        """Supprime l'EXE et les fichiers associés"""
        # DÉPRÉCIÉ - Maintenant géré par lockdown_actions.py
        lockdown_actions.log_action("_delete_exe (DEPRECATED) appelé dans usb_surveillance_exe. Utiliser lockdown_actions.")
        pass # Laisser vide ou supprimer
    
    def _block_restart(self):
        """Bloque temporairement le redémarrage des applications"""
        # DÉPRÉCIÉ - Maintenant géré par lockdown_actions.py
        lockdown_actions.log_action("_block_restart (DEPRECATED) appelé dans usb_surveillance_exe. Utiliser lockdown_actions.")
        pass # Laisser vide ou supprimer
    
    def get_status(self) -> dict:
        """Retourne l'état de la protection"""
        status = {
            "protection_active": self.usb_watchdog is not None,
            "protection_triggered": self.protection_triggered
        }
        
        if self.usb_watchdog:
            status.update(self.usb_watchdog.get_status())
        
        return status


# Fonction d'intégration pour vos applications existantes
def start_usb_protection(drive_letter: str = "G", token_file: str = "sys.dat") -> SecurityProtection:
    """
    Démarre la protection USB complète
    
    Usage:
        protection = start_usb_protection()
        # Votre application continue normalement
        # La protection surveille en arrière-plan
    """
    protection = SecurityProtection()
    protection.initialize_protection(drive_letter, token_file)
    return protection


if __name__ == "__main__":
    print("[SECURITE] Test de la surveillance USB")
    
    # Démarrer la protection
    protection = start_usb_protection()
    
    try:
        print("[OK] Protection active - Testez en retirant/insérant la clé USB")
        print("[OK] Appuyez sur Ctrl+C pour arrêter")
        
        while True:
            status = protection.get_status()
            print(f"[STATUT] Status: USB={'[OK]' if status.get('usb_present') else '[NON]'} | "
                  f"Échecs: {status.get('consecutive_failures', 0)} | "
                  f"Surveillance: {'[OK]' if status.get('monitoring') else '[NON]'}")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n[OK] Arrêt demandé par l'utilisateur")
        if protection.usb_watchdog:
            protection.usb_watchdog.stop_monitoring()
        print("👋 Au revoir!")