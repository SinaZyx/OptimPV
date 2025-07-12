"""Test de démarrage Streamlit pour détecter toutes les erreurs d'imports.

Ce test lance streamlit run app.py et capture toutes les erreurs
pour identifier exactement quels imports posent problème.
"""

import subprocess
import sys
import os
import time
from pathlib import Path
import signal

def test_streamlit_startup():
    """Lance Streamlit et capture les erreurs de démarrage."""
    print("🚀 Test de démarrage Streamlit...")
    print("Cela va lancer l'application et capturer les erreurs")
    
    # Changer vers le répertoire du projet
    project_root = Path(__file__).parent.parent.parent.parent.parent
    os.chdir(project_root)
    
    print(f"📁 Répertoire: {project_root}")
    print("⏳ Lancement de streamlit run app.py...")
    
    try:
        # Lancer Streamlit avec timeout
        process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless", "true"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            universal_newlines=True
        )
        
        # Attendre un peu pour que Streamlit démarre
        stdout_lines = []
        stderr_lines = []
        
        start_time = time.time()
        timeout = 30  # 30 secondes timeout
        
        while time.time() - start_time < timeout:
            # Lire stdout
            if process.stdout:
                line = process.stdout.readline()
                if line:
                    stdout_lines.append(line.strip())
                    print(f"📤 STDOUT: {line.strip()}")
            
            # Lire stderr
            if process.stderr:
                line = process.stderr.readline()
                if line:
                    stderr_lines.append(line.strip())
                    print(f"📥 STDERR: {line.strip()}")
            
            # Vérifier si le processus s'est terminé
            if process.poll() is not None:
                break
                
            # Si on voit "Network URL" ou "Local URL", c'est que ça marche
            if any("Local URL" in line or "Network URL" in line for line in stdout_lines):
                print("✅ Streamlit démarré avec succès!")
                break
                
            time.sleep(0.1)
        
        # Tuer le processus s'il tourne encore
        if process.poll() is None:
            print("⏹️ Arrêt du processus Streamlit...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        # Analyser les erreurs
        print("\n" + "="*60)
        print("📊 ANALYSE DES ERREURS")
        print("="*60)
        
        errors_found = []
        import_errors = []
        
        all_output = stdout_lines + stderr_lines
        
        for line in all_output:
            # Chercher les erreurs d'import
            if "ModuleNotFoundError" in line:
                import_errors.append(line)
                print(f"❌ IMPORT ERROR: {line}")
            elif "ImportError" in line:
                import_errors.append(line)
                print(f"❌ IMPORT ERROR: {line}")
            elif "NameError" in line:
                errors_found.append(line)
                print(f"❌ NAME ERROR: {line}")
            elif "AttributeError" in line:
                errors_found.append(line)
                print(f"❌ ATTRIBUTE ERROR: {line}")
            elif "Traceback" in line:
                print(f"🔍 TRACEBACK: {line}")
            elif "Error" in line and "error" not in line.lower():
                errors_found.append(line)
                print(f"⚠️ OTHER ERROR: {line}")
        
        # Résumé
        print(f"\n📈 RÉSUMÉ:")
        print(f"- Erreurs d'import: {len(import_errors)}")
        print(f"- Autres erreurs: {len(errors_found)}")
        
        if len(import_errors) == 0 and len(errors_found) == 0:
            print("🎉 AUCUNE ERREUR DÉTECTÉE!")
            print("✅ L'application semble démarrer correctement")
            return True
        else:
            print("⚠️ Des erreurs ont été détectées")
            return False
            
    except FileNotFoundError:
        print("❌ Streamlit n'est pas installé")
        print("💡 Installez avec: pip install streamlit")
        return False
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_python_import_only():
    """Test d'import Python simple sans Streamlit."""
    print("\n🐍 Test d'import Python simple...")
    
    try:
        # Test import de l'app principal
        process = subprocess.run(
            [sys.executable, "-c", "import app; print('✅ Import app.py réussi')"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path(__file__).parent.parent.parent.parent.parent
        )
        
        if process.returncode == 0:
            print("✅ Import Python de app.py réussi")
            print(f"📤 Output: {process.stdout}")
            return True
        else:
            print("❌ Erreur d'import Python")
            print(f"📥 Error: {process.stderr}")
            
            # Analyser l'erreur
            stderr = process.stderr
            if "No module named 'streamlit'" in stderr:
                print("💡 Problème: Streamlit non installé")
            elif "ModuleNotFoundError" in stderr:
                print("💡 Problème: Module manquant détecté")
            elif "ImportError" in stderr:
                print("💡 Problème: Erreur d'import détectée")
            
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout lors de l'import")
        return False
    except Exception as e:
        print(f"❌ Erreur test import: {e}")
        return False

def main():
    """Fonction principale."""
    print("🧪 TEST DE DÉMARRAGE STREAMLIT COMPLET")
    print("="*60)
    print("Ce test va révéler TOUTES les erreurs réelles de l'application")
    print("="*60)
    
    # Test 1: Import Python simple
    python_ok = test_python_import_only()
    
    # Test 2: Démarrage Streamlit complet (seulement si Python OK)
    if python_ok:
        streamlit_ok = test_streamlit_startup()
    else:
        print("⏭️ Streamlit test skippé (import Python failed)")
        streamlit_ok = False
    
    # Résumé final
    print("\n" + "="*60)
    print("🏁 RÉSUMÉ FINAL")
    print("="*60)
    
    if python_ok and streamlit_ok:
        print("🎉 SUCCESS: L'application démarre sans erreur!")
    elif python_ok:
        print("⚠️ PARTIAL: Import Python OK, mais problèmes Streamlit")
    else:
        print("❌ FAILED: Erreurs d'import dès le niveau Python")
    
    print("\n💡 ACTIONS RECOMMANDÉES:")
    if not python_ok:
        print("1. Corriger les erreurs d'import Python de base")
        print("2. Installer les dépendances manquantes")
    elif not streamlit_ok:
        print("1. Installer Streamlit: pip install streamlit")
        print("2. Vérifier les imports spécifiques à Streamlit")
    else:
        print("1. ✅ Tout fonctionne!")
    
    return python_ok and streamlit_ok

if __name__ == "__main__":
    main()