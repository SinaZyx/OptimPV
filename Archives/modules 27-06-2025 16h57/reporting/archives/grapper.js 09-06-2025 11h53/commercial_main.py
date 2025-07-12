"""
Module principal de génération de rapports commerciaux OptimPV.
Structure modulaire optimisée pour la maintenance.
"""

import streamlit as st
import logging
from datetime import datetime
from typing import Dict, Any

# Imports des sous-modules
from .commercial_data_handler import CommercialDataHandler
from .commercial_ui_handler import CommercialUIHandler
from .grapesjs_editor import GrapesJSEditor
from .html_generator import HTMLGenerator
from .professional_template_generator import ProfessionalTemplateGenerator

logger = logging.getLogger(__name__)

class CommercialCustomerReportModule:
    """Module principal de génération de rapports commerciaux orientés client."""
    
    def __init__(self):
        """Initialise le module de rapport commercial."""
        if 'reports' not in st.session_state:
            st.session_state.reports = {}
        
        # Initialiser les sous-modules
        self.data_handler = CommercialDataHandler()
        self.ui_handler = CommercialUIHandler()
        self.grapesjs_editor = GrapesJSEditor()
        self.html_generator = HTMLGenerator()
        self.professional_template = ProfessionalTemplateGenerator()
        
        logger.info("Module de rapport commercial initialisé")
    
    def show_ui(self):
        """Interface utilisateur principale pour le module de rapport commercial"""
        st.markdown("<h1 class='main-header'>📑 Rapports Commerciaux OptimPV</h1>", unsafe_allow_html=True)
        
        # Interface directe vers l'éditeur de proposition commerciale
        self._show_commercial_proposal_editor()
    
    def _show_commercial_proposal_editor(self):
        """Éditeur de proposition commerciale avec GrapesJS"""
        st.markdown("<h2 class='sub-header'>🎨 Éditeur Visuel de Proposition Commerciale</h2>", unsafe_allow_html=True)
        
        # Récupération automatique des données
        project_data = self.data_handler.get_all_project_data()
        
        if not project_data['is_valid']:
            st.warning("⚠️ Données insuffisantes pour générer une proposition. Veuillez d'abord effectuer une analyse complète.")
            return
        
        # Affichage des données dans la sidebar
        self.ui_handler.show_project_data_sidebar(project_data)
        
        # Interface directe de l'éditeur visuel avec template premium intégré
        self.grapesjs_editor.show_editor(project_data)

        # Section Export
        self._show_export_section(project_data)
    
    def _show_standard_report(self):
        """Affiche l'interface pour le rapport standard"""
        st.markdown("<h2 class='sub-header'>🎯 Rapport Commercial Orienté Client</h2>", unsafe_allow_html=True)
        
        # Vérifier les données
        if not st.session_state.get('data_imported'):
            st.warning("⚠️ Aucune donnée n'a été importée. Veuillez d'abord importer des données dans l'onglet 'Importation Données'.")
            return
        
        # Vérifier qu'une optimisation a été effectuée
        has_optimization = (st.session_state.get('constrained_optim_results') or 
                           st.session_state.get('optimization_results') or
                           st.session_state.get('floor_price_results'))
        
        if not has_optimization:
            st.warning("⚠️ Aucune analyse n'a été effectuée. Veuillez d'abord lancer une optimisation dans l'onglet 'Analyse & Optimisation'.")
            return
        
        # Interface du rapport standard (existante)
        st.info("Interface rapport standard - À implémenter selon besoins")
    
    def _show_professional_template_report(self):
        """Affiche l'interface pour le template professionnel d'autoconsommation."""
        st.markdown("<h2 class='sub-header'>📋 Template Professionnel - Proposition d'Autoconsommation Collective</h2>", unsafe_allow_html=True)
        
        # Vérifier les données
        if not st.session_state.get('data_imported'):
            st.warning("⚠️ Aucune donnée n'a été importée. Veuillez d'abord importer des données dans l'onglet 'Importation Données'.")
            return
        
        # Vérifier qu'une optimisation a été effectuée
        has_optimization = (st.session_state.get('constrained_optim_results') or 
                           st.session_state.get('optimization_results') or
                           st.session_state.get('floor_price_results'))
        
        if not has_optimization:
            st.warning("⚠️ Aucune analyse n'a été effectuée. Veuillez d'abord lancer une optimisation dans l'onglet 'Analyse & Optimisation'.")
            return
        
        # Récupération des données du projet
        project_data = self.data_handler.get_all_project_data()
        
        if not project_data['is_valid']:
            st.error("❌ Données insuffisantes pour générer le rapport professionnel.")
            return
        
        # Configuration des données spécifiques au template
        st.subheader("🎯 Configuration du Rapport")
        
        with st.expander("📝 Informations Client et Projet", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                client_name = st.text_input("Nom du client", value="[NOM DU CLIENT]", key="prof_client_name")
                project_name = st.text_input("Nom du projet", value="Projet Autoconsommation Collective", key="prof_project_name")
                localisation = st.text_input("Localisation installation", value="[Adresse de l'installation]", key="prof_location")
                
            with col2:
                contact_name = st.text_input("Nom du contact commercial", value="Nom et Prénom", key="prof_contact_name")
                contact_title = st.text_input("Titre du contact", value="Responsable Commercial", key="prof_contact_title")
                contact_phone = st.text_input("Téléphone contact", value="01 23 45 67 89", key="prof_contact_phone")
                contact_email = st.text_input("Email contact", value="contact@optimpv.fr", key="prof_contact_email")
        
        with st.expander("⚡ Données Techniques", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                puissance_kwc = st.number_input("Puissance installée (kWc)", value=project_data.get('puissance_kwc', 100.0), min_value=0.0, key="prof_puissance")
                production_annuelle = st.number_input("Production annuelle (kWh)", value=project_data.get('production_annuelle', 110000), min_value=0, key="prof_production")
                
            with col2:
                taux_couverture = st.number_input("Taux de couverture solaire (%)", value=project_data.get('taux_couverture', 30), min_value=0, max_value=100, key="prof_couverture")
                co2_annual = st.number_input("CO2 évité par an (tonnes)", value=project_data.get('co2_avoided_annual', 50.0), min_value=0.0, key="prof_co2")
        
        with st.expander("💰 Conditions Commerciales", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                duree_contrat = st.number_input("Durée du contrat (années)", value=20, min_value=1, max_value=30, key="prof_duree")
                indexation = st.selectbox("Type d'indexation", options=["Fixe", "Indexé sur l'inflation", "Indexé sur l'électricité"], index=0, key="prof_indexation")
                
            with col2:
                date_mise_service = st.text_input("Date de mise en service", value="T2 2025", key="prof_date_service")
        
        # Compilation des données pour le template
        template_data = {
            # Données client
            "client_name": client_name,
            "project_name": project_name,
            "localisation": localisation,
            
            # Données financières depuis l'optimisation
            "prix_optimal": project_data.get('prix_optimal', 15.0),
            "economie_totale": project_data.get('economie_totale', 150000),
            "economie_annuelle": project_data.get('economie_annuelle', 7500),
            "economie_percentage": project_data.get('economie_percentage', 15),
            "cout_annuel_actuel": project_data.get('cout_annuel_actuel', 50000),
            "cout_annuel_avec_solaire": project_data.get('cout_annuel_avec_solaire', 42500),
            "reduction_percentage": project_data.get('reduction_percentage', 15),
            
            # Données techniques
            "puissance_kwc": puissance_kwc,
            "production_annuelle": production_annuelle,
            "taux_couverture": taux_couverture,
            "part_solaire": taux_couverture,
            "equivalent_foyers": int(puissance_kwc / 2.5),  # Estimation standard
            
            # Données environnementales
            "co2_avoided_annual": co2_annual,
            "cars_equivalent": int(co2_annual / 5),  # Estimation standard
            
            # Conditions contractuelles
            "duree_contrat": duree_contrat,
            "indexation": indexation,
            "date_mise_service": date_mise_service,
            
            # Contact
            "contact_name": contact_name,
            "contact_title": contact_title,
            "contact_phone": contact_phone,
            "contact_email": contact_email,
            
            # Informations entreprise
            "company_info": {
                'name': 'OptimPV - Votre Partenaire Énergie',
                'address': '123 Avenue de l\'Énergie Verte\n75001 Paris, France',
                'phone': '01 23 45 67 89',
                'email': 'contact@optimpv.fr',
                'website': 'www.optimpv.fr'
            }
        }
        
        # Bouton de génération
        st.markdown("---")
        st.subheader("📄 Génération du Rapport")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🎯 Générer le Rapport Professionnel", type="primary", use_container_width=True):
                with st.spinner("Génération du rapport en cours..."):
                    try:
                        # Générer le rapport HTML
                        html_content = self.professional_template.generate_report(template_data)
                        
                        # Stocker dans session state
                        st.session_state['professional_report'] = html_content
                        st.session_state['professional_report_data'] = template_data
                        
                        st.success("✅ Rapport professionnel généré avec succès!")
                        
                    except Exception as e:
                        st.error(f"❌ Erreur lors de la génération : {str(e)}")
                        logger.error(f"Erreur génération template professionnel: {e}")
        
        # Section de téléchargement
        if st.session_state.get('professional_report'):
            st.markdown("---")
            st.subheader("📥 Téléchargement")
            
            report_data = st.session_state.get('professional_report_data', {})
            filename = f"proposition_autoconsommation_{report_data.get('client_name', 'client').replace(' ', '_').lower()}.html"
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                st.download_button(
                    "📄 Télécharger HTML",
                    data=st.session_state['professional_report'],
                    file_name=filename,
                    mime="text/html",
                    use_container_width=True
                )
            
            with col2:
                if st.button("👁️ Prévisualiser", use_container_width=True):
                    st.session_state['show_preview'] = True
            
            with col3:
                st.info("💡 Convertir en PDF via navigateur")
        
        # Prévisualisation
        if st.session_state.get('show_preview'):
            st.markdown("---")
            st.subheader("👁️ Prévisualisation du Rapport")
            
            if st.button("❌ Fermer la prévisualisation"):
                st.session_state['show_preview'] = False
                st.rerun()
            
            # Afficher le HTML dans un composant
            st.components.v1.html(
                st.session_state['professional_report'],
                height=800,
                scrolling=True
            )
    
    def _show_export_section(self, project_data: Dict[str, Any]):
        """Section d'export des documents"""
        st.markdown("---")
        st.header("📄 Génération du Document")
        
        # Afficher le template sélectionné
        selected_template = st.session_state.get('selected_template_mode', 'Solaire Standard')
        if selected_template == "Template Premium Turquoise":
            st.info(f"🎨 **Template sélectionné :** {selected_template} - Le document généré utilisera le design turquoise premium")
        else:
            st.info(f"📋 **Template sélectionné :** {selected_template} - Le document généré utilisera le design standard")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎨 Générer la Proposition", type="primary"):
                # Choisir le générateur selon le template sélectionné dans l'éditeur
                selected_template = st.session_state.get('selected_template_mode', 'Solaire Standard')
                
                if selected_template == "Template Premium Turquoise":
                    html_content = self.html_generator.generate_premium_turquoise_proposal(project_data)
                    st.success("✅ Proposition turquoise premium générée avec succès!")
                else:
                    # Pour "Solaire Standard" et "Vierge", utiliser le générateur classique
                    html_content = self.html_generator.generate_complete_proposal(project_data)
                    st.success("✅ Proposition standard générée avec succès!")
                
                st.session_state['solar_proposal'] = html_content

        with col2:
            if st.session_state.get('solar_proposal'):
                st.download_button(
                    "📥 Télécharger HTML",
                    data=st.session_state['solar_proposal'],
                    file_name=f"proposition_solaire_{project_data['client_name'].replace(' ', '_')}.html",
                    mime="text/html"
                )

        # Aperçu
        if st.button("👁️ Aperçu") and st.session_state.get('solar_proposal'):
            with st.expander("Aperçu de la proposition", expanded=True):
                st.components.v1.html(st.session_state['solar_proposal'], height=600, scrolling=True)
    
    # Méthodes de compatibilité avec l'ancien code
    def generate_html_report(self, *args, **kwargs):
        """Génère un rapport HTML commercial"""
        project_data = self.data_handler.get_all_project_data()
        return self.html_generator.generate_complete_proposal(project_data)
    
    def generate_pdf_report(self, *args, **kwargs):
        """Génère un rapport PDF commercial"""
        html_content = self.generate_html_report(*args, **kwargs)
        return html_content
    
    def format_number(self, number, decimals=0):
        """Formate un nombre"""
        return f"{number:,.{decimals}f}".replace(',', ' ')
    
    def format_currency(self, amount):
        """Formate une devise"""
        return f"{amount:,.0f} €".replace(',', ' ')
    
    def format_percentage(self, percentage):
        """Formate un pourcentage"""
        return f"{percentage:.1f}%"