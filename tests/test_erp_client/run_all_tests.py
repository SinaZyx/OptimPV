"""Script pour exécuter tous les tests du module ERP.

Ce script lance tous les tests du module ERP et génère un rapport détaillé.
"""

import os
import sys
import pytest
import time
from datetime import datetime

# Ajouter le chemin parent pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


def run_all_tests():
    """Exécute tous les tests du module ERP."""
    print("=" * 80)
    print("TESTS COMPLETS DU MODULE ERP CLIENT")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Répertoire: {os.path.dirname(os.path.abspath(__file__))}")
    print("=" * 80)
    
    # Définir les modules de test
    test_modules = [
        ("Database", "test_database.py"),
        ("Models", "test_models.py"),
        ("Services", "test_services.py"),
        ("UI Integration", "test_ui_integration.py"),
        ("Module Integration", "test_module_integration.py"),
        ("End-to-End", "test_end_to_end.py")
    ]
    
    # Options pytest
    pytest_args = [
        "-v",  # Verbose
        "--tb=short",  # Traceback court
        "--color=yes",  # Couleurs
        "-p", "no:warnings",  # Pas d'avertissements
    ]
    
    results = {}
    total_time = 0
    
    # Exécuter chaque module de test
    for name, test_file in test_modules:
        print(f"\n{'=' * 40}")
        print(f"Exécution des tests: {name}")
        print(f"Fichier: {test_file}")
        print(f"{'=' * 40}")
        
        test_path = os.path.join(os.path.dirname(__file__), test_file)
        
        if not os.path.exists(test_path):
            print(f"❌ Fichier non trouvé: {test_path}")
            results[name] = {"status": "NOT_FOUND", "tests": 0, "passed": 0, "failed": 0}
            continue
        
        start_time = time.time()
        
        # Exécuter les tests pour ce module
        result = pytest.main(pytest_args + [test_path, "-q"])
        
        elapsed_time = time.time() - start_time
        total_time += elapsed_time
        
        # Analyser le résultat
        if result == 0:
            status = "PASSED"
            print(f"✅ {name}: Tous les tests sont passés ({elapsed_time:.2f}s)")
        else:
            status = "FAILED"
            print(f"❌ {name}: Des tests ont échoué ({elapsed_time:.2f}s)")
        
        results[name] = {
            "status": status,
            "time": elapsed_time,
            "return_code": result
        }
    
    # Résumé final
    print("\n" + "=" * 80)
    print("RÉSUMÉ DES TESTS")
    print("=" * 80)
    
    passed_modules = sum(1 for r in results.values() if r["status"] == "PASSED")
    failed_modules = sum(1 for r in results.values() if r["status"] == "FAILED")
    not_found_modules = sum(1 for r in results.values() if r["status"] == "NOT_FOUND")
    
    print(f"\nModules testés: {len(test_modules)}")
    print(f"✅ Réussis: {passed_modules}")
    print(f"❌ Échoués: {failed_modules}")
    print(f"⚠️  Non trouvés: {not_found_modules}")
    print(f"\nTemps total: {total_time:.2f}s")
    
    # Détails par module
    print("\nDétails par module:")
    print("-" * 60)
    for name, result in results.items():
        status_icon = "✅" if result["status"] == "PASSED" else "❌" if result["status"] == "FAILED" else "⚠️"
        if result["status"] != "NOT_FOUND":
            print(f"{status_icon} {name:<25} {result['time']:>8.2f}s")
        else:
            print(f"{status_icon} {name:<25} {'N/A':>8}")
    
    # Exécuter également un test de couverture si disponible
    print("\n" + "=" * 80)
    print("TEST DE COUVERTURE")
    print("=" * 80)
    
    try:
        import coverage
        
        print("Exécution des tests avec couverture...")
        
        # Créer une instance de coverage
        cov = coverage.Coverage(source=['modules/erp_client'])
        cov.start()
        
        # Réexécuter tous les tests avec coverage
        pytest.main([
            "--quiet",
            os.path.dirname(__file__),
            "--ignore=run_all_tests.py"
        ])
        
        cov.stop()
        cov.save()
        
        # Générer le rapport
        print("\nRapport de couverture:")
        print("-" * 60)
        cov.report()
        
        # Sauvegarder le rapport HTML si possible
        html_dir = os.path.join(os.path.dirname(__file__), "coverage_html")
        cov.html_report(directory=html_dir)
        print(f"\n📊 Rapport HTML généré dans: {html_dir}")
        
    except ImportError:
        print("⚠️  Module 'coverage' non installé. Installer avec: pip install coverage")
    except Exception as e:
        print(f"❌ Erreur lors du test de couverture: {e}")
    
    # Retourner le code de sortie global
    if failed_modules > 0:
        return 1
    return 0


def run_specific_test_category(category):
    """Exécute une catégorie spécifique de tests."""
    categories = {
        "unit": ["test_database.py", "test_models.py", "test_services.py"],
        "integration": ["test_ui_integration.py", "test_module_integration.py"],
        "e2e": ["test_end_to_end.py"],
        "quick": ["test_models.py", "test_services.py"],
        "full": None  # Tous les tests
    }
    
    if category not in categories:
        print(f"❌ Catégorie inconnue: {category}")
        print(f"   Catégories disponibles: {', '.join(categories.keys())}")
        return 1
    
    test_files = categories[category]
    
    if test_files is None:
        # Exécuter tous les tests
        return run_all_tests()
    
    print(f"Exécution de la catégorie: {category}")
    print(f"Tests: {', '.join(test_files)}")
    
    pytest_args = ["-v", "--tb=short", "--color=yes"]
    test_paths = [os.path.join(os.path.dirname(__file__), f) for f in test_files]
    
    return pytest.main(pytest_args + test_paths)


if __name__ == "__main__":
    # Vérifier les arguments
    if len(sys.argv) > 1:
        category = sys.argv[1]
        exit_code = run_specific_test_category(category)
    else:
        exit_code = run_all_tests()
    
    # Message final
    if exit_code == 0:
        print("\n✅ Tous les tests sont passés avec succès!")
    else:
        print("\n❌ Des tests ont échoué. Vérifier les détails ci-dessus.")
    
    sys.exit(exit_code)