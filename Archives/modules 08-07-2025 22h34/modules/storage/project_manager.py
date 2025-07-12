"""
Project Manager - Gestion complète des projets OptimPV
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import io
import glob
import shutil
import hashlib
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import zipfile
import tempfile

logger = logging.getLogger(__name__)

class DataNormalizer:
    """Normalise les différents formats de données pour une gestion uniforme"""
    
    @staticmethod
    def normalize_economic_results(data: Any) -> Dict[str, Any]:
        """Normalise les résultats économiques dans un format standard"""
        from .debug_logger import storage_logger
        storage_logger.log_data_inspection("economic_results_raw", data, "normalize")
        
        normalized = {}
        
        # Si c'est déjà un dict de scénarios
        if isinstance(data, dict) and any(isinstance(v, dict) for v in data.values()):
            for scenario, results in data.items():
                if isinstance(results, dict):
                    normalized[scenario] = DataNormalizer._normalize_economic_scenario(results)
        
        # Si c'est un dict simple de résultats
        elif isinstance(data, dict) and not any(isinstance(v, dict) for v in data.values()):
            normalized['Scénario principal'] = DataNormalizer._normalize_economic_scenario(data)
        
        # Si on a des résultats directs dans session_state
        else:
            # Chercher les indicateurs économiques
            scenario_data = {}
            indicators = ['lcoe', 'van', 'tri', 'payback', 'roi', 'ebitda', 
                         'VAN_Projet', 'VAN_Fonds_Propres', 'TRI_Projet', 'TRI_Fonds_Propres']
            
            for indicator in indicators:
                if hasattr(st.session_state, indicator) and st.session_state.get(indicator) is not None:
                    scenario_data[indicator] = st.session_state.get(indicator)
            
            if scenario_data:
                normalized['Scénario actuel'] = scenario_data
        
        storage_logger.log_data_inspection("economic_results_normalized", normalized, "normalize")
        return normalized
    
    @staticmethod
    def _normalize_economic_scenario(results: Dict[str, Any]) -> Dict[str, Any]:
        """Normalise un scénario économique individuel"""
        normalized = {}
        
        # Copier toutes les clés sauf monthly_data
        for key, value in results.items():
            if key == 'monthly_data':
                # Gérer DataFrame/dict/list
                if isinstance(value, pd.DataFrame):
                    normalized[key] = value.to_dict('records')
                elif isinstance(value, list):
                    normalized[key] = value
                elif isinstance(value, dict):
                    normalized[key] = value
            else:
                # Convertir numpy en types Python standards
                if isinstance(value, np.ndarray):
                    normalized[key] = value.tolist()
                elif isinstance(value, (np.integer, np.floating)):
                    normalized[key] = value.item()
                elif isinstance(value, np.bool_):
                    normalized[key] = bool(value)
                else:
                    normalized[key] = value
        
        return normalized
    
    @staticmethod
    def normalize_optimization_results(data: Any) -> Dict[str, Any]:
        """Normalise les résultats d'optimisation dans un format standard"""
        from .debug_logger import storage_logger
        storage_logger.log_data_inspection("optimization_results_raw", data, "normalize")
        
        normalized = {}
        
        # Détecter le format
        if isinstance(data, dict):
            for scenario, results in data.items():
                if isinstance(results, dict):
                    # Format avec scenario_name
                    if 'scenario_name' in results:
                        normalized[scenario] = {
                            'scenario_name': results['scenario_name'],
                            'prix_optimal': results.get('prix_optimal', results.get('optimal_price', 0)),
                            'indicateurs_optimaux': results.get('indicateurs_optimaux', {}),
                            'prix_testes': results.get('prix_testes', []),
                            'resultats_detailles': results.get('resultats_detailles', [])
                        }
                    # Format avec best_result
                    elif 'best_result' in results:
                        normalized[scenario] = {
                            'scenario_name': scenario,
                            'prix_optimal': results['best_result'].get('optimal_price', 0),
                            'indicateurs_optimaux': results['best_result'],
                            'constraints': results.get('constraints', {}),
                            'status': results.get('status', 'unknown')
                        }
                    else:
                        normalized[scenario] = results
        
        # Si on a des résultats directs
        elif hasattr(st.session_state, 'optimal_price'):
            normalized['Scénario actuel'] = {
                'prix_optimal': st.session_state.get('optimal_price', 0),
                'indicateurs_optimaux': {
                    'VAN': st.session_state.get('optimal_van', 0),
                    'TRI': st.session_state.get('optimal_tri', 0)
                }
            }
        
        storage_logger.log_data_inspection("optimization_results_normalized", normalized, "normalize")
        return normalized

class ProjectManager:
    """Gestionnaire de projets pour OptimPV"""
    
    def __init__(self, storage_module):
        self.storage = storage_module
    
    def save_current_project(self, project_name: str, description: str = "", tags: List[str] = None, is_favorite: bool = False) -> str:
        """
        Sauvegarde améliorée du projet avec capture complète des données
        
        Args:
            project_name: Nom du projet
            description: Description optionnelle
            tags: Tags optionnels
            is_favorite: Marquer comme favori
            
        Returns:
            ID du projet sauvegardé
        """
        try:
            # Générer un ID unique avec timestamp et nom
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_id = f"{timestamp}_{project_name.replace(' ', '_')}"
            project_dir = f"projects/{project_id}"
            
            # Créer le répertoire du projet
            os.makedirs(project_dir, exist_ok=True)
            
            # 1. Calculer les métriques du projet
            active_modules = self.storage.data_utils.get_active_modules()
            completeness = self.storage.data_utils.calculate_completeness_score()
            validation = self.storage.data_utils.validate_project_data()
            data_sizes = self.storage.data_utils.calculate_data_size()
            
            # 2. Créer le manifeste du projet
            manifest = {
                'name': project_name,
                'description': description,
                'tags': tags if tags else [],
                'is_favorite': is_favorite,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'storage_version': self.storage.storage_version,
                'data_size': data_sizes,
                'active_modules': active_modules,
                'completeness': completeness,
                'validation': validation,
                'python_version': sys.version,
                'streamlit_version': st.__version__
            }
            
            # 3. Sauvegarder l'état complet du session_state
            session_data = self.storage.data_utils.get_all_session_state_data()
            with open(os.path.join(project_dir, 'session_state_complete.json'), 'w') as f:
                json.dump(session_data, f, indent=4, default=self.storage.data_utils._json_serializer)
            
            # 4. Sauvegarder les visualisations
            visualizations_saved = self.save_visualizations_snapshot(project_dir)
            manifest['visualizations'] = visualizations_saved
            
            # 5. Configuration spécifique
            if 'config' in st.session_state and st.session_state.config:
                with open(os.path.join(project_dir, 'config.json'), 'w') as f:
                    json.dump(st.session_state.config, f, indent=4)
                manifest['has_config'] = True
            else:
                manifest['has_config'] = False
            
            # 6. Scénarios
            if 'scenarios' in st.session_state and st.session_state.scenarios:
                with open(os.path.join(project_dir, 'scenarios.json'), 'w') as f:
                    json.dump(st.session_state.scenarios, f, indent=4)
                manifest['has_scenarios'] = True
            else:
                manifest['has_scenarios'] = False
            
            # 7. Données de production/consommation
            self._save_energy_data(project_dir, manifest)
            
            # 8. Résultats économiques (format amélioré)
            self._save_economic_results(project_dir, manifest)
            
            # 9. Résultats d'optimisation (format amélioré)
            self._save_optimization_results(project_dir, manifest)
            
            # 10. Résultats Monte Carlo
            self._save_monte_carlo_results(project_dir, manifest)
            
            # 11. Générer les checksums pour l'intégrité
            checksums = self.generate_file_checksums(project_dir)
            manifest['file_checksums'] = checksums
            
            # 12. Créer un README automatique
            self.generate_project_readme(project_dir, manifest)
            
            # Sauvegarder le manifeste enrichi
            with open(os.path.join(project_dir, 'manifest.json'), 'w') as f:
                json.dump(manifest, f, indent=4, default=self.storage.data_utils._json_serializer)
            
            # Mettre à jour l'historique
            st.session_state.project_history[project_id] = manifest
            
            logger.info(f"Projet {project_id} sauvegardé avec succès")
            return project_id
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde : {e}")
            # Nettoyer en cas d'erreur
            if os.path.exists(project_dir):
                shutil.rmtree(project_dir)
            raise e
    
    def load_project(self, project_id: str) -> bool:
        """
        Charge un projet sauvegardé (version améliorée)
        
        Args:
            project_id: ID du projet à charger
            
        Returns:
            True si le chargement a réussi
        """
        try:
            project_dir = f"projects/{project_id}"
            manifest_path = os.path.join(project_dir, 'manifest.json')
            
            if not os.path.exists(manifest_path):
                st.error(f"❌ Projet {project_id} introuvable")
                return False
            
            # Charger le manifeste
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Vérifier l'intégrité des fichiers si disponible
            if 'file_checksums' in manifest:
                if not self.verify_file_integrity(project_dir, manifest['file_checksums']):
                    st.warning("⚠️ Certains fichiers du projet semblent corrompus")
            
            # Charger l'état complet du session_state si disponible
            session_state_path = os.path.join(project_dir, 'session_state_complete.json')
            if os.path.exists(session_state_path):
                with open(session_state_path, 'r') as f:
                    data = json.load(f)
                
                # Charger dans le session_state
                for key, value in data.items():
                    if not key.endswith('_pickled'):
                        st.session_state[key] = value
                
                # Traitement des données pickled
                import pickle
                import base64
                for key, value in data.items():
                    if key.endswith('_pickled'):
                        original_key = key[:-8]  # Retirer '_pickled'
                        try:
                            decoded_data = base64.b64decode(value)
                            st.session_state[original_key] = pickle.loads(decoded_data)
                        except:
                            logger.warning(f"Impossible de décoder les données pickled pour {original_key}")
            
            # Chargements spécifiques pour compatibilité
            self._load_specific_data(project_dir, manifest)
            
            # Recalculer et sauvegarder l'état après chargement
            updated_completeness = self.storage.data_utils.calculate_completeness_score()
            manifest['completeness'] = updated_completeness
            manifest['current_state'] = {
                'data_imported': updated_completeness['components']['data_imported'],
                'optimization_done': updated_completeness['components']['optimization_done'],
                'economic_analysis': updated_completeness['components']['economic_analysis']
            }
            
            # Sauvegarder le manifeste mis à jour
            try:
                with open(manifest_path, 'w', encoding='utf-8') as f:
                    json.dump(manifest, f, indent=2, ensure_ascii=False, default=self.storage.data_utils._json_serializer)
            except Exception as save_error:
                logger.warning(f"Impossible de sauvegarder le manifeste mis à jour: {save_error}")
            
            # Mettre à jour l'historique des projets
            st.session_state.project_history[project_id] = manifest
            
            # Afficher un résumé du chargement
            st.success(f"✅ Projet chargé avec succès!")
            if manifest.get('storage_version') == '2.0':
                st.info(f"📊 Sauvegarde améliorée - Score: {manifest.get('completeness', {}).get('score', 0)}% - Taille: {manifest.get('data_size', {}).get('total_size_mb', 0)} MB")
            
            return True
            
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement du projet : {str(e)}")
            logger.error(f"Erreur chargement projet {project_id} : {e}")
            return False
    
    def delete_project(self, project_id: str) -> bool:
        """Supprime un projet de manière sécurisée"""
        try:
            project_dir = f"projects/{project_id}"
            
            if not os.path.exists(project_dir):
                return False
            
            # Supprimer le répertoire
            shutil.rmtree(project_dir)
            
            # Mettre à jour l'historique
            if project_id in st.session_state.project_history:
                del st.session_state.project_history[project_id]
            
            logger.info(f"Projet {project_id} supprimé")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du projet {project_id}: {e}")
            return False
    
    def export_project(self, project_id: str) -> Optional[bytes]:
        """Exporte un projet au format ZIP"""
        try:
            project_dir = f"projects/{project_id}"
            
            if not os.path.exists(project_dir):
                return None
            
            # Créer un ZIP en mémoire
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Ajouter tous les fichiers du projet
                for root, dirs, files in os.walk(project_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, project_dir)
                        zipf.write(file_path, arcname)
            
            return zip_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export du projet {project_id}: {e}")
            return None
    
    def import_project(self, zip_file, new_name: str = None) -> Optional[str]:
        """Importe un projet depuis un fichier ZIP"""
        try:
            # Créer un répertoire temporaire
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extraire le ZIP
                with zipfile.ZipFile(zip_file, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Chercher le manifeste
                manifest_path = os.path.join(temp_dir, 'manifest.json')
                if not os.path.exists(manifest_path):
                    st.error("❌ Fichier projet invalide (manifest.json manquant)")
                    return None
                
                # Charger et modifier le manifeste
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                # Générer un nouvel ID
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                original_name = new_name if new_name else manifest.get('name', 'Projet_Importé')
                project_id = f"{timestamp}_{original_name.replace(' ', '_')}"
                
                # Mettre à jour le manifeste
                manifest['name'] = original_name
                manifest['imported_at'] = datetime.now().isoformat()
                manifest['original_id'] = manifest.get('id', 'unknown')
                
                # Créer le nouveau répertoire projet
                new_project_dir = f"projects/{project_id}"
                shutil.copytree(temp_dir, new_project_dir)
                
                # Sauvegarder le manifeste modifié
                with open(os.path.join(new_project_dir, 'manifest.json'), 'w') as f:
                    json.dump(manifest, f, indent=4, default=self.storage.data_utils._json_serializer)
                
                # Mettre à jour l'historique
                st.session_state.project_history[project_id] = manifest
                
                logger.info(f"Projet importé avec l'ID {project_id}")
                return project_id
                
        except Exception as e:
            logger.error(f"Erreur lors de l'import du projet: {e}")
            st.error(f"❌ Erreur lors de l'import: {str(e)}")
            return None
    
    # Méthodes utilitaires privées
    
    def _save_energy_data(self, project_dir: str, manifest: Dict[str, Any]):
        """Sauvegarde les données énergétiques"""
        # Sites data (nouveau format)
        if 'sites' in st.session_state and st.session_state.sites:
            with open(os.path.join(project_dir, 'sites_data.json'), 'w') as f:
                json.dump(st.session_state.sites, f, indent=4, default=self.storage.data_utils._json_serializer)
            manifest['has_sites_data'] = True
        else:
            manifest['has_sites_data'] = False
        
        # Production data (ancien format pour compatibilité)
        if 'production_data' in st.session_state and st.session_state.production_data is not None:
            st.session_state.production_data.to_csv(os.path.join(project_dir, 'production_data.csv'), index=False)
            manifest['has_production_data'] = True
            manifest['has_consumption_data'] = False
        else:
            manifest['has_production_data'] = False
            manifest['has_consumption_data'] = False
        
        if 'processed_data' in st.session_state and st.session_state.processed_data is not None:
            st.session_state.processed_data.to_csv(os.path.join(project_dir, 'processed_data.csv'), index=False)
            manifest['has_processed_data'] = True
        else:
            manifest['has_processed_data'] = False
    
    def _save_economic_results(self, project_dir: str, manifest: Dict[str, Any]):
        """Sauvegarde les résultats économiques avec format amélioré et logging"""
        from .debug_logger import storage_logger
        
        try:
            storage_logger.log_operation("save_economic_results", {
                'project_dir': project_dir,
                'has_economic_results': 'economic_results' in st.session_state
            })
            
            # Collecter toutes les sources possibles de résultats économiques
            raw_data = None
            
            # Priorité 1 : economic_results
            if 'economic_results' in st.session_state and st.session_state.economic_results:
                raw_data = st.session_state.economic_results
                storage_logger.log_data_inspection("economic_results_source", raw_data, "save")
            
            # Priorité 2 : autres clés possibles
            elif any(hasattr(st.session_state, key) for key in ['economic_analysis_results', 'analysis_results']):
                for key in ['economic_analysis_results', 'analysis_results']:
                    if hasattr(st.session_state, key) and getattr(st.session_state, key):
                        raw_data = getattr(st.session_state, key)
                        storage_logger.log_data_inspection(f"{key}_source", raw_data, "save")
                        break
            
            # Normaliser les données
            if raw_data is not None:
                normalized_data = DataNormalizer.normalize_economic_results(raw_data)
            else:
                normalized_data = DataNormalizer.normalize_economic_results(None)
            
            if normalized_data:
                # Sauvegarder avec gestion d'erreur
                try:
                    with open(os.path.join(project_dir, 'economic_results.json'), 'w') as f:
                        json.dump(normalized_data, f, indent=4, default=self.storage.data_utils._json_serializer)
                    
                    manifest['has_economic_results'] = True
                    storage_logger.log_operation("save_economic_results", {
                        'scenarios_count': len(normalized_data),
                        'scenarios': list(normalized_data.keys())
                    }, status="SUCCESS")
                    
                except Exception as e:
                    storage_logger.log_error("save_economic_results_write", e, {
                        'data_keys': list(normalized_data.keys()) if normalized_data else []
                    })
                    manifest['has_economic_results'] = False
            else:
                manifest['has_economic_results'] = False
                storage_logger.log_operation("save_economic_results", {
                    'result': 'no_data'
                }, status="WARNING")
                
        except Exception as e:
            storage_logger.log_error("save_economic_results", e)
            manifest['has_economic_results'] = False
    
    def _save_optimization_results(self, project_dir: str, manifest: Dict[str, Any]):
        """Sauvegarde les résultats d'optimisation avec format amélioré et logging"""
        from .debug_logger import storage_logger
        
        try:
            storage_logger.log_operation("save_optimization_results", {
                'project_dir': project_dir,
                'has_optimization_results': 'optimization_results' in st.session_state,
                'has_constrained_results': 'constrained_optim_results' in st.session_state
            })
            
            # Collecter toutes les sources
            raw_data = None
            
            # Vérifier les différentes sources
            for key in ['optimization_results', 'constrained_optim_results', 'optim_results']:
                if hasattr(st.session_state, key) and getattr(st.session_state, key):
                    raw_data = getattr(st.session_state, key)
                    storage_logger.log_data_inspection(f"{key}_source", raw_data, "save")
                    break
            
            # Normaliser
            if raw_data is not None:
                normalized_data = DataNormalizer.normalize_optimization_results(raw_data)
            else:
                normalized_data = DataNormalizer.normalize_optimization_results(None)
            
            if normalized_data:
                try:
                    # Sauvegarder dans un format unifié
                    with open(os.path.join(project_dir, 'optimization_results_unified.json'), 'w') as f:
                        json.dump(normalized_data, f, indent=4, default=self.storage.data_utils._json_serializer)
                    
                    manifest['has_optimization_results'] = True
                    manifest['optimization_format'] = 'unified'
                    
                    storage_logger.log_operation("save_optimization_results", {
                        'scenarios_count': len(normalized_data),
                        'scenarios': list(normalized_data.keys())
                    }, status="SUCCESS")
                    
                except Exception as e:
                    storage_logger.log_error("save_optimization_results_write", e)
                    manifest['has_optimization_results'] = False
            else:
                manifest['has_optimization_results'] = False
                storage_logger.log_operation("save_optimization_results", {
                    'result': 'no_data'
                }, status="WARNING")
                
        except Exception as e:
            storage_logger.log_error("save_optimization_results", e)
            manifest['has_optimization_results'] = False
    
    def _save_monte_carlo_results(self, project_dir: str, manifest: Dict[str, Any]):
        """Sauvegarde les résultats Monte Carlo"""
        if 'monte_carlo_results' in st.session_state and st.session_state.monte_carlo_results:
            with open(os.path.join(project_dir, 'monte_carlo_results.json'), 'w') as f:
                # Convertir les données pour la sérialisation JSON
                monte_carlo_results = {}
                for scenario, results in st.session_state.monte_carlo_results.items():
                    monte_carlo_results[scenario] = {
                        'scenario_name': results['scenario_name'],
                        'prix_revente': results['prix_revente'],
                        'n_iterations': results['n_iterations'],
                        'ecart_type_production': results['ecart_type_production'],
                        'ecart_type_consommation': results['ecart_type_consommation'],
                        'statistics': results['statistics'],
                        'probabilities': results['probabilities']
                    }
                json.dump(monte_carlo_results, f, indent=4)
            manifest['has_monte_carlo_results'] = True
        else:
            manifest['has_monte_carlo_results'] = False
    
    def _load_specific_data(self, project_dir: str, manifest: Dict[str, Any]):
        """Charge des données spécifiques pour compatibilité"""
        
        # 1. Charger la configuration
        config_path = os.path.join(project_dir, 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                st.session_state.config = json.load(f)
        
        # 2. Charger les scénarios
        scenarios_path = os.path.join(project_dir, 'scenarios.json')
        if os.path.exists(scenarios_path):
            with open(scenarios_path, 'r') as f:
                st.session_state.scenarios = json.load(f)
        
        # 3. Charger les données de sites
        sites_data_path = os.path.join(project_dir, 'sites_data.json')
        if os.path.exists(sites_data_path):
            with open(sites_data_path, 'r') as f:
                st.session_state.sites = json.load(f)
        
        # 4. Charger les résultats économiques
        economic_path = os.path.join(project_dir, 'economic_results.json')
        if os.path.exists(economic_path):
            with open(economic_path, 'r') as f:
                economic_data = json.load(f)
                # Reconstituer les DataFrames si nécessaire
                for scenario, results in economic_data.items():
                    if isinstance(results, dict) and 'monthly_data' in results:
                        if isinstance(results['monthly_data'], list):
                            # Convertir back en DataFrame
                            results['monthly_data'] = pd.DataFrame(results['monthly_data'])
                            # Convertir l'index en datetime si nécessaire
                            if 'Temps' in results['monthly_data'].columns:
                                results['monthly_data']['Temps'] = pd.to_datetime(results['monthly_data']['Temps'])
                                results['monthly_data'].set_index('Temps', inplace=True)
                st.session_state.economic_results = economic_data
        
        # 5. Charger les résultats d'optimisation (ancien format)
        optimization_path = os.path.join(project_dir, 'optimization_results.json')
        if os.path.exists(optimization_path):
            with open(optimization_path, 'r') as f:
                optimization_data = json.load(f)
                st.session_state.optimization_results = optimization_data
                
                # Marquer l'optimisation comme terminée
                st.session_state.optimization_completed = True
        
        # 5b. Charger les résultats d'optimisation contrainte (nouveau format)
        constrained_optimization_path = os.path.join(project_dir, 'constrained_optim_results.json')
        if os.path.exists(constrained_optimization_path):
            with open(constrained_optimization_path, 'r') as f:
                constrained_optimization_data = json.load(f)
                st.session_state.constrained_optim_results = constrained_optimization_data
                
                # Marquer l'optimisation contrainte comme terminée
                st.session_state.optimization_completed = True
        
        # 6. Charger les résultats Monte Carlo
        monte_carlo_path = os.path.join(project_dir, 'monte_carlo_results.json')
        if os.path.exists(monte_carlo_path):
            with open(monte_carlo_path, 'r') as f:
                st.session_state.monte_carlo_results = json.load(f)
    
    def save_visualizations_snapshot(self, project_dir: str) -> Dict[str, bool]:
        """Sauvegarde les visualisations comme images et tableaux"""
        saved_visualizations = {}
        
        try:
            viz_dir = os.path.join(project_dir, 'visualizations')
            os.makedirs(viz_dir, exist_ok=True)
            
            # Sauvegarder les graphiques Plotly en HTML et PNG si possible
            for key, value in st.session_state.items():
                if key.startswith('chart_') or key.startswith('fig_'):
                    try:
                        if hasattr(value, 'write_html'):
                            # C'est un graphique Plotly
                            html_path = os.path.join(viz_dir, f"{key}.html")
                            value.write_html(html_path)
                            saved_visualizations[key] = True
                        elif isinstance(value, pd.DataFrame):
                            # C'est un DataFrame - sauvegarder en Excel
                            excel_path = os.path.join(viz_dir, f"{key}.xlsx")
                            value.to_excel(excel_path, index=True)
                            saved_visualizations[key] = True
                    except Exception as e:
                        logger.warning(f"Impossible de sauvegarder la visualisation {key}: {e}")
                        saved_visualizations[key] = False
            
        except Exception as e:
            logger.warning(f"Erreur lors de la sauvegarde des visualisations: {e}")
        
        return saved_visualizations
    
    def generate_file_checksums(self, project_dir: str) -> Dict[str, str]:
        """Génère les checksums des fichiers pour vérification d'intégrité"""
        checksums = {}
        
        try:
            for root, dirs, files in os.walk(project_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, project_dir)
                    
                    # Calculer le checksum MD5
                    hash_md5 = hashlib.md5()
                    with open(file_path, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hash_md5.update(chunk)
                    
                    checksums[relative_path] = hash_md5.hexdigest()
        
        except Exception as e:
            logger.warning(f"Erreur lors du calcul des checksums: {e}")
        
        return checksums
    
    def verify_file_integrity(self, project_dir: str, expected_checksums: Dict[str, str]) -> bool:
        """Vérifie l'intégrité des fichiers avec les checksums"""
        for rel_path, expected_checksum in expected_checksums.items():
            file_path = os.path.join(project_dir, rel_path)
            
            if not os.path.exists(file_path):
                logger.warning(f"Fichier manquant: {rel_path}")
                return False
            
            # Calculer le checksum actuel
            hash_md5 = hashlib.md5()
            try:
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_md5.update(chunk)
                
                actual_checksum = hash_md5.hexdigest()
                
                if actual_checksum != expected_checksum:
                    logger.warning(f"Checksum incorrect pour {rel_path}")
                    return False
                    
            except Exception as e:
                logger.warning(f"Erreur de lecture pour {rel_path}: {e}")
                return False
        
        return True
    
    def generate_project_readme(self, project_dir: str, manifest: Dict[str, Any]):
        """Génère un README automatique pour le projet"""
        try:
            readme_content = f"""# {manifest['name']}

## Description
{manifest.get('description', 'Aucune description fournie')}

## Informations du projet
- **Créé le**: {manifest['created_at']}
- **Dernière modification**: {manifest['updated_at']}
- **Version de stockage**: {manifest['storage_version']}
- **Taille des données**: {manifest.get('data_size', {}).get('total_size_mb', 0)} MB

## Score de complétude: {manifest.get('completeness', {}).get('score', 0)}%

### État des modules:
"""
            
            # Ajouter l'état des composants
            components = manifest.get('completeness', {}).get('components', {})
            for component, status in components.items():
                status_icon = "✅" if status else "❌"
                readme_content += f"- {status_icon} **{component.replace('_', ' ').title()}**\n"
            
            readme_content += f"\n## Modules actifs\n"
            for module in manifest.get('active_modules', []):
                readme_content += f"- {module}\n"
            
            # Ajouter les informations sur les visualisations
            if manifest.get('visualizations'):
                readme_content += f"\n## Visualisations sauvegardées: {len(manifest['visualizations'])}\n"
            
            # Ajouter les tags si présents
            if manifest.get('tags'):
                readme_content += f"\n## Tags\n"
                for tag in manifest['tags']:
                    readme_content += f"- {tag}\n"
            
            readme_content += f"\n---\n*README généré automatiquement par OptimPV {manifest['storage_version']}*"
            
            # Sauvegarder le README
            with open(os.path.join(project_dir, 'README.md'), 'w', encoding='utf-8') as f:
                f.write(readme_content)
                
        except Exception as e:
            logger.warning(f"Erreur lors de la génération du README: {e}")