#!/usr/bin/env python3
"""
Test complet du placement TVA avec logging étendu incluant les valeurs affichées dans les tableaux
"""

import os
import sys
from datetime import datetime

# Ajouter le chemin pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules', 'engine_module'))

# Créer une version simplifiée des fonctions de logging pour le test
def log_tva_placement(message, data=None):
    """Version simplifiée de la fonction de logging"""
    try:
        log_file_path = os.path.join(os.path.dirname(__file__), '..', 'log.txt')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] TVA_PLACEMENT: {message}"
        
        if data is not None:
            if isinstance(data, dict):
                for key, value in data.items():
                    log_entry += f"\n  {key}: {value}"
            else:
                log_entry += f"\n  Data: {data}"
        
        log_entry += "\n" + "="*80 + "\n"
        
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(message)
        if data:
            print(f"  Data: {data}")
            
    except Exception as e:
        print(f"Erreur logging TVA: {e}")

def clear_tva_log():
    """Vide le fichier de log au début"""
    try:
        log_file_path = os.path.join(os.path.dirname(__file__), '..', 'log.txt')
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.write(f"=== NOUVEAU LOG TVA PLACEMENT AVEC TABLEAUX - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
    except Exception as e:
        print(f"Erreur initialisation log: {e}")

def simulate_complete_tva_flow():
    """Simule le flux complet avec calculs et affichage"""
    
    print("🧪 SIMULATION COMPLÈTE TVA - CALCUL + AFFICHAGE")
    print("=" * 50)
    
    # Initialiser le log
    clear_tva_log()
    
    # 1. SIMULATION DES CALCULS (comme avant)
    log_tva_placement("=== PHASE 1: CALCULS MOTEUR ===")
    
    # Paramètres
    log_tva_placement("DÉBUT ANALYSE PLACEMENT TVA", {
        "taux_provision_annual": "2.50%",
        "taux_tva_annual": "1.50%", 
        "pct_tva_a_placer": "80.0%",
        "duree_construction": 3,
        "nombre_mois_total": 24
    })
    
    # Mois 6 avec remboursement TVA
    mois = 6
    log_tva_placement(f"MOIS {mois} - ANALYSE COLONNES TVA", {
        "VAT_Collectee": "2,173.00€",
        "VAT_Deductible_CAPEX": "15,000.00€",
        "VAT_Due_Mois": "-12,827.00€",
        "VAT_Payment": "-12,827.00€"
    })
    
    log_tva_placement(f"MOIS {mois} - REMBOURSEMENT TVA DÉTECTÉ (Option 1)", {
        "Méthode": "Crédit TVA (VAT_Due_Mois négatif)",
        "Montant_remboursement": "12,827.00€"
    })
    
    montant_a_placer = 12827.0 * 0.80
    log_tva_placement(f"MOIS {mois} - PLACEMENT TVA EFFECTUÉ", {
        "Montant_à_placer": f"{montant_a_placer:,.2f}€",
        "Solde_placement_TVA_avant": "0.00€",
        "Solde_placement_TVA_après": f"{montant_a_placer:,.2f}€"
    })
    
    # Intérêts sur les mois suivants
    solde = montant_a_placer
    taux_mensuel = (1.015 ** (1/12)) - 1
    interets_total = 0
    
    for m in range(7, 25):
        interets = solde * taux_mensuel
        solde += interets
        interets_total += interets
    
    # Résumé des calculs
    log_tva_placement("=== RÉSUMÉ FINAL PLACEMENT TVA ===", {
        "Total_placement_TVA_effectué": f"{montant_a_placer:,.2f}€",
        "Solde_final_placement_TVA": f"{solde:,.2f}€",
        "Intérêts_TVA_générés": f"{interets_total:,.2f}€",
        "Nombre_de_mois_analysés": 24
    })
    
    # Données pour les tableaux
    log_tva_placement("=== DONNÉES POUR TABLEAUX - MOIS AVEC PLACEMENT TVA ===", {})
    
    log_tva_placement(f"TABLEAU FLUX - MOIS {mois}", {
        "Mois": f"{mois} (2025-06)",
        "VAT_Due_Mois": "-12,827.00€",
        "VAT_Payment": "-12,827.00€",
        "Placement_Exces_TVA": f"{montant_a_placer:,.2f}€",
        "Solde_Placement_TVA_Cumul": f"{montant_a_placer:,.2f}€",
        "Interets_Placements_Mensuels": "0.00€",
        "Total_Placements": f"{montant_a_placer:,.2f}€",
        "Tresorerie_Non_Placee": "39,738.40€"  # Exemple
    })
    
    # 2. SIMULATION DE L'AFFICHAGE DANS LES TABLEAUX
    log_tva_placement("=== PHASE 2: AFFICHAGE TABLEAUX ===")
    
    # Simulation du tableau de flux de trésorerie
    log_tva_placement("AFFICHAGE TABLEAU - placement_tva_mois", {
        "Ligne": "(+) Nouveau Placement Excédent TVA",
        "Année": 2025,
        "Valeurs_non_nulles": {"Mois_6": f"{montant_a_placer:,.2f}€"},
        "Total_annuel": f"{montant_a_placer:,.2f}€"
    })
    
    # PROBLÈME POTENTIEL : Si ici on voit 137€ au lieu de 10,261€
    # C'est que la valeur est mal récupérée du DataFrame
    log_tva_placement("AFFICHAGE TABLEAU - placement_tva_mois (PROBLÈME?)", {
        "Ligne": "(+) Nouveau Placement Excédent TVA",
        "Année": 2025,
        "Valeurs_non_nulles": {"Mois_6": "137.00€"},  # Simulation du bug
        "Total_annuel": "137.00€",
        "ALERTE": "Valeur incorrecte! Attendu: 10,261.60€"
    })
    
    # Simulation du compte de résultat
    log_tva_placement("COMPTE DE RÉSULTAT - ANNÉE 2025", {
        "Intérêts_placements_annuels": f"{interets_total:,.2f}€",
        "Revenus_exploitation": "150,000.00€",
        "Intérêts_sur_dette": "3,500.00€",
        "IS_décaissé": "8,500.00€"
    })
    
    print("\n✅ Simulation complète terminée!")

def analyze_comparison():
    """Analyse et compare les valeurs calculées vs affichées"""
    
    print("\n📊 ANALYSE DE COMPARAISON")
    print("=" * 50)
    
    expected_placement = 10261.60
    
    print(f"✅ VALEUR ATTENDUE : {expected_placement:,.2f}€")
    print(f"   (80% de 12,827€)")
    
    print("\n🔍 POINTS DE VÉRIFICATION:")
    print("1. Dans 'TABLEAU FLUX - MOIS 6':")
    print(f"   - Placement_Exces_TVA doit être {expected_placement:,.2f}€")
    
    print("\n2. Dans 'AFFICHAGE TABLEAU - placement_tva_mois':")
    print(f"   - Valeurs_non_nulles.Mois_6 doit être {expected_placement:,.2f}€")
    print("   - Si c'est 137€, le problème est dans la récupération des données")
    
    print("\n3. Causes possibles du bug 137€:")
    print("   - Mauvaise colonne lue dans le DataFrame")
    print("   - Division par 1000 incorrecte")
    print("   - Confusion avec les intérêts mensuels")
    print("   - Problème de timing (mois décalé)")

def main():
    """Fonction principale"""
    print("\n" + "="*60)
    print("🧪 TEST COMPLET TVA AVEC LOGS TABLEAUX")
    print("="*60 + "\n")
    
    # 1. Simuler le flux complet
    simulate_complete_tva_flow()
    
    # 2. Analyser les différences
    analyze_comparison()
    
    # 3. Lire et afficher le log
    log_path = os.path.join(os.path.dirname(__file__), '..', 'log.txt')
    if os.path.exists(log_path):
        print("\n📜 EXTRAIT DU LOG GÉNÉRÉ:")
        print("-" * 50)
        
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Afficher les lignes importantes
        important_patterns = [
            "PLACEMENT TVA EFFECTUÉ",
            "AFFICHAGE TABLEAU",
            "PROBLÈME",
            "ALERTE"
        ]
        
        for line in lines[-50:]:  # Dernières 50 lignes
            for pattern in important_patterns:
                if pattern in line:
                    print(line.rstrip())
                    break
    
    print("\n" + "="*60)
    print("💡 ACTIONS:")
    print("1. Exécutez OptimPV réel pour voir les vraies valeurs")
    print("2. Comparez avec ce test pour identifier la différence")
    print("3. Le log montrera exactement où 137€ apparaît")
    print("="*60)

if __name__ == "__main__":
    main()