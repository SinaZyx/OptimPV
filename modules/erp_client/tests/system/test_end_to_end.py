"""Tests end-to-end pour le module ERP.

Tests complets simulant l'utilisation réelle :
- Scénarios utilisateur complets
- Tests de performance
- Tests de régression
"""

import pytest
import time
from datetime import datetime
from modules.erp_client.models.client import Client, TypeClient


class TestCompleteUserScenarios:
    """Tests de scénarios utilisateur complets."""
    
    def test_complete_client_lifecycle(self):
        """Test du cycle de vie complet d'un client."""
        print("🎬 Test cycle de vie client complet...")
        
        try:
            # Étape 1: Création d'un client
            client = Client(
                code_client="E2E001",
                nom="Client End-to-End",
                type_client=TypeClient.PROSUMER,
                email="e2e@example.com",
                telephone="0123456789",
                adresse="123 Rue Test",
                code_postal="06000",
                ville="Nice"
            )
            
            print("✅ 1. Création client réussie")
            
            # Étape 2: Validation
            errors = client.validate()
            assert len(errors) == 0, f"Erreurs de validation: {errors}"
            print("✅ 2. Validation client réussie")
            
            # Étape 3: Conversion pour stockage
            client_dict = client.to_dict()
            assert 'code_client' in client_dict
            print("✅ 3. Conversion pour stockage réussie")
            
            # Étape 4: Restauration depuis stockage
            restored_client = Client.from_dict(client_dict)
            assert restored_client.nom == client.nom
            assert restored_client.type_client == client.type_client
            print("✅ 4. Restauration depuis stockage réussie")
            
            # Étape 5: Modification
            restored_client.notes = "Client modifié lors du test E2E"
            restored_client.date_modification = datetime.now()
            print("✅ 5. Modification client réussie")
            
            print("🎉 Cycle de vie client complet OK!")
            
        except Exception as e:
            print(f"❌ Erreur dans le cycle de vie client: {e}")
            raise
    
    def test_multiple_clients_creation(self):
        """Test création de plusieurs clients (performance)."""
        print("⚡ Test création multiple clients...")
        
        start_time = time.time()
        clients = []
        
        try:
            for i in range(100):
                client = Client(
                    code_client=f"PERF{i:03d}",
                    nom=f"Client Performance {i}",
                    type_client=TypeClient.PRODUCTEUR if i % 2 == 0 else TypeClient.CONSOMMATEUR
                )
                clients.append(client)
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert len(clients) == 100
            assert duration < 1.0, f"Création trop lente: {duration:.2f}s"
            
            print(f"✅ Création de 100 clients en {duration:.3f}s")
            
        except Exception as e:
            print(f"❌ Erreur test performance: {e}")
            raise
    
    def test_client_data_integrity(self):
        """Test intégrité des données client."""
        print("🔒 Test intégrité des données...")
        
        try:
            # Données avec caractères spéciaux
            client = Client(
                code_client="INTEG001",
                nom="Client Spécial éàù€@#",
                type_client=TypeClient.PROSUMER,
                email="special.chars+test@domain-name.com",
                notes="Notes avec caractères spéciaux: éàù€$£¥"
            )
            
            # Test conversion et restauration
            data = client.to_dict()
            restored = Client.from_dict(data)
            
            assert restored.nom == client.nom
            assert restored.email == client.email
            assert restored.notes == client.notes
            
            print("✅ Intégrité des caractères spéciaux OK")
            
            # Test avec valeurs limites
            client_limits = Client(
                code_client="L" * 50,  # Longueur max
                nom="N" * 200,         # Longueur max
                type_client=TypeClient.PRODUCTEUR,
                latitude=90.0,         # Limite max
                longitude=-180.0       # Limite min
            )
            
            errors = client_limits.validate()
            # Devrait passer sans erreur pour les valeurs limites valides
            assert len([e for e in errors if "latitude" in e or "longitude" in e]) == 0
            
            print("✅ Intégrité des valeurs limites OK")
            
        except Exception as e:
            print(f"❌ Erreur test intégrité: {e}")
            raise


class TestSystemPerformance:
    """Tests de performance système."""
    
    def test_model_creation_performance(self):
        """Test performance création modèles."""
        print("📊 Test performance modèles...")
        
        start_time = time.time()
        
        for i in range(1000):
            client = Client(
                code_client=f"PERF{i:04d}",
                nom=f"Performance Client {i}",
                type_client=TypeClient.PRODUCTEUR
            )
            # Test propriétés calculées
            _ = client.is_producteur
            _ = client.nom_complet
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ 1000 créations de modèles en {duration:.3f}s")
        assert duration < 2.0, f"Performance insuffisante: {duration:.2f}s"
    
    def test_validation_performance(self):
        """Test performance validation."""
        print("🔍 Test performance validation...")
        
        client = Client(
            code_client="VALID001",
            nom="Client Validation Performance",
            type_client=TypeClient.PROSUMER,
            email="valid@test.com",
            latitude=43.7,
            longitude=7.2
        )
        
        start_time = time.time()
        
        for i in range(1000):
            errors = client.validate()
            assert len(errors) == 0
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ 1000 validations en {duration:.3f}s")
        assert duration < 1.0, f"Validation trop lente: {duration:.2f}s"


class TestRegressionTests:
    """Tests de régression pour éviter les régressions."""
    
    def test_type_client_enum_regression(self):
        """Test régression pour l'enum TypeClient."""
        print("🔄 Test régression TypeClient...")
        
        try:
            # Test toutes les valeurs d'enum
            assert TypeClient.PRODUCTEUR.value == "producteur"
            assert TypeClient.CONSOMMATEUR.value == "consommateur"
            assert TypeClient.PROSUMER.value == "prosumer"
            
            # Test conversion depuis string
            assert TypeClient("producteur") == TypeClient.PRODUCTEUR
            assert TypeClient("consommateur") == TypeClient.CONSOMMATEUR
            assert TypeClient("prosumer") == TypeClient.PROSUMER
            
            print("✅ Régression TypeClient OK")
            
        except Exception as e:
            print(f"❌ Régression détectée dans TypeClient: {e}")
            raise
    
    def test_client_properties_regression(self):
        """Test régression pour les propriétés calculées."""
        print("📐 Test régression propriétés client...")
        
        try:
            # Test producteur
            prod = Client("PROD", "Producteur", TypeClient.PRODUCTEUR)
            assert prod.is_producteur is True
            assert prod.is_consommateur is False
            
            # Test consommateur
            cons = Client("CONS", "Consommateur", TypeClient.CONSOMMATEUR)
            assert cons.is_producteur is False
            assert cons.is_consommateur is True
            
            # Test prosumer
            pros = Client("PROS", "Prosumer", TypeClient.PROSUMER)
            assert pros.is_producteur is True
            assert pros.is_consommateur is True
            
            print("✅ Régression propriétés client OK")
            
        except Exception as e:
            print(f"❌ Régression détectée dans propriétés: {e}")
            raise


if __name__ == "__main__":
    # Tests manuels sans pytest
    print("🧪 Tests système end-to-end...")
    
    try:
        # Tests scénarios complets
        test_scenarios = TestCompleteUserScenarios()
        test_scenarios.test_complete_client_lifecycle()
        test_scenarios.test_multiple_clients_creation()
        test_scenarios.test_client_data_integrity()
        
        # Tests performance
        test_perf = TestSystemPerformance()
        test_perf.test_model_creation_performance()
        test_perf.test_validation_performance()
        
        # Tests régression
        test_regression = TestRegressionTests()
        test_regression.test_type_client_enum_regression()
        test_regression.test_client_properties_regression()
        
        print("🎉 Tous les tests système sont passés !")
        
    except Exception as e:
        print(f"❌ Erreur dans les tests système : {e}")
        import traceback
        traceback.print_exc()