"""
OptimPV Launcher SANS BOUCLE - Une seule instance
AVEC PROTECTION LICENCE
"""

import sys
import os
import subprocess
import time
import webbrowser
import socket
import datetime
import traceback

# PROTECTION LICENCE - VERIFICATION AU DEMARRAGE
try:
    from licence_guard import initialize_protection
    print("[PROTECTION] Verification de la licence...")
    if not initialize_protection():
        print("[PROTECTION] ACCES REFUSE - Licence invalide")
        sys.exit(1)
    print("[PROTECTION] Licence validee - Acces autorise")
except ImportError:
    print("[PROTECTION] ERREUR - Module licence_guard introuvable")
    sys.exit(1)
except Exception as e:
    print(f"[PROTECTION] ERREUR - {e}")
    sys.exit(1)

# Configuration du log (DESACTIVE pour mode final)
LOG_FILE = None

def write_log(message):
    """Ecrire dans le fichier log (desactive)"""
    # Log desactive pour executable final
    pass

def log_system_info():
    """Logger les informations système"""
    write_log("=== DEBUT SESSION OPTIMPV ===")
    write_log(f"Python executable: {sys.executable}")
    write_log(f"Frozen (PyInstaller): {getattr(sys, 'frozen', False)}")
    if getattr(sys, 'frozen', False):
        write_log(f"_MEIPASS: {sys._MEIPASS}")
    write_log(f"Working directory: {os.getcwd()}")
    write_log(f"Script path: {__file__}")

def find_app_file():
    """Trouve le fichier app.py"""
    write_log("Recherche du fichier app.py...")
    
    if getattr(sys, 'frozen', False):
        write_log("Mode PyInstaller détecté")
        # Dans PyInstaller, app.py est dans _MEIPASS
        base_dir = sys._MEIPASS
        app_path = os.path.join(base_dir, "app.py")
        write_log(f"Tentative 1: {app_path}")
        
        if os.path.exists(app_path):
            write_log(f"TROUVE: {app_path}")
            return app_path
        
        # Si pas trouvé, chercher dans le répertoire de l'exe
        exe_dir = os.path.dirname(sys.executable)
        app_path = os.path.join(exe_dir, "app.py")
        write_log(f"Tentative 2: {app_path}")
        
        if os.path.exists(app_path):
            write_log(f"TROUVE: {app_path}")
            return app_path
            
        # Lister le contenu de _MEIPASS pour debug
        write_log(f"Contenu de _MEIPASS ({base_dir}):")
        try:
            for item in os.listdir(base_dir):
                write_log(f"  - {item}")
        except Exception as e:
            write_log(f"Erreur listage _MEIPASS: {e}")
            
        # Si toujours pas trouvé, utiliser le chemin direct
        write_log("Fallback: utilisation de 'app.py' direct")
        return "app.py"
    else:
        write_log("Mode développement")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.join(base_dir, "app.py")
        write_log(f"Chemin dev: {app_path}")
        
        if os.path.exists(app_path):
            write_log(f"TROUVE: {app_path}")
            return app_path
        else:
            write_log("NON TROUVE en mode dev")
            return None

def check_port_available(port):
    """Verifie si un port est disponible"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.bind(('localhost', port))
            return True
    except:
        return False

def check_port_in_use(port):
    """Verifie si un port est deja utilise par Streamlit"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            result = s.connect_ex(('localhost', port))
            if result == 0:
                # Port ouvert, verifier si c'est Streamlit
                try:
                    import requests
                    response = requests.get(f'http://localhost:{port}', timeout=3)
                    if 'streamlit' in response.text.lower():
                        write_log(f"Port {port} deja utilise par Streamlit")
                        return True
                except:
                    pass
            return False
    except:
        return False

def find_available_port():
    """Trouve un port disponible"""
    for port in [8501, 8502, 8503, 8504, 8505]:
        if check_port_available(port):
            return port
    return None

def main():
    """Point d'entree principal - UNE SEULE EXECUTION"""
    try:
        log_system_info()
        
        print("=" * 60)
        print("    OPTIMPV - LANCEMENT UNIQUE")
        print("=" * 60)
        write_log("Démarrage de OptimPV")
        
        # 1. Verifier app.py
        print("[INFO] Recherche de l'application...")
        write_log("Recherche de l'application...")
        app_path = find_app_file()
        
        if not app_path:
            write_log("ERREUR: app.py non trouvé!")
            print("[ERROR] Fichier app.py non trouve!")
            return 1
        
        # Vérifier si c'est un chemin complet ou relatif
        if os.path.exists(app_path):
            write_log(f"Application trouvée: {app_path}")
            print(f"[OK] Application trouvee: {app_path}")
        else:
            write_log(f"Application (module): {app_path}")
            print(f"[OK] Application (module): {app_path}")
            # Dans PyInstaller, streamlit peut trouver app.py dans _MEIPASS
        
        # 2. Verifier si Streamlit tourne deja
        print("[INFO] Verification des ports existants...")
        write_log("Verification des ports existants...")
        for existing_port in [8501, 8502, 8503, 8504, 8505]:
            if check_port_in_use(existing_port):
                write_log(f"OptimPV deja actif sur port {existing_port}")
                print(f"[INFO] OptimPV deja actif sur http://localhost:{existing_port}")
                print(f"[INFO] Ouverture du navigateur...")
                try:
                    webbrowser.open(f"http://localhost:{existing_port}")
                    write_log("Navigateur ouvert vers instance existante")
                    print("[OK] Navigateur ouvert - OptimPV est pret!")
                    print("[INFO] Appuyez sur Entree pour fermer...")
                    input()
                    return 0
                except Exception as e:
                    write_log(f"Erreur ouverture navigateur: {e}")
        
        # 3. Trouver un port libre
        print("[INFO] Recherche d'un port disponible...")
        write_log("Recherche d'un port disponible...")
        port = find_available_port()
        
        if not port:
            write_log("ERREUR: Aucun port libre trouvé")
            print("[ERROR] Aucun port libre trouve (8501-8505)")
            return 1
        
        write_log(f"Port {port} disponible")
        print(f"[OK] Port {port} disponible")
        
        # 3. Lancer Streamlit UNE SEULE FOIS
        url = f"http://localhost:{port}"
        write_log(f"URL: {url}")
        print(f"[INFO] Lancement UNIQUE de OptimPV sur {url}...")
        
    except Exception as e:
        write_log(f"ERREUR dans main(): {e}")
        write_log(f"Traceback: {traceback.format_exc()}")
        print(f"[ERROR] Erreur: {e}")
        return 1
    
    try:
        # Différent comportement selon le mode (dev vs exe)
        if getattr(sys, 'frozen', False):
            # Mode PyInstaller - lancer directement l'app
            write_log("Mode PyInstaller - lancement direct")
            print("[INFO] Mode executable - lancement direct...")
            
            try:
                # Changer le répertoire de travail vers _MEIPASS
                original_cwd = os.getcwd()
                write_log(f"Changement répertoire: {original_cwd} -> {sys._MEIPASS}")
                os.chdir(sys._MEIPASS)
                
                # Importer et lancer l'app directement
                write_log("Import de streamlit.web.cli...")
                import streamlit.web.cli as stcli
                
                # Arguments pour streamlit avec mode production
                args = [
                    "streamlit", "run", "app.py",
                    "--server.port", str(port),
                    "--server.headless", "true", 
                    "--browser.gatherUsageStats", "false",
                    "--global.developmentMode", "false"
                ]
                
                write_log(f"Arguments Streamlit: {args}")
                sys.argv = args
                
                print("[INFO] Demarrage Streamlit integre...")
                print("[INFO] Ouverture automatique du navigateur...")
                
                # Ouvrir le navigateur apres un delai
                import threading
                def open_browser():
                    time.sleep(3)
                    try:
                        webbrowser.open(url)
                        write_log("Navigateur ouvert automatiquement")
                    except Exception as e:
                        write_log(f"Erreur ouverture navigateur: {e}")
                
                threading.Thread(target=open_browser, daemon=True).start()
                
                write_log("Appel de stcli.main()...")
                print("[OK] OptimPV demarre...")
                print(f"[OK] URL: {url}")
                print("[INFO] ** ATTENTION: Ne fermez PAS cette console **")
                print("[INFO] ** La fermer arretera OptimPV **")
                print("[INFO] ** Utilisez Ctrl+C pour arreter proprement **")
                
                stcli.main()
                write_log("stcli.main() terminé")
                
            except Exception as e:
                write_log(f"ERREUR mode PyInstaller: {e}")
                write_log(f"Traceback: {traceback.format_exc()}")
                raise
            
        else:
            # Mode développement - utiliser subprocess normalement
            write_log("Mode développement - utilisation os.execv")
            cmd = [
                sys.executable, "-m", "streamlit", "run", app_path,
                "--server.port", str(port),
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false"
            ]
            
            write_log(f"Commande execv: {cmd}")
            print("[INFO] Demarrage Streamlit...")
            
            # IMPORTANT: exec remplace le processus actuel
            # Pas de subprocess = pas de boucle
            os.execv(sys.executable, cmd)
        
        # Ce code ne sera JAMAIS atteint car exec remplace le processus
        
    except Exception as e:
        write_log(f"ERREUR GENERALE: {e}")
        write_log(f"Traceback complet: {traceback.format_exc()}")
        print(f"[ERROR] Erreur lors du lancement: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        write_log(f"=== FIN SESSION - Code: {exit_code} ===")
        sys.exit(exit_code)
    except Exception as e:
        write_log(f"ERREUR FATALE: {e}")
        write_log(f"Traceback: {traceback.format_exc()}")
        print(f"[FATAL] {e}")
        sys.exit(1)