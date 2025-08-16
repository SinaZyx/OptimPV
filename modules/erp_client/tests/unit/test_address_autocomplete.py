"""Tests unitaires pour le service d'autocomplétion d'adresse."""

import unittest
from unittest.mock import Mock, patch
import json

from ...services.address_autocomplete import (
    AddressAutocompleteService,
    AddressSuggestion,
    get_address_service
)


class TestAddressAutocompleteService(unittest.TestCase):
    """Tests pour le service d'autocomplétion d'adresse."""
    
    def setUp(self):
        """Initialisation avant chaque test."""
        self.service = AddressAutocompleteService()
    
    def test_suggestion_creation(self):
        """Test de la création d'une suggestion d'adresse."""
        suggestion = AddressSuggestion(
            label="10 Rue de la Paix, 75002 Paris",
            street="10 Rue de la Paix",
            postcode="75002",
            city="Paris",
            citycode="75102",
            latitude=48.8699,
            longitude=2.3312,
            score=0.95
        )
        
        self.assertEqual(suggestion.display_label, "10 Rue de la Paix, 75002 Paris")
        self.assertEqual(suggestion.postcode, "75002")
        self.assertEqual(suggestion.city, "Paris")
        self.assertAlmostEqual(suggestion.latitude, 48.8699, places=4)
        self.assertAlmostEqual(suggestion.longitude, 2.3312, places=4)
    
    @patch('requests.Session.get')
    def test_search_addresses_success(self, mock_get):
        """Test de recherche d'adresses avec succès."""
        # Mock de la réponse API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "properties": {
                        "label": "10 Rue de la Paix, 75002 Paris",
                        "name": "10 Rue de la Paix",
                        "postcode": "75002",
                        "city": "Paris",
                        "citycode": "75102",
                        "score": 0.95
                    },
                    "geometry": {
                        "coordinates": [2.3312, 48.8699]
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Test
        results = self.service.search_addresses("10 rue de la paix")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].street, "10 Rue de la Paix")
        self.assertEqual(results[0].postcode, "75002")
        self.assertEqual(results[0].city, "Paris")
    
    def test_search_addresses_short_query(self):
        """Test avec une requête trop courte."""
        results = self.service.search_addresses("ab")
        self.assertEqual(results, [])
    
    @patch('requests.Session.get')
    def test_search_addresses_timeout(self, mock_get):
        """Test de gestion du timeout."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()
        
        results = self.service.search_addresses("test address")
        self.assertEqual(results, [])
    
    @patch('requests.Session.get')
    def test_get_address_details_success(self, mock_get):
        """Test du géocodage inverse."""
        # Mock de la réponse
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [{
                "properties": {
                    "label": "5 Avenue Anatole France, 75007 Paris",
                    "name": "5 Avenue Anatole France",
                    "postcode": "75007",
                    "city": "Paris",
                    "citycode": "75107",
                    "score": 0.99
                }
            }]
        }
        mock_get.return_value = mock_response
        
        # Test
        result = self.service.get_address_details(48.8584, 2.2945)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.postcode, "75007")
        self.assertEqual(result.city, "Paris")
    
    def test_parse_zone_from_postcode(self):
        """Test de la détection de zone géographique."""
        # Test Île-de-France
        self.assertEqual(self.service.parse_zone_from_postcode("75001"), "Île-de-France")
        self.assertEqual(self.service.parse_zone_from_postcode("92100"), "Île-de-France")
        
        # Test PACA
        self.assertEqual(self.service.parse_zone_from_postcode("13001"), "PACA")
        self.assertEqual(self.service.parse_zone_from_postcode("06000"), "PACA")
        
        # Test Occitanie
        self.assertEqual(self.service.parse_zone_from_postcode("31000"), "Occitanie")
        self.assertEqual(self.service.parse_zone_from_postcode("34000"), "Occitanie")
        
        # Test code non mappé
        self.assertEqual(self.service.parse_zone_from_postcode("99999"), "Zone 99")
        
        # Test codes invalides
        self.assertEqual(self.service.parse_zone_from_postcode(""), "Non définie")
        self.assertEqual(self.service.parse_zone_from_postcode("1"), "Non définie")
        self.assertEqual(self.service.parse_zone_from_postcode(None), "Non définie")
    
    def test_get_address_service_singleton(self):
        """Test que get_address_service retourne un singleton."""
        service1 = get_address_service()
        service2 = get_address_service()
        
        self.assertIs(service1, service2)


class TestAddressIntegration(unittest.TestCase):
    """Tests d'intégration (nécessitent une connexion Internet)."""
    
    @unittest.skip("Test d'intégration - nécessite une connexion Internet")
    def test_real_api_search(self):
        """Test avec l'API réelle."""
        service = AddressAutocompleteService()
        results = service.search_addresses("tour eiffel paris")
        
        self.assertGreater(len(results), 0)
        # Vérifier qu'on trouve bien quelque chose près de la Tour Eiffel
        found_paris = any("Paris" in r.city for r in results)
        self.assertTrue(found_paris)


if __name__ == '__main__':
    unittest.main()