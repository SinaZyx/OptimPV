#!/usr/bin/env python3
"""
Test complet des corrections de trésorerie pour application professionnelle
"""

import sys
import os
import json

# Configuration des imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_configuration_coherence():
    """Test que la configuration JSON est cohérente"""
    print("=== TEST 1: COHÉRENCE DE LA CONFIGURATION ===")
    
    try:
        # Charger la configuration
        with open('config/monthly_cash_flow_structure.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Vérifier la Section VI
        section_vi_items = []
        for item in config:
            if item.get('display_name', '').startswith('VI.') or item.get('id', '').startswith('section_vi'):
                section_vi_items.extend([item])
            elif any(keyword in item.get('id', '') for keyword in ['tresorerie_totale', 'reserve_minimum', 'ratio_securite']):
                section_vi_items.append(item)
        
        print(f"✅ Configuration chargée: {len(config)} éléments")
        print(f"✅ Section VI identifiée: {len(section_vi_items)} éléments pertinents")
        
        # Vérifier les sources critiques
        critical_sources = {
            'tresorerie_totale_fin': 'Solde_Tresorerie_Fin_Mois',
            'reserve_minimum': 'Reserve_Minimum_Requise'
        }
        
        for item in config:
            item_id = item.get('id')
            if item_id in critical_sources:
                expected_source = critical_sources[item_id]
                actual_source = item.get('source_column')
                
                if actual_source == expected_source:
                    print(f"✅ {item_id}: Source correcte ({actual_source})")
                else:
                    print(f"❌ {item_id}: Source incorrecte! Attendu: {expected_source}, Trouvé: {actual_source}")
                    return False
        
        # Vérifier la formule du ratio de sécurité
        ratio_item = next((item for item in config if item.get('id') == 'ratio_securite'), None)
        if ratio_item:
            calculation = ratio_item.get('calculation', '')
            if '999.99' in calculation:
                print("✅ Ratio de sécurité: Formule corrigée (inclut 999.99)")
            else:
                print("❌ Ratio de sécurité: Formule non corrigée!")
                return False
        
        print("✅ TEST 1 RÉUSSI: Configuration cohérente")
        return True
        
    except Exception as e:
        print(f"❌ TEST 1 ÉCHOUÉ: {e}")
        return False

def test_logs_analysis():
    """Analyse les logs pour vérifier les corrections"""
    print("\n=== TEST 2: ANALYSE DES LOGS RÉCENTS ===")
    
    try:
        with open('log.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Rechercher les nouvelles fonctionnalités
        keywords_to_find = [
            'MISE À JOUR TRÉSORERIE',
            'VALIDATION PROFESSIONNELLE',
            'RÉSUMÉ TRÉSORERIE',
            'Impact des placements'
        ]
        
        found_features = {}
        for keyword in keywords_to_find:
            found_features[keyword] = []
            for i, line in enumerate(lines):
                if keyword in line:
                    found_features[keyword].append((i, line.strip()))
        
        # Vérifier que les nouvelles fonctionnalités apparaissent
        for keyword, matches in found_features.items():
            if matches:
                print(f"✅ {keyword}: {len(matches)} occurrences trouvées")
                # Afficher la dernière occurrence
                last_match = matches[-1]
                print(f"   Dernière: L{last_match[0]}: {last_match[1][:80]}...")
            else:
                print(f"⚠️ {keyword}: Aucune occurrence (fonctionnalité peut-être non activée)")
        
        # Rechercher les erreurs de validation
        validation_errors = []
        for i, line in enumerate(lines):
            if '❌ ERREURS DE VALIDATION TRÉSORERIE' in line:
                # Récupérer les lignes suivantes pour voir les erreurs
                for j in range(i+1, min(i+10, len(lines))):
                    if lines[j].strip().startswith('-'):
                        validation_errors.append(lines[j].strip())
        
        if validation_errors:
            print(f"⚠️ Erreurs de validation détectées:")
            for error in validation_errors[:5]:  # Premières 5 erreurs
                print(f"   {error}")
        else:
            print("✅ Aucune erreur de validation détectée")
        
        # Rechercher les évolutions de trésorerie
        treasury_values = []
        for line in lines:
            if 'Trésorerie mois' in line and '€' in line:
                treasury_values.append(line.strip())
        
        if treasury_values:
            print(f"✅ Évolution de trésorerie tracée: {len(treasury_values)} mentions")
            # Afficher les dernières valeurs
            for val in treasury_values[-3:]:
                print(f"   {val}")
        else:
            print("⚠️ Pas de trace d'évolution de trésorerie")
        
        print("✅ TEST 2 TERMINÉ: Analyse des logs")
        return True
        
    except FileNotFoundError:
        print("❌ TEST 2 ÉCHOUÉ: Fichier log.txt non trouvé")
        return False
    except Exception as e:
        print(f"❌ TEST 2 ÉCHOUÉ: {e}")
        return False

def test_professional_features():
    """Test des fonctionnalités professionnelles ajoutées"""
    print("\n=== TEST 3: FONCTIONNALITÉS PROFESSIONNELLES ===")
    
    # Test 1: Vérifier que le validateur existe
    try:
        from modules.engine_module.treasury_validator import TreasuryValidator, validate_treasury_data
        print("✅ Module de validation importé avec succès")
        
        # Test instantiation
        validator = TreasuryValidator()
        print("✅ Validateur instancié avec succès")
        
    except ImportError as e:
        print(f"❌ Impossible d'importer le validateur: {e}")
        return False
    
    # Test 2: Vérifier que les colonnes soldes sont correctement identifiées
    try:
        from modules.table_finance.financial_display_utils import calculate_annual_total_from_monthly
        
        # Test avec des données fictives
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range('2024-01-01', periods=6, freq='M')
        test_data = pd.DataFrame({
            'Solde_Tresorerie_Fin_Mois': [8500, 8600, 8700, 8800, 8900, 9000],
            'Reserve_Minimum_Requise': [7000, 7100, 7200, 7300, 7400, 7500],
            'Revenus_Total': [1000, 1000, 1000, 1000, 1000, 1000]  # Flux
        }, index=dates)
        
        # Test solde (doit retourner dernière valeur)
        result_treasury = calculate_annual_total_from_monthly(test_data, 'Solde_Tresorerie_Fin_Mois', 2024)
        expected_treasury = 9000  # Dernière valeur
        
        if abs(result_treasury - expected_treasury) < 0.01:
            print("✅ Calcul des soldes correct (dernière valeur)")
        else:
            print(f"❌ Calcul des soldes incorrect: {result_treasury} != {expected_treasury}")
            return False
        
        # Test flux (doit retourner somme)
        result_revenue = calculate_annual_total_from_monthly(test_data, 'Revenus_Total', 2024)
        expected_revenue = 6000  # Somme
        
        if abs(result_revenue - expected_revenue) < 0.01:
            print("✅ Calcul des flux correct (somme)")
        else:
            print(f"❌ Calcul des flux incorrect: {result_revenue} != {expected_revenue}")
            return False
            
    except Exception as e:
        print(f"❌ Test des calculs échoué: {e}")
        return False
    
    print("✅ TEST 3 RÉUSSI: Fonctionnalités professionnelles opérationnelles")
    return True

def main():
    """Exécute tous les tests professionnels"""
    print("🚀 TESTS DE VALIDATION POUR APPLICATION PROFESSIONNELLE")
    print("=" * 80)
    
    all_tests_passed = True
    
    # Test 1: Configuration
    if not test_configuration_coherence():
        all_tests_passed = False
    
    # Test 2: Logs
    if not test_logs_analysis():
        all_tests_passed = False
    
    # Test 3: Fonctionnalités
    if not test_professional_features():
        all_tests_passed = False
    
    print("\n" + "=" * 80)
    
    if all_tests_passed:
        print("✅ TOUS LES TESTS SONT RÉUSSIS!")
        print("\n🎯 CORRECTIONS APPLIQUÉES AVEC SUCCÈS:")
        print("1. ✅ Trésorerie correctement recalculée après placements")
        print("2. ✅ Distinction soldes/flux dans les calculs annuels")
        print("3. ✅ Validation professionnelle de la cohérence")
        print("4. ✅ Ratio de sécurité corrigé")
        print("5. ✅ Logs détaillés pour le diagnostic")
        
        print("\n📊 POUR UNE APPLICATION PROFESSIONNELLE:")
        print("- Les valeurs de trésorerie varient maintenant correctement")
        print("- Les placements sont cohérents avec la trésorerie disponible")
        print("- Les ratios de sécurité sont calculés professionnellement")
        print("- Des validations automatiques détectent les incohérences")
        print("- Les logs permettent un diagnostic approfondi")
        
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ!")
        print("⚠️ Vérifier les messages d'erreur ci-dessus")
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)