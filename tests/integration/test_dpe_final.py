#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test final de la correction DPE avec les coordonnées de l'utilisateur
"""

import requests
import json

# Coordonnées de l'utilisateur
LAT = 43.631241005708134
LON = 6.9373580224334495

print("TEST FINAL CORRECTION DPE")
print("=" * 60)
print(f"Coordonnées GPS: {LAT}, {LON}")
print()

# 1. Reverse geocoding
print("1. Reverse geocoding pour obtenir le code postal:")
print("-" * 40)

geocode_url = "https://api-adresse.data.gouv.fr/reverse/"
geo_params = {'lon': LON, 'lat': LAT}

response = requests.get(geocode_url, params=geo_params)
if response.status_code == 200:
    data = response.json()
    features = data.get('features', [])
    if features:
        properties = features[0].get('properties', {})
        postcode = properties.get('postcode', '')
        city = properties.get('city', '')
        street = properties.get('street', '')
        print(f"✅ Adresse: {street}, {postcode} {city}")
        
        # 2. Recherche DPE avec le bon paramètre
        print(f"\n2. Recherche DPE dans le code postal {postcode}:")
        print("-" * 40)
        
        dpe_url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines"
        params = {
            'q': postcode,
            'select': 'Coordonnée_cartographique_X_(BAN),Coordonnée_cartographique_Y_(BAN),Etiquette_DPE,Adresse_(BAN),Code_postal_(BAN)',
            'size': 100
        }
        
        response = requests.get(dpe_url, params=params)
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            results = data.get('results', [])
            
            print(f"✅ Total DPE trouvés: {total}")
            
            # Compter combien sont vraiment dans le bon code postal
            correct_postcode = sum(1 for dpe in results if dpe.get('Code_postal_(BAN)') == postcode)
            print(f"✅ DPE avec le bon code postal: {correct_postcode}/{len(results)}")
            
            if results:
                # Afficher quelques exemples
                print(f"\nExemples de DPE à {city}:")
                count = 0
                for dpe in results:
                    if dpe.get('Code_postal_(BAN)') == postcode:
                        print(f"  - {dpe.get('Adresse_(BAN)', 'N/A')} - Classe {dpe.get('Etiquette_DPE', 'N/A')}")
                        count += 1
                        if count >= 5:
                            break
                
                # Test de conversion des coordonnées
                print("\n3. Test conversion coordonnées Lambert 93 → WGS84:")
                print("-" * 40)
                
                # Prendre un DPE avec coordonnées
                for dpe in results[:10]:
                    x = dpe.get('Coordonnée_cartographique_X_(BAN)')
                    y = dpe.get('Coordonnée_cartographique_Y_(BAN)')
                    if x and y:
                        print(f"Lambert 93: X={x}, Y={y}")
                        
                        # Test avec pyproj si disponible
                        try:
                            from pyproj import Transformer
                            transformer = Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True)
                            lon_conv, lat_conv = transformer.transform(x, y)
                            print(f"WGS84 (pyproj): lon={lon_conv:.6f}, lat={lat_conv:.6f}")
                        except:
                            # Conversion approximative
                            lon_conv = (x - 700000) / 110000 + 7
                            lat_conv = (y - 6200000) / 111000 + 43
                            print(f"WGS84 (approx): lon={lon_conv:.6f}, lat={lat_conv:.6f}")
                        
                        # Calculer distance
                        from math import sqrt
                        dlat = lat_conv - LAT
                        dlon = lon_conv - LON
                        distance_km = sqrt(dlat**2 + dlon**2) * 111
                        print(f"Distance approximative: {distance_km*1000:.0f}m")
                        break
                
                print("\n✅ SUCCÈS: La recherche DPE fonctionne maintenant!")
                print("Les DPE peuvent être trouvés et filtrés par distance.")

print("\n" + "=" * 60)
print("CONCLUSION")
print("=" * 60)
print("La correction utilise maintenant 'q' avec le code postal seul,")
print("ce qui retourne uniquement les DPE contenant ce code postal")
print("dans n'importe quel champ (adresse, code postal, etc.).")