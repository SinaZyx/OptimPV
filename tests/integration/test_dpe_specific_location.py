#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test spécifique pour les coordonnées GPS fournies par l'utilisateur
Vérifie pourquoi aucun DPE n'est trouvé alors qu'il devrait y en avoir
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json

# Coordonnées fournies par l'utilisateur
TEST_LAT = 43.631241005708134
TEST_LON = 6.9373580224334495

def test_manual_api_call():
    """Test direct de l'API ADEME DPE"""
    print("=" * 60)
    print("TEST DIRECT API ADEME DPE")
    print(f"Coordonnées: {TEST_LAT}, {TEST_LON}")
    print("=" * 60)
    print()
    
    # URL de l'API ADEME
    url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines"
    
    # Test 1: Recherche avec différents rayons
    for radius in [100, 200, 500, 1000]:
        print(f"\nTest avec rayon de {radius}m:")
        print("-" * 40)
        
        params = {
            'lat_lon': f'POINT({TEST_LON} {TEST_LAT})',
            'lat_lon_distance': f'{radius}m',
            'size': 10  # Limiter pour le test
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                total = data.get('total', 0)
                results = data.get('results', [])
                
                print(f"Total DPE trouvés: {total}")
                
                if results:
                    print(f"Premiers résultats:")
                    for i, dpe in enumerate(results[:3]):
                        print(f"  DPE {i+1}:")
                        print(f"    - Adresse: {dpe.get('adresse_ban', 'N/A')}")
                        print(f"    - Classe: {dpe.get('classe_consommation_energie', 'N/A')}")
                        print(f"    - Type: {dpe.get('type_batiment', 'N/A')}")
                        if 'latitude' in dpe and 'longitude' in dpe:
                            print(f"    - Coords: {dpe['latitude']}, {dpe['longitude']}")
            else:
                print(f"Erreur HTTP: {response.text[:200]}")
                
        except Exception as e:
            print(f"Erreur: {e}")

def test_alternative_search():
    """Test avec des paramètres alternatifs"""
    print("\n\n" + "=" * 60)
    print("TEST AVEC PARAMÈTRES ALTERNATIFS")
    print("=" * 60)
    
    url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines"
    
    # Test 2: Recherche par bounding box
    print("\nTest par bounding box:")
    print("-" * 40)
    
    # Créer une bounding box autour du point (environ 500m)
    delta = 0.005  # Environ 500m
    bbox = {
        'lat_min': TEST_LAT - delta,
        'lat_max': TEST_LAT + delta,
        'lon_min': TEST_LON - delta,
        'lon_max': TEST_LON + delta
    }
    
    params = {
        'latitude': f'[{bbox["lat_min"]}:{bbox["lat_max"]}]',
        'longitude': f'[{bbox["lon_min"]}:{bbox["lon_max"]}]',
        'size': 100
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            print(f"Total DPE dans la bounding box: {total}")
            
            if total > 0:
                print("✅ DPE trouvés avec la recherche par bounding box!")
    except Exception as e:
        print(f"Erreur: {e}")

def test_commune_search():
    """Test de recherche par commune"""
    print("\n\n" + "=" * 60)
    print("TEST PAR COMMUNE")
    print("=" * 60)
    
    # D'abord, identifier la commune via reverse geocoding
    geocode_url = f"https://api-adresse.data.gouv.fr/reverse/"
    params = {
        'lon': TEST_LON,
        'lat': TEST_LAT
    }
    
    try:
        response = requests.get(geocode_url, params=params)
        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])
            if features:
                properties = features[0].get('properties', {})
                city = properties.get('city', '')
                postcode = properties.get('postcode', '')
                print(f"Commune identifiée: {city} ({postcode})")
                
                # Rechercher les DPE de cette commune
                dpe_url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines"
                params = {
                    'code_postal_ban': postcode,
                    'size': 10
                }
                
                response = requests.get(dpe_url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    total = data.get('total', 0)
                    print(f"Total DPE dans la commune {city}: {total}")
                    
    except Exception as e:
        print(f"Erreur: {e}")

def analyze_api_structure():
    """Analyse la structure de l'API pour comprendre les champs disponibles"""
    print("\n\n" + "=" * 60)
    print("ANALYSE DE LA STRUCTURE API")
    print("=" * 60)
    
    url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/schema"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            schema = response.json()
            
            print("\nChamps géographiques disponibles:")
            geo_fields = [field for field in schema if 'lat' in field['key'].lower() or 'lon' in field['key'].lower() or 'geo' in field['key'].lower()]
            
            for field in geo_fields:
                print(f"  - {field['key']}: {field.get('description', 'N/A')}")
                
    except Exception as e:
        print(f"Erreur: {e}")

def test_our_implementation():
    """Test notre implémentation actuelle"""
    print("\n\n" + "=" * 60)
    print("TEST DE NOTRE IMPLÉMENTATION")
    print("=" * 60)
    
    try:
        from modules.prospect_mapping.core.data_handler import get_all_dpe_around_point
        
        for radius in [100, 500, 1000]:
            print(f"\nTest get_all_dpe_around_point avec rayon {radius}m:")
            df_dpe = get_all_dpe_around_point(TEST_LAT, TEST_LON, radius)
            print(f"Nombre de DPE trouvés: {len(df_dpe)}")
            
            if len(df_dpe) > 0:
                print("Colonnes disponibles:", list(df_dpe.columns))
                print("\nPremiers DPE:")
                print(df_dpe[['adresse', 'dpe_classe_energie', 'distance_m']].head(3))
                
    except Exception as e:
        print(f"Erreur lors du test de notre implémentation: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Exécution de tous les tests"""
    print("\n" + "=" * 60)
    print("DIAGNOSTIC RECHERCHE DPE")
    print(f"Point GPS: {TEST_LAT}, {TEST_LON}")
    print("=" * 60 + "\n")
    
    test_manual_api_call()
    test_alternative_search()
    test_commune_search()
    analyze_api_structure()
    test_our_implementation()
    
    print("\n" + "=" * 60)
    print("FIN DU DIAGNOSTIC")
    print("=" * 60)

if __name__ == "__main__":
    main()