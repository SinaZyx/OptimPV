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
    'MAPBOX_STYLES': {
        'Plan Standard': 'mapbox://styles/mapbox/light-v10',
        'Satellite': 'mapbox://styles/mapbox/satellite-v9',
        'Satellite + Rues': 'mapbox://styles/mapbox/satellite-streets-v12',
        'Sombre': 'mapbox://styles/mapbox/dark-v10',
        'Cadastral': 'mapbox://styles/mapbox/streets-v12',
        'OpenStreetMap': 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'
    },
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
                       interaction_mode: str = "Navigation", tooltip_mode: str = "Survol normal",
                       map_style: str = "Plan Standard", opacity: float = 0.7,
                       show_borders: bool = True, color_by: str = "Consommation",
                       dpe_data: Optional[pd.DataFrame] = None, show_dpe: bool = False,
                       search_location: Optional[dict] = None,
                       erp_client_data: Optional[pd.DataFrame] = None, show_erp_clients: bool = False) -> pdk.Deck:
    """
    Crée une carte cadastrale 2D interactive de prospection.
    
    Args:
        data: DataFrame avec colonnes longitude, latitude, consommation_kwh, footprint_polygon
        mapbox_api_key: Clé API Mapbox (optionnelle)
        interaction_mode: Mode d'interaction ("Navigation" ou "Sélection")
        tooltip_mode: Mode d'affichage des tooltips
        map_style: Style de fond de carte
        opacity: Transparence des polygones (0-1)
        show_borders: Afficher les bordures des parcelles
        color_by: Critère de coloration ("Consommation", "Nombre de logements", "Surface estimée")
        
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
    data_visual = _prepare_visual_data_robust(data, color_by, opacity)
    
    # Créer la couche cadastrale
    cadastral_layer = _create_robust_cadastral_layer(data_visual, show_borders)
    
    # Créer les couches supplémentaires
    layers = [cadastral_layer]
    
    # Ajouter la couche DPE si demandée
    if show_dpe and dpe_data is not None and len(dpe_data) > 0:
        dpe_layer = _create_dpe_layer(dpe_data)
        layers.append(dpe_layer)
    
    # Ajouter le marqueur de recherche si présent
    if search_location:
        search_marker_layer = _create_search_marker_layer(search_location)
        layers.append(search_marker_layer)
    
    # Ajouter la couche des clients ERP si demandée
    if show_erp_clients and erp_client_data is not None and len(erp_client_data) > 0:
        erp_client_layer = _create_erp_client_layer(erp_client_data)
        layers.append(erp_client_layer)
    
    # Calculer le centre de vue (centré sur la recherche si présente)
    if search_location:
        view_state = pdk.ViewState(
            latitude=search_location['latitude'],
            longitude=search_location['longitude'],
            zoom=15,
            pitch=0,
            bearing=0
        )
    else:
        view_state = _calculate_view_state(data_visual)
    
    # Créer un tooltip simple (non-interactif) car l'interaction se fait via sélection
    tooltip_config = _create_simple_tooltip(data_visual)
    
    # Sélectionner le style de carte
    selected_style = MAP_CONFIG['MAPBOX_STYLES'].get(map_style, MAP_CONFIG['MAPBOX_STYLES']['Plan Standard'])
    
    # Utiliser le style OpenStreetMap si pas de clé Mapbox et style satellite demandé
    if not mapbox_api_key and map_style in ['Satellite', 'Satellite + Rues']:
        selected_style = MAP_CONFIG['MAPBOX_STYLES']['OpenStreetMap']
        logger.info("Pas de clé Mapbox: utilisation d'OpenStreetMap au lieu du style satellite")
    
    # Paramètres supplémentaires pour améliorer l'interaction
    deck_params = {
        'map_style': selected_style,
        'initial_view_state': view_state,
        'layers': layers,
        'tooltip': tooltip_config,
        'map_provider': 'mapbox' if mapbox_api_key and map_style != 'OpenStreetMap' else None,
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

def _prepare_visual_data_robust(data: pd.DataFrame, color_by: str = "Consommation", opacity: float = 0.7) -> pd.DataFrame:
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
    
    # Déterminer la valeur à utiliser pour la coloration
    if color_by == "Nombre de logements" and 'nombre_de_logements' in data_visual.columns:
        color_values = data_visual['nombre_de_logements'].fillna(1)
        min_val = color_values.min()
        max_val = color_values.max()
    elif color_by == "Surface estimée":
        # Estimer la surface basée sur la consommation (100 kWh/m²/an en moyenne)
        color_values = data_visual['consommation_kwh'] / 100
        min_val = color_values.min()
        max_val = color_values.quantile(0.90)
    else:  # Par défaut : Consommation
        color_values = data_visual['consommation_kwh']
        min_val = color_values.min()
        max_val = color_values.quantile(0.90)
    
    # Normaliser les valeurs (0-1)
    if max_val > min_val:
        values_normalized = (color_values - min_val) / (max_val - min_val)
    else:
        values_normalized = pd.Series([0.5] * len(color_values))
    values_normalized = np.clip(values_normalized, 0, 1)
    
    # Ajuster l'opacité
    opacity_int = int(opacity * 255)
    
    # Palette de couleurs avec opacité ajustable
    COLOR_RANGE_CUSTOM = [
        [144, 238, 144, opacity_int],  # Vert clair
        [173, 255, 47, opacity_int],   # Vert-jaune
        [255, 255, 0, opacity_int],    # Jaune
        [255, 165, 0, opacity_int],    # Orange
        [255, 69, 0, opacity_int],     # Rouge-orange
        [220, 20, 60, opacity_int],    # Rouge foncé
    ]
    
    # Assigner les couleurs
    color_indices = (values_normalized * (len(COLOR_RANGE_CUSTOM) - 1)).astype(int)
    color_indices = np.clip(color_indices, 0, len(COLOR_RANGE_CUSTOM) - 1)
    
    colors = []
    for idx in color_indices:
        colors.append(COLOR_RANGE_CUSTOM[idx])
    
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

def _create_robust_cadastral_layer(data: pd.DataFrame, show_borders: bool = True) -> pdk.Layer:
    """Crée une couche cadastrale 2D avec interaction améliorée."""
    
    data_list = data.to_dict('records')
    
    # Définir la couleur et largeur des bordures selon le paramètre
    if show_borders:
        line_color = [0, 0, 0, 255]  # Noir
        line_width_min = 2
        line_width_max = 4
    else:
        line_color = [0, 0, 0, 0]  # Transparent
        line_width_min = 0
        line_width_max = 0
    
    return pdk.Layer(
        'PolygonLayer',
        data=data_list,
        get_polygon='footprint_polygon',
        get_fill_color='fill_color',
        extruded=False,
        pickable=True,
        filled=True,
        get_line_color=line_color,
        line_width_min_pixels=line_width_min,
        line_width_max_pixels=line_width_max,
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

def _create_dpe_layer(dpe_data: pd.DataFrame) -> pdk.Layer:
    """Crée une couche pour afficher les points DPE."""
    # Importer la fonction de couleur depuis data_handler
    from .data_handler import create_dpe_color_map
    
    # Ajouter les couleurs selon la classe énergétique
    dpe_visual = dpe_data.copy()
    dpe_visual['fill_color'] = dpe_visual['dpe_classe_energie'].apply(create_dpe_color_map)
    
    return pdk.Layer(
        'ScatterplotLayer',
        data=dpe_visual,
        get_position=['longitude', 'latitude'],
        get_fill_color='fill_color',
        get_line_color=[0, 0, 0, 100],
        get_radius=15,  # Rayon fixe de 15m
        radius_min_pixels=5,
        radius_max_pixels=20,
        pickable=True,
        auto_highlight=True,
        line_width_min_pixels=1
    )

def _create_search_marker_layer(location: dict) -> pdk.Layer:
    """Crée un marqueur pour indiquer le point de recherche."""
    marker_data = pd.DataFrame([{
        'latitude': location['latitude'],
        'longitude': location['longitude'],
        'address': location.get('address', 'Point recherché')
    }])
    
    return pdk.Layer(
        'IconLayer',
        data=marker_data,
        get_position=['longitude', 'latitude'],
        get_icon={
            'url': 'https://raw.githubusercontent.com/visgl/deck.gl-data/master/website/icon-atlas.png',
            'width': 128,
            'height': 128,
            'anchorY': 128,
            'mask': True
        },
        get_size=40,
        get_color=[255, 0, 0, 200],  # Rouge
        pickable=True
    )

def _create_erp_client_layer(erp_data: pd.DataFrame) -> pdk.Layer:
    """Crée une couche pour afficher les clients ERP."""
    
    # Préparer les données pour l'affichage
    erp_visual = erp_data.copy()
    
    # S'assurer que les couleurs sont au bon format
    if 'color' in erp_visual.columns:
        # Convertir les couleurs si nécessaire
        erp_visual['fill_color'] = erp_visual['color']
    else:
        # Couleurs par défaut selon le type
        color_map = {
            'producteur': [0, 255, 0, 200],     # Vert
            'consommateur': [255, 0, 0, 200],   # Rouge
            'prosumer': [0, 0, 255, 200]        # Bleu
        }
        erp_visual['fill_color'] = erp_visual['type_client'].map(color_map).fillna([128, 128, 128, 200])
    
    # Créer le tooltip HTML pour les clients ERP
    erp_visual['tooltip_html'] = erp_visual.apply(
        lambda row: f"""
        <div style="
            background-color: #ffffff; 
            padding: 15px; 
            border-radius: 8px; 
            border: 2px solid #1E88E5; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.2); 
            font-family: 'Segoe UI', Arial, sans-serif; 
            font-size: 13px; 
            max-width: 300px;
            color: #2c3e50;
        ">
            <div style="font-weight: bold; margin-bottom: 10px; font-size: 16px; color: #1E88E5;">
                🏢 {row.get('nom', 'Client ERP')}
            </div>
            
            <div style="margin-bottom: 6px;">
                <b>📋 Type:</b> {row.get('type_client', 'N/A')}
            </div>
            
            <div style="margin-bottom: 6px;">
                <b>🏷️ Code:</b> {row.get('code_client', 'N/A')}
            </div>
            
            <div style="margin-bottom: 6px;">
                <b>📍 Adresse:</b> {row.get('adresse', 'N/A')}
            </div>
            
            <div style="margin-bottom: 6px;">
                <b>🏘️ Zone:</b> {row.get('zone_geographique', 'N/A')}
            </div>
            
            <div style="margin: 10px 0; padding: 8px; background-color: #e3f2fd; border-radius: 6px; border-left: 4px solid #1E88E5;">
                <b>💰 Prix:</b> {row.get('prix_kwh', 0):.3f} €/kWh
            </div>
            
            <div style="font-size: 11px; color: #95a5a6; margin-top: 10px; text-align: center; font-style: italic;">
                Module ERP - Gestion Clients
            </div>
        </div>
        """, axis=1
    )
    
    return pdk.Layer(
        'ScatterplotLayer',
        data=erp_visual,
        get_position=['longitude', 'latitude'],
        get_fill_color='fill_color',
        get_line_color=[255, 255, 255, 255],
        get_radius=150,  # Rayon de 150m pour être visible
        radius_min_pixels=10,
        radius_max_pixels=30,
        pickable=True,
        auto_highlight=True,
        line_width_min_pixels=2,
        opacity=0.8
    )