"""
Tests pour les modèles de données des clés de répartition
"""

import unittest
from datetime import datetime
import sys
import os

# Ajouter le chemin du module parent
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.repartition_keys.key_models import (
    RepartitionKey, RepartitionPeriod, RepartitionRule, RepartitionTemplate,
    KeyType, PeriodType, RuleType, RepartitionCondition
)


class TestRepartitionKey(unittest.TestCase):
    """Tests pour le modèle RepartitionKey"""
    
    def test_creation_key_valide(self):
        """Test de création d'une clé valide"""
        key = RepartitionKey(
            site_id="site_001",
            participant_name="Site A",
            value=25.5,
            key_type=KeyType.STATIC
        )
        
        self.assertEqual(key.site_id, "site_001")
        self.assertEqual(key.participant_name, "Site A")
        self.assertEqual(key.value, 25.5)
        self.assertEqual(key.key_type, KeyType.STATIC)
    
    def test_validation_valeur(self):
        """Test de validation de la valeur (0-100)"""
        # Valeur négative
        with self.assertRaises(ValueError):
            RepartitionKey(
                site_id="site_001",
                participant_name="Site A",
                value=-5,
                key_type=KeyType.STATIC
            )
        
        # Valeur > 100
        with self.assertRaises(ValueError):
            RepartitionKey(
                site_id="site_001",
                participant_name="Site A",
                value=101,
                key_type=KeyType.STATIC
            )
    
    def test_serialisation(self):
        """Test de sérialisation/désérialisation"""
        key = RepartitionKey(
            site_id="site_001",
            participant_name="Site A",
            value=50.0,
            key_type=KeyType.STATIC,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 12, 31)
        )
        
        # Convertir en dict
        key_dict = key.to_dict()
        self.assertIsInstance(key_dict, dict)
        self.assertEqual(key_dict['site_id'], "site_001")
        self.assertEqual(key_dict['value'], 50.0)
        
        # Recréer depuis dict
        key2 = RepartitionKey.from_dict(key_dict)
        self.assertEqual(key2.site_id, key.site_id)
        self.assertEqual(key2.value, key.value)
        self.assertEqual(key2.period_start, key.period_start)


class TestRepartitionPeriod(unittest.TestCase):
    """Tests pour le modèle RepartitionPeriod"""
    
    def setUp(self):
        """Préparer les données de test"""
        self.keys = [
            RepartitionKey("site_001", "Site A", 30.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 40.0, KeyType.STATIC),
            RepartitionKey("site_003", "Site C", 30.0, KeyType.STATIC)
        ]
    
    def test_validation_totale(self):
        """Test de validation de la somme = 100%"""
        period = RepartitionPeriod(
            period_id="period_001",
            period_type=PeriodType.MONTHLY,
            period_name="Janvier 2024",
            keys=self.keys
        )
        
        self.assertTrue(period.total_validation)
        self.assertEqual(period.validation_details['total'], 100.0)
        self.assertTrue(period.validation_details['is_valid'])
    
    def test_validation_echoue(self):
        """Test quand la somme != 100%"""
        keys_invalides = [
            RepartitionKey("site_001", "Site A", 30.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 40.0, KeyType.STATIC)
        ]
        
        period = RepartitionPeriod(
            period_id="period_002",
            period_type=PeriodType.MONTHLY,
            period_name="Février 2024",
            keys=keys_invalides
        )
        
        self.assertFalse(period.total_validation)
        self.assertEqual(period.validation_details['total'], 70.0)
        self.assertFalse(period.validation_details['is_valid'])
    
    def test_get_key_for_site(self):
        """Test de récupération d'une clé par site"""
        period = RepartitionPeriod(
            period_id="period_001",
            period_type=PeriodType.MONTHLY,
            period_name="Janvier 2024",
            keys=self.keys
        )
        
        key = period.get_key_for_site("site_002")
        self.assertIsNotNone(key)
        self.assertEqual(key.participant_name, "Site B")
        self.assertEqual(key.value, 40.0)
        
        # Site inexistant
        key_none = period.get_key_for_site("site_999")
        self.assertIsNone(key_none)


class TestRepartitionRule(unittest.TestCase):
    """Tests pour le modèle RepartitionRule"""
    
    def test_creation_rule(self):
        """Test de création d'une règle"""
        conditions = [
            RepartitionCondition("hour", ">=", 8),
            RepartitionCondition("hour", "<=", 18)
        ]
        
        rule = RepartitionRule(
            rule_id="rule_001",
            rule_name="Heures de bureau",
            rule_type=RuleType.TIME_BASED,
            priority=100,
            conditions=conditions,
            target_sites=["site_001", "site_002"],
            enabled=True
        )
        
        self.assertEqual(rule.rule_id, "rule_001")
        self.assertEqual(rule.priority, 100)
        self.assertEqual(len(rule.conditions), 2)
        self.assertTrue(rule.enabled)
    
    def test_rule_application(self):
        """Test d'application d'une règle selon le contexte"""
        condition = RepartitionCondition("production", ">", 100)
        
        rule = RepartitionRule(
            rule_id="rule_002",
            rule_name="Production élevée",
            rule_type=RuleType.PRODUCTION_BASED,
            conditions=[condition]
        )
        
        # Contexte où la règle s'applique
        context1 = {"production": 150}
        self.assertTrue(rule.applies_to_context(context1))
        
        # Contexte où la règle ne s'applique pas
        context2 = {"production": 50}
        self.assertFalse(rule.applies_to_context(context2))
        
        # Règle désactivée
        rule.enabled = False
        self.assertFalse(rule.applies_to_context(context1))


class TestRepartitionCondition(unittest.TestCase):
    """Tests pour les conditions de règles"""
    
    def test_operateurs(self):
        """Test de tous les opérateurs de condition"""
        test_cases = [
            (RepartitionCondition("value", "<", 100), {"value": 50}, True),
            (RepartitionCondition("value", "<", 100), {"value": 150}, False),
            (RepartitionCondition("value", "<=", 100), {"value": 100}, True),
            (RepartitionCondition("value", ">", 100), {"value": 150}, True),
            (RepartitionCondition("value", ">=", 100), {"value": 100}, True),
            (RepartitionCondition("value", "==", 100), {"value": 100}, True),
            (RepartitionCondition("value", "!=", 100), {"value": 50}, True),
            (RepartitionCondition("value", "in", [1, 2, 3]), {"value": 2}, True),
            (RepartitionCondition("value", "not_in", [1, 2, 3]), {"value": 4}, True),
        ]
        
        for condition, context, expected in test_cases:
            result = condition.evaluate(context)
            self.assertEqual(result, expected, 
                f"Échec pour {condition.operator} avec {context}")


class TestRepartitionTemplate(unittest.TestCase):
    """Tests pour les templates de répartition"""
    
    def test_template_equitable(self):
        """Test du template de répartition équitable"""
        template = RepartitionTemplate(
            template_id="equitable",
            template_name="Répartition Équitable",
            description="Répartition équitable entre tous",
            template_type="equitable"
        )
        
        sites_config = {
            "site_001": {"nom_fichier": "Site A"},
            "site_002": {"nom_fichier": "Site B"},
            "site_003": {"nom_fichier": "Site C"},
            "site_004": {"nom_fichier": "Site D"}
        }
        
        keys = template.apply_to_sites(sites_config)
        
        self.assertEqual(len(keys), 4)
        for key in keys:
            self.assertEqual(key.value, 25.0)  # 100/4 = 25
            self.assertEqual(key.key_type, KeyType.STATIC)


def run_tests():
    """Exécuter tous les tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    print("=== Tests des modèles de répartition ===\n")
    run_tests()