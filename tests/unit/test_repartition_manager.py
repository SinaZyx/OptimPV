"""
Tests pour le gestionnaire principal des clés de répartition
"""

import unittest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from datetime import datetime, timedelta
import sys

# Ajouter le chemin du module parent
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.repartition_keys.key_manager import RepartitionKeyManager
from modules.repartition_keys.key_models import (
    RepartitionKey, RepartitionPeriod, RepartitionRule,
    KeyType, PeriodType, RuleType
)


class TestRepartitionKeyManager(unittest.TestCase):
    """Tests pour la classe RepartitionKeyManager"""
    
    def setUp(self):
        """Préparer le gestionnaire et les données de test"""
        # Configuration des sites
        self.sites_config = {
            "site_001": {
                "nom_fichier": "Site A",
                "site_type": "Producteur",
                "puissance_kwc": 100,
                "consommation_moyenne": 500
            },
            "site_002": {
                "nom_fichier": "Site B",
                "site_type": "Producteur",
                "puissance_kwc": 150,
                "consommation_moyenne": 800
            },
            "site_003": {
                "nom_fichier": "Site C",
                "site_type": "Consommateur",
                "puissance_kwc": 0,
                "consommation_moyenne": 1200
            }
        }
        
        # Créer le gestionnaire
        self.manager = RepartitionKeyManager(self.sites_config)
        
        # Données de production et consommation
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        self.production_data = pd.Series(
            np.random.uniform(100, 300, len(dates)),
            index=dates,
            name='Production'
        )
        
        self.consumption_data = pd.DataFrame({
            'site_001': np.random.uniform(50, 150, len(dates)),
            'site_002': np.random.uniform(100, 250, len(dates)),
            'site_003': np.random.uniform(200, 400, len(dates))
        }, index=dates)
    
    def test_initialization(self):
        """Test de l'initialisation du gestionnaire"""
        self.assertIsInstance(self.manager, RepartitionKeyManager)
        self.assertEqual(len(self.manager.sites_config), 3)
        self.assertIn('mode', self.manager.config)
        self.assertEqual(self.manager.config['mode'], 'static')
    
    def test_set_static_keys(self):
        """Test de la définition des clés statiques"""
        keys = [
            RepartitionKey("site_001", "Site A", 30.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 45.0, KeyType.STATIC),
            RepartitionKey("site_003", "Site C", 25.0, KeyType.STATIC)
        ]
        
        success = self.manager.set_keys(keys)
        self.assertTrue(success)
        
        # Vérifier que les clés sont stockées
        stored_keys = self.manager.get_current_keys()
        self.assertEqual(len(stored_keys), 3)
        self.assertEqual(stored_keys[0].value, 30.0)
    
    def test_set_invalid_keys(self):
        """Test avec des clés invalides (somme != 100%)"""
        invalid_keys = [
            RepartitionKey("site_001", "Site A", 30.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 40.0, KeyType.STATIC)
            # Somme = 70%
        ]
        
        success = self.manager.set_keys(invalid_keys)
        self.assertFalse(success)
    
    def test_apply_keys_to_production(self):
        """Test de l'application des clés à la production"""
        # Définir des clés
        keys = [
            RepartitionKey("site_001", "Site A", 25.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 50.0, KeyType.STATIC),
            RepartitionKey("site_003", "Site C", 25.0, KeyType.STATIC)
        ]
        self.manager.set_keys(keys)
        
        # Appliquer à la production
        result = self.manager.apply_keys_to_production(self.production_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn('Production_Site A', result.columns)
        self.assertIn('Production_Site B', result.columns)
        self.assertIn('Production_Site C', result.columns)
        
        # Vérifier les allocations
        total_prod = self.production_data.sum()
        self.assertAlmostEqual(
            result['Production_Site A'].sum(),
            total_prod * 0.25,
            places=2
        )
        self.assertAlmostEqual(
            result['Production_Site B'].sum(),
            total_prod * 0.50,
            places=2
        )
    
    def test_validate_keys_coherence(self):
        """Test de la validation de cohérence"""
        # Clés valides
        valid_keys = [
            RepartitionKey("site_001", "Site A", 33.33, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 33.33, KeyType.STATIC),
            RepartitionKey("site_003", "Site C", 33.34, KeyType.STATIC)
        ]
        self.manager.set_keys(valid_keys)
        
        is_valid, message = self.manager.validate_keys_coherence()
        self.assertTrue(is_valid)
        self.assertIn("valides", message.lower())
    
    def test_apply_template_equitable(self):
        """Test de l'application d'un template équitable"""
        success = self.manager.apply_template('equitable')
        self.assertTrue(success)
        
        keys = self.manager.get_current_keys()
        self.assertEqual(len(keys), 3)
        
        # Vérifier que chaque clé a ~33.33%
        for key in keys:
            self.assertAlmostEqual(key.value, 100/3, places=1)
    
    def test_apply_template_consumption_based(self):
        """Test du template basé sur la consommation"""
        success = self.manager.apply_template(
            'consumption_based',
            consumption_data=self.consumption_data
        )
        self.assertTrue(success)
        
        keys = self.manager.get_current_keys()
        
        # Le site avec la plus grande consommation devrait avoir 
        # la plus grande allocation
        keys_dict = {k.site_id: k.value for k in keys}
        consumption_totals = self.consumption_data.sum()
        max_consumer = consumption_totals.idxmax()
        
        # Vérifier que le plus gros consommateur a la plus grande part
        max_allocation = max(k.value for k in keys)
        self.assertEqual(keys_dict[max_consumer], max_allocation)
    
    def test_export_import_configuration(self):
        """Test export/import de configuration"""
        # Définir des clés
        keys = [
            RepartitionKey("site_001", "Site A", 40.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 35.0, KeyType.STATIC),
            RepartitionKey("site_003", "Site C", 25.0, KeyType.STATIC)
        ]
        self.manager.set_keys(keys)
        
        # Exporter
        export_dict = self.manager.export_to_dict()
        
        self.assertIn('mode', export_dict)
        self.assertIn('keys', export_dict)
        self.assertIn('created_at', export_dict)
        self.assertEqual(len(export_dict['keys']), 3)
        
        # Créer un nouveau gestionnaire et importer
        new_manager = RepartitionKeyManager(self.sites_config)
        success = new_manager.import_from_dict(export_dict)
        
        self.assertTrue(success)
        new_keys = new_manager.get_current_keys()
        self.assertEqual(len(new_keys), 3)
        self.assertEqual(new_keys[0].value, 40.0)
    
    def test_save_load_file(self):
        """Test de sauvegarde/chargement depuis fichier"""
        # Définir des clés
        keys = [
            RepartitionKey("site_001", "Site A", 20.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 50.0, KeyType.STATIC),
            RepartitionKey("site_003", "Site C", 30.0, KeyType.STATIC)
        ]
        self.manager.set_keys(keys)
        
        # Sauvegarder dans un fichier temporaire
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
            self.manager.save_to_file(temp_file)
        
        try:
            # Vérifier que le fichier existe
            self.assertTrue(os.path.exists(temp_file))
            
            # Charger dans un nouveau gestionnaire
            new_manager = RepartitionKeyManager(self.sites_config)
            success = new_manager.load_from_file(temp_file)
            
            self.assertTrue(success)
            new_keys = new_manager.get_current_keys()
            self.assertEqual(len(new_keys), 3)
            self.assertEqual(new_keys[1].value, 50.0)
        
        finally:
            # Nettoyer
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_history_management(self):
        """Test de la gestion de l'historique"""
        # Ajouter plusieurs configurations
        configs = [
            [
                RepartitionKey("site_001", "Site A", 30.0, KeyType.STATIC),
                RepartitionKey("site_002", "Site B", 40.0, KeyType.STATIC),
                RepartitionKey("site_003", "Site C", 30.0, KeyType.STATIC)
            ],
            [
                RepartitionKey("site_001", "Site A", 25.0, KeyType.STATIC),
                RepartitionKey("site_002", "Site B", 50.0, KeyType.STATIC),
                RepartitionKey("site_003", "Site C", 25.0, KeyType.STATIC)
            ],
            [
                RepartitionKey("site_001", "Site A", 33.33, KeyType.STATIC),
                RepartitionKey("site_002", "Site B", 33.33, KeyType.STATIC),
                RepartitionKey("site_003", "Site C", 33.34, KeyType.STATIC)
            ]
        ]
        
        for config in configs:
            self.manager.set_keys(config)
        
        # Vérifier l'historique
        history = self.manager.get_history()
        self.assertGreaterEqual(len(history), 3)
        
        # Restaurer depuis l'historique
        success = self.manager.restore_from_history(0)
        self.assertTrue(success)
        
        restored_keys = self.manager.get_current_keys()
        self.assertEqual(restored_keys[0].value, 30.0)
    
    def test_update_sites_config(self):
        """Test de mise à jour de la configuration des sites"""
        # Configuration initiale avec 3 sites
        initial_keys = [
            RepartitionKey("site_001", "Site A", 33.33, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 33.33, KeyType.STATIC),
            RepartitionKey("site_003", "Site C", 33.34, KeyType.STATIC)
        ]
        self.manager.set_keys(initial_keys)
        
        # Nouvelle configuration avec un site ajouté et un supprimé
        new_sites_config = {
            "site_001": self.sites_config["site_001"],
            "site_002": self.sites_config["site_002"],
            # site_003 supprimé
            "site_004": {
                "nom_fichier": "Site D",
                "site_type": "Producteur",
                "puissance_kwc": 80
            }
        }
        
        self.manager.update_sites_config(new_sites_config)
        
        # Vérifier les ajustements
        keys = self.manager.get_current_keys()
        site_ids = [k.site_id for k in keys]
        
        self.assertIn("site_001", site_ids)
        self.assertIn("site_002", site_ids)
        self.assertNotIn("site_003", site_ids)
        self.assertIn("site_004", site_ids)
        
        # La somme devrait toujours être 100%
        total = sum(k.value for k in keys)
        self.assertAlmostEqual(total, 100.0, places=2)
    
    def test_temporal_mode_setup(self):
        """Test du mode temporel"""
        # Passer en mode temporel
        self.manager.config['mode'] = 'temporal'
        
        # Créer des périodes mensuelles
        periods = []
        for month in range(1, 4):  # Jan, Fév, Mars
            period = RepartitionPeriod(
                period_id=f"month_{month}",
                period_type=PeriodType.MONTHLY,
                period_name=f"Mois {month}",
                keys=[
                    RepartitionKey("site_001", "Site A", 30.0 + month*5, KeyType.STATIC),
                    RepartitionKey("site_002", "Site B", 40.0 - month*5, KeyType.STATIC),
                    RepartitionKey("site_003", "Site C", 30.0, KeyType.STATIC)
                ],
                start_date=datetime(2024, month, 1),
                end_date=datetime(2024, month, 28)
            )
            periods.append(period)
        
        # Définir les périodes
        self.manager.set_temporal_periods(periods)
        
        # Vérifier
        stored_periods = self.manager.get_temporal_periods()
        self.assertEqual(len(stored_periods), 3)
        
        # Vérifier les clés pour chaque période
        jan_keys = stored_periods[0].keys
        self.assertEqual(jan_keys[0].value, 35.0)  # 30 + 1*5
        
        mar_keys = stored_periods[2].keys
        self.assertEqual(mar_keys[0].value, 45.0)  # 30 + 3*5
    
    def test_calculate_impact_metrics(self):
        """Test du calcul des métriques d'impact"""
        # Définir des clés
        keys = [
            RepartitionKey("site_001", "Site A", 30.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 50.0, KeyType.STATIC),
            RepartitionKey("site_003", "Site C", 20.0, KeyType.STATIC)
        ]
        self.manager.set_keys(keys)
        
        # Calculer les métriques
        metrics = self.manager.calculate_impact_metrics(
            self.production_data,
            self.consumption_data
        )
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('total_production', metrics)
        self.assertIn('total_consumption', metrics)
        self.assertIn('self_consumption_rate', metrics)
        self.assertIn('coverage_rate', metrics)
        self.assertIn('participant_metrics', metrics)
        
        # Vérifier les métriques par participant
        self.assertEqual(len(metrics['participant_metrics']), 3)
        for site_id in self.sites_config:
            site_name = self.sites_config[site_id]['nom_fichier']
            self.assertIn(site_name, metrics['participant_metrics'])


class TestRepartitionKeyManagerEdgeCases(unittest.TestCase):
    """Tests des cas limites pour le gestionnaire"""
    
    def test_empty_sites_config(self):
        """Test avec configuration vide"""
        manager = RepartitionKeyManager({})
        keys = manager.get_current_keys()
        self.assertEqual(len(keys), 0)
    
    def test_single_site(self):
        """Test avec un seul site"""
        single_site = {
            "site_001": {"nom_fichier": "Site Unique", "site_type": "Producteur"}
        }
        manager = RepartitionKeyManager(single_site)
        
        # Appliquer template équitable
        manager.apply_template('equitable')
        keys = manager.get_current_keys()
        
        self.assertEqual(len(keys), 1)
        self.assertEqual(keys[0].value, 100.0)
    
    def test_invalid_template_name(self):
        """Test avec nom de template invalide"""
        sites = {
            "site_001": {"nom_fichier": "Site A"},
            "site_002": {"nom_fichier": "Site B"}
        }
        manager = RepartitionKeyManager(sites)
        
        success = manager.apply_template('template_inexistant')
        self.assertFalse(success)
    
    def test_corrupted_import_data(self):
        """Test import avec données corrompues"""
        sites = {
            "site_001": {"nom_fichier": "Site A"},
            "site_002": {"nom_fichier": "Site B"}
        }
        manager = RepartitionKeyManager(sites)
        
        # Données corrompues
        corrupted_data = {
            "mode": "static",
            # Manque 'keys'
            "created_at": "2024-01-01"
        }
        
        success = manager.import_from_dict(corrupted_data)
        self.assertFalse(success)
    
    def test_production_data_mismatch(self):
        """Test avec données de production incompatibles"""
        sites = {
            "site_001": {"nom_fichier": "Site A"},
            "site_002": {"nom_fichier": "Site B"}
        }
        manager = RepartitionKeyManager(sites)
        
        # Définir des clés
        keys = [
            RepartitionKey("site_001", "Site A", 60.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 40.0, KeyType.STATIC)
        ]
        manager.set_keys(keys)
        
        # Production vide
        empty_production = pd.Series([], dtype=float)
        result = manager.apply_keys_to_production(empty_production)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)


def run_tests():
    """Exécuter tous les tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    print("=== Tests du gestionnaire de clés de répartition ===\n")
    run_tests()