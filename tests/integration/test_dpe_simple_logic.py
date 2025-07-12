#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple de la logique DPE sans dépendances
"""

import requests
import json
import math

# Coordonnées de test
LAT = 43.631241005708134
LON = 6.9373580224334495
RADIUS_M = 1000

print("TEST LOGIQUE DPE SIMPLIFIÉE")
print("=" * 60)
print(f"Coordonnées: {LAT}, {LON}")
print(f"Rayon de recherche: {RADIUS_M}m")
print()

# 1. Reverse geocoding
geocode_url = "https://api-adresse.data.gouv.fr/reverse/"
response = requests.get(geocode_url, params={'lon': LON, 'lat': LAT})
geo_data = response.json()
postcode = geo_data['features'][0]['properties']['postcode']
city = geo_data['features'][0]['properties']['city']
print(f"1. Localisation: {city} ({postcode})")

# 2. Recherche DPE
print(f"\n2. Recherche DPE dans {postcode}...")
dpe_url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines"
params = {
    'q': postcode,
    'select': 'Coordonnée_cartographique_X_(BAN),Coordonnée_cartographique_Y_(BAN),Etiquette_DPE,Adresse_(BAN)',
    'size': 1000
}

response = requests.get(dpe_url, params=params)
data = response.json()
results = data.get('results', [])
print(f"   → {len(results)} DPE récupérés")

# 3. Conversion et filtrage
dpe_proches = []
for dpe in results:
    x = dpe.get('Coordonnée_cartographique_X_(BAN)')
    y = dpe.get('Coordonnée_cartographique_Y_(BAN)')
    
    if x and y:
        # Conversion approximative Lambert 93 → WGS84
        # Formule simplifiée pour la région PACA
        lon_dpe = 2.33722917 + x * 0.00000899316 - y * 0.00000000459
        lat_dpe = -5.60811916 + x * 0.00000000473 + y * 0.00000905753
        
        # Calcul distance approximative
        dlat = lat_dpe - LAT
        dlon = lon_dpe - LON
        distance_m = math.sqrt(dlat**2 + dlon**2) * 111000
        
        if distance_m <= RADIUS_M:
            dpe_proches.append({
                'adresse': dpe.get('Adresse_(BAN)', 'N/A'),
                'classe': dpe.get('Etiquette_DPE', 'N/A'),
                'distance_m': distance_m,
                'lat': lat_dpe,
                'lon': lon_dpe
            })

# Trier par distance
dpe_proches.sort(key=lambda x: x['distance_m'])

print(f"\n3. Résultats après filtrage par distance:")
print(f"   → {len(dpe_proches)} DPE dans un rayon de {RADIUS_M}m")

if dpe_proches:
    print(f"\n4. Les 10 DPE les plus proches:")
    for i, dpe in enumerate(dpe_proches[:10]):
        print(f"   {i+1}. {dpe['adresse']}")
        print(f"      Classe: {dpe['classe']}, Distance: {dpe['distance_m']:.0f}m")
        print(f"      Coords: {dpe['lat']:.6f}, {dpe['lon']:.6f}")
else:
    print("\n❌ Aucun DPE trouvé dans le rayon spécifié")
    print("\nDiagnostic:")
    print("- La conversion Lambert 93 → WGS84 nécessite pyproj pour être précise")
    print("- Sans pyproj, la conversion approximative peut être très imprécise")
    print("- Les DPE existent mais sont peut-être mal géolocalisés avec la formule approximative")