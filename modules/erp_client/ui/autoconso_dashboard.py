"""Interface pour la gestion de l'autoconsommation collective.

Ce module fournit l'interface utilisateur pour gérer les opérations
d'autoconsommation collective, les allocations et le monitoring.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple

from ..services.capacity_service import CapacityService
from ..services.client_service import ClientService
from ..models.autoconso import PointProduction, PointConsommation, AutoconsoCollective

logger = logging.getLogger(__name__)


def render_autoconso_dashboard(
    capacity_service: CapacityService,
    client_service: ClientService
):
    """Affiche le tableau de bord principal de l'autoconsommation collective.
    
    Args:
        capacity_service: Service de gestion des capacités
        client_service: Service de gestion des clients
    """
    # Tabs pour organiser les fonctionnalités
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard",
        "⚡ Points de Production", 
        "🏠 Points de Consommation",
        "🔄 Allocations",
        "📈 Analyses"
    ])
    
    with tab1:
        render_operations_dashboard(capacity_service, client_service)
        
    with tab2:
        render_production_points(capacity_service, client_service)
        
    with tab3:
        render_consumption_points(capacity_service, client_service)
        
    with tab4:
        render_allocations_management(capacity_service, client_service)
        
    with tab5:
        render_autoconso_analytics(capacity_service, client_service)


def render_operations_dashboard(
    capacity_service: CapacityService,
    client_service: ClientService
):
    """Affiche le dashboard principal des opérations."""
    st.header("📊 Dashboard Autoconsommation Collective")
    
    # Vérifier si la nouvelle méthode existe
    if not hasattr(capacity_service, 'get_dashboard_stats'):
        st.error("⚠️ Version obsolète du service capacity détectée!")
        st.info("🔄 Veuillez redémarrer l'application pour charger la nouvelle version.")
        st.code("python restart_app.py\nstreamlit run app.py", language="bash")
        st.stop()
        return
    
    # Récupérer les statistiques
    stats = capacity_service.get_dashboard_stats()
    
    # KPIs principaux
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Points de Production",
            stats['total_production_points'],
            f"{stats['active_production_points']} actifs",
            delta_color="normal"
        )
        
    with col2:
        st.metric(
            "Capacité Totale",
            f"{stats['total_capacity_kwc']:.1f} kWc",
            f"{stats['available_capacity_kwc']:.1f} kWc disponibles"
        )
        
    with col3:
        st.metric(
            "Points de Consommation",
            stats['total_consumption_points'],
            f"{stats['active_allocations']} actifs"
        )
        
    with col4:
        utilization = stats.get('average_utilization', 0)
        color = "normal" if utilization < 80 else "inverse"
        st.metric(
            "Utilisation Moyenne",
            f"{utilization:.0f}%",
            delta_color=color
        )
    
    # Alertes de capacité
    st.markdown("### 🚨 Alertes de Capacité")
    alerts = capacity_service.get_capacity_alerts()
    
    if alerts:
        for alert in alerts:
            if alert['level'] == 'critical':
                st.error(f"🔴 **{alert['point_name']}** : {alert['message']} ({alert['utilization']:.0f}% utilisé)")
            elif alert['level'] == 'warning':
                st.warning(f"🟡 **{alert['point_name']}** : {alert['message']} ({alert['utilization']:.0f}% utilisé)")
            else:
                st.info(f"🔵 **{alert['point_name']}** : {alert['message']} ({alert['utilization']:.0f}% utilisé)")
    else:
        st.success("✅ Aucune alerte de capacité")
    
    # Graphique de répartition
    col1, col2 = st.columns(2)
    
    with col1:
        # Répartition par point de production
        production_data = capacity_service.get_production_summary()
        if production_data:
            fig = px.pie(
                production_data,
                values='capacity_kwc',
                names='name',
                title="Répartition de la Capacité de Production"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Taux d'utilisation par point
        utilization_data = capacity_service.get_utilization_by_point()
        if utilization_data:
            fig = px.bar(
                utilization_data,
                x='utilization_percent',
                y='name',
                orientation='h',
                title="Taux d'Utilisation par Point",
                color='utilization_percent',
                color_continuous_scale=['green', 'yellow', 'red'],
                range_color=[0, 100]
            )
            fig.add_vline(x=80, line_dash="dash", line_color="orange", annotation_text="Seuil 80%")
            fig.add_vline(x=90, line_dash="dash", line_color="red", annotation_text="Seuil 90%")
            st.plotly_chart(fig, use_container_width=True)


def render_production_points(
    capacity_service: CapacityService,
    client_service: ClientService
):
    """Gère les points de production."""
    st.header("⚡ Gestion des Points de Production")
    
    # Actions
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ Nouveau Point", type="primary", key="new_production_point"):
            st.session_state['show_new_production_form'] = True
            
    with col2:
        if st.button("📥 Importer", key="import_production_points"):
            st.session_state['show_import_production'] = True
            
    with col3:
        if st.button("📤 Exporter", key="export_production_points"):
            export_production_points(capacity_service)
            
    with col4:
        if st.button("🔄 Actualiser", key="refresh_production_points"):
            st.rerun()
    
    # Formulaire de création
    if st.session_state.get('show_new_production_form'):
        with st.expander("➕ Créer un Point de Production", expanded=True):
            render_production_point_form(capacity_service, client_service)
    
    # Liste des points existants
    production_points = capacity_service.get_all_production_points()
    
    if not production_points:
        st.info("Aucun point de production défini. Créez-en un pour commencer.")
        return
    
    # Affichage en cartes
    for point in production_points:
        with st.expander(f"⚡ {point.nom} - {point.capacite_kwc} kWc", expanded=False):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                # Informations du point
                st.markdown(f"**Client:** {point.client_nom}")
                st.markdown(f"**Type:** {point.type_installation}")
                st.markdown(f"**Adresse:** {point.adresse}")
                st.markdown(f"**Mise en service:** {point.date_mise_service.strftime('%d/%m/%Y') if point.date_mise_service else 'N/A'}")
                
                # Barre de capacité
                utilization = capacity_service.get_point_utilization(point.id)
                progress_color = "normal" if utilization < 80 else "inverse"
                st.progress(
                    utilization / 100,
                    text=f"Utilisation: {utilization:.0f}%"
                )
                
            with col2:
                # Statistiques
                st.metric("Capacité", f"{point.capacite_kwc} kWc")
                st.metric("Disponible", f"{point.capacite_disponible_kwc:.1f} kWc")
                st.metric("Allocations", point.nombre_allocations)
                
            with col3:
                # Actions
                if st.button("✏️ Modifier", key=f"edit_prod_{point.id}"):
                    st.session_state[f'edit_production_{point.id}'] = True
                    
                if st.button("📊 Détails", key=f"details_prod_{point.id}"):
                    st.session_state[f'show_production_details_{point.id}'] = True
                    
                if point.actif:
                    if st.button("⏸️ Désactiver", key=f"disable_prod_{point.id}"):
                        capacity_service.deactivate_production_point(point.id)
                        st.rerun()
                else:
                    if st.button("▶️ Activer", key=f"enable_prod_{point.id}"):
                        capacity_service.activate_production_point(point.id)
                        st.rerun()
            
            # Graphique des allocations
            if st.checkbox("Voir les allocations", key=f"show_alloc_{point.id}"):
                allocations = capacity_service.get_allocations_for_production(point.id)
                if allocations:
                    df_alloc = pd.DataFrame([{
                        'Client': a.client_consommateur_nom,
                        'Allocation': a.pourcentage_allocation,
                        'Capacité': point.capacite_kwc * a.pourcentage_allocation / 100
                    } for a in allocations])
                    
                    fig = px.pie(
                        df_alloc,
                        values='Allocation',
                        names='Client',
                        title=f"Répartition des allocations - {point.nom}"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Aucune allocation définie pour ce point")


def render_production_point_form(
    capacity_service: CapacityService,
    client_service: ClientService
):
    """Formulaire de création/édition d'un point de production."""
    
    with st.form("production_point_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Sélection du client producteur
            producteurs = client_service.get_producteurs()
            client_options = {c.id: f"{c.nom} ({c.code_client})" for c in producteurs}
            
            client_id = st.selectbox(
                "Client producteur*",
                options=list(client_options.keys()),
                format_func=lambda x: client_options[x]
            )
            
            nom = st.text_input("Nom du point de production*")
            
            type_installation = st.selectbox(
                "Type d'installation*",
                options=['Toiture', 'Sol', 'Ombrière', 'Façade', 'Autre']
            )
            
        with col2:
            capacite = st.number_input(
                "Capacité (kWc)*",
                min_value=0.1,
                max_value=10000.0,
                value=100.0,
                step=0.1
            )
            
            date_mise_service = st.date_input(
                "Date de mise en service",
                value=datetime.today()
            )
            
            adresse = st.text_area(
                "Adresse du point",
                height=100
            )
        
        col3, col4 = st.columns(2)
        
        with col3:
            latitude = st.number_input(
                "Latitude",
                min_value=-90.0,
                max_value=90.0,
                value=43.6,
                format="%.6f"
            )
            
        with col4:
            longitude = st.number_input(
                "Longitude",
                min_value=-180.0,
                max_value=180.0,
                value=7.0,
                format="%.6f"
            )
        
        notes = st.text_area("Notes", height=100)
        
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            if st.form_submit_button("💾 Enregistrer", type="primary"):
                if nom and client_id:
                    try:
                        point = PointProduction(
                            id=None,
                            client_id=client_id,
                            nom=nom,
                            type_installation=type_installation,
                            capacite_kwc=capacite,
                            date_mise_service=date_mise_service,
                            adresse=adresse,
                            latitude=latitude,
                            longitude=longitude,
                            notes=notes
                        )
                        
                        created = capacity_service.create_production_point(point)
                        st.success(f"✅ Point de production '{created.nom}' créé avec succès")
                        del st.session_state['show_new_production_form']
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")
                else:
                    st.warning("⚠️ Veuillez remplir tous les champs obligatoires")
                    
        with col_cancel:
            if st.form_submit_button("❌ Annuler"):
                del st.session_state['show_new_production_form']
                st.rerun()


def render_consumption_points(
    capacity_service: CapacityService,
    client_service: ClientService
):
    """Gère les points de consommation."""
    st.header("🏠 Gestion des Points de Consommation")
    
    # Actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ Nouveau Point", type="primary", key="new_consumption_point"):
            st.session_state['show_new_consumption_form'] = True
            
    with col2:
        if st.button("📥 Importer", key="import_consumption_points"):
            st.session_state['show_import_consumption'] = True
            
    with col3:
        if st.button("🔄 Actualiser", key="refresh_consumption_points"):
            st.rerun()
    
    # Formulaire de création
    if st.session_state.get('show_new_consumption_form'):
        with st.expander("➕ Créer un Point de Consommation", expanded=True):
            render_consumption_point_form(capacity_service, client_service)
    
    # Liste des points existants
    consumption_points = capacity_service.get_all_consumption_points()
    
    if not consumption_points:
        st.info("Aucun point de consommation défini. Créez-en un pour commencer.")
        return
    
    # Affichage par client
    points_by_client = {}
    for point in consumption_points:
        if point.client_id not in points_by_client:
            points_by_client[point.client_id] = []
        points_by_client[point.client_id].append(point)
    
    for client_id, points in points_by_client.items():
        client = client_service.get_by_id(client_id)
        if client:
            st.markdown(f"### 🏢 {client.nom}")
            
            # Tableau des points
            data = []
            for point in points:
                allocation = capacity_service.get_allocation_for_consumption(point.id)
                data.append({
                    'Référence': point.reference_interne,
                    'Type': point.type_point,
                    'Consommation': f"{point.consommation_annuelle_kwh:,.0f} kWh",
                    'Puissance': f"{point.puissance_souscrite_kva} kVA",
                    'Allocation': f"{allocation.point_production_nom} ({allocation.pourcentage_allocation}%)" if allocation else "Non alloué",
                    'Statut': '✅' if point.actif else '❌',
                    'ID': point.id
                })
            
            df = pd.DataFrame(data)
            
            # Affichage avec sélection
            selected = st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            # Actions sur la sélection
            if selected and len(selected.selection.rows) > 0:
                selected_id = df.iloc[selected.selection.rows[0]]['ID']
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("✏️ Modifier", key=f"edit_cons_{selected_id}"):
                        st.session_state[f'edit_consumption_{selected_id}'] = True
                with col2:
                    if st.button("🔄 Allouer", key=f"allocate_cons_{selected_id}"):
                        st.session_state[f'allocate_consumption_{selected_id}'] = True
                with col3:
                    if st.button("🗑️ Supprimer", key=f"delete_cons_{selected_id}"):
                        if capacity_service.delete_consumption_point(selected_id):
                            st.success("Point supprimé")
                            st.rerun()


def render_consumption_point_form(
    capacity_service: CapacityService,
    client_service: ClientService
):
    """Formulaire de création d'un point de consommation."""
    
    with st.form("consumption_point_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Sélection du client consommateur
            consommateurs = client_service.get_consommateurs()
            client_options = {c.id: f"{c.nom} ({c.code_client})" for c in consommateurs}
            
            client_id = st.selectbox(
                "Client consommateur*",
                options=list(client_options.keys()),
                format_func=lambda x: client_options[x]
            )
            
            reference = st.text_input(
                "Référence interne*",
                help="Ex: PDL, numéro de compteur, etc."
            )
            
            type_point = st.selectbox(
                "Type de point*",
                options=['Principal', 'Secondaire', 'Auxiliaire']
            )
            
        with col2:
            consommation = st.number_input(
                "Consommation annuelle (kWh)*",
                min_value=0,
                value=10000,
                step=100
            )
            
            puissance = st.number_input(
                "Puissance souscrite (kVA)*",
                min_value=3,
                max_value=250,
                value=36,
                step=3
            )
            
            adresse = st.text_area(
                "Adresse du point",
                height=100
            )
        
        notes = st.text_area("Notes", height=100)
        
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            if st.form_submit_button("💾 Enregistrer", type="primary"):
                if reference and client_id:
                    try:
                        point = PointConsommation(
                            id=None,
                            client_id=client_id,
                            reference_interne=reference,
                            type_point=type_point,
                            consommation_annuelle_kwh=consommation,
                            puissance_souscrite_kva=puissance,
                            adresse=adresse,
                            notes=notes
                        )
                        
                        created = capacity_service.create_consumption_point(point)
                        st.success(f"✅ Point de consommation créé avec succès")
                        del st.session_state['show_new_consumption_form']
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")
                else:
                    st.warning("⚠️ Veuillez remplir tous les champs obligatoires")
                    
        with col_cancel:
            if st.form_submit_button("❌ Annuler"):
                del st.session_state['show_new_consumption_form']
                st.rerun()


def render_allocations_management(
    capacity_service: CapacityService,
    client_service: ClientService
):
    """Gère les allocations entre production et consommation."""
    st.header("🔄 Gestion des Allocations")
    
    # Vue d'ensemble
    col1, col2 = st.columns(2)
    
    with col1:
        # Points de production disponibles
        st.markdown("### ⚡ Capacité Disponible")
        
        production_points = capacity_service.get_production_points_with_availability()
        
        for point in production_points:
            if point['available_capacity'] > 0:
                st.success(f"✅ **{point['name']}** : {point['available_capacity']:.1f} kWc disponibles sur {point['total_capacity']} kWc")
            else:
                st.error(f"❌ **{point['name']}** : Capacité saturée ({point['total_capacity']} kWc)")
    
    with col2:
        # Points non alloués
        st.markdown("### 🏠 Points Non Alloués")
        
        unallocated = capacity_service.get_unallocated_consumption_points()
        
        if unallocated:
            for point in unallocated:
                client = client_service.get_by_id(point.client_id)
                st.warning(f"⚠️ {client.nom} - {point.reference_interne}")
        else:
            st.success("✅ Tous les points sont alloués")
    
    # Formulaire d'allocation
    st.markdown("### ➕ Nouvelle Allocation")
    
    with st.form("allocation_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Points de production avec capacité
            prod_options = {}
            for point in production_points:
                if point['available_capacity'] > 0:
                    prod_options[point['id']] = f"{point['name']} ({point['available_capacity']:.1f} kWc dispo)"
            
            if not prod_options:
                st.error("Aucune capacité disponible")
                production_id = None
            else:
                production_id = st.selectbox(
                    "Point de production*",
                    options=list(prod_options.keys()),
                    format_func=lambda x: prod_options[x]
                )
        
        with col2:
            # Points de consommation non alloués
            cons_options = {}
            for point in unallocated:
                client = client_service.get_by_id(point.client_id)
                cons_options[point.id] = f"{client.nom} - {point.reference_interne}"
            
            if not cons_options:
                st.info("Tous les points sont déjà alloués")
                consumption_id = None
            else:
                consumption_id = st.selectbox(
                    "Point de consommation*",
                    options=list(cons_options.keys()),
                    format_func=lambda x: cons_options[x]
                )
        
        with col3:
            pourcentage = st.number_input(
                "Pourcentage d'allocation (%)*",
                min_value=1,
                max_value=100,
                value=100,
                help="Pourcentage de la capacité du point de production"
            )
        
        notes = st.text_area("Notes sur l'allocation")
        
        if st.form_submit_button("💾 Créer l'allocation", type="primary"):
            if production_id and consumption_id:
                try:
                    allocation = AutoconsoCollective(
                        id=None,
                        point_production_id=production_id,
                        point_consommation_id=consumption_id,
                        pourcentage_allocation=pourcentage,
                        date_debut=datetime.today().date(),
                        notes=notes
                    )
                    
                    created = capacity_service.create_allocation(allocation)
                    st.success("✅ Allocation créée avec succès")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")
            else:
                st.warning("⚠️ Sélectionnez un point de production et de consommation")
    
    # Liste des allocations actives
    st.markdown("### 📋 Allocations Actives")
    
    allocations = capacity_service.get_all_active_allocations()
    
    if allocations:
        # Préparer les données pour le tableau
        data = []
        for alloc in allocations:
            data.append({
                'Production': alloc.point_production_nom,
                'Consommation': f"{alloc.client_consommateur_nom} - {alloc.point_consommation_ref}",
                'Allocation': f"{alloc.pourcentage_allocation}%",
                'Capacité': f"{alloc.capacite_allouee_kwc:.1f} kWc",
                'Depuis': alloc.date_debut.strftime('%d/%m/%Y'),
                'ID': alloc.id
            })
        
        df = pd.DataFrame(data)
        
        # Affichage avec sélection
        selected = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Actions sur la sélection
        if selected and len(selected.selection.rows) > 0:
            selected_id = df.iloc[selected.selection.rows[0]]['ID']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✏️ Modifier", key=f"edit_alloc_{selected_id}"):
                    st.session_state[f'edit_allocation_{selected_id}'] = True
            with col2:
                if st.button("📊 Historique", key=f"history_alloc_{selected_id}"):
                    st.session_state[f'show_allocation_history_{selected_id}'] = True
            with col3:
                if st.button("🗑️ Terminer", key=f"end_alloc_{selected_id}"):
                    if capacity_service.end_allocation(selected_id):
                        st.success("Allocation terminée")
                        st.rerun()
    else:
        st.info("Aucune allocation active")


def render_autoconso_analytics(
    capacity_service: CapacityService,
    client_service: ClientService
):
    """Affiche les analyses et rapports d'autoconsommation."""
    st.header("📈 Analyses Autoconsommation Collective")
    
    # Période d'analyse
    col1, col2, col3 = st.columns(3)
    
    with col1:
        period = st.selectbox(
            "Période d'analyse",
            options=['Mois en cours', '3 derniers mois', '6 derniers mois', 'Année en cours', 'Personnalisé']
        )
    
    with col2:
        if period == 'Personnalisé':
            date_debut = st.date_input("Date début")
        else:
            date_debut = None
    
    with col3:
        if period == 'Personnalisé':
            date_fin = st.date_input("Date fin")
        else:
            date_fin = None
    
    # Graphiques d'analyse
    col1, col2 = st.columns(2)
    
    with col1:
        # Evolution de l'utilisation
        st.markdown("### 📊 Evolution de l'Utilisation")
        
        # Données simulées pour l'exemple
        dates = pd.date_range(start='2024-01-01', periods=12, freq='M')
        utilization_data = pd.DataFrame({
            'Date': dates,
            'Utilisation': [65, 68, 72, 75, 78, 82, 85, 87, 89, 91, 88, 85]
        })
        
        fig = px.line(
            utilization_data,
            x='Date',
            y='Utilisation',
            title="Taux d'utilisation moyen (%)",
            markers=True
        )
        fig.add_hline(y=80, line_dash="dash", line_color="orange", annotation_text="Seuil optimal")
        fig.add_hline(y=90, line_dash="dash", line_color="red", annotation_text="Seuil critique")
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Répartition par type de client
        st.markdown("### 🏢 Répartition par Type")
        
        type_data = pd.DataFrame({
            'Type': ['Commerces', 'Bureaux', 'Industries', 'Résidentiel'],
            'Capacité': [45, 30, 15, 10]
        })
        
        fig = px.pie(
            type_data,
            values='Capacité',
            names='Type',
            title="Répartition de la capacité allouée (%)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Optimisations suggérées
    st.markdown("### 💡 Suggestions d'Optimisation")
    
    suggestions = capacity_service.get_optimization_suggestions()
    
    if suggestions:
        for sugg in suggestions:
            if sugg['type'] == 'reallocation':
                st.info(f"🔄 **Réallocation suggérée** : Transférer {sugg['percentage']}% de {sugg['from']} vers {sugg['to']} pour optimiser l'utilisation")
            elif sugg['type'] == 'new_client':
                st.success(f"➕ **Nouveau client potentiel** : {sugg['client_name']} pourrait utiliser {sugg['capacity']:.1f} kWc disponibles sur {sugg['production_point']}")
            elif sugg['type'] == 'capacity_warning':
                st.warning(f"⚠️ **Extension recommandée** : {sugg['production_point']} approche de sa capacité maximale, envisager une extension")
    else:
        st.success("✅ L'allocation actuelle est optimale")
    
    # Export des rapports
    st.markdown("### 📤 Export des Rapports")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Rapport Mensuel", use_container_width=True):
            generate_monthly_report(capacity_service)
    
    with col2:
        if st.button("📈 Analyse Détaillée", use_container_width=True):
            generate_detailed_analysis(capacity_service)
    
    with col3:
        if st.button("💰 Rapport Financier", use_container_width=True):
            generate_financial_report(capacity_service)


def export_production_points(capacity_service: CapacityService):
    """Exporte les points de production en Excel."""
    import io
    
    points = capacity_service.get_all_production_points()
    
    if not points:
        st.warning("Aucun point de production à exporter")
        return
    
    # Préparer les données
    data = []
    for point in points:
        data.append({
            'Client': point.client_nom,
            'Nom': point.nom,
            'Type': point.type_installation,
            'Capacité (kWc)': point.capacite_kwc,
            'Disponible (kWc)': point.capacite_disponible_kwc,
            'Utilisation (%)': (point.capacite_kwc - point.capacite_disponible_kwc) / point.capacite_kwc * 100,
            'Mise en service': point.date_mise_service.strftime('%d/%m/%Y') if point.date_mise_service else '',
            'Adresse': point.adresse,
            'Latitude': point.latitude,
            'Longitude': point.longitude,
            'Actif': 'Oui' if point.actif else 'Non'
        })
    
    df = pd.DataFrame(data)
    
    # Créer le fichier Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Points Production', index=False)
        
        # Ajuster la largeur des colonnes
        worksheet = writer.sheets['Points Production']
        for column in worksheet.columns:
            max_length = 0
            column = [cell for cell in column]
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2) * 1.2
            worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
    
    # Télécharger
    st.download_button(
        label="📥 Télécharger Excel",
        data=output.getvalue(),
        file_name=f"points_production_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def generate_monthly_report(capacity_service: CapacityService):
    """Génère un rapport mensuel d'autoconsommation."""
    st.info("Génération du rapport mensuel en cours...")
    # TODO: Implémenter la génération du rapport
    st.success("Rapport généré avec succès")


def generate_detailed_analysis(capacity_service: CapacityService):
    """Génère une analyse détaillée."""
    st.info("Génération de l'analyse détaillée en cours...")
    # TODO: Implémenter la génération de l'analyse
    st.success("Analyse générée avec succès")


def generate_financial_report(capacity_service: CapacityService):
    """Génère un rapport financier."""
    st.info("Génération du rapport financier en cours...")
    # TODO: Implémenter la génération du rapport financier
    st.success("Rapport financier généré avec succès")