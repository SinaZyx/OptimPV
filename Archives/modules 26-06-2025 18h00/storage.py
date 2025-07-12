import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import io
import glob
from datetime import datetime, timedelta
import shutil
import sys
import logging
import hashlib
import pickle
import base64
from typing import Dict, Any, List, Optional, Tuple
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Activer les logs de debug pour le diagnostic
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class StorageModule:
    """
    Version 2.0 du module de stockage avec interface Hub de Projets
    - Interface unifiée et intuitive
    - Comparaison intelligente de projets
    - Visualisations graphiques avancées
    """
    
    def __init__(self):
        # Créer le répertoire 'projects' s'il n'existe pas
        if not os.path.exists('projects'):
            os.makedirs('projects')
        
        # Initialiser les structures de données si elles n'existent pas
        if 'project_history' not in st.session_state:
            self.load_project_history()
        
        # État de l'interface
        if 'storage_ui_state' not in st.session_state:
            st.session_state.storage_ui_state = {
                'comparison_mode': False,
                'first_project_id': None,
                'filter_search': '',
                'filter_tags': [],
                'filter_favorites_only': False,
                'show_save_dialog': False
            }
        
        # Version du système de sauvegarde
        self.storage_version = "2.0"
        
        # Clés à exclure de la sauvegarde automatique
        self.excluded_keys = {
            '_streamlit_internal', 'auth_status', 'password_verified',
            'project_history', 'temp_data', 'ui_state', 'storage_ui_state'
        }
        
        # Préfixes de clés à exclure
        self.excluded_prefixes = {'nav_', 'ui_', '_st'}
    
    def load_project_history(self):
        """Charge l'historique des projets depuis le système de fichiers"""
        st.session_state.project_history = {}
        
        # Parcourir les projets sauvegardés
        project_dirs = glob.glob('projects/*')
        for project_dir in project_dirs:
            if os.path.isdir(project_dir):
                project_id = os.path.basename(project_dir)
                
                # Vérifier s'il y a un fichier manifest.json
                manifest_path = os.path.join(project_dir, 'manifest.json')
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                        
                        # Ajouter le projet à l'historique
                        st.session_state.project_history[project_id] = manifest
                    except:
                        # Ignorer les projets avec un manifest corrompu
                        continue
    
    def show_ui(self):
        """Interface principale du Hub de Projets"""
        st.markdown("""
        <style>
        .project-card {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .project-card:hover {
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        }
        .metric-container {
            display: flex;
            justify-content: space-around;
            margin: 15px 0;
        }
        .action-buttons {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .module-badge {
            display: inline-block;
            padding: 3px 8px;
            margin: 2px;
            border-radius: 15px;
            font-size: 0.8em;
            background-color: #e1e4e8;
        }
        .module-badge.active {
            background-color: #28a745;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # En-tête avec actions principales
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if st.button("➕ Sauvegarder le projet actuel", type="primary", use_container_width=True):
                st.session_state.storage_ui_state['show_save_dialog'] = True
        
        with col2:
            uploaded_file = st.file_uploader("⬆️ Importer un projet (ZIP)", type=["zip"], label_visibility="collapsed")
            if uploaded_file:
                self._handle_import(uploaded_file)
        
        with col3:
            if st.button("🔄 Actualiser", use_container_width=True):
                self.load_project_history()
                st.rerun()
        
        # Barre de filtrage
        st.markdown("---")
        filter_col1, filter_col2, filter_col3 = st.columns([3, 2, 1])
        
        with filter_col1:
            st.session_state.storage_ui_state['filter_search'] = st.text_input(
                "🔍 Rechercher", 
                value=st.session_state.storage_ui_state['filter_search'],
                placeholder="Nom du projet, description..."
            )
        
        with filter_col2:
            # TODO: Implémenter système de tags
            pass
        
        with filter_col3:
            st.session_state.storage_ui_state['filter_favorites_only'] = st.checkbox(
                "⭐ Favoris",
                value=st.session_state.storage_ui_state['filter_favorites_only']
            )
        
        # Afficher le dialogue de sauvegarde si demandé
        if st.session_state.storage_ui_state.get('show_save_dialog', False):
            self._show_save_dialog()
        
        # Affichage des projets sous forme de cartes
        self._display_project_cards()
    
    def _display_project_cards(self):
        """Affiche les projets sous forme de cartes visuelles"""
        # Filtrer les projets
        filtered_projects = self._filter_projects()
        
        if not filtered_projects:
            st.info("Aucun projet trouvé. Créez votre premier projet en utilisant le bouton 'Sauvegarder' ci-dessus.")
            return
        
        # Mode comparaison activé ?
        comparison_mode = st.session_state.storage_ui_state['comparison_mode']
        first_project_id = st.session_state.storage_ui_state['first_project_id']
        
        # Afficher les projets
        for project_id, manifest in filtered_projects:
            self._display_single_project_card(project_id, manifest, comparison_mode, first_project_id)
    
    def _display_single_project_card(self, project_id: str, manifest: dict, comparison_mode: bool, first_project_id: str):
        """Affiche une carte de projet unique"""
        # Conteneur principal de la carte
        with st.container():
            st.markdown('<div class="project-card">', unsafe_allow_html=True)
            
            # En-tête de la carte
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Nom et description
                is_favorite = manifest.get('is_favorite', False)
                favorite_icon = "⭐" if is_favorite else ""
                st.markdown(f"### {favorite_icon} {manifest['name']}")
                if manifest.get('description'):
                    st.caption(manifest['description'])
            
            with col2:
                # Bouton favori
                if st.button("⭐" if not is_favorite else "★", 
                           key=f"fav_{project_id}",
                           help="Marquer comme favori"):
                    self._toggle_favorite(project_id)
            
            # Métriques principales
            col1, col2, col3 = st.columns(3)
            
            with col1:
                completeness_score = manifest.get('completeness', {}).get('score', 0)
                st.metric("📊 Complétude", f"{completeness_score}%")
            
            with col2:
                quality_score = manifest.get('validation', {}).get('data_quality_score', 100)
                st.metric("🔍 Qualité", f"{quality_score}%")
            
            with col3:
                size_mb = manifest.get('data_size', {}).get('total_size_mb', 0)
                st.metric("💾 Taille", f"{size_mb:.1f} MB")
            
            # Modules actifs
            st.markdown("**Modules:**")
            modules_html = ""
            components = manifest.get('completeness', {}).get('components', {})
            
            module_mapping = {
                'data_imported': ('Données', '📊'),
                'config_set': ('Config', '⚙️'),
                'scenarios_defined': ('Scénarios', '🎭'),
                'economic_analysis': ('Économie', '💰'),
                'optimization_done': ('Optimisation', '⚡'),
                'monte_carlo_done': ('Monte Carlo', '🎲')
            }
            
            for key, (label, icon) in module_mapping.items():
                is_active = components.get(key, False)
                class_name = "module-badge active" if is_active else "module-badge"
                modules_html += f'<span class="{class_name}">{icon} {label}</span>'
            
            st.markdown(modules_html, unsafe_allow_html=True)
            
            # Boutons d'action
            if not comparison_mode:
                # Mode normal
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    if st.button("▶️ Charger", key=f"load_{project_id}", use_container_width=True):
                        self._load_project(project_id)
                
                with col2:
                    if st.button("🗑️ Supprimer", key=f"delete_{project_id}", use_container_width=True):
                        self._delete_project(project_id)
                
                with col3:
                    if st.button("⬇️ Exporter", key=f"export_{project_id}", use_container_width=True):
                        self._export_project(project_id)
                
                with col4:
                    if st.button("📋 Dupliquer", key=f"duplicate_{project_id}", use_container_width=True):
                        self._duplicate_project(project_id)
                
                with col5:
                    if st.button("✨ Comparer", key=f"compare_{project_id}", use_container_width=True):
                        st.session_state.storage_ui_state['comparison_mode'] = True
                        st.session_state.storage_ui_state['first_project_id'] = project_id
                        st.rerun()
            
            elif project_id == first_project_id:
                # Projet sélectionné pour comparaison
                st.info("📍 Projet sélectionné pour comparaison")
                if st.button("❌ Annuler la comparaison", key=f"cancel_{project_id}", use_container_width=True):
                    st.session_state.storage_ui_state['comparison_mode'] = False
                    st.session_state.storage_ui_state['first_project_id'] = None
                    st.rerun()
            
            else:
                # Mode comparaison - autres projets
                if st.button("🎯 Comparer avec celui-ci", key=f"compare_with_{project_id}", type="primary", use_container_width=True):
                    self._show_comparison_dashboard(first_project_id, project_id)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def _filter_projects(self) -> List[Tuple[str, dict]]:
        """Filtre les projets selon les critères définis"""
        filtered = []
        search_term = st.session_state.storage_ui_state['filter_search'].lower()
        favorites_only = st.session_state.storage_ui_state['filter_favorites_only']
        
        for project_id, manifest in st.session_state.project_history.items():
            # Filtre favoris
            if favorites_only and not manifest.get('is_favorite', False):
                continue
            
            # Filtre recherche
            if search_term:
                searchable_text = f"{manifest.get('name', '')} {manifest.get('description', '')}".lower()
                if search_term not in searchable_text:
                    continue
            
            filtered.append((project_id, manifest))
        
        # Trier par date de modification décroissante
        filtered.sort(key=lambda x: x[1].get('updated_at', ''), reverse=True)
        
        return filtered
    
    def _show_save_dialog(self):
        """Affiche la boîte de dialogue de sauvegarde"""
        with st.container():
            st.markdown("---")
            st.markdown("### 💾 Sauvegarder le projet actuel")
            
            # Générer un nom par défaut
            default_name = f"Projet_{datetime.now().strftime('%Y%m%d_%H%M')}"
            
            # Utiliser des clés uniques pour éviter les conflits
            name = st.text_input("Nom du projet", value=default_name, key="save_project_name_input")
            description = st.text_area("Description (optionnel)", height=100, key="save_project_description_input")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Sauvegarder", type="primary", use_container_width=True, key="confirm_save_button"):
                    if name.strip():
                        try:
                            with st.spinner("Sauvegarde en cours..."):
                                project_id = self.save_current_project(name.strip(), description.strip())
                                
                                if project_id:
                                    st.success(f"✅ Projet sauvegardé avec succès! (ID: {project_id})")
                                    # Fermer le dialogue et actualiser
                                    st.session_state.storage_ui_state['show_save_dialog'] = False
                                    self.load_project_history()
                                    st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la sauvegarde : {str(e)}")
                    else:
                        st.error("Le nom du projet ne peut pas être vide")
            
            with col2:
                if st.button("❌ Annuler", use_container_width=True, key="cancel_save_button"):
                    st.session_state.storage_ui_state['show_save_dialog'] = False
                    st.rerun()
            
            with col3:
                st.empty()  # Colonne vide pour l'espacement
            
            st.markdown("---")
    
    def _toggle_favorite(self, project_id: str):
        """Bascule le statut favori d'un projet"""
        manifest_path = os.path.join('projects', project_id, 'manifest.json')
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            manifest['is_favorite'] = not manifest.get('is_favorite', False)
            
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=4)
            
            self.load_project_history()
            st.rerun()
    
    def _load_project(self, project_id: str):
        """Charge un projet"""
        success = self.load_project(project_id)
        if success:
            st.rerun()
    
    def _delete_project(self, project_id: str):
        """Supprime un projet avec confirmation"""
        manifest = st.session_state.project_history.get(project_id, {})
        project_name = manifest.get('name', 'Sans nom')
        
        # Demander confirmation
        if st.session_state.get(f'confirm_delete_{project_id}', False):
            if self.delete_project(project_id):
                st.success(f"✅ Projet '{project_name}' supprimé avec succès")
                self.load_project_history()
                st.rerun()
        else:
            st.session_state[f'confirm_delete_{project_id}'] = True
            st.warning(f"⚠️ Êtes-vous sûr de vouloir supprimer '{project_name}' ? Cliquez à nouveau pour confirmer.")
    
    def _export_project(self, project_id: str):
        """Exporte un projet"""
        export_data = self.export_project(project_id)
        
        if export_data:
            manifest = st.session_state.project_history.get(project_id, {})
            project_name = manifest.get('name', 'projet')
            
            st.download_button(
                label="📥 Télécharger le fichier ZIP",
                data=export_data,
                file_name=f"{project_name.replace(' ', '_')}_export.zip",
                mime="application/zip"
            )
    
    def _duplicate_project(self, project_id: str):
        """Duplique un projet"""
        manifest = st.session_state.project_history.get(project_id, {})
        original_name = manifest.get('name', 'Sans nom')
        
        with st.form(f"duplicate_form_{project_id}"):
            new_name = st.text_input("Nouveau nom", value=f"{original_name} - Copie")
            
            if st.form_submit_button("Dupliquer"):
                # Exporter puis réimporter avec nouveau nom
                export_data = self.export_project(project_id)
                if export_data:
                    new_id = self.import_project(export_data, new_name)
                    if new_id:
                        st.success(f"✅ Projet dupliqué avec succès! (ID: {new_id})")
                        self.load_project_history()
                        st.rerun()
    
    def _handle_import(self, uploaded_file):
        """Gère l'import d'un projet"""
        with st.form("import_form"):
            new_name = st.text_input("Nom du projet (optionnel)")
            
            if st.form_submit_button("Importer"):
                project_id = self.import_project(uploaded_file, new_name)
                if project_id:
                    st.success(f"✅ Projet importé avec succès! (ID: {project_id})")
                    self.load_project_history()
                    st.rerun()
    
    def _show_comparison_dashboard(self, project_id1: str, project_id2: str):
        """Affiche le dashboard de comparaison détaillé"""
        # Réinitialiser l'état de comparaison
        st.session_state.storage_ui_state['comparison_mode'] = False
        st.session_state.storage_ui_state['first_project_id'] = None
        
        # Charger les données complètes des deux projets
        comparison_data = self.compare_projects_advanced(project_id1, project_id2)
        
        if not comparison_data:
            st.error("Erreur lors de la comparaison des projets")
            return
        
        # Afficher le dashboard
        manifest1 = comparison_data['manifest1']
        manifest2 = comparison_data['manifest2']
        
        st.markdown(f"## 📊 Comparaison : {manifest1['name']} vs {manifest2['name']}")
        
        # Créer des onglets pour organiser la comparaison
        tabs = st.tabs(["📈 Synthèse", "⚙️ Configuration", "💰 Économie", "⚡ Optimisation", "🎲 Monte Carlo"])
        
        with tabs[0]:
            self._show_synthesis_comparison(comparison_data)
        
        with tabs[1]:
            self._show_config_comparison(comparison_data)
        
        with tabs[2]:
            self._show_economic_comparison(comparison_data)
        
        with tabs[3]:
            self._show_optimization_comparison(comparison_data)
        
        with tabs[4]:
            self._show_monte_carlo_comparison(comparison_data)
    
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
        
        # Analyser les changements de configuration
        for key in set(config1.keys()) | set(config2.keys()):
            val1 = config1.get(key)
            val2 = config2.get(key)
            
            if val1 != val2:
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
                key in self.excluded_keys or
                any(key.startswith(prefix) for prefix in self.excluded_prefixes)
            )
            
            if not should_exclude and self._is_serializable(value):
                try:
                    # Tentative de sérialisation pour vérifier
                    json.dumps(value, default=self._json_serializer)
                    all_data[key] = value
                except (TypeError, ValueError):
                    # Si non sérialisable en JSON, essayer pickle
                    try:
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
        except:
            return False
    
    def _json_serializer(self, obj):
        """Sérialiseur personnalisé pour JSON"""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return str(obj)
        else:
            return str(obj)
    
    def calculate_data_size(self) -> Dict[str, Any]:
        """Calcule la taille des données du projet"""
        sizes = {}
        total_size = 0
        
        for key, value in st.session_state.items():
            if key not in self.excluded_keys:
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
        
        if 'production_data' in st.session_state:
            modules.append('data_import')
        if 'config' in st.session_state:
            modules.append('configuration')
        if 'economic_results' in st.session_state:
            modules.append('economic_analysis')
        if 'optimization_results' in st.session_state:
            modules.append('optimization')
        if 'monte_carlo_results' in st.session_state:
            modules.append('monte_carlo')
        if any(key.startswith('chart_') for key in st.session_state.keys()):
            modules.append('visualization')
        
        return modules
    
    def calculate_completeness_score(self) -> Dict[str, Any]:
        """Calcule un score de complétude du projet"""
        components = {
            'data_imported': 'production_data' in st.session_state and st.session_state.get('production_data') is not None,
            'config_set': 'config' in st.session_state and bool(st.session_state.get('config')),
            'scenarios_defined': 'scenarios' in st.session_state and bool(st.session_state.get('scenarios')),
            'economic_analysis': 'economic_results' in st.session_state and bool(st.session_state.get('economic_results')),
            'optimization_done': 'optimization_results' in st.session_state and bool(st.session_state.get('optimization_results')),
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
        
        return validation_results
    
    def generate_file_checksums(self, project_dir: str) -> Dict[str, str]:
        """Génère les checksums des fichiers pour vérifier l'intégrité"""
        checksums = {}
        
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        checksum = hashlib.md5(content).hexdigest()
                        rel_path = os.path.relpath(file_path, project_dir)
                        checksums[rel_path] = checksum
                except:
                    continue
        
        return checksums
    
    def save_visualizations_snapshot(self, project_dir: str) -> Dict[str, bool]:
        """Sauvegarde les visualisations en tant qu'images"""
        saved_charts = {}
        charts_dir = os.path.join(project_dir, 'charts')
        os.makedirs(charts_dir, exist_ok=True)
        
        # Rechercher les graphiques Plotly dans session_state
        for key, value in st.session_state.items():
            if isinstance(value, go.Figure):
                try:
                    # Sauvegarder en HTML interactif
                    html_path = os.path.join(charts_dir, f"{key}.html")
                    value.write_html(html_path)
                    
                    # Sauvegarder en PNG statique
                    png_path = os.path.join(charts_dir, f"{key}.png")
                    value.write_image(png_path, width=1200, height=800)
                    
                    saved_charts[key] = True
                except Exception as e:
                    saved_charts[key] = False
        
        # Sauvegarder les DataFrames affichés comme tableaux Excel
        tables_dir = os.path.join(project_dir, 'tables')
        os.makedirs(tables_dir, exist_ok=True)
        
        for key, value in st.session_state.items():
            if isinstance(value, pd.DataFrame) and not value.empty:
                try:
                    excel_path = os.path.join(tables_dir, f"{key}.xlsx")
                    value.to_excel(excel_path, index=False)
                    saved_charts[f"table_{key}"] = True
                except:
                    saved_charts[f"table_{key}"] = False
        
        return saved_charts
    
    def save_current_project(self, project_name, description="", tags=None, is_favorite=False):
        """
        Sauvegarde améliorée du projet actuel avec capture exhaustive
        
        Args:
            project_name: Nom du projet
            description: Description du projet
            tags: Liste des tags
            is_favorite: Marquer comme favori
            
        Returns:
            str: ID du projet sauvegardé
        """
        # Validation préalable
        validation = self.validate_project_data()
        if not validation['is_valid']:
            raise ValueError(f"Validation échouée: {', '.join(validation['errors'])}")
        
        # Générer un ID unique pour le projet
        project_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{project_name.replace(' ', '_')}"
        
        # Créer le répertoire du projet
        project_dir = os.path.join('projects', project_id)
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        
        # Calculer les métadonnées avancées
        data_sizes = self.calculate_data_size()
        active_modules = self.get_active_modules()
        completeness = self.calculate_completeness_score()
        
        # Créer le manifeste enrichi
        manifest = {
            'name': project_name,
            'description': description,
            'tags': tags if tags else [],
            'is_favorite': is_favorite,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'storage_version': self.storage_version,
            'data_size': data_sizes,
            'active_modules': active_modules,
            'completeness': completeness,
            'validation': validation,
            'python_version': sys.version,
            'streamlit_version': st.__version__
        }
        
        # Sauvegarder les données du projet
        try:
            # 1. Sauvegarde exhaustive de session_state
            all_session_data = self.get_all_session_state_data()
            with open(os.path.join(project_dir, 'session_state_complete.json'), 'w') as f:
                json.dump(all_session_data, f, indent=4, default=self._json_serializer)
            manifest['has_complete_session'] = True
            
            # 2. Sauvegarde des visualisations
            saved_charts = self.save_visualizations_snapshot(project_dir)
            manifest['saved_visualizations'] = saved_charts
            
            # 3. Configuration (maintenir compatibilité)
            if 'config' in st.session_state:
                with open(os.path.join(project_dir, 'config.json'), 'w') as f:
                    json.dump(st.session_state.config, f, indent=4)
                manifest['has_config'] = True
            else:
                manifest['has_config'] = False
            
            # 4. Scénarios
            if 'scenarios' in st.session_state:
                with open(os.path.join(project_dir, 'scenarios.json'), 'w') as f:
                    json.dump(st.session_state.scenarios, f, indent=4)
                manifest['has_scenarios'] = True
            else:
                manifest['has_scenarios'] = False
            
            # 5. Données de production et consommation
            if 'production_data' in st.session_state and st.session_state.production_data is not None:
                st.session_state.production_data.to_csv(os.path.join(project_dir, 'production_data.csv'), index=False)
                manifest['has_production_data'] = True
            else:
                manifest['has_production_data'] = False
            
            if 'consumption_data' in st.session_state and st.session_state.consumption_data is not None:
                st.session_state.consumption_data.to_csv(os.path.join(project_dir, 'consumption_data.csv'), index=False)
                manifest['has_consumption_data'] = True
            else:
                manifest['has_consumption_data'] = False
            
            if 'processed_data' in st.session_state and st.session_state.processed_data is not None:
                st.session_state.processed_data.to_csv(os.path.join(project_dir, 'processed_data.csv'), index=False)
                manifest['has_processed_data'] = True
            else:
                manifest['has_processed_data'] = False
            
            # 6. Résultats économiques
            if 'economic_results' in st.session_state and st.session_state.economic_results:
                with open(os.path.join(project_dir, 'economic_results.json'), 'w') as f:
                    # Convertir les arrays numpy en listes pour la sérialisation JSON
                    economic_results = {}
                    for scenario, results in st.session_state.economic_results.items():
                        economic_results[scenario] = {k: v if not isinstance(v, np.ndarray) else v.tolist() for k, v in results.items()}
                    json.dump(economic_results, f, indent=4)
                manifest['has_economic_results'] = True
            else:
                manifest['has_economic_results'] = False
            
            # 7. Résultats d'optimisation
            if 'optimization_results' in st.session_state and st.session_state.optimization_results:
                with open(os.path.join(project_dir, 'optimization_results.json'), 'w') as f:
                    # Convertir les données pour la sérialisation JSON
                    optimization_results = {}
                    for scenario, results in st.session_state.optimization_results.items():
                        optimization_results[scenario] = {
                            'scenario_name': results['scenario_name'],
                            'prix_optimal': results['prix_optimal'],
                            'indicateurs_optimaux': {k: v if not isinstance(v, np.ndarray) else v.tolist() for k, v in results['indicateurs_optimaux'].items()},
                            'prix_testes': results['prix_testes']
                        }
                    json.dump(optimization_results, f, indent=4)
                manifest['has_optimization_results'] = True
            else:
                manifest['has_optimization_results'] = False
            
            # 8. Résultats Monte Carlo
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
            
            # 9. Générer les checksums pour l'intégrité
            checksums = self.generate_file_checksums(project_dir)
            manifest['file_checksums'] = checksums
            
            # 10. Créer un README automatique
            self.generate_project_readme(project_dir, manifest)
            
            # Sauvegarder le manifeste enrichi
            with open(os.path.join(project_dir, 'manifest.json'), 'w') as f:
                json.dump(manifest, f, indent=4, default=self._json_serializer)
            
            # Mettre à jour l'historique des projets
            st.session_state.project_history[project_id] = manifest
            
            return project_id
        
        except Exception as e:
            # En cas d'erreur, supprimer le répertoire du projet
            shutil.rmtree(project_dir, ignore_errors=True)
            raise e
    
    def generate_project_readme(self, project_dir: str, manifest: Dict[str, Any]):
        """Génère un README automatique pour le projet"""
        readme_content = f"""# {manifest['name']}

## Description
{manifest.get('description', 'Aucune description fournie')}

## Informations du Projet
- **Créé le**: {datetime.fromisoformat(manifest['created_at']).strftime('%d/%m/%Y à %H:%M')}
- **Version de sauvegarde**: {manifest.get('storage_version', 'N/A')}
- **Score de complétude**: {manifest.get('completeness', {}).get('score', 0)}%
- **Taille des données**: {manifest.get('data_size', {}).get('total_size_mb', 0)} MB

## Modules Actifs
{", ".join(manifest.get('active_modules', []))}

## Contenu du Projet

### Données Disponibles
- Configuration: {'✅' if manifest.get('has_config') else '❌'}
- Scénarios: {'✅' if manifest.get('has_scenarios') else '❌'}
- Données de production: {'✅' if manifest.get('has_production_data') else '❌'}
- Données de consommation: {'✅' if manifest.get('has_consumption_data') else '❌'}
- Résultats économiques: {'✅' if manifest.get('has_economic_results') else '❌'}
- Résultats d'optimisation: {'✅' if manifest.get('has_optimization_results') else '❌'}
- Résultats Monte Carlo: {'✅' if manifest.get('has_monte_carlo_results') else '❌'}

### Visualisations Sauvegardées
{len([k for k, v in manifest.get('saved_visualizations', {}).items() if v])} graphiques et tableaux sauvegardés

## Validation des Données
- **Statut**: {'✅ Valide' if manifest.get('validation', {}).get('is_valid') else '❌ Problèmes détectés'}
- **Score de qualité**: {manifest.get('validation', {}).get('data_quality_score', 0)}%

### Avertissements
{chr(10).join(['- ' + w for w in manifest.get('validation', {}).get('warnings', [])])}

## Structure des Fichiers
```
{manifest['name']}/
├── manifest.json              # Métadonnées du projet
├── session_state_complete.json # Capture exhaustive de l'état
├── config.json                 # Configuration
├── scenarios.json              # Scénarios définis
├── production_data.csv         # Données de production
├── consumption_data.csv        # Données de consommation
├── economic_results.json       # Résultats économiques
├── optimization_results.json   # Résultats d'optimisation
├── monte_carlo_results.json    # Résultats Monte Carlo
├── charts/                     # Graphiques sauvegardés
└── tables/                     # Tableaux Excel
```

## Comment Utiliser ce Projet
1. Ouvrez OptimPV
2. Allez dans l'onglet "Sauvegarde et Historique"
3. Cliquez sur "Charger le projet sélectionné"
4. Sélectionnez ce projet dans la liste

---
*Généré automatiquement par OptimPV v{manifest.get('storage_version')}*
"""
        
        with open(os.path.join(project_dir, 'README.md'), 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def load_project(self, project_id):
        """
        Charge un projet sauvegardé (version améliorée)
        
        Args:
            project_id: ID du projet à charger
            
        Returns:
            bool: True si le chargement a réussi, False sinon
        """
        project_dir = os.path.join('projects', project_id)
        
        if not os.path.exists(project_dir):
            return False
        
        try:
            # Vérifier le manifeste
            manifest_path = os.path.join(project_dir, 'manifest.json')
            if not os.path.exists(manifest_path):
                return False
            
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Vérifier l'intégrité des fichiers si les checksums existent
            if 'file_checksums' in manifest:
                if not self.verify_file_integrity(project_dir, manifest['file_checksums']):
                    st.warning("Certains fichiers ont été modifiés depuis la sauvegarde")
            
            # Charger d'abord la session complète si disponible
            session_complete_path = os.path.join(project_dir, 'session_state_complete.json')
            if os.path.exists(session_complete_path):
                with open(session_complete_path, 'r') as f:
                    complete_session = json.load(f)
                
                # Restaurer les données de session (en excluant les clés de navigation et UI)
                excluded_restore_keys = {
                    'storage_ui_state'  # Exclure l'état de l'interface storage
                }
                
                for key, value in complete_session.items():
                    # Exclure les clés de navigation, UI et système
                    if (key.startswith('nav_') or 
                        key.startswith('ui_') or
                        key.startswith('_') or
                        key in excluded_restore_keys):
                        continue
                        
                    if key.endswith('_pickled'):
                        # Restaurer les objets pickleés
                        original_key = key[:-8]  # Enlever '_pickled'
                        if (original_key.startswith('nav_') or 
                            original_key.startswith('ui_') or
                            original_key.startswith('_')):
                            continue
                        try:
                            pickled_data = base64.b64decode(value.encode('utf-8'))
                            st.session_state[original_key] = pickle.loads(pickled_data)
                        except:
                            continue
                    else:
                        st.session_state[key] = value
            
            # 1. Charger la configuration
            if manifest.get('has_config', False):
                config_path = os.path.join(project_dir, 'config.json')
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        st.session_state.config = json.load(f)
            
            # 2. Charger les scénarios
            if manifest.get('has_scenarios', False):
                scenarios_path = os.path.join(project_dir, 'scenarios.json')
                if os.path.exists(scenarios_path):
                    with open(scenarios_path, 'r') as f:
                        st.session_state.scenarios = json.load(f)
            
            # 3. Charger les données de production et consommation
            if manifest.get('has_production_data', False):
                production_path = os.path.join(project_dir, 'production_data.csv')
                if os.path.exists(production_path):
                    st.session_state.production_data = pd.read_csv(production_path)
                    
                    # Convertir la colonne Temps en datetime si elle existe
                    if 'Temps' in st.session_state.production_data.columns:
                        st.session_state.production_data['Temps'] = pd.to_datetime(st.session_state.production_data['Temps'])
            
            if manifest.get('has_consumption_data', False):
                consumption_path = os.path.join(project_dir, 'consumption_data.csv')
                if os.path.exists(consumption_path):
                    st.session_state.consumption_data = pd.read_csv(consumption_path)
                    
                    # Convertir la colonne Temps en datetime si elle existe
                    if 'Temps' in st.session_state.consumption_data.columns:
                        st.session_state.consumption_data['Temps'] = pd.to_datetime(st.session_state.consumption_data['Temps'])
            
            if manifest.get('has_processed_data', False):
                processed_path = os.path.join(project_dir, 'processed_data.csv')
                if os.path.exists(processed_path):
                    st.session_state.processed_data = pd.read_csv(processed_path)
                    
                    # Convertir la colonne Temps en datetime si elle existe
                    if 'Temps' in st.session_state.processed_data.columns:
                        st.session_state.processed_data['Temps'] = pd.to_datetime(st.session_state.processed_data['Temps'])
                    
                    # Marquer les données comme importées
                    st.session_state.data_imported = True
            
            # 4. Charger les résultats économiques
            if manifest.get('has_economic_results', False):
                economic_path = os.path.join(project_dir, 'economic_results.json')
                if os.path.exists(economic_path):
                    with open(economic_path, 'r') as f:
                        st.session_state.economic_results = json.load(f)
            
            # 5. Charger les résultats d'optimisation
            if manifest.get('has_optimization_results', False):
                optimization_path = os.path.join(project_dir, 'optimization_results.json')
                if os.path.exists(optimization_path):
                    with open(optimization_path, 'r') as f:
                        optimization_data = json.load(f)
                        st.session_state.optimization_results = optimization_data
                        
                        # Marquer l'optimisation comme terminée
                        st.session_state.optimization_completed = True
            
            # 6. Charger les résultats Monte Carlo
            if manifest.get('has_monte_carlo_results', False):
                monte_carlo_path = os.path.join(project_dir, 'monte_carlo_results.json')
                if os.path.exists(monte_carlo_path):
                    with open(monte_carlo_path, 'r') as f:
                        st.session_state.monte_carlo_results = json.load(f)
            
            # Mettre à jour le manifeste (dernière utilisation)
            manifest['updated_at'] = datetime.now().isoformat()
            manifest['last_loaded_at'] = datetime.now().isoformat()
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=4, default=self._json_serializer)
            
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
    
    def verify_file_integrity(self, project_dir: str, expected_checksums: Dict[str, str]) -> bool:
        """Vérifie l'intégrité des fichiers avec les checksums"""
        for rel_path, expected_checksum in expected_checksums.items():
            file_path = os.path.join(project_dir, rel_path)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        actual_checksum = hashlib.md5(content).hexdigest()
                        if actual_checksum != expected_checksum:
                            return False
                except:
                    return False
        return True
    
    def delete_project(self, project_id):
        """
        Supprime un projet sauvegardé
        
        Args:
            project_id: ID du projet à supprimer
            
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        project_dir = os.path.join('projects', project_id)
        
        if not os.path.exists(project_dir):
            return False
        
        try:
            # Supprimer le répertoire du projet
            shutil.rmtree(project_dir)
            
            # Supprimer le projet de l'historique
            if project_id in st.session_state.project_history:
                del st.session_state.project_history[project_id]
            
            return True
        except Exception as e:
            st.error(f"Erreur lors de la suppression du projet : {str(e)}")
            return False
    
    def export_project(self, project_id):
        """
        Exporte un projet au format ZIP
        
        Args:
            project_id: ID du projet à exporter
            
        Returns:
            bytes: Données binaires du fichier ZIP
        """
        project_dir = os.path.join('projects', project_id)
        
        if not os.path.exists(project_dir):
            return None
        
        try:
            # Créer un fichier ZIP en mémoire
            buffer = io.BytesIO()
            
            # Archiver le répertoire du projet
            shutil.make_archive(base_name=os.path.join(project_dir, 'export'),
                               format='zip',
                               root_dir=project_dir)
            
            # Lire le fichier ZIP généré
            with open(os.path.join(project_dir, 'export.zip'), 'rb') as f:
                buffer.write(f.read())
            
            # Supprimer le fichier ZIP temporaire
            os.remove(os.path.join(project_dir, 'export.zip'))
            
            buffer.seek(0)
            return buffer
        except Exception as e:
            st.error(f"Erreur lors de l'exportation du projet : {str(e)}")
            return None
    
    def import_project(self, zip_file, new_name=None):
        """
        Importe un projet depuis un fichier ZIP
        
        Args:
            zip_file: Fichier ZIP contenant le projet
            new_name: Nouveau nom pour le projet (facultatif)
            
        Returns:
            str: ID du projet importé
        """
        try:
            # Créer un répertoire temporaire
            temp_dir = f"temp_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Sauvegarder le fichier ZIP
            zip_path = os.path.join(temp_dir, 'import.zip')
            with open(zip_path, 'wb') as f:
                f.write(zip_file.getvalue())
            
            # Extraire le fichier ZIP
            shutil.unpack_archive(zip_path, temp_dir, 'zip')
            
            # Vérifier le manifeste
            manifest_path = os.path.join(temp_dir, 'manifest.json')
            if not os.path.exists(manifest_path):
                shutil.rmtree(temp_dir, ignore_errors=True)
                return None
            
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Générer un nouvel ID pour le projet
            project_name = new_name if new_name else manifest['name']
            project_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{project_name.replace(' ', '_')}"
            
            # Créer le répertoire du projet
            project_dir = os.path.join('projects', project_id)
            os.makedirs(project_dir, exist_ok=True)
            
            # Copier les fichiers du projet
            for file in os.listdir(temp_dir):
                if file != 'import.zip':
                    shutil.copy2(os.path.join(temp_dir, file), os.path.join(project_dir, file))
            
            # Mettre à jour le manifeste
            if new_name:
                manifest['name'] = new_name
            manifest['imported_at'] = datetime.now().isoformat()
            manifest['updated_at'] = datetime.now().isoformat()
            
            with open(os.path.join(project_dir, 'manifest.json'), 'w') as f:
                json.dump(manifest, f, indent=4)
            
            # Supprimer le répertoire temporaire
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            # Mettre à jour l'historique des projets
            st.session_state.project_history[project_id] = manifest
            
            return project_id
        except Exception as e:
            st.error(f"Erreur lors de l'importation du projet : {str(e)}")
            return None

    def _calculate_change(self, val1, val2):
        """Calcule le changement entre deux valeurs"""
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            if val1 != 0:
                return {'absolute': val2 - val1, 'percent': (val2 - val1) / val1 * 100}
            else:
                return {'absolute': val2 - val1, 'percent': None}
        else:
            return {'from': val1, 'to': val2}
    
    def _show_synthesis_comparison(self, comparison_data):
        """Affiche la synthèse de la comparaison"""
        # Diagnostic d'état des projets
        manifest1 = comparison_data['manifest1']
        manifest2 = comparison_data['manifest2']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### 📋 État du projet : {manifest1['name']}")
            completeness1 = manifest1.get('completeness', {}).get('components', {})
            self._show_project_status_mini(completeness1)
        
        with col2:
            st.markdown(f"#### 📋 État du projet : {manifest2['name']}")
            completeness2 = manifest2.get('completeness', {}).get('components', {})
            self._show_project_status_mini(completeness2)
        
        st.markdown("### 🎯 Principaux écarts")
        
        differences = comparison_data['key_differences']
        perf_delta = differences['performance_delta']
        
        # Métriques principales (si disponibles)
        if perf_delta:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                van_delta = perf_delta.get('VAN', {})
                if van_delta.get('delta') is not None:
                    st.metric(
                        "VAN Optimale",
                        f"{van_delta['project2']:,.0f} €",
                        delta=f"{van_delta['delta']:+,.0f} €"
                    )
                else:
                    st.metric("VAN Optimale", "Non disponible")
            
            with col2:
                roi_delta = perf_delta.get('ROI', {})
                if roi_delta.get('delta') is not None:
                    st.metric(
                        "ROI Optimal",
                        f"{roi_delta['project2']:.1f}%",
                        delta=f"{roi_delta['delta']:+.1f}%"
                    )
                else:
                    st.metric("ROI Optimal", "Non disponible")
            
            with col3:
                payback_delta = perf_delta.get('payback_years', {})
                if payback_delta.get('delta') is not None:
                    st.metric(
                        "Temps de Retour",
                        f"{payback_delta['project2']:.1f} ans",
                        delta=f"{payback_delta['delta']:+.1f} ans",
                        delta_color="inverse"
                    )
                else:
                    st.metric("Temps de Retour", "Non disponible")
            
            with col4:
                price_delta = perf_delta.get('optimal_price', {})
                if price_delta.get('delta') is not None:
                    st.metric(
                        "Prix Optimal",
                        f"{price_delta['project2']:.3f} €/kWh",
                        delta=f"{price_delta['delta']:+.3f} €/kWh"
                    )
                else:
                    st.metric("Prix Optimal", "Non disponible")
        else:
            st.info("⚡ Les métriques de performance nécessitent que les deux projets aient fait une optimisation.")
        
        # Conclusion automatique
        st.markdown("### 🤖 Analyse automatique")
        conclusion = self._generate_automatic_conclusion(comparison_data)
        st.info(conclusion)
        
        # Graphique radar de comparaison
        self._show_radar_comparison(comparison_data)
    
    def _generate_automatic_conclusion(self, comparison_data):
        """Génère une conclusion automatique basée sur les différences"""
        manifest1 = comparison_data['manifest1']
        manifest2 = comparison_data['manifest2']
        differences = comparison_data['key_differences']
        perf_delta = differences['performance_delta']
        
        conclusion = f"La comparaison entre **'{manifest1['name']}'** et **'{manifest2['name']}'** révèle que :\n\n"
        
        # Analyser la VAN
        van_delta = perf_delta.get('VAN', {})
        if van_delta.get('delta') and van_delta['delta'] > 0:
            conclusion += f"- Le second projet présente une **VAN supérieure** de {van_delta['delta']:,.0f} € "
            conclusion += f"(+{van_delta.get('delta_percent', 0):.1f}%), "
        elif van_delta.get('delta') and van_delta['delta'] < 0:
            conclusion += f"- Le premier projet présente une **VAN supérieure** de {-van_delta['delta']:,.0f} € "
            conclusion += f"({van_delta.get('delta_percent', 0):.1f}%), "
        
        # Analyser les changements de configuration majeurs
        config_changes = differences['config_changes']
        major_changes = [c for c in config_changes if c['parameter'] in ['capex_scenario', 'puissance_kwc_installee', 'duree_ppa']]
        
        if major_changes:
            conclusion += "\n- Les principales différences de configuration incluent : "
            for change in major_changes[:3]:  # Limiter à 3 changements
                param = change['parameter']
                if isinstance(change['change'], dict) and 'percent' in change['change']:
                    conclusion += f"\n  • {param}: {change['change']['percent']:+.1f}%"
        
        # Analyser le ROI
        roi_delta = perf_delta.get('ROI', {})
        if roi_delta.get('delta'):
            if roi_delta['delta'] > 0:
                conclusion += f"\n- Le ROI est **amélioré** de {roi_delta['delta']:.1f} points"
            else:
                conclusion += f"\n- Le ROI est **réduit** de {-roi_delta['delta']:.1f} points"
        
        return conclusion
    
    def _show_project_status_mini(self, components):
        """Affiche un mini statut du projet"""
        status_items = [
            ("📊 Données", components.get('data_imported', False)),
            ("⚙️ Config", components.get('config_set', False)),
            ("🎭 Scénarios", components.get('scenarios_defined', False)),
            ("💰 Économie", components.get('economic_analysis', False)),
            ("⚡ Optimisation", components.get('optimization_done', False)),
            ("🎲 Monte Carlo", components.get('monte_carlo_done', False))
        ]
        
        for label, status in status_items:
            icon = "✅" if status else "❌"
            color = "green" if status else "red"
            st.markdown(f"<span style='color: {color};'>{icon} {label}</span>", unsafe_allow_html=True)
    
    def _show_radar_comparison(self, comparison_data):
        """Affiche un graphique radar comparant les projets"""
        import plotly.graph_objects as go
        
        # Préparer les données pour le radar
        categories = []
        values1 = []
        values2 = []
        
        # Score de complétude
        manifest1 = comparison_data['manifest1']
        manifest2 = comparison_data['manifest2']
        
        categories.append('Complétude')
        values1.append(manifest1.get('completeness', {}).get('score', 0))
        values2.append(manifest2.get('completeness', {}).get('score', 0))
        
        # Qualité des données
        categories.append('Qualité')
        values1.append(manifest1.get('validation', {}).get('data_quality_score', 100))
        values2.append(manifest2.get('validation', {}).get('data_quality_score', 100))
        
        # Performance financière (normaliser sur 100)
        perf_delta = comparison_data['key_differences']['performance_delta']
        
        if 'ROI' in perf_delta:
            categories.append('ROI')
            roi1 = perf_delta['ROI'].get('project1', 0)
            roi2 = perf_delta['ROI'].get('project2', 0)
            max_roi = max(roi1, roi2) if max(roi1, roi2) > 0 else 1
            values1.append(roi1 / max_roi * 100)
            values2.append(roi2 / max_roi * 100)
        
        # Créer le graphique radar
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values1,
            theta=categories,
            fill='toself',
            name=manifest1['name'][:20] + '...' if len(manifest1['name']) > 20 else manifest1['name']
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=values2,
            theta=categories,
            fill='toself',
            name=manifest2['name'][:20] + '...' if len(manifest2['name']) > 20 else manifest2['name']
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            title="Comparaison Multi-Critères"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_config_comparison(self, comparison_data):
        """Affiche la comparaison des configurations"""
        st.markdown("### ⚙️ Différences de Configuration")
        
        config_changes = comparison_data['key_differences']['config_changes']
        
        if not config_changes:
            st.info("Les configurations sont identiques")
            return
        
        # Créer un DataFrame pour afficher les différences
        df_data = []
        for change in config_changes:
            row = {
                'Paramètre': change['parameter'],
                f"{comparison_data['manifest1']['name']}": change['project1'],
                f"{comparison_data['manifest2']['name']}": change['project2']
            }
            
            # Ajouter la variation si applicable
            if isinstance(change['change'], dict) and 'percent' in change['change']:
                row['Variation'] = f"{change['change']['percent']:+.1f}%"
            
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        
        # Appliquer un style pour mettre en évidence les différences
        def highlight_differences(row):
            return ['background-color: #ffe6e6' if i > 0 else '' for i in range(len(row))]
        
        styled_df = df.style.apply(highlight_differences, axis=1)
        st.dataframe(styled_df, use_container_width=True)
    
    def _show_economic_comparison(self, comparison_data):
        """Affiche la comparaison économique avec graphiques"""
        st.markdown("### 💰 Analyse Économique Comparative")
        
        economic1 = comparison_data['economic1']
        economic2 = comparison_data['economic2']
        
        # Debug des données économiques
        logger.debug(f"DEBUG COMPARAISON ÉCONOMIE:")
        logger.debug(f"  economic1 bool: {bool(economic1)}, type: {type(economic1)}, contenu: {economic1}")
        logger.debug(f"  economic2 bool: {bool(economic2)}, type: {type(economic2)}, contenu: {economic2}")
        
        if not economic1 or not economic2:
            missing_info = []
            if not economic1:
                missing_info.append(f"**{comparison_data['manifest1']['name']}** : Aucune analyse économique")
                logger.debug(f"  -> Projet 1 manque economic_results")
            if not economic2:
                missing_info.append(f"**{comparison_data['manifest2']['name']}** : Aucune analyse économique")
                logger.debug(f"  -> Projet 2 manque economic_results")
            
            st.info("📊 " + "\n".join(missing_info) + "\n\n💡 *Effectuez d'abord une analyse économique dans l'onglet 'Analyse Économique' pour ces projets.*")
        else:
            # Les deux projets ont des données économiques, afficher la comparaison
            # Graphique des flux de trésorerie
            self._plot_cashflow_comparison(economic1, economic2, comparison_data)
            
            # Tableau comparatif des indicateurs économiques
            self._show_economic_indicators_table(economic1, economic2, comparison_data)
    
    def _plot_cashflow_comparison(self, economic1, economic2, comparison_data):
        """Trace la comparaison des flux de trésorerie"""
        # Extraire les flux de trésorerie si disponibles
        cashflows1 = economic1.get('annual_cashflows', [])
        cashflows2 = economic2.get('annual_cashflows', [])
        
        if cashflows1 and cashflows2:
            fig = go.Figure()
            
            # Ajouter les traces
            years = list(range(1, max(len(cashflows1), len(cashflows2)) + 1))
            
            fig.add_trace(go.Scatter(
                x=years[:len(cashflows1)],
                y=cashflows1,
                mode='lines+markers',
                name=comparison_data['manifest1']['name'],
                line=dict(color='blue', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=years[:len(cashflows2)],
                y=cashflows2,
                mode='lines+markers',
                name=comparison_data['manifest2']['name'],
                line=dict(color='red', width=2)
            ))
            
            # Ajouter une ligne horizontale à zéro
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            
            fig.update_layout(
                title="Comparaison des Flux de Trésorerie Annuels",
                xaxis_title="Année",
                yaxis_title="Flux de Trésorerie (€)",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _show_economic_indicators_table(self, economic1, economic2, comparison_data):
        """Affiche un tableau comparatif des indicateurs économiques"""
        indicators = [
            ('CAPEX Total', 'total_capex'),
            ('OPEX Annuel Moyen', 'average_annual_opex'),
            ('Revenus Annuels Moyens', 'average_annual_revenue'),
            ('Cash Flow Cumulé', 'cumulative_cashflow'),
            ('LCOE', 'lcoe')
        ]
        
        data = []
        for label, key in indicators:
            val1 = economic1.get(key, 'N/A')
            val2 = economic2.get(key, 'N/A')
            
            row = {
                'Indicateur': label,
                comparison_data['manifest1']['name']: f"{val1:,.0f}" if isinstance(val1, (int, float)) else val1,
                comparison_data['manifest2']['name']: f"{val2:,.0f}" if isinstance(val2, (int, float)) else val2
            }
            
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                diff = val2 - val1
                row['Différence'] = f"{diff:+,.0f}"
                if val1 != 0:
                    row['Variation %'] = f"{(diff/val1*100):+.1f}%"
            
            data.append(row)
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    
    def _show_optimization_comparison(self, comparison_data):
        """Affiche la comparaison des résultats d'optimisation"""
        st.markdown("### ⚡ Comparaison des Optimisations")
        
        opt1 = comparison_data['optimization1']
        opt2 = comparison_data['optimization2']
        
        if not opt1 or not opt2:
            missing_info = []
            if not opt1:
                missing_info.append(f"**{comparison_data['manifest1']['name']}** : Aucune optimisation")
            if not opt2:
                missing_info.append(f"**{comparison_data['manifest2']['name']}** : Aucune optimisation")
            
            st.info("⚡ " + "\n".join(missing_info) + "\n\n💡 *Effectuez d'abord une optimisation dans l'onglet 'Optimisation' pour ces projets.*")
            return
        
        # Trouver les scénarios communs
        scenarios1 = set(opt1.keys()) - {'metadata'}
        scenarios2 = set(opt2.keys()) - {'metadata'}
        common_scenarios = scenarios1 & scenarios2
        
        if not common_scenarios:
            st.warning("Aucun scénario commun trouvé pour la comparaison")
            return
        
        # Sélecteur de scénario
        scenario = st.selectbox(
            "Sélectionner un scénario à comparer",
            options=list(common_scenarios)
        )
        
        if scenario:
            self._plot_optimization_curves(opt1[scenario], opt2[scenario], comparison_data)
            self._show_optimization_metrics(opt1[scenario], opt2[scenario], comparison_data)
    
    def _plot_optimization_curves(self, opt_data1, opt_data2, comparison_data):
        """Trace les courbes d'optimisation"""
        # Créer des subplots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("VAN vs Prix de Vente", "ROI vs Prix de Vente")
        )
        
        # Extraire les données d'optimisation
        if 'optimization_data' in opt_data1:
            prices1 = [d['prix'] for d in opt_data1['optimization_data']]
            vans1 = [d['VAN'] for d in opt_data1['optimization_data']]
            rois1 = [d['ROI'] for d in opt_data1['optimization_data']]
            
            # VAN
            fig.add_trace(
                go.Scatter(x=prices1, y=vans1, mode='lines+markers', 
                          name=comparison_data['manifest1']['name'],
                          line=dict(color='blue')),
                row=1, col=1
            )
            
            # ROI
            fig.add_trace(
                go.Scatter(x=prices1, y=rois1, mode='lines+markers',
                          name=comparison_data['manifest1']['name'],
                          line=dict(color='blue'), showlegend=False),
                row=1, col=2
            )
        
        if 'optimization_data' in opt_data2:
            prices2 = [d['prix'] for d in opt_data2['optimization_data']]
            vans2 = [d['VAN'] for d in opt_data2['optimization_data']]
            rois2 = [d['ROI'] for d in opt_data2['optimization_data']]
            
            # VAN
            fig.add_trace(
                go.Scatter(x=prices2, y=vans2, mode='lines+markers',
                          name=comparison_data['manifest2']['name'],
                          line=dict(color='red')),
                row=1, col=1
            )
            
            # ROI
            fig.add_trace(
                go.Scatter(x=prices2, y=rois2, mode='lines+markers',
                          name=comparison_data['manifest2']['name'],
                          line=dict(color='red'), showlegend=False),
                row=1, col=2
            )
        
        # Mettre à jour les axes
        fig.update_xaxes(title_text="Prix de Vente (€/kWh)", row=1, col=1)
        fig.update_xaxes(title_text="Prix de Vente (€/kWh)", row=1, col=2)
        fig.update_yaxes(title_text="VAN (€)", row=1, col=1)
        fig.update_yaxes(title_text="ROI (%)", row=1, col=2)
        
        fig.update_layout(height=400, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_optimization_metrics(self, opt_data1, opt_data2, comparison_data):
        """Affiche les métriques d'optimisation"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**{comparison_data['manifest1']['name']}**")
            if 'best_result' in opt_data1:
                best = opt_data1['best_result']
                st.metric("Prix Optimal", f"{best.get('optimal_price', 0):.3f} €/kWh")
                st.metric("VAN Optimale", f"{best.get('VAN', 0):,.0f} €")
                st.metric("ROI Optimal", f"{best.get('ROI', 0):.1f}%")
        
        with col2:
            st.markdown(f"**{comparison_data['manifest2']['name']}**")
            if 'best_result' in opt_data2:
                best = opt_data2['best_result']
                st.metric("Prix Optimal", f"{best.get('optimal_price', 0):.3f} €/kWh")
                st.metric("VAN Optimale", f"{best.get('VAN', 0):,.0f} €")
                st.metric("ROI Optimal", f"{best.get('ROI', 0):.1f}%")
    
    def _show_monte_carlo_comparison(self, comparison_data):
        """Affiche la comparaison Monte Carlo"""
        st.markdown("### 🎲 Analyse de Risque (Monte Carlo)")
        
        mc1 = comparison_data['monte_carlo1']
        mc2 = comparison_data['monte_carlo2']
        
        if not mc1 or not mc2:
            missing_info = []
            if not mc1:
                missing_info.append(f"**{comparison_data['manifest1']['name']}** : Aucune simulation Monte Carlo")
            if not mc2:
                missing_info.append(f"**{comparison_data['manifest2']['name']}** : Aucune simulation Monte Carlo")
            
            st.info("🎲 " + "\n".join(missing_info) + "\n\n💡 *Effectuez d'abord une simulation Monte Carlo dans l'onglet 'Simulation Monte Carlo' pour ces projets.*")
        else:
            # Les deux projets ont des données Monte Carlo, afficher la comparaison
            # Comparer les distributions de VAN
            self._plot_van_distributions(mc1, mc2, comparison_data)
            
            # Tableau des statistiques de risque
            self._show_risk_statistics(mc1, mc2, comparison_data)
    
    def _plot_van_distributions(self, mc1, mc2, comparison_data):
        """Trace les distributions de VAN"""
        # Extraire les VAN simulées
        vans1 = mc1.get('simulated_vans', [])
        vans2 = mc2.get('simulated_vans', [])
        
        if vans1 and vans2:
            fig = go.Figure()
            
            # Histogrammes
            fig.add_trace(go.Histogram(
                x=vans1,
                name=comparison_data['manifest1']['name'],
                opacity=0.7,
                nbinsx=30
            ))
            
            fig.add_trace(go.Histogram(
                x=vans2,
                name=comparison_data['manifest2']['name'],
                opacity=0.7,
                nbinsx=30
            ))
            
            fig.update_layout(
                title="Distribution des VAN (Simulations Monte Carlo)",
                xaxis_title="VAN (€)",
                yaxis_title="Fréquence",
                barmode='overlay'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _show_risk_statistics(self, mc1, mc2, comparison_data):
        """Affiche les statistiques de risque"""
        stats = [
            ('VAN Moyenne', 'mean_van'),
            ('Écart-Type VAN', 'std_van'),
            ('VAN au 5e Percentile', 'van_p5'),
            ('VAN au 95e Percentile', 'van_p95'),
            ('Probabilité VAN > 0', 'prob_positive_van')
        ]
        
        data = []
        for label, key in stats:
            val1 = mc1.get(key, 'N/A')
            val2 = mc2.get(key, 'N/A')
            
            row = {
                'Statistique': label,
                comparison_data['manifest1']['name']: self._format_stat_value(val1, key),
                comparison_data['manifest2']['name']: self._format_stat_value(val2, key)
            }
            
            data.append(row)
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    
    def _format_stat_value(self, value, key):
        """Formate une valeur statistique"""
        if value == 'N/A':
            return value
        
        if 'prob' in key:
            return f"{value:.1%}"
        elif isinstance(value, (int, float)):
            return f"{value:,.0f}"
        else:
            return str(value)

# Pour maintenir la compatibilité avec l'ancien code
def show_storage_ui():
    """Point d'entrée pour l'interface de stockage"""
    storage = StorageModule()
    storage.show_ui()