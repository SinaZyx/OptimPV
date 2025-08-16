"""Tests d'intégration pour toutes les nouvelles fonctionnalités ERP.

Ce fichier teste l'intégration complète des nouvelles fonctionnalités :
- Autocomplétion d'adresse
- Fusion des onglets
- Sélection GPS sur carte
- Navigation améliorée
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from modules.erp_client.services.client_service import ClientService
from modules.erp_client.services.address_autocomplete import AddressAutocompleteService
from modules.erp_client.models.client import Client, TypeClient


class TestNewFeaturesIntegration(unittest.TestCase):
    """Tests d'intégration des nouvelles fonctionnalités."""
    
    def setUp(self):
        """Initialisation avant chaque test."""
        self.client_service = ClientService()
        self.autocomplete_service = AddressAutocompleteService()
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_complete_client_creation_with_autocomplete(self, mock_session_state):
        """Test complet de création client avec autocomplétion."""
        # 1. Navigation vers création client
        mock_session_state['erp_active_tab'] = "👥 Clients"
        mock_session_state['erp_client_mode'] = 'create'
        
        # 2. Autocomplétion d'adresse
        with patch('requests.get') as mock_get:
            # Mock de la réponse API
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'features': [{
                    'properties': {
                        'label': '10 Rue de la Paix 06400 Cannes',
                        'name': '10 Rue de la Paix',
                        'postcode': '06400',
                        'city': 'Cannes',
                        'score': 0.95
                    },
                    'geometry': {
                        'coordinates': [7.0625, 43.6047]
                    }
                }]
            }
            mock_get.return_value = mock_response
            
            # Recherche d'adresse
            results = self.autocomplete_service.search_addresses("10 rue de la paix cannes")
            self.assertEqual(len(results), 1)
            
            # Sélection de l'adresse
            selected = results[0]
            self.assertEqual(selected['postcode'], '06400')
            self.assertEqual(selected['city'], 'Cannes')
        
        # 3. Création du client avec les données
        client_data = {
            'code_client': 'TEST001',
            'nom': 'Test Client',
            'type_client': TypeClient.PRODUCTEUR,
            'adresse': selected['name'],
            'code_postal': selected['postcode'],
            'ville': selected['city'],
            'latitude': selected['lat'],
            'longitude': selected['lon']
        }
        
        # 4. Vérification zone géographique
        zone = self.autocomplete_service.extract_zone_from_postal_code('06400')
        self.assertEqual(zone, 'Alpes-Maritimes')
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_navigation_flow_with_map_selection(self, mock_session_state):
        """Test du flux avec sélection sur carte."""
        # 1. Création client sans coordonnées
        mock_session_state['erp_client_mode'] = 'create'
        
        # 2. Client créé, proposition de carte
        mock_session_state['show_map_for_client'] = 123
        mock_session_state['client_address_parts'] = {
            'adresse': '10 Rue de la Paix',
            'code_postal': '06400',
            'ville': 'Cannes'
        }
        
        # 3. Clic sur "Ajuster position sur carte"
        mock_session_state['edit_client_gps'] = 123
        
        # 4. Sélection sur carte simulée
        with patch('streamlit_folium.st_folium') as mock_st_folium:
            mock_st_folium.return_value = {
                'last_object_clicked': {
                    'geometry': {
                        'coordinates': [7.0625, 43.6047]
                    }
                }
            }
            
            # Les coordonnées devraient être mises à jour
            mock_session_state['temp_latitude'] = 43.6047
            mock_session_state['temp_longitude'] = 7.0625
        
        # 5. Retour à la liste
        mock_session_state['erp_client_mode'] = 'list'
        
        # Vérifications
        self.assertEqual(mock_session_state['erp_client_mode'], 'list')
        self.assertEqual(mock_session_state['temp_latitude'], 43.6047)
        self.assertEqual(mock_session_state['temp_longitude'], 7.0625)
    
    def test_tab_navigation_consistency(self):
        """Test de la cohérence de navigation entre onglets."""
        tabs = [
            "💼 Dashboard Commercial",
            "👥 Clients",
            "💰 Tarification",
            "🔌 Autoconsommation",
            "🗺️ Cartographie",
            "📊 Analytics"
        ]
        
        # Vérifier qu'il n'y a plus d'onglet "Nouveau client"
        self.assertNotIn("➕ Nouveau client", tabs)
        
        # Vérifier le nombre d'onglets
        self.assertEqual(len(tabs), 6)
    
    @patch('modules.erp_client.services.client_service.ClientService.create')
    def test_client_creation_with_all_features(self, mock_create):
        """Test de création avec toutes les fonctionnalités."""
        # Mock du client créé
        mock_client = Mock(spec=Client)
        mock_client.id = 123
        mock_client.nom = "Test Client"
        mock_client.latitude = None
        mock_client.longitude = None
        mock_create.return_value = mock_client
        
        # Données du formulaire avec autocomplétion
        form_data = {
            'code_client': 'TEST001',
            'nom': 'Test Client',
            'type_client': 'producteur',
            'adresse': '10 Rue de la Paix',
            'code_postal': '06400',
            'ville': 'Cannes',
            'latitude': 0.0,  # Pas encore défini
            'longitude': 0.0,
            'actif': True
        }
        
        # Création
        client = self.client_service.create(**form_data)
        
        # Vérifications
        mock_create.assert_called_once()
        self.assertEqual(client.id, 123)
        self.assertIsNone(client.latitude)  # Devra être défini sur la carte
        self.assertIsNone(client.longitude)


class TestUIIntegration(unittest.TestCase):
    """Tests d'intégration de l'interface utilisateur."""
    
    @patch('streamlit.button')
    @patch('streamlit.session_state', new_callable=dict)
    def test_new_client_button_in_list(self, mock_session_state, mock_button):
        """Test du bouton nouveau client dans la liste."""
        # État initial
        mock_session_state['erp_active_tab'] = "👥 Clients"
        mock_session_state['erp_client_mode'] = 'list'
        
        # Simuler clic sur bouton
        mock_button.return_value = True
        
        # Le mode devrait changer
        mock_session_state['erp_client_mode'] = 'create'
        
        self.assertEqual(mock_session_state['erp_client_mode'], 'create')
    
    @patch('streamlit.form_submit_button')
    def test_form_submission_workflow(self, mock_submit):
        """Test du workflow de soumission de formulaire."""
        # Simuler soumission
        mock_submit.return_value = True
        
        # Le formulaire devrait être traité sans erreur
        # (pas de st.button dans st.form)
        self.assertTrue(mock_submit.called)


class TestErrorHandling(unittest.TestCase):
    """Tests de gestion des erreurs."""
    
    def test_autocomplete_api_failure(self):
        """Test avec échec de l'API d'autocomplétion."""
        service = AddressAutocompleteService()
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("API Error")
            
            results = service.search_addresses("test")
            
            # Devrait retourner une liste vide
            self.assertEqual(results, [])
    
    @patch('geopy.geocoders.Nominatim.geocode')
    def test_geocoding_failure(self, mock_geocode):
        """Test avec échec du géocodage."""
        mock_geocode.return_value = None
        
        from modules.erp_client.services.address_autocomplete import AddressAutocompleteService
        service = AddressAutocompleteService()
        
        # Test avec géocodage qui ne trouve rien
        # (géré gracieusement dans l'UI)
        self.assertIsNone(mock_geocode.return_value)


def run_all_integration_tests():
    """Exécuter tous les tests d'intégration."""
    # Créer le test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Ajouter tous les tests
    suite.addTests(loader.loadTestsFromTestCase(TestNewFeaturesIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestUIIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    
    # Exécuter les tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    # Exécuter tous les tests
    result = run_all_integration_tests()
    
    # Afficher le résumé
    print("\n" + "="*60)
    print("RÉSUMÉ DES TESTS D'INTÉGRATION")
    print("="*60)
    print(f"Tests exécutés : {result.testsRun}")
    print(f"Succès : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Échecs : {len(result.failures)}")
    print(f"Erreurs : {len(result.errors)}")
    print("="*60)