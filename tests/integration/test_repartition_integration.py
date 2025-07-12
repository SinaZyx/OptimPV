"""
Tests d'intégration complets pour le système de clés de répartition
"""

import unittest
import pandas as pd
import numpy as np
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta
import sys

# Ajouter le chemin du module parent
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.repartition_keys.key_manager import RepartitionKeyManager
from modules.repartition_keys.key_models import (
    RepartitionKey, RepartitionPeriod, RepartitionRule,
    KeyType, PeriodType, RuleType, RepartitionCondition
)
from modules.repartition_keys.key_calculations import (
    apply_static_keys, apply_temporal_keys, apply_dynamic_rules,
    optimize_repartition, calculate_repartition_metrics
)
from modules.repartition_keys.key_validators import RepartitionValidator
from modules.repartition_keys.key_storage import RepartitionStorage


class TestIntegrationCompleteWorkflow(unittest.TestCase):
    """Tests d'intégration du workflow complet"""
    
    def setUp(self):
        """Préparer l'environnement de test"""
        # Configuration complète des sites
        self.sites_config = {
            "site_001": {
                "nom_fichier": "Résidence Les Mimosas",
                "site_type": "Résidentiel",
                "puissance_kwc": 100,
                "consommation_moyenne": 1500,
                "nb_logements": 20
            },
            "site_002": {
                "nom_fichier": "Entreprise TechCorp",
                "site_type": "PME",
                "puissance_kwc": 200,
                "consommation_moyenne": 3000,
                "surface_m2": 1000
            },
            "site_003": {
                "nom_fichier": "Commerce SuperMarket",
                "site_type": "Commerce",
                "puissance_kwc": 150,
                "consommation_moyenne": 2500,
                "horaires": "8h-20h"
            },
            "site_004": {
                "nom_fichier": "École Jean Jaurès",
                "site_type": "Public",
                "puissance_kwc": 80,
                "consommation_moyenne": 800,
                "fermeture_ete": True
            }
        }
        
        # Créer le gestionnaire
        self.manager = RepartitionKeyManager(self.sites_config)
        
        # Créer un dossier temporaire pour les tests
        self.test_dir = tempfile.mkdtemp()
        
        # Données de production/consommation sur 1 an
        self.dates = pd.date_range('2024-01-01', '2024-12-31', freq='H')
        
        # Production solaire réaliste (variation journalière et saisonnière)
        hour_of_day = self.dates.hour
        day_of_year = self.dates.dayofyear
        
        # Profil journalier (0 la nuit, pic à midi)
        daily_profile = np.where(
            (hour_of_day >= 6) & (hour_of_day <= 18),
            np.sin((hour_of_day - 6) * np.pi / 12),
            0
        )
        
        # Variation saisonnière (plus en été)
        seasonal_factor = 0.7 + 0.3 * np.sin((day_of_year - 80) * 2 * np.pi / 365)
        
        # Production totale = 530 kWc installés
        max_production = 530
        self.production_data = pd.Series(
            max_production * daily_profile * seasonal_factor * np.random.uniform(0.8, 1.0, len(self.dates)),
            index=self.dates,
            name='Production'
        )
        
        # Consommation par site (profils différents)
        self.consumption_data = pd.DataFrame(index=self.dates)
        
        # Résidentiel : consommation matin/soir
        residential_profile = np.where(
            (hour_of_day < 9) | (hour_of_day > 17),
            1.2,  # Plus élevé matin/soir
            0.6   # Plus bas en journée
        )
        self.consumption_data['site_001'] = 60 * residential_profile * np.random.uniform(0.8, 1.2, len(self.dates))
        
        # PME : consommation heures de bureau
        pme_profile = np.where(
            (hour_of_day >= 8) & (hour_of_day <= 18) & (self.dates.weekday < 5),
            1.5,  # Élevé en semaine jour
            0.3   # Bas soir/weekend
        )
        self.consumption_data['site_002'] = 120 * pme_profile * np.random.uniform(0.9, 1.1, len(self.dates))
        
        # Commerce : consommation 8h-20h tous les jours
        commerce_profile = np.where(
            (hour_of_day >= 8) & (hour_of_day <= 20),
            1.4,
            0.2
        )
        self.consumption_data['site_003'] = 100 * commerce_profile * np.random.uniform(0.85, 1.15, len(self.dates))
        
        # École : consommation semaine scolaire
        school_profile = np.where(
            (hour_of_day >= 8) & (hour_of_day <= 17) & 
            (self.dates.weekday < 5) & 
            (~self.dates.month.isin([7, 8])),  # Pas juillet/août
            1.0,
            0.1
        )
        self.consumption_data['site_004'] = 40 * school_profile * np.random.uniform(0.8, 1.2, len(self.dates))
    
    def tearDown(self):
        """Nettoyer après les tests"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_scenario_1_static_keys_full_year(self):
        """Scénario 1 : Clés statiques sur une année complète"""
        print("\n=== Scénario 1 : Répartition statique équitable ===")
        
        # 1. Appliquer template équitable
        self.manager.apply_template('equitable')
        
        # 2. Valider la configuration
        is_valid, msg = self.manager.validate_keys_coherence()
        self.assertTrue(is_valid)
        print(f"Validation : {msg}")
        
        # 3. Appliquer aux données de production
        allocated_production = self.manager.apply_keys_to_production(self.production_data)
        
        # 4. Calculer les métriques
        metrics = self.manager.calculate_impact_metrics(
            self.production_data,
            self.consumption_data
        )
        
        # 5. Vérifications
        self.assertAlmostEqual(metrics['total_production'], self.production_data.sum(), places=2)
        self.assertGreater(metrics['self_consumption_rate'], 50)  # Au moins 50% d'autoconsommation
        
        # 6. Afficher les résultats
        print(f"Production totale : {metrics['total_production']:.0f} kWh")
        print(f"Taux d'autoconsommation global : {metrics['self_consumption_rate']:.1f}%")
        print("\nRésultats par participant :")
        for site_name, site_metrics in metrics['participant_metrics'].items():
            print(f"  {site_name}:")
            print(f"    - Énergie allouée : {site_metrics['total_allocated']:.0f} kWh")
            print(f"    - Consommation : {site_metrics['total_consumption']:.0f} kWh")
            print(f"    - Taux d'autoconsommation : {site_metrics['self_consumption_rate']:.1f}%")
    
    def test_scenario_2_consumption_based_optimization(self):
        """Scénario 2 : Optimisation basée sur la consommation"""
        print("\n=== Scénario 2 : Optimisation basée sur la consommation ===")
        
        # 1. Appliquer template basé sur la consommation
        self.manager.apply_template('consumption_based', consumption_data=self.consumption_data)
        
        # 2. Afficher la répartition
        keys = self.manager.get_current_keys()
        print("Répartition optimisée :")
        for key in keys:
            print(f"  - {key.participant_name} : {key.value:.1f}%")
        
        # 3. Appliquer et calculer les métriques
        allocated_production = self.manager.apply_keys_to_production(self.production_data)
        metrics = self.manager.calculate_impact_metrics(
            self.production_data,
            self.consumption_data
        )
        
        # 4. Vérifier l'amélioration vs équitable
        # Sauvegarder les métriques optimisées
        optimized_self_consumption = metrics['self_consumption_rate']
        
        # Comparer avec répartition équitable
        self.manager.apply_template('equitable')
        equitable_metrics = self.manager.calculate_impact_metrics(
            self.production_data,
            self.consumption_data
        )
        equitable_self_consumption = equitable_metrics['self_consumption_rate']
        
        print(f"\nComparaison des taux d'autoconsommation :")
        print(f"  - Répartition équitable : {equitable_self_consumption:.1f}%")
        print(f"  - Répartition optimisée : {optimized_self_consumption:.1f}%")
        print(f"  - Gain : +{optimized_self_consumption - equitable_self_consumption:.1f} points")
        
        # L'optimisation devrait améliorer le taux
        self.assertGreater(optimized_self_consumption, equitable_self_consumption)
    
    def test_scenario_3_temporal_keys_seasonal(self):
        """Scénario 3 : Clés temporelles avec variations saisonnières"""
        print("\n=== Scénario 3 : Variations saisonnières ===")
        
        # 1. Passer en mode temporel
        self.manager.config['mode'] = 'temporal'
        
        # 2. Créer des périodes saisonnières
        periods = []
        
        # Hiver : favoriser résidentiel et commerce
        periods.append(RepartitionPeriod(
            "winter", PeriodType.CUSTOM, "Hiver",
            keys=[
                RepartitionKey("site_001", "Résidence Les Mimosas", 35.0, KeyType.STATIC),
                RepartitionKey("site_002", "Entreprise TechCorp", 20.0, KeyType.STATIC),
                RepartitionKey("site_003", "Commerce SuperMarket", 35.0, KeyType.STATIC),
                RepartitionKey("site_004", "École Jean Jaurès", 10.0, KeyType.STATIC)
            ],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 31)
        ))
        
        # Printemps : équilibré
        periods.append(RepartitionPeriod(
            "spring", PeriodType.CUSTOM, "Printemps",
            keys=[
                RepartitionKey("site_001", "Résidence Les Mimosas", 25.0, KeyType.STATIC),
                RepartitionKey("site_002", "Entreprise TechCorp", 30.0, KeyType.STATIC),
                RepartitionKey("site_003", "Commerce SuperMarket", 25.0, KeyType.STATIC),
                RepartitionKey("site_004", "École Jean Jaurès", 20.0, KeyType.STATIC)
            ],
            start_date=datetime(2024, 4, 1),
            end_date=datetime(2024, 6, 30)
        ))
        
        # Été : moins pour l'école (fermée)
        periods.append(RepartitionPeriod(
            "summer", PeriodType.CUSTOM, "Été",
            keys=[
                RepartitionKey("site_001", "Résidence Les Mimosas", 30.0, KeyType.STATIC),
                RepartitionKey("site_002", "Entreprise TechCorp", 35.0, KeyType.STATIC),
                RepartitionKey("site_003", "Commerce SuperMarket", 30.0, KeyType.STATIC),
                RepartitionKey("site_004", "École Jean Jaurès", 5.0, KeyType.STATIC)
            ],
            start_date=datetime(2024, 7, 1),
            end_date=datetime(2024, 9, 30)
        ))
        
        # Automne : favoriser PME et école
        periods.append(RepartitionPeriod(
            "autumn", PeriodType.CUSTOM, "Automne",
            keys=[
                RepartitionKey("site_001", "Résidence Les Mimosas", 20.0, KeyType.STATIC),
                RepartitionKey("site_002", "Entreprise TechCorp", 35.0, KeyType.STATIC),
                RepartitionKey("site_003", "Commerce SuperMarket", 20.0, KeyType.STATIC),
                RepartitionKey("site_004", "École Jean Jaurès", 25.0, KeyType.STATIC)
            ],
            start_date=datetime(2024, 10, 1),
            end_date=datetime(2024, 12, 31)
        ))
        
        # 3. Définir les périodes
        self.manager.set_temporal_periods(periods)
        
        # 4. Appliquer aux données
        allocated_production = apply_temporal_keys(
            self.production_data,
            periods,
            self.production_data.index
        )
        
        # 5. Calculer les métriques par saison
        print("Métriques par saison :")
        for period in periods:
            # Filtrer les données pour cette période
            mask = (self.production_data.index >= period.start_date) & \
                   (self.production_data.index <= period.end_date)
            
            period_prod = self.production_data[mask]
            period_cons = self.consumption_data[mask]
            period_alloc = allocated_production[mask]
            
            # Calculer les métriques
            metrics = calculate_repartition_metrics(
                period_prod,
                period_alloc,
                period_cons
            )
            
            print(f"\n{period.period_name} :")
            print(f"  - Production : {metrics['total_production']:.0f} kWh")
            print(f"  - Taux d'autoconsommation : {metrics['self_consumption_rate']:.1f}%")
    
    def test_scenario_4_dynamic_rules_priority(self):
        """Scénario 4 : Règles dynamiques avec priorités"""
        print("\n=== Scénario 4 : Règles de priorité dynamiques ===")
        
        # 1. Créer des règles de priorité
        rules = []
        
        # Règle 1 : Priorité résidentiel le matin et soir
        rules.append(RepartitionRule(
            "residential_priority",
            "Priorité résidentiel matin/soir",
            RuleType.TIME_BASED,
            priority=100,
            parameters={
                'time_allocations': {
                    '6': {'site_001': 50, 'site_002': 15, 'site_003': 25, 'site_004': 10},
                    '7': {'site_001': 45, 'site_002': 20, 'site_003': 25, 'site_004': 10},
                    '8': {'site_001': 35, 'site_002': 25, 'site_003': 30, 'site_004': 10},
                    '18': {'site_001': 40, 'site_002': 15, 'site_003': 35, 'site_004': 10},
                    '19': {'site_001': 50, 'site_002': 10, 'site_003': 35, 'site_004': 5},
                    '20': {'site_001': 60, 'site_002': 5, 'site_003': 30, 'site_004': 5}
                },
                'default_allocation': {'site_001': 25, 'site_002': 30, 'site_003': 25, 'site_004': 20}
            },
            target_sites=['site_001', 'site_002', 'site_003', 'site_004'],
            conditions=[],
            enabled=True
        ))
        
        # Règle 2 : Priorité PME en journée (jours ouvrés)
        rules.append(RepartitionRule(
            "business_hours",
            "Priorité PME heures bureau",
            RuleType.TIME_BASED,
            priority=90,
            parameters={
                'time_allocations': {
                    '9': {'site_001': 15, 'site_002': 45, 'site_003': 25, 'site_004': 15},
                    '10': {'site_001': 15, 'site_002': 50, 'site_003': 20, 'site_004': 15},
                    '11': {'site_001': 15, 'site_002': 50, 'site_003': 20, 'site_004': 15},
                    '12': {'site_001': 20, 'site_002': 40, 'site_003': 25, 'site_004': 15},
                    '13': {'site_001': 20, 'site_002': 40, 'site_003': 25, 'site_004': 15},
                    '14': {'site_001': 15, 'site_002': 50, 'site_003': 20, 'site_004': 15},
                    '15': {'site_001': 15, 'site_002': 50, 'site_003': 20, 'site_004': 15},
                    '16': {'site_001': 15, 'site_002': 45, 'site_003': 25, 'site_004': 15},
                    '17': {'site_001': 20, 'site_002': 40, 'site_003': 25, 'site_004': 15}
                }
            },
            target_sites=['site_001', 'site_002', 'site_003', 'site_004'],
            conditions=[
                RepartitionCondition("weekday", "<", 5)  # Lundi-Vendredi
            ],
            enabled=True
        ))
        
        # 2. Appliquer les règles
        # Sélectionner une journée type (mardi en mars)
        test_date = datetime(2024, 3, 12)  # Un mardi
        test_data_mask = (self.production_data.index.date == test_date.date())
        
        test_production = self.production_data[test_data_mask]
        test_consumption = self.consumption_data[test_data_mask]
        
        # Appliquer les règles
        allocated_production = apply_dynamic_rules(
            test_production,
            test_consumption,
            rules
        )
        
        # 3. Analyser les résultats heure par heure
        print(f"Analyse horaire pour le {test_date.strftime('%d/%m/%Y')} :")
        print("Heure | Production | Site 1 (%) | Site 2 (%) | Site 3 (%) | Site 4 (%)")
        print("-" * 70)
        
        for hour in range(24):
            hour_mask = test_production.index.hour == hour
            if hour_mask.any():
                prod_hour = test_production[hour_mask].iloc[0]
                if prod_hour > 0:
                    alloc_hour = allocated_production[hour_mask].iloc[0]
                    pct_1 = (alloc_hour['Production_site_001'] / prod_hour * 100) if prod_hour > 0 else 0
                    pct_2 = (alloc_hour['Production_site_002'] / prod_hour * 100) if prod_hour > 0 else 0
                    pct_3 = (alloc_hour['Production_site_003'] / prod_hour * 100) if prod_hour > 0 else 0
                    pct_4 = (alloc_hour['Production_site_004'] / prod_hour * 100) if prod_hour > 0 else 0
                    
                    print(f" {hour:2d}h  | {prod_hour:7.1f} kW | {pct_1:10.1f} | {pct_2:10.1f} | {pct_3:10.1f} | {pct_4:10.1f}")
    
    def test_scenario_5_complete_workflow_with_storage(self):
        """Scénario 5 : Workflow complet avec stockage et historique"""
        print("\n=== Scénario 5 : Workflow complet avec persistance ===")
        
        # 1. Initialiser le stockage
        storage = RepartitionStorage(self.test_dir)
        
        # 2. Créer plusieurs configurations et les sauvegarder
        configs = {
            "config_equitable": {
                "name": "Répartition Équitable",
                "template": "equitable"
            },
            "config_optimisee": {
                "name": "Optimisée Consommation",
                "template": "consumption_based"
            },
            "config_priorite_pme": {
                "name": "Priorité PME",
                "keys": [
                    RepartitionKey("site_001", "Résidence Les Mimosas", 20.0, KeyType.STATIC),
                    RepartitionKey("site_002", "Entreprise TechCorp", 50.0, KeyType.STATIC),
                    RepartitionKey("site_003", "Commerce SuperMarket", 20.0, KeyType.STATIC),
                    RepartitionKey("site_004", "École Jean Jaurès", 10.0, KeyType.STATIC)
                ]
            }
        }
        
        saved_configs = []
        
        for config_id, config_data in configs.items():
            if 'template' in config_data:
                self.manager.apply_template(
                    config_data['template'],
                    consumption_data=self.consumption_data if config_data['template'] == 'consumption_based' else None
                )
            else:
                self.manager.set_keys(config_data['keys'])
            
            # Sauvegarder
            config_dict = self.manager.export_to_dict()
            config_dict['name'] = config_data['name']
            
            success = storage.save_configuration(config_id, config_dict)
            self.assertTrue(success)
            saved_configs.append(config_id)
            
            print(f"✓ Configuration '{config_data['name']}' sauvegardée")
        
        # 3. Lister les configurations
        available_configs = storage.list_configurations()
        self.assertEqual(len(available_configs), 3)
        print(f"\nConfigurations disponibles : {len(available_configs)}")
        
        # 4. Charger et comparer les configurations
        print("\nComparaison des configurations :")
        results = {}
        
        for config_info in available_configs:
            # Charger la configuration
            config_data = storage.load_configuration(config_info['filename'])
            self.assertIsNotNone(config_data)
            
            # Appliquer au gestionnaire
            self.manager.import_from_dict(config_data)
            
            # Calculer les métriques
            allocated = self.manager.apply_keys_to_production(self.production_data)
            metrics = self.manager.calculate_impact_metrics(
                self.production_data,
                self.consumption_data
            )
            
            results[config_data['name']] = metrics
            
            print(f"\n{config_data['name']} :")
            print(f"  - Taux autoconsommation : {metrics['self_consumption_rate']:.1f}%")
            print(f"  - Taux couverture : {metrics['coverage_rate']:.1f}%")
        
        # 5. Identifier la meilleure configuration
        best_config = max(results.items(), key=lambda x: x[1]['self_consumption_rate'])
        print(f"\n✨ Meilleure configuration : {best_config[0]}")
        print(f"   Taux d'autoconsommation : {best_config[1]['self_consumption_rate']:.1f}%")
    
    def test_scenario_6_validation_and_error_handling(self):
        """Scénario 6 : Validation et gestion d'erreurs"""
        print("\n=== Scénario 6 : Tests de validation ===")
        
        validator = RepartitionValidator()
        
        # Test 1 : Clés invalides (somme != 100%)
        print("\nTest 1 : Somme incorrecte")
        invalid_keys = [
            RepartitionKey("site_001", "Site A", 30.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 40.0, KeyType.STATIC)
            # Manque 30% !
        ]
        
        success = self.manager.set_keys(invalid_keys)
        self.assertFalse(success)
        print("✓ Rejet correct des clés invalides")
        
        # Test 2 : Sites manquants
        print("\nTest 2 : Sites manquants")
        partial_keys = [
            RepartitionKey("site_001", "Site A", 50.0, KeyType.STATIC),
            RepartitionKey("site_002", "Site B", 50.0, KeyType.STATIC)
            # site_003 et site_004 manquants
        ]
        
        result = validator.validate_complete(partial_keys, self.sites_config)
        self.assertFalse(result['is_valid'])
        self.assertIn('coverage', ' '.join(result['errors']).lower())
        print("✓ Détection correcte des sites manquants")
        
        # Test 3 : Périodes temporelles qui se chevauchent
        print("\nTest 3 : Chevauchement temporel")
        overlapping_periods = [
            RepartitionPeriod(
                "p1", PeriodType.CUSTOM, "Période 1",
                keys=[
                    RepartitionKey("site_001", "Site A", 25.0, KeyType.STATIC),
                    RepartitionKey("site_002", "Site B", 25.0, KeyType.STATIC),
                    RepartitionKey("site_003", "Site C", 25.0, KeyType.STATIC),
                    RepartitionKey("site_004", "Site D", 25.0, KeyType.STATIC)
                ],
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 3, 31)
            ),
            RepartitionPeriod(
                "p2", PeriodType.CUSTOM, "Période 2",
                keys=[
                    RepartitionKey("site_001", "Site A", 25.0, KeyType.STATIC),
                    RepartitionKey("site_002", "Site B", 25.0, KeyType.STATIC),
                    RepartitionKey("site_003", "Site C", 25.0, KeyType.STATIC),
                    RepartitionKey("site_004", "Site D", 25.0, KeyType.STATIC)
                ],
                start_date=datetime(2024, 3, 15),  # Chevauche avec p1 !
                end_date=datetime(2024, 6, 30)
            )
        ]
        
        is_coherent, issues = validator.validate_temporal_coherence(overlapping_periods)
        self.assertFalse(is_coherent)
        self.assertTrue(any('chevauchement' in issue.lower() for issue in issues))
        print("✓ Détection correcte du chevauchement temporel")
        
        # Test 4 : Gestion de sites dynamiques
        print("\nTest 4 : Ajout/suppression de sites")
        
        # Configuration initiale
        self.manager.apply_template('equitable')
        initial_keys = self.manager.get_current_keys()
        self.assertEqual(len(initial_keys), 4)
        
        # Nouvelle configuration avec sites modifiés
        new_sites_config = {
            "site_001": self.sites_config["site_001"],
            "site_002": self.sites_config["site_002"],
            # site_003 supprimé
            # site_004 supprimé
            "site_005": {
                "nom_fichier": "Nouveau Bâtiment",
                "site_type": "Tertiaire",
                "puissance_kwc": 120
            }
        }
        
        # Mettre à jour
        self.manager.update_sites_config(new_sites_config)
        updated_keys = self.manager.get_current_keys()
        
        self.assertEqual(len(updated_keys), 3)
        self.assertTrue(any(k.site_id == "site_005" for k in updated_keys))
        
        # Vérifier que la somme est toujours 100%
        total = sum(k.value for k in updated_keys)
        self.assertAlmostEqual(total, 100.0, places=2)
        print("✓ Gestion correcte de l'ajout/suppression de sites")


def run_integration_tests():
    """Exécuter tous les tests d'intégration"""
    # Configuration pour avoir des outputs détaillés
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestIntegrationCompleteWorkflow)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Résumé
    print("\n" + "="*70)
    print("RÉSUMÉ DES TESTS D'INTÉGRATION")
    print("="*70)
    print(f"Tests exécutés : {result.testsRun}")
    print(f"Succès : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Échecs : {len(result.failures)}")
    print(f"Erreurs : {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ TOUS LES TESTS D'INTÉGRATION SONT PASSÉS !")
    else:
        print("\n❌ Certains tests ont échoué")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("=== Tests d'intégration du système de clés de répartition ===\n")
    success = run_integration_tests()