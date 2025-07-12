import streamlit as st
import sys
import os

# Ajouter le chemin du dossier parent pour l'import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules import reporting as reporting_module

# Instancie le module de reporting
report = reporting_module.ReportingModule()

# Simule les données nécessaires dans st.session_state
st.session_state['data_imported'] = True
st.session_state['constrained_optim_results'] = {
    'Scénario Test': {
        'indicateurs_au_prix_optimal': {
            'npv_project': 100000,
            'irr_project': 0.12,
            'npv': 80000,
            'irr': 0.15,
            'lcoe': 0.085,
            'payback_project': 8,
            'payback_period': 6,
            'avg_dscr': 1.3,
            'monthly_data': None
        },
        'prix_optimal_const': 0.13
    }
}
st.session_state['config'] = {
    'nom_projet': 'Projet Démo',
    'localisation': 'Paris',
    'date_debut_ppa': '2024-01-01',
    'duree_ppa': 240,
    'tarif_edf_reference': 0.20,
    'taux_inflation': 0.02,
    'capex': 120000,
    'puissance_kwc': 50
}

# Génère le rapport HTML
html = report.generate_html_report(
    title="Aperçu Rapport Test",
    client_name="Client Test",
    project_name="Projet Démo"
)

# Affiche l'aperçu dans Streamlit
st.components.v1.html(html, height=900, scrolling=True) 