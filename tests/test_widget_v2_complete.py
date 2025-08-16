"""Test complet du widget d'autocomplétion v2."""

import streamlit as st
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.erp_client.ui.components.address_autocomplete_widget_v2 import AddressAutocompleteWidget, render_address_autocomplete_v2

st.set_page_config(page_title="Test Widget V2", layout="wide")

st.title("🧪 Test Widget Autocomplétion V2")

# Test 1: Widget seul (hors formulaire)
st.header("Test 1: Widget hors formulaire")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Widget Classe")
    widget = AddressAutocompleteWidget(key_prefix="test_widget_1")
    result = widget.render()
    
    if result.is_complete():
        st.success("Adresse complète !")
        st.json(result.to_dict())

with col2:
    st.subheader("Fonction de compatibilité")
    street, postal, city, lat, lon = render_address_autocomplete_v2(
        key_prefix="test_compat_1"
    )
    
    if street and postal and city:
        st.success("Adresse sélectionnée !")
        st.write(f"**Rue:** {street}")
        st.write(f"**Code postal:** {postal}")
        st.write(f"**Ville:** {city}")
        if lat and lon:
            st.write(f"**GPS:** {lat:.6f}, {lon:.6f}")

st.divider()

# Test 2: Dans un formulaire
st.header("Test 2: Widget dans un formulaire")

with st.form("test_form"):
    st.subheader("Formulaire avec autocomplétion")
    
    # Autres champs
    nom = st.text_input("Nom du client")
    
    # Widget d'autocomplétion
    street, postal, city, lat, lon = render_address_autocomplete_v2(
        key_prefix="test_form_address"
    )
    
    # Bouton submit
    submitted = st.form_submit_button("Enregistrer", type="primary")
    
    if submitted:
        st.success("Formulaire soumis !")
        data = {
            "nom": nom,
            "adresse": street,
            "code_postal": postal,
            "ville": city,
            "latitude": lat,
            "longitude": lon
        }
        st.json(data)

# Test 3: Mode manuel
st.divider()
st.header("Test 3: Configuration personnalisée")

config = {
    'min_search_length': 2,
    'max_suggestions': 10,
    'show_coordinates': True,
    'show_confidence_score': False,
    'placeholder_text': "Tapez une adresse française...",
    'no_results_text': "Aucune adresse trouvée 😕",
    'error_text': "Oups ! Erreur de recherche 🔍"
}

widget_custom = AddressAutocompleteWidget(
    key_prefix="test_custom",
    config=config
)

result_custom = widget_custom.render()

if result_custom.is_complete():
    st.balloons()
    st.success("Super ! Adresse trouvée avec config personnalisée")
    st.json(result_custom.to_dict())