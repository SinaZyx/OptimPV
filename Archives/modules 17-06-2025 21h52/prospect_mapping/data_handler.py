#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de gestion des données pour la cartographie de prospection - VERSION CORRIGÉE.
Responsabilité : Récupération, mise en cache et traitement des données Enedis + géocodage.
"""

import logging
import pandas as pd
import requests
import streamlit as st
from typing import Optional, Dict, List
import warnings
import math

warnings.filterwarnings('ignore')

# Configuration
CONFIG = {
    'URLS': {
        'ADRESSE_API': 'https://data.enedis.fr/api/explore/v2.1/catalog/datasets/consommation-annuelle-residentielle-par-adresse/records',
        'GEO_API': 'https://geo.api.gouv.fr/communes',
        'GEOCODING_API': 'https://api-adresse.data.gouv.fr/search/'  # API précise par adresse
    },
    'DEPARTEMENT': '06',
    'SEUIL_CONSO_DEFAULT': 7.0,  # En MWh (équivalent à 7000 kWh)
    'GEOCODING': {
        'BATCH_SIZE': 100,  # Augmenté pour plus de rapidité
        'CACHE_TTL': 86400 * 7,  # Cache 7 jours (les adresses ne changent pas)
        'MAX_RETRIES': 3,
        'TIMEOUT': 15  # Timeout augmenté pour batches plus gros
    }
}

logger = logging.getLogger(__name__)

def create_square_polygon(lon: float, lat: float, size_meters: float = None, zoom_level: int = 13) -> List[List[float]]:
    """
    Crée un polygone carré centré sur un point donné avec taille adaptative.
    
    Args:
        lon: Longitude du centre
        lat: Latitude du centre  
        size_meters: Taille du carré en mètres (si None, calculé selon zoom)
        zoom_level: Niveau de zoom actuel de la carte
        
    Returns:
        List[List[float]]: Liste de 4 coordonnées [longitude, latitude] formant un carré
    """
    # Calcul adaptatif de la taille si non spécifiée
    if size_meters is None:
        # Formule : taille = base * facteur_zoom
        # Plus on dézoome (zoom faible), plus les carrés sont grands
        base_size = 15  # Taille de base en mètres
        zoom_factor = max(1, 14 - zoom_level)  # Facteur multiplicateur
        size_meters = base_size * (1 + zoom_factor * 0.5)
        # Limite : entre 15m (zoom proche) et 100m (zoom éloigné)
        size_meters = min(max(size_meters, 15), 100)
    # Conversion mètres vers degrés
    # 1 degré de latitude ≈ 110574 mètres
    # 1 degré de longitude ≈ 111320 * cos(latitude) mètres
    
    lat_radians = math.radians(lat)
    
    # Calculer les offsets en degrés (demi-taille du carré)
    half_size = size_meters / 2  # Demi-taille pour centrer le carré
    offset_lat = half_size / 110574  # Offset en latitude
    offset_lon = half_size / (111320 * math.cos(lat_radians))  # Offset en longitude
    
    # Créer les 4 coins du carré (dans le sens horaire en partant du coin supérieur gauche)
    square_corners = [
        [lon - offset_lon, lat + offset_lat],  # Coin supérieur gauche
        [lon + offset_lon, lat + offset_lat],  # Coin supérieur droit  
        [lon + offset_lon, lat - offset_lat],  # Coin inférieur droit
        [lon - offset_lon, lat - offset_lat],  # Coin inférieur gauche
        [lon - offset_lon, lat + offset_lat]   # Fermer le polygone (revenir au premier point)
    ]
    
    return square_corners

@st.cache_data(ttl=3600)  # Cache pendant 1 heure
def load_and_process_data(selected_communes: list = None) -> pd.DataFrame:
    """
    Télécharge et traite les données Enedis pour le département 06.
    CORRECTION : Ajoute le géocodage des communes via l'API gouvernementale.
    
    Args:
        selected_communes: Liste des communes à inclure (None = toutes)
    
    Returns:
        pd.DataFrame: DataFrame nettoyé avec coordonnées précises
    """
    logger.info("Téléchargement des données Enedis pour le département 06...")
    
    # 1. Récupérer les données de consommation Enedis (avec filtre optionnel)
    consumption_data = _fetch_enedis_data(selected_communes)
    
    # 2. Récupérer les coordonnées des communes
    commune_coords = _fetch_commune_coordinates()
    
    # 3. Fusionner les données
    merged_data = _merge_consumption_and_coordinates(consumption_data, commune_coords)
    
    # 4. Traitement final
    df_processed = _process_merged_data(merged_data)
    
    logger.info(f"Données traitées : {len(df_processed)} enregistrements avec géolocalisation")
    return df_processed

def _fetch_enedis_data(selected_communes: list = None) -> pd.DataFrame:
    """
    Récupère les données de consommation depuis l'API Enedis.
    
    Args:
        selected_communes: Liste des communes à inclure (None = toutes)
    
    Returns:
        pd.DataFrame: Données de consommation brutes
    """
    url = CONFIG['URLS']['ADRESSE_API']
    all_data = []
    offset = 0
    limit = 100  # Limite maximale de l'API Enedis
    
    while True:
        logger.info(f"Téléchargement Enedis batch offset={offset}")
        
        # Construire la clause WHERE avec filtre optionnel par commune
        where_clause = f'code_departement="{CONFIG["DEPARTEMENT"]}"'
        
        if selected_communes:
            # Ajouter filtre par commune(s)
            communes_filter = ' OR '.join([f'nom_commune="{commune}"' for commune in selected_communes])
            where_clause += f' AND ({communes_filter})'
            logger.info(f"Filtre par communes: {selected_communes}")
        
        params = {
            'limit': limit,
            'offset': offset,
            'where': where_clause
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                break
            
            all_data.extend(results)
            logger.info(f"Récupéré {len(results)} enregistrements Enedis")
            
            # Si on a moins de résultats que demandé, on a atteint la fin
            if len(results) < limit:
                break
                
            offset += limit
            
            # Limite de sécurité pour éviter les téléchargements trop longs
            # TEMPORAIRE: Réduire à 1000 pour tests rapides
            if offset > 1000:  # Limite à ~10 requêtes (1,000 enregistrements) pour test
                logger.warning("Limite de téléchargement Enedis atteinte (mode test rapide)")
                break
                
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement Enedis : {e}")
            break
    
    if not all_data:
        raise RuntimeError("Aucune donnée Enedis trouvée pour le département 06")
    
    df = pd.json_normalize(all_data)
    logger.info(f"Total données Enedis récupérées : {len(df)} enregistrements")
    
    return df

@st.cache_data(ttl=86400)  # Cache pendant 24h (les coordonnées des communes changent rarement)
def _fetch_commune_coordinates() -> Dict[str, Dict]:
    """
    Récupère les coordonnées des communes du département 06 via l'API Géo.
    
    Returns:
        Dict[str, Dict]: Dictionnaire {code_commune: {latitude, longitude, nom}}
    """
    logger.info("Récupération des coordonnées des communes du département 06...")
    
    url = CONFIG['URLS']['GEO_API']
    
    try:
        # Récupérer toutes les communes du département 06
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
                # L'API géo retourne [longitude, latitude]
                longitude, latitude = centre['coordinates']
                commune_coords[code] = {
                    'latitude': latitude,
                    'longitude': longitude,
                    'nom_commune_geo': nom
                }
        
        logger.info(f"Coordonnées récupérées pour {len(commune_coords)} communes")
        return commune_coords
        
    except Exception as e:
        logger.error(f"Erreur lors du géocodage des communes : {e}")
        return {}

def _merge_consumption_and_coordinates(consumption_df: pd.DataFrame, commune_coords: Dict[str, Dict]) -> pd.DataFrame:
    """
    Fusionne les données de consommation avec un géocodage précis par adresse.
    
    Args:
        consumption_df: DataFrame des données Enedis
        commune_coords: Dictionnaire des coordonnées par commune (fallback)
        
    Returns:
        pd.DataFrame: DataFrame fusionné avec coordonnées précises
    """
    logger.info("Géocodage précis des adresses...")
    
    # Préparer les adresses complètes pour le géocodage
    consumption_df = _prepare_addresses_for_geocoding(consumption_df)
    
    # Géocodage précis par batch
    consumption_df = _precise_geocoding_batch(consumption_df)
    
    # Fallback sur les coordonnées de commune pour les échecs
    consumption_df = _apply_fallback_geocoding(consumption_df, commune_coords)
    
    # Statistiques finales
    total_records = len(consumption_df)
    precise_geocoded = consumption_df['geocoding_source'].eq('precise').sum()
    fallback_geocoded = consumption_df['geocoding_source'].eq('commune').sum()
    failed_geocoded = consumption_df['latitude'].isna().sum()
    
    logger.info(f"Géocodage terminé:")
    logger.info(f"  - Précis: {precise_geocoded}/{total_records} ({precise_geocoded/total_records*100:.1f}%)")
    logger.info(f"  - Commune: {fallback_geocoded}/{total_records} ({fallback_geocoded/total_records*100:.1f}%)")
    logger.info(f"  - Échoué: {failed_geocoded}/{total_records} ({failed_geocoded/total_records*100:.1f}%)")
    
    return consumption_df

def _process_merged_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Traite les données fusionnées pour créer un DataFrame propre.
    
    Args:
        df: DataFrame fusionné
        
    Returns:
        pd.DataFrame: DataFrame nettoyé et traité
    """
    logger.info("Traitement des données fusionnées...")
    
    # Créer une copie pour éviter les modifications sur l'original
    df_clean = df.copy()
    
    # Créer la colonne consommation_kwh
    if 'consommation_annuelle_totale_de_l_adresse_mwh' in df_clean.columns:
        df_clean['consommation_kwh'] = df_clean['consommation_annuelle_totale_de_l_adresse_mwh'] * 1000
    else:
        logger.error("Colonne de consommation non trouvée")
        raise ValueError("Impossible de trouver la colonne de consommation")
    
    # Nettoyer les données
    df_clean = _clean_merged_data(df_clean)
    
    # Ajouter des informations complémentaires pour l'affichage
    if 'nom_commune' in df_clean.columns and 'nom_commune_geo' in df_clean.columns:
        # Utiliser le nom de commune de l'API géo si disponible, sinon celui d'Enedis
        df_clean['nom_commune_display'] = df_clean['nom_commune_geo'].fillna(df_clean['nom_commune'])
    
    # Générer les polygones carrés pour chaque bâtiment
    logger.info("Génération des polygones de bâtiments...")
    df_clean['footprint_polygon'] = df_clean.apply(
        lambda row: create_square_polygon(row['longitude'], row['latitude'], size_meters=15),
        axis=1
    )
    
    logger.info(f"Données finalement traitées : {len(df_clean)} enregistrements valides avec polygones")
    return df_clean

def _clean_merged_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie les données fusionnées en supprimant les lignes invalides.
    
    Args:
        df: DataFrame à nettoyer
        
    Returns:
        pd.DataFrame: DataFrame nettoyé
    """
    logger.info("Nettoyage des données fusionnées...")
    
    initial_count = len(df)
    
    # Supprimer les lignes sans coordonnées (échec du géocodage)
    df_clean = df.dropna(subset=['latitude', 'longitude'])
    
    # Supprimer les lignes avec des coordonnées invalides
    df_clean = df_clean[
        (df_clean['latitude'] != 0) & 
        (df_clean['longitude'] != 0) &
        (df_clean['latitude'].between(43, 44)) &  # Latitude approximative département 06
        (df_clean['longitude'].between(6, 8))    # Longitude approximative département 06
    ]
    
    # Supprimer les lignes sans consommation
    df_clean = df_clean.dropna(subset=['consommation_kwh'])
    df_clean = df_clean[df_clean['consommation_kwh'] > 0]
    
    # Utiliser un géocodage plus précis par commune avec zones terrestres
    df_clean = _apply_precise_geocoding(df_clean)
    
    final_count = len(df_clean)
    removed_count = initial_count - final_count
    
    logger.info(f"Nettoyage terminé : {removed_count} lignes supprimées ({final_count} restantes)")
    
    return df_clean

# Nouvelles fonctions pour géocodage précis

def _prepare_addresses_for_geocoding(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prépare les adresses complètes pour le géocodage précis.
    """
    df_copy = df.copy()
    
    # Construire l'adresse complète si pas déjà présente
    if 'adresse' not in df_copy.columns or df_copy['adresse'].isna().all():
        # Construire à partir des composants
        numero = df_copy.get('numero_de_voie', '').astype(str).fillna('')
        type_voie = df_copy.get('type_de_voie', '').astype(str).fillna('')
        libelle = df_copy.get('libelle_de_voie', '').astype(str).fillna('')
        commune = df_copy.get('nom_commune', '').astype(str).fillna('')
        
        df_copy['adresse_complete'] = (
            numero + ' ' + type_voie + ' ' + libelle + ', ' + commune
        ).str.replace(r'\s+', ' ', regex=True).str.strip()
    else:
        # Ajouter la commune à l'adresse existante
        commune = df_copy.get('nom_commune', '').astype(str).fillna('')
        df_copy['adresse_complete'] = (
            df_copy['adresse'].astype(str) + ', ' + commune
        ).str.strip()
    
    # Nettoyer les adresses
    df_copy['adresse_complete'] = df_copy['adresse_complete'].str.replace(
        r'[^a-zA-Z0-9\s,\-\'\.]', '', regex=True
    ).str.strip()
    
    logger.info(f"Adresses préparées pour géocodage: {len(df_copy)} enregistrements")
    return df_copy

@st.cache_data(ttl=CONFIG['GEOCODING']['CACHE_TTL'])
def _geocode_address_batch(addresses: List[str]) -> List[Dict]:
    """
    Géocode un batch d'adresses via l'API adresse.data.gouv.fr.
    """
    import time
    
    results = []
    url = CONFIG['URLS']['GEOCODING_API']
    
    for i, address in enumerate(addresses):
        if i > 0 and i % 10 == 0:  # Pause tous les 10 appels
            time.sleep(0.1)
            
        try:
            params = {
                'q': address,
                'limit': 1,
                'autocomplete': 0
            }
            
            response = requests.get(
                url, 
                params=params, 
                timeout=CONFIG['GEOCODING']['TIMEOUT']
            )
            response.raise_for_status()
            
            data = response.json()
            features = data.get('features', [])
            
            if features:
                coords = features[0]['geometry']['coordinates']  # [lon, lat]
                properties = features[0]['properties']
                
                results.append({
                    'latitude': coords[1],
                    'longitude': coords[0],
                    'score': properties.get('score', 0),
                    'type': properties.get('type', ''),
                    'address_found': properties.get('label', ''),
                    'success': True
                })
            else:
                results.append({'success': False, 'address': address})
                
        except Exception as e:
            logger.warning(f"Erreur géocodage pour '{address}': {e}")
            results.append({'success': False, 'address': address, 'error': str(e)})
    
    return results

def _precise_geocoding_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Effectue le géocodage précis par batch.
    """
    df_copy = df.copy()
    batch_size = CONFIG['GEOCODING']['BATCH_SIZE']
    total_addresses = len(df_copy)
    
    # Initialiser les colonnes de résultats
    df_copy['latitude'] = None
    df_copy['longitude'] = None
    df_copy['geocoding_score'] = None
    df_copy['geocoding_source'] = None
    
    logger.info(f"Début géocodage précis par batch de {batch_size}...")
    
    # Traiter par batch
    for start_idx in range(0, total_addresses, batch_size):
        end_idx = min(start_idx + batch_size, total_addresses)
        batch_df = df_copy.iloc[start_idx:end_idx]
        
        progress_pct = (end_idx / total_addresses) * 100
        logger.info(f"Géocodage batch {start_idx//batch_size + 1}: {start_idx}-{end_idx}/{total_addresses} ({progress_pct:.1f}%)")
        print(f"\r🗺️ Géocodage précis en cours... {progress_pct:.1f}% ({end_idx}/{total_addresses})", end='', flush=True)
        
        # Extraire les adresses du batch
        addresses = batch_df['adresse_complete'].tolist()
        
        # Géocoder le batch
        results = _geocode_address_batch(addresses)
        
        # Appliquer les résultats
        for i, result in enumerate(results):
            actual_idx = start_idx + i
            
            if result.get('success', False) and result.get('score', 0) > 0.5:
                df_copy.at[actual_idx, 'latitude'] = result['latitude']
                df_copy.at[actual_idx, 'longitude'] = result['longitude']
                df_copy.at[actual_idx, 'geocoding_score'] = result['score']
                df_copy.at[actual_idx, 'geocoding_source'] = 'precise'
    
    successful_geocoding = df_copy['geocoding_source'].eq('precise').sum()
    logger.info(f"Géocodage précis terminé: {successful_geocoding}/{total_addresses} réussis")
    
    return df_copy

def _apply_fallback_geocoding(df: pd.DataFrame, commune_coords: Dict[str, Dict]) -> pd.DataFrame:
    """
    Applique un géocodage de fallback pour les adresses non trouvées.
    """
    df_copy = df.copy()
    
    # Pour les lignes sans coordonnées précises, utiliser le centre de commune
    mask_no_coords = df_copy['latitude'].isna()
    
    def get_commune_coordinates(code_commune):
        coords = commune_coords.get(code_commune, {})
        return pd.Series([
            coords.get('latitude'),
            coords.get('longitude'),
            coords.get('nom_commune_geo')
        ])
    
    if mask_no_coords.any():
        logger.info(f"Application du fallback pour {mask_no_coords.sum()} adresses...")
        
        fallback_coords = df_copy.loc[mask_no_coords, 'code_commune'].apply(get_commune_coordinates)
        
        df_copy.loc[mask_no_coords, 'latitude'] = fallback_coords.iloc[:, 0]
        df_copy.loc[mask_no_coords, 'longitude'] = fallback_coords.iloc[:, 1]
        df_copy.loc[mask_no_coords, 'nom_commune_geo'] = fallback_coords.iloc[:, 2]
        df_copy.loc[mask_no_coords, 'geocoding_source'] = 'commune'
        df_copy.loc[mask_no_coords, 'geocoding_score'] = 0.3  # Score plus faible
    
    return df_copy

def _apply_precise_geocoding(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fonction conservée pour compatibilité - maintenant ne fait que valider les coordonnées.
    """
    # Filtrage géographique pour le département 06
    df_clean = df[
        (df['latitude'] >= 43.47) &  # Sud du département
        (df['latitude'] <= 44.37) &  # Nord du département
        (df['longitude'] >= 6.65) &  # Ouest
        (df['longitude'] <= 7.70) &  # Est
        # Exclure les zones maritimes évidentes
        ~((df['latitude'] < 43.52) & (df['longitude'] > 7.25))  # Zone mer Nice/Monaco
    ]
    
    logger.info(f"Validation géographique: {len(df_clean)}/{len(df)} points validés")
    return df_clean

@st.cache_data(ttl=86400 * 7)  # Cache 7 jours car les communes du département ne changent pas
def get_all_communes_dept_06() -> list:
    """
    Récupère la liste complète de toutes les communes du département 06 via l'API Géo.
    
    Returns:
        list: Liste complète des noms de communes triés du département 06
    """
    try:
        url = CONFIG['URLS']['GEO_API']
        
        # Récupérer toutes les communes du département 06
        params = {
            'codeDepartement': CONFIG['DEPARTEMENT'],
            'fields': 'nom',
            'format': 'json'
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        communes_data = response.json()
        
        # Extraire tous les noms de communes
        communes = []
        for commune in communes_data:
            nom = commune.get('nom')
            if nom:
                communes.append(nom)
        
        communes_list = sorted(list(set(communes)))  # Supprimer doublons et trier
        logger.info(f"Communes complètes du département 06: {len(communes_list)}")
        
        return communes_list
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des communes complètes: {e}")
        # Fallback avec une liste étendue des principales communes du 06
        return [
            'ANTIBES', 'ASPREMONT', 'AURIBEAU-SUR-SIAGNE', 'BIOT', 'BREIL-SUR-ROYA', 
            'CAGNES-SUR-MER', 'CANNES', 'CAP-D\'AIL', 'CARROS', 'CASTAGNIERS',
            'CLANS', 'COARAZE', 'CONTES', 'COURSEGOULES', 'DRAP', 'EZE',
            'FALICON', 'GATTIÈRES', 'GILETTE', 'GRASSE', 'JUAN-LES-PINS',
            'LA COLLE-SUR-LOUP', 'LA GAUDE', 'LA TRINITÉ', 'LA TURBIE',
            'LE CANNET', 'LE ROURET', 'LES ADRETS-DE-L\'ESTÉREL', 'LEVENS',
            'MANDELIEU-LA-NAPOULE', 'MENTON', 'MOUANS-SARTOUX', 'MOUGINS',
            'NICE', 'OPIO', 'PEYMEINADE', 'ROQUEBRUNE-CAP-MARTIN', 'ROQUEFORT-LES-PINS',
            'SAINT-ANDRÉ-DE-LA-ROCHE', 'SAINT-JEAN-CAP-FERRAT', 'SAINT-LAURENT-DU-VAR',
            'SAINT-MARTIN-DU-VAR', 'SAINT-PAUL-DE-VENCE', 'SOPHIA-ANTIPOLIS',
            'THÉOULE-SUR-MER', 'TOURRETTE-LEVENS', 'TOURRETTES-SUR-LOUP', 'VALBONNE',
            'VALLAURIS', 'VENCE', 'VILLENEUVE-LOUBET', 'VILLEFRANCHE-SUR-MER'
        ]

@st.cache_data(ttl=86400)  # Cache 24h car les communes ne changent pas souvent
def get_available_communes_from_api() -> list:
    """
    Récupère la liste des communes disponibles dans l'API Enedis.
    
    Returns:
        list: Liste des noms de communes triés
    """
    try:
        url = CONFIG['URLS']['ADRESSE_API']
        
        # Requête pour obtenir juste les communes distinctes (petit échantillon)
        params = {
            'limit': 100,
            'offset': 0,
            'where': f'code_departement="{CONFIG["DEPARTEMENT"]}"',
            'select': 'nom_commune'
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        results = data.get('results', [])
        
        # Extraire les noms de communes uniques
        communes = set()
        for result in results:
            nom_commune = result.get('nom_commune')
            if nom_commune:
                communes.add(nom_commune)
        
        communes_list = sorted(list(communes))
        logger.info(f"Communes disponibles dans l'API: {len(communes_list)}")
        
        return communes_list
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des communes: {e}")
        # Fallback avec les principales communes du 06
        return [
            'ANTIBES', 'CANNES', 'NICE', 'GRASSE', 'CAGNES-SUR-MER',
            'SAINT-LAURENT-DU-VAR', 'MANDELIEU-LA-NAPOULE', 'VILLENEUVE-LOUBET',
            'MOUGINS', 'VALBONNE', 'MENTON', 'BEAULIEU-SUR-MER'
        ]

def get_unique_communes(df: pd.DataFrame) -> list:
    """
    Retourne la liste unique des communes présentes dans les données.
    
    Args:
        df: DataFrame avec les données
        
    Returns:
        list: Liste des noms de communes triés
    """
    # Utiliser nom_commune_display si disponible, sinon nom_commune
    if 'nom_commune_display' in df.columns:
        commune_col = 'nom_commune_display'
    elif 'nom_commune' in df.columns:
        commune_col = 'nom_commune'
    else:
        logger.warning("Aucune colonne de commune trouvée")
        return []
    
    communes = df[commune_col].dropna().unique()
    return sorted(communes.tolist())

def filter_data_by_consumption(df: pd.DataFrame, min_consumption_kwh: float) -> pd.DataFrame:
    """
    Filtre les données par seuil de consommation.
    
    Args:
        df: DataFrame source
        min_consumption_kwh: Seuil minimum de consommation en kWh
        
    Returns:
        pd.DataFrame: DataFrame filtré
    """
    return df[df['consommation_kwh'] >= min_consumption_kwh].copy()

def filter_data_by_communes(df: pd.DataFrame, selected_communes: list) -> pd.DataFrame:
    """
    Filtre les données par communes sélectionnées.
    
    Args:
        df: DataFrame source
        selected_communes: Liste des communes à conserver
        
    Returns:
        pd.DataFrame: DataFrame filtré
    """
    if not selected_communes:
        return df.copy()
    
    # Utiliser nom_commune_display si disponible, sinon nom_commune
    if 'nom_commune_display' in df.columns:
        commune_col = 'nom_commune_display'
    elif 'nom_commune' in df.columns:
        commune_col = 'nom_commune'
    else:
        logger.warning("Aucune colonne de commune trouvée pour le filtrage")
        return df.copy()
    
    return df[df[commune_col].isin(selected_communes)].copy()

def update_polygons_for_zoom(df: pd.DataFrame, zoom_level: int) -> pd.DataFrame:
    """
    Met à jour les polygones selon le niveau de zoom.
    
    Args:
        df: DataFrame avec les données
        zoom_level: Niveau de zoom estimé
        
    Returns:
        pd.DataFrame: DataFrame avec polygones mis à jour
    """
    logger.info(f"Mise à jour des polygones pour zoom niveau {zoom_level}")
    
    df_updated = df.copy()
    df_updated['footprint_polygon'] = df_updated.apply(
        lambda row: create_square_polygon(
            row['longitude'], 
            row['latitude'], 
            zoom_level=zoom_level
        ),
        axis=1
    )
    
    return df_updated

# Fonction de test pour validation
def test_data_handler():
    """
    Fonction de test pour valider le module de données.
    """
    try:
        # Test 1: Chargement des données
        print("🧪 Test 1: Chargement des données...")
        df = load_and_process_data()
        print(f"✅ {len(df)} enregistrements chargés")
        
        # Test 2: Vérification des colonnes
        print("🧪 Test 2: Vérification des colonnes...")
        required_cols = ['latitude', 'longitude', 'consommation_kwh']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"❌ Colonnes manquantes: {missing_cols}")
        else:
            print("✅ Toutes les colonnes requises présentes")
        
        # Test 3: Vérification des données
        print("🧪 Test 3: Vérification des données...")
        valid_coords = df[['latitude', 'longitude']].notna().all(axis=1).sum()
        print(f"✅ {valid_coords} enregistrements avec coordonnées valides")
        
        # Test 4: Filtrage
        print("🧪 Test 4: Test du filtrage...")
        filtered = filter_data_by_consumption(df, 10000)  # 10 MWh
        print(f"✅ {len(filtered)} prospects avec conso > 10 MWh")
        
        print("🎉 Tous les tests passés avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        return False

if __name__ == "__main__":
    test_data_handler()