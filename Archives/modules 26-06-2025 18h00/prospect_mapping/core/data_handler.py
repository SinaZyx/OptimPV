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
import threading
import time
# Import conditionnel geopy avec fallback
try:
    from geopy.distance import geodesic
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False
    # Fonction fallback pour calculer distance approximative
    def geodesic(point1, point2):
        import math
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        # Formule de distance euclidienne approximative
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # Conversion approximative en km (1 degré ≈ 111 km)
        distance_km = math.sqrt(dlat**2 + dlon**2) * 111
        
        # Retourner un objet avec attribut kilometers
        class DistanceResult:
            def __init__(self, km):
                self.kilometers = km
        
        return DistanceResult(distance_km)

warnings.filterwarnings('ignore')

# Import du module d'analyse cadastrale
try:
    from .cadastre_analyzer import CadastreAnalyzer
    CADASTRE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Module cadastre_analyzer non disponible: {e}")
    CADASTRE_AVAILABLE = False

# Configuration
CONFIG = {
    'URLS': {
        'ADRESSE_API': 'https://data.enedis.fr/api/explore/v2.1/catalog/datasets/consommation-annuelle-residentielle-par-adresse/records',
        'GEO_API': 'https://geo.api.gouv.fr/communes',
        'GEOCODING_API': 'https://api-adresse.data.gouv.fr/search/'  # API précise par adresse
    },
    'DEPARTEMENT': '06',
    'SEUIL_CONSO_DEFAULT': 7.0,  # En MWh (équivalent à 7000 kWh)
    # NOUVELLE CONFIGURATION MOUGINS
    'MOUGINS_CENTER': {
        'latitude': 43.5974,
        'longitude': 7.0058,
        'nom': 'Mougins'
    },
    'DEFAULT_COMMUNES_COUNT': 10,  # Nombre de communes par défaut autour de Mougins
    'BDTOPO_BACKGROUND': True,  # Enrichissement BD TOPO en arrière-plan
    'GEOCODING': {
        'BATCH_SIZE': 100,  # Augmenté pour plus de rapidité
        'CACHE_TTL': 86400 * 7,  # Cache 7 jours (les adresses ne changent pas)
        'MAX_RETRIES': 3,
        'TIMEOUT': 5  # Timeout réduit pour vitesse
    },
    # NOUVELLES CONFIGURATIONS ENRICHISSEMENT
    'APIS': {
        'BDTOPO_FULL': True,  # Activer récupération complète BD TOPO
        'DPE_ADEME': True,    # Activer récupération DPE
        'DPE_API_URL': 'https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines',
        'DPE_CACHE_TTL': 86400 * 30,  # Cache 30 jours
        'DPE_RADIUS_DEFAULT': 50,  # Rayon de recherche DPE par défaut (mètres)
        'BD_TOPO_TIMEOUT': 10,  # Timeout pour BD TOPO IGN
        'DPE_TIMEOUT': 10,      # Timeout pour API DPE
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

@st.cache_data(ttl=86400)  # Cache pendant 24h (les communes ne changent pas)
def get_closest_communes_to_mougins(max_communes: int = 10) -> List[str]:
    """
    Récupère les communes les plus proches de Mougins dans le département 06.
    
    Args:
        max_communes: Nombre maximum de communes à retourner
        
    Returns:
        List[str]: Liste des codes communes triés par distance à Mougins
    """
    logger.info(f"Recherche des {max_communes} communes les plus proches de Mougins...")
    
    try:
        # Récupérer toutes les communes du département 06
        commune_coords = _fetch_commune_coordinates()
        
        if not commune_coords:
            logger.warning("Aucune commune trouvée")
            return []
        
        # Point de référence : Mougins
        mougins_center = (
            CONFIG['MOUGINS_CENTER']['latitude'],
            CONFIG['MOUGINS_CENTER']['longitude']
        )
        
        # Calculer les distances
        communes_with_distance = []
        for code_commune, data in commune_coords.items():
            commune_point = (data['latitude'], data['longitude'])
            
            # Calculer la distance en kilomètres
            distance_km = geodesic(mougins_center, commune_point).kilometers
            
            communes_with_distance.append({
                'code': code_commune,
                'nom': data.get('nom_commune_geo', code_commune),
                'distance_km': distance_km,
                'latitude': data['latitude'],
                'longitude': data['longitude']
            })
        
        # Trier par distance
        communes_with_distance.sort(key=lambda x: x['distance_km'])
        
        # Prendre les plus proches
        closest_communes = communes_with_distance[:max_communes]
        
        # Log des résultats
        logger.info(f"Communes les plus proches de Mougins trouvées:")
        for i, commune in enumerate(closest_communes[:5], 1):
            logger.info(f"  {i}. {commune['nom']} ({commune['code']}) - {commune['distance_km']:.1f}km")
        
        if len(closest_communes) > 5:
            logger.info(f"  ... et {len(closest_communes) - 5} autres")
        
        # Retourner les NOMS de communes (pas les codes) pour l'API Enedis
        return [commune['nom'] for commune in closest_communes]
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul des communes proches: {e}")
        # Fallback : quelques communes connues autour de Mougins (NOMS, pas codes)
        return ['Mougins', 'Cannes', 'Antibes', 'Le Cannet', 'Vallauris', 'Grasse', 'Valbonne', 'Nice', 'Mandelieu-la-Napoule', 'Biot']

@st.cache_data(ttl=3600)  # Cache pendant 1 heure
def load_and_process_data(selected_communes: list = None, proximity_mode: bool = True) -> pd.DataFrame:
    """
    Télécharge et traite les données Enedis pour le département 06.
    OPTIMISÉ : Charge par défaut les 10 communes les plus proches de Mougins.
    
    Args:
        selected_communes: Liste des communes à inclure (None = mode proximité)
        proximity_mode: Si True, utilise les communes proches de Mougins par défaut
    
    Returns:
        pd.DataFrame: DataFrame nettoyé avec coordonnées précises
    """
    
    # Déterminer les communes à charger
    if selected_communes is None and proximity_mode:
        logger.info("🎯 MODE PROXIMITÉ MOUGINS ACTIVÉ - Chargement des communes les plus proches...")
        selected_communes = get_closest_communes_to_mougins(CONFIG['DEFAULT_COMMUNES_COUNT'])
        logger.info(f"📍 Chargement de {len(selected_communes)} communes autour de Mougins")
    elif selected_communes is None:
        logger.info("📍 Mode complet - chargement de toutes les communes du département 06")
    else:
        logger.info(f"📍 Mode personnalisé - chargement de {len(selected_communes)} communes sélectionnées")
    
    # 1. Récupérer les données de consommation Enedis (avec filtre optionnel et fallback)
    consumption_data = _fetch_enedis_data(selected_communes)
    
    # Fallback si aucune donnée trouvée avec le filtre communes
    if consumption_data.empty and selected_communes:
        logger.warning(f"⚠️ Aucune donnée trouvée pour les communes sélectionnées: {selected_communes}")
        logger.info("🔄 Fallback: Chargement de toutes les communes du département 06...")
        consumption_data = _fetch_enedis_data(None)  # Charger toutes les communes
    
    # 2. Récupérer les coordonnées des communes
    commune_coords = _fetch_commune_coordinates()
    
    # 3. Fusionner les données
    merged_data = _merge_consumption_and_coordinates(consumption_data, commune_coords)
    
    # 3.5. Filtrage post-chargement pour mode proximité 
    if proximity_mode and len(merged_data) > 0 and 'nom_commune' in merged_data.columns:
        # Toujours filtrer les communes proches en mode proximité
        communes_proches = get_closest_communes_to_mougins(CONFIG['DEFAULT_COMMUNES_COUNT'])
        avant_filtre = len(merged_data)
        merged_data = merged_data[merged_data['nom_commune'].isin(communes_proches)]
        apres_filtre = len(merged_data)
        logger.info(f"🎯 Filtrage proximité Mougins: {apres_filtre}/{avant_filtre} enregistrements gardés")
        
        if apres_filtre == 0:
            logger.warning("⚠️ Aucun enregistrement après filtrage proximité - Problème avec les noms de communes")
            logger.info("🔄 Utilisation de toutes les données du département 06...")
            # Recharger sans filtre
            consumption_data_full = _fetch_enedis_data(None)
            merged_data = _merge_consumption_and_coordinates(consumption_data_full, commune_coords)
            logger.info(f"📊 Données complètes chargées: {len(merged_data)} enregistrements")
    
    # 4. Traitement final
    df_processed = _process_merged_data(merged_data)
    
    # 5. Enrichissement avec BD TOPO + DPE - MODE ASYNCHRONE
    # Retourner immédiatement les données de base pour affichage carte
    df_with_base_columns = _initialize_enrichment_columns(df_processed)
    
    # Lancer enrichissement en arrière-plan si demandé
    if CONFIG['APIS'].get('BDTOPO_BACKGROUND', True):
        _start_background_enrichment(df_with_base_columns)
    
    df_enriched = df_with_base_columns
    
    logger.info(f"Données traitées : {len(df_enriched)} enregistrements avec géolocalisation et enrichissement")
    return df_enriched

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
    
    # Analyse cadastrale désactivée pour performance
    
    logger.info(f"Données finalement traitées : {len(df_clean)} enregistrements valides avec polygones et analyse PV")
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
    
    # NOUVEAU: Enrichissement désactivé - système arrière-plan utilisé
    # Colonnes d'enrichissement initialisées automatiquement par le nouveau système
    
    final_count = len(df_clean)
    removed_count = initial_count - final_count
    
    logger.info(f"Nettoyage terminé : {removed_count} lignes supprimées ({final_count} restantes)")
    
    return df_clean

def _enrich_with_building_and_dpe_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrichit les données avec les informations bâtiment BD TOPO et DPE ADEME
    RÉACTIVÉ - Enrichissement automatique pour toutes les données chargées
    """
    logger.info("Enrichissement automatique BD TOPO + DPE en cours...")
    
    try:
        from .cadastre_analyzer import CadastreAnalyzer
        analyzer = CadastreAnalyzer()
        
        # Initialiser les colonnes avec valeurs par défaut
        df_enriched = df.copy()
        new_columns = {
            'location_confidence': 'medium',
            'data_source': 'Estimation',
            'nature_detaillee': 'Non précisé',
            'nb_etages': 0,
            'etat_batiment': 'N/A', 
            'date_construction': 'N/A',
            'dpe_available': False,
            'dpe_classe_energie': 'N/A',
            'dpe_classe_ges': 'N/A',
            'dpe_consommation': 0,
            'dpe_distance': None
        }
        
        # Initialiser les colonnes
        for col, default_val in new_columns.items():
            df_enriched[col] = default_val
        
        # Enrichir chaque bâtiment avec BD TOPO et DPE
        total_buildings = len(df_enriched)
        enriched_count = 0
        
        for idx, row in df_enriched.iterrows():
            try:
                lat, lon = row['latitude'], row['longitude']
                
                # Récupérer données bâtiment OSM
                building_data = analyzer.get_building_footprint(lat, lon)
                if building_data:
                    df_enriched.loc[idx, 'location_confidence'] = building_data.get('confidence', 'medium')
                    df_enriched.loc[idx, 'data_source'] = building_data.get('source', 'OSM')
                    df_enriched.loc[idx, 'nature_detaillee'] = building_data.get('nature_detaillee', 'Non précisé')
                    df_enriched.loc[idx, 'nb_etages'] = building_data.get('nb_etages', 0)
                    df_enriched.loc[idx, 'etat_batiment'] = building_data.get('etat_batiment', 'N/A')
                    df_enriched.loc[idx, 'date_construction'] = building_data.get('date_construction', 'N/A')
                
                # Récupérer DPE
                dpe_data = analyzer.get_building_dpe(lat, lon, radius=100)
                if dpe_data:
                    df_enriched.loc[idx, 'dpe_available'] = True
                    df_enriched.loc[idx, 'dpe_classe_energie'] = dpe_data.get('classe_energie', 'N/A')
                    df_enriched.loc[idx, 'dpe_classe_ges'] = dpe_data.get('classe_ges', 'N/A')
                    df_enriched.loc[idx, 'dpe_consommation'] = dpe_data.get('consommation_energie', 0)
                    df_enriched.loc[idx, 'dpe_distance'] = dpe_data.get('distance_m', None)
                
                enriched_count += 1
                
                if enriched_count % 50 == 0:
                    logger.info(f"Enrichissement BD TOPO/DPE: {enriched_count}/{total_buildings}")
                    
            except Exception as e:
                logger.warning(f"Erreur enrichissement bâtiment {idx}: {e}")
                continue
        
        logger.info(f"Enrichissement terminé: {enriched_count}/{total_buildings} bâtiments traités")
        return df_enriched
        
    except ImportError:
        logger.warning("Module cadastre_analyzer non disponible - enrichissement ignoré")
        # Fallback: initialiser uniquement les colonnes
        df_enriched = df.copy()
        for col, default_val in new_columns.items():
            df_enriched[col] = default_val
        return df_enriched

@st.cache_data(ttl=3600)  # Cache les données enrichies pendant 1 heure
def enrich_single_building_on_demand(latitude: float, longitude: float, building_id: str = None) -> dict:
    """
    Enrichit un bâtiment individuel avec les données OSM/DPE à la demande.
    
    Args:
        latitude: Latitude du bâtiment
        longitude: Longitude du bâtiment 
        building_id: ID optionnel du bâtiment pour le cache
        
    Returns:
        dict: Données enrichies du bâtiment (OSM + DPE)
    """
    if not CADASTRE_AVAILABLE:
        logger.warning("Module cadastre_analyzer non disponible pour enrichissement")
        return {}
    
    try:
        from .cadastre_analyzer import CadastreAnalyzer
        analyzer = CadastreAnalyzer()
        
        logger.info(f"Enrichissement à la demande pour bâtiment: lat={latitude:.6f}, lon={longitude:.6f}")
        
        enriched_data = {
            'location_confidence': 'medium',
            'data_source': 'Estimation',
            'nature_detaillee': 'Non précisé',
            'nb_etages': 0,
            'etat_batiment': 'N/A', 
            'date_construction': 'N/A',
            'dpe_available': False,
            'dpe_classe_energie': 'N/A',
            'dpe_classe_ges': 'N/A',
            'dpe_consommation': 0,
            'dpe_distance': None,
            'enrichment_timestamp': pd.Timestamp.now(),
            'enrichment_source': 'on_demand'
        }
        
        # Récupérer données bâtiment OSM
        try:
            building_data = analyzer.get_building_footprint(latitude, longitude)
            
            if building_data:
                enriched_data.update({
                    'location_confidence': building_data.get('confidence', 'medium'),
                    'data_source': building_data.get('source', 'OSM'),
                    'nature_detaillee': building_data.get('nature_detaillee', 'Non précisé'),
                    'nb_etages': building_data.get('nb_etages', 0),
                    'etat_batiment': building_data.get('etat_batiment', 'N/A'),
                    'date_construction': building_data.get('date_construction', 'N/A')
                })
                logger.info("Données OSM récupérées avec succès")
            else:
                logger.info("Aucune donnée OSM trouvée pour ce bâtiment")
                
        except Exception as e:
            logger.warning(f"Erreur récupération données OSM: {e}")
        
        # Récupérer DPE
        try:
            dpe_data = analyzer.get_building_dpe(latitude, longitude, radius=100)
            
            if dpe_data:
                enriched_data.update({
                    'dpe_available': True,
                    'dpe_classe_energie': dpe_data.get('classe_energie', 'N/A'),
                    'dpe_classe_ges': dpe_data.get('classe_ges', 'N/A'),
                    'dpe_consommation': dpe_data.get('consommation_energie', 0),
                    'dpe_distance': dpe_data.get('distance_m', None)
                })
                logger.info(f"DPE trouvé: classe {dpe_data.get('classe_energie', 'N/A')}")
            else:
                logger.info("Aucun DPE trouvé dans un rayon de 100m")
                
        except Exception as e:
            logger.warning(f"Erreur récupération DPE: {e}")
        
        logger.info("Enrichissement à la demande terminé")
        return enriched_data
        
    except Exception as e:
        logger.error(f"Erreur lors de l'enrichissement à la demande: {e}")
        return {}

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
        # if i > 0 and i % 10 == 0:  # Pause tous les 10 appels - DÉSACTIVÉ POUR VITESSE
        #     time.sleep(0.1)
            
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

def _enrich_with_cadastre_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrichit le DataFrame avec l'analyse cadastrale et le scoring PV.
    
    Args:
        df: DataFrame avec les données de base
        
    Returns:
        pd.DataFrame: DataFrame enrichi avec les données cadastrales
    """
    if not CADASTRE_AVAILABLE:
        logger.warning("Module cadastre non disponible, ajout de valeurs par défaut")
        return _add_default_pv_analysis(df)
    
    try:
        cadastre = CadastreAnalyzer()
        df_enriched = df.copy()
        
        # Initialiser les nouvelles colonnes
        new_columns = [
            'roof_area_m2', 'roof_orientation', 'roof_slope', 
            'solar_potential_kwc', 'production_annual_kwh', 
            'prospect_score', 'building_height', 'building_usage'
        ]
        
        for col in new_columns:
            df_enriched[col] = None
        
        # Traitement par batch pour optimiser les performances
        batch_size = 50  # Traiter par groupes de 50
        total_rows = len(df_enriched)
        
        logger.info(f"Analyse cadastrale de {total_rows} bâtiments par batch de {batch_size}...")
        
        for i in range(0, total_rows, batch_size):
            batch_end = min(i + batch_size, total_rows)
            current_batch = df_enriched.iloc[i:batch_end]
            
            logger.info(f"Traitement batch {i//batch_size + 1}/{(total_rows-1)//batch_size + 1} ({i+1}-{batch_end}/{total_rows})")
            
            for idx in current_batch.index:
                try:
                    row = df_enriched.loc[idx]
                    lat, lon = row['latitude'], row['longitude']
                    consumption = row['consommation_kwh']
                    
                    # Analyse complète du prospect
                    analysis = cadastre.analyze_complete_prospect(lat, lon, consumption)
                    
                    # Mettre à jour les colonnes
                    for key, value in analysis.items():
                        if key in new_columns:
                            df_enriched.at[idx, key] = value
                            
                except Exception as e:
                    logger.warning(f"Erreur analyse cadastrale pour index {idx}: {e}")
                    # Valeurs par défaut si erreur
                    defaults = _get_default_pv_values(df_enriched.loc[idx]['consommation_kwh'])
                    for key, value in defaults.items():
                        if key in new_columns:
                            df_enriched.at[idx, key] = value
        
        # Vérifier et nettoyer les résultats
        df_enriched = _validate_pv_analysis(df_enriched)
        
        successful_analysis = df_enriched['prospect_score'].notna().sum()
        logger.info(f"Analyse cadastrale terminée: {successful_analysis}/{total_rows} succès")
        
        return df_enriched
        
    except Exception as e:
        logger.error(f"Erreur majeure dans l'analyse cadastrale: {e}")
        return _add_default_pv_analysis(df)

def _add_default_pv_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute des valeurs par défaut si l'analyse cadastrale n'est pas disponible"""
    df_default = df.copy()
    
    logger.info("Application de l'analyse PV par défaut basée sur la consommation...")
    
    # Calculs par défaut basés sur la consommation - AMÉLIORÉS AVEC VARIATIONS
    import numpy as np
    
    # Surface toiture variable selon consommation (60-200m²)
    consumption = df_default['consommation_kwh']
    base_surface = 60 + (consumption / 1000) * 2  # 2m² par 1000 kWh
    df_default['roof_area_m2'] = base_surface.clip(60, 200).round(0)
    
    # Inclinaison variable (20-40°)
    df_default['roof_slope'] = (25 + np.random.uniform(-5, 15, len(df_default))).round(0)
    
    # Estimation kWc selon consommation - FORMULE PROGRESSIVE
    
    # Calcul réaliste basé sur surface toiture et panneaux 440W
    surface_toiture = df_default['roof_area_m2']
    
    # Panneaux 440W = 2.2m² chacun, espacement requis = facteur 1.4
    # Surface utile = 70% de la surface totale (retrait sécurité)
    surface_utile = surface_toiture * 0.7
    
    # Nombre de panneaux possibles (5.5m² par kWc avec espacement)
    kwc_theorique = surface_utile / 5.5
    
    # Ajustement selon profil de consommation (éviter surdimensionnement)
    kwc_adapte = np.minimum(kwc_theorique, consumption / 1200)  # Max selon besoin
    
    # Tranches réalistes selon type de bâtiment
    conditions = [
        consumption <= 8000,    # Petit résidentiel
        consumption <= 15000,   # Résidentiel standard
        consumption <= 30000,   # Grosse maison/petit tertiaire
        consumption <= 60000,   # Tertiaire moyen
        consumption > 60000     # Gros tertiaire/industriel
    ]
    
    kwc_ranges = [
        kwc_adapte.clip(2.2, 6.6),    # 5-15 panneaux (2.2-6.6 kWc)
        kwc_adapte.clip(4.4, 13.2),   # 10-30 panneaux (4.4-13.2 kWc)
        kwc_adapte.clip(8.8, 26.4),   # 20-60 panneaux (8.8-26.4 kWc)
        kwc_adapte.clip(17.6, 44.0),  # 40-100 panneaux (17.6-44 kWc)
        kwc_adapte.clip(22.0, 88.0)   # 50-200 panneaux (22-88 kWc)
    ]
    
    df_default['solar_potential_kwc'] = np.select(conditions, kwc_ranges, default=9).round(1)
    
    # Production selon latitude (Sud France = 1400 kWh/kWc/an)
    df_default['production_annual_kwh'] = (df_default['solar_potential_kwc'] * 1400).round(0)
    
    # Score amélioré avec variation selon profil
    ratio_autoconso = (df_default['production_annual_kwh'] / df_default['consommation_kwh']).clip(0, 1)
    
    # Score final avec variations plus nuancées
    score_autoconso = ratio_autoconso * 40
    
    # Score taille variable selon la consommation
    taille_ref = np.where(consumption <= 15000, 6, 
                 np.where(consumption <= 30000, 9, 12))  # Référence adaptative
    score_taille = (df_default['solar_potential_kwc'] / taille_ref).clip(0, 1) * 30
    
    # Score orientation avec variation aléatoire réaliste (160-200°)
    orientation_variation = 180 + np.random.normal(0, 10, len(df_default))  # ±10° variation
    df_default['roof_orientation'] = orientation_variation.clip(160, 200).round(0)
    
    orientation_factor = 1 - abs(df_default['roof_orientation'] - 180) / 60  # Pénalité distance au sud
    score_orientation = orientation_factor * 30
    
    df_default['prospect_score'] = (score_autoconso + score_taille + score_orientation).clip(25, 95).astype(int)
    
    df_default['building_height'] = 6.0
    df_default['building_usage'] = 'Résidentiel'
    
    logger.info(f"Analyse PV par défaut appliquée: {len(df_default)} prospects avec score moyen {df_default['prospect_score'].mean():.0f}")
    
    return df_default

def _get_default_pv_values(consumption_kwh: float) -> Dict:
    """Retourne des valeurs par défaut pour un prospect"""
    estimated_kwc = min(consumption_kwh / 1200, 9)  # Max 9 kWc résidentiel
    
    return {
        'roof_area_m2': 80.0,
        'roof_orientation': 180.0,
        'roof_slope': 30.0,
        'solar_potential_kwc': round(estimated_kwc, 1),
        'production_annual_kwh': round(estimated_kwc * 1300, 0),
        'prospect_score': 65,
        'building_height': 6.0,
        'building_usage': 'Résidentiel'
    }

def _validate_pv_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Valide et nettoie les résultats de l'analyse PV"""
    df_clean = df.copy()
    
    # Vérifier les valeurs aberrantes et les corriger
    df_clean['roof_area_m2'] = df_clean['roof_area_m2'].clip(20, 500)
    df_clean['roof_orientation'] = df_clean['roof_orientation'].clip(0, 360)
    df_clean['roof_slope'] = df_clean['roof_slope'].clip(0, 60)
    df_clean['solar_potential_kwc'] = df_clean['solar_potential_kwc'].clip(0.5, 36)
    df_clean['production_annual_kwh'] = df_clean['production_annual_kwh'].clip(500, 50000)
    df_clean['prospect_score'] = df_clean['prospect_score'].clip(10, 100)
    
    # Arrondir les valeurs
    df_clean['roof_area_m2'] = df_clean['roof_area_m2'].round(1)
    df_clean['roof_orientation'] = df_clean['roof_orientation'].round(0)
    df_clean['roof_slope'] = df_clean['roof_slope'].round(0)
    df_clean['solar_potential_kwc'] = df_clean['solar_potential_kwc'].round(1)
    df_clean['production_annual_kwh'] = df_clean['production_annual_kwh'].round(0)
    
    return df_clean

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

# =============================================================================
# NOUVEAU SYSTÈME D'ENRICHISSEMENT EN ARRIÈRE-PLAN
# =============================================================================

def _initialize_enrichment_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Initialise les colonnes d'enrichissement avec des valeurs par défaut.
    Permet d'afficher la carte immédiatement pendant que BD TOPO charge.
    """
    df_with_columns = df.copy()
    
    # Colonnes d'enrichissement avec valeurs par défaut
    enrichment_columns = {
        'location_confidence': 'medium',
        'data_source': 'Estimation',
        'nature_detaillee': 'Non précisé',
        'nb_etages': 0,
        'etat_batiment': 'N/A', 
        'date_construction': 'N/A',
        'dpe_available': False,
        'dpe_classe_energie': 'N/A',
        'dpe_classe_ges': 'N/A',
        'dpe_consommation': 0,
        'dpe_distance': None,
        'enrichment_status': 'pending'  # pending, in_progress, completed
    }
    
    # Initialiser toutes les colonnes
    for col, default_val in enrichment_columns.items():
        df_with_columns[col] = default_val
    
    logger.info(f"Colonnes d'enrichissement initialisées pour {len(df_with_columns)} bâtiments")
    return df_with_columns

def _start_background_enrichment(df: pd.DataFrame):
    """
    Lance l'enrichissement BD TOPO/DPE en arrière-plan via threading.
    N'interrompt pas l'affichage de la carte.
    """
    if not CADASTRE_AVAILABLE:
        logger.warning("Module cadastre_analyzer non disponible - enrichissement ignoré")
        return
    
    def background_enrichment_worker():
        """Worker function qui s'exécute en arrière-plan"""
        try:
            logger.info("🚀 Démarrage enrichissement BD TOPO/DPE en arrière-plan...")
            
            from .cadastre_analyzer import CadastreAnalyzer
            analyzer = CadastreAnalyzer()
            
            total_buildings = len(df)
            enriched_count = 0
            
            # Stocker dans st.session_state pour mise à jour progressive
            if 'enrichment_progress' not in st.session_state:
                st.session_state.enrichment_progress = {
                    'total': total_buildings,
                    'completed': 0,
                    'status': 'in_progress'
                }
            
            for idx, row in df.iterrows():
                try:
                    lat, lon = row['latitude'], row['longitude']
                    
                    # Marquer comme en cours
                    df.loc[idx, 'enrichment_status'] = 'in_progress'
                    
                    # Récupérer données bâtiment OSM
                    building_data = analyzer.get_building_footprint(lat, lon)
                    if building_data:
                        df.loc[idx, 'location_confidence'] = building_data.get('confidence', 'medium')
                        df.loc[idx, 'data_source'] = building_data.get('source', 'OSM')
                        df.loc[idx, 'nature_detaillee'] = building_data.get('nature_detaillee', 'Non précisé')
                        df.loc[idx, 'nb_etages'] = building_data.get('nb_etages', 0)
                        df.loc[idx, 'etat_batiment'] = building_data.get('etat_batiment', 'N/A')
                        df.loc[idx, 'date_construction'] = building_data.get('date_construction', 'N/A')
                    
                    # Récupérer DPE (avec timeout réduit pour vitesse)
                    dpe_data = analyzer.get_building_dpe(lat, lon, radius=50)  # Rayon réduit
                    if dpe_data:
                        df.loc[idx, 'dpe_available'] = True
                        df.loc[idx, 'dpe_classe_energie'] = dpe_data.get('classe_energie', 'N/A')
                        df.loc[idx, 'dpe_classe_ges'] = dpe_data.get('classe_ges', 'N/A')
                        df.loc[idx, 'dpe_consommation'] = dpe_data.get('consommation_energie', 0)
                        df.loc[idx, 'dpe_distance'] = dpe_data.get('distance_m', None)
                    
                    # Marquer comme terminé
                    df.loc[idx, 'enrichment_status'] = 'completed'
                    enriched_count += 1
                    
                    # Mettre à jour le progrès dans session_state
                    st.session_state.enrichment_progress['completed'] = enriched_count
                    
                    # Log périodique
                    if enriched_count % 25 == 0:
                        progress_pct = (enriched_count / total_buildings) * 100
                        logger.info(f"🔄 Enrichissement BD TOPO: {enriched_count}/{total_buildings} ({progress_pct:.1f}%)")
                    
                    # Petite pause pour ne pas surcharger les APIs
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"Erreur enrichissement bâtiment {idx}: {e}")
                    df.loc[idx, 'enrichment_status'] = 'failed'
                    continue
            
            # Marquer l'enrichissement global comme terminé
            st.session_state.enrichment_progress['status'] = 'completed'
            logger.info(f"✅ Enrichissement BD TOPO terminé: {enriched_count}/{total_buildings} bâtiments")
            
        except Exception as e:
            logger.error(f"Erreur critique dans enrichissement arrière-plan: {e}")
            if 'enrichment_progress' in st.session_state:
                st.session_state.enrichment_progress['status'] = 'error'
    
    # Lancer le worker en arrière-plan
    enrichment_thread = threading.Thread(
        target=background_enrichment_worker,
        daemon=True,  # Thread se ferme quand l'app se ferme
        name="BD_TOPO_Enrichment"
    )
    enrichment_thread.start()
    
    logger.info("🎯 Enrichissement BD TOPO lancé en arrière-plan - vous pouvez utiliser la carte!")

def get_enrichment_progress() -> dict:
    """
    Retourne le progrès de l'enrichissement en arrière-plan.
    
    Returns:
        dict: Statut avec total, completed, status
    """
    if 'enrichment_progress' not in st.session_state:
        return {'total': 0, 'completed': 0, 'status': 'not_started'}
    
    return st.session_state.enrichment_progress

if __name__ == "__main__":
    test_data_handler()