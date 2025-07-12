"""
Utilitaires communs pour tous les graphiques du module visualization
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union, List
import streamlit as st

# Thème Plotly unifié
PLOTLY_THEME = {
    'layout': {
        'font': {'family': 'Arial, sans-serif', 'size': 12},
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(248,249,250,0.8)',
        'margin': {'l': 60, 'r': 30, 't': 50, 'b': 60},
        'hovermode': 'x unified',
        'hoverlabel': {
            'bgcolor': 'white',
            'font_size': 12,
            'font_family': 'Arial, sans-serif'
        }
    },
    'colorway': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f'],
    'grid': {
        'rows': 1,
        'columns': 1,
        'pattern': 'independent'
    }
}

# Couleurs standard
COLORS = {
    'primary': '#1f77b4',
    'success': '#2ca02c', 
    'warning': '#ff7f0e',
    'danger': '#d62728',
    'info': '#17a2b8',
    'light': '#f8f9fa',
    'dark': '#343a40',
    'positive': '#28a745',
    'negative': '#dc3545',
    'neutral': '#6c757d'
}

# Formatage des nombres
def format_number(value: Union[int, float], decimals: int = 0, suffix: str = '') -> str:
    """
    Formate un nombre avec séparateurs de milliers et suffixe
    """
    if pd.isna(value):
        return "N/A"
    
    if decimals == 0:
        formatted = f"{int(value):,}".replace(',', ' ')
    else:
        formatted = f"{value:,.{decimals}f}".replace(',', ' ')
    
    return f"{formatted}{suffix}"

def format_currency(value: Union[int, float], decimals: int = 0) -> str:
    """
    Formate une valeur monétaire en euros
    """
    return format_number(value, decimals, ' €')

def format_percentage(value: Union[int, float], decimals: int = 1) -> str:
    """
    Formate un pourcentage
    """
    return format_number(value, decimals, '%')

# Validation des données
def validate_chart_data(data: Any, required_fields: List[str] = None) -> bool:
    """
    Valide que les données nécessaires pour un graphique sont présentes
    """
    if data is None:
        return False
    
    if isinstance(data, pd.DataFrame):
        if data.empty:
            return False
        if required_fields:
            return all(field in data.columns for field in required_fields)
    
    elif isinstance(data, dict):
        if not data:
            return False
        if required_fields:
            return all(field in data for field in required_fields)
    
    return True

def apply_theme(fig: go.Figure) -> go.Figure:
    """
    Applique le thème standard à une figure Plotly
    """
    fig.update_layout(**PLOTLY_THEME['layout'])
    return fig

# Helpers pour annotations
def add_value_annotations(fig: go.Figure, trace_index: int = 0, 
                         format_func: callable = format_number, 
                         position: str = 'top') -> go.Figure:
    """
    Ajoute des annotations de valeurs sur un graphique
    """
    trace = fig.data[trace_index]
    
    if hasattr(trace, 'y') and trace.y is not None:
        for i, value in enumerate(trace.y):
            if not pd.isna(value):
                fig.add_annotation(
                    x=trace.x[i] if hasattr(trace, 'x') else i,
                    y=value,
                    text=format_func(value),
                    showarrow=False,
                    yshift=10 if position == 'top' else -10,
                    font=dict(size=10)
                )
    
    return fig

def create_metric_card(title: str, value: Union[str, int, float], 
                      delta: Optional[Union[str, int, float]] = None,
                      delta_color: str = 'normal') -> Dict[str, Any]:
    """
    Crée les données pour une carte métrique
    """
    card_data = {
        'title': title,
        'value': value if isinstance(value, str) else format_number(value),
        'delta': delta,
        'delta_color': delta_color
    }
    
    return card_data

# Gestion des erreurs
def handle_chart_error(error: Exception, chart_name: str) -> go.Figure:
    """
    Crée un graphique d'erreur avec message explicite
    """
    fig = go.Figure()
    fig.add_annotation(
        text=f"Erreur lors de la création du graphique {chart_name}<br>Détails: {str(error)}",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color=COLORS['danger'])
    )
    fig.update_layout(
        height=400,
        paper_bgcolor='rgba(255,240,240,0.5)'
    )
    return fig

# Export helpers
def prepare_chart_for_export(fig: go.Figure, title: str = None) -> go.Figure:
    """
    Prépare un graphique pour l'export (PDF/PNG)
    """
    export_fig = go.Figure(fig)
    
    # Fond blanc pour l'export
    export_fig.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    
    # Titre si fourni
    if title:
        export_fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16, 'family': 'Arial, sans-serif'}
            }
        )
    
    return export_fig

# Cache pour performances
@st.cache_data
def compute_heavy_calculation(data: pd.DataFrame, calculation_type: str) -> Any:
    """
    Cache les calculs lourds pour améliorer les performances
    """
    # Cette fonction sera étendue selon les besoins spécifiques
    pass

# Utilitaires de layout
def create_grid_layout(n_items: int, n_cols: int = 3) -> List[List[int]]:
    """
    Crée une disposition en grille pour organiser les éléments
    """
    n_rows = (n_items + n_cols - 1) // n_cols
    grid = []
    
    for row in range(n_rows):
        row_items = []
        for col in range(n_cols):
            idx = row * n_cols + col
            if idx < n_items:
                row_items.append(idx)
        grid.append(row_items)
    
    return grid

# Synchronisation des axes
def sync_y_axes(figs: List[go.Figure]) -> None:
    """
    Synchronise les axes Y de plusieurs graphiques
    """
    if not figs:
        return
    
    # Trouve les limites min/max communes
    y_min = float('inf')
    y_max = float('-inf')
    
    for fig in figs:
        for trace in fig.data:
            if hasattr(trace, 'y') and trace.y is not None:
                y_vals = [y for y in trace.y if not pd.isna(y)]
                if y_vals:
                    y_min = min(y_min, min(y_vals))
                    y_max = max(y_max, max(y_vals))
    
    # Applique les limites communes
    for fig in figs:
        fig.update_yaxes(range=[y_min * 0.95, y_max * 1.05])

# Messages user-friendly
def get_user_friendly_message(error_type: str) -> str:
    """
    Retourne un message d'erreur user-friendly selon le type d'erreur
    """
    messages = {
        'no_data': "Aucune donnée disponible pour afficher ce graphique.",
        'missing_fields': "Certaines données requises sont manquantes.",
        'calculation_error': "Une erreur s'est produite lors du calcul.",
        'invalid_format': "Le format des données n'est pas valide.",
        'permission_denied': "Vous n'avez pas les permissions pour voir ces données.",
        'default': "Une erreur inattendue s'est produite."
    }
    
    return messages.get(error_type, messages['default'])

# Génération de données de test
def generate_test_data(data_type: str, n_points: int = 12) -> pd.DataFrame:
    """
    Génère des données de test pour le développement/démo
    """
    if data_type == 'time_series':
        dates = pd.date_range(start='2024-01-01', periods=n_points, freq='M')
        values = np.random.randint(1000, 5000, n_points)
        return pd.DataFrame({'date': dates, 'value': values})
    
    elif data_type == 'categories':
        categories = [f'Cat_{i}' for i in range(n_points)]
        values = np.random.randint(100, 1000, n_points)
        return pd.DataFrame({'category': categories, 'value': values})
    
    else:
        return pd.DataFrame()