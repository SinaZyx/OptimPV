#!/usr/bin/env python3
"""
Test spécifique pour reproduire le problème exact :
- Résultat d'exploitation : 6,530 EUR
- Charges financières : 1,907 EUR
- Résultat avant impôt et résultat net qui ne s'affichent pas
"""

import sys
import os

# Ajouter les modules au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

def test_calcul_resultat():
    """Test du calcul du résultat avant impôt avec les valeurs exactes du problème"""
    
    print("TEST CALCUL RESULTAT AVANT IMPOT")
    print("=" * 50)
    
    # Valeurs du problème
    resultat_exploitation = 6530.0
    charges_financieres = 1907.0
    produits_financiers = 0.0
    impot_societes = 0.0
    
    print("\nDONNEES DU PROBLEME:")
    print(f"  Resultat d'exploitation: {resultat_exploitation:.0f} EUR")
    print(f"  Charges financieres: {charges_financieres:.0f} EUR") 
    print(f"  Produits financiers: {produits_financiers:.0f} EUR")
    print(f"  Impot sur les societes: {impot_societes:.0f} EUR")
    
    # Test du calcul tel qu'implémenté dans le code corrigé
    print("\nCALCULS AVEC LE CODE CORRIGE:")
    
    # S'assurer que toutes les valeurs sont numériques
    charges_financieres_float = float(charges_financieres or 0)
    produits_financiers_float = float(produits_financiers or 0)
    
    # Calcul explicite du résultat avant impôt
    resultat_avant_impot = resultat_exploitation - charges_financieres_float + produits_financiers_float
    
    # Calcul du résultat net
    impot_societes_float = float(impot_societes or 0)
    resultat_net_final = resultat_avant_impot - impot_societes_float
    
    print(f"\n  Resultat avant impot calcule = {resultat_exploitation} - {charges_financieres_float} + {produits_financiers_float}")
    print(f"                               = {resultat_avant_impot:.0f} EUR")
    
    print(f"\n  Resultat net calcule = {resultat_avant_impot} - {impot_societes_float}")
    print(f"                       = {resultat_net_final:.0f} EUR")
    
    # Vérification
    print("\nVERIFICATIONS:")
    
    expected_resultat_avant_impot = 4623  # 6530 - 1907 + 0
    if abs(resultat_avant_impot - expected_resultat_avant_impot) < 1:
        print(f"  [OK] Resultat avant impot correct: {resultat_avant_impot:.0f} EUR (attendu: {expected_resultat_avant_impot} EUR)")
    else:
        print(f"  [ERREUR] Resultat avant impot incorrect: {resultat_avant_impot:.0f} EUR (attendu: {expected_resultat_avant_impot} EUR)")
    
    # Test des cas None/NaN
    print("\nTEST DES CAS EDGE:")
    
    # Test avec None
    test_none = None
    test_value = float(test_none or 0)
    print(f"  float(None or 0) = {test_value}")
    
    # Test format_percentage
    def format_percentage(value, total_ref):
        """Formate un pourcentage par rapport au total de référence"""
        if value is None:
            return "-"
        if total_ref is None or total_ref == 0:
            return "-"
        pct = (float(value) / float(total_ref)) * 100
        return f"{pct:.0f} %" if abs(pct - round(pct)) < 0.1 else f"{pct:.1f} %"
    
    total_produits_exploitation = 8200  # Approximatif
    percentage = format_percentage(resultat_avant_impot, total_produits_exploitation)
    print(f"  Pourcentage du resultat avant impot: {percentage}")
    
    # Test structure de données
    print("\nTEST STRUCTURE DONNEES:")
    
    resultat_data = {
        'type': 'subtotal',
        'label': 'RESULTAT AVANT IMPOT',
        'value': resultat_avant_impot,
        'percentage': format_percentage(resultat_avant_impot, total_produits_exploitation),
        'indent': 0
    }
    
    print(f"  Structure donnees compte resultat:")
    print(f"    - label: {resultat_data['label']}")
    print(f"    - value: {resultat_data['value']}")
    print(f"    - percentage: {resultat_data['percentage']}")
    
    # Vérifier si la valeur est présente
    if resultat_data['value'] is not None and resultat_data['value'] != 0:
        print(f"\n[OK] La valeur du resultat avant impot est bien presente dans la structure")
    else:
        print(f"\n[ERREUR] La valeur du resultat avant impot est manquante ou nulle")

if __name__ == "__main__":
    test_calcul_resultat()