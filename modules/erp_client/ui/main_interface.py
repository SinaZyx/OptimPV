"""Interface principale du module ERP pour l'intégration dans OptimPV.

Ce module fournit le point d'entrée principal pour toutes les fonctionnalités
ERP dans l'application Streamlit.
"""

import streamlit as st
import pandas as pd
import logging
from typing import Optional
from datetime import datetime

from ..services.client_service import ClientService
from ..services.pricing_service import PricingService
from ..services.capacity_service import CapacityService
from ..services.inflation_service import InflationService
from ..database.erp_database import ERPDatabase

from .client_form import render_client_form, render_client_quick_create
from .client_list import render_client_list
from .pricing_dashboard import render_pricing_dashboard

logger = logging.getLogger(__name__)


def render_erp_module():
    """Point d'entrée principal du module ERP dans l'application OptimPV."""
    
    # Initialiser les services dans la session si nécessaire
    if 'erp_services' not in st.session_state:
        st.session_state.erp_services = initialize_erp_services()
        
    services = st.session_state.erp_services
    
    # Header du module
    st.title("🏢 Module ERP - Gestion Clients")
    
    # Navigation par onglets professionnels
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "💼 Dashboard Commercial",
        "👥 Clients",
        "➕ Nouveau client", 
        "💰 Tarification",
        "🔌 Autoconsommation",
        "🗺️ Cartographie",
        "📊 Analytics"
    ])
    
    with tab1:
        render_commercial_dashboard_tab(services)
        
    with tab2:
        render_clients_tab(services)
        
    with tab3:
        render_new_client_tab(services)
        
    with tab4:
        render_pricing_tab(services)
        
    with tab5:
        render_autoconso_tab(services)
        
    with tab6:
        render_map_tab(services)
        
    with tab7:
        render_statistics_tab(services)
        
    # Gérer les actions depuis d'autres modules
    handle_cross_module_actions(services)


def initialize_erp_services() -> dict:
    """Initialise tous les services ERP.
    
    Returns:
        Dictionnaire contenant tous les services
    """
    try:
        # Initialiser la base de données
        db = ERPDatabase()
        
        # Créer les services avec imports explicites pour forcer le rechargement
        from ..services.client_service import ClientService as CS
        from ..services.pricing_service import PricingService as PS
        from ..services.capacity_service import CapacityService as CPS
        from ..services.inflation_service import InflationService as IS
        
        services = {
            'client': CS(),
            'pricing': PS(),
            'capacity': CPS(),
            'inflation': IS(),
            'database': db
        }
        
        # Vérifier que les méthodes existent
        if hasattr(services['capacity'], 'get_dashboard_stats'):
            logger.info("Services ERP initialisés avec succès (nouvelle version)")
        else:
            logger.warning("Service capacity sans get_dashboard_stats - ancienne version?")
            
        return services
        
    except Exception as e:
        logger.error(f"Erreur initialisation services ERP: {e}")
        st.error(f"Erreur lors de l'initialisation du module ERP: {str(e)}")
        return {}


def render_commercial_dashboard_tab(services: dict):
    """Onglet du dashboard commercial.
    
    Args:
        services: Dictionnaire des services ERP
    """
    from .commercial_dashboard import render_commercial_dashboard
    
    render_commercial_dashboard(
        client_service=services['client'],
        pricing_service=services['pricing'],
        capacity_service=services['capacity']
    )


def render_clients_tab(services: dict):
    """Onglet de gestion de la liste des clients version professionnelle.
    
    Args:
        services: Dictionnaire des services ERP
    """
    from .client_list_pro import render_professional_client_list
    
    render_professional_client_list(
        client_service=services['client'],
        pricing_service=services['pricing'],
        capacity_service=services['capacity']
    )


def render_new_client_tab(services: dict):
    """Onglet de création de nouveau client.
    
    Args:
        services: Dictionnaire des services ERP
    """
    st.header("➕ Créer un nouveau client")
    
    # Choix du mode de création
    mode = st.radio(
        "Mode de création",
        options=["Formulaire complet", "Création rapide"],
        horizontal=True
    )
    
    if mode == "Formulaire complet":
        result = render_client_form(client_service=services['client'])
        if result:
            st.balloons()
            # Proposer des actions suivantes
            st.success(f"✅ Client '{result.nom}' créé avec succès!")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💰 Définir les prix"):
                    st.session_state['selected_client_id'] = result.id
                    st.session_state['active_tab'] = 2  # Onglet prix
                    st.rerun()
                    
            with col2:
                if st.button("🔌 Gérer l'autoconso"):
                    st.session_state['selected_client_id'] = result.id
                    st.session_state['active_tab'] = 3  # Onglet autoconso
                    st.rerun()
                    
            with col3:
                if st.button("➕ Créer un autre"):
                    st.rerun()
                    
    else:
        # Création rapide
        result = render_client_quick_create()
        if result:
            st.success(f"✅ Client '{result.nom}' créé rapidement!")


def render_pricing_tab(services: dict):
    """Onglet de gestion des prix et évolutions.
    
    Args:
        services: Dictionnaire des services ERP
    """
    render_pricing_dashboard(
        client_service=services['client'],
        pricing_service=services['pricing'],
        inflation_service=services['inflation']
    )


def render_autoconso_tab(services: dict):
    """Onglet de gestion de l'autoconsommation collective.
    
    Args:
        services: Dictionnaire des services ERP
    """
    from .autoconso_dashboard import render_autoconso_dashboard
    
    render_autoconso_dashboard(
        capacity_service=services['capacity'],
        client_service=services['client']
    )


def render_map_tab(services: dict):
    """Onglet de cartographie des clients.
    
    Args:
        services: Dictionnaire des services ERP
    """
    # Utiliser la nouvelle carte dédiée aux clients ERP
    from .client_map import render_client_map
    
    render_client_map(
        client_service=services['client'],
        capacity_service=services['capacity']
    )


def render_statistics_tab(services: dict):
    """Onglet des statistiques et tableaux de bord.
    
    Args:
        services: Dictionnaire des services ERP
    """
    st.header("📊 Statistiques & Tableaux de bord")
    
    # Statistiques générales
    stats = services['client'].get_statistics()
    
    # Valeurs par défaut si None
    total_clients = stats.get('total_clients', 0) or 0
    clients_actifs = stats.get('clients_actifs', 0) or 0
    avec_coordonnees = stats.get('avec_coordonnees', 0) or 0
    par_type = stats.get('par_type', {}) or {}
    par_zone = stats.get('par_zone', {}) or {}
    
    # KPIs principaux
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pourcentage_actifs = (clients_actifs/total_clients*100) if total_clients > 0 else 0
        st.metric(
            "Clients actifs",
            clients_actifs,
            f"{pourcentage_actifs:.0f}% du total"
        )
        
    with col2:
        total_producteurs = par_type.get('producteur', 0) + par_type.get('prosumer', 0)
        st.metric(
            "Producteurs",
            total_producteurs,
            "Incluant prosumers"
        )
        
    with col3:
        zones_count = len(par_zone)
        st.metric(
            "Zones actives",
            zones_count,
            "Zones géographiques"
        )
        
    with col4:
        taux_geocodage = (avec_coordonnees / clients_actifs * 100) if clients_actifs > 0 else 0
        st.metric(
            "Taux géocodage",
            f"{taux_geocodage:.0f}%",
            f"{avec_coordonnees} clients"
        )
        
    # Graphiques
    st.markdown("### 📈 Répartition des clients")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Répartition par type
        if par_type:
            import plotly.express as px
            
            df_types = pd.DataFrame(
                list(par_type.items()),
                columns=['Type', 'Nombre']
            )
            
            fig = px.pie(
                df_types,
                values='Nombre',
                names='Type',
                title="Répartition par type de client"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
    with col2:
        # Top zones
        if par_zone:
            df_zones = pd.DataFrame(
                list(par_zone.items()),
                columns=['Zone', 'Nombre']
            ).sort_values('Nombre', ascending=False).head(10)
            
            fig = px.bar(
                df_zones,
                x='Nombre',
                y='Zone',
                orientation='h',
                title="Top 10 des zones"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
    # Statistiques base de données
    with st.expander("🗄️ Statistiques base de données"):
        db_stats = services['database'].get_database_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Clients", db_stats.get('clients', 0))
        with col2:
            st.metric("Prix définis", db_stats.get('prix_clients', 0))
        with col3:
            st.metric("Points production", db_stats.get('points_production', 0))
        with col4:
            st.metric("Allocations autoconso", db_stats.get('autoconso_collective', 0))


def handle_cross_module_actions(services: dict):
    """Gère les actions provenant d'autres modules.
    
    Args:
        services: Dictionnaire des services ERP
    """
    # Si un client a été sélectionné depuis le core_analyzer
    if st.session_state.get('erp_select_client_for_analysis'):
        client_id = st.session_state['erp_select_client_for_analysis']
        client = services['client'].get_by_id(client_id)
        
        if client:
            # Récupérer le prix actif
            prix = services['pricing'].get_active_price(client_id)
            
            if prix:
                # Stocker les informations pour le core_analyzer
                st.session_state['current_client'] = client
                st.session_state['client_pricing'] = {
                    'prix_kwh': prix.prix_kwh,
                    'type_tarif': prix.type_tarif,
                    'client_name': client.nom,
                    'client_code': client.code_client
                }
                
                st.success(f"Client '{client.nom}' sélectionné pour l'analyse")
            else:
                st.warning(f"Le client '{client.nom}' n'a pas de prix défini")
                
        # Nettoyer la demande
        del st.session_state['erp_select_client_for_analysis']




def export_clients(client_service: ClientService):
    """Exporte la liste des clients.
    
    Args:
        client_service: Service de gestion des clients
    """
    import pandas as pd
    import io
    
    clients = client_service.get_all(include_inactive=True)
    
    if not clients:
        st.warning("Aucun client à exporter")
        return
        
    # Préparer les données
    data = []
    for client in clients:
        data.append({
            'Code': client.code_client,
            'Nom': client.nom,
            'Type': client.type_client,
            'Adresse': client.adresse,
            'Code postal': client.code_postal,
            'Ville': client.ville,
            'Zone': client.zone_geographique,
            'Téléphone': client.telephone,
            'Email': client.email,
            'SIRET': client.siret,
            'Contact': client.contact_principal,
            'Latitude': client.latitude,
            'Longitude': client.longitude,
            'Actif': client.actif,
            'Notes': client.notes
        })
        
    df = pd.DataFrame(data)
    
    # Créer le fichier Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Clients', index=False)
        
    # Télécharger
    st.download_button(
        label="📥 Télécharger Excel",
        data=output.getvalue(),
        file_name=f"export_clients_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )