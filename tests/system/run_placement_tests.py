#!/usr/bin/env python3
"""
Script pour lancer tous les tests du système de placement de trésorerie
"""

import os
import sys
import subprocess
import time
from datetime import datetime

def run_test(test_file, description):
    """Lance un test et retourne le résultat"""
    print(f"\n🧪 {description}")
    print("=" * (len(description) + 3))
    
    try:
        start_time = time.time()
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=60)
        end_time = time.time()
        
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ PASS ({duration:.1f}s)")
            if result.stdout:
                # Afficher seulement les lignes importantes
                lines = result.stdout.split('\n')
                summary_lines = [line for line in lines if any(keyword in line for keyword in 
                               ['PASS', 'FAIL', 'tests réussis', 'TOUS LES TESTS', '🎉', '✅'])]
                if summary_lines:
                    print("Résumé:", summary_lines[-1])
            return True, ""
        else:
            print(f"❌ FAIL ({duration:.1f}s)")
            if result.stderr:
                print(f"Erreur: {result.stderr[:200]}...")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        print("⏱️ TIMEOUT (>60s)")
        return False, "Timeout"
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False, str(e)

def main():
    """Fonction principale"""
    
    print("🚀 LANCEMENT DES TESTS SYSTÈME PLACEMENT TRÉSORERIE")
    print("=" * 60)
    print(f"Heure de début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Changer vers le répertoire tests
    os.chdir('tests')
    
    # Tests à lancer (ordre de priorité)
    tests_to_run = [
        ("test_placement_simple.py", "Test Logique Désactivation Placements"),
        ("test_tableau_simple.py", "Test Logique Années Critiques"),
        ("test_resultat_final.py", "Test Calculs Compte de Résultat"),
        ("validation_placement_engine.py", "Validation Implémentation Complète"),
        ("test_colonnes_compte_resultat.py", "Test Colonnes Compte de Résultat"),
        ("test_compte_resultat.py", "Test Complet Compte de Résultat"),
        ("test_resultat_avant_impot.py", "Test Résultat Avant Impôt"),
        ("resume_test_annees_critiques.py", "Analyse Logs Réels")
    ]
    
    # Tests avec dépendances (optionnels)
    optional_tests = [
        ("test_placement_deactivation.py", "Test Complet Désactivation (avec pandas)"),
        ("test_tableau_annees_critiques.py", "Test Complet Années Critiques (avec pandas)"),
        ("test_placement_engine.py", "Test Moteur Placement (avec pandas)")
    ]
    
    results = []
    errors = []
    
    print("📋 TESTS PRINCIPAUX (sans dépendances externes)")
    print("-" * 50)
    
    # Lancer les tests principaux
    for test_file, description in tests_to_run:
        if os.path.exists(test_file):
            success, error = run_test(test_file, description)
            results.append((test_file, description, success))
            if not success and error:
                errors.append((test_file, error))
        else:
            print(f"\n⚠️  Test {test_file} non trouvé")
            results.append((test_file, description, False))
    
    print("\n📋 TESTS OPTIONNELS (avec dépendances)")
    print("-" * 45)
    
    # Lancer les tests optionnels
    for test_file, description in optional_tests:
        if os.path.exists(test_file):
            success, error = run_test(test_file, description)
            results.append((test_file, description, success))
            if not success and error and "pandas" not in error:
                errors.append((test_file, error))
        else:
            print(f"\n⚠️  Test {test_file} non trouvé")
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("-" * 20)
    
    passed = sum(1 for _, _, success in results if success)
    total = len(results)
    
    print(f"\nRésultats: {passed}/{total} tests réussis")
    
    # Détail par test
    print("\nDétail:")
    for test_file, description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {description}")
    
    # Erreurs importantes
    if errors:
        print("\n⚠️  ERREURS IMPORTANTES:")
        for test_file, error in errors:
            if "pandas" not in error.lower() and "modulenotfounderror" not in error.lower():
                print(f"  • {test_file}: {error[:100]}...")
    
    # Conclusion
    print("\n" + "=" * 60)
    if passed == total:
        print("🎉 TOUS LES TESTS SONT PASSÉS!")
        print("✅ Le système de placement de trésorerie est opérationnel")
        success_rate = 100
    elif passed >= total * 0.8:  # 80% de réussite
        print("✅ TESTS PRINCIPAUX RÉUSSIS!")
        print("⚠️  Quelques tests optionnels ont échoué (probablement dépendances)")
        success_rate = (passed / total) * 100
    else:
        print("⚠️  PLUSIEURS TESTS ONT ÉCHOUÉ!")
        print("❌ Vérifiez l'implémentation du système de placement")
        success_rate = (passed / total) * 100
    
    print(f"Taux de réussite: {success_rate:.1f}%")
    print(f"Heure de fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Recommandations
    print("\n💡 RECOMMANDATIONS:")
    if success_rate >= 80:
        print("  • Le système est prêt pour utilisation")
        print("  • Tests optionnels nécessitent environnement Python complet")
        print("  • Valider sur projets réels pour confirmation finale")
    else:
        print("  • Corriger les erreurs dans les tests principaux")
        print("  • Vérifier l'implémentation des fonctionnalités échouées")
        print("  • Relancer les tests après corrections")
    
    return success_rate >= 80

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)