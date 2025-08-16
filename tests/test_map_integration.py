"""Script de test pour l'intégration de la carte dans le formulaire client ERP."""

import streamlit as st
import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.erp_client.ui.map_selector import render_coordinate_selector, render_geocoding_assistant

st.set_page_config(
    page_title="Test Sélection GPS",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ Test de sélection GPS sur carte")

st.markdown("""
Cette page teste l'intégration de la carte interactive pour la sélection
des coordonnées GPS dans le module ERP Client.
""")

# Test 1: Sélecteur de coordonnées simple
st.header("1. Sélecteur de coordonnées simple")
col1, col2 = st.columns([2, 1])

with col1:
    lat1, lon1 = render_coordinate_selector(
        initial_lat=43.60,
        initial_lon=7.06,
        zoom_start=13
    )

with col2:
    st.info("**Coordonnées sélectionnées:**")
    if lat1 and lon1:
        st.success(f"Latitude: {lat1:.6f}")
        st.success(f"Longitude: {lon1:.6f}")
    else:
        st.warning("Aucune sélection")

st.divider()

# Test 2: Assistant de géocodage
st.header("2. Assistant de géocodage avec adresse")

col3, col4 = st.columns([1, 2])

with col3:
    adresse = st.text_input("Adresse", value="")
    code_postal = st.text_input("Code postal", value="")
    ville = st.text_input("Ville", value="")

with col4:
    if adresse or code_postal or ville:
        lat2, lon2 = render_geocoding_assistant({
            'adresse': adresse,
            'code_postal': code_postal,
            'ville': ville
        })
        
        if lat2 and lon2:
            st.success(f"📍 Position trouvée: {lat2:.6f}, {lon2:.6f}")
    else:
        st.info("Entrez une adresse pour tester le géocodage")

st.divider()

# Test 3: Persistance session state
st.header("3. Test de persistance")

if st.button("Afficher l'état de la session"):
    st.json({
        'selected_coordinates': st.session_state.get('selected_coordinates', 'Non défini'),
        'temp_latitude': st.session_state.get('temp_latitude', 'Non défini'),
        'temp_longitude': st.session_state.get('temp_longitude', 'Non défini')
    })

if st.button("Nettoyer la session", type="secondary"):
    keys_to_clean = ['selected_coordinates', 'temp_latitude', 'temp_longitude']
    for key in keys_to_clean:
        if key in st.session_state:
            del st.session_state[key]
    st.success("Session nettoyée!")
    st.rerun()

# Instructions
with st.sidebar:
    st.markdown("""
    ## 📋 Instructions de test
    
    ### Test 1: Sélection simple
    1. Cliquez sur la carte pour placer un marqueur
    2. Vérifiez que les coordonnées s'affichent
    3. Basculez entre vue Satellite et Plan
    
    ### Test 2: Géocodage
    1. Entrez une adresse complète
    2. Cliquez sur "Localiser l'adresse"
    3. Affinez la position sur la carte
    
    ### Test 3: Persistance
    1. Sélectionnez une position
    2. Cliquez sur "Afficher l'état"
    3. Vérifiez la persistance
    
    ### Notes
    - La carte utilise vue satellite par défaut
    - Les coordonnées sont en WGS84
    - Le zoom est optimisé pour la sélection de bâtiments
    """)

# Footer
st.markdown("---")
st.caption("Test d'intégration carte ERP Client - OptimPV")