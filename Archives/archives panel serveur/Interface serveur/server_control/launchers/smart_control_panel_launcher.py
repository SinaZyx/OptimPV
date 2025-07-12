#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Launcher Intelligent pour le Panneau de Contrôle OptimPV
========================================================

Détecte automatiquement les serveurs existants et propose des actions intelligentes.
"""

import subprocess
import sys
import os
import socket
import requests
import psutil
import time
from pathlib import Path

def find_available_port(start_port=8504):
    """Trouve un port disponible à partir du port de départ"""
    for port in range(start_port, start_port + 10):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

def find_running_servers():
    """Trouve tous les serveurs OptimPV en cours d'exécution"""
    servers = []
    
    # Chercher les processus Python avec Streamlit
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'])
                
                # Identifier les différents types de serveurs
                if 'streamlit' in cmdline:
                    server_type = "Inconnu"
                    port = None
                    
                    # Extraire le port
                    if '--server.port' in cmdline:
                        try:
                            port_idx = cmdline.split().index('--server.port')
                            port = int(cmdline.split()[port_idx + 1])
                        except (ValueError, IndexError):
                            pass
                    
                    # Identifier le type de serveur
                    if 'server_control_panel' in cmdline:
                        server_type = "Panel de Contrôle"
                    elif 'launcher.py' in cmdline or 'app.py' in cmdline:
                        server_type = "Application OptimPV"
                    
                    if port:
                        # Vérifier si le serveur répond
                        try:
                            response = requests.get(f"http://127.0.0.1:{port}", timeout=1)
                            status = "✅ Actif" if response.status_code == 200 else "⚠️ Problème"
                        except:
                            status = "❌ Non accessible"
                        
                        servers.append({
                            'pid': proc.info['pid'],
                            'type': server_type,
                            'port': port,
                            'status': status,
                            'url': f"http://127.0.0.1:{port}",
                            'cmdline': cmdline
                        })
        except:
            continue
    
    return servers

def stop_server_by_pid(pid):
    """Arrête un serveur par son PID"""
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        time.sleep(2)
        if proc.is_running():
            proc.kill()
        return True
    except:
        return False

def show_server_status():
    """Affiche l'état des serveurs"""
    print("\n🔍 DÉTECTION DES SERVEURS EN COURS...")
    print("=" * 60)
    
    servers = find_running_servers()
    
    if not servers:
        print("ℹ️  Aucun serveur OptimPV détecté")
        return servers
    
    print(f"📊 {len(servers)} serveur(s) détecté(s):")
    print()
    
    for i, server in enumerate(servers, 1):
        print(f"{i}. {server['type']}")
        print(f"   📍 Port: {server['port']}")
        print(f"   🔗 URL: {server['url']}")
        print(f"   📊 État: {server['status']}")
        print(f"   🆔 PID: {server['pid']}")
        print()
    
    return servers

def main():
    """Lance le panneau de contrôle intelligent"""
    
    print("=" * 60)
    print("🧠 OPTIMPV - PANNEAU DE CONTRÔLE INTELLIGENT")
    print("=" * 60)
    print("Analyse de l'environnement...")
    
    # Détecter les serveurs existants
    servers = show_server_status()
    
    # Chercher spécifiquement les panels de contrôle
    control_panels = [s for s in servers if "Panel de Contrôle" in s['type']]
    optimpv_apps = [s for s in servers if "Application OptimPV" in s['type']]
    
    print("=" * 60)
    print("🎯 OPTIONS DISPONIBLES:")
    print("=" * 60)
    
    if control_panels:
        print(f"📋 {len(control_panels)} Panel(s) de Contrôle déjà actif(s):")
        for panel in control_panels:
            print(f"   • {panel['url']} - {panel['status']}")
        print()
        
        print("1️⃣  Ouvrir un panel existant dans le navigateur")
        print("2️⃣  Arrêter tous les panels et en créer un nouveau")
        print("3️⃣  Créer un nouveau panel sur un autre port")
        print("4️⃣  Arrêter un panel spécifique")
    else:
        print("📋 Aucun Panel de Contrôle actif")
        print("1️⃣  Créer un nouveau Panel de Contrôle")
    
    if optimpv_apps:
        print(f"\n🌞 {len(optimpv_apps)} Application(s) OptimPV active(s):")
        for app in optimpv_apps:
            print(f"   • {app['url']} - {app['status']}")
    
    print("\n0️⃣  Quitter")
    print("=" * 60)
    
    try:
        choice = input("Votre choix: ").strip()
        
        if choice == "0":
            print("👋 Au revoir !")
            return
        
        elif choice == "1":
            if control_panels:
                # Ouvrir le premier panel dans le navigateur
                import webbrowser
                url = control_panels[0]['url']
                print(f"🌐 Ouverture de {url} dans le navigateur...")
                webbrowser.open(url)
            else:
                # Créer un nouveau panel
                create_new_panel()
        
        elif choice == "2" and control_panels:
            # Arrêter tous les panels et en créer un nouveau
            print("🛑 Arrêt de tous les panels de contrôle...")
            for panel in control_panels:
                if stop_server_by_pid(panel['pid']):
                    print(f"✅ Panel PID {panel['pid']} arrêté")
                else:
                    print(f"❌ Erreur arrêt PID {panel['pid']}")
            
            time.sleep(2)
            create_new_panel()
        
        elif choice == "3" and control_panels:
            # Créer un nouveau panel sur un autre port
            create_new_panel()
        
        elif choice == "4" and control_panels:
            # Arrêter un panel spécifique
            print("\nQuels panels arrêter ?")
            for i, panel in enumerate(control_panels, 1):
                print(f"{i}. PID {panel['pid']} - Port {panel['port']}")
            
            try:
                panel_choice = int(input("Numéro du panel à arrêter: ")) - 1
                if 0 <= panel_choice < len(control_panels):
                    panel = control_panels[panel_choice]
                    if stop_server_by_pid(panel['pid']):
                        print(f"✅ Panel PID {panel['pid']} arrêté")
                    else:
                        print(f"❌ Erreur arrêt PID {panel['pid']}")
                else:
                    print("❌ Choix invalide")
            except ValueError:
                print("❌ Veuillez entrer un numéro valide")
        
        else:
            print("❌ Choix invalide")
    
    except KeyboardInterrupt:
        print("\n👋 Arrêt demandé")

def create_new_panel():
    """Crée un nouveau panel de contrôle"""
    print("\n🚀 CRÉATION D'UN NOUVEAU PANEL DE CONTRÔLE")
    print("=" * 50)
    
    # Chemin vers le script modulaire (nouveau)
    current_dir = Path(__file__).parent
    panel_script = current_dir.parent / "core" / "server_control_panel.py"
    
    if not panel_script.exists():
        print(f"❌ Erreur: Script non trouvé - {panel_script}")
        print("💡 Vérification des scripts disponibles...")
        
        # Chercher des alternatives
        core_dir = current_dir.parent / "core"
        if core_dir.exists():
            available_scripts = list(core_dir.glob("server_control_panel*.py"))
            if available_scripts:
                print("📋 Scripts disponibles:")
                for script in available_scripts:
                    print(f"   • {script.name}")
                # Utiliser le premier script trouvé
                panel_script = available_scripts[0]
                print(f"🔄 Utilisation de: {panel_script.name}")
            else:
                print("❌ Aucun script de panneau de contrôle trouvé")
                input("Appuyez sur Entrée pour fermer...")
                return
        else:
            print("❌ Dossier core non trouvé")
            input("Appuyez sur Entrée pour fermer...")
            return
    
    # Trouver un port disponible
    available_port = find_available_port(8504)
    if not available_port:
        print("❌ Erreur: Aucun port disponible trouvé entre 8504-8513")
        input("Appuyez sur Entrée pour fermer...")
        return
    
    print(f"🔍 Port disponible trouvé: {available_port}")
    
    # Configuration optimisée pour Streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(panel_script),
        "--server.headless", "false",
        "--server.address", "127.0.0.1", 
        "--server.port", str(available_port),
        "--browser.gatherUsageStats", "false",
        "--global.developmentMode", "false",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
        "--server.maxUploadSize", "1"
    ]
    
    print(f"🌐 Interface accessible sur: http://127.0.0.1:{available_port}")
    print("🔧 Démarrage du panel...")
    
    try:
        # Lancer Streamlit avec optimisations
        subprocess.run(cmd, check=True, cwd=current_dir)
    except KeyboardInterrupt:
        print("\n🔴 Arrêt du panneau de contrôle demandé")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erreur lors du lancement: {e}")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")

if __name__ == "__main__":
    main() 