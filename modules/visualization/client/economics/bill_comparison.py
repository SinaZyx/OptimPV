"""
Module pour la comparaison des factures client
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from ...shared.chart_utilities import (
    apply_theme, format_currency, format_percentage, validate_chart_data,
    COLORS, handle_chart_error
)

def create_facture_comparison_chart(results_data, config):
    """
    Crée un graphique comparant la facture annuelle avec et sans ACOC.
    """
    try:
        if not validate_chart_data(results_data, ['monthly_data']):
            return None
        
        monthly_data_df = results_data.get('monthly_data')
        if not isinstance(monthly_data_df, pd.DataFrame) or monthly_data_df.empty:
            return None

        # Utiliser une copie
        monthly_data = monthly_data_df.copy()
        
        prix_optimal = results_data.get('prix_revente', 0)
        tarif_edf = config.get('tarif_edf_reference', 0.21)
        
        # Gestion des noms de colonnes alternatives
        required_cols = ['Autoconsommation_kWh', 'Consommation_kWh']
        alt_cols_map = {
            'Autoconsommation_kWh': ['autoconsumption_kwh', 'autoconsommation_kwh'],
            'Consommation_kWh': ['consumption_kwh', 'consommation_kwh']
        }

        for req_col, alt_names in alt_cols_map.items():
            if req_col not in monthly_data.columns:
                for alt_name in alt_names:
                    if alt_name in monthly_data.columns:
                        monthly_data.rename(columns={alt_name: req_col}, inplace=True)
                        break
        
        if not all(col in monthly_data.columns for col in required_cols):
            st.warning(f"Colonnes nécessaires pour la comparaison de facture non trouvées: {required_cols}")
            return None

        autoconsommation_annuelle = monthly_data['Autoconsommation_kWh'].sum()
        consommation_annuelle = monthly_data['Consommation_kWh'].sum()
        
        facture_edf = consommation_annuelle * tarif_edf
        facture_autoconso = autoconsommation_annuelle * prix_optimal
        reste_consommation = max(0, consommation_annuelle - autoconsommation_annuelle)
        facture_reste_edf = reste_consommation * tarif_edf
        facture_totale_acoc = facture_autoconso + facture_reste_edf
        
        economie = facture_edf - facture_totale_acoc
        pourcentage_economie = (economie / facture_edf) * 100 if facture_edf > 0 else 0
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=['Facture Standard EDF'], 
            y=[facture_edf], 
            name='Tarif EDF Standard',
            marker_color=COLORS['danger'], 
            text=[format_currency(facture_edf)], 
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            x=['Facture avec ACOC'], 
            y=[facture_autoconso], 
            name='Partie Autoconsommation',
            marker_color=COLORS['success'], 
            text=[format_currency(facture_autoconso)], 
            textposition='inside'
        ))
        
        if reste_consommation > 0:
            fig.add_trace(go.Bar(
                x=['Facture avec ACOC'], 
                y=[facture_reste_edf], 
                name='Partie Restante EDF',
                marker_color=COLORS['warning'], 
                text=[format_currency(facture_reste_edf)], 
                textposition='inside'
            ))
            
        fig.add_annotation(
            x=0.5, 
            y=max(facture_edf, facture_totale_acoc) * 1.1,
            text=f"Économie: {format_currency(economie)} ({format_percentage(pourcentage_economie)})",
            showarrow=False, 
            font=dict(size=14, color=COLORS['success'])
        )
        
        fig.update_layout(
            title="Comparaison de Facture Annuelle d'Électricité",
            yaxis_title="Montant Annuel (€)", 
            barmode='stack', 
            showlegend=True, 
            height=450,
            yaxis=dict(tickformat=",.0f €"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        
        return apply_theme(fig)
        
    except Exception as e:
        return handle_chart_error(e, "Comparaison de Facture")