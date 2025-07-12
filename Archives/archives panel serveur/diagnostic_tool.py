# diagnostic_tool.py

import sys
import os
import platform
import importlib
import टाइम # Correction de l'erreur de frappe time -> time
from datetime import datetime

# Tentative d'import du logger global
try:
    from optimpv_main import logger
except (ImportError, ModuleNotFoundError):
    # Fallback logger si le logger principal n'est pas disponible
    import tempfile
    class DiagnosticFallbackLogger:
        def __init__(self, filepath):
            self.filepath = filepath
            self._log(f"=== DiagnosticFallbackLogger Initialized ({time.time()}) ===")
        def _log(self, msg, level="INFO"):
            formatted_msg = f"[{level}] {time.strftime('%Y-%m-%d %H:%M:%S')}: {msg}"
            print(formatted_msg)
            try:
                with open(self.filepath, 'a', encoding='utf-8') as f:
                    f.write(f"{formatted_msg}\n")
                    f.flush()
            except Exception:
                pass # Silencieux en cas d'échec du log de fallback
        def write(self, msg, level="INFO"): self._log(msg, level)
        def info(self, msg): self._log(msg, "INFO")
        def warning(self, msg): self._log(msg, "WARNING")
        def error(self, msg): self._log(msg, "ERROR")
    logger = DiagnosticFallbackLogger(os.path.join(tempfile.gettempdir(), f"diagnostic_tool_fallback_{os.getpid()}.log"))
    logger.info("DiagnosticTool: Global logger from optimpv_main not found. Using fallback.")

# Tentative d'import du PathManager
try:
    from Interface_serveur.server_control.core.path_manager import PathManager
    # Si PathManager est importé avec succès, on peut l'utiliser pour obtenir des chemins canoniques.
    # Exemple: app_root = PathManager.get_app_root()
except (ImportError, ModuleNotFoundError):
    logger.warning("DiagnosticTool: PathManager not found. Path information may be limited.")
    PathManager = None # Définir à None pour pouvoir vérifier son existence plus tard

def get_system_info():
    """Récupère les informations système de base."""
    logger.info("Gathering system information...")
    info = {
        "Timestamp": datetime.now().isoformat(),
        "Platform": platform.platform(),
        "Python Version": sys.version,
        "Python Executable": sys.executable,
        "Working Directory": os.getcwd(),
        "Frozen App (PyInstaller)": getattr(sys, 'frozen', False),
        "MEIPASS (PyInstaller Temp Dir)": getattr(sys, '_MEIPASS', 'N/A' if getattr(sys, 'frozen', False) else 'Not a frozen app'),
        "Command Line Arguments": sys.argv,
        "System Path": sys.path
    }
    if PathManager:
        try:
            info["App Root (PathManager)"] = str(PathManager.get_app_root())
            info["Security Dir (PathManager)"] = str(PathManager.get_security_dir())
        except Exception as e:
            logger.error(f"Error getting paths from PathManager: {e}")
            info["PathManager Error"] = str(e)
            
    logger.info("System information gathered.")
    return info

def check_critical_imports():
    """Vérifie une liste d'imports critiques pour l'application."""
    logger.info("Checking critical imports...")
    # Liste similaire à validate_build.py, mais peut être adaptée pour le runtime
    imports_to_check = [
        'streamlit', 'pandas', 'numpy', 'plotly', 'requests', 'psutil',
        'watchdog', 'wmi', 'win32com', 'win32api', 'pythoncom',
        # Modules internes (ajuster les chemins si nécessaire pour l'import runtime)
        # Ces chemins supposent que OptimPV est structuré pour que ces imports fonctionnent
        # Si ce script est à la racine, et que sys.path est correctement configuré par optimpv_main ou le hook.
        'Interface_serveur.server_control.core.path_manager',
        'Interface_serveur.server_control.core.config_manager',
        'Interface_serveur.server_control.core.error_handler',
        'Interface_serveur.server_control.security.hardware_protection',
        'Interface_serveur.server_control.security.usb_surveillance_exe',
        'Interface_serveur.server_control.security.lockdown_actions',
        'Interface_serveur.server_control.launchers.base_launcher',
        'app', # app.py
        'import_utils',
        'optimpv_main' # Le point d'entrée lui-même peut être vérifié s'il est importable
    ]
    results = {}
    for module_name in imports_to_check:
        try:
            importlib.import_module(module_name)
            results[module_name] = "OK"
            logger.info(f"Import check for '{module_name}': OK")
        except ImportError as e:
            results[module_name] = f"FAILED: {e}"
            logger.error(f"Import check for '{module_name}': FAILED - {e}")
        except Exception as e:
            results[module_name] = f"ERROR: {e}"
            logger.error(f"Import check for '{module_name}': ERROR - {e}")
    logger.info("Critical imports check complete.")
    return results

def check_config_files():
    """Vérifie la présence et l'accès aux fichiers de configuration principaux."""
    logger.info("Checking configuration files...")
    if not PathManager:
        logger.warning("PathManager not available, cannot perform detailed config file check.")
        return {"status": "PathManager not available, check skipped."}
        
    results = {}
    config_files_to_check = [
        "network_admin_config.json",
        "license.json",
        "security_config.json", # Exemple, si vous l'ajoutez
        "app_settings.json"   # Exemple
    ]
    for conf_file in config_files_to_check:
        try:
            path = PathManager.get_config_file(conf_file)
            if path and path.exists():
                results[conf_file] = f"Found at: {path} (Readable: {os.access(path, os.R_OK)})"
                logger.info(f"Config file '{conf_file}' found at {path}.")
            else:
                results[conf_file] = f"NOT FOUND (PathManager default was: {path})"
                logger.warning(f"Config file '{conf_file}' NOT FOUND. PathManager default: {path}")
        except Exception as e:
            results[conf_file] = f"Error checking: {e}"
            logger.error(f"Error checking config file '{conf_file}': {e}")
    logger.info("Configuration files check complete.")
    return results

def run_full_diagnostic():
    """Exécute une suite complète de diagnostics et retourne un rapport."""
    logger.info("=== Starting Full Diagnostic ===")
    report_parts = []

    report_parts.append("OptimPV Diagnostic Report")
    report_parts.append("=" * 30)

    # 1. System Information
    report_parts.append("\n--- System Information ---")
    system_info = get_system_info()
    for key, value in system_info.items():
        report_parts.append(f"{key}: {value}")

    # 2. Critical Imports Check
    report_parts.append("\n--- Critical Imports Check ---")
    import_results = check_critical_imports()
    for module, status in import_results.items():
        report_parts.append(f"Import '{module}': {status}")

    # 3. Configuration Files Check
    report_parts.append("\n--- Configuration Files Check ---")
    config_file_results = check_config_files()
    for file, status in config_file_results.items():
        report_parts.append(f"Config File '{file}': {status}")
        
    # 4. USB Drive Check (Exemple basique)
    report_parts.append("\n--- Basic USB Drive Check (G:) ---")
    try:
        g_drive = "G:/"
        if os.path.exists(g_drive):
            report_parts.append(f"Drive {g_drive} is accessible.")
            # Vous pourriez ajouter une vérification pour sys.dat ici si vous voulez
            # token_path = os.path.join(g_drive, "sys.dat")
            # report_parts.append(f"Token file {token_path} exists: {os.path.exists(token_path)}")
        else:
            report_parts.append(f"Drive {g_drive} is NOT accessible.")
    except Exception as e:
        report_parts.append(f"Error checking drive {g_drive}: {e}")

    report_parts.append("\n" + "="*30)
    report_parts.append("End of Diagnostic Report")
    logger.info("=== Full Diagnostic Complete ===")
    
    # Joindre toutes les parties du rapport en une seule chaîne
    return "\n".join(report_parts)

if __name__ == '__main__':
    # Ce bloc permet d'exécuter le diagnostic directement
    # python diagnostic_tool.py
    print("Running diagnostic tool directly...")
    diagnostic_report = run_full_diagnostic()
    print("\n--- DIAGNOSTIC REPORT START ---")
    print(diagnostic_report)
    print("--- DIAGNOSTIC REPORT END ---")
    
    # Sauvegarder aussi dans un fichier si exécuté directement
    report_filename = f"optimpv_diagnostic_direct_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_filename, 'w', encoding='utf-8') as f_report:
        f_report.write(diagnostic_report)
    print(f"\nReport also saved to: {os.path.abspath(report_filename)}")
    print(f"Diagnostic tool log available at: {LOG_FILE}") 