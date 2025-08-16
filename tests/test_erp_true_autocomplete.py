"""Test de la vraie autocomplétion dans le module ERP."""

import streamlit as st
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.erp_client.ui.client_form import render_client_form
from modules.erp_client.services.client_service import ClientService
from modules.erp_client.models.client import Client

st.set_page_config(page_title="Test ERP - Vraie Autocomplétion", layout="wide")

st.title("🚀 Test Module ERP avec Vraie Autocomplétion")

# Créer un service client
client_service = ClientService()

# Test création nouveau client
st.header("➕ Nouveau Client avec Autocomplétion Temps Réel")

# Afficher le formulaire
new_client = render_client_form(client=None, client_service=client_service)

if new_client:
    st.success(f"✅ Client '{new_client.nom}' créé avec succès!")
    st.json({
        "id": new_client.id,
        "code": new_client.code_client,
        "nom": new_client.nom,
        "adresse": new_client.adresse,
        "code_postal": new_client.code_postal,
        "ville": new_client.ville,
        "latitude": new_client.latitude,
        "longitude": new_client.longitude,
        "zone_geographique": new_client.zone_geographique
    })

# Séparateur
st.divider()

# Instructions
st.markdown("""
### 📖 Comment utiliser la vraie autocomplétion ?

1. **Dans le formulaire ci-dessus**, allez dans la section "📍 Coordonnées"
2. **Cochez "🔍 Rechercher"** dans la section adresse
3. **Commencez à taper** une adresse (ex: "386 avenue saint basile")
4. **Les suggestions apparaissent** automatiquement pendant la frappe
5. **Sélectionnez** l'adresse dans la liste déroulante
6. **Les détails** s'affichent avec GPS, code postal, ville

### 🎯 Différences avec l'ancienne version

| Fonctionnalité | Ancienne Version | Nouvelle Version |
|----------------|------------------|------------------|
| Recherche | Bouton "Rechercher" | Checkbox + Temps réel |
| Suggestions | Après clic bouton | Pendant la frappe |
| Interface | Radio + Selectbox | Recherche + Dropdown |
| Expérience | Plusieurs étapes | Une seule étape fluide |

### ✨ Avantages de la vraie autocomplétion

- **Plus rapide** : Résultats instantanés
- **Plus intuitif** : Comme sur les vrais sites web
- **Compatible formulaires** : Fonctionne dans st.form()
- **GPS automatique** : Coordonnées remplies automatiquement
- **Zone géographique** : Détectée via le code postal
""")

# Test avec client existant
with st.expander("🔧 Test avec client existant"):
    # Lister les clients
    clients = client_service.list_clients()
    
    if clients:
        client_names = [f"{c.code_client} - {c.nom}" for c in clients]
        selected_idx = st.selectbox(
            "Sélectionnez un client à éditer",
            range(len(clients)),
            format_func=lambda x: client_names[x]
        )
        
        if st.button("✏️ Éditer ce client"):
            selected_client = clients[selected_idx]
            st.session_state['edit_client'] = selected_client
            st.rerun()
    
    # Si on édite un client
    if 'edit_client' in st.session_state:
        st.subheader("✏️ Édition avec autocomplétion")
        edited = render_client_form(
            client=st.session_state['edit_client'],
            client_service=client_service
        )
        
        if edited:
            st.success("✅ Client modifié!")
            del st.session_state['edit_client']
            st.rerun()