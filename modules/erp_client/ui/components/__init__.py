"""Composants UI réutilisables pour le module ERP client."""

from .address_autocomplete_widget import (
    render_address_autocomplete,
    render_simple_address_search
)

__all__ = [
    'render_address_autocomplete',
    'render_simple_address_search'
]