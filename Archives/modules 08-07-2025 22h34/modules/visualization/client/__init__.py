"""
Module client pour les visualisations orientees client
"""
from .economics import (
    create_price_comparison_chart,
    create_annual_savings_chart,
    create_cumulative_savings_chart,
    create_facture_comparison_chart
)
from .energy import create_energy_distribution_pie

# Imports pour compatibilite avec l'ancien systeme
from ..client_charts import *

__all__ = [
    'create_price_comparison_chart',
    'create_annual_savings_chart', 
    'create_cumulative_savings_chart',
    'create_facture_comparison_chart',
    'create_energy_distribution_pie'
]