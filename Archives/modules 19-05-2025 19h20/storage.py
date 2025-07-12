import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import io
import glob
from datetime import datetime, timedelta
import shutil

class StorageModule:
    def __init__(self):
        # Créer le répertoire 'projects' s'il n'existe pas
        if not os.path.exists('projects'):
            os.makedirs('projects')
        
        # Initialiser les structures de données si elles n'existent pas
        if 'project_history' not in st.session_state:
            self.load_project_history()
    
    def load_project_history(self):
        """
        Charge l'historique des projets depuis le système de fichiers
        """
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
    
    def save_current_project(self, project_name, description=""):
        """
        Sauvegarde le projet actuel
        
        Args:
            project_name: Nom du projet
            description: Description du projet
            
        Returns:
            str: ID du projet sauvegardé
        """
        # Générer un ID unique pour le projet
        project_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{project_name.replace(' ', '_')}"
        
        # Créer le répertoire du projet
        project_dir = os.path.join('projects', project_id)
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        
        # Créer le manifeste du projet
        manifest = {
            'name': project_name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Sauvegarder les données du projet
        try:
            # 1. Configuration
            if 'config' in st.session_state:
                with open(os.path.join(project_dir, 'config.json'), 'w') as f:
                    json.dump(st.session_state.config, f, indent=4)
                manifest['has_config'] = True
            else:
                manifest['has_config'] = False
            
            # 2. Scénarios
            if 'scenarios' in st.session_state:
                with open(os.path.join(project_dir, 'scenarios.json'), 'w') as f:
                    json.dump(st.session_state.scenarios, f, indent=4)
                manifest['has_scenarios'] = True
            else:
                manifest['has_scenarios'] = False
            
            # 3. Données de production et consommation
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
            
            # 4. Résultats économiques
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
            
            # 5. Résultats d'optimisation
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
            
            # 6. Résultats Monte Carlo
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
            
            # Sauvegarder le manifeste
            with open(os.path.join(project_dir, 'manifest.json'), 'w') as f:
                json.dump(manifest, f, indent=4)
            
            # Mettre à jour l'historique des projets
            st.session_state.project_history[project_id] = manifest
            
            return project_id
        
        except Exception as e:
            # En cas d'erreur, supprimer le répertoire du projet
            shutil.rmtree(project_dir, ignore_errors=True)
            raise e
    
    def load_project(self, project_id):
        """
        Charge un projet sauvegardé
        
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
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=4)
            
            # Mettre à jour l'historique des projets
            st.session_state.project_history[project_id] = manifest
            
            return True
        
        except Exception as e:
            st.error(f"Erreur lors du chargement du projet : {str(e)}")
            return False
    
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
    
    def show_ui(self):
        """Affiche l'interface utilisateur du module de stockage"""
        st.markdown("<h1 class='main-header'>Sauvegarde et Historique</h1>", unsafe_allow_html=True)
        
        # Créer des onglets pour les différentes fonctionnalités
        tab1, tab2, tab3 = st.tabs(["Sauvegarde du Projet", "Historique des Projets", "Import/Export"])
        
        with tab1:
            st.markdown("<h3 class='sub-header'>Sauvegarde du Projet Actuel</h3>", unsafe_allow_html=True)
            
            st.markdown("""
            Vous pouvez sauvegarder l'état actuel du projet pour y revenir plus tard. Cela inclut :
            - Les données importées
            - La configuration et les scénarios
            - Les résultats des analyses économiques
            - Les résultats d'optimisation
            - Les résultats des simulations Monte Carlo
            """)
            
            # Formulaire de sauvegarde
            col1, col2 = st.columns(2)
            
            with col1:
                project_name = st.text_input("Nom du projet", value="Projet Autoconsommation", key="save_project_name")
            
            with col2:
                project_description = st.text_area("Description (facultative)", key="save_project_description")
            
            # Vérifier que des données sont importées
            if not st.session_state.data_imported:
                st.warning("Aucune donnée n'a été importée. Veuillez d'abord importer des données.")
            
            # Bouton de sauvegarde
            if st.button("Sauvegarder le projet", key="save_project_button"):
                with st.spinner("Sauvegarde en cours..."):
                    try:
                        project_id = self.save_current_project(project_name, project_description)
                        st.success(f"Projet sauvegardé avec succès (ID: {project_id}).")
                    except Exception as e:
                        st.error(f"Erreur lors de la sauvegarde du projet : {str(e)}")
        
        with tab2:
            st.markdown("<h3 class='sub-header'>Historique des Projets</h3>", unsafe_allow_html=True)
            
            # Bouton pour actualiser l'historique
            if st.button("Actualiser l'historique", key="refresh_history"):
                self.load_project_history()
                st.rerun()
            
            # Afficher l'historique des projets
            if not st.session_state.project_history:
                st.info("Aucun projet sauvegardé disponible.")
            else:
                # Créer un tableau des projets
                projects_data = []
                for project_id, manifest in st.session_state.project_history.items():
                    # Calculer le statut du projet
                    status = []
                    if manifest.get('has_production_data', False):
                        status.append("Données")
                    if manifest.get('has_economic_results', False):
                        status.append("Économie")
                    if manifest.get('has_optimization_results', False):
                        status.append("Optimisation")
                    if manifest.get('has_monte_carlo_results', False):
                        status.append("Monte Carlo")
                    
                    status_str = ", ".join(status) if status else "Vide"
                    
                    projects_data.append({
                        "ID": project_id,
                        "Nom": manifest['name'],
                        "Description": manifest.get('description', ""),
                        "Créé le": datetime.fromisoformat(manifest['created_at']).strftime("%d/%m/%Y %H:%M"),
                        "Modifié le": datetime.fromisoformat(manifest['updated_at']).strftime("%d/%m/%Y %H:%M"),
                        "Statut": status_str
                    })
                
                # Trier par date de modification décroissante
                projects_data.sort(key=lambda x: x["Modifié le"], reverse=True)
                
                # Créer un DataFrame
                df_projects = pd.DataFrame(projects_data)
                
                # Afficher le tableau
                st.dataframe(df_projects, use_container_width=True)
                
                # Sélectionner un projet à charger
                selected_project_id = st.selectbox(
                    "Sélectionner un projet à charger",
                    options=df_projects["ID"].tolist(),
                    format_func=lambda x: f"{df_projects[df_projects['ID'] == x]['Nom'].iloc[0]} ({x})",
                    key="load_project_id"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Bouton pour charger le projet
                    if st.button("Charger le projet sélectionné", key="load_project_button"):
                        with st.spinner("Chargement en cours..."):
                            if self.load_project(selected_project_id):
                                st.success(f"Projet '{df_projects[df_projects['ID'] == selected_project_id]['Nom'].iloc[0]}' chargé avec succès.")
                                st.rerun()
                            else:
                                st.error("Erreur lors du chargement du projet.")
                
                with col2:
                    # Bouton pour supprimer le projet
                    if st.button("Supprimer le projet sélectionné", key="delete_project_button"):
                        # Demander une confirmation
                        if st.button("Confirmer la suppression", key="confirm_delete"):
                            with st.spinner("Suppression en cours..."):
                                if self.delete_project(selected_project_id):
                                    st.success(f"Projet supprimé avec succès.")
                                    # Actualiser l'historique
                                    self.load_project_history()
                                    st.rerun()
                                else:
                                    st.error("Erreur lors de la suppression du projet.")
        
        with tab3:
            st.markdown("<h3 class='sub-header'>Import/Export de Projets</h3>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Exporter un Projet")
                
                # Sélectionner un projet à exporter
                if not st.session_state.project_history:
                    st.info("Aucun projet disponible pour l'exportation.")
                else:
                    # Créer une liste des projets
                    project_options = []
                    for project_id, manifest in st.session_state.project_history.items():
                        project_options.append((project_id, manifest['name']))
                    
                    # Trier par nom
                    project_options.sort(key=lambda x: x[1])
                    
                    # Sélectionner un projet
                    export_project_id = st.selectbox(
                        "Sélectionner un projet à exporter",
                        options=[p[0] for p in project_options],
                        format_func=lambda x: next(p[1] for p in project_options if p[0] == x),
                        key="export_project_id"
                    )
                    
                    # Bouton pour exporter le projet
                    if st.button("Exporter le projet", key="export_project_button"):
                        with st.spinner("Exportation en cours..."):
                            export_data = self.export_project(export_project_id)
                            if export_data:
                                # Trouver le nom du projet
                                project_name = next(p[1] for p in project_options if p[0] == export_project_id)
                                
                                # Proposer le téléchargement
                                st.download_button(
                                    label="Télécharger le projet exporté",
                                    data=export_data,
                                    file_name=f"{project_name.replace(' ', '_')}_export.zip",
                                    mime="application/zip"
                                )
                            else:
                                st.error("Erreur lors de l'exportation du projet.")
            
            with col2:
                st.markdown("### Importer un Projet")
                
                # Uploader un fichier ZIP
                uploaded_file = st.file_uploader("Sélectionner un fichier ZIP de projet", type=["zip"], key="import_project_file")
                
                if uploaded_file is not None:
                    # Option pour renommer le projet
                    new_name = st.text_input("Nouveau nom pour le projet (facultatif)", key="import_project_name")
                    
                    # Bouton pour importer le projet
                    if st.button("Importer le projet", key="import_project_button"):
                        with st.spinner("Importation en cours..."):
                            project_id = self.import_project(uploaded_file, new_name)
                            if project_id:
                                st.success(f"Projet importé avec succès (ID: {project_id}).")
                                # Actualiser l'historique
                                self.load_project_history()
                                st.rerun()
                            else:
                                st.error("Erreur lors de l'importation du projet.")
        
        # Création d'un quatrième onglet pour les fonctionnalités avancées
        tab4 = st.tabs(["Fonctionnalités Avancées"])[0]
        
        with tab4:
            st.markdown("<h3 class='sub-header'>Fonctionnalités Avancées</h3>", unsafe_allow_html=True)
            
            # Créer des sections pour les différentes fonctionnalités avancées
            advanced_tab1, advanced_tab2, advanced_tab3 = st.tabs(["Duplication de Projet", "Comparaison de Projets", "Recherche Avancée"])
            
            with advanced_tab1:
                st.markdown("### Duplication de Projet")
                st.markdown("""
                Cette fonctionnalité vous permet de créer une copie d'un projet existant avec un nouveau nom.
                C'est utile pour créer des variantes d'un projet sans modifier l'original.
                """)
                
                # Sélectionner un projet à dupliquer
                if not st.session_state.project_history:
                    st.info("Aucun projet disponible pour la duplication.")
                else:
                    # Créer une liste des projets
                    project_options = []
                    for project_id, manifest in st.session_state.project_history.items():
                        project_options.append((project_id, manifest['name']))
                    
                    # Trier par nom
                    project_options.sort(key=lambda x: x[1])
                    
                    # Sélectionner un projet
                    duplicate_project_id = st.selectbox(
                        "Sélectionner un projet à dupliquer",
                        options=[p[0] for p in project_options],
                        format_func=lambda x: next(p[1] for p in project_options if p[0] == x),
                        key="duplicate_project_id"
                    )
                    
                    # Option pour le nouveau nom
                    original_name = next(p[1] for p in project_options if p[0] == duplicate_project_id)
                    duplicate_name = st.text_input(
                        "Nouveau nom pour la copie",
                        value=f"{original_name} - Copie",
                        key="duplicate_project_name"
                    )
                    
                    # Bouton pour dupliquer le projet
                    if st.button("Dupliquer le projet", key="duplicate_project_button"):
                        with st.spinner("Duplication en cours..."):
                            try:
                                # Étape 1 : Exporter le projet
                                export_data = self.export_project(duplicate_project_id)
                                if export_data:
                                    # Étape 2 : Importer le projet avec un nouveau nom
                                    project_id = self.import_project(export_data, duplicate_name)
                                    if project_id:
                                        st.success(f"Projet dupliqué avec succès (ID: {project_id}).")
                                        # Actualiser l'historique
                                        self.load_project_history()
                                        st.rerun()
                                    else:
                                        st.error("Erreur lors de l'importation du projet dupliqué.")
                                else:
                                    st.error("Erreur lors de l'exportation du projet pour la duplication.")
                            except Exception as e:
                                st.error(f"Erreur lors de la duplication du projet : {str(e)}")
            
            with advanced_tab2:
                st.markdown("### Comparaison de Projets")
                st.markdown("""
                Cette fonctionnalité vous permet de comparer deux projets différents pour en analyser les différences
                en termes de configuration, de résultats économiques et d'optimisation.
                """)
                
                # Sélectionner les projets à comparer
                if len(st.session_state.project_history) < 2:
                    st.info("Au moins deux projets sont nécessaires pour effectuer une comparaison.")
                else:
                    # Créer une liste des projets
                    project_options = []
                    for project_id, manifest in st.session_state.project_history.items():
                        project_options.append((project_id, manifest['name']))
                    
                    # Trier par nom
                    project_options.sort(key=lambda x: x[1])
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Sélectionner le premier projet
                        compare_project_id1 = st.selectbox(
                            "Premier projet",
                            options=[p[0] for p in project_options],
                            format_func=lambda x: next(p[1] for p in project_options if p[0] == x),
                            key="compare_project_id1"
                        )
                    
                    with col2:
                        # Sélectionner le deuxième projet
                        remaining_options = [p for p in project_options if p[0] != compare_project_id1]
                        compare_project_id2 = st.selectbox(
                            "Deuxième projet",
                            options=[p[0] for p in remaining_options],
                            format_func=lambda x: next(p[1] for p in project_options if p[0] == x),
                            key="compare_project_id2"
                        )
                    
                    # Bouton pour comparer les projets
                    if st.button("Comparer les projets", key="compare_projects_button"):
                        with st.spinner("Comparaison en cours..."):
                            try:
                                # Récupérer les manifestes des projets
                                manifest1 = st.session_state.project_history[compare_project_id1]
                                manifest2 = st.session_state.project_history[compare_project_id2]
                                
                                # Afficher un tableau comparatif
                                st.markdown("#### Comparaison des Caractéristiques")
                                
                                comparison_data = []
                                comparison_data.append({
                                    "Caractéristique": "Nom du projet",
                                    "Projet 1": manifest1['name'],
                                    "Projet 2": manifest2['name']
                                })
                                
                                comparison_data.append({
                                    "Caractéristique": "Date de création",
                                    "Projet 1": datetime.fromisoformat(manifest1['created_at']).strftime("%d/%m/%Y %H:%M"),
                                    "Projet 2": datetime.fromisoformat(manifest2['created_at']).strftime("%d/%m/%Y %H:%M")
                                })
                                
                                comparison_data.append({
                                    "Caractéristique": "Dernière modification",
                                    "Projet 1": datetime.fromisoformat(manifest1['updated_at']).strftime("%d/%m/%Y %H:%M"),
                                    "Projet 2": datetime.fromisoformat(manifest2['updated_at']).strftime("%d/%m/%Y %H:%M")
                                })
                                
                                # Comparer les données disponibles
                                for feature, label in [
                                    ('has_production_data', "Données de production"),
                                    ('has_consumption_data', "Données de consommation"),
                                    ('has_processed_data', "Données traitées"),
                                    ('has_economic_results', "Résultats économiques"),
                                    ('has_optimization_results', "Résultats d'optimisation"),
                                    ('has_monte_carlo_results', "Résultats Monte Carlo")
                                ]:
                                    comparison_data.append({
                                        "Caractéristique": label,
                                        "Projet 1": "✅" if manifest1.get(feature, False) else "❌",
                                        "Projet 2": "✅" if manifest2.get(feature, False) else "❌"
                                    })
                                
                                # Afficher le tableau comparatif
                                df_comparison = pd.DataFrame(comparison_data)
                                st.dataframe(df_comparison, use_container_width=True)
                                
                                # Comparer les résultats d'optimisation si disponibles dans les deux projets
                                if manifest1.get('has_optimization_results', False) and manifest2.get('has_optimization_results', False):
                                    st.markdown("#### Comparaison des Résultats d'Optimisation")
                                    
                                    # Charger les résultats d'optimisation
                                    with open(os.path.join('projects', compare_project_id1, 'optimization_results.json'), 'r') as f:
                                        optimization1 = json.load(f)
                                    
                                    with open(os.path.join('projects', compare_project_id2, 'optimization_results.json'), 'r') as f:
                                        optimization2 = json.load(f)
                                    
                                    # Extraire les scénarios
                                    scenarios1 = list(optimization1.keys())
                                    scenarios2 = list(optimization2.keys())
                                    
                                    # Trouver les scénarios communs
                                    common_scenarios = set(scenarios1).intersection(set(scenarios2))
                                    
                                    if common_scenarios:
                                        # Sélectionner un scénario commun
                                        common_scenario = st.selectbox(
                                            "Sélectionner un scénario commun",
                                            options=list(common_scenarios),
                                            key="compare_scenario"
                                        )
                                        
                                        # Comparer les résultats pour ce scénario
                                        results1 = optimization1[common_scenario]
                                        results2 = optimization2[common_scenario]
                                        
                                        # Créer un tableau comparatif
                                        optim_comparison = []
                                        
                                        optim_comparison.append({
                                            "Indicateur": "Prix optimal (€/kWh)",
                                            "Projet 1": f"{results1['prix_optimal']:.4f}",
                                            "Projet 2": f"{results2['prix_optimal']:.4f}",
                                            "Différence": f"{results2['prix_optimal'] - results1['prix_optimal']:.4f}"
                                        })
                                        
                                        indic1 = results1['indicateurs_optimaux']
                                        indic2 = results2['indicateurs_optimaux']
                                        
                                        optim_comparison.append({
                                            "Indicateur": "ROI (%)",
                                            "Projet 1": f"{indic1['roi']*100:.2f}%",
                                            "Projet 2": f"{indic2['roi']*100:.2f}%",
                                            "Différence": f"{(indic2['roi'] - indic1['roi'])*100:.2f}%"
                                        })
                                        
                                        if indic1.get('irr') is not None and indic2.get('irr') is not None:
                                            optim_comparison.append({
                                                "Indicateur": "TRI (%)",
                                                "Projet 1": f"{indic1['irr']*100:.2f}%",
                                                "Projet 2": f"{indic2['irr']*100:.2f}%",
                                                "Différence": f"{(indic2['irr'] - indic1['irr'])*100:.2f}%"
                                            })
                                        
                                        optim_comparison.append({
                                            "Indicateur": "VAN (€)",
                                            "Projet 1": f"{indic1['npv']:,.2f}",
                                            "Projet 2": f"{indic2['npv']:,.2f}",
                                            "Différence": f"{indic2['npv'] - indic1['npv']:,.2f}"
                                        })
                                        
                                        optim_comparison.append({
                                            "Indicateur": "DSCR moyen",
                                            "Projet 1": f"{indic1['avg_dscr']:.2f}",
                                            "Projet 2": f"{indic2['avg_dscr']:.2f}",
                                            "Différence": f"{indic2['avg_dscr'] - indic1['avg_dscr']:.2f}"
                                        })
                                        
                                        # Afficher le tableau comparatif
                                        df_optim_comparison = pd.DataFrame(optim_comparison)
                                        st.dataframe(df_optim_comparison, use_container_width=True)
                                    else:
                                        st.info("Aucun scénario commun trouvé entre les deux projets.")
                                else:
                                    st.info("Les résultats d'optimisation ne sont pas disponibles dans les deux projets.")
                            except Exception as e:
                                st.error(f"Erreur lors de la comparaison des projets : {str(e)}")
            
            with advanced_tab3:
                st.markdown("### Recherche Avancée")
                st.markdown("""
                Cette fonctionnalité vous permet de rechercher des projets selon différents critères,
                comme le nom, la date, ou les caractéristiques spécifiques.
                """)
                
                if not st.session_state.project_history:
                    st.info("Aucun projet disponible pour la recherche.")
                else:
                    # Options de recherche
                    search_options = st.multiselect(
                        "Critères de recherche",
                        options=["Nom", "Date", "Caractéristiques"],
                        default=["Nom"],
                        key="search_options"
                    )
                    
                    # Filtres de recherche
                    filters = {}
                    
                    if "Nom" in search_options:
                        filters["name"] = st.text_input("Rechercher par nom", key="search_name")
                    
                    if "Date" in search_options:
                        col1, col2 = st.columns(2)
                        with col1:
                            filters["date_from"] = st.date_input(
                                "Date de début",
                                value=datetime.now() - timedelta(days=30),
                                key="search_date_from"
                            )
                        with col2:
                            filters["date_to"] = st.date_input(
                                "Date de fin",
                                value=datetime.now(),
                                key="search_date_to"
                            )
                    
                    if "Caractéristiques" in search_options:
                        features = st.multiselect(
                            "Caractéristiques requises",
                            options=[
                                "Données de production",
                                "Données de consommation",
                                "Résultats économiques",
                                "Résultats d'optimisation",
                                "Résultats Monte Carlo"
                            ],
                            key="search_features"
                        )
                        
                        # Mapper les caractéristiques aux clés du manifeste
                        feature_map = {
                            "Données de production": "has_production_data",
                            "Données de consommation": "has_consumption_data",
                            "Résultats économiques": "has_economic_results",
                            "Résultats d'optimisation": "has_optimization_results",
                            "Résultats Monte Carlo": "has_monte_carlo_results"
                        }
                        
                        filters["features"] = [feature_map[f] for f in features]
                    
                    # Bouton pour lancer la recherche
                    if st.button("Rechercher", key="search_button"):
                        # Appliquer les filtres
                        filtered_projects = []
                        
                        for project_id, manifest in st.session_state.project_history.items():
                            # Filtrer par nom
                            if "name" in filters and filters["name"] and filters["name"].lower() not in manifest['name'].lower():
                                continue
                            
                            # Filtrer par date
                            if "date_from" in filters and "date_to" in filters:
                                created_date = datetime.fromisoformat(manifest['created_at']).date()
                                if created_date < filters["date_from"] or created_date > filters["date_to"]:
                                    continue
                            
                            # Filtrer par caractéristiques
                            if "features" in filters and filters["features"]:
                                if not all(manifest.get(f, False) for f in filters["features"]):
                                    continue
                            
                            # Ajouter le projet filtré
                            filtered_projects.append({
                                "ID": project_id,
                                "Nom": manifest['name'],
                                "Description": manifest.get('description', ""),
                                "Créé le": datetime.fromisoformat(manifest['created_at']).strftime("%d/%m/%Y %H:%M"),
                                "Modifié le": datetime.fromisoformat(manifest['updated_at']).strftime("%d/%m/%Y %H:%M")
                            })
                        
                        # Afficher les résultats
                        if filtered_projects:
                            st.markdown(f"#### Résultats de la recherche ({len(filtered_projects)} projets trouvés)")
                            df_results = pd.DataFrame(filtered_projects)
                            st.dataframe(df_results, use_container_width=True)
                            
                            # Sélectionner un projet à charger
                            selected_result_id = st.selectbox(
                                "Sélectionner un projet à charger",
                                options=[p["ID"] for p in filtered_projects],
                                format_func=lambda x: next(p["Nom"] for p in filtered_projects if p["ID"] == x),
                                key="search_result_id"
                            )
                            
                            if st.button("Charger le projet sélectionné", key="load_search_result"):
                                with st.spinner("Chargement en cours..."):
                                    if self.load_project(selected_result_id):
                                        st.success(f"Projet '{next(p['Nom'] for p in filtered_projects if p['ID'] == selected_result_id)}' chargé avec succès.")
                                        st.rerun()
                                    else:
                                        st.error("Erreur lors du chargement du projet.")
                        else:
                            st.info("Aucun projet ne correspond aux critères de recherche.")