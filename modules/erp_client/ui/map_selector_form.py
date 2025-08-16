"""Composant de sélection de coordonnées sur carte pour formulaires.

Version adaptée pour fonctionner à l'intérieur d'un st.form().
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def render_map_in_form(
    address_parts: dict,
    initial_lat: Optional[float] = None,
    initial_lon: Optional[float] = None
) -> Tuple[Optional[float], Optional[float]]:
    """Affiche une carte pour sélection de coordonnées compatible avec st.form.
    
    Args:
        address_parts: Dictionnaire avec adresse, code_postal, ville
        initial_lat: Latitude initiale
        initial_lon: Longitude initiale
        
    Returns:
        Tuple (latitude, longitude) sélectionnées
    """
    # Construire l'adresse complète
    address_components = []
    if address_parts.get('adresse'):
        address_components.append(address_parts['adresse'])
    if address_parts.get('code_postal'):
        address_components.append(address_parts['code_postal'])
    if address_parts.get('ville'):
        address_components.append(address_parts['ville'])
    
    full_address = ", ".join(address_components)
    
    st.info("💡 Après avoir rempli le formulaire, vous pourrez sélectionner précisément l'emplacement sur une carte")
    
    # Si on a déjà des coordonnées, les afficher
    if initial_lat and initial_lon:
        st.success(f"📍 Position actuelle : {initial_lat:.6f}, {initial_lon:.6f}")
    
    # Stocker l'adresse pour utilisation après soumission
    if 'pending_geocoding' not in st.session_state:
        st.session_state.pending_geocoding = False
    
    if full_address.strip():
        st.session_state.pending_address = full_address
        st.markdown(f"**Adresse à localiser :** {full_address}")
    
    return initial_lat, initial_lon