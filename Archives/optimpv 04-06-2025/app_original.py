import streamlit as st

# This should be the FIRST Streamlit command
st.set_page_config(
    page_title="OptimPV - Optimisation Autoconsommation",
    page_icon="☀️", layout="wide", initial_sidebar_state="expanded"
)

import pandas as pd
import numpy as np
import os
import sys
import json
import hashlib
import time
from datetime import datetime

# Ajouter le chemin du dossier 'modules' au path Python
# (Cette partie est conservée et est correcte)
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'modules'))
if module_path not in sys.path:
    sys.path.append(module_path)

# --- Imports des Modules ---
# Garder les imports existants car vous préférez en avoir plus
from modules.config import ConfigModule
from modules.data_import import DataImportModule
# Mise à jour de l'import du module de visualisation
try:
    from modules.visualization.main_visualization_ui import VisualizationModule  # type: ignore
except ImportError as e:
    print(f"ERREUR APP: Impossible d'importer VisualizationModule depuis son nouvel emplacement: {e}")
    # Définir une classe factice pour éviter que l'app ne crashe complètement
    class VisualizationModule:
        def __init__(self, *args, **kwargs): pass
        def show_ui(self, *args, **kwargs):
            st.error(f"Le module d'interface utilisateur pour 'Visualisation' "
                     f"(attendu dans `modules/visualization/main_visualization_ui.py`) "
                     f"est manquant ou contient une erreur.\nErreur: {e}")
            st.warning("Veuillez vérifier la structure de vos fichiers et les imports.")
from modules.reporting import ReportingModule
from modules.storage import StorageModule
from modules.engine_module.core_analyzer import AnalysisEngine 

# NOUVEAU : Importer la fonction UI principale de la nouvelle structure
try:
    from modules.optimisation_analyse.ui_page import display_analysis_optimisation_section
except ImportError as e:
    # Gérer le cas où le module UI n'est pas encore créé ou trouvé
    # On définit une fonction placeholder pour éviter que l'app crashe
    print(f"ERREUR APP: Impossible d'importer l'UI d'analyse/optimisation: {e}")
    def display_analysis_optimisation_section(scenario_name):
        st.error("Le module d'interface utilisateur pour 'Analyse & Optimisation' "
                 f"(attendu dans `modules/optimisation_analyse/ui_page.py`) est manquant ou contient une erreur.\n"
                 f"Erreur: {e}")
        st.warning("Veuillez créer/corriger ce fichier.")

# --- Gestion de l'Authentification ---
def get_password_file_path():
    """Retourne le chemin du fichier de mot de passe dans AppData"""
    appdata_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'OptimPV')
    return os.path.join(appdata_dir, "config", "panel_password.json")

def hash_password(password):
    """Hash un mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_panel_password():
    """Charge le mot de passe du panneau depuis le fichier de configuration"""
    password_file = get_password_file_path()
    
    # Créer le dossier config s'il n'existe pas
    os.makedirs(os.path.dirname(password_file), exist_ok=True)
    
    # Si le fichier n'existe pas, créer avec le mot de passe par défaut
    if not os.path.exists(password_file):
        default_password = "panel123"
        password_data = {
            "password_hash": hash_password(default_password),
            "created_date": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat()
        }
        with open(password_file, 'w') as f:
            json.dump(password_data, f, indent=2)
        return password_data["password_hash"]
    
    # Charger le mot de passe existant
    try:
        with open(password_file, 'r') as f:
            password_data = json.load(f)
        return password_data.get("password_hash", hash_password("panel123"))
    except:
        # En cas d'erreur, retourner le hash du mot de passe par défaut
        return hash_password("panel123")

def save_panel_password(new_password):
    """Sauvegarde un nouveau mot de passe pour le panneau"""
    password_file = get_password_file_path()
    
    password_data = {
        "password_hash": hash_password(new_password),
        "created_date": datetime.now().isoformat() if not os.path.exists(password_file) else None,
        "last_modified": datetime.now().isoformat()
    }
    
    # Si le fichier existe, conserver la date de création
    if os.path.exists(password_file):
        try:
            with open(password_file, 'r') as f:
                existing_data = json.load(f)
            password_data["created_date"] = existing_data.get("created_date", datetime.now().isoformat())
        except:
            password_data["created_date"] = datetime.now().isoformat()
    
    with open(password_file, 'w') as f:
        json.dump(password_data, f, indent=2)

def show_password_change_interface():
    """Interface pour changer le mot de passe du panneau (à utiliser dans l'admin)"""
    st.subheader("🔐 Gestion du Mot de Passe OptimPV")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info("Modifiez le mot de passe d'accès au panneau OptimPV principal.")
        
        current_password = st.text_input("Mot de passe actuel :", type="password", key="current_panel_pwd")
        new_password = st.text_input("Nouveau mot de passe :", type="password", key="new_panel_pwd")
        confirm_password = st.text_input("Confirmer le nouveau mot de passe :", type="password", key="confirm_panel_pwd")
        
        if st.button("🔄 Changer le Mot de Passe", type="primary"):
            if not all([current_password, new_password, confirm_password]):
                st.error("❌ Veuillez remplir tous les champs.")
            elif new_password != confirm_password:
                st.error("❌ Les nouveaux mots de passe ne correspondent pas.")
            elif len(new_password) < 6:
                st.error("❌ Le nouveau mot de passe doit contenir au moins 6 caractères.")
            else:
                # Vérifier le mot de passe actuel
                stored_hash = load_panel_password()
                current_hash = hash_password(current_password)
                
                if current_hash == stored_hash:
                    # Sauvegarder le nouveau mot de passe
                    save_panel_password(new_password)
                    st.success("✅ Mot de passe modifié avec succès !")
                    st.info("Le nouveau mot de passe sera effectif lors de la prochaine connexion.")
                else:
                    st.error("❌ Mot de passe actuel incorrect.")
    
    with col2:
        st.markdown("### ℹ️ Informations")
        st.caption("**Mot de passe par défaut :** `panel123`")
        st.caption("**Longueur minimale :** 6 caractères")
        st.caption("**Stockage :** Hash SHA-256 sécurisé")
        
        # Afficher la date de dernière modification
        try:
            password_file = get_password_file_path()
            if os.path.exists(password_file):
                with open(password_file, 'r') as f:
                    password_data = json.load(f)
                last_modified = password_data.get("last_modified", "Inconnue")
                if last_modified != "Inconnue":
                    last_modified = datetime.fromisoformat(last_modified).strftime("%d/%m/%Y %H:%M")
                st.caption(f"**Dernière modification :** {last_modified}")
        except:
            st.caption("**Dernière modification :** Inconnue")

def check_panel_authentication():
    """Vérifie l'authentification pour accéder au panneau OptimPV"""
    if 'panel_authenticated' not in st.session_state:
        st.session_state.panel_authenticated = False
    
    if not st.session_state.panel_authenticated:
        st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🔐 OptimPV - Accès Sécurisé</h1>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### Authentification Requise")
            st.info("Veuillez saisir le mot de passe pour accéder au panneau OptimPV.")
            
            password_input = st.text_input("Mot de passe :", type="password", key="panel_password_input")
            
            if st.button("🔓 Se Connecter", type="primary", use_container_width=True):
                if password_input:
                    stored_hash = load_panel_password()
                    input_hash = hash_password(password_input)
                    
                    if input_hash == stored_hash:
                        st.session_state.panel_authenticated = True
                        st.success("✅ Authentification réussie !")
                        st.info("🔄 Redirection vers OptimPV...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Mot de passe incorrect !")
                else:
                    st.warning("⚠️ Veuillez saisir un mot de passe.")
        
        return False
    
    return True

# --- CSS (Conservé) ---
def load_css():
    # ... (votre code CSS inchangé) ...
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem; color: #1E88E5; text-align: center; margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.5rem; color: #424242; margin-bottom: 1rem;
        }
        /* ... (autres styles CSS) ... */
         .card {
             background-color: #f9f9f9; padding: 1rem; border-radius: 5px;
             box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 1rem;
         }
         .info-box {
             background-color: #e3f2fd; padding: 1rem; border-radius: 5px;
             border-left: 5px solid #1E88E5; margin-bottom: 1rem;
         }
         .success-box {
             background-color: #e8f5e9; padding: 1rem; border-radius: 5px;
             border-left: 5px solid #4CAF50; margin-bottom: 1rem;
         }
         .warning-box {
             background-color: #fff8e1; padding: 1rem; border-radius: 5px;
             border-left: 5px solid #FFC107; margin-bottom: 1rem;
         }
    </style>
    """, unsafe_allow_html=True)

# --- Initialisation Session (Modifiée) ---
def initialize_session():
    """Initialise l'état de la session Streamlit si nécessaire."""
    # Instancier les modules qui gèrent leur propre UI ou état globalement
    if 'config_module' not in st.session_state:
        st.session_state.config_module = ConfigModule()
    if 'data_import_module' not in st.session_state:
        st.session_state.data_import_module = DataImportModule()
    if 'visualization_module' not in st.session_state:
        st.session_state.visualization_module = VisualizationModule()
    if 'reporting_module' not in st.session_state:
        st.session_state.reporting_module = ReportingModule()
    if 'storage_module' not in st.session_state:
        st.session_state.storage_module = StorageModule()

    # !! SUPPRIMÉ : L'instanciation de AnalysisModule/AnalysisEngine se fait maintenant
    #    dans la fonction UI dédiée (ui_page.py) pour assurer que les dernières 
    #    données/config sont utilisées au moment de l'appel.
    # if 'analysis_module' not in st.session_state:
    #    # Ancienne initialisation - à supprimer ou commenter
    #    # st.session_state.analysis_module = AnalysisModule() # ANCIEN NOM
    #    pass 

    # Initialiser les états de base (conservé)
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Accueil"
    if 'data_imported' not in st.session_state:
        st.session_state.data_imported = False
    if 'analysis_run' not in st.session_state: # Gardé pour l'état sidebar
        st.session_state.analysis_run = False
        
    # Assurer l'existence des clés de résultats (conservé)
    if 'economic_results' not in st.session_state: st.session_state.economic_results = {}
    if 'optimization_results' not in st.session_state: st.session_state.optimization_results = {}
    if 'monte_carlo_results' not in st.session_state: st.session_state.monte_carlo_results = {}
    if 'floor_price_results' not in st.session_state: st.session_state.floor_price_results = {} # Ajouté au cas où

# --- Fonction Principale (Modifiée) ---
def main():
    # Configuration de la page (conservé)
    # st.set_page_config(
    #     page_title="OptimPV - Optimisation Autoconsommation", # Titre légèrement raccourci
    #     page_icon="☀️", layout="wide", initial_sidebar_state="expanded"
    # )
    
    load_css()
    initialize_session()
    
    # Vérification de l'authentification AVANT d'afficher l'interface
    if not check_panel_authentication():
        return  # Arrêter l'exécution si pas authentifié
    
    # Barre latérale (conservée)
    with st.sidebar:
        # ... (votre code sidebar inchangé : titre, image, navigation, état projet) ...
        st.markdown("<h2 style='text-align: center;'>OptimPV</h2>", unsafe_allow_html=True)
        # Utilisez une image locale ou gardez le placeholder
        try: 
            st.image("assets/logo.png", width=150) # Exemple chemin local
        except: 
            st.image("https://via.placeholder.com/150x150.png?text=OptimPV", width=150)
        
        st.header("Navigation")
        pages = {
             "Accueil": "🏠",
             "Importation Données": "📊",
             "Configuration": "⚙️",
             "Analyse & Optimisation": "💡", # Icône changée
             "Visualisation": "📈", "Rapports": "📑", "Historique": "📁"
        }
        
        for page, icon in pages.items():
             disabled = False
             if page in ["Analyse & Optimisation", "Visualisation", "Rapports"] and not st.session_state.get('data_imported', False):
                 disabled = True
             
             # Utiliser st.session_state.current_page pour déterminer le bouton actif (style)
             button_type = "primary" if st.session_state.current_page == page else "secondary"
             
             if st.button(f"{icon} {page}", key=f"nav_{page}", disabled=disabled, type=button_type, use_container_width=True):
                 st.session_state.current_page = page
                 st.rerun() # Force le rechargement pour afficher la bonne page

        st.markdown("---")
        st.markdown("### État du Projet")
        if st.session_state.get('data_imported', False): st.success("✅ Données importées")
        else: st.warning("❌ Données non importées")
        # Peut-être utiliser la présence de résultats pour analysis_run ?
        # Remplacer l'ancienne vérification par la nouvelle basée sur le flag dédié
        # analysis_done = bool(st.session_state.get('economic_results') or st.session_state.get('optimisation_results'))
        analysis_done = st.session_state.get('analyse_optimisation_terminee', False)
        if analysis_done: st.success("✅ Analyse effectuée")
        else: st.warning("❌ Analyse non effectuée")
        
        # DÉBUT CODE DÉBOGAGE CAPEX_MODIFIER
        st.markdown("---")
        st.markdown("### 🔍 DEBUG Scénarios")
        if "scenarios" in st.session_state and "Base" in st.session_state.scenarios:
            capex_mod_actuel = st.session_state.scenarios["Base"].get("capex_modifier", "non défini")
            st.warning(f"capex_modifier Base = {capex_mod_actuel}")
            if capex_mod_actuel != 0.0:
                st.error("⚠️ Valeur incorrecte! Devrait être 0.0")
        else:
            st.error("Scénarios non initialisés!")
            
        if st.button("Réinitialiser Scénarios", type="primary"):
            if "scenarios" in st.session_state:
                del st.session_state.scenarios
            # Réinitialiser avec la version du fichier
            config_module = ConfigModule()
            config_module.initialize_default_scenarios()
            st.success(f"Scénarios réinitialisés! capex_modifier Base = {st.session_state.scenarios['Base'].get('capex_modifier')}")
            st.rerun()
        # FIN CODE DÉBOGAGE CAPEX_MODIFIER
        
        st.markdown("---")
        st.markdown("<p style='text-align: center; font-size: 0.8em;'>© 2024-2025</p>", unsafe_allow_html=True)

    # --- Contenu Principal (Navigation Modifiée) ---
    
    # Afficher la page actuelle
    current_page = st.session_state.current_page
    
    if current_page == "Accueil":
        # Le titre est maintenant géré par la fonction show_home_page si vous préférez
        show_home_page()
    elif current_page == "Configuration":
        st.session_state.config_module.show_ui()
    elif current_page == "Importation Données":
        st.session_state.data_import_module.show_ui()
        
    elif current_page == "Analyse & Optimisation":
        # Vérifier si les données sont importées avant d'afficher
        if st.session_state.get('data_imported', False):
            # --- NOUVEAU : Sélection Scénario + Appel UI Page ---
            st.markdown("<h1 class='main-header'>Analyse & Optimisation</h1>", unsafe_allow_html=True) # Garder un titre principal
            
            # Sélection du scénario ici, dans l'application principale
            if 'scenarios' in st.session_state and st.session_state.scenarios:
                available_scenarios = list(st.session_state.scenarios.keys())
                # Utiliser une clé unique pour ce selectbox dans app.py
                scenario_choisi = st.selectbox(
                    "Choisissez le scénario à analyser :", 
                    options=available_scenarios,
                    key="app_scenario_selector" 
                )
                
                if scenario_choisi:
                    # Appel de la fonction UI dédiée du nouveau module
                    # Elle gère tout l'affichage et les interactions de cette section
                    display_analysis_optimisation_section(scenario_choisi) 
                else:
                    st.warning("Aucun scénario sélectionné ou disponible.")
            else:
                st.warning("Aucun scénario défini. Veuillez aller à la page Configuration.")
            # --- FIN NOUVEAU ---
        else:
            st.warning("Veuillez importer des données avant d'accéder à cette section.")
            
    elif current_page == "Visualisation":
        if st.session_state.get('data_imported', False):
            st.session_state.visualization_module.show_ui()
        else:
            st.warning("Veuillez importer des données avant d'accéder à cette section.")
    elif current_page == "Rapports":
        if st.session_state.get('data_imported', False):
            st.session_state.reporting_module.show_ui()
        else:
            st.warning("Veuillez importer des données avant d'accéder à cette section.")
    elif current_page == "Historique":
        st.session_state.storage_module.show_ui()

# --- Page d'accueil (Conservée) ---
def show_home_page():
    # ... (votre code show_home_page inchangé) ...
    st.markdown("<h1 class='main-header'>OptimPV - Optimisation de l'Autoconsommation Collective</h1>", unsafe_allow_html=True)
    st.markdown("<div class='info-box'>", unsafe_allow_html=True)
    st.markdown("""
    Bienvenue dans l'application OptimPV, conçue pour optimiser l'autoconsommation collective de sites photovoltaïques. 
    Cette application vous permet de déterminer le prix de revente optimal de l'électricité excédentaire à des acheteurs locaux, 
    tout en garantissant la rentabilité de votre projet sur 20 à 25 ans.
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<h2 class='sub-header'>Fonctionnalités Principales</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### 📊 Analyse des données PV*SOL")
        st.markdown("- Import automatique des fichiers CSV/Excel\n- Analyse production/consommation\n- Calcul taux d'autoconsommation")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### 💰 Analyse Économique")
        st.markdown("- Configuration des hypothèses\n- Calcul indicateurs : DSCR, ROI, TRI, VAN\n- Simulation de scénarios")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### 💡 Analyse & Optimisation") # Mise à jour nom
        st.markdown("- Optimisation multi-critères du prix\n- Analyse de sensibilité & robustesse (Monte Carlo)\n- Visualisation interactive des compromis")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### 📈 Visualisation & Rapports")
        st.markdown("- Graphiques avancés\n- Génération de rapports PDF/Excel\n- Sauvegarde et historique des projets")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<h2 class='sub-header'>Guide de Démarrage Rapide</h2>", unsafe_allow_html=True)
    st.markdown("<div class='success-box'>", unsafe_allow_html=True)
    st.markdown("""
    1.  **Configuration** : Définissez les hypothèses économiques et techniques.
    2.  **Importation** : Chargez vos données de production et consommation.
    3.  **Analyse & Optimisation** : Lancez les calculs, trouvez le prix optimal et explorez les résultats.
    4.  **Visualisation** : Affinez votre compréhension avec les graphiques dédiés.
    5.  **Rapports** : Exportez vos conclusions.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

# --- Point d'Entrée ---
if __name__ == "__main__":
    main()