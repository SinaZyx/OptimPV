"""Service d'autocomplétion d'adresse utilisant l'API du gouvernement français.

Ce module fournit une interface pour rechercher des adresses françaises
avec autocomplétion via l'API api-adresse.data.gouv.fr.
"""

import requests
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import streamlit as st

logger = logging.getLogger(__name__)


# Fonction cachée pour la recherche (sans self pour éviter l'erreur de hash)
@st.cache_data(ttl=3600)
def _cached_address_search(query: str, limit: int = 5, postcode: Optional[str] = None) -> List[Dict]:
    """Recherche cachée d'adresses via l'API gouvernementale."""
    if len(query) < 3:
        return []
    
    try:
        params = {
            'q': query,
            'limit': limit,
            'type': 'housenumber',
            'autocomplete': 1
        }
        
        if postcode:
            params['postcode'] = postcode
            
        response = requests.get(
            "https://api-adresse.data.gouv.fr/search/",
            params=params,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            for feature in data.get('features', []):
                props = feature.get('properties', {})
                coords = feature.get('geometry', {}).get('coordinates', [0, 0])
                
                results.append({
                    'label': props.get('label', ''),
                    'name': props.get('name', ''),
                    'postcode': props.get('postcode', ''),
                    'city': props.get('city', ''),
                    'score': props.get('score', 0),
                    'lat': coords[1] if len(coords) > 1 else None,
                    'lon': coords[0] if len(coords) > 0 else None
                })
                
            return results
            
    except Exception as e:
        logger.error(f"Erreur API adresse: {e}")
        
    return []


@dataclass
class AddressSuggestion:
    """Représente une suggestion d'adresse."""
    label: str  # L'adresse complète affichée
    street: str  # Nom de rue
    postcode: str  # Code postal
    city: str  # Ville
    citycode: str  # Code INSEE
    latitude: float
    longitude: float
    score: float  # Score de pertinence
    
    @property
    def display_label(self) -> str:
        """Label formaté pour l'affichage."""
        return f"{self.street}, {self.postcode} {self.city}"


class AddressAutocompleteService:
    """Service d'autocomplétion d'adresse via l'API du gouvernement français."""
    
    BASE_URL = "https://api-adresse.data.gouv.fr/search/"
    
    def __init__(self):
        """Initialise le service d'autocomplétion."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OptimPV/1.0 (Photovoltaic Management System)'
        })
    
    def search_addresses(self, query: str, limit: int = 5, 
                        postcode: Optional[str] = None) -> List[AddressSuggestion]:
        """Recherche des adresses correspondant à la requête.
        
        Args:
            query: Texte de recherche (min 3 caractères)
            limit: Nombre maximum de résultats
            postcode: Code postal pour filtrer les résultats
            
        Returns:
            Liste des suggestions d'adresse
        """
        # Utiliser la fonction cachée qui retourne des dictionnaires
        results = _cached_address_search(query, limit, postcode)
        
        # Convertir en AddressSuggestion pour compatibilité
        suggestions = []
        for result in results:
            suggestions.append(AddressSuggestion(
                label=result['label'],
                street=result['name'],
                postcode=result['postcode'],
                city=result['city'],
                citycode='',  # Non fourni par la fonction cachée
                latitude=result['lat'],
                longitude=result['lon'],
                score=result['score']
            ))
        
        return suggestions
    
    def search_addresses_dict(self, query: str, limit: int = 5, 
                             postcode: Optional[str] = None) -> List[Dict]:
        """Version qui retourne des dictionnaires pour le widget v2.
        
        Args:
            query: Texte de recherche (min 3 caractères)
            limit: Nombre maximum de résultats
            postcode: Code postal pour filtrer les résultats
            
        Returns:
            Liste des suggestions sous forme de dictionnaires
        """
        return _cached_address_search(query, limit, postcode)
    
    def get_address_details(self, latitude: float, longitude: float) -> Optional[AddressSuggestion]:
        """Recherche inversée: obtient l'adresse à partir des coordonnées GPS.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            
        Returns:
            Suggestion d'adresse ou None
        """
        try:
            url = "https://api-adresse.data.gouv.fr/reverse/"
            params = {
                'lon': longitude,
                'lat': latitude
            }
            
            response = self.session.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            features = data.get('features', [])
            
            if features:
                feature = features[0]
                props = feature.get('properties', {})
                
                return AddressSuggestion(
                    label=props.get('label', ''),
                    street=props.get('name', ''),
                    postcode=props.get('postcode', ''),
                    city=props.get('city', ''),
                    citycode=props.get('citycode', ''),
                    longitude=longitude,
                    latitude=latitude,
                    score=props.get('score', 0)
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche inversée: {e}")
            return None
    
    def parse_zone_from_postcode(self, postcode: str) -> str:
        """Détermine la zone géographique à partir du code postal.
        
        Args:
            postcode: Code postal
            
        Returns:
            Zone géographique
        """
        if not postcode or len(postcode) < 2:
            return "Non définie"
            
        dept = postcode[:2]
        
        # Zones par département (exemple simplifié)
        zones = {
            # Île-de-France
            '75': 'Île-de-France', '77': 'Île-de-France', '78': 'Île-de-France',
            '91': 'Île-de-France', '92': 'Île-de-France', '93': 'Île-de-France',
            '94': 'Île-de-France', '95': 'Île-de-France',
            # PACA
            '04': 'PACA', '05': 'PACA', '06': 'PACA', '13': 'PACA', '83': 'PACA', '84': 'PACA',
            # Occitanie
            '09': 'Occitanie', '11': 'Occitanie', '12': 'Occitanie', '30': 'Occitanie',
            '31': 'Occitanie', '32': 'Occitanie', '34': 'Occitanie', '46': 'Occitanie',
            '48': 'Occitanie', '65': 'Occitanie', '66': 'Occitanie', '81': 'Occitanie', '82': 'Occitanie',
            # Auvergne-Rhône-Alpes
            '01': 'Auvergne-Rhône-Alpes', '03': 'Auvergne-Rhône-Alpes', '07': 'Auvergne-Rhône-Alpes',
            '15': 'Auvergne-Rhône-Alpes', '26': 'Auvergne-Rhône-Alpes', '38': 'Auvergne-Rhône-Alpes',
            '42': 'Auvergne-Rhône-Alpes', '43': 'Auvergne-Rhône-Alpes', '63': 'Auvergne-Rhône-Alpes',
            '69': 'Auvergne-Rhône-Alpes', '73': 'Auvergne-Rhône-Alpes', '74': 'Auvergne-Rhône-Alpes',
            # Nouvelle-Aquitaine
            '16': 'Nouvelle-Aquitaine', '17': 'Nouvelle-Aquitaine', '19': 'Nouvelle-Aquitaine',
            '23': 'Nouvelle-Aquitaine', '24': 'Nouvelle-Aquitaine', '33': 'Nouvelle-Aquitaine',
            '40': 'Nouvelle-Aquitaine', '47': 'Nouvelle-Aquitaine', '64': 'Nouvelle-Aquitaine',
            '79': 'Nouvelle-Aquitaine', '86': 'Nouvelle-Aquitaine', '87': 'Nouvelle-Aquitaine',
        }
        
        return zones.get(dept, f"Zone {dept}")
    
    def extract_zone_from_postal_code(self, postal_code: str) -> Optional[str]:
        """
        Extrait la zone géographique à partir du code postal.
        Version compatible avec l'ancienne interface.
        
        Args:
            postal_code: Code postal français
            
        Returns:
            Nom du département ou None si non trouvé
        """
        if not postal_code or len(postal_code) < 2:
            return None
            
        # Pour les codes postaux spécifiques d'intérêt
        dept = postal_code[:2]
        
        # Retourner le nom du département pour les zones d'intérêt
        dept_names = {
            '06': 'Alpes-Maritimes',
            '75': 'Paris',
            '13': 'Bouches-du-Rhône',
            '69': 'Rhône',
            '33': 'Gironde'
        }
        
        return dept_names.get(dept)


# Instance singleton pour l'utilisation dans l'application
_address_service = None

def get_address_service() -> AddressAutocompleteService:
    """Retourne l'instance singleton du service d'autocomplétion."""
    global _address_service
    if _address_service is None:
        _address_service = AddressAutocompleteService()
    return _address_service