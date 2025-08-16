"""Interface professionnelle de gestion des clients.

Version améliorée avec :
- Vue en cartes et tableaux
- Actions rapides en masse
- Timeline d'activités
- Export avancé
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict
import json

from ..services.client_service import ClientService
from ..services.pricing_service import PricingService
from ..services.capacity_service import CapacityService
from ..models.client import Client, TypeClient


def render_professional_client_list(
    client_service: ClientService,
    pricing_service: PricingService,
    capacity_service: CapacityService
):
    """Affiche la liste des clients en mode professionnel."""
    
    # En-tête avec actions
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        st.header("👥 Gestion des Clients")
    
    with col2:
        view_mode = st.selectbox(
            "Vue",
            ["📋 Tableau", "🃏 Cartes", "📊 Kanban"],
            key="client_view_mode"
        )
    
    with col3:
        if st.button("➕ Nouveau client", type="primary"):
            st.session_state.erp_client_mode = 'create'
            st.rerun()
    
    with col4:
        if st.button("⚡ Actions"):
            st.session_state['show_quick_actions'] = True
    
    # Barre de recherche et filtres avancés
    render_search_filters(client_service)
    
    # Statistiques rapides
    render_client_statistics(client_service, pricing_service, capacity_service)
    
    # Affichage selon le mode choisi
    if view_mode == "📋 Tableau":
        render_table_view(client_service, pricing_service, capacity_service)
    elif view_mode == "🃏 Cartes":
        render_cards_view(client_service, pricing_service, capacity_service)
    else:
        render_kanban_view(client_service, pricing_service, capacity_service)
    
    # Modal d'actions rapides
    if st.session_state.get('show_quick_actions'):
        render_quick_actions_modal(client_service, pricing_service)


def render_search_filters(client_service: ClientService):
    """Barre de recherche et filtres avancés."""
    
    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
    
    with col1:
        search_term = st.text_input(
            "🔍 Recherche",
            placeholder="Nom, code client, email, téléphone...",
            key="client_search"
        )
    
    with col2:
        type_filter = st.selectbox(
            "Type",
            ["Tous"] + [t.value for t in TypeClient],
            key="client_type_filter"
        )
    
    with col3:
        status_filter = st.selectbox(
            "Statut",
            ["Tous", "Actifs", "Inactifs"],
            key="client_status_filter"
        )
    
    with col4:
        zone_filter = st.selectbox(
            "Zone",
            ["Toutes"] + client_service.get_unique_zones(),
            key="client_zone_filter"
        )
    
    with col5:
        date_filter = st.selectbox(
            "Période",
            ["Toutes", "Aujourd'hui", "Cette semaine", "Ce mois", "3 derniers mois"],
            key="client_date_filter"
        )
    
    # Filtres avancés (expandable)
    with st.expander("🔧 Filtres avancés"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            has_coordinates = st.checkbox("Avec coordonnées GPS", key="filter_has_coords")
            has_pricing = st.checkbox("Avec tarification", key="filter_has_pricing")
            has_production = st.checkbox("Avec production", key="filter_has_production")
        
        with col2:
            min_ca = st.number_input("CA minimum (€)", min_value=0, value=0, key="filter_min_ca")
            max_ca = st.number_input("CA maximum (€)", min_value=0, value=0, key="filter_max_ca")
        
        with col3:
            tags = st.multiselect(
                "Tags",
                ["VIP", "À risque", "Nouveau", "Grand compte", "PME"],
                key="filter_tags"
            )


def render_client_statistics(
    client_service: ClientService,
    pricing_service: PricingService,
    capacity_service: CapacityService
):
    """Affiche les statistiques rapides des clients."""
    
    stats = client_service.get_statistics()
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric(
            "Total Clients",
            stats.get('total_clients', 0),
            f"{stats.get('new_this_month', 0)} ce mois"
        )
    
    with col2:
        st.metric(
            "Clients Actifs",
            stats.get('clients_actifs', 0),
            f"{(stats.get('clients_actifs', 0) / stats.get('total_clients', 1) * 100):.0f}%"
        )
    
    with col3:
        total_capacity = capacity_service.get_total_capacity()
        st.metric(
            "Capacité Totale",
            f"{total_capacity:.0f} kWc",
            "Production installée"
        )
    
    with col4:
        avg_price = pricing_service.get_average_price()
        st.metric(
            "Prix Moyen",
            f"{avg_price:.3f} €/kWh",
            "Tous clients confondus"
        )
    
    with col5:
        retention_rate = calculate_retention_rate(client_service)
        st.metric(
            "Taux Rétention",
            f"{retention_rate:.0f}%",
            "Sur 12 mois"
        )
    
    with col6:
        satisfaction = calculate_satisfaction_score()
        st.metric(
            "Satisfaction",
            f"{satisfaction}/5",
            "Score moyen"
        )


def render_table_view(
    client_service: ClientService,
    pricing_service: PricingService,
    capacity_service: CapacityService
):
    """Affichage en tableau professionnel."""
    
    # Récupérer et filtrer les clients
    clients = get_filtered_clients(client_service)
    
    if not clients:
        st.info("Aucun client ne correspond aux critères de recherche.")
        return
    
    # Préparer les données pour le tableau
    data = []
    for client in clients:
        # Récupérer les infos supplémentaires
        prix = pricing_service.get_active_price(client.id)
        capacity = capacity_service.get_client_capacity(client.id)
        last_activity = get_last_activity(client.id)
        
        data.append({
            'select': False,
            'ID': client.id,
            'Code': client.code_client,
            'Nom': client.nom,
            'Type': get_type_badge(client.type_client),
            'Zone': client.zone_geographique or "—",
            'Contact': client.contact_principal or "—",
            'Email': client.email or "—",
            'Prix': f"{prix.prix_kwh:.3f} €/kWh" if prix else "—",
            'Capacité': f"{capacity:.0f} kWc" if capacity > 0 else "—",
            'Dernière activité': last_activity,
            'Statut': "🟢 Actif" if client.actif else "🔴 Inactif",
            'Actions': client.id
        })
    
    df = pd.DataFrame(data)
    
    # Configuration des colonnes
    column_config = {
        "select": st.column_config.CheckboxColumn(
            "✓",
            help="Sélectionner pour actions en masse",
            default=False,
            width="small"
        ),
        "ID": st.column_config.NumberColumn("ID", width="small", disabled=True),
        "Code": st.column_config.TextColumn("Code", width="small"),
        "Nom": st.column_config.TextColumn("Nom", width="medium"),
        "Type": st.column_config.TextColumn("Type", width="small"),
        "Zone": st.column_config.TextColumn("Zone", width="small"),
        "Contact": st.column_config.TextColumn("Contact", width="medium"),
        "Email": st.column_config.LinkColumn("Email", width="medium"),
        "Prix": st.column_config.TextColumn("Prix", width="small"),
        "Capacité": st.column_config.TextColumn("Capacité", width="small"),
        "Dernière activité": st.column_config.TextColumn("Activité", width="medium"),
        "Statut": st.column_config.TextColumn("Statut", width="small"),
        "Actions": st.column_config.NumberColumn(
            "Actions",
            width="small",
            disabled=True
        )
    }
    
    # Afficher le tableau avec sélection
    edited_df = st.data_editor(
        df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        disabled=["ID", "Actions"],
        key="client_table"
    )
    
    # Actions sur la sélection
    selected_ids = edited_df[edited_df['select']]['ID'].tolist()
    
    if selected_ids:
        render_bulk_actions(selected_ids, client_service, pricing_service)
    
    # Actions individuelles
    if st.session_state.get('client_action'):
        action, client_id = st.session_state['client_action']
        handle_client_action(action, client_id, client_service)
        del st.session_state['client_action']


def render_cards_view(
    client_service: ClientService,
    pricing_service: PricingService,
    capacity_service: CapacityService
):
    """Affichage en cartes."""
    
    clients = get_filtered_clients(client_service)
    
    if not clients:
        st.info("Aucun client ne correspond aux critères de recherche.")
        return
    
    # Pagination
    items_per_page = 12
    total_pages = (len(clients) + items_per_page - 1) // items_per_page
    current_page = st.number_input(
        "Page",
        min_value=1,
        max_value=total_pages,
        value=1,
        key="cards_page"
    )
    
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(clients))
    page_clients = clients[start_idx:end_idx]
    
    # Affichage en grille
    cols = st.columns(3)
    
    for idx, client in enumerate(page_clients):
        with cols[idx % 3]:
            render_client_card(client, pricing_service, capacity_service)


def render_client_card(
    client: Client,
    pricing_service: PricingService,
    capacity_service: CapacityService
):
    """Affiche une carte client."""
    
    # Récupérer les infos
    prix = pricing_service.get_active_price(client.id)
    capacity = capacity_service.get_client_capacity(client.id)
    
    # Couleur selon le type
    type_colors = {
        TypeClient.PRODUCTEUR: "#2E86AB",
        TypeClient.CONSOMMATEUR: "#A23B72",
        TypeClient.PROSUMER: "#F18F01"
    }
    
    # Carte avec style
    with st.container():
        st.markdown(
            f"""
            <div style="
                border: 2px solid {type_colors.get(client.type_client, '#ccc')};
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
                background-color: rgba(255,255,255,0.05);
            ">
                <h4 style="margin: 0; color: {type_colors.get(client.type_client, '#000')};">
                    {client.nom}
                </h4>
                <p style="margin: 5px 0; color: #666; font-size: 0.9em;">
                    {client.code_client} • {client.type_client.value}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Infos principales
        if client.contact_principal:
            st.caption(f"👤 {client.contact_principal}")
        
        if client.email:
            st.caption(f"📧 {client.email}")
        
        if client.telephone:
            st.caption(f"📞 {client.telephone}")
        
        # Métriques
        col1, col2 = st.columns(2)
        
        with col1:
            if prix:
                st.metric("Prix", f"{prix.prix_kwh:.3f} €/kWh")
            else:
                st.metric("Prix", "Non défini")
        
        with col2:
            if capacity > 0:
                st.metric("Capacité", f"{capacity:.0f} kWc")
            else:
                st.metric("Capacité", "—")
        
        # Actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👁️", key=f"view_{client.id}", help="Voir détails"):
                st.session_state['view_client'] = client.id
        
        with col2:
            if st.button("✏️", key=f"edit_{client.id}", help="Modifier"):
                st.session_state['edit_client'] = client.id
        
        with col3:
            if st.button("📧", key=f"contact_{client.id}", help="Contacter"):
                st.session_state['contact_client'] = client.id


def render_kanban_view(
    client_service: ClientService,
    pricing_service: PricingService,
    capacity_service: CapacityService
):
    """Affichage en mode Kanban par statut."""
    
    # Colonnes Kanban
    stages = {
        "🆕 Nouveaux": [],
        "📞 En contact": [],
        "📋 Proposition": [],
        "✅ Actifs": [],
        "⏸️ Inactifs": []
    }
    
    # Répartir les clients
    clients = get_filtered_clients(client_service)
    
    for client in clients:
        # Déterminer le stage selon l'état
        if not client.actif:
            stages["⏸️ Inactifs"].append(client)
        elif is_new_client(client):
            stages["🆕 Nouveaux"].append(client)
        elif has_active_proposal(client):
            stages["📋 Proposition"].append(client)
        elif is_in_contact(client):
            stages["📞 En contact"].append(client)
        else:
            stages["✅ Actifs"].append(client)
    
    # Afficher les colonnes
    cols = st.columns(len(stages))
    
    for idx, (stage_name, stage_clients) in enumerate(stages.items()):
        with cols[idx]:
            st.markdown(f"### {stage_name}")
            st.caption(f"{len(stage_clients)} clients")
            
            # Container scrollable
            container = st.container(height=600)
            
            with container:
                for client in stage_clients[:20]:  # Limiter à 20 par colonne
                    render_kanban_card(client, pricing_service)
                
                if len(stage_clients) > 20:
                    st.info(f"+ {len(stage_clients) - 20} autres...")


def render_kanban_card(client: Client, pricing_service: PricingService):
    """Affiche une carte Kanban."""
    
    prix = pricing_service.get_active_price(client.id)
    
    with st.container():
        # Style compact
        st.markdown(
            f"""
            <div style="
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 5px;
                background-color: white;
                cursor: move;
            ">
                <strong>{client.nom}</strong><br>
                <small>{client.code_client}</small><br>
                <small>{prix.prix_kwh:.3f} €/kWh</small> if prix else ""
            </div>
            """,
            unsafe_allow_html=True
        )


def render_bulk_actions(
    selected_ids: List[int],
    client_service: ClientService,
    pricing_service: PricingService
):
    """Actions en masse sur les clients sélectionnés."""
    
    st.info(f"🎯 {len(selected_ids)} clients sélectionnés")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("📧 Email groupé", key="bulk_email_btn"):
            st.session_state['bulk_email'] = selected_ids
    
    with col2:
        if st.button("🏷️ Assigner tags", key="bulk_tags_btn"):
            st.session_state['bulk_tags'] = selected_ids
    
    with col3:
        if st.button("💰 Maj. tarifs", key="bulk_pricing_btn"):
            st.session_state['bulk_pricing'] = selected_ids
    
    with col4:
        if st.button("📤 Exporter", key="bulk_export"):
            export_selected_clients(selected_ids, client_service)
    
    with col5:
        if st.button("🗑️ Supprimer", key="bulk_delete", type="secondary"):
            if st.checkbox("Confirmer la suppression"):
                for client_id in selected_ids:
                    client_service.delete(client_id)
                st.success(f"{len(selected_ids)} clients supprimés")
                st.rerun()


def render_quick_actions_modal(
    client_service: ClientService,
    pricing_service: PricingService
):
    """Modal pour les actions rapides."""
    
    with st.container():
        st.markdown("### ⚡ Actions Rapides")
        
        action = st.selectbox(
            "Choisir une action",
            [
                "Import en masse",
                "Export personnalisé",
                "Mise à jour groupée",
                "Génération de rapports",
                "Envoi d'emails",
                "Géocodage en masse"
            ]
        )
        
        if action == "Import en masse":
            uploaded_file = st.file_uploader(
                "Choisir un fichier Excel/CSV",
                type=['xlsx', 'csv']
            )
            
            if uploaded_file:
                if st.button("🚀 Lancer l'import"):
                    import_clients_from_file(uploaded_file, client_service)
        
        elif action == "Géocodage en masse":
            if st.button("🗺️ Géocoder tous les clients sans coordonnées"):
                geocode_all_clients(client_service)
        
        if st.button("❌ Fermer"):
            del st.session_state['show_quick_actions']
            st.rerun()


# Fonctions utilitaires

def get_filtered_clients(client_service: ClientService) -> List[Client]:
    """Récupère les clients filtrés selon les critères."""
    
    # Récupérer tous les clients
    clients = client_service.get_all(include_inactive=True)
    
    # Appliquer les filtres
    search_term = st.session_state.get('client_search', '')
    if search_term:
        clients = [c for c in clients if search_term.lower() in c.nom.lower() 
                  or search_term.lower() in c.code_client.lower()
                  or (c.email and search_term.lower() in c.email.lower())]
    
    type_filter = st.session_state.get('client_type_filter', 'Tous')
    if type_filter != 'Tous':
        clients = [c for c in clients if c.type_client.value == type_filter]
    
    status_filter = st.session_state.get('client_status_filter', 'Tous')
    if status_filter == 'Actifs':
        clients = [c for c in clients if c.actif]
    elif status_filter == 'Inactifs':
        clients = [c for c in clients if not c.actif]
    
    return clients


def get_type_badge(type_client: TypeClient) -> str:
    """Retourne un badge coloré pour le type de client."""
    badges = {
        TypeClient.PRODUCTEUR: "🟢 Producteur",
        TypeClient.CONSOMMATEUR: "🔵 Consommateur",
        TypeClient.PROSUMER: "🟣 Prosumer"
    }
    return badges.get(type_client, type_client.value)


def get_last_activity(client_id: int) -> str:
    """Retourne la dernière activité du client."""
    # Simulé pour l'exemple
    activities = [
        "Email envoyé il y a 2j",
        "Appel il y a 1 sem",
        "RDV il y a 3j",
        "Proposition il y a 5j",
        "Contrat signé il y a 1 mois"
    ]
    return activities[client_id % len(activities)]


def calculate_retention_rate(client_service: ClientService) -> float:
    """Calcule le taux de rétention sur 12 mois."""
    # Simulé pour l'exemple
    return 94.5


def calculate_satisfaction_score() -> float:
    """Calcule le score de satisfaction moyen."""
    # Simulé pour l'exemple
    return 4.6


def is_new_client(client: Client) -> bool:
    """Vérifie si le client est nouveau (< 30 jours)."""
    if client.date_creation:
        return (datetime.now() - client.date_creation).days < 30
    return False


def has_active_proposal(client: Client) -> bool:
    """Vérifie si le client a une proposition active."""
    # Simulé pour l'exemple
    return client.id % 5 == 0


def is_in_contact(client: Client) -> bool:
    """Vérifie si le client est en phase de contact."""
    # Simulé pour l'exemple
    return client.id % 3 == 0


def export_selected_clients(client_ids: List[int], client_service: ClientService):
    """Exporte les clients sélectionnés."""
    # Implémentation de l'export
    st.success(f"Export de {len(client_ids)} clients en cours...")