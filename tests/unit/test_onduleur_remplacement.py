#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests pour vérifier le bon fonctionnement du remplacement d'onduleur
avec et sans placements de trésorerie.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Ajouter le chemin parent pour importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.engine_module.core_analyzer import CoreFinancialEngine
from modules.engine_module.equity_calculations import EquityCalculations


def create_test_config(placement_actif=True):
    """Créer une configuration de test pour le remplacement onduleur"""
    config = {
        # Configuration générale
        'capex_scenario': 50000,
        'puissance_kwc': 50,
        'date_debut_simulation': '2024-01-01',
        'duree_construction': 0,
        'duree_ppa': 240,  # 20 ans
        
        # Configuration onduleur
        'opex_onduleur_provision_globale': True,
        'opex_onduleur_total_cost_global': 10190,
        'opex_onduleur_lifetime_global': 10,  # Remplacement après 10 ans
        
        # Configuration placement
        'placement_tresorerie_active': placement_actif,
        'taux_placement_provision_onduleur': 2.5,
        
        # Autres paramètres
        'inflation_rate': 2.0,
        'debt_ratio': 0.0,  # Pas de dette pour simplifier
        'taux_actualisation': 6.0,
        
        # Production
        'production_annuelle_kwh': 50000,
        'prix_elec_moyen': 0.15,  # 15 c€/kWh
        
        # OPEX
        'opex_maintenance': 500,
        'opex_assurance': 300,
        'opex_admin': 200,
        'turpe_annual': 1000,
    }
    
    # Configuration sites (simple)
    sites_config = {
        'site_1': {
            'site_type': 'Producteur',
            'puissance_kwc': 50,
            'production_annuelle_kwh': 50000,
        }
    }
    
    return config, sites_config


def run_test_scenario(placement_actif):
    """Exécuter un scénario de test avec ou sans placement"""
    print(f"\n{'='*60}")
    print(f"TEST SCÉNARIO: Placements {'ACTIVÉS' if placement_actif else 'DÉSACTIVÉS'}")
    print(f"{'='*60}")
    
    # Créer la configuration
    global_config, sites_config = create_test_config(placement_actif)
    
    # Créer l'instance du moteur
    engine = CoreFinancialEngine()
    
    # Exécuter l'analyse
    try:
        results = engine.calculate_financial_analysis(
            global_config=global_config,
            sites_config=sites_config,
            scenario_name=f"Test_Onduleur_Placement_{'ON' if placement_actif else 'OFF'}"
        )
        
        # Récupérer les données mensuelles
        monthly_df = results.get('monthly_data')
        if monthly_df is None or monthly_df.empty:
            print("❌ ERREUR: Pas de données mensuelles générées")
            return None
            
        # Trouver le mois de remplacement (mois 120 = année 10)
        mois_remplacement = 10 * 12  # 120 mois
        
        if len(monthly_df) > mois_remplacement:
            row_remplacement = monthly_df.iloc[mois_remplacement]
            
            # Extraire les valeurs clés
            capital_provisions = 10190  # Montant provisionné
            taux_annuel = 2.5 / 100
            duree_ans = 10
            
            # Calcul théorique des intérêts composés
            interets_theoriques = capital_provisions * ((1 + taux_annuel) ** duree_ans - 1) if placement_actif else 0
            
            # Inflation sur 10 ans
            inflation_10_ans = (1 + 0.02) ** 10
            cout_onduleur_indexe = capital_provisions * inflation_10_ans
            
            # Valeurs du DataFrame
            fonds_libere = row_remplacement.get('Fonds_Reserve_Onduleur_Liberation', 0)
            onduleur_paye = row_remplacement.get('Remplacement_Onduleur_Paye', 0)
            deficit_enregistre = row_remplacement.get('Deficit_Financement_Onduleur', 0)
            
            # Calcul du déficit théorique
            deficit_theorique = cout_onduleur_indexe - (capital_provisions + interets_theoriques)
            
            print(f"\n📊 RÉSULTATS AU MOIS {mois_remplacement + 1} (Année 11):")
            print(f"  - Capital provisionné: {capital_provisions:,.0f}€")
            print(f"  - Intérêts théoriques: {interets_theoriques:,.0f}€")
            print(f"  - Fonds total libéré: {fonds_libere:,.0f}€")
            print(f"  - Coût onduleur indexé: {cout_onduleur_indexe:,.0f}€")
            print(f"  - Montant payé: {-onduleur_paye:,.0f}€")
            print(f"  - Déficit enregistré: {deficit_enregistre:,.0f}€")
            print(f"  - Déficit théorique: {deficit_theorique:,.0f}€")
            
            # Vérifications
            print(f"\n🧪 VÉRIFICATIONS:")
            
            # Test 1: Fonds libéré
            fonds_attendu = capital_provisions + interets_theoriques
            test1_ok = abs(fonds_libere - fonds_attendu) < 100  # Tolérance 100€
            print(f"  1. Fonds libéré correct: {'✅ PASS' if test1_ok else '❌ FAIL'}")
            if not test1_ok:
                print(f"     Attendu: {fonds_attendu:,.0f}€, Obtenu: {fonds_libere:,.0f}€")
            
            # Test 2: Paiement onduleur
            test2_ok = abs(-onduleur_paye - cout_onduleur_indexe) < 100
            print(f"  2. Paiement onduleur correct: {'✅ PASS' if test2_ok else '❌ FAIL'}")
            if not test2_ok:
                print(f"     Attendu: {cout_onduleur_indexe:,.0f}€, Obtenu: {-onduleur_paye:,.0f}€")
            
            # Test 3: Déficit
            test3_ok = abs(deficit_enregistre - deficit_theorique) < 100
            print(f"  3. Déficit correct: {'✅ PASS' if test3_ok else '❌ FAIL'}")
            if not test3_ok:
                print(f"     Attendu: {deficit_theorique:,.0f}€, Obtenu: {deficit_enregistre:,.0f}€")
            
            # Test 4: Impact sur FCFE
            fcfe_mois = row_remplacement.get('FCFE', 0)
            print(f"\n  4. Impact sur FCFE:")
            print(f"     FCFE du mois: {fcfe_mois:,.0f}€")
            print(f"     Devrait inclure: +{fonds_libere:,.0f}€ (libération) et {onduleur_paye:,.0f}€ (paiement)")
            
            # Récupérer le LCOE
            lcoe = results.get('lcoe_cents', 0)
            print(f"\n📈 LCOE calculé: {lcoe:.3f} c€/kWh")
            
            return {
                'placement_actif': placement_actif,
                'fonds_libere': fonds_libere,
                'onduleur_paye': -onduleur_paye,
                'deficit': deficit_enregistre,
                'lcoe': lcoe,
                'tests_passed': test1_ok and test2_ok and test3_ok
            }
        else:
            print("❌ ERREUR: Pas assez de mois simulés pour atteindre le remplacement")
            return None
            
    except Exception as e:
        print(f"❌ ERREUR lors de l'exécution: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Fonction principale pour exécuter les tests"""
    print("🚀 DÉBUT DES TESTS - REMPLACEMENT ONDULEUR")
    print("="*60)
    
    # Test 1: Avec placements activés
    results_avec = run_test_scenario(placement_actif=True)
    
    # Test 2: Sans placements
    results_sans = run_test_scenario(placement_actif=False)
    
    # Comparaison finale
    print(f"\n{'='*60}")
    print("📊 COMPARAISON FINALE")
    print(f"{'='*60}")
    
    if results_avec and results_sans:
        print(f"\n📈 Impact des placements:")
        print(f"  - Intérêts générés: {results_avec['fonds_libere'] - results_sans['fonds_libere']:,.0f}€")
        print(f"  - Réduction du déficit: {results_sans['deficit'] - results_avec['deficit']:,.0f}€")
        print(f"  - LCOE avec placements: {results_avec['lcoe']:.3f} c€/kWh")
        print(f"  - LCOE sans placements: {results_sans['lcoe']:.3f} c€/kWh")
        print(f"  - Différence LCOE: {results_sans['lcoe'] - results_avec['lcoe']:+.3f} c€/kWh")
        
        # Vérification logique finale
        print(f"\n🎯 VÉRIFICATION LOGIQUE:")
        if results_sans['lcoe'] > results_avec['lcoe']:
            print("  ✅ CORRECT: Le LCOE est plus élevé sans placements (déficit plus important)")
        else:
            print("  ❌ PROBLÈME: Le LCOE devrait être plus élevé sans placements!")
            
        if results_avec['tests_passed'] and results_sans['tests_passed']:
            print("\n✅ TOUS LES TESTS SONT PASSÉS!")
        else:
            print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ")
    else:
        print("❌ Impossible de comparer - un des scénarios a échoué")


if __name__ == "__main__":
    main()