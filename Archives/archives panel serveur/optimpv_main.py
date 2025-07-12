#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OptimPV - Point d'entrée principal EXE avec protections avancées
===============================================================
"""

import os
import time
import sys

# Déplacons l'initialisation du logger et l'ajout du diagnostic tout en haut du fichier,
# après les imports initiaux de os, time, sys.

def setup_early_logging():
    """Configuration de logging immédiate et robuste"""
    import tempfile
    log_dir = tempfile.gettempdir()  # Toujours accessible
    log_file = os.path.join(log_dir, f"optimpv_startup_{os.getpid()}.log")
    
    # Logger basique qui écrit TOUJOURS
    class SimpleLogger:
        def __init__(self, filepath):
            self.filepath = filepath
            self.write(f"=== STARTUP {time.time()} ===")
        
        def write(self, msg):
            with open(self.filepath, 'a', encoding='utf-8') as f:
                f.write(f"{msg}\n")
                f.flush()
            print(msg)  # Double sortie console
    
    return SimpleLogger(log_file)

logger = setup_early_logging()

# --- MODE DIAGNOSTIC ---
# Placé ici, après l'initialisation du logger et les imports de base.
if '--diagnose' in sys.argv:
    logger.write("Diagnostic mode activated.", level="INFO") # Utiliser la méthode du logger avec niveau
    try:
        from diagnostic_tool import run_full_diagnostic
        report = run_full_diagnostic()
        
        # Afficher le rapport sur la console (sera aussi loggué par le logger via print)
        print("\n--- OPTIMPV DIAGNOSTIC REPORT ---")
        print(report)
        print("--- END OF DIAGNOSTIC REPORT ---\n")
        
        if '--save-report' in sys.argv:
            report_filename = 'diagnostic_report.txt'
            try:
                with open(report_filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                logger.write(f"Diagnostic report saved to {os.path.abspath(report_filename)}", level="INFO")
            except Exception as e_save:
                logger.write(f"Failed to save diagnostic report to {report_filename}: {e_save}", level="ERROR")
        
        # Après le diagnostic, on quitte l'application pour ne pas continuer le démarrage normal.
        logger.write("Diagnostic complete. Exiting application.", level="INFO")
        sys.exit(0)
        
    except ImportError as e_diag_import:
        logger.write(f"Could not import diagnostic_tool: {e_diag_import}. Cannot run diagnostics.", level="ERROR")
        # On pourrait choisir de quitter ici aussi si le diagnostic est critique
        # sys.exit(1)
    except Exception as e_diag:
        logger.write(f"An error occurred during diagnostic mode: {e_diag}", level="ERROR")
        # sys.exit(1)

# --- DÉBOGAGE ULTRA-PRÉCOCE AVEC PAUSES ---
logger.write("=== DÉMARRAGE IMMÉDIAT optimpv_main.py ===")
logger.write("Console ouverte - script Python en cours d'exécution...")

logger.write(f"Python version: {sys.version}")
logger.write(f"Executable: {sys.executable}")
logger.write(f"Mode frozen: {getattr(sys, 'frozen', False)}")
logger.write(f"Répertoire courant: {os.getcwd()}")

# Forcer l'affichage immédiat
sys.stdout.flush()
sys.stderr.flush()

logger.write("Pause de 5 secondes pour vérifier que la console reste ouverte...")
time.sleep(5)
logger.write("Pause terminée, continuation du script...")

# --- JOURNALISATION ULTRA-PRÉCOCE ---
# Configuration de base avant même les imports
logger.write("Début de la configuration de journalisation (ancienne méthode)...")

logger.write("Pause de 3 secondes avant les imports...")
time.sleep(3)

# --- IMPORTS AVEC JOURNALISATION ---
logger.write("Début des imports")

try:
    from pathlib import Path
    logger.write("Import pathlib: OK")
except Exception as e:
    logger.write(f"Import pathlib: ERREUR - {e}")

try:
    import threading
    logger.write("Import threading: OK")
except Exception as e:
    logger.write(f"Import threading: ERREUR - {e}")

try:
    import traceback
    logger.write("Import traceback: OK")
except Exception as e:
    logger.write(f"Import traceback: ERREUR - {e}")

try:
    import logging
    logger.write("Import logging: OK")
except Exception as e:
    logger.write(f"Import logging: ERREUR - {e}")

logger.write("Tous les imports de base terminés")

logger.write("Pause de 3 secondes avant la configuration logging avancée...")
time.sleep(3)

# --- CONFIGURATION LOGGING AVANCÉE ---
# L'ancien système de logging est désactivé au profit du SimpleLogger
# Si un logging plus avancé est nécessaire plus tard, il faudra l'intégrer
# avec le logger SimpleLogger ou le remplacer consciemment.
logger.write("Configuration logging avancée (ancienne méthode) - maintenant gérée par SimpleLogger.")

logger.write("--- DÉBUT CONFIGURATION CHEMINS ---")

logger.write("Pause de 3 secondes avant la configuration des chemins...")
time.sleep(3)

# Configuration des chemins pour l'EXE
if getattr(sys, 'frozen', False):
    logger.write("Application détectée comme 'frozen' (EXE)")
    
    if hasattr(sys, '_MEIPASS'):
        application_path = Path(sys._MEIPASS)
        logger.write(f"_MEIPASS détecté: {application_path}")
    else:
        application_path = Path(sys.executable).parent
        logger.write(f"Pas de _MEIPASS, application_path basé sur sys.executable: {application_path}")
    
    try:
        logger.write(f"Contenu de application_path ({application_path}):")
        for item in os.listdir(application_path):
            logger.write(f"  - {item}")
    except Exception as e_ls:
        logger.write(f"Erreur lors du listage de application_path: {e_ls}")
    
    if str(application_path) not in sys.path:
        sys.path.insert(0, str(application_path))
        logger.write(f"Ajout de {application_path} à sys.path")
    else:
        logger.write(f"{application_path} est déjà dans sys.path")
else:
    application_path = Path(__file__).parent if "__file__" in globals() else Path.cwd()
    if str(application_path) not in sys.path:
        sys.path.insert(0, str(application_path))
    logger.write(f"Mode développement, application_path: {application_path}")

logger.write(f"sys.path actuel: {sys.path}")

logger.write("Pause de 5 secondes avant l'import du module principal...")
time.sleep(5)

logger.write("--- DÉBUT IMPORT MODULE PRINCIPAL ---")

# Import du module principal avec protection
try:
    logger.write("Tentative d'importation de 'integration_protection_exe'...")
    
    from integration_protection_exe import start_optimpv_with_protection
    
    logger.write("'integration_protection_exe' importé avec succès")
    
    logger.write("Pause de 3 secondes avant l'appel de start_optimpv_with_protection()...")
    time.sleep(3)
    
    logger.write("Appel de start_optimpv_with_protection()...")
    
    start_optimpv_with_protection()
    
    logger.write("start_optimpv_with_protection() terminé")

except ImportError as e_import:
    logger.write(f"ERREUR D'IMPORTATION DÉTAILLÉE: {e_import}")
    # logger.write(f"Traceback complet: {traceback.format_exc()}") # traceback n'est pas formaté ici directement
    
    logger.write("Modules de protection non trouvés")
    
    logger.write("Pause de 10 secondes pour examiner l'erreur...")
    time.sleep(10)
    
    logger.write("Tentative de démarrage en mode dégradé...")
    
    try:
        logger.write("Tentative d'importation de 'optimpv_main_original'...")
        
        from optimpv_main_original import main
        
        logger.write("'optimpv_main_original' importé avec succès")
        
        main()
    except ImportError as e_fallback_import:
        logger.write(f"ERREUR D'IMPORTATION FALLBACK: {e_fallback_import}")
        # logger.write(f"Traceback complet: {traceback.format_exc()}")
        
        logger.write("Impossible de démarrer l'application (même en mode dégradé)")
        
        logger.write("Pause de 30 secondes avant fermeture...")
        if getattr(sys, 'frozen', False):
            time.sleep(30)
        sys.exit(1)
    except Exception as e_fallback_other:
        logger.write(f"ERREUR INATTENDUE FALLBACK: {e_fallback_other}")
        # logger.write(f"Traceback complet: {traceback.format_exc()}")
        
        logger.write("Impossible de démarrer l'application (erreur inattendue en mode dégradé)")
        
        logger.write("Pause de 30 secondes avant fermeture...")
        if getattr(sys, 'frozen', False):
            time.sleep(30)
        sys.exit(1)

except Exception as e_main:
    logger.write(f"ERREUR GÉNÉRALE DANS optimpv_main.py: {e_main}")
    # logger.write(f"Traceback complet: {traceback.format_exc()}")
    
    logger.write("Pause de 30 secondes avant fermeture...")
    if getattr(sys, 'frozen', False):
        time.sleep(30)
    sys.exit(1)

logger.write("--- FIN optimpv_main.py ---")

logger.write("Pause finale de 10 secondes...")
time.sleep(10)
logger.write("Script terminé normalement.")

# Le code de diagnostic doit être ajouté AVANT sys.exit() si on veut qu'il s'exécute
# Cependant, la structure actuelle du script optimpv_main.py semble être un wrapper
# qui lance ensuite d'autres choses. Le diagnostic devrait idéalement être tout au début.
