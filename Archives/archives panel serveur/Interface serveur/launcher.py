#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OptimPV Desktop Launcher
========================

Ce launcher démarre automatiquement le serveur Streamlit et l'interface desktop native.
Créé pour un packaging sécurisé avec Nuitka + UPX.

Fonctionnalités :
- Démarrage automatique de Streamlit en mode headless
- Interface native avec pywebview 
- Interface d'administration réseau sécurisée
- Configuration dynamique IP/port
- Gestion propre de l'arrêt du serveur
- Port dynamique avec fallback
- Gestion des erreurs et logs
"""

import os
import sys
import time
import signal
import socket
import logging
import subprocess
import threading
import webbrowser
from pathlib import Path
from typing import Optional

# AJOUT : Configuration des chemins des modules (comme dans app.py)
# Ajouter le chemin du dossier 'modules' au path Python
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'modules'))
if module_path not in sys.path:
    sys.path.append(module_path)

# Ajouter aussi le répertoire racine au path pour les imports relatifs
root_path = os.path.abspath(os.path.dirname(__file__))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

import webview
import streamlit.web.cli as stcli

# Import du module d'administration
try:
    from admin_config import NetworkAdminConfig
    ADMIN_MODULE_AVAILABLE = True
except ImportError:
    ADMIN_MODULE_AVAILABLE = False
    print("Module d'administration non disponible")


# Configuration des logs dans AppData
appdata_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'OptimPV')
os.makedirs(appdata_dir, exist_ok=True)
launcher_log_file = os.path.join(appdata_dir, 'optimpv_launcher.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(launcher_log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('OptimPV_Launcher')


class StreamlitServerManager:
    """Gestionnaire du serveur Streamlit"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.port: int = 8502
        self.host: str = "127.0.0.1"
        self.app_file: str = "../app.py"
        self.admin_config = None
        
        # Charger la configuration admin si disponible
        if ADMIN_MODULE_AVAILABLE:
            try:
                self.admin_config = NetworkAdminConfig()
                network_config = self.admin_config.get_network_config()
                self.host = network_config.get('ip', '127.0.0.1')
                configured_port = network_config.get('port', 8504)
                self.port = 8502 if configured_port == 8504 else configured_port
                logger.info(f"Configuration réseau chargée: {self.host}:{self.port}")
            except Exception as e:
                logger.error(f"Erreur chargement config admin: {e}")
                self.admin_config = None
        
    def find_available_port(self, start_port: Optional[int] = None) -> int:
        """Trouve un port disponible en commençant par start_port"""
        if start_port is None:
            start_port = self.port
            
        for port in range(start_port, start_port + 100):
            # Éviter le port 8504 réservé au panneau de contrôle
            if port == 8504:
                continue
                
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.host if self.host != "0.0.0.0" else "127.0.0.1", port))
                    logger.info(f"Port {port} disponible")
                    return port
            except OSError:
                continue
        
        logger.error("Aucun port disponible trouvé")
        raise RuntimeError("Impossible de trouver un port libre")
    
    def start_server(self) -> str:
        """Démarre le serveur Streamlit et retourne l'URL"""
        
        # Détection du mode d'exécution
        is_frozen = getattr(sys, 'frozen', False)
        
        # Trouver le script à exécuter
        if is_frozen:
            # Mode EXE - chercher dans les ressources intégrées
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(sys.executable)
            
            # Chercher le script Streamlit
            possible_scripts = [
                os.path.join(base_path, "Interface serveur", "server_control", "core", "server_control_panel.py"),
                os.path.join(base_path, "app.py"),
                os.path.join(base_path, "server_control", "core", "server_control_panel.py"),
                "../app.py"  # Fallback
            ]
            
            app_file = None
            for script in possible_scripts:
                if os.path.exists(script):
                    app_file = script
                    logger.info(f"Script trouvé: {script}")
                    break
                    
            if not app_file:
                logger.error("Aucun script Streamlit trouvé dans l'EXE")
                raise FileNotFoundError("Script Streamlit manquant")
                
        else:
            # Mode développement - utiliser le chemin existant
            app_file = self.app_file
            if not os.path.exists(app_file):
                logger.error(f"Fichier {app_file} introuvable")
                raise FileNotFoundError(f"Le fichier {app_file} est requis")
        
        # Utiliser le port configuré ou trouver un port libre
        try:
            self.port = self.find_available_port(self.port)
        except RuntimeError:
            # Fallback sur le port par défaut si la config échoue
            logger.warning("Fallback sur configuration par défaut")
            self.host = "127.0.0.1"
            self.port = self.find_available_port(8502)
        
        # Configuration de l'environnement Python
        env = os.environ.copy()
        
        if is_frozen:
            # Mode EXE - configurer l'environnement pour les ressources intégrées
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(sys.executable)
                
            modules_path = os.path.join(base_path, 'modules')
            interface_path = os.path.join(base_path, 'Interface serveur')
            
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{base_path}{os.pathsep}{modules_path}{os.pathsep}{interface_path}{os.pathsep}{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = f"{base_path}{os.pathsep}{modules_path}{os.pathsep}{interface_path}"
        else:
            # Mode développement - configuration existante
            current_dir = os.path.abspath(os.path.dirname(__file__))
            modules_path = os.path.join(current_dir, 'modules')
            
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{current_dir}{os.pathsep}{modules_path}{os.pathsep}{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = f"{current_dir}{os.pathsep}{modules_path}"
        
        logger.info(f"Configuration PYTHONPATH: {env['PYTHONPATH']}")
        
        # Configuration du mode headless (votre logique existante)
        force_headless = True
        browser_mode = "headless_always"
        
        if self.admin_config:
            try:
                network_config = self.admin_config.get_network_config()
                browser_mode = network_config.get('browser_mode', 'headless_always')
                force_headless_panel = network_config.get('force_headless_panel', True)
                
                if browser_mode == "headless_always":
                    force_headless = True
                elif browser_mode == "headless_network_only":
                    force_headless = (self.host == "0.0.0.0" or not self.host.startswith("127."))
                elif browser_mode == "auto_open_local":
                    force_headless = not (self.host in ["127.0.0.1", "localhost"])
                
                if self.port == 8501 and force_headless_panel:
                    force_headless = True
                    
                logger.info(f"Mode navigateur configuré: {browser_mode}")
                
            except Exception as e:
                logger.warning(f"Erreur lecture config navigateur: {e}, utilisation mode par défaut")
                force_headless = True
        else:
            # Fallback si pas de config admin
            if self.host in ["127.0.0.1", "localhost"] and self.port != 8501:
                force_headless = True
            elif self.host == "0.0.0.0" or not self.host.startswith("127."):
                force_headless = True
            
        logger.info(f"Mode headless appliqué: {force_headless} (IP: {self.host}, Port: {self.port}, Mode: {browser_mode})")
        
        # ===== SOLUTION SIMPLIFIÉE =====
        if is_frozen:
            # MODE EXE - Chercher Python dans le système
            try:
                import shutil
                
                # Chercher Python installé sur le système
                python_paths = [
                    shutil.which('python'),
                    shutil.which('python3'),
                    shutil.which('py'),
                    r'C:\Python39\python.exe',
                    r'C:\Python310\python.exe',
                    r'C:\Python311\python.exe',
                    r'C:\Python312\python.exe',
                    r'C:\Users\{}\AppData\Local\Programs\Python\Python39\python.exe'.format(os.environ.get('USERNAME', '')),
                    r'C:\Users\{}\AppData\Local\Programs\Python\Python310\python.exe'.format(os.environ.get('USERNAME', '')),
                    r'C:\Users\{}\AppData\Local\Programs\Python\Python311\python.exe'.format(os.environ.get('USERNAME', '')),
                    r'C:\Users\{}\AppData\Local\Programs\Python\Python312\python.exe'.format(os.environ.get('USERNAME', ''))
                ]
                
                python_exe = None
                for path in python_paths:
                    if path and os.path.exists(path):
                        python_exe = path
                        logger.info(f"Python trouvé: {python_exe}")
                        break
                
                if not python_exe:
                    raise RuntimeError("Python non trouvé sur le système. Installez Python pour utiliser OptimPV.")
                
                # Créer un script temporaire pour lancer Streamlit
                import tempfile
                script_content = f'''
import sys
import os

# Ajouter les chemins nécessaires
sys.path.insert(0, r"{base_path}")
sys.path.insert(0, r"{modules_path}")
sys.path.insert(0, r"{interface_path}")

# Changer le répertoire de travail
os.chdir(r"{base_path}")

# Configurer l'environnement
os.environ["PYTHONPATH"] = r"{base_path};{modules_path};{interface_path}"

# Importer et lancer Streamlit
try:
    import streamlit.web.cli as stcli
    sys.argv = [
        "streamlit", "run", r"{app_file}",
        "--server.headless=true",
        "--server.address={self.host}",
        "--server.port={self.port}",
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false",
        "--server.enableCORS=true",
        "--server.enableXsrfProtection=false"
    ]
    print(f"Démarrage Streamlit sur {{sys.argv[3]}} avec les options: {{' '.join(sys.argv[4:])}}")
    stcli.main()
except Exception as e:
    print(f"Erreur Streamlit: {{e}}")
    import traceback
    traceback.print_exc()
    import time
    time.sleep(10)  # Garde la fenêtre ouverte pour voir l'erreur
'''
                
                # Créer le fichier temporaire
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                    f.write(script_content)
                    temp_script = f.name
                
                logger.info(f"Script temporaire créé: {temp_script}")
                logger.info(f"Lancement avec Python: {python_exe}")
                
                # Lancer Python avec le script temporaire
                cmd = [python_exe, temp_script]
                
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                # Attendre que le serveur soit prêt
                display_host = "127.0.0.1" if self.host == "0.0.0.0" else self.host
                url = f"http://{display_host}:{self.port}"
                
                logger.info(f"Attente du démarrage du serveur sur {url}...")
                
                if self._wait_for_server(url, timeout=60):  # Plus de temps pour le premier démarrage
                    logger.info(f"Serveur Streamlit démarré (EXE via Python) sur {url}")
                    
                    # Nettoyer le fichier temporaire après un délai
                    def cleanup_temp_file():
                        import time
                        time.sleep(5)  # Attendre que Python ait lu le fichier
                        try:
                            os.unlink(temp_script)
                        except:
                            pass
                    
                    import threading
                    cleanup_thread = threading.Thread(target=cleanup_temp_file, daemon=True)
                    cleanup_thread.start()
                    
                    return url
                else:
                    # Nettoyer en cas d'échec
                    try:
                        os.unlink(temp_script)
                    except:
                        pass
                    raise RuntimeError("Le serveur Streamlit n'a pas pu démarrer dans les temps")
                    
            except Exception as e:
                logger.error(f"Erreur démarrage Streamlit mode EXE: {e}")
                raise RuntimeError(f"Impossible de démarrer Streamlit en mode EXE: {str(e)}")
        else:
            # MODE DÉVELOPPEMENT - Code existant inchangé
            cmd = [
                sys.executable, "-m", "streamlit", "run", 
                app_file,
                "--server.headless", "true",
                "--server.address", self.host,
                "--server.port", str(self.port),
                "--browser.gatherUsageStats", "false",
                "--global.developmentMode", "false",
                "--server.enableCORS", "true",
                "--server.enableXsrfProtection", "false",
                "--browser.serverAddress", self.host,
                "--browser.serverPort", str(self.port)
            ]
            
            logger.info(f"Démarrage Streamlit: {' '.join(cmd)}")
            logger.info(f"Configuration réseau: {self.host}:{self.port}")
            
            try:
                # Démarrer le processus Streamlit avec l'environnement configuré
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    cwd=os.path.dirname(__file__),
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                # Attendre que le serveur soit prêt
                display_host = "127.0.0.1" if self.host == "0.0.0.0" else self.host
                url = f"http://{display_host}:{self.port}"
                
                if self._wait_for_server(url, timeout=30):
                    logger.info(f"Serveur Streamlit démarré sur {url}")
                    
                    # Affichage des informations d'accès réseau
                    if self.host == "0.0.0.0" and self.admin_config:
                        network_config = self.admin_config.get_network_config()
                        if network_config.get('external_access', False):
                            logger.info("🌐 Accès réseau activé - Le serveur est accessible depuis d'autres machines")
                            logger.info(f"📱 Accès local: {url}")
                            logger.info(f"🌍 Accès réseau: http://<IP_DE_VOTRE_MACHINE>:{self.port}")
                    
                    return url
                else:
                    raise RuntimeError("Le serveur Streamlit n'a pas pu démarrer")
                    
            except Exception as e:
                logger.error(f"Erreur lors du démarrage de Streamlit: {e}")
                raise
            
    
    def _wait_for_server(self, url: str, timeout: int = 30) -> bool:
        """Attend que le serveur soit accessible"""
        import requests
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
        
        return False
    
    def stop_server(self):
        """Arrête proprement le serveur Streamlit"""
        if self.process:
            logger.info("Arrêt du serveur Streamlit...")
            
            try:
                # Vérifier le type de processus
                if hasattr(self.process, 'terminate'):
                    # Processus normal ou multiprocessing.Process
                    self.process.terminate()
                    
                    try:
                        if hasattr(self.process, 'wait'):
                            self.process.wait(timeout=5)
                        elif hasattr(self.process, 'join'):
                            self.process.join(timeout=5)
                        logger.info("Serveur arrêté proprement")
                    except (subprocess.TimeoutExpired, Exception):
                        logger.warning("Arrêt forcé du serveur")
                        if hasattr(self.process, 'kill'):
                            self.process.kill()
                            self.process.wait()
                        elif hasattr(self.process, 'terminate'):
                            self.process.terminate()
                            
            except Exception as e:
                logger.error(f"Erreur lors de l'arrêt du serveur: {e}")
                
            finally:
                self.process = None


class OptimPVApp:
    """Application principale OptimPV"""
    
    def __init__(self):
        self.server_manager = StreamlitServerManager()
        self.window = None
        self.admin_window = None
        self.url = None
        
    def setup_signal_handlers(self):
        """Configure les gestionnaires de signaux pour un arrêt propre"""
        def signal_handler(signum, frame):
            logger.info(f"Signal {signum} reçu, arrêt de l'application...")
            self.cleanup()
            sys.exit(0)
        
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
    
    def on_window_closed(self):
        """Callback appelé à la fermeture de la fenêtre"""
        logger.info("Fermeture de la fenêtre détectée - Serveur reste actif")
        print(f"\n🔄 Serveur OptimPV toujours actif sur: {self.url}")
        print("📝 Utilisez le panneau de contrôle pour arrêter le serveur")
        print("🌐 Vous pouvez rouvrir l'application en relançant le launcher")
        # Ne pas appeler self.cleanup() pour garder le serveur actif
    
    def show_admin_interface(self):
        """Affiche l'interface d'administration dans une nouvelle fenêtre"""
        if not ADMIN_MODULE_AVAILABLE:
            logger.warning("Module d'administration non disponible")
            return
            
        if self.url is None:
            logger.warning("Serveur non démarré, impossible d'ouvrir l'interface d'administration")
            return
            
        try:
            # Créer une URL pour l'admin (page spéciale)
            admin_url = self.url + "?admin=true"
            
            # Créer une nouvelle fenêtre pour l'administration
            self.admin_window = webview.create_window(
                title="OptimPV - Administration Réseau",
                url="admin_config.py",  # URL vers l'interface admin
                width=1200,
                height=800,
                min_size=(800, 600),
                resizable=True,
                on_top=True
            )
            
            logger.info("Interface d'administration ouverte")
            
        except Exception as e:
            logger.error(f"Erreur ouverture interface admin: {e}")
    
    def cleanup(self):
        """Nettoyage avant fermeture"""
        logger.info("Nettoyage en cours...")
        self.server_manager.stop_server()
        logger.info("Application fermée")
    
    def run(self, use_browser=False, keep_server_alive=False):
        """Lance l'application complète
        
        Args:
            use_browser (bool): Si True, ouvre dans le navigateur au lieu de pywebview
            keep_server_alive (bool): Si True, garde le serveur actif après fermeture de la fenêtre
        """
        try:
            logger.info("=== Démarrage OptimPV Desktop ===")
            
            # Configuration des gestionnaires de signaux
            self.setup_signal_handlers()
            
            # Démarrer le serveur Streamlit
            logger.info("Démarrage du serveur Streamlit...")
            self.url = self.server_manager.start_server()
            
            # Afficher les informations de configuration
            if ADMIN_MODULE_AVAILABLE and self.server_manager.admin_config:
                network_config = self.server_manager.admin_config.get_network_config()
                logger.info(f"Configuration réseau active:")
                logger.info(f"  - IP: {network_config['ip']}")
                logger.info(f"  Port: {network_config['port']}")
                logger.info(f"  Accès externe: {network_config['external_access']}")
                if network_config['custom_domain']:
                    logger.info(f"  - Domaine: {network_config['custom_domain']}")
            
            if use_browser:
                # Ouvrir dans le navigateur web par défaut
                logger.info(f"Ouverture dans le navigateur: {self.url}")
                webbrowser.open(self.url)
                
                # Attendre que l'utilisateur ferme manuellement
                print(f"\n🌐 OptimPV est ouvert dans votre navigateur: {self.url}")
                print("📝 Appuyez sur Ctrl+C pour arrêter le serveur")
                
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Arrêt demandé par l'utilisateur")
            else:
                # Créer la fenêtre native principale (comportement par défaut)
                logger.info("Création de l'interface native...")
                self.window = webview.create_window(
                    title="OptimPV - Optimisation Autoconsommation",
                    url=self.url,
                    width=1400,
                    height=900,
                    min_size=(1000, 700),
                    resizable=True,
                    fullscreen=False,
                    on_top=False
                )
                
                # Configurer les événements de fermeture
                if not keep_server_alive:
                    self.window.events.closed += self.on_window_closed
                else:
                    # Mode serveur persistant
                    def on_window_closed_persistent():
                        logger.info("Fenêtre fermée - Serveur reste actif")
                        print(f"\n🔄 Serveur OptimPV toujours actif sur: {self.url}")
                        print("📝 Appuyez sur Ctrl+C dans cette console pour arrêter le serveur")
                        print("🌐 Vous pouvez rouvrir l'application en relançant le launcher")
                    
                    self.window.events.closed += on_window_closed_persistent
                
                # Ajouter un menu pour l'administration si disponible
                if ADMIN_MODULE_AVAILABLE:
                    # Note: webview permet d'ajouter des menus personnalisés
                    # Pour simplifier, on affiche juste un log
                    logger.info("Interface d'administration disponible")
                    logger.info("Pour accéder à l'admin: Ctrl+Shift+A (si implémenté)")
                
                # Démarrer l'interface
                logger.info(f"Ouverture de l'interface sur {self.url}")
                webview.start(debug=False)
                
                # Après fermeture de la fenêtre, garder le serveur actif
                logger.info("Interface fermée - Serveur reste actif")
                print(f"\n🔄 Serveur OptimPV toujours actif sur: {self.url}")
                print("📝 Utilisez le panneau de contrôle pour arrêter le serveur")
                print("🌐 Appuyez sur Ctrl+C pour arrêter le serveur")
                
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Arrêt demandé par l'utilisateur")
            
        except KeyboardInterrupt:
            logger.info("Interruption clavier détectée")
        except Exception as e:
            logger.error(f"Erreur fatale: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Ne plus nettoyer automatiquement - le serveur reste actif
            # self.cleanup() sera appelé seulement via Ctrl+C ou panneau de contrôle
            pass


def check_dependencies():
    """Vérifie que toutes les dépendances sont présentes"""
    required_modules = ['streamlit', 'webview', 'requests', 'pandas', 'numpy']
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        logger.error(f"Modules manquants: {missing}")
        print(f"ERREUR: Modules manquants: {', '.join(missing)}")
        print("Installez-les avec: pip install " + " ".join(missing))
        return False
    
    return True


def show_startup_info():
    """Affiche les informations de démarrage"""
    logger.info("=== OptimPV Desktop - Informations de Démarrage ===")
    
    if ADMIN_MODULE_AVAILABLE:
        try:
            admin_config = NetworkAdminConfig()
            network_config = admin_config.get_network_config()
            
            logger.info("Configuration réseau:")
            logger.info(f"  IP: {network_config['ip']}")
            logger.info(f"  Port: {network_config['port']}")
            logger.info(f"  Accès externe: {'Activé' if network_config['external_access'] else 'Désactivé'}")
            
            if network_config['custom_domain']:
                logger.info(f"  Domaine personnalisé: {network_config['custom_domain']}")
            
            logger.info(f"  IPs autorisées: {', '.join(network_config['allowed_ips'])}")
            
        except Exception as e:
            logger.error(f"Erreur lecture config admin: {e}")
    else:
        logger.info("Configuration par défaut (127.0.0.1:8501)")
    
    logger.info("=" * 50)


def create_admin_launcher():
    """Crée un lanceur séparé pour l'interface d'administration"""
    if not ADMIN_MODULE_AVAILABLE:
        print("Module d'administration non disponible")
        return
    
    try:
        from admin_config import create_admin_interface
        create_admin_interface()
    except Exception as e:
        logger.error(f"Erreur lancement interface admin: {e}")


def main():
    """Point d'entrée principal"""
    # Changer vers le répertoire du script
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    logger.info(f"Répertoire de travail: {script_dir}")
    
    # Afficher les informations de démarrage
    show_startup_info()
    
    # Vérifier les dépendances
    if not check_dependencies():
        input("Appuyez sur Entrée pour fermer...")
        sys.exit(1)
    
    # Vérifier les arguments de ligne de commande
    if len(sys.argv) > 1:
        if sys.argv[1] == "--admin":
            logger.info("Lancement de l'interface d'administration")
            create_admin_launcher()
            return
        elif sys.argv[1] == "--browser":
            logger.info("Lancement avec ouverture dans le navigateur")
            app = OptimPVApp()
            app.run(use_browser=True)
            return
        elif sys.argv[1] == "--persistent":
            logger.info("Lancement en mode serveur persistant")
            app = OptimPVApp()
            app.run(keep_server_alive=True)
            return
        elif sys.argv[1] == "--help":
            print("\n🚀 OptimPV - Options de lancement:")
            print("  python launcher.py              → Interface desktop native (défaut)")
            print("  python launcher.py --browser    → Ouvre dans le navigateur web")
            print("  python launcher.py --persistent → Serveur reste actif après fermeture")
            print("  python launcher.py --admin      → Interface d'administration")
            print("  python launcher.py --help       → Affiche cette aide")
            return
    
    # Lancer l'application principale (interface native par défaut)
    app = OptimPVApp()
    app.run()


if __name__ == "__main__":
    main() 