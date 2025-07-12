"""Tests d'intégration pour l'interface utilisateur du module ERP.

Ce module teste l'interface Streamlit et les interactions utilisateur.
"""

import pytest
import streamlit as st
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
import pandas as pd
import tempfile
import os

from modules.erp_client.ui.main_interface import render_erp_module
from modules.erp_client.ui.client_form import render_client_form
from modules.erp_client.ui.client_list import render_client_list
from modules.erp_client.ui.pricing_interface import render_pricing_interface
from modules.erp_client.ui.autoconso_dashboard import (
    render_autoconso_dashboard,
    render_operations_dashboard,
    render_production_points,
    render_allocations_management
)
from modules.erp_client.models.client import Client, TypeClient
from modules.erp_client.models.pricing import PrixClient, TypeTarif
from modules.erp_client.models.autoconso import PointProduction, PointConsommation


class TestMainInterface:
    """Tests pour l'interface principale."""
    
    @pytest.fixture
    def mock_services(self):
        """Mock des services."""
        mock_db = Mock()
        mock_client_service = Mock()
        mock_pricing_service = Mock()
        mock_capacity_service = Mock()
        mock_geo_service = Mock()
        
        # Configuration par défaut
        mock_client_service.get_statistics.return_value = {
            'total_clients': 10,
            'clients_actifs': 8,
            'producteurs': 4,
            'consommateurs': 5,
            'prosumers': 1
        }
        
        return {
            'db': mock_db,
            'client_service': mock_client_service,
            'pricing_service': mock_pricing_service,
            'capacity_service': mock_capacity_service,
            'geo_service': mock_geo_service
        }
    
    @patch('streamlit.tabs')
    def test_main_interface_tabs(self, mock_tabs, mock_services):
        """Test la création des onglets principaux."""
        # Mock des tabs
        mock_tabs.return_value = [Mock() for _ in range(5)]
        
        with patch('modules.erp_client.database.erp_database.ERPDatabase', return_value=mock_services['db']):
            with patch('modules.erp_client.services.client_service.ClientService', return_value=mock_services['client_service']):
                render_erp_module()
        
        # Vérifier que les tabs sont créés
        mock_tabs.assert_called_once()
        tabs = mock_tabs.call_args[0][0]
        assert len(tabs) == 5
        assert "👥 Clients" in tabs
        assert "💰 Tarification" in tabs
        assert "⚡ Autoconsommation" in tabs
        assert "🗺️ Cartographie" in tabs
        assert "📊 Rapports" in tabs


class TestClientForm:
    """Tests pour le formulaire client."""
    
    @pytest.fixture
    def mock_client_service(self):
        """Mock du service client."""
        service = Mock()
        service.get_by_code.return_value = None  # Pas de doublon par défaut
        service.create.side_effect = lambda c: Client(**c.__dict__, id=1)
        return service
    
    @patch('streamlit.form')
    @patch('streamlit.text_input')
    @patch('streamlit.selectbox')
    @patch('streamlit.form_submit_button')
    def test_create_client_form(self, mock_submit, mock_select, mock_input, mock_form, mock_client_service):
        """Test la création d'un client via formulaire."""
        # Configuration des mocks
        mock_form.return_value.__enter__ = Mock(return_value=Mock())
        mock_form.return_value.__exit__ = Mock(return_value=None)
        
        mock_input.side_effect = ["CL001", "Test Client", "test@example.com", "+33123456789"]
        mock_select.return_value = "producteur"
        mock_submit.return_value = True
        
        # Appel de la fonction
        with patch('streamlit.success') as mock_success:
            render_client_form(mock_client_service)
        
        # Vérifications
        mock_client_service.create.assert_called_once()
        created_client = mock_client_service.create.call_args[0][0]
        assert created_client.code_client == "CL001"
        assert created_client.nom == "Test Client"
        assert created_client.type_client == TypeClient.PRODUCTEUR
        
        mock_success.assert_called_once()
    
    @patch('streamlit.form')
    @patch('streamlit.text_input')
    @patch('streamlit.form_submit_button')
    def test_duplicate_code_validation(self, mock_submit, mock_input, mock_form, mock_client_service):
        """Test la validation des codes en double."""
        # Configuration
        mock_form.return_value.__enter__ = Mock(return_value=Mock())
        mock_form.return_value.__exit__ = Mock(return_value=None)
        
        mock_input.side_effect = ["CL001", "Test Client"]
        mock_submit.return_value = True
        
        # Le code existe déjà
        mock_client_service.get_by_code.return_value = Mock(code_client="CL001")
        
        with patch('streamlit.error') as mock_error:
            render_client_form(mock_client_service)
        
        # Vérifier qu'une erreur est affichée
        mock_error.assert_called()
        assert "existe déjà" in mock_error.call_args[0][0]
        mock_client_service.create.assert_not_called()


class TestClientList:
    """Tests pour la liste des clients."""
    
    @pytest.fixture
    def mock_clients(self):
        """Clients de test."""
        return [
            Client(
                id=1,
                code_client="CL001",
                nom="Client Alpha",
                type_client=TypeClient.PRODUCTEUR,
                ville="Nice",
                actif=True
            ),
            Client(
                id=2,
                code_client="CL002",
                nom="Client Beta",
                type_client=TypeClient.CONSOMMATEUR,
                ville="Paris",
                actif=True
            ),
            Client(
                id=3,
                code_client="CL003",
                nom="Client Gamma",
                type_client=TypeClient.PROSUMER,
                ville="Nice",
                actif=False
            )
        ]
    
    @patch('streamlit.dataframe')
    @patch('streamlit.text_input')
    @patch('streamlit.selectbox')
    def test_client_list_display(self, mock_select, mock_input, mock_df, mock_clients):
        """Test l'affichage de la liste des clients."""
        mock_client_service = Mock()
        mock_client_service.search.return_value = mock_clients
        mock_client_service.get_statistics.return_value = {
            'total_clients': 3,
            'clients_actifs': 2
        }
        
        # Configuration des filtres
        mock_input.return_value = ""  # Pas de recherche
        mock_select.side_effect = ["Tous", "Toutes"]  # Type et zone
        
        render_client_list(mock_client_service)
        
        # Vérifier l'appel dataframe
        mock_df.assert_called_once()
        df_arg = mock_df.call_args[0][0]
        assert isinstance(df_arg, pd.DataFrame)
        assert len(df_arg) == 3
        assert "Client Alpha" in df_arg['Nom'].values
    
    @patch('streamlit.dataframe')
    @patch('streamlit.text_input')
    def test_client_search(self, mock_input, mock_df):
        """Test la recherche de clients."""
        mock_client_service = Mock()
        mock_client_service.search.return_value = [
            Client(
                id=1,
                code_client="CL001",
                nom="Client Alpha",
                type_client=TypeClient.PRODUCTEUR
            )
        ]
        mock_client_service.get_statistics.return_value = {
            'total_clients': 1,
            'clients_actifs': 1
        }
        
        mock_input.return_value = "Alpha"
        
        with patch('streamlit.selectbox', return_value="Tous"):
            render_client_list(mock_client_service)
        
        # Vérifier que la recherche est appelée avec le bon terme
        mock_client_service.search.assert_called()
        call_args = mock_client_service.search.call_args[1]
        assert call_args.get('search_term') == "Alpha"


class TestPricingInterface:
    """Tests pour l'interface de tarification."""
    
    @pytest.fixture
    def mock_pricing_service(self):
        """Mock du service de pricing."""
        service = Mock()
        service.get_prix_actif.return_value = PrixClient(
            id=1,
            client_id=1,
            prix_kwh=0.15,
            date_debut=date.today(),
            type_tarif=TypeTarif.FIXE
        )
        service.get_historique_prix.return_value = []
        service.calculate_projections.return_value = [
            {'annee': 2024, 'prix_projete': 0.15},
            {'annee': 2025, 'prix_projete': 0.153}
        ]
        return service
    
    @patch('streamlit.selectbox')
    @patch('streamlit.metric')
    def test_display_current_price(self, mock_metric, mock_select, mock_pricing_service):
        """Test l'affichage du prix actuel."""
        mock_client_service = Mock()
        mock_client_service.get_all.return_value = [
            Client(id=1, code_client="CL001", nom="Test", type_client=TypeClient.CONSOMMATEUR)
        ]
        
        mock_select.return_value = 1  # ID du client sélectionné
        
        render_pricing_interface(mock_pricing_service, mock_client_service)
        
        # Vérifier l'affichage du prix
        mock_metric.assert_called()
        metric_calls = mock_metric.call_args_list
        
        # Chercher l'appel avec le prix
        prix_displayed = False
        for call in metric_calls:
            if "0.150" in str(call):
                prix_displayed = True
                break
        
        assert prix_displayed
    
    @patch('streamlit.form')
    @patch('streamlit.number_input')
    @patch('streamlit.date_input')
    @patch('streamlit.selectbox')
    @patch('streamlit.form_submit_button')
    def test_create_new_price(self, mock_submit, mock_select, mock_date, mock_number, mock_form, mock_pricing_service):
        """Test la création d'un nouveau prix."""
        # Configuration
        mock_form.return_value.__enter__ = Mock(return_value=Mock())
        mock_form.return_value.__exit__ = Mock(return_value=None)
        
        mock_number.side_effect = [0.16, 5.0]  # Prix et remise
        mock_date.return_value = date.today()
        mock_select.side_effect = [1, "fixe"]  # Client et type tarif
        mock_submit.return_value = True
        
        mock_client_service = Mock()
        mock_client_service.get_all.return_value = [
            Client(id=1, code_client="CL001", nom="Test", type_client=TypeClient.CONSOMMATEUR)
        ]
        
        mock_pricing_service.create.return_value = Mock(id=1)
        
        with patch('streamlit.success') as mock_success:
            render_pricing_interface(mock_pricing_service, mock_client_service)
        
        # Vérifier la création
        mock_pricing_service.create.assert_called()
        created_prix = mock_pricing_service.create.call_args[0][0]
        assert created_prix.prix_kwh == 0.16
        assert created_prix.remise_pourcentage == 5.0


class TestAutoconsoIntegration:
    """Tests pour l'interface d'autoconsommation."""
    
    @pytest.fixture
    def mock_capacity_service(self):
        """Mock du service de capacité."""
        service = Mock()
        service.get_dashboard_stats.return_value = {
            'total_production_points': 5,
            'active_production_points': 4,
            'total_capacity_kwc': 500.0,
            'available_capacity_kwc': 200.0,
            'total_consumption_points': 10,
            'active_allocations': 8,
            'average_utilization': 60.0
        }
        service.get_capacity_alerts.return_value = [
            {
                'point_name': 'Production 1',
                'level': 'warning',
                'message': 'Capacité élevée',
                'utilization': 85.0
            }
        ]
        service.get_all_production_points.return_value = []
        service.get_all_consumption_points.return_value = []
        return service
    
    @patch('streamlit.metric')
    def test_dashboard_metrics(self, mock_metric, mock_capacity_service):
        """Test l'affichage des métriques du dashboard."""
        mock_client_service = Mock()
        
        render_operations_dashboard(mock_capacity_service, mock_client_service)
        
        # Vérifier que les métriques sont affichées
        assert mock_metric.call_count >= 4
        
        # Vérifier le contenu des métriques
        metric_values = [call[0][1] for call in mock_metric.call_args_list]
        assert 5 in metric_values  # total_production_points
        assert "500.0 kWc" in metric_values or 500.0 in metric_values
    
    @patch('streamlit.warning')
    def test_capacity_alerts_display(self, mock_warning, mock_capacity_service):
        """Test l'affichage des alertes de capacité."""
        mock_client_service = Mock()
        
        render_operations_dashboard(mock_capacity_service, mock_client_service)
        
        # Vérifier qu'une alerte warning est affichée
        mock_warning.assert_called()
        warning_text = mock_warning.call_args[0][0]
        assert "Production 1" in warning_text
        assert "85.0%" in warning_text
    
    @patch('streamlit.form')
    @patch('streamlit.selectbox')
    @patch('streamlit.number_input')
    @patch('streamlit.form_submit_button')
    def test_create_allocation(self, mock_submit, mock_number, mock_select, mock_form, mock_capacity_service):
        """Test la création d'une allocation."""
        # Configuration
        mock_form.return_value.__enter__ = Mock(return_value=Mock())
        mock_form.return_value.__exit__ = Mock(return_value=None)
        
        # Points disponibles
        mock_capacity_service.get_production_points_with_availability.return_value = [
            {'id': 1, 'name': 'Prod 1', 'available_capacity': 50.0, 'total_capacity': 100.0}
        ]
        mock_capacity_service.get_unallocated_consumption_points.return_value = [
            Mock(id=1, client_id=1, reference_interne="REF001")
        ]
        
        mock_client_service = Mock()
        mock_client_service.get_by_id.return_value = Mock(nom="Client Test")
        
        mock_select.side_effect = [1, 1]  # IDs production et consommation
        mock_number.return_value = 30.0  # Pourcentage
        mock_submit.return_value = True
        
        mock_capacity_service.create_allocation.return_value = Mock(id=1)
        
        with patch('streamlit.success') as mock_success:
            render_allocations_management(mock_capacity_service, mock_client_service)
        
        # Vérifier la création
        mock_capacity_service.create_allocation.assert_called()
        created_alloc = mock_capacity_service.create_allocation.call_args[0][0]
        assert created_alloc.pourcentage_allocation == 30.0


class TestMapIntegration:
    """Tests pour l'intégration cartographique."""
    
    @patch('modules.erp_client.connectors.map_connector.get_erp_clients_for_map')
    def test_map_connector(self, mock_get_clients):
        """Test le connecteur de carte."""
        # Données de test
        mock_get_clients.return_value = [
            {
                'id': 1,
                'nom': 'Client Test',
                'type_client': 'producteur',
                'latitude': 43.7,
                'longitude': 7.26,
                'adresse': '123 rue Test',
                'points_production': 2,
                'capacite_totale': 150.0
            }
        ]
        
        from modules.erp_client.connectors.map_connector import get_erp_clients_for_map
        
        clients = get_erp_clients_for_map()
        
        assert len(clients) == 1
        assert clients[0]['nom'] == 'Client Test'
        assert clients[0]['capacite_totale'] == 150.0


class TestExportFunctionality:
    """Tests pour les fonctionnalités d'export."""
    
    @patch('streamlit.download_button')
    @patch('pandas.ExcelWriter')
    def test_export_clients_excel(self, mock_writer, mock_download):
        """Test l'export des clients en Excel."""
        mock_client_service = Mock()
        mock_client_service.get_all.return_value = [
            Client(
                id=1,
                code_client="CL001",
                nom="Test Client",
                type_client=TypeClient.PRODUCTEUR,
                email="test@example.com"
            )
        ]
        
        # Simuler un contexte manager pour ExcelWriter
        mock_writer_instance = MagicMock()
        mock_writer.return_value.__enter__.return_value = mock_writer_instance
        
        # Import et appel de la fonction d'export
        from modules.erp_client.ui.reports_interface import export_clients_excel
        
        with patch('io.BytesIO') as mock_io:
            mock_buffer = Mock()
            mock_io.return_value = mock_buffer
            mock_buffer.getvalue.return_value = b"excel_data"
            
            export_clients_excel(mock_client_service)
        
        # Vérifier l'appel du bouton de téléchargement
        mock_download.assert_called_once()
        assert mock_download.call_args[1]['label'] == "📥 Télécharger Excel"
        assert mock_download.call_args[1]['data'] == b"excel_data"
        assert "clients_export" in mock_download.call_args[1]['file_name']