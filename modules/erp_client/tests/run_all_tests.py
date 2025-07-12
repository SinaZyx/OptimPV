"""Script principal pour lancer tous les tests du module ERP.

Ce script lance tous les tests dans l'ordre logique :
1. Vérification des imports (utils)
2. Tests unitaires (unit)
3. Tests d'intégration (integration)  
4. Tests système (system)
"""

import os
import sys
import subprocess
import time
from datetime import datetime


def print_header(title: str):
    """Affiche un en-tête formaté."""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def print_section(title: str):
    """Affiche une section formatée."""
    print(f"\n📋 {title}")
    print("-" * 40)


def run_python_script(script_path: str, description: str) -> bool:
    """Exécute un script Python et retourne True si succès."""
    print(f"🚀 Lancement: {description}")
    print(f"   Fichier: {script_path}")
    
    if not os.path.exists(script_path):
        print(f"❌ Fichier non trouvé: {script_path}")
        return False
    
    try:
        start_time = time.time()
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, text=True, timeout=60)
        end_time = time.time()
        
        if result.returncode == 0:
            print(f"✅ Succès en {end_time - start_time:.2f}s")
            if result.stdout:
                # Afficher seulement les lignes importantes (succès et erreurs)
                lines = result.stdout.split('\n')
                for line in lines:
                    if any(marker in line for marker in ['✅', '❌', '⚠️', '🎉', 'ERROR', 'FAILED']):
                        print(f"   {line}")
        else:
            print(f"❌ Échec (code {result.returncode}) en {end_time - start_time:.2f}s")
            if result.stderr:
                print(f"   Erreur: {result.stderr[:200]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout (>60s)")
        return False
    except Exception as e:
        print(f"❌ Erreur d'exécution: {e}")
        return False
    
    return True


def main():
    """Fonction principale."""
    print_header("🧪 SUITE DE TESTS COMPLETE - MODULE ERP")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Chemin de base
    base_path = "/mnt/c/Users/kingc/OptimPV/modules/erp_client/tests"
    
    # Définir l'ordre des tests
    test_suite = [
        {
            "category": "🔧 UTILITAIRES",
            "tests": [
                (f"{base_path}/utils/test_imports_integrity.py", "Vérification intégrité des imports"),
                (f"{base_path}/utils/check_imports_simple.py", "Vérification rapide des imports"),
            ]
        },
        {
            "category": "🧪 TESTS UNITAIRES", 
            "tests": [
                (f"{base_path}/unit/test_models.py", "Tests des modèles de données"),
                (f"{base_path}/unit/test_services.py", "Tests des services métier"),
            ]
        },
        {
            "category": "🔗 TESTS D'INTÉGRATION",
            "tests": [
                (f"{base_path}/integration/test_database.py", "Tests base de données"),
                (f"{base_path}/integration/test_map_integration.py", "Tests intégration carte"),
            ]
        },
        {
            "category": "🎭 TESTS SYSTÈME",
            "tests": [
                (f"{base_path}/system/test_end_to_end.py", "Tests end-to-end complets"),
            ]
        }
    ]
    
    # Statistiques globales
    total_tests = sum(len(category["tests"]) for category in test_suite)
    passed_tests = 0
    failed_tests = 0
    skipped_tests = 0
    
    # Exécuter tous les tests
    for category in test_suite:
        print_section(category["category"])
        
        for script_path, description in category["tests"]:
            if run_python_script(script_path, description):
                passed_tests += 1
            else:
                failed_tests += 1
    
    # Rapport final
    print_header("📊 RAPPORT FINAL")
    print(f"✅ Tests réussis: {passed_tests}")
    print(f"❌ Tests échoués: {failed_tests}")
    print(f"📊 Total tests: {total_tests}")
    
    if failed_tests == 0:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
        print("🛡️  Le module ERP est prêt pour l'utilisation")
    else:
        print(f"\n⚠️  {failed_tests} test(s) ont échoué")
        print("🔧 Veuillez corriger les erreurs avant de continuer")
    
    # Recommandations
    print_section("💡 RECOMMANDATIONS")
    if failed_tests > 0:
        print("1. Vérifiez les erreurs d'imports en premier")
        print("2. Installez les dépendances manquantes")
        print("3. Corrigez les erreurs de base avant les tests avancés")
    else:
        print("1. ✅ Module ERP validé et fonctionnel")
        print("2. ✅ Tous les imports sont corrects")
        print("3. ✅ Prêt pour l'utilisation en production")
    
    return failed_tests == 0


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrompus par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)