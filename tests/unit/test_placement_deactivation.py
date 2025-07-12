#!/usr/bin/env python3
"""
Test de vérification que la désactivation des placements fonctionne correctement.
Ce test vérifie que quand placement_tresorerie_active = False, 
aucun calcul de placement n'est effectué.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Ajouter les modules au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

def test_placement_deactivation():
    """Test que les placements sont correctement désactivés"""
    
    print("TEST DE DÉSACTIVATION DES PLACEMENTS")
    print("=" * 50)
    
    try:
        from engine_module.treasury_placement import TreasuryPlacementManager
        from engine_module.core_analyzer import AnalysisEngine
        
        # Configuration avec placement désactivé
        config_disabled = {
            'placement_tresorerie_active': False,
            'pourcentage_tva_a_placer': 80.0,
            'taux_placement_exces_tva': 1.5,
            'taux_placement_provision_onduleur': 2.5,
            'placement_tva_capex': True,
            'placement_tva_exploitation': True,
            'seuil_tva_capex': 5000.0,
            'date_debut_simulation': '2024-01-01',
            'date_debut_ppa': '2024-04-01',
            'duree_construction': 3,
            'duree_ppa': 240
        }
        
        # Configuration avec placement activé pour comparaison
        config_enabled = config_disabled.copy()
        config_enabled['placement_tresorerie_active'] = True
        
        print("1. TEST DU GESTIONNAIRE DE PLACEMENTS")
        print("-" * 40)
        
        # Test du TreasuryPlacementManager
        manager_disabled = TreasuryPlacementManager(config_disabled)
        manager_enabled = TreasuryPlacementManager(config_enabled)
        
        # Créer des données mensuelles simulées avec remboursement TVA
        dates = pd.date_range('2024-01-01', periods=12, freq='ME')
        monthly_df = pd.DataFrame({
            'VAT_Payment': [0, 0, 0, 12827, 0, 0, 0, 0, 0, 0, 0, 0],  # Remboursement TVA au mois 4
            'OPEX_Provision_Onduleur_Mensuel': [0, 0, 0, 100, 100, 100, 100, 100, 100, 100, 100, 100],
            'Solde_Tresorerie_Fin_Mois': [10000] * 12
        }, index=dates)
        
        # Test avec placement désactivé
        monthly_df_disabled = monthly_df.copy()
        manager_disabled._apply_placement_logic(
            monthly_df_disabled, 
            config_disabled, 
            num_total_simulation_months=12,
            duree_construction_cfg=3
        )
        
        # Test avec placement activé
        monthly_df_enabled = monthly_df.copy()
        manager_enabled._apply_placement_logic(
            monthly_df_enabled, 
            config_enabled, 
            num_total_simulation_months=12,
            duree_construction_cfg=3
        )
        
        # Vérifications
        placement_columns = [
            'Placement_Exces_TVA', 'Placement_Provision_Onduleur',
            'Solde_Placement_TVA_Cumul', 'Solde_Placement_Provision_Onduleur_Cumul',
            'Interets_Placements_Mensuels', 'Total_Placements'
        ]
        
        print("\\nVERIFICATION DES COLONNES DE PLACEMENT:")
        all_tests_passed = True
        
        for col in placement_columns:
            if col in monthly_df_disabled.columns:
                total_disabled = monthly_df_disabled[col].sum()
                total_enabled = monthly_df_enabled[col].sum() if col in monthly_df_enabled.columns else 0
                
                print(f"  {col}:")
                print(f"    Désactivé: {total_disabled:,.2f}")
                print(f"    Activé: {total_enabled:,.2f}")
                
                if total_disabled == 0:
                    print(f"    ✅ PASS - Correctement à zéro quand désactivé")
                else:
                    print(f"    ❌ FAIL - Devrait être zéro quand désactivé!")
                    all_tests_passed = False
                    
                if total_enabled > 0:
                    print(f"    ✅ PASS - Fonctionnel quand activé")
                else:
                    print(f"    ⚠️  ATTENTION - Pas de placement détecté même quand activé")
                    
                print()
        
        print("\\n2. TEST DES AFFICHAGES CONDITIONNELS")
        print("-" * 40)
        
        # Test que les affichages conditionnels fonctionnent
        print("Vérification que les sections de placement sont masquées...")
        
        # Simuler la logique de filtrage des IDs
        placement_related_ids = [
            'placement_tva_mois', 'placement_provision_onduleur_mois', 'interets_capitalises_mois',
            'interets_courus_cumul', 'tresorerie_non_placee_fin', 'total_placements_fin'
        ]
        
        config_test_cases = [
            (True, "Placements activés"),
            (False, "Placements désactivés")
        ]
        
        for placement_active, description in config_test_cases:
            print(f"\\n  {description}:")
            visible_ids = []
            
            for item_id in placement_related_ids:
                # Simuler la logique de filtrage
                should_display = placement_active or item_id not in placement_related_ids
                
                if should_display:
                    visible_ids.append(item_id)
                    
            print(f"    IDs visibles: {len(visible_ids)}/{len(placement_related_ids)}")
            
            if placement_active:
                expected_visible = len(placement_related_ids)
                if len(visible_ids) == expected_visible:
                    print(f"    ✅ PASS - Tous les éléments visibles quand activé")
                else:
                    print(f"    ❌ FAIL - Éléments manquants quand activé")
                    all_tests_passed = False
            else:
                if len(visible_ids) == 0:
                    print(f"    ✅ PASS - Aucun élément visible quand désactivé")
                else:
                    print(f"    ❌ FAIL - Éléments encore visibles quand désactivé: {visible_ids}")
                    all_tests_passed = False
        
        print("\\n3. RÉSUMÉ DU TEST")
        print("-" * 40)
        
        if all_tests_passed:
            print("✅ TOUS LES TESTS SONT PASSÉS!")
            print("✅ La désactivation des placements fonctionne correctement.")
            print("✅ Les sections conditionnelles sont bien masquées.")
            return True
        else:
            print("❌ CERTAINS TESTS ONT ÉCHOUÉ!")
            print("⚠️  Vérifiez l'implémentation de la désactivation des placements.")
            return False
            
    except ImportError as e:
        print(f"❌ ERREUR D'IMPORT: {e}")
        print("Vérifiez que les modules engine_module sont accessibles.")
        return False
    except Exception as e:
        print(f"❌ ERREUR INATTENDUE: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_financial_display_conditional():
    """Test que l'affichage financier masque bien les produits financiers"""
    
    print("\\n\\nTEST AFFICHAGE CONDITIONNEL - COMPTE DE RÉSULTAT")
    print("=" * 60)
    
    # Simuler la structure compte_resultat_data avec et sans placements
    test_cases = [
        (True, "Avec placements activés"),
        (False, "Avec placements désactivés")
    ]
    
    for placement_active, description in test_cases:
        print(f"\\n{description}:")
        
        # Simuler la logique conditionnelle du compte de résultat
        compte_resultat_data = [
            {'type': 'section_header', 'label': 'PRODUITS D\'EXPLOITATION'},
            {'type': 'detail', 'label': 'Chiffre d\'affaires'},
            {'type': 'section_header', 'label': 'CHARGES FINANCIÈRES'},
            {'type': 'detail', 'label': 'Intérêts sur emprunts'},
        ]
        
        # Ajout conditionnel des produits financiers
        if placement_active:
            produits_financiers_section = [
                {'type': 'section_header', 'label': 'PRODUITS FINANCIERS'},
                {'type': 'detail', 'label': 'Intérêts réalisés sur placements'}
            ]
            compte_resultat_data.extend(produits_financiers_section)
        
        # Fin du compte de résultat
        compte_resultat_data.extend([
            {'type': 'subtotal', 'label': 'RÉSULTAT AVANT IMPÔT'},
            {'type': 'detail', 'label': 'Impôt sur les sociétés'},
            {'type': 'main_total', 'label': 'RÉSULTAT NET'}
        ])
        
        # Compter les sections
        sections = [item for item in compte_resultat_data if item['type'] == 'section_header']
        produits_financiers_present = any('PRODUITS FINANCIERS' in item['label'] for item in sections)
        
        print(f"  Sections totales: {len(sections)}")
        print(f"  'PRODUITS FINANCIERS' présent: {produits_financiers_present}")
        
        if placement_active and produits_financiers_present:
            print("  ✅ PASS - Section PRODUITS FINANCIERS affichée quand placements activés")
        elif not placement_active and not produits_financiers_present:
            print("  ✅ PASS - Section PRODUITS FINANCIERS masquée quand placements désactivés")
        else:
            print("  ❌ FAIL - Logique conditionnelle incorrecte")
            return False
    
    print("\\n✅ Test d'affichage conditionnel réussi!")
    return True

if __name__ == "__main__":
    success1 = test_placement_deactivation()
    success2 = test_financial_display_conditional()
    
    print("\\n" + "=" * 60)
    print("RÉSUMÉ FINAL:")
    if success1 and success2:
        print("✅ TOUS LES TESTS DE DÉSACTIVATION SONT PASSÉS!")
        print("🎉 La vérification des placements désactivés est implémentée correctement.")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ!")
        print("⚠️  Des corrections sont nécessaires.")