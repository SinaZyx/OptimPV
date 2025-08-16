"""Script pour exécuter tous les tests des nouvelles fonctionnalités ERP.

Usage:
    python run_new_features_tests.py [all|autocomplete|navigation|map|integration]
"""

import sys
import os
import unittest
from datetime import datetime

# Ajouter le chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


def run_specific_tests(test_type='all'):
    """Exécuter des tests spécifiques selon le type."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Dictionnaire des modules de test
    test_modules = {
        'autocomplete': 'test_address_autocomplete',
        'navigation': 'test_navigation_tabs',
        'map': 'test_map_selector',
        'integration': 'test_new_features_integration'
    }
    
    if test_type == 'all':
        # Charger tous les tests
        for module_name in test_modules.values():
            try:
                module = __import__(module_name)
                suite.addTests(loader.loadTestsFromModule(module))
            except ImportError as e:
                print(f"⚠️  Impossible de charger {module_name}: {e}")
    else:
        # Charger un test spécifique
        module_name = test_modules.get(test_type)
        if module_name:
            try:
                module = __import__(module_name)
                suite.addTests(loader.loadTestsFromModule(module))
            except ImportError as e:
                print(f"❌ Erreur lors du chargement de {module_name}: {e}")
                return None
        else:
            print(f"❌ Type de test inconnu: {test_type}")
            print(f"   Types disponibles: {', '.join(test_modules.keys())}")
            return None
    
    return suite


def main():
    """Fonction principale."""
    print("="*60)
    print("TESTS DES NOUVELLES FONCTIONNALITES ERP")
    print("="*60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Déterminer quel test exécuter
    test_type = sys.argv[1] if len(sys.argv) > 1 else 'all'
    
    print(f"Type de test: {test_type}")
    print()
    
    # Créer et exécuter la suite de tests
    suite = run_specific_tests(test_type)
    
    if suite:
        # Configurer le runner avec plus de détails
        runner = unittest.TextTestRunner(
            verbosity=2,
            stream=sys.stdout,
            failfast=False
        )
        
        # Exécuter les tests
        result = runner.run(suite)
        
        # Afficher le résumé
        print("\n" + "="*60)
        print("RESUME DES TESTS")
        print("="*60)
        
        total_tests = result.testsRun
        success = total_tests - len(result.failures) - len(result.errors)
        
        print(f"Total des tests executes : {total_tests}")
        print(f"[OK] Succes : {success}")
        print(f"[FAIL] Echecs : {len(result.failures)}")
        print(f"[ERROR] Erreurs : {len(result.errors)}")
        
        # Taux de réussite
        if total_tests > 0:
            success_rate = (success / total_tests) * 100
            print(f"\nTaux de reussite : {success_rate:.1f}%")
        
        # Détails des échecs
        if result.failures:
            print("\n" + "="*60)
            print("DETAILS DES ECHECS")
            print("="*60)
            for test, traceback in result.failures:
                print(f"\n{test}:")
                print(traceback)
        
        # Détails des erreurs
        if result.errors:
            print("\n" + "="*60)
            print("DETAILS DES ERREURS")
            print("="*60)
            for test, traceback in result.errors:
                print(f"\n{test}:")
                print(traceback)
        
        # Code de sortie
        if result.failures or result.errors:
            sys.exit(1)
        else:
            print("\n[OK] Tous les tests sont passes avec succes!")
            sys.exit(0)


if __name__ == '__main__':
    main()