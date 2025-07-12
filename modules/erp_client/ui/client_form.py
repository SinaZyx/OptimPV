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
            
            # Zone géographique
            zone_geographique = st.text_input(
                "Zone géographique",
                value=client.zone_geographique if is_edit and client.zone_geographique else "",
                help="Sera assignée automatiquement selon le code postal si vide"
            )
            
            # Statut
            actif = st.checkbox(
                "Client actif",
                value=client.actif if is_edit else True
            )
            
        with col2:
            st.markdown("### 📍 Coordonnées")
            
            # Adresse
            adresse = st.text_area(
                "Adresse",
                value=client.adresse if is_edit and client.adresse else "",
                height=100
            )
            
            # Code postal et ville
            col_cp, col_ville = st.columns([1, 2])
            with col_cp:
                code_postal = st.text_input(
                    "Code postal",
                    value=client.code_postal if is_edit and client.code_postal else "",
                    max_chars=10
                )
            with col_ville:
                ville = st.text_input(
                    "Ville",
                    value=client.ville if is_edit and client.ville else "",
                    max_chars=100
                )
                
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
                st.markdown("**Coordonnées GPS** (laisser vide pour géocodage auto)")
                col_lat, col_lon = st.columns(2)
                with col_lat:
                    latitude = st.number_input(
                        "Latitude",
                        value=client.latitude if is_edit and client.latitude else 0.0,
                        min_value=-90.0,
                        max_value=90.0,
                        format="%.6f",
                        help="Entre -90 et 90"
                    )
                with col_lon:
                    longitude = st.number_input(
                        "Longitude", 
                        value=client.longitude if is_edit and client.longitude else 0.0,
                        min_value=-180.0,
                        max_value=180.0,
                        format="%.6f",
                        help="Entre -180 et 180"
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
            
            # Gérer les coordonnées GPS
            if latitude != 0.0 or longitude != 0.0:
                client_data['latitude'] = latitude if latitude != 0.0 else None
                client_data['longitude'] = longitude if longitude != 0.0 else None
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
                        
            return result
            
        except ValueError as e:
            st.error(f"❌ Erreur de validation: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erreur formulaire client: {e}")
            st.error(f"❌ Erreur lors de l'enregistrement: {str(e)}")
            return None
            
    elif cancel:
        st.info("Opération annulée")
        return None
        
    return None


def render_client_quick_create() -> Optional[Client]:
    """Affiche un formulaire de création rapide de client.
    
    Returns:
        Client créé ou None
    """
    client_service = ClientService()
    
    st.subheader("⚡ Création rapide client")
    
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
        
    if st.button("➕ Créer", type="primary"):
        if not code or not nom:
            st.error("Code et nom obligatoires")
            return None
            
        try:
            client = Client(
                code_client=code,
                nom=nom,
                type_client=type_client
            )
            
            result = client_service.create_client(client)
            st.success(f"✅ Client '{result.nom}' créé!")
            return result
            
        except Exception as e:
            st.error(f"❌ Erreur: {str(e)}")
            return None
            
    return None