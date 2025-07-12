#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Compilation OptimPV - Version avec Protection USB
==========================================================
"""

import os
import sys
import subprocess
import shutil
import time
from pathlib import Path
import logging

# Logger global pour le script de build
logger = logging.getLogger("OptimPVBuilder")

def setup_logging():
    """Configure le logging pour le script OptimPVBuilder."""
    log_file = Path("build_optimpv.log") 
    logger.setLevel(logging.INFO) 

    # Supprimer les anciens handlers pour éviter la duplication de logs si le script est appelé plusieurs fois
    if logger.hasHandlers():
        logger.handlers.clear()

    # Handler pour fichier
    fh = logging.FileHandler(log_file, mode='w', encoding='utf-8') # mode 'w' pour écraser à chaque build
    fh.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s - %(filename)s:%(lineno)d - %(message)s"))
    logger.addHandler(fh)

    # Handler pour console
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s")) 
    logger.addHandler(ch)
    
    logger.info("Logging pour OptimPVBuilder initialisé.")
    return logger

SECURITY_MODULES_DIR = Path("Interface serveur/server_control/security")

def print_banner():
    """Affiche la bannière de compilation"""
    print("=" * 60)
    print("           OPTIMPV - COMPILATION EXE SÉCURISÉE")
    print("=" * 60)
    print("[SECURITE] Protections incluses :")
    print("  • Protection USB avec surveillance temps réel")
    print("  • Authentification MAC avec liste blanche")
    print("  • Lockdown automatique en cas de violation")
    print("  • Suppression sécurisée de l'EXE")
    print("  • Fermeture forcée des navigateurs")
    print("=" * 60)

def create_main_entry_point():
    """Crée le point d'entrée principal avec gestion d'erreur détaillée et journalisation"""
    main_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OptimPV - Point d'entrée principal EXE avec protections avancées
===============================================================
"""

# --- JOURNALISATION ULTRA-PRÉCOCE ---
# Configuration de base avant même les imports
import sys
import os

# Créer un fichier de log simple dès le début
try:
    # Essayer plusieurs emplacements pour le log
    log_locations = [
        os.path.join(os.environ.get('APPDATA', ''), 'OptimPV', 'Logs', 'optimpv_exe_debug.log'),
        os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), 'optimpv_exe_debug.log'),
        'optimpv_exe_debug.log'
    ]
    
    log_file = None
    for log_path in log_locations:
        try:
            # Créer le répertoire si nécessaire
            log_dir = os.path.dirname(log_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            # Tester l'écriture
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write("=== DÉMARRAGE OPTIMPV EXE ===\\n")
                f.write(f"Timestamp: {__import__('time').time()}\\n")
                f.write(f"Python version: {sys.version}\\n")
                f.write(f"Executable: {sys.executable}\\n")
                f.write(f"Mode frozen: {getattr(sys, 'frozen', False)}\\n")
                f.write(f"Log file: {log_path}\\n")
                f.write("\\n")
            
            log_file = log_path
            break
        except Exception as e:
            continue
    
    if not log_file:
        # Dernier recours: écrire dans le répertoire courant
        log_file = 'optimpv_emergency.log'
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("=== DÉMARRAGE OPTIMPV EXE (EMERGENCY LOG) ===\\n")
    
    # Fonction de log simple
    def log_message(message, level="INFO"):
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                timestamp = __import__('time').strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {level}: {message}\\n")
                f.flush()
        except:
            pass
    
    log_message("Configuration de journalisation simple réussie", "INFO")
    
except Exception as e:
    # Si même la journalisation simple échoue, continuer sans
    def log_message(message, level="INFO"):
        pass

# --- IMPORTS AVEC JOURNALISATION ---
log_message("Début des imports", "DEBUG")

try:
    from pathlib import Path
    log_message("Import pathlib: OK", "DEBUG")
except Exception as e:
    log_message(f"Import pathlib: ERREUR - {e}", "ERROR")

try:
    import time
    log_message("Import time: OK", "DEBUG")
except Exception as e:
    log_message(f"Import time: ERREUR - {e}", "ERROR")

try:
    import threading
    log_message("Import threading: OK", "DEBUG")
except Exception as e:
    log_message(f"Import threading: ERREUR - {e}", "ERROR")

try:
    import traceback
    log_message("Import traceback: OK", "DEBUG")
except Exception as e:
    log_message(f"Import traceback: ERREUR - {e}", "ERROR")

try:
    import logging
    log_message("Import logging: OK", "DEBUG")
except Exception as e:
    log_message(f"Import logging: ERREUR - {e}", "ERROR")

log_message("Tous les imports de base terminés", "INFO")

# --- CONFIGURATION LOGGING AVANCÉE ---
try:
    if log_file:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            filename=log_file,
            filemode='a'  # Append au fichier déjà créé
        )
        logging.info("=== CONFIGURATION LOGGING AVANCÉE ===")
        logging.info(f"Fichier de log: {log_file}")
        
        # Rediriger stdout et stderr vers le logger
        class StreamToLogger:
            def __init__(self, logger_instance, log_level=logging.INFO):
                self.logger = logger_instance
                self.log_level = log_level

            def write(self, buf):
                for line in buf.rstrip().splitlines():
                    self.logger.log(self.log_level, line.rstrip())

            def flush(self):
                pass

        sys.stdout = StreamToLogger(logging.getLogger('STDOUT'), logging.INFO)
        sys.stderr = StreamToLogger(logging.getLogger('STDERR'), logging.ERROR)
        logging.info("stdout et stderr redirigés vers le logger")
    else:
        logging.basicConfig(level=logging.DEBUG, handlers=[logging.NullHandler()])
        logging.error("Impossible de configurer le fichier de log")
        
except Exception as e:
    log_message(f"Erreur configuration logging avancée: {e}", "ERROR")

log_message("--- DÉBUT CONFIGURATION CHEMINS ---", "INFO")
logging.info("--- DÉBUT CONFIGURATION CHEMINS ---")

# Configuration des chemins pour l'EXE
if getattr(sys, 'frozen', False):
    log_message("Application détectée comme 'frozen' (EXE)", "DEBUG")
    logging.debug("Application détectée comme 'frozen' (EXE)")
    
    if hasattr(sys, '_MEIPASS'):
        application_path = Path(sys._MEIPASS)
        log_message(f"_MEIPASS détecté: {application_path}", "DEBUG")
        logging.debug(f"_MEIPASS détecté: {application_path}")
    else:
        application_path = Path(sys.executable).parent
        log_message(f"Pas de _MEIPASS, application_path basé sur sys.executable: {application_path}", "DEBUG")
        logging.debug(f"Pas de _MEIPASS, application_path basé sur sys.executable: {application_path}")
    
    try:
        log_message(f"Contenu de application_path ({application_path}):", "DEBUG")
        logging.debug(f"Contenu de application_path ({application_path}):")
        for item in os.listdir(application_path):
            log_message(f"  - {item}", "DEBUG")
            logging.debug(f"  - {item}")
    except Exception as e_ls:
        log_message(f"Erreur lors du listage de application_path: {e_ls}", "ERROR")
        logging.error(f"Erreur lors du listage de application_path: {e_ls}")
    
    if str(application_path) not in sys.path:
        sys.path.insert(0, str(application_path))
        log_message(f"Ajout de {application_path} à sys.path", "DEBUG")
        logging.debug(f"Ajout de {application_path} à sys.path")
    else:
        log_message(f"{application_path} est déjà dans sys.path", "DEBUG")
        logging.debug(f"{application_path} est déjà dans sys.path")
else:
    application_path = Path(__file__).parent if "__file__" in globals() else Path.cwd()
    if str(application_path) not in sys.path:
        sys.path.insert(0, str(application_path))
    log_message(f"Mode développement, application_path: {application_path}", "DEBUG")
    logging.debug(f"Mode développement, application_path: {application_path}")

log_message(f"sys.path actuel: {sys.path}", "DEBUG")
logging.debug(f"sys.path actuel: {sys.path}")

log_message("--- DÉBUT IMPORT MODULE PRINCIPAL ---", "INFO")
logging.info("--- DÉBUT IMPORT MODULE PRINCIPAL ---")

# Import du module principal avec protection
try:
    log_message("Tentative d'importation de 'integration_protection_exe'...", "DEBUG")
    logging.debug("Tentative d'importation de 'integration_protection_exe'...")
    
    from integration_protection_exe import start_optimpv_with_protection
    
    log_message("'integration_protection_exe' importé avec succès", "DEBUG")
    logging.debug("'integration_protection_exe' importé avec succès")
    
    log_message("Appel de start_optimpv_with_protection()...", "DEBUG")
    logging.debug("Appel de start_optimpv_with_protection()...")
    
    start_optimpv_with_protection()
    
    log_message("start_optimpv_with_protection() terminé", "DEBUG")
    logging.debug("start_optimpv_with_protection() terminé")

except ImportError as e_import:
    log_message(f"ERREUR D'IMPORTATION DÉTAILLÉE: {e_import}", "ERROR")
    logging.error(f"ERREUR D'IMPORTATION DÉTAILLÉE: {e_import}", exc_info=True)
    
    log_message("Modules de protection non trouvés", "ERROR")
    logging.error("Modules de protection non trouvés")
    
    log_message("Tentative de démarrage en mode dégradé...", "INFO")
    logging.info("Tentative de démarrage en mode dégradé...")
    
    try:
        log_message("Tentative d'importation de 'optimpv_main_original'...", "DEBUG")
        logging.debug("Tentative d'importation de 'optimpv_main_original'...")
        
        from optimpv_main_original import main
        
        log_message("'optimpv_main_original' importé avec succès", "DEBUG")
        logging.debug("'optimpv_main_original' importé avec succès")
        
        main()
    except ImportError as e_fallback_import:
        log_message(f"ERREUR D'IMPORTATION FALLBACK: {e_fallback_import}", "ERROR")
        logging.error(f"ERREUR D'IMPORTATION FALLBACK: {e_fallback_import}", exc_info=True)
        
        log_message("Impossible de démarrer l'application (même en mode dégradé)", "ERROR")
        logging.error("Impossible de démarrer l'application (même en mode dégradé)")
        
        if getattr(sys, 'frozen', False):
            time.sleep(15)
        sys.exit(1)
    except Exception as e_fallback_other:
        log_message(f"ERREUR INATTENDUE FALLBACK: {e_fallback_other}", "ERROR")
        logging.error(f"ERREUR INATTENDUE FALLBACK: {e_fallback_other}", exc_info=True)
        
        log_message("Impossible de démarrer l'application (erreur inattendue en mode dégradé)", "ERROR")
        logging.error("Impossible de démarrer l'application (erreur inattendue en mode dégradé)")
        
        if getattr(sys, 'frozen', False):
            time.sleep(15)
        sys.exit(1)

except Exception as e_main:
    log_message(f"ERREUR GÉNÉRALE DANS optimpv_main.py: {e_main}", "ERROR")
    logging.error(f"ERREUR GÉNÉRALE DANS optimpv_main.py: {e_main}", exc_info=True)
    
    if getattr(sys, 'frozen', False):
        time.sleep(15)
    sys.exit(1)

log_message("--- FIN optimpv_main.py ---", "INFO")
logging.info("--- FIN optimpv_main.py ---")
'''
    
    # Écrire le fichier
    with open("optimpv_main.py", "w", encoding="utf-8") as f:
        f.write(main_content)
    
    print("  [OK] Point d'entrée principal créé: optimpv_main.py (avec journalisation ultra-robuste)")

def create_pyinstaller_spec():
    """Crée le fichier .spec pour PyInstaller avec tous les modules de sécurité"""
    print("\n[CONFIG] Création du fichier de configuration PyInstaller sécurisé...")
    
    # Doit correspondre à la définition dans build_optimpv_exe.py
    # S'assurer que les barres obliques inverses sont correctement échappées pour Windows si nécessaire.
    # En utilisant des barres obliques normales, Path les gère correctement sur toutes les plateformes.
    security_modules_dir_str = "Interface serveur/server_control/security"

    # Dépendances pour Streamlit et autres bibliothèques courantes
    hidden_imports = [
        'streamlit',
        'streamlit.web.server.server', # Nécessaire pour Streamlit >= 1.12
        'streamlit.web.server.websocket_headers', # Pour websocket headers
        'streamlit.runtime.scriptrunner.script_runner', # Pour certains callbacks
        'streamlit.runtime.caching.storage.dummy_cache_storage', # Pour le cache
        'pandas',
        'numpy',
        'plotly',
        'watchdog',
        'babel', # Pour Streamlit dates/times
        'pyarrow', # Pour certains formats de données avec Streamlit
        'psutil', # Souvent utilisé par des libs de monitoring ou Streamlit lui-même
        'jinja2', # Moteur de template utilisé par Streamlit/dépendances
        'altair',
        'configparser',
        'sqlite3',
        'tkinter',
        'requests',
        # AJOUTER les imports manquants détectés
        'win32com', # win32com.client est un sous-module
        'win32com.client', 
        'win32api',
        'win32con',
        'pythoncom',
        'wmi', # Ajout de wmi utilisé dans usb_surveillance_exe.py
        # Modules de sécurité explicites (utiliser le format d'import Python)
        'Interface_serveur.server_control.security.hardware_protection',
        'Interface_serveur.server_control.security.usb_surveillance_exe',
        'Interface_serveur.server_control.security.lockdown_actions',
        'Interface_serveur.server_control.security.integration_protection_exe', # Assurer que celui-ci est là
        # Autres dépendances potentielles basées sur les erreurs courantes
        'pkg_resources.py2_warn', 
        'pkg_resources.extern', 
        'win32timezone', # Pour la gestion des fuseaux horaires sur Windows
        # Dépendances de vos modules custom, si elles ne sont pas auto-détectées
        # Par exemple, si vous avez des imports dynamiques ou des plugins
        # 'mon_module_custom.plugin_a',
        # 'mon_module_custom.plugin_b',
    ]
    logger.info(f"Hidden imports pour PyInstaller: {hidden_imports}")

    # Définir le chemin de l'icône. Doit être relatif au .spec ou absolu.
    # Si 'assets/optimpv.ico' est à la racine du projet, et que le .spec est aussi à la racine.
    app_icon_path = 'assets/optimpv.ico' 
    # Vérifier si l'icône existe, sinon ne pas la mettre pour éviter une erreur PyInstaller
    if not os.path.exists(app_icon_path):
        logger.warning(f"Icône {app_icon_path} non trouvée. L'EXE n'aura pas d'icône personnalisée.")
        app_icon_spec_entry = "None" # PyInstaller spec utilise None comme chaîne pour pas d'icône
    else:
        logger.info(f"Utilisation de l'icône: {app_icon_path}")
        # S'assurer que le chemin est correctement formaté pour la f-string (ex: échapper les backslashes si nécessaire sur Windows)
        # Pour PyInstaller, les chemins dans le .spec peuvent généralement utiliser des slashes.
        app_icon_spec_entry = f"'{app_icon_path.replace('\\', '/')}'" # Remplacer backslashes et mettre entre apostrophes

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path # Assurez-vous que Path est importé ici

SECURITY_MODULES_DIR = Path("{security_modules_dir_str}") # Définir SECURITY_MODULES_DIR ici

block_cipher = None

# Données à inclure dans l'EXE
added_files = []

# Ajouter seulement les dossiers qui existent
if os.path.exists('Interface serveur'):
    added_files.append(('Interface serveur', 'Interface serveur'))
if os.path.exists('modules'):
    added_files.append(('modules', 'modules'))
if os.path.exists('config'):
    added_files.append(('config', 'config'))
if os.path.exists('data'):
    added_files.append(('data', 'data'))
if os.path.exists('network_admin_config.json'):
    added_files.append(('network_admin_config.json', '.'))
if os.path.exists('requirements.txt'):
    added_files.append(('requirements.txt', '.'))
if os.path.exists('license.json'):
    added_files.append(('license.json', '.'))

# Ajouter les modules de sécurité
security_module_files = [
    'hardware_protection.py',
    'usb_surveillance_exe.py',
    'integration_protection_exe.py',
    'lockdown_actions.py',
    # Les suivants sont probablement des outils de dev, pas nécessaires au runtime de l'EXE principal
    # 'create_token.py',
    # 'exemple_protection.py',
    # 'usb_token_manager.py'
]

for module_file in security_module_files:
    module_path = SECURITY_MODULES_DIR / module_file
    if module_path.exists():
        added_files.append((str(module_path), '.')) 
    else:
        print(f"  INFO: Module de securite {{module_path}} non trouve et ne sera pas inclus dans l'EXE.")

a = Analysis(
    ['optimpv_main.py'],
    pathex=['.'],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=['.'],
    hooksconfig={{}},
    runtime_hooks=['runtime_hook.py'],
    excludes=['tkinter', 'matplotlib.backends._tkagg'],
    win_no_prefer_redirects=True,
    win_private_assemblies=True,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='OptimPV',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Garder True pour debug initial, False en production finale
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon={app_icon_spec_entry},  # Icône personnalisée
    uac_admin=False, # Pas besoin des droits admin par défaut
)
'''
    
    with open("optimpv.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    print("  [OK] Fichier de configuration créé: optimpv.spec")

def check_security_modules():
    """Vérifie la présence des modules de sécurité requis"""
    print("\n[RECHERCHE] Vérification des modules de sécurité...")
    
    # Modules de sécurité requis
    required_modules = [
        "hardware_protection.py",
        "usb_surveillance_exe.py", 
        "integration_protection_exe.py",
        "lockdown_actions.py"
    ]
    
    missing_modules = []
    
    # Vérifier si le répertoire des modules de sécurité existe
    if not SECURITY_MODULES_DIR.exists():
        print(f"  [ERREUR] Répertoire des modules de sécurité non trouvé: {SECURITY_MODULES_DIR}")
        print("  Modules requis:")
        for module in required_modules:
            expected_path = SECURITY_MODULES_DIR / module
            print(f"  [ERREUR] {expected_path} (répertoire parent {SECURITY_MODULES_DIR} manquant)")
        return False
    
    # Vérifier chaque module
    for module in required_modules:
        module_path = SECURITY_MODULES_DIR / module
        if not module_path.exists():
            missing_modules.append(module)
            print(f"  [ERREUR] {module_path}")
        else:
            print(f"  [OK] {module_path}")
    
    if missing_modules:
        print(f"\n[ATTENTION] Modules de sécurité manquants: {', '.join(missing_modules)}")
        print("  La compilation peut échouer ou l'EXE peut ne pas fonctionner correctement.")
        return False
    else:
        print("[OK] Tous les modules de sécurité sont présents")
        return True

def create_usb_token_for_testing():
    """Crée un token USB de test sur le lecteur G: si disponible"""
    print("\n[CLE] Création d'un token USB de test...")
    
    # Vérifier si le lecteur G: existe
    test_drive = Path("G:")
    if test_drive.exists():
        try:
            # Créer le token de test
            sys.path.insert(0, str(SECURITY_MODULES_DIR))
            from hardware_protection import HardwareProtection
            
            hw_protection = HardwareProtection()
            success, token_path = hw_protection.create_usb_token("G:")
            
            if success:
                print(f"  [OK] Token USB créé: {token_path}")
                print("  Ce token permettra de tester l'EXE avec accès complet")
            else:
                print("  [ATTENTION] Échec création token USB")
        except Exception as e:
            print(f"  [ERREUR] Erreur création token: {e}")
    else:
        print("  [ATTENTION] Lecteur G: non trouvé - Token non créé")
        print("  Vous pouvez créer un token manuellement après compilation")

def test_security_before_build():
    """Teste les modules de sécurité avant la compilation"""
    try:
        # Ajouter le répertoire de sécurité au path pour les tests
        security_modules_abs_path = Path.cwd() / SECURITY_MODULES_DIR
        if security_modules_abs_path.exists():
            sys.path.insert(0, str(security_modules_abs_path))
            print(f"  [INFO] Ajout de {security_modules_abs_path} à sys.path pour les tests de sécurité.")
        else:
            print(f"  [ATTENTION] Attention: Le répertoire des modules de sécurité ({SECURITY_MODULES_DIR}) n'a pas été trouvé. " \
                  "Les tests de sécurité ne peuvent pas être effectués.")
            return False
        
        # Test d'import des modules
        try:
            from hardware_protection import HardwareProtection
            from usb_surveillance_exe import USBSurveillanceEXE
            from lockdown_actions import execute_full_lockdown
            print("  [OK] Imports des modules de sécurité OK")
            
            # Test de détection machine
            hw_protection = HardwareProtection()
            machine_info = hw_protection.get_machine_info()
            print(f"  [OK] Détection machine OK - ID: {machine_info['machine_id']}")
            
            # Test des vérifications
            usb_valid, usb_message = hw_protection.verify_usb_token()
            print(f"  [RADIO] Test USB: {'[OK]' if usb_valid else '[ATTENTION]'} {usb_message}")
            
            mac_valid, mac_message = hw_protection.verify_machine_license()
            print(f"  [LOCK] Test MAC: {'[OK]' if mac_valid else '[ATTENTION]'} {mac_message}")
            
            print("[OK] Tests de sécurité réussis")
            return True
            
        except Exception as e:
            print(f"  [ERREUR] Erreur lors des tests: {e}")
            return False
            
    except Exception as e:
        print(f"  [ERREUR] Erreur générale tests sécurité: {e}")
        return False

def show_final_summary():
    """Affiche le résumé final après compilation"""
    exe_path = Path("dist/OptimPV.exe")
    
    if exe_path.exists():
        file_size = exe_path.stat().st_size / (1024 * 1024)  # Taille en MB
        print("[CELEBRATION] COMPILATION OPTIMPV SÉCURISÉE TERMINÉE AVEC SUCCÈS !")
        print("=" * 70)
        print(f"[FICHIER] Exécutable: {exe_path}")
        print(f"[TAILLE] Taille: {file_size:.1f} MB")
        print()
        print("[SECURITE] FONCTIONNALITÉS DE SÉCURITÉ INTÉGRÉES:")
        print()
        print("   • [CLE] Support token USB avec surveillance temps réel")
        print("   • [OEIL] Surveillance continue de la clé USB")
        print("   • [SECURITE] Protection anti-copie avec destruction automatique")
        print("   • [GLOBE] Fermeture forcée des navigateurs (y compris headless)")
        print("   • [SUPPRESSION] Suppression automatique de l'EXE")
        print("   • [VERROUILLAGE] Blocage temporaire du redémarrage")
        print()
        print("[UTILISATION] UTILISATION:")
        print("   OptimPV.exe                 # Menu de sélection")
        print("   OptimPV.exe --panel         # Panneau de contrôle direct")
        print("   OptimPV.exe --server        # Serveur persistant")
        print("   OptimPV.exe --status        # Statut de sécurité")
        print()
        print("[CLE] GESTION DES TOKENS USB:")
        print("   • Insérez votre clé USB autorisée pour un accès complet")
        print("   • Sans clé USB: accès restreint si MAC autorisée")
        print("   • Sans clé USB ni MAC autorisée: lockdown immédiat")
        print("   • Retrait de la clé pendant utilisation:")
        print("     - Si MAC autorisée: passage en mode restreint")
        print("     - Si MAC non autorisée: lockdown complet")
        print()
        print("[ATTENTION] AVERTISSEMENTS IMPORTANTS:")
        print("   • L'EXE se supprime automatiquement en cas de violation")
        print("   • Gardez une copie de sauvegarde de l'EXE")
        print("   • Testez d'abord avec votre clé USB")
        print("   • Les navigateurs seront fermés en cas de lockdown")
        print("   • Aucune trace n'est laissée après suppression")
        print("=" * 70)
    else:
        print("[ERREUR] EXE non trouvé - Compilation échouée")

def validate_build_environment():
    """Vérifie que tous les fichiers requis existent"""
    logger.info("Validation de l'environnement de build...")
    required_files = [
        'app.py',
        'optimpv_main.py', # Ajout optimpv_main.py qui est référencé
        'Interface serveur/launcher.py',
        # Les chemins vers les modules de sécurité doivent être relatifs à la racine du projet
        SECURITY_MODULES_DIR / 'integration_protection_exe.py',
        SECURITY_MODULES_DIR / 'hardware_protection.py',
        SECURITY_MODULES_DIR / 'usb_surveillance_exe.py',
        SECURITY_MODULES_DIR / 'lockdown_actions.py',
        # Fichier pour le hook streamlit, s'il est utilisé
        'hook-streamlit.py',
        # Fichier de configuration réseau s'il est packagé
        'network_admin_config.json'
    ]
    missing = []
    for f_path in required_files:
        # Convertir en chaîne si c'est un objet Path pour os.path.exists
        f_str = str(f_path) 
        if not Path(f_str).exists():
            missing.append(f_str)
            
    if missing:
        error_msg = f"Fichiers manquants pour le build : {missing}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    logger.info("Validation de l'environnement de build: OK")
    return True

def main():
    # global logger # logger est maintenant défini au niveau du module
    # logger = setup_logging() # Appeler setup_logging pour configurer le logger existant
    setup_logging() # Le logger est déjà global, on le configure juste
    
    try:
        validate_build_environment() # Appel de la validation ici
        print_banner()
        
        # Vérifications préliminaires
        if not check_dependencies():
            print("\n[ERREUR] Dépendances manquantes. Arrêt de la compilation.")
            return False
        
        if not check_security_modules():
            print("\n[ERREUR] Modules de sécurité manquants. Arrêt de la compilation.")
            return False
        
        # Tests de sécurité
        if not test_security_before_build():
            print("\n[ATTENTION] Problèmes détectés lors des tests de sécurité.")
            print("La compilation va continuer mais l'EXE pourrait ne pas fonctionner correctement.")
            
            response = input("Continuer malgré les erreurs ? (o/N): ").strip().lower()
            if response not in ['o', 'oui', 'y', 'yes']:
                print("Compilation annulée.")
                return False
        
        # Création du token USB de test
        create_usb_token_for_testing()
        
        # Préparation de l'environnement
        prepare_build_environment()
        
        # Création des fichiers
        create_main_entry_point()
        create_pyinstaller_spec()
        
        # Demander confirmation avant compilation
        print(f"\n[CLE] Création d'un token USB de test...")
        create_usb_token_for_testing()
        
        compiler_name = "PyInstaller"
        print(f"\n[ATTENTION] ATTENTION: La compilation va commencer avec {compiler_name}.")
        print("Cela peut prendre plusieurs minutes...")
        print("[SECURITE] L'EXE contiendra toutes les protections de sécurité.")
        
        response = input("Continuer avec la compilation ? (O/n): ").strip().lower()
        if response in ['n', 'non', 'no']:
            print("Compilation annulée par l'utilisateur.")
            return False
        
        # Compilation
        success = compile_exe("pyinstaller")
        
        if success:
            show_final_summary()
            return True
        else:
            print("\n[ERREUR] Échec de la compilation.")
            return False

    except Exception as e:
        print(f"Erreur lors de la compilation: {e}")
        return False

def check_dependencies():
    """Vérifie que toutes les dépendances sont installées"""
    print("\n[RECHERCHE] Vérification des dépendances...")
    
    # Dépendances Python requises
    required_python_deps = [
        "streamlit", "psutil", "requests", "pandas", "numpy", 
        "plotly", "pathlib", "threading", "subprocess"
    ]
    
    missing_python = []
    
    for dep in required_python_deps:
        try:
            __import__(dep)
            print(f"  [OK] {dep}")
        except ImportError:
            missing_python.append(dep)
            print(f"  [ERREUR] {dep}")
    
    # Vérifier les dépendances intégrées
    builtin_deps = ["os", "sys", "time", "json", "hashlib", "uuid", "platform"]
    for dep in builtin_deps:
        print(f"  [OK] {dep} (intégré)")
    
    # Vérifier les dépendances optionnelles
    optional_deps = ["PIL", "webview", "cryptography"]
    for dep in optional_deps:
        try:
            __import__(dep)
            print(f"  [OK] {dep}")
        except ImportError:
            print(f"  [ERREUR] {dep}")
    
    # Vérifier PyInstaller
    try:
        import PyInstaller
        print(f"  [OK] PyInstaller {PyInstaller.__version__}")
    except ImportError:
        missing_python.append("PyInstaller")
        print(f"  [ERREUR] PyInstaller")
    
    if missing_python:
        print(f"\n[ATTENTION] Dépendances manquantes: {', '.join(missing_python)}")
        print("Installez-les avec: pip install " + " ".join(missing_python))
        return False
    
    if "PyInstaller" in missing_python:
        print("\n[ATTENTION] PyInstaller non disponible !")
        print("Installez-le avec: pip install pyinstaller")
        return False
    
    print("[OK] Toutes les dépendances sont installées")
    return True

def prepare_build_environment():
    """Prépare l'environnement de build en nettoyant les anciens artefacts"""
    print("\n[OUTILS] Préparation de l'environnement de build...")
    
    # Nettoyer les anciens builds
    cleanup_items = [
        "dist", "build", "optimpv.spec", "optimpv_main.py",
        "__pycache__"
    ]
    
    for item in cleanup_items:
        item_path = Path(item)
        if item_path.exists():
            if item_path.is_file():
                print(f"  [SUPPRESSION] Nettoyage du fichier existant: {item_path}...")
                item_path.unlink()
            else:
                print(f"  [SUPPRESSION] Nettoyage du dossier existant: {item_path}...")
                import shutil
                shutil.rmtree(item_path)
    
    # Créer les dossiers nécessaires
    Path("dist").mkdir(exist_ok=True)
    Path("build").mkdir(exist_ok=True)
    
    print("  [OK] Environnement de build préparé (artefacts précédents nettoyés)")

def compile_exe(compiler_type):
    """Compile l'EXE avec le compilateur spécifié"""
    if compiler_type == "pyinstaller":
        return compile_with_pyinstaller()
    else:
        print(f"[ERREUR] Compilateur non supporté: {compiler_type}")
        return False

def compile_with_pyinstaller():
    """Compile avec PyInstaller"""
    try:
        import subprocess
        import time
        
        # Ajouter l'option --debug=all pour le débogage
        cmd = ["python", "-m", "PyInstaller", "optimpv.spec", "--clean", "--noconfirm", "--debug=all"]
        
        print(f"[OUTILS] Commande: {' '.join(cmd)}")
        print("[DEBUG] Option --debug=all ajoutée pour le débogage de l'EXE")
        print("Compilation en cours...")
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
        end_time = time.time()
        
        if result.returncode == 0:
            print("[OK] Compilation réussie !")
            print(f"Temps de compilation: {end_time - start_time:.1f}s")
            
            # Vérifier que l'EXE a été créé
            exe_path = Path("dist/OptimPV.exe")
            if exe_path.exists():
                print(f"[OK] EXE créé: {exe_path}")
                print(f"[DEBUG] Taille de l'EXE: {exe_path.stat().st_size / (1024*1024):.1f} MB")
                return True
            else:
                print("[ERREUR] EXE non trouvé dans dist/")
                return False
        else:
            print("[ERREUR] Erreur de compilation:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("[ERREUR] Timeout de compilation (30 minutes)")
        return False
    except Exception as e:
        print(f"[ERREUR] Erreur lors de la compilation: {e}")
        return False

def cleanup_build_files():
    """Nettoie les fichiers de build temporaires"""
    cleanup_items = [
        "build", "optimpv_main.py", "__pycache__"
    ]
    
    for item in cleanup_items:
        item_path = Path(item)
        if item_path.exists():
            if item_path.is_file():
                print(f"  [SUPPRESSION] Supprimé: {item}")
                item_path.unlink()
            else:
                print(f"  [SUPPRESSION] Dossier supprimé: {item}")
                import shutil
                shutil.rmtree(item_path)
    
    print("  [OK] Nettoyage terminé")

if __name__ == "__main__":
    main()