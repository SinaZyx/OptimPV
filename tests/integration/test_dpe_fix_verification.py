#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de vérification de la correction pour la recherche DPE
"""

import requests
import json

# Coordonnées de test fournies
LAT = 43.631241005708134
LON = 6.9373580224334495

def test_corrected_api():
    """Test de l'API avec les bons paramètres"""
    print("TEST DE LA CORRECTION API DPE")
    print("=" * 60)
    print(f"Coordonnées: {LAT}, {LON}")
    print()
    
    # 1. D'abord obtenir le code postal
    print("1. Reverse geocoding pour obtenir le code postal:")
    print("-" * 40)
    
    geocode_url = "https://api-adresse.data.gouv.fr/reverse/"
    geo_params = {'lon': LON, 'lat': LAT}
    
    try:
        response = requests.get(geocode_url, params=geo_params)
        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])
            if features:
                properties = features[0].get('properties', {})
                postcode = properties.get('postcode', '')
                city = properties.get('city', '')
                print(f"✅ Localisation: {city} ({postcode})")
                
                # 2. Rechercher les DPE avec le code postal
                print(f"\n2. Recherche DPE dans le code postal {postcode}:")
                print("-" * 40)
                
                dpe_url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines"
                params = {
                    'Code_postal_(BAN)': postcode,
                    'select': 'Etiquette_DPE,Adresse_(BAN),Coordonnée_cartographique_X_(BAN),Coordonnée_cartographique_Y_(BAN)',
                    'size': 100
                }
                
                response = requests.get(dpe_url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    total = data.get('total', 0)
                    results = data.get('results', [])
                    
                    print(f"✅ Total DPE dans {city}: {total}")
                    
                    if results:
                        print(f"\nExemples de DPE trouvés:")
                        for i, dpe in enumerate(results[:5]):
                            print(f"  {i+1}. {dpe.get('Adresse_(BAN)', 'N/A')} - Classe {dpe.get('Etiquette_DPE', 'N/A')}")
                            
                        # Vérifier si on a des coordonnées
                        with_coords = sum(1 for dpe in results if dpe.get('Coordonnée_cartographique_X_(BAN)'))
                        print(f"\n{with_coords}/{len(results)} DPE ont des coordonnées")
                        
                        if with_coords > 0:
                            print("\n✅ SUCCÈS: Les DPE peuvent être récupérés et géolocalisés!")
                            print("La correction devrait fonctionner maintenant.")
                        else:
                            print("⚠️ Les DPE n'ont pas de coordonnées")
                            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def verify_column_names():
    """Vérifier les noms exacts des colonnes"""
    print("\n\n3. VÉRIFICATION DES NOMS DE COLONNES")
    print("=" * 60)
    
    url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines"
    response = requests.get(url, params={'size': 1})
    
    if response.status_code == 200:
        data = response.json()
        if data.get('results'):
            dpe = data['results'][0]
            
            print("Colonnes importantes trouvées:")
            important_keys = [
                'Etiquette_DPE', 'Etiquette_GES', 'Consommation_énergétique',
                'Adresse_(BAN)', 'Code_postal_(BAN)', 'Libellé_commune_(BAN)',
                'Coordonnée_cartographique_X_(BAN)', 'Coordonnée_cartographique_Y_(BAN)',
                'Type_bâtiment', 'Surface_habitable_logement'
            ]
            
            for key in important_keys:
                if key in dpe:
                    value = dpe[key]
                    if value:
                        print(f"  ✅ {key}: {str(value)[:50]}")
                    else:
                        print(f"  ⚠️  {key}: (vide)")
                else:
                    print(f"  ❌ {key}: NON TROUVÉ")

def main():
    test_corrected_api()
    verify_column_names()
    
    print("\n\n" + "=" * 60)
    print("RÉSUMÉ DE LA CORRECTION")
    print("=" * 60)
    print()
    print("Problème identifié:")
    print("- L'API ADEME n'accepte pas de recherche géospatiale directe")
    print("- Les coordonnées sont en Lambert 93, pas en lat/lon")
    print()
    print("Solution implémentée:")
    print("1. Reverse geocoding pour obtenir le code postal")
    print("2. Recherche par code postal")
    print("3. Conversion Lambert 93 → WGS84 (lat/lon)")
    print("4. Filtrage par distance côté client")
    print()
    print("✅ Cette approche devrait maintenant fonctionner!")

if __name__ == "__main__":
    main()