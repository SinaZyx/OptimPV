"""Tests pour les services du module ERP.

Ce module teste tous les services (ClientService, PricingService, CapacityService)
et leurs interactions avec la base de données.
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch
import logging

from modules.erp_client.database.erp_database import ERPDatabase
from modules.erp_client.services.client_service import ClientService
from modules.erp_client.services.pricing_service import PricingService
from modules.erp_client.services.capacity_service import CapacityService
from modules.erp_client.services.geolocation_service import GeolocationService
from modules.erp_client.models.client import Client, TypeClient
from modules.erp_client.models.pricing import PrixClient, TypeTarif
from modules.erp_client.models.autoconso import (
    PointProduction, PointConsommation, AutoconsoCollective
)


class TestClientService:
    """Tests pour le service de gestion des clients."""
    
    @pytest.fixture
    def temp_db_dir(self):
        """Crée un répertoire temporaire pour les tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def db(self, temp_db_dir):
        """Crée une instance de base de données pour les tests."""
        db_path = os.path.join(temp_db_dir, "test_erp.db")
        return ERPDatabase(db_path)
    
    @pytest.fixture
    def client_service(self, db):
        """Crée une instance du service client."""
        return ClientService(db)
    
    def test_create_client(self, client_service):
        """Test la création d'un client."""
        client = Client(
            code_client="CL001",
            nom="Test Client",
            type_client=TypeClient.PRODUCTEUR,
            email="test@example.com",
            telephone="+33123456789"
        )
        
        created = client_service.create(client)
        
        assert created.id is not None
        assert created.code_client == "CL001"
        assert created.nom == "Test Client"
    
    def test_create_duplicate_code(self, client_service):
        """Test la création avec un code client en double."""
        client1 = Client(
            code_client="CL001",
            nom="Client 1",
            type_client=TypeClient.PRODUCTEUR
        )
        client_service.create(client1)
        
        client2 = Client(
            code_client="CL001",
            nom="Client 2",
            type_client=TypeClient.CONSOMMATEUR
        )
        
        with pytest.raises(ValueError, match="code client existe déjà"):
            client_service.create(client2)
    
    def test_get_by_id(self, client_service):
        """Test la récupération par ID."""
        client = Client(
            code_client="CL001",
            nom="Test Client",
            type_client=TypeClient.PROSUMER
        )
        created = client_service.create(client)
        
        retrieved = client_service.get_by_id(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.code_client == "CL001"
        
        # Test avec ID inexistant
        assert client_service.get_by_id(9999) is None
    
    def test_get_by_code(self, client_service):
        """Test la récupération par code."""
        client = Client(
            code_client="CL001",
            nom="Test Client",
            type_client=TypeClient.PRODUCTEUR
        )
        client_service.create(client)
        
        # Test avec différentes casses
        assert client_service.get_by_code("CL001") is not None
        assert client_service.get_by_code("cl001") is not None
        assert client_service.get_by_code("CL999") is None
    
    def test_update_client(self, client_service):
        """Test la mise à jour d'un client."""
        client = Client(
            code_client="CL001",
            nom="Ancien Nom",
            type_client=TypeClient.CONSOMMATEUR
        )
        created = client_service.create(client)
        
        # Mise à jour
        created.nom = "Nouveau Nom"
        created.email = "nouveau@example.com"
        
        updated = client_service.update(created)
        
        assert updated.nom == "Nouveau Nom"
        assert updated.email == "nouveau@example.com"
        
        # Vérifier en base
        retrieved = client_service.get_by_id(created.id)
        assert retrieved.nom == "Nouveau Nom"
    
    def test_delete_client(self, client_service):
        """Test la suppression d'un client."""
        client = Client(
            code_client="CL001",
            nom="Test Client",
            type_client=TypeClient.PRODUCTEUR
        )
        created = client_service.create(client)
        
        # Suppression
        assert client_service.delete(created.id) is True
        
        # Vérifier que le client n'existe plus
        assert client_service.get_by_id(created.id) is None
        
        # Suppression d'un ID inexistant
        assert client_service.delete(9999) is False
    
    def test_search_clients(self, client_service):
        """Test la recherche de clients."""
        # Créer plusieurs clients
        clients_data = [
            ("CL001", "Alpha Industries", TypeClient.PRODUCTEUR, "Nice"),
            ("CL002", "Beta Corp", TypeClient.CONSOMMATEUR, "Paris"),
            ("CL003", "Gamma Solutions", TypeClient.PROSUMER, "Nice"),
            ("CL004", "Delta Energy", TypeClient.PRODUCTEUR, "Lyon")
        ]
        
        for code, nom, type_client, ville in clients_data:
            client = Client(
                code_client=code,
                nom=nom,
                type_client=type_client,
                ville=ville
            )
            client_service.create(client)
        
        # Test recherche par nom
        results = client_service.search("Beta")
        assert len(results) == 1
        assert results[0].nom == "Beta Corp"
        
        # Test recherche par ville
        results = client_service.search(zone="Nice")
        assert len(results) == 2
        
        # Test recherche par type
        results = client_service.search(type_client=TypeClient.PRODUCTEUR)
        assert len(results) == 2
        
        # Test recherche combinée
        results = client_service.search(zone="Nice", type_client=TypeClient.PROSUMER)
        assert len(results) == 1
        assert results[0].nom == "Gamma Solutions"
    
    def test_get_statistics(self, client_service):
        """Test les statistiques des clients."""
        # Base vide
        stats = client_service.get_statistics()
        assert stats['total_clients'] == 0
        assert stats['clients_actifs'] == 0
        
        # Ajouter des clients
        for i in range(5):
            client = Client(
                code_client=f"CL00{i}",
                nom=f"Client {i}",
                type_client=TypeClient.PRODUCTEUR if i % 2 == 0 else TypeClient.CONSOMMATEUR,
                actif=i < 3  # Seuls les 3 premiers sont actifs
            )
            client_service.create(client)
        
        stats = client_service.get_statistics()
        assert stats['total_clients'] == 5
        assert stats['clients_actifs'] == 3
        assert stats['producteurs'] == 3  # Indices 0, 2, 4
        assert stats['consommateurs'] == 2  # Indices 1, 3
        assert stats['prosumers'] == 0
    
    def test_get_producteurs(self, client_service):
        """Test la récupération des producteurs."""
        # Créer différents types de clients
        prod1 = client_service.create(Client(
            code_client="PROD001",
            nom="Producteur 1",
            type_client=TypeClient.PRODUCTEUR
        ))
        
        prod2 = client_service.create(Client(
            code_client="PROS001",
            nom="Prosumer 1",
            type_client=TypeClient.PROSUMER
        ))
        
        cons = client_service.create(Client(
            code_client="CONS001",
            nom="Consommateur 1",
            type_client=TypeClient.CONSOMMATEUR
        ))
        
        producteurs = client_service.get_producteurs()
        
        # Les producteurs incluent producteurs et prosumers
        assert len(producteurs) == 2
        codes = [p.code_client for p in producteurs]
        assert "PROD001" in codes
        assert "PROS001" in codes
        assert "CONS001" not in codes
    
    def test_bulk_import(self, client_service):
        """Test l'import en masse de clients."""
        clients_data = [
            {
                'code_client': 'IMP001',
                'nom': 'Import 1',
                'type_client': 'producteur',
                'email': 'imp1@example.com'
            },
            {
                'code_client': 'IMP002',
                'nom': 'Import 2',
                'type_client': 'consommateur',
                'email': 'imp2@example.com'
            }
        ]
        
        results = client_service.bulk_import(clients_data)
        
        assert results['success'] == 2
        assert results['errors'] == 0
        
        # Vérifier que les clients sont créés
        assert client_service.get_by_code("IMP001") is not None
        assert client_service.get_by_code("IMP002") is not None
        
        # Test avec erreur
        clients_data_error = [
            {
                'code_client': 'IMP001',  # Doublon
                'nom': 'Duplicate',
                'type_client': 'producteur'
            },
            {
                'code_client': 'IMP003',
                'nom': 'Valid',
                'type_client': 'invalid_type'  # Type invalide
            }
        ]
        
        results = client_service.bulk_import(clients_data_error)
        assert results['success'] == 0
        assert results['errors'] == 2


class TestPricingService:
    """Tests pour le service de gestion des prix."""
    
    @pytest.fixture
    def pricing_service(self, db, client_service):
        """Crée une instance du service de pricing."""
        return PricingService(db)
    
    @pytest.fixture
    def test_client(self, client_service):
        """Crée un client de test."""
        return client_service.create(Client(
            code_client="CL001",
            nom="Client Test Prix",
            type_client=TypeClient.CONSOMMATEUR
        ))
    
    def test_create_prix(self, pricing_service, test_client):
        """Test la création d'un prix."""
        prix = PrixClient(
            client_id=test_client.id,
            prix_kwh=0.15,
            date_debut=date.today(),
            type_tarif=TypeTarif.FIXE,
            reference_prix="TARIF_2024"
        )
        
        created = pricing_service.create(prix)
        
        assert created.id is not None
        assert created.prix_kwh == 0.15
        assert created.type_tarif == TypeTarif.FIXE
    
    def test_get_prix_actif(self, pricing_service, test_client):
        """Test la récupération du prix actif."""
        # Créer plusieurs prix
        prix_ancien = PrixClient(
            client_id=test_client.id,
            prix_kwh=0.14,
            date_debut=date.today() - timedelta(days=365),
            date_fin=date.today() - timedelta(days=1),
            type_tarif=TypeTarif.FIXE
        )
        pricing_service.create(prix_ancien)
        
        prix_actuel = PrixClient(
            client_id=test_client.id,
            prix_kwh=0.15,
            date_debut=date.today(),
            type_tarif=TypeTarif.INDEXE
        )
        pricing_service.create(prix_actuel)
        
        prix_futur = PrixClient(
            client_id=test_client.id,
            prix_kwh=0.16,
            date_debut=date.today() + timedelta(days=30),
            type_tarif=TypeTarif.DYNAMIQUE
        )
        pricing_service.create(prix_futur)
        
        # Récupérer le prix actif
        prix_actif = pricing_service.get_prix_actif(test_client.id)
        
        assert prix_actif is not None
        assert prix_actif.prix_kwh == 0.15
        assert prix_actif.type_tarif == TypeTarif.INDEXE
    
    def test_get_historique_prix(self, pricing_service, test_client):
        """Test la récupération de l'historique des prix."""
        # Créer un historique
        dates = [
            date(2023, 1, 1),
            date(2023, 6, 1),
            date(2024, 1, 1)
        ]
        
        for i, date_debut in enumerate(dates):
            prix = PrixClient(
                client_id=test_client.id,
                prix_kwh=0.10 + i * 0.02,
                date_debut=date_debut,
                type_tarif=TypeTarif.FIXE
            )
            pricing_service.create(prix)
        
        historique = pricing_service.get_historique_prix(test_client.id)
        
        assert len(historique) == 3
        # Vérifier l'ordre (plus récent en premier)
        assert historique[0].date_debut == date(2024, 1, 1)
        assert historique[2].date_debut == date(2023, 1, 1)
    
    def test_update_prix(self, pricing_service, test_client):
        """Test la mise à jour d'un prix."""
        prix = PrixClient(
            client_id=test_client.id,
            prix_kwh=0.15,
            date_debut=date.today(),
            type_tarif=TypeTarif.FIXE
        )
        created = pricing_service.create(prix)
        
        # Mise à jour
        created.prix_kwh = 0.16
        created.remise_pourcentage = 5.0
        
        updated = pricing_service.update(created)
        
        assert updated.prix_kwh == 0.16
        assert updated.remise_pourcentage == 5.0
        assert updated.prix_effectif == 0.152  # 0.16 * 0.95
    
    def test_projections_prix(self, pricing_service, test_client):
        """Test les projections de prix avec inflation."""
        prix_actuel = PrixClient(
            client_id=test_client.id,
            prix_kwh=0.15,
            date_debut=date.today(),
            type_tarif=TypeTarif.INDEXE,
            reference_prix="INDEX_2024"
        )
        pricing_service.create(prix_actuel)
        
        # Projections sur 5 ans avec 2% d'inflation
        projections = pricing_service.calculate_projections(
            client_id=test_client.id,
            annees=5,
            taux_inflation=0.02
        )
        
        assert len(projections) == 5
        # Vérifier la progression
        for i in range(5):
            expected = 0.15 * (1.02 ** (i + 1))
            assert abs(projections[i]['prix_projete'] - expected) < 0.001
            assert projections[i]['annee'] == date.today().year + i + 1
    
    def test_bulk_update_prix(self, pricing_service, client_service):
        """Test la mise à jour en masse des prix."""
        # Créer plusieurs clients
        clients = []
        for i in range(3):
            client = client_service.create(Client(
                code_client=f"BULK{i:03d}",
                nom=f"Client Bulk {i}",
                type_client=TypeClient.CONSOMMATEUR
            ))
            clients.append(client)
            
            # Créer un prix initial
            pricing_service.create(PrixClient(
                client_id=client.id,
                prix_kwh=0.15,
                date_debut=date.today(),
                type_tarif=TypeTarif.FIXE
            ))
        
        # Mise à jour en masse
        updates = pricing_service.bulk_update_prix(
            zone_geographique=None,  # Tous les clients
            nouveau_prix=0.16,
            type_tarif=TypeTarif.INDEXE,
            date_debut=date.today() + timedelta(days=1)
        )
        
        assert updates['success'] == 3
        assert updates['errors'] == 0
        
        # Vérifier les nouveaux prix
        for client in clients:
            prix_actif = pricing_service.get_prix_actif(
                client.id,
                date_reference=date.today() + timedelta(days=1)
            )
            assert prix_actif.prix_kwh == 0.16
            assert prix_actif.type_tarif == TypeTarif.INDEXE


class TestCapacityService:
    """Tests pour le service de gestion des capacités."""
    
    @pytest.fixture
    def capacity_service(self, db):
        """Crée une instance du service de capacité."""
        return CapacityService(db)
    
    @pytest.fixture
    def clients(self, client_service):
        """Crée des clients de test."""
        prod = client_service.create(Client(
            code_client="PROD001",
            nom="Producteur Test",
            type_client=TypeClient.PRODUCTEUR
        ))
        
        cons = client_service.create(Client(
            code_client="CONS001",
            nom="Consommateur Test",
            type_client=TypeClient.CONSOMMATEUR
        ))
        
        return {'producteur': prod, 'consommateur': cons}
    
    def test_create_production_point(self, capacity_service, clients):
        """Test la création d'un point de production."""
        point = PointProduction(
            client_id=clients['producteur'].id,
            nom="Toiture Solaire",
            type_installation="Toiture",
            capacite_kwc=100.0,
            date_mise_service=date.today(),
            adresse="123 rue du Soleil"
        )
        
        created = capacity_service.create_production_point(point)
        
        assert created.id is not None
        assert created.capacite_kwc == 100.0
        assert created.capacite_disponible_kwc == 100.0
    
    def test_create_consumption_point(self, capacity_service, clients):
        """Test la création d'un point de consommation."""
        point = PointConsommation(
            client_id=clients['consommateur'].id,
            reference_interne="PDL123456",
            type_point="Principal",
            consommation_annuelle_kwh=50000,
            puissance_souscrite_kva=36
        )
        
        created = capacity_service.create_consumption_point(point)
        
        assert created.id is not None
        assert created.reference_interne == "PDL123456"
        assert created.consommation_annuelle_kwh == 50000
    
    def test_create_allocation(self, capacity_service, clients):
        """Test la création d'une allocation."""
        # Créer les points
        prod_point = capacity_service.create_production_point(
            PointProduction(
                client_id=clients['producteur'].id,
                nom="Production Test",
                capacite_kwc=100.0
            )
        )
        
        cons_point = capacity_service.create_consumption_point(
            PointConsommation(
                client_id=clients['consommateur'].id,
                reference_interne="REF001"
            )
        )
        
        # Créer l'allocation
        allocation = AutoconsoCollective(
            point_production_id=prod_point.id,
            point_consommation_id=cons_point.id,
            pourcentage_allocation=50.0,
            date_debut=date.today()
        )
        
        created = capacity_service.create_allocation(allocation)
        
        assert created.id is not None
        assert created.pourcentage_allocation == 50.0
        
        # Vérifier la mise à jour de la capacité disponible
        prod_point_updated = capacity_service.get_production_point(prod_point.id)
        assert prod_point_updated.capacite_disponible_kwc == 50.0
    
    def test_capacity_validation(self, capacity_service, clients):
        """Test la validation de capacité lors des allocations."""
        # Créer un point de production
        prod_point = capacity_service.create_production_point(
            PointProduction(
                client_id=clients['producteur'].id,
                nom="Production Limitée",
                capacite_kwc=100.0
            )
        )
        
        # Créer deux points de consommation
        cons_points = []
        for i in range(2):
            point = capacity_service.create_consumption_point(
                PointConsommation(
                    client_id=clients['consommateur'].id,
                    reference_interne=f"REF00{i+1}"
                )
            )
            cons_points.append(point)
        
        # Première allocation : 70%
        alloc1 = capacity_service.create_allocation(
            AutoconsoCollective(
                point_production_id=prod_point.id,
                point_consommation_id=cons_points[0].id,
                pourcentage_allocation=70.0,
                date_debut=date.today()
            )
        )
        assert alloc1 is not None
        
        # Deuxième allocation : 40% (devrait échouer)
        with pytest.raises(ValueError, match="Capacité insuffisante"):
            capacity_service.create_allocation(
                AutoconsoCollective(
                    point_production_id=prod_point.id,
                    point_consommation_id=cons_points[1].id,
                    pourcentage_allocation=40.0,
                    date_debut=date.today()
                )
            )
    
    def test_get_dashboard_stats(self, capacity_service, clients):
        """Test les statistiques du dashboard."""
        # Créer des données de test
        for i in range(3):
            prod_point = capacity_service.create_production_point(
                PointProduction(
                    client_id=clients['producteur'].id,
                    nom=f"Production {i+1}",
                    capacite_kwc=100.0 * (i + 1)
                )
            )
            
            if i < 2:  # Créer des allocations pour les 2 premiers
                cons_point = capacity_service.create_consumption_point(
                    PointConsommation(
                        client_id=clients['consommateur'].id,
                        reference_interne=f"CONS{i+1:03d}"
                    )
                )
                
                capacity_service.create_allocation(
                    AutoconsoCollective(
                        point_production_id=prod_point.id,
                        point_consommation_id=cons_point.id,
                        pourcentage_allocation=60.0,
                        date_debut=date.today()
                    )
                )
        
        stats = capacity_service.get_dashboard_stats()
        
        assert stats['total_production_points'] == 3
        assert stats['active_production_points'] == 3
        assert stats['total_capacity_kwc'] == 600.0  # 100 + 200 + 300
        assert stats['available_capacity_kwc'] == 420.0  # 40 + 80 + 300
        assert stats['total_consumption_points'] == 2
        assert stats['active_allocations'] == 2
    
    def test_capacity_alerts(self, capacity_service, clients):
        """Test les alertes de capacité."""
        # Créer des points avec différents taux d'utilisation
        points_data = [
            ("Saturé", 100.0, 95.0),    # 95% utilisé - critique
            ("Presque plein", 100.0, 85.0),  # 85% utilisé - warning
            ("Normal", 100.0, 50.0),     # 50% utilisé - ok
        ]
        
        for nom, capacite, allocation_pct in points_data:
            prod_point = capacity_service.create_production_point(
                PointProduction(
                    client_id=clients['producteur'].id,
                    nom=nom,
                    capacite_kwc=capacite
                )
            )
            
            if allocation_pct > 0:
                cons_point = capacity_service.create_consumption_point(
                    PointConsommation(
                        client_id=clients['consommateur'].id,
                        reference_interne=f"REF_{nom}"
                    )
                )
                
                capacity_service.create_allocation(
                    AutoconsoCollective(
                        point_production_id=prod_point.id,
                        point_consommation_id=cons_point.id,
                        pourcentage_allocation=allocation_pct,
                        date_debut=date.today()
                    )
                )
        
        alerts = capacity_service.get_capacity_alerts()
        
        assert len(alerts) == 2  # Seulement saturé et presque plein
        
        # Vérifier les niveaux
        alert_levels = {alert['point_name']: alert['level'] for alert in alerts}
        assert alert_levels.get("Saturé") == "critical"
        assert alert_levels.get("Presque plein") == "warning"
    
    def test_optimization_suggestions(self, capacity_service, clients):
        """Test les suggestions d'optimisation."""
        # Créer un scénario pour optimisation
        # Point 1: sous-utilisé (30%)
        prod1 = capacity_service.create_production_point(
            PointProduction(
                client_id=clients['producteur'].id,
                nom="Sous-utilisé",
                capacite_kwc=200.0
            )
        )
        
        cons1 = capacity_service.create_consumption_point(
            PointConsommation(
                client_id=clients['consommateur'].id,
                reference_interne="CONS001",
                consommation_annuelle_kwh=100000
            )
        )
        
        capacity_service.create_allocation(
            AutoconsoCollective(
                point_production_id=prod1.id,
                point_consommation_id=cons1.id,
                pourcentage_allocation=30.0,
                date_debut=date.today()
            )
        )
        
        # Point 2: sur-utilisé (90%)
        prod2 = capacity_service.create_production_point(
            PointProduction(
                client_id=clients['producteur'].id,
                nom="Sur-utilisé",
                capacite_kwc=100.0
            )
        )
        
        cons2 = capacity_service.create_consumption_point(
            PointConsommation(
                client_id=clients['consommateur'].id,
                reference_interne="CONS002",
                consommation_annuelle_kwh=50000
            )
        )
        
        capacity_service.create_allocation(
            AutoconsoCollective(
                point_production_id=prod2.id,
                point_consommation_id=cons2.id,
                pourcentage_allocation=90.0,
                date_debut=date.today()
            )
        )
        
        suggestions = capacity_service.get_optimization_suggestions()
        
        assert len(suggestions) > 0
        
        # Vérifier les types de suggestions
        suggestion_types = [s['type'] for s in suggestions]
        assert 'reallocation' in suggestion_types or 'capacity_warning' in suggestion_types


class TestGeolocationService:
    """Tests pour le service de géolocalisation."""
    
    @pytest.fixture
    def geo_service(self):
        """Crée une instance du service de géolocalisation."""
        return GeolocationService()
    
    @patch('geopy.geocoders.Nominatim.geocode')
    def test_geocode_address(self, mock_geocode, geo_service):
        """Test le géocodage d'une adresse."""
        # Mock de la réponse
        mock_location = Mock()
        mock_location.latitude = 43.7
        mock_location.longitude = 7.26
        mock_geocode.return_value = mock_location
        
        coords = geo_service.geocode_address("Nice, France")
        
        assert coords is not None
        assert coords['latitude'] == 43.7
        assert coords['longitude'] == 7.26
        
        # Test avec adresse invalide
        mock_geocode.return_value = None
        coords = geo_service.geocode_address("Adresse inexistante xyz123")
        assert coords is None
    
    def test_calculate_distance(self, geo_service):
        """Test le calcul de distance."""
        # Nice vers Paris
        distance = geo_service.calculate_distance(
            43.7102, 7.2620,  # Nice
            48.8566, 2.3522   # Paris
        )
        
        # La distance devrait être environ 686 km
        assert 680 < distance < 690
        
        # Test distance nulle
        distance = geo_service.calculate_distance(43.7, 7.26, 43.7, 7.26)
        assert distance == 0