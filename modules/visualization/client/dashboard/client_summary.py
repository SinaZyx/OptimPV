"""
Dashboard synthétique pour les clients
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ...shared.chart_utilities import (
    apply_theme, format_currency, format_percentage, format_number,
    create_metric_card, validate_chart_data, COLORS
)
from ..economics import create_price_comparison_chart, create_annual_savings_chart
from ..energy import create_energy_distribution_pie

def display_client_dashboard(results_data, config):
    """
    Affiche le dashboard synthétique client avec KPIs et graphiques mini
    """
    if not results_data:
        st.warning("Aucune donnée disponible pour le dashboard client.")
        return
    
    # Section KPIs principaux
    st.markdown("### 📊 Tableau de Bord Client")
    
    # Ligne de KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    # KPI 1: Prix optimal
    prix_optimal = results_data.get('prix_revente', 0)
    tarif_edf = config.get('tarif_edf_reference', 0.21)
    economie_pct = ((tarif_edf - prix_optimal) / tarif_edf * 100) if tarif_edf > 0 else 0
    
    with col1:
        st.metric(
            label="Prix Optimal",
            value=f"{prix_optimal:.4f} €/kWh",
            delta=f"-{economie_pct:.1f}% vs EDF",
            delta_color="normal"
        )
    
    # KPI 2: Économie annuelle
    if 'monthly_data' in results_data:
        monthly_data = results_data['monthly_data']
        if isinstance(monthly_data, pd.DataFrame) and 'Autoconsommation_kWh' in monthly_data.columns:
            autoconso_annuelle = monthly_data['Autoconsommation_kWh'].sum()
            economie_annuelle = (tarif_edf - prix_optimal) * autoconso_annuelle
        else:
            economie_annuelle = 0
    else:
        economie_annuelle = 0
    
    with col2:
        st.metric(
            label="Économie Annuelle",
            value=format_currency(economie_annuelle),
            delta=f"{economie_pct:.1f}%",
            delta_color="normal"
        )
    
    # KPI 3: Taux d'autoconsommation
    taux_autoconso = results_data.get('taux_autoconsommation', 0) * 100
    
    with col3:
        st.metric(
            label="Taux d'Autoconsommation",
            value=f"{taux_autoconso:.1f}%",
            delta="Optimal" if taux_autoconso > 30 else "À améliorer",
            delta_color="normal" if taux_autoconso > 30 else "inverse"
        )
    
    # KPI 4: Économies cumulées sur 10 ans
    economie_10ans = economie_annuelle * 10 * 1.02**5  # Approximation avec inflation
    
    with col4:
        st.metric(
            label="Économies sur 10 ans",
            value=format_currency(economie_10ans),
            delta="Estimé avec inflation",
            delta_color="off"
        )
    
    # Section graphiques miniatures
    st.markdown("### 📈 Vue d'Ensemble")
    
    # Utiliser des tabs pour organiser
    tab1, tab2, tab3 = st.tabs(["💰 Économies", "⚡ Énergie", "📊 Comparaisons"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            # Mini graphique économies annuelles
            fig_savings = create_annual_savings_summary(results_data, config)
            if fig_savings:
                st.plotly_chart(fig_savings, use_container_width=True)
                
        with col2:
            # Projection économies
            fig_projection = create_savings_projection_sparkline(results_data, config)
            if fig_projection:
                st.plotly_chart(fig_projection, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            # Distribution énergie
            fig_energy = create_energy_distribution_pie(results_data)
            if fig_energy:
                fig_energy.update_layout(height=350)
                st.plotly_chart(fig_energy, use_container_width=True)
                
        with col2:
            # Pattern journalier simplifié
            fig_pattern = create_daily_pattern_summary(results_data)
            if fig_pattern:
                st.plotly_chart(fig_pattern, use_container_width=True)
    
    with tab3:
        # Comparaison prix
        fig_comparison = create_price_comparison_chart(results_data, config)
        if fig_comparison:
            fig_comparison.update_layout(height=350)
            st.plotly_chart(fig_comparison, use_container_width=True)
    
    # Section "En un coup d'œil"
    st.markdown("### 🎯 Économies en un Coup d'Œil")
    
    # Créer un résumé visuel attractif
    create_visual_summary(results_data, config)
    
    # Boutons d'action
    st.markdown("### 🚀 Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Générer Rapport PDF", key="client_pdf"):
            st.info("Génération du rapport PDF en cours...")
            # TODO: Implémenter la génération PDF
            
    with col2:
        if st.button("📧 Envoyer par Email", key="client_email"):
            st.info("Préparation de l'email...")
            # TODO: Implémenter l'envoi email
            
    with col3:
        if st.button("📊 Voir Détails", key="client_details"):
            st.session_state.view_mode = "detailed"
            st.rerun()

def create_annual_savings_summary(results_data, config):
    """
    Crée un graphique résumé des économies annuelles
    """
    try:
        if not validate_chart_data(results_data, ['monthly_data']):
            return None
            
        monthly_data = results_data['monthly_data']
        prix_optimal = results_data.get('prix_revente', 0)
        tarif_edf = config.get('tarif_edf_reference', 0.21)
        
        # Calculs mensuels
        if 'Autoconsommation_kWh' in monthly_data.columns:
            monthly_savings = monthly_data['Autoconsommation_kWh'] * (tarif_edf - prix_optimal)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=monthly_savings.index.strftime('%b'),
                y=monthly_savings.values,
                marker_color=COLORS['success'],
                text=[format_currency(v) for v in monthly_savings.values],
                textposition='outside'
            ))
            
            fig.update_layout(
                title="Économies Mensuelles",
                yaxis_title="Économies (€)",
                height=350,
                showlegend=False
            )
            
            return apply_theme(fig)
            
    except Exception:
        return None

def create_savings_projection_sparkline(results_data, config):
    """
    Crée un sparkline de projection des économies
    """
    try:
        economie_annuelle = 0
        if 'monthly_data' in results_data:
            monthly_data = results_data['monthly_data']
            prix_optimal = results_data.get('prix_revente', 0)
            tarif_edf = config.get('tarif_edf_reference', 0.21)
            
            if 'Autoconsommation_kWh' in monthly_data.columns:
                autoconso_annuelle = monthly_data['Autoconsommation_kWh'].sum()
                economie_annuelle = (tarif_edf - prix_optimal) * autoconso_annuelle
        
        if economie_annuelle > 0:
            # Projection sur 20 ans avec inflation
            years = list(range(1, 21))
            inflation = config.get('taux_inflation', 2.0) / 100
            projections = [economie_annuelle * (1 + inflation)**i for i in range(20)]
            cumulative = pd.Series(projections).cumsum()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=years,
                y=cumulative,
                mode='lines+markers',
                line=dict(color=COLORS['primary'], width=3),
                fill='tozeroy',
                fillcolor='rgba(31, 119, 180, 0.2)',
                marker=dict(size=6)
            ))
            
            # Annotations pour jalons
            for year in [5, 10, 20]:
                if year <= len(years):
                    fig.add_annotation(
                        x=year,
                        y=cumulative.iloc[year-1],
                        text=format_currency(cumulative.iloc[year-1]),
                        showarrow=False,
                        yshift=10
                    )
            
            fig.update_layout(
                title="Projection Économies Cumulées",
                xaxis_title="Années",
                yaxis_title="Économies Cumulées (€)",
                height=350,
                showlegend=False
            )
            
            return apply_theme(fig)
            
    except Exception:
        return None

def create_daily_pattern_summary(results_data):
    """
    Crée un graphique simplifié du pattern journalier
    """
    try:
        if 'hourly_aggregated_data' not in results_data:
            return None
            
        df_hourly = results_data['hourly_aggregated_data']
        if not isinstance(df_hourly, pd.DataFrame) or df_hourly.empty:
            return None
            
        df = df_hourly.copy()
        if not isinstance(df.index, pd.DatetimeIndex):
            return None
            
        df['hour'] = df.index.hour
        
        # Moyennes par heure
        hourly_avg = df.groupby('hour')[['production_kwh', 'consumption_kwh']].mean()
        
        fig = go.Figure()
        
        # Zone de production
        fig.add_trace(go.Scatter(
            x=hourly_avg.index,
            y=hourly_avg['production_kwh'],
            mode='lines',
            name='Production',
            line=dict(color='gold', width=3),
            fill='tozeroy',
            fillcolor='rgba(255, 215, 0, 0.3)'
        ))
        
        # Ligne de consommation
        fig.add_trace(go.Scatter(
            x=hourly_avg.index,
            y=hourly_avg['consumption_kwh'],
            mode='lines',
            name='Consommation',
            line=dict(color=COLORS['primary'], width=3)
        ))
        
        fig.update_layout(
            title="Profil Énergétique Moyen",
            xaxis_title="Heure",
            yaxis_title="kWh",
            height=350,
            xaxis=dict(
                tickmode='array',
                tickvals=[0, 6, 12, 18, 23],
                ticktext=['00h', '06h', '12h', '18h', '23h']
            ),
            legend=dict(orientation="h", y=1.1)
        )
        
        return apply_theme(fig)
        
    except Exception:
        return None

def create_visual_summary(results_data, config):
    """
    Crée un résumé visuel attractif des économies
    """
    # Calculs
    prix_optimal = results_data.get('prix_revente', 0)
    tarif_edf = config.get('tarif_edf_reference', 0.21)
    economie_unitaire = tarif_edf - prix_optimal
    
    if 'monthly_data' in results_data:
        monthly_data = results_data['monthly_data']
        if 'Autoconsommation_kWh' in monthly_data.columns:
            autoconso_annuelle = monthly_data['Autoconsommation_kWh'].sum()
            economie_annuelle = economie_unitaire * autoconso_annuelle
        else:
            autoconso_annuelle = 0
            economie_annuelle = 0
    else:
        autoconso_annuelle = 0
        economie_annuelle = 0
    
    # Affichage en colonnes
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Carte visuelle
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                    padding: 2rem; border-radius: 10px; text-align: center;">
            <h2 style="color: #2c3e50; margin-bottom: 1rem;">Votre Économie</h2>
            <div style="font-size: 3rem; color: #27ae60; font-weight: bold;">
                {format_currency(economie_annuelle)}
            </div>
            <div style="color: #7f8c8d; margin-top: 0.5rem;">par an</div>
            <hr style="margin: 1.5rem 0; opacity: 0.3;">
            <div style="display: flex; justify-content: space-around; text-align: center;">
                <div>
                    <div style="font-size: 1.5rem; color: #3498db;">{format_number(autoconso_annuelle)} kWh</div>
                    <div style="color: #7f8c8d; font-size: 0.9rem;">Autoconsommés/an</div>
                </div>
                <div>
                    <div style="font-size: 1.5rem; color: #e74c3c;">{economie_unitaire:.3f} €/kWh</div>
                    <div style="color: #7f8c8d; font-size: 0.9rem;">Économie unitaire</div>
                </div>
            </div>
            <div style="margin-top: 1.5rem; padding: 1rem; background: rgba(52, 152, 219, 0.1); 
                        border-radius: 5px;">
                <strong>Sur 20 ans :</strong> {format_currency(economie_annuelle * 20 * 1.02**10)}
                <div style="font-size: 0.8rem; color: #7f8c8d;">(avec inflation 2%/an)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)