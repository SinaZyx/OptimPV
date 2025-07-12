#!/usr/bin/env python3
"""
OptimPV - Actions de Verrouillage de Sécurité Centralisées
========================================================

Ce module contient les fonctions pour exécuter les mesures de sécurité
(fermeture de processus, suppression de fichiers, etc.)
"""

import os
import sys
import time
import subprocess
import psutil
import shutil
import platform
import tempfile
import threading
from pathlib import Path

# --- Configuration pour la journalisation --- DÉSACTIVÉE pour ne laisser aucune trace
LOG_FILE_PATH = "lockdown_actions.log"
ENABLE_LOGGING = False  # MODIFIÉ : Désactivé pour ne laisser aucune trace

def log_action(message):
    # MODIFIÉ : Logging complètement désactivé pour ne laisser aucune trace
    pass

def kill_all_browsers():
    """Ferme tous les navigateurs (y compris headless) - Version agressive et complète"""
    browser_processes = [
        # Navigateurs principaux
        "chrome.exe", "firefox.exe", "msedge.exe", "iexplore.exe",
        "opera.exe", "brave.exe", "vivaldi.exe", "safari.exe",
        "chromium.exe", "waterfox.exe", "palemoon.exe",
        # WebDrivers et processus headless
        "chromedriver.exe", "geckodriver.exe", "msedgedriver.exe",
        "operadriver.exe", "phantomjs.exe",
        # Processus Chrome spécifiques
        "chrome_proxy.exe", "chrome_crashpad_handler.exe",
        # Edge spécifiques
        "msedgewebview2.exe", "msedge_proxy.exe",
        # Firefox spécifiques
        "firefox_crashreporter.exe", "plugin-container.exe"
    ]
    
    killed_count = 0
    
    try:
        # PHASE 1: Fermeture douce avec psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                process_name = proc.info['name'].lower()
                cmdline = ' '.join(proc.info.get('cmdline', [])).lower()
                
                should_kill = False
                
                # Vérifier par nom de processus
                if any(browser.lower().replace('.exe', '') in process_name for browser in browser_processes):
                    should_kill = True
                
                # Vérifier les indicateurs headless dans la ligne de commande
                if not should_kill:
                    headless_indicators = [
                        '--headless', '--no-sandbox', '--disable-gpu',
                        '--remote-debugging', 'selenium', 'webdriver',
                        '--disable-web-security', '--disable-features',
                        '--automation', '--test-type'
                    ]
                    if any(indicator in cmdline for indicator in headless_indicators):
                        should_kill = True
                
                if should_kill:
                    try:
                        proc.terminate()  # Fermeture douce d'abord
                        killed_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Attendre un peu pour la fermeture douce
        time.sleep(1)
        
        # PHASE 2: Fermeture forcée avec psutil.kill()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                process_name = proc.info['name'].lower()
                cmdline = ' '.join(proc.info.get('cmdline', [])).lower()
                
                should_kill = False
                
                if any(browser.lower().replace('.exe', '') in process_name for browser in browser_processes):
                    should_kill = True
                
                if not should_kill:
                    headless_indicators = [
                        '--headless', '--no-sandbox', '--disable-gpu',
                        '--remote-debugging', 'selenium', 'webdriver'
                    ]
                    if any(indicator in cmdline for indicator in headless_indicators):
                        should_kill = True
                
                if should_kill:
                    try:
                        proc.kill()  # Fermeture forcée
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # PHASE 3: Fermeture système avec taskkill (Windows)
        if platform.system() == "Windows":
            for browser_exe_name in browser_processes:
                try:
                    # Utiliser taskkill avec /F pour forcer
                    subprocess.run([
                        "taskkill", "/F", "/IM", browser_exe_name, "/T"
                    ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, check=False)
                except Exception:
                    pass
            
            # Commandes taskkill supplémentaires pour les processus récalcitrants
            additional_kill_commands = [
                ["taskkill", "/F", "/FI", "IMAGENAME eq chrome*", "/T"],
                ["taskkill", "/F", "/FI", "IMAGENAME eq firefox*", "/T"],
                ["taskkill", "/F", "/FI", "IMAGENAME eq msedge*", "/T"],
                ["taskkill", "/F", "/FI", "WINDOWTITLE eq *Chrome*", "/T"],
                ["taskkill", "/F", "/FI", "WINDOWTITLE eq *Firefox*", "/T"],
                ["taskkill", "/F", "/FI", "WINDOWTITLE eq *Edge*", "/T"]
            ]
            
            for cmd in additional_kill_commands:
                try:
                    subprocess.run(cmd, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, check=False)
                except Exception:
                    pass
        
        # PHASE 4: Nettoyage des processus orphelins
        time.sleep(0.5)
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                process_name = proc.info['name'].lower()
                if any(browser_name in process_name for browser_name in ['chrome', 'firefox', 'edge', 'opera', 'brave']):
                    try:
                        proc.kill()
                    except:
                        pass
            except:
                continue
                
    except Exception:
        pass
    
    return killed_count

def kill_python_processes():
    """Ferme tous les processus Python/Streamlit (sauf le processus actuel) - Version silencieuse"""
    current_pid = os.getpid()
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['pid'] == current_pid:
                    continue
                process_name = proc.info['name'].lower()
                cmdline = ' '.join(proc.info.get('cmdline', [])).lower()
                should_kill = False
                if process_name in ['python.exe', 'python', 'pythonw.exe']:
                    if any(keyword in cmdline for keyword in ['optimpv', 'streamlit', 'server_control', 'launcher', 'app.py']):
                        should_kill = True
                elif 'streamlit' in process_name:
                    should_kill = True
                if should_kill:
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass

def delete_current_exe():
    """Supprime l'EXE en cours d'exécution - Version sans trace"""
    if not getattr(sys, 'frozen', False):
        return

    try:
        exe_path = Path(sys.executable)
        exe_dir = exe_path.parent

        # MÉTHODE SIMPLIFIÉE : Suppression directe sans script batch
        if platform.system() == "Windows":
            try:
                # Tentative de suppression directe
                os.remove(exe_path)
            except Exception:
                # Si échec, renommer puis supprimer
                try:
                    temp_name = exe_dir / f"_{exe_path.stem}_{int(time.time())}.tmp"
                    exe_path.rename(temp_name)
                    os.remove(temp_name)
                except Exception:
                    pass
        else:
            try:
                os.remove(exe_path)
            except Exception:
                pass

        # Supprimer les fichiers associés sans laisser de trace
        associated_files = ["OptimPV.exe", "launcher.exe", "server_control_panel.exe"]
        for filename in associated_files:
            file_path = exe_dir / filename
            if file_path.exists() and file_path != exe_path:
                try:
                    file_path.unlink()
                except Exception:
                    pass

    except Exception:
        pass

def create_external_cleanup_script():
    """Crée un script externe pour suppression complète sans trace"""
    if not getattr(sys, 'frozen', False):
        return None
    
    try:
        # Informations sur l'application
        exe_path = Path(sys.executable)
        meipass_path = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else None
        current_pid = os.getpid()
        
        # Créer le script de nettoyage dans le dossier temp système
        temp_dir = Path(tempfile.gettempdir())
        script_name = f"cleanup_{int(time.time())}.bat" if platform.system() == "Windows" else f"cleanup_{int(time.time())}.sh"
        script_path = temp_dir / script_name
        
        if platform.system() == "Windows":
            # Script batch Windows pour suppression complète
            script_content = f'''@echo off
REM Script de nettoyage OptimPV - Suppression sans trace
echo Nettoyage OptimPV en cours...

REM Attendre que le processus principal se termine
timeout /t 5 /nobreak >nul 2>&1

REM Forcer l'arrêt du processus si encore actif
taskkill /F /PID {current_pid} >nul 2>&1

REM Attendre un peu plus
timeout /t 2 /nobreak >nul 2>&1

REM Supprimer l'EXE principal
if exist "{exe_path}" (
    del /F /Q "{exe_path}" >nul 2>&1
    echo EXE principal supprime
)

REM Supprimer le dossier _MEIPASS complet si existe
if exist "{meipass_path}" (
    rmdir /S /Q "{meipass_path}" >nul 2>&1
    echo Dossier temporaire PyInstaller supprime
)

REM Supprimer les fichiers temporaires avec pattern OptimPV
for /f %%i in ('dir /b "%TEMP%\\*OptimPV*" 2^>nul') do (
    del /F /Q "%TEMP%\\%%i" >nul 2>&1
)

REM Supprimer les dossiers temporaires avec pattern _MEI
for /f %%i in ('dir /b /ad "%TEMP%\\*_MEI*" 2^>nul') do (
    rmdir /S /Q "%TEMP%\\%%i" >nul 2>&1
)

REM Nettoyer les fichiers .mp et autres artefacts
for /f %%i in ('dir /b "%TEMP%\\*OptimPV*.mp" 2^>nul') do (
    del /F /Q "%TEMP%\\%%i" >nul 2>&1
)
for /f %%i in ('dir /b "%TEMP%\\*OptimPV*.tmp" 2^>nul') do (
    del /F /Q "%TEMP%\\%%i" >nul 2>&1
)

REM Attendre avant auto-suppression
timeout /t 1 /nobreak >nul 2>&1

REM Auto-suppression du script
del /F /Q "%~f0" >nul 2>&1
'''
        else:
            # Script shell Linux/Mac
            script_content = f'''#!/bin/bash
# Script de nettoyage OptimPV - Suppression sans trace
echo "Nettoyage OptimPV en cours..."

# Attendre que le processus principal se termine
sleep 5

# Forcer l'arrêt du processus si encore actif
kill -9 {current_pid} 2>/dev/null

# Attendre un peu plus
sleep 2

# Supprimer l'EXE principal
if [ -f "{exe_path}" ]; then
    rm -f "{exe_path}" 2>/dev/null
    echo "EXE principal supprimé"
fi

# Supprimer le dossier _MEIPASS complet si existe
if [ -d "{meipass_path}" ]; then
    rm -rf "{meipass_path}" 2>/dev/null
    echo "Dossier temporaire PyInstaller supprimé"
fi

# Supprimer les fichiers temporaires avec pattern OptimPV
find /tmp -name "*OptimPV*" -type f -delete 2>/dev/null

# Supprimer les dossiers temporaires avec pattern _MEI
find /tmp -name "*_MEI*" -type d -exec rm -rf {{}} + 2>/dev/null

# Auto-suppression du script
rm -f "$0" 2>/dev/null
'''
        
        # Écrire le script
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Rendre exécutable sur Unix
        if platform.system() != "Windows":
            os.chmod(script_path, 0o755)
        
        return script_path
        
    except Exception as e:
        print(f"Erreur création script de nettoyage: {e}")
        return None

def execute_external_cleanup():
    """Lance le script externe de nettoyage et se termine immédiatement"""
    script_path = create_external_cleanup_script()
    
    if not script_path:
        print("Impossible de créer le script de nettoyage externe")
        return False
    
    try:
        if platform.system() == "Windows":
            # Lancer le script en arrière-plan sans fenêtre
            subprocess.Popen([
                "cmd", "/c", str(script_path)
            ], creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
        else:
            # Lancer le script en arrière-plan
            subprocess.Popen([
                "/bin/bash", str(script_path)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("Script de nettoyage externe lancé")
        return True
        
    except Exception as e:
        print(f"Erreur lancement script externe: {e}")
        return False

def execute_silent_lockdown():
    """Exécute une séquence de lockdown silencieuse sans laisser de traces"""
    print("[ALERTE] LOCKDOWN SILENCIEUX - SUPPRESSION COMPLÈTE")
    
    # Phase 1: Fermeture des navigateurs
    print("Phase 1: Fermeture navigateurs...")
    killed_browsers = kill_all_browsers()
    time.sleep(0.5)
    
    # Phase 2: Fermeture des processus Python/Streamlit
    print("Phase 2: Fermeture processus Python...")
    kill_python_processes()
    time.sleep(0.5)
    
    # Phase 3: Lancement du script externe de nettoyage complet
    print("Phase 3: Lancement nettoyage externe...")
    cleanup_launched = execute_external_cleanup()
    
    if cleanup_launched:
        print("[OK] Script de nettoyage externe lancé - Suppression complète en cours")
        # Attendre un court instant pour que le script externe démarre
        time.sleep(1)
    else:
        print("[ATTENTION] Échec script externe - Tentative suppression directe")
        # Fallback: tentative de suppression directe
        delete_current_exe()
    
    # Phase 4: Fermeture immédiate et définitive
    print("Phase 4: Fermeture système...")
    try:
        os._exit(1)
    except:
        sys.exit(1)

# FONCTION PRINCIPALE MODIFIÉE pour ne laisser aucune trace
def execute_full_lockdown():
    """Exécute la séquence complète de lockdown sans laisser de traces"""
    execute_silent_lockdown()

if __name__ == "__main__":
    # Test silencieux
    execute_silent_lockdown()

# ... existing code ... 