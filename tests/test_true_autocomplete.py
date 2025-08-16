"""Test de la vraie autocomplétion en temps réel."""

import streamlit as st
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.erp_client.ui.components.true_autocomplete_widget import (
    TrueAutocompleteWidget, 
    render_true_autocomplete,
    FormCompatibleAutocomplete
)

st.set_page_config(page_title="Test Vraie Autocomplétion", layout="wide")

st.title("🚀 Test Vraie Autocomplétion en Temps Réel")
st.markdown("Cette version affiche des suggestions **pendant que vous tapez**, comme sur les vrais sites web!")

# Test 1: Widget standalone
st.header("1️⃣ Autocomplétion Temps Réel")
st.info("Commencez à taper une adresse (min 3 caractères) pour voir les suggestions apparaître automatiquement")

result = render_true_autocomplete(
    key="test_auto_1",
    placeholder="Ex: 386 avenue saint basile",
    min_chars=3
)

if result:
    st.success("Vous avez sélectionné:")
    st.json(result)

# Séparateur
st.divider()

# Test 2: Dans un formulaire
st.header("2️⃣ Version Compatible Formulaire")

with st.form("test_form_auto"):
    st.subheader("Formulaire avec Autocomplétion")
    
    # Autres champs
    nom = st.text_input("Nom du client", placeholder="Jean Dupont")
    email = st.text_input("Email", placeholder="jean@example.com")
    
    st.markdown("---")
    
    # Widget d'autocomplétion pour formulaire
    form_widget = FormCompatibleAutocomplete(key="form_auto_1")
    adresse, cp, ville, lat, lon = form_widget.render_in_form()
    
    st.markdown("---")
    
    # Bouton submit
    submitted = st.form_submit_button("💾 Enregistrer", type="primary")
    
    if submitted:
        if adresse and cp and ville:
            st.success("✅ Formulaire enregistré!")
            data = {
                "nom": nom,
                "email": email,
                "adresse": adresse,
                "code_postal": cp,
                "ville": ville,
                "latitude": lat,
                "longitude": lon
            }
            st.json(data)
        else:
            st.error("Veuillez sélectionner une adresse")

# Test 3: Multiple widgets
st.divider()
st.header("3️⃣ Multiples Widgets")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Adresse de livraison")
    livraison = render_true_autocomplete(
        key="livraison_auto",
        placeholder="Adresse de livraison...",
        min_chars=3
    )
    if livraison:
        st.info(f"📦 {livraison['label']}")

with col2:
    st.subheader("Adresse de facturation")
    facturation = render_true_autocomplete(
        key="facturation_auto",
        placeholder="Adresse de facturation...",
        min_chars=3
    )
    if facturation:
        st.info(f"💳 {facturation['label']}")

# Instructions
st.divider()
st.markdown("""
### 📖 Comment ça marche ?

1. **Autocomplétion temps réel** : Les suggestions apparaissent automatiquement après 3 caractères
2. **Debounce intégré** : Attente de 300ms après la dernière frappe avant de chercher
3. **Mise en surbrillance** : Le texte recherché est mis en **gras** dans les suggestions
4. **Score de confiance** : Chaque suggestion affiche son score de pertinence
5. **Compatible formulaires** : Version spéciale pour les `st.form()`

### 🎯 Différences avec la v2

| Fonctionnalité | Widget v2 | Vraie Autocomplétion |
|----------------|-----------|---------------------|
| Suggestions | Après recherche manuelle | En temps réel |
| Interface | Radio + Selectbox | Suggestions cliquables |
| Expérience | Comme un formulaire | Comme Google/Amazon |
| Performance | Une recherche à la fois | Debounce intelligent |
""")

# Debug info
with st.expander("🐛 Debug Info"):
    st.write("Session State Keys:")
    for key in st.session_state:
        if "auto" in key:
            st.write(f"- {key}: {st.session_state[key]}")