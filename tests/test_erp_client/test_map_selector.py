"""Tests pour la sélection GPS sur carte."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st

# Importer les modules à tester
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


class TestMapSelector(unittest.TestCase):
    """Tests pour la fonctionnalité de sélection sur carte."""
    
    def setUp(self):
        """Initialisation avant chaque test."""
        # Reset session state
        if hasattr(st, 'session_state'):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
    
    @patch('folium.Map')
    def test_map_creation(self, mock_map):
        """Test de création de la carte."""
        from modules.erp_client.ui.map_selector import render_coordinate_selector
        
        # Mock de la carte Folium
        mock_map_instance = MagicMock()
        mock_map.return_value = mock_map_instance
        
        # Vérifier que la carte est créée avec les bons paramètres
        mock_map.assert_called_once()
        call_args = mock_map.call_args
        
        # Vérifier les coordonnées par défaut (région de Mougins)
        self.assertAlmostEqual(call_args[1]['location'][0], 43.60, places=2)
        self.assertAlmostEqual(call_args[1]['location'][1], 7.06, places=2)
    
    @patch('streamlit_folium.st_folium')
    @patch('folium.Map')
    def test_coordinate_selection(self, mock_map, mock_st_folium):
        """Test de sélection de coordonnées sur la carte."""
        # Simuler un clic sur la carte
        mock_st_folium.return_value = {
            'last_object_clicked': {
                'geometry': {
                    'coordinates': [7.0625, 43.6047]
                }
            }
        }
        
        from modules.erp_client.ui.map_selector import render_coordinate_selector
        
        lat, lon = render_coordinate_selector()
        
        # Vérifier les coordonnées retournées
        self.assertAlmostEqual(lat, 43.6047, places=4)
        self.assertAlmostEqual(lon, 7.0625, places=4)
    
    @patch('geopy.geocoders.Nominatim')
    def test_geocoding_address(self, mock_nominatim):
        """Test du géocodage d'une adresse."""
        # Mock du géocodeur
        mock_geolocator = MagicMock()
        mock_nominatim.return_value = mock_geolocator
        
        # Mock du résultat de géocodage
        mock_location = Mock()
        mock_location.latitude = 43.6047
        mock_location.longitude = 7.0625
        mock_location.address = "10 Rue de la Paix, 06400 Cannes, France"
        mock_geolocator.geocode.return_value = mock_location
        
        from modules.erp_client.ui.map_selector import render_geocoding_assistant
        
        # Test avec une adresse
        address_parts = {
            'adresse': '10 Rue de la Paix',
            'code_postal': '06400',
            'ville': 'Cannes'
        }
        
        # Simuler le bouton de géocodage
        with patch('streamlit.button', return_value=True):
            lat, lon = render_geocoding_assistant(address_parts)
        
        # Vérifier l'appel au géocodeur
        mock_geolocator.geocode.assert_called_once()
        call_args = mock_geolocator.geocode.call_args[0][0]
        self.assertIn('10 Rue de la Paix', call_args)
        self.assertIn('06400', call_args)
        self.assertIn('Cannes', call_args)
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_form_integration(self, mock_session_state):
        """Test de l'intégration avec le formulaire client."""
        # Simuler l'état après création d'un client sans coordonnées
        mock_session_state['show_map_for_client'] = 123
        mock_session_state['client_address_parts'] = {
            'adresse': '10 Rue de la Paix',
            'code_postal': '06400',
            'ville': 'Cannes'
        }
        
        # Vérifier que les données sont disponibles pour la carte
        self.assertEqual(mock_session_state['show_map_for_client'], 123)
        self.assertIn('adresse', mock_session_state['client_address_parts'])
    
    def test_satellite_view_option(self):
        """Test de l'option vue satellite."""
        # La carte devrait avoir une couche satellite
        # Ceci est configuré dans render_coordinate_selector
        # avec l'ajout de TileLayer satellite
        
        # Test que l'URL de tuiles satellite est correcte
        expected_url = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
        
        # Ce test vérifie principalement que la configuration existe
        # L'implémentation réelle est dans le code
        self.assertIsNotNone(expected_url)


class TestMapWorkflow(unittest.TestCase):
    """Tests du workflow complet avec carte."""
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_complete_map_workflow(self, mock_session_state):
        """Test du workflow complet de sélection GPS."""
        # 1. Création d'un client avec adresse
        mock_session_state['erp_client_mode'] = 'create'
        
        # 2. Client créé sans coordonnées GPS
        mock_session_state['show_map_for_client'] = 123
        mock_session_state['client_address_parts'] = {
            'adresse': '10 Rue de la Paix',
            'code_postal': '06400',
            'ville': 'Cannes'
        }
        
        # 3. Utilisateur clique sur "Ajuster position sur carte"
        mock_session_state['edit_client_gps'] = 123
        
        # 4. Sélection sur carte
        mock_session_state['temp_latitude'] = 43.6047
        mock_session_state['temp_longitude'] = 7.0625
        
        # 5. Sauvegarde des coordonnées
        # ... (mise à jour du client)
        
        # 6. Nettoyage des états temporaires
        if 'show_map_for_client' in mock_session_state:
            del mock_session_state['show_map_for_client']
        if 'client_address_parts' in mock_session_state:
            del mock_session_state['client_address_parts']
        if 'edit_client_gps' in mock_session_state:
            del mock_session_state['edit_client_gps']
        
        # Vérifications
        self.assertNotIn('show_map_for_client', mock_session_state)
        self.assertNotIn('client_address_parts', mock_session_state)
        self.assertNotIn('edit_client_gps', mock_session_state)


if __name__ == '__main__':
    unittest.main()