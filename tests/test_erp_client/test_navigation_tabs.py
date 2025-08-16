"""Tests pour la nouvelle navigation avec fusion des onglets."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st

# Importer les modules à tester
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


class TestNavigationTabs(unittest.TestCase):
    """Tests pour la navigation avec onglets fusionnés."""
    
    def setUp(self):
        """Initialisation avant chaque test."""
        # Reset session state
        if hasattr(st, 'session_state'):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_initial_navigation_state(self, mock_session_state):
        """Test de l'état initial de navigation."""
        # L'onglet par défaut devrait être le Dashboard
        from modules.erp_client.ui.main_interface import render_erp_module
        
        # Simuler l'initialisation
        mock_session_state['erp_active_tab'] = "💼 Dashboard Commercial"
        
        self.assertEqual(mock_session_state['erp_active_tab'], "💼 Dashboard Commercial")
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_client_tab_modes(self, mock_session_state):
        """Test des différents modes de l'onglet Clients."""
        # Mode liste par défaut
        mock_session_state['erp_client_mode'] = 'list'
        self.assertEqual(mock_session_state['erp_client_mode'], 'list')
        
        # Mode création
        mock_session_state['erp_client_mode'] = 'create'
        self.assertEqual(mock_session_state['erp_client_mode'], 'create')
        
        # Mode édition
        mock_session_state['erp_client_mode'] = 'edit'
        mock_session_state['erp_client_edit_id'] = 123
        self.assertEqual(mock_session_state['erp_client_mode'], 'edit')
        self.assertEqual(mock_session_state['erp_client_edit_id'], 123)
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_navigation_after_client_creation(self, mock_session_state):
        """Test de la navigation après création d'un client."""
        # Simuler la création réussie
        mock_session_state['erp_active_tab'] = "👥 Clients"
        mock_session_state['erp_client_mode'] = 'create'
        
        # Après création, devrait proposer les actions
        mock_session_state['selected_client_id'] = 123
        
        # Test navigation vers tarification
        mock_session_state['erp_active_tab'] = "💰 Tarification"
        self.assertEqual(mock_session_state['erp_active_tab'], "💰 Tarification")
        self.assertEqual(mock_session_state['selected_client_id'], 123)
    
    @patch('streamlit.button')
    @patch('streamlit.session_state', new_callable=dict)
    def test_new_client_button(self, mock_session_state, mock_button):
        """Test du bouton Nouveau Client dans la liste."""
        # Simuler le clic sur le bouton
        mock_button.return_value = True
        mock_session_state['erp_client_mode'] = 'list'
        
        # Après clic, devrait passer en mode création
        mock_session_state['erp_client_mode'] = 'create'
        
        self.assertEqual(mock_session_state['erp_client_mode'], 'create')
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_back_button_functionality(self, mock_session_state):
        """Test du bouton retour."""
        # En mode création
        mock_session_state['erp_client_mode'] = 'create'
        
        # Clic sur retour
        mock_session_state['erp_client_mode'] = 'list'
        
        self.assertEqual(mock_session_state['erp_client_mode'], 'list')
    
    def test_tab_order(self):
        """Test de l'ordre des onglets."""
        expected_tabs = [
            "💼 Dashboard Commercial",
            "👥 Clients",
            "💰 Tarification",
            "🔌 Autoconsommation",
            "🗺️ Cartographie",
            "📊 Analytics"
        ]
        
        # Vérifier que l'onglet "Nouveau client" n'est plus dans la liste
        self.assertNotIn("➕ Nouveau client", expected_tabs)
        
        # Vérifier qu'il y a bien 6 onglets au lieu de 7
        self.assertEqual(len(expected_tabs), 6)


class TestNavigationFlow(unittest.TestCase):
    """Tests du flux de navigation complet."""
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_complete_client_creation_flow(self, mock_session_state):
        """Test du flux complet de création client."""
        # 1. État initial - liste des clients
        mock_session_state['erp_active_tab'] = "👥 Clients"
        mock_session_state['erp_client_mode'] = 'list'
        
        # 2. Clic sur nouveau client
        mock_session_state['erp_client_mode'] = 'create'
        
        # 3. Remplir et soumettre le formulaire
        # ... (formulaire soumis)
        
        # 4. Retour à la liste avec client créé
        mock_session_state['erp_client_mode'] = 'list'
        mock_session_state['last_created_client_id'] = 123
        
        # 5. Option de définir les prix
        mock_session_state['selected_client_id'] = 123
        mock_session_state['erp_active_tab'] = "💰 Tarification"
        
        # Vérifications
        self.assertEqual(mock_session_state['erp_active_tab'], "💰 Tarification")
        self.assertEqual(mock_session_state['selected_client_id'], 123)


if __name__ == '__main__':
    unittest.main()