"""Test rapide pour vérifier que get_total_capacity fonctionne.

Ce test vérifie directement que la méthode get_total_capacity 
a été ajoutée au CapacityService et fonctionne correctement.
"""

import sys
import os
from pathlib import Path

# Ajouter le projet au path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_capacity_service_methods():
    """Teste que toutes les méthodes de CapacityService existent."""
    print("🔍 Test CapacityService methods...")
    
    try:
        from modules.erp_client.services.capacity_service import CapacityService
        
        # Créer une instance
        service = CapacityService()
        
        # Vérifier que les méthodes existent
        required_methods = [
            'get_total_capacity',
            'get_client_capacity', 
            'get_dashboard_stats'
        ]
        
        missing_methods = []
        for method_name in required_methods:
            if hasattr(service, method_name):
                print(f"✅ Méthode {method_name} présente")
            else:
                missing_methods.append(method_name)
                print(f"❌ Méthode {method_name} manquante")
        
        if missing_methods:
            print(f"\n❌ Méthodes manquantes: {missing_methods}")
            return False
        else:
            print(f"\n✅ Toutes les méthodes requises sont présentes!")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_capacity_service_calls():
    """Teste que les méthodes peuvent être appelées sans erreur."""
    print("\n🔍 Test appels CapacityService...")
    
    try:
        from modules.erp_client.services.capacity_service import CapacityService
        
        service = CapacityService()
        
        # Test get_total_capacity
        try:
            total = service.get_total_capacity()
            print(f"✅ get_total_capacity() retourne: {total}")
        except Exception as e:
            print(f"❌ get_total_capacity() erreur: {e}")
            return False
        
        # Test get_client_capacity
        try:
            client_cap = service.get_client_capacity(1)
            print(f"✅ get_client_capacity(1) retourne: {client_cap}")
        except Exception as e:
            print(f"❌ get_client_capacity() erreur: {e}")
            return False
        
        # Test get_dashboard_stats
        try:
            stats = service.get_dashboard_stats()
            print(f"✅ get_dashboard_stats() retourne: {type(stats)}")
        except Exception as e:
            print(f"❌ get_dashboard_stats() erreur: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test d'appel: {e}")
        return False

def main():
    """Fonction principale."""
    print("🧪 TEST RAPIDE CORRECTION CAPACITY SERVICE")
    print("="*50)
    
    # Test 1: Vérifier présence des méthodes
    methods_ok = test_capacity_service_methods()
    
    # Test 2: Vérifier que les méthodes fonctionnent
    calls_ok = test_capacity_service_calls()
    
    # Résultat
    print("\n" + "="*50)
    if methods_ok and calls_ok:
        print("🎉 SUCCESS: Correction CapacityService validée!")
        print("✅ La méthode get_total_capacity fonctionne")
        print("✅ L'erreur AttributeError est corrigée")
    else:
        print("❌ FAILED: Problèmes détectés")
        if not methods_ok:
            print("- Méthodes manquantes")
        if not calls_ok:
            print("- Erreurs d'exécution")
    
    return methods_ok and calls_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)