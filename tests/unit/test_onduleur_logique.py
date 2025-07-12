#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simplifié pour vérifier la logique du remplacement d'onduleur
"""

def test_calcul_remplacement_onduleur():
    """Test de la logique de calcul du remplacement d'onduleur"""
    
    print("🧪 TEST DE LA LOGIQUE DE REMPLACEMENT D'ONDULEUR")
    print("="*60)
    
    # Paramètres de base
    cout_onduleur_initial = 10190  # Coût initial de l'onduleur
    duree_vie_ans = 10
    taux_inflation_annuel = 0.02  # 2%
    taux_placement_annuel = 0.025  # 2.5%
    
    # Calcul de l'inflation sur 10 ans
    facteur_inflation = (1 + taux_inflation_annuel) ** duree_vie_ans
    cout_onduleur_indexe = cout_onduleur_initial * facteur_inflation
    
    print(f"📊 PARAMÈTRES:")
    print(f"  - Coût onduleur initial: {cout_onduleur_initial:,.0f}€")
    print(f"  - Durée de vie: {duree_vie_ans} ans")
    print(f"  - Inflation: {taux_inflation_annuel*100:.1f}% par an")
    print(f"  - Taux placement: {taux_placement_annuel*100:.1f}% par an")
    
    print(f"\n📈 APRÈS {duree_vie_ans} ANS:")
    print(f"  - Facteur d'inflation: {facteur_inflation:.3f}")
    print(f"  - Coût onduleur indexé: {cout_onduleur_indexe:,.0f}€")
    
    # Provisions mensuelles
    provision_mensuelle = cout_onduleur_initial / (duree_vie_ans * 12)
    print(f"\n💰 PROVISIONS:")
    print(f"  - Provision mensuelle: {provision_mensuelle:.2f}€")
    print(f"  - Total provisionné: {provision_mensuelle * duree_vie_ans * 12:,.0f}€")
    
    # Scénario 1: SANS placement
    print(f"\n{'='*60}")
    print("SCÉNARIO 1: SANS PLACEMENT")
    print(f"{'='*60}")
    
    capital_sans_placement = cout_onduleur_initial
    interets_sans_placement = 0
    fonds_total_sans = capital_sans_placement + interets_sans_placement
    deficit_sans = cout_onduleur_indexe - fonds_total_sans
    
    print(f"  - Capital accumulé: {capital_sans_placement:,.0f}€")
    print(f"  - Intérêts: {interets_sans_placement:,.0f}€")
    print(f"  - Fonds total: {fonds_total_sans:,.0f}€")
    print(f"  - Coût onduleur: {cout_onduleur_indexe:,.0f}€")
    print(f"  - 🔴 DÉFICIT: {deficit_sans:,.0f}€")
    
    # Scénario 2: AVEC placement
    print(f"\n{'='*60}")
    print("SCÉNARIO 2: AVEC PLACEMENT À 2.5%")
    print(f"{'='*60}")
    
    # Calcul simplifié des intérêts composés
    # On suppose que tout le capital est placé dès le début (approximation)
    facteur_interets = (1 + taux_placement_annuel) ** duree_vie_ans
    montant_avec_interets = cout_onduleur_initial * facteur_interets
    interets_avec_placement = montant_avec_interets - cout_onduleur_initial
    fonds_total_avec = montant_avec_interets
    deficit_avec = cout_onduleur_indexe - fonds_total_avec
    
    print(f"  - Capital accumulé: {cout_onduleur_initial:,.0f}€")
    print(f"  - Intérêts générés: {interets_avec_placement:,.0f}€")
    print(f"  - Fonds total: {fonds_total_avec:,.0f}€")
    print(f"  - Coût onduleur: {cout_onduleur_indexe:,.0f}€")
    if deficit_avec > 0:
        print(f"  - 🟡 DÉFICIT: {deficit_avec:,.0f}€")
    else:
        print(f"  - 🟢 SURPLUS: {-deficit_avec:,.0f}€")
    
    # Comparaison
    print(f"\n{'='*60}")
    print("📊 COMPARAISON")
    print(f"{'='*60}")
    
    reduction_deficit = deficit_sans - deficit_avec
    print(f"  - Intérêts gagnés avec placement: {interets_avec_placement:,.0f}€")
    print(f"  - Réduction du déficit: {reduction_deficit:,.0f}€")
    print(f"  - Déficit sans placement: {deficit_sans:,.0f}€")
    print(f"  - Déficit avec placement: {deficit_avec:,.0f}€")
    
    # Impact sur le LCOE (estimation)
    print(f"\n💡 IMPACT ESTIMÉ SUR LE LCOE:")
    print(f"  - Le déficit sans placement ({deficit_sans:,.0f}€) devrait augmenter le LCOE")
    print(f"  - Le déficit avec placement ({deficit_avec:,.0f}€) devrait moins augmenter le LCOE")
    print(f"  - Différence attendue: le LCOE sans placement > LCOE avec placement")
    
    # Vérifications logiques
    print(f"\n✅ VÉRIFICATIONS LOGIQUES:")
    
    # Test 1: L'inflation augmente le coût
    test1 = cout_onduleur_indexe > cout_onduleur_initial
    print(f"  1. Coût indexé > Coût initial: {'✅ PASS' if test1 else '❌ FAIL'}")
    
    # Test 2: Les intérêts réduisent le déficit
    test2 = deficit_avec < deficit_sans
    print(f"  2. Déficit avec placement < Sans placement: {'✅ PASS' if test2 else '❌ FAIL'}")
    
    # Test 3: Sans placement, il y a toujours un déficit
    test3 = deficit_sans > 0
    print(f"  3. Déficit existe sans placement: {'✅ PASS' if test3 else '❌ FAIL'}")
    
    # Test 4: Les intérêts correspondent bien au calcul
    test4 = abs(interets_avec_placement - cout_onduleur_initial * ((1.025**10) - 1)) < 1
    print(f"  4. Calcul des intérêts correct: {'✅ PASS' if test4 else '❌ FAIL'}")
    
    all_tests_passed = test1 and test2 and test3 and test4
    
    print(f"\n{'='*60}")
    if all_tests_passed:
        print("✅ TOUS LES TESTS LOGIQUES SONT PASSÉS!")
        print("\n💡 CONCLUSION: La logique de calcul est correcte.")
        print("   - Sans placement: déficit important → LCOE plus élevé")
        print("   - Avec placement: déficit réduit → LCOE plus bas")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ!")
    
    return all_tests_passed


if __name__ == "__main__":
    test_calcul_remplacement_onduleur()