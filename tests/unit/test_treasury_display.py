#!/usr/bin/env python3
"""
Test de l'affichage de la trésorerie et des placements
Test les corrections apportées à la Section VI
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime

# Import des modules à tester
from modules.table_finance.financial_display_utils import calculate_annual_total_from_monthly

def test_treasury_values():
    """Test que les valeurs de trésorerie sont correctement calculées comme soldes"""
    print("\n=== TEST 1: Valeurs de trésorerie (soldes) ===")
    
    # Créer un DataFrame de test avec des valeurs de trésorerie variables
    dates = pd.date_range('2024-01-01', periods=12, freq='M')
    test_data = pd.DataFrame({
        'Solde_Tresorerie_Fin_Mois': [8500, 8266, 8100, 8500, 9000, 9500, 10000, 10225, 9800, 9500, 9200, 8900],
        'Reserve_Minimum_Requise': [7000] * 12,  # Valeur constante pour la réserve
        'Total_Placements': [0, 0, 0, 10250, 10263, 10276, 10289, 10302, 10315, 10328, 10341, 10354],
    }, index=dates)
    
    # Test pour Solde_Tresorerie_Fin_Mois (doit retourner la dernière valeur)
    result_tresorerie = calculate_annual_total_from_monthly(test_data, 'Solde_Tresorerie_Fin_Mois', 2024)
    expected_tresorerie = 8900  # Dernière valeur
    
    print(f"Trésorerie fin de mois - Attendu: {expected_tresorerie}€, Obtenu: {result_tresorerie}€")
    assert abs(result_tresorerie - expected_tresorerie) < 0.01, f"Erreur: trésorerie devrait être {expected_tresorerie}, pas {result_tresorerie}"
    
    # Test pour Reserve_Minimum_Requise (doit retourner la dernière valeur)
    result_reserve = calculate_annual_total_from_monthly(test_data, 'Reserve_Minimum_Requise', 2024)
    expected_reserve = 7000  # Dernière valeur
    
    print(f"Réserve minimum - Attendu: {expected_reserve}€, Obtenu: {result_reserve}€")
    assert abs(result_reserve - expected_reserve) < 0.01, f"Erreur: réserve devrait être {expected_reserve}, pas {result_reserve}"
    
    # Test pour Total_Placements (doit retourner la dernière valeur)
    result_placements = calculate_annual_total_from_monthly(test_data, 'Total_Placements', 2024)
    expected_placements = 10354  # Dernière valeur
    
    print(f"Total placements - Attendu: {expected_placements}€, Obtenu: {result_placements}€")
    assert abs(result_placements - expected_placements) < 0.01, f"Erreur: placements devrait être {expected_placements}, pas {result_placements}"
    
    print("✅ TEST 1 RÉUSSI: Les soldes retournent bien la dernière valeur")
    return True

def test_flux_values():
    """Test que les flux sont correctement calculés comme sommes"""
    print("\n=== TEST 2: Valeurs de flux (sommes) ===")
    
    # Créer un DataFrame de test
    dates = pd.date_range('2024-01-01', periods=12, freq='M')
    test_data = pd.DataFrame({
        'Revenus_Total': [1000] * 12,  # 12,000 attendu
        'OPEX': [100] * 12,  # 1,200 attendu
        'Interets_Placements_Mensuels': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120],  # 780 attendu
    }, index=dates)
    
    # Test pour Revenus_Total (doit retourner la somme)
    result_revenus = calculate_annual_total_from_monthly(test_data, 'Revenus_Total', 2024)
    expected_revenus = 12000
    
    print(f"Revenus totaux - Attendu: {expected_revenus}€, Obtenu: {result_revenus}€")
    assert abs(result_revenus - expected_revenus) < 0.01, f"Erreur: revenus devrait être {expected_revenus}, pas {result_revenus}"
    
    # Test pour Interets_Placements_Mensuels (doit retourner la somme)
    result_interets = calculate_annual_total_from_monthly(test_data, 'Interets_Placements_Mensuels', 2024)
    expected_interets = 780
    
    print(f"Intérêts placements - Attendu: {expected_interets}€, Obtenu: {result_interets}€")
    assert abs(result_interets - expected_interets) < 0.01, f"Erreur: intérêts devrait être {expected_interets}, pas {result_interets}"
    
    print("✅ TEST 2 RÉUSSI: Les flux retournent bien la somme")
    return True

def test_ratio_calculation():
    """Test le calcul du ratio de sécurité"""
    print("\n=== TEST 3: Calcul du ratio de sécurité ===")
    
    # Test de la formule lambda du ratio
    ratio_formula = eval("lambda row: (row.get('Solde_Tresorerie_Fin_Mois', 0) / row.get('Reserve_Minimum_Requise', 1)) if row.get('Reserve_Minimum_Requise', 0) > 0 else (999.99 if row.get('Solde_Tresorerie_Fin_Mois', 0) > 0 else 0)")
    
    # Test 1: Ratio normal
    row1 = {'Solde_Tresorerie_Fin_Mois': 10000, 'Reserve_Minimum_Requise': 7000}
    ratio1 = ratio_formula(row1)
    expected1 = 10000 / 7000  # ~1.43
    print(f"Ratio normal - Attendu: {expected1:.2f}, Obtenu: {ratio1:.2f}")
    assert abs(ratio1 - expected1) < 0.01
    
    # Test 2: Réserve = 0, trésorerie > 0
    row2 = {'Solde_Tresorerie_Fin_Mois': 10000, 'Reserve_Minimum_Requise': 0}
    ratio2 = ratio_formula(row2)
    expected2 = 999.99
    print(f"Réserve=0, Tréso>0 - Attendu: {expected2}, Obtenu: {ratio2}")
    assert ratio2 == expected2
    
    # Test 3: Réserve = 0, trésorerie = 0
    row3 = {'Solde_Tresorerie_Fin_Mois': 0, 'Reserve_Minimum_Requise': 0}
    ratio3 = ratio_formula(row3)
    expected3 = 0
    print(f"Réserve=0, Tréso=0 - Attendu: {expected3}, Obtenu: {ratio3}")
    assert ratio3 == expected3
    
    # Test 4: Trésorerie négative
    row4 = {'Solde_Tresorerie_Fin_Mois': -5000, 'Reserve_Minimum_Requise': 7000}
    ratio4 = ratio_formula(row4)
    expected4 = -5000 / 7000  # ~-0.71
    print(f"Tréso négative - Attendu: {expected4:.2f}, Obtenu: {ratio4:.2f}")
    assert abs(ratio4 - expected4) < 0.01
    
    print("✅ TEST 3 RÉUSSI: Le ratio de sécurité est correctement calculé")
    return True

def analyze_logs():
    """Analyse les logs pour identifier les problèmes"""
    print("\n=== ANALYSE DES LOGS ===")
    
    try:
        with open('log.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Rechercher les dernières entrées pertinentes
        treasury_lines = []
        placement_lines = []
        error_lines = []
        
        for i, line in enumerate(lines):
            if 'Solde_Tresorerie_Fin_Mois' in line:
                treasury_lines.append((i, line.strip()))
            if 'Total_Placements' in line or 'total_placements' in line:
                placement_lines.append((i, line.strip()))
            if 'ERROR' in line or 'ERREUR' in line:
                error_lines.append((i, line.strip()))
        
        # Afficher les dernières lignes pertinentes
        print("\n📊 Dernières mentions de trésorerie:")
        for i, line in treasury_lines[-5:]:
            print(f"  Ligne {i}: {line}")
        
        print("\n💰 Dernières mentions de placements:")
        for i, line in placement_lines[-5:]:
            print(f"  Ligne {i}: {line}")
        
        print("\n❌ Dernières erreurs:")
        for i, line in error_lines[-5:]:
            print(f"  Ligne {i}: {line}")
        
        # Recherche spécifique du problème 8500
        print("\n🔍 Recherche de la valeur 8500:")
        found_8500 = False
        for i, line in enumerate(lines):
            if '8500' in line or '8,500' in line:
                print(f"  Ligne {i}: {line.strip()}")
                found_8500 = True
                # Afficher le contexte
                if i > 0:
                    print(f"    Contexte -1: {lines[i-1].strip()}")
                if i < len(lines) - 1:
                    print(f"    Contexte +1: {lines[i+1].strip()}")
        
        if not found_8500:
            print("  ⚠️ Valeur 8500 non trouvée dans les logs")
        
    except FileNotFoundError:
        print("❌ Fichier log.txt non trouvé")
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse des logs: {e}")

def main():
    """Exécute tous les tests"""
    print("🚀 DÉMARRAGE DES TESTS DE LA SECTION VI")
    print("=" * 60)
    
    try:
        # Test 1: Soldes
        test_treasury_values()
        
        # Test 2: Flux
        test_flux_values()
        
        # Test 3: Ratio
        test_ratio_calculation()
        
        # Analyse des logs
        analyze_logs()
        
        print("\n" + "=" * 60)
        print("✅ TOUS LES TESTS SONT RÉUSSIS!")
        print("\n💡 Recommandations:")
        print("1. Si la trésorerie reste à 8500€, vérifier initial_cash_balance dans la config")
        print("2. Si les placements > trésorerie, c'est normal (fonds de réserve ségrégué)")
        print("3. La réserve minimum devrait maintenant afficher la valeur mensuelle")
        print("4. Le ratio de sécurité devrait être cohérent (999.99 si pas de réserve requise)")
        
    except AssertionError as e:
        print(f"\n❌ ÉCHEC DU TEST: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()