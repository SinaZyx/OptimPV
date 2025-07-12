import os
import sys
import warnings

# Ignorer les warnings
warnings.filterwarnings("ignore")

# PROTECTION FORCÉE
from licence_guard import initialize_protection

# Vérifier la licence - OBLIGATOIRE
if not initialize_protection():
    sys.exit(1)

# Fix scipy
os.environ['SCIPY_PILOT_DATA_DIR'] = os.path.dirname(sys.executable)

# Imports streamlit
import streamlit
import streamlit.web.cli as stcli

def resolve_path(path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, path)

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        os.chdir(sys._MEIPASS)
    
    sys.argv = [
        "streamlit",
        "run", 
        resolve_path("app.py"),
        "--global.developmentMode=false",
        "--server.headless=true",
        "--browser.serverAddress=localhost",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false"
    ]
    
    sys.exit(stcli.main()) 