"""
Module de facturation PMO pour OptimPV
Gestion de la facturation d'autoconsommation collective photovoltaïque
"""

from .main import show_facturation_page
from .database import BillingDatabase
from .models import Project, Participant, Invoice
from .invoice_generator import InvoiceGenerator
from .email_sender import EmailSender

__version__ = "1.0.0"
__author__ = "OptimPV Team"

def get_module_info():
    """Retourne les informations du module"""
    return {
        "name": "Facturation PMO",
        "version": __version__,
        "description": "Module de facturation pour l'autoconsommation collective",
        "icon": "💰",
        "author": __author__,
        "dependencies": [
            "streamlit",
            "pandas", 
            "numpy",
            "reportlab (optionnel pour PDF)"
        ]
    }

# Export des fonctions principales
__all__ = [
    'show_facturation_page',
    'get_module_info',
    'BillingDatabase',
    'Project',
    'Participant', 
    'Invoice',
    'InvoiceGenerator',
    'EmailSender'
]