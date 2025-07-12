"""
Graphiques interactifs avancés avec fonctionnalités modernes
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Callable
import json
from datetime import datetime, timedelta

class InteractiveChartManager:
    """Gestionnaire pour les graphiques interactifs avec synchronisation"""
    
    def __init__(self):
        """Initialise le gestionnaire de graphiques"""
        if 'chart_state' not in st.session_state:
            st.session_state.chart_state = {
                'zoom_range': None,
                'selected_points': [],
                'brush_selection': None,
                'drill_level': 0,
                'sync_enabled': True
            }
    
    def create_synchronized_charts(
        self,
        datasets: List[Dict[str, Any]],
        chart_configs: List[Dict[str, Any]],
        sync_axis: str = 'x',
        height: int = 400
    ) -> List[go.Figure]:
        """
        Crée plusieurs graphiques avec zoom synchronisé
        
        Args:
            datasets: Liste des datasets
            chart_configs: Configuration pour chaque graphique
            sync_axis: Axe à synchroniser ('x', 'y', ou 'both')
            height: Hauteur des graphiques
            
        Returns:
            Liste des figures Plotly
        """
        figures = []
        
        for i, (data, config) in enumerate(zip(datasets, chart_configs)):
            fig = self._create_single_chart(data, config)
            
            # Ajouter la synchronisation
            if st.session_state.chart_state['sync_enabled']:
                fig.update_layout(
                    uirevision='constant',  # Préserve l'état du zoom
                    xaxis=dict(
                        rangeslider=dict(visible=False),
                        type='date' if config.get('x_type') == 'date' else 'linear'
                    )
                )
                
                # Si un range est défini, l'appliquer
                if st.session_state.chart_state['zoom_range'] and sync_axis in ['x', 'both']:
                    fig.update_xaxes(range=st.session_state.chart_state['zoom_range'])
            
            # Style moderne
            fig.update_layout(
                height=height,
                margin=dict(l=0, r=0, t=40, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter, sans-serif"),
                hovermode='x unified',
                hoverlabel=dict(
                    bgcolor='rgba(255, 255, 255, 0.9)',
                    font_size=14,
                    font_family="Inter"
                )
            )
            
            figures.append(fig)
        
        return figures
    
    def _create_single_chart(self, data: Dict[str, Any], config: Dict[str, Any]) -> go.Figure:
        """Crée un graphique unique selon la configuration"""
        chart_type = config.get('type', 'line')
        
        if chart_type == 'line':
            fig = go.Figure()
            
            for series in data.get('series', []):
                fig.add_trace(go.Scatter(
                    x=series['x'],
                    y=series['y'],
                    name=series.get('name', 'Série'),
                    mode='lines+markers' if config.get('show_markers') else 'lines',
                    line=dict(
                        width=3,
                        shape='spline' if config.get('smooth') else 'linear'
                    ),
                    marker=dict(size=6),
                    hovertemplate='%{y:.2f}<extra></extra>'
                ))
                
        elif chart_type == 'bar':
            fig = go.Figure()
            
            for series in data.get('series', []):
                fig.add_trace(go.Bar(
                    x=series['x'],
                    y=series['y'],
                    name=series.get('name', 'Série'),
                    text=series['y'],
                    textposition='auto',
                    hovertemplate='%{y:.2f}<extra></extra>'
                ))
                
        elif chart_type == 'area':
            fig = go.Figure()
            
            for series in data.get('series', []):
                fig.add_trace(go.Scatter(
                    x=series['x'],
                    y=series['y'],
                    name=series.get('name', 'Série'),
                    mode='lines',
                    fill='tonexty' if len(fig.data) > 0 else 'tozeroy',
                    stackgroup='one' if config.get('stacked') else None,
                    hovertemplate='%{y:.2f}<extra></extra>'
                ))
        
        # Titre et axes
        fig.update_layout(
            title=dict(
                text=config.get('title', ''),
                font=dict(size=18, weight=600)
            ),
            xaxis_title=config.get('x_label', ''),
            yaxis_title=config.get('y_label', ''),
            showlegend=config.get('show_legend', True),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_drill_down_chart(
        self,
        data: pd.DataFrame,
        hierarchy: List[str],
        value_col: str,
        chart_type: str = 'bar',
        title: str = "Drill-Down Chart"
    ) -> go.Figure:
        """
        Crée un graphique avec capacité de drill-down
        
        Args:
            data: DataFrame avec les données
            hierarchy: Liste des colonnes pour la hiérarchie
            value_col: Colonne des valeurs
            chart_type: Type de graphique
            title: Titre du graphique
        """
        current_level = st.session_state.chart_state.get('drill_level', 0)
        current_level = min(current_level, len(hierarchy) - 1)
        
        # Grouper les données selon le niveau actuel
        group_cols = hierarchy[:current_level + 1]
        grouped = data.groupby(group_cols)[value_col].sum().reset_index()
        
        # Créer le graphique
        if chart_type == 'bar':
            fig = go.Figure(data=[
                go.Bar(
                    x=grouped[group_cols[-1]],
                    y=grouped[value_col],
                    text=grouped[value_col].round(2),
                    textposition='auto',
                    hovertemplate='<b>%{x}</b><br>Valeur: %{y:.2f}<extra></extra>',
                    marker_color='rgba(30, 136, 229, 0.8)'
                )
            ])
        elif chart_type == 'sunburst':
            # Préparer les données pour sunburst
            fig = go.Figure(data=[
                go.Sunburst(
                    labels=grouped[group_cols[-1]],
                    parents=[''] * len(grouped),
                    values=grouped[value_col],
                    branchvalues="total",
                    hovertemplate='<b>%{label}</b><br>Valeur: %{value:.2f}<extra></extra>'
                )
            ])
        
        # Mise en page
        fig.update_layout(
            title=dict(
                text=f"{title} - Niveau: {group_cols[-1]}",
                font=dict(size=20)
            ),
            height=500,
            showlegend=False,
            margin=dict(l=0, r=0, t=60, b=0)
        )
        
        # Ajouter les boutons de navigation
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            if current_level > 0:
                if st.button("⬆️ Niveau précédent", key="drill_up"):
                    st.session_state.chart_state['drill_level'] = current_level - 1
                    st.rerun()
                    
        with col3:
            if current_level < len(hierarchy) - 1:
                if st.button("⬇️ Drill down", key="drill_down"):
                    st.session_state.chart_state['drill_level'] = current_level + 1
                    st.rerun()
        
        return fig
    
    def create_brush_link_charts(
        self,
        data: pd.DataFrame,
        x_col: str,
        y_cols: List[str],
        link_col: Optional[str] = None
    ) -> Tuple[go.Figure, go.Figure]:
        """
        Crée deux graphiques avec sélection brush & link
        
        Args:
            data: DataFrame source
            x_col: Colonne X
            y_cols: Colonnes Y (au moins 2)
            link_col: Colonne pour le lien (catégorie)
        """
        # Graphique principal avec sélection
        fig_main = go.Figure()
        
        # Ajouter les traces
        if link_col and link_col in data.columns:
            for category in data[link_col].unique():
                mask = data[link_col] == category
                fig_main.add_trace(go.Scatter(
                    x=data.loc[mask, x_col],
                    y=data.loc[mask, y_cols[0]],
                    mode='markers',
                    name=str(category),
                    marker=dict(size=8)
                ))
        else:
            fig_main.add_trace(go.Scatter(
                x=data[x_col],
                y=data[y_cols[0]],
                mode='markers',
                name=y_cols[0],
                marker=dict(
                    size=8,
                    color=data[y_cols[0]],
                    colorscale='Viridis',
                    showscale=True
                )
            ))
        
        # Configuration pour la sélection
        fig_main.update_layout(
            title="Sélectionnez des points (cliquez et glissez)",
            dragmode='lasso',
            height=400,
            hovermode='closest'
        )
        
        # Graphique secondaire
        fig_detail = go.Figure()
        
        if len(y_cols) >= 2:
            fig_detail.add_trace(go.Scatter(
                x=data[y_cols[0]],
                y=data[y_cols[1]],
                mode='markers',
                text=data[x_col] if isinstance(data[x_col].iloc[0], str) else None,
                marker=dict(
                    size=10,
                    color=data[y_cols[1]],
                    colorscale='Plasma',
                    showscale=True
                )
            ))
            
            fig_detail.update_layout(
                title="Vue détaillée (corrélation)",
                xaxis_title=y_cols[0],
                yaxis_title=y_cols[1],
                height=400
            )
        
        return fig_main, fig_detail

def create_animated_time_series(
    data: pd.DataFrame,
    date_col: str,
    value_cols: List[str],
    animation_speed: int = 100,
    title: str = "Évolution temporelle"
) -> go.Figure:
    """
    Crée un graphique temporel avec animation
    
    Args:
        data: DataFrame avec données temporelles
        date_col: Colonne de dates
        value_cols: Colonnes de valeurs
        animation_speed: Vitesse d'animation en ms
        title: Titre du graphique
    """
    # Préparer les données pour l'animation
    data_sorted = data.sort_values(date_col)
    dates = pd.to_datetime(data_sorted[date_col])
    
    # Créer les frames d'animation
    frames = []
    for i in range(1, len(data_sorted) + 1):
        frame_data = []
        for col in value_cols:
            frame_data.append(go.Scatter(
                x=dates[:i],
                y=data_sorted[col].iloc[:i],
                mode='lines+markers',
                name=col,
                line=dict(width=3)
            ))
        frames.append(go.Frame(data=frame_data, name=str(i)))
    
    # Figure initiale
    fig = go.Figure(
        data=[go.Scatter(x=[], y=[], mode='lines+markers', name=col) for col in value_cols],
        frames=frames
    )
    
    # Mise en page avec boutons d'animation
    fig.update_layout(
        title=dict(text=title, font=dict(size=20)),
        updatemenus=[{
            'type': 'buttons',
            'showactive': False,
            'buttons': [
                {
                    'label': '▶️ Play',
                    'method': 'animate',
                    'args': [None, {
                        'frame': {'duration': animation_speed, 'redraw': True},
                        'fromcurrent': True,
                        'transition': {'duration': animation_speed, 'easing': 'quadratic-in-out'}
                    }]
                },
                {
                    'label': '⏸️ Pause',
                    'method': 'animate',
                    'args': [[None], {
                        'frame': {'duration': 0, 'redraw': False},
                        'mode': 'immediate',
                        'transition': {'duration': 0}
                    }]
                }
            ],
            'direction': 'left',
            'pad': {'r': 10, 't': 10},
            'x': 0.1,
            'xanchor': 'right',
            'y': 0,
            'yanchor': 'top'
        }],
        sliders=[{
            'steps': [
                {
                    'args': [[str(i)], {
                        'frame': {'duration': 300, 'redraw': True},
                        'mode': 'immediate',
                        'transition': {'duration': 300}
                    }],
                    'label': str(dates.iloc[i-1].date()),
                    'method': 'animate'
                } for i in range(1, len(data_sorted) + 1)
            ],
            'active': 0,
            'y': 0,
            'len': 0.9,
            'x': 0.1,
            'xanchor': 'left',
            'y': -0.1,
            'yanchor': 'top',
            'transition': {'duration': 300, 'easing': 'cubic-in-out'}
        }],
        height=500,
        xaxis=dict(
            range=[dates.min(), dates.max()],
            rangeslider=dict(visible=True)
        ),
        yaxis=dict(
            range=[
                min([data_sorted[col].min() for col in value_cols]) * 0.9,
                max([data_sorted[col].max() for col in value_cols]) * 1.1
            ]
        )
    )
    
    return fig

def create_realtime_chart_placeholder(
    chart_id: str,
    update_interval: int = 1000,
    max_points: int = 100
) -> None:
    """
    Crée un placeholder pour un graphique temps réel
    
    Args:
        chart_id: Identifiant unique du graphique
        update_interval: Intervalle de mise à jour en ms
        max_points: Nombre maximum de points à afficher
    """
    # Placeholder pour le graphique
    chart_placeholder = st.empty()
    
    # CSS et JavaScript pour la mise à jour temps réel
    st.markdown(f"""
    <script>
    // Simulation de données temps réel
    let data_{chart_id} = {{
        x: [],
        y: []
    }};
    
    function updateRealtimeChart_{chart_id}() {{
        // Ajouter un nouveau point
        const now = new Date();
        const value = Math.sin(Date.now() / 1000) * 100 + Math.random() * 20;
        
        data_{chart_id}.x.push(now);
        data_{chart_id}.y.push(value);
        
        // Limiter le nombre de points
        if (data_{chart_id}.x.length > {max_points}) {{
            data_{chart_id}.x.shift();
            data_{chart_id}.y.shift();
        }}
        
        // Mettre à jour le graphique
        // (Intégration avec Plotly.js nécessaire)
    }}
    
    // Lancer les mises à jour
    setInterval(updateRealtimeChart_{chart_id}, {update_interval});
    </script>
    """, unsafe_allow_html=True)
    
    # Graphique initial
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[],
        y=[],
        mode='lines',
        name='Temps réel',
        line=dict(color='#1E88E5', width=2)
    ))
    
    fig.update_layout(
        title="Données temps réel",
        xaxis=dict(title="Temps", type='date'),
        yaxis=dict(title="Valeur"),
        height=400
    )
    
    chart_placeholder.plotly_chart(fig, use_container_width=True, key=chart_id)