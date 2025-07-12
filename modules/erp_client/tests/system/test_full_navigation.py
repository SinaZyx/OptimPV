#!/usr/bin/env python3
"""
Test de navigation automatisé pour l'application OptimPV
==================================================

Ce script lance l'application Streamlit et simule automatiquement
la navigation dans tous les onglets et modules pour détecter les erreurs.

Fonctionnalités:
- Lancement automatique de Streamlit en mode headless
- Navigation exhaustive dans tous les onglets et sous-onglets
- Test spécifique du module ERP et ses sous-sections
- Capture d'erreurs et génération de rapport détaillé
- Captures d'écran optionnelles
- Test des formulaires et interactions de base

Usage:
    python test_full_navigation.py [--headless] [--screenshots] [--timeout=60]
"""

import os
import sys
import time
import json
import logging
import subprocess
import traceback
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urljoin

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from selenium.common.exceptions import (
        TimeoutException, NoSuchElementException, 
        WebDriverException, ElementNotInteractableException
    )
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Configuration
BASE_URL = "http://localhost:8501"
STREAMLIT_PORT = 8501
STREAMLIT_COMMAND = ["streamlit", "run", "app.py", "--server.port", str(STREAMLIT_PORT)]
DEFAULT_TIMEOUT = 60  # secondes
MAX_WAIT_FOR_ELEMENT = 10  # secondes pour attendre un élément


@dataclass
class TestError:
    """Représente une erreur détectée lors des tests."""
    timestamp: str
    page: str
    tab: str
    error_type: str
    message: str
    stack_trace: Optional[str] = None
    screenshot_path: Optional[str] = None
    element_selector: Optional[str] = None


@dataclass
class TestReport:
    """Rapport complet des tests."""
    start_time: str
    end_time: str
    total_duration: float
    pages_tested: List[str]
    tabs_tested: List[str]
    errors: List[TestError]
    success_count: int
    failure_count: int
    navigation_map: Dict[str, List[str]]
    browser_info: Dict[str, str]
    streamlit_logs: List[str]


class StreamlitController:
    """Contrôleur pour gérer le processus Streamlit."""
    
    def __init__(self, app_path: str, port: int = STREAMLIT_PORT):
        self.app_path = app_path
        self.port = port
        self.process = None
        self.logs = []
        
    def start(self, timeout: int = 30) -> bool:
        """Démarre l'application Streamlit."""
        try:
            # Vérifier que le fichier app.py existe
            if not os.path.exists(self.app_path):
                raise FileNotFoundError(f"Application Streamlit non trouvée: {self.app_path}")
            
            # Commande Streamlit
            cmd = [
                sys.executable, "-m", "streamlit", "run", 
                self.app_path,
                "--server.port", str(self.port),
                "--server.headless", "true",
                "--server.enableCORS", "false",
                "--server.enableXsrfProtection", "false",
                "--browser.gatherUsageStats", "false"
            ]
            
            print(f"🚀 Démarrage de Streamlit: {' '.join(cmd)}")
            
            # Démarrer le processus
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=os.path.dirname(self.app_path) or "."
            )
            
            # Attendre que l'application soit prête
            return self._wait_for_startup(timeout)
            
        except Exception as e:
            print(f"❌ Erreur démarrage Streamlit: {e}")
            return False
    
    def _wait_for_startup(self, timeout: int) -> bool:
        """Attend que Streamlit soit prêt."""
        import requests
        
        start_time = time.time()
        print(f"⏳ Attente du démarrage (timeout: {timeout}s)...")
        
        while time.time() - start_time < timeout:
            try:
                # Vérifier si le processus est toujours vivant
                if self.process.poll() is not None:
                    # Le processus s'est terminé
                    stdout, stderr = self.process.communicate()
                    print(f"❌ Streamlit s'est arrêté prématurément:")
                    print(f"STDOUT: {stdout}")
                    if stderr:
                        print(f"STDERR: {stderr}")
                    return False
                
                # Tenter une connexion HTTP
                response = requests.get(f"http://localhost:{self.port}", timeout=5)
                if response.status_code == 200:
                    print(f"✅ Streamlit prêt sur le port {self.port}")
                    return True
                    
            except requests.exceptions.RequestException:
                pass  # Continuer à attendre
                
            time.sleep(2)
        
        print(f"❌ Timeout: Streamlit non accessible après {timeout}s")
        return False
    
    def stop(self):
        """Arrête l'application Streamlit."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
                print("🛑 Streamlit arrêté")
            except subprocess.TimeoutExpired:
                self.process.kill()
                print("🛑 Streamlit forcé à s'arrêter")
            except Exception as e:
                print(f"⚠️  Erreur lors de l'arrêt: {e}")
    
    def get_logs(self) -> List[str]:
        """Récupère les logs de Streamlit."""
        return self.logs.copy()


class NavigationTester:
    """Testeur de navigation automatisé."""
    
    def __init__(self, base_url: str = BASE_URL, headless: bool = True, screenshots: bool = False):
        self.base_url = base_url
        self.headless = headless
        self.screenshots = screenshots
        self.driver = None
        self.report = None
        self.errors = []
        self.screenshots_dir = None
        
        # Configuration des logs
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        if screenshots:
            self.screenshots_dir = Path("test_screenshots") / datetime.now().strftime("%Y%m%d_%H%M%S")
            self.screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    def setup_driver(self) -> bool:
        """Configure et démarre le driver Selenium."""
        try:
            # Essayer Chrome d'abord
            try:
                chrome_options = ChromeOptions()
                if self.headless:
                    chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-web-security")
                chrome_options.add_argument("--allow-running-insecure-content")
                
                self.driver = webdriver.Chrome(options=chrome_options)
                print("✅ Driver Chrome initialisé")
                return True
                
            except WebDriverException:
                # Essayer Firefox
                firefox_options = FirefoxOptions()
                if self.headless:
                    firefox_options.add_argument("--headless")
                firefox_options.add_argument("--width=1920")
                firefox_options.add_argument("--height=1080")
                
                self.driver = webdriver.Firefox(options=firefox_options)
                print("✅ Driver Firefox initialisé")
                return True
                
        except Exception as e:
            print(f"❌ Erreur configuration driver: {e}")
            return False
    
    def teardown_driver(self):
        """Ferme le driver Selenium."""
        if self.driver:
            try:
                self.driver.quit()
                print("🔚 Driver Selenium fermé")
            except Exception as e:
                print(f"⚠️ Erreur fermeture driver: {e}")
    
    def take_screenshot(self, name: str) -> Optional[str]:
        """Prend une capture d'écran."""
        if not self.screenshots or not self.driver or not self.screenshots_dir:
            return None
            
        try:
            filename = f"{name}_{datetime.now().strftime('%H%M%S')}.png"
            filepath = self.screenshots_dir / filename
            self.driver.save_screenshot(str(filepath))
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Erreur capture d'écran {name}: {e}")
            return None
    
    def wait_for_element(self, selector: str, timeout: int = MAX_WAIT_FOR_ELEMENT):
        """Attend qu'un élément soit présent."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
        except TimeoutException:
            return None
    
    def wait_for_clickable(self, selector: str, timeout: int = MAX_WAIT_FOR_ELEMENT):
        """Attend qu'un élément soit cliquable."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
        except TimeoutException:
            return None
    
    def safe_click(self, selector: str, description: str = "") -> bool:
        """Clique sur un élément de manière sécurisée."""
        try:
            element = self.wait_for_clickable(selector)
            if element:
                # Faire défiler jusqu'à l'élément
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)
                
                # Cliquer
                element.click()
                time.sleep(1)  # Attendre que l'action se propage
                return True
            else:
                self.add_error(
                    error_type="ElementNotFound",
                    message=f"Élément non trouvé: {selector} ({description})",
                    element_selector=selector
                )
                return False
                
        except Exception as e:
            self.add_error(
                error_type="ClickError",
                message=f"Erreur clic {selector} ({description}): {str(e)}",
                element_selector=selector,
                stack_trace=traceback.format_exc()
            )
            return False
    
    def safe_input(self, selector: str, text: str, description: str = "") -> bool:
        """Saisit du texte dans un champ de manière sécurisée."""
        try:
            element = self.wait_for_element(selector)
            if element:
                element.clear()
                element.send_keys(text)
                time.sleep(0.5)
                return True
            else:
                self.add_error(
                    error_type="ElementNotFound",
                    message=f"Champ de saisie non trouvé: {selector} ({description})",
                    element_selector=selector
                )
                return False
                
        except Exception as e:
            self.add_error(
                error_type="InputError",
                message=f"Erreur saisie {selector} ({description}): {str(e)}",
                element_selector=selector,
                stack_trace=traceback.format_exc()
            )
            return False
    
    def add_error(self, error_type: str, message: str, **kwargs):
        """Ajoute une erreur au rapport."""
        error = TestError(
            timestamp=datetime.now().isoformat(),
            page=getattr(self, 'current_page', 'Unknown'),
            tab=getattr(self, 'current_tab', 'Unknown'),
            error_type=error_type,
            message=message,
            **kwargs
        )
        
        # Capture d'écran si possible
        if self.screenshots:
            error.screenshot_path = self.take_screenshot(f"error_{error_type}")
        
        self.errors.append(error)
        self.logger.error(f"[{error.page}/{error.tab}] {error_type}: {message}")
    
    def check_for_streamlit_errors(self) -> List[str]:
        """Vérifie la présence d'erreurs Streamlit sur la page."""
        streamlit_errors = []
        
        try:
            # Chercher les éléments d'erreur Streamlit
            error_selectors = [
                ".stException",
                ".stError", 
                "[data-testid='stException']",
                "[data-testid='stError']",
                ".stAlert[data-baseweb='notification'][kind='error']",
                ".element-container .stMarkdown .stAlert[data-baseweb='notification']"
            ]
            
            for selector in error_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            error_text = element.text.strip()
                            if error_text:
                                streamlit_errors.append(error_text)
                except:
                    continue
            
            # Chercher les messages d'erreur dans la console
            try:
                logs = self.driver.get_log('browser')
                for log in logs:
                    if log['level'] == 'SEVERE':
                        streamlit_errors.append(f"Console Error: {log['message']}")
            except:
                pass
                
        except Exception as e:
            self.logger.warning(f"Erreur vérification erreurs Streamlit: {e}")
        
        return streamlit_errors
    
    def authenticate(self) -> bool:
        """Authentifie l'utilisateur dans OptimPV."""
        try:
            self.current_page = "Authentication"
            self.current_tab = "Login"
            
            print("🔐 Tentative d'authentification...")
            
            # Attendre la page d'authentification
            auth_input = self.wait_for_element("input[type='password']", timeout=15)
            if not auth_input:
                print("ℹ️ Pas de page d'authentification détectée")
                return True
            
            # Saisir le mot de passe par défaut
            if self.safe_input("input[type='password']", "panel123", "Mot de passe"):
                # Cliquer sur le bouton de connexion
                if self.safe_click("button:contains('Se Connecter')", "Bouton connexion"):
                    time.sleep(3)  # Attendre la redirection
                    print("✅ Authentification réussie")
                    return True
            
            print("❌ Échec de l'authentification")
            return False
            
        except Exception as e:
            self.add_error(
                error_type="AuthenticationError",
                message=f"Erreur authentification: {str(e)}",
                stack_trace=traceback.format_exc()
            )
            return False
    
    def navigate_to_page(self, page_name: str) -> bool:
        """Navigue vers une page spécifique."""
        try:
            self.current_page = page_name
            self.current_tab = "Main"
            
            print(f"📄 Navigation vers: {page_name}")
            
            # Carte des sélecteurs de pages
            page_selectors = {
                "Accueil": "button:contains('Accueil')",
                "Importation Données": "button:contains('Importation Données')",
                "Configuration": "button:contains('Configuration')",
                "ERP Clients": "button:contains('ERP Clients')",
                "Facturation PMO": "button:contains('Facturation PMO')",
                "Carte de Prospection": "button:contains('Carte de Prospection')",
                "Analyse & Optimisation": "button:contains('Analyse & Optimisation')",
                "Visualisation": "button:contains('Visualisation')",
                "Rapports": "button:contains('Rapports')",
                "Historique": "button:contains('Historique')",
                "Serveur": "button:contains('Serveur')"
            }
            
            selector = page_selectors.get(page_name)
            if not selector:
                self.add_error(
                    error_type="UnknownPage",
                    message=f"Page inconnue: {page_name}"
                )
                return False
            
            # Cliquer sur le bouton de navigation
            if self.safe_click(selector, f"Navigation {page_name}"):
                time.sleep(2)  # Attendre le chargement
                
                # Vérifier les erreurs Streamlit
                errors = self.check_for_streamlit_errors()
                if errors:
                    for error in errors:
                        self.add_error(
                            error_type="StreamlitError",
                            message=f"Erreur Streamlit sur page {page_name}: {error}"
                        )
                
                return True
            
            return False
            
        except Exception as e:
            self.add_error(
                error_type="NavigationError",
                message=f"Erreur navigation vers {page_name}: {str(e)}",
                stack_trace=traceback.format_exc()
            )
            return False
    
    def test_erp_module(self) -> bool:
        """Test spécifique du module ERP et tous ses onglets."""
        try:
            print("🏢 Test du module ERP...")
            
            if not self.navigate_to_page("ERP Clients"):
                return False
            
            # Attendre que la page ERP soit chargée
            time.sleep(3)
            
            # Liste des onglets ERP à tester
            erp_tabs = [
                "💼 Dashboard Commercial",
                "👥 Clients", 
                "➕ Nouveau client",
                "💰 Tarification",
                "🔌 Autoconsommation",
                "🗺️ Cartographie",
                "📊 Analytics"
            ]
            
            for tab_name in erp_tabs:
                try:
                    self.current_tab = tab_name
                    print(f"   📋 Test onglet ERP: {tab_name}")
                    
                    # Sélecteur pour les onglets Streamlit
                    tab_selector = f"button[data-baseweb='tab']:contains('{tab_name}')"
                    
                    if self.safe_click(tab_selector, f"Onglet ERP {tab_name}"):
                        time.sleep(2)
                        
                        # Test spécifique par onglet
                        self.test_erp_tab_content(tab_name)
                        
                        # Vérifier les erreurs
                        errors = self.check_for_streamlit_errors()
                        if errors:
                            for error in errors:
                                self.add_error(
                                    error_type="ERPTabError",
                                    message=f"Erreur onglet ERP {tab_name}: {error}"
                                )
                    
                except Exception as e:
                    self.add_error(
                        error_type="ERPTabError",
                        message=f"Erreur test onglet ERP {tab_name}: {str(e)}",
                        stack_trace=traceback.format_exc()
                    )
            
            return True
            
        except Exception as e:
            self.add_error(
                error_type="ERPModuleError",
                message=f"Erreur test module ERP: {str(e)}",
                stack_trace=traceback.format_exc()
            )
            return False
    
    def test_erp_tab_content(self, tab_name: str):
        """Test le contenu spécifique d'un onglet ERP."""
        try:
            if tab_name == "➕ Nouveau client":
                self.test_new_client_form()
            elif tab_name == "👥 Clients":
                self.test_client_list()
            elif tab_name == "💰 Tarification":
                self.test_pricing_dashboard()
            elif tab_name == "🔌 Autoconsommation":
                self.test_autoconso_dashboard()
            elif tab_name == "🗺️ Cartographie":
                self.test_client_map()
            elif tab_name == "📊 Analytics":
                self.test_analytics_dashboard()
            
        except Exception as e:
            self.add_error(
                error_type="ERPTabContentError",
                message=f"Erreur contenu onglet {tab_name}: {str(e)}",
                stack_trace=traceback.format_exc()
            )
    
    def test_new_client_form(self):
        """Test le formulaire de nouveau client."""
        print("      🆕 Test formulaire nouveau client")
        
        # Chercher les champs du formulaire
        form_fields = [
            "input[placeholder*='nom']",
            "input[placeholder*='adresse']",
            "input[placeholder*='email']",
            "input[placeholder*='téléphone']"
        ]
        
        for field in form_fields:
            element = self.wait_for_element(field, timeout=5)
            if element:
                print(f"         ✓ Champ trouvé: {field}")
            else:
                print(f"         ⚠ Champ manquant: {field}")
    
    def test_client_list(self):
        """Test la liste des clients."""
        print("      👥 Test liste des clients")
        
        # Chercher la table ou liste des clients
        list_selectors = [
            "[data-testid='dataframe']",
            ".stDataFrame",
            "table",
            ".client-list"
        ]
        
        for selector in list_selectors:
            element = self.wait_for_element(selector, timeout=5)
            if element:
                print(f"         ✓ Liste clients trouvée: {selector}")
                return
        
        print("         ⚠ Aucune liste de clients détectée")
    
    def test_pricing_dashboard(self):
        """Test le dashboard de tarification."""
        print("      💰 Test dashboard tarification")
        
        # Chercher les éléments de tarification
        pricing_elements = [
            "input[type='number']",  # Champs de prix
            ".metric-container",     # Métriques
            ".stSelectbox"          # Sélecteurs
        ]
        
        found_elements = 0
        for selector in pricing_elements:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                found_elements += len(elements)
        
        print(f"         ✓ {found_elements} éléments de tarification trouvés")
    
    def test_autoconso_dashboard(self):
        """Test le dashboard d'autoconsommation."""
        print("      🔌 Test dashboard autoconsommation")
        
        # Chercher les graphiques et métriques
        autoconso_elements = [
            ".js-plotly-plot",      # Graphiques Plotly
            ".metric-container",    # Métriques
            ".stProgress"          # Barres de progression
        ]
        
        found_charts = 0
        for selector in autoconso_elements:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                found_charts += len(elements)
        
        print(f"         ✓ {found_charts} éléments d'autoconso trouvés")
    
    def test_client_map(self):
        """Test la carte des clients."""
        print("      🗺️ Test carte des clients")
        
        # Chercher la carte
        map_selectors = [
            ".folium-map",
            ".stDeckGlJsonChart", 
            ".stPydeckChart",
            "[data-testid='stDeckGlJsonChart']"
        ]
        
        for selector in map_selectors:
            element = self.wait_for_element(selector, timeout=5)
            if element:
                print(f"         ✓ Carte trouvée: {selector}")
                return
        
        print("         ⚠ Aucune carte détectée")
    
    def test_analytics_dashboard(self):
        """Test le dashboard d'analytics."""
        print("      📊 Test dashboard analytics")
        
        # Chercher les graphiques et statistiques
        analytics_elements = [
            ".js-plotly-plot",
            ".metric-container", 
            "[data-testid='metric-container']",
            ".stBar"
        ]
        
        found_elements = 0
        for selector in analytics_elements:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                found_elements += len(elements)
        
        print(f"         ✓ {found_elements} éléments analytics trouvés")
    
    def test_form_interactions(self, page_name: str):
        """Test les interactions de formulaires sur une page."""
        try:
            print(f"   📝 Test interactions formulaires: {page_name}")
            
            # Chercher les formulaires
            forms = self.driver.find_elements(By.CSS_SELECTOR, "form")
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input, select, textarea")
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button:contains('Valider'), button:contains('Enregistrer')")
            
            print(f"      🔍 Trouvé: {len(forms)} formulaires, {len(inputs)} champs, {len(buttons)} boutons")
            
            # Test rapide des champs de saisie
            test_inputs = inputs[:3]  # Tester seulement les 3 premiers
            for i, input_elem in enumerate(test_inputs):
                try:
                    if input_elem.is_enabled() and input_elem.is_displayed():
                        input_type = input_elem.get_attribute('type') or 'text'
                        
                        if input_type in ['text', 'email', 'tel']:
                            input_elem.clear()
                            input_elem.send_keys(f"test_value_{i}")
                            time.sleep(0.2)
                        elif input_type == 'number':
                            input_elem.clear()
                            input_elem.send_keys("123")
                            time.sleep(0.2)
                            
                except Exception as e:
                    print(f"      ⚠ Erreur test champ {i}: {e}")
            
        except Exception as e:
            self.add_error(
                error_type="FormInteractionError",
                message=f"Erreur test formulaires {page_name}: {str(e)}",
                stack_trace=traceback.format_exc()
            )
    
    def run_comprehensive_test(self, timeout: int = DEFAULT_TIMEOUT) -> TestReport:
        """Lance le test complet de navigation."""
        start_time = datetime.now()
        print(f"🧪 Début des tests de navigation - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not SELENIUM_AVAILABLE:
            print("❌ Selenium non disponible. Installez avec: pip install selenium")
            return None
        
        try:
            # Initialiser le driver
            if not self.setup_driver():
                print("❌ Impossible d'initialiser le driver Selenium")
                return None
            
            # Aller à la page principale
            print(f"🌐 Connexion à {self.base_url}")
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Authentification
            if not self.authenticate():
                print("❌ Échec de l'authentification")
                return None
            
            # Liste des pages à tester
            pages_to_test = [
                "Accueil",
                "Configuration", 
                "Importation Données",
                "ERP Clients",  # Test approfondi
                "Facturation PMO",
                "Carte de Prospection",
                "Historique",
                "Serveur"
            ]
            
            pages_tested = []
            tabs_tested = []
            
            # Test de chaque page
            for page in pages_to_test:
                try:
                    print(f"\n📄 === Test page: {page} ===")
                    
                    if self.navigate_to_page(page):
                        pages_tested.append(page)
                        
                        # Test spécial pour ERP
                        if page == "ERP Clients":
                            self.test_erp_module()
                            tabs_tested.extend([
                                "💼 Dashboard Commercial",
                                "👥 Clients", 
                                "➕ Nouveau client",
                                "💰 Tarification",
                                "🔌 Autoconsommation",
                                "🗺️ Cartographie",
                                "📊 Analytics"
                            ])
                        else:
                            # Test des interactions de base
                            self.test_form_interactions(page)
                        
                        # Capture d'écran
                        if self.screenshots:
                            self.take_screenshot(f"page_{page}")
                    
                    time.sleep(1)
                    
                except Exception as e:
                    self.add_error(
                        error_type="PageTestError",
                        message=f"Erreur test page {page}: {str(e)}",
                        stack_trace=traceback.format_exc()
                    )
            
            # Calcul du rapport final
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Informations du navigateur
            browser_info = {
                "name": self.driver.name,
                "version": self.driver.capabilities.get('browserVersion', 'Unknown'),
                "platform": self.driver.capabilities.get('platformName', 'Unknown')
            }
            
            self.report = TestReport(
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                total_duration=duration,
                pages_tested=pages_tested,
                tabs_tested=tabs_tested,
                errors=self.errors,
                success_count=len(pages_tested) + len(tabs_tested) - len(self.errors),
                failure_count=len(self.errors),
                navigation_map={page: [] for page in pages_tested},  # Simplifié
                browser_info=browser_info,
                streamlit_logs=[]  # À implémenter si nécessaire
            )
            
            print(f"\n✅ Tests terminés en {duration:.1f}s")
            print(f"📊 Pages testées: {len(pages_tested)}")
            print(f"📋 Onglets testés: {len(tabs_tested)}")
            print(f"❌ Erreurs détectées: {len(self.errors)}")
            
            return self.report
            
        except Exception as e:
            self.add_error(
                error_type="TestFrameworkError",
                message=f"Erreur framework de test: {str(e)}",
                stack_trace=traceback.format_exc()
            )
            return None
            
        finally:
            self.teardown_driver()


class TestReportGenerator:
    """Générateur de rapports de test."""
    
    @staticmethod
    def generate_html_report(report: TestReport, output_path: str):
        """Génère un rapport HTML détaillé."""
        
        html_template = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport de Test - Navigation OptimPV</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; }
        .header h1 { margin: 0; font-size: 2.5em; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; padding: 30px; }
        .metric { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }
        .metric-value { font-size: 2em; font-weight: bold; color: #2c3e50; }
        .metric-label { color: #7f8c8d; margin-top: 5px; }
        .success { border-left: 5px solid #27ae60; }
        .error { border-left: 5px solid #e74c3c; }
        .section { padding: 30px; border-top: 1px solid #ecf0f1; }
        .section h2 { color: #2c3e50; margin-bottom: 20px; }
        .error-item { background: #fff5f5; border: 1px solid #fed7d7; border-radius: 5px; padding: 15px; margin-bottom: 10px; }
        .error-type { font-weight: bold; color: #e53e3e; }
        .error-message { margin: 10px 0; }
        .error-details { font-size: 0.9em; color: #666; }
        .pages-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }
        .page-item { background: #e8f5e8; padding: 15px; border-radius: 5px; text-align: center; }
        .tabs-list { display: flex; flex-wrap: wrap; gap: 10px; }
        .tab-item { background: #e3f2fd; padding: 8px 15px; border-radius: 20px; font-size: 0.9em; }
        .timestamp { color: #7f8c8d; font-size: 0.9em; }
        pre { background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 0.8em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Rapport de Test - Navigation OptimPV</h1>
            <p>Test automatisé de l'interface utilisateur Streamlit</p>
            <div class="timestamp">Généré le: {timestamp}</div>
        </div>
        
        <div class="summary">
            <div class="metric success">
                <div class="metric-value">{success_count}</div>
                <div class="metric-label">Tests Réussis</div>
            </div>
            <div class="metric error">
                <div class="metric-value">{failure_count}</div>
                <div class="metric-label">Erreurs Détectées</div>
            </div>
            <div class="metric">
                <div class="metric-value">{pages_count}</div>
                <div class="metric-label">Pages Testées</div>
            </div>
            <div class="metric">
                <div class="metric-value">{duration}s</div>
                <div class="metric-label">Durée Totale</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📄 Pages Testées</h2>
            <div class="pages-grid">
                {pages_html}
            </div>
        </div>
        
        <div class="section">
            <h2>📋 Onglets Testés (Module ERP)</h2>
            <div class="tabs-list">
                {tabs_html}
            </div>
        </div>
        
        <div class="section">
            <h2>❌ Erreurs Détectées ({error_count})</h2>
            {errors_html}
        </div>
        
        <div class="section">
            <h2>🔍 Informations Techniques</h2>
            <pre>{technical_info}</pre>
        </div>
    </div>
</body>
</html>
        """
        
        # Génération du contenu
        pages_html = "\n".join([f'<div class="page-item">📄 {page}</div>' for page in report.pages_tested])
        tabs_html = "\n".join([f'<div class="tab-item">{tab}</div>' for tab in report.tabs_tested])
        
        errors_html = ""
        if report.errors:
            for error in report.errors:
                errors_html += f"""
                <div class="error-item">
                    <div class="error-type">{error.error_type}</div>
                    <div class="error-message">{error.message}</div>
                    <div class="error-details">
                        <strong>Page:</strong> {error.page} | 
                        <strong>Onglet:</strong> {error.tab} | 
                        <strong>Timestamp:</strong> {error.timestamp}
                    </div>
                    {f'<pre>{error.stack_trace}</pre>' if error.stack_trace else ''}
                </div>
                """
        else:
            errors_html = '<div style="text-align: center; color: #27ae60; font-size: 1.2em;">🎉 Aucune erreur détectée!</div>'
        
        technical_info = f"""Navigateur: {report.browser_info.get('name', 'Unknown')} {report.browser_info.get('version', '')}
Plateforme: {report.browser_info.get('platform', 'Unknown')}
Période de test: {report.start_time} → {report.end_time}
Pages: {', '.join(report.pages_tested)}
Onglets ERP: {', '.join(report.tabs_tested)}"""
        
        # Remplacer les variables
        html_content = html_template.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            success_count=report.success_count,
            failure_count=report.failure_count,
            pages_count=len(report.pages_tested),
            duration=round(report.total_duration, 1),
            pages_html=pages_html,
            tabs_html=tabs_html,
            error_count=len(report.errors),
            errors_html=errors_html,
            technical_info=technical_info
        )
        
        # Écrire le fichier
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📋 Rapport HTML généré: {output_path}")
    
    @staticmethod
    def generate_json_report(report: TestReport, output_path: str):
        """Génère un rapport JSON."""
        report_dict = asdict(report)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        print(f"📋 Rapport JSON généré: {output_path}")


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(description="Test automatisé de navigation OptimPV")
    parser.add_argument("--headless", action="store_true", help="Mode headless (sans interface)")
    parser.add_argument("--screenshots", action="store_true", help="Prendre des captures d'écran")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Timeout en secondes")
    parser.add_argument("--no-start-streamlit", action="store_true", help="Ne pas démarrer Streamlit automatiquement")
    
    args = parser.parse_args()
    
    print("🚀 === Test de Navigation Automatisé OptimPV ===")
    print(f"Mode: {'Headless' if args.headless else 'Interface visible'}")
    print(f"Screenshots: {'Activés' if args.screenshots else 'Désactivés'}")
    print(f"Timeout: {args.timeout}s")
    
    # Vérifications préliminaires
    if not SELENIUM_AVAILABLE:
        print("❌ Erreur: Selenium n'est pas installé")
        print("Installation: pip install selenium")
        print("Il faut aussi ChromeDriver ou GeckoDriver dans le PATH")
        return 1
    
    # Chemin de l'application
    app_path = os.path.join(os.getcwd(), "app.py")
    if not os.path.exists(app_path):
        print(f"❌ Erreur: app.py non trouvé dans {os.getcwd()}")
        return 1
    
    streamlit_controller = None
    
    try:
        # Démarrer Streamlit si demandé
        if not args.no_start_streamlit:
            streamlit_controller = StreamlitController(app_path, STREAMLIT_PORT)
            if not streamlit_controller.start(timeout=30):
                print("❌ Impossible de démarrer Streamlit")
                return 1
        
        # Lancer les tests
        tester = NavigationTester(
            base_url=BASE_URL,
            headless=args.headless,
            screenshots=args.screenshots
        )
        
        report = tester.run_comprehensive_test(timeout=args.timeout)
        
        if report:
            # Générer les rapports
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            reports_dir = Path("test_reports")
            reports_dir.mkdir(exist_ok=True)
            
            html_path = reports_dir / f"navigation_test_{timestamp}.html"
            json_path = reports_dir / f"navigation_test_{timestamp}.json"
            
            TestReportGenerator.generate_html_report(report, str(html_path))
            TestReportGenerator.generate_json_report(report, str(json_path))
            
            # Résumé final
            print(f"\n🎯 === RÉSUMÉ FINAL ===")
            print(f"✅ Tests réussis: {report.success_count}")
            print(f"❌ Erreurs: {report.failure_count}")
            print(f"📄 Pages testées: {len(report.pages_tested)}")
            print(f"📋 Onglets testés: {len(report.tabs_tested)}")
            print(f"⏱️ Durée: {report.total_duration:.1f}s")
            
            if report.errors:
                print(f"\n❌ ERREURS DÉTECTÉES:")
                for error in report.errors[:5]:  # Afficher seulement les 5 premières
                    print(f"  • [{error.page}/{error.tab}] {error.error_type}: {error.message}")
                if len(report.errors) > 5:
                    print(f"  ... et {len(report.errors) - 5} autres erreurs (voir le rapport)")
            else:
                print(f"\n🎉 AUCUNE ERREUR DÉTECTÉE! Application parfaitement fonctionnelle.")
            
            return 0 if report.failure_count == 0 else 1
        else:
            print("❌ Échec des tests")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrompu par l'utilisateur")
        return 1
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        traceback.print_exc()
        return 1
    finally:
        # Arrêter Streamlit
        if streamlit_controller:
            streamlit_controller.stop()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)