# security/lockdown.py
"""
Mécanismes de lockdown et auto-destruction sécurisée
"""

import os
import sys
import time
import glob
import shutil
import tempfile
import subprocess
import random
from pathlib import Path
from typing import List, Optional

try:
    import win32api
    import win32con
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

from utils.logger import SecureLogger
from config.constants import CLEANUP_EXTENSIONS, BASE_DIR


class LockdownManager:
    """Gestionnaire de lockdown et auto-destruction"""
    
    def __init__(self):
        self.logger = SecureLogger()
        self.lockdown_in_progress = False
        
    def execute_lockdown(self, severity: str = "HIGH"):
        """
        Exécuter séquence de lockdown selon la sévérité
        
        Niveaux:
        - LOW: Simple arrêt et nettoyage logs
        - MEDIUM: Nettoyage complet + désactivation
        - HIGH: Nettoyage + suppression configs
        - CRITICAL: Auto-destruction totale
        """
        if self.lockdown_in_progress:
            return
            
        self.lockdown_in_progress = True
        
        try:
            self.logger.log_security_event('LOCKDOWN_INITIATED', {
                'severity': severity,
                'timestamp': time.time()
            }, severity='CRITICAL')
            
            if severity == "LOW":
                self._low_severity_lockdown()
            elif severity == "MEDIUM":
                self._medium_severity_lockdown()
            elif severity == "HIGH":
                self._high_severity_lockdown()
            else:  # CRITICAL
                self._critical_severity_lockdown()
                
        except Exception as e:
            # En cas d'erreur, forcer arrêt brutal
            print(f"Erreur lockdown: {e}")
            os._exit(1)
    
    def _low_severity_lockdown(self):
        """Lockdown léger - arrêt propre"""
        print("\n🔒 Lockdown de sécurité (niveau: BAS)")
        
        # 1. Arrêter processus enfants
        self._terminate_child_processes()
        
        # 2. Nettoyer fichiers temporaires
        self._clean_temp_files()
        
        # 3. Log final
        self.logger.log_security_event('LOCKDOWN_COMPLETED', {
            'severity': 'LOW'
        })
        
        # 4. Arrêt normal
        sys.exit(0)
    
    def _medium_severity_lockdown(self):
        """Lockdown moyen - nettoyage étendu"""
        print("\n🔒 Lockdown de sécurité (niveau: MOYEN)")
        
        # 1. Actions du niveau bas
        self._terminate_child_processes()
        self._clean_temp_files()
        
        # 2. Effacer logs sensibles
        self._wipe_sensitive_logs()
        
        # 3. Désactiver autorisations temporaires
        self._disable_temp_permissions()
        
        # 4. Nettoyer mémoire
        self._clear_memory_traces()
        
        # 5. Arrêt
        sys.exit(1)
    
    def _high_severity_lockdown(self):
        """Lockdown élevé - suppression configurations"""
        print("\n⚠️ Lockdown de sécurité (niveau: ÉLEVÉ)")
        
        # 1. Actions des niveaux précédents
        self._terminate_child_processes()
        self._clean_temp_files()
        self._wipe_sensitive_logs()
        
        # 2. Supprimer configurations réseau
        self._delete_network_configs()
        
        # 3. Effacer liste blanche MAC
        self._wipe_mac_whitelist()
        
        # 4. Supprimer certificats/clés
        self._delete_crypto_materials()
        
        # 5. Nettoyer registre Windows
        if WIN32_AVAILABLE:
            self._clean_registry()
        
        # 6. Arrêt forcé
        os._exit(1)
    
    def _critical_severity_lockdown(self):
        """Lockdown critique - auto-destruction totale"""
        print("\n🚨 LOCKDOWN CRITIQUE - AUTO-DESTRUCTION")
        
        # 1. Toutes les actions précédentes
        self._terminate_child_processes()
        self._clean_temp_files()
        self._wipe_sensitive_logs()
        self._delete_network_configs()
        self._wipe_mac_whitelist()
        self._delete_crypto_materials()
        
        # 2. Effacement sécurisé de TOUS les fichiers
        self._secure_wipe_all_files()
        
        # 3. Corruption des fichiers système
        self._corrupt_system_files()
        
        # 4. Auto-suppression de l'exécutable
        self._self_destruct()
        
        # Ne devrait jamais atteindre cette ligne
        os._exit(1)
    
    def _terminate_child_processes(self):
        """Terminer tous les processus enfants"""
        try:
            import psutil
            
            current_process = psutil.Process()
            children = current_process.children(recursive=True)
            
            # Terminer gracieusement
            for child in children:
                try:
                    child.terminate()
                except:
                    pass
            
            # Attendre un peu
            time.sleep(1)
            
            # Forcer si nécessaire
            for child in children:
                try:
                    if child.is_running():
                        child.kill()
                except:
                    pass
                    
        except Exception:
            pass
    
    def _clean_temp_files(self):
        """Nettoyer fichiers temporaires"""
        temp_patterns = [
            os.path.join(tempfile.gettempdir(), "optimv_*"),
            os.path.join(tempfile.gettempdir(), "streamlit_*"),
            "logs/*.tmp",
            "temp/*"
        ]
        
        for pattern in temp_patterns:
            try:
                for file in glob.glob(pattern):
                    self._secure_delete(file)
            except:
                pass
    
    def _wipe_sensitive_logs(self):
        """Effacer logs sensibles"""
        log_patterns = [
            "logs/security_*.log",
            "logs/events_*.jsonl",
            "config/secure/*.enc"
        ]
        
        for pattern in log_patterns:
            try:
                for file in glob.glob(pattern):
                    self._secure_delete(file, passes=3)
            except:
                pass
    
    def _disable_temp_permissions(self):
        """Désactiver permissions temporaires"""
        try:
            # Effacer tokens de session
            session_files = glob.glob("config/secure/session_*.dat")
            for file in session_files:
                self._secure_delete(file)
                
        except Exception:
            pass
    
    def _clear_memory_traces(self):
        """Effacer traces en mémoire"""
        try:
            # Écraser variables sensibles
            import gc
            
            # Forcer garbage collection
            for _ in range(3):
                gc.collect()
                
            # Remplir mémoire avec données aléatoires
            try:
                dummy = [random.randbytes(1024*1024) for _ in range(10)]
                del dummy
            except:
                pass
                
        except Exception:
            pass
    
    def _delete_network_configs(self):
        """Supprimer configurations réseau"""
        config_files = [
            "config/network_settings.json",
            "config/firewall_rules.json",
            "config/ip_whitelist.json"
        ]
        
        for file in config_files:
            if os.path.exists(file):
                self._secure_delete(file, passes=3)
    
    def _wipe_mac_whitelist(self):
        """Effacer liste blanche MAC"""
        try:
            mac_file = "config/secure/mac_whitelist.enc"
            if os.path.exists(mac_file):
                self._secure_delete(mac_file, passes=5)
        except:
            pass
    
    def _delete_crypto_materials(self):
        """Supprimer matériel cryptographique"""
        crypto_patterns = [
            "config/secure/*.key",
            "config/secure/*.pem",
            "config/secure/*.crt",
            "config/secure/master_key.enc"
        ]
        
        for pattern in crypto_patterns:
            for file in glob.glob(pattern):
                self._secure_delete(file, passes=7)
    
    def _clean_registry(self):
        """Nettoyer entrées registre Windows"""
        if not WIN32_AVAILABLE:
            return
            
        try:
            import winreg
            
            # Clés à supprimer
            keys_to_delete = [
                (winreg.HKEY_CURRENT_USER, r"Software\OptimPV"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\OptimPV")
            ]
            
            for root, path in keys_to_delete:
                try:
                    winreg.DeleteKey(root, path)
                except:
                    pass
                    
        except Exception:
            pass
    
    def _secure_wipe_all_files(self):
        """Effacement sécurisé de tous les fichiers"""
        # Répertoires à effacer
        directories = [
            "config",
            "logs", 
            "temp",
            "app_bundle"
        ]
        
        for directory in directories:
            if os.path.exists(directory):
                try:
                    # Effacer récursivement
                    for root, dirs, files in os.walk(directory, topdown=False):
                        for file in files:
                            filepath = os.path.join(root, file)
                            self._secure_delete(filepath, passes=3)
                        
                        # Supprimer répertoire vide
                        try:
                            os.rmdir(root)
                        except:
                            pass
                except:
                    pass
    
    def _corrupt_system_files(self):
        """Corrompre fichiers système (rendre inutilisable)"""
        critical_files = [
            "panel/main_panel.py",
            "security/auth_core.py",
            "app_bundle/app.py"
        ]
        
        corruption_data = random.randbytes(1024)
        
        for file in critical_files:
            if os.path.exists(file):
                try:
                    with open(file, 'wb') as f:
                        f.write(corruption_data)
                except:
                    pass
    
    def _self_destruct(self):
        """Auto-suppression de l'exécutable"""
        try:
            # Créer script batch pour suppression
            batch_content = f"""
@echo off
echo Nettoyage en cours...
timeout /t 2 /nobreak > nul
del /f /q "{sys.executable}"
rd /s /q "{BASE_DIR}"
del /f /q "%~f0"
"""
            
            batch_path = os.path.join(tempfile.gettempdir(), "cleanup.bat")
            
            with open(batch_path, 'w') as f:
                f.write(batch_content)
            
            # Lancer en arrière-plan
            subprocess.Popen(
                batch_path,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW if WIN32_AVAILABLE else 0
            )
            
        except Exception:
            pass
    
    def _secure_delete(self, filepath: str, passes: int = 1):
        """Suppression sécurisée d'un fichier avec écrasement"""
        if not os.path.exists(filepath):
            return
            
        try:
            filesize = os.path.getsize(filepath)
            
            with open(filepath, "ba+", buffering=0) as f:
                for _ in range(passes):
                    # Patterns d'écrasement DoD 5220.22-M
                    patterns = [
                        b'\x00' * 1024,  # Zéros
                        b'\xFF' * 1024,  # Uns
                        random.randbytes(1024)  # Aléatoire
                    ]
                    
                    for pattern in patterns:
                        f.seek(0)
                        while f.tell() < filesize:
                            f.write(pattern)
                        f.flush()
                        os.fsync(f.fileno())
            
            # Renommer avant suppression
            temp_name = os.path.join(
                os.path.dirname(filepath),
                f"tmp_{random.randint(1000, 9999)}.tmp"
            )
            os.rename(filepath, temp_name)
            
            # Supprimer
            os.unlink(temp_name)
            
        except Exception:
            # Fallback: suppression simple
            try:
                os.unlink(filepath)
            except:
                pass
    
    def trigger_delayed_lockdown(self, delay_seconds: int, severity: str = "HIGH"):
        """Déclencher lockdown après délai"""
        import threading
        
        def delayed_execution():
            time.sleep(delay_seconds)
            self.execute_lockdown(severity)
        
        thread = threading.Thread(target=delayed_execution, daemon=True)
        thread.start()
    
    def emergency_wipe(self):
        """Effacement d'urgence immédiat"""
        # Pas de logs, pas de délais, destruction immédiate
        self._secure_wipe_all_files()
        self._self_destruct()
        os._exit(1)# Mécanismes d'auto-destruction et de verrouillage 