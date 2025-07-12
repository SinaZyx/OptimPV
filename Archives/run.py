import os
import sys
import warnings

# Ignorer les warnings
warnings.filterwarnings("ignore")

# Fix pour scipy/seaborn - DOIT ETRE FAIT AVANT TOUTE IMPORTATION
os.environ['SCIPY_PILOT_DATA_DIR'] = os.path.dirname(sys.executable)

# Patch critique pour scipy AVANT l'importation
def patch_scipy_early():
    """Patch critique pour scipy execute avant toute importation"""
    # Methode 1: Patcher le module avant import
    import importlib
    import importlib.util
    
    # Intercepter l'import de scipy.stats._distn_infrastructure
    original_import = __builtins__.__import__
    
    def scipy_import_wrapper(name, globals=None, locals=None, fromlist=(), level=0):
        if 'scipy.stats._distn_infrastructure' in name:
            try:
                # Importer le module
                module = original_import(name, globals, locals, fromlist, level)
                # S'assurer que obj existe avant del obj
                if hasattr(module, '__dict__') and 'obj' not in module.__dict__:
                    module.obj = object()
                return module
            except Exception:
                pass
        
        return original_import(name, globals, locals, fromlist, level)
    
    __builtins__.__import__ = scipy_import_wrapper
    
    # Methode 2: Pre-definir dans sys.modules si necessaire
    try:
        import scipy.stats._distn_infrastructure as distn
        if not hasattr(distn, 'obj'):
            distn.obj = object()
    except ImportError:
        pass
    except Exception:
        pass

# Appliquer le patch immediatement
patch_scipy_early()

# Maintenant importer streamlit
import streamlit
import streamlit.web.cli as stcli

def resolve_path(path):
    if getattr(sys, 'frozen', False):
        # Si compile avec PyInstaller
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, path)

if __name__ == "__main__":
    # Definir le repertoire de travail
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
