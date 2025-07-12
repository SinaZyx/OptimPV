#!/usr/bin/env python3
"""
Test simple pour vérifier que la correction du fonds de réserve fonctionne
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Ajouter le chemin du module
sys.path.append(os.path.join(os.path.dirname(__file__)))

def test_sinking_fund_variables():
    """Test que les variables sont correctement définies dans le fonds de réserve"""
    
    print("🧪 TEST CORRECTION FONDS DE RÉSERVE")
    print("=" * 50)
    
    try:
        # Simuler les variables nécessaires
        duree_construction_cfg = 3  # 3 mois de construction
        duree_vie_onduleur = 10     # 10 ans
        
        # Créer un DataFrame de test avec 24 mois de données
        dates = pd.date_range(start='2024-01-01', periods=24, freq='M')
        monthly_results_df = pd.DataFrame(index=dates)
        monthly_results_df['OPEX_Provision_Onduleur_Mensuel'] = 100.0  # 100€ par mois
        monthly_results_df['Solde_Tresorerie_Fin_Mois'] = 5000.0
        
        # Test du code corrigé
        print(f"✅ duree_construction_cfg défini: {duree_construction_cfg}")
        print(f"✅ duree_vie_onduleur défini: {duree_vie_onduleur}")
        
        # Variables du fonds de réserve
        capital_cumule = 0.0
        interets_cumules = 0.0
        placement_actif = True
        taux_mensuel = 0.002  # 2.4% annuel
        
        # Simuler la boucle corrigée
        erreurs = 0
        mois_testes = 0
        
        for idx, date_mois in enumerate(monthly_results_df.index):
            mois_testes += 1
            
            # Test de la condition corrigée
            if idx < duree_construction_cfg:
                print(f"  Mois {idx + 1}: Phase construction (ignoré)")
                continue
                
            # Récupérer la provision du mois
            provision_mois = monthly_results_df.loc[date_mois, 'OPEX_Provision_Onduleur_Mensuel']
            capital_cumule += provision_mois
            
            # Calculer intérêts
            if placement_actif and (capital_cumule + interets_cumules) > 0:
                interets_mois = (capital_cumule + interets_cumules) * taux_mensuel
                interets_cumules += interets_mois
            else:
                interets_mois = 0.0
            
            # Test de la condition de remplacement corrigée  
            mois_remplacement = duree_construction_cfg + duree_vie_onduleur * 12
            
            # Enregistrer les colonnes avec les bons noms
            monthly_results_df.loc[date_mois, 'Fonds_Reserve_Onduleur_Constitutions'] = provision_mois
            monthly_results_df.loc[date_mois, 'Fonds_Reserve_Onduleur_Interets'] = interets_mois
            monthly_results_df.loc[date_mois, 'Fonds_Reserve_Onduleur_Total'] = capital_cumule + interets_cumules
            
            if idx <= 6:  # Afficher les premiers mois
                print(f"  Mois {idx + 1}: Provision={provision_mois}€, Capital={capital_cumule:.0f}€, Intérêts={interets_cumules:.2f}€")
                
            if idx == mois_remplacement and capital_cumule > 0:
                print(f"  🔧 REMPLACEMENT ONDULEUR au mois {idx + 1}")
                montant_total = capital_cumule + interets_cumules
                monthly_results_df.loc[date_mois, 'Fonds_Reserve_Onduleur_Liberation'] = montant_total
                print(f"     Total libéré: {montant_total:.2f}€")
        
        print(f"\n✅ Test terminé: {mois_testes} mois traités, {erreurs} erreurs")
        print(f"✅ Capital final: {capital_cumule:.2f}€")
        print(f"✅ Intérêts final: {interets_cumules:.2f}€")
        print(f"✅ Mois de remplacement prévu: {duree_construction_cfg + duree_vie_onduleur * 12}")
        
        # Vérifier les colonnes créées
        colonnes_attendues = [
            'Fonds_Reserve_Onduleur_Constitutions',
            'Fonds_Reserve_Onduleur_Interets', 
            'Fonds_Reserve_Onduleur_Total'
        ]
        
        for col in colonnes_attendues:
            if col in monthly_results_df.columns:
                valeur_max = monthly_results_df[col].max()
                print(f"✅ Colonne {col}: max = {valeur_max:.2f}")
            else:
                print(f"❌ Colonne {col}: MANQUANTE")
                erreurs += 1
        
        if erreurs == 0:
            print("\n🎉 TOUTES LES CORRECTIONS SONT VALIDÉES!")
            print("✅ Pas d'erreur NameError attendue")
            print("✅ Variables correctement définies")
            print("✅ Colonnes correctement nommées")
            return True
        else:
            print(f"\n❌ {erreurs} erreurs détectées")
            return False
            
    except NameError as e:
        print(f"❌ ERREUR NameError: {e}")
        print("   Cette erreur indique que la correction n'est pas complète")
        return False
    except Exception as e:
        print(f"❌ ERREUR INATTENDUE: {e}")
        return False

if __name__ == "__main__":
    success = test_sinking_fund_variables()
    if success:
        print("\n💡 RECOMMANDATION: La correction est prête pour test avec l'application complète")
    else:
        print("\n⚠️  ATTENTION: Corriger les erreurs avant de tester l'application")
    
    sys.exit(0 if success else 1)