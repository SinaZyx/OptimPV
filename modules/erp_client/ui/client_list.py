"""Interface Streamlit pour la liste et la recherche de clients.

Ce module fournit les composants UI pour afficher, rechercher et gérer
la liste des clients dans le système ERP.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import logging
from typing import Optional, List, Dict, Any

from ..models.client import Client
from ..services.client_service import ClientService
from ..services.pricing_service import PricingService

logger = logging.getLogger(__name__)


def render_client_list(client_service: ClientService = None, pricing_service: PricingService = None):
    """Affiche la liste des clients avec fonctionnalités de recherche et filtrage.
    
    Args:
        client_service: Service de gestion des clients
        pricing_service: Service de gestion des prix
    """
    if client_service is None:
        client_service = ClientService()
    if pricing_service is None:
        pricing_service = PricingService()
        
    # En-tête avec statistiques
    render_client_statistics(client_service)
    
    # Barre de recherche et filtres
    search_params = render_search_filters()
    
    # Récupérer et afficher les clients
    with st.spinner("Chargement des clients..."):
        if any(search_params.values()):
            # Recherche avec critères
            clients = client_service.search_clients(**search_params)
        else:
            # Tous les clients actifs
            clients = client_service.get_all(include_inactive=search_params.get('include_inactive', False))
            
    if not clients:
        st.info("🔍 Aucun client trouvé avec ces critères")
        return
        
    # Options d'affichage
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"**{len(clients)} client(s) trouvé(s)**")
    with col2:
        view_mode = st.selectbox(
            "Affichage",
            options=['table', 'cartes'],
            label_visibility="collapsed"
        )
    with col3:
        if st.button("🔄 Actualiser", key="refresh_client_list"):
            st.rerun()
            
    # Affichage selon le mode choisi
    if view_mode == 'table':
        render_clients_table(clients, client_service, pricing_service)
    else:
        render_clients_cards(clients, client_service, pricing_service)


def render_client_statistics(client_service: ClientService):
    """Affiche les statistiques des clients."""
    stats = client_service.get_statistics()
    
    # Valeurs par défaut si None
    total_clients = stats.get('total_clients', 0) or 0
    clients_actifs = stats.get('clients_actifs', 0) or 0
    avec_coordonnees = stats.get('avec_coordonnees', 0) or 0
    sans_coordonnees = stats.get('sans_coordonnees', 0) or 0
    par_type = stats.get('par_type', {}) or {}
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total clients",
            total_clients,
            f"{clients_actifs} actifs",
            delta_color="normal"
        )
        
    with col2:
        producteurs = par_type.get('producteur', 0) + par_type.get('prosumer', 0)
        st.metric(
            "Producteurs",
            producteurs,
            "Incluant prosumers"
        )
        
    with col3:
        consommateurs = par_type.get('consommateur', 0) + par_type.get('prosumer', 0)
        st.metric(
            "Consommateurs",
            consommateurs,
            "Incluant prosumers"
        )
        
    with col4:
        pct_geocodes = (avec_coordonnees / clients_actifs * 100) if clients_actifs > 0 else 0
        st.metric(
            "Géocodés",
            f"{pct_geocodes:.0f}%",
            f"{avec_coordonnees} clients"
        )


def render_search_filters() -> Dict[str, Any]:
    """Affiche les filtres de recherche.
    
    Returns:
        Dictionnaire des paramètres de recherche
    """
    with st.expander("🔍 Recherche et filtres", expanded=True):
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            search_term = st.text_input(
                "Rechercher",
                placeholder="Nom, code, ville...",
                label_visibility="collapsed"
            )
            
        with col2:
            type_client = st.selectbox(
                "Type",
                options=['Tous'] + ['producteur', 'consommateur', 'prosumer'],
                label_visibility="collapsed"
            )
            
        with col3:
            zone = st.text_input(
                "Zone",
                placeholder="Zone géographique",
                label_visibility="collapsed"
            )
            
        with col4:
            include_inactive = st.checkbox("Inactifs", value=False)
            
    # Construire les paramètres
    params = {}
    if search_term:
        params['search_term'] = search_term
    if type_client != 'Tous':
        params['type_client'] = type_client
    if zone:
        params['zone_geographique'] = zone
    params['actif_only'] = not include_inactive
        
    return params


def render_clients_table(clients: List[Client], client_service: ClientService, pricing_service: PricingService):
    """Affiche les clients sous forme de tableau.
    
    Args:
        clients: Liste des clients
        client_service: Service clients
        pricing_service: Service prix
    """
    # Préparer les données pour le DataFrame
    data = []
    for client in clients:
        # Prix actuel
        prix_actuel = pricing_service.get_active_price(client.id)
        prix_str = f"{prix_actuel.prix_kwh:.4f} €/kWh" if prix_actuel else "Non défini"
        
        data.append({
            'Code': client.code_client,
            'Nom': client.nom,
            'Type': client.type_client.value.capitalize(),
            'Ville': client.ville or '-',
            'Zone': client.zone_geographique or '-',
            'Prix': prix_str,
            'Contact': client.contact_principal or '-',
            'Téléphone': client.telephone or '-',
            'Email': client.email or '-',
            'Actif': '✅' if client.actif else '❌',
            'ID': client.id
        })
        
    df = pd.DataFrame(data)
    
    # Configuration du tableau
    column_config = {
        'Code': st.column_config.TextColumn('Code', width='small'),
        'Nom': st.column_config.TextColumn('Nom', width='medium'),
        'Type': st.column_config.TextColumn('Type', width='small'),
        'Ville': st.column_config.TextColumn('Ville', width='small'),
        'Zone': st.column_config.TextColumn('Zone', width='small'),
        'Prix': st.column_config.TextColumn('Prix', width='small'),
        'Contact': st.column_config.TextColumn('Contact', width='medium'),
        'Téléphone': st.column_config.TextColumn('Tél.', width='small'),
        'Email': st.column_config.TextColumn('Email', width='medium'),
        'Actif': st.column_config.TextColumn('Actif', width='small'),
        'ID': st.column_config.NumberColumn('ID', width='small')
    }
    
    # Sélection dans le tableau
    selected = st.dataframe(
        df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # Actions sur la sélection
    if selected and len(selected.selection.rows) > 0:
        selected_row = selected.selection.rows[0]
        selected_client_id = df.iloc[selected_row]['ID']
        selected_client = next((c for c in clients if c.id == selected_client_id), None)
        
        if selected_client:
            render_client_actions(selected_client, client_service, pricing_service)


def render_clients_cards(clients: List[Client], client_service: ClientService, pricing_service: PricingService):
    """Affiche les clients sous forme de cartes.
    
    Args:
        clients: Liste des clients  
        client_service: Service clients
        pricing_service: Service prix
    """
    # Grouper par type pour un meilleur affichage
    grouped = {
        'producteur': [],
        'consommateur': [],
        'prosumer': []
    }
    
    for client in clients:
        grouped[client.type_client.value].append(client)
        
    # Afficher chaque groupe
    for type_client, type_clients in grouped.items():
        if not type_clients:
            continue
            
        # Icône selon le type
        icon = {
            'producteur': '⚡',
            'consommateur': '🏠',
            'prosumer': '🔄'
        }[type_client]
        
        st.markdown(f"### {icon} {type_client.capitalize()}s ({len(type_clients)})")
        
        # Afficher en colonnes
        cols = st.columns(3)
        for idx, client in enumerate(type_clients):
            with cols[idx % 3]:
                render_client_card(client, pricing_service)
                
                # Actions rapides
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("👁️", key=f"view_{client.id}", help="Voir détails"):
                        st.session_state[f'view_client_{client.id}'] = True
                with col2:
                    if st.button("✏️", key=f"edit_{client.id}", help="Éditer"):
                        st.session_state[f'edit_client_{client.id}'] = True
                with col3:
                    if st.button("💰", key=f"price_{client.id}", help="Gérer prix"):
                        st.session_state[f'price_client_{client.id}'] = True
                        
                # Modal de détails
                if st.session_state.get(f'view_client_{client.id}'):
                    render_client_details_modal(client, client_service, pricing_service)


def render_client_card(client: Client, pricing_service: PricingService):
    """Affiche une carte client.
    
    Args:
        client: Client à afficher
        pricing_service: Service prix
    """
    # Conteneur avec bordure
    with st.container():
        # Statut
        status_color = "🟢" if client.actif else "🔴"
        st.markdown(f"{status_color} **{client.nom}**")
        st.caption(f"Code: {client.code_client}")
        
        # Localisation
        if client.ville:
            st.text(f"📍 {client.ville}")
        if client.zone_geographique:
            st.text(f"🗺️ {client.zone_geographique}")
            
        # Prix
        prix = pricing_service.get_active_price(client.id)
        if prix:
            st.text(f"💰 {prix.prix_kwh:.4f} €/kWh")
        else:
            st.text("💰 Prix non défini")
            
        # Contact
        if client.contact_principal:
            st.caption(f"👤 {client.contact_principal}")
        if client.telephone:
            st.caption(f"📞 {client.telephone}")
            
        st.markdown("---")


def render_client_actions(client: Client, client_service: ClientService, pricing_service: PricingService):
    """Affiche les actions disponibles pour un client.
    
    Args:
        client: Client sélectionné
        client_service: Service clients  
        pricing_service: Service prix
    """
    st.markdown("### Actions client")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("👁️ Détails", use_container_width=True):
            st.session_state['show_client_details'] = client.id
            
    with col2:
        if st.button("✏️ Éditer", use_container_width=True):
            st.session_state['edit_client'] = client.id
            
    with col3:
        if st.button("💰 Prix", use_container_width=True):
            st.session_state['manage_prices'] = client.id
            
    with col4:
        if st.button("🔌 Autoconso", use_container_width=True):
            st.session_state['manage_autoconso'] = client.id
            
    with col5:
        if st.button("🗑️ Supprimer", use_container_width=True, type="secondary"):
            if st.session_state.get('confirm_delete') == client.id:
                # Confirmation
                if client_service.delete_client(client.id):
                    st.success(f"Client {client.nom} supprimé")
                    st.rerun()
            else:
                st.session_state['confirm_delete'] = client.id
                st.warning("Cliquez à nouveau pour confirmer")


def render_client_details_modal(client: Client, client_service: ClientService, pricing_service: PricingService):
    """Affiche une modal avec les détails complets d'un client.
    
    Args:
        client: Client à afficher
        client_service: Service clients
        pricing_service: Service prix
    """
    @st.dialog(f"Détails client: {client.nom}")
    def show_details():
        # Informations générales
        st.markdown("### 📋 Informations générales")
        col1, col2 = st.columns(2)
        
        with col1:
            st.text(f"Code: {client.code_client}")
            st.text(f"Type: {client.type_client.value.capitalize()}")
            st.text(f"Statut: {'Actif' if client.actif else 'Inactif'}")
            
        with col2:
            st.text(f"Créé le: {client.date_creation.strftime('%d/%m/%Y') if client.date_creation else 'N/A'}")
            st.text(f"Modifié le: {client.date_modification.strftime('%d/%m/%Y') if client.date_modification else 'N/A'}")
            
        # Coordonnées
        st.markdown("### 📍 Coordonnées")
        if client.adresse:
            st.text(f"Adresse: {client.adresse}")
        if client.code_postal or client.ville:
            st.text(f"Ville: {client.code_postal} {client.ville}")
        if client.zone_geographique:
            st.text(f"Zone: {client.zone_geographique}")
            
        col3, col4 = st.columns(2)
        with col3:
            if client.telephone:
                st.text(f"Tél: {client.telephone}")
            if client.email:
                st.text(f"Email: {client.email}")
                
        with col4:
            if client.has_coordinates:
                st.text(f"GPS: {client.latitude:.6f}, {client.longitude:.6f}")
                
        # Informations commerciales
        st.markdown("### 💼 Informations commerciales")
        if client.siret:
            st.text(f"SIRET: {client.siret}")
        if client.contact_principal:
            st.text(f"Contact: {client.contact_principal}")
            
        # Prix actuel
        prix = pricing_service.get_active_price(client.id)
        if prix:
            st.text(f"Prix actuel: {prix.prix_kwh:.4f} €/kWh ({prix.type_tarif})")
            
        # Notes
        if client.notes:
            st.markdown("### 📝 Notes")
            st.text_area("", value=client.notes, disabled=True, height=100)
            
        # Bouton fermer
        if st.button("Fermer", use_container_width=True):
            del st.session_state[f'view_client_{client.id}']
            st.rerun()
            
    show_details()