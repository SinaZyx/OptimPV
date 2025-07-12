"""
Module pour l'analyse des économies client
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ...shared.chart_utilities import (
    apply_theme, format_currency, format_percentage, validate_chart_data,
    COLORS, handle_chart_error
)

def create_annual_savings_chart(results_data, config):
    """
    Calcule et affiche l'économie annuelle estimée pour le client.
    """
    try:
        if not validate_chart_data(results_data, ['monthly_data', 'prix_revente']):
            return None
        
        monthly_data = results_data.get('monthly_data')
        if not isinstance(monthly_data, pd.DataFrame) or monthly_data.empty:
            return None
        
        prix_optimal = results_data.get('prix_revente', 0)
        tarif_edf = config.get('tarif_edf_reference', 0.21)
        
        if 'Autoconsommation_kWh' in monthly_data.columns:
            autoconsommation_annuelle = monthly_data['Autoconsommation_kWh'].sum()
        else:
            return None
        
        economie_kwh = tarif_edf - prix_optimal
        economie_annuelle = economie_kwh * autoconsommation_annuelle
        economie_pct = (economie_kwh / tarif_edf) * 100 if tarif_edf > 0 else 0
        
        fig = go.Figure()
        
        fig.add_trace(go.Indicator(
            mode="number+gauge+delta", 
            value=economie_annuelle,
            number={"prefix": "", "suffix": " €", "valueformat": ",.2f"},
            title={"text": "Économie Annuelle (€)"},
            gauge={
                "axis": {"range": [0, economie_annuelle * 1.5 if economie_annuelle > 0 else 100]},
                "bar": {"color": COLORS['success']},
                "steps": [{"range": [0, economie_annuelle], "color": "#e8f5e9"}]
            },
            domain={"row": 0, "column": 0}
        ))
        
        fig.add_trace(go.Indicator(
            mode="number+gauge+delta", 
            value=economie_pct,
            number={"suffix": " %", "valueformat": ".1f"},
            title={"text": "Économie (%)"},
            gauge={
                "axis": {"range": [0, 100]}, 
                "bar": {"color": COLORS['success']},
                "steps": [{"range": [0, economie_pct], "color": "#e8f5e9"}]
            },
            domain={"row": 0, "column": 1}
        ))
        
        fig.update_layout(
            grid={"rows": 1, "columns": 2, "pattern": "independent"},
            title="Économies pour le Client", 
            height=250
        )
        
        return apply_theme(fig)
        
    except Exception as e:
        return handle_chart_error(e, "Économies Annuelles")

def create_cumulative_savings_chart(results_data, config):
    """
    Crée un graphique montrant les économies cumulées sur plusieurs années.
    """
    try:
        if not validate_chart_data(results_data, ['monthly_data']):
            return None
        
        monthly_data_df = results_data.get('monthly_data')
        if not isinstance(monthly_data_df, pd.DataFrame) or monthly_data_df.empty:
            return None

        monthly_data = monthly_data_df.copy()
        
        prix_vente_scenario = results_data.get('prix_revente') 
        if prix_vente_scenario is None:
            prix_vente_scenario = config.get('prix_vente_initial', 0.15) 
                
        tarif_edf = config.get('tarif_edf_reference', 0.21)
        taux_inflation = config.get('taux_inflation', 2.0) / 100
        
        # Gestion des colonnes alternatives
        autoconso_col = None
        if 'Autoconsommation_kWh' in monthly_data.columns:
            autoconso_col = 'Autoconsommation_kWh'
        else:
            alt_cols = ['autoconsumption_kwh', 'autoconsommation_kwh']
            for alt in alt_cols:
                if alt in monthly_data.columns:
                    monthly_data.rename(columns={alt: 'Autoconsommation_kWh'}, inplace=True)
                    autoconso_col = 'Autoconsommation_kWh'
                    break
            else:
                st.warning("Colonne d'autoconsommation non trouvée pour économies cumulées.")
                return None
        
        # Conversion index en datetime si nécessaire
        if not isinstance(monthly_data.index, pd.DatetimeIndex):
            try:
                monthly_data.index = pd.to_datetime(monthly_data.index)
            except Exception:
                st.error("Index non Datetime pour économies cumulées.")
                return None
                
        autoconsommation_par_an = monthly_data[autoconso_col].resample('YE').sum()
        autoconsommation_annuelle_ref = autoconsommation_par_an.mean() if not autoconsommation_par_an.empty else 0
        
        if autoconsommation_annuelle_ref <= 0:
            st.warning("Volume d'autoconsommation annuel moyen nul ou négatif pour économies cumulées.")
            return None

        duree_projet = config.get('duree_ppa', 240) // 12
        if duree_projet <= 0: 
            duree_projet = 20
        
        annees = list(range(1, duree_projet + 1))
        economies_annuelles = []
        
        for i in range(duree_projet):
            tarif_edf_annee = tarif_edf * (1 + taux_inflation) ** i
            prix_vente_annee = prix_vente_scenario * (1 + taux_inflation) ** i
            economie_kwh_annee = tarif_edf_annee - prix_vente_annee
            economie_annuelle = economie_kwh_annee * autoconsommation_annuelle_ref 
            economies_annuelles.append(economie_annuelle)
        
        economies_cumulees_liste = np.cumsum(economies_annuelles)
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(
                x=annees, 
                y=economies_annuelles, 
                name="Économie Annuelle",
                marker_color='rgba(44, 160, 44, 0.7)',
                hovertemplate="Année %{x}<br>Économie: %{y:,.0f} €"
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=annees, 
                y=economies_cumulees_liste, 
                name="Économies Cumulées",
                line=dict(color=COLORS['danger'], width=3), 
                mode='lines+markers',
                marker=dict(size=6),
                hovertemplate="Année %{x}<br>Économies Cumulées: %{y:,.0f} €"
            ),
            secondary_y=True
        )
        
        total_savings = 0
        if economies_cumulees_liste.size > 0:
            total_savings = economies_cumulees_liste[-1]
            fig.add_annotation(
                x=duree_projet, y=total_savings, ax=40, ay=-40,
                text=f"Total sur {duree_projet} ans:<br><b>{format_currency(total_savings)}</b>",
                showarrow=True, arrowhead=1, arrowsize=1, arrowwidth=1.5, 
                arrowcolor=COLORS['danger'],
                font=dict(size=11, color=COLORS['danger']), 
                bordercolor=COLORS['danger'],
                borderwidth=1, bgcolor="rgba(255,255,255,0.7)", align="left",
                secondary_y="y2"
            )
            
        # Milestones
        milestones = [5, 10, 15]
        for milestone in milestones:
            if 0 < milestone <= len(economies_cumulees_liste):
                milestone_idx = milestone - 1
                fig.add_annotation(
                    x=milestone, 
                    y=economies_cumulees_liste[milestone_idx],
                    text=format_currency(economies_cumulees_liste[milestone_idx]),
                    showarrow=False, yshift=10, 
                    font=dict(size=10, color=COLORS['danger']),
                    secondary_y="y2"
                )
                
        fig.update_layout(
            title="Évolution des Économies Estimées sur la Durée du Projet",
            barmode='group',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=500, 
            hovermode="x unified"
        )
        
        fig.update_xaxes(
            title_text="Année", 
            dtick=1 if duree_projet <= 10 else (2 if duree_projet <= 20 else 5)
        )
        fig.update_yaxes(title_text="Économie Annuelle (€)", secondary_y=False, tickformat=",.0f")
        fig.update_yaxes(
            title_text="Économies Cumulées (€)", 
            secondary_y=True, 
            tickformat=",.0f", 
            range=[0, total_savings * 1.1 if economies_cumulees_liste.size > 0 and total_savings > 0 else None]
        )
        
        return apply_theme(fig)
        
    except Exception as e:
        return handle_chart_error(e, "Économies Cumulées")