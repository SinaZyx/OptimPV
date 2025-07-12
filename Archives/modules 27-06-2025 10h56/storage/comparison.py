"""
Project Comparison - Comparaison avancée entre projets OptimPV
"""

import streamlit as st
import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ProjectComparison:
    """Gestionnaire de comparaison de projets"""
    
    def __init__(self, storage_module):
        self.storage = storage_module
    
    def compare_projects_advanced(self, project_id1: str, project_id2: str) -> Optional[Dict[str, Any]]:
        """
        Effectue une comparaison avancée entre deux projets
        Charge toutes les données pertinentes et prépare les analyses
        """
        try:
            # Chemins des projets
            project_dir1 = os.path.join('projects', project_id1)
            project_dir2 = os.path.join('projects', project_id2)
            
            # Charger les manifestes
            with open(os.path.join(project_dir1, 'manifest.json'), 'r') as f:
                manifest1 = json.load(f)
            
            with open(os.path.join(project_dir2, 'manifest.json'), 'r') as f:
                manifest2 = json.load(f)
            
            # Charger les configurations
            config1 = {}
            config2 = {}
            
            config_path1 = os.path.join(project_dir1, 'config.json')
            config_path2 = os.path.join(project_dir2, 'config.json')
            
            if os.path.exists(config_path1):
                with open(config_path1, 'r') as f:
                    config1 = json.load(f)
            
            if os.path.exists(config_path2):
                with open(config_path2, 'r') as f:
                    config2 = json.load(f)
            
            # Charger les résultats économiques
            economic1 = {}
            economic2 = {}
            
            economic_path1 = os.path.join(project_dir1, 'economic_results.json')
            economic_path2 = os.path.join(project_dir2, 'economic_results.json')
            
            if os.path.exists(economic_path1):
                with open(economic_path1, 'r') as f:
                    economic1 = json.load(f)
                    logger.debug(f"DEBUG: Chargé economic1 de {project_id1}: {bool(economic1)} - Clés: {list(economic1.keys()) if economic1 else 'Vide'}")
            else:
                logger.debug(f"DEBUG: Fichier economic_results.json n'existe pas pour {project_id1}")
            
            if os.path.exists(economic_path2):
                with open(economic_path2, 'r') as f:
                    economic2 = json.load(f)
                    logger.debug(f"DEBUG: Chargé economic2 de {project_id2}: {bool(economic2)} - Clés: {list(economic2.keys()) if economic2 else 'Vide'}")
            else:
                logger.debug(f"DEBUG: Fichier economic_results.json n'existe pas pour {project_id2}")
            
            # Charger les résultats d'optimisation
            optimization1 = {}
            optimization2 = {}
            
            optimization_path1 = os.path.join(project_dir1, 'optimization_results.json')
            optimization_path2 = os.path.join(project_dir2, 'optimization_results.json')
            
            if os.path.exists(optimization_path1):
                with open(optimization_path1, 'r') as f:
                    optimization1 = json.load(f)
                    logger.debug(f"DEBUG: Chargé optimization1 de {project_id1}: {bool(optimization1)} - Clés: {list(optimization1.keys()) if optimization1 else 'Vide'}")
            else:
                logger.debug(f"DEBUG: Fichier optimization_results.json n'existe pas pour {project_id1}")
            
            if os.path.exists(optimization_path2):
                with open(optimization_path2, 'r') as f:
                    optimization2 = json.load(f)
                    logger.debug(f"DEBUG: Chargé optimization2 de {project_id2}: {bool(optimization2)} - Clés: {list(optimization2.keys()) if optimization2 else 'Vide'}")
            else:
                logger.debug(f"DEBUG: Fichier optimization_results.json n'existe pas pour {project_id2}")
            
            # Charger les résultats Monte Carlo
            monte_carlo1 = {}
            monte_carlo2 = {}
            
            monte_carlo_path1 = os.path.join(project_dir1, 'monte_carlo_results.json')
            monte_carlo_path2 = os.path.join(project_dir2, 'monte_carlo_results.json')
            
            if os.path.exists(monte_carlo_path1):
                with open(monte_carlo_path1, 'r') as f:
                    monte_carlo1 = json.load(f)
            
            if os.path.exists(monte_carlo_path2):
                with open(monte_carlo_path2, 'r') as f:
                    monte_carlo2 = json.load(f)
            
            # Analyser les différences principales
            key_differences = self._analyze_key_differences(
                config1, config2, economic1, economic2, optimization1, optimization2
            )
            
            return {
                'manifest1': manifest1,
                'manifest2': manifest2,
                'config1': config1,
                'config2': config2,
                'economic1': economic1,
                'economic2': economic2,
                'optimization1': optimization1,
                'optimization2': optimization2,
                'monte_carlo1': monte_carlo1,
                'monte_carlo2': monte_carlo2,
                'key_differences': key_differences
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la comparaison avancée: {e}")
            return None
    
    def _analyze_key_differences(self, config1, config2, economic1, economic2, optimization1, optimization2):
        """Analyse les différences clés entre deux projets"""
        differences = {
            'config_changes': [],
            'performance_delta': {},
            'financial_impact': {},
            'risk_assessment': {}
        }
        
        # Analyser les changements de configuration avec gestion robuste
        for key in set(config1.keys()) | set(config2.keys()):
            val1 = config1.get(key)
            val2 = config2.get(key)
            
            # Gestion robuste des comparaisons
            is_different = self._is_significantly_different(val1, val2, key)
            
            if is_different:
                differences['config_changes'].append({
                    'parameter': key,
                    'project1': val1,
                    'project2': val2,
                    'change': self._calculate_change(val1, val2)
                })
        
        # Analyser les différences de performance
        if optimization1 and optimization2:
            # Trouver le meilleur scénario commun
            scenarios1 = set(optimization1.keys()) - {'metadata'}
            scenarios2 = set(optimization2.keys()) - {'metadata'}
            common_scenarios = scenarios1 & scenarios2
            
            if common_scenarios:
                scenario = list(common_scenarios)[0]
                
                if 'best_result' in optimization1.get(scenario, {}):
                    best1 = optimization1[scenario]['best_result']
                    best2 = optimization2[scenario].get('best_result', {})
                    
                    # Comparer les métriques clés
                    metrics = ['VAN', 'ROI', 'payback_years', 'optimal_price']
                    for metric in metrics:
                        val1 = best1.get(metric, 0)
                        val2 = best2.get(metric, 0)
                        
                        differences['performance_delta'][metric] = {
                            'project1': val1,
                            'project2': val2,
                            'delta': val2 - val1 if isinstance(val1, (int, float)) else None,
                            'delta_percent': ((val2 - val1) / val1 * 100) if val1 and isinstance(val1, (int, float)) else None
                        }
        
        return differences
    
    def _is_significantly_different(self, val1, val2, parameter_name):
        """Détermine si deux valeurs sont significativement différentes"""
        # Si l'une des valeurs est None et l'autre pas
        if (val1 is None) != (val2 is None):
            return True
            
        # Si les deux sont None
        if val1 is None and val2 is None:
            return False
            
        # Pour les valeurs numériques, utiliser un seuil de tolérance
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            # Seuils spécifiques selon le paramètre
            tolerance_map = {
                'capex_scenario': 1000,      # 1000€ pour CAPEX
                'puissance_kwc_installee': 0.1,  # 0.1 kWc pour puissance
                'prix_revente': 0.001,       # 0.001€/kWh pour prix
                'duree_ppa': 0.1,           # 0.1 année pour durée
                'couts_racks': 100,         # 100€ pour coûts équipements
                'couts_onduleurs': 100,
                'couts_modules': 100,
                'cout_raccordement': 100,
                'cout_etude': 100
            }
            
            # Utiliser le seuil spécifique ou un seuil général
            if parameter_name in tolerance_map:
                threshold = tolerance_map[parameter_name]
            else:
                # Seuil général: 1% de la valeur ou 0.01 minimum
                threshold = max(abs(val1) * 0.01, 0.01) if val1 != 0 else 0.01
            
            return abs(val1 - val2) > threshold
        
        # Pour les autres types, comparaison exacte
        return val1 != val2
    
    def _calculate_change(self, val1, val2):
        """Calcule le changement entre deux valeurs"""
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            if val1 != 0:
                return {'absolute': val2 - val1, 'percent': (val2 - val1) / val1 * 100}
            else:
                return {'absolute': val2 - val1, 'percent': None}
        else:
            return {'from': val1, 'to': val2}