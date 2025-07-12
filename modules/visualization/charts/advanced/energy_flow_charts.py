"""
Visualisations avancées pour les flux énergétiques et analyses complexes
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import plotly.express as px

def create_energy_sankey_diagram(
    energy_flows: Dict[str, Any],
    title: str = "Flux Énergétiques",
    height: int = 600,
    color_scheme: str = "viridis"
) -> go.Figure:
    """
    Crée un diagramme de Sankey pour visualiser les flux énergétiques
    
    Args:
        energy_flows: Dictionnaire avec sources, targets, values et labels
        title: Titre du diagramme
        height: Hauteur du graphique
        color_scheme: Schéma de couleurs
    """
    # Préparer les données pour Sankey
    source = energy_flows.get('source', [])
    target = energy_flows.get('target', [])
    value = energy_flows.get('value', [])
    labels = energy_flows.get('labels', [])
    
    # Couleurs personnalisées pour les nœuds
    node_colors = [
        'rgba(31, 119, 180, 0.8)',  # Production solaire
        'rgba(255, 127, 14, 0.8)',   # Réseau
        'rgba(44, 160, 44, 0.8)',    # Autoconsommation
        'rgba(214, 39, 40, 0.8)',    # Injection réseau
        'rgba(148, 103, 189, 0.8)',  # Stockage
        'rgba(140, 86, 75, 0.8)',    # Consommation
        'rgba(227, 119, 194, 0.8)',  # Pertes
    ]
    
    # Couleurs des liens basées sur la source
    link_colors = []
    for s in source:
        if s == 0:  # Production solaire
            link_colors.append('rgba(31, 119, 180, 0.4)')
        elif s == 1:  # Réseau
            link_colors.append('rgba(255, 127, 14, 0.4)')
        else:
            link_colors.append('rgba(128, 128, 128, 0.4)')
    
    # Créer le diagramme Sankey
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="white", width=0.5),
            label=labels,
            color=node_colors[:len(labels)],
            hovertemplate='%{label}<br>Total: %{value:.0f} kWh<extra></extra>'
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_colors,
            hovertemplate='De %{source.label} vers %{target.label}<br>%{value:.0f} kWh<extra></extra>'
        )
    )])
    
    # Mise en page moderne
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=24, weight=600),
            x=0.5,
            xanchor='center'
        ),
        font=dict(size=12, family="Inter, sans-serif"),
        height=height,
        margin=dict(l=0, r=0, t=60, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_consumption_heatmap(
    data: pd.DataFrame,
    date_col: str,
    value_col: str,
    title: str = "Carte de Chaleur - Consommation",
    aggregation: str = "hourly",
    colorscale: str = "RdYlBu_r"
) -> go.Figure:
    """
    Crée une heatmap temporelle de la consommation
    
    Args:
        data: DataFrame avec les données
        date_col: Colonne de dates
        value_col: Colonne de valeurs
        title: Titre
        aggregation: 'hourly', 'daily', 'weekly'
        colorscale: Échelle de couleurs Plotly
    """
    # Convertir en datetime
    data[date_col] = pd.to_datetime(data[date_col])
    
    if aggregation == "hourly":
        # Heatmap heure x jour de la semaine
        data['hour'] = data[date_col].dt.hour
        data['dayofweek'] = data[date_col].dt.dayofweek
        pivot = data.pivot_table(
            values=value_col,
            index='hour',
            columns='dayofweek',
            aggfunc='mean'
        )
        
        x_labels = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
        y_labels = [f"{h:02d}h" for h in range(24)]
        
    elif aggregation == "daily":
        # Heatmap jour x mois
        data['day'] = data[date_col].dt.day
        data['month'] = data[date_col].dt.month
        pivot = data.pivot_table(
            values=value_col,
            index='day',
            columns='month',
            aggfunc='mean'
        )
        
        x_labels = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 
                   'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
        y_labels = [str(d) for d in range(1, 32)]
        
    elif aggregation == "weekly":
        # Heatmap semaine x mois
        data['week'] = data[date_col].dt.isocalendar().week
        data['month'] = data[date_col].dt.month
        pivot = data.pivot_table(
            values=value_col,
            index='week',
            columns='month',
            aggfunc='mean'
        )
        
        x_labels = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 
                   'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
        y_labels = [f"S{w}" for w in range(1, 53)]
    
    # Créer la heatmap
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=x_labels[:pivot.shape[1]],
        y=y_labels[:pivot.shape[0]],
        colorscale=colorscale,
        hoverongaps=False,
        hovertemplate='%{x}<br>%{y}<br>Valeur: %{z:.1f}<extra></extra>',
        colorbar=dict(
            title=dict(text="kWh", side="right"),
            thickness=15,
            len=0.7,
            x=1.02
        )
    ))
    
    # Mise en page
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=20, weight=600)
        ),
        xaxis=dict(
            title="",
            tickmode='array',
            tickvals=list(range(len(x_labels[:pivot.shape[1]]))),
            ticktext=x_labels[:pivot.shape[1]],
            side='top'
        ),
        yaxis=dict(
            title="",
            tickmode='array',
            tickvals=list(range(len(y_labels[:pivot.shape[0]]))),
            ticktext=y_labels[:pivot.shape[0]],
            autorange='reversed'
        ),
        height=max(400, pivot.shape[0] * 20),
        margin=dict(l=60, r=60, t=100, b=60)
    )
    
    return fig

def create_3d_surface_analysis(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    z_col: str,
    title: str = "Analyse 3D",
    colorscale: str = "Viridis"
) -> go.Figure:
    """
    Crée une surface 3D pour l'analyse multi-paramètres
    
    Args:
        data: DataFrame avec les données
        x_col, y_col, z_col: Colonnes pour les axes
        title: Titre
        colorscale: Échelle de couleurs
    """
    # Créer une grille régulière si nécessaire
    x_unique = sorted(data[x_col].unique())
    y_unique = sorted(data[y_col].unique())
    
    # Pivot pour créer la matrice Z
    z_matrix = data.pivot_table(
        values=z_col,
        index=y_col,
        columns=x_col,
        aggfunc='mean'
    ).values
    
    # Créer la surface 3D
    fig = go.Figure(data=[go.Surface(
        x=x_unique,
        y=y_unique,
        z=z_matrix,
        colorscale=colorscale,
        contours=dict(
            z=dict(
                show=True,
                usecolormap=True,
                highlightcolor="limegreen",
                project=dict(z=True)
            )
        ),
        hovertemplate='%{x}<br>%{y}<br>%{z:.2f}<extra></extra>'
    )])
    
    # Mise en page
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=20, weight=600)
        ),
        scene=dict(
            xaxis=dict(title=x_col, gridcolor='rgb(255, 255, 255)'),
            yaxis=dict(title=y_col, gridcolor='rgb(255, 255, 255)'),
            zaxis=dict(title=z_col, gridcolor='rgb(255, 255, 255)'),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            ),
            aspectratio=dict(x=1, y=1, z=0.7)
        ),
        height=600,
        margin=dict(l=0, r=0, t=60, b=0)
    )
    
    return fig

def create_radar_comparison_chart(
    categories: List[str],
    datasets: List[Dict[str, Any]],
    title: str = "Comparaison Multi-Critères",
    fill: bool = True
) -> go.Figure:
    """
    Crée un graphique radar pour comparaison multi-critères
    
    Args:
        categories: Liste des catégories
        datasets: Liste de datasets avec 'name' et 'values'
        title: Titre
        fill: Remplir les zones
    """
    fig = go.Figure()
    
    # Ajouter chaque dataset
    for i, dataset in enumerate(datasets):
        values = dataset['values']
        # Fermer le polygone
        values_closed = values + [values[0]]
        categories_closed = categories + [categories[0]]
        
        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill='toself' if fill else 'none',
            name=dataset['name'],
            line=dict(width=3),
            opacity=0.7 if fill else 1.0,
            hovertemplate='%{theta}<br>%{r:.1f}<extra></extra>'
        ))
    
    # Mise en page
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max([max(d['values']) for d in datasets]) * 1.1],
                tickfont=dict(size=10)
            ),
            angularaxis=dict(
                tickfont=dict(size=12),
                rotation=90,
                direction='clockwise'
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        showlegend=True,
        title=dict(
            text=title,
            font=dict(size=20, weight=600),
            x=0.5,
            xanchor='center'
        ),
        height=500,
        margin=dict(l=80, r=80, t=100, b=80)
    )
    
    return fig

def create_gantt_installation_chart(
    tasks: List[Dict[str, Any]],
    title: str = "Planning d'Installation",
    show_dependencies: bool = True
) -> go.Figure:
    """
    Crée un diagramme de Gantt pour le planning d'installation
    
    Args:
        tasks: Liste des tâches avec start, end, name, resource
        title: Titre
        show_dependencies: Afficher les dépendances
    """
    # Convertir en DataFrame pour faciliter le traitement
    df_tasks = pd.DataFrame(tasks)
    df_tasks['Start'] = pd.to_datetime(df_tasks['start'])
    df_tasks['Finish'] = pd.to_datetime(df_tasks['end'])
    
    # Créer le diagramme de Gantt
    fig = go.Figure()
    
    # Couleurs par ressource
    colors = {
        'Électricien': 'rgba(31, 119, 180, 0.8)',
        'Installateur': 'rgba(255, 127, 14, 0.8)',
        'Technicien': 'rgba(44, 160, 44, 0.8)',
        'Autre': 'rgba(148, 103, 189, 0.8)'
    }
    
    # Ajouter les barres
    for i, task in df_tasks.iterrows():
        color = colors.get(task.get('resource', 'Autre'), 'rgba(128, 128, 128, 0.8)')
        
        fig.add_trace(go.Bar(
            name=task['name'],
            x=[task['Finish'] - task['Start']],
            y=[task['name']],
            base=task['Start'],
            orientation='h',
            marker=dict(
                color=color,
                line=dict(color='white', width=2)
            ),
            showlegend=False,
            hovertemplate='<b>%{y}</b><br>' +
                         'Début: %{base|%d/%m/%Y}<br>' +
                         'Durée: %{x}<br>' +
                         '<extra></extra>'
        ))
        
        # Ajouter les dépendances si demandé
        if show_dependencies and 'depends_on' in task and task['depends_on']:
            # Logique pour dessiner les flèches de dépendance
            pass
    
    # Mise en page
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=20, weight=600)
        ),
        xaxis=dict(
            type='date',
            title='Timeline',
            tickformat='%d %b',
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)'
        ),
        yaxis=dict(
            title='',
            autorange='reversed',
            showgrid=False
        ),
        height=max(400, len(df_tasks) * 60),
        margin=dict(l=150, r=20, t=80, b=60),
        bargap=0.2,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    # Ajouter une légende manuelle pour les ressources
    for resource, color in colors.items():
        fig.add_trace(go.Scatter(
            x=[None],
            y=[None],
            mode='markers',
            name=resource,
            marker=dict(size=10, color=color)
        ))
    
    return fig

def create_network_energy_flow(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    title: str = "Réseau de Distribution Énergétique"
) -> go.Figure:
    """
    Crée un graphe de réseau pour visualiser la distribution d'énergie
    
    Args:
        nodes: Liste des nœuds avec id, label, x, y, type
        edges: Liste des arêtes avec source, target, value
        title: Titre
    """
    # Créer les traces pour les arêtes
    edge_traces = []
    
    for edge in edges:
        source_node = next(n for n in nodes if n['id'] == edge['source'])
        target_node = next(n for n in nodes if n['id'] == edge['target'])
        
        # Largeur proportionnelle au flux
        width = max(1, edge['value'] / 1000)  # Ajuster selon les valeurs
        
        edge_trace = go.Scatter(
            x=[source_node['x'], target_node['x']],
            y=[source_node['y'], target_node['y']],
            mode='lines',
            line=dict(
                width=width,
                color='rgba(125, 125, 125, 0.5)'
            ),
            hoverinfo='text',
            text=f"{edge['value']:.0f} kWh",
            showlegend=False
        )
        edge_traces.append(edge_trace)
    
    # Créer les traces pour les nœuds
    node_colors = {
        'source': 'rgba(31, 119, 180, 1)',
        'consumer': 'rgba(255, 127, 14, 1)',
        'storage': 'rgba(44, 160, 44, 1)',
        'grid': 'rgba(214, 39, 40, 1)'
    }
    
    node_trace = go.Scatter(
        x=[n['x'] for n in nodes],
        y=[n['y'] for n in nodes],
        mode='markers+text',
        text=[n['label'] for n in nodes],
        textposition='top center',
        marker=dict(
            size=[n.get('size', 20) for n in nodes],
            color=[node_colors.get(n.get('type', 'source'), 'gray') for n in nodes],
            line=dict(width=2, color='white')
        ),
        hoverinfo='text',
        hovertext=[f"{n['label']}<br>Type: {n.get('type', 'N/A')}" for n in nodes]
    )
    
    # Créer la figure
    fig = go.Figure(data=edge_traces + [node_trace])
    
    # Mise en page
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=20, weight=600)
        ),
        showlegend=False,
        height=600,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=0, r=0, t=60, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig