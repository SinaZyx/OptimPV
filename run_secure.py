import os
import sys
import warnings
import multiprocessing

# Ignorer les warnings
warnings.filterwarnings("ignore")

# PROTECTION FORCÉE
from licence_guard import initialize_protection

# Vérifier la licence - OBLIGATOIRE
if not initialize_protection():
    sys.exit(1)

# Fix scipy
os.environ['SCIPY_PILOT_DATA_DIR'] = os.path.dirname(sys.executable)

def resolve_path(path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, path)

if __name__ == "__main__":
    # Support pour les processus gelés (frozen) - CRUCIAL pour PyInstaller
    multiprocessing.freeze_support()
    
    # Lancer le panel d'administration d'abord
    import streamlit.web.cli as stcli
    import threading
    import time
    import webbrowser
    
    # Trouver app.py
    app_path = resolve_path("app.py")
    
    # Configuration Streamlit pour l'application principale
    main_port = "8507"  # Port principal
    sys.argv = [
        "streamlit", "run", app_path,
        "--server.port", main_port,
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--server.runOnSave", "false",
        "--logger.level", "warning",
        "--global.developmentMode", "false"
    ]
    
    # Afficher des informations de debug
    print(f"OptimPV Starting...")
    print(f"App: {app_path}")
    print(f"Port: {main_port}")
    print("="*50)
    print("UTILISATION:")
    print(f"1. Application: http://localhost:{main_port}")
    print("2. Choisir 'Administration' pour vous connecter")
    print("3. Mot de passe par défaut: 'password'")
    print("4. Puis choisir 'Application OptimPV'")
    print("="*50)
    
    # Fonction pour ouvrir le navigateur après un délai
    def open_browser():
        time.sleep(3)  # Attendre que le panel démarre
        try:
            url = f'http://localhost:{main_port}'
            print(f"Opening main app: {url}")
            webbrowser.open(url)
        except Exception as e:
            print(f"Browser open failed: {e}")
    
    # Lancer l'ouverture du navigateur en arrière-plan
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Lancer le panel d'administration
    sys.exit(stcli.main()) 