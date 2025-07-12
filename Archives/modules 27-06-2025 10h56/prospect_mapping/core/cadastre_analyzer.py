#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'analyse cadastrale pour OptimPV.
Responsabilité : Récupération des données cadastrales et calcul du potentiel solaire.
"""

import logging
import requests
import math
import time
from typing import Dict, Optional, Tuple
from functools import lru_cache

logger = logging.getLogger(__name__)

# Import du module de précision
try:
    from .precision_helper import PrecisionHelper
    PRECISION_HELPER_AVAILABLE = True
except ImportError:
    PRECISION_HELPER_AVAILABLE = False
    logger.warning("Module precision_helper non disponible")

# Import conditionnel des librairies géométriques
try:
    from shapely.geometry import Polygon, Point
    from shapely.ops import transform
    import pyproj
    GEOMETRY_LIBS_AVAILABLE = True
except ImportError:
    # Fallback sans les librairies géométriques
    GEOMETRY_LIBS_AVAILABLE = False
    logger.warning("Libraries shapely/pyproj non disponibles, utilisation de géométrie basique")

class CadastreAnalyzer:
    """Analyse cadastrale pour le calcul du potentiel photovoltaïque"""
    
    def __init__(self):
        """Initialisation du module d'analyse cadastrale"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OptimPV/2.0 (analyse-cadastrale)'
        })
        
        # URLs des APIs
        # BD TOPO IGN désactivé (problème de connectivité)
        # self.bdtopo_url = "https://wxs.ign.fr/choisirgeoportail/geoportail/wfs"
        self.bdtopo_url = None  # Désactivé, utilise OSM directement
        self.cadastre_url = "https://apicarto.ign.fr/api/cadastre/parcelle"
        
        # Cache pour éviter les appels répétés
        self._cache = {}
        self._cache_timeout = 24 * 3600  # 24h
        
        # Configuration APIs
        self.config = {
            'BDTOPO_FULL': True,
            'DPE_ADEME': True,
            'DPE_API_URL': 'https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines',
            'DPE_CACHE_TTL': 86400 * 30,  # Cache 30 jours
        }
        
        # Module de précision
        self.precision_helper = PrecisionHelper() if PRECISION_HELPER_AVAILABLE else None
        
    @lru_cache(maxsize=1000)
    def get_building_footprint(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Récupère l'emprise au sol du bâtiment via BD TOPO IGN
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dict avec les informations du bâtiment ou None
        """
        try:
            # BD TOPO IGN désactivé - Utiliser directement OSM
            if self.bdtopo_url is None:
                logger.info("BD TOPO désactivé, utilisation directe d'OSM")
                return self._get_osm_building_fallback(lat, lon)
            
            # Code BD TOPO conservé mais ne sera pas exécuté
            params = {
                'service': 'WFS',
                'version': '2.0.0',
                'request': 'GetFeature',
                'typename': 'BDTOPO_V3:batiment',
                'outputFormat': 'application/json',
                'crs': 'EPSG:4326',
                'bbox': f"{lon-0.001},{lat-0.001},{lon+0.001},{lat+0.001}"
            }
            
            response = self.session.get(self.bdtopo_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('features'):
                    # Prendre le bâtiment le plus proche
                    if GEOMETRY_LIBS_AVAILABLE:
                        point = Point(lon, lat)
                    else:
                        point = (lon, lat)  # Simple tuple
                    closest_building = None
                    min_distance = float('inf')
                    
                    for feature in data['features']:
                        if feature['geometry']['type'] == 'Polygon':
                            if GEOMETRY_LIBS_AVAILABLE:
                                building_poly = Polygon(feature['geometry']['coordinates'][0])
                                distance = point.distance(building_poly.centroid)
                            else:
                                # Calcul de distance simple sans shapely
                                coords = feature['geometry']['coordinates'][0]
                                center_lon = sum(c[0] for c in coords) / len(coords)
                                center_lat = sum(c[1] for c in coords) / len(coords)
                                distance = math.sqrt((point[0] - center_lon)**2 + (point[1] - center_lat)**2)
                            
                            if distance < min_distance:
                                min_distance = distance
                                closest_building = feature
                    
                    if closest_building:
                        props = closest_building['properties']
                        coords = closest_building['geometry']['coordinates'][0]
                        
                        if GEOMETRY_LIBS_AVAILABLE:
                            geometry = Polygon(coords)
                        else:
                            geometry = coords  # Liste de coordonnées simple
                        
                        return {
                            'geometry': geometry,
                            'surface': props.get('SURFACE', 100),
                            'hauteur': props.get('HAUTEUR', 6),
                            'nature': props.get('NATURE', 'Bâtiment'),
                            'usage': props.get('USAGE_1', 'Résidentiel'),
                            # NOUVEAUX CHAMPS BD TOPO ENRICHIS
                            'nature_detaillee': props.get('NATURE_DETAILLEE'),
                            'etat_batiment': props.get('ETAT_BATIMENT', 'En service'),
                            'nb_etages': props.get('NB_ETAGES', 0),
                            'nb_logements': props.get('NB_LOGEMENTS', 1),
                            'materiaux': props.get('MATERIAUX'),
                            'date_construction': props.get('DATE_CONS'),
                            'toponyme': props.get('TOPONYME'),
                            'usage_2': props.get('USAGE_2'),  # Usage secondaire
                            'source': 'BD_TOPO_IGN',
                            'confidence': 'high'
                        }
            
        except Exception as e:
            logger.warning(f"Erreur récupération bâtiment BD TOPO pour {lat},{lon}: {e}")
            
        # Fallback 1: Essayer OpenStreetMap via precision_helper
        if self.precision_helper:
            try:
                osm_buildings = self.precision_helper.get_building_candidates_osm(lat, lon, 50)
                if osm_buildings:
                    best_building = osm_buildings[0]  # Le plus proche
                    
                    if GEOMETRY_LIBS_AVAILABLE:
                        # Créer polygon à partir des coordonnées OSM
                        coords = [(p['lon'], p['lat']) for p in best_building['coords']]
                        geometry = Polygon(coords) if len(coords) >= 3 else coords
                    else:
                        geometry = [(p['lon'], p['lat']) for p in best_building['coords']]
                    
                    # Mapper les types de bâtiments OSM vers des noms français
                    building_type_map = {
                        'residential': 'Bâtiment résidentiel',
                        'house': 'Maison individuelle',
                        'apartments': 'Immeuble d\'appartements',
                        'commercial': 'Bâtiment commercial',
                        'office': 'Bâtiment de bureaux',
                        'industrial': 'Bâtiment industriel',
                        'retail': 'Commerce',
                        'hotel': 'Hôtel',
                        'hospital': 'Établissement de santé',
                        'school': 'Établissement scolaire'
                    }
                    
                    # Estimer le nombre d'étages basé sur la hauteur
                    estimated_floors = max(1, int(best_building.get('height', 6) / 3))
                    
                    return {
                        'geometry': geometry,
                        'surface': best_building['surface_m2'],
                        'hauteur': best_building.get('height', 6),
                        'nature': 'Bâtiment',
                        'usage': 'Résidentiel' if best_building['building_type'] == 'residential' else 'Autre',
                        # CHAMPS ENRICHIS CORRECTEMENT MAPPÉS
                        'nature_detaillee': building_type_map.get(best_building['building_type'], f"Bâtiment {best_building['building_type']}"),
                        'etat_batiment': 'En service',
                        'nb_etages': estimated_floors,
                        'nb_logements': estimated_floors if best_building['building_type'] == 'residential' else 1,
                        'materiaux': 'Non précisé',
                        'date_construction': 'Non précisée',
                        'source': 'OSM',
                        'confidence': 'high' if best_building['distance'] < 20 else 'medium',
                        'distance_m': best_building['distance']
                    }
                    
            except Exception as osm_error:
                logger.warning(f"Erreur OSM fallback pour {lat},{lon}: {osm_error}")
        
        # Fallback 2: Bâtiment fictif avec informations de précision
        return self._create_fallback_building(lat, lon)
    
    def _create_fallback_building(self, lat: float, lon: float) -> Dict:
        """Crée un bâtiment fictif si l'API échoue"""
        # Carré de 10x10m autour du point
        offset = 0.00005  # ~5m en degrés
        coords = [
            [lon - offset, lat - offset],
            [lon + offset, lat - offset],
            [lon + offset, lat + offset],
            [lon - offset, lat + offset],
            [lon - offset, lat - offset]
        ]
        
        if GEOMETRY_LIBS_AVAILABLE:
            geometry = Polygon(coords)
        else:
            geometry = coords  # Liste de coordonnées simple
        
        return {
            'geometry': geometry,
            'surface': 100,
            'hauteur': 6,
            'nature': 'Bâtiment',
            'usage': 'Résidentiel',
            'source': 'Estimation',
            'confidence': 'low',
            'distance_m': 0,
            'precision_note': 'Bâtiment non localisé précisément - valeurs estimées'
        }
    
    def get_building_dpe(self, lat: float, lon: float, radius: int = 50) -> Optional[Dict]:
        """
        Récupère les DPE des bâtiments proches via l'API ADEME
        
        Args:
            lat: Latitude
            lon: Longitude  
            radius: Rayon de recherche en mètres
            
        Returns:
            Dict avec les données DPE ou None
        """
        if not self.config.get('DPE_ADEME', True):
            return None
            
        cache_key = f"dpe_{lat:.5f}_{lon:.5f}_{radius}"
        
        # Vérifier le cache
        if cache_key in self._cache:
            cache_data = self._cache[cache_key]
            if time.time() - cache_data['timestamp'] < self.config['DPE_CACHE_TTL']:
                logger.debug(f"DPE cache hit pour {lat},{lon}")
                return cache_data['data']
        
        try:
            logger.info(f"Recherche DPE pour {lat:.5f},{lon:.5f} dans rayon {radius}m")
            
            # Calculer une bounding box autour du point
            # Conversion approximative : 1° ≈ 111km
            radius_deg = radius / 111000  # Convertir mètres en degrés
            
            bbox_lon_min = lon - radius_deg
            bbox_lat_min = lat - radius_deg  
            bbox_lon_max = lon + radius_deg
            bbox_lat_max = lat + radius_deg
            
            # Paramètres pour l'API ADEME DPE (utilisation bbox)
            params = {
                'size': 20,  # Plus de résultats pour avoir le choix
                'bbox': f'{bbox_lon_min},{bbox_lat_min},{bbox_lon_max},{bbox_lat_max}',
                'select': 'Etiquette_GES,Conso_5_usages_par_m²_é_primaire,Emission_GES_5_usages_par_m²,Année_construction,Type_bâtiment,Surface_habitable_logement,Type_énergie_n°1,Surface_climatisée,Adresse_(BAN),_geopoint'
            }
            
            response = self.session.get(
                self.config['DPE_API_URL'], 
                params=params, 
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('results') and len(data['results']) > 0:
                    # Filtrer par distance réelle et prendre le plus proche
                    valid_dpes = []
                    
                    for dpe in data['results']:
                        # Extraire coordonnées du _geopoint
                        geopoint = dpe.get('_geopoint', {})
                        if isinstance(geopoint, dict):
                            dpe_lat = float(geopoint.get('lat', lat))
                            dpe_lon = float(geopoint.get('lon', lon))
                        else:
                            # Si _geopoint est une string "lat,lon"
                            try:
                                coords = str(geopoint).split(',')
                                dpe_lat = float(coords[0])
                                dpe_lon = float(coords[1])
                            except:
                                continue  # Skip ce DPE
                        
                        distance = self._calculate_distance(lat, lon, dpe_lat, dpe_lon)
                        
                        if distance <= radius:
                            valid_dpes.append((dpe, distance))
                    
                    if valid_dpes:
                        # Analyser plusieurs DPE pour avoir une vue d'ensemble
                        logger.info(f"Trouvé {len(valid_dpes)} DPE dans rayon {radius}m")
                        
                        # Trier par distance et analyser les plus proches
                        valid_dpes.sort(key=lambda x: x[1])
                        
                        # Si plusieurs DPE très proches, donner des statistiques
                        if len(valid_dpes) > 1:
                            # Analyser les DPE de même adresse/bâtiment (distance < 10m)
                            same_building = [dpe for dpe, dist in valid_dpes if dist < 10]
                            
                            if len(same_building) > 1:
                                logger.info(f"Multiple DPE pour même bâtiment: {len(same_building)} trouvés")
                                
                                # Calculer les moyennes pour donner une estimation plus représentative
                                total_surface = sum(float(dpe.get('Surface_habitable_logement', 0) or 0) for dpe in same_building)
                                total_conso = sum(float(dpe.get('Conso_5_usages_par_m²_é_primaire', 0) or 0) for dpe in same_building)
                                
                                avg_surface = total_surface / len(same_building) if len(same_building) > 0 else 0
                                avg_conso = total_conso / len(same_building) if len(same_building) > 0 else 0
                                
                                # Prendre le premier pour les autres infos, mais avec moyennes calculées
                                best_dpe, best_distance = valid_dpes[0]
                                
                                # Calculer la classe énergie à partir de la consommation moyenne
                                classe_energie = self._get_classe_energie_from_conso(avg_conso)
                                
                                return {
                                    'classe_energie': classe_energie,
                                    'classe_ges': best_dpe.get('Etiquette_GES', 'N/A'), 
                                    'consommation_energie': avg_conso,
                                    'surface_habitable': avg_surface,
                                    'annee_construction': best_dpe.get('Année_construction', 'N/A'),
                                    'type_batiment': best_dpe.get('Type_bâtiment', 'N/A'),
                                    'type_energie_chauffage': best_dpe.get('Type_énergie_n°1', 'N/A'),
                                    'presence_climatisation': best_dpe.get('Surface_climatisée', 0) > 0,
                                    'adresse': best_dpe.get('Adresse_(BAN)', 'N/A'),
                                    'distance_m': best_distance,
                                    'source': 'ADEME_DPE_V2',
                                    'nb_dpe_analyses': len(same_building),
                                    'note': f"Moyenne de {len(same_building)} DPE du même bâtiment"
                                }
                        
                        # Sinon, prendre le plus proche
                        best_dpe, distance = valid_dpes[0]
                        # Déduire classe énergie depuis consommation
                        conso_primaire = float(best_dpe.get('Conso_5_usages_par_m²_é_primaire', 0) or 0)
                        classe_energie = self._get_classe_energie_from_conso(conso_primaire)
                            
                        dpe_data = {
                            'classe_energie': classe_energie,
                            'classe_ges': best_dpe.get('Etiquette_GES', 'N/A'),
                            'consommation_energie': conso_primaire,
                            'annee_construction': best_dpe.get('Année_construction'),
                            'type_batiment': best_dpe.get('Type_bâtiment', 'Maison'),
                            'surface_habitable': best_dpe.get('Surface_habitable_logement', 0),
                            'type_energie_chauffage': best_dpe.get('Type_énergie_n°1', 'Électricité'),
                            'presence_climatisation': bool(best_dpe.get('Surface_climatisée', 0) > 0),
                            'adresse': best_dpe.get('Adresse_(BAN)', ''),
                            'distance_m': round(distance, 1),
                            'source': 'ADEME_DPE_V2'
                        }
                        
                        # Mettre en cache
                        self._cache[cache_key] = {
                            'data': dpe_data,
                            'timestamp': time.time()
                        }
                        
                        logger.info(f"DPE trouvé: classe {dpe_data['classe_energie']} à {distance:.1f}m")
                        return dpe_data
            else:
                logger.warning(f"Erreur API DPE: status {response.status_code}")
                
        except Exception as e:
            logger.warning(f"Erreur récupération DPE pour {lat},{lon}: {e}")
        
        # Cache le résultat négatif pour éviter les appels répétés
        self._cache[cache_key] = {
            'data': None,
            'timestamp': time.time()
        }
        
        return None
    
    def _get_classe_energie_from_conso(self, conso_primaire: float) -> str:
        """Convertit une consommation en kWh/m²/an vers classe énergie DPE"""
        if conso_primaire <= 50:
            return 'A'
        elif conso_primaire <= 90:
            return 'B'
        elif conso_primaire <= 150:
            return 'C'
        elif conso_primaire <= 230:
            return 'D'
        elif conso_primaire <= 330:
            return 'E'
        elif conso_primaire <= 450:
            return 'F'
        else:
            return 'G'
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcule la distance en mètres entre deux points GPS"""
        # Formule de Haversine simplifiée
        R = 6371000  # Rayon de la Terre en mètres
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2) 
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def calculate_roof_area(self, building_data: Dict) -> float:
        """
        Calcule la surface de toiture exploitable avec données enrichies BD TOPO
        
        Args:
            building_data: Données du bâtiment enrichies
            
        Returns:
            Surface de toiture en m²
        """
        try:
            surface_sol = building_data.get('surface', 100)
            usage = building_data.get('usage', 'Résidentiel').lower()
            nature = building_data.get('nature', 'Bâtiment').lower()
            nature_detaillee = building_data.get('nature_detaillee', '').lower()
            nb_etages = building_data.get('nb_etages', 0)
            
            # Utiliser nb_etages pour affiner le calcul
            if nb_etages > 3:
                # Immeuble : seul le dernier étage compte pour le solaire
                surface_toit_base = surface_sol
                coeff_toit = 1.0  # Généralement toit plat
            else:
                # Maison/petit bâtiment : toute la surface disponible
                surface_toit_base = surface_sol
                
                # Affiner selon nature_detaillee
                if 'industriel' in nature_detaillee and 'leger' in nature_detaillee:
                    coeff_toit = 1.0  # Toit plat quasi certain
                elif 'collectif' in nature_detaillee:
                    coeff_toit = 1.0  # Immeubles = toit plat souvent
                elif 'maison' in nature_detaillee or 'individuel' in nature_detaillee:
                    coeff_toit = 1.3  # Toit 2 pans avec surface inclinée
                elif 'logistique' in nature_detaillee:
                    coeff_toit = 1.0  # Grandes surfaces, toits plats
                    surface_toit_base *= 1.2  # Bonus pour grandes surfaces
                elif 'commercial' in nature_detaillee:
                    coeff_toit = 1.0  # Généralement toit plat
                else:
                    # Fallback selon usage classique
                    if 'industriel' in usage or 'commercial' in usage:
                        coeff_toit = 1.0  # Toit plat
                    elif 'résidentiel' in usage or 'maison' in nature:
                        coeff_toit = 1.2  # Toit 2 pans
                    else:
                        coeff_toit = 1.1  # Mixte
            
            # Surface exploitable (retrait sécurité)
            # Adapté selon le type de bâtiment
            if 'logistique' in nature_detaillee or 'industriel' in nature_detaillee:
                retrait_securite = 0.8  # 20% de retrait (moins d'obstacles)
            elif nb_etages > 5:
                retrait_securite = 0.6  # 40% de retrait (installations techniques)
            else:
                retrait_securite = 0.7  # 30% de retrait standard
            
            surface_toiture = surface_toit_base * coeff_toit * retrait_securite
            
            # Minimum adapté au type de bâtiment
            min_surface = 20 if nb_etages <= 2 else 50
            
            return max(surface_toiture, min_surface)
            
        except Exception as e:
            logger.warning(f"Erreur calcul surface toiture: {e}")
            return 80  # Valeur par défaut
    
    def analyze_roof_orientation(self, building_polygon) -> float:
        """
        Détermine l'orientation principale du bâtiment
        
        Args:
            building_polygon: Polygone du bâtiment
            
        Returns:
            Azimut en degrés (180° = plein sud)
        """
        try:
            # Récupérer les coordonnées du polygone
            if GEOMETRY_LIBS_AVAILABLE and hasattr(building_polygon, 'exterior'):
                coords = list(building_polygon.exterior.coords)
            else:
                # Fallback: building_polygon est une liste de coordonnées
                coords = building_polygon if isinstance(building_polygon, list) else []
            
            # Calculer l'orientation du plus long côté
            max_length = 0
            best_orientation = 180  # Par défaut plein sud
            
            for i in range(len(coords) - 1):
                x1, y1 = coords[i]
                x2, y2 = coords[i + 1]
                
                # Longueur du segment
                length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                
                if length > max_length:
                    max_length = length
                    # Calculer l'azimut (0° = Nord, 90° = Est, 180° = Sud, 270° = Ouest)
                    angle = math.degrees(math.atan2(x2 - x1, y2 - y1))
                    # Normaliser entre 0 et 360
                    azimut = (angle + 360) % 360
                    
                    # Prendre l'orientation la plus proche du sud (180°)
                    if abs(azimut - 180) > abs((azimut + 180) % 360 - 180):
                        azimut = (azimut + 180) % 360
                    
                    best_orientation = azimut
            
            return best_orientation
            
        except Exception as e:
            logger.warning(f"Erreur calcul orientation: {e}")
            return 180  # Plein sud par défaut
    
    def estimate_roof_slope(self, height: float, usage: str) -> float:
        """
        Estime l'inclinaison de la toiture
        
        Args:
            height: Hauteur du bâtiment
            usage: Type d'usage du bâtiment
            
        Returns:
            Angle d'inclinaison en degrés
        """
        usage_lower = usage.lower()
        
        if 'industriel' in usage_lower or 'commercial' in usage_lower:
            return 5  # Toit plat/faible pente
        elif 'résidentiel' in usage_lower:
            if height > 15:  # Immeuble
                return 15
            else:  # Maison individuelle
                return 30
        else:
            return 20  # Valeur moyenne
    
    def detect_roof_obstacles(self, lat: float, lon: float, radius: int = 50) -> Dict:
        """
        Détecte les obstacles proches (optionnel via OSM)
        
        Args:
            lat: Latitude
            lon: Longitude
            radius: Rayon de recherche en mètres
            
        Returns:
            Dict avec les obstacles détectés
        """
        # Pour l'instant, estimation simple
        # TODO: Intégrer Overpass API si nécessaire
        
        return {
            'trees_nearby': False,
            'buildings_shadow': False,
            'obstacles_score': 0.9  # 90% de surface libre
        }
    
    def calculate_solar_potential(self, roof_area: float, orientation: float, 
                                slope: float, obstacles: Optional[Dict] = None) -> float:
        """
        Calcule le potentiel d'installation en kWc
        
        Args:
            roof_area: Surface de toiture en m²
            orientation: Azimut en degrés
            slope: Inclinaison en degrés
            obstacles: Obstacles détectés
            
        Returns:
            Puissance installable en kWc
        """
        try:
            # Surface utile (marge sécurité déjà appliquée)
            surface_utile = roof_area
            
            # Facteur d'orientation (1.0 = plein sud, 0.7 = est/ouest, 0.3 = nord)
            angle_deviation = abs(orientation - 180)
            if angle_deviation <= 45:  # Sud ± 45°
                facteur_orientation = math.cos(math.radians(angle_deviation))
            elif angle_deviation <= 135:  # Est/Ouest
                facteur_orientation = 0.7
            else:  # Nord
                facteur_orientation = 0.3
            
            # Facteur d'inclinaison (optimal entre 20-40°)
            if 20 <= slope <= 40:
                facteur_inclinaison = 0.95
            elif 10 <= slope <= 50:
                facteur_inclinaison = 0.85
            elif slope < 10:
                facteur_inclinaison = 0.75  # Toit plat
            else:
                facteur_inclinaison = 0.70  # Trop pentu
            
            # Facteur obstacles
            facteur_obstacles = obstacles.get('obstacles_score', 0.9) if obstacles else 0.9
            
            # Calcul puissance avec panneaux 440W (1 kWc ≈ 5.5m² avec espacement moderne)
            # Panneaux 440W = 2.2m² par panneau → 1 kWc = 2.27 panneaux = 5m² utiles + espacement
            puissance_kwc = (surface_utile / 5.5) * facteur_orientation * facteur_inclinaison * facteur_obstacles
            
            # Limites réalistes
            return max(min(puissance_kwc, 36), 0.5)  # Entre 0.5 et 36 kWc
            
        except Exception as e:
            logger.warning(f"Erreur calcul potentiel solaire: {e}")
            return 6.0  # Valeur par défaut 6 kWc
    
    def calculate_production_annual(self, kwc_installed: float, lat: float) -> float:
        """
        Calcule la production annuelle estimée
        
        Args:
            kwc_installed: Puissance installée en kWc
            lat: Latitude pour l'irradiation
            
        Returns:
            Production annuelle en kWh
        """
        try:
            # Irradiation selon latitude (France)
            if lat >= 45:  # Nord
                irradiation_kwh_kwc = 1200
            elif lat >= 44:  # Centre
                irradiation_kwh_kwc = 1300
            else:  # Sud (Alpes-Maritimes)
                irradiation_kwh_kwc = 1400
            
            # Performance du système (pertes onduleur, câblage, etc.)
            facteur_performance = 0.85
            
            production_annuelle = kwc_installed * irradiation_kwh_kwc * facteur_performance
            
            return round(production_annuelle, 0)
            
        except Exception as e:
            logger.warning(f"Erreur calcul production: {e}")
            return kwc_installed * 1200  # Fallback conservateur
    
    def analyze_complete_prospect(self, lat: float, lon: float, 
                                consumption_kwh: float) -> Dict:
        """
        Analyse complète d'un prospect
        
        Args:
            lat: Latitude
            lon: Longitude  
            consumption_kwh: Consommation annuelle en kWh
            
        Returns:
            Dict avec toutes les analyses
        """
        try:
            # 1. Récupérer le bâtiment
            building_data = self.get_building_footprint(lat, lon)
            
            if not building_data:
                return self._get_default_analysis(consumption_kwh)
            
            # 2. Récupérer les DPE si activé
            dpe_data = None
            if self.config.get('DPE_ADEME', True):
                dpe_data = self.get_building_dpe(lat, lon)
                if dpe_data:
                    logger.info(f"BD TOPO enrichie : {len([k for k in building_data.keys() if k not in ['geometry', 'surface', 'hauteur', 'nature', 'usage']])} nouveaux champs récupérés")
                    logger.info(f"DPE trouvé : classe {dpe_data['classe_energie']} à {dpe_data['distance_m']}m")
            
            # 3. Analyses
            roof_area = self.calculate_roof_area(building_data)
            orientation = self.analyze_roof_orientation(building_data['geometry'])
            slope = self.estimate_roof_slope(building_data['hauteur'], building_data['usage'])
            obstacles = self.detect_roof_obstacles(lat, lon)
            
            # 4. Potentiel solaire
            solar_potential = self.calculate_solar_potential(roof_area, orientation, slope, obstacles)
            annual_production = self.calculate_production_annual(solar_potential, lat)
            
            # 5. Score de prospection enrichi
            prospect_score = self._calculate_prospect_score(
                annual_production, consumption_kwh, orientation, solar_potential,
                building_data, dpe_data
            )
            
            result = {
                'roof_area_m2': round(roof_area, 1),
                'roof_orientation': round(orientation, 0),
                'roof_slope': round(slope, 0),
                'solar_potential_kwc': round(solar_potential, 1),
                'production_annual_kwh': round(annual_production, 0),
                'prospect_score': prospect_score,
                'building_height': building_data['hauteur'],
                'building_usage': building_data['usage'],
                # Informations de précision
                'data_source': building_data.get('source', 'IGN'),
                'location_confidence': building_data.get('confidence', 'medium'),
                'distance_to_building': building_data.get('distance_m', 0),
                'precision_note': building_data.get('precision_note', ''),
                'surface_source': f"Surface {building_data.get('source', 'estimée')}: {round(roof_area, 1)}m²",
                
                # NOUVELLES DONNÉES BÂTIMENT ENRICHIES
                'nature_detaillee': building_data.get('nature_detaillee', 'Non précisé'),
                'nb_etages': building_data.get('nb_etages', 0),
                'etat_batiment': building_data.get('etat_batiment', 'N/A'),
                'date_construction': building_data.get('date_construction', 'N/A'),
                'nb_logements': building_data.get('nb_logements', 1),
                'materiaux': building_data.get('materiaux', 'N/A'),
                'toponyme': building_data.get('toponyme', ''),
                'usage_2': building_data.get('usage_2', ''),
            }
            
            # Ajouter les données DPE si disponibles
            if dpe_data:
                result['dpe_data'] = dpe_data
                result['dpe_available'] = True
                result['dpe_classe_energie'] = dpe_data['classe_energie']
                result['dpe_classe_ges'] = dpe_data['classe_ges']
                result['dpe_consommation'] = dpe_data['consommation_energie']
                result['dpe_distance'] = dpe_data['distance_m']
            else:
                result['dpe_available'] = False
                result['dpe_classe_energie'] = 'N/A'
                result['dpe_classe_ges'] = 'N/A'
                result['dpe_consommation'] = 0
                result['dpe_distance'] = None
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur analyse complète pour {lat},{lon}: {e}")
            return self._get_default_analysis(consumption_kwh)
    
    def _calculate_prospect_score(self, production: float, consumption: float, 
                                orientation: float, kwc: float, building_data: Dict = None, 
                                dpe_data: Dict = None) -> int:
        """Calcule le score de prospection enrichi (0-100)"""
        try:
            # Base: Taux d'autoconsommation (30% du score)
            autoconso_rate = min(production / consumption, 1.0) if consumption > 0 else 0.5
            score_autoconso = autoconso_rate * 30
            
            # Score orientation (25% du score)
            orientation_score = max(0, 1 - abs(orientation - 180) / 180) * 25
            
            # Score taille installation (25% du score)
            size_score = min(kwc / 9, 1.0) * 25  # 9 kWc = max résidentiel type
            
            base_score = score_autoconso + orientation_score + size_score
            
            # NOUVEAUX BONUS/MALUS avec données enrichies (20% du score total)
            bonus_malus = 0
            
            if building_data:
                # Bonus/malus selon état bâtiment
                etat = building_data.get('etat_batiment', '').lower()
                if 'en construction' in etat:
                    bonus_malus += 10  # Opportunité d'intégrer le PV dès le début
                elif 'détruit' in etat or 'en ruine' in etat:
                    bonus_malus -= 15  # Pas viable
                
                # Bonus si bâtiment récent (toiture en bon état)
                date_construction = building_data.get('date_construction')
                if date_construction:
                    try:
                        age = 2024 - int(date_construction)
                        if age < 10:
                            bonus_malus += 5  # Toiture récente
                        elif age > 40:
                            bonus_malus -= 5  # Toiture potentiellement à refaire
                    except (ValueError, TypeError):
                        pass
                
                # Ajustement selon type précis
                nature_det = building_data.get('nature_detaillee', '').lower()
                if 'logistique' in nature_det:
                    bonus_malus += 10  # Grandes surfaces, toits plats
                elif 'industriel' in nature_det and 'leger' in nature_det:
                    bonus_malus += 8  # Bon potentiel industriel
                elif 'commercial' in nature_det:
                    bonus_malus += 5  # Potentiel commercial
                
                # Bonus selon nombre d'étages
                nb_etages = building_data.get('nb_etages', 0)
                if nb_etages == 1:
                    bonus_malus += 3  # Maison plain-pied = toit accessible
                elif nb_etages > 6:
                    bonus_malus -= 3  # Contraintes techniques
            
            # Bonus si DPE mauvais (forte conso = bon potentiel éco solaire)
            if dpe_data:
                classe_energie = dpe_data.get('classe_energie', '')
                if classe_energie in ['F', 'G']:
                    bonus_malus += 15  # Fort potentiel d'économies
                elif classe_energie in ['D', 'E']:
                    bonus_malus += 8   # Bon potentiel
                elif classe_energie in ['A', 'B']:
                    bonus_malus -= 5   # Déjà performant énergétiquement
                
                # Bonus selon type d'énergie chauffage
                type_energie = dpe_data.get('type_energie_chauffage', '').lower()
                if 'électricité' in type_energie:
                    bonus_malus += 5  # Synérgie avec PV
                elif 'fioul' in type_energie:
                    bonus_malus += 8  # Fort potentiel de substitution
                elif 'gaz' in type_energie:
                    bonus_malus += 3  # Bon potentiel
            
            # Appliquer les bonus/malus (limité à ±20 points)
            bonus_malus = max(-20, min(bonus_malus, 20))
            
            total_score = base_score + bonus_malus
            
            return max(10, min(int(total_score), 100))
            
        except Exception as e:
            logger.warning(f"Erreur calcul score: {e}")
            return 50
    
    def _get_default_analysis(self, consumption_kwh: float) -> Dict:
        """Analyse par défaut si les APIs échouent"""
        # Estimation basique selon consommation
        estimated_kwc = min(consumption_kwh / 1200, 9)  # Max 9 kWc résidentiel
        
        return {
            'roof_area_m2': 80.0,
            'roof_orientation': 180.0,  # Plein sud
            'roof_slope': 30.0,
            'solar_potential_kwc': round(estimated_kwc, 1),
            'production_annual_kwh': round(estimated_kwc * 1300, 0),
            'prospect_score': 65,  # Score moyen
            'building_height': 6.0,
            'building_usage': 'Résidentiel'
        }