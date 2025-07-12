#!/usr/bin/env python3
"""
Test pour vérifier les noms de colonnes utilisés dans le compte de résultat
et identifier pourquoi les valeurs pourraient être nulles
"""

import sys
import os

# Ajouter les modules au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

def test_colonnes_requises():
    """Vérifie les colonnes requises pour le compte de résultat"""
    
    print("TEST DES COLONNES REQUISES POUR LE COMPTE DE RESULTAT")
    print("=" * 60)
    
    # Liste des colonnes utilisées dans annual_summary_display.py
    colonnes_requises = {
        'PRODUITS': [
            'Revenus_Surplus',
            'Revenus_Autoconsommation', 
            'Prime_Autoconso_Encaissee'
        ],
        'CHARGES_VARIABLES': [
            'TURPE',
            'OPEX_Maintenance_Mensuel',
            'OPEX_Assurance_Mensuel',
            'OPEX_Admin_Mensuel',
            'OPEX_Provision_Onduleur_Mensuel'
        ],
        'AUTRES_CHARGES': [
            'Amortissement',
            'Interets_Payes'
        ],
        'PRODUITS_FINANCIERS': [
            'Interets_Debloques_Imposables'
        ],
        'IMPOTS': [
            'Total_IS_Decaisse_Mois'
        ]
    }
    
    print("\nCOLONNES UTILISEES DANS LE CODE:")
    for categorie, colonnes in colonnes_requises.items():
        print(f"\n{categorie}:")
        for col in colonnes:
            print(f"  - {col}")
    
    # Vérifier les variations possibles des noms
    print("\n\nVARIATIONS POSSIBLES DES NOMS DE COLONNES:")
    
    variations_possibles = {
        'Interets_Payes': [
            'Interets_Payes',
            'Interets_Dette',
            'Charges_Interets',
            'Interets_Emprunts'
        ],
        'Interets_Debloques_Imposables': [
            'Interets_Debloques_Imposables',
            'Interets_Placements_Debloques',
            'Produits_Financiers',
            'Interets_Realises'
        ]
    }
    
    for colonne_code, variations in variations_possibles.items():
        print(f"\n{colonne_code}:")
        for var in variations:
            print(f"  - {var}")
    
    # Test de la fonction calculate_annual_total_from_monthly
    print("\n\nTEST DE LA FONCTION calculate_annual_total_from_monthly:")
    
    from table_finance.financial_display_utils import calculate_annual_total_from_monthly
    import pandas as pd
    import numpy as np
    
    # Créer un DataFrame de test avec différents cas
    dates = pd.date_range('2024-01-01', periods=12, freq='ME')
    
    test_cases = {
        'colonne_existante': [100] * 12,  # 1200 total
        'colonne_avec_nan': [100, np.nan, 100, 100, np.nan, 100, 100, 100, np.nan, 100, 100, 100],  # 900 total
        'colonne_vide': [np.nan] * 12,  # 0 total
        'colonne_zeros': [0] * 12  # 0 total
    }
    
    df_test = pd.DataFrame(test_cases, index=dates)
    
    for col_name in test_cases.keys():
        result = calculate_annual_total_from_monthly(df_test, col_name, 2024)
        print(f"\n  {col_name}: {result}")
        
        # Vérifier le type de retour
        if result is None:
            print(f"    -> ATTENTION: Retourne None!")
        elif pd.isna(result):
            print(f"    -> ATTENTION: Retourne NaN!")
        elif result == 0:
            print(f"    -> Retourne 0 (valeur nulle)")
        else:
            print(f"    -> OK: Retourne une valeur numerique")
    
    # Test avec colonne inexistante
    print("\n  colonne_inexistante:")
    try:
        result = calculate_annual_total_from_monthly(df_test, 'colonne_inexistante', 2024)
        print(f"    Resultat: {result}")
        if result is None:
            print(f"    -> ATTENTION: Retourne None pour colonne inexistante!")
    except Exception as e:
        print(f"    -> Exception: {e}")
    
    # Recommandations
    print("\n\nRECOMMANDATIONS:")
    print("1. Verifier que les colonnes 'Interets_Payes' et 'Interets_Debloques_Imposables' existent")
    print("2. S'assurer que calculate_annual_total_from_monthly retourne 0 et non None/NaN")
    print("3. Verifier les logs de debug pour voir les valeurs calculees")
    print("4. Utiliser les variantes de noms si necessaire")

if __name__ == "__main__":
    test_colonnes_requises()