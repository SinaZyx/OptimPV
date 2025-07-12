#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de gestion des tooltips interactifs pour la cartographie.
Fournit une solution alternative pour l'interaction avec les informations des parcelles.
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class InteractiveTooltipHandler:
    """Gestionnaire de tooltips interactifs pour la carte de prospection."""
    
    def __init__(self):
        """Initialise le gestionnaire de tooltips."""
        if 'selected_parcel' not in st.session_state:
            st.session_state.selected_parcel = None
        if 'tooltip_visible' not in st.session_state:
            st.session_state.tooltip_visible = False
    
    def show_parcel_details(self, parcel_data: Dict[str, Any], position: str = "sidebar"):
        """
        Affiche les détails d'une parcelle de manière interactive.
        
        Args:
            parcel_data: Dictionnaire contenant les données de la parcelle
            position: "sidebar" ou "main" pour l'emplacement de l'affichage
        """
        if position == "sidebar":
            container = st.sidebar
        else:
            container = st
        
        with container.container():
            # En-tête avec bouton de fermeture
            col1, col2 = container.columns([4, 1])
            with col1:
                container.subheader("🏢 Détails de la Parcelle")
            with col2:
                if container.button("✖", key="close_tooltip", help="Fermer"):
                    st.session_state.selected_parcel = None
                    st.session_state.tooltip_visible = False
                    st.rerun()
            
            # Informations principales
            container.write("---")
            
            # Commune
            container.write(f"**📍 Commune :** {parcel_data.get('nom_commune', 'Inconnue')}")
            
            # Adresse
            container.write(f"**🏠 Adresse :** {parcel_data.get('adresse', 'Non disponible')}")
            
            # Nombre de logements
            container.write(f"**🏘️ Logements :** {parcel_data.get('nombre_de_logements', 0)}")
            
            # Consommation
            consommation_kwh = parcel_data.get('consommation_kwh', 0)
            consommation_mwh = consommation_kwh / 1000
            
            container.metric(
                label="⚡ Consommation annuelle",
                value=f"{consommation_kwh:,.0f} kWh",
                delta=f"{consommation_mwh:.1f} MWh"
            )
            
            # Boutons d'action
            container.write("---")
            container.write("**🗺️ Actions :**")
            
            col1, col2 = container.columns(2)
            
            latitude = parcel_data.get('latitude', 0)
            longitude = parcel_data.get('longitude', 0)
            
            with col1:
                # Lien Google Earth
                earth_url = f"https://earth.google.com/web/search/{latitude},{longitude}"
                if container.button("🌍 Vue 3D", key="earth_view", use_container_width=True):
                    self._open_url(earth_url)
            
            with col2:
                # Lien Google Maps
                maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"
                if container.button("🗺️ Maps", key="maps_view", use_container_width=True):
                    self._open_url(maps_url)
            
            # Informations supplémentaires
            with container.expander("📊 Plus d'informations"):
                info_df = pd.DataFrame({
                    'Propriété': ['Latitude', 'Longitude', 'Code Commune', 'Index'],
                    'Valeur': [
                        f"{latitude:.6f}",
                        f"{longitude:.6f}",
                        parcel_data.get('code_commune', 'N/A'),
                        parcel_data.get('object_index', 'N/A')
                    ]
                })
                container.dataframe(info_df, hide_index=True, use_container_width=True)
    
    def _open_url(self, url: str):
        """
        Ouvre une URL dans un nouvel onglet en utilisant JavaScript.
        
        Args:
            url: URL à ouvrir
        """
        js_code = f"""
        <script>
        window.open('{url}', '_blank');
        </script>
        """
        st.components.v1.html(js_code, height=0)
    
    def create_enhanced_tooltip(self, data: pd.DataFrame) -> dict:
        """
        Crée un tooltip amélioré avec support pour l'interaction via session state.
        
        Args:
            data: DataFrame avec les données des parcelles
            
        Returns:
            dict: Configuration du tooltip pour PyDeck
        """
        # Ajouter les colonnes nécessaires
        if 'consommation_mwh' not in data.columns:
            data['consommation_mwh'] = data['consommation_kwh'] / 1000
        
        if 'object_index' not in data.columns:
            data['object_index'] = range(len(data))
        
        # Template HTML simplifié qui stocke l'index de l'objet cliqué
        tooltip_html = '''
        <div style="
            background-color: #ffffff; 
            padding: 15px; 
            border-radius: 8px; 
            border: 2px solid #2c3e50; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.2); 
            font-family: Arial, sans-serif; 
            font-size: 13px;
            max-width: 300px;
            cursor: pointer;
        ">
            <div style="font-weight: bold; color: #2c3e50; margin-bottom: 8px;">
                🏢 Parcelle #{object_index}
            </div>
            
            <div style="margin-bottom: 5px;">
                <b>📍 Commune :</b> {nom_commune}
            </div>
            
            <div style="margin-bottom: 5px;">
                <b>🏠 Adresse :</b> {adresse}
            </div>
            
            <div style="margin-bottom: 5px;">
                <b>⚡ Consommation :</b> {consommation_kwh:,.0f} kWh
            </div>
            
            <div style="margin-top: 10px; padding: 8px; background-color: #e3f2fd; border-radius: 4px; text-align: center; font-weight: bold; color: #1976d2;">
                ℹ️ Cliquez pour plus de détails
            </div>
        </div>
        '''
        
        return {
            'html': tooltip_html,
            'style': {
                'backgroundColor': 'transparent',
                'border': 'none'
            }
        }
    
    def handle_deck_selection(self, deck_widget, data: pd.DataFrame):
        """
        Gère la sélection d'une parcelle sur la carte.
        
        Args:
            deck_widget: Widget PyDeck retourné par st.pydeck_chart
            data: DataFrame original avec toutes les données
        """
        # Cette fonction doit être appelée après l'affichage de la carte
        # pour capturer les événements de clic
        
        if deck_widget and hasattr(deck_widget, 'selected_objects'):
            selected = deck_widget.selected_objects
            if selected and len(selected) > 0:
                # Récupérer l'index de l'objet sélectionné
                selected_index = selected[0].get('object_index')
                if selected_index is not None:
                    # Récupérer les données complètes de la parcelle
                    parcel_data = data.iloc[selected_index].to_dict()
                    
                    # Mettre à jour l'état de la session
                    st.session_state.selected_parcel = parcel_data
                    st.session_state.tooltip_visible = True
                    
                    # Forcer le rerun pour afficher les détails
                    st.rerun()

def integrate_interactive_tooltips(map_data: pd.DataFrame, filtered_data: pd.DataFrame):
    """
    Fonction d'intégration pour ajouter les tooltips interactifs à l'interface.
    
    Args:
        map_data: Données utilisées pour la carte
        filtered_data: Données filtrées complètes
    """
    # Initialiser le gestionnaire
    handler = InteractiveTooltipHandler()
    
    # Si une parcelle est sélectionnée, afficher ses détails
    if st.session_state.get('tooltip_visible') and st.session_state.get('selected_parcel'):
        handler.show_parcel_details(st.session_state.selected_parcel)
    
    return handler