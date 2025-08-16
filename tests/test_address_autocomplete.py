"""Script de test pour l'autocomplétion d'adresse.

Ce script permet de tester rapidement la fonctionnalité d'autocomplétion
d'adresse sans avoir à naviguer dans toute l'application.
"""

import streamlit as st
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from modules.erp_client.services.address_autocomplete import get_address_service
from modules.erp_client.ui.components.address_autocomplete_widget import (
    render_address_autocomplete,
    render_simple_address_search
)


def main():
    st.set_page_config(
        page_title="Test Autocomplétion Adresse",
        page_icon="🏠",
        layout="wide"
    )
    
    st.title("🏠 Test de l'Autocomplétion d'Adresse")
    st.markdown("---")
    
    # Test du service directement
    st.header("1️⃣ Test du Service d'Autocomplétion")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Recherche directe via l'API", placeholder="Ex: 10 rue de la paix paris")
    with col2:
        search_button = st.button("🔍 Rechercher", use_container_width=True)
    
    if search_button and len(query) >= 3:
        service = get_address_service()
        with st.spinner("Recherche en cours..."):
            suggestions = service.search_addresses(query, limit=10)
        
        if suggestions:
            st.success(f"✅ {len(suggestions)} résultats trouvés")
            
            for i, suggestion in enumerate(suggestions):
                with st.expander(f"📍 {suggestion.display_label} (Score: {suggestion.score:.2f})"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write("**Adresse:**", suggestion.street)
                        st.write("**Code postal:**", suggestion.postcode)
                    with col2:
                        st.write("**Ville:**", suggestion.city)
                        st.write("**Code INSEE:**", suggestion.citycode)
                    with col3:
                        st.write("**Latitude:**", f"{suggestion.latitude:.6f}")
                        st.write("**Longitude:**", f"{suggestion.longitude:.6f}")
                    
                    # Zone géographique
                    zone = service.parse_zone_from_postcode(suggestion.postcode)
                    st.info(f"🗺️ Zone: {zone}")
        else:
            st.warning("Aucun résultat trouvé")
    
    st.markdown("---")
    
    # Test du widget complet
    st.header("2️⃣ Test du Widget Complet d'Autocomplétion")
    
    def on_address_selected(suggestion):
        st.balloons()
        st.success(f"Adresse sélectionnée: {suggestion.display_label}")
    
    adresse, code_postal, ville, latitude, longitude = render_address_autocomplete(
        key_prefix="test_widget",
        on_address_selected=on_address_selected,
        show_coordinates=True
    )
    
    # Affichage des résultats
    if adresse:
        st.markdown("### Résultats de la sélection:")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Adresse:** {adresse}")
            st.info(f"**Code postal:** {code_postal}")
            st.info(f"**Ville:** {ville}")
        with col2:
            if latitude and longitude:
                st.success(f"**Latitude:** {latitude:.6f}")
                st.success(f"**Longitude:** {longitude:.6f}")
                
                # Lien vers Google Maps
                maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"
                st.markdown(f"[🗺️ Voir sur Google Maps]({maps_url})")
    
    st.markdown("---")
    
    # Test du widget simple
    st.header("3️⃣ Test du Widget Simple")
    
    selected = render_simple_address_search(
        label="Recherche rapide d'adresse",
        key="simple_test"
    )
    
    if selected:
        st.success(f"Sélection: {selected.display_label}")
        st.json({
            "street": selected.street,
            "postcode": selected.postcode,
            "city": selected.city,
            "coordinates": [selected.latitude, selected.longitude]
        })
    
    # Informations sur l'API
    with st.sidebar:
        st.header("ℹ️ Informations")
        st.info(
            "Cette fonctionnalité utilise l'API officielle du gouvernement français "
            "(api-adresse.data.gouv.fr) qui est:\n\n"
            "- ✅ Gratuite et sans limite\n"
            "- ✅ Sans inscription requise\n"
            "- ✅ Données officielles\n"
            "- ✅ Mise à jour régulièrement"
        )
        
        st.markdown("### 📊 Statistiques de test")
        if 'test_count' not in st.session_state:
            st.session_state.test_count = 0
        
        if st.button("Incrémenter compteur"):
            st.session_state.test_count += 1
        
        st.metric("Nombre de tests", st.session_state.test_count)


if __name__ == "__main__":
    main()