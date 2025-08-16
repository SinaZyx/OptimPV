"""
Module pour l'analyse des flux de trésorerie investisseur
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from ...shared.chart_utilities import (
    apply_theme, format_currency, validate_chart_data,
    COLORS, handle_chart_error
)

def create_waterfall_cashflow_chart(results, year_index=4):
    """
    Crée un graphique en cascade pour une année spécifique.
    """
    try:
        if not validate_chart_data(results, ['monthly_data']):
            return None
            
        monthly_df = results.get('monthly_data')
        if not isinstance(monthly_df, pd.DataFrame) or monthly_df.empty:
            return None
        
        df_agg = monthly_df.copy()
        if not isinstance(df_agg.index, pd.DatetimeIndex):
            try: 
                df_agg.index = pd.to_datetime(df_agg.index)
            except: 
                return None
    
        annual_data = df_agg.resample('Y').sum()
        years = annual_data.index.year.tolist()
        if not years:
            return None
            
        year_index = min(year_index, len(years) - 1)  # S'assurer que l'index est valide
        
        year_data = annual_data.iloc[year_index]
        selected_year = years[year_index]
        
        annual_tax_payment = year_data.get('Tax_Payment', 0.0)

        components = []
        values = []
        
        if 'Revenus_Autoconsommation' in year_data:
            components.append("Revenus Autoconsommation")
            values.append(year_data['Revenus_Autoconsommation'])
        if 'Revenus_Surplus' in year_data:
            components.append("Revenus Surplus")
            values.append(year_data['Revenus_Surplus'])
        if 'OPEX' in year_data:
            components.append("OPEX")
            values.append(-year_data['OPEX'])
        if 'Service_Dette' in year_data and abs(year_data['Service_Dette']) > 1e-6:
            components.append("Service de la Dette")
            values.append(-year_data['Service_Dette'])
        
        components.append("Impôts Payés")
        values.append(-annual_tax_payment) 
        
        components.append("Cash-flow Net Annuel")
            
        fig = go.Figure(go.Waterfall(
            name=f"Cascade Cash-flow Année {selected_year}", 
            orientation="v",
            measure=["relative"] * (len(components) - 1) + ["total"],
            x=components, 
            textposition="outside",
            text=[format_currency(v) for v in values[:-1]] + [""],
            y=values, 
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": COLORS['danger']}},
            increasing={"marker": {"color": COLORS['success']}},
            totals={"marker": {"color": COLORS['primary']}}
        ))
        
        fig.update_layout(
            title=f"Cascade du Cash-flow - Année {selected_year}",
            showlegend=False, 
            height=500,
            xaxis_title="Composantes du Cash-flow Annuel", 
            yaxis_title="Montant (€)",
            yaxis=dict(tickformat=",.0f €")
        )
        
        return apply_theme(fig)
        
    except Exception as e:
        return handle_chart_error(e, "Cascade Cash-flow")

def create_debt_balance_chart(results):
    """
    Crée un graphique de l'évolution du solde de la dette.
    """
    try:
        if not validate_chart_data(results, ['monthly_data']):
            return None
            
        monthly_df = results.get('monthly_data')
        if not isinstance(monthly_df, pd.DataFrame) or monthly_df.empty or 'Solde_Dette_Fin_Mois' not in monthly_df.columns:
            return None

        df_chart = monthly_df.copy()
        if not isinstance(df_chart.index, pd.DatetimeIndex):
            if 'Temps' in df_chart.columns:
                try: 
                    df_chart.index = pd.to_datetime(df_chart['Temps'])
                except: 
                    return None
            else:
                try: 
                    df_chart.index = pd.to_datetime(df_chart.index)
                except: 
                    return None

        fig = px.line(
            df_chart, 
            y='Solde_Dette_Fin_Mois',
            title="Évolution du Solde de la Dette Restante",
            labels={'index': 'Date', 'Solde_Dette_Fin_Mois': 'Solde Restant Dû (€)'}
        )
        
        fig.update_traces(line_color=COLORS['danger'])
        fig.update_layout(yaxis_tickformat=",.0f")
        
        return apply_theme(fig)
        
    except Exception as e:
        return handle_chart_error(e, "Évolution Dette")