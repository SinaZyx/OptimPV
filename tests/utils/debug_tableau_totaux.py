#!/usr/bin/env python3
"""
Script de diagnostic pour vérifier les totaux annuels dans OptimPV.
"""

import pandas as pd
import numpy as np
import sys
import os

# Ajouter le chemin des modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules', 'table_finance'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules', 'engine_module'))

from financial_display_utils import calculate_annual_total_from_monthly

def diagnose_data_columns(monthly_df):
    """Diagnostique les colonnes présentes dans les données"""
    print("🔍 DIAGNOSTIC DES COLONNES DE DONNÉES")
    print("=" * 60)
    
    # Colonnes de placement à vérifier
    placement_columns = [
        'Total_Placements',
        'Tresorerie_Non_Placee', 
        'Solde_Placement_TVA_Cumul',
        'Solde_Placement_Provision_Onduleur_Cumul',
        'Interets_Placements_Mensuels',
        'Placement_Exces_TVA',
        'Placement_Provision_Onduleur'
    ]
    
    print("📊 COLONNES DE PLACEMENT:")
    for col in placement_columns:
        if col in monthly_df.columns:
            non_zero_count = (monthly_df[col] != 0).sum()
            max_val = monthly_df[col].max()
            min_val = monthly_df[col].min()
            print(f"  ✅ {col}: {non_zero_count} valeurs non-nulles, Max={max_val:.2f}, Min={min_val:.2f}")
        else:
            print(f"  ❌ {col}: COLONNE MANQUANTE")
    
    # Vérifier les années disponibles
    if isinstance(monthly_df.index, pd.DatetimeIndex):
        available_years = sorted(monthly_df.index.year.unique())
        print(f"\n📅 ANNÉES DISPONIBLES: {available_years}")
        
        # Calculer les totaux pour la première année
        if available_years:
            year = available_years[0]
            print(f"\n📈 TOTAUX POUR L'ANNÉE {year}:")
            
            for col in placement_columns:
                if col in monthly_df.columns:
                    total = calculate_annual_total_from_monthly(monthly_df, col, year)
                    print(f"  {col}: {total:,.2f}€")

def diagnose_placement_activation(config_dict):
    """Vérifie si le placement TVA est activé"""
    print("\n🔧 DIAGNOSTIC ACTIVATION PLACEMENT TVA")
    print("=" * 60)
    
    placement_active = config_dict.get("placement_tresorerie_active", False)
    print(f"📌 Placement TVA activé: {placement_active}")
    
    if placement_active:
        pct_tva = config_dict.get("pourcentage_tva_a_placer", 0)
        taux_tva = config_dict.get("taux_placement_exces_tva", 0)
        taux_provision = config_dict.get("taux_placement_provision_onduleur", 0)
        
        print(f"   📊 % TVA à placer: {pct_tva}%")
        print(f"   💰 Taux placement TVA: {taux_tva}%")
        print(f"   🔧 Taux placement provision: {taux_provision}%")
    else:
        print("   ⚠️  Le placement TVA est DÉSACTIVÉ - Les colonnes de placement seront vides")

def run_full_diagnosis():
    """Lance un diagnostic complet"""
    print("🧪 DIAGNOSTIC COMPLET - TOTAUX ANNUELS OPTIMV")
    print("=" * 80)
    
    try:
        # Essayer de charger des données de test ou réelles
        print("🔍 Recherche de données de simulation récentes...")
        
        # Vous pouvez adapter ces chemins selon votre structure
        possible_data_paths = [
            "temp_results.pkl",
            "data/last_simulation.pkl", 
            "exports/recent_data.csv"
        ]
        
        data_found = False
        for path in possible_data_paths:
            if os.path.exists(path):
                print(f"📁 Données trouvées: {path}")
                
                try:
                    if path.endswith('.pkl'):
                        import pickle
                        with open(path, 'rb') as f:
                            results = pickle.load(f)
                        monthly_df = results.get('monthly_data')
                    elif path.endswith('.csv'):
                        monthly_df = pd.read_csv(path, index_col=0, parse_dates=True)
                    
                    if monthly_df is not None:
                        diagnose_data_columns(monthly_df)
                        data_found = True
                        break
                        
                except Exception as e:
                    print(f"   ❌ Erreur lecture {path}: {e}")
        
        if not data_found:
            print("⚠️  Aucun fichier de données trouvé.")
            print("💡 Lancez d'abord une simulation dans OptimPV pour générer des données.")
            
            # Créer des données de test
            print("\n🧪 Création de données de test pour vérification...")
            test_dates = pd.date_range('2024-01-01', periods=12, freq='M')
            test_df = pd.DataFrame({
                'Total_Placements': [0, 0, 0, 100, 200, 300, 400, 500, 600, 700, 800, 900],
                'Tresorerie_Non_Placee': [1000] * 12,
                'Interets_Placements_Mensuels': [10] * 12,
            }, index=test_dates)
            
            diagnose_data_columns(test_df)
        
    except Exception as e:
        print(f"❌ ERREUR PENDANT LE DIAGNOSTIC: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_full_diagnosis() 