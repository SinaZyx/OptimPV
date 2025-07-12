#!/usr/bin/env python3
"""
Test minimal pour vérifier si les imports ERP fonctionnent.
"""

import sys
import os

# Ajouter le répertoire du projet au path
project_root = '/mnt/c/Users/kingc/OptimPV'
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_pricing_service_direct():
    """Test d'import direct du PricingService uniquement."""
    print("Test 1: Import direct PricingService")
    try:
        from modules.erp_client.services.pricing_service import PricingService
        print("✅ PricingService importé")
        
        # Vérifier la méthode
        if hasattr(PricingService, 'get_average_price'):
            print("✅ Méthode get_average_price trouvée")
        else:
            print("❌ Méthode get_average_price manquante")
            
        # Créer une instance
        ps = PricingService()
        print("✅ Instance créée")
        
        if hasattr(ps, 'get_average_price'):
            print("✅ Méthode disponible sur l'instance")
            return True
        else:
            print("❌ Méthode non disponible sur l'instance")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_client_map_import():
    """Test d'import client_map avec folium manquant."""
    print("\nTest 2: Import client_map (folium peut manquer)")
    try:
        from modules.erp_client.ui.client_map import render_client_map
        print("✅ client_map importé sans erreur")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    print("TEST MINIMAL DES IMPORTS ERP")
    print("=" * 40)
    
    results = []
    results.append(test_pricing_service_direct())
    results.append(test_client_map_import())
    
    print("\n" + "=" * 40)
    print("RÉSUMÉ:")
    if all(results):
        print("✅ TOUS LES TESTS RÉUSSIS")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")

if __name__ == "__main__":
    main()