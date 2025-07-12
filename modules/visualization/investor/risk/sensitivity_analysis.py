"""
Module pour l'analyse de sensibilité
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ...shared.chart_utilities import (
    apply_theme, format_number, format_currency, format_percentage,
    validate_chart_data, COLORS, handle_chart_error
)

def create_sensitivity_tornado_chart(base_result, sensitivity_results):
    """
    Crée un graphique Tornado montrant l'impact des variations des paramètres.
    """
    try:
        if not base_result or not sensitivity_results:
            return None
        if 'npv' not in base_result or 'irr' not in base_result:
            return None
            
        base_npv = base_result.get('npv', 0)
        base_irr = base_result.get('irr', 0) * 100
        
        tornado_data = []
        for param, results_sens in sensitivity_results.items():
            param_values = []
            npv_deltas = []
            irr_deltas = []
            
            for value, result_sens in results_sens.items():
                if 'npv' in result_sens and 'irr' in result_sens:
                    param_values.append(value)
                    npv_deltas.append(result_sens['npv'] - base_npv)
                    irr_deltas.append(result_sens['irr'] * 100 - base_irr)
                    
            if param_values:
                tornado_data.append({
                    'parameter': param, 
                    'min_npv_delta': min(npv_deltas),
                    'max_npv_delta': max(npv_deltas), 
                    'min_irr_delta': min(irr_deltas),
                    'max_irr_delta': max(irr_deltas)
                })
                
        if not tornado_data:
            return None
            
        fig = make_subplots(
            rows=1, cols=2, 
            subplot_titles=("Impact sur la VAN (€)", "Impact sur le TRI (%)"), 
            horizontal_spacing=0.1
        )
        
        # Trier par impact sur la VAN
        tornado_data.sort(key=lambda x: abs(x['max_npv_delta'] - x['min_npv_delta']), reverse=True)
        parameters = [item['parameter'] for item in tornado_data]
        
        # Graphique VAN
        fig.add_trace(go.Bar(
            y=parameters, 
            x=[item['min_npv_delta'] for item in tornado_data], 
            orientation='h', 
            name='Impact Négatif VAN', 
            marker=dict(color=COLORS['danger'], opacity=0.7), 
            showlegend=True
        ), row=1, col=1)
        
        fig.add_trace(go.Bar(
            y=parameters, 
            x=[item['max_npv_delta'] for item in tornado_data], 
            orientation='h', 
            name='Impact Positif VAN', 
            marker=dict(color=COLORS['success'], opacity=0.7), 
            showlegend=True
        ), row=1, col=1)
        
        # Graphique TRI
        fig.add_trace(go.Bar(
            y=parameters, 
            x=[item['min_irr_delta'] for item in tornado_data], 
            orientation='h', 
            name='Impact Négatif TRI', 
            marker=dict(color=COLORS['danger'], opacity=0.7), 
            showlegend=False
        ), row=1, col=2)
        
        fig.add_trace(go.Bar(
            y=parameters, 
            x=[item['max_irr_delta'] for item in tornado_data], 
            orientation='h', 
            name='Impact Positif TRI', 
            marker=dict(color=COLORS['success'], opacity=0.7), 
            showlegend=False
        ), row=1, col=2)
        
        fig.update_layout(
            barmode='relative', 
            height=500, 
            title="Analyse de Sensibilité (Tornado)", 
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        fig.update_xaxes(title_text="Variation VAN (€)", row=1, col=1)
        fig.update_xaxes(title_text="Variation TRI (%)", row=1, col=2)
        fig.update_yaxes(title_text="Paramètre", row=1, col=1)
        fig.update_yaxes(title_text="", row=1, col=2)
        
        return apply_theme(fig)
        
    except Exception as e:
        return handle_chart_error(e, "Tornado Chart")

def display_sensitivity_analysis_section(selected_scenario):
    """
    Affiche la section d'analyse de sensibilité pour le scénario sélectionné.
    """
    try:
        if 'constrained_optim_results' not in st.session_state or \
           selected_scenario not in st.session_state.constrained_optim_results:
            st.warning(f"Résultats d'optimisation non trouvés pour le scénario {selected_scenario}.")
            return

        optim_results_base = st.session_state.constrained_optim_results[selected_scenario]
        base_results = optim_results_base.get('indicateurs_au_prix_optimal')
        
        if not base_results or 'monthly_data' not in base_results: 
            st.error(f"Indicateurs manquants pour scénario de base {selected_scenario}.")
            return
        
        # Vérifier si des résultats de sensibilité existent
        if 'sensitivity_results' in st.session_state and \
           selected_scenario in st.session_state.sensitivity_results:
            
            results_sensitivity = st.session_state.sensitivity_results[selected_scenario]
            
            # Paramètres à afficher
            params_for_tornado = list(results_sensitivity.keys())

            if len(params_for_tornado) > 0:
                tornado_fig = create_sensitivity_tornado_chart(base_results, results_sensitivity)
                if tornado_fig:
                    st.plotly_chart(tornado_fig, use_container_width=True)
                else:
                    st.warning("Impossible de créer le graphique Tornado de sensibilité.")
            else:
                st.info("Aucun paramètre de sensibilité sélectionné ou disponible pour le graphique Tornado.")

        else:
            st.info(f"Aucun résultat d'analyse de sensibilité disponible pour le scénario '{selected_scenario}'.")
            st.caption("Pour effectuer une analyse de sensibilité, utilisez le module d'optimisation avec les paramètres appropriés.")
            
    except Exception as e:
        st.error(f"Erreur lors de l'affichage de l'analyse de sensibilité: {e}")