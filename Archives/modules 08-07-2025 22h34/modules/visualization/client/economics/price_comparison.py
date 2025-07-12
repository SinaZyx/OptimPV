"""
Module pour la comparaison des prix client
"""
import streamlit as st
import plotly.graph_objects as go
from ...shared.chart_utilities import apply_theme, format_currency, format_percentage, COLORS

def create_price_comparison_chart(results_data, config):
    """
    Crée un graphique de comparaison entre le prix optimal et le tarif EDF.
    """
    if not results_data or 'prix_revente' not in results_data:
        return None
    
    prix_optimal = results_data.get('prix_revente', 0)
    tarif_edf = config.get('tarif_edf_reference', 0.21)
    
    if tarif_edf > 0:
        economie_pct = ((tarif_edf - prix_optimal) / tarif_edf) * 100
    else:
        economie_pct = 0
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=['Prix Optimal', 'Tarif EDF'],
        y=[prix_optimal, tarif_edf],
        text=[f"{prix_optimal:.4f} €/kWh", f"{tarif_edf:.4f} €/kWh"],
        textposition='outside',
        marker_color=[COLORS['success'], COLORS['danger']],
        hoverinfo='text',
        hovertext=[f"Prix Optimal: {prix_optimal:.4f} €/kWh", f"Tarif EDF: {tarif_edf:.4f} €/kWh"]
    ))
    
    fig.add_annotation(
        x=0.5, y=max(prix_optimal, tarif_edf) * 1.15,
        text=f"Économie: {format_percentage(economie_pct)}", 
        showarrow=False,
        font=dict(size=14, color=COLORS['success'] if economie_pct > 0 else COLORS['danger'])
    )
    
    fig.update_layout(
        title="Comparaison des Prix (€/kWh)", 
        yaxis_title="Prix (€/kWh)",
        showlegend=False, 
        height=400, 
        yaxis=dict(tickformat=",.4f"),
        xaxis=dict(tickangle=-45)
    )
    
    return apply_theme(fig)