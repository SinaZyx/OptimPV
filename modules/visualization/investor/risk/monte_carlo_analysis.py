"""
Module pour l'analyse Monte Carlo et risques
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ...shared.chart_utilities import (
    apply_theme, format_number, format_currency, format_percentage,
    validate_chart_data, COLORS, handle_chart_error
)

def create_monte_carlo_results_chart(mc_results):
    """
    Crée un graphique des résultats de la simulation Monte Carlo.
    """
    try:
        if not mc_results or not isinstance(mc_results, dict) or \
           'probabilities' not in mc_results or \
           'results' not in mc_results or \
           'statistics' not in mc_results:
            st.warning("Données MC invalides pour graphique.")
            return None
        
        raw_values_mc = mc_results.get('results', {})
        stats_mc = mc_results.get('statistics', {})
        contraintes_mc = mc_results.get('contraintes_mc_cibles_appliquees', mc_results.get('contraintes_mc', {}))
        scenario_name_mc = mc_results.get('scenario_name', 'Inconnu')
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Distribution VAN Equity (€)", 
                "Distribution TRI Equity (%)", 
                "Distribution Payback Equity (ans)", 
                "Distribution DSCR Moyen"
            ),
            vertical_spacing=0.15, 
            horizontal_spacing=0.1
        )
        
        metrics_mc_plot = [
            {
                'key': 'npv', 
                'name': 'VAN Equity (€)', 
                'unit': '€', 
                'multiplier': 1, 
                'row': 1, 
                'col': 1, 
                'color': COLORS['primary'], 
                'target_key': None
            },
            {
                'key': 'irr', 
                'name': 'TRI Equity (%)', 
                'unit': '%', 
                'multiplier': 100, 
                'row': 1, 
                'col': 2, 
                'color': COLORS['success'], 
                'target_key': 'cout_fonds_propres'
            },
            {
                'key': 'payback_period', 
                'name': 'Payback Equity (ans)', 
                'unit': 'ans', 
                'multiplier': 1, 
                'row': 2, 
                'col': 1, 
                'color': COLORS['warning'], 
                'target_key': 'payback_max_equity_annees'
            },
            {
                'key': 'avg_dscr', 
                'name': 'DSCR Moyen', 
                'unit': None, 
                'multiplier': 1, 
                'row': 2, 
                'col': 2, 
                'color': COLORS['danger'], 
                'target_key': 'dscr_moyen_min'
            }
        ]
        
        for metric in metrics_mc_plot:
            metric_key_mc = metric['key']
            values_key_mc = f"{metric_key_mc}_values" 
            
            if values_key_mc not in raw_values_mc or metric_key_mc not in stats_mc:
                print(f"WARN MC Plot: Données manquantes pour {metric_key_mc}")
                continue
                 
            data_values_mc = np.array(raw_values_mc[values_key_mc])
            data_values_mc = data_values_mc[np.isfinite(data_values_mc)]
            stat_info_mc = stats_mc[metric_key_mc]
            mean_val_mc = stat_info_mc.get('mean', np.nan)
            
            target_val_mc = None
            if metric.get('target_key'):
                target_val_mc = contraintes_mc.get(metric['target_key'], st.session_state.config.get(metric['target_key']))

            fig.add_trace(go.Histogram(
                x=data_values_mc * metric['multiplier'], 
                name=metric['name'],
                marker_color=metric['color'], 
                opacity=0.75, 
                nbinsx=30
            ), row=metric['row'], col=metric['col'])
            
            # Ligne moyenne
            if pd.notna(mean_val_mc):
                mean_plot_mc = mean_val_mc * metric['multiplier']
                fig.add_vline(
                    x=mean_plot_mc, 
                    line_width=2, 
                    line_dash="dash", 
                    line_color=COLORS['neutral'],
                    annotation_text=f"Moy: {format_number(mean_plot_mc, 2)}{metric.get('unit','')}", 
                    annotation_position="top right", 
                    row=metric['row'], 
                    col=metric['col']
                )
            
            # Ligne cible
            if target_val_mc is not None and pd.notna(target_val_mc):
                target_plot_mc = target_val_mc * metric['multiplier'] if metric_key_mc != 'irr' else target_val_mc
                
                color_cible_mc = COLORS['success']
                if metric_key_mc == 'payback_period': 
                    color_cible_mc = COLORS['danger']
                    
                fig.add_vline(
                    x=target_plot_mc, 
                    line_width=2, 
                    line_dash="dot", 
                    line_color=color_cible_mc,
                    annotation_text=f"Cible: {format_number(target_plot_mc, 2)}{metric.get('unit','')}", 
                    annotation_position="bottom right", 
                    row=metric['row'], 
                    col=metric['col']
                )
                          
            fig.update_xaxes(title_text=metric['name'], row=metric['row'], col=metric['col'])
            fig.update_yaxes(title_text="Fréquence", row=metric['row'], col=metric['col'])

        fig.update_layout(
            title_text=f"Distributions Monte Carlo - Scénario: {scenario_name_mc}",
            height=700, 
            showlegend=False, 
            bargap=0.1
        )
        
        return apply_theme(fig)
        
    except Exception as e:
        return handle_chart_error(e, "Monte Carlo")

def create_monte_carlo_boxplot(mc_results):
    """
    Crée des box plots pour les résultats clés de Monte Carlo.
    """
    try:
        if not mc_results or 'results' not in mc_results or 'statistics' not in mc_results:
            return None

        data_mc_box = mc_results.get('results', {})
        metrics_mc_box_plot = {
            'npv': {'name': 'VAN Equity (€)', 'data_key': 'npv_values'},
            'irr': {'name': 'TRI Equity (%)', 'data_key': 'irr_values', 'multiplier': 100},
            'payback_period': {'name': 'Payback Equity (ans)', 'data_key': 'payback_period_values'},
            'avg_dscr': {'name': 'DSCR Moyen', 'data_key': 'avg_dscr_values'}
        }

        fig = go.Figure()
        
        for i, (key_box, info_box) in enumerate(metrics_mc_box_plot.items()):
            values_box = data_mc_box.get(info_box['data_key'])
            if values_box is not None:
                valid_values_box = np.array(values_box)
                valid_values_box = valid_values_box[np.isfinite(valid_values_box)]
                if len(valid_values_box) > 0:
                    multiplier_box = info_box.get('multiplier', 1)
                    fig.add_trace(go.Box(
                        y=valid_values_box * multiplier_box, 
                        name=info_box['name'],
                        boxpoints='outliers', 
                        jitter=0.3, 
                        pointpos=-1.8,
                        marker_color=list(COLORS.values())[i % len(COLORS)]
                    ))
                    
        fig.update_layout(
            title="Distribution des Résultats Clés (Monte Carlo - Box Plots)",
            yaxis_title="Valeur", 
            showlegend=True,
            height=500
        )
        
        return apply_theme(fig)
        
    except Exception as e:
        return handle_chart_error(e, "Monte Carlo Box Plot")