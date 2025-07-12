#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test pour vérifier si le cache Streamlit bloque les résultats
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Coordonnées de test
LAT = 43.631241005708134
LON = 6.9373580224334495

print("TEST CACHE STREAMLIT DPE")
print("=" * 60)

# Essayer de vider le cache
try:
    import streamlit as st
    # Vider le cache de la fonction
    from modules.prospect_mapping.core.data_handler import get_all_dpe_around_point
    if hasattr(get_all_dpe_around_point, 'clear'):
        get_all_dpe_around_point.clear()
        print("✅ Cache Streamlit vidé")
except:
    print("⚠️ Streamlit non disponible ou pas de cache")

# Test direct sans Streamlit
print("\nTest direct de la fonction get_all_dpe_around_point:")
print("-" * 40)

try:
    # Import direct sans cache
    import modules.prospect_mapping.core.data_handler as dh
    
    # Forcer le rechargement du module
    import importlib
    importlib.reload(dh)
    
    # Appeler directement la fonction interne si elle existe
    # ou créer une version sans cache
    import pandas as pd
    import requests
    import numpy as np
    
    # Test direct de l'API
    print(f"\n1. Test direct API pour {LAT}, {LON}:")
    
    # Reverse geocoding
    geocode_url = "https://api-adresse.data.gouv.fr/reverse/"
    geo_response = requests.get(geocode_url, params={'lon': LON, 'lat': LAT})
    geo_data = geo_response.json()
    
    if geo_data.get('features'):
        postcode = geo_data['features'][0]['properties']['postcode']
        city = geo_data['features'][0]['properties']['city']
        print(f"   Localisation: {city} ({postcode})")
        
        # Requête DPE
        dpe_url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines"
        params = {
            'q': postcode,
            'select': 'Etiquette_DPE,Adresse_(BAN)',
            'size': 10
        }
        
        response = requests.get(dpe_url, params=params)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"   → {len(results)} DPE trouvés")
            
            if results:
                print("\n   Exemples:")
                for i, dpe in enumerate(results[:3]):
                    print(f"     {i+1}. {dpe.get('Adresse_(BAN)', 'N/A')} - Classe {dpe.get('Etiquette_DPE', 'N/A')}")
    
    # Test de la fonction complète
    print(f"\n2. Test fonction get_all_dpe_around_point:")
    df = dh.get_all_dpe_around_point(LAT, LON, 500)
    print(f"   → Retourne un DataFrame avec {len(df)} lignes")
    
    if len(df) > 0:
        print(f"   → Colonnes: {list(df.columns)}")
        print("\n✅ La fonction fonctionne correctement!")
    else:
        print("\n❌ La fonction retourne un DataFrame vide")
        
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("RECOMMANDATIONS")
print("=" * 60)
print("1. Vider le cache Streamlit dans l'interface")
print("2. Vérifier les logs de l'application")
print("3. S'assurer que pandas est installé dans l'environnement")