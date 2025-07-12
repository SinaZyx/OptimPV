"""
Tests pour les validateurs de clés de répartition
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Ajouter le chemin du module parent
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.repartition_keys.key_models import (
    RepartitionKey, RepartitionPeriod, RepartitionRule, 
    KeyType, PeriodType, RuleType
)
from modules.repartition_keys.key_validators import (
    RepartitionValidator, quick_validate_keys
)


class TestRepartitionValidator(unittest.TestCase):
    """Tests pour le validateur de clés de répartition"""
    
    def setUp(self):
        """Initialiser le validateur et les données de test"""
        self.validator = RepartitionValidator()
        
        # Clés de test valides (somme = 100%)
        self.valid_keys = [
            RepartitionKey("site_001", "Site A", 30.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 45.0, KeyType.STATIC),
            RepartitionKey("site_003", "Site C", 25.0, KeyType.STATIC)
        ]
        
        # Configuration des sites
        self.sites_config = {
            "site_001": {"nom_fichier": "Site A", "site_type": "Producteur"},
            "site_002": {"nom_fichier": "Site B", "site_type": "Producteur"},
            "site_003": {"nom_fichier": "Site C", "site_type": "Consommateur"},
            "site_004": {"nom_fichier": "Site D", "site_type": "Producteur"}
        }
    
    def test_validate_keys_sum_valid(self):
        """Test validation somme = 100%"""
        is_valid, message = self.validator.validate_keys_sum(self.valid_keys)
        
        self.assertTrue(is_valid)
        self.assertIn("100", message)
    
    def test_validate_keys_sum_invalid(self):
        """Test validation somme != 100%"""
        invalid_keys = [
            RepartitionKey("site_001", "Site A", 30.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 40.0, KeyType.STATIC)
        ]
        
        is_valid, message = self.validator.validate_keys_sum(invalid_keys)
        
        self.assertFalse(is_valid)
        self.assertIn("70", message)  # Somme actuelle
    
    def test_validate_keys_sum_empty(self):
        """Test validation avec liste vide"""
        is_valid, message = self.validator.validate_keys_sum([])
        
        self.assertFalse(is_valid)
        self.assertIn("Aucune clé", message)
    
    def test_validate_key_values(self):
        """Test validation des valeurs individuelles"""
        # Clés avec valeurs invalides
        invalid_value_keys = [
            RepartitionKey("site_001", "Site A", -5.0, KeyType.STATIC),  # Négatif
            RepartitionKey("site_002", "Site B", 0.0, KeyType.STATIC),   # Zéro
            RepartitionKey("site_003", "Site C", 105.0, KeyType.STATIC)  # > 100
        ]
        
        # Forcer la création malgré la validation du modèle
        for key in invalid_value_keys:
            key._value = key.value  # Contourner la validation pour le test
        
        is_valid, errors = self.validator.validate_key_values(invalid_value_keys)
        
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 3)
        self.assertTrue(any("négative" in error for error in errors))
        self.assertTrue(any("aucune allocation" in error for error in errors))
        self.assertTrue(any("> 100%" in error for error in errors))
    
    def test_validate_site_coverage(self):
        """Test validation de la couverture des sites"""
        # Clés qui ne couvrent pas tous les sites
        partial_keys = [
            RepartitionKey("site_001", "Site A", 50.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 50.0, KeyType.STATIC)
            # site_003 et site_004 manquants
        ]
        
        is_covered, missing = self.validator.validate_site_coverage(
            partial_keys, self.sites_config
        )
        
        self.assertFalse(is_covered)
        self.assertEqual(len(missing), 2)
        self.assertIn("Site C", missing)
        self.assertIn("Site D", missing)
    
    def test_validate_temporal_coherence(self):
        """Test validation de la cohérence temporelle"""
        # Périodes avec chevauchement
        periods = [
            RepartitionPeriod(
                "p1", PeriodType.MONTHLY, "Janvier",
                keys=self.valid_keys,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31)
            ),
            RepartitionPeriod(
                "p2", PeriodType.MONTHLY, "Février",
                keys=self.valid_keys,
                start_date=datetime(2024, 1, 15),  # Chevauchement !
                end_date=datetime(2024, 2, 28)
            )
        ]
        
        is_coherent, issues = self.validator.validate_temporal_coherence(periods)
        
        self.assertFalse(is_coherent)
        self.assertTrue(any("Chevauchement" in issue for issue in issues))
    
    def test_validate_temporal_gaps(self):
        """Test détection des trous temporels"""
        # Périodes avec trou
        periods = [
            RepartitionPeriod(
                "p1", PeriodType.MONTHLY, "Janvier",
                keys=self.valid_keys,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31)
            ),
            RepartitionPeriod(
                "p2", PeriodType.MONTHLY, "Mars",  # Février manquant
                keys=self.valid_keys,
                start_date=datetime(2024, 3, 1),
                end_date=datetime(2024, 3, 31)
            )
        ]
        
        is_coherent, issues = self.validator.validate_temporal_coherence(periods)
        
        self.assertFalse(is_coherent)
        self.assertTrue(any("Trou" in issue for issue in issues))
    
    def test_validate_consumption_allocation_ratio(self):
        """Test validation du ratio consommation/allocation"""
        # Données de consommation fictives
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        consumption_data = pd.DataFrame({
            'timestamp': dates,
            'site_001': np.random.uniform(10, 20, 100),  # Faible conso
            'site_002': np.random.uniform(80, 100, 100), # Forte conso
            'site_003': np.random.uniform(40, 60, 100)   # Conso moyenne
        }).set_index('timestamp')
        
        # Clés déséquilibrées par rapport à la consommation
        unbalanced_keys = [
            RepartitionKey("site_001", "Site A", 70.0, KeyType.STATIC),  # Trop pour sa conso
            RepartitionKey("site_002", "Site B", 20.0, KeyType.STATIC),  # Pas assez
            RepartitionKey("site_003", "Site C", 10.0, KeyType.STATIC)
        ]
        
        is_coherent, warnings = self.validator.validate_consumption_allocation_ratio(
            unbalanced_keys, consumption_data, threshold=2.0
        )
        
        self.assertFalse(is_coherent)
        self.assertTrue(len(warnings) > 0)
        self.assertTrue(any("très supérieure" in w for w in warnings))
        self.assertTrue(any("très inférieure" in w for w in warnings))
    
    def test_validate_complete(self):
        """Test validation complète"""
        result = self.validator.validate_complete(
            self.valid_keys,
            self.sites_config
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('is_valid', result)
        self.assertIn('errors', result)
        self.assertIn('warnings', result)
        self.assertIn('details', result)
        
        # Avec des clés valides couvrant seulement une partie des sites
        partial_result = self.validator.validate_complete(
            self.valid_keys[:2],  # Seulement 2 sites sur 4
            self.sites_config
        )
        
        self.assertFalse(partial_result['is_valid'])
        self.assertTrue(len(partial_result['errors']) > 0)


class TestQuickValidation(unittest.TestCase):
    """Tests pour la validation rapide"""
    
    def test_quick_validate_valid(self):
        """Test validation rapide avec clés valides"""
        keys = [
            RepartitionKey("site_001", "Site A", 25.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 25.0, KeyType.STATIC),
            RepartitionKey("site_003", "Site C", 25.0, KeyType.STATIC),
            RepartitionKey("site_004", "Site D", 25.0, KeyType.STATIC)
        ]
        
        is_valid, message = quick_validate_keys(keys)
        
        self.assertTrue(is_valid)
        self.assertIn("valides", message.lower())
    
    def test_quick_validate_invalid_sum(self):
        """Test validation rapide avec somme invalide"""
        keys = [
            RepartitionKey("site_001", "Site A", 30.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 30.0, KeyType.STATIC)
        ]
        
        is_valid, message = quick_validate_keys(keys)
        
        self.assertFalse(is_valid)
        self.assertIn("60", message)  # Somme actuelle


def run_tests():
    """Exécuter tous les tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    print("=== Tests des validateurs de répartition ===\n")
    run_tests()