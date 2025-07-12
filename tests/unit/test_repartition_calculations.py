"""
Tests pour les calculs de répartition
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
    KeyType, PeriodType, RuleType, RepartitionCondition
)
from modules.repartition_keys.key_calculations import (
    apply_static_keys, apply_temporal_keys, apply_dynamic_rules,
    optimize_repartition, calculate_repartition_metrics
)


class TestStaticKeysCalculation(unittest.TestCase):
    """Tests pour l'application des clés statiques"""
    
    def setUp(self):
        """Préparer les données de test"""
        # Série de production sur 24h
        self.dates = pd.date_range('2024-01-01', periods=24, freq='H')
        self.production = pd.Series(
            data=np.array([0, 0, 0, 0, 0, 10, 50, 100, 150, 200, 
                          250, 300, 300, 250, 200, 150, 100, 50, 
                          10, 0, 0, 0, 0, 0]),
            index=self.dates
        )
        
        # Clés de répartition
        self.keys = [
            RepartitionKey("site_001", "Site A", 30.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 45.0, KeyType.STATIC),
            RepartitionKey("site_003", "Site C", 25.0, KeyType.STATIC)
        ]
    
    def test_apply_static_keys_basic(self):
        """Test application basique des clés statiques"""
        result = apply_static_keys(self.production, self.keys)
        
        # Vérifier la structure du résultat
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), len(self.production))
        self.assertIn('Production_Site A', result.columns)
        self.assertIn('Production_Site B', result.columns)
        self.assertIn('Production_Site C', result.columns)
        
        # Vérifier les allocations
        total_prod = self.production.sum()
        self.assertAlmostEqual(
            result['Production_Site A'].sum(),
            total_prod * 0.30,
            places=2
        )
        self.assertAlmostEqual(
            result['Production_Site B'].sum(),
            total_prod * 0.45,
            places=2
        )
        self.assertAlmostEqual(
            result['Production_Site C'].sum(),
            total_prod * 0.25,
            places=2
        )
    
    def test_apply_static_keys_verification(self):
        """Test des colonnes de vérification"""
        result = apply_static_keys(self.production, self.keys)
        
        # Colonnes de vérification
        self.assertIn('_Total_Allocated', result.columns)
        self.assertIn('_Difference', result.columns)
        
        # Vérifier que la somme est correcte
        for idx in result.index:
            allocated = result.loc[idx, '_Total_Allocated']
            expected = self.production.loc[idx]
            self.assertAlmostEqual(allocated, expected, places=5)
            
            # Différence proche de zéro
            diff = result.loc[idx, '_Difference']
            self.assertLess(abs(diff), 0.01)
    
    def test_apply_static_keys_empty(self):
        """Test avec production vide"""
        empty_production = pd.Series([], dtype=float)
        result = apply_static_keys(empty_production, self.keys)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)


class TestTemporalKeysCalculation(unittest.TestCase):
    """Tests pour l'application des clés temporelles"""
    
    def setUp(self):
        """Préparer les données de test"""
        # Production sur 3 mois
        self.dates = pd.date_range('2024-01-01', '2024-03-31', freq='D')
        self.production = pd.Series(
            data=np.random.uniform(100, 300, len(self.dates)),
            index=self.dates
        )
        
        # Périodes temporelles
        self.temporal_periods = [
            RepartitionPeriod(
                "jan", PeriodType.MONTHLY, "Janvier",
                keys=[
                    RepartitionKey("site_001", "Site A", 40.0, KeyType.STATIC),
                    RepartitionKey("site_002", "Site B", 35.0, KeyType.STATIC),
                    RepartitionKey("site_003", "Site C", 25.0, KeyType.STATIC)
                ],
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31)
            ),
            RepartitionPeriod(
                "feb", PeriodType.MONTHLY, "Février",
                keys=[
                    RepartitionKey("site_001", "Site A", 30.0, KeyType.STATIC),
                    RepartitionKey("site_002", "Site B", 40.0, KeyType.STATIC),
                    RepartitionKey("site_003", "Site C", 30.0, KeyType.STATIC)
                ],
                start_date=datetime(2024, 2, 1),
                end_date=datetime(2024, 2, 29)
            ),
            RepartitionPeriod(
                "mar", PeriodType.MONTHLY, "Mars",
                keys=[
                    RepartitionKey("site_001", "Site A", 33.33, KeyType.STATIC),
                    RepartitionKey("site_002", "Site B", 33.33, KeyType.STATIC),
                    RepartitionKey("site_003", "Site C", 33.34, KeyType.STATIC)
                ],
                start_date=datetime(2024, 3, 1),
                end_date=datetime(2024, 3, 31)
            )
        ]
    
    def test_apply_temporal_keys(self):
        """Test application des clés temporelles"""
        result = apply_temporal_keys(
            self.production, 
            self.temporal_periods,
            self.production.index
        )
        
        # Vérifier la structure
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), len(self.production))
        
        # Vérifier les allocations pour janvier
        jan_data = result.loc['2024-01-15']
        jan_prod = self.production.loc['2024-01-15']
        
        self.assertAlmostEqual(
            jan_data['Production_Site A'],
            jan_prod * 0.40,
            places=2
        )
        
        # Vérifier les allocations pour février
        feb_data = result.loc['2024-02-15']
        feb_prod = self.production.loc['2024-02-15']
        
        self.assertAlmostEqual(
            feb_data['Production_Site B'],
            feb_prod * 0.40,
            places=2
        )
        
        # Vérifier les allocations pour mars
        mar_data = result.loc['2024-03-15']
        mar_prod = self.production.loc['2024-03-15']
        
        self.assertAlmostEqual(
            mar_data['Production_Site C'],
            mar_prod * 0.3334,
            places=2
        )


class TestDynamicRulesCalculation(unittest.TestCase):
    """Tests pour l'application des règles dynamiques"""
    
    def setUp(self):
        """Préparer les données de test"""
        # Production et consommation sur 24h
        self.dates = pd.date_range('2024-01-01', periods=24, freq='H')
        self.production = pd.Series(
            data=np.array([0, 0, 0, 0, 0, 10, 50, 100, 150, 200,
                          250, 300, 300, 250, 200, 150, 100, 50,
                          10, 0, 0, 0, 0, 0]),
            index=self.dates
        )
        
        self.consumption = pd.DataFrame({
            'site_001': [5, 5, 5, 5, 10, 20, 40, 60, 80, 100,
                        100, 100, 80, 60, 40, 30, 20, 10,
                        5, 5, 5, 5, 5, 5],
            'site_002': [10, 10, 10, 10, 20, 30, 50, 80, 100, 120,
                        150, 150, 120, 100, 80, 50, 30, 20,
                        10, 10, 10, 10, 10, 10],
            'site_003': [2, 2, 2, 2, 5, 10, 20, 30, 40, 50,
                        60, 60, 50, 40, 30, 20, 10, 5,
                        2, 2, 2, 2, 2, 2]
        }, index=self.dates)
    
    def test_apply_priority_rules(self):
        """Test application des règles de priorité"""
        # Règle de priorité : site_002 prioritaire
        priority_rule = RepartitionRule(
            rule_id="priority_1",
            rule_name="Priorité Site B",
            rule_type=RuleType.PRIORITY,
            priority=100,
            parameters={
                'priority_order': ['site_002', 'site_001', 'site_003']
            },
            target_sites=['site_001', 'site_002', 'site_003'],
            conditions=[],
            enabled=True
        )
        
        result = apply_dynamic_rules(
            self.production,
            self.consumption,
            [priority_rule]
        )
        
        # Vérifier que site_002 reçoit sa consommation en priorité
        for idx in result.index:
            if self.production.loc[idx] > 0:
                allocated_site2 = result.loc[idx, 'Production_site_002']
                needed_site2 = self.consumption.loc[idx, 'site_002']
                available = self.production.loc[idx]
                
                # Site 2 devrait recevoir min(besoin, disponible)
                expected = min(needed_site2, available)
                self.assertAlmostEqual(allocated_site2, expected, places=2)
    
    def test_apply_time_based_rules(self):
        """Test application des règles basées sur le temps"""
        # Règle : allocation différente selon l'heure
        time_rule = RepartitionRule(
            rule_id="time_1",
            rule_name="Heures pleines/creuses",
            rule_type=RuleType.TIME_BASED,
            priority=50,
            parameters={
                'time_allocations': {
                    '8': {'site_001': 40, 'site_002': 40, 'site_003': 20},
                    '12': {'site_001': 30, 'site_002': 50, 'site_003': 20},
                    '18': {'site_001': 50, 'site_002': 30, 'site_003': 20}
                },
                'default_allocation': {'site_001': 33.33, 'site_002': 33.33, 'site_003': 33.34}
            },
            target_sites=['site_001', 'site_002', 'site_003'],
            conditions=[],
            enabled=True
        )
        
        result = apply_dynamic_rules(
            self.production,
            self.consumption,
            [time_rule]
        )
        
        # Vérifier l'allocation à 8h
        hour_8_idx = self.dates[8]  # 8h du matin
        if self.production.loc[hour_8_idx] > 0:
            total_8h = result.loc[hour_8_idx, ['Production_site_001', 
                                               'Production_site_002', 
                                               'Production_site_003']].sum()
            site1_pct = result.loc[hour_8_idx, 'Production_site_001'] / total_8h * 100
            self.assertAlmostEqual(site1_pct, 40, places=0)


class TestOptimization(unittest.TestCase):
    """Tests pour l'optimisation de la répartition"""
    
    def setUp(self):
        """Préparer les données de test"""
        # Configuration des sites
        self.sites_config = {
            "site_001": {"nom_fichier": "Site A", "puissance_kwc": 100},
            "site_002": {"nom_fichier": "Site B", "puissance_kwc": 150},
            "site_003": {"nom_fichier": "Site C", "puissance_kwc": 50}
        }
        
        # Données de production/consommation
        dates = pd.date_range('2024-01-01', periods=365, freq='D')
        self.production = pd.DataFrame({
            'Total': np.random.uniform(500, 1500, len(dates))
        }, index=dates)
        
        self.consumption = pd.DataFrame({
            'site_001': np.random.uniform(200, 400, len(dates)),
            'site_002': np.random.uniform(300, 600, len(dates)),
            'site_003': np.random.uniform(100, 200, len(dates))
        }, index=dates)
    
    def test_optimize_maximize_self_consumption(self):
        """Test optimisation pour maximiser l'autoconsommation"""
        optimized_keys = optimize_repartition(
            self.production,
            self.consumption,
            self.sites_config,
            objective='maximize_self_consumption'
        )
        
        # Vérifier le résultat
        self.assertIsInstance(optimized_keys, list)
        self.assertEqual(len(optimized_keys), 3)
        
        # Vérifier que la somme fait 100%
        total = sum(key.value for key in optimized_keys)
        self.assertAlmostEqual(total, 100.0, places=2)
        
        # Le site avec la plus grande consommation devrait avoir
        # une allocation proportionnellement plus importante
        keys_dict = {k.site_id: k.value for k in optimized_keys}
        consumption_totals = self.consumption.sum()
        
        # Site avec la plus grande consommation
        max_consumer = consumption_totals.idxmax()
        max_consumer_allocation = keys_dict[max_consumer]
        
        # Devrait avoir une allocation significative
        self.assertGreater(max_consumer_allocation, 30.0)


class TestMetricsCalculation(unittest.TestCase):
    """Tests pour le calcul des métriques"""
    
    def test_calculate_metrics(self):
        """Test calcul des métriques de répartition"""
        # Données de test
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        production_data = pd.Series(
            np.random.uniform(100, 300, len(dates)),
            index=dates
        )
        
        allocated_data = pd.DataFrame({
            'Production_Site A': production_data * 0.3,
            'Production_Site B': production_data * 0.5,
            'Production_Site C': production_data * 0.2
        }, index=dates)
        
        consumption_data = pd.DataFrame({
            'Site A': np.random.uniform(50, 150, len(dates)),
            'Site B': np.random.uniform(100, 250, len(dates)),
            'Site C': np.random.uniform(30, 80, len(dates))
        }, index=dates)
        
        metrics = calculate_repartition_metrics(
            production_data,
            allocated_data,
            consumption_data
        )
        
        # Vérifier la structure des métriques
        self.assertIn('total_production', metrics)
        self.assertIn('total_allocated', metrics)
        self.assertIn('allocation_efficiency', metrics)
        self.assertIn('participant_metrics', metrics)
        
        # Vérifier l'efficacité d'allocation (devrait être ~100%)
        self.assertAlmostEqual(metrics['allocation_efficiency'], 100.0, places=1)
        
        # Vérifier les métriques par participant
        self.assertIn('Site A', metrics['participant_metrics'])
        site_a_metrics = metrics['participant_metrics']['Site A']
        self.assertIn('total_allocated', site_a_metrics)
        self.assertIn('total_consumption', site_a_metrics)
        self.assertIn('self_consumption_rate', site_a_metrics)


def run_tests():
    """Exécuter tous les tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    print("=== Tests des calculs de répartition ===\n")
    run_tests()