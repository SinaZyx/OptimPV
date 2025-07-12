#!/usr/bin/env python3
"""
Script de debug pour identifier pourquoi l'optimisation LCOE ne fonctionne pas
"""

def debug_optimization_flow():
    """Debug du flux d'optimisation"""
    
    print("🔍 DEBUG OPTIMISATION LCOE - CAPEX DIVISÉ PAR 10")
    print("=" * 55)
    
    # Simuler le problème
    print("\n📊 DONNÉES ACTUELLES (CAPEX ÷ 10)")
    print("-" * 35)
    
    production_totale = 18818  # kWh/an
    capex_reduit = 6500  # € (au lieu de 65,000€)
    duree_projet = 20
    
    lcoe_theorique = capex_reduit / (production_totale * duree_projet)
    print(f"Production: {production_totale:,} kWh/an")
    print(f"CAPEX réduit: {capex_reduit:,}€")  
    print(f"LCOE théorique: {lcoe_theorique:.4f}€/kWh")
    print(f"Bornes optimisation: [0.01€ - 0.80€/kWh]")
    
    if 0.01 <= lcoe_theorique <= 0.80:
        print("✅ LCOE dans les bornes → Devrait converger")
    else:
        print("❌ LCOE hors bornes")
    
    # Causes possibles techniques
    print(f"\n🔍 CAUSES TECHNIQUES POSSIBLES:")
    print("-" * 35)
    
    causes = [
        "1. calculate_financial_indicators() retourne None",
        "2. NPV/TRI calcul échoue (division par zéro)",
        "3. Colonnes manquantes dans monthly_results_df",
        "4. Valeurs NaN dans les flux de trésorerie",
        "5. Erreur dans le fonds de réserve", 
        "6. Problème d'import de modules",
        "7. Configuration corrompue",
        "8. Données sites_data invalides"
    ]
    
    for cause in causes:
        print(f"   {cause}")
    
    # Points de contrôle
    print(f"\n🎯 POINTS DE CONTRÔLE À VÉRIFIER:")
    print("-" * 40)
    
    checks = [
        "A. Logs 'CALC INDICATORS' → Erreur avant optimisation ?",
        "B. Valeur retournée par calculate_financial_indicators",
        "C. Présence de 'npv_projet' dans les résultats", 
        "D. Logs 'SIMULATE_PRICE_DEBUG' → NPV = nan ?",
        "E. Message d'erreur complet dans la console",
        "F. Test avec projet vide (sans fonds de réserve)"
    ]
    
    for i, check in enumerate(checks, 1):
        print(f"   {check}")
    
    return True

def generate_debug_commands():
    """Génère les commandes pour débugger"""
    
    print(f"\n🔧 COMMANDES DE DEBUG À EXÉCUTER:")
    print("-" * 40)
    
    commands = [
        "1. Vérifier les logs complets dans la console",
        "2. Chercher 'ERROR' dans les logs",
        "3. Chercher 'SIMULATE_PRICE_DEBUG' dans les logs", 
        "4. Vérifier si monthly_results_df contient des NaN",
        "5. Tester avec placement_tresorerie_active = False"
    ]
    
    for cmd in commands:
        print(f"   {cmd}")

if __name__ == "__main__":
    debug_optimization_flow()
    generate_debug_commands()
    
    print(f"\n🎯 CONCLUSION:")
    print(f"Avec CAPEX ÷ 10, le problème est 100% TECHNIQUE, pas économique.")
    print(f"Il faut identifier l'erreur exacte dans les logs.")