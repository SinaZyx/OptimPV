"""
Dashboard synthétique pour les investisseurs
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ...shared.chart_utilities import (
    apply_theme, format_currency, format_percentage, format_number,
    create_metric_card, validate_chart_data, COLORS
)
from ..financial import create_financial_indicators_chart, create_waterfall_cashflow_chart
from ..risk import create_monte_carlo_results_chart

def display_investor_dashboard(results_data, config, mc_results=None):
    """
    Affiche le dashboard synthétique investisseur avec KPIs financiers et alertes
    """
    if not results_data:
        st.warning("Aucune donnée disponible pour le dashboard investisseur.")
        return
    
    # Section KPIs financiers principaux
    st.markdown("### 💼 Tableau de Bord Investisseur")
    
    # Ligne de KPIs principaux
    col1, col2, col3, col4 = st.columns(4)
    
    # KPI 1: VAN (NPV)
    npv = results_data.get('npv', 0)
    npv_color = "normal" if npv > 0 else "inverse"
    
    with col1:
        st.metric(
            label="VAN du Projet",
            value=format_currency(npv),
            delta="Rentable" if npv > 0 else "Non rentable",
            delta_color=npv_color
        )
    
    # KPI 2: TRI (IRR)
    irr = results_data.get('irr', 0) * 100
    target_irr = config.get('cout_fonds_propres', 8.0)
    irr_delta = irr - target_irr
    
    with col2:
        st.metric(
            label="TRI du Projet",
            value=f"{irr:.1f}%",
            delta=f"{irr_delta:+.1f}% vs cible",
            delta_color="normal" if irr > target_irr else "inverse"
        )
    
    # KPI 3: LCOE
    lcoe = results_data.get('lcoe', 0)
    prix_vente = results_data.get('prix_revente', 0)
    
    with col3:
        st.metric(
            label="LCOE",
            value=f"{lcoe:.3f} €/kWh",
            delta=f"{((prix_vente - lcoe) / lcoe * 100):.1f}% marge" if lcoe > 0 else "N/A",
            delta_color="normal" if prix_vente > lcoe else "inverse"
        )
    
    # KPI 4: Payback
    payback = results_data.get('payback_period', 0)
    payback_target = config.get('payback_max_years', 10)
    
    with col4:
        st.metric(
            label="Payback",
            value=f"{payback:.1f} ans",
            delta="OK" if payback < payback_target else "Élevé",
            delta_color="normal" if payback < payback_target else "inverse"
        )
    
    # Section santé financière
    st.markdown("### 🏥 Santé Financière")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Graphique gauge DSCR
        fig_dscr = create_dscr_gauge(results_data, config)
        if fig_dscr:
            st.plotly_chart(fig_dscr, use_container_width=True)
    
    with col2:
        # Alertes et statuts
        display_financial_alerts(results_data, config)
    
    # Section graphiques financiers
    st.markdown("### 📊 Analyse Financière")
    
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Cash-flow", "📈 Revenus", "⚡ Risques", "🎯 Synthèse"])
    
    with tab1:
        # Mini waterfall année en cours
        current_year = pd.Timestamp.now().year
        if 'monthly_data' in results_data:
            monthly_data = results_data['monthly_data']
            if isinstance(monthly_data, pd.DataFrame) and isinstance(monthly_data.index, pd.DatetimeIndex):
                years_available = monthly_data.index.year.unique()
                if current_year in years_available:
                    year_idx = list(years_available).index(current_year)
                else:
                    year_idx = min(4, len(years_available) - 1)
                    
                fig_waterfall = create_waterfall_cashflow_chart(results_data, year_idx)
                if fig_waterfall:
                    fig_waterfall.update_layout(height=400)
                    st.plotly_chart(fig_waterfall, use_container_width=True)
    
    with tab2:
        # Revenus cumulés et projection
        fig_revenue = create_revenue_projection_chart(results_data)
        if fig_revenue:
            st.plotly_chart(fig_revenue, use_container_width=True)
    
    with tab3:
        # Résultats Monte Carlo si disponibles
        if mc_results:
            col1, col2 = st.columns(2)
            with col1:
                # Probabilités de succès
                display_success_probabilities(mc_results)
            with col2:
                # Mini graphique MC
                fig_mc_mini = create_mc_mini_chart(mc_results)
                if fig_mc_mini:
                    st.plotly_chart(fig_mc_mini, use_container_width=True)
        else:
            st.info("Aucune analyse Monte Carlo disponible. Lancez une simulation pour voir les risques.")
    
    with tab4:
        # Vue synthétique exécutive
        create_executive_summary(results_data, config)
    
    # Section actions
    st.markdown("### 🚀 Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Rapport Détaillé", key="investor_detailed"):
            st.session_state.view_mode = "detailed"
            st.rerun()
            
    with col2:
        if st.button("📄 Export PDF", key="investor_pdf"):
            st.info("Génération du rapport investisseur...")
            # TODO: Implémenter export PDF
            
    with col3:
        if st.button("📈 Analyse Sensibilité", key="investor_sensitivity"):
            st.session_state.show_sensitivity = True
            st.rerun()
            
    with col4:
        if st.button("🎲 Simulation MC", key="investor_mc"):
            st.session_state.run_monte_carlo = True
            st.rerun()

def create_dscr_gauge(results_data, config):
    """
    Crée un graphique gauge pour le DSCR moyen
    """
    try:
        avg_dscr = results_data.get('avg_dscr', 0)
        target_dscr = config.get('target_dscr', 1.2)
        
        # Définir les zones de couleur
        if avg_dscr < 1.0:
            bar_color = COLORS['danger']
            status = "Critique"
        elif avg_dscr < target_dscr:
            bar_color = COLORS['warning']
            status = "Attention"
        else:
            bar_color = COLORS['success']
            status = "Sain"
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=avg_dscr,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "DSCR Moyen"},
            delta={'reference': target_dscr, 'position': "bottom"},
            gauge={
                'axis': {'range': [None, 2.5]},
                'bar': {'color': bar_color},
                'steps': [
                    {'range': [0, 1.0], 'color': "rgba(255,0,0,0.2)"},
                    {'range': [1.0, target_dscr], 'color': "rgba(255,165,0,0.2)"},
                    {'range': [target_dscr, 2.5], 'color': "rgba(0,255,0,0.2)"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': target_dscr
                }
            }
        ))
        
        fig.add_annotation(
            text=f"<b>{status}</b>",
            x=0.5, y=0.3,
            showarrow=False,
            font=dict(size=20, color=bar_color)
        )
        
        fig.update_layout(height=300)
        
        return apply_theme(fig)
        
    except Exception:
        return None

def display_financial_alerts(results_data, config):
    """
    Affiche les alertes financières
    """
    alerts = []
    
    # Vérification NPV
    npv = results_data.get('npv', 0)
    if npv < 0:
        alerts.append(("🔴", "VAN négative", "danger"))
    
    # Vérification IRR
    irr = results_data.get('irr', 0) * 100
    target_irr = config.get('cout_fonds_propres', 8.0)
    if irr < target_irr:
        alerts.append(("🟠", f"TRI < cible ({irr:.1f}% < {target_irr}%)", "warning"))
    
    # Vérification DSCR
    avg_dscr = results_data.get('avg_dscr', 0)
    if avg_dscr < 1.0:
        alerts.append(("🔴", f"DSCR critique ({avg_dscr:.2f})", "danger"))
    elif avg_dscr < config.get('target_dscr', 1.2):
        alerts.append(("🟡", f"DSCR faible ({avg_dscr:.2f})", "warning"))
    
    # Vérification Payback
    payback = results_data.get('payback_period', 0)
    if payback > config.get('payback_max_years', 10):
        alerts.append(("🟠", f"Payback élevé ({payback:.1f} ans)", "warning"))
    
    if not alerts:
        st.success("✅ Tous les indicateurs sont dans les cibles")
    else:
        for icon, message, level in alerts:
            if level == "danger":
                st.error(f"{icon} {message}")
            elif level == "warning":
                st.warning(f"{icon} {message}")
            else:
                st.info(f"{icon} {message}")

def create_revenue_projection_chart(results_data):
    """
    Crée un graphique de projection des revenus
    """
    try:
        if 'monthly_data' not in results_data:
            return None
            
        monthly_data = results_data['monthly_data']
        if not isinstance(monthly_data, pd.DataFrame):
            return None
            
        # Agrégation annuelle
        annual_data = monthly_data.resample('YE').sum()
        
        if 'Revenus_Total' in annual_data.columns:
            revenues = annual_data['Revenus_Total']
            cumulative_revenues = revenues.cumsum()
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Revenus annuels
            fig.add_trace(
                go.Bar(
                    x=annual_data.index.year,
                    y=revenues,
                    name="Revenus Annuels",
                    marker_color=COLORS['primary'],
                    text=[format_currency(v) for v in revenues],
                    textposition='outside'
                ),
                secondary_y=False
            )
            
            # Revenus cumulés
            fig.add_trace(
                go.Scatter(
                    x=annual_data.index.year,
                    y=cumulative_revenues,
                    name="Revenus Cumulés",
                    line=dict(color=COLORS['success'], width=3),
                    mode='lines+markers'
                ),
                secondary_y=True
            )
            
            fig.update_layout(
                title="Projection des Revenus",
                height=400,
                hovermode='x unified'
            )
            fig.update_xaxes(title_text="Année")
            fig.update_yaxes(title_text="Revenus Annuels (€)", secondary_y=False)
            fig.update_yaxes(title_text="Revenus Cumulés (€)", secondary_y=True)
            
            return apply_theme(fig)
            
    except Exception:
        return None

def display_success_probabilities(mc_results):
    """
    Affiche les probabilités de succès des critères
    """
    if 'probabilities' not in mc_results:
        return
        
    probs = mc_results['probabilities']
    
    st.markdown("#### Probabilités de Succès")
    
    metrics = [
        ('VAN > 0', probs.get('npv_positive', 0)),
        ('TRI > Cible', probs.get('irr_above_target', 0)),
        ('Payback < Max', probs.get('payback_below_max', 0)),
        ('DSCR > Min', probs.get('dscr_above_min', 0))
    ]
    
    for label, prob in metrics:
        color = COLORS['success'] if prob > 0.8 else (COLORS['warning'] if prob > 0.6 else COLORS['danger'])
        st.markdown(f"""
        <div style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between;">
                <span>{label}</span>
                <span style="color: {color}; font-weight: bold;">{prob*100:.1f}%</span>
            </div>
            <div style="background: #f0f0f0; height: 10px; border-radius: 5px; overflow: hidden;">
                <div style="background: {color}; width: {prob*100}%; height: 100%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def create_mc_mini_chart(mc_results):
    """
    Crée un mini graphique Monte Carlo pour le dashboard
    """
    try:
        if 'results' not in mc_results or 'statistics' not in mc_results:
            return None
            
        stats = mc_results['statistics']
        
        # Créer un graphique radar des moyennes normalisées
        categories = ['VAN', 'TRI', 'DSCR', 'Payback']
        
        # Normaliser les valeurs pour le radar (0-1)
        values = []
        
        # VAN: normalisé par rapport à un seuil positif
        npv_mean = stats.get('npv', {}).get('mean', 0)
        npv_norm = min(1, max(0, (npv_mean + 100000) / 200000))  # Échelle -100k à +100k
        values.append(npv_norm)
        
        # TRI: normalisé 0-20%
        irr_mean = stats.get('irr', {}).get('mean', 0) * 100
        irr_norm = min(1, max(0, irr_mean / 20))
        values.append(irr_norm)
        
        # DSCR: normalisé 0-2.5
        dscr_mean = stats.get('avg_dscr', {}).get('mean', 0)
        dscr_norm = min(1, max(0, dscr_mean / 2.5))
        values.append(dscr_norm)
        
        # Payback: inversé et normalisé 0-20 ans
        payback_mean = stats.get('payback_period', {}).get('mean', 20)
        payback_norm = min(1, max(0, (20 - payback_mean) / 20))
        values.append(payback_norm)
        
        fig = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            fillcolor='rgba(31, 119, 180, 0.3)',
            line=dict(color=COLORS['primary'])
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            title="Performance Globale (MC)",
            height=300,
            showlegend=False
        )
        
        return apply_theme(fig)
        
    except Exception:
        return None

def create_executive_summary(results_data, config):
    """
    Crée un résumé exécutif visuel
    """
    # Calculs clés
    npv = results_data.get('npv', 0)
    irr = results_data.get('irr', 0) * 100
    payback = results_data.get('payback_period', 0)
    lcoe = results_data.get('lcoe', 0)
    
    # Investissement et financement
    capex = config.get('cout_initial_par_kwc', 1000) * config.get('puissance_installee_kwc', 100)
    dette_ratio = config.get('ratio_dette', 0.8)
    equity = capex * (1 - dette_ratio)
    debt = capex * dette_ratio
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 10px; color: white;">
        <h3 style="text-align: center; margin-bottom: 2rem;">Synthèse Exécutive</h3>
        
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem;">
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;">
                <h4>Investissement</h4>
                <div style="font-size: 1.5rem; font-weight: bold;">{capex}</div>
                <div style="font-size: 0.9rem; opacity: 0.8;">
                    Fonds propres: {equity}<br>
                    Dette: {debt}
                </div>
            </div>
            
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;">
                <h4>Rentabilité</h4>
                <div style="font-size: 1.5rem; font-weight: bold;">TRI: {irr:.1f}%</div>
                <div style="font-size: 0.9rem; opacity: 0.8;">
                    VAN: {npv}<br>
                    Payback: {payback:.1f} ans
                </div>
            </div>
        </div>
        
        <div style="margin-top: 1.5rem; text-align: center; padding: 1rem; 
                    background: rgba(255,255,255,0.2); border-radius: 8px;">
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">
                Coût de Production: <strong>{lcoe:.3f} €/kWh</strong>
            </div>
            <div style="font-size: 0.9rem; opacity: 0.9;">
                Prix de Vente: {prix_vente:.3f} €/kWh 
                ({marge:.1f}% de marge)
            </div>
        </div>
    </div>
    """.format(
        capex=format_currency(capex),
        equity=format_currency(equity),
        debt=format_currency(debt),
        irr=irr,
        npv=format_currency(npv),
        payback=payback,
        lcoe=lcoe,
        prix_vente=results_data.get('prix_revente', 0),
        marge=((results_data.get('prix_revente', 0) - lcoe) / lcoe * 100) if lcoe > 0 else 0
    ), unsafe_allow_html=True)