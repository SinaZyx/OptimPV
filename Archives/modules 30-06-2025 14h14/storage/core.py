"""
Core StorageModule - Classe principale du système de stockage
"""

import streamlit as st
import os
import logging
from typing import Dict, Any, List

from .project_manager import ProjectManager
from .comparison import ProjectComparison
from .data_utils import DataUtils
from .ui_components import UIComponents
from .debug_logger import storage_logger

logger = logging.getLogger(__name__)

class StorageModule:
    """
    Version 2.0 du module de stockage avec interface Hub de Projets
    - Interface unifiée et intuitive
    - Comparaison intelligente de projets
    - Visualisations graphiques avancées
    """
    
    def __init__(self):
        # Logger l'initialisation
        storage_logger.log_operation("StorageModule.__init__", {
            'projects_dir_exists': os.path.exists('projects')
        })
        
        try:
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
            
            # Initialiser les composants
            self.project_manager = ProjectManager(self)
            self.comparison = ProjectComparison(self)
            self.data_utils = DataUtils(self)
            self.ui_components = UIComponents(self)
            
            # Log success
            storage_logger.log_operation("StorageModule.__init__", {
                'status': 'initialized',
                'excluded_keys': list(self.excluded_keys),
                'excluded_prefixes': list(self.excluded_prefixes)
            }, status="SUCCESS")
            
        except Exception as e:
            storage_logger.log_error("StorageModule.__init__", e)
            raise
    
    def load_project_history(self):
        """Charge l'historique des projets depuis le système de fichiers"""
        import glob
        import json
        
        st.session_state.project_history = {}
        
        # Parcourir les projets sauvegardés
        project_dirs = glob.glob('projects/*')
        for project_dir in project_dirs:
            if os.path.isdir(project_dir):
                project_id = os.path.basename(project_dir)
                manifest_path = os.path.join(project_dir, 'manifest.json')
                
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                            st.session_state.project_history[project_id] = manifest
                    except Exception as e:
                        logger.warning(f"Impossible de charger le manifeste pour {project_id}: {e}")
    
    def show_ui(self):
        """Affiche l'interface utilisateur principale"""
        self.ui_components.show_main_ui()
        
        # Ajouter l'interface de debug en bas
        storage_logger.show_debug_ui()
    
    # Méthodes déléguées pour compatibilité
    def save_current_project(self, name: str, description: str = "", tags: List[str] = None):
        """Sauvegarde le projet actuel"""
        return self.project_manager.save_current_project(name, description, tags)
    
    def load_project(self, project_id: str):
        """Charge un projet"""
        return self.project_manager.load_project(project_id)
    
    def compare_projects_advanced(self, project_id1: str, project_id2: str):
        """Compare deux projets de manière avancée"""
        return self.comparison.compare_projects_advanced(project_id1, project_id2)
    
    def get_active_modules(self) -> List[str]:
        """Détermine quels modules sont actifs dans le projet"""
        return self.data_utils.get_active_modules()
    
    def calculate_completeness_score(self) -> Dict[str, Any]:
        """Calcule un score de complétude du projet"""
        return self.data_utils.calculate_completeness_score()