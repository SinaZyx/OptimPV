#!/usr/bin/env python3
"""
Diagnostic économique pour comprendre pourquoi l'optimisation LCOE ne converge pas
"""

def diagnostic_petites_maisons():
    """Analyse économique des petites maisons vs gros sites"""
    
    print("🔍 DIAGNOSTIC ÉCONOMIQUE - LCOE NON CONVERGENT")
    print("=" * 55)
    
    # Données du projet actuel (4 petites maisons)
    print("\n📊 PROJET ACTUEL - 4 PETITES MAISONS")
    print("-" * 40)
    
    production_unitaire = 4704.57  # kWh/an/maison
    consommation_unitaire = 4218.76  # kWh/an/maison
    nb_maisons = 4
    capex_total = 65000  # €
    duree_projet = 20  # ans
    
    production_totale = production_unitaire * nb_maisons
    consommation_totale = consommation_unitaire * nb_maisons
    surplus = production_totale - consommation_totale
    
    print(f"Production totale: {production_totale:,.0f} kWh/an")
    print(f"Consommation totale: {consommation_totale:,.0f} kWh/an") 
    print(f"Surplus à vendre: {surplus:,.0f} kWh/an")
    print(f"CAPEX total: {capex_total:,.0f}€")
    
    # Calcul LCOE minimum nécessaire
    production_totale_projet = production_totale * duree_projet
    lcoe_minimum = capex_total / production_totale_projet
    
    print(f"\n💡 ANALYSE ÉCONOMIQUE:")
    print(f"Production sur {duree_projet} ans: {production_totale_projet:,.0f} kWh")
    print(f"LCOE minimum (CAPEX seul): {lcoe_minimum:.3f}€/kWh")
    
    # Avec OPEX estimés
    opex_annuel_estime = capex_total * 0.02  # 2% du CAPEX/an
    opex_total = opex_annuel_estime * duree_projet
    lcoe_avec_opex = (capex_total + opex_total) / production_totale_projet
    
    print(f"OPEX estimé (2%/an): {opex_total:,.0f}€")
    print(f"LCOE avec OPEX: {lcoe_avec_opex:.3f}€/kWh")
    
    # Avec financement
    taux_emprunt = 0.04  # 4%
    ratio_dette = 0.7  # 70% dette
    cout_financement = (capex_total * ratio_dette * taux_emprunt * duree_projet) / 2  # Simplifié
    lcoe_avec_financement = (capex_total + opex_total + cout_financement) / production_totale_projet
    
    print(f"Coût financement estimé: {cout_financement:,.0f}€")
    print(f"LCOE avec financement: {lcoe_avec_financement:.3f}€/kWh")
    
    # Comparaison avec bornes d'optimisation
    print(f"\n⚠️  PROBLÈME IDENTIFIÉ:")
    print(f"LCOE nécessaire: {lcoe_avec_financement:.3f}€/kWh")
    print(f"Borne max optimisation: 0.500€/kWh")
    
    if lcoe_avec_financement > 0.5:
        print(f"❌ PROJET NON VIABLE: LCOE > borne max")
        print(f"   Dépassement: +{(lcoe_avec_financement - 0.5)*1000:.1f} c€/kWh")
    else:
        print(f"✅ PROJET POTENTIELLEMENT VIABLE")
    
    # Simulation gros site
    print(f"\n📊 SIMULATION - AVEC GROS SITE")
    print("-" * 35)
    
    # Ajouter un gros site (exemple: 100kWc)
    production_gros_site = 130000  # kWh/an pour 100kWc
    consommation_gros_site = 80000  # kWh/an (industrie)
    capex_gros_site = 80000  # €/100kWc (économie d'échelle)
    
    production_totale_avec_gros = production_totale + production_gros_site
    capex_total_avec_gros = capex_total + capex_gros_site
    
    production_totale_projet_avec_gros = production_totale_avec_gros * duree_projet
    lcoe_avec_gros = capex_total_avec_gros / production_totale_projet_avec_gros
    
    opex_total_avec_gros = (capex_total_avec_gros * 0.02) * duree_projet
    cout_financement_avec_gros = (capex_total_avec_gros * ratio_dette * taux_emprunt * duree_projet) / 2
    lcoe_final_avec_gros = (capex_total_avec_gros + opex_total_avec_gros + cout_financement_avec_gros) / production_totale_projet_avec_gros
    
    print(f"Production totale: {production_totale_avec_gros:,.0f} kWh/an")
    print(f"CAPEX total: {capex_total_avec_gros:,.0f}€")
    print(f"LCOE final: {lcoe_final_avec_gros:.3f}€/kWh")
    
    if lcoe_final_avec_gros <= 0.5:
        print(f"✅ AVEC GROS SITE: VIABLE")
        print(f"   Marge de sécurité: {(0.5 - lcoe_final_avec_gros)*1000:.1f} c€/kWh")
    else:
        print(f"❌ MÊME AVEC GROS SITE: NON VIABLE")
    
    # Recommandations
    print(f"\n💡 RECOMMANDATIONS:")
    print(f"1. Réduire CAPEX (négociation, subventions)")
    print(f"2. Augmenter taille projet (économies d'échelle)")
    print(f"3. Améliorer financement (taux plus bas)")
    print(f"4. Vérifier paramètres OPEX dans config")
    print(f"5. Ajuster bornes d'optimisation si nécessaire")
    
    return {
        "lcoe_petites_maisons": lcoe_avec_financement,
        "lcoe_avec_gros_site": lcoe_final_avec_gros,
        "viable_petites_seules": lcoe_avec_financement <= 0.5,
        "viable_avec_gros": lcoe_final_avec_gros <= 0.5
    }

if __name__ == "__main__":
    resultats = diagnostic_petites_maisons()
    
    print(f"\n🎯 CONCLUSION:")
    if resultats["viable_petites_seules"]:
        print(f"✅ Les petites maisons seules devraient fonctionner")
    else:
        print(f"❌ Les petites maisons seules ne sont pas viables économiquement")
        print(f"   C'est pourquoi l'optimisation LCOE ne converge pas")
    
    if resultats["viable_avec_gros"]:
        print(f"✅ Avec un gros site, le projet devient viable") 
        print(f"   C'est pourquoi ça marche quand vous ajoutez un gros site")