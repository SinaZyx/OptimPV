#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Version standalone du data_handler qui fonctionne sans Streamlit.
Pour les tests et le débogage.
"""

import logging
import requests
from typing import Optional, Dict
import warnings

warnings.filterwarnings('ignore')

# Configuration
CONFIG = {
    'URLS': {
        'ADRESSE_API': 'https://data.enedis.fr/api/explore/v2.1/catalog/datasets/consommation-annuelle-residentielle-par-adresse/records',
        'GEO_API': 'https://geo.api.gouv.fr/communes'
    },
    'DEPARTEMENT': '06',
    'SEUIL_CONSO_DEFAULT': 7.0,
}

# Cache simple en mémoire (remplace @st.cache_data)
_data_cache = {}
_coords_cache = {}

logger = logging.getLogger(__name__)

def load_and_process_data(use_cache=True):
    """
    Télécharge et traite les données Enedis pour le département 06.
    Version standalone qui fonctionne sans Streamlit.
    
    Returns:
        list: Liste de dictionnaires avec les données traitées
    """
    cache_key = f"enedis_data_{CONFIG['DEPARTEMENT']}"
    
    if use_cache and cache_key in _data_cache:
        print("📋 Utilisation des données en cache")
        return _data_cache[cache_key]
    
    print("📡 Téléchargement des données Enedis pour le département 06...")
    
    # 1. Récupérer les données de consommation Enedis
    consumption_data = _fetch_enedis_data()
    
    # 2. Récupérer les coordonnées des communes
    commune_coords = _fetch_commune_coordinates()
    
    # 3. Fusionner les données
    merged_data = _merge_consumption_and_coordinates(consumption_data, commune_coords)
    
    # 4. Traitement final
    processed_data = _process_merged_data(merged_data)
    
    if use_cache:
        _data_cache[cache_key] = processed_data
    
    print(f"✅ Données traitées : {len(processed_data)} enregistrements avec géolocalisation")
    return processed_data

def _fetch_enedis_data():
    """Récupère les données de consommation depuis l'API Enedis."""
    url = CONFIG['URLS']['ADRESSE_API']
    all_data = []
    offset = 0
    limit = 100  # Limite maximale de l'API Enedis
    
    while True:
        print(f"📡 Téléchargement Enedis batch offset={offset}")
        
        params = {
            'limit': limit,
            'offset': offset,
            'where': f'code_departement="{CONFIG["DEPARTEMENT"]}"'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                print("📄 Fin des données atteinte")
                break
            
            all_data.extend(results)
            print(f"✅ Récupéré {len(results)} enregistrements Enedis (total: {len(all_data)})")
            
            # Si on a moins de résultats que demandé, on a atteint la fin
            if len(results) < limit:
                break
                
            offset += limit
            
            # Limite de sécurité pour les tests (500 enregistrements max)
            if offset > 500:
                print("⚠️ Limite de test atteinte")
                break
                
        except Exception as e:
            print(f"❌ Erreur lors du téléchargement Enedis : {e}")
            break
    
    if not all_data:
        raise RuntimeError("Aucune donnée Enedis trouvée pour le département 06")
    
    print(f"📊 Total données Enedis récupérées : {len(all_data)} enregistrements")
    return all_data

def _fetch_commune_coordinates():
    """Récupère les coordonnées des communes du département 06 via l'API Géo."""
    cache_key = f"coords_{CONFIG['DEPARTEMENT']}"
    
    if cache_key in _coords_cache:
        print("🗺️ Utilisation des coordonnées en cache")
        return _coords_cache[cache_key]
    
    print("🗺️ Récupération des coordonnées des communes du département 06...")
    
    url = CONFIG['URLS']['GEO_API']
    
    try:
        params = {
            'codeDepartement': CONFIG['DEPARTEMENT'],
            'fields': 'nom,code,centre',
            'format': 'json'
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        communes_data = response.json()
        
        # Créer le dictionnaire de mapping
        commune_coords = {}
        for commune in communes_data:
            code = commune.get('code')
            nom = commune.get('nom')
            centre = commune.get('centre', {})
            
            if code and centre and 'coordinates' in centre:
                longitude, latitude = centre['coordinates']
                commune_coords[code] = {
                    'latitude': latitude,
                    'longitude': longitude,
                    'nom_commune_geo': nom
                }
        
        print(f"✅ Coordonnées récupérées pour {len(commune_coords)} communes")
        _coords_cache[cache_key] = commune_coords
        return commune_coords
        
    except Exception as e:
        print(f"❌ Erreur lors du géocodage des communes : {e}")
        return {}

def _merge_consumption_and_coordinates(consumption_data, commune_coords):
    """Fusionne les données de consommation avec les coordonnées des communes."""
    print("🔗 Fusion des données de consommation et coordonnées...")
    
    merged_data = []
    geocoded_count = 0
    
    for record in consumption_data:
        code_commune = record.get('code_commune')
        coords = commune_coords.get(code_commune, {})
        
        # Créer un nouvel enregistrement fusionné
        merged_record = record.copy()
        merged_record.update(coords)
        
        if coords:
            geocoded_count += 1
        
        merged_data.append(merged_record)
    
    total_records = len(consumption_data)
    geocoding_rate = (geocoded_count / total_records * 100) if total_records > 0 else 0
    
    print(f"📍 Géocodage : {geocoded_count}/{total_records} enregistrements ({geocoding_rate:.1f}%)")
    
    return merged_data

def _process_merged_data(merged_data):
    """Traite les données fusionnées pour créer une liste propre."""
    print("🔧 Traitement des données fusionnées...")
    
    processed_data = []
    
    for record in merged_data:
        # Vérifier que l'enregistrement a les données nécessaires
        if not record.get('latitude') or not record.get('longitude'):
            continue
            
        if not record.get('consommation_annuelle_totale_de_l_adresse_mwh'):
            continue
        
        # Créer l'enregistrement traité
        processed_record = record.copy()
        
        # Convertir MWh en kWh
        mwh = record.get('consommation_annuelle_totale_de_l_adresse_mwh', 0)
        processed_record['consommation_kwh'] = mwh * 1000
        
        # Validation des coordonnées (département 06)
        lat = processed_record['latitude']
        lon = processed_record['longitude']
        
        if not (43 <= lat <= 44 and 6 <= lon <= 8):
            continue
        
        # Ajouter une dispersion aléatoire pour éviter la superposition
        import random
        random.seed(42)  # Pour la reproductibilité
        
        dispersion = 0.01  # ±0.01 degré (environ 1km)
        processed_record['latitude'] += random.uniform(-dispersion, dispersion)
        processed_record['longitude'] += random.uniform(-dispersion, dispersion)
        
        # Nom de commune pour l'affichage
        processed_record['nom_commune_display'] = (
            record.get('nom_commune_geo') or record.get('nom_commune', 'Inconnue')
        )
        
        processed_data.append(processed_record)
    
    print(f"✅ Données finalement traitées : {len(processed_data)} enregistrements valides")
    return processed_data

def get_unique_communes(data):
    """Retourne la liste unique des communes présentes dans les données."""
    communes = set()
    for record in data:
        commune = record.get('nom_commune_display') or record.get('nom_commune')
        if commune:
            communes.add(commune)
    return sorted(list(communes))

def filter_data_by_consumption(data, min_consumption_kwh):
    """Filtre les données par seuil de consommation."""
    return [record for record in data if record.get('consommation_kwh', 0) >= min_consumption_kwh]

def filter_data_by_communes(data, selected_communes):
    """Filtre les données par communes sélectionnées."""
    if not selected_communes:
        return data.copy()
    
    return [
        record for record in data 
        if record.get('nom_commune_display') in selected_communes or 
           record.get('nom_commune') in selected_communes
    ]

def test_complete_pipeline():
    """Test du pipeline complet."""
    print("🚀 Test du pipeline complet")
    print("=" * 50)
    
    try:
        # 1. Chargement des données
        data = load_and_process_data()
        print(f"✅ Pipeline réussi: {len(data)} enregistrements")
        
        # 2. Test des fonctions de filtrage
        communes = get_unique_communes(data)
        print(f"📋 {len(communes)} communes trouvées")
        
        # 3. Test du filtrage par consommation
        high_consumption = filter_data_by_consumption(data, 20000)  # > 20 MWh
        print(f"⚡ {len(high_consumption)} prospects haute consommation (>20 MWh)")
        
        # 4. Afficher un échantillon
        if data:
            sample = data[0]
            print(f"\n📄 Échantillon de données:")
            print(f"  Commune: {sample.get('nom_commune_display')}")
            print(f"  Consommation: {sample.get('consommation_kwh'):.0f} kWh")
            print(f"  Coordonnées: {sample.get('latitude'):.4f}, {sample.get('longitude'):.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans le pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(level=logging.INFO)
    
    # Lancer le test complet
    success = test_complete_pipeline()
    
    if success:
        print("\n🎉 Le module de cartographie fonctionne parfaitement !")
        print("Pour l'utiliser avec Streamlit, installez les dépendances:")
        print("pip install streamlit pandas numpy pydeck")
    else:
        print("\n❌ Des problèmes ont été détectés dans le module.")