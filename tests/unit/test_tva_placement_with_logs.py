#!/usr/bin/env python3
"""
Test complet du placement TVA avec génération et analyse des logs
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# Ajouter le chemin pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import des modules nécessaires
from modules.engine_module.core_analyzer import AnalysisEngine
from modules.config import ConfigModule

def create_test_scenario():
    """Crée un scénario de test avec remboursement TVA"""
    print("📋 Création du scénario de test...")
    
    # Configuration globale
    config = {
        "nom_projet": "Test Placement TVA",
        "localisation": "France",
        "date_debut_ppa": "2025-01-01",
        "duree_ppa": 240,  # 20 ans
        "duree_construction": 3,  # 3 mois
        "amortissement_duree": 15,
        "valeur_residuelle_pct": 10.0,
        "cout_demantelement_pct": 5.0,
        "degradation_rate": 0.5,
        
        # Paramètres économiques
        "taux_inflation": 2.0,
        "taux_imposition": 25.0,
        "tarif_edf_reference": 0.21,
        
        # Paramètres de placement TVA
        "placement_tresorerie_active": True,
        "pourcentage_tva_a_placer": 80.0,  # 80%
        "taux_placement_provision_onduleur": 2.5,
        "taux_placement_exces_tva": 1.5,
        
        # TVA
        "tva_taux": 20.0,
        "remboursement_credit_tva_actif": True,
        "seuil_remboursement_tva": 1000.0,
        
        # Financement
        "capex_total": 100000.0,
        "debt_ratio": 70.0,
        "taux_interet_dette": 3.5,
        "duree_dette": 180,  # 15 ans
        
        # OPEX
        "opex_maintenance_pct": 1.0,
        "opex_assurance_pct": 0.5,
        "opex_admin_pct": 0.5,
        "opex_provision_onduleur_pct": 0.5,
        
        # Autres
        "turpe_injection_eur_per_mw": 1000.0,
        "cout_fonds_propres": 8.0,
        "bfr_receivables_days": 30,
        "bfr_payables_days": 45
    }
    
    # Données de production simulées
    dates = pd.date_range(start='2025-01-01', periods=240, freq='M')
    
    # Créer des données de sites avec production et consommation
    sites_data = []
    
    # Site unique avec production constante
    for month_date in dates:
        sites_data.append({
            'Site': 'Site_Test',
            'Date': month_date,
            'Production_kWh': 10000,  # Production constante
            'Consommation_kWh': 8000,  # Consommation constante
            'Prix_Vente_Surplus': 0.08,  # 8 cts/kWh
            'Valorisation_Autoconso': 0.15  # 15 cts/kWh
        })
    
    sites_df = pd.DataFrame(sites_data)
    
    return config, sites_df

def run_analysis_with_tva():
    """Lance l'analyse avec le moteur et génère les logs"""
    print("\n🚀 Lancement de l'analyse...")
    
    # Créer le scénario
    config, sites_df = create_test_scenario()
    
    # Initialiser le moteur d'analyse
    engine = AnalysisEngine()
    
    # Paramètres du scénario
    scenario_params = {
        'name': 'Test_TVA_Placement',
        'capex_total': config['capex_total'],
        'puissance_installee_kwc': 100.0,  # 100 kWc
        'debt_ratio': config['debt_ratio'],
        'cout_fonds_propres': config['cout_fonds_propres']
    }
    
    # Simuler un remboursement TVA important au mois 6
    # Pour cela, on va créer une situation où il y a un gros CAPEX avec TVA déductible
    
    try:
        # Appeler une méthode d'analyse simplifiée
        # Note: Cette partie dépend de l'API exacte du moteur
        # Je vais créer une structure de données minimale
        
        # Créer un DataFrame mensuel de test
        dates = pd.date_range(start='2025-01-31', periods=24, freq='M')
        monthly_df = pd.DataFrame(index=dates)
        
        # Colonnes nécessaires pour le placement TVA
        monthly_df['VAT_Collectee'] = 0.0
        monthly_df['VAT_Deductible_CAPEX'] = 0.0
        monthly_df['VAT_Deductible_OPEX_TURPE'] = 0.0
        monthly_df['VAT_Due_Mois'] = 0.0
        monthly_df['VAT_Payment'] = 0.0
        monthly_df['OPEX_Provision_Onduleur_Mensuel'] = 100.0  # 100€/mois
        monthly_df['Solde_Tresorerie_Debut_Mois'] = 50000.0
        monthly_df['Solde_Tresorerie_Fin_Mois'] = 50000.0
        monthly_df['Flux_Tresorerie_Net'] = 0.0
        
        # Simuler un gros crédit de TVA au mois 6 (après construction)
        # TVA déductible sur CAPEX concentrée
        monthly_df.loc[monthly_df.index[5], 'VAT_Deductible_CAPEX'] = 15000.0
        monthly_df.loc[monthly_df.index[5], 'VAT_Collectee'] = 2173.0
        monthly_df.loc[monthly_df.index[5], 'VAT_Due_Mois'] = -12827.0  # Crédit de TVA
        monthly_df.loc[monthly_df.index[5], 'VAT_Payment'] = -12827.0  # Remboursement
        
        # Appliquer la logique de placement
        print("📊 Application de la logique de placement TVA...")
        engine._apply_placement_logic(
            monthly_df, 
            config, 
            24,  # nombre total de mois
            3    # durée construction
        )
        
        print("✅ Analyse terminée avec succès!")
        
        return True, monthly_df
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def check_log_file():
    """Vérifie que le fichier log.txt a été créé"""
    print("\n🔍 Vérification du fichier log...")
    
    log_path = os.path.join(os.path.dirname(__file__), '..', 'log.txt')
    
    if os.path.exists(log_path):
        file_size = os.path.getsize(log_path)
        mod_time = datetime.fromtimestamp(os.path.getmtime(log_path))
        print(f"✅ Fichier log.txt trouvé!")
        print(f"   - Taille: {file_size:,} octets")
        print(f"   - Dernière modification: {mod_time}")
        return True, log_path
    else:
        print("❌ Fichier log.txt non trouvé!")
        print(f"   Chemin attendu: {log_path}")
        return False, None

def analyze_log_content(log_path):
    """Analyse le contenu du log et affiche les résultats"""
    print("\n📊 Analyse du contenu du log...")
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📁 Taille totale du log: {len(content):,} caractères")
        
        # Rechercher les éléments clés
        if "DÉBUT ANALYSE PLACEMENT TVA" in content:
            print("✅ Analyse de placement TVA initialisée")
        
        # Chercher le remboursement de 12,827€
        if "12,827" in content or "12827" in content:
            print("✅ Montant de 12,827€ trouvé dans les logs!")
            
            # Extraire le contexte
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "12,827" in line or "12827" in line:
                    print(f"\n📍 Contexte (ligne {i+1}):")
                    # Afficher 3 lignes avant et après
                    start = max(0, i-3)
                    end = min(len(lines), i+4)
                    for j in range(start, end):
                        prefix = ">>>" if j == i else "   "
                        print(f"{prefix} {lines[j]}")
        else:
            print("❌ Montant de 12,827€ NON trouvé dans les logs")
        
        # Chercher les placements effectués
        if "PLACEMENT TVA EFFECTUÉ" in content:
            print("\n✅ Des placements TVA ont été effectués")
            
            # Extraire les montants
            import re
            montants = re.findall(r"Montant_à_placer[:\s]+([\d,\.]+)€", content)
            if montants:
                print("💰 Montants placés:")
                for m in montants:
                    print(f"   - {m}€")
                    if "10,261" in m or "10261" in m:
                        print("   ✅ CORRECT: 80% de 12,827€ = 10,261€")
        
        # Chercher les alertes
        alertes = content.count("ALERTE COHÉRENCE")
        if alertes > 0:
            print(f"\n⚠️ {alertes} alerte(s) de cohérence détectée(s)")
        
        # Résumé final
        if "RÉSUMÉ FINAL PLACEMENT TVA" in content:
            print("\n📋 Résumé final trouvé dans les logs")
            # Extraire la section résumé
            resume_start = content.find("RÉSUMÉ FINAL PLACEMENT TVA")
            resume_section = content[resume_start:resume_start+500]
            print(resume_section)
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse du log: {e}")
        return False

def main():
    """Fonction principale du test"""
    print("=" * 60)
    print("🧪 TEST PLACEMENT TVA AVEC ANALYSE DES LOGS")
    print("=" * 60)
    
    # 1. Lancer l'analyse
    success, monthly_df = run_analysis_with_tva()
    
    if not success:
        print("\n❌ L'analyse a échoué. Vérifiez les erreurs ci-dessus.")
        return
    
    # 2. Vérifier la création du log
    log_exists, log_path = check_log_file()
    
    if not log_exists:
        print("\n❌ Le fichier log n'a pas été créé.")
        return
    
    # 3. Analyser le contenu
    analyze_success = analyze_log_content(log_path)
    
    # 4. Afficher les résultats du DataFrame si disponible
    if monthly_df is not None:
        print("\n📊 Résultats du DataFrame:")
        
        # Colonnes TVA
        tva_cols = [col for col in monthly_df.columns if 'TVA' in col or 'VAT' in col]
        placement_cols = ['Placement_Exces_TVA', 'Solde_Placement_TVA_Cumul']
        
        # Afficher les lignes avec des valeurs non nulles
        non_zero_rows = monthly_df[(monthly_df[tva_cols + placement_cols] != 0).any(axis=1)]
        
        if not non_zero_rows.empty:
            print("\nLignes avec activité TVA/Placement:")
            print(non_zero_rows[tva_cols + placement_cols])
    
    # 5. Recommandations finales
    print("\n" + "=" * 60)
    print("🔧 PROCHAINES ÉTAPES:")
    print("1. Examinez le fichier log.txt pour plus de détails")
    print("2. Utilisez: python analyze_tva_log.py")
    print("3. Si le placement est incorrect, le log montrera exactement où")
    print("=" * 60)

if __name__ == "__main__":
    main()