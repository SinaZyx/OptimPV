"""
Intégration du système DOCX dans l'interface Streamlit OptimPV
Module d'interface pour la génération de rapports DOCX
"""

import io
import tempfile
import os
from datetime import datetime
from typing import Optional, Dict, Any
import traceback

# Import conditionnel de streamlit
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    # Créer un mock minimal pour éviter les erreurs
    class st:
        @staticmethod
        def warning(msg): print(f"⚠️ {msg}")
        @staticmethod
        def error(msg): print(f"❌ {msg}")
        @staticmethod
        def success(msg): print(f"✅ {msg}")
        @staticmethod
        def info(msg): print(f"ℹ️ {msg}")
        class session_state:
            @staticmethod
            def get(key, default=None): return default

# Vérifier d'abord avec le checker autonome
try:
    from .docx_system.standalone_checker import DocxSystemChecker
    DEPENDENCY_MANAGER_AVAILABLE = DocxSystemChecker.get_quick_status()
except:
    DEPENDENCY_MANAGER_AVAILABLE = False

# Import du gestionnaire de dépendances si disponible
if DEPENDENCY_MANAGER_AVAILABLE:
    try:
        from .docx_system.dependency_manager import DocxDependencyManager
    except ImportError:
        DEPENDENCY_MANAGER_AVAILABLE = False

# Import du système DOCX
try:
    from .docx_system.template_based_generator import TemplateBasedGenerator as DocxTemplateGenerator
    from .docx_system.data_extractor import OptimPVDataExtractor
    from .docx_system.commercial_chart_generator import CommercialChartGenerator as DocxChartGenerator
    DOCX_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Système DOCX non disponible: {e}")
    DOCX_SYSTEM_AVAILABLE = False


class DocxIntegrationModule:
    """
    Module d'intégration pour la génération de rapports DOCX
    Interface Streamlit pour le système de templates DOCX
    """
    
    def __init__(self):
        """Initialise le module d'intégration DOCX"""
        self.docx_generator = None
        self.dependency_manager = None
        
        # Initialiser le gestionnaire de dépendances
        if DEPENDENCY_MANAGER_AVAILABLE:
            try:
                self.dependency_manager = DocxDependencyManager()
                print("✅ DOCX INTEGRATION: Gestionnaire de dépendances initialisé")
            except Exception as e:
                print(f"⚠️ DOCX INTEGRATION: Erreur gestionnaire dépendances: {e}")
                self.dependency_manager = None
        
        # Initialiser le générateur DOCX si les dépendances sont disponibles
        if DOCX_SYSTEM_AVAILABLE and self.dependency_manager and self.dependency_manager.is_system_ready():
            try:
                self.docx_generator = DocxTemplateGenerator()
                print("✅ DOCX INTEGRATION: Système DOCX initialisé")
            except Exception as e:
                print(f"❌ DOCX INTEGRATION: Erreur initialisation: {e}")
                self.docx_generator = None
        
        # Cache pour les derniers rapports générés
        self.last_generated_reports = {}
    
    def show_docx_ui(self):
        """Affiche l'interface utilisateur pour la génération DOCX"""
        # Vérifier l'état du système et afficher l'interface appropriée
        if not self.dependency_manager:
            self._show_docx_unavailable_message()
            return
        
        if not self.dependency_manager.is_system_ready():
            self._show_dependency_installation_ui()
            return
        
        if not self.docx_generator:
            self._show_docx_unavailable_message()
            return
        
        # Vérifier les prérequis
        if not self._check_prerequisites():
            return
        
        st.markdown("## 📄 Génération de Rapports DOCX")
        
        # Section de configuration
        self._show_docx_configuration_section()
        
        st.markdown("---")
        
        # Section de génération
        self._show_docx_generation_section()
        
        st.markdown("---")
        
        # Section de téléchargement si rapports disponibles
        self._show_docx_download_section()
    
    def _show_dependency_installation_ui(self):
        """Affiche l'interface d'installation des dépendances"""
        st.warning("📦 Installation des Dépendances DOCX Requise")
        
        if not self.dependency_manager:
            st.error("❌ Gestionnaire de dépendances non disponible")
            return
        
        # Statut des dépendances
        dependency_status = self.dependency_manager.get_dependency_status()
        missing_deps = self.dependency_manager.get_missing_dependencies()
        
        # Affichage du statut
        st.markdown("### 📋 État des Dépendances")
        
        cols = st.columns(len(dependency_status))
        for i, (package, status) in enumerate(dependency_status.items()):
            with cols[i % len(cols)]:
                icon = "✅" if status['installed'] else "❌"
                required_text = " (requis)" if status['required'] else " (optionnel)"
                st.metric(
                    label=f"{icon} {package}",
                    value="Installé" if status['installed'] else "Manquant",
                    help=status['description'] + required_text
                )
        
        if missing_deps:
            st.markdown("### 🔧 Installation Automatique")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.info(f"**{len(missing_deps)} dépendances manquantes** : {', '.join(missing_deps)}")
            
            with col2:
                if st.button("🚀 Installer Automatiquement", type="primary", use_container_width=True):
                    self._install_dependencies_automatically()
            
            with col3:
                if st.button("📋 Instructions Manuelles", type="secondary", use_container_width=True):
                    st.session_state.show_manual_instructions = True
                    st.rerun()
            
            # Instructions manuelles si demandées
            if st.session_state.get('show_manual_instructions', False):
                with st.expander("📋 Instructions d'Installation Manuelle", expanded=True):
                    instructions = self.dependency_manager.get_installation_instructions()
                    st.markdown(instructions)
                    
                    # Script d'installation téléchargeable
                    script = self.dependency_manager.generate_installation_script()
                    st.download_button(
                        label="💾 Télécharger Script d'Installation",
                        data=script,
                        file_name="install_docx_dependencies.sh",
                        mime="text/x-shellscript",
                        help="Script bash pour installer les dépendances"
                    )
                    
                    if st.button("❌ Fermer Instructions"):
                        st.session_state.show_manual_instructions = False
                        st.rerun()
        
        # Mode dégradé
        st.markdown("---")
        st.markdown("### 📄 Mode Dégradé Disponible")
        
        alternatives = self.dependency_manager.get_alternative_formats()
        st.info(f"""
        **En attendant l'installation des dépendances DOCX, vous pouvez utiliser :**
        • {chr(10).join([f'• {alt}' for alt in alternatives])}
        
        Les rapports HTML peuvent être convertis en Word manuellement.
        """)
        
        if st.button("📄 Générer Rapport HTML de Fallback", type="secondary"):
            self._generate_fallback_report()
    
    def _show_docx_unavailable_message(self):
        """Affiche un message si le système DOCX n'est pas disponible"""
        st.error("📄 Système DOCX non disponible")
        
        st.markdown("""
        ### ⚠️ Erreur du Système
        
        Le gestionnaire de dépendances DOCX n'a pas pu être initialisé.
        Cela peut être dû à un problème de configuration ou d'installation.
        
        **Solutions recommandées :**
        1. Redémarrez l'application OptimPV
        2. Vérifiez l'installation Python
        3. Contactez le support technique
        """)
        
        if st.button("🔄 Réessayer", type="secondary"):
            st.rerun()
    
    def _check_prerequisites(self, show_warnings: bool = True) -> bool:
        """Vérifie que tous les prérequis sont remplis"""
        # Vérifier données importées
        if not st.session_state.get('data_imported'):
            if show_warnings:
                st.warning("⚠️ Aucune donnée n'a été importée. Veuillez d'abord importer des données dans l'onglet 'Importation Données'.")
            return False
        
        # Vérifier optimisation effectuée
        has_optimization = (st.session_state.get('constrained_optim_results') or 
                           st.session_state.get('optimization_results') or
                           st.session_state.get('floor_price_results'))
        
        if not has_optimization:
            if show_warnings:
                st.warning("⚠️ Aucune analyse n'a été effectuée. Veuillez d'abord lancer une optimisation dans l'onglet 'Analyse & Optimisation'.")
            return False
        
        return True
    
    def _show_docx_configuration_section(self):
        """Affiche la section de configuration des rapports DOCX"""
        st.markdown("### ⚙️ Configuration du Rapport")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Type de rapport
            report_type = st.selectbox(
                "Type de rapport DOCX",
                options=["commercial", "technique", "financier"],
                index=0,
                help="Sélectionnez le type de rapport à générer"
            )
            
            # Titre personnalisé
            custom_title = st.text_input(
                "Titre du rapport",
                value="Rapport OptimPV - Analyse de Projet",
                help="Titre qui apparaîtra sur la page de garde"
            )
            
            # Nom du client
            client_name = st.text_input(
                "Nom du client",
                value=st.session_state.get('config', {}).get('client_name', ''),
                placeholder="Société ABC / M. Dupont",
                help="Nom du client pour personnalisation"
            )
        
        with col2:
            # Nom du projet
            project_name = st.text_input(
                "Nom du projet",
                value=st.session_state.get('config', {}).get('project_name', 'Projet Solaire'),
                help="Nom/description du projet"
            )
            
            # Options avancées
            st.markdown("**Options avancées :**")
            
            include_charts = st.checkbox(
                "Inclure les graphiques haute résolution",
                value=True,
                help="Génère et intègre les graphiques dans le rapport"
            )
            
            generate_debug = st.checkbox(
                "Générer les données de debug (YAML)",
                value=False,
                help="Exporte les données extraites en format YAML pour debug"
            )
        
        # Stocker la configuration dans la session
        st.session_state.docx_config = {
            'report_type': report_type,
            'custom_title': custom_title,
            'client_name': client_name,
            'project_name': project_name,
            'include_charts': include_charts,
            'generate_debug': generate_debug
        }
        
        # Aperçu de la configuration
        self._show_configuration_preview()
    
    def _show_configuration_preview(self):
        """Affiche un aperçu de la configuration"""
        if 'docx_config' not in st.session_state:
            return
        
        config = st.session_state.docx_config
        
        with st.expander("👁️ Aperçu de la configuration", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Type de rapport", config['report_type'].title())
                st.metric("Graphiques", "Inclus" if config['include_charts'] else "Exclus")
            
            with col2:
                st.metric("Titre", config['custom_title'][:20] + "..." if len(config['custom_title']) > 20 else config['custom_title'])
                st.metric("Debug", "Activé" if config['generate_debug'] else "Désactivé")
            
            with col3:
                st.metric("Client", config['client_name'] or "Non spécifié")
                st.metric("Projet", config['project_name'][:15] + "..." if len(config['project_name']) > 15 else config['project_name'])
    
    def _show_docx_generation_section(self):
        """Affiche la section de génération des rapports"""
        st.markdown("### 🚀 Génération du Rapport DOCX")
        
        if 'docx_config' not in st.session_state:
            st.warning("⚠️ Veuillez d'abord configurer les paramètres du rapport ci-dessus.")
            return
        
        config = st.session_state.docx_config
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("📄 Générer le Rapport DOCX", type="primary", use_container_width=True):
                self._generate_docx_report(config)
        
        with col2:
            # Bouton de prévisualisation des données
            if st.button("👁️ Prévisualiser Données", type="secondary", use_container_width=True):
                self._preview_extracted_data()
        
        with col3:
            # Bouton de test rapide
            if st.button("🧪 Test Rapide", type="secondary", use_container_width=True):
                self._quick_test_docx_system()
    
    def _generate_docx_report(self, config: Dict[str, Any]):
        """Génère le rapport DOCX avec la configuration donnée"""
        try:
            with st.spinner(f"🔄 Génération du rapport {config['report_type']} en cours..."):
                
                # Génération du rapport
                docx_buffer = self.docx_generator.generate_complete_report(
                    report_type=config['report_type'],
                    title=config['custom_title'],
                    client_name=config['client_name'] if config['client_name'] else None,
                    project_name=config['project_name']
                )
                
                if docx_buffer:
                    # Créer un nom de fichier unique
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"rapport_{config['report_type']}_{timestamp}.docx"
                    
                    # Stocker le rapport généré
                    self.last_generated_reports[config['report_type']] = {
                        'buffer': docx_buffer,
                        'filename': filename,
                        'config': config.copy(),
                        'generated_at': datetime.now()
                    }
                    
                    st.success(f"✅ Rapport {config['report_type']} généré avec succès !")
                    st.info(f"📁 Fichier: {filename}")
                    
                    # Génération des données de debug si demandé
                    if config['generate_debug']:
                        self._generate_debug_data()
                    
                    # Forcer l'actualisation pour afficher les boutons de téléchargement
                    st.rerun()
                    
                else:
                    st.error("❌ Erreur lors de la génération du rapport DOCX")
        
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération: {str(e)}")
            with st.expander("🐛 Détails de l'erreur", expanded=False):
                st.code(traceback.format_exc())
    
    def _preview_extracted_data(self):
        """Prévisualise les données extraites"""
        try:
            with st.spinner("🔍 Extraction des données pour prévisualisation..."):
                data_extractor = OptimPVDataExtractor()
                data = data_extractor.extract_all_data()
                
                st.success(f"✅ {len(data)} variables extraites")
                
                with st.expander("📊 Données extraites", expanded=True):
                    # Organiser les données par catégories
                    categories = {
                        "Configuration Projet": [k for k in data.keys() if any(x in k for x in ['project', 'client', 'date', 'duree'])],
                        "Données Énergétiques": [k for k in data.keys() if any(x in k for x in ['consumption', 'production', 'autoconsumption', 'taux'])],
                        "Données Financières": [k for k in data.keys() if any(x in k for x in ['cout', 'economie', 'prix', 'van', 'tri', 'capex', 'opex'])],
                        "Autres": [k for k in data.keys()]
                    }
                    
                    # Supprimer les doublons
                    displayed_keys = set()
                    for cat, keys in categories.items():
                        categories[cat] = [k for k in keys if k not in displayed_keys]
                        displayed_keys.update(categories[cat])
                    
                    # Afficher par catégories
                    for category, keys in categories.items():
                        if keys:
                            st.markdown(f"**{category}:**")
                            for key in keys[:10]:  # Limiter l'affichage
                                value = data[key]
                                if isinstance(value, (int, float)):
                                    if key.endswith('_total') or 'cout' in key or 'economie' in key:
                                        st.text(f"• {key}: {value:,.2f}")
                                    else:
                                        st.text(f"• {key}: {value}")
                                else:
                                    display_value = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                                    st.text(f"• {key}: {display_value}")
                            
                            if len(keys) > 10:
                                st.text(f"... et {len(keys)-10} autres variables")
                            st.text("")
        
        except Exception as e:
            st.error(f"❌ Erreur prévisualisation données: {str(e)}")
    
    def _quick_test_docx_system(self):
        """Test rapide du système DOCX"""
        try:
            with st.spinner("🧪 Test du système DOCX..."):
                # Test d'extraction des données
                data_extractor = OptimPVDataExtractor()
                data = data_extractor.extract_all_data()
                
                # Test de génération des graphiques
                chart_generator = DocxChartGenerator()
                temp_dir = tempfile.mkdtemp()
                chart_generator.output_dir = temp_dir
                charts = chart_generator.generate_all_charts(data)
                
                # Résultats du test
                st.success("✅ Test système DOCX réussi !")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Variables extraites", len(data))
                    st.metric("Données énergétiques", "✅" if data.get('total_consumption', 0) > 0 else "❌")
                
                with col2:
                    st.metric("Graphiques générés", len(charts))
                    st.metric("Optimisation détectée", "✅" if data.get('prix_optimal', 0) > 0 else "❌")
                
                # Nettoyage
                chart_generator.cleanup_charts()
        
        except Exception as e:
            st.error(f"❌ Échec du test: {str(e)}")
            with st.expander("🐛 Détails de l'erreur", expanded=False):
                st.code(traceback.format_exc())
    
    def _show_docx_download_section(self):
        """Affiche la section de téléchargement des rapports générés"""
        if not self.last_generated_reports:
            return
        
        st.markdown("### 💾 Téléchargement des Rapports")
        
        for report_type, report_data in self.last_generated_reports.items():
            
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.text(f"📄 Rapport {report_type.title()}")
                st.caption(f"Généré le {report_data['generated_at'].strftime('%d/%m/%Y à %H:%M')}")
            
            with col2:
                st.download_button(
                    label="💾 Télécharger DOCX",
                    data=report_data['buffer'].getvalue(),
                    file_name=report_data['filename'],
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"download_{report_type}",
                    help=f"Télécharger le rapport {report_type} au format DOCX"
                )
            
            with col3:
                if st.button(f"🔄 Regénérer", key=f"regen_{report_type}", help=f"Regénérer le rapport {report_type}"):
                    config = report_data['config']
                    self._generate_docx_report(config)
            
            with col4:
                if st.button(f"🗑️ Supprimer", key=f"delete_{report_type}", help=f"Supprimer le rapport {report_type} du cache"):
                    del self.last_generated_reports[report_type]
                    st.rerun()
        
        # Bouton de nettoyage global
        if len(self.last_generated_reports) > 1:
            if st.button("🧹 Nettoyer tous les rapports", type="secondary"):
                self.last_generated_reports.clear()
                st.success("✅ Cache des rapports nettoyé")
                st.rerun()
    
    def _generate_debug_data(self):
        """Génère les données de debug en format YAML"""
        try:
            data_extractor = OptimPVDataExtractor()
            data = data_extractor.extract_all_data()
            
            # Conversion en YAML simple (sans dépendance externe)
            yaml_content = "# Données extraites OptimPV - Debug\n"
            yaml_content += f"# Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n\n"
            
            for key, value in data.items():
                if isinstance(value, str):
                    yaml_content += f"{key}: \"{value}\"\n"
                elif isinstance(value, (list, dict)):
                    yaml_content += f"{key}: {str(value)}\n"
                else:
                    yaml_content += f"{key}: {value}\n"
            
            # Proposer le téléchargement
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"optimpv_debug_data_{timestamp}.yaml"
            
            st.download_button(
                label="📥 Télécharger Données Debug (YAML)",
                data=yaml_content,
                file_name=filename,
                mime="text/yaml",
                help="Télécharger les données extraites pour debug"
            )
            
        except Exception as e:
            st.warning(f"⚠️ Impossible de générer les données de debug: {e}")
    
    def add_docx_to_existing_interface(self, report_module):
        """
        Ajoute les options DOCX à une interface de rapport existante
        
        Args:
            report_module: Module de rapport existant (CustomerReportingModule, etc.)
        """
        if not DOCX_SYSTEM_AVAILABLE or not self.docx_generator:
            return
        
        st.markdown("---")
        st.markdown("### 📄 Export DOCX Professionnel")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info("""
            **Nouveau :** Générez des rapports Word professionnels avec :
            • Mise en forme corporate OptimPV
            • Graphiques haute résolution intégrés
            • Templates modifiables par l'équipe marketing
            """)
        
        with col2:
            if st.button("📄 Générer DOCX", type="secondary", use_container_width=True):
                # Configuration rapide
                config = {
                    'report_type': 'commercial',
                    'custom_title': 'Rapport Client OptimPV',
                    'client_name': '',
                    'project_name': st.session_state.get('config', {}).get('project_name', 'Projet Solaire'),
                    'include_charts': True,
                    'generate_debug': False
                }
                
                self._generate_docx_report(config)
    
    def _install_dependencies_automatically(self):
        """Installe automatiquement les dépendances manquantes"""
        if not self.dependency_manager:
            st.error("❌ Gestionnaire de dépendances non disponible")
            return
        
        missing_deps = self.dependency_manager.get_missing_dependencies()
        
        if not missing_deps:
            st.success("✅ Toutes les dépendances sont déjà installées !")
            return
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = {}
        total_deps = len(missing_deps)
        
        for i, package in enumerate(missing_deps):
            progress = (i + 1) / total_deps
            progress_bar.progress(progress)
            status_text.text(f"Installation de {package}...")
            
            success, message = self.dependency_manager.install_package(package)
            results[package] = (success, message)
        
        progress_bar.empty()
        status_text.empty()
        
        # Afficher les résultats
        st.markdown("### 📊 Résultats de l'Installation")
        
        success_count = 0
        for package, (success, message) in results.items():
            if success:
                st.success(message)
                success_count += 1
            else:
                st.error(message)
        
        if success_count == total_deps:
            st.balloons()
            st.success(f"🎉 Toutes les dépendances ({success_count}/{total_deps}) ont été installées avec succès !")
            st.info("🔄 **Redémarrez OptimPV** pour activer le système DOCX complet.")
            
            if st.button("🔄 Redémarrer Interface DOCX", type="primary"):
                # Réinitialiser le module
                self.__init__()
                st.rerun()
        else:
            st.warning(f"⚠️ Installation partielle : {success_count}/{total_deps} dépendances installées.")
            st.info("Consultez les instructions manuelles pour les packages non installés.")
    
    def _generate_fallback_report(self):
        """Génère un rapport de fallback en HTML"""
        try:
            if not self.dependency_manager:
                st.error("❌ Gestionnaire de dépendances non disponible")
                return
            
            with st.spinner("📄 Génération du rapport HTML de fallback..."):
                
                # Extraire les données basiques
                try:
                    from .docx_system.data_extractor import OptimPVDataExtractor
                    extractor = OptimPVDataExtractor()
                    data = extractor.extract_all_data()
                except ImportError:
                    # Fallback avec données minimales de session
                    data = {
                        'project_name': st.session_state.get('config', {}).get('project_name', 'Projet OptimPV'),
                        'client_name': 'Client OptimPV',
                        'puissance_kwc_total': 25.0,
                        'prix_optimal': 0.16,
                        'economie_totale_finale': 8000,
                        'duree_projet': 20,
                        'generated_datetime': datetime.now().strftime('%d/%m/%Y à %H:%M')
                    }
                
                # Générer le rapport HTML de fallback
                html_report = self.dependency_manager.create_fallback_report(data, "commercial")
                
                # Proposer le téléchargement
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"rapport_fallback_optimpv_{timestamp}.html"
                
                st.success("✅ Rapport HTML de fallback généré !")
                
                # Aperçu
                with st.expander("👁️ Aperçu du Rapport", expanded=False):
                    st.components.v1.html(html_report, height=400, scrolling=True)
                
                # Téléchargement
                st.download_button(
                    label="💾 Télécharger Rapport HTML",
                    data=html_report,
                    file_name=filename,
                    mime="text/html",
                    help="Rapport HTML compatible avec tous les navigateurs"
                )
                
        except Exception as e:
            st.error(f"❌ Erreur génération rapport fallback: {str(e)}")
            with st.expander("🐛 Détails de l'erreur"):
                st.code(traceback.format_exc())
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retourne le statut du système DOCX"""
        # Le système est disponible si on a le gestionnaire de dépendances
        system_available = DEPENDENCY_MANAGER_AVAILABLE and self.dependency_manager is not None
        dependencies_ready = self.dependency_manager.is_system_ready() if self.dependency_manager else False
        # Check prerequisites without showing warnings
        prerequisites_ok = self._check_prerequisites(show_warnings=False) if system_available else False
        
        return {
            'available': system_available,
            'dependencies_ready': dependencies_ready,
            'generator_ready': self.docx_generator is not None,
            'reports_cached': len(self.last_generated_reports),
            'prerequisites_ok': prerequisites_ok,
            'can_install': system_available and not dependencies_ready
        }