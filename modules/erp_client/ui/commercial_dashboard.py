"""Dashboard commercial professionnel pour le module ERP.

Interface haute performance pour la gestion commerciale avec :
- Pipeline de ventes
- Suivi des opportunités
- KPIs commerciaux avancés
- Gestion des tâches et relances
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import json

from ..services.client_service import ClientService
from ..services.pricing_service import PricingService
from ..services.capacity_service import CapacityService
from ..models.client import Client, TypeClient
from ..models.pricing import PrixClient, TypeTarif


def render_commercial_dashboard(
    client_service: ClientService,
    pricing_service: PricingService,
    capacity_service: CapacityService
):
    """Affiche le dashboard commercial principal."""
    
    # En-tête professionnel
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.title("💼 Dashboard Commercial")
        st.caption(f"Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    with col2:
        periode = st.selectbox(
            "Période",
            ["Aujourd'hui", "Cette semaine", "Ce mois", "Ce trimestre", "Cette année"],
            index=2
        )
    
    with col3:
        if st.button("📊 Exporter rapport", type="primary"):
            export_commercial_report(client_service, pricing_service, capacity_service)
    
    # KPIs principaux
    render_kpis_row(client_service, pricing_service, capacity_service, periode)
    
    # Graphiques principaux
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_pipeline_chart(client_service, pricing_service)
    
    with col2:
        render_conversion_funnel(client_service)
    
    # Tableaux de bord détaillés
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Pipeline Commercial",
        "📈 Performance",
        "👥 Portefeuille Clients",
        "📅 Activités",
        "🎯 Objectifs"
    ])
    
    with tab1:
        render_pipeline_details(client_service, pricing_service, capacity_service)
    
    with tab2:
        render_performance_metrics(client_service, pricing_service, capacity_service, periode)
    
    with tab3:
        render_portfolio_analysis(client_service, pricing_service, capacity_service)
    
    with tab4:
        render_activities_tracker(client_service)
    
    with tab5:
        render_objectives_dashboard(client_service, pricing_service)


def render_kpis_row(
    client_service: ClientService,
    pricing_service: PricingService,
    capacity_service: CapacityService,
    periode: str
):
    """Affiche la ligne des KPIs principaux."""
    
    # Calculer les métriques selon la période
    metrics = calculate_period_metrics(client_service, pricing_service, capacity_service, periode)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric(
            "💰 CA Potentiel",
            f"{metrics['ca_potentiel']:,.0f}€",
            f"{metrics['ca_variation']:+.1f}%",
            help="Chiffre d'affaires potentiel total du pipeline"
        )
    
    with col2:
        st.metric(
            "🤝 Nouveaux Clients",
            metrics['nouveaux_clients'],
            f"{metrics['clients_variation']:+.0f}%",
            help=f"Nouveaux clients {periode.lower()}"
        )
    
    with col3:
        st.metric(
            "📊 Taux Conversion",
            f"{metrics['taux_conversion']:.1f}%",
            f"{metrics['conversion_variation']:+.1f}pp",
            help="Taux de conversion prospect → client"
        )
    
    with col4:
        st.metric(
            "⚡ Capacité Vendue",
            f"{metrics['capacite_vendue']:.0f} kWc",
            f"{metrics['capacite_variation']:+.1f}%",
            help="Capacité totale vendue"
        )
    
    with col5:
        st.metric(
            "💵 Panier Moyen",
            f"{metrics['panier_moyen']:,.0f}€",
            f"{metrics['panier_variation']:+.1f}%",
            help="Valeur moyenne par client"
        )
    
    with col6:
        st.metric(
            "⏱️ Cycle Vente",
            f"{metrics['cycle_vente']} jours",
            f"{metrics['cycle_variation']:+.0f}%",
            delta_color="inverse",
            help="Durée moyenne du cycle de vente"
        )


def render_pipeline_chart(client_service: ClientService, pricing_service: PricingService):
    """Affiche le graphique du pipeline commercial."""
    
    # Données du pipeline
    pipeline_stages = {
        "🎯 Prospects": {"count": 45, "value": 2_500_000, "color": "#636EFA"},
        "📞 Qualifiés": {"count": 28, "value": 1_800_000, "color": "#EF553B"},
        "📋 Propositions": {"count": 15, "value": 1_200_000, "color": "#00CC96"},
        "🤝 Négociation": {"count": 8, "value": 800_000, "color": "#AB63FA"},
        "✅ Signés": {"count": 3, "value": 450_000, "color": "#FFA15A"}
    }
    
    # Créer le graphique en entonnoir
    fig = go.Figure()
    
    stages = list(pipeline_stages.keys())
    counts = [pipeline_stages[s]["count"] for s in stages]
    values = [pipeline_stages[s]["value"] for s in stages]
    colors = [pipeline_stages[s]["color"] for s in stages]
    
    # Barres horizontales pour le pipeline
    fig.add_trace(go.Bar(
        y=stages,
        x=values,
        orientation='h',
        text=[f"{c} opportunities<br>{v/1000:.0f}k€" for c, v in zip(counts, values)],
        textposition='inside',
        marker=dict(color=colors),
        hovertemplate='<b>%{y}</b><br>Nombre: %{text}<br>Valeur: %{x:,.0f}€<extra></extra>'
    ))
    
    fig.update_layout(
        title={
            'text': "Pipeline Commercial",
            'font': {'size': 20}
        },
        xaxis_title="Valeur potentielle (€)",
        yaxis_title="",
        height=400,
        showlegend=False,
        xaxis=dict(tickformat=",.0f"),
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_conversion_funnel(client_service: ClientService):
    """Affiche l'entonnoir de conversion."""
    
    # Données de conversion
    funnel_data = pd.DataFrame({
        'Étape': ['Visiteurs', 'Prospects', 'Qualifiés', 'Propositions', 'Clients'],
        'Nombre': [500, 120, 80, 40, 15],
        'Taux': [100, 24, 16, 8, 3]
    })
    
    fig = go.Figure(go.Funnel(
        y=funnel_data['Étape'],
        x=funnel_data['Nombre'],
        textinfo="value+percent initial",
        marker=dict(
            color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
        ),
        connector=dict(line=dict(color="rgb(63, 63, 63)", width=3))
    ))
    
    fig.update_layout(
        title="Entonnoir de Conversion",
        height=400,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_pipeline_details(
    client_service: ClientService,
    pricing_service: PricingService,
    capacity_service: CapacityService
):
    """Affiche les détails du pipeline commercial."""
    
    st.subheader("🎯 Détails du Pipeline")
    
    # Filtres
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        stage_filter = st.selectbox(
            "Étape",
            ["Toutes", "Prospects", "Qualifiés", "Propositions", "Négociation", "Signés"],
            key="pipeline_stage_filter"
        )
    
    with col2:
        commercial_filter = st.selectbox(
            "Commercial",
            ["Tous", "Jean Dupont", "Marie Martin", "Pierre Durand"],
            key="pipeline_commercial_filter"
        )
    
    with col3:
        priority_filter = st.selectbox(
            "Priorité",
            ["Toutes", "🔴 Haute", "🟡 Moyenne", "🟢 Basse"],
            key="pipeline_priority_filter"
        )
    
    with col4:
        value_filter = st.selectbox(
            "Valeur",
            ["Toutes", "> 100k€", "50-100k€", "< 50k€"],
            key="pipeline_value_filter"
        )
    
    # Tableau des opportunités
    opportunities_data = generate_opportunities_data()
    
    # Appliquer les filtres
    if stage_filter != "Toutes":
        opportunities_data = opportunities_data[opportunities_data['Étape'] == stage_filter]
    
    # Configuration du dataframe
    column_config = {
        "Priorité": st.column_config.TextColumn("Priorité", width="small"),
        "Client": st.column_config.TextColumn("Client", width="medium"),
        "Étape": st.column_config.SelectboxColumn(
            "Étape",
            options=["Prospects", "Qualifiés", "Propositions", "Négociation", "Signés"],
            width="small"
        ),
        "Valeur": st.column_config.NumberColumn(
            "Valeur",
            format="%.0f €",
            width="small"
        ),
        "Probabilité": st.column_config.ProgressColumn(
            "Probabilité",
            min_value=0,
            max_value=100,
            format="%d%%",
            width="small"
        ),
        "Commercial": st.column_config.TextColumn("Commercial", width="small"),
        "Prochaine action": st.column_config.DateColumn(
            "Prochaine action",
            format="DD/MM/YYYY",
            width="small"
        )
    }
    
    # Afficher le tableau interactif
    selected = st.dataframe(
        opportunities_data,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # Actions sur la sélection
    if selected and len(selected.selection.rows) > 0:
        selected_opp = opportunities_data.iloc[selected.selection.rows[0]]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📝 Modifier", key="edit_opp"):
                st.session_state['edit_opportunity'] = selected_opp
        
        with col2:
            if st.button("📧 Envoyer proposition", key="send_proposal"):
                st.success(f"Proposition envoyée à {selected_opp['Client']}")
        
        with col3:
            if st.button("📞 Programmer appel", key="schedule_call"):
                st.session_state['schedule_call'] = selected_opp
        
        with col4:
            if st.button("✅ Marquer comme gagné", key="mark_won"):
                st.balloons()
                st.success(f"Félicitations ! Affaire {selected_opp['Client']} gagnée !")


def render_performance_metrics(
    client_service: ClientService,
    pricing_service: PricingService,
    capacity_service: CapacityService,
    periode: str
):
    """Affiche les métriques de performance."""
    
    st.subheader("📈 Métriques de Performance")
    
    # Graphique d'évolution du CA
    col1, col2 = st.columns(2)
    
    with col1:
        # Évolution du CA
        dates = pd.date_range(end=date.today(), periods=12, freq='M')
        ca_data = pd.DataFrame({
            'Date': dates,
            'CA Réalisé': [150000 + i * 10000 + (i % 3) * 20000 for i in range(12)],
            'CA Objectif': [180000 + i * 5000 for i in range(12)]
        })
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=ca_data['Date'],
            y=ca_data['CA Réalisé'],
            name='CA Réalisé',
            line=dict(color='#2E86AB', width=3),
            fill='tonexty',
            fillcolor='rgba(46, 134, 171, 0.2)'
        ))
        
        fig.add_trace(go.Scatter(
            x=ca_data['Date'],
            y=ca_data['CA Objectif'],
            name='CA Objectif',
            line=dict(color='#A23B72', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title="Évolution du Chiffre d'Affaires",
            xaxis_title="",
            yaxis_title="Montant (€)",
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Répartition par type de client
        client_stats = client_service.get_statistics()
        
        # Calculer le CA par type
        ca_by_type = {
            'Producteurs': 450000,
            'Consommateurs': 320000,
            'Prosumers': 180000
        }
        
        fig = go.Figure(data=[go.Pie(
            labels=list(ca_by_type.keys()),
            values=list(ca_by_type.values()),
            hole=.4,
            marker_colors=['#2E86AB', '#A23B72', '#F18F01']
        )])
        
        fig.update_layout(
            title="CA par Type de Client",
            height=400,
            annotations=[dict(
                text='950k€',
                x=0.5, y=0.5,
                font_size=24,
                showarrow=False
            )]
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Tableau de bord des commerciaux
    st.markdown("### 👥 Performance par Commercial")
    
    commercial_data = pd.DataFrame({
        'Commercial': ['Jean Dupont', 'Marie Martin', 'Pierre Durand', 'Sophie Bernard'],
        'CA Réalisé': [320000, 280000, 245000, 105000],
        'Objectif': [300000, 300000, 250000, 150000],
        'Taux': [106.7, 93.3, 98.0, 70.0],
        'Nb Clients': [15, 12, 11, 8],
        'Panier Moyen': [21333, 23333, 22273, 13125]
    })
    
    # Créer des colonnes pour chaque commercial
    cols = st.columns(len(commercial_data))
    
    for idx, (_, row) in enumerate(commercial_data.iterrows()):
        with cols[idx]:
            # Indicateur de performance
            color = "🟢" if row['Taux'] >= 100 else "🟡" if row['Taux'] >= 80 else "🔴"
            
            st.markdown(f"**{color} {row['Commercial']}**")
            st.metric(
                "CA Réalisé",
                f"{row['CA Réalisé']:,.0f}€",
                f"{row['Taux']:.1f}% de l'objectif"
            )
            st.metric(
                "Clients",
                row['Nb Clients'],
                f"Panier: {row['Panier Moyen']:,.0f}€"
            )
            
            # Barre de progression
            st.progress(min(row['Taux'] / 100, 1.0))


def render_portfolio_analysis(
    client_service: ClientService,
    pricing_service: PricingService,
    capacity_service: CapacityService
):
    """Analyse du portefeuille clients."""
    
    st.subheader("👥 Analyse du Portefeuille")
    
    # Matrice BCG simplifiée
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Générer des données pour la matrice
        clients_data = []
        
        # Simuler des données pour l'exemple
        client_names = [
            "SolarPark Côte d'Azur", "Green Energy SA", "EcoPower Industries",
            "Sunshine Collective", "WindTech Solutions", "BioEnergy Corp",
            "CleanPower Ltd", "RenewaCorp", "EcoVolt Systems", "Future Energy"
        ]
        
        for i, name in enumerate(client_names):
            clients_data.append({
                'name': name,
                'growth': 5 + i * 3 + (i % 4) * 5,  # Croissance
                'share': 3 + i * 2 + (i % 3) * 4,   # Part de marché
                'revenue': 50000 + i * 20000 + (i % 5) * 30000,  # CA
                'size': 20 + i * 5  # Taille du point
            })
        
        df_matrix = pd.DataFrame(clients_data)
        
        # Créer la matrice BCG
        fig = px.scatter(
            df_matrix,
            x='share',
            y='growth',
            size='revenue',
            hover_data=['name', 'revenue'],
            labels={
                'share': 'Part de marché relative (%)',
                'growth': 'Taux de croissance (%)',
                'revenue': 'CA annuel'
            },
            title="Matrice de Portefeuille (type BCG)"
        )
        
        # Ajouter les quadrants
        fig.add_hline(y=10, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_vline(x=10, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Annotations des quadrants
        fig.add_annotation(x=5, y=20, text="❓ Dilemmes", showarrow=False, font=dict(size=14))
        fig.add_annotation(x=15, y=20, text="⭐ Stars", showarrow=False, font=dict(size=14))
        fig.add_annotation(x=5, y=5, text="🐕 Poids morts", showarrow=False, font=dict(size=14))
        fig.add_annotation(x=15, y=5, text="🐄 Vaches à lait", showarrow=False, font=dict(size=14))
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Répartition géographique
        st.markdown("### 🗺️ Répartition Géographique")
        
        geo_data = {
            'Nice': 35,
            'Cannes': 25,
            'Antibes': 20,
            'Grasse': 10,
            'Autres': 10
        }
        
        fig = go.Figure(data=[go.Pie(
            labels=list(geo_data.keys()),
            values=list(geo_data.values()),
            textinfo='label+percent',
            hole=0.3
        )])
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Top clients
        st.markdown("### 🏆 Top 5 Clients")
        
        top_clients = pd.DataFrame({
            'Client': ['SolarPark Côte d\'Azur', 'Green Energy SA', 'EcoPower Industries', 'Sunshine Collective', 'WindTech Solutions'],
            'CA': [250000, 180000, 150000, 120000, 100000],
            'Évolution': ['+15%', '+8%', '+12%', '-5%', '+20%']
        })
        
        for _, row in top_clients.iterrows():
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.text(row['Client'])
            with col2:
                st.text(f"{row['CA']:,.0f}€")
            with col3:
                color = "🟢" if row['Évolution'].startswith('+') else "🔴"
                st.text(f"{color} {row['Évolution']}")


def render_activities_tracker(client_service: ClientService):
    """Suivi des activités commerciales."""
    
    st.subheader("📅 Suivi des Activités")
    
    # Calendrier des activités
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Activités du jour
        st.markdown("### 📆 Aujourd'hui")
        
        activities = [
            {"heure": "09:00", "type": "📞", "action": "Appel Client A", "commercial": "Jean Dupont", "statut": "✅"},
            {"heure": "10:30", "type": "🤝", "action": "RDV Client B", "commercial": "Marie Martin", "statut": "⏳"},
            {"heure": "14:00", "type": "📧", "action": "Envoi proposition Client C", "commercial": "Pierre Durand", "statut": "⏳"},
            {"heure": "16:00", "type": "📊", "action": "Présentation Client D", "commercial": "Jean Dupont", "statut": "⏳"}
        ]
        
        for activity in activities:
            col_time, col_type, col_action, col_comm, col_status = st.columns([1, 1, 3, 2, 1])
            
            with col_time:
                st.text(activity['heure'])
            with col_type:
                st.text(activity['type'])
            with col_action:
                st.text(activity['action'])
            with col_comm:
                st.text(activity['commercial'])
            with col_status:
                st.text(activity['statut'])
            
            st.divider()
    
    with col2:
        # Statistiques d'activités
        st.markdown("### 📊 Cette semaine")
        
        activity_stats = pd.DataFrame({
            'Type': ['Appels', 'Emails', 'RDV', 'Propositions'],
            'Réalisé': [45, 120, 12, 8],
            'Objectif': [50, 100, 15, 10]
        })
        
        for _, row in activity_stats.iterrows():
            st.metric(
                row['Type'],
                row['Réalisé'],
                f"{(row['Réalisé']/row['Objectif']*100):.0f}% de l'objectif"
            )
            st.progress(min(row['Réalisé'] / row['Objectif'], 1.0))


def render_objectives_dashboard(client_service: ClientService, pricing_service: PricingService):
    """Tableau de bord des objectifs."""
    
    st.subheader("🎯 Suivi des Objectifs")
    
    # Objectifs annuels
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # CA annuel
        ca_objectif = 3_000_000
        ca_realise = 2_150_000
        progress = ca_realise / ca_objectif
        
        st.markdown("### 💰 Chiffre d'Affaires")
        st.metric(
            "Réalisé YTD",
            f"{ca_realise:,.0f}€",
            f"{progress*100:.1f}% de l'objectif annuel"
        )
        st.progress(progress)
        st.caption(f"Objectif: {ca_objectif:,.0f}€")
    
    with col2:
        # Nouveaux clients
        clients_objectif = 100
        clients_realise = 73
        progress = clients_realise / clients_objectif
        
        st.markdown("### 👥 Nouveaux Clients")
        st.metric(
            "Acquis YTD",
            clients_realise,
            f"{progress*100:.1f}% de l'objectif annuel"
        )
        st.progress(progress)
        st.caption(f"Objectif: {clients_objectif} clients")
    
    with col3:
        # Capacité installée
        capacite_objectif = 5000  # kWc
        capacite_realise = 3750
        progress = capacite_realise / capacite_objectif
        
        st.markdown("### ⚡ Capacité Installée")
        st.metric(
            "Installé YTD",
            f"{capacite_realise} kWc",
            f"{progress*100:.1f}% de l'objectif annuel"
        )
        st.progress(progress)
        st.caption(f"Objectif: {capacite_objectif} kWc")
    
    # Prévisions
    st.markdown("### 📈 Prévisions de Fin d'Année")
    
    # Calculer les prévisions basées sur la tendance actuelle
    mois_ecoules = datetime.now().month
    mois_restants = 12 - mois_ecoules
    
    ca_prevision = ca_realise + (ca_realise / mois_ecoules * mois_restants)
    clients_prevision = int(clients_realise + (clients_realise / mois_ecoules * mois_restants))
    capacite_prevision = capacite_realise + (capacite_realise / mois_ecoules * mois_restants)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        delta = ((ca_prevision / ca_objectif) - 1) * 100
        color = "inverse" if delta < 0 else "normal"
        st.metric(
            "CA prévisionnel",
            f"{ca_prevision:,.0f}€",
            f"{delta:+.1f}% vs objectif",
            delta_color=color
        )
    
    with col2:
        delta = ((clients_prevision / clients_objectif) - 1) * 100
        color = "inverse" if delta < 0 else "normal"
        st.metric(
            "Clients prévisionnels",
            clients_prevision,
            f"{delta:+.1f}% vs objectif",
            delta_color=color
        )
    
    with col3:
        delta = ((capacite_prevision / capacite_objectif) - 1) * 100
        color = "inverse" if delta < 0 else "normal"
        st.metric(
            "Capacité prévisionnelle",
            f"{capacite_prevision:.0f} kWc",
            f"{delta:+.1f}% vs objectif",
            delta_color=color
        )


def calculate_period_metrics(
    client_service: ClientService,
    pricing_service: PricingService,
    capacity_service: CapacityService,
    periode: str
) -> Dict:
    """Calcule les métriques pour la période sélectionnée."""
    
    # Simuler des métriques pour l'exemple
    # Dans un cas réel, ces valeurs seraient calculées depuis la base de données
    
    metrics = {
        'ca_potentiel': 4_750_000,
        'ca_variation': 12.5,
        'nouveaux_clients': 15,
        'clients_variation': 25.0,
        'taux_conversion': 28.5,
        'conversion_variation': 3.2,
        'capacite_vendue': 450.0,
        'capacite_variation': 18.0,
        'panier_moyen': 85_000,
        'panier_variation': -5.2,
        'cycle_vente': 35,
        'cycle_variation': -12.0
    }
    
    # Ajuster selon la période
    period_multipliers = {
        "Aujourd'hui": 0.05,
        "Cette semaine": 0.25,
        "Ce mois": 1.0,
        "Ce trimestre": 3.0,
        "Cette année": 12.0
    }
    
    multiplier = period_multipliers.get(periode, 1.0)
    
    for key in ['ca_potentiel', 'nouveaux_clients', 'capacite_vendue']:
        metrics[key] = int(metrics[key] * multiplier)
    
    return metrics


def generate_opportunities_data() -> pd.DataFrame:
    """Génère des données d'opportunités pour l'exemple."""
    
    opportunities = []
    stages = ["Prospects", "Qualifiés", "Propositions", "Négociation"]
    priorities = ["🔴", "🟡", "🟢"]
    commercials = ["Jean Dupont", "Marie Martin", "Pierre Durand", "Sophie Bernard"]
    
    client_names = [
        "SolarTech Industries", "Green Power SA", "EcoEnergy Corp",
        "Renewable Solutions", "CleanTech Ltd", "Future Energy Systems",
        "Smart Grid Technologies", "BioWatt Industries", "WindPower Collective",
        "Solar Innovations", "EcoPark Development", "Sustainable Energy Group"
    ]
    
    for i, client in enumerate(client_names[:12]):
        stage = stages[i % len(stages)]
        probability = {
            "Prospects": 20,
            "Qualifiés": 40,
            "Propositions": 60,
            "Négociation": 80
        }[stage]
        
        opportunities.append({
            'Priorité': priorities[i % len(priorities)],
            'Client': client,
            'Étape': stage,
            'Valeur': 50000 + (i * 25000) + (i % 3) * 50000,
            'Probabilité': probability,
            'Commercial': commercials[i % len(commercials)],
            'Prochaine action': date.today() + timedelta(days=i % 7)
        })
    
    return pd.DataFrame(opportunities)


def export_commercial_report(
    client_service: ClientService,
    pricing_service: PricingService,
    capacity_service: CapacityService
):
    """Exporte le rapport commercial au format Excel."""
    
    import io
    
    # Créer un buffer pour le fichier Excel
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Feuille 1: KPIs
        kpis_data = pd.DataFrame({
            'Indicateur': ['CA Potentiel', 'Nouveaux Clients', 'Taux Conversion', 'Capacité Vendue'],
            'Valeur': ['4,750,000€', '15', '28.5%', '450 kWc'],
            'Variation': ['+12.5%', '+25.0%', '+3.2pp', '+18.0%']
        })
        kpis_data.to_excel(writer, sheet_name='KPIs', index=False)
        
        # Feuille 2: Pipeline
        pipeline_data = generate_opportunities_data()
        pipeline_data.to_excel(writer, sheet_name='Pipeline', index=False)
        
        # Feuille 3: Performance commerciaux
        commercial_data = pd.DataFrame({
            'Commercial': ['Jean Dupont', 'Marie Martin', 'Pierre Durand', 'Sophie Bernard'],
            'CA Réalisé': [320000, 280000, 245000, 105000],
            'Objectif': [300000, 300000, 250000, 150000],
            'Taux Atteinte': ['106.7%', '93.3%', '98.0%', '70.0%']
        })
        commercial_data.to_excel(writer, sheet_name='Performance', index=False)
    
    # Préparer le téléchargement
    st.download_button(
        label="📥 Télécharger le rapport commercial",
        data=output.getvalue(),
        file_name=f"rapport_commercial_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )