"""
UI Components - Composants d'interface utilisateur pour le module de stockage
"""

import streamlit as st
import os
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)

class UIComponents:
    """Composants d'interface utilisateur pour le stockage"""
    
    def __init__(self, storage_module):
        self.storage = storage_module
    
    def show_main_ui(self):
        """Affiche l'interface utilisateur principale"""
        st.markdown("""
        <style>
        .project-card {
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            background-color: #f8f9fa;
        }
        .module-badge {
            display: inline-block;
            padding: 4px 8px;
            margin: 2px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .module-badge.active {
            background-color: #28a745;
            color: white;
        }
        .module-badge:not(.active) {
            background-color: #6c757d;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # En-tête
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.title("📁 Hub de Projets OptimPV")
            st.caption("Système de stockage et comparaison de projets - Version 2.0")
        
        with col2:
            # Bouton pour sauvegarder le projet actuel
            if st.button("💾 Sauvegarder", type="primary", use_container_width=True):
                st.session_state.storage_ui_state['show_save_dialog'] = True
        
        # Dialogue de sauvegarde
        if st.session_state.storage_ui_state.get('show_save_dialog', False):
            self._show_save_dialog()
        
        # Statistiques rapides
        self._show_quick_stats()
        
        # Filtres et recherche
        self._show_filters()
        
        # Mode comparaison info
        if st.session_state.storage_ui_state['comparison_mode']:
            first_project = st.session_state.storage_ui_state['first_project_id']
            if first_project:
                st.info(f"🔍 Mode comparaison actif. Projet sélectionné: **{st.session_state.project_history[first_project]['name']}**. Cliquez sur un autre projet pour comparer.")
            
            if st.button("❌ Annuler la comparaison"):
                st.session_state.storage_ui_state['comparison_mode'] = False
                st.session_state.storage_ui_state['first_project_id'] = None
                st.rerun()
        
        # Afficher les projets
        self._display_project_cards()
        
        # Section d'import de projet
        st.markdown("---")
        st.subheader("📥 Importer un projet")
        uploaded_file = st.file_uploader("Choisir un fichier projet (.zip)", type=['zip'])
        if uploaded_file:
            self._handle_import(uploaded_file)
    
    def _show_quick_stats(self):
        """Affiche les statistiques rapides"""
        total_projects = len(st.session_state.project_history)
        
        if total_projects > 0:
            # Calculer les statistiques
            favorites = sum(1 for p in st.session_state.project_history.values() if p.get('is_favorite', False))
            total_size = sum(p.get('data_size', {}).get('total_size_mb', 0) for p in st.session_state.project_history.values())
            avg_completeness = sum(p.get('completeness', {}).get('score', 0) for p in st.session_state.project_history.values()) / total_projects
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📁 Projets", total_projects)
            
            with col2:
                st.metric("⭐ Favoris", favorites)
            
            with col3:
                st.metric("💾 Taille totale", f"{total_size:.1f} MB")
            
            with col4:
                st.metric("📊 Complétude moy.", f"{avg_completeness:.1f}%")
    
    def _show_filters(self):
        """Affiche les filtres de recherche"""
        st.markdown("### 🔍 Filtres")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("🔍 Rechercher", value=st.session_state.storage_ui_state['filter_search'])
            if search_term != st.session_state.storage_ui_state['filter_search']:
                st.session_state.storage_ui_state['filter_search'] = search_term
                st.rerun()
        
        with col2:
            # Récupérer tous les tags existants
            all_tags = set()
            for project in st.session_state.project_history.values():
                all_tags.update(project.get('tags', []))
            
            if all_tags:
                selected_tags = st.multiselect("🏷️ Tags", list(all_tags), default=st.session_state.storage_ui_state['filter_tags'])
                if selected_tags != st.session_state.storage_ui_state['filter_tags']:
                    st.session_state.storage_ui_state['filter_tags'] = selected_tags
                    st.rerun()
        
        with col3:
            favorites_only = st.checkbox("⭐ Favoris uniquement", value=st.session_state.storage_ui_state['filter_favorites_only'])
            if favorites_only != st.session_state.storage_ui_state['filter_favorites_only']:
                st.session_state.storage_ui_state['filter_favorites_only'] = favorites_only
                st.rerun()
    
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
                    # Gérer l'état de confirmation
                    confirm_key = f"confirm_delete_{project_id}"
                    is_confirming = st.session_state.get(confirm_key, False)
                    
                    if not is_confirming:
                        if st.button("🗑️ Supprimer", key=f"delete_{project_id}", use_container_width=True):
                            self._delete_project(project_id)
                    else:
                        # Afficher que la suppression est en cours de confirmation
                        st.info("⏳ Confirmation...")
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
            else:
                # Mode comparaison
                if project_id != first_project_id:
                    if st.button(f"⚖️ Comparer avec {manifest['name']}", key=f"compare_with_{project_id}", use_container_width=True):
                        self._show_comparison_dashboard(first_project_id, project_id)
                else:
                    st.info("✅ Projet sélectionné pour la comparaison")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def _filter_projects(self) -> List[Tuple[str, dict]]:
        """Filtre les projets selon les critères définis"""
        search_term = st.session_state.storage_ui_state['filter_search'].lower()
        selected_tags = st.session_state.storage_ui_state['filter_tags']
        favorites_only = st.session_state.storage_ui_state['filter_favorites_only']
        
        filtered = []
        
        for project_id, manifest in st.session_state.project_history.items():
            # Filtre par recherche
            if search_term:
                searchable_text = f"{manifest['name']} {manifest.get('description', '')}".lower()
                if search_term not in searchable_text:
                    continue
            
            # Filtre par tags
            if selected_tags:
                project_tags = manifest.get('tags', [])
                if not any(tag in project_tags for tag in selected_tags):
                    continue
            
            # Filtre par favoris
            if favorites_only and not manifest.get('is_favorite', False):
                continue
            
            filtered.append((project_id, manifest))
        
        # Trier par date de modification (plus récent en premier)
        filtered.sort(key=lambda x: x[1].get('updated_at', ''), reverse=True)
        
        return filtered
    
    def _show_save_dialog(self):
        """Affiche le dialogue de sauvegarde"""
        with st.form("save_project_form"):
            st.subheader("💾 Sauvegarder le projet actuel")
            
            col1, col2 = st.columns(2)
            
            with col1:
                project_name = st.text_input("Nom du projet *", placeholder="Mon projet OptimPV")
                description = st.text_area("Description", placeholder="Description optionnelle du projet")
            
            with col2:
                tags_input = st.text_input("Tags", placeholder="tag1, tag2, tag3")
                is_favorite = st.checkbox("Marquer comme favori")
            
            # Boutons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.form_submit_button("💾 Sauvegarder", type="primary", use_container_width=True):
                    if project_name:
                        # Traiter les tags
                        tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else []
                        
                        # Sauvegarder le projet
                        try:
                            project_id = self.storage.project_manager.save_current_project(
                                project_name, description, tags, is_favorite
                            )
                            st.success(f"✅ Projet '{project_name}' sauvegardé avec succès! (ID: {project_id})")
                            st.session_state.storage_ui_state['show_save_dialog'] = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la sauvegarde: {str(e)}")
                    else:
                        st.error("❌ Le nom du projet est obligatoire")
            
            with col2:
                if st.form_submit_button("❌ Annuler", use_container_width=True):
                    st.session_state.storage_ui_state['show_save_dialog'] = False
                    st.rerun()
    
    def _toggle_favorite(self, project_id: str):
        """Bascule le statut favori d'un projet"""
        if project_id in st.session_state.project_history:
            manifest = st.session_state.project_history[project_id]
            manifest['is_favorite'] = not manifest.get('is_favorite', False)
            
            # Sauvegarder le manifeste modifié
            try:
                import json
                manifest_path = f"projects/{project_id}/manifest.json"
                with open(manifest_path, 'w') as f:
                    json.dump(manifest, f, indent=4, default=self.storage.data_utils._json_serializer)
                st.rerun()
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du favori: {e}")
    
    def _load_project(self, project_id: str):
        """Charge un projet"""
        success = self.storage.project_manager.load_project(project_id)
        if success:
            st.rerun()
    
    def _delete_project(self, project_id: str):
        """Supprime un projet avec confirmation via session_state"""
        from .debug_logger import storage_logger
        
        manifest = st.session_state.project_history.get(project_id, {})
        project_name = manifest.get('name', project_id)
        
        # Utiliser session_state pour gérer l'état de confirmation
        confirm_key = f"confirm_delete_{project_id}"
        
        # Initialiser l'état si nécessaire
        if confirm_key not in st.session_state:
            st.session_state[confirm_key] = False
        
        if not st.session_state[confirm_key]:
            # Premier clic - demander confirmation
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.warning(f"⚠️ Êtes-vous sûr de vouloir supprimer '{project_name}' ?")
            
            with col2:
                if st.button("✅ Confirmer", key=f"confirm_btn_{project_id}", type="primary"):
                    storage_logger.log_operation("delete_project_confirm", {
                        'project_id': project_id,
                        'project_name': project_name
                    })
                    st.session_state[confirm_key] = True
                    st.rerun()
        else:
            # Confirmation reçue - procéder à la suppression
            try:
                storage_logger.log_operation("delete_project_execute", {
                    'project_id': project_id,
                    'project_name': project_name
                })
                
                success = self.storage.project_manager.delete_project(project_id)
                
                if success:
                    storage_logger.log_operation("delete_project_execute", {
                        'project_id': project_id,
                        'result': 'success'
                    }, status="SUCCESS")
                    
                    # Nettoyer l'état
                    del st.session_state[confirm_key]
                    st.success(f"✅ Projet '{project_name}' supprimé avec succès")
                    
                    # Recharger l'historique et rafraîchir
                    self.storage.load_project_history()
                    st.rerun()
                else:
                    storage_logger.log_operation("delete_project_execute", {
                        'project_id': project_id,
                        'result': 'failed'
                    }, status="ERROR")
                    
                    st.error(f"❌ Erreur lors de la suppression du projet '{project_name}'")
                    # Réinitialiser l'état
                    st.session_state[confirm_key] = False
                    
            except Exception as e:
                storage_logger.log_error("delete_project_execute", e, {
                    'project_id': project_id
                })
                st.error(f"❌ Erreur : {str(e)}")
                st.session_state[confirm_key] = False
    
    def _export_project(self, project_id: str):
        """Exporte un projet"""
        zip_data = self.storage.project_manager.export_project(project_id)
        if zip_data:
            manifest = st.session_state.project_history.get(project_id, {})
            project_name = manifest.get('name', project_id)
            filename = f"{project_name}_{project_id}.zip"
            
            st.download_button(
                label=f"⬇️ Télécharger {project_name}",
                data=zip_data,
                file_name=filename,
                mime="application/zip",
                key=f"download_{project_id}"
            )
    
    def _duplicate_project(self, project_id: str):
        """Duplique un projet"""
        # Exporter le projet
        zip_data = self.storage.project_manager.export_project(project_id)
        if zip_data:
            # Créer un nouveau nom
            original_name = st.session_state.project_history[project_id]['name']
            new_name = f"{original_name} (Copie)"
            
            # Importer comme nouveau projet
            import io
            zip_file = io.BytesIO(zip_data)
            new_id = self.storage.project_manager.import_project(zip_file, new_name)
            
            if new_id:
                st.success(f"✅ Projet dupliqué avec succès! (ID: {new_id})")
                self.storage.load_project_history()
                st.rerun()
    
    def _handle_import(self, uploaded_file):
        """Gère l'import d'un projet"""
        with st.form("import_form"):
            new_name = st.text_input("Nom du projet (optionnel)")
            
            if st.form_submit_button("Importer"):
                project_id = self.storage.project_manager.import_project(uploaded_file, new_name)
                if project_id:
                    st.success(f"✅ Projet importé avec succès! (ID: {project_id})")
                    self.storage.load_project_history()
                    st.rerun()
    
    def _show_comparison_dashboard(self, project_id1: str, project_id2: str):
        """Affiche le dashboard de comparaison détaillé"""
        # Réinitialiser l'état de comparaison
        st.session_state.storage_ui_state['comparison_mode'] = False
        st.session_state.storage_ui_state['first_project_id'] = None
        
        # Charger les données complètes des deux projets
        comparison_data = self.storage.comparison.compare_projects_advanced(project_id1, project_id2)
        
        if not comparison_data:
            st.error("Erreur lors de la comparaison des projets")
            return
        
        # Afficher le dashboard
        manifest1 = comparison_data['manifest1']
        manifest2 = comparison_data['manifest2']
        
        st.markdown(f"## 📊 Comparaison : {manifest1['name']} vs {manifest2['name']}")
        
        # Import dynamique de la visualisation pour éviter les dépendances circulaires
        try:
            from .visualization import ComparisonVisualization
            viz = ComparisonVisualization(self.storage)
            
            # Créer des onglets pour organiser la comparaison
            tabs = st.tabs(["📈 Synthèse", "⚙️ Configuration", "💰 Économie", "⚡ Optimisation", "🎲 Monte Carlo"])
            
            with tabs[0]:
                viz._show_synthesis_comparison(comparison_data)
            
            with tabs[1]:
                viz._show_config_comparison(comparison_data)
            
            with tabs[2]:
                viz._show_economic_comparison(comparison_data)
            
            with tabs[3]:
                viz._show_optimization_comparison(comparison_data)
            
            with tabs[4]:
                viz._show_monte_carlo_comparison(comparison_data)
                
        except ImportError as e:
            st.error(f"Module de visualisation non disponible: {e}")
            # Affichage basique sans visualisations
            st.json(comparison_data['key_differences'])