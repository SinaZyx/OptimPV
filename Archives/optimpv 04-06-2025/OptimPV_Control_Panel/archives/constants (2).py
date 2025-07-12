# config/constants.py
"""
Constantes et configuration du système
"""

import os
import sys
from pathlib import Path

# Version du système
SYSTEM_VERSION = "2.0.0"
SYSTEM_NAME = "OptimPV Control Panel"

# Chemins de base
if getattr(sys, 'frozen', False):
    # Exécutable compilé
    BASE_DIR = Path(sys.executable).parent
else:
    # Mode développement
    BASE_DIR = Path(__file__).parent.parent

# Répertoires
CONFIG_DIR = BASE_DIR / "config"
SECURE_CONFIG_DIR = CONFIG_DIR / "secure"
LOGS_DIR = BASE_DIR / "logs"
TEMP_DIR = BASE_DIR / "temp"

# Créer répertoires si nécessaire
for directory in [CONFIG_DIR, SECURE_CONFIG_DIR, LOGS_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Sécurité - UTILISER UNIQUEMENT LE TOKEN MASTER
LOCKDOWN_DELAY = 3  # Secondes avant lockdown
MIN_PASSWORD_LENGTH = 8
TOKEN_FILE_NAME = "optimpv_master.key"  # CHANGÉ : Utiliser le token master
TOKEN_SIGNATURE = b"OPTIMPV_TOKEN_V2"

# Token Master pour activation système (même fichier maintenant)
MASTER_TOKEN_FILE = "optimpv_master.key"
MASTER_TOKEN_SIGNATURE = b"OPTIMPV_MASTER_V2"

# Réseau
DEFAULT_BIND_ADDRESS = "127.0.0.1"
DEFAULT_PORT = 8501
CONTROL_PANEL_PORT = 8502

# Limites système
MAX_LOG_SIZE_MB = 50
MAX_LOG_FILES = 10
LOG_RETENTION_DAYS = 30

# Processus
PROCESS_CHECK_INTERVAL = 1  # Secondes
USB_CHECK_INTERVAL = 1  # Secondes
SECURITY_CHECK_INTERVAL = 30  # Secondes

# Messages d'erreur génériques (pour éviter fuites d'info)
GENERIC_ERROR_MESSAGES = {
    'AUTH_FAILED': "Erreur d'authentification. Code: 0x80070005",
    'FILE_ERROR': "Erreur système. Code: 0x80070002",
    'PERMISSION_ERROR': "Accès refusé. Code: 0x80070005",
    'SYSTEM_ERROR': "Erreur système critique. Code: 0x800705AA"
}

# Processus suspects à surveiller
SUSPICIOUS_PROCESSES = [
    # Debuggers
    'ollydbg', 'x64dbg', 'x32dbg', 'windbg', 'ida', 'ida64',
    'ghidra', 'radare2', 'immunity', 'gdb',
    
    # Analyse réseau
    'wireshark', 'fiddler', 'burpsuite', 'charles', 'tcpdump',
    'networkminer', 'ettercap',
    
    # Analyse système
    'processhacker', 'procexp', 'procmon', 'autoruns',
    'regmon', 'filemon', 'apimonitor',
    
    # Virtualisation/Sandbox
    'vboxservice', 'vboxtray', 'vmtoolsd', 'vmwaretray',
    'xenservice', 'qemu', 'prl_tools',
    
    # Injection/Hooking
    'cheatengine', 'artmoney', 'injector', 'hookshark'
]

# Extensions de fichiers à nettoyer en lockdown
CLEANUP_EXTENSIONS = [
    '.log', '.tmp', '.temp', '.cache', '.pyc',
    '.enc', '.key', '.token', '.session'
]

# Configuration par défaut
DEFAULT_CONFIG = {
    'server': {
        'bind_address': DEFAULT_BIND_ADDRESS,
        'port': DEFAULT_PORT,
        'allow_external': False,
        'auto_open_browser': True,
        'headless': True
    },
    'security': {
        'enable_mac_whitelist': True,
        'enable_usb_token': True,
        'enable_anti_tamper': True,
        'lockdown_on_tamper': True,
        'session_timeout_minutes': 60
    },
    'logging': {
        'level': 'INFO',
        'encrypt_security_logs': True,
        'retention_days': LOG_RETENTION_DAYS
    }
}