#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de recherche DPE par adresse au lieu du code postal
"""

import requests
import json
import math

# Coordonnées de test
LAT = 43.631241005708134
LON = 6.9373580224334495

print("TEST RECHERCHE DPE PAR ADRESSE")
print("=" * 60)
print(f"Coordonnées: {LAT}, {LON}")
print()

# 1. Reverse geocoding pour obtenir l'adresse complète
print("1. Reverse geocoding:")
print("-" * 40)

geocode_url = "https://api-adresse.data.gouv.fr/reverse/"
response = requests.get(geocode_url, params={'lon': LON, 'lat': LAT})
geo_data = response.json()

if geo_data.get('features'):
    props = geo_data['features'][0]['properties']
    street = props.get('street', '')
    housenumber = props.get('housenumber', '')
    postcode = props.get('postcode', '')
    city = props.get('city', '')
    
    print(f"Adresse trouvée:")
    print(f"  Rue: {street}")
    print(f"  Ville: {city} ({postcode})")
    
    # 2. Recherche DPE par différentes méthodes
    print(f"\n2. Test différentes recherches DPE:")
    print("-" * 40)
    
    dpe_url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines"
    
    # Test A: Recherche par nom de rue
    if street:
        print(f"\nA. Recherche par rue '{street}':")
        params = {
            'q': street,
            'size': 20
        }
        response = requests.get(dpe_url, params=params)
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            results = data.get('results', [])
            print(f"   → {total} résultats")
            
            # Afficher quelques résultats
            if results:
                print("   Exemples:")
                for i, dpe in enumerate(results[:3]):
                    print(f"     - {dpe.get('Adresse_(BAN)', 'N/A')}")
    
    # Test B: Recherche par ville
    print(f"\nB. Recherche par ville '{city}':")
    params = {
        'q': city,
        'size': 100
    }
    response = requests.get(dpe_url, params=params)
    if response.status_code == 200:
        data = response.json()
        total = data.get('total', 0)
        print(f"   → {total} résultats")
    
    # Test C: Recherche combinée rue + ville
    print(f"\nC. Recherche combinée '{street} {city}':")
    params = {
        'q': f"{street} {city}",
        'size': 50
    }
    response = requests.get(dpe_url, params=params)
    if response.status_code == 200:
        data = response.json()
        total = data.get('total', 0)
        results = data.get('results', [])
        print(f"   → {total} résultats")
        
        if results:
            # Afficher les DPE qui correspondent vraiment à la zone
            print("\n3. DPE trouvés dans la zone:")
            print("-" * 40)
            
            dpe_in_zone = []
            for dpe in results:
                adresse = dpe.get('Adresse_(BAN)', '')
                if city.lower() in adresse.lower() or postcode in adresse:
                    dpe_in_zone.append(dpe)
            
            print(f"DPE dans {city}: {len(dpe_in_zone)}")
            for i, dpe in enumerate(dpe_in_zone[:5]):
                print(f"  {i+1}. {dpe.get('Adresse_(BAN)', 'N/A')} - Classe {dpe.get('Etiquette_DPE', 'N/A')}")

print("\n" + "=" * 60)
print("CONCLUSION")
print("=" * 60)
print("La recherche par adresse peut être plus précise que par code postal")
print("mais nécessite toujours une conversion des coordonnées pour le filtrage")