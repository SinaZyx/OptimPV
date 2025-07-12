"""Test direct du CapacityService sans dépendances."""

import sys
import importlib.util
from pathlib import Path

def test_capacity_service_direct():
    """Teste CapacityService en direct."""
    print("🔍 Test direct CapacityService...")
    
    # Charger le module directement
    capacity_path = Path(__file__).parent / "modules" / "erp_client" / "services" / "capacity_service.py"
    
    spec = importlib.util.spec_from_file_location("capacity_service", capacity_path)
    capacity_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(capacity_module)
    
    # Tester la classe
    CapacityService = capacity_module.CapacityService
    
    # Vérifier que les méthodes existent
    methods = [
        'get_total_capacity',
        'get_client_capacity',
        'get_dashboard_stats'
    ]
    
    all_present = True
    for method in methods:
        if hasattr(CapacityService, method):
            print(f"✅ Méthode {method} présente")
        else:
            print(f"❌ Méthode {method} manquante")
            all_present = False
    
    # Vérifier le code source
    import inspect
    if hasattr(CapacityService, 'get_total_capacity'):
        source = inspect.getsource(CapacityService.get_total_capacity)
        if "SELECT COALESCE(SUM(capacite_kwc), 0)" in source:
            print("✅ get_total_capacity contient la bonne requête SQL")
        else:
            print("❌ get_total_capacity requête SQL incorrecte")
            all_present = False
    
    return all_present

def main():
    """Fonction principale."""
    print("🧪 TEST DIRECT CAPACITY SERVICE")
    print("="*40)
    
    success = test_capacity_service_direct()
    
    if success:
        print("\n🎉 SUCCESS: CapacityService est corrigé!")
        print("✅ get_total_capacity est présente et correcte")
        print("✅ L'erreur AttributeError devrait être résolue")
    else:
        print("\n❌ FAILED: Problèmes dans CapacityService")
    
    return success

if __name__ == "__main__":
    main()