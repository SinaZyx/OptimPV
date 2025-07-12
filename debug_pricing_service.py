#!/usr/bin/env python3
"""
Script de débogage pour tracer le problème AttributeError get_average_price.

Ce script va:
1. Importer directement le PricingService
2. Vérifier si la méthode existe
3. Créer une instance et tester les méthodes
4. Simuler le chemin d'erreur complet
"""

import sys
import os
import traceback

# Ajouter le répertoire du projet au path
project_root = '/mnt/c/Users/kingc/OptimPV'
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_direct_import():
    """Test d'import direct du PricingService"""
    print("=" * 60)
    print("1. TEST D'IMPORT DIRECT")
    print("=" * 60)
    
    try:
        from modules.erp_client.services.pricing_service import PricingService
        print("✅ Import direct de PricingService réussi")
        
        # Vérifier si la méthode existe dans la classe
        if hasattr(PricingService, 'get_average_price'):
            print("✅ Méthode get_average_price trouvée dans la classe")
        else:
            print("❌ Méthode get_average_price MANQUANTE dans la classe")
            print("Méthodes disponibles:")
            for attr in dir(PricingService):
                if not attr.startswith('_'):
                    print(f"  - {attr}")
            return False
            
        # Créer une instance
        pricing_service = PricingService()
        print("✅ Instance PricingService créée")
        
        # Vérifier si la méthode existe dans l'instance
        if hasattr(pricing_service, 'get_average_price'):
            print("✅ Méthode get_average_price trouvée dans l'instance")
        else:
            print("❌ Méthode get_average_price MANQUANTE dans l'instance")
            print("Méthodes disponibles dans l'instance:")
            for attr in dir(pricing_service):
                if not attr.startswith('_'):
                    print(f"  - {attr}")
            return False
            
        # Tester l'appel de la méthode
        try:
            result = pricing_service.get_average_price()
            print(f"✅ get_average_price() appelée avec succès, résultat: {result}")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de l'appel get_average_price(): {e}")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'import direct: {e}")
        traceback.print_exc()
        return False

def test_erp_module_import():
    """Test d'import via le module ERP"""
    print("\n" + "=" * 60)
    print("2. TEST D'IMPORT VIA MODULE ERP")
    print("=" * 60)
    
    try:
        from modules.erp_client import render_erp_module
        print("✅ Import de render_erp_module réussi")
        
        # Test import des services via le module ERP
        from modules.erp_client.services.pricing_service import PricingService as PS_ERP
        from modules.erp_client.ui.main_interface import initialize_erp_services
        
        print("✅ Import des services ERP réussi")
        
        # Initialiser les services comme dans main_interface
        services = initialize_erp_services()
        print("✅ Services ERP initialisés")
        
        if 'pricing' in services:
            pricing_service = services['pricing']
            print("✅ Service pricing trouvé dans les services")
            
            # Vérifier le type
            print(f"Type du service pricing: {type(pricing_service)}")
            
            # Vérifier si la méthode existe
            if hasattr(pricing_service, 'get_average_price'):
                print("✅ Méthode get_average_price trouvée")
                
                # Tester l'appel
                try:
                    result = pricing_service.get_average_price()
                    print(f"✅ get_average_price() appelée avec succès: {result}")
                    return True
                except Exception as e:
                    print(f"❌ Erreur lors de l'appel: {e}")
                    traceback.print_exc()
                    return False
            else:
                print("❌ Méthode get_average_price MANQUANTE")
                print("Méthodes disponibles:")
                for attr in dir(pricing_service):
                    if not attr.startswith('_'):
                        print(f"  - {attr}")
                return False
        else:
            print("❌ Service pricing MANQUANT dans les services")
            print("Services disponibles:", list(services.keys()))
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test ERP: {e}")
        traceback.print_exc()
        return False

def test_client_list_pro_path():
    """Test du chemin complet client_list_pro"""
    print("\n" + "=" * 60)
    print("3. TEST CHEMIN CLIENT_LIST_PRO")
    print("=" * 60)
    
    try:
        # Simuler le chemin d'erreur complet
        from modules.erp_client.ui.main_interface import initialize_erp_services
        from modules.erp_client.ui.client_list_pro import render_professional_client_list
        
        print("✅ Import des modules UI réussi")
        
        # Initialiser les services
        services = initialize_erp_services()
        print("✅ Services initialisés")
        
        # Extraire les services comme dans render_clients_tab
        client_service = services['client']
        pricing_service = services['pricing']
        capacity_service = services['capacity']
        
        print(f"Types des services:")
        print(f"  - client_service: {type(client_service)}")
        print(f"  - pricing_service: {type(pricing_service)}")
        print(f"  - capacity_service: {type(capacity_service)}")
        
        # Vérifier la méthode get_average_price spécifiquement
        if hasattr(pricing_service, 'get_average_price'):
            print("✅ pricing_service.get_average_price trouvée")
            
            # Tester l'appel exact qui échoue
            try:
                avg_price = pricing_service.get_average_price()
                print(f"✅ get_average_price() réussie: {avg_price}")
                return True
            except AttributeError as e:
                print(f"❌ AttributeError lors de l'appel: {e}")
                print(f"Type de pricing_service: {type(pricing_service)}")
                print(f"Attributs de pricing_service: {[attr for attr in dir(pricing_service) if not attr.startswith('_')]}")
                return False
            except Exception as e:
                print(f"❌ Autre erreur lors de l'appel: {e}")
                traceback.print_exc()
                return False
        else:
            print("❌ pricing_service.get_average_price MANQUANTE")
            print(f"Attributs disponibles: {[attr for attr in dir(pricing_service) if not attr.startswith('_')]}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur dans test client_list_pro: {e}")
        traceback.print_exc()
        return False

def main():
    """Lance tous les tests de débogage"""
    print("DIAGNOSTIC COMPLET DU PROBLÈME AttributeError get_average_price")
    print("=" * 80)
    
    results = []
    
    # Test 1: Import direct
    results.append(test_direct_import())
    
    # Test 2: Import via module ERP
    results.append(test_erp_module_import())
    
    # Test 3: Chemin client_list_pro
    results.append(test_client_list_pro_path())
    
    # Résumé
    print("\n" + "=" * 80)
    print("RÉSUMÉ DES TESTS")
    print("=" * 80)
    
    test_names = [
        "Import direct PricingService",
        "Import via module ERP", 
        "Chemin client_list_pro complet"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"{i+1}. {name}: {status}")
    
    if all(results):
        print("\n🎉 TOUS LES TESTS RÉUSSIS - Le problème pourrait être ailleurs")
    else:
        print("\n⚠️ PROBLÈME DÉTECTÉ - Voir les détails ci-dessus")

if __name__ == "__main__":
    main()