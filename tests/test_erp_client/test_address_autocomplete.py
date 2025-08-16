"""Tests pour la fonctionnalité d'autocomplétion d'adresse."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import time

# Importer les modules à tester
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from modules.erp_client.services.address_autocomplete import AddressAutocompleteService


class TestAddressAutocompleteService(unittest.TestCase):
    """Tests unitaires pour le service d'autocomplétion d'adresse."""
    
    def setUp(self):
        """Initialisation avant chaque test."""
        self.service = AddressAutocompleteService()
    
    @patch('requests.get')
    def test_search_addresses_success(self, mock_get):
        """Test de recherche d'adresses avec succès."""
        # Préparer la réponse simulée
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'features': [
                {
                    'properties': {
                        'label': '10 Rue de la Paix 75002 Paris',
                        'name': '10 Rue de la Paix',
                        'postcode': '75002',
                        'city': 'Paris',
                        'score': 0.95
                    },
                    'geometry': {
                        'coordinates': [2.3312, 48.8696]
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Tester la recherche
        results = self.service.search_addresses("10 rue de la paix paris")
        
        # Vérifications
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['label'], '10 Rue de la Paix 75002 Paris')
        self.assertEqual(results[0]['postcode'], '75002')
        self.assertEqual(results[0]['city'], 'Paris')
        self.assertAlmostEqual(results[0]['lat'], 48.8696)
        self.assertAlmostEqual(results[0]['lon'], 2.3312)
        
    @patch('requests.get')
    def test_search_addresses_no_results(self, mock_get):
        """Test de recherche sans résultats."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'features': []}
        mock_get.return_value = mock_response
        
        results = self.service.search_addresses("adresse inexistante xyz123")
        self.assertEqual(results, [])
        
    @patch('requests.get')
    def test_search_addresses_api_error(self, mock_get):
        """Test avec erreur API."""
        mock_get.side_effect = Exception("API Error")
        
        results = self.service.search_addresses("test")
        self.assertEqual(results, [])
        
    @patch('requests.get')
    def test_reverse_geocode_success(self, mock_get):
        """Test du géocodage inverse."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'features': [{
                'properties': {
                    'label': '10 Rue de la Paix 75002 Paris',
                    'name': '10 Rue de la Paix',
                    'postcode': '75002',
                    'city': 'Paris'
                }
            }]
        }
        mock_get.return_value = mock_response
        
        result = self.service.reverse_geocode(48.8696, 2.3312)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['city'], 'Paris')
        self.assertEqual(result['postcode'], '75002')
        
    def test_extract_zone_from_postal_code(self):
        """Test de l'extraction de zone géographique."""
        # Alpes-Maritimes (06)
        self.assertEqual(self.service.extract_zone_from_postal_code("06000"), "Alpes-Maritimes")
        self.assertEqual(self.service.extract_zone_from_postal_code("06400"), "Alpes-Maritimes")
        
        # Paris (75)
        self.assertEqual(self.service.extract_zone_from_postal_code("75001"), "Paris")
        self.assertEqual(self.service.extract_zone_from_postal_code("75020"), "Paris")
        
        # Autres
        self.assertIsNone(self.service.extract_zone_from_postal_code("13000"))
        self.assertIsNone(self.service.extract_zone_from_postal_code(""))
        self.assertIsNone(self.service.extract_zone_from_postal_code(None))


class TestAddressAutocompleteIntegration(unittest.TestCase):
    """Tests d'intégration avec l'API réelle (à exécuter manuellement)."""
    
    @unittest.skip("Test d'intégration avec API réelle - exécuter manuellement")
    def test_real_api_search(self):
        """Test avec l'API réelle du gouvernement."""
        service = AddressAutocompleteService()
        
        # Test avec une vraie adresse
        results = service.search_addresses("10 rue de la paix paris")
        
        self.assertGreater(len(results), 0)
        self.assertIn('label', results[0])
        self.assertIn('postcode', results[0])
        self.assertIn('city', results[0])
        
        # Respecter la limite de taux
        time.sleep(0.5)
        
    @unittest.skip("Test d'intégration avec API réelle - exécuter manuellement")
    def test_real_api_reverse_geocode(self):
        """Test du géocodage inverse avec l'API réelle."""
        service = AddressAutocompleteService()
        
        # Coordonnées de la Tour Eiffel
        result = service.reverse_geocode(48.8584, 2.2945)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['city'], 'Paris')


if __name__ == '__main__':
    unittest.main()