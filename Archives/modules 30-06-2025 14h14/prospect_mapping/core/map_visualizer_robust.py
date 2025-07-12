#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de visualisation cartographique pour la prospection - STYLE CADASTRAL 2D.
Version robuste avec gestion des colonnes manquantes.
"""

import logging
import pandas as pd
import pydeck as pdk
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

# Configuration cadastrale française
MAP_CONFIG = {
    'DEPARTMENT_06_CENTER': {
        'latitude': 43.7102,
        'longitude': 7.2620,
        'zoom': 13,    # Zoom rapproché pour voir les parcelles
        'pitch': 0     # Vue 2D orthogonale (style cadastre)
    },
    'MAPBOX_STYLE': 'mapbox://styles/mapbox/light-v10',
    'COLOR_RANGE_CADASTRAL': [
        [144, 238, 144, 180],  # Vert clair (très faible consommation)
        [173, 255, 47, 180],   # Vert-jaune (faible consommation)
        [255, 255, 0, 180],    # Jaune (consommation moyenne-faible)
        [255, 165, 0, 180],    # Orange (consommation moyenne)
        [255, 69, 0, 180],     # Rouge-orange (forte consommation)
        [220, 20, 60, 180],    # Rouge foncé (très forte consommation)
    ]
}

# Configuration pour le tooltip interactif
TOOLTIP_CONFIG = {
    'HOVER_DELAY': 200,  # Délai avant affichage (ms)
    'STICKY_MODE': True,  # Le tooltip reste affiché après le clic
    'OFFSET': {'x': 10, 'y': 10},  # Décalage par rapport au curseur
}

def create_prospect_map(data: pd.DataFrame, mapbox_api_key: Optional[str] = None, 
                       interaction_mode: str = "Navigation", tooltip_mode: str = "Survol normal") -> pdk.Deck:
    """
    Crée une carte cadastrale 2D interactive de prospection.
    
    Args:
        data: DataFrame avec colonnes longitude, latitude, consommation_kwh, footprint_polygon
        mapbox_api_key: Clé API Mapbox (optionnelle)
        interaction_mode: Mode d'interaction ("Navigation" ou "Sélection")
        tooltip_mode: Mode d'affichage des tooltips
        
    Returns:
        pdk.Deck: Objet carte pydeck configuré en style cadastral
    """
    logger.info(f"Création de la carte cadastrale avec {len(data)} bâtiments")
    logger.debug(f"Colonnes disponibles: {list(data.columns)}")
    logger.debug(f"Consommations: min={data['consommation_kwh'].min()}, max={data['consommation_kwh'].max()}")
    
    if len(data) == 0:
        logger.warning("Aucune donnée à afficher sur la carte")
        return _create_empty_map()
    
    # Vérifier les colonnes requises pour la vue cadastrale
    required_columns = ['longitude', 'latitude', 'consommation_kwh']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        raise ValueError(f"Colonnes manquantes pour la vue cadastrale : {missing_columns}")
    
    # Préparer les données visuelles
    data_visual = _prepare_visual_data_robust(data)
    
    # Créer la couche cadastrale
    cadastral_layer = _create_robust_cadastral_layer(data_visual)
    
    # Calculer le centre de vue
    view_state = _calculate_view_state(data_visual)
    
    # Créer un tooltip simple (non-interactif) car l'interaction se fait via sélection
    tooltip_config = _create_simple_tooltip(data_visual)
    
    # Paramètres supplémentaires pour améliorer l'interaction
    deck_params = {
        'map_style': MAP_CONFIG['MAPBOX_STYLE'],
        'initial_view_state': view_state,
        'layers': [cadastral_layer],
        'tooltip': tooltip_config,
        'map_provider': 'mapbox' if mapbox_api_key else None,
        'api_keys': {'mapbox': mapbox_api_key} if mapbox_api_key else None,
        # Amélioration de l'interaction
        'parameters': {
            'pickingRadius': 10,  # Augmente la zone de détection du clic
            'pickMultipleObjects': False,  # Un seul objet à la fois
        }
    }
    
    # Créer la carte
    deck = pdk.Deck(**deck_params)
    
    logger.info("Carte cadastrale créée avec succès")
    return deck

def _prepare_visual_data_robust(data: pd.DataFrame) -> pd.DataFrame:
    """Prépare les données pour la visualisation cadastrale de manière robuste."""
    data_visual = data.copy()
    
    # S'assurer que les colonnes essentielles existent et sont propres
    _ensure_clean_columns(data_visual)
    
    # Ajouter un numéro de parcelle cohérent si pas déjà présent
    if 'numero_parcelle' not in data_visual.columns:
        # Utiliser un index séquentiel pour maintenir la cohérence avec l'interface
        data_visual = data_visual.reset_index(drop=True)
        data_visual['numero_parcelle'] = range(1, len(data_visual) + 1)
    
    # Ajouter la colonne MWh pour le tooltip
    if 'consommation_mwh' not in data_visual.columns:
        data_visual['consommation_mwh'] = (data_visual['consommation_kwh'] / 1000).round(1)
    
    # Calculer les couleurs selon le score de prospection
    if 'prospect_score' in data_visual.columns:
        scores = data_visual['prospect_score'].fillna(50)
        
        # Palette de couleurs selon score
        COLOR_RANGE_SCORE = [
            [220, 20, 60, 180],    # Rouge (score < 40)
            [255, 140, 0, 180],    # Orange (score 40-60)
            [255, 215, 0, 180],    # Or (score 60-80)
            [50, 205, 50, 180],    # Vert (score > 80)
        ]
        
        colors = []
        for score in scores:
            if score < 40:
                colors.append(COLOR_RANGE_SCORE[0])
            elif score < 60:
                colors.append(COLOR_RANGE_SCORE[1])
            elif score < 80:
                colors.append(COLOR_RANGE_SCORE[2])
            else:
                colors.append(COLOR_RANGE_SCORE[3])
        
        data_visual['fill_color'] = colors
    else:
        # Fallback sur la consommation si pas de score
        consumption = data_visual['consommation_kwh']
        min_val = consumption.min()
        max_val = consumption.quantile(0.90)  # Utiliser le 90e percentile
        
        # Normaliser la consommation (0-1)
        consumption_normalized = (consumption - min_val) / (max_val - min_val)
        consumption_normalized = np.clip(consumption_normalized, 0, 1)
        
        # Assigner les couleurs cadastrales
        color_indices = (consumption_normalized * (len(MAP_CONFIG['COLOR_RANGE_CADASTRAL']) - 1)).astype(int)
        color_indices = np.clip(color_indices, 0, len(MAP_CONFIG['COLOR_RANGE_CADASTRAL']) - 1)
        
        # Convertir en RGB avec alpha
        colors = []
        for idx in color_indices:
            colors.append(MAP_CONFIG['COLOR_RANGE_CADASTRAL'][idx])
        
        data_visual['fill_color'] = colors
    
    return data_visual

def _ensure_clean_columns(df: pd.DataFrame):
    """S'assurer que toutes les colonnes nécessaires au tooltip sont propres."""
    
    # Adresse : essayer plusieurs sources
    if 'adresse' not in df.columns or df['adresse'].isna().all():
        if 'numero_de_voie' in df.columns and 'libelle_de_voie' in df.columns:
            df['adresse'] = df['numero_de_voie'].astype(str) + ' ' + df['libelle_de_voie'].astype(str)
        else:
            df['adresse'] = 'Adresse non disponible'
    
    # Nettoyer l'adresse
    df['adresse'] = df['adresse'].fillna('Adresse inconnue').astype(str)
    
    # Commune : essayer plusieurs sources
    if 'nom_commune' not in df.columns or df['nom_commune'].isna().all():
        if 'nom_commune_display' in df.columns:
            df['nom_commune'] = df['nom_commune_display']
        elif 'nom_commune_geo' in df.columns:
            df['nom_commune'] = df['nom_commune_geo']
        else:
            df['nom_commune'] = 'Commune inconnue'
    
    df['nom_commune'] = df['nom_commune'].fillna('Commune inconnue').astype(str)
    
    # Logements
    if 'nombre_de_logements' not in df.columns:
        df['nombre_de_logements'] = 0
    df['nombre_de_logements'] = df['nombre_de_logements'].fillna(0).astype(int)
    
    # Consommation (arrondir pour un affichage plus propre et s'assurer qu'elle n'est pas nulle)
    df['consommation_kwh'] = df['consommation_kwh'].fillna(0).round(0).astype(int)
    
    # Ajouter des logs pour debug si nécessaire
    logger.debug(f"Consommation min/max après nettoyage: {df['consommation_kwh'].min()}/{df['consommation_kwh'].max()}")

def _create_robust_cadastral_layer(data: pd.DataFrame) -> pdk.Layer:
    """Crée une couche cadastrale 2D avec interaction améliorée."""
    
    data_list = data.to_dict('records')
    
    return pdk.Layer(
        'PolygonLayer',
        data=data_list,
        get_polygon='footprint_polygon',
        get_fill_color='fill_color',
        extruded=False,
        pickable=True,
        filled=True,
        get_line_color=[0, 0, 0, 255],
        line_width_min_pixels=2,  # Augmenté pour meilleure visibilité
        line_width_max_pixels=4,  # Augmenté
        auto_highlight=True,
        highlight_color=[255, 255, 0, 200],  # Jaune vif pour meilleure visibilité
        # Nouveaux paramètres pour l'interaction
        updateTriggers={
            'getPolygon': 1,  # Force la mise à jour
        },
        # Augmenter la zone cliquable
        pickable_area_padding=5
    )

def _create_simple_tooltip(data: pd.DataFrame) -> dict:
    """Crée un tooltip simple pour l'affichage d'informations de base."""
    
    # Ajouter les colonnes calculées nécessaires
    data_copy = data.copy()
    if 'consommation_mwh' not in data_copy.columns:
        data_copy['consommation_mwh'] = data_copy['consommation_kwh'] / 1000
    
    # Template HTML simple et propre avec format pydeck correct
    tooltip_html = '''
    <div style="
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 8px; 
        border: 2px solid #2c3e50; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.2); 
        font-family: 'Segoe UI', Arial, sans-serif; 
        font-size: 13px; 
        max-width: 280px;
        color: #2c3e50;
    ">
        <div style="font-weight: bold; margin-bottom: 10px; font-size: 16px; color: #2c3e50;">
            🏢 Parcelle #{numero_parcelle}
        </div>
        
        <div style="margin-bottom: 6px;">
            <b>📍 Commune:</b> {nom_commune}
        </div>
        
        <div style="margin-bottom: 6px;">
            <b>🏠 Adresse:</b> {adresse}
        </div>
        
        <div style="margin-bottom: 6px;">
            <b>🏘️ Logements:</b> {nombre_de_logements}
        </div>
        
        <div style="margin: 10px 0; padding: 8px; background-color: #fff3cd; border-radius: 6px; border-left: 4px solid #ffc107;">
            <b>⚡ Consommation:</b><br>
            <span style="color: #e74c3c; font-weight: bold; font-size: 16px;">
                {consommation_kwh} kWh/an
            </span><br>
            <span style="color: #666; font-size: 11px;">({consommation_mwh} MWh/an)</span>
        </div>
        
        <div style="font-size: 11px; color: #95a5a6; margin-top: 10px; text-align: center; font-style: italic;">
            👆 Utilisez le menu sous la carte pour sélectionner
        </div>
    </div>
    '''
    
    # Debug: Vérifier que les données ont bien les bonnes colonnes
    logger.debug(f"Colonnes pour tooltip: {list(data_copy.columns)}")
    if len(data_copy) > 0:
        sample_row = data_copy.iloc[0]
        logger.debug(f"Exemple de données: consommation_kwh={sample_row.get('consommation_kwh', 'MANQUANT')}, consommation_mwh={sample_row.get('consommation_mwh', 'MANQUANT')}")
    
    return {
        'html': tooltip_html,
        'style': {
            'backgroundColor': 'rgba(255, 255, 255, 0.9)',
            'color': '#2c3e50'
        }
    }

def _create_adaptive_tooltip(data: pd.DataFrame) -> dict:
    """Wrapper pour maintenir la compatibilité - utilise le nouveau tooltip simple."""
    return _create_simple_tooltip(data)

def _calculate_view_state(data: pd.DataFrame) -> pdk.ViewState:
    """Calcule l'état de vue optimal pour les données."""
    if len(data) == 0:
        return pdk.ViewState(**MAP_CONFIG['DEPARTMENT_06_CENTER'])
    
    # Calculer le centre géographique
    center_lat = data['latitude'].mean()
    center_lon = data['longitude'].mean()
    
    # Calculer la dispersion pour ajuster le zoom
    lat_range = data['latitude'].max() - data['latitude'].min()
    lon_range = data['longitude'].max() - data['longitude'].min()
    max_range = max(lat_range, lon_range)
    
    # Ajuster le zoom cadastral
    if max_range > 1:
        zoom = 9
    elif max_range > 0.5:
        zoom = 10
    elif max_range > 0.2:
        zoom = 12
    else:
        zoom = 13
    
    return pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=zoom,
        pitch=0  # Vue 2D cadastrale obligatoire
    )

def _create_empty_map() -> pdk.Deck:
    """Crée une carte vide centrée sur le département 06."""
    view_state = pdk.ViewState(**MAP_CONFIG['DEPARTMENT_06_CENTER'])
    
    return pdk.Deck(
        map_style=MAP_CONFIG['MAPBOX_STYLE'],
        initial_view_state=view_state,
        layers=[]
    )

def get_map_legend_info(data: pd.DataFrame) -> dict:
    """Génère les informations pour la légende de la carte."""
    if len(data) == 0:
        return {'min_consumption': 0, 'max_consumption': 0, 'total_points': 0}
    
    consumption = data['consommation_kwh']
    
    return {
        'min_consumption': consumption.min(),
        'max_consumption': consumption.max(),
        'mean_consumption': consumption.mean(),
        'total_points': len(data),
        'color_range_info': [
            {'color': '🟢 Vert clair', 'range': 'Très faible consommation'},
            {'color': '🟡 Jaune', 'range': 'Consommation moyenne'},
            {'color': '🔴 Rouge', 'range': 'Forte consommation'}
        ]
    }