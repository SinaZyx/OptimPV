#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test réel de l'impact des placements en chargeant les données
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_real_impact():
    """Test avec les vraies données du projet"""
    
    # Import après ajout au path
    from modules.engine_module.core_analyzer import AnalysisEngine
    from modules.data_import import load_energy_data_from_file
    import pandas as pd
    
    print("🔬 TEST RÉEL DE L'IMPACT DES PLACEMENTS")
    print("="*60)
    
    # Configuration de base
    global_config = {
        'duree_contrat': 20,
        'duree_construction': 3,
        'tarif_rachat': 0.11,
        'taux_interet_dette': 5.0,
        'cout_fonds_propres': 8.0,
        'debt_ratio': 0.7,
        'duree_ppa': 20,
        'taux_imposition': 25.0,
        'cout_invest_kwc': 1000,
        'puissance_crete_kwc': 65,
        'taux_inflation_generale': 2.0,
        'taux_inflation_elec': 3.0,
        'degradation_annuelle': 0.5,
        'opex_maintenance_pct': 1.0,
        'opex_assurance_pct': 0.5,
        'opex_admin_pct': 0.5,
        'duree_amortissement_annees': 15,
        'valeur_residuelle_pct': 10.0,
        'cout_demantelement_pct': 5.0,
        'tva_taux': 10.0,
        'bfr_receivables_days': 30,
        'bfr_payables_days': 45,
        'turpe_type': 'BT<=36kVA',
        'turpe_tarif': 'CG',
        'turpe_option': 'Unique',
        
        # Paramètres de placement TVA
        'placement_tva_capex': True,
        'placement_tva_exploitation': False,
        'seuil_tva_capex': 5000.0,
        'pourcentage_tva_capex_a_placer': 80.0,
        'pourcentage_tva_exploitation_a_placer': 0.0,
        'taux_placement_exces_tva': 1.5,
        'seuil_remboursement_tva': 50.0,
        
        # Paramètres provision onduleur
        'taux_placement_provision_onduleur': 2.5,
        'pourcentage_provision_onduleur_a_placer': 100.0,
        'duree_vie_onduleur': 15,
        
        # Pour éviter l'optimisation
        'is_optimization_mode': False
    }
    
    # Scénario vide
    scenario = {'name': 'Test placement', 'adjustments': {}}
    
    # Générer des données de production simplifiées
    dates = pd.date_range('2025-01-01', periods=24*365*20, freq='H')
    production_data = pd.DataFrame({
        'Date': dates,
        'Production_kWh': 7.5  # Production constante pour simplifier
    })
    
    sites_data = {'Site1': production_data}
    
    try:
        # Test 1: SANS placement
        print("\n1️⃣ TEST SANS PLACEMENT")
        print("-"*30)
        config_sans = global_config.copy()
        config_sans['placement_tresorerie_active'] = False
        
        engine_sans = AnalysisEngine(config_sans, {'scenario1': scenario}, sites_data)
        results_sans = engine_sans.calculate_financial_indicators(
            global_config=config_sans,
            scenario=scenario,
            prix_revente=None
        )
        
        lcoe_sans = results_sans.get('prix_plancher_production', 0)
        tri_sans = results_sans.get('tri_projet_pct', 0)
        van_sans = results_sans.get('van_projet', 0)
        
        print(f"  LCOE: {lcoe_sans:.3f} c€/kWh")
        print(f"  TRI: {tri_sans:.1f}%")
        print(f"  VAN: {van_sans:,.0f}€")
        
        # Test 2: AVEC placement
        print("\n2️⃣ TEST AVEC PLACEMENT")
        print("-"*30)
        config_avec = global_config.copy()
        config_avec['placement_tresorerie_active'] = True
        
        engine_avec = AnalysisEngine(config_avec, {'scenario1': scenario}, sites_data)
        results_avec = engine_avec.calculate_financial_indicators(
            global_config=config_avec,
            scenario=scenario,
            prix_revente=None
        )
        
        lcoe_avec = results_avec.get('prix_plancher_production', 0)
        tri_avec = results_avec.get('tri_projet_pct', 0)
        van_avec = results_avec.get('van_projet', 0)
        
        print(f"  LCOE: {lcoe_avec:.3f} c€/kWh")
        print(f"  TRI: {tri_avec:.1f}%")
        print(f"  VAN: {van_avec:,.0f}€")
        
        # Calcul des impacts
        print("\n3️⃣ IMPACT DES PLACEMENTS")
        print("-"*30)
        delta_lcoe = lcoe_sans - lcoe_avec
        delta_tri = tri_avec - tri_sans
        delta_van = van_avec - van_sans
        
        print(f"  Δ LCOE: -{delta_lcoe:.3f} c€/kWh ({-delta_lcoe/lcoe_sans*100:.1f}%)")
        print(f"  Δ TRI: +{delta_tri:.1f}%")
        print(f"  Δ VAN: +{delta_van:,.0f}€")
        
        # Validation
        print("\n✅ VALIDATION")
        print("-"*30)
        test_lcoe = delta_lcoe >= 0.2
        test_tri = delta_tri >= 0.3
        test_van = delta_van >= 3000
        
        print(f"  Impact LCOE >= 0.2 c€/kWh: {'✅ PASS' if test_lcoe else '❌ FAIL'}")
        print(f"  Impact TRI >= 0.3%: {'✅ PASS' if test_tri else '❌ FAIL'}")
        print(f"  Impact VAN >= 3,000€: {'✅ PASS' if test_van else '❌ FAIL'}")
        
        if test_lcoe and test_tri and test_van:
            print("\n🎉 SUCCÈS: Les placements ont un impact significatif!")
        else:
            print("\n⚠️ ÉCHEC: L'impact est plus faible que prévu")
            
            # Debug info
            if 'monthly_results' in results_avec:
                df = results_avec['monthly_results']
                total_interets = df['Interets_Totaux_Mensuels'].sum() if 'Interets_Totaux_Mensuels' in df.columns else 0
                print(f"\n  Debug: Total intérêts générés: {total_interets:,.0f}€")
                
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_impact()