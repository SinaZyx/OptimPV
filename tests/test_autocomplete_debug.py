"""Script de test pour déboguer l'autocomplétion d'adresse."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
import logging

# Configurer le logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("="*60)
print("TEST DIRECT API GOUVERNEMENTALE")
print("="*60)

# Test 1: Appel direct à l'API
query = "386 avenue saint basile"
url = "https://api-adresse.data.gouv.fr/search/"
params = {
    'q': query,
    'limit': 5,
    'type': 'housenumber',
    'autocomplete': 1
}

print(f"\nRecherche: '{query}'")
print(f"URL: {url}")
print(f"Params: {params}")

try:
    response = requests.get(url, params=params, timeout=10)
    print(f"\nStatus code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Nombre de résultats: {len(data.get('features', []))}")
        
        for i, feature in enumerate(data.get('features', [])[:3]):
            props = feature.get('properties', {})
            print(f"\nRésultat {i+1}:")
            print(f"  Label: {props.get('label')}")
            print(f"  Score: {props.get('score')}")
            print(f"  Ville: {props.get('city')}")
            print(f"  Code postal: {props.get('postcode')}")
    else:
        print(f"Erreur API: {response.text}")
        
except Exception as e:
    print(f"Erreur: {e}")

# Test 2: Test avec le service
print("\n" + "="*60)
print("TEST AVEC LE SERVICE")
print("="*60)

try:
    from modules.erp_client.services.address_autocomplete import AddressAutocompleteService
    
    service = AddressAutocompleteService()
    results = service.search_addresses(query)
    
    print(f"Nombre de résultats du service: {len(results)}")
    for i, result in enumerate(results[:3]):
        print(f"\nRésultat {i+1}:")
        print(f"  {result}")
        
except Exception as e:
    print(f"Erreur service: {e}")
    import traceback
    traceback.print_exc()