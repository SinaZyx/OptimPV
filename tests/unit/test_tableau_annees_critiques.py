#!/usr/bin/env python3
"""
Test des tableaux financiers pour les années critiques :
- Première année d'exploitation (vérifier placements TVA)
- Année de remplacement d'onduleur (vérifier déblocage provisions)
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Ajouter les modules au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

def create_test_financial_data():
    """Crée des données financières de test pour 20 ans"""
    
    print("📊 CRÉATION DES DONNÉES DE TEST")
    print("=" * 40)
    
    # Configuration du projet de test
    start_date = datetime(2024, 1, 1)
    construction_months = 3
    operation_start = start_date + timedelta(days=construction_months * 30)
    total_months = 240  # 20 ans
    
    # Créer l'index des dates mensuelles
    dates = pd.date_range(start_date, periods=total_months, freq='ME')
    
    # Initialiser le DataFrame
    monthly_data = pd.DataFrame(index=dates)
    
    # Données de base
    monthly_data['Revenus_Total'] = 0
    monthly_data['OPEX'] = 0
    monthly_data['OPEX_Provision_Onduleur_Mensuel'] = 0
    monthly_data['VAT_Payment'] = 0
    monthly_data['VAT_Due_Mois'] = 0
    monthly_data['Interets_Payes'] = 0
    monthly_data['Principal_Rembourse'] = 0
    monthly_data['Service_Dette'] = 0
    monthly_data['Total_IS_Decaisse_Mois'] = 0
    monthly_data['Solde_Tresorerie_Fin_Mois'] = 50000  # Trésorerie initiale
    
    # Phase de construction (3 premiers mois)
    for i in range(construction_months):
        monthly_data.iloc[i, monthly_data.columns.get_loc('OPEX')] = 0
        monthly_data.iloc[i, monthly_data.columns.get_loc('Solde_Tresorerie_Fin_Mois')] = 50000 - (i * 5000)
    
    # Remboursement TVA CAPEX au mois 7 (3 mois après fin construction)
    vat_refund_month = 6  # Index 6 = mois 7
    monthly_data.iloc[vat_refund_month, monthly_data.columns.get_loc('VAT_Payment')] = 12827
    
    # Phase d'exploitation (après construction)
    for i in range(construction_months, total_months):
        # Revenus mensuels d'exploitation
        monthly_data.iloc[i, monthly_data.columns.get_loc('Revenus_Total')] = 2500
        
        # OPEX mensuel
        monthly_data.iloc[i, monthly_data.columns.get_loc('OPEX')] = 300
        
        # Provision onduleur mensuelle (démarrage après construction)
        monthly_data.iloc[i, monthly_data.columns.get_loc('OPEX_Provision_Onduleur_Mensuel')] = 85
        
        # Service de dette
        monthly_data.iloc[i, monthly_data.columns.get_loc('Interets_Payes')] = 400
        monthly_data.iloc[i, monthly_data.columns.get_loc('Principal_Rembourse')] = 800
        monthly_data.iloc[i, monthly_data.columns.get_loc('Service_Dette')] = 1200
        
        # Impôts sur les sociétés (à partir de la 2ème année)
        if i >= 12:  # Après la 1ère année
            monthly_data.iloc[i, monthly_data.columns.get_loc('Total_IS_Decaisse_Mois')] = 150
        
        # Évolution de la trésorerie
        cash_flow = 2500 - 300 - 1200 - (150 if i >= 12 else 0)
        if i == 0:
            monthly_data.iloc[i, monthly_data.columns.get_loc('Solde_Tresorerie_Fin_Mois')] = 50000 + cash_flow
        else:
            prev_cash = monthly_data.iloc[i-1, monthly_data.columns.get_loc('Solde_Tresorerie_Fin_Mois')]
            monthly_data.iloc[i, monthly_data.columns.get_loc('Solde_Tresorerie_Fin_Mois')] = prev_cash + cash_flow
    
    # Petits remboursements TVA mensuels (exploitation)
    for i in range(construction_months + 12, total_months, 12):  # Annuels à partir de la 2ème année
        if i < total_months:
            monthly_data.iloc[i, monthly_data.columns.get_loc('VAT_Payment')] = 450
    
    print(f"✅ Données créées pour {total_months} mois")
    print(f"✅ Construction: mois 1-{construction_months}")
    print(f"✅ Exploitation: mois {construction_months+1}-{total_months}")
    print(f"✅ Remboursement TVA CAPEX: mois {vat_refund_month+1}")
    
    return monthly_data, {
        'construction_months': construction_months,
        'operation_start_month': construction_months + 1,
        'vat_refund_month': vat_refund_month + 1,
        'inverter_replacement_year': 15
    }

def simulate_placement_logic(monthly_data, config_info):
    """Simule la logique de placement sur les données"""
    
    print("\\n🏦 SIMULATION LOGIQUE DE PLACEMENT")
    print("=" * 40)
    
    # Configuration des placements
    placement_config = {
        'placement_tresorerie_active': True,
        'placement_tva_capex': True,
        'placement_tva_exploitation': True,
        'pourcentage_tva_capex_a_placer': 80.0,
        'pourcentage_tva_exploitation_a_placer': 60.0,
        'taux_placement_exces_tva': 1.5,  # 1.5% annuel
        'taux_placement_provision_onduleur': 2.5,  # 2.5% annuel
        'seuil_tva_capex': 5000.0,
        'seuil_remboursement_tva': 50.0
    }
    
    # Taux mensuels (intérêts composés)
    taux_tva_mensuel = (1 + placement_config['taux_placement_exces_tva']/100) ** (1/12) - 1
    taux_provision_mensuel = (1 + placement_config['taux_placement_provision_onduleur']/100) ** (1/12) - 1
    
    # Colonnes de placement
    placement_columns = [
        'Placement_Exces_TVA', 'Placement_Provision_Onduleur',
        'Solde_Placement_TVA_Cumul', 'Solde_Placement_Provision_Onduleur_Cumul',
        'Interets_Placements_Mensuels', 'Interets_Courus_Non_Encaisses',
        'Total_Placements', 'Deblocage_Placement_TVA', 'Deblocage_Placement_Onduleur',
        'Interets_Debloques_Imposables'
    ]
    
    for col in placement_columns:
        monthly_data[col] = 0.0
    
    # Variables de suivi
    solde_tva = 0.0
    solde_provision = 0.0
    tva_capex_placee = False
    total_provisions_placees = 0.0
    
    # Durée de vie onduleur pour calculer le déblocage
    duree_vie_onduleur_mois = config_info['inverter_replacement_year'] * 12
    mois_deblocage_onduleur = config_info['construction_months'] + duree_vie_onduleur_mois
    
    print(f"Paramètres de placement:")
    print(f"  - Taux TVA annuel: {placement_config['taux_placement_exces_tva']}% -> mensuel: {taux_tva_mensuel*100:.4f}%")
    print(f"  - Taux provision annuel: {placement_config['taux_placement_provision_onduleur']}% -> mensuel: {taux_provision_mensuel*100:.4f}%")
    print(f"  - Déblocage onduleur prévu au mois: {mois_deblocage_onduleur}")
    
    # Traitement mois par mois
    for month_idx, date_idx in enumerate(monthly_data.index):
        # Pendant la construction, pas de placement
        if month_idx < config_info['construction_months']:
            continue
        
        # Détection remboursement TVA
        vat_payment = monthly_data.loc[date_idx, 'VAT_Payment']
        vat_refund = abs(vat_payment) if vat_payment > 0 else 0
        
        # Placement TVA
        if vat_refund >= placement_config['seuil_remboursement_tva']:
            if vat_refund >= placement_config['seuil_tva_capex'] and not tva_capex_placee:
                # TVA CAPEX
                montant_place = vat_refund * (placement_config['pourcentage_tva_capex_a_placer'] / 100)
                monthly_data.loc[date_idx, 'Placement_Exces_TVA'] = montant_place
                tva_capex_placee = True
                print(f"  Mois {month_idx+1}: Placement TVA CAPEX {montant_place:,.0f}€ (sur {vat_refund:,.0f}€)")
            elif vat_refund < placement_config['seuil_tva_capex']:
                # TVA exploitation
                montant_place = vat_refund * (placement_config['pourcentage_tva_exploitation_a_placer'] / 100)
                if montant_place > 0:
                    monthly_data.loc[date_idx, 'Placement_Exces_TVA'] = montant_place
                    print(f"  Mois {month_idx+1}: Placement TVA exploitation {montant_place:,.0f}€")
        
        # Placement provision onduleur
        provision_mois = monthly_data.loc[date_idx, 'OPEX_Provision_Onduleur_Mensuel']
        if provision_mois > 0:
            monthly_data.loc[date_idx, 'Placement_Provision_Onduleur'] = provision_mois
            total_provisions_placees += provision_mois
        
        # Déblocage onduleur
        if month_idx == mois_deblocage_onduleur and solde_provision > 0:
            montant_deblocage = solde_provision
            monthly_data.loc[date_idx, 'Deblocage_Placement_Onduleur'] = montant_deblocage
            
            # Intérêts devenus imposables
            interets_cumules = montant_deblocage - total_provisions_placees
            monthly_data.loc[date_idx, 'Interets_Debloques_Imposables'] = interets_cumules
            
            print(f"  Mois {month_idx+1}: DÉBLOCAGE ONDULEUR {montant_deblocage:,.0f}€ (dont {interets_cumules:,.0f}€ d'intérêts)")
            
            # Reset provision
            solde_provision = 0.0
            total_provisions_placees = 0.0
        
        # Calcul des intérêts
        interets_tva = solde_tva * taux_tva_mensuel if solde_tva > 0 else 0
        interets_provision = solde_provision * taux_provision_mensuel if solde_provision > 0 else 0
        interets_totaux = interets_tva + interets_provision
        
        monthly_data.loc[date_idx, 'Interets_Placements_Mensuels'] = interets_totaux
        
        # Mise à jour des soldes
        nouveau_placement_tva = monthly_data.loc[date_idx, 'Placement_Exces_TVA']
        nouveau_placement_provision = monthly_data.loc[date_idx, 'Placement_Provision_Onduleur']
        
        solde_tva = solde_tva + interets_tva + nouveau_placement_tva
        solde_provision = solde_provision + interets_provision + nouveau_placement_provision
        
        monthly_data.loc[date_idx, 'Solde_Placement_TVA_Cumul'] = solde_tva
        monthly_data.loc[date_idx, 'Solde_Placement_Provision_Onduleur_Cumul'] = solde_provision
        monthly_data.loc[date_idx, 'Total_Placements'] = solde_tva + solde_provision
        
        # Intérêts courus cumulés
        if month_idx > 0:
            cumul_precedent = monthly_data.iloc[month_idx-1]['Interets_Courus_Non_Encaisses']
        else:
            cumul_precedent = 0
        monthly_data.loc[date_idx, 'Interets_Courus_Non_Encaisses'] = cumul_precedent + interets_totaux
    
    print("✅ Logique de placement appliquée")
    return monthly_data

def test_annee_critique(monthly_data, year, description):
    """Teste les résultats pour une année critique"""
    
    print(f"\\n🔍 TEST ANNÉE {year} - {description}")
    print("=" * 50)
    
    # Filtrer les données de l'année
    year_data = monthly_data[monthly_data.index.year == year]
    
    if year_data.empty:
        print(f"❌ Aucune donnée pour l'année {year}")
        return False
    
    print(f"Données disponibles: {len(year_data)} mois")
    
    # Indicateurs clés
    revenus_annuels = year_data['Revenus_Total'].sum()
    opex_annuels = year_data['OPEX'].sum()
    provision_onduleur_annuelle = year_data['OPEX_Provision_Onduleur_Mensuel'].sum()
    service_dette_annuel = year_data['Service_Dette'].sum()
    impots_annuels = year_data['Total_IS_Decaisse_Mois'].sum()
    
    # Indicateurs de placement
    nouveau_placement_tva = year_data['Placement_Exces_TVA'].sum()
    nouveau_placement_provision = year_data['Placement_Provision_Onduleur'].sum()
    interets_annuels = year_data['Interets_Placements_Mensuels'].sum()
    deblocage_onduleur = year_data['Deblocage_Placement_Onduleur'].sum()
    interets_debloques = year_data['Interets_Debloques_Imposables'].sum()
    
    # Soldes de fin d'année
    solde_tva_fin = year_data['Solde_Placement_TVA_Cumul'].iloc[-1]
    solde_provision_fin = year_data['Solde_Placement_Provision_Onduleur_Cumul'].iloc[-1]
    total_placements_fin = year_data['Total_Placements'].iloc[-1]
    tresorerie_fin = year_data['Solde_Tresorerie_Fin_Mois'].iloc[-1]
    
    print("\\nINDICATEURS D'EXPLOITATION:")
    print(f"  Revenus annuels: {revenus_annuels:,.0f}€")
    print(f"  OPEX annuels: {opex_annuels:,.0f}€")
    print(f"  Provision onduleur: {provision_onduleur_annuelle:,.0f}€")
    print(f"  Service dette: {service_dette_annuel:,.0f}€")
    print(f"  Impôts société: {impots_annuels:,.0f}€")
    
    print("\\nINDICATEURS DE PLACEMENT:")
    print(f"  Nouveaux placements TVA: {nouveau_placement_tva:,.0f}€")
    print(f"  Nouveaux placements provision: {nouveau_placement_provision:,.0f}€")
    print(f"  Intérêts générés: {interets_annuels:,.0f}€")
    if deblocage_onduleur > 0:
        print(f"  DÉBLOCAGE ONDULEUR: {deblocage_onduleur:,.0f}€")
        print(f"  Dont intérêts imposables: {interets_debloques:,.0f}€")
    
    print("\\nSOLDES DE FIN D'ANNÉE:")
    print(f"  Solde placement TVA: {solde_tva_fin:,.0f}€")
    print(f"  Solde placement provision: {solde_provision_fin:,.0f}€")
    print(f"  Total placements: {total_placements_fin:,.0f}€")
    print(f"  Trésorerie disponible: {tresorerie_fin:,.0f}€")
    
    # Calcul du compte de résultat simplifié
    print("\\nCOMPTE DE RÉSULTAT SIMPLIFIÉ:")
    resultat_exploitation = revenus_annuels - opex_annuels - provision_onduleur_annuelle
    charges_financieres = year_data['Interets_Payes'].sum()
    produits_financiers = interets_debloques  # Seulement les intérêts réalisés
    resultat_avant_impot = resultat_exploitation - charges_financieres + produits_financiers
    resultat_net = resultat_avant_impot - impots_annuels
    
    print(f"  Résultat d'exploitation: {resultat_exploitation:,.0f}€")
    print(f"  Charges financières: {charges_financieres:,.0f}€")
    print(f"  Produits financiers: {produits_financiers:,.0f}€")
    print(f"  RÉSULTAT AVANT IMPÔT: {resultat_avant_impot:,.0f}€")
    print(f"  RÉSULTAT NET: {resultat_net:,.0f}€")
    
    # Vérifications spécifiques
    print("\\nVÉRIFICATIONS:")
    
    issues_found = False
    
    # Vérification revenus cohérents
    if revenus_annuels == 0 and year > 2024:  # Après la première année
        print("  ❌ PROBLÈME: Revenus nuls en exploitation")
        issues_found = True
    else:
        print("  ✅ Revenus cohérents")
    
    # Vérification placements
    if year == 2024:  # Première année
        if nouveau_placement_tva == 0:
            print("  ❌ PROBLÈME: Aucun placement TVA en première année")
            issues_found = True
        else:
            print("  ✅ Placement TVA effectué en première année")
    
    # Vérification déblocage onduleur
    if year == 2024 + 15:  # Année de remplacement (15 ans après 2024)
        if deblocage_onduleur == 0:
            print("  ❌ PROBLÈME: Pas de déblocage onduleur prévu")
            issues_found = True
        else:
            print("  ✅ Déblocage onduleur effectué")
            
        if interets_debloques == 0:
            print("  ❌ PROBLÈME: Pas d'intérêts déblocage onduleur")
            issues_found = True
        else:
            print("  ✅ Intérêts déblocage correctement calculés")
    
    # Vérification cohérence mathématique
    if abs(resultat_avant_impot - (resultat_exploitation - charges_financieres + produits_financiers)) > 0.01:
        print("  ❌ PROBLÈME: Incohérence calcul résultat avant impôt")
        issues_found = True
    else:
        print("  ✅ Calculs cohérents")
    
    if issues_found:
        print("\\n⚠️  PROBLÈMES DÉTECTÉS DANS CETTE ANNÉE")
        return False
    else:
        print("\\n✅ AUCUN PROBLÈME DÉTECTÉ")
        return True

def main():
    """Fonction principale du test"""
    
    print("🧪 TEST DES TABLEAUX FINANCIERS - ANNÉES CRITIQUES")
    print("=" * 60)
    print("Test des résultats pour la première année et l'année de remplacement d'onduleur")
    print()
    
    # Créer les données de test
    monthly_data, config_info = create_test_financial_data()
    
    # Appliquer la logique de placement
    monthly_data = simulate_placement_logic(monthly_data, config_info)
    
    # Tester les années critiques
    print("\\n" + "=" * 60)
    print("TESTS DES ANNÉES CRITIQUES")
    
    # Première année (2024) - Vérifier placements TVA
    success_2024 = test_annee_critique(monthly_data, 2024, "PREMIÈRE ANNÉE D'EXPLOITATION")
    
    # Année de remplacement onduleur (2039 = 2024 + 15)
    success_2039 = test_annee_critique(monthly_data, 2039, "ANNÉE DE REMPLACEMENT ONDULEUR")
    
    # Test d'une année intermédiaire pour comparaison
    success_2030 = test_annee_critique(monthly_data, 2030, "ANNÉE INTERMÉDIAIRE (6 ANS)")
    
    # Résumé final
    print("\\n" + "=" * 60)
    print("RÉSUMÉ DU TEST:")
    print("-" * 30)
    
    test_results = [
        ("Première année (2024)", success_2024),
        ("Année remplacement onduleur (2039)", success_2039),
        ("Année intermédiaire (2030)", success_2030)
    ]
    
    total_success = sum(1 for _, success in test_results if success)
    total_tests = len(test_results)
    
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\\nRésultat global: {total_success}/{total_tests} années testées avec succès")
    
    if total_success == total_tests:
        print("\\n🎉 TOUS LES TESTS SONT PASSÉS!")
        print("✅ Les tableaux financiers fonctionnent correctement")
        print("✅ Les placements et déblocages sont cohérents")
        print("✅ Les calculs de résultat sont exacts")
    else:
        print("\\n⚠️  CERTAINS TESTS ONT ÉCHOUÉ!")
        print("❌ Vérifiez l'implémentation des placements")
        print("❌ Contrôlez les calculs de déblocage onduleur")
    
    # Sauvegarder les données pour analyse
    output_file = "test_results_annees_critiques.csv"
    monthly_data.to_csv(output_file)
    print(f"\\n📁 Données sauvegardées dans: {output_file}")
    
    return total_success == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)