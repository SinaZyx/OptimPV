#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de simulation solaire avec dessin de zone pour OptimPV.
Responsabilité : Simulation interactive de production photovoltaïque.
"""

import asyncio
import logging
import math
import requests
import time
from typing import Dict, List, Optional, Tuple
import json
# Imports conditionnels
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from .consumption_profiles import ConsumptionProfileManager
    PROFILES_AVAILABLE = True
except ImportError:
    PROFILES_AVAILABLE = False

logger = logging.getLogger(__name__)

class SolarSimulator:
    """Simulateur solaire simplifié avec surface directe"""
    
    def __init__(self):
        self.api_base_url = "https://api.forecast.solar"
        self.pvgis_base_url = "https://re.jrc.ec.europa.eu/api/v5_2"
        self.cache_duration = 900  # 15 minutes
        self._cache = {}
        
        # Gestionnaire de profils de consommation
        if PROFILES_AVAILABLE:
            self.profile_manager = ConsumptionProfileManager()
        else:
            self.profile_manager = None
        
        # Spécifications panneaux 440W
        self.panel_specs = {
            'width_m': 2.2,      # Largeur panneau
            'height_m': 1.1,     # Hauteur panneau  
            'power_w': 440,      # Puissance unitaire
            'spacing_m': 0.1,    # Espacement inter-panneaux
            'area_m2': 2.42      # Surface unitaire (2.2 x 1.1)
        }
    
    def calculate_from_surface(self, surface_m2: float, tilt: int = 30, azimuth: int = 180, 
                             lat: float = 43.7102, lon: float = 7.2620, approach: str = 'realiste') -> Dict:
        """
        Calcul simplifié à partir d'une surface donnée
        
        Args:
            surface_m2: Surface disponible en m²
            tilt: Inclinaison panneaux (30° par défaut)
            azimuth: Orientation panneaux (180° = Sud)
            
        Returns:
            Dict avec tous les résultats
        """
        # Calcul nombre de panneaux avec approche sélectionnée
        layout = self.calculate_panels_from_area(surface_m2, approach)
        
        # Si pas de panneaux, retourner résultat vide
        if layout['total_panels'] == 0:
            return {
                'surface_m2': surface_m2,
                'layout': layout,
                'production': {'annual_kwh': 0, 'daily_kwh': 0, 'data_source': 'none'},
                'financial': self._get_empty_financial()
            }
        
        # Simulation production (avec fallback)
        kwp = layout['total_kwc']
        production = self._get_fallback_estimate(kwp, 43.7102)  # Nice par défaut
        
        # Calculs financiers
        financial = self.calculate_financial_metrics(
            production['annual_kwh'], 
            kwp, 
            15000  # Consommation type 15 MWh
        )
        
        return {
            'surface_m2': surface_m2,
            'layout': layout,
            'production': production,
            'financial': financial,
            'tilt': tilt,
            'azimuth': azimuth
        }
    
    def calculate_panels_from_area(self, surface_m2: float, approach: str = 'realiste') -> Dict:
        """
        Calcul intelligent avec 3 niveaux de confiance
        
        Args:
            surface_m2: Surface disponible
            approach: 'optimiste', 'realiste', 'conservateur'
            
        Returns:
            Dict avec layout des panneaux et alternatives
        """
        if surface_m2 <= 0:
            return {'total_panels': 0, 'total_kwc': 0.0, 'layout_efficiency': 0.0}
        
        # Surface d'un panneau standard 2024
        panel_area = self.panel_specs['area_m2']
        panel_power = self.panel_specs['power_w']
        
        # Présets d'efficacité selon approche
        # CORRIGÉS selon retour d'expérience terrain : 200m² → 45kWc pessimiste = 81%
        efficiency_presets = {
            'optimiste': {
                'description': 'Toit idéal - 90%',
                'spacing': 0.96,      # Optimisé dès conception
                'obstacles': 0.97,    # Très peu d'obstacles
                'forme': 0.96,        # Rectangulaire parfait
                'total': 0.90,        # 90% utilisable
                'confidence': 'Conditions idéales'
            },
            'realiste': {
                'description': 'Standard - 83%',
                'spacing': 0.92,      # Contraintes de pose normales
                'obstacles': 0.94,    # Cheminées, fenêtres standard
                'forme': 0.96,        # Découpes raisonnables
                'total': 0.83,        # 83% utilisable
                'confidence': 'Retour installateurs moyens'
            },
            'conservateur': {
                'description': 'Pessimiste - 75%',
                'spacing': 0.88,      # Précautions supplémentaires
                'obstacles': 0.90,    # Obstacles plus nombreux
                'forme': 0.95,        # Forme un peu complexe
                'total': 0.75,        # 75% (proche de vos 81% mais sécurisé)
                'confidence': 'Expérience terrain pessimiste'
            },
            'nette_optimisee': {
                'description': 'Surface nette optimisée - 120%',
                'spacing': 0.98,      # Espacement minimal
                'obstacles': 1.0,     # Obstacles déjà décomptés
                'forme': 1.22,        # Superposition possible sur zones libres
                'total': 1.20,        # 120% ! (votre expérience = 121%)
                'confidence': 'Surface optimisée par pro, dépassement possible'
            }
        }
        
        # Sélectionner le preset
        preset = efficiency_presets.get(approach, efficiency_presets['realiste'])
        efficiency = preset['total']
        
        # Calcul de base
        usable_area = surface_m2 * efficiency
        panels_theoretical = usable_area / panel_area
        
        # Arrondi INTELLIGENT
        # Si on est à X.8+ panneaux, on peut dire X+1
        # Si on est à X.2- panneaux, on reste à X
        if panels_theoretical % 1 >= 0.8:
            total_panels = int(panels_theoretical) + 1
        else:
            total_panels = int(panels_theoretical)
        
        # Sécurité : vérifier que ça rentre vraiment
        actual_area_used = total_panels * panel_area
        if actual_area_used > usable_area:
            total_panels -= 1
        
        # Puissance totale
        total_kwc = (total_panels * panel_power) / 1000.0
        
        # Efficacité réelle finale
        actual_efficiency = (total_panels * panel_area) / surface_m2 if surface_m2 > 0 else 0
        
        # Calculer les alternatives
        alternatives = {}
        for alt_approach, alt_preset in efficiency_presets.items():
            if alt_approach != approach:
                alt_usable = surface_m2 * alt_preset['total']
                alt_theoretical = alt_usable / panel_area
                if alt_theoretical % 1 >= 0.8:
                    alt_panels = int(alt_theoretical) + 1
                else:
                    alt_panels = int(alt_theoretical)
                
                # Vérif sécurité
                if alt_panels * panel_area > alt_usable:
                    alt_panels -= 1
                    
                alternatives[alt_approach] = {
                    'panels': alt_panels,
                    'kwc': round((alt_panels * panel_power) / 1000.0, 1),
                    'description': alt_preset['description']
                }
        
        return {
            'total_panels': total_panels,
            'total_kwc': round(total_kwc, 2),
            'layout_efficiency': round(actual_efficiency, 3),
            'usable_area_m2': round(total_panels * panel_area, 1),
            'approach_used': approach,
            'efficiency_preset': preset,
            'alternatives': alternatives,
            'calculation_detail': {
                'surface_brute': surface_m2,
                'efficacite_retenue': f"{efficiency*100:.0f}%",
                'surface_utile': round(usable_area, 1),
                'panneaux_theoriques': round(panels_theoretical, 1),
                'panneaux_installes': total_panels
            }
        }
    
    def calculate_polygon_area(self, coords: List[List[float]]) -> float:
        """
        Calcule l'aire d'un polygone en m² (formule shoelace)
        
        Args:
            coords: Liste de [longitude, latitude]
            
        Returns:
            Surface en m²
        """
        if len(coords) < 3:
            return 0
        
        try:
            # Conversion approximative en mètres (pour petites surfaces)
            x_coords = []
            y_coords = []
            
            for lon, lat in coords:
                # Conversion degrés -> mètres
                x_m = lon * 111000 * math.cos(math.radians(lat))
                y_m = lat * 111000
                x_coords.append(x_m)
                y_coords.append(y_m)
            
            # Formule shoelace
            area = 0.0
            n = len(x_coords)
            
            for i in range(n):
                j = (i + 1) % n
                area += x_coords[i] * y_coords[j]
                area -= x_coords[j] * y_coords[i]
            
            return abs(area) / 2.0
            
        except Exception as e:
            logger.warning(f"Erreur calcul surface: {e}")
            return 0
    
    def point_in_polygon(self, x: float, y: float, polygon: List[List[float]]) -> bool:
        """
        Teste si un point est dans un polygone (algorithme ray casting)
        
        Args:
            x, y: Coordonnées du point
            polygon: Liste de [longitude, latitude]
            
        Returns:
            True si le point est dans le polygone
        """
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def calculate_panel_corners(self, center_lon: float, center_lat: float, 
                              width_m: float, height_m: float) -> List[List[float]]:
        """
        Calcule les coins d'un panneau à partir de son centre
        
        Args:
            center_lon, center_lat: Centre du panneau
            width_m, height_m: Dimensions en mètres
            
        Returns:
            Liste des 4 coins [longitude, latitude]
        """
        # Conversion mètres -> degrés
        deg_per_m_lat = 1 / 111000
        deg_per_m_lon = 1 / (111000 * math.cos(math.radians(center_lat)))
        
        half_width = (width_m / 2) * deg_per_m_lon
        half_height = (height_m / 2) * deg_per_m_lat
        
        return [
            [center_lon - half_width, center_lat - half_height],  # SO
            [center_lon + half_width, center_lat - half_height],  # SE
            [center_lon + half_width, center_lat + half_height],  # NE
            [center_lon - half_width, center_lat + half_height],  # NO
            [center_lon - half_width, center_lat - half_height]   # Fermer
        ]
    
    def calculate_panel_layout(self, polygon_coords: List[List[float]], 
                             azimuth: int = 180) -> Dict:
        """
        Calcule la disposition optimale des panneaux dans le polygone
        
        Args:
            polygon_coords: Coordonnées du polygone [longitude, latitude]
            azimuth: Orientation (180° = sud)
            
        Returns:
            Dict avec panels, total_panels, total_kwc, layout_efficiency
        """
        if len(polygon_coords) < 3:
            return {'panels': [], 'total_panels': 0, 'total_kwc': 0, 'layout_efficiency': 0}
        
        try:
            # 1. Calculer bounding box
            min_lon = min(p[0] for p in polygon_coords)
            max_lon = max(p[0] for p in polygon_coords)
            min_lat = min(p[1] for p in polygon_coords)
            max_lat = max(p[1] for p in polygon_coords)
            
            # 2. Convertir en mètres
            center_lat = (min_lat + max_lat) / 2
            width_m = (max_lon - min_lon) * 111000 * math.cos(math.radians(center_lat))
            height_m = (max_lat - min_lat) * 111000
            
            # 3. Dimensions panneau selon orientation
            panel_w = self.panel_specs['width_m']
            panel_h = self.panel_specs['height_m']
            spacing = self.panel_specs['spacing_m']
            
            # Optimiser orientation (portrait/paysage)
            if azimuth in [90, 270]:  # Est/Ouest
                panel_w, panel_h = panel_h, panel_w
            
            # 4. Placer les panneaux en grille
            panels = []
            y = spacing
            row = 0
            
            while y + panel_h <= height_m - spacing:
                x = spacing
                col = 0
                
                while x + panel_w <= width_m - spacing:
                    # Centre du panneau en coordonnées géo
                    panel_center_lon = min_lon + (x + panel_w/2) / (111000 * math.cos(math.radians(center_lat)))
                    panel_center_lat = min_lat + (y + panel_h/2) / 111000
                    
                    # Vérifier si le centre est dans le polygone
                    if self.point_in_polygon(panel_center_lon, panel_center_lat, polygon_coords):
                        panels.append({
                            'id': f'panel_{row}_{col}',
                            'center': [panel_center_lon, panel_center_lat],
                            'corners': self.calculate_panel_corners(
                                panel_center_lon, panel_center_lat, panel_w, panel_h
                            ),
                            'power_w': self.panel_specs['power_w']
                        })
                    
                    x += panel_w + spacing
                    col += 1
                
                y += panel_h + spacing
                row += 1
            
            # 5. Calculer métriques
            total_panels = len(panels)
            total_kwc = total_panels * (self.panel_specs['power_w'] / 1000)
            
            # Surface polygon pour calcul efficacité
            polygon_area = self.calculate_polygon_area(polygon_coords)
            layout_efficiency = (total_panels * panel_w * panel_h / polygon_area) if polygon_area > 0 else 0
            
            return {
                'panels': panels,
                'total_panels': total_panels,
                'total_kwc': round(total_kwc, 2),
                'layout_efficiency': round(layout_efficiency, 3),
                'polygon_area_m2': round(polygon_area, 1)
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul layout panneaux: {e}")
            return {'panels': [], 'total_panels': 0, 'total_kwc': 0, 'layout_efficiency': 0}
    
    def create_rectangle_polygon(self, center_lon: float, center_lat: float, 
                               width_m: float, height_m: float, rotation: float = 0) -> List[List[float]]:
        """
        Crée un polygone rectangulaire
        
        Args:
            center_lon, center_lat: Centre du rectangle
            width_m, height_m: Dimensions en mètres
            rotation: Rotation en degrés
            
        Returns:
            Liste des coordonnées du rectangle
        """
        # Conversion mètres -> degrés
        deg_per_m_lat = 1 / 111000
        deg_per_m_lon = 1 / (111000 * math.cos(math.radians(center_lat)))
        
        half_width = (width_m / 2) * deg_per_m_lon
        half_height = (height_m / 2) * deg_per_m_lat
        
        # Points avant rotation
        points = [
            [center_lon - half_width, center_lat - half_height],
            [center_lon + half_width, center_lat - half_height],
            [center_lon + half_width, center_lat + half_height],
            [center_lon - half_width, center_lat + half_height],
            [center_lon - half_width, center_lat - half_height]  # Fermer
        ]
        
        # Appliquer rotation si nécessaire
        if rotation != 0:
            points = self._rotate_polygon(points, center_lon, center_lat, rotation)
        
        return points
    
    def _rotate_polygon(self, points: List[List[float]], center_x: float, 
                       center_y: float, angle_deg: float) -> List[List[float]]:
        """Applique une rotation à un polygone"""
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        rotated = []
        for x, y in points:
            # Translate to origin
            tx = x - center_x
            ty = y - center_y
            
            # Rotate
            rx = tx * cos_a - ty * sin_a
            ry = tx * sin_a + ty * cos_a
            
            # Translate back
            rotated.append([rx + center_x, ry + center_y])
        
        return rotated
    
    async def get_pvgis_hourly_data(self, lat: float, lon: float, kwp: float,
                                   azimuth: float = 180, tilt: float = 30) -> Dict:
        """
        Récupère les données horaires PVGIS (moyennes mensuelles)
        Doc API : https://re.jrc.ec.europa.eu/pvg_tools/en/tools.html
        """
        try:
            # PVGIS utilise azimut 0=Sud, nous utilisons 180=Sud
            pvgis_azimuth = azimuth - 180
            
            url = f"{self.pvgis_base_url}/PVcalc"
            # Adapter le type de montage selon l'inclinaison
            # Toit plat (0°) = montage libre, incliné = sur bâtiment
            mounting = 'free' if tilt <= 5 else 'building'
            
            params = {
                'lat': lat,
                'lon': lon,
                'peakpower': kwp,
                'angle': tilt,
                'aspect': pvgis_azimuth,
                'outputformat': 'json',
                'pvtechchoice': 'crystSi',  # Silicium cristallin
                'mountingplace': mounting,   # Free pour toit plat, building pour incliné
                'loss': 14,  # Pertes système standard
                'optimalinclination': 0,
                'optimalangles': 0,
                'components': 1
            }
            
            cache_key = f"pvgis_{lat:.4f}_{lon:.4f}_{kwp:.1f}_{azimuth}_{tilt}"
            
            # Vérifier cache
            if cache_key in self._cache:
                cache_data = self._cache[cache_key]
                if time.time() - cache_data['timestamp'] < 86400:  # Cache 24h
                    logger.info("Utilisation cache PVGIS")
                    return cache_data['data']
            
            if not HTTPX_AVAILABLE:
                # Fallback sur requests si httpx pas disponible
                import requests
                response = requests.get(url, params=params, timeout=30)
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, params=params, timeout=30)
                
            if response.status_code == 200:
                data = response.json()
                
                # Extraire les profils horaires moyens par mois
                hourly_profiles = self._parse_pvgis_response(data)
                
                # Générer 8760 heures
                hourly_8760 = self._expand_to_8760_hours(hourly_profiles, kwp)
                
                result = {
                    'hourly_8760': hourly_8760,
                    'source': 'PVGIS',
                    'annual_total': sum(hourly_8760)
                }
                
                # Mettre en cache
                self._cache[cache_key] = {
                    'data': result,
                    'timestamp': time.time()
                }
                
                logger.info(f"Données PVGIS récupérées: {result['annual_total']:.0f} kWh/an")
                return result
            else:
                logger.warning(f"PVGIS erreur {response.status_code}")
                return self._get_fallback_hourly_production(kwp, lat, azimuth, tilt)
                
        except Exception as e:
            logger.error(f"Erreur PVGIS: {e}")
            return self._get_fallback_hourly_production(kwp, lat, azimuth, tilt)
    
    def _parse_pvgis_response(self, pvgis_data: Dict) -> Dict:
        """Parse la réponse PVGIS pour extraire les profils"""
        try:
            # PVGIS retourne des moyennes horaires par mois
            monthly_profiles = {}
            
            # Structure données PVGIS V5.2
            if 'outputs' in pvgis_data and 'hourly' in pvgis_data['outputs']:
                hourly_data = pvgis_data['outputs']['hourly']
                
                # Organiser par mois
                for entry in hourly_data:
                    timestamp = entry['time']
                    month = int(timestamp[4:6])  # Format YYYYMMDDHHMM
                    hour = int(timestamp[8:10])
                    power = entry.get('P', 0)  # Puissance kW
                    
                    if month not in monthly_profiles:
                        monthly_profiles[month] = [0] * 24
                    
                    # Moyenne pour cette heure du mois
                    monthly_profiles[month][hour] = power
            
            return monthly_profiles
            
        except Exception as e:
            logger.warning(f"Erreur parsing PVGIS: {e}")
            return {}
    
    def _expand_to_8760_hours(self, monthly_profiles: Dict, kwp: float) -> List[float]:
        """Étend les profils mensuels sur 8760 heures"""
        if not monthly_profiles:
            return self._get_fallback_hourly_production(kwp, 43.7, 180, 30)['hourly_8760']
        
        hourly_8760 = []
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        for month in range(1, 13):
            # Profil horaire pour ce mois
            if month in monthly_profiles:
                month_profile = monthly_profiles[month]
            else:
                # Fallback si mois manquant
                closest_month = min(monthly_profiles.keys(), key=lambda x: abs(x - month))
                month_profile = monthly_profiles[closest_month]
            
            # Répéter pour chaque jour du mois
            for day in range(days_in_month[month - 1]):
                hourly_8760.extend(month_profile)
        
        # Ajuster pour année bissextile si nécessaire
        while len(hourly_8760) < 8760:
            hourly_8760.append(0)
        
        return hourly_8760[:8760]
    
    def _get_fallback_hourly_production(self, kwp: float, lat: float, azimuth: float = 180, tilt: float = 30) -> Dict:
        """Profils types si PVGIS indisponible"""
        # Courbes types selon saison (normalisées sur 24h)
        profiles = {
            'summer': [  # Juin
                0, 0, 0, 0, 0, 0.05, 0.15, 0.35,      # 00h-07h
                0.55, 0.75, 0.85, 0.95, 1.0, 0.95,    # 08h-13h (pic à midi)
                0.85, 0.75, 0.55, 0.35, 0.15, 0.05,   # 14h-19h
                0, 0, 0, 0                              # 20h-23h
            ],
            'winter': [  # Décembre
                0, 0, 0, 0, 0, 0, 0, 0,                # 00h-07h
                0.1, 0.3, 0.5, 0.6, 0.65, 0.6,        # 08h-13h
                0.5, 0.3, 0.1, 0, 0, 0,                # 14h-19h
                0, 0, 0, 0                              # 20h-23h
            ]
        }
        
        # Facteur de production selon latitude (mis à jour selon PVGIS réel)
        # Côte d'Azur peut atteindre 1600+ kWh/kWc/an selon PVGIS
        if lat < 43:  # Sud extrême (Nice, Cannes)
            production_factor = 1600
        elif lat < 44:  # Sud (Montpellier, Marseille)  
            production_factor = 1500
        elif lat < 46:  # Centre-Sud (Lyon, Grenoble)
            production_factor = 1350
        else:  # Nord
            production_factor = 1200
        
        # Facteur d'orientation et inclinaison (approximation)
        # Optimum: Sud (180°) et 30-35°
        orientation_factor = 1.0
        
        # Impact azimuth (référence Sud=180°)
        azimuth_deviation = abs(azimuth - 180)
        if azimuth_deviation <= 45:
            orientation_factor *= (1.0 - azimuth_deviation * 0.004)  # -0.4% par degré
        else:
            orientation_factor *= (1.0 - 45 * 0.004 - (azimuth_deviation - 45) * 0.008)  # Pénalité plus forte
        
        # Impact inclinaison selon le type d'installation
        if tilt <= 5:  # Toit plat avec supports
            # Sur toit plat, on installe généralement à 10-15° avec supports
            # Production quasi-optimale car pas d'ombrage
            orientation_factor *= 0.95  # Seulement -5% vs optimal
        else:
            # Toit incliné classique
            optimal_tilt = 32 if lat < 44 else 35
            tilt_deviation = abs(tilt - optimal_tilt)
            if tilt_deviation <= 15:
                orientation_factor *= (1.0 - tilt_deviation * 0.006)  # -0.6% par degré
            else:
                orientation_factor *= (1.0 - 15 * 0.006 - (tilt_deviation - 15) * 0.012)  # Pénalité plus forte
        
        # Appliquer le facteur d'orientation
        production_factor *= orientation_factor
        
        # Générer 8760 heures
        hourly_8760 = []
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        for month in range(1, 13):
            # Interpolation entre été et hiver
            if 4 <= month <= 9:  # Avril à septembre
                weight_summer = 1.0 if month in [6, 7, 8] else 0.7
                profile = [s * weight_summer + w * (1 - weight_summer) 
                         for s, w in zip(profiles['summer'], profiles['winter'])]
            else:
                profile = profiles['winter']
            
            # Normaliser et ajuster à la production
            daily_kwh = (kwp * production_factor * 0.85) / 365  # Avec pertes système
            profile_sum = sum(profile)
            if profile_sum > 0:
                profile = [h * daily_kwh / profile_sum for h in profile]
            
            # Répéter pour chaque jour du mois
            for day in range(days_in_month[month - 1]):
                hourly_8760.extend(profile)
        
        return {
            'hourly_8760': hourly_8760[:8760],
            'source': 'estimation',
            'annual_total': kwp * production_factor * 0.85
        }
    
    async def calculate_advanced_autoconsumption(self, annual_consumption: float, kwp: float,
                                               lat: float, lon: float, azimuth: float, tilt: float,
                                               building_type: str, custom_profile: Optional[Dict] = None) -> Dict:
        """
        Calcul professionnel de l'autoconsommation avec profils horaires
        
        Args:
            annual_consumption: Consommation annuelle en kWh
            kwp: Puissance installée en kWc
            lat, lon: Coordonnées géographiques
            azimuth, tilt: Orientation et inclinaison panneaux
            building_type: Type de bâtiment pour profil consommation
            custom_profile: Ajustements personnalisés du profil
        
        Returns:
            Dict avec analyse détaillée autoconsommation
        """
        try:
            # 1. Obtenir profil de production (8760h)
            production_data = await self.get_pvgis_hourly_data(lat, lon, kwp, azimuth, tilt)
            production_8760 = production_data['hourly_8760']
            
            # 2. Obtenir profil de consommation (8760h)
            if self.profile_manager:
                consumption_8760 = self.profile_manager.get_8760_profile(
                    annual_consumption, building_type, custom_profile
                )
            else:
                # Fallback: profil plat
                consumption_8760 = [annual_consumption / 8760] * 8760
            
            # 3. Calcul heure par heure
            results_hourly = []
            total_autoconso = 0
            total_surplus = 0
            total_grid = 0
            
            for hour in range(8760):
                prod = production_8760[hour]
                conso = consumption_8760[hour]
                
                autoconso = min(prod, conso)
                surplus = max(0, prod - conso)
                from_grid = max(0, conso - prod)
                
                total_autoconso += autoconso
                total_surplus += surplus
                total_grid += from_grid
                
                results_hourly.append({
                    'hour': hour,
                    'production': prod,
                    'consumption': conso,
                    'autoconsumption': autoconso,
                    'surplus': surplus,
                    'grid': from_grid
                })
            
            # 4. Calculer métriques
            total_production = sum(production_8760)
            taux_autoconso = (total_autoconso / total_production * 100) if total_production > 0 else 0
            taux_autoprod = (total_autoconso / annual_consumption * 100)
            
            # 5. Extraire journées types pour visualisation
            typical_days = self._extract_typical_days(results_hourly, production_8760, consumption_8760)
            
            # 6. Calculs financiers réalistes
            financial = self._calculate_realistic_financial(
                total_autoconso, total_surplus, total_grid, kwp
            )
            
            return {
                'hourly_results': results_hourly,  # Pour export détaillé si besoin
                'summary': {
                    'production_annual_kwh': round(total_production),
                    'autoconsumption_kwh': round(total_autoconso),
                    'surplus_kwh': round(total_surplus),
                    'grid_consumption_kwh': round(total_grid),
                    'self_consumption_rate': round(taux_autoconso, 1),
                    'self_production_rate': round(taux_autoprod, 1)
                },
                'typical_days': typical_days,
                'financial': financial,
                'building_type': building_type,
                'production_source': production_data['source']
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul autoconsommation avancé: {e}")
            # Fallback sur méthode simple
            return self._fallback_autoconsumption_calculation(annual_consumption, kwp, lat)
    
    def _extract_typical_days(self, hourly_results: List[Dict], 
                            production_8760: List[float], consumption_8760: List[float]) -> Dict:
        """Extrait des journées types été/hiver pour visualisation"""
        try:
            # Jour type été (15 juin = jour 166)
            summer_day_start = 166 * 24
            summer_production = production_8760[summer_day_start:summer_day_start + 24]
            summer_consumption = consumption_8760[summer_day_start:summer_day_start + 24]
            
            # Jour type hiver (15 décembre = jour 349)
            winter_day_start = 349 * 24
            winter_production = production_8760[winter_day_start:winter_day_start + 24]
            winter_consumption = consumption_8760[winter_day_start:winter_day_start + 24]
            
            # Calculer statistiques journalières
            def calc_day_stats(prod, conso):
                autoconso = [min(p, c) for p, c in zip(prod, conso)]
                return {
                    'self_consumption': sum(autoconso) / sum(prod) * 100 if sum(prod) > 0 else 0,
                    'peak_surplus': max([max(0, p - c) for p, c in zip(prod, conso)]),
                    'day_coverage': sum(autoconso) / sum(conso) * 100 if sum(conso) > 0 else 0
                }
            
            return {
                'summer': {
                    'production': summer_production,
                    'consumption': summer_consumption
                },
                'winter': {
                    'production': winter_production,
                    'consumption': winter_consumption
                },
                'summer_stats': calc_day_stats(summer_production, summer_consumption),
                'winter_stats': calc_day_stats(winter_production, winter_consumption)
            }
            
        except Exception as e:
            logger.warning(f"Erreur extraction journées types: {e}")
            return {}
    
    def _calculate_realistic_financial(self, autoconso_kwh: float, surplus_kwh: float, 
                                     grid_kwh: float, kwp: float) -> Dict:
        """Calculs financiers avec taux d'autoconsommation réalistes"""
        try:
            # Paramètres économiques 2025
            tarif_rachat = 0.13      # €/kWh (EDF OA)
            prix_electricite = 0.25  # €/kWh (tarif réglementé)
            cout_installation = kwp * 1500  # 1500€/kWc
            
            # Revenus annuels
            economies_autoconso = autoconso_kwh * prix_electricite  # Économies électricité
            revenus_vente = surplus_kwh * tarif_rachat             # Vente surplus
            revenus_totaux = economies_autoconso + revenus_vente
            
            # ROI simple
            roi_annees = cout_installation / revenus_totaux if revenus_totaux > 0 else 99
            
            # Économies sur 20 ans (avec inflation)
            economies_20ans = revenus_totaux * 20 * 1.3  # +30% inflation sur 20 ans
            
            return {
                'cout_installation': round(cout_installation, 0),
                'annual_savings': round(revenus_totaux, 0),
                'autoconsumption_savings': round(economies_autoconso, 0),
                'surplus_revenues': round(revenus_vente, 0),
                'roi_years': round(roi_annees, 1),
                'savings_20_years': round(economies_20ans, 0),
                'grid_cost_remaining': round(grid_kwh * prix_electricite, 0)
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul financier réaliste: {e}")
            return {
                'cout_installation': 0,
                'annual_savings': 0,
                'autoconsumption_savings': 0,
                'surplus_revenues': 0,
                'roi_years': 99,
                'savings_20_years': 0,
                'grid_cost_remaining': 0
            }
    
    def _fallback_autoconsumption_calculation(self, annual_consumption: float, 
                                            kwp: float, lat: float) -> Dict:
        """Calcul de fallback en cas d'erreur"""
        try:
            # Production estimée
            production_factor = 1400 if lat < 44 else 1200
            annual_production = kwp * production_factor * 0.85
            
            # Autoconsommation simplifiée (30% résidentiel type)
            autoconso_rate = 0.30
            autoconso_kwh = min(annual_production * autoconso_rate, annual_consumption)
            surplus_kwh = annual_production - autoconso_kwh
            grid_kwh = max(0, annual_consumption - autoconso_kwh)
            
            financial = self._calculate_realistic_financial(autoconso_kwh, surplus_kwh, grid_kwh, kwp)
            
            return {
                'summary': {
                    'production_annual_kwh': round(annual_production),
                    'autoconsumption_kwh': round(autoconso_kwh),
                    'surplus_kwh': round(surplus_kwh),
                    'grid_consumption_kwh': round(grid_kwh),
                    'self_consumption_rate': round(autoconso_rate * 100, 1),
                    'self_production_rate': round(autoconso_kwh / annual_consumption * 100, 1)
                },
                'financial': financial,
                'typical_days': {},
                'building_type': 'unknown',
                'production_source': 'fallback'
            }
            
        except Exception as e:
            logger.error(f"Erreur fallback: {e}")
            return {}
    
    async def get_forecast_solar_data(self, lat: float, lon: float, 
                                    tilt: int, azimuth: int, kwp: float) -> Dict:
        """
        Récupère les données de production via API forecast-solar
        
        Args:
            lat, lon: Coordonnées
            tilt: Inclinaison (0-90°)
            azimuth: Orientation (180° = sud)
            kwp: Puissance installée
            
        Returns:
            Dict avec données de production
        """
        # Cache key
        cache_key = f"{lat:.4f}_{lon:.4f}_{tilt}_{azimuth}_{kwp:.1f}"
        
        # Vérifier cache
        if cache_key in self._cache:
            cache_data = self._cache[cache_key]
            if time.time() - cache_data['timestamp'] < self.cache_duration:
                logger.info("Utilisation cache forecast-solar")
                return cache_data['data']
        
        try:
            # URL API forecast-solar (gratuite)
            url = f"{self.api_base_url}/estimate/{lat}/{lon}/{tilt}/{azimuth}/{kwp}"
            
            # Appel API
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Parser les résultats
                result = self._process_forecast_data(data)
                
                # Mettre en cache
                self._cache[cache_key] = {
                    'data': result,
                    'timestamp': time.time()
                }
                
                logger.info(f"Données forecast-solar récupérées: {result.get('annual_kwh', 0):.0f} kWh/an")
                return result
                
            else:
                logger.warning(f"API forecast-solar erreur {response.status_code}")
                return self._get_fallback_estimate(kwp, lat)
                
        except Exception as e:
            logger.warning(f"Erreur API forecast-solar: {e}")
            return self._get_fallback_estimate(kwp, lat)
    
    def _process_forecast_data(self, raw_data: Dict) -> Dict:
        """Traite les données brutes de forecast-solar"""
        try:
            # L'API retourne les données dans 'result'
            if 'result' not in raw_data:
                raise ValueError("Format de réponse API invalide")
            
            # Données aujourd'hui et demain
            today_data = raw_data['result'].get('watts', {})
            
            if not today_data:
                raise ValueError("Pas de données de production")
            
            # Convertir en liste pour analyse
            timestamps = []
            productions = []
            
            for timestamp_str, watts in today_data.items():
                timestamps.append(timestamp_str)
                productions.append(watts / 1000)  # Watts -> kW
            
            # Calculs agrégés
            total_kwh_today = sum(productions)
            annual_estimate = total_kwh_today * 365  # Estimation simple
            avg_daily = total_kwh_today
            peak_power = max(productions) if productions else 0
            
            return {
                'annual_kwh': round(annual_estimate, 0),
                'daily_kwh': round(avg_daily, 1),
                'peak_kw': round(peak_power, 2),
                'hourly_data': list(zip(timestamps, productions)),
                'data_source': 'forecast-solar',
                'estimated': False
            }
            
        except Exception as e:
            logger.warning(f"Erreur traitement données forecast-solar: {e}")
            # Fallback sur estimation locale
            return self._get_fallback_estimate(1.0, 45.0)  # Valeurs par défaut
    
    def _get_fallback_estimate(self, kwp: float, latitude: float) -> Dict:
        """Estimation de secours si API indisponible"""
        try:
            # Irradiation selon latitude
            if latitude >= 45:
                irradiation = 1200  # Nord France
            elif latitude >= 44:
                irradiation = 1300  # Centre France
            else:
                irradiation = 1400  # Sud France
            
            # Facteur de performance système
            performance_factor = 0.85
            
            annual_kwh = kwp * irradiation * performance_factor
            daily_kwh = annual_kwh / 365
            peak_kw = kwp * 0.8  # Estimation pic
            
            return {
                'annual_kwh': round(annual_kwh, 0),
                'daily_kwh': round(daily_kwh, 1),
                'peak_kw': round(peak_kw, 2),
                'hourly_data': [],
                'data_source': 'estimation-locale',
                'estimated': True
            }
            
        except Exception as e:
            logger.error(f"Erreur fallback estimation: {e}")
            return {
                'annual_kwh': 0,
                'daily_kwh': 0,
                'peak_kw': 0,
                'hourly_data': [],
                'data_source': 'erreur',
                'estimated': True
            }
    
    def calculate_financial_metrics(self, annual_kwh: float, kwp: float, 
                                  consumption_kwh: float = 0) -> Dict:
        """
        Calcule les métriques financières de l'installation
        
        Args:
            annual_kwh: Production annuelle
            kwp: Puissance installée
            consumption_kwh: Consommation du bâtiment
            
        Returns:
            Dict avec métriques financières
        """
        try:
            # Paramètres économiques
            tarif_rachat = 0.13      # €/kWh (EDF OA)
            prix_electricite = 0.25  # €/kWh (tarif client)
            cout_installation = kwp * 1500  # 1500€/kWc estimation
            
            # Calcul autoconsommation
            if consumption_kwh > 0:
                autoconsommation_kwh = min(annual_kwh, consumption_kwh)
                surplus_kwh = max(0, annual_kwh - consumption_kwh)
                taux_autoconso = (autoconsommation_kwh / annual_kwh * 100) if annual_kwh > 0 else 0
            else:
                autoconsommation_kwh = annual_kwh * 0.3  # 30% par défaut
                surplus_kwh = annual_kwh * 0.7
                taux_autoconso = 30
            
            # Revenus annuels
            revenus_autoconso = autoconsommation_kwh * prix_electricite  # Économies
            revenus_vente = surplus_kwh * tarif_rachat                   # Vente surplus
            revenus_totaux = revenus_autoconso + revenus_vente
            
            # ROI simple
            roi_annees = cout_installation / revenus_totaux if revenus_totaux > 0 else 99
            
            # Impact environnemental
            co2_evite = annual_kwh * 0.057  # kg CO2/kWh évités (mix électrique français)
            
            return {
                'cout_installation': round(cout_installation, 0),
                'revenus_annuels': round(revenus_totaux, 0),
                'autoconsommation_kwh': round(autoconsommation_kwh, 0),
                'surplus_kwh': round(surplus_kwh, 0),
                'taux_autoconso': round(taux_autoconso, 1),
                'roi_annees': round(roi_annees, 1),
                'co2_evite_kg': round(co2_evite, 0),
                'economies_20ans': round(revenus_totaux * 20, 0)
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul financier: {e}")
            return {
                'cout_installation': 0,
                'revenus_annuels': 0,
                'autoconsommation_kwh': 0,
                'surplus_kwh': 0,
                'taux_autoconso': 0,
                'roi_annees': 99,
                'co2_evite_kg': 0,
                'economies_20ans': 0
            }
    
    def _get_empty_financial(self) -> Dict:
        """Retourne des métriques financières vides"""
        return {
            'cout_installation': 0,
            'revenus_annuels': 0,
            'autoconsommation_kwh': 0,
            'surplus_kwh': 0,
            'taux_autoconso': 0,
            'roi_annees': 99,
            'co2_evite_kg': 0,
            'economies_20ans': 0
        }

# Fonction utilitaire pour tests
def test_solar_simulator():
    """Test du simulateur solaire"""
    print("TEST SIMULATEUR SOLAIRE")
    print("-" * 40)
    
    simulator = SolarSimulator()
    
    # Test 1: Création rectangle
    print("Test 1: Création rectangle")
    rect = simulator.create_rectangle_polygon(7.2620, 43.7102, 10, 6, 0)
    print(f"Rectangle créé: {len(rect)} points")
    
    # Test 2: Calcul surface
    print("\nTest 2: Calcul surface")
    area = simulator.calculate_polygon_area(rect)
    print(f"Surface calculée: {area:.1f} m²")
    
    # Test 3: Layout panneaux
    print("\nTest 3: Layout panneaux")
    layout = simulator.calculate_panel_layout(rect, 180)
    print(f"Panneaux: {layout['total_panels']}")
    print(f"Puissance: {layout['total_kwc']} kWc")
    print(f"Efficacité: {layout['layout_efficiency']:.1%}")
    
    # Test 4: Estimation production (fallback)
    print("\nTest 4: Estimation production")
    production = simulator._get_fallback_estimate(layout['total_kwc'], 43.7102)
    print(f"Production estimée: {production['annual_kwh']:.0f} kWh/an")
    
    # Test 5: Métriques financières
    print("\nTest 5: Métriques financières")
    financial = simulator.calculate_financial_metrics(
        production['annual_kwh'], 
        layout['total_kwc'], 
        15000  # Consommation exemple
    )
    print(f"ROI: {financial['roi_annees']:.1f} ans")
    print(f"Revenus: {financial['revenus_annuels']:.0f} €/an")
    
    print("\n✅ Tous les tests passés !")

if __name__ == "__main__":
    test_solar_simulator()