"""
Module de visualisation pour les clés de répartition
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime

from .key_models import RepartitionKey, RepartitionPeriod


def create_repartition_pie_chart(keys: List[RepartitionKey]) -> go.Figure:
    """
    Crée un graphique camembert interactif de la répartition actuelle
    
    Args:
        keys: Liste des clés de répartition
        
    Returns:
        Figure Plotly
    """
    if not keys:
        # Graphique vide avec message
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune clé de répartition définie",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        fig.update_layout(
            height=400,
            showlegend=False
        )
        return fig
    
    # Préparer les données
    labels = [key.participant_name for key in keys]
    values = [key.value for key in keys]
    
    # Créer le graphique camembert
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        textposition='inside',
        texttemplate='%{label}<br>%{value:.1f}%',
        hovertemplate='<b>%{label}</b><br>' +
                      'Allocation: %{value:.1f}%<br>' +
                      'Part: %{percent}<br>' +
                      '<extra></extra>',
        marker=dict(
            colors=px.colors.qualitative.Set3,
            line=dict(color='white', width=2)
        )
    )])
    
    # Mise en forme
    fig.update_layout(
        title={
            'text': 'Répartition de la Production',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        height=500,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05
        ),
        annotations=[
            dict(
                text=f'Total<br>{sum(values):.1f}%',
                x=0.5, y=0.5,
                font_size=16,
                showarrow=False
            )
        ]
    )
    
    return fig


def create_temporal_evolution_chart(temporal_periods: List[RepartitionPeriod]) -> go.Figure:
    """
    Crée un graphique d'évolution temporelle des clés
    
    Args:
        temporal_periods: Liste des périodes temporelles
        
    Returns:
        Figure Plotly
    """
    if not temporal_periods:
        # Graphique vide
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune période temporelle définie",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        fig.update_layout(height=400)
        return fig
    
    # Collecter tous les participants uniques
    all_participants = set()
    for period in temporal_periods:
        for key in period.keys:
            all_participants.add(key.participant_name)
    
    # Créer les traces pour chaque participant
    fig = go.Figure()
    
    for participant in sorted(all_participants):
        x_values = []
        y_values = []
        
        for period in temporal_periods:
            # Trouver la clé pour ce participant dans cette période
            key = next((k for k in period.keys if k.participant_name == participant), None)
            
            if key:
                # Utiliser la date de début de la période
                period_date = period.start_date if period.start_date else datetime.now()
                x_values.append(period_date)
                y_values.append(key.value)
        
        # Ajouter la trace
        if x_values:
            fig.add_trace(go.Scatter(
                x=x_values,
                y=y_values,
                mode='lines+markers',
                name=participant,
                line=dict(width=3),
                marker=dict(size=8)
            ))
    
    # Mise en forme
    fig.update_layout(
        title={
            'text': 'Évolution Temporelle des Clés de Répartition',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title="Période",
        yaxis_title="Allocation (%)",
        height=500,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.02
        ),
        yaxis=dict(
            range=[0, 105],
            ticksuffix="%"
        )
    )
    
    # Ajouter une ligne de référence à 100%
    fig.add_hline(
        y=100, 
        line_dash="dash", 
        line_color="gray",
        annotation_text="Total = 100%"
    )
    
    return fig


def create_impact_comparison_chart(
    baseline: Dict[str, float], 
    scenario: Dict[str, float]
) -> go.Figure:
    """
    Crée un graphique de comparaison avant/après modification des clés
    
    Args:
        baseline: Allocations de base (dict participant -> valeur)
        scenario: Nouvelles allocations (dict participant -> valeur)
        
    Returns:
        Figure Plotly
    """
    # Obtenir tous les participants
    all_participants = sorted(set(baseline.keys()) | set(scenario.keys()))
    
    # Préparer les données
    baseline_values = [baseline.get(p, 0) for p in all_participants]
    scenario_values = [scenario.get(p, 0) for p in all_participants]
    differences = [scenario.get(p, 0) - baseline.get(p, 0) for p in all_participants]
    
    # Créer le graphique
    fig = go.Figure()
    
    # Barres de base
    fig.add_trace(go.Bar(
        name='Répartition Actuelle',
        x=all_participants,
        y=baseline_values,
        marker_color='lightblue',
        text=[f'{v:.1f}%' for v in baseline_values],
        textposition='auto'
    ))
    
    # Barres du scénario
    fig.add_trace(go.Bar(
        name='Nouvelle Répartition',
        x=all_participants,
        y=scenario_values,
        marker_color='darkblue',
        text=[f'{v:.1f}%' for v in scenario_values],
        textposition='auto'
    ))
    
    # Mise en forme
    fig.update_layout(
        title={
            'text': 'Comparaison des Répartitions',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title="Participants",
        yaxis_title="Allocation (%)",
        barmode='group',
        height=500,
        showlegend=True,
        yaxis=dict(
            range=[0, max(max(baseline_values), max(scenario_values)) * 1.1],
            ticksuffix="%"
        )
    )
    
    # Ajouter les annotations pour les différences significatives
    for i, (participant, diff) in enumerate(zip(all_participants, differences)):
        if abs(diff) > 1:  # Seulement si la différence est significative
            fig.add_annotation(
                x=participant,
                y=max(baseline_values[i], scenario_values[i]) + 2,
                text=f'{diff:+.1f}%',
                showarrow=False,
                font=dict(
                    color='green' if diff > 0 else 'red',
                    size=12
                )
            )
    
    return fig


def create_consumption_vs_allocation_chart(
    allocation_data: pd.DataFrame,
    consumption_data: Optional[pd.DataFrame] = None
) -> go.Figure:
    """
    Crée un graphique consommation réelle vs allocation
    
    Args:
        allocation_data: DataFrame avec les allocations par participant
        consumption_data: DataFrame avec la consommation par participant (optionnel)
        
    Returns:
        Figure Plotly
    """
    # Calculer les totaux par participant
    allocation_totals = {}
    consumption_totals = {}
    
    # Totaux d'allocation
    for col in allocation_data.columns:
        if col.startswith('Production_'):
            participant = col.replace('Production_', '')
            allocation_totals[participant] = allocation_data[col].sum()
    
    # Totaux de consommation si disponibles
    if consumption_data is not None:
        for col in consumption_data.columns:
            if col in allocation_totals:
                consumption_totals[col] = consumption_data[col].sum()
    
    # Créer le graphique
    participants = sorted(allocation_totals.keys())
    
    fig = go.Figure()
    
    # Barres d'allocation
    fig.add_trace(go.Bar(
        name='Production Allouée',
        x=participants,
        y=[allocation_totals[p] for p in participants],
        marker_color='blue',
        yaxis='y'
    ))
    
    # Ligne de consommation si disponible
    if consumption_totals:
        fig.add_trace(go.Scatter(
            name='Consommation Réelle',
            x=participants,
            y=[consumption_totals.get(p, 0) for p in participants],
            mode='lines+markers',
            marker_color='red',
            line=dict(width=3),
            marker=dict(size=10),
            yaxis='y'
        ))
    
    # Mise en forme
    fig.update_layout(
        title={
            'text': 'Allocation vs Consommation',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title="Participants",
        yaxis_title="Énergie (kWh)",
        height=500,
        hovermode='x unified',
        showlegend=True,
        yaxis=dict(title="Énergie (kWh)")
    )
    
    return fig


def create_allocation_heatmap(
    temporal_data: pd.DataFrame,
    participant: str
) -> go.Figure:
    """
    Crée une heatmap de l'allocation pour un participant sur le temps
    
    Args:
        temporal_data: DataFrame avec les allocations temporelles
        participant: Nom du participant
        
    Returns:
        Figure Plotly
    """
    column_name = f"Production_{participant}"
    
    if column_name not in temporal_data.columns:
        # Graphique vide
        fig = go.Figure()
        fig.add_annotation(
            text=f"Aucune donnée pour {participant}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        fig.update_layout(height=400)
        return fig
    
    # Préparer les données pour la heatmap
    # Grouper par heure et jour
    data = temporal_data[[column_name]].copy()
    data['hour'] = data.index.hour
    data['date'] = data.index.date
    
    # Pivot pour créer la matrice
    pivot_data = data.pivot_table(
        values=column_name,
        index='hour',
        columns='date',
        aggfunc='mean'
    )
    
    # Créer la heatmap
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='Blues',
        text=np.round(pivot_data.values, 1),
        texttemplate='%{text}',
        textfont={"size": 10},
        hovertemplate='Date: %{x}<br>Heure: %{y}h<br>Allocation: %{z:.1f} kWh<extra></extra>'
    ))
    
    # Mise en forme
    fig.update_layout(
        title={
            'text': f'Pattern d\'Allocation - {participant}',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title="Date",
        yaxis_title="Heure de la journée",
        height=500,
        yaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=1,
            ticksuffix='h'
        )
    )
    
    return fig


def create_rules_impact_chart(
    rules_results: Dict[str, Dict]
) -> go.Figure:
    """
    Visualise l'impact de chaque règle sur la répartition
    
    Args:
        rules_results: Résultats par règle {rule_name: {participant: allocation}}
        
    Returns:
        Figure Plotly
    """
    # Préparer les données
    rule_names = list(rules_results.keys())
    
    # Obtenir tous les participants
    all_participants = set()
    for results in rules_results.values():
        all_participants.update(results.keys())
    
    participants = sorted(all_participants)
    
    # Créer le graphique
    fig = go.Figure()
    
    # Une trace par règle
    for rule_name in rule_names:
        values = [rules_results[rule_name].get(p, 0) for p in participants]
        
        fig.add_trace(go.Bar(
            name=rule_name,
            x=participants,
            y=values,
            text=[f'{v:.1f}' for v in values],
            textposition='auto'
        ))
    
    # Mise en forme
    fig.update_layout(
        title={
            'text': 'Impact des Règles de Répartition',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title="Participants",
        yaxis_title="Allocation (%)",
        barmode='stack',
        height=500,
        showlegend=True,
        yaxis=dict(ticksuffix="%")
    )
    
    return fig


def create_optimization_progress_chart(
    iterations: List[Dict]
) -> go.Figure:
    """
    Visualise la progression de l'optimisation
    
    Args:
        iterations: Liste des itérations avec leurs métriques
        
    Returns:
        Figure Plotly
    """
    if not iterations:
        return go.Figure()
    
    # Extraire les métriques
    iteration_numbers = list(range(len(iterations)))
    objectives = [it.get('objective_value', 0) for it in iterations]
    
    # Créer le graphique
    fig = go.Figure()
    
    # Courbe de l'objectif
    fig.add_trace(go.Scatter(
        x=iteration_numbers,
        y=objectives,
        mode='lines+markers',
        name='Valeur Objectif',
        line=dict(color='blue', width=3),
        marker=dict(size=8)
    ))
    
    # Marquer le meilleur point
    best_idx = objectives.index(max(objectives))
    fig.add_trace(go.Scatter(
        x=[best_idx],
        y=[objectives[best_idx]],
        mode='markers',
        name='Optimum',
        marker=dict(
            size=15,
            color='red',
            symbol='star'
        )
    ))
    
    # Mise en forme
    fig.update_layout(
        title={
            'text': 'Progression de l\'Optimisation',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title="Itération",
        yaxis_title="Valeur de l'Objectif",
        height=400,
        showlegend=True
    )
    
    return fig