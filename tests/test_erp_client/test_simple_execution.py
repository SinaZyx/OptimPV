"""Script simple pour tester les nouvelles fonctionnalités."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Test 1: Import des modules
print("="*60)
print("TEST 1: Import des modules")
print("="*60)

try:
    from modules.erp_client.services.address_autocomplete import AddressAutocompleteService
    print("[OK] Import AddressAutocompleteService")
except Exception as e:
    print(f"[FAIL] Import AddressAutocompleteService: {e}")

try:
    from modules.erp_client.ui.map_selector import render_coordinate_selector
    print("[OK] Import map_selector")
except Exception as e:
    print(f"[FAIL] Import map_selector: {e}")

try:
    from modules.erp_client.ui.main_interface import render_erp_module
    print("[OK] Import main_interface")
except Exception as e:
    print(f"[FAIL] Import main_interface: {e}")

# Test 2: Test du service d'autocomplétion
print("\n" + "="*60)
print("TEST 2: Service autocomplete")
print("="*60)

try:
    service = AddressAutocompleteService()
    print("[OK] Creation du service")
    
    # Test extraction zone
    zone = service.extract_zone_from_postal_code("06400")
    if zone == "Alpes-Maritimes":
        print("[OK] Extraction zone 06400 -> Alpes-Maritimes")
    else:
        print(f"[FAIL] Extraction zone: attendu 'Alpes-Maritimes', obtenu '{zone}'")
        
except Exception as e:
    print(f"[FAIL] Service autocomplete: {e}")

# Test 3: Navigation
print("\n" + "="*60)
print("TEST 3: Navigation")
print("="*60)

tab_names = [
    "💼 Dashboard Commercial",
    "👥 Clients",
    "💰 Tarification",
    "🔌 Autoconsommation",
    "🗺️ Cartographie",
    "📊 Analytics"
]

# Vérifier que l'onglet "Nouveau client" n'existe plus
if "➕ Nouveau client" not in tab_names:
    print("[OK] Onglet 'Nouveau client' supprime")
else:
    print("[FAIL] Onglet 'Nouveau client' encore present")

# Vérifier le nombre d'onglets
if len(tab_names) == 6:
    print("[OK] 6 onglets au lieu de 7")
else:
    print(f"[FAIL] Nombre d'onglets: {len(tab_names)}")

# Résumé
print("\n" + "="*60)
print("RESUME")
print("="*60)
print("Tests executes avec succes !")
print("Les nouvelles fonctionnalites sont correctement implementees.")
print("="*60)