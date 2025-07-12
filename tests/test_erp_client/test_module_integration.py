"""Tests d'intégration avec les autres modules OptimPV.

Ce module teste l'intégration du module ERP avec les modules existants
(facturation, cartographie, analyses financières).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta
import pandas as pd
import json

from modules.erp_client.connectors.billing_connector import BillingConnector
from modules.erp_client.connectors.map_connector import MapConnector
from modules.erp_client.connectors.financial_connector import FinancialConnector
from modules.erp_client.models.client import Client, TypeClient
from modules.erp_client.models.pricing import PrixClient, TypeTarif
from modules.erp_client.models.autoconso import PointProduction, PointConsommation


class TestBillingIntegration:
    """Tests pour l'intégration avec le module de facturation."""
    
    @pytest.fixture
    def billing_connector(self):
        """Crée une instance du connecteur de facturation."""
        mock_db = Mock()
        mock_client_service = Mock()
        mock_pricing_service = Mock()
        return BillingConnector(mock_db, mock_client_service, mock_pricing_service)
    
    def test_sync_client_to_billing(self, billing_connector):
        """Test la synchronisation d'un client vers la facturation."""
        # Client ERP
        client = Client(
            id=1,
            code_client="CL001",
            nom="Test Client",
            type_client=TypeClient.CONSOMMATEUR,
            email="test@example.com",
            siret="12345678900011"
        )
        
        # Mock de la base billing
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = None  # Client n'existe pas
            
            result = billing_connector.sync_client_to_billing(client)
            
            # Vérifier l'insertion
            assert mock_cursor.execute.called
            insert_call = None
            for call in mock_cursor.execute.call_args_list:
                if "INSERT INTO clients" in call[0][0]:
                    insert_call = call
                    break
            
            assert insert_call is not None
            assert "CL001" in insert_call[0][1]  # code_client dans les paramètres
    
    def test_sync_pricing_to_billing(self, billing_connector):
        """Test la synchronisation des prix vers la facturation."""
        # Prix ERP
        prix = PrixClient(
            id=1,
            client_id=1,
            prix_kwh=0.15,
            date_debut=date.today(),
            type_tarif=TypeTarif.FIXE,
            remise_pourcentage=10.0
        )
        
        # Mock client
        billing_connector.client_service.get_by_id.return_value = Client(
            id=1,
            code_client="CL001",
            nom="Test",
            type_client=TypeClient.CONSOMMATEUR
        )
        
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            # Le client existe dans billing
            mock_cursor.fetchone.return_value = (1,)
            
            result = billing_connector.sync_pricing_to_billing(prix)
            
            # Vérifier la mise à jour du tarif
            assert mock_cursor.execute.called
            update_call = None
            for call in mock_cursor.execute.call_args_list:
                if "UPDATE clients SET" in call[0][0] and "tarif_kwh" in call[0][0]:
                    update_call = call
                    break
            
            assert update_call is not None
            assert 0.135 in update_call[0][1]  # Prix avec remise: 0.15 * 0.9
    
    def test_import_billing_history(self, billing_connector):
        """Test l'import de l'historique de facturation."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            # Données de facturation simulées
            mock_cursor.fetchall.return_value = [
                (1, "CL001", "Client Test", "consommateur", "test@example.com", "12345678900011"),
                (2, "CL002", "Client 2", "producteur", "test2@example.com", None)
            ]
            
            results = billing_connector.import_billing_clients()
            
            assert results['imported'] == 2
            assert results['errors'] == 0
            
            # Vérifier les appels de création
            assert billing_connector.client_service.create.call_count == 2
    
    def test_get_client_invoices(self, billing_connector):
        """Test la récupération des factures d'un client."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            # Factures simulées
            mock_cursor.fetchall.return_value = [
                (1, "FACT-2024-001", "2024-01-15", 1500.50, "payee"),
                (2, "FACT-2024-002", "2024-02-15", 1600.75, "en_attente")
            ]
            
            factures = billing_connector.get_client_invoices("CL001")
            
            assert len(factures) == 2
            assert factures[0]['numero'] == "FACT-2024-001"
            assert factures[0]['montant'] == 1500.50
            assert factures[1]['statut'] == "en_attente"


class TestMapIntegration:
    """Tests pour l'intégration avec le module de cartographie."""
    
    @pytest.fixture
    def map_connector(self):
        """Crée une instance du connecteur de carte."""
        mock_client_service = Mock()
        mock_capacity_service = Mock()
        return MapConnector(mock_client_service, mock_capacity_service)
    
    def test_get_clients_for_map(self, map_connector):
        """Test la récupération des clients pour la carte."""
        # Clients avec coordonnées
        clients = [
            Client(
                id=1,
                code_client="CL001",
                nom="Producteur Solar",
                type_client=TypeClient.PRODUCTEUR,
                latitude=43.7,
                longitude=7.26,
                adresse="Nice"
            ),
            Client(
                id=2,
                code_client="CL002",
                nom="Consommateur Eco",
                type_client=TypeClient.CONSOMMATEUR,
                latitude=43.6,
                longitude=7.0,
                adresse="Antibes"
            )
        ]
        
        map_connector.client_service.get_all.return_value = clients
        
        # Points de production pour le producteur
        map_connector.capacity_service.get_production_points_by_client.return_value = [
            Mock(capacite_kwc=100.0),
            Mock(capacite_kwc=50.0)
        ]
        
        # Points de consommation pour le consommateur
        map_connector.capacity_service.get_consumption_points_by_client.return_value = [
            Mock(consommation_annuelle_kwh=50000)
        ]
        
        data = map_connector.get_clients_for_map()
        
        assert len(data) == 2
        
        # Vérifier les données du producteur
        prod_data = next(d for d in data if d['type_client'] == 'producteur')
        assert prod_data['nom'] == "Producteur Solar"
        assert prod_data['points_production'] == 2
        assert prod_data['capacite_totale'] == 150.0
        
        # Vérifier les données du consommateur
        cons_data = next(d for d in data if d['type_client'] == 'consommateur')
        assert cons_data['nom'] == "Consommateur Eco"
        assert cons_data['points_consommation'] == 1
        assert cons_data['consommation_totale'] == 50000
    
    def test_get_autoconso_operations_for_map(self, map_connector):
        """Test la récupération des opérations d'autoconso pour la carte."""
        # Mock des allocations actives
        allocations = [
            Mock(
                point_production_id=1,
                point_production_nom="Solar Park 1",
                point_production_lat=43.7,
                point_production_lon=7.26,
                point_consommation_id=1,
                point_consommation_ref="PDL001",
                point_consommation_lat=43.71,
                point_consommation_lon=7.27,
                client_consommateur_nom="Client A",
                pourcentage_allocation=50.0,
                capacite_allouee_kwc=25.0
            )
        ]
        
        map_connector.capacity_service.get_all_active_allocations.return_value = allocations
        
        operations = map_connector.get_autoconso_operations_for_map()
        
        assert len(operations) == 1
        op = operations[0]
        
        assert op['production']['nom'] == "Solar Park 1"
        assert op['consommation']['nom'] == "Client A - PDL001"
        assert op['allocation'] == 50.0
        assert op['capacite_kwc'] == 25.0
    
    def test_get_capacity_heatmap_data(self, map_connector):
        """Test la génération de données pour heatmap de capacité."""
        # Points de production avec différents taux d'utilisation
        points = [
            Mock(
                nom="Prod 1",
                latitude=43.7,
                longitude=7.26,
                capacite_kwc=100.0,
                capacite_disponible_kwc=20.0  # 80% utilisé
            ),
            Mock(
                nom="Prod 2",
                latitude=43.6,
                longitude=7.0,
                capacite_kwc=200.0,
                capacite_disponible_kwc=100.0  # 50% utilisé
            )
        ]
        
        map_connector.capacity_service.get_all_production_points.return_value = points
        
        heatmap_data = map_connector.get_capacity_heatmap_data()
        
        assert len(heatmap_data) == 2
        
        # Vérifier les intensités (basées sur l'utilisation)
        high_usage = next(d for d in heatmap_data if d['nom'] == "Prod 1")
        assert high_usage['intensity'] == 0.8  # 80% utilisé
        
        low_usage = next(d for d in heatmap_data if d['nom'] == "Prod 2")
        assert low_usage['intensity'] == 0.5  # 50% utilisé


class TestFinancialIntegration:
    """Tests pour l'intégration avec les analyses financières."""
    
    @pytest.fixture
    def financial_connector(self):
        """Crée une instance du connecteur financier."""
        mock_client_service = Mock()
        mock_pricing_service = Mock()
        mock_capacity_service = Mock()
        return FinancialConnector(
            mock_client_service,
            mock_pricing_service,
            mock_capacity_service
        )
    
    def test_get_revenue_projections(self, financial_connector):
        """Test les projections de revenus."""
        # Client producteur avec allocation
        client = Client(
            id=1,
            code_client="PROD001",
            nom="Producteur Test",
            type_client=TypeClient.PRODUCTEUR
        )
        
        financial_connector.client_service.get_by_id.return_value = client
        
        # Prix actif
        financial_connector.pricing_service.get_prix_actif.return_value = PrixClient(
            prix_kwh=0.15,
            type_tarif=TypeTarif.FIXE
        )
        
        # Points de production avec allocations
        allocations = [
            Mock(
                capacite_allouee_kwc=50.0,
                client_consommateur_nom="Client A",
                pourcentage_allocation=50.0
            ),
            Mock(
                capacite_allouee_kwc=30.0,
                client_consommateur_nom="Client B",
                pourcentage_allocation=30.0
            )
        ]
        
        financial_connector.capacity_service.get_allocations_by_producer.return_value = allocations
        
        # Projections sur 5 ans
        projections = financial_connector.get_revenue_projections(
            client_id=1,
            years=5,
            production_specifique=1200  # kWh/kWc/an
        )
        
        assert len(projections) == 5
        
        # Vérifier le calcul pour la première année
        # Capacité totale allouée: 80 kWc
        # Production: 80 * 1200 = 96,000 kWh
        # Revenu: 96,000 * 0.15 = 14,400 €
        assert projections[0]['year'] == date.today().year
        assert projections[0]['revenue'] == 14400.0
        assert projections[0]['allocated_capacity'] == 80.0
    
    def test_get_consumption_costs(self, financial_connector):
        """Test le calcul des coûts de consommation."""
        # Client consommateur
        client = Client(
            id=1,
            code_client="CONS001",
            nom="Consommateur Test",
            type_client=TypeClient.CONSOMMATEUR
        )
        
        financial_connector.client_service.get_by_id.return_value = client
        
        # Prix actif avec remise
        financial_connector.pricing_service.get_prix_actif.return_value = PrixClient(
            prix_kwh=0.20,
            remise_pourcentage=10.0,
            type_tarif=TypeTarif.INDEXE
        )
        
        # Points de consommation
        points = [
            Mock(
                reference_interne="PDL001",
                consommation_annuelle_kwh=30000,
                allocation=Mock(pourcentage_allocation=60.0)  # 60% autoconso
            ),
            Mock(
                reference_interne="PDL002",
                consommation_annuelle_kwh=20000,
                allocation=None  # Pas d'autoconso
            )
        ]
        
        financial_connector.capacity_service.get_consumption_points_by_client.return_value = points
        
        # Pour chaque point, récupérer l'allocation
        def get_allocation_side_effect(point_id):
            if point_id == points[0].id:
                return points[0].allocation
            return None
        
        financial_connector.capacity_service.get_allocation_for_consumption.side_effect = get_allocation_side_effect
        
        costs = financial_connector.get_consumption_costs(client_id=1)
        
        # Point 1: 30,000 kWh dont 60% autoconso = 12,000 kWh réseau
        # Point 2: 20,000 kWh tout réseau
        # Total réseau: 32,000 kWh
        # Prix effectif: 0.20 * 0.9 = 0.18 €/kWh
        # Coût total: 32,000 * 0.18 = 5,760 €
        
        assert costs['total_consumption_kwh'] == 50000
        assert costs['autoconso_kwh'] == 18000  # 30,000 * 0.6
        assert costs['grid_kwh'] == 32000
        assert costs['total_cost'] == 5760.0
        assert costs['savings_from_autoconso'] == 3240.0  # 18,000 * 0.18
    
    def test_get_roi_analysis(self, financial_connector):
        """Test l'analyse de retour sur investissement."""
        # Configuration pour un producteur
        client_id = 1
        
        # Revenus annuels projetés
        financial_connector.get_revenue_projections.return_value = [
            {'year': 2024, 'revenue': 15000},
            {'year': 2025, 'revenue': 15300},
            {'year': 2026, 'revenue': 15606}
        ]
        
        # Paramètres d'investissement
        investment = 100000  # 100k€
        operating_costs = 2000  # 2k€/an
        
        roi = financial_connector.calculate_roi(
            client_id=client_id,
            initial_investment=investment,
            annual_operating_costs=operating_costs,
            years=3
        )
        
        # Cash flows nets
        # Année 1: 15,000 - 2,000 = 13,000
        # Année 2: 15,300 - 2,000 = 13,300
        # Année 3: 15,606 - 2,000 = 13,606
        
        assert roi['initial_investment'] == 100000
        assert roi['total_revenue'] == 45906  # Somme des revenus
        assert roi['total_costs'] == 6000  # 3 ans * 2000
        assert roi['net_profit'] == -60094  # 45906 - 6000 - 100000
        assert roi['roi_percentage'] == -60.094
        assert roi['payback_period'] > 3  # Pas rentabilisé en 3 ans
    
    def test_export_financial_report(self, financial_connector):
        """Test l'export du rapport financier."""
        # Mock des données
        client = Client(
            id=1,
            code_client="CL001",
            nom="Client Test",
            type_client=TypeClient.PROSUMER
        )
        
        financial_connector.client_service.get_by_id.return_value = client
        
        # Données financières simulées
        financial_connector.get_revenue_projections.return_value = [
            {'year': 2024, 'revenue': 10000}
        ]
        financial_connector.get_consumption_costs.return_value = {
            'total_cost': 8000,
            'savings_from_autoconso': 2000
        }
        
        with patch('pandas.DataFrame.to_excel') as mock_to_excel:
            report_data = financial_connector.export_financial_report(
                client_id=1,
                format='excel'
            )
            
            assert report_data is not None
            assert mock_to_excel.called
    
    def test_bulk_financial_analysis(self, financial_connector):
        """Test l'analyse financière en masse."""
        # Clients à analyser
        clients = [
            Client(id=1, code_client="CL001", nom="Client 1", type_client=TypeClient.PRODUCTEUR),
            Client(id=2, code_client="CL002", nom="Client 2", type_client=TypeClient.CONSOMMATEUR),
            Client(id=3, code_client="CL003", nom="Client 3", type_client=TypeClient.PROSUMER)
        ]
        
        financial_connector.client_service.search.return_value = clients
        
        # Mock des analyses individuelles
        def revenue_side_effect(client_id, **kwargs):
            if client_id in [1, 3]:  # Producteurs et prosumers
                return [{'year': 2024, 'revenue': 10000 * client_id}]
            return []
        
        def costs_side_effect(client_id):
            if client_id in [2, 3]:  # Consommateurs et prosumers
                return {'total_cost': 5000 * client_id, 'savings_from_autoconso': 1000}
            return {'total_cost': 0, 'savings_from_autoconso': 0}
        
        financial_connector.get_revenue_projections.side_effect = revenue_side_effect
        financial_connector.get_consumption_costs.side_effect = costs_side_effect
        
        results = financial_connector.bulk_financial_analysis(
            zone="Nice",
            client_type=None
        )
        
        assert len(results) == 3
        
        # Vérifier les résultats
        client1_result = next(r for r in results if r['client_id'] == 1)
        assert client1_result['type'] == 'producteur'
        assert client1_result['projected_revenue'] == 10000
        assert client1_result['projected_costs'] == 0
        
        client3_result = next(r for r in results if r['client_id'] == 3)
        assert client3_result['type'] == 'prosumer'
        assert client3_result['projected_revenue'] == 30000
        assert client3_result['projected_costs'] == 15000