#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'aide à la précision pour OptimPV.
Fournit des outils pour améliorer la localisation des bâtiments.
"""

import requests
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class PrecisionHelper:
    """Outils pour améliorer la précision de localisation"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OptimPV/2.0 (precision-helper)'
        })
    
    def get_building_candidates_osm(self, lat: float, lon: float, radius: int = 100) -> List[Dict]:
        """
        Récupère les bâtiments proches via OpenStreetMap Overpass API
        
        Args:
            lat: Latitude du point
            lon: Longitude du point  
            radius: Rayon de recherche en mètres
            
        Returns:
            List[Dict]: Liste des bâtiments avec surface et coordonnées
        """
        try:
            # Requête Overpass pour bâtiments dans un rayon
            overpass_query = f"""
            [out:json][timeout:10];
            (
              way["building"]
                (around:{radius},{lat},{lon});
              relation["building"]
                (around:{radius},{lat},{lon});
            );
            out geom;
            """
            
            response = self.session.post(
                'https://overpass-api.de/api/interpreter',
                data=overpass_query,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                buildings = []
                
                for element in data.get('elements', []):
                    if element.get('type') == 'way' and 'geometry' in element:
                        building_info = self._process_osm_building(element, lat, lon)
                        if building_info:
                            buildings.append(building_info)
                
                # Trier par distance
                buildings.sort(key=lambda x: x['distance'])
                logger.info(f"Trouvé {len(buildings)} bâtiments OSM dans rayon {radius}m")
                
                return buildings[:5]  # Top 5 plus proches
                
        except Exception as e:
            logger.warning(f"Erreur requête OSM: {e}")
            
        return []
    
    def _process_osm_building(self, element: Dict, target_lat: float, target_lon: float) -> Optional[Dict]:
        """Traite un bâtiment OSM et calcule ses propriétés"""
        try:
            coords = element.get('geometry', [])
            if len(coords) < 3:
                return None
            
            # Calculer le centre du bâtiment
            center_lat = sum(p['lat'] for p in coords) / len(coords)
            center_lon = sum(p['lon'] for p in coords) / len(coords)
            
            # Distance au point cible
            distance = ((target_lat - center_lat)**2 + (target_lon - center_lon)**2) ** 0.5 * 111000  # Approx en mètres
            
            # Estimation surface (approximation rectangle)
            if len(coords) >= 4:
                # Calculer l'aire du polygone (formule shoelace simplifiée)
                area = self._calculate_polygon_area(coords)
            else:
                area = 100  # Défaut
            
            # Récupérer les tags
            tags = element.get('tags', {})
            building_type = tags.get('building', 'residential')
            
            return {
                'center_lat': center_lat,
                'center_lon': center_lon,
                'distance': distance,
                'surface_m2': max(area, 30),  # Min 30m²
                'building_type': building_type,
                'coords': coords,
                'source': 'OSM'
            }
            
        except Exception as e:
            logger.warning(f"Erreur traitement bâtiment OSM: {e}")
            return None
    
    def _calculate_polygon_area(self, coords: List[Dict]) -> float:
        """Calcule l'aire d'un polygone en m² (approximation)"""
        try:
            if len(coords) < 3:
                return 100
            
            # Formule shoelace adaptée (approximation pour petites surfaces)
            x_coords = [p['lon'] for p in coords]
            y_coords = [p['lat'] for p in coords]
            
            area = 0.0
            n = len(coords)
            
            for i in range(n):
                j = (i + 1) % n
                area += x_coords[i] * y_coords[j]
                area -= x_coords[j] * y_coords[i]
            
            area = abs(area) / 2.0
            
            # Conversion approximative degrés → m² (pour latitude ~43°)
            area_m2 = area * 111000 * 111000 * 0.7  # Facteur correction latitude
            
            return min(max(area_m2, 30), 2000)  # Entre 30 et 2000 m²
            
        except Exception:
            return 100
    
    def suggest_building_selection(self, address: str, lat: float, lon: float) -> Dict:
        """
        Suggère le meilleur bâtiment pour une adresse donnée
        
        Returns:
            Dict avec recommandations et alternatives
        """
        try:
            # Rechercher bâtiments proches
            candidates = self.get_building_candidates_osm(lat, lon, 50)
            
            result = {
                'address': address,
                'input_coords': (lat, lon),
                'candidates_found': len(candidates),
                'recommendation': None,
                'alternatives': candidates,
                'confidence': 'low'
            }
            
            if candidates:
                best_candidate = candidates[0]  # Le plus proche
                
                # Évaluer la confiance
                if best_candidate['distance'] < 20:  # < 20m
                    confidence = 'high'
                elif best_candidate['distance'] < 50:  # < 50m
                    confidence = 'medium'
                else:
                    confidence = 'low'
                
                result.update({
                    'recommendation': best_candidate,
                    'confidence': confidence,
                    'distance_to_best': best_candidate['distance'],
                    'recommended_surface': best_candidate['surface_m2']
                })
                
                logger.info(f"Recommandation bâtiment: {confidence} confiance, {best_candidate['distance']:.0f}m, {best_candidate['surface_m2']:.0f}m²")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur suggestion bâtiment: {e}")
            return {
                'address': address,
                'error': str(e),
                'candidates_found': 0,
                'confidence': 'error'
            }

def test_precision_helper():
    """Test du module de précision"""
    print("TEST MODULE PRECISION")
    print("-" * 30)
    
    helper = PrecisionHelper()
    
    # Test avec adresse à Nice
    lat, lon = 43.7102, 7.2620
    address = "Place Masséna, Nice"
    
    print(f"Test pour: {address}")
    print(f"Coordonnées: {lat}, {lon}")
    
    suggestion = helper.suggest_building_selection(address, lat, lon)
    
    print(f"\nRésultats:")
    print(f"  Candidats trouvés: {suggestion['candidates_found']}")
    print(f"  Confiance: {suggestion['confidence']}")
    
    if suggestion.get('recommendation'):
        rec = suggestion['recommendation']
        print(f"  Recommandation:")
        print(f"    Distance: {rec['distance']:.0f}m")
        print(f"    Surface: {rec['surface_m2']:.0f}m²")
        print(f"    Type: {rec['building_type']}")
    
    print(f"\nAlternatives disponibles: {len(suggestion.get('alternatives', []))}")

if __name__ == "__main__":
    test_precision_helper()