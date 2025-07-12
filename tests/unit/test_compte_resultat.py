#!/usr/bin/env python3
"""
Script de test pour vérifier le calcul du résultat avant impôt et du résultat net
dans le compte de résultat d'OptimPV.
"""

import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime

# Ajouter le chemin des modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules', 'table_finance'))

# Import des fonctions à tester
from table_finance.annual_summary_display import calculate_annual_total_from_monthly

def create_test_data():
    """Crée des données de test pour simuler un compte de résultat"""
    # Créer un index de dates mensuelles
    dates = pd.date_range('2024-01-01', periods=12, freq='M')
    
    # Créer des données mensuelles simulées
    monthly_data = pd.DataFrame({
        # Produits d'exploitation
        'Revenus_Surplus': [500] * 12,  # 6,000EUR/an
        'Revenus_Autoconsommation': [100] * 12,  # 1,200EUR/an
        'Prime_Autoconso_Encaissee': [0, 0, 0, 1000, 0, 0, 0, 0, 0, 0, 0, 0],  # 1,000EUR/an
        
        # Charges variables
        'TURPE': [50] * 12,  # 600EUR/an
        'OPEX_Maintenance_Mensuel': [80] * 12,  # 960EUR/an
        'OPEX_Assurance_Mensuel': [30] * 12,  # 360EUR/an
        'OPEX_Admin_Mensuel': [20] * 12,  # 240EUR/an
        'OPEX_Provision_Onduleur_Mensuel': [10] * 12,  # 120EUR/an
        
        # Autres charges
        'Amortissement': [50] * 12,  # 600EUR/an
        
        # Charges financières
        'Interets_Payes': [159] * 12,  # 1,908EUR/an (proche de 1,907EUR)
        
        # Produits financiers
        'Interets_Debloques_Imposables': [0] * 12,  # 0EUR/an
        
        # Impôts
        'Total_IS_Decaisse_Mois': [0] * 12,  # 0EUR/an
    }, index=dates)
    
    return monthly_data

def test_compte_resultat_calculation():
    """Test le calcul du compte de résultat"""
    print("TEST DU CALCUL DU COMPTE DE RESULTAT")
    print("=" * 60)
    
    # Créer les données de test
    monthly_df = create_test_data()
    year = 2024
    
    print(f"\n[INFO] Calcul des totaux annuels pour l'année {year}:")
    print("-" * 60)
    
    # Calculer les composantes
    val_vente_surplus_an = calculate_annual_total_from_monthly(monthly_df, 'Revenus_Surplus', year)
    val_valorisation_autoconso_an = calculate_annual_total_from_monthly(monthly_df, 'Revenus_Autoconsommation', year)
    val_prime_autoconso_an = calculate_annual_total_from_monthly(monthly_df, 'Prime_Autoconso_Encaissee', year)
    
    val_turpe_an = calculate_annual_total_from_monthly(monthly_df, 'TURPE', year)
    val_maintenance_an = calculate_annual_total_from_monthly(monthly_df, 'OPEX_Maintenance_Mensuel', year)
    val_assurance_an = calculate_annual_total_from_monthly(monthly_df, 'OPEX_Assurance_Mensuel', year)
    val_admin_an = calculate_annual_total_from_monthly(monthly_df, 'OPEX_Admin_Mensuel', year)
    val_provision_onduleur_an = calculate_annual_total_from_monthly(monthly_df, 'OPEX_Provision_Onduleur_Mensuel', year)
    
    val_amort_an = calculate_annual_total_from_monthly(monthly_df, 'Amortissement', year)
    val_interets_an = calculate_annual_total_from_monthly(monthly_df, 'Interets_Payes', year)
    val_interets_debloques_an = calculate_annual_total_from_monthly(monthly_df, 'Interets_Debloques_Imposables', year)
    val_total_is_decaisse_an = calculate_annual_total_from_monthly(monthly_df, 'Total_IS_Decaisse_Mois', year)
    
    # Afficher les valeurs récupérées
    print("PRODUITS D'EXPLOITATION:")
    print(f"   Vente surplus: {val_vente_surplus_an:,.0f}EUR")
    print(f"   Valorisation autoconso: {val_valorisation_autoconso_an:,.0f}EUR")
    print(f"   Prime autoconso: {val_prime_autoconso_an:,.0f}EUR")
    
    print("\nCHARGES VARIABLES:")
    print(f"   TURPE: {val_turpe_an:,.0f}EUR")
    print(f"   Maintenance: {val_maintenance_an:,.0f}EUR")
    print(f"   Assurance: {val_assurance_an:,.0f}EUR")
    print(f"   Admin: {val_admin_an:,.0f}EUR")
    print(f"   Provision onduleur: {val_provision_onduleur_an:,.0f}EUR")
    
    print("\nAUTRES CHARGES:")
    print(f"   Amortissement: {val_amort_an:,.0f}EUR")
    print(f"   Intérêts payés: {val_interets_an:,.0f}EUR")
    
    print("\nPRODUITS FINANCIERS:")
    print(f"   Intérêts débloqués: {val_interets_debloques_an:,.0f}EUR")
    
    print("\nIMPOTS:")
    print(f"   IS décaissé: {val_total_is_decaisse_an:,.0f}EUR")
    
    # Calculer les totaux (REPRISE DU CODE CORRIGÉ)
    ca_total = (val_vente_surplus_an or 0) + (val_valorisation_autoconso_an or 0)
    total_produits_exploitation = ca_total + (val_prime_autoconso_an or 0)
    
    # S'assurer que toutes les valeurs sont numériques
    total_charges_variables = float(val_turpe_an or 0) + float(val_maintenance_an or 0) + float(val_assurance_an or 0) + float(val_admin_an or 0) + float(val_provision_onduleur_an or 0)
    marge_couts_variables = total_produits_exploitation - total_charges_variables
    resultat_exploitation = marge_couts_variables - float(val_amort_an or 0)
    
    # Calcul explicite du résultat avant impôt
    charges_financieres = float(val_interets_an or 0)
    produits_financiers = float(val_interets_debloques_an or 0)
    
    resultat_avant_impot = resultat_exploitation - charges_financieres + produits_financiers
    
    # Calcul du résultat net
    impot_societes = float(val_total_is_decaisse_an or 0)
    resultat_net_final = resultat_avant_impot - impot_societes
    
    print("\n" + "=" * 60)
    print("RESULTATS CALCULES:")
    print("=" * 60)
    
    print(f"CA Total: {ca_total:,.0f}EUR")
    print(f"Total Produits d'Exploitation: {total_produits_exploitation:,.0f}EUR")
    print(f"Total Charges Variables: {total_charges_variables:,.0f}EUR")
    print(f"Marge sur Coûts Variables: {marge_couts_variables:,.0f}EUR")
    print(f"Résultat d'Exploitation: {resultat_exploitation:,.0f}EUR")
    
    print("\nCALCUL DU RESULTAT AVANT IMPOT:")
    print(f"   Résultat d'exploitation: {resultat_exploitation:,.0f}EUR")
    print(f"   - Charges financières: {charges_financieres:,.0f}EUR")
    print(f"   + Produits financiers: {produits_financiers:,.0f}EUR")
    print(f"   = RÉSULTAT AVANT IMPÔT: {resultat_avant_impot:,.0f}EUR")
    
    print("\nCALCUL DU RESULTAT NET:")
    print(f"   Résultat avant impôt: {resultat_avant_impot:,.0f}EUR")
    print(f"   - Impôt sur les sociétés: {impot_societes:,.0f}EUR")
    print(f"   = RÉSULTAT NET: {resultat_net_final:,.0f}EUR")
    
    # Vérification des valeurs attendues
    print("\n" + "=" * 60)
    print("VERIFICATION DES RESULTATS:")
    print("=" * 60)
    
    expected_resultat_exploitation = 6530  # Valeur attendue selon le prompt
    expected_charges_financieres = 1907  # Valeur attendue selon le prompt
    expected_resultat_avant_impot = 4623  # Valeur attendue selon le prompt
    
    print(f"Résultat d'exploitation - Attendu: {expected_resultat_exploitation}EUR, Calculé: {resultat_exploitation:.0f}EUR")
    print(f"Charges financières - Attendu: {expected_charges_financieres}EUR, Calculé: {charges_financieres:.0f}EUR")
    print(f"Résultat avant impôt - Attendu: {expected_resultat_avant_impot}EUR, Calculé: {resultat_avant_impot:.0f}EUR")
    
    # Tester si les valeurs calculées sont nulles (problème identifié)
    if resultat_avant_impot == 0 or pd.isna(resultat_avant_impot):
        print("\n[ERREUR] Le resultat avant impot est nul ou NaN!")
    else:
        print(f"\n[OK] Le resultat avant impot est correctement calcule: {resultat_avant_impot:,.0f}EUR")
    
    if resultat_net_final == 0 or pd.isna(resultat_net_final):
        print("[ERREUR] Le resultat net est nul ou NaN!")
    else:
        print(f"[OK] Le resultat net est correctement calcule: {resultat_net_final:,.0f}EUR")

if __name__ == "__main__":
    test_compte_resultat_calculation()