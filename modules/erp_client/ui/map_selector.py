"""Composant de sélection de coordonnées sur carte interactive.

Ce module fournit une interface de carte permettant à l'utilisateur
de sélectionner précisément l'emplacement d'un client.
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def render_coordinate_selector(
    address: str = "",
    initial_lat: float = 43.60,
    initial_lon: float = 7.06,
    zoom_start: int = 13
) -> Tuple[Optional[float], Optional[float]]:
    """Affiche une carte interactive pour sélectionner des coordonnées.
    
    Args:
        address: Adresse à géocoder initialement
        initial_lat: Latitude initiale (défaut: région de Mougins)
        initial_lon: Longitude initiale
        zoom_start: Niveau de zoom initial
        
    Returns:
        Tuple (latitude, longitude) ou (None, None) si aucune sélection
    """
    st.markdown("### 🗺️ Sélectionnez l'emplacement exact sur la carte")
    
    # Instructions
    with st.expander("📋 Instructions", expanded=True):
        st.info("""
        1. **Cliquez sur la carte** pour placer un marqueur à l'emplacement exact du bâtiment
        2. **Déplacez le marqueur** si nécessaire en cliquant ailleurs
        3. **Zoomez** avec la molette ou les boutons +/- pour plus de précision
        4. Les coordonnées GPS seront automatiquement mises à jour
        """)
    
    # Créer la carte
    m = folium.Map(
        location=[initial_lat, initial_lon],
        zoom_start=zoom_start,
        control_scale=True,
        prefer_canvas=True
    )
    
    # Ajouter les tuiles satellite comme couche par défaut
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Ajouter aussi une couche plan standard
    folium.TileLayer(
        'OpenStreetMap',
        name='Plan',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Ajouter le contrôle de couches
    folium.LayerControl().add_to(m)
    
    # Récupérer les coordonnées depuis session state si disponibles
    if 'selected_coordinates' not in st.session_state:
        st.session_state.selected_coordinates = {'lat': None, 'lon': None}
    
    # Ajouter un marqueur s'il y a des coordonnées initiales ou sélectionnées
    marker_lat = st.session_state.selected_coordinates['lat'] or initial_lat
    marker_lon = st.session_state.selected_coordinates['lon'] or initial_lon
    
    if marker_lat and marker_lon and (marker_lat != 43.60 or marker_lon != 7.06):
        folium.Marker(
            [marker_lat, marker_lon],
            popup="Position sélectionnée",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
    
    # Ajouter un plugin pour permettre le clic sur la carte
    m.add_child(folium.LatLngPopup())
    
    # JavaScript pour capturer les clics
    click_js = """
    <script>
    var lastClickedLat = null;
    var lastClickedLng = null;
    
    document.addEventListener('DOMContentLoaded', function() {
        // Attendre que la carte soit chargée
        setTimeout(function() {
            var mapElement = document.querySelector('.folium-map');
            if (mapElement && mapElement._map) {
                mapElement._map.on('click', function(e) {
                    lastClickedLat = e.latlng.lat;
                    lastClickedLng = e.latlng.lng;
                });
            }
        }, 1000);
    });
    </script>
    """
    m.get_root().html.add_child(folium.Element(click_js))
    
    # Afficher la carte avec interaction
    map_data = st_folium(
        m,
        height=500,
        width=None,
        returned_objects=["all_drawings", "last_object_clicked_popup"],
        key="coordinate_selector",
        feature_group_to_add=folium.FeatureGroup()
    )
    
    # Récupérer les coordonnées cliquées
    selected_lat = None
    selected_lon = None
    
    # Vérifier les données de la carte
    if map_data and 'last_object_clicked_popup' in map_data and map_data['last_object_clicked_popup']:
        try:
            selected_lat = map_data['last_object_clicked_popup']['lat']
            selected_lon = map_data['last_object_clicked_popup']['lng']
            # Stocker dans session state
            st.session_state.selected_coordinates = {'lat': selected_lat, 'lon': selected_lon}
        except Exception as e:
            logger.debug(f"Erreur lors de la récupération des coordonnées: {e}")
    
    # Utiliser les coordonnées de session state si pas de nouveau clic
    if selected_lat is None and st.session_state.selected_coordinates['lat']:
        selected_lat = st.session_state.selected_coordinates['lat']
        selected_lon = st.session_state.selected_coordinates['lon']
    
    # Afficher les coordonnées sélectionnées
    col1, col2 = st.columns(2)
    with col1:
        if selected_lat:
            st.success(f"📍 Latitude: {selected_lat:.6f}")
        else:
            st.info("📍 Latitude: Non définie")
    
    with col2:
        if selected_lon:
            st.success(f"📍 Longitude: {selected_lon:.6f}")
        else:
            st.info("📍 Longitude: Non définie")
    
    return selected_lat, selected_lon


def render_geocoding_assistant(address_parts: dict) -> Tuple[Optional[float], Optional[float]]:
    """Assistant de géocodage avec carte interactive.
    
    Args:
        address_parts: Dictionnaire contenant adresse, code_postal, ville
        
    Returns:
        Tuple (latitude, longitude) ou (None, None)
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
    
    if not full_address.strip():
        st.warning("⚠️ Veuillez entrer une adresse pour afficher la carte")
        return None, None
    
    # Bouton pour géocoder l'adresse
    if st.button("🔍 Localiser l'adresse sur la carte", type="primary"):
        with st.spinner("Recherche de l'adresse..."):
            try:
                from geopy.geocoders import Nominatim
                geolocator = Nominatim(user_agent="optimpv_erp", timeout=10)
                location = geolocator.geocode(f"{full_address}, France")
                
                if location:
                    st.success(f"✅ Adresse trouvée : {location.address}")
                    # Mettre à jour les coordonnées initiales
                    return render_coordinate_selector(
                        address=full_address,
                        initial_lat=location.latitude,
                        initial_lon=location.longitude,
                        zoom_start=17  # Zoom élevé pour sélection précise
                    )
                else:
                    st.error("❌ Adresse non trouvée. Veuillez sélectionner manuellement sur la carte.")
                    return render_coordinate_selector(address=full_address)
                    
            except Exception as e:
                st.error(f"❌ Erreur de géocodage : {str(e)}")
                return render_coordinate_selector(address=full_address)
    
    # Option pour sélectionner manuellement
    if st.checkbox("📍 Sélectionner manuellement sur la carte"):
        return render_coordinate_selector(address=full_address)
    
    return None, None