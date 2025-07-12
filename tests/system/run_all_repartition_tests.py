"""
Script principal pour exécuter tous les tests du module de répartition
"""

import sys
import os
import unittest
from datetime import datetime

# Ajouter le chemin du module parent
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Importer tous les modules de test
from test_repartition_models import TestRepartitionKey, TestRepartitionPeriod, TestRepartitionRule, TestRepartitionCondition, TestRepartitionTemplate
from test_repartition_validators import TestRepartitionValidator, TestQuickValidation
from test_repartition_calculations import TestStaticKeysCalculation, TestTemporalKeysCalculation, TestDynamicRulesCalculation, TestOptimization, TestMetricsCalculation
from test_repartition_manager import TestRepartitionKeyManager, TestRepartitionKeyManagerEdgeCases
from test_repartition_integration import TestIntegrationCompleteWorkflow


def run_all_tests():
    """Exécuter tous les tests avec un rapport détaillé"""
    
    print("="*80)
    print("EXÉCUTION DE TOUS LES TESTS DU MODULE DE RÉPARTITION")
    print(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()
    
    # Créer une suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Ajouter tous les tests par catégorie
    test_categories = {
        "Modèles de données": [
            TestRepartitionKey,
            TestRepartitionPeriod,
            TestRepartitionRule,
            TestRepartitionCondition,
            TestRepartitionTemplate
        ],
        "Validateurs": [
            TestRepartitionValidator,
            TestQuickValidation
        ],
        "Calculs": [
            TestStaticKeysCalculation,
            TestTemporalKeysCalculation,
            TestDynamicRulesCalculation,
            TestOptimization,
            TestMetricsCalculation
        ],
        "Manager principal": [
            TestRepartitionKeyManager,
            TestRepartitionKeyManagerEdgeCases
        ],
        "Tests d'intégration": [
            TestIntegrationCompleteWorkflow
        ]
    }
    
    # Statistiques
    total_test_cases = 0
    category_stats = {}
    
    # Ajouter les tests à la suite
    for category, test_classes in test_categories.items():
        category_suite = unittest.TestSuite()
        for test_class in test_classes:
            tests = loader.loadTestsFromTestCase(test_class)
            category_suite.addTests(tests)
            total_test_cases += tests.countTestCases()
        
        category_stats[category] = tests.countTestCases()
        suite.addTests(category_suite)
    
    # Afficher le résumé avant exécution
    print("RÉSUMÉ DES TESTS À EXÉCUTER :")
    print("-" * 40)
    for category, count in category_stats.items():
        print(f"{category:.<30} {count} tests")
    print("-" * 40)
    print(f"{'TOTAL':.<30} {total_test_cases} tests")
    print()
    
    # Exécuter les tests avec un runner personnalisé
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    print("EXÉCUTION DES TESTS...")
    print("="*80)
    
    start_time = datetime.now()
    result = runner.run(suite)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Afficher le rapport final
    print("\n" + "="*80)
    print("RAPPORT FINAL")
    print("="*80)
    
    print(f"\nTemps d'exécution : {duration:.2f} secondes")
    print(f"Tests exécutés : {result.testsRun}")
    print(f"Succès : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Échecs : {len(result.failures)}")
    print(f"Erreurs : {len(result.errors)}")
    
    # Détails des échecs
    if result.failures:
        print("\nDÉTAILS DES ÉCHECS :")
        print("-" * 40)
        for test, traceback in result.failures:
            print(f"\n❌ {test}")
            print(traceback)
    
    # Détails des erreurs
    if result.errors:
        print("\nDÉTAILS DES ERREURS :")
        print("-" * 40)
        for test, traceback in result.errors:
            print(f"\n⚠️ {test}")
            print(traceback)
    
    # Conclusion
    print("\n" + "="*80)
    if result.wasSuccessful():
        print("✅ TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS !")
        print("Le module de répartition des clés est prêt à l'emploi.")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("Veuillez corriger les erreurs avant de déployer.")
    print("="*80)
    
    return result.wasSuccessful()


def run_specific_category(category_name):
    """Exécuter uniquement les tests d'une catégorie spécifique"""
    
    categories = {
        "models": [TestRepartitionKey, TestRepartitionPeriod, TestRepartitionRule, TestRepartitionCondition, TestRepartitionTemplate],
        "validators": [TestRepartitionValidator, TestQuickValidation],
        "calculations": [TestStaticKeysCalculation, TestTemporalKeysCalculation, TestDynamicRulesCalculation, TestOptimization, TestMetricsCalculation],
        "manager": [TestRepartitionKeyManager, TestRepartitionKeyManagerEdgeCases],
        "integration": [TestIntegrationCompleteWorkflow]
    }
    
    if category_name not in categories:
        print(f"Catégorie '{category_name}' non reconnue.")
        print(f"Catégories disponibles : {', '.join(categories.keys())}")
        return False
    
    print(f"\nExécution des tests de la catégorie : {category_name}")
    print("-" * 50)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for test_class in categories[category_name]:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # Vérifier les arguments de ligne de commande
    if len(sys.argv) > 1:
        category = sys.argv[1]
        success = run_specific_category(category)
    else:
        # Exécuter tous les tests
        success = run_all_tests()
    
    # Code de sortie
    sys.exit(0 if success else 1)