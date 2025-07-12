"""
Module pour la visualisation de la distribution énergétique
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from ...shared.chart_utilities import (
    apply_theme, format_number, format_percentage, validate_chart_data,
    COLORS, handle_chart_error
)

def create_energy_distribution_pie(results_data):
    """
    Crée un graphique camembert de la répartition de l'énergie produite.
    """
    try:
        if not validate_chart_data(results_data, ['monthly_data']):
            return None
        
        monthly_data_df = results_data.get('monthly_data')
        if not isinstance(monthly_data_df, pd.DataFrame) or monthly_data_df.empty:
            return None
        
        # Utiliser une copie pour éviter SettingWithCopyWarning
        monthly_data = monthly_data_df.copy()

        # Gestion des noms de colonnes alternatives
        required_cols = ['Autoconsommation_kWh', 'Surplus_kWh']
        alt_cols_map = {
            'Autoconsommation_kWh': ['autoconsumption_kwh', 'autoconsommation_kwh'],
            'Surplus_kWh': ['surplus_kwh', 'surplus']
        }
        
        for req_col, alt_names in alt_cols_map.items():
            if req_col not in monthly_data.columns:
                for alt_name in alt_names:
                    if alt_name in monthly_data.columns:
                        monthly_data.rename(columns={alt_name: req_col}, inplace=True)
                        break
        
        if not all(col in monthly_data.columns for col in required_cols):
            st.warning(f"Colonnes nécessaires pour le camembert non trouvées: {required_cols}")
            return None
                    
        autoconsommation_totale = monthly_data['Autoconsommation_kWh'].sum()
        surplus_total = monthly_data['Surplus_kWh'].sum()
        
        labels = ['Autoconsommation Locale', 'Surplus Injecté']
        values = [autoconsommation_totale, surplus_total]
        colors = [COLORS['success'], COLORS['warning']]
        
        production_totale = autoconsommation_totale + surplus_total
        taux_autoconsommation = (autoconsommation_totale / production_totale * 100) if production_totale > 0 else 0
        
        fig = go.Figure(data=[go.Pie(
            labels=labels, 
            values=values, 
            marker=dict(colors=colors),
            textinfo='value+percent', 
            insidetextorientation='radial',
            hoverinfo='label+value+percent', 
            hole=0.4,
            texttemplate='%{value:,.0f} kWh<br>%{percent}'
        )])
        
        fig.add_annotation(
            text=f"{format_percentage(taux_autoconsommation, 1)}<br>Autoconsommation",
            x=0.5, y=0.5, 
            font_size=14, 
            showarrow=False
        )
        
        fig.update_layout(
            title="Répartition de l'Énergie Produite", 
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
        )
        
        return apply_theme(fig)
        
    except Exception as e:
        return handle_chart_error(e, "Distribution Énergétique")