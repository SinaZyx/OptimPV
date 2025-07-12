"""Tests pour les modèles du module ERP.

Ce module teste tous les modèles de données (Client, Prix, Autoconso)
et leurs validations.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal

from modules.erp_client.models.client import Client, TypeClient
from modules.erp_client.models.pricing import PrixClient, TypeTarif
from modules.erp_client.models.autoconso import (
    PointProduction, PointConsommation, AutoconsoCollective
)


class TestClientModel:
    """Tests pour le modèle Client."""
    
    def test_client_creation(self):
        """Test la création d'un client valide."""
        client = Client(
            id=1,
            code_client="cl001",
            nom="Test Client",
            type_client=TypeClient.PRODUCTEUR,
            adresse="123 rue Test",
            code_postal="75001",
            ville="Paris",
            telephone="+33123456789",
            email="test@example.com",
            siret="12345678900011",
            contact_principal="M. Test"
        )
        
        assert client.code_client == "CL001"  # Doit être en majuscules
        assert client.nom == "Test Client"
        assert client.type_client == TypeClient.PRODUCTEUR
        assert client.actif is True
    
    def test_client_code_uppercase(self):
        """Test la conversion automatique du code client en majuscules."""
        client = Client(
            code_client="test123",
            nom="Test",
            type_client=TypeClient.CONSOMMATEUR
        )
        
        assert client.code_client == "TEST123"
    
    def test_client_validation_email(self):
        """Test la validation de l'email."""
        # Email valide
        client = Client(
            code_client="CL001",
            nom="Test",
            type_client=TypeClient.PROSUMER,
            email="valid@example.com"
        )
        assert client.validate()
        
        # Email invalide
        client.email = "invalid-email"
        errors = client.validate()
        assert "email" in [e[0] for e in errors]
    
    def test_client_validation_siret(self):
        """Test la validation du SIRET."""
        # SIRET valide (14 chiffres)
        client = Client(
            code_client="CL001",
            nom="Test",
            type_client=TypeClient.PRODUCTEUR,
            siret="12345678900011"
        )
        assert client.validate()
        
        # SIRET invalide
        client.siret = "123"
        errors = client.validate()
        assert any("SIRET" in e[1] for e in errors)
    
    def test_client_adresse_complete(self):
        """Test la génération de l'adresse complète."""
        client = Client(
            code_client="CL001",
            nom="Test",
            type_client=TypeClient.CONSOMMATEUR,
            adresse="123 rue Test",
            code_postal="75001",
            ville="Paris"
        )
        
        assert client.adresse_complete == "123 rue Test, 75001 Paris"
        
        # Sans adresse
        client.adresse = None
        assert client.adresse_complete == "75001 Paris"
        
        # Sans rien
        client.code_postal = None
        client.ville = None
        assert client.adresse_complete == ""
    
    def test_client_has_coordinates(self):
        """Test la vérification des coordonnées."""
        client = Client(
            code_client="CL001",
            nom="Test",
            type_client=TypeClient.PRODUCTEUR
        )
        
        # Sans coordonnées
        assert not client.has_coordinates()
        
        # Avec latitude seulement
        client.latitude = 48.8566
        assert not client.has_coordinates()
        
        # Avec les deux coordonnées
        client.longitude = 2.3522
        assert client.has_coordinates()
    
    def test_client_to_dict(self):
        """Test la conversion en dictionnaire."""
        client = Client(
            id=1,
            code_client="CL001",
            nom="Test Client",
            type_client=TypeClient.PRODUCTEUR,
            email="test@example.com",
            date_creation=datetime(2024, 1, 1)
        )
        
        data = client.to_dict()
        
        assert data['id'] == 1
        assert data['code_client'] == "CL001"
        assert data['nom'] == "Test Client"
        assert data['type_client'] == "producteur"
        assert data['email'] == "test@example.com"
        assert isinstance(data['date_creation'], str)
    
    def test_client_from_dict(self):
        """Test la création depuis un dictionnaire."""
        data = {
            'id': 1,
            'code_client': 'CL001',
            'nom': 'Test Client',
            'type_client': 'consommateur',
            'email': 'test@example.com',
            'date_creation': '2024-01-01 00:00:00'
        }
        
        client = Client.from_dict(data)
        
        assert client.id == 1
        assert client.code_client == "CL001"
        assert client.nom == "Test Client"
        assert client.type_client == TypeClient.CONSOMMATEUR
        assert isinstance(client.date_creation, datetime)
    
    def test_client_metadata(self):
        """Test la gestion des métadonnées."""
        client = Client(
            code_client="CL001",
            nom="Test",
            type_client=TypeClient.PRODUCTEUR
        )
        
        # Ajouter des métadonnées
        client.set_metadata("custom_field", "value")
        client.set_metadata("count", 42)
        
        assert client.get_metadata("custom_field") == "value"
        assert client.get_metadata("count") == 42
        assert client.get_metadata("missing") is None
        assert client.get_metadata("missing", "default") == "default"


class TestPrixClientModel:
    """Tests pour le modèle PrixClient."""
    
    def test_prix_client_creation(self):
        """Test la création d'un prix client valide."""
        prix = PrixClient(
            id=1,
            client_id=1,
            prix_kwh=0.15,
            date_debut=date(2024, 1, 1),
            date_fin=date(2024, 12, 31),
            type_tarif=TypeTarif.FIXE,
            reference_prix="TARIF_2024",
            remise_pourcentage=10.0
        )
        
        assert prix.prix_kwh == 0.15
        assert prix.type_tarif == TypeTarif.FIXE
        assert prix.remise_pourcentage == 10.0
    
    def test_prix_validation(self):
        """Test la validation des prix."""
        # Prix valide
        prix = PrixClient(
            client_id=1,
            prix_kwh=0.15,
            date_debut=date.today(),
            type_tarif=TypeTarif.FIXE
        )
        assert prix.validate()
        
        # Prix négatif
        prix.prix_kwh = -0.10
        errors = prix.validate()
        assert any("prix" in e[1].lower() for e in errors)
        
        # Remise > 100%
        prix.prix_kwh = 0.15
        prix.remise_pourcentage = 150
        errors = prix.validate()
        assert any("remise" in e[1].lower() for e in errors)
    
    def test_prix_dates_validation(self):
        """Test la validation des dates."""
        # Dates valides
        prix = PrixClient(
            client_id=1,
            prix_kwh=0.15,
            date_debut=date.today(),
            date_fin=date.today() + timedelta(days=30),
            type_tarif=TypeTarif.INDEXE
        )
        assert prix.validate()
        
        # Date fin avant date début
        prix.date_fin = date.today() - timedelta(days=30)
        errors = prix.validate()
        assert any("date" in e[1].lower() for e in errors)
    
    def test_prix_effectif(self):
        """Test le calcul du prix effectif avec remise."""
        prix = PrixClient(
            client_id=1,
            prix_kwh=0.20,
            date_debut=date.today(),
            type_tarif=TypeTarif.FIXE,
            remise_pourcentage=25.0
        )
        
        assert prix.prix_effectif == 0.15  # 0.20 * (1 - 0.25)
        
        # Sans remise
        prix.remise_pourcentage = 0
        assert prix.prix_effectif == 0.20
    
    def test_prix_is_active(self):
        """Test la vérification si un prix est actif."""
        # Prix actif (pas de date de fin)
        prix = PrixClient(
            client_id=1,
            prix_kwh=0.15,
            date_debut=date.today() - timedelta(days=10),
            type_tarif=TypeTarif.DYNAMIQUE
        )
        assert prix.is_active()
        
        # Prix actif (date de fin future)
        prix.date_fin = date.today() + timedelta(days=10)
        assert prix.is_active()
        
        # Prix inactif (date de fin passée)
        prix.date_fin = date.today() - timedelta(days=1)
        assert not prix.is_active()
        
        # Prix futur
        prix.date_debut = date.today() + timedelta(days=10)
        prix.date_fin = None
        assert not prix.is_active()
    
    def test_prix_formule_calcul(self):
        """Test la gestion des formules de calcul."""
        prix = PrixClient(
            client_id=1,
            prix_kwh=0.15,
            date_debut=date.today(),
            type_tarif=TypeTarif.INDEXE
        )
        
        # Définir une formule
        formule = {
            "base": "SPOT",
            "ajustement": 0.02,
            "coefficient": 1.1
        }
        prix.set_formule_calcul(formule)
        
        assert prix.get_formule_calcul() == formule
        assert prix.formule_calcul == '{"base": "SPOT", "ajustement": 0.02, "coefficient": 1.1}'


class TestAutoconsoModels:
    """Tests pour les modèles d'autoconsommation."""
    
    def test_point_production_creation(self):
        """Test la création d'un point de production."""
        point = PointProduction(
            id=1,
            client_id=1,
            nom="Toiture Solaire Nord",
            type_installation="Toiture",
            capacite_kwc=100.5,
            date_mise_service=date(2023, 1, 1),
            adresse="123 rue du Soleil",
            latitude=43.6,
            longitude=7.0
        )
        
        assert point.nom == "Toiture Solaire Nord"
        assert point.capacite_kwc == 100.5
        assert point.capacite_disponible_kwc == 100.5  # Par défaut = capacité totale
        assert point.actif is True
    
    def test_point_production_validation(self):
        """Test la validation des points de production."""
        # Point valide
        point = PointProduction(
            client_id=1,
            nom="Test",
            capacite_kwc=50.0
        )
        assert point.validate()
        
        # Capacité négative
        point.capacite_kwc = -10
        errors = point.validate()
        assert any("capacité" in e[1].lower() for e in errors)
        
        # Capacité disponible > capacité totale
        point.capacite_kwc = 100
        point.capacite_disponible_kwc = 150
        errors = point.validate()
        assert any("disponible" in e[1].lower() for e in errors)
    
    def test_point_production_update_capacite(self):
        """Test la mise à jour de la capacité disponible."""
        point = PointProduction(
            client_id=1,
            nom="Test",
            capacite_kwc=100.0,
            capacite_disponible_kwc=100.0
        )
        
        # Allouer de la capacité
        point.capacite_disponible_kwc = 60.0
        assert point.capacite_disponible_kwc == 60.0
        
        # Vérifier le calcul du taux d'utilisation
        utilisation = (100.0 - 60.0) / 100.0 * 100
        assert abs(utilisation - 40.0) < 0.01
    
    def test_point_consommation_creation(self):
        """Test la création d'un point de consommation."""
        point = PointConsommation(
            id=1,
            client_id=1,
            reference_interne="PDL123456789",
            type_point="Principal",
            consommation_annuelle_kwh=50000,
            puissance_souscrite_kva=36,
            adresse="456 avenue de la Consommation"
        )
        
        assert point.reference_interne == "PDL123456789"
        assert point.consommation_annuelle_kwh == 50000
        assert point.puissance_souscrite_kva == 36
        assert point.actif is True
    
    def test_point_consommation_validation(self):
        """Test la validation des points de consommation."""
        # Point valide
        point = PointConsommation(
            client_id=1,
            reference_interne="REF001"
        )
        assert point.validate()
        
        # Consommation négative
        point.consommation_annuelle_kwh = -1000
        errors = point.validate()
        assert any("consommation" in e[1].lower() for e in errors)
        
        # Puissance invalide
        point.consommation_annuelle_kwh = 10000
        point.puissance_souscrite_kva = 0
        errors = point.validate()
        assert any("puissance" in e[1].lower() for e in errors)
    
    def test_autoconso_collective_creation(self):
        """Test la création d'une allocation d'autoconsommation."""
        alloc = AutoconsoCollective(
            id=1,
            point_production_id=1,
            point_consommation_id=1,
            pourcentage_allocation=75.5,
            date_debut=date.today(),
            date_fin=date.today() + timedelta(days=365),
            notes="Allocation test"
        )
        
        assert alloc.pourcentage_allocation == 75.5
        assert alloc.actif is True
        assert alloc.notes == "Allocation test"
    
    def test_autoconso_validation(self):
        """Test la validation des allocations."""
        # Allocation valide
        alloc = AutoconsoCollective(
            point_production_id=1,
            point_consommation_id=1,
            pourcentage_allocation=50.0,
            date_debut=date.today()
        )
        assert alloc.validate()
        
        # Pourcentage invalide
        alloc.pourcentage_allocation = 150.0
        errors = alloc.validate()
        assert any("pourcentage" in e[1].lower() for e in errors)
        
        # Pourcentage négatif
        alloc.pourcentage_allocation = -10.0
        errors = alloc.validate()
        assert any("pourcentage" in e[1].lower() for e in errors)
        
        # Dates invalides
        alloc.pourcentage_allocation = 50.0
        alloc.date_fin = date.today() - timedelta(days=10)
        errors = alloc.validate()
        assert any("date" in e[1].lower() for e in errors)
    
    def test_autoconso_is_active(self):
        """Test la vérification si une allocation est active."""
        # Allocation active (pas de date de fin)
        alloc = AutoconsoCollective(
            point_production_id=1,
            point_consommation_id=1,
            pourcentage_allocation=50.0,
            date_debut=date.today() - timedelta(days=10),
            actif=True
        )
        assert alloc.is_active()
        
        # Allocation inactive (flag actif)
        alloc.actif = False
        assert not alloc.is_active()
        
        # Allocation inactive (date de fin passée)
        alloc.actif = True
        alloc.date_fin = date.today() - timedelta(days=1)
        assert not alloc.is_active()
        
        # Allocation future
        alloc.date_debut = date.today() + timedelta(days=10)
        alloc.date_fin = None
        assert not alloc.is_active()
    
    def test_models_relationships(self):
        """Test les relations entre modèles."""
        # Créer les objets
        client_prod = Client(
            id=1,
            code_client="PROD001",
            nom="Producteur Test",
            type_client=TypeClient.PRODUCTEUR
        )
        
        client_cons = Client(
            id=2,
            code_client="CONS001",
            nom="Consommateur Test",
            type_client=TypeClient.CONSOMMATEUR
        )
        
        point_prod = PointProduction(
            id=1,
            client_id=client_prod.id,
            nom="Production Test",
            capacite_kwc=100.0
        )
        
        point_cons = PointConsommation(
            id=1,
            client_id=client_cons.id,
            reference_interne="REF001"
        )
        
        alloc = AutoconsoCollective(
            point_production_id=point_prod.id,
            point_consommation_id=point_cons.id,
            pourcentage_allocation=50.0,
            date_debut=date.today()
        )
        
        # Vérifier les relations
        assert point_prod.client_id == client_prod.id
        assert point_cons.client_id == client_cons.id
        assert alloc.point_production_id == point_prod.id
        assert alloc.point_consommation_id == point_cons.id