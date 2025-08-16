"""
Module pour les indicateurs financiers investisseur
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ...shared.chart_utilities import (
    apply_theme, format_currency, validate_chart_data,
    COLORS, handle_chart_error
)

def create_financial_indicators_chart(results):
    """
    Crée un graphique des indicateurs financiers annuels.
    """
    try:
        if not validate_chart_data(results, ['monthly_data']):
            return None
        
        monthly_df = results.get('monthly_data')
        if not isinstance(monthly_df, pd.DataFrame) or monthly_df.empty:
            st.warning("DataFrame mensuel vide pour graphique indicateurs.")
            return None
        
        df_agg = monthly_df.copy()
        if not isinstance(df_agg.index, pd.DatetimeIndex):
            try: 
                df_agg.index = pd.to_datetime(df_agg.index)
            except: 
                st.error("Index non Datetime pour graphique indicateurs.")
                return None
                
        annual_data = df_agg.resample('Y').sum()
        annual_data['Year'] = annual_data.index.year
        
        # Calcul FCFE si manquant
        if 'FCFE' not in annual_data.columns and all(c in annual_data for c in ['Resultat_Net', 'Amortissement', 'Principal_Rembourse']):
            annual_data['FCFE'] = annual_data['Resultat_Net'] + annual_data['Amortissement'] - annual_data['Principal_Rembourse']
        
        if 'FCFE' in annual_data.columns:
            annual_data['Cumulative_FCFE'] = annual_data['FCFE'].cumsum()
        else: 
            annual_data['Cumulative_FCFE'] = 0
        
        # Calcul CADS pour DSCR
        if 'Tax_Payment' in annual_data.columns and 'EBITDA' in annual_data.columns:
            annual_data['CADS'] = annual_data['EBITDA'] - annual_data['Tax_Payment']
        elif 'EBITDA' in annual_data.columns:
            st.info("Colonne 'Tax_Payment' non trouvée pour DSCR annuel, CADS = EBITDA.")
            annual_data['CADS'] = annual_data['EBITDA']
        else:
            annual_data['CADS'] = 0

        # Calcul DSCR
        if 'Service_Dette' in annual_data.columns:
            annual_data['DSCR_Calculated'] = np.where(
                np.abs(annual_data['Service_Dette']) > 1e-9,
                annual_data['CADS'] / annual_data['Service_Dette'], np.inf
            )
            annual_data.loc[(annual_data['CADS'] <= 0) & (np.abs(annual_data['Service_Dette']) <= 1e-9), 'DSCR_Calculated'] = np.nan
        else:
            annual_data['DSCR_Calculated'] = np.nan
        
        # Création du graphique
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.15,
            subplot_titles=("Flux Financiers Annuels", "DSCR Annuel")
        )
        
        # Graphique 1: Flux financiers
        if 'Revenus_Total' in annual_data:
            fig.add_trace(go.Bar(
                x=annual_data['Year'], 
                y=annual_data['Revenus_Total'], 
                name='Revenus', 
                marker_color=COLORS['success']
            ), row=1, col=1)
            
        if 'OPEX' in annual_data:
            fig.add_trace(go.Bar(
                x=annual_data['Year'], 
                y=annual_data['OPEX'], 
                name='OPEX', 
                marker_color=COLORS['warning']
            ), row=1, col=1)
            
        if 'FCFE' in annual_data:
            fig.add_trace(go.Scatter(
                x=annual_data['Year'], 
                y=annual_data['FCFE'], 
                name='FCFE', 
                mode='lines+markers', 
                line=dict(color='#9467bd'), 
                marker=dict(symbol='circle')
            ), row=1, col=1)
            
        if 'Cumulative_FCFE' in annual_data:
            fig.add_trace(go.Scatter(
                x=annual_data['Year'], 
                y=annual_data['Cumulative_FCFE'], 
                name='FCFE Cumulé', 
                mode='lines+markers', 
                line=dict(color=COLORS['danger']), 
                marker=dict(symbol='diamond')
            ), row=1, col=1)
        
        # Graphique 2: DSCR
        if 'DSCR_Calculated' in annual_data and annual_data['DSCR_Calculated'].notna().any():
            fig.add_trace(go.Scatter(
                x=annual_data['Year'], 
                y=annual_data['DSCR_Calculated'], 
                name='DSCR', 
                mode='lines+markers', 
                line=dict(color=COLORS['info'])
            ), row=2, col=1)
            
            target_dscr = st.session_state.config.get('target_dscr', 1.2)
            fig.add_shape(
                type="line", 
                layer='below',
                x0=annual_data['Year'].min(), 
                y0=target_dscr,
                x1=annual_data['Year'].max(), 
                y1=target_dscr,
                line=dict(color=COLORS['warning'], width=2, dash="dash"), 
                row=2, col=1
            )
            fig.add_annotation(
                x=annual_data['Year'].max(), 
                y=target_dscr, 
                text=f"Cible DSCR: {target_dscr}",
                showarrow=False, 
                yshift=10, 
                xanchor='right', 
                font=dict(color=COLORS['warning']), 
                row=2, col=1
            )
        
        fig.update_layout(
            height=650, 
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), 
            barmode='relative'
        )
        fig.update_yaxes(title_text="Montant (€)", row=1, col=1)
        
        # Ajustement échelle DSCR
        dscr_max_val = 2.5
        if 'DSCR_Calculated' in annual_data and annual_data['DSCR_Calculated'].notna().any():
            finite_dscr = annual_data['DSCR_Calculated'][np.isfinite(annual_data['DSCR_Calculated'])]
            if not finite_dscr.empty:
                dscr_max_val = max(2.5, finite_dscr.max() * 1.1)
                
        fig.update_yaxes(title_text="DSCR", range=[0, dscr_max_val], row=2, col=1)
        fig.update_xaxes(title_text="Année", row=2, col=1)
        
        return apply_theme(fig)
        
    except Exception as e:
        return handle_chart_error(e, "Indicateurs Financiers")