#!/usr/bin/env python3
"""
Script de lancement simplifié pour les tests de navigation OptimPV
================================================================

Ce script facilite l'exécution des tests automatisés avec différentes options.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def install_requirements():
    """Installe les dépendances nécessaires."""
    requirements_file = Path(__file__).parent / "requirements.txt"
    if requirements_file.exists():
        print("📦 Installation des dépendances...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ])
            print("✅ Dépendances installées")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur installation dépendances: {e}")
            return False
    return True

def setup_webdriver():
    """Configure automatiquement le webdriver."""
    print("🔧 Configuration du webdriver...")
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.firefox import GeckoDriverManager
        
        # Essayer Chrome
        try:
            ChromeDriverManager().install()
            print("✅ ChromeDriver configuré")
            return True
        except:
            pass
        
        # Essayer Firefox
        try:
            GeckoDriverManager().install()
            print("✅ GeckoDriver configuré")
            return True
        except:
            pass
            
        print("⚠️ Aucun driver automatique configuré - utilisation du PATH système")
        return True
        
    except ImportError:
        print("⚠️ webdriver-manager non installé - utilisation du PATH système")
        return True

def main():
    parser = argparse.ArgumentParser(description="Lanceur de tests de navigation OptimPV")
    parser.add_argument("--quick", action="store_true", help="Test rapide (headless, pas de screenshots)")
    parser.add_argument("--full", action="store_true", help="Test complet avec screenshots")
    parser.add_argument("--visible", action="store_true", help="Test avec navigateur visible")
    parser.add_argument("--install-deps", action="store_true", help="Installer les dépendances d'abord")
    
    args = parser.parse_args()
    
    if args.install_deps:
        if not install_requirements():
            return 1
        setup_webdriver()
    
    # Construire la commande
    test_script = Path(__file__).parent / "test_full_navigation.py"
    cmd = [sys.executable, str(test_script)]
    
    if args.quick:
        cmd.extend(["--headless", "--timeout", "30"])
    elif args.full:
        cmd.extend(["--headless", "--screenshots", "--timeout", "120"])
    elif args.visible:
        cmd.extend(["--screenshots", "--timeout", "120"])
    else:
        # Mode par défaut
        print("Mode par défaut: test rapide headless")
        cmd.extend(["--headless", "--timeout", "60"])
    
    print(f"🚀 Lancement: {' '.join(cmd)}")
    
    try:
        return subprocess.call(cmd)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrompu")
        return 1

if __name__ == "__main__":
    sys.exit(main())