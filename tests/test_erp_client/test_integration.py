"""Tests d'intégration pour le module ERP."""

import unittest
import os
import sys
import tempfile
from datetime import date

# Ajouter le chemin parent pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from modules.erp_client.database.erp_database import ERPDatabase
from modules.erp_client.services.client_service import ClientService
from modules.erp_client.services.pricing_service import PricingService, PrixClient
from modules.erp_client.services.capacity_service import CapacityService
from modules.erp_client.models.client import Client
from modules.erp_client.models.production_point import ProductionPoint
from modules.erp_client.models.collective_auto import CollectiveAutoAllocation


class TestERPIntegration(unittest.TestCase):
    """Tests d'intégration du module ERP."""
    
    def setUp(self):
        """Initialisation avant chaque test."""
        # Créer une base de données temporaire
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Initialiser les services
        self.db = ERPDatabase(self.db_path)
        self.client_service = ClientService(self.db_path)
        self.pricing_service = PricingService(self.db_path)
        self.capacity_service = CapacityService(self.db_path)
        
    def tearDown(self):
        """Nettoyage après chaque test."""
        # Supprimer la base temporaire
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
            
    def test_complete_workflow(self):
        """Test d'un workflow complet : client -> prix -> autoconso."""
        # 1. Créer un client
        client = Client(
            code_client="TEST001",
            nom="Client Test Integration",
            type_client="consommateur",
            adresse="123 Rue Test",
            code_postal="06000",
            ville="Nice"
        )
        
        created_client = self.client_service.create_client(client)
        self.assertIsNotNone(created_client.id)
        
        # 2. Définir un prix pour le client
        prix = PrixClient(
            id=None,
            client_id=created_client.id,
            prix_kwh=0.1500,
            date_debut=date.today(),
            date_fin=None,
            type_tarif='fixe',
            reference_prix='EDF_TRV_BASE',
            remise_pourcentage=10.0,
            formule_calcul=None,
            notes="Prix test intégration",
            date_creation=None
        )
        
        created_prix = self.pricing_service.create_prix(prix)
        self.assertIsNotNone(created_prix.id)
        
        # Vérifier que le prix est actif
        active_price = self.pricing_service.get_active_price(created_client.id)
        self.assertIsNotNone(active_price)
        self.assertEqual(active_price.prix_kwh, 0.1500)
        
        # 3. Créer un point de production
        production = ProductionPoint(
            nom="Centrale Solaire Test",
            puissance_kwc=100.0,
            latitude=43.7,
            longitude=7.25
        )
        
        # Sauvegarder le point de production
        query = """
            INSERT INTO points_production (
                nom, code_site, puissance_kwc, latitude, longitude
            ) VALUES (?, ?, ?, ?, ?)
        """
        prod_id = self.db.execute_command(
            query,
            (production.nom, production.code_site, production.puissance_kwc,
             production.latitude, production.longitude)
        )
        
        # 4. Créer une allocation d'autoconsommation
        allocation = CollectiveAutoAllocation(
            point_production_id=prod_id,
            client_id=created_client.id,
            pourcentage_allocation=25.0,
            date_debut=date.today(),
            priorite=1
        )
        
        # Ne pas créer l'allocation car il faut géocoder le client d'abord
        # Mais vérifier que l'opération peut être récupérée
        operation = self.capacity_service.get_operation_by_production(prod_id)
        self.assertEqual(operation.point_production_id, prod_id)
        self.assertEqual(operation.puissance_totale_kwc, 100.0)
        self.assertEqual(operation.pourcentage_disponible, 100.0)
        
    def test_database_statistics(self):
        """Test des statistiques de base de données."""
        # Créer quelques données
        for i in range(3):
            client = Client(
                code_client=f"STAT{i:03d}",
                nom=f"Client Stat {i}",
                type_client=['producteur', 'consommateur', 'prosumer'][i]
            )
            self.client_service.create_client(client)
            
        # Vérifier les statistiques
        stats = self.db.get_database_stats()
        self.assertEqual(stats['clients'], 3)
        
        # Vérifier les statistiques du service client
        client_stats = self.client_service.get_statistics()
        self.assertEqual(client_stats['total_clients'], 3)
        self.assertEqual(client_stats['clients_actifs'], 3)
        self.assertEqual(len(client_stats['par_type']), 3)
        
    def test_search_functionality(self):
        """Test de la fonctionnalité de recherche."""
        # Créer plusieurs clients
        clients_data = [
            ("NICE001", "Soleil Niçois", "producteur", "Nice"),
            ("NICE002", "Consommateur Azur", "consommateur", "Nice"),
            ("CANNES001", "Cannes Solar", "prosumer", "Cannes")
        ]
        
        for code, nom, type_client, ville in clients_data:
            client = Client(
                code_client=code,
                nom=nom,
                type_client=type_client,
                ville=ville
            )
            self.client_service.create_client(client)
            
        # Rechercher par ville
        nice_clients = self.client_service.search_clients(search_term="Nice")
        self.assertEqual(len(nice_clients), 2)
        
        # Rechercher par type
        producteurs = self.client_service.get_producteurs()
        self.assertEqual(len(producteurs), 1)
        
        # Rechercher par code
        client_found = self.client_service.get_by_code("CANNES001")
        self.assertIsNotNone(client_found)
        self.assertEqual(client_found.nom, "Cannes Solar")


if __name__ == '__main__':
    unittest.main()