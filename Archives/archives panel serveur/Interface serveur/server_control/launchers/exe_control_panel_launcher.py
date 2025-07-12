#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Launcher pour Exécutable - Panneau de Contrôle OptimPV
======================================================

Version adaptée pour les exécutables compilés (Nuitka, PyInstaller, etc.)
"""

import subprocess
import sys
import os
import socket
import time
import threading
import webbrowser
from pathlib import Path

def is_compiled_executable():
    """Détecte si on est dans un exécutable compilé"""
    return (
        getattr(sys, 'frozen', False) or  # PyInstaller
        hasattr(sys, '_MEIPASS') or      # PyInstaller
        '__compiled__' in globals()       # Nuitka
    )

def get_executable_dir():
    """Retourne le répertoire de l'exécutable"""
    if is_compiled_executable():
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller
            return Path(getattr(sys, '_MEIPASS'))  # type: ignore
        else:
            # Nuitka ou autres
            return Path(sys.executable).parent
    else:
        # Mode développement
        return Path(__file__).parent.parent.parent.parent

def find_available_port(start_port=8504):
    """Trouve un port disponible"""
    for port in range(start_port, start_port + 20):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

def check_if_server_running():
    """Vérifie si un serveur OptimPV tourne déjà"""
    # Vérifier les ports courants
    common_ports = [8501, 8502, 8503, 8504, 8505]
    
    for port in common_ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result = s.connect_ex(('127.0.0.1', port))
                if result == 0:
                    # Port occupé, vérifier si c'est OptimPV
                    try:
                        import requests
                        response = requests.get(f"http://127.0.0.1:{port}", timeout=2)
                        if response.status_code == 200:
                            content = response.text.lower()
                            if 'optimpv' in content or 'streamlit' in content:
                                return port, f"http://127.0.0.1:{port}"
                    except:
                        pass
        except:
            continue
    
    return None, None

def launch_embedded_server():
    """Lance le serveur embarqué dans l'exe"""
    print("🚀 Démarrage du serveur OptimPV embarqué...")
    
    # Trouver un port disponible
    port = find_available_port(8502)
    if not port:
        print("❌ Erreur: Aucun port disponible")
        return None
    
    print(f"🔍 Port sélectionné: {port}")
    
    # Dans un exe, on lance directement Streamlit avec le module embarqué
    try:
        # Import du module principal
        if is_compiled_executable():
            # En mode exe, importer directement
            import streamlit.web.cli as stcli
            
            # Configurer les arguments pour Streamlit
            sys.argv = [
                'streamlit',
                'run',
                'app.py',  # Le fichier principal embarqué
                '--server.headless', 'true',
                '--server.address', '127.0.0.1',
                '--server.port', str(port),
                '--browser.gatherUsageStats', 'false',
                '--global.developmentMode', 'false'
            ]
            
            # Lancer Streamlit dans un thread séparé
            def run_streamlit():
                try:
                    stcli.main()
                except SystemExit:
                    pass  # Streamlit fait un sys.exit(), on l'ignore
            
            server_thread = threading.Thread(target=run_streamlit, daemon=True)
            server_thread.start()
            
            # Attendre que le serveur soit prêt
            url = f"http://127.0.0.1:{port}"
            print(f"⏳ Attente du démarrage sur {url}...")
            
            for i in range(30):  # 30 secondes max
                try:
                    import requests
                    response = requests.get(url, timeout=1)
                    if response.status_code == 200:
                        print(f"✅ Serveur démarré avec succès !")
                        return url
                except:
                    pass
                time.sleep(1)
                print(f"   Tentative {i+1}/30...")
            
            print("❌ Timeout - Le serveur n'a pas démarré")
            return None
            
        else:
            # Mode développement - utiliser subprocess
            exe_dir = get_executable_dir()
            app_file = exe_dir / "app.py"
            
            if not app_file.exists():
                print(f"❌ Fichier app.py non trouvé dans {exe_dir}")
                return None
            
            cmd = [
                sys.executable, "-m", "streamlit", "run",
                str(app_file),
                "--server.headless", "true",
                "--server.address", "127.0.0.1",
                "--server.port", str(port),
                "--browser.gatherUsageStats", "false"
            ]
            
            print(f"🔧 Commande: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(exe_dir)
            )
            
            # Attendre que le serveur soit prêt
            url = f"http://127.0.0.1:{port}"
            for i in range(15):
                try:
                    import requests
                    response = requests.get(url, timeout=1)
                    if response.status_code == 200:
                        print(f"✅ Serveur démarré !")
                        return url
                except:
                    pass
                time.sleep(1)
            
            print("❌ Le serveur n'a pas démarré")
            return None
            
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        return None

def main():
    """Fonction principale pour exe"""
    
    print("=" * 60)
    if is_compiled_executable():
        print("📦 OPTIMPV - EXÉCUTABLE AUTONOME")
    else:
        print("🔧 OPTIMPV - MODE DÉVELOPPEMENT")
    print("=" * 60)
    
    # Vérifier si un serveur tourne déjà
    existing_port, existing_url = check_if_server_running()
    
    if existing_port:
        print(f"🔍 Serveur OptimPV détecté sur le port {existing_port}")
        print(f"🌐 URL: {existing_url}")
        print()
        print("Options:")
        print("1️⃣  Ouvrir le serveur existant dans le navigateur")
        print("2️⃣  Lancer un nouveau serveur sur un autre port")
        print("0️⃣  Quitter")
        print()
        
        try:
            choice = input("Votre choix: ").strip()
            
            if choice == "1":
                print(f"🌐 Ouverture de {existing_url}...")
                if existing_url:  # Vérification de sécurité
                    webbrowser.open(existing_url)
                return
            elif choice == "2":
                print("🚀 Lancement d'un nouveau serveur...")
                url = launch_embedded_server()
                if url:
                    print(f"🌐 Nouveau serveur disponible: {url}")
                    webbrowser.open(url)
                return
            elif choice == "0":
                print("👋 Au revoir !")
                return
            else:
                print("❌ Choix invalide")
                return
                
        except KeyboardInterrupt:
            print("\n👋 Arrêt demandé")
            return
    
    else:
        print("ℹ️  Aucun serveur OptimPV détecté")
        print("🚀 Lancement du serveur...")
        
        url = launch_embedded_server()
        if url:
            print(f"✅ Serveur OptimPV démarré avec succès !")
            print(f"🌐 URL: {url}")
            print()
            print("🌐 Ouverture automatique dans le navigateur...")
            webbrowser.open(url)
            
            print()
            print("=" * 60)
            print("📋 SERVEUR ACTIF")
            print("=" * 60)
            print(f"🔗 Accès: {url}")
            print("⚠️  IMPORTANT: Dans un exe, le serveur s'arrête si vous fermez cette fenêtre !")
            print("💡 Pour garder le serveur actif, laissez cette fenêtre ouverte")
            print("🔴 Appuyez sur Ctrl+C pour arrêter le serveur")
            print("=" * 60)
            
            try:
                # Maintenir le processus principal actif
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🔴 Arrêt du serveur demandé")
                print("👋 Au revoir !")
        else:
            print("❌ Impossible de démarrer le serveur")
            input("Appuyez sur Entrée pour fermer...")

if __name__ == "__main__":
    main() 