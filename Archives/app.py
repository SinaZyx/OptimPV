import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import base64
from modules.config import ConfigModule
from modules.data_import import DataImportModule
from modules.economic_analysis import EconomicAnalysisModule
from modules.optimization import OptimizationModule
from modules.visualization import VisualizationModule
from modules.reporting import ReportingModule
from modules.storage import StorageModule

# Configuration de la page Streamlit
st.set_page_config(
    page_title="OptimPV - Optimisation de l'Autoconsommation Collective",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fonction pour charger le CSS
def load_css():
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            color: #1E88E5;
            text-align: center;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.5rem;
            color: #424242;
            margin-bottom: 1rem;
        }
        .card {
            background-color: #f9f9f9;
            padding: 1rem;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        .info-box {
            background-color: #e3f2fd;
            padding: 1rem;
            border-radius: 5px;
            border-left: 5px solid #1E88E5;
            margin-bottom: 1rem;
        }
        .success-box {
            background-color: #e8f5e9;
            padding: 1rem;
            border-radius: 5px;
            border-left: 5px solid #4CAF50;
            margin-bottom: 1rem;
        }
        .warning-box {
            background-color: #fff8e1;
            padding: 1rem;
            border-radius: 5px;
            border-left: 5px solid #FFC107;
            margin-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

# Initialisation des modules et de la session
def initialize_session():
    """Initialise les variables de session lors du premier lancement de l'application"""
    
    # Vérifier si la configuration existe, sinon la créer
    if 'config' not in st.session_state:
        st.session_state.config = {
            'project_name': 'Projet PV',
            'capex': 85000,  # Coût initial de l'installation en €
            'opex': 200,    # Coût annuel d'exploitation en €
            'degradation_rate': 0.5,  # Taux de dégradation annuelle en %
            'debt_ratio': 80,         # Part de dette dans le financement en %
            'debt_term_years': 15,    # Durée du prêt en années
            'debt_rate': 4.5,         # Taux d'intérêt annuel en %
            'taux_imposition': 25,    # Taux d'imposition en %
            'taux_inflation': 2,      # Taux d'inflation annuel en %
            'prix_vente_initial': 0.12,  # Prix de vente initial du kWh en €
            'date_debut_ppa': datetime.now().isoformat(),  # Date de début du contrat PPA
            'duree_ppa': 240,         # Durée du contrat PPA en mois
            'prix_achat_reseau': 0.2015,  # Prix d'achat du réseau en €/kWh
            'cout_fonds_propres': 0,  # Coût des fonds propres en %
            'target_dscr': 1.2        # DSCR cible (Debt Service Coverage Ratio)
        }
    
    # Initialiser le mapping de colonnes s'il n'existe pas
    if 'column_mapping' not in st.session_state:
        st.session_state.column_mapping = {
            'date': 'Temps',
            'production': 'Énergie PV (CA) déduction faite de la consommation en veille',
            'consumption': 'Consommation'
        }
    
    # Initialisation des clés de session si elles n'existent pas
    if 'config_module' not in st.session_state:
        st.session_state.config_module = ConfigModule()
    
    if 'data_import_module' not in st.session_state:
        st.session_state.data_import_module = DataImportModule()
    
    if 'economic_analysis_module' not in st.session_state:
        st.session_state.economic_analysis_module = EconomicAnalysisModule()
    
    if 'optimization_module' not in st.session_state:
        st.session_state.optimization_module = OptimizationModule()
    
    if 'visualization_module' not in st.session_state:
        st.session_state.visualization_module = VisualizationModule()
    
    if 'reporting_module' not in st.session_state:
        st.session_state.reporting_module = ReportingModule()
    
    if 'storage_module' not in st.session_state:
        st.session_state.storage_module = StorageModule()
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Accueil"
    
    if 'data_imported' not in st.session_state:
        st.session_state.data_imported = False
    
    if 'optimization_completed' not in st.session_state:
        st.session_state.optimization_completed = False

# Interface principale
def main():
    # Charger le CSS
    load_css()
    
    # Initialiser la session
    initialize_session()
    
    # Barre latérale pour la navigation
    with st.sidebar:
        st.markdown("<h2 style='text-align: center;'>OptimPV</h2>", unsafe_allow_html=True)
        st.image("https://via.placeholder.com/150x150.png?text=OptimPV", width=150)
        
        st.header("Navigation")
        
        # Options de navigation
        pages = {
            "Accueil": "🏠",
            "Configuration": "⚙️",
            "Importation Données": "📊",
            "Analyse Économique": "💰",
            "Optimisation": "🎯",
            "Visualisation": "📈",
            "Rapports": "📑",
            "Historique": "📁"
        }
        
        for page, icon in pages.items():
            # Ajouter des conditions pour activer/désactiver certaines pages
            disabled = False
            if page in ["Analyse Économique", "Optimisation", "Visualisation", "Rapports"] and not st.session_state.data_imported:
                disabled = True
            
            if not disabled:
                if st.button(f"{icon} {page}", key=f"nav_{page}"):
                    st.session_state.current_page = page
            else:
                st.button(f"{icon} {page}", key=f"nav_{page}", disabled=True)
        
        st.markdown("---")
        st.markdown("### État du Projet")
        
        # Afficher l'état du projet
        if st.session_state.data_imported:
            st.success("✅ Données importées")
        else:
            st.warning("❌ Données non importées")
        
        if st.session_state.optimization_completed:
            st.success("✅ Optimisation terminée")
        else:
            st.warning("❌ Optimisation non terminée")
    
    # Contenu principal
    if st.session_state.current_page == "Accueil":
        show_home_page()
    elif st.session_state.current_page == "Configuration":
        st.session_state.config_module.show_ui()
    elif st.session_state.current_page == "Importation Données":
        st.session_state.data_import_module.show_ui()
    elif st.session_state.current_page == "Analyse Économique":
        st.session_state.economic_analysis_module.show_ui()
    elif st.session_state.current_page == "Optimisation":
        st.session_state.optimization_module.show_ui()
    elif st.session_state.current_page == "Visualisation":
        st.session_state.visualization_module.show_ui()
    elif st.session_state.current_page == "Rapports":
        st.session_state.reporting_module.show_ui()
    elif st.session_state.current_page == "Historique":
        st.session_state.storage_module.show_ui()

# Page d'accueil
def show_home_page():
    st.markdown("<h1 class='main-header'>OptimPV - Optimisation de l'Autoconsommation Collective</h1>", unsafe_allow_html=True)
    
    st.markdown("<div class='info-box'>", unsafe_allow_html=True)
    st.markdown("""
    Bienvenue dans l'application OptimPV, conçue pour optimiser l'autoconsommation collective de sites photovoltaïques.
    Cette application vous permet de déterminer le prix de revente optimal de l'électricité excédentaire à des acheteurs locaux,
    tout en garantissant la rentabilité de votre projet sur 20 à 25 ans.
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Présentation des fonctionnalités principales
    st.markdown("<h2 class='sub-header'>Fonctionnalités Principales</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### 📊 Analyse des données PV*SOL")
        st.markdown("""
        - Import automatique des fichiers CSV/Excel de PV*SOL
        - Analyse de la production et de la consommation
        - Calcul du taux d'autoconsommation
        """)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### 💰 Analyse Économique")
        st.markdown("""
        - Configuration des hypothèses financières
        - Calcul des indicateurs : DSCR, ROI, TRI, VAN
        - Simulation de différents scénarios économiques
        """)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### 🎯 Optimisation du Prix de Revente")
        st.markdown("""
        - Simulation Monte Carlo de la variabilité production/consommation
        - Détermination du prix optimal de revente (€/kWh)
        - Respect des contraintes de compétitivité et rentabilité
        """)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### 📈 Visualisation et Rapports")
        st.markdown("""
        - Graphiques interactifs des résultats
        - Génération de rapports détaillés
        - Sauvegarde et comparaison historique des projets
        """)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Guide de démarrage rapide
    st.markdown("<h2 class='sub-header'>Guide de Démarrage Rapide</h2>", unsafe_allow_html=True)
    
    st.markdown("<div class='success-box'>", unsafe_allow_html=True)
    st.markdown("""
    1. **Configuration** : Définissez les hypothèses économiques et techniques du projet
    2. **Importation** : Chargez les données exportées depuis PV*SOL
    3. **Analyse** : Explorez les différents scénarios économiques
    4. **Optimisation** : Déterminez le prix de revente optimal
    5. **Rapports** : Générez des rapports détaillés pour la prise de décision
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Pied de page
    st.markdown("---")
    st.markdown("<p style='text-align: center;'>© 2023 OptimPV - Tous droits réservés</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()