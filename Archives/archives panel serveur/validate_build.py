import importlib
import sys
import os
import tempfile
import time

# Configuration du logger pour ce script de validation
# Ce logger est indépendant de celui de l'application principale
LOG_DIR = tempfile.gettempdir()
LOG_FILE = os.path.join(LOG_DIR, f"optimpv_validate_build_{os.getpid()}.log")

class ValidationLogger:
    def __init__(self, filepath):
        self.filepath = filepath
        self._log(f"=== VALIDATE BUILD SCRIPT START ({time.time()}) ===")

    def _log(self, msg, console_too=True):
        with open(self.filepath, 'a', encoding='utf-8') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
            f.flush()
        if console_too:
            print(msg)
    
    def info(self, msg):
        self._log(f"[INFO] {msg}")

    def warning(self, msg):
        self._log(f"[WARNING] {msg}")

    def error(self, msg):
        self._log(f"[ERROR] {msg}")

logger = ValidationLogger(LOG_FILE)

# Définition de la racine du projet pour aider à la résolution des imports locaux
# Ce script (`validate_build.py`) est supposé être à la racine du projet.
# Si ce n'est pas le cas, ce chemin doit être ajusté.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Ajouter temporairement des chemins à sys.path pour aider à trouver les modules locaux
# Ceci est particulièrement utile si le script est exécuté depuis un autre répertoire
# ou si la structure du projet est complexe.
PATHS_TO_ADD = [
    PROJECT_ROOT, # Racine du projet
    os.path.join(PROJECT_ROOT, "Interface serveur"),
    os.path.join(PROJECT_ROOT, "Interface serveur", "server_control"),
    os.path.join(PROJECT_ROOT, "Interface serveur", "server_control", "core"),
    os.path.join(PROJECT_ROOT, "Interface serveur", "server_control", "security"),
    os.path.join(PROJECT_ROOT, "Interface serveur", "server_control", "launchers"),
    # Ajoutez d'autres chemins si nécessaire pour vos modules custom
]

for p_add in PATHS_TO_ADD:
    if p_add not in sys.path:
        sys.path.insert(0, p_add)
        logger.info(f"Added to sys.path: {p_add}")

logger.info(f"Current sys.path (first 5 entries): {sys.path[:5]}")

def validate_imports(imports_to_check: list):
    """Teste une liste d'imports critiques.
    Retourne une liste des imports qui ont échoué.
    """
    logger.info("--- Starting Critical Import Validation ---")
    failed_imports = []
    
    for module_name in imports_to_check:
        try:
            logger.info(f"Attempting to import: '{module_name}'...")
            # Utiliser importlib.import_module pour un contrôle plus fin
            importlib.import_module(module_name)
            logger.info(f"  SUCCESS: '{module_name}' imported successfully.")
        except ImportError as e:
            logger.error(f"  FAILURE: '{module_name}' failed to import. Error: {e}")
            failed_imports.append((module_name, str(e)))
        except Exception as e:
            logger.error(f"  FAILURE: '{module_name}' failed with an unexpected error during import: {e}")
            failed_imports.append((module_name, f"Unexpected error: {str(e)}"))
            
    if not failed_imports:
        logger.info("All critical imports validated successfully!")
    else:
        logger.warning("Some critical imports failed.")
        
    logger.info("--- Critical Import Validation Complete ---")
    return failed_imports

def main():
    logger.info("Starting OptimPV Build Validation Script...")

    # Liste des imports critiques à vérifier
    # Adaptez cette liste en fonction des dépendances réelles et critiques de votre application
    critical_imports = [
        # Bibliothèques tierces majeures
        'streamlit',
        'pandas',
        'numpy',
        'plotly',
        'requests',
        'psutil',
        'watchdog',
        'wmi',          # Pour la surveillance USB sur Windows
        'win32com',     # Pour la détection USB et autres tâches Windows
        'win32api',     # Partie de pywin32
        'pythoncom',    # Partie de pywin32
        
        # Modules internes de OptimPV (utilisez le nom d'importation Python complet)
        # Core modules
        'core.path_manager',      # Assumant qu'il est dans server_control.core
        'core.config_manager',    # Assumant qu'il est dans server_control.core
        'core.error_handler',     # Assumant qu'il est dans server_control.core
        
        # Security modules
        'security.hardware_protection',
        'security.usb_surveillance_exe',
        'security.lockdown_actions',
        'security.integration_protection_exe',
        
        # Launcher modules
        'launchers.base_launcher', # La classe de base des lanceurs
        # 'launchers.main_launcher', # Si vous avez un lanceur principal spécifique
        
        # Point d'entrée principal de l'application (si importable comme module)
        # 'optimpv_main', # Attention, ce script a beaucoup d'effets de bord au chargement
        
        # Application principale Streamlit (si elle a une logique importable)
        'app', # Fichier app.py à la racine
        
        # Autres modules custom importants
        'import_utils', # Fichier import_utils.py à la racine
        # 'network_admin_config' # Si c'est un module Python et non juste un JSON
    ]

    failed = validate_imports(critical_imports)

    if failed:
        logger.error("\n=== VALIDATION FAILED ===")
        logger.error("The following critical imports could not be resolved:")
        for module, error in failed:
            logger.error(f"  - Module: {module}, Error: {error}")
        logger.error("Please check your environment, PYTHONPATH, and aidentified module paths.")
        logger.error("Validation script log: " + LOG_FILE)
        sys.exit(1) # Quitter avec un code d'erreur si des imports échouent
    else:
        logger.info("\n=== VALIDATION SUCCESSFUL ===")
        logger.info("All critical imports are resolved.")
        logger.info("Validation script log: " + LOG_FILE)
        sys.exit(0) # Quitter avec succès

if __name__ == "__main__":
    main() 