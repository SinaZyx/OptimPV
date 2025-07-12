"""
Data Utils - Utilitaires pour la manipulation et validation des données
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class DataUtils:
    """Utilitaires pour la manipulation et validation des données"""
    
    def __init__(self, storage_module):
        self.storage = storage_module
    
    def _json_serializer(self, obj):
        """Sérialiseur JSON personnalisé pour gérer tous les types de données"""
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        elif isinstance(obj, timedelta):
            return str(obj)
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        else:
            return str(obj)
    
    def get_all_session_state_data(self) -> Dict[str, Any]:
        """
        Capture exhaustive de tout le session_state pertinent
        
        Returns:
            Dict contenant toutes les données de session_state filtrées
        """
        all_data = {}
        for key, value in st.session_state.items():
            # Vérifier si la clé doit être exclue
            should_exclude = (
                key.startswith('_') or
                key in self.storage.excluded_keys or
                any(key.startswith(prefix) for prefix in self.storage.excluded_prefixes)
            )
            
            if not should_exclude and self._is_serializable(value):
                try:
                    # Tentative de sérialisation pour vérifier
                    json.dumps(value, default=self._json_serializer)
                    all_data[key] = value
                except (TypeError, ValueError):
                    # Si non sérialisable en JSON, essayer pickle
                    try:
                        import pickle
                        import base64
                        pickled = pickle.dumps(value)
                        all_data[f"{key}_pickled"] = base64.b64encode(pickled).decode('utf-8')
                    except:
                        # Ignorer les objets non sérialisables
                        continue
        return all_data
    
    def _is_serializable(self, obj) -> bool:
        """Vérifie si un objet est sérialisable"""
        try:
            json.dumps(obj, default=self._json_serializer)
            return True
        except (TypeError, ValueError):
            return False
    
    def calculate_data_size(self) -> Dict[str, Any]:
        """Calcule la taille des données du projet"""
        sizes = {}
        total_size = 0
        
        for key, value in st.session_state.items():
            if key not in self.storage.excluded_keys:
                try:
                    size = sys.getsizeof(value)
                    sizes[key] = size
                    total_size += size
                except:
                    sizes[key] = 0
        
        return {
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'individual_sizes': sizes
        }
    
    def get_active_modules(self) -> List[str]:
        """Détermine quels modules sont actifs dans le projet"""
        modules = []
        
        # Vérifier les données importées - liste étendue de clés
        data_keys = ['sites', 'production_data', 'uploaded_data', 'df_production', 
                     'energy_data', 'consumption_data', 'processed_data']
        
        data_found = any(key in st.session_state and st.session_state.get(key) is not None 
                         for key in data_keys)
        
        if data_found or ('data_imported' in st.session_state and st.session_state.data_imported):
            modules.append('data_import')
        
        if 'config' in st.session_state:
            modules.append('configuration')
        
        # Vérifier l'analyse économique
        if ('economic_results' in st.session_state and st.session_state.economic_results) or \
           ('economic_analysis_completed' in st.session_state and st.session_state.economic_analysis_completed):
            modules.append('economic_analysis')
        
        # Vérifier l'optimisation
        if ('optimization_results' in st.session_state and st.session_state.optimization_results) or \
           ('constrained_optim_results' in st.session_state and st.session_state.constrained_optim_results) or \
           ('optimization_completed' in st.session_state and st.session_state.optimization_completed):
            modules.append('optimization')
        
        if 'monte_carlo_results' in st.session_state:
            modules.append('monte_carlo')
        
        if any(key.startswith('chart_') for key in st.session_state.keys()):
            modules.append('visualization')
        
        return modules
    
    def calculate_completeness_score(self) -> Dict[str, Any]:
        """Calcule un score de complétude du projet"""
        # Détecter les données importées - liste étendue de clés possibles
        data_keys = ['sites', 'production_data', 'uploaded_data', 'df_production', 
                     'energy_data', 'consumption_data', 'processed_data', 'sites_data']
        
        data_imported = False
        for key in data_keys:
            if key in st.session_state:
                data = st.session_state.get(key)
                if data is not None:
                    # Vérifier si c'est un DataFrame non vide
                    if hasattr(data, 'empty') and not data.empty:
                        data_imported = True
                        break
                    # Vérifier si c'est un dict non vide
                    elif isinstance(data, dict) and len(data) > 0:
                        data_imported = True
                        break
                    # Vérifier si c'est une liste non vide
                    elif isinstance(data, list) and len(data) > 0:
                        data_imported = True
                        break
        
        # Vérifier aussi les flags explicites
        if not data_imported:
            data_imported = st.session_state.get('data_imported', False)
        
        # Détection améliorée de l'optimisation
        optimization_done = (
            ('optimization_results' in st.session_state and bool(st.session_state.get('optimization_results'))) or
            ('constrained_optim_results' in st.session_state and bool(st.session_state.get('constrained_optim_results'))) or
            ('optimization_completed' in st.session_state and st.session_state.get('optimization_completed', False)) or
            ('optimal_price' in st.session_state and st.session_state.get('optimal_price') is not None)
        )

        # Détection améliorée de l'analyse économique
        economic_done = (
            ('economic_results' in st.session_state and bool(st.session_state.get('economic_results'))) or
            ('economic_analysis_completed' in st.session_state and st.session_state.get('economic_analysis_completed', False)) or
            ('lcoe' in st.session_state and st.session_state.get('lcoe') is not None)
        )

        components = {
            'data_imported': data_imported,
            'config_set': 'config' in st.session_state and bool(st.session_state.get('config')),
            'scenarios_defined': 'scenarios' in st.session_state and bool(st.session_state.get('scenarios')),
            'economic_analysis': economic_done,
            'optimization_done': optimization_done,
            'monte_carlo_done': 'monte_carlo_results' in st.session_state and bool(st.session_state.get('monte_carlo_results'))
        }
        
        completed = sum(components.values())
        total = len(components)
        score = (completed / total) * 100
        
        return {
            'score': round(score, 1),
            'completed_components': completed,
            'total_components': total,
            'components': components
        }
    
    def validate_project_data(self) -> Dict[str, Any]:
        """Valide la cohérence et qualité des données"""
        validation_results = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'data_quality_score': 100
        }
        
        # Vérifier les données de production
        if 'production_data' in st.session_state:
            prod_data = st.session_state.production_data
            if prod_data is not None:
                if prod_data.empty:
                    validation_results['errors'].append("Données de production vides")
                    validation_results['is_valid'] = False
                elif prod_data.isnull().sum().sum() > len(prod_data) * 0.1:
                    validation_results['warnings'].append("Plus de 10% de valeurs manquantes dans les données")
                    validation_results['data_quality_score'] -= 10
        
        # Vérifier la configuration
        if 'config' in st.session_state:
            config = st.session_state.config
            if not isinstance(config, dict) or not config:
                validation_results['warnings'].append("Configuration incomplète ou invalide")
                validation_results['data_quality_score'] -= 15
        
        # Vérifier la cohérence des résultats
        if 'economic_results' in st.session_state and 'optimization_results' in st.session_state:
            # Vérifier que les scénarios correspondent
            eco_scenarios = set(st.session_state.economic_results.keys())
            opt_scenarios = set(st.session_state.optimization_results.keys())
            if eco_scenarios != opt_scenarios:
                validation_results['warnings'].append("Incohérence entre scénarios économiques et d'optimisation")
                validation_results['data_quality_score'] -= 5
        
        # Ajuster le score de qualité
        validation_results['data_quality_score'] = max(0, validation_results['data_quality_score'])
        
        return validation_results