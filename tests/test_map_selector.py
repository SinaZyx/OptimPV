"""Tests pour le module de sélection de coordonnées sur carte."""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Streamlit avant l'import
sys.modules['streamlit'] = MagicMock()
sys.modules['streamlit_folium'] = MagicMock()
sys.modules['folium'] = MagicMock()

from modules.erp_client.ui.map_selector import render_coordinate_selector, render_geocoding_assistant


class TestMapSelector(unittest.TestCase):
    """Tests pour le sélecteur de carte."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        # Reset des mocks
        sys.modules['streamlit'].session_state = {}
        
    def test_render_coordinate_selector_default(self):
        """Test du rendu avec valeurs par défaut."""
        with patch('modules.erp_client.ui.map_selector.st_folium') as mock_folium:
            # Configuration du mock
            mock_folium.return_value = {
                'last_object_clicked_popup': None,
                'all_drawings': []
            }
            
            lat, lon = render_coordinate_selector()
            
            # Vérification
            self.assertIsNone(lat)
            self.assertIsNone(lon)
            mock_folium.assert_called_once()
            
    def test_render_coordinate_selector_with_click(self):
        """Test avec un clic sur la carte."""
        with patch('modules.erp_client.ui.map_selector.st_folium') as mock_folium:
            # Simuler un clic
            mock_folium.return_value = {
                'last_object_clicked_popup': {
                    'lat': 43.601234,
                    'lng': 7.062345
                },
                'all_drawings': []
            }
            
            lat, lon = render_coordinate_selector()
            
            # Vérification
            self.assertAlmostEqual(lat, 43.601234, places=6)
            self.assertAlmostEqual(lon, 7.062345, places=6)
            
    def test_render_geocoding_assistant_empty_address(self):
        """Test avec adresse vide."""
        lat, lon = render_geocoding_assistant({})
        
        # Vérification
        self.assertIsNone(lat)
        self.assertIsNone(lon)
        
    def test_render_geocoding_assistant_with_address(self):
        """Test avec une adresse valide."""
        address_parts = {
            'adresse': '10 rue de la Paix',
            'code_postal': '75002',
            'ville': 'Paris'
        }
        
        # Mock du bouton qui n'est pas cliqué
        sys.modules['streamlit'].button = MagicMock(return_value=False)
        sys.modules['streamlit'].checkbox = MagicMock(return_value=False)
        
        lat, lon = render_geocoding_assistant(address_parts)
        
        # Vérification
        self.assertIsNone(lat)
        self.assertIsNone(lon)
        
    def test_session_state_persistence(self):
        """Test de la persistance des coordonnées dans session state."""
        # Initialiser session state
        sys.modules['streamlit'].session_state = {
            'selected_coordinates': {
                'lat': 43.6,
                'lon': 7.06
            }
        }
        
        with patch('modules.erp_client.ui.map_selector.st_folium') as mock_folium:
            # Pas de nouveau clic
            mock_folium.return_value = {
                'last_object_clicked_popup': None,
                'all_drawings': []
            }
            
            lat, lon = render_coordinate_selector()
            
            # Les coordonnées de session doivent être utilisées
            self.assertEqual(lat, 43.6)
            self.assertEqual(lon, 7.06)


if __name__ == '__main__':
    unittest.main()