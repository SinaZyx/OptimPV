"""Interface Streamlit pour le tableau de bord des prix et évolutions.

Ce module fournit les visualisations et analyses des prix clients,
incluant les projections avec inflation et les comparaisons tarifaires.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date, timedelta
import logging
from typing import Optional, List, Dict, Any

from ..models.client import Client
from ..services.client_service import ClientService
from ..services.pricing_service import PricingService, PrixClient
from ..services.inflation_service import InflationService

logger = logging.getLogger(__name__)


def render_pricing_dashboard(
    client_service: ClientService = None,
    pricing_service: PricingService = None,
    inflation_service: InflationService = None
):
    """Affiche le tableau de bord complet des prix.
    
    Args:
        client_service: Service clients
        pricing_service: Service prix
        inflation_service: Service inflation
    """
    if client_service is None:
        client_service = ClientService()
    if pricing_service is None:
        pricing_service = PricingService()
    if inflation_service is None:
        inflation_service = InflationService()
        
    st.title("💰 Tableau de bord Prix & Évolutions")
    
    # Sélection du client (obligatoire)
    client = select_client_for_pricing(client_service)
    if not client:
        st.warning("⚠️ Veuillez sélectionner un client pour accéder aux analyses de prix")
        return
        
    # Onglets principaux
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Prix actuel",
        "📈 Historique",
        "🔮 Projections",
        "⚖️ Comparaisons",
        "⚡ Gestion prix"
    ])
    
    with tab1:
        render_current_pricing(client, pricing_service)
        
    with tab2:
        render_price_history(client, pricing_service)
        
    with tab3:
        render_price_projections(client, pricing_service, inflation_service)
        
    with tab4:
        render_price_comparisons(client, pricing_service, inflation_service)
        
    with tab5:
        render_price_management(client, pricing_service)


def select_client_for_pricing(client_service: ClientService) -> Optional[Client]:
    """Widget de sélection du client pour l'analyse des prix.
    
    Args:
        client_service: Service clients
        
    Returns:
        Client sélectionné ou None
    """
    # Récupérer tous les clients actifs
    clients = client_service.get_all(include_inactive=False)
    
    if not clients:
        st.error("Aucun client actif dans la base")
        return None
        
    # Préparer les options
    client_options = {f"{c.nom} ({c.code_client})": c for c in clients}
    
    # Widget de sélection
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_name = st.selectbox(
            "🔍 Sélectionner un client",
            options=list(client_options.keys()),
            index=0 if not st.session_state.get('selected_client_id') else None,
            placeholder="Choisir un client..."
        )
        
    with col2:
        if st.button("🔄 Actualiser"):
            st.rerun()
            
    if selected_name:
        client = client_options[selected_name]
        st.session_state['selected_client_id'] = client.id
        
        # Afficher les infos du client
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Type", client.type_client.value.capitalize())
        with col2:
            st.metric("Zone", client.zone_geographique or "Non définie")
        with col3:
            st.metric("Ville", client.ville or "Non renseignée")
        with col4:
            status = "🟢 Actif" if client.actif else "🔴 Inactif"
            st.metric("Statut", status)
            
        return client
        
    return None


def render_current_pricing(client: Client, pricing_service: PricingService):
    """Affiche les informations de prix actuelles du client.
    
    Args:
        client: Client sélectionné
        pricing_service: Service prix
    """
    st.subheader("📊 Tarification actuelle")
    
    # Récupérer le prix actif
    current_price = pricing_service.get_active_price(client.id)
    
    if not current_price:
        st.warning("⚠️ Aucun prix défini pour ce client")
        
        # Proposer de créer un prix
        if st.button("➕ Définir un prix", type="primary"):
            st.session_state['create_price'] = True
        return
        
    # Affichage du prix actuel
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Prix actuel",
            f"{current_price.prix_kwh:.4f} €/kWh",
            help="Prix hors taxes"
        )
        
    with col2:
        st.metric(
            "Type de tarif",
            current_price.type_tarif.value.capitalize(),
            help="Fixe, indexé ou dynamique"
        )
        
    with col3:
        if current_price.remise_pourcentage > 0:
            st.metric(
                "Remise appliquée",
                f"{current_price.remise_pourcentage:.1f}%"
            )
        else:
            st.metric("Remise", "Aucune")
            
    # Détails du prix
    with st.expander("📋 Détails du tarif", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Date de début:** {current_price.date_debut.strftime('%d/%m/%Y')}")
            if current_price.date_fin:
                st.write(f"**Date de fin:** {current_price.date_fin.strftime('%d/%m/%Y')}")
            else:
                st.write("**Date de fin:** Indéterminée")
                
        with col2:
            if current_price.reference_prix:
                st.write(f"**Référence:** {current_price.reference_prix}")
            if current_price.notes:
                st.write(f"**Notes:** {current_price.notes}")
                
        # Formule de calcul si dynamique
        if current_price.type_tarif == 'dynamique' and current_price.formule_calcul:
            st.markdown("### 🧮 Formule de calcul")
            st.json(current_price.formule_calcul)
            
    # Comparaison avec références
    st.markdown("### 📊 Positionnement tarifaire")
    
    references = {
        'EDF TRV Base': pricing_service.PRIX_REFERENCES['EDF_TRV_BASE'],
        'EDF TRV HP': pricing_service.PRIX_REFERENCES['EDF_TRV_HP'],
        'EDF TRV HC': pricing_service.PRIX_REFERENCES['EDF_TRV_HC'],
        'Spot moyen': pricing_service.PRIX_REFERENCES['SPOT_MOYEN']
    }
    
    # Graphique de comparaison
    fig = go.Figure()
    
    # Prix du client
    fig.add_trace(go.Bar(
        name='Prix client',
        x=['Prix client'],
        y=[current_price.prix_kwh],
        marker_color='darkblue',
        text=[f"{current_price.prix_kwh:.4f}"],
        textposition='outside'
    ))
    
    # Prix de référence
    for ref_name, ref_price in references.items():
        diff_pct = ((current_price.prix_kwh - ref_price) / ref_price) * 100
        color = 'green' if current_price.prix_kwh < ref_price else 'red'
        
        fig.add_trace(go.Bar(
            name=ref_name,
            x=[ref_name],
            y=[ref_price],
            marker_color=color,
            opacity=0.6,
            text=[f"{ref_price:.4f}<br>{diff_pct:+.1f}%"],
            textposition='outside'
        ))
        
    fig.update_layout(
        title="Comparaison avec les prix de référence",
        yaxis_title="Prix (€/kWh)",
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_price_history(client: Client, pricing_service: PricingService):
    """Affiche l'historique des prix du client.
    
    Args:
        client: Client sélectionné
        pricing_service: Service prix
    """
    st.subheader("📈 Historique des prix")
    
    # Récupérer l'historique
    price_history = pricing_service.get_price_history(client.id)
    
    if not price_history:
        st.info("Aucun historique de prix disponible")
        return
        
    # Préparer les données pour le graphique
    dates = []
    prices = []
    
    for prix in price_history:
        # Point de début
        dates.append(prix.date_debut)
        prices.append(prix.prix_kwh)
        
        # Point de fin si défini
        if prix.date_fin:
            dates.append(prix.date_fin)
            prices.append(prix.prix_kwh)
        else:
            # Prolonger jusqu'à aujourd'hui
            dates.append(date.today())
            prices.append(prix.prix_kwh)
            
    # Créer le graphique
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode='lines+markers',
        name='Prix €/kWh',
        line=dict(shape='hv', width=2),
        marker=dict(size=8)
    ))
    
    # Ajouter les annotations pour chaque période
    for i, prix in enumerate(price_history):
        fig.add_annotation(
            x=prix.date_debut,
            y=prix.prix_kwh,
            text=f"{prix.prix_kwh:.4f} €/kWh<br>{prix.type_tarif}",
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-40
        )
        
    fig.update_layout(
        title="Évolution historique des prix",
        xaxis_title="Date",
        yaxis_title="Prix (€/kWh)",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tableau détaillé
    with st.expander("📊 Détail de l'historique"):
        history_data = []
        for prix in price_history:
            history_data.append({
                'Début': prix.date_debut.strftime('%d/%m/%Y'),
                'Fin': prix.date_fin.strftime('%d/%m/%Y') if prix.date_fin else 'En cours',
                'Prix (€/kWh)': f"{prix.prix_kwh:.4f}",
                'Type': prix.type_tarif.value.capitalize(),
                'Remise': f"{prix.remise_pourcentage}%" if prix.remise_pourcentage > 0 else '-',
                'Référence': prix.reference_prix or '-',
                'Notes': prix.notes or '-'
            })
            
        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True, hide_index=True)


def render_price_projections(
    client: Client,
    pricing_service: PricingService,
    inflation_service: InflationService
):
    """Affiche les projections de prix avec inflation.
    
    Args:
        client: Client sélectionné
        pricing_service: Service prix
        inflation_service: Service inflation
    """
    st.subheader("🔮 Projections de prix")
    
    # Paramètres de projection
    col1, col2, col3 = st.columns(3)
    
    with col1:
        projection_years = st.slider(
            "Horizon de projection (années)",
            min_value=1,
            max_value=30,
            value=10,
            step=1
        )
        
    with col2:
        scenario = st.selectbox(
            "Scénario d'inflation",
            options=['conservateur', 'modere', 'pessimiste'],
            index=1,
            format_func=lambda x: x.capitalize()
        )
        
    with col3:
        custom_rate = st.number_input(
            "Ou taux personnalisé (%)",
            min_value=0.0,
            max_value=10.0,
            value=0.0,
            step=0.1,
            help="Laisser à 0 pour utiliser le scénario"
        )
        
    # Récupérer le prix actuel
    current_price = pricing_service.get_active_price(client.id)
    if not current_price:
        st.warning("Aucun prix actuel défini")
        return
        
    # Calculer les projections
    if custom_rate > 0:
        # Projection avec taux personnalisé
        projections = inflation_service.project_value(
            initial_value=current_price.prix_kwh,
            years=projection_years,
            custom_rates=[custom_rate] * projection_years,
            category='electricite'
        )
    else:
        # Projection avec scénario
        projections = inflation_service.project_value(
            initial_value=current_price.prix_kwh,
            years=projection_years,
            inflation_scenario=scenario,
            category='electricite'
        )
        
    # Graphique des projections
    fig = go.Figure()
    
    # Prix projeté
    years = [p['year'] for p in projections]
    values = [p['value'] for p in projections]
    
    fig.add_trace(go.Scatter(
        x=years,
        y=values,
        mode='lines+markers',
        name='Prix projeté',
        line=dict(width=3),
        marker=dict(size=8)
    ))
    
    # Zone d'incertitude
    if scenario == 'modere':
        # Ajouter les scénarios optimiste et pessimiste
        proj_optimiste = inflation_service.project_value(
            initial_value=current_price.prix_kwh,
            years=projection_years,
            inflation_scenario='conservateur',
            category='electricite'
        )
        proj_pessimiste = inflation_service.project_value(
            initial_value=current_price.prix_kwh,
            years=projection_years,
            inflation_scenario='pessimiste',
            category='electricite'
        )
        
        values_min = [p['value'] for p in proj_optimiste]
        values_max = [p['value'] for p in proj_pessimiste]
        
        fig.add_trace(go.Scatter(
            x=years + years[::-1],
            y=values_max + values_min[::-1],
            fill='toself',
            fillcolor='rgba(0,100,255,0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Plage d\'incertitude',
            showlegend=True
        ))
        
    fig.update_layout(
        title=f"Projection du prix sur {projection_years} ans",
        xaxis_title="Année",
        yaxis_title="Prix (€/kWh)",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Métriques clés
    col1, col2, col3, col4 = st.columns(4)
    
    final_projection = projections[-1]
    
    with col1:
        st.metric(
            "Prix initial",
            f"{projections[0]['value']:.4f} €/kWh"
        )
        
    with col2:
        st.metric(
            f"Prix en {final_projection['year']}",
            f"{final_projection['value']:.4f} €/kWh",
            f"+{final_projection['cumulative_inflation']:.1f}%"
        )
        
    with col3:
        augmentation_totale = final_projection['value'] - projections[0]['value']
        st.metric(
            "Augmentation totale",
            f"+{augmentation_totale:.4f} €/kWh",
            f"{(augmentation_totale/projections[0]['value']*100):.1f}%"
        )
        
    with col4:
        taux_moyen = (pow(final_projection['value']/projections[0]['value'], 1/projection_years) - 1) * 100
        st.metric(
            "Inflation moyenne",
            f"{taux_moyen:.2f}% /an"
        )
        
    # Impact sur la facture
    with st.expander("💡 Impact sur la facture annuelle"):
        conso_annuelle = st.number_input(
            "Consommation annuelle (kWh)",
            min_value=1000,
            max_value=1000000,
            value=10000,
            step=1000
        )
        
        # Calculer l'impact
        impact = inflation_service.calculate_price_evolution_impact(
            annual_consumption_kwh=conso_annuelle,
            current_price_kwh=current_price.prix_kwh,
            years=projection_years,
            inflation_scenario=scenario
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            facture_actuelle = conso_annuelle * current_price.prix_kwh
            st.metric(
                "Facture actuelle",
                f"{facture_actuelle:,.0f} €/an"
            )
            
        with col2:
            facture_future = conso_annuelle * final_projection['value']
            st.metric(
                f"Facture en {final_projection['year']}",
                f"{facture_future:,.0f} €/an",
                f"+{((facture_future/facture_actuelle-1)*100):.1f}%"
            )
            
        st.info(
            f"💰 Coût cumulé sur {projection_years} ans: "
            f"**{impact['cumulative_cost_variable']:,.0f} €**"
        )


def render_price_comparisons(
    client: Client,
    pricing_service: PricingService,
    inflation_service: InflationService
):
    """Affiche les comparaisons de prix et analyses.
    
    Args:
        client: Client sélectionné
        pricing_service: Service prix
        inflation_service: Service inflation
    """
    st.subheader("⚖️ Analyses comparatives")
    
    current_price = pricing_service.get_active_price(client.id)
    if not current_price:
        st.warning("Aucun prix actuel défini")
        return
        
    # Comparaison avec les références
    st.markdown("### 📊 Comparaison avec les tarifs de référence")
    
    comparison = pricing_service.compare_with_reference(
        client_id=client.id,
        reference_type='EDF_TRV_BASE',
        period_years=5
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        delta_color = "inverse" if comparison['avantageux'] else "normal"
        st.metric(
            "Écart vs TRV",
            f"{comparison['difference_pct']:+.1f}%",
            f"{comparison['difference']:+.4f} €/kWh",
            delta_color=delta_color
        )
        
    with col2:
        st.metric(
            "Économie annuelle",
            f"{comparison['economie_annuelle']:,.0f} €",
            "Sur base 10 MWh/an"
        )
        
    with col3:
        st.metric(
            f"Économie sur {comparison['periode_ans']} ans",
            f"{comparison['economie_periode']:,.0f} €"
        )
        
    # Comparaison multi-scénarios
    st.markdown("### 🔮 Comparaison des scénarios d'évolution")
    
    # Paramètres
    col1, col2 = st.columns(2)
    with col1:
        horizon = st.slider("Horizon (années)", 5, 20, 10)
    with col2:
        conso_ref = st.number_input(
            "Consommation de référence (MWh/an)",
            min_value=1,
            max_value=1000,
            value=10
        )
        
    # Calculer les scénarios
    scenarios = inflation_service.compare_scenarios(
        initial_value=current_price.prix_kwh,
        years=horizon,
        category='electricite'
    )
    
    # Graphique comparatif
    fig = go.Figure()
    
    colors = {
        'conservateur': 'green',
        'modere': 'blue',
        'pessimiste': 'red'
    }
    
    for scenario_name, projections in scenarios.items():
        years = [p['year'] for p in projections]
        values = [p['value'] for p in projections]
        
        fig.add_trace(go.Scatter(
            x=years,
            y=values,
            mode='lines+markers',
            name=scenario_name.capitalize(),
            line=dict(color=colors[scenario_name], width=2)
        ))
        
    fig.update_layout(
        title="Évolution du prix selon différents scénarios",
        xaxis_title="Année",
        yaxis_title="Prix (€/kWh)",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tableau comparatif des coûts
    st.markdown("### 💰 Impact financier par scénario")
    
    comparison_data = []
    for scenario_name in ['conservateur', 'modere', 'pessimiste']:
        scenario_data = scenarios[scenario_name]
        
        # Coût cumulé
        cout_cumule = sum(
            p['value'] * conso_ref * 1000 
            for p in scenario_data
        )
        
        # Prix final
        prix_final = scenario_data[-1]['value']
        
        comparison_data.append({
            'Scénario': scenario_name.capitalize(),
            'Prix final': f"{prix_final:.4f} €/kWh",
            'Augmentation': f"+{((prix_final/current_price.prix_kwh-1)*100):.1f}%",
            'Coût cumulé': f"{cout_cumule:,.0f} €",
            'Coût moyen/an': f"{cout_cumule/horizon:,.0f} €"
        })
        
    df_comparison = pd.DataFrame(comparison_data)
    st.dataframe(df_comparison, use_container_width=True, hide_index=True)
    
    # Analyse de sensibilité
    with st.expander("📈 Analyse de sensibilité"):
        st.markdown("**Impact d'une variation de ±1% du taux d'inflation**")
        
        base_rate = inflation_service.PROJECTIONS_DEFAUT[scenario]['electricite']
        
        # Calcul avec +1% et -1%
        proj_plus = inflation_service.project_value(
            initial_value=current_price.prix_kwh,
            years=horizon,
            custom_rates=[base_rate + 1] * horizon
        )
        
        proj_moins = inflation_service.project_value(
            initial_value=current_price.prix_kwh,
            years=horizon,
            custom_rates=[base_rate - 1] * horizon
        )
        
        impact_plus = (proj_plus[-1]['value'] - scenarios['modere'][-1]['value']) / scenarios['modere'][-1]['value'] * 100
        impact_moins = (proj_moins[-1]['value'] - scenarios['modere'][-1]['value']) / scenarios['modere'][-1]['value'] * 100
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Impact de +1% inflation", f"{impact_plus:+.1f}% sur le prix final")
        with col2:
            st.metric("Impact de -1% inflation", f"{impact_moins:+.1f}% sur le prix final")


def render_price_management(client: Client, pricing_service: PricingService):
    """Interface de gestion des prix du client.
    
    Args:
        client: Client sélectionné
        pricing_service: Service prix
    """
    st.subheader("⚡ Gestion des prix")
    
    # Actions disponibles
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ Nouveau prix", type="primary", use_container_width=True):
            st.session_state['create_price'] = True
            
    with col2:
        current_price = pricing_service.get_active_price(client.id)
        if current_price and st.button("✏️ Modifier prix actuel", use_container_width=True):
            st.session_state['edit_price'] = current_price.id
            
    with col3:
        if current_price and st.button("📋 Dupliquer prix", use_container_width=True):
            st.session_state['duplicate_price'] = current_price.id
            
    # Formulaire de création/édition
    if st.session_state.get('create_price') or st.session_state.get('edit_price'):
        render_price_form(client, pricing_service)
        
    # Liste des prix
    st.markdown("### 📜 Historique des prix")
    
    price_history = pricing_service.get_price_history(client.id)
    
    if not price_history:
        st.info("Aucun prix défini pour ce client")
    else:
        for prix in price_history:
            with st.expander(
                f"{'🟢' if prix.is_active() else '⚫'} "
                f"{prix.prix_kwh:.4f} €/kWh - "
                f"{prix.date_debut.strftime('%d/%m/%Y')} → "
                f"{prix.date_fin.strftime('%d/%m/%Y') if prix.date_fin else 'En cours'}"
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Type:** {prix.type_tarif.value.capitalize()}")
                    st.write(f"**Référence:** {prix.reference_prix or 'Aucune'}")
                    st.write(f"**Remise:** {prix.remise_pourcentage}%")
                    
                with col2:
                    st.write(f"**ID:** {prix.id}")
                    st.write(f"**Créé le:** {prix.date_creation.strftime('%d/%m/%Y %H:%M') if prix.date_creation else 'N/A'}")
                    if prix.notes:
                        st.write(f"**Notes:** {prix.notes}")
                        
                # Actions
                col3, col4, col5 = st.columns(3)
                with col3:
                    if st.button("✏️ Modifier", key=f"edit_{prix.id}"):
                        st.session_state['edit_price'] = prix.id
                with col4:
                    if prix.is_active() and not prix.date_fin:
                        if st.button("🛑 Clôturer", key=f"close_{prix.id}"):
                            st.session_state['close_price'] = prix.id
                with col5:
                    if not prix.is_active():
                        if st.button("🗑️ Supprimer", key=f"delete_{prix.id}"):
                            st.session_state['delete_price'] = prix.id


def render_price_form(client: Client, pricing_service: PricingService):
    """Affiche le formulaire de création/édition de prix.
    
    Args:
        client: Client concerné
        pricing_service: Service prix
    """
    is_edit = 'edit_price' in st.session_state
    
    # Récupérer le prix à éditer si applicable
    if is_edit:
        prix_id = st.session_state['edit_price']
        prix_list = pricing_service.get_price_history(client.id)
        current_prix = next((p for p in prix_list if p.id == prix_id), None)
        if not current_prix:
            st.error("Prix introuvable")
            return
    else:
        current_prix = None
        
    st.markdown(f"### {'✏️ Modification' if is_edit else '➕ Nouveau'} prix")
    
    with st.form("price_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            prix_kwh = st.number_input(
                "Prix €/kWh *",
                min_value=0.0001,
                max_value=1.0,
                value=float(current_prix.prix_kwh) if is_edit else 0.2000,
                step=0.0001,
                format="%.4f"
            )
            
            type_tarif = st.selectbox(
                "Type de tarif *",
                options=['fixe', 'indexe', 'dynamique'],
                index=['fixe', 'indexe', 'dynamique'].index(current_prix.type_tarif) if is_edit else 0
            )
            
            remise = st.number_input(
                "Remise %",
                min_value=0.0,
                max_value=100.0,
                value=float(current_prix.remise_pourcentage) if is_edit else 0.0,
                step=0.1
            )
            
        with col2:
            date_debut = st.date_input(
                "Date de début *",
                value=current_prix.date_debut if is_edit else date.today(),
                min_value=date.today() if not is_edit else None
            )
            
            has_end_date = st.checkbox(
                "Date de fin définie",
                value=current_prix.date_fin is not None if is_edit else False
            )
            
            if has_end_date:
                date_fin = st.date_input(
                    "Date de fin",
                    value=current_prix.date_fin if is_edit and current_prix.date_fin else date.today() + timedelta(days=365),
                    min_value=date_debut + timedelta(days=1)
                )
            else:
                date_fin = None
                
            reference_prix = st.selectbox(
                "Prix de référence",
                options=['Aucun'] + list(pricing_service.PRIX_REFERENCES.keys()),
                index=0
            )
            
        # Notes
        notes = st.text_area(
            "Notes",
            value=current_prix.notes if is_edit and current_prix.notes else "",
            height=100
        )
        
        # Boutons
        col1, col2, col3 = st.columns([1, 1, 3])
        
        with col1:
            submit = st.form_submit_button(
                "💾 Enregistrer" if is_edit else "✅ Créer",
                type="primary",
                use_container_width=True
            )
            
        with col2:
            cancel = st.form_submit_button(
                "❌ Annuler",
                use_container_width=True
            )
            
    if submit:
        try:
            prix_data = PrixClient(
                id=current_prix.id if is_edit else None,
                client_id=client.id,
                prix_kwh=prix_kwh,
                date_debut=date_debut,
                date_fin=date_fin,
                type_tarif=type_tarif,
                reference_prix=reference_prix if reference_prix != 'Aucun' else None,
                remise_pourcentage=remise,
                formule_calcul=None,  # TODO: implémenter l'éditeur de formules
                notes=notes if notes else None,
                date_creation=current_prix.date_creation if is_edit else None
            )
            
            if is_edit:
                result = pricing_service.update_prix(prix_data)
                st.success("Prix mis à jour avec succès!")
            else:
                result = pricing_service.create_prix(prix_data)
                st.success("Prix créé avec succès!")
                
            # Nettoyer la session
            if 'create_price' in st.session_state:
                del st.session_state['create_price']
            if 'edit_price' in st.session_state:
                del st.session_state['edit_price']
                
            st.rerun()
            
        except Exception as e:
            st.error(f"Erreur: {str(e)}")
            
    elif cancel:
        # Nettoyer la session
        if 'create_price' in st.session_state:
            del st.session_state['create_price']
        if 'edit_price' in st.session_state:
            del st.session_state['edit_price']
        st.rerun()