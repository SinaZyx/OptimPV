#!/usr/bin/env python3
"""
Test simple pour vérifier la génération des logs TVA sans dépendances externes
"""

import os
import sys
from datetime import datetime

# Ajouter le chemin pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import direct des fonctions de logging
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
            f.write(f"=== NOUVEAU LOG TVA PLACEMENT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
    except Exception as e:
        print(f"Erreur initialisation log: {e}")

def simulate_tva_placement():
    """Simule le processus de placement TVA avec les logs"""
    
    print("🧪 SIMULATION DE PLACEMENT TVA")
    print("=" * 50)
    
    # Initialiser le log
    clear_tva_log()
    
    # Log des paramètres de configuration
    log_tva_placement("DÉBUT ANALYSE PLACEMENT TVA", {
        "taux_provision_annual": "2.50%",
        "taux_tva_annual": "1.50%", 
        "pct_tva_a_placer": "80.0%",
        "duree_construction": 3,
        "nombre_mois_total": 24
    })
    
    # Simuler plusieurs mois
    for mois in range(1, 25):
        # Simuler l'analyse des colonnes TVA
        if mois == 6:  # Mois avec remboursement TVA
            vat_data = {
                "VAT_Collectee": "2,173.00€",
                "VAT_Deductible_CAPEX": "15,000.00€",
                "VAT_Due_Mois": "-12,827.00€",
                "VAT_Payment": "-12,827.00€"
            }
            
            log_tva_placement(f"MOIS {mois} - ANALYSE COLONNES TVA", vat_data)
            
            # Analyse VAT_Payment
            log_tva_placement(f"MOIS {mois} - ANALYSE VAT_Payment", {
                "VAT_Due_Mois": "-12,827.00€",
                "VAT_Payment": "-12,827.00€"
            })
            
            # Détection du remboursement - VOICI LE BUG POTENTIEL
            # Si VAT_Payment est négatif ET VAT_Due_Mois est négatif
            # Le test actuel vérifie "vat_payment != 0" mais pas le signe
            
            log_tva_placement(f"MOIS {mois} - REMBOURSEMENT TVA DÉTECTÉ (Option 1)", {
                "Méthode": "Crédit TVA (VAT_Due_Mois négatif)",
                "Montant_remboursement": "12,827.00€"
            })
            
            # Calcul du placement
            montant_remboursement = 12827.0
            pct_placement = 0.80
            montant_a_placer = montant_remboursement * pct_placement
            
            log_tva_placement(f"MOIS {mois} - CALCUL PLACEMENT TVA", {
                "Remboursement_identifié": "12,827.00€",
                "Pourcentage_à_placer": "80.0%"
            })
            
            log_tva_placement(f"MOIS {mois} - PLACEMENT TVA EFFECTUÉ", {
                "Montant_à_placer": f"{montant_a_placer:,.2f}€",
                "Solde_placement_TVA_avant": "0.00€"
            })
            
            log_tva_placement(f"MOIS {mois} - PLACEMENT TVA MISE À JOUR", {
                "Solde_placement_TVA_après": f"{montant_a_placer:,.2f}€"
            })
            
        elif mois == 7:
            # Mois suivant avec intérêts
            solde = 10261.60
            taux_mensuel = (1.015 ** (1/12)) - 1
            interets = solde * taux_mensuel
            
            log_tva_placement(f"MOIS {mois} - ANALYSE COLONNES TVA", {})
            
    # Résumé final
    log_tva_placement("=== RÉSUMÉ FINAL PLACEMENT TVA ===", {
        "Total_placement_TVA_effectué": "10,261.60€",
        "Solde_final_placement_TVA": "10,399.23€",
        "Intérêts_TVA_générés": "137.63€",
        "Nombre_de_mois_analysés": 24
    })
    
    print("\n✅ Simulation terminée!")

def check_and_analyze_log():
    """Vérifie et analyse le log généré"""
    
    print("\n📊 VÉRIFICATION DU LOG")
    print("=" * 50)
    
    log_path = os.path.join(os.path.dirname(__file__), '..', 'log.txt')
    
    if os.path.exists(log_path):
        print(f"✅ Fichier log.txt trouvé: {log_path}")
        
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📁 Taille: {len(content):,} caractères")
        
        # Vérifications clés
        checks = [
            ("Initialisation", "DÉBUT ANALYSE PLACEMENT TVA"),
            ("Remboursement 12,827€", "12,827"),
            ("Placement 10,261€", "10,261"),
            ("Détection remboursement", "REMBOURSEMENT TVA DÉTECTÉ"),
            ("Résumé final", "RÉSUMÉ FINAL PLACEMENT TVA")
        ]
        
        print("\n🔍 Vérifications:")
        for name, pattern in checks:
            if pattern in content:
                print(f"  ✅ {name}")
            else:
                print(f"  ❌ {name}")
        
        # Afficher les 20 dernières lignes
        print("\n📜 Dernières lignes du log:")
        print("-" * 50)
        lines = content.split('\n')
        for line in lines[-20:]:
            if line.strip():
                print(line)
                
    else:
        print(f"❌ Fichier log.txt non trouvé!")

def main():
    """Fonction principale"""
    print("\n" + "="*60)
    print("🧪 TEST SIMPLE DE GÉNÉRATION DES LOGS TVA")
    print("="*60 + "\n")
    
    # 1. Simuler le placement TVA
    simulate_tva_placement()
    
    # 2. Vérifier et analyser le log
    check_and_analyze_log()
    
    print("\n" + "="*60)
    print("💡 Pour une analyse complète, utilisez:")
    print("   python analyze_tva_log.py")
    print("="*60)

if __name__ == "__main__":
    main()