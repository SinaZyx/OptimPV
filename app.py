import streamlit as st
import os
import sys
import pandas as pd
import numpy as np
import json
import hashlib
import time
import subprocess
import socket
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="OptimPV - Optimisation Autoconsommation", 
    page_icon="☀️", layout="wide", initial_sidebar_state="expanded"
)

# CSS pour masquer le menu hamburger (3 points)
hide_menu_style = """
<style>
    #MainMenu {visibility: hidden;}
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    #stDecoration {display:none;}
</style>
"""
# st.markdown(hide_menu_style, unsafe_allow_html=True)  # Temporairement désactivé pour accéder au clear cache


# Ajouter le chemin du dossier 'modules' au path Python
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'modules'))
if module_path not in sys.path:
    sys.path.append(module_path)

# --- Imports des Modules ---
from modules.config import ConfigModule
from modules.data_import import DataImportModule

# Import du module de sécurité
try:
    from modules.security_config import get_default_password_hash
except ImportError:
    # Fallback en cas d'erreur
    def get_default_password_hash():
        import hashlib
        return hashlib.sha256("panel123".encode()).hexdigest()

# Import du module de visualisation moderne avec toutes les fonctionnalités
try:
    # Forcer l'utilisation de l'interface moderne avec toutes les fonctionnalités
    from modules.visualization import (
        ModernVisualizationUI, 
        MODERN_UI_AVAILABLE,
        create_visualization_interface
    )
    
    if MODERN_UI_AVAILABLE:
        print("✅ Interface de visualisation moderne chargée avec succès")
        print("   - Thèmes personnalisables activés")
        print("   - Graphiques interactifs disponibles")
        print("   - Dashboard personnalisable prêt")
        # Créer l'interface moderne avec toutes les fonctionnalités
        VisualizationModule = ModernVisualizationUI
    else:
        # Fallback vers l'ancienne interface
        print("⚠️ Interface moderne non disponible, chargement de l'interface classique")
        from modules.visualization.main_visualization_ui import VisualizationModule
        
except ImportError as e:
    print(f"ERREUR APP: Impossible d'importer le module de visualisation: {e}")
    # Fallback complet si aucune interface n'est disponible
    try:
        from modules.visualization.main_visualization_ui import VisualizationModule
        print("✅ Interface classique chargée en mode de secours")
    except ImportError:
        print("❌ Aucune interface de visualisation disponible")
        class VisualizationModule:
            def __init__(self, *args, **kwargs): 
                self.error_message = str(e)
            def show_ui(self, *args, **kwargs):
                st.error(f"Le module d'interface utilisateur pour 'Visualisation' "
                         f"est manquant ou contient une erreur.\nErreur: {self.error_message}")
                st.warning("Veuillez vérifier la structure de vos fichiers et les imports.")

from modules.reporting import ReportingModule
from modules.storage import StorageModule
from modules.engine_module.core_analyzer import AnalysisEngine 

# Import de l'analyse et optimisation
try:
    from modules.optimisation_analyse.ui_page import display_analysis_optimisation_section
except ImportError as e:
    print(f"ERREUR APP: Impossible d'importer l'UI d'analyse/optimisation: {e}")
    error_msg = str(e)  # Capturer le message d'erreur
    def display_analysis_optimisation_section(scenario_name):
        st.error("Le module d'interface utilisateur pour 'Analyse & Optimisation' "
                 f"(attendu dans `modules/optimisation_analyse/ui_page.py`) est manquant ou contient une erreur.\n"
                 f"Erreur: {error_msg}")
        st.warning("Veuillez créer/corriger ce fichier.")

# Import du module de cartographie de prospection (VERSION RÉORGANISÉE)
try:
    # Essayer l'import via __init__.py d'abord
    from modules.prospect_mapping import render_ui as show_prospect_map_ui, get_module_info
    if show_prospect_map_ui is None:
        raise ImportError("render_ui est None")
        
    # Afficher les informations de version au démarrage
    module_info = get_module_info()
    print(f"✅ Module Prospect Mapping chargé - Version {module_info['version']}")
    print(f"   Mode amélioré: {'✅ Activé' if module_info['enhanced'] else '❌ Standard'}")
    if module_info['enhanced']:
        print("   Nouvelles fonctionnalités: proximité Mougins, enrichissement à la demande")
        
except (ImportError, AttributeError) as e:
    print(f"AVERTISSEMENT: Import via __init__.py échoué: {e}")
    print("Tentative d'import direct depuis ui.py...")
    
    try:
        # Import direct depuis le fichier ui.py (à la racine prospect_mapping)
        from modules.prospect_mapping.ui import show_prospect_map_ui
        from modules.prospect_mapping import get_module_info
        
        module_info = get_module_info()
        print(f"✅ Module Prospect Mapping chargé (import direct) - Version {module_info['version']}")
        print("   Optimisations: Mode proximité Mougins + enrichissement à la demande")
        
    except ImportError as e2:
        print(f"ERREUR APP: Impossible d'importer le module de prospection: {e2}")
        error_msg = str(e2)  # Capturer le message d'erreur
        def show_prospect_map_ui():
            st.error("Le module de cartographie de prospection "
                 f"(attendu dans `modules/prospect_mapping/`) est manquant ou contient une erreur.\n"
                 f"Erreur: {error_msg}")
            st.warning("Veuillez vérifier la structure de vos fichiers et les imports.")

# Import du module de facturation PMO
try:
    from modules.facturation import show_facturation_page, get_module_info as get_facturation_info
    
    # Afficher les informations de version au démarrage
    facturation_info = get_facturation_info()
    print(f"✅ Module Facturation PMO chargé - Version {facturation_info['version']}")
    print(f"   {facturation_info['description']}")
    
except ImportError as e:
    print(f"ERREUR APP: Impossible d'importer le module de facturation: {e}")
    error_msg = str(e)  # Capturer le message d'erreur
    def show_facturation_page():
        st.error("Le module de facturation PMO "
             f"(attendu dans `modules/facturation/`) est manquant ou contient une erreur.\n"
             f"Erreur: {error_msg}")
        st.warning("Veuillez vérifier la structure de vos fichiers et les imports.")

# Import du module ERP - Gestion Clients
try:
    from modules.erp_client import render_erp_module
    print("✅ Module ERP Clients chargé avec succès")
    print("   Gestion complète des clients avec tarification et autoconsommation collective")
    ERP_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Module ERP non disponible: {e}")
    ERP_MODULE_AVAILABLE = False
    def render_erp_module():
        st.error("Le module ERP n'est pas disponible. Veuillez vérifier l'installation.")
        st.info("Ce module permet la gestion complète des clients, des prix et de l'autoconsommation collective.")

# --- Gestion de l'Authentification ---
def get_password_file_path():
    """Retourne le chemin du fichier de mot de passe dans AppData"""
    if sys.platform == "win32":
        appdata_dir = os.path.join(os.environ.get('APPDATA'), 'OptimPV')
    else:
        appdata_dir = os.path.join(os.path.expanduser('~'), '.optimpv')
    return os.path.join(appdata_dir, "panel_password.hash")

def hash_password(password):
    """Hash un mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_panel_password():
    """Charge le mot de passe du panneau depuis le fichier de configuration"""
    password_file = get_password_file_path()
    
    # Créer le dossier config s'il n'existe pas
    os.makedirs(os.path.dirname(password_file), exist_ok=True)
    
    # Si le fichier n'existe pas, créer avec le mot de passe par défaut du module sécurisé
    if not os.path.exists(password_file):
        password_data = {
            "password_hash": get_default_password_hash(),
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
        return password_data.get("password_hash")
    except:
        # En cas d'erreur, retourner le hash du mot de passe par défaut
        return get_default_password_hash()

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
    """Interface pour changer le mot de passe du panneau"""
    st.subheader("🔐 Gestion du Mot de Passe OptimPV")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info("Modifiez le mot de passe d'accès au panneau OptimPV principal.")
        
        current_password = st.text_input("Mot de passe actuel :", type="password", key="current_panel_pwd")
        new_password = st.text_input("Nouveau mot de passe :", type="password", key="new_panel_pwd")
        confirm_password = st.text_input("Confirmer le nouveau mot de passe :", type="password", key="confirm_panel_pwd")
        
        if st.button("🔄 Changer le Mot de Passe", type="primary"):
            if current_password and new_password and confirm_password:
                # Vérifier le mot de passe actuel
                stored_hash = load_panel_password()
                current_hash = hash_password(current_password)
                
                if current_hash == stored_hash:
                    if new_password == confirm_password:
                        if len(new_password) >= 6:
                            save_panel_password(new_password)
                            st.success("✅ Mot de passe modifié avec succès !")
                            st.info("Le nouveau mot de passe sera effectif au prochain démarrage.")
                        else:
                            st.error("❌ Le nouveau mot de passe doit contenir au moins 6 caractères.")
                    else:
                        st.error("❌ Les nouveaux mots de passe ne correspondent pas.")
                else:
                    st.error("❌ Mot de passe actuel incorrect.")
            else:
                st.warning("⚠️ Veuillez remplir tous les champs.")

def check_panel_authentication():
    """Vérifie l'authentification du panneau"""
    if st.session_state.get('panel_authenticated', False):
        return True
    
    st.markdown("<h1 class='main-header'>🔐 Authentification OptimPV</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("### À propos d'OptimPV")
        st.info("""
        OptimPV est une solution complète d'optimisation de l'autoconsommation collective 
        qui vous aide à déterminer le prix optimal de revente de votre surplus 
        d'électricité photovoltaïque.
        
        **Fonctionnalités principales :**
        - Analyse financière complète (VAN, TRI, LCOE)
        - Optimisation du prix de vente
        - Simulation de flux de trésorerie
        - Cartographie de prospection
        - Rapports détaillés
        """)
    
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

# --- Contrôle du Serveur ---
def check_port_in_use(port):
    """Vérifie si un port est utilisé"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def show_server_control_page():
    """Interface de contrôle du serveur OptimPV"""
    st.markdown("<h1 class='main-header'>🖥️ Contrôle du Serveur OptimPV</h1>", unsafe_allow_html=True)
    
    # Vérifier l'état du serveur
    server_running = False
    current_port = None
    for port in range(8501, 8506):
        if check_port_in_use(port):
            server_running = True
            current_port = port
            break
    
    st.markdown("### État du Serveur")
    
    if server_running:
        st.success(f"✅ Serveur OptimPV actif sur le port {current_port}")
        st.info(f"URL: http://localhost:{current_port}")
    else:
        st.error("❌ Serveur OptimPV arrêté")
    
    st.markdown("### Actions")
    
    if st.button("🔴 Arrêter OptimPV", type="primary", use_container_width=True):
        # Méthode ultra-simple: juste tuer le processus
        import os
        import sys
        
        st.warning("⚠️ Arrêt d'OptimPV...")
        
        # Essayer plusieurs méthodes
        try:
            # Méthode 1: taskkill
            os.system("taskkill /f /im OptimPV*.exe")
            st.info("Commande d'arrêt envoyée")
        except:
            pass
        
        try:
            # Méthode 2: sys.exit direct
            sys.exit(0)
        except:
            pass
        
        try:
            # Méthode 3: os._exit (plus brutal)
            os._exit(0)
        except:
            st.error("Impossible d'arrêter automatiquement")
    
    st.markdown("---")
    st.info("""
    **Ports utilisés:** 8501-8505
    
    **Pour redémarrer:** Relancez l'executable OptimPV
    """)
    
    st.markdown("---")
    
    # Section de gestion du mot de passe
    with st.expander("🔐 Modifier le Mot de Passe d'Accès"):
        show_password_change_interface()

# --- CSS ---
def load_css():
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem; color: #1E88E5; text-align: center; margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.5rem; color: #424242; margin-bottom: 1rem;
        }
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

# --- Initialisation Session ---
def initialize_session():
    """Initialise l'état de la session Streamlit si nécessaire."""
    # Instancier les modules
    if 'config_module' not in st.session_state:
        st.session_state.config_module = ConfigModule()
    if 'data_import_module' not in st.session_state:
        st.session_state.data_import_module = DataImportModule()
    if 'visualization_module' not in st.session_state:
        # Créer le module de visualisation avec toutes les fonctionnalités
        try:
            # Essayer de créer l'interface moderne si disponible
            if MODERN_UI_AVAILABLE:
                # Vérifier si create_visualization_interface est disponible
                if 'create_visualization_interface' in globals():
                    st.session_state.visualization_module = create_visualization_interface(use_modern=True)
                    print("✅ Module de visualisation moderne initialisé avec create_visualization_interface")
                else:
                    # Créer directement l'interface moderne
                    st.session_state.visualization_module = ModernVisualizationUI()
                    print("✅ Module de visualisation moderne initialisé directement")
            else:
                st.session_state.visualization_module = VisualizationModule()
                print("✅ Module de visualisation classique initialisé")
        except Exception as e:
            print(f"Erreur lors de l'initialisation du module de visualisation: {e}")
            st.session_state.visualization_module = VisualizationModule()
    if 'reporting_module' not in st.session_state:
        st.session_state.reporting_module = ReportingModule()
    if 'storage_module' not in st.session_state:
        st.session_state.storage_module = StorageModule()

    # Initialiser les états de base
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Accueil"
    if 'data_imported' not in st.session_state:
        st.session_state.data_imported = False
    if 'analysis_run' not in st.session_state:
        st.session_state.analysis_run = False
        
    # Assurer l'existence des clés de résultats
    if 'economic_results' not in st.session_state: st.session_state.economic_results = {}
    if 'optimization_results' not in st.session_state: st.session_state.optimization_results = {}
    if 'monte_carlo_results' not in st.session_state: st.session_state.monte_carlo_results = {}
    if 'floor_price_results' not in st.session_state: st.session_state.floor_price_results = {}

# --- Fonction Principale ---
def main():
    load_css()
    initialize_session()
    
    # Vérification de l'authentification AVANT d'afficher l'interface
    if not check_panel_authentication():
        return
    
    # Barre latérale
    with st.sidebar:
        st.markdown("<h2 style='text-align: center;'>OptimPV</h2>", unsafe_allow_html=True)
        
        try: 
            st.image("assets/logo.png", width=150)
        except: 
            st.image("https://via.placeholder.com/150x150.png?text=OptimPV", width=150)
        
        st.header("Navigation")
        
        # Page d'accueil toujours visible
        if st.button(f"🏠 Accueil", key="nav_Accueil", 
                    type="primary" if st.session_state.current_page == "Accueil" else "secondary", 
                    use_container_width=True):
            st.session_state.current_page = "Accueil"
            st.rerun()
        
        # Catégorie: Données & Configuration
        with st.expander("📋 **Données & Configuration**", expanded=True):
            pages_data = {
                "Importation Données": "📊",
                "Configuration": "⚙️"
            }
            for page, icon in pages_data.items():
                button_type = "primary" if st.session_state.current_page == page else "secondary"
                if st.button(f"{icon} {page}", key=f"nav_{page}", type=button_type, use_container_width=True):
                    st.session_state.current_page = page
                    st.rerun()
        
        # Catégorie: Gestion Commerciale
        with st.expander("💼 **Gestion Commerciale**", expanded=True):
            pages_commercial = {
                "ERP Clients": "🏢",
                "Facturation PMO": "💰",
                "Carte de Prospection": "🗺️"
            }
            for page, icon in pages_commercial.items():
                button_type = "primary" if st.session_state.current_page == page else "secondary"
                if st.button(f"{icon} {page}", key=f"nav_{page}", type=button_type, use_container_width=True):
                    st.session_state.current_page = page
                    st.rerun()
        
        # Catégorie: Analyse & Résultats
        with st.expander("📊 **Analyse & Résultats**", expanded=True):
            pages_analysis = {
                "Analyse & Optimisation": "💡",
                "Visualisation": "📈",
                "Rapports": "📑"
            }
            data_imported = st.session_state.get('data_imported', False)
            for page, icon in pages_analysis.items():
                disabled = not data_imported
                button_type = "primary" if st.session_state.current_page == page else "secondary"
                
                if disabled:
                    st.button(f"{icon} {page}", key=f"nav_{page}", disabled=True, 
                             use_container_width=True, help="Importez des données d'abord")
                else:
                    if st.button(f"{icon} {page}", key=f"nav_{page}", type=button_type, use_container_width=True):
                        st.session_state.current_page = page
                        st.rerun()
        
        # Catégorie: Outils & Administration
        with st.expander("🛠️ **Outils & Admin**", expanded=False):
            pages_tools = {
                "Historique": "📁",
                "Serveur": "🖥️"
            }
            for page, icon in pages_tools.items():
                button_type = "primary" if st.session_state.current_page == page else "secondary"
                if st.button(f"{icon} {page}", key=f"nav_{page}", type=button_type, use_container_width=True):
                    st.session_state.current_page = page
                    st.rerun()

        st.markdown("---")
        st.markdown("<p style='text-align: center; font-size: 0.8em;'>© 2024-2025</p>", unsafe_allow_html=True)

    # --- Contenu Principal ---
    current_page = st.session_state.current_page
    
    if current_page == "Accueil":
        show_home_page()
    elif current_page == "Configuration":
        st.session_state.config_module.show_ui()
    elif current_page == "Importation Données":
        st.session_state.data_import_module.show_ui()
    elif current_page == "Analyse & Optimisation":
        if st.session_state.get('data_imported', False):
            st.markdown("<h1 class='main-header'>Analyse & Optimisation</h1>", unsafe_allow_html=True)
            
            if 'scenarios' in st.session_state and st.session_state.scenarios:
                available_scenarios = list(st.session_state.scenarios.keys())
                scenario_choisi = st.selectbox(
                    "Choisissez le scénario à analyser :", 
                    options=available_scenarios,
                    key="app_scenario_selector" 
                )
                
                if scenario_choisi:
                    display_analysis_optimisation_section(scenario_choisi) 
                else:
                    st.warning("Aucun scénario sélectionné ou disponible.")
            else:
                st.warning("Aucun scénario défini. Veuillez aller à la page Configuration.")
        else:
            st.warning("Veuillez importer des données avant d'accéder à cette section.")
    elif current_page == "ERP Clients":
        render_erp_module()
    elif current_page == "Carte de Prospection":
        show_prospect_map_ui()
    elif current_page == "Facturation PMO":
        show_facturation_page()
    elif current_page == "Visualisation":
        if st.session_state.get('data_imported', False):
            # Titre principal
            st.markdown("<h1 class='main-header'>📊 Visualisation des Données</h1>", unsafe_allow_html=True)
            
            # Vérifier quelle interface est utilisée
            if hasattr(st.session_state.visualization_module, 'is_modern_ui') and st.session_state.visualization_module.is_modern_ui:
                # Afficher un badge pour l'interface moderne
                col1, col2, col3 = st.columns([2, 1, 2])
                with col2:
                    st.success("✨ Interface Moderne Activée")
                
                # Message informatif sur les fonctionnalités disponibles
                with st.expander("🎨 Fonctionnalités de l'Interface Moderne", expanded=False):
                    st.info("""
                    **Nouvelles fonctionnalités disponibles :**
                    - 🎨 **Thèmes personnalisables** : Clair, Sombre, Professionnel
                    - 📊 **Graphiques interactifs avancés** : Sankey, Heatmap, 3D
                    - 🎯 **Dashboard personnalisable** : Glisser-déposer les widgets
                    - ✨ **Animations fluides** : Transitions et effets visuels
                    - 📈 **Visualisations temps réel** : Mise à jour dynamique
                    - 🔍 **Filtres avancés** : Multi-critères et sauvegardables
                    """)
            
            # Appeler la méthode show_ui avec les données disponibles
            try:
                # Passer toutes les données nécessaires au module de visualisation
                st.session_state.visualization_module.show_ui(
                    config=st.session_state.get('config', {}),
                    scenarios=st.session_state.get('scenarios', {}),
                    sites_data=st.session_state.get('sites_data', {}),
                    economic_results=st.session_state.get('economic_results', {}),
                    optimization_results=st.session_state.get('optimization_results', {}),
                    monte_carlo_results=st.session_state.get('monte_carlo_results', {}),
                    floor_price_results=st.session_state.get('floor_price_results', {})
                )
            except TypeError as e:
                # Si la méthode n'accepte pas d'arguments, l'appeler sans arguments
                print(f"Fallback vers show_ui sans arguments: {e}")
                st.session_state.visualization_module.show_ui()
            except Exception as e:
                st.error(f"Erreur lors du chargement de l'interface de visualisation: {str(e)}")
                st.info("Essayez de rafraîchir la page ou de réimporter vos données.")
        else:
            st.warning("⚠️ Veuillez importer des données avant d'accéder à cette section.")
            st.info("👉 Allez dans 'Importation Données' pour charger vos fichiers Excel.")
    elif current_page == "Rapports":
        if st.session_state.get('data_imported', False):
            st.session_state.reporting_module.show_ui()
        else:
            st.warning("Veuillez importer des données avant d'accéder à cette section.")
    elif current_page == "Historique":
        st.session_state.storage_module.show_ui()
    elif current_page == "Serveur":
        show_server_control_page()

# --- Page d'accueil ---
def show_home_page():
    st.markdown("<h1 class='main-header'>OptimPV - Optimisation de l'Autoconsommation Collective</h1>", unsafe_allow_html=True)
    st.markdown("<div class='info-box'>", unsafe_allow_html=True)
    st.markdown("""
    Bienvenue dans l'application OptimPV, conçue pour optimiser l'autoconsommation collective de sites photovoltaïques. 
    Cette application vous permet de déterminer le prix de revente optimal de l'électricité excédentaire à des acheteurs locaux, 
    tout en garantissant la rentabilité de votre projet sur 20 à 25 ans.
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Objectifs")
        st.markdown("""
        - **Optimiser** le prix de vente de l'électricité excédentaire
        - **Maximiser** la rentabilité de votre installation photovoltaïque
        - **Analyser** différents scénarios d'autoconsommation
        - **Évaluer** l'impact financier sur 20-25 ans
        """)
    
    with col2:
        st.markdown("### 📊 Fonctionnalités")
        st.markdown("""
        - **Analyse financière** : VAN, TRI, LCOE
        - **Optimisation tarifaire** : Prix optimal automatique
        - **Simulation** : Flux de trésorerie détaillés
        - **Cartographie** : Prospection géographique
        - **Rapports** : Documentation complète
        """)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🔄 Étapes d'utilisation")
        st.markdown("""
        1. **Configuration** : Définir vos paramètres
        2. **Import** : Charger vos données
        3. **Analyse** : Calculer la rentabilité
        4. **Optimisation** : Trouver le prix optimal
        5. **Rapports** : Générer la documentation
        """)
    
    with col2:
        st.markdown("### 📈 Indicateurs clés")
        st.markdown("""
        - **VAN** : Valeur Actualisée Nette
        - **TRI** : Taux de Rendement Interne  
        - **LCOE** : Coût Actualisé de l'Énergie
        - **Temps de retour** : Période d'amortissement
        - **Bénéfices** : Gains sur 20-25 ans
        """)
    
    with col3:
        st.markdown("### 🎯 Résultats attendus")
        st.markdown("""
        - Prix de vente **optimisé**
        - Rentabilité **maximisée** 
        - Risques **évalués**
        - Décisions **éclairées**
        - Projet **viable**
        """)

if __name__ == "__main__":
    main()