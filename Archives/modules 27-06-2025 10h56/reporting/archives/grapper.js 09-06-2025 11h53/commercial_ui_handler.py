"""
Module de gestion de l'interface utilisateur pour les rapports commerciaux OptimPV.
Gère l'affichage et les interactions utilisateur.
"""

import streamlit as st
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class CommercialUIHandler:
    """Gestionnaire de l'interface utilisateur pour les rapports commerciaux."""
    
    def __init__(self):
        """Initialise le gestionnaire UI."""
        pass
    
    def show_project_data_sidebar(self, project_data: Dict[str, Any]):
        """
        Affiche les données du projet dans la sidebar.
        
        Args:
            project_data: Données consolidées du projet
        """
        with st.sidebar:
            st.header("📋 Données du Projet")
            
            st.subheader("👤 Client")
            st.write(f"**Nom :** {project_data['client_name']}")
            
            st.subheader("⚡ Données Énergétiques")
            st.metric("Production annuelle", f"{project_data['total_production']:,} kWh".replace(",", " "))
            st.metric("Consommation", f"{project_data['total_consumption']:,} kWh".replace(",", " "))
            st.metric("Puissance estimée", f"{project_data['power_kwc']} kWc")
            
            st.subheader("💰 Données Financières")
            st.metric("Prix solaire optimal", f"{project_data['solar_price']:.1f} ct/kWh")
            st.metric("Économie annuelle", f"{project_data['annual_savings']:,} €".replace(",", " "))
            st.metric("Économie 20 ans", f"{project_data['total_savings_20y']:,} €".replace(",", " "))
            
            st.subheader("🌱 Impact Environnemental")
            st.metric("CO₂ évité/an", f"{project_data['co2_avoided']} tonnes")
            
            # Informations sur le meilleur scénario
            if project_data.get('best_scenario'):
                st.subheader("🎯 Scénario Optimal")
                st.info(f"**{project_data['best_scenario']}**")
    
    def show_simple_config_mode(self, project_data: Dict[str, Any]):
        """
        Affiche le mode configuration simple.
        
        Args:
            project_data: Données du projet
        """
        st.info("📝 **Mode Configuration Simple** - Ajustez les paramètres si nécessaire")
        
        # Onglets pour l'édition
        tabs = st.tabs([
            "📄 Page de Garde",
            "📋 Résumé Exécutif", 
            "📊 Impact Financier",
            "🔧 Détails Techniques"
        ])
        
        # Tab 1: Page de Garde
        with tabs[0]:
            st.header("Page de Couverture")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Informations principales")
                title = st.text_input("Titre principal", project_data['template']["cover"]["title"])
                subtitle = st.text_area("Sous-titre", 
                    "Proposition personnalisée pour votre transition énergétique", height=80)
                
            with col2:
                st.subheader("Métriques clés")
                st.info(f"""
                **Prix Garanti:** {project_data['solar_price']} ct/kWh  
                **Économie sur 20 ans:** {project_data['total_savings_20y']:,} €  
                **Puissance:** {project_data['power_kwc']} kWc
                """.replace(",", " "))

        # Tab 2: Résumé Exécutif
        with tabs[1]:
            st.header("Résumé Exécutif")
            st.info("💡 Présentez l'opportunité en quelques paragraphes")
            
            summary_text = st.text_area(
                "Contenu du résumé",
                value=project_data['template']["executive_summary"].replace("<p>", "").replace("</p>", "").replace("<strong>", "**").replace("</strong>", "**"),
                height=200
            )

        # Tab 3: Impact Financier
        with tabs[2]:
            st.header("Impact Financier")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Économie annuelle", f"{project_data['annual_savings']:,} €".replace(",", " "))
                st.metric("Pourcentage d'économie", f"{project_data['savings_percentage']}%")
                
            with col2:
                st.metric("Couverture solaire", f"{project_data['solar_coverage']}%")
                st.metric("Production annuelle", f"{project_data['total_production']:,} kWh".replace(",", " "))

        # Tab 4: Détails Techniques
        with tabs[3]:
            st.header("Détails Techniques")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Puissance installée", f"{project_data['power_kwc']} kWc")
                st.metric("CO₂ évité par an", f"{project_data['co2_avoided']} tonnes")
                
            with col2:
                st.metric("Arbres équivalents", f"{project_data['co2_avoided'] * 50} arbres")
                st.metric("Énergie verte", f"{project_data['total_production']//1000} MWh")
    
    def show_data_validation_errors(self, errors: list):
        """
        Affiche les erreurs de validation des données.
        
        Args:
            errors: Liste des erreurs de validation
        """
        st.error("❌ **Erreurs de validation des données :**")
        for error in errors:
            st.write(f"• {error}")
    
    def show_loading_spinner(self, message: str = "Chargement..."):
        """
        Affiche un spinner de chargement.
        
        Args:
            message: Message à afficher pendant le chargement
        """
        return st.spinner(message)
    
    def show_success_message(self, message: str):
        """
        Affiche un message de succès.
        
        Args:
            message: Message de succès
        """
        st.success(f"✅ {message}")
    
    def show_warning_message(self, message: str):
        """
        Affiche un message d'avertissement.
        
        Args:
            message: Message d'avertissement
        """
        st.warning(f"⚠️ {message}")
    
    def show_info_message(self, message: str):
        """
        Affiche un message d'information.
        
        Args:
            message: Message d'information
        """
        st.info(f"ℹ️ {message}")
    
    def create_download_button(self, data: str, filename: str, label: str = "📥 Télécharger"):
        """
        Crée un bouton de téléchargement.
        
        Args:
            data: Données à télécharger
            filename: Nom du fichier
            label: Libellé du bouton
        
        Returns:
            Bouton de téléchargement Streamlit
        """
        return st.download_button(
            label=label,
            data=data,
            file_name=filename,
            mime="text/html"
        )
    
    def create_export_section(self, project_data: Dict[str, Any]):
        """
        Crée la section d'export avec boutons d'action.
        
        Args:
            project_data: Données du projet
        
        Returns:
            Dict avec les états des boutons
        """
        col1, col2, col3 = st.columns(3)
        
        button_states = {}
        
        with col1:
            button_states['generate'] = st.button("🎨 Générer la Proposition", type="primary")
                
        with col2:
            button_states['download'] = st.session_state.get('solar_proposal') is not None
            if button_states['download']:
                self.create_download_button(
                    st.session_state['solar_proposal'],
                    f"proposition_solaire_{project_data['client_name'].replace(' ', '_')}.html",
                    "📥 Télécharger HTML"
                )
                
        with col3:
            button_states['preview'] = st.button("👁️ Aperçu")
            
        return button_states
    
    def show_preview(self, html_content: str, height: int = 600):
        """
        Affiche un aperçu du contenu HTML.
        
        Args:
            html_content: Contenu HTML à afficher
            height: Hauteur de l'aperçu
        """
        with st.expander("Aperçu de la proposition", expanded=True):
            st.components.v1.html(html_content, height=height, scrolling=True)
    
    def get_editor_mode_selection(self) -> str:
        """
        Affiche le sélecteur de mode d'édition.
        
        Returns:
            Mode d'édition sélectionné
        """
        return st.radio(
            "Choisissez votre mode d'édition",
            ["✨ Éditeur Visuel (GrapesJS)", "📝 Mode Configuration Simple"],
            index=0
        )
    
    def show_data_summary(self, project_data: Dict[str, Any]):
        """
        Affiche un résumé des données du projet.
        
        Args:
            project_data: Données du projet
        """
        st.markdown("### 📊 Résumé du Projet")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Client", project_data['client_name'])
            
        with col2:
            st.metric("Économie Annuelle", f"{project_data['annual_savings']:,} €".replace(",", " "))
            
        with col3:
            st.metric("Puissance", f"{project_data['power_kwc']} kWc")
            
        with col4:
            st.metric("CO₂ Évité", f"{project_data['co2_avoided']} T/an")