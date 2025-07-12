#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple pour comprendre l'API ADEME DPE
"""

import requests
import json

# Coordonnées de test
LAT = 43.631241005708134
LON = 6.9373580224334495

def test_api_parameters():
    """Test différents paramètres de l'API"""
    print("TEST DES PARAMÈTRES API ADEME")
    print("=" * 60)
    
    base_url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines"
    
    # Test 1: Sans paramètres pour voir la structure
    print("\n1. Structure d'un DPE (premier résultat):")
    print("-" * 40)
    
    response = requests.get(base_url, params={'size': 1})
    if response.status_code == 200:
        data = response.json()
        if data.get('results'):
            dpe = data['results'][0]
            # Afficher toutes les clés
            for key in sorted(dpe.keys()):
                if 'lat' in key.lower() or 'lon' in key.lower() or 'geo' in key.lower() or 'adresse' in key.lower():
                    print(f"  {key}: {dpe.get(key, 'N/A')}")
    
    # Test 2: Recherche par code postal
    print("\n2. Test recherche par code postal 06250 (Mougins):")
    print("-" * 40)
    
    params = {
        'code_postal_ban': '06250',
        'size': 5
    }
    
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        total = data.get('total', 0)
        print(f"Total DPE à Mougins (06250): {total}")
        
        if data.get('results'):
            for i, dpe in enumerate(data['results'][:3]):
                print(f"\nDPE {i+1}:")
                print(f"  Adresse: {dpe.get('adresse_ban', 'N/A')}")
                print(f"  Classe: {dpe.get('classe_consommation_energie', 'N/A')}")
                print(f"  Lat/Lon: {dpe.get('latitude', 'N/A')}, {dpe.get('longitude', 'N/A')}")

def test_geospatial_search():
    """Test de la recherche géospatiale"""
    print("\n\n3. TEST RECHERCHE GÉOSPATIALE")
    print("=" * 60)
    
    base_url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines"
    
    # Essayer différents formats de paramètres géospatiaux
    tests = [
        {
            'name': 'Format geo_distance',
            'params': {
                'geo_distance': f'{LAT},{LON},500m',
                'size': 10
            }
        },
        {
            'name': 'Format lat_lon avec _geopoint',
            'params': {
                '_geopoint': f'{LAT},{LON}',
                '_geodistance': '500',
                'size': 10
            }
        },
        {
            'name': 'Format simple lat/lon range',
            'params': {
                'latitude': f'[{LAT-0.005}:{LAT+0.005}]',
                'longitude': f'[{LON-0.005}:{LON+0.005}]',
                'size': 10
            }
        },
        {
            'name': 'Format q avec near',
            'params': {
                'q': f'near({LAT},{LON},500)',
                'size': 10
            }
        }
    ]
    
    for test in tests:
        print(f"\nTest: {test['name']}")
        print(f"Params: {test['params']}")
        print("-" * 40)
        
        try:
            response = requests.get(base_url, params=test['params'])
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                total = data.get('total', 0)
                results = data.get('results', [])
                
                print(f"Total: {total}")
                if results and total < 100000:  # Si on a des résultats filtrés
                    print("✅ Filtrage géospatial fonctionne!")
                    # Afficher le premier résultat
                    dpe = results[0]
                    print(f"Premier DPE:")
                    print(f"  Adresse: {dpe.get('adresse_ban', 'N/A')}")
                    print(f"  Lat/Lon: {dpe.get('latitude', 'N/A')}, {dpe.get('longitude', 'N/A')}")
                elif total > 1000000:
                    print("❌ Pas de filtrage (tous les DPE retournés)")
            else:
                print(f"Erreur: {response.text[:100]}")
                
        except Exception as e:
            print(f"Exception: {e}")

def check_api_documentation():
    """Vérifier la documentation de l'API"""
    print("\n\n4. VÉRIFICATION DE LA DOCUMENTATION API")
    print("=" * 60)
    
    # Essayer d'accéder à la doc
    doc_urls = [
        "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/api-docs.json",
        "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/schema",
        "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants"
    ]
    
    for url in doc_urls:
        print(f"\nTest URL: {url}")
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("✅ Accessible")
                if 'schema' in url:
                    data = response.json()
                    print("Champs géospatiaux trouvés:")
                    for field in data:
                        if any(term in field.get('key', '').lower() for term in ['lat', 'lon', 'geo', 'coord']):
                            print(f"  - {field['key']}: {field.get('type', 'N/A')}")
        except:
            print("❌ Non accessible")

def main():
    test_api_parameters()
    test_geospatial_search()
    check_api_documentation()

if __name__ == "__main__":
    main()