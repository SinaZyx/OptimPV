#!/usr/bin/env python3
"""
Test final pour vérifier que le résultat avant impôt et le résultat net
s'affichent correctement après les corrections
"""

import sys
import os
import pandas as pd
import numpy as np

# Ajouter les modules au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from table_finance.financial_display_utils import calculate_annual_total_from_monthly

def test_calcul_avec_colonnes_manquantes():
    """Test le calcul du compte de résultat avec des colonnes manquantes"""
    
    print("TEST FINAL - CALCUL COMPTE DE RESULTAT AVEC COLONNES MANQUANTES")
    print("=" * 70)
    
    # Créer un DataFrame avec certaines colonnes manquantes
    dates = pd.date_range('2024-01-01', periods=12, freq='ME')
    
    # Données partielles - certaines colonnes sont volontairement omises
    monthly_data = pd.DataFrame({
        'Revenus_Surplus': [500] * 12,
        'Revenus_Autoconsommation': [100] * 12,
        'Prime_Autoconso_Encaissee': [0, 0, 0, 1000, 0, 0, 0, 0, 0, 0, 0, 0],
        'TURPE': [50] * 12,
        'OPEX_Maintenance_Mensuel': [80] * 12,
        'OPEX_Assurance_Mensuel': [30] * 12,
        'OPEX_Admin_Mensuel': [20] * 12,
        'OPEX_Provision_Onduleur_Mensuel': [10] * 12,
        'Amortissement': [50] * 12,
        # 'Interets_Payes' est MANQUANT
        # 'Interets_Debloques_Imposables' est MANQUANT
        'Total_IS_Decaisse_Mois': [0] * 12
    }, index=dates)
    
    year = 2024
    
    print("\nCOLONNES PRESENTES DANS LES DONNEES:")
    for col in monthly_data.columns:
        print(f"  - {col}")
    
    print("\nCOLONNES MANQUANTES:")
    print("  - Interets_Payes")
    print("  - Interets_Debloques_Imposables")
    
    print("\n" + "-" * 70)
    print("CALCUL DES TOTAUX ANNUELS:")
    
    # Calculer toutes les composantes
    val_vente_surplus_an = calculate_annual_total_from_monthly(monthly_data, 'Revenus_Surplus', year)
    val_valorisation_autoconso_an = calculate_annual_total_from_monthly(monthly_data, 'Revenus_Autoconsommation', year)
    val_prime_autoconso_an = calculate_annual_total_from_monthly(monthly_data, 'Prime_Autoconso_Encaissee', year)
    
    val_turpe_an = calculate_annual_total_from_monthly(monthly_data, 'TURPE', year)
    val_maintenance_an = calculate_annual_total_from_monthly(monthly_data, 'OPEX_Maintenance_Mensuel', year)
    val_assurance_an = calculate_annual_total_from_monthly(monthly_data, 'OPEX_Assurance_Mensuel', year)
    val_admin_an = calculate_annual_total_from_monthly(monthly_data, 'OPEX_Admin_Mensuel', year)
    val_provision_onduleur_an = calculate_annual_total_from_monthly(monthly_data, 'OPEX_Provision_Onduleur_Mensuel', year)
    
    val_amort_an = calculate_annual_total_from_monthly(monthly_data, 'Amortissement', year)
    
    # Colonnes manquantes
    val_interets_an = calculate_annual_total_from_monthly(monthly_data, 'Interets_Payes', year)
    val_interets_debloques_an = calculate_annual_total_from_monthly(monthly_data, 'Interets_Debloques_Imposables', year)
    
    val_total_is_decaisse_an = calculate_annual_total_from_monthly(monthly_data, 'Total_IS_Decaisse_Mois', year)
    
    # Afficher les valeurs récupérées
    print(f"\nInterets_Payes (colonne manquante): {val_interets_an}")
    print(f"  Type: {type(val_interets_an)}, Is NaN: {pd.isna(val_interets_an)}")
    
    print(f"\nInterets_Debloques_Imposables (colonne manquante): {val_interets_debloques_an}")
    print(f"  Type: {type(val_interets_debloques_an)}, Is NaN: {pd.isna(val_interets_debloques_an)}")
    
    # Calculer avec le code corrigé
    print("\n" + "-" * 70)
    print("CALCUL DU COMPTE DE RESULTAT (CODE CORRIGE):")
    
    # Calculs avec gestion des None/NaN
    ca_total = (val_vente_surplus_an or 0) + (val_valorisation_autoconso_an or 0)
    total_produits_exploitation = ca_total + (val_prime_autoconso_an or 0)
    
    # S'assurer que toutes les valeurs sont numériques
    total_charges_variables = float(val_turpe_an or 0) + float(val_maintenance_an or 0) + float(val_assurance_an or 0) + float(val_admin_an or 0) + float(val_provision_onduleur_an or 0)
    marge_couts_variables = total_produits_exploitation - total_charges_variables
    resultat_exploitation = marge_couts_variables - float(val_amort_an or 0)
    
    # IMPORTANT: Gestion des valeurs manquantes
    charges_financieres = float(val_interets_an or 0)
    produits_financiers = float(val_interets_debloques_an or 0)
    
    # Calcul explicite
    resultat_avant_impot = resultat_exploitation - charges_financieres + produits_financiers
    
    # Calcul du résultat net
    impot_societes = float(val_total_is_decaisse_an or 0)
    resultat_net_final = resultat_avant_impot - impot_societes
    
    print(f"\nResultat d'exploitation: {resultat_exploitation:.0f} EUR")
    print(f"Charges financieres: {charges_financieres:.0f} EUR")
    print(f"Produits financiers: {produits_financiers:.0f} EUR")
    print(f"RESULTAT AVANT IMPOT: {resultat_avant_impot:.0f} EUR")
    print(f"Impot societes: {impot_societes:.0f} EUR")
    print(f"RESULTAT NET: {resultat_net_final:.0f} EUR")
    
    # Vérifications
    print("\n" + "-" * 70)
    print("VERIFICATIONS:")
    
    if pd.isna(resultat_avant_impot):
        print("[ERREUR] Le resultat avant impot est NaN!")
    elif resultat_avant_impot == 0:
        print("[ATTENTION] Le resultat avant impot est 0")
    else:
        print("[OK] Le resultat avant impot est calcule correctement")
    
    if pd.isna(resultat_net_final):
        print("[ERREUR] Le resultat net est NaN!")
    elif resultat_net_final == 0:
        print("[ATTENTION] Le resultat net est 0")
    else:
        print("[OK] Le resultat net est calcule correctement")
    
    # Test de la structure pour l'affichage
    print("\n" + "-" * 70)
    print("TEST STRUCTURE AFFICHAGE:")
    
    def format_percentage(value, total_ref):
        """Formate un pourcentage par rapport au total de référence"""
        if value is None or pd.isna(value):
            return "-"
        if total_ref is None or pd.isna(total_ref) or total_ref == 0:
            return "-"
        pct = (float(value) / float(total_ref)) * 100
        return f"{pct:.0f} %" if abs(pct - round(pct)) < 0.1 else f"{pct:.1f} %"
    
    resultat_data = {
        'type': 'subtotal',
        'label': 'RESULTAT AVANT IMPOT',
        'value': resultat_avant_impot,
        'percentage': format_percentage(resultat_avant_impot, total_produits_exploitation),
        'indent': 0
    }
    
    print(f"Structure pour affichage HTML:")
    print(f"  label: {resultat_data['label']}")
    print(f"  value: {resultat_data['value']} (type: {type(resultat_data['value'])})")
    print(f"  percentage: {resultat_data['percentage']}")
    
    if resultat_data['value'] is not None and not pd.isna(resultat_data['value']):
        print("\n[OK] Les valeurs devraient s'afficher correctement dans le compte de resultat")
    else:
        print("\n[ERREUR] Les valeurs ne s'afficheront pas dans le compte de resultat")

if __name__ == "__main__":
    test_calcul_avec_colonnes_manquantes()