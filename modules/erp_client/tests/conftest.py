"""Configuration pytest pour tous les tests ERP.

Ce fichier configure pytest avec :
- Fixtures communes
- Configuration des tests
- Helpers partagés
"""

import pytest
import tempfile
import os
from typing import Generator

# Fixtures communes pour tous les tests


@pytest.fixture
def temp_database() -> Generator[str, None, None]:
    """Fixture pour créer une base de données temporaire."""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    yield temp_db.name
    
    # Cleanup
    if os.path.exists(temp_db.name):
        os.unlink(temp_db.name)


@pytest.fixture
def sample_client_data():
    """Fixture avec des données client de test."""
    return {
        'code_client': 'TEST001',
        'nom': 'Client Test',
        'type_client': 'producteur',
        'email': 'test@example.com',
        'telephone': '0123456789',
        'adresse': '123 Rue Test',
        'code_postal': '06000',
        'ville': 'Nice',
        'actif': True
    }


@pytest.fixture
def mock_services():
    """Fixture pour mocker les services."""
    class MockClientService:
        def get_all(self):
            return []
        
        def get_statistics(self):
            return {'total_clients': 0, 'clients_actifs': 0}
    
    class MockPricingService:
        def get_average_price(self):
            return 0.15
    
    class MockCapacityService:
        def get_total_capacity(self):
            return 1000.0
    
    return {
        'client': MockClientService(),
        'pricing': MockPricingService(),
        'capacity': MockCapacityService()
    }


# Configuration pytest
def pytest_configure(config):
    """Configuration globale pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )