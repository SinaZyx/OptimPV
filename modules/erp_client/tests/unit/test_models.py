"""Tests unitaires pour les modèles de données.

Tests pour :
- Client (validation, conversion, propriétés)
- TypeClient enum
- Autres modèles (pricing, autoconso, etc.)
"""

import pytest
from datetime import datetime
from modules.erp_client.models.client import Client, TypeClient


class TestClient:
    """Tests pour le modèle Client."""
    
    def test_client_creation_valid(self):
        """Test création d'un client valide."""
        client = Client(
            code_client="TEST001",
            nom="Test Client",
            type_client=TypeClient.PRODUCTEUR
        )
        
        assert client.code_client == "TEST001"
        assert client.nom == "Test Client"
        assert client.type_client == TypeClient.PRODUCTEUR
        assert client.actif is True
        assert client.date_creation is not None
    
    def test_client_creation_with_string_type(self):
        """Test création avec type string (auto-conversion)."""
        client = Client(
            code_client="TEST002",
            nom="Test Client 2",
            type_client="consommateur"
        )
        
        assert client.type_client == TypeClient.CONSOMMATEUR
    
    def test_client_validation_empty_code(self):
        """Test validation avec code client vide."""
        with pytest.raises(ValueError, match="Le code client ne peut pas être vide"):
            Client(
                code_client="",
                nom="Test Client",
                type_client=TypeClient.PRODUCTEUR
            )
    
    def test_client_validation_invalid_type(self):
        """Test validation avec type invalide."""
        with pytest.raises(ValueError, match="Type client invalide"):
            Client(
                code_client="TEST003",
                nom="Test Client",
                type_client="invalid_type"
            )
    
    def test_client_properties(self):
        """Test des propriétés calculées."""
        # Test producteur
        client_prod = Client(
            code_client="PROD001",
            nom="Producteur Test",
            type_client=TypeClient.PRODUCTEUR
        )
        assert client_prod.is_producteur is True
        assert client_prod.is_consommateur is False
        
        # Test prosumer
        client_prosumer = Client(
            code_client="PROS001",
            nom="Prosumer Test",
            type_client=TypeClient.PROSUMER
        )
        assert client_prosumer.is_producteur is True
        assert client_prosumer.is_consommateur is True
    
    def test_client_coordinates(self):
        """Test gestion des coordonnées GPS."""
        client = Client(
            code_client="GEO001",
            nom="Client Géolocalisé",
            type_client=TypeClient.CONSOMMATEUR,
            latitude=43.7102,
            longitude=7.2620
        )
        
        assert client.has_coordinates is True
        
        client_no_coords = Client(
            code_client="NOGEO001",
            nom="Client Sans Géoloc",
            type_client=TypeClient.CONSOMMATEUR
        )
        
        assert client_no_coords.has_coordinates is False
    
    def test_client_to_dict_from_dict(self):
        """Test conversion dict ↔ objet."""
        original = Client(
            code_client="CONV001",
            nom="Client Conversion",
            type_client=TypeClient.PROSUMER,
            email="test@example.com",
            latitude=43.0,
            longitude=7.0
        )
        
        # Conversion vers dict
        data = original.to_dict()
        assert data['code_client'] == "CONV001"
        assert data['type_client'] == "prosumer"  # Enum converti en string
        
        # Conversion depuis dict
        restored = Client.from_dict(data)
        assert restored.code_client == original.code_client
        assert restored.type_client == original.type_client
        assert restored.email == original.email
    
    def test_client_validation_method(self):
        """Test méthode validate()."""
        # Client valide
        client = Client(
            code_client="VALID001",
            nom="Client Valide",
            type_client=TypeClient.PRODUCTEUR,
            email="valid@example.com"
        )
        
        errors = client.validate()
        assert len(errors) == 0
        
        # Client avec erreurs
        client_invalid = Client(
            code_client="INV",
            nom="",
            type_client=TypeClient.PRODUCTEUR,
            email="invalid-email",
            latitude=100  # Latitude invalide
        )
        
        errors = client_invalid.validate()
        assert len(errors) > 0
        assert any("nom" in error.lower() for error in errors)
        assert any("email" in error.lower() for error in errors)
        assert any("latitude" in error.lower() for error in errors)


class TestTypeClient:
    """Tests pour l'enum TypeClient."""
    
    def test_enum_values(self):
        """Test des valeurs de l'enum."""
        assert TypeClient.PRODUCTEUR.value == "producteur"
        assert TypeClient.CONSOMMATEUR.value == "consommateur"
        assert TypeClient.PROSUMER.value == "prosumer"
    
    def test_enum_creation_from_string(self):
        """Test création depuis string."""
        assert TypeClient("producteur") == TypeClient.PRODUCTEUR
        assert TypeClient("consommateur") == TypeClient.CONSOMMATEUR
        assert TypeClient("prosumer") == TypeClient.PROSUMER
    
    def test_enum_invalid_value(self):
        """Test avec valeur invalide."""
        with pytest.raises(ValueError):
            TypeClient("invalid")


if __name__ == "__main__":
    # Tests manuels sans pytest
    print("🧪 Tests unitaires des modèles...")
    
    try:
        # Test création client
        client = Client(
            code_client="TEST001",
            nom="Test Client",
            type_client="producteur"
        )
        print("✅ Création client OK")
        
        # Test propriétés
        assert client.is_producteur
        print("✅ Propriétés client OK")
        
        # Test conversion
        data = client.to_dict()
        restored = Client.from_dict(data)
        assert restored.nom == client.nom
        print("✅ Conversion dict OK")
        
        print("🎉 Tous les tests sont passés !")
        
    except Exception as e:
        print(f"❌ Erreur dans les tests : {e}")
        import traceback
        traceback.print_exc()