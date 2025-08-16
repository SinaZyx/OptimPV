"""Interface Streamlit pour le formulaire de gestion des clients.

Ce module fournit les composants UI pour créer et éditer des clients
dans le système ERP.
"""

import streamlit as st
from datetime import datetime
import logging
from typing import Optional, Dict, Any

from ..models.client import Client
from ..services.client_service import ClientService
from .components.address_autocomplete_widget_v2 import render_address_autocomplete_v2
from .components.address_autocomplete_widget import render_address_autocomplete
from .components.true_autocomplete_widget import FormCompatibleAutocomplete

logger = logging.getLogger(__name__)


def render_client_form(client: Optional[Client] = None, client_service: ClientService = None) -> Optional[Client]:
    """Affiche le formulaire de création/édition de client.
    
    Args:
        client: Client existant pour édition (None pour création)
        client_service: Service de gestion des clients
        
    Returns:
        Client créé/modifié ou None si annulé
    """
    if client_service is None:
        client_service = ClientService()
        
    is_edit = client is not None
    
    st.subheader("✏️ Édition client" if is_edit else "➕ Nouveau client")
    
    with st.form("client_form", clear_on_submit=False):
        # D'abord obtenir l'adresse avec autocomplétion (invisible, juste pour récupérer les valeurs)
        # On fait cela en premier pour avoir code_postal disponible
        adresse = None
        code_postal = None
        ville = None
        lat_auto = None
        lon_auto = None
        
        # Colonnes pour la mise en page
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📋 Informations générales")
            
            # Code client
            code_client = st.text_input(
                "Code client *",
                value=client.code_client if is_edit else "",
                max_chars=50,
                help="Code unique du client (sera converti en majuscules)",
                disabled=is_edit  # Ne pas permettre la modification du code
            )
            
            # Nom
            nom = st.text_input(
                "Nom du client *",
                value=client.nom if is_edit else "",
                max_chars=200,
                help="Raison sociale ou nom complet"
            )
            
            # Type de client
            types_client = ['producteur', 'consommateur', 'prosumer']
            type_index = types_client.index(client.type_client) if is_edit else 1
            type_client = st.selectbox(
                "Type de client *",
                options=types_client,
                index=type_index,
                format_func=lambda x: x.capitalize()
            )
            
            # Zone géographique (sera mise à jour après l'autocomplétion)
            zone_geographique = st.text_input(
                "Zone géographique",
                value=client.zone_geographique if is_edit and client.zone_geographique else "",
                help="Sera détectée automatiquement via le code postal de l'adresse",
                key="zone_geo_input"
            )
            
            # Statut
            actif = st.checkbox(
                "Client actif",
                value=client.actif if is_edit else True
            )
            
        with col2:
            st.markdown("### 📍 Coordonnées")
            
            # Widget d'autocomplétion d'adresse avec vraie autocomplétion
            st.markdown("#### 🏠 Adresse avec autocomplétion en temps réel")
            
            # Utiliser le nouveau widget avec vraie autocomplétion
            autocomplete_widget = FormCompatibleAutocomplete(
                key=f"client_form_autocomplete_{client.id if is_edit else 'new'}"
            )
            
            # Si on édite, pré-remplir les valeurs
            if is_edit and client.adresse:
                # Mettre les valeurs existantes dans le state
                state_key = f"client_form_autocomplete_{client.id}_state"
                if state_key not in st.session_state:
                    st.session_state[state_key] = {
                        "search_query": f"{client.adresse} {client.code_postal} {client.ville}",
                        "suggestions": [],
                        "selected_index": 0
                    }
            
            # Afficher le widget
            adresse, code_postal, ville, lat_auto, lon_auto = autocomplete_widget.render_in_form()
            
            # Mise à jour automatique des coordonnées si une adresse a été sélectionnée
            if lat_auto is not None and lon_auto is not None:
                st.session_state.temp_latitude = lat_auto
                st.session_state.temp_longitude = lon_auto
                
            # Téléphone et email
            telephone = st.text_input(
                "Téléphone",
                value=client.telephone if is_edit and client.telephone else "",
                max_chars=20
            )
            
            email = st.text_input(
                "Email",
                value=client.email if is_edit and client.email else "",
                max_chars=200
            )
            
        # Séparateur
        st.markdown("---")
        
        # Informations complémentaires
        with st.expander("📊 Informations complémentaires", expanded=False):
            col3, col4 = st.columns(2)
            
            with col3:
                siret = st.text_input(
                    "SIRET",
                    value=client.siret if is_edit and client.siret else "",
                    max_chars=20,
                    help="14 chiffres (espaces autorisés)"
                )
                
                contact_principal = st.text_input(
                    "Contact principal",
                    value=client.contact_principal if is_edit and client.contact_principal else "",
                    max_chars=200
                )
                
            with col4:
                # Coordonnées GPS
                st.markdown("**Coordonnées GPS**")
                
                # Initialiser les coordonnées dans session state si nécessaire
                if 'temp_latitude' not in st.session_state:
                    st.session_state.temp_latitude = client.latitude if is_edit and client.latitude else None
                if 'temp_longitude' not in st.session_state:
                    st.session_state.temp_longitude = client.longitude if is_edit and client.longitude else None
                
                # Note pour la sélection sur carte
                if adresse or ville or code_postal:
                    if st.session_state.get('temp_latitude') and st.session_state.get('temp_longitude'):
                        st.success("✅ Coordonnées GPS détectées automatiquement via l'autocomplétion")
                    else:
                        st.info("💡 Après création/modification, vous pourrez ajuster précisément la position sur une carte")
                
                # Saisie des coordonnées
                col_lat, col_lon = st.columns(2)
                with col_lat:
                    # Utiliser les coordonnées de l'autocomplétion si disponibles
                    default_lat = st.session_state.get('temp_latitude', 
                                                      client.latitude if is_edit and client.latitude else 0.0)
                    latitude = st.number_input(
                        "Latitude",
                        value=float(default_lat) if default_lat else 0.0,
                        min_value=-90.0,
                        max_value=90.0,
                        format="%.6f",
                        help="Entre -90 et 90 (rempli automatiquement si adresse sélectionnée)"
                    )
                        
                with col_lon:
                    # Utiliser les coordonnées de l'autocomplétion si disponibles
                    default_lon = st.session_state.get('temp_longitude',
                                                      client.longitude if is_edit and client.longitude else 0.0)
                    longitude = st.number_input(
                        "Longitude", 
                        value=float(default_lon) if default_lon else 0.0,
                        min_value=-180.0,
                        max_value=180.0,
                        format="%.6f",
                        help="Entre -180 et 180 (rempli automatiquement si adresse sélectionnée)"
                    )
                    
            # Notes
            notes = st.text_area(
                "Notes",
                value=client.notes if is_edit and client.notes else "",
                height=100,
                help="Informations complémentaires libres"
            )
            
        # Boutons d'action
        col_submit, col_cancel, col_empty = st.columns([1, 1, 3])
        
        with col_submit:
            submit = st.form_submit_button(
                "💾 Enregistrer" if is_edit else "✅ Créer",
                type="primary",
                use_container_width=True
            )
            
        with col_cancel:
            cancel = st.form_submit_button(
                "❌ Annuler",
                use_container_width=True
            )
            
    # Traitement du formulaire
    if submit:
        try:
            # Validation des champs obligatoires
            if not code_client and not is_edit:
                st.error("Le code client est obligatoire")
                return None
            if not nom:
                st.error("Le nom du client est obligatoire")
                return None
                
            # Créer l'objet Client
            client_data = {
                'code_client': code_client.upper() if not is_edit else client.code_client,
                'nom': nom,
                'type_client': type_client,
                'adresse': adresse if adresse else None,
                'code_postal': code_postal if code_postal else None,
                'ville': ville if ville else None,
                'zone_geographique': zone_geographique if zone_geographique else None,
                'telephone': telephone if telephone else None,
                'email': email if email else None,
                'siret': siret if siret else None,
                'contact_principal': contact_principal if contact_principal else None,
                'notes': notes if notes else None,
                'actif': actif
            }
            
            # Gérer les coordonnées GPS depuis session state
            if st.session_state.temp_latitude is not None and st.session_state.temp_longitude is not None:
                client_data['latitude'] = st.session_state.temp_latitude
                client_data['longitude'] = st.session_state.temp_longitude
            else:
                client_data['latitude'] = None
                client_data['longitude'] = None
                
            if is_edit:
                # Mise à jour
                client_data['id'] = client.id
                client_data['date_creation'] = client.date_creation
                updated_client = Client(**client_data)
                result = client_service.update_client(updated_client)
                st.success(f"✅ Client '{result.nom}' mis à jour avec succès!")
            else:
                # Création
                new_client = Client(**client_data)
                result = client_service.create_client(new_client)
                st.success(f"✅ Client '{result.nom}' créé avec succès!")
                
                # Géocodage automatique si adresse fournie
                if result.adresse and not result.has_coordinates:
                    with st.spinner("🌍 Géocodage de l'adresse..."):
                        lat, lon = client_service.geocode_client(result)
                        if lat and lon:
                            client_service.update_coordinates(result.id, lat, lon)
                            st.info(f"📍 Coordonnées GPS trouvées: {lat:.6f}, {lon:.6f}")
                            
                # Attribution automatique de zone
                if result.code_postal and not result.zone_geographique:
                    zone = client_service.assign_zone_by_postal_code(result)
                    if zone:
                        st.info(f"🗺️ Zone géographique assignée: {zone}")
            
            # Proposition de géolocalisation sur carte si coordonnées pas définies
            if result and (not result.latitude or not result.longitude or (result.latitude == 0.0 and result.longitude == 0.0)):
                if adresse or ville or code_postal:
                    st.session_state['show_map_for_client'] = result.id
                    st.session_state['client_address_parts'] = {
                        'adresse': adresse,
                        'code_postal': code_postal,
                        'ville': ville
                    }
                    st.info("📍 Cliquez sur 'Ajuster position sur carte' ci-dessous pour définir précisément l'emplacement")
                        
            return result
            
        except ValueError as e:
            st.error(f"❌ Erreur de validation: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erreur formulaire client: {e}")
            st.error(f"❌ Erreur lors de l'enregistrement: {str(e)}")
            return None
            
    elif cancel:
        # Retour à la liste des clients
        if 'erp_client_mode' in st.session_state:
            st.session_state.erp_client_mode = 'list'
        # Nettoyer le session state
        if 'temp_latitude' in st.session_state:
            del st.session_state.temp_latitude
        if 'temp_longitude' in st.session_state:
            del st.session_state.temp_longitude
        if 'selected_coordinates' in st.session_state:
            del st.session_state.selected_coordinates
        st.rerun()
        
    return None


def render_client_quick_create() -> Optional[Client]:
    """Affiche un formulaire de création rapide de client.
    
    Returns:
        Client créé ou None
    """
    client_service = ClientService()
    
    st.subheader("⚡ Création rapide client")
    
    # Première ligne : informations de base
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        code = st.text_input("Code client *", max_chars=50)
        
    with col2:
        nom = st.text_input("Nom *", max_chars=200)
        
    with col3:
        type_client = st.selectbox(
            "Type *",
            options=['consommateur', 'producteur', 'prosumer']
        )
    
    # Option pour ajouter une adresse
    with st.expander("📍 Ajouter une adresse (optionnel)", expanded=False):
        from .components.address_autocomplete_widget import render_simple_address_search
        
        st.info("💡 Recherchez et sélectionnez une adresse pour remplir automatiquement les champs")
        
        selected_address = render_simple_address_search(
            label="Recherche d'adresse",
            key="quick_create_address",
            help_text="Tapez au moins 3 caractères pour rechercher une adresse"
        )
        
        if selected_address:
            st.success(f"✅ Adresse sélectionnée: {selected_address.display_label}")
            
            # Afficher les détails
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Code postal:** {selected_address.postcode}")
                st.write(f"**Ville:** {selected_address.city}")
            with col2:
                st.write(f"**Latitude:** {selected_address.latitude:.6f}")
                st.write(f"**Longitude:** {selected_address.longitude:.6f}")
        
    if st.button("➕ Créer", type="primary"):
        if not code or not nom:
            st.error("Code et nom obligatoires")
            return None
            
        try:
            # Préparer les données du client
            client_data = {
                'code_client': code.upper(),
                'nom': nom,
                'type_client': type_client
            }
            
            # Ajouter l'adresse si sélectionnée
            if selected_address:
                client_data.update({
                    'adresse': selected_address.street,
                    'code_postal': selected_address.postcode,
                    'ville': selected_address.city,
                    'latitude': selected_address.latitude,
                    'longitude': selected_address.longitude
                })
                
                # Zone géographique
                from ..services.address_autocomplete import get_address_service
                service = get_address_service()
                client_data['zone_geographique'] = service.parse_zone_from_postcode(selected_address.postcode)
            
            client = Client(**client_data)
            result = client_service.create_client(client)
            
            st.success(f"✅ Client '{result.nom}' créé!")
            
            if selected_address:
                st.info(f"📍 Avec adresse: {selected_address.display_label}")
            
            # Retour automatique à la liste après création
            if 'erp_client_mode' in st.session_state:
                st.session_state.erp_client_mode = 'list'
                import time
                time.sleep(2)  # Pause pour voir les messages de succès
                st.rerun()
            return result
            
        except Exception as e:
            st.error(f"❌ Erreur: {str(e)}")
            return None
            
    return None