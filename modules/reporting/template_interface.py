"""
Interface simple pour utiliser votre template Word personnalisée
Génère des propositions DOCX avec vos placeholders
"""

import streamlit as st
import io
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Import du générateur de template
try:
    from .docx_system.template_based_generator import TemplateBasedGenerator
    TEMPLATE_GENERATOR_AVAILABLE = True
except ImportError:
    TEMPLATE_GENERATOR_AVAILABLE = False

# Import du gestionnaire de données
try:
    from .commercial_data_handler import CommercialDataHandler
    DATA_HANDLER_AVAILABLE = True
except ImportError:
    try:
        from .archives.commercial_data_handler import CommercialDataHandler
        DATA_HANDLER_AVAILABLE = True
    except ImportError:
        DATA_HANDLER_AVAILABLE = False


class TemplateInterface:
    """Interface simple pour utiliser votre template Word"""
    
    def __init__(self):
        """Initialise l'interface"""
        self.template_generator = None
        self.data_handler = None
        
        if TEMPLATE_GENERATOR_AVAILABLE:
            try:
                self.template_generator = TemplateBasedGenerator()
            except Exception as e:
                st.error(f"Erreur initialisation template : {e}")
        
        if DATA_HANDLER_AVAILABLE:
            try:
                self.data_handler = CommercialDataHandler()
            except Exception as e:
                st.warning(f"Gestionnaire de données non disponible : {e}")
    
    def show_interface(self):
        """Affiche l'interface principale"""
        st.markdown("# 📄 Génération avec Votre Template Word")
        
        if not TEMPLATE_GENERATOR_AVAILABLE:
            st.error("❌ Système de template non disponible. Vérifiez l'installation de python-docx.")
            return
        
        if not self.template_generator:
            st.error("❌ Générateur de template non initialisé.")
            return
        
        # Vérifier que la template existe
        template_path = "/mnt/c/Users/kingc/OptimPV/modules/reporting/templates/Business-Proposal-Template.docx"
        if not os.path.exists(template_path):
            st.error(f"❌ Template non trouvée à : {template_path}")
            st.info("💡 Placez votre template Word à cet emplacement.")
            return
        
        st.success("✅ Template Word détectée !")
        st.info("🎯 **Votre template va être utilisée avec les données de votre projet OptimPV**")
        
        # Configuration
        st.markdown("## ⚙️ Configuration du Document")
        
        col1, col2 = st.columns(2)
        
        with col1:
            client_name = st.text_input(
                "👤 Nom du Client", 
                value=self._get_client_name(),
                placeholder="Nom de votre client"
            )
        
        with col2:
            project_name = st.text_input(
                "🏗️ Nom du Projet", 
                value=self._get_project_name(),
                placeholder="Nom du projet"
            )
        
        # Vérification des données
        self._show_data_status()
        
        st.markdown("---")
        
        # Génération
        st.markdown("## 🚀 Génération du Document")
        
        col_gen1, col_gen2 = st.columns([2, 1])
        
        with col_gen1:
            if st.button("📄 **GÉNÉRER AVEC VOTRE TEMPLATE WORD**", type="primary", use_container_width=True):
                self._generate_document(client_name, project_name)
        
        with col_gen2:
            st.info("💡 Utilisera vos placeholders")
    
    def _get_client_name(self) -> str:
        """Récupère le nom du client depuis les données"""
        try:
            if self.data_handler:
                project_data = self.data_handler.get_all_project_data()
                return project_data.get('client_name', 'Mon Client')
            return st.session_state.get('config', {}).get('client_name', 'Mon Client')
        except:
            return 'Mon Client'
    
    def _get_project_name(self) -> str:
        """Récupère le nom du projet depuis les données"""
        try:
            if self.data_handler:
                project_data = self.data_handler.get_all_project_data()
                return project_data.get('project_name', 'Projet Autoconsommation')
            return st.session_state.get('config', {}).get('project_name', 'Projet Autoconsommation')
        except:
            return 'Projet Autoconsommation'
    
    def _show_data_status(self):
        """Affiche l'état des données disponibles"""
        st.markdown("### 📊 État des Données")
        
        # Vérifier les données disponibles
        has_config = bool(st.session_state.get('config'))
        has_optimization = bool(st.session_state.get('constrained_optim_results') or 
                              st.session_state.get('optimization_results'))
        has_data = bool(st.session_state.get('processed_data') is not None)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status = "✅ OK" if has_config else "❌ Manquant"
            st.metric("Configuration", status)
        
        with col2:
            status = "✅ OK" if has_optimization else "❌ Manquant"
            st.metric("Optimisation", status)
        
        with col3:
            status = "✅ OK" if has_data else "❌ Manquant"
            st.metric("Données Énergétiques", status)
        
        if not (has_config and has_optimization and has_data):
            st.warning("⚠️ Certaines données manquent. Le document sera généré avec des valeurs par défaut.")
    
    def _generate_document(self, client_name: str, project_name: str):
        """Génère le document avec la template"""
        try:
            with st.spinner("🔄 Génération en cours avec votre template..."):
                
                # Générer le document
                doc_bytes = self.template_generator.generate_from_template(
                    client_name=client_name,
                    project_name=project_name
                )
                
                if doc_bytes:
                    # Nom du fichier
                    filename = f"proposition_{client_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                    
                    # Bouton de téléchargement
                    st.success("✅ Document généré avec succès !")
                    
                    st.download_button(
                        label="📥 **TÉLÉCHARGER VOTRE PROPOSITION**",
                        data=doc_bytes,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary",
                        use_container_width=True
                    )
                    
                    st.balloons()
                    
                    # Informations sur le document généré
                    st.info(f"""
                    📄 **Document généré :**
                    - **Template utilisée :** Business-Proposal-Template.docx
                    - **Client :** {client_name}
                    - **Projet :** {project_name}
                    - **Date :** {datetime.now().strftime('%d/%m/%Y à %H:%M')}
                    """)
                    
                else:
                    st.error("❌ Erreur lors de la génération du document")
                    
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération : {str(e)}")
            st.exception(e)


def show_template_interface():
    """Fonction principale pour afficher l'interface"""
    interface = TemplateInterface()
    interface.show_interface()


if __name__ == "__main__":
    # Test en mode standalone
    print("🧪 Test de l'interface template")
    interface = TemplateInterface()
    print("✅ Interface initialisée")