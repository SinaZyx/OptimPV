"""
Module pour l'analyse des revenus investisseur
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from ...shared.chart_utilities import (
    apply_theme, format_currency, validate_chart_data,
    COLORS, handle_chart_error
)

def create_annual_revenue_breakdown_chart(results):
    """
    Crée un graphique en barres empilées de la répartition annuelle des revenus.
    """
    try:
        if not validate_chart_data(results, ['monthly_data']):
            return None
            
        monthly_df = results.get('monthly_data')
        if not isinstance(monthly_df, pd.DataFrame) or monthly_df.empty:
            return None
        
        required_cols = ['Revenus_Autoconsommation', 'Revenus_Surplus', 'Prime_Autoconso_Encaissee']
        monthly_df_agg = monthly_df.copy()

        # Vérifier les colonnes requises
        if not all(col in monthly_df_agg.columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in monthly_df_agg.columns]
            st.warning(f"Colonnes manquantes pour la répartition des revenus: {missing_cols}")
            
            # Si Prime_Autoconso_Encaissee manque, on peut continuer sans
            if 'Prime_Autoconso_Encaissee' not in monthly_df_agg.columns:
                monthly_df_agg['Prime_Autoconso_Encaissee'] = 0.0
                required_cols.remove('Prime_Autoconso_Encaissee')
                if not all(col in monthly_df_agg.columns for col in ['Revenus_Autoconsommation', 'Revenus_Surplus']):
                    return None

        if not isinstance(monthly_df_agg.index, pd.DatetimeIndex):
            try: 
                monthly_df_agg.index = pd.to_datetime(monthly_df_agg.index)
            except: 
                return None
        
        annual_revenues = monthly_df_agg[required_cols].resample('YE').sum()
        annual_revenues.index = annual_revenues.index.year

        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=annual_revenues.index, 
            y=annual_revenues['Revenus_Autoconsommation'],
            name='Revenus Autoconsommation', 
            marker_color=COLORS['primary'],
            text=[format_currency(v) for v in annual_revenues['Revenus_Autoconsommation']],
            textposition='inside'
        ))
        
        fig.add_trace(go.Bar(
            x=annual_revenues.index, 
            y=annual_revenues['Revenus_Surplus'],
            name='Revenus Surplus (OA)', 
            marker_color=COLORS['warning'],
            text=[format_currency(v) for v in annual_revenues['Revenus_Surplus']],
            textposition='inside'
        ))
        
        if 'Prime_Autoconso_Encaissee' in annual_revenues.columns and annual_revenues['Prime_Autoconso_Encaissee'].sum() > 0:
            fig.add_trace(go.Bar(
                x=annual_revenues.index, 
                y=annual_revenues['Prime_Autoconso_Encaissee'],
                name='Prime Autoconsommation', 
                marker_color=COLORS['success'],
                text=[format_currency(v) for v in annual_revenues['Prime_Autoconso_Encaissee']],
                textposition='inside'
            ))
            
        fig.update_layout(
            barmode='stack', 
            title="Répartition Annuelle des Revenus",
            xaxis_title="Année", 
            yaxis_title="Revenus Annuels (€)",
            legend_title="Source de Revenus", 
            yaxis_tickformat=",.0f",
            height=500
        )
        
        return apply_theme(fig)
        
    except Exception as e:
        return handle_chart_error(e, "Répartition Revenus")