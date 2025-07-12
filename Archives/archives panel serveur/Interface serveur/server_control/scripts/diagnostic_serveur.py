#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Diagnostic OptimPV Server
===================================

Script pour diagnostiquer les problèmes de démarrage du serveur OptimPV.
"""

import os
import sys
import subprocess
import requests
import time
from pathlib import Path

def diagnostic_complet():
    """Effectue un diagnostic complet du système"""
    
    print("=" * 60)
    print("🔍 DIAGNOSTIC SERVEUR OPTIMPV")
    print("=" * 60)
    
    # Aller au répertoire racine du projet (2 niveaux au-dessus)
    current_dir = Path(__file__).parent.parent.parent
    os.chdir(current_dir)
    
    # 1. Vérification de l'environnement
    print("\n📋 1. ENVIRONNEMENT SYSTÈME")
    print(f"Python: {sys.executable}")
    print(f"Version: {sys.version}")
    print(f"Répertoire: {current_dir}")
    print(f"Plateforme: {sys.platform}")
    
    # 2. Vérification des fichiers requis
    print("\n📂 2. FICHIERS REQUIS")
    fichiers_requis = [
        "launcher.py",
        "app.py", 
        "server_control/core/server_control_panel.py",
        "server_control/launchers/control_panel_launcher.py",
        "admin_config.py"
    ]
    
    fichiers_manquants = []
    for fichier in fichiers_requis:
        if os.path.exists(fichier):
            print(f"  ✅ {fichier}")
        else:
            print(f"  ❌ {fichier}")
            fichiers_manquants.append(fichier)
    
    if fichiers_manquants:
        print(f"\n⚠️  FICHIERS MANQUANTS: {', '.join(fichiers_manquants)}")
        return False
    
    # 3. Vérification des dépendances Python
    print("\n🐍 3. DÉPENDANCES PYTHON")
    dependencies = [
        "streamlit",
        "psutil",
        "requests", 
        "hashlib",
        "json",
        "pandas",
        "numpy"
    ]
    
    missing_deps = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ❌ {dep}")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\n⚠️  DÉPENDANCES MANQUANTES: {', '.join(missing_deps)}")
        print(f"Installez avec: pip install {' '.join(missing_deps)}")
        return False
    
    # 4. Test de lancement du launcher
    print("\n🚀 4. TEST LAUNCHER.PY")
    
    try:
        # Test de syntaxe du launcher
        with open("launcher.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        print("  ✅ Fichier launcher.py lisible")
        
        # Test de compilation du code
        try:
            compile(content, "launcher.py", "exec")
            print("  ✅ Syntaxe launcher.py valide")
        except SyntaxError as e:
            print(f"  ❌ Erreur de syntaxe dans launcher.py: {e}")
            return False
            
    except Exception as e:
        print(f"  ❌ Erreur lecture launcher.py: {e}")
        return False
    
    # 5. Test de lancement en mode diagnostic
    print("\n🔧 5. TEST DÉMARRAGE SERVEUR")
    
    # Vérifier si un serveur tourne déjà
    if test_serveur_en_marche():
        print("  ⚠️  Un serveur OptimPV semble déjà en marche")
        arreter_serveurs_existants()
    
    # Lancer le serveur en mode test
    print("  🔄 Tentative de démarrage du serveur...")
    
    cmd = [sys.executable, "launcher.py"]
    print(f"  Commande: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd()
        )
        
        print(f"  ✅ Processus lancé (PID: {process.pid})")
        
        # Attendre et surveiller
        for i in range(15):  # 15 secondes max
            time.sleep(1)
            
            # Vérifier si le processus est mort
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print(f"  ❌ Processus terminé prématurément (code: {process.returncode})")
                if stderr:
                    print(f"  Erreur: {stderr.strip()}")
                if stdout:
                    print(f"  Sortie: {stdout.strip()}")
                return False
            
            # Tester la connexion
            if test_connexion_serveur():
                print(f"  ✅ Serveur accessible après {i+1} secondes!")
                
                # Arrêter le serveur de test
                process.terminate()
                time.sleep(2)
                if process.poll() is None:
                    process.kill()
                
                print("  ✅ Serveur de test arrêté")
                return True
            
            print(f"    Tentative {i+1}/15...")
        
        # Timeout
        print("  ❌ Timeout - Le serveur ne répond pas après 15 secondes")
        
        # Récupérer les logs
        try:
            stdout, stderr = process.communicate(timeout=2)
            if stderr:
                print(f"  Erreurs: {stderr.strip()}")
            if stdout:
                print(f"  Sortie: {stdout.strip()}")
        except:
            pass
        
        # Arrêter le processus
        process.terminate()
        time.sleep(1)
        if process.poll() is None:
            process.kill()
        
        return False
        
    except Exception as e:
        print(f"  ❌ Erreur lors du lancement: {e}")
        return False

def test_serveur_en_marche():
    """Test si un serveur OptimPV est déjà en marche"""
    try:
        response = requests.get("http://127.0.0.1:8501", timeout=2)
        return response.status_code == 200
    except:
        return False

def test_connexion_serveur():
    """Test de connexion au serveur"""
    try:
        response = requests.get("http://127.0.0.1:8501", timeout=2)
        if response.status_code == 200:
            # Vérifier que c'est bien Streamlit
            content = response.text.lower()
            return 'streamlit' in content
        return False
    except:
        return False

def arreter_serveurs_existants():
    """Arrête tous les serveurs Python/Streamlit en marche"""
    print("  🔄 Arrêt des serveurs existants...")
    
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'streamlit' in cmdline and 'app.py' in cmdline:
                        print(f"    Arrêt du processus {proc.info['pid']}")
                        proc.terminate()
            except:
                continue
        
        time.sleep(2)
        print("  ✅ Serveurs existants arrêtés")
        
    except Exception as e:
        print(f"  ⚠️  Erreur lors de l'arrêt: {e}")

def test_ports():
    """Test des ports utilisés"""
    print("\n🌐 6. TEST DES PORTS")
    
    ports_to_test = [8501, 8502, 8503]
    
    for port in ports_to_test:
        try:
            response = requests.get(f"http://127.0.0.1:{port}", timeout=1)
            print(f"  Port {port}: 🟢 OCCUPÉ (HTTP {response.status_code})")
        except requests.exceptions.ConnectRefused:
            print(f"  Port {port}: 🔴 LIBRE")
        except requests.exceptions.Timeout:
            print(f"  Port {port}: 🟡 TIMEOUT")
        except Exception as e:
            print(f"  Port {port}: ❓ INCONNU ({e})")

def test_configuration():
    """Test de la configuration réseau"""
    print("\n⚙️  7. CONFIGURATION RÉSEAU")
    
    try:
        from admin_config import NetworkAdminConfig
        admin_config = NetworkAdminConfig()
        config = admin_config.get_network_config()
        
        print(f"  IP: {config['ip']}")
        print(f"  Port: {config['port']}")
        print(f"  Accès externe: {config.get('external_access', False)}")
        print(f"  IPs autorisées: {config.get('allowed_ips', [])}")
        
        # Test de la configuration
        if admin_config.validate_ip(config['ip']):
            print("  ✅ IP valide")
        else:
            print("  ❌ IP invalide")
            
        if admin_config.validate_port(config['port']):
            print("  ✅ Port valide")
        else:
            print("  ❌ Port invalide")
            
    except Exception as e:
        print(f"  ❌ Erreur configuration: {e}")

def main():
    """Fonction principale du diagnostic"""
    
    success = diagnostic_complet()
    
    # Tests supplémentaires
    test_ports()
    test_configuration()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 DIAGNOSTIC RÉUSSI!")
        print("✅ Le serveur OptimPV peut être démarré normalement")
        print("\n🚀 PROCHAINES ÉTAPES:")
        print("1. Lancez le panneau de contrôle: python control_panel_launcher.py")
        print("2. Ouvrez http://127.0.0.1:8503 dans votre navigateur")
        print("3. Cliquez 'Démarrer le Serveur' dans l'onglet 'Contrôle Serveur'")
    else:
        print("❌ DIAGNOSTIC ÉCHOUÉ!")
        print("⚠️  Problèmes détectés - consultez les messages ci-dessus")
        print("\n🔧 SOLUTIONS POSSIBLES:")
        print("1. Vérifiez que tous les fichiers sont présents")
        print("2. Installez les dépendances manquantes")
        print("3. Vérifiez la syntaxe de launcher.py")
        print("4. Redémarrez votre terminal/console")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
    input("\nAppuyez sur Entrée pour fermer...") 