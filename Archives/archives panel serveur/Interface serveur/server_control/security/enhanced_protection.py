"""
Module de protection hardware avancée pour OptimPV
==================================================

Inspiré des meilleures pratiques de sécurité :
- Double facteur : USB + MAC Address  
- Chiffrement AES + HMAC pour l'intégrité
- Erreurs masquées pour éviter la reconnaissance
- Zero fallback : aucune récupération automatique

Architecture sécurisée sans révéler les mécanismes internes.
"""

import os
import json
import hmac
import hashlib
import platform
import psutil
import socket
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging

# Configuration discrète du logging
logger = logging.getLogger('system_integrity')

class USBSecurityToken:
    """Gestionnaire de token USB sécurisé"""
    
    def __init__(self):
        self.token_file = "sys.dat"  # Nom discret
        
    def get_usb_drives(self) -> List[Dict]:
        """Détecte les lecteurs USB disponibles"""
        usb_drives = []
        
        try:
            if platform.system() == "Windows":
                try:
                    import win32api
                    import win32file
                    drives = win32api.GetLogicalDriveStrings()
                    drives = drives.split('\000')[:-1]
                    
                    for drive in drives:
                        drive_type = win32file.GetDriveType(drive)
                        if drive_type == 2:  # Lecteur amovible
                            try:
                                volume_info = win32api.GetVolumeInformation(drive)
                                usb_drives.append({
                                    'drive': drive,
                                    'label': volume_info[0],
                                    'serial': volume_info[1],
                                    'filesystem': volume_info[4]
                                })
                            except:
                                pass
                except ImportError:
                    # Fallback si win32 non disponible
                    partitions = psutil.disk_partitions()
                    for partition in partitions:
                        if 'removable' in partition.opts:
                            usb_drives.append({
                                'drive': partition.mountpoint,
                                'device': partition.device
                            })
            else:
                # Linux/Mac - utiliser psutil
                partitions = psutil.disk_partitions()
                for partition in partitions:
                    if 'removable' in partition.opts or '/media' in partition.mountpoint:
                        usb_drives.append({
                            'drive': partition.mountpoint,
                            'device': partition.device,
                            'filesystem': partition.fstype
                        })
                        
        except Exception as e:
            logger.error(f"Erreur détection USB: {e}")
            # Fallback final avec psutil
            try:
                partitions = psutil.disk_partitions()
                for partition in partitions:
                    if 'removable' in partition.opts:
                        usb_drives.append({
                            'drive': partition.mountpoint,
                            'device': partition.device
                        })
            except:
                pass
                    
        return usb_drives
        
    def find_security_token(self) -> Optional[str]:
        """Recherche le token de sécurité sur les lecteurs USB"""
        usb_drives = self.get_usb_drives()
        
        for drive_info in usb_drives:
            token_path = os.path.join(drive_info['drive'], self.token_file)
            if os.path.exists(token_path):
                try:
                    with open(token_path, 'r', encoding='utf-8') as f:
                        token_data = f.read().strip()
                        # Vérification basique du format
                        if len(token_data) == 32 and all(c in '0123456789ABCDEF' for c in token_data):
                            return token_data
                except:
                    continue
                    
        return None
        
    def create_security_token(self, usb_drive: str) -> str:
        """Crée un token de sécurité sur la clé USB"""
        # Génération d'un ID unique basé sur timestamp + machine
        machine_id = socket.gethostname()
        timestamp = str(int(datetime.now().timestamp()))
        raw_id = f"{machine_id}_{timestamp}_{os.urandom(8).hex()}"
        
        # Hachage pour créer l'ID final
        token_id = hashlib.sha256(raw_id.encode()).hexdigest()[:32].upper()
        
        # Écriture sur la clé USB
        token_path = os.path.join(usb_drive, self.token_file)
        with open(token_path, 'w', encoding='utf-8') as f:
            f.write(token_id)
            
        return token_id


class CryptoManager:
    """Gestionnaire de chiffrement et intégrité"""
    
    def __init__(self, master_key: Optional[str] = None):
        # Clé maître embarquée (en production, utiliser une clé plus complexe)
        self.master_key = master_key or "OptimPV_Security_2025_Alpha"
        self.salt = b'optimpv_salt_2025'
        
    def _derive_key(self, password: str) -> bytes:
        """Dérive une clé de chiffrement"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
    def encrypt_data(self, data: str) -> bytes:
        """Chiffre les données avec AES"""
        key = self._derive_key(self.master_key)
        fernet = Fernet(key)
        return fernet.encrypt(data.encode())
        
    def decrypt_data(self, encrypted_data: bytes) -> str:
        """Déchiffre les données"""
        key = self._derive_key(self.master_key)
        fernet = Fernet(key)
        return fernet.decrypt(encrypted_data).decode()
        
    def generate_hmac(self, data: bytes) -> str:
        """Génère un HMAC pour vérifier l'intégrité"""
        return hmac.new(
            self.master_key.encode(),
            data,
            hashlib.sha256
        ).hexdigest()
        
    def verify_hmac(self, data: bytes, hmac_value: str) -> bool:
        """Vérifie l'intégrité via HMAC"""
        expected_hmac = self.generate_hmac(data)
        return hmac.compare_digest(expected_hmac, hmac_value)


class EnhancedSecurityConfig:
    """Configuration sécurisée avec chiffrement et intégrité"""
    
    def __init__(self, config_file: str = "secure_config.dat"):
        self.config_file = config_file
        self.crypto = CryptoManager()
        self.usb_token = USBSecurityToken()
        
    def create_initial_config(self, usb_drive: str, authorized_mac: str, admin_password: str) -> bool:
        """Crée la configuration initiale lors du premier déploiement"""
        try:
            # Créer le token USB
            usb_id = self.usb_token.create_security_token(usb_drive)
            
            # Configuration sécurisée
            config_data = {
                "usb_id": usb_id,
                "authorized_mac": authorized_mac,
                "admin_password_hash": hashlib.sha256(admin_password.encode()).hexdigest(),
                "created_date": datetime.now().isoformat(),
                "version": "2.0",
                "license_type": "enterprise"
            }
            
            # Chiffrement
            json_data = json.dumps(config_data, indent=2)
            encrypted_data = self.crypto.encrypt_data(json_data)
            
            # HMAC pour l'intégrité
            hmac_value = self.crypto.generate_hmac(encrypted_data)
            
            # Structure finale
            final_data = {
                "data": base64.b64encode(encrypted_data).decode(),
                "integrity": hmac_value,
                "version": "2.0"
            }
            
            # Sauvegarde
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Erreur création config: {e}")
            return False
            
    def load_secure_config(self) -> Optional[Dict]:
        """Charge et déchiffre la configuration sécurisée"""
        try:
            # Vérifier l'existence
            if not os.path.exists(self.config_file):
                return None
                
            # Charger le fichier
            with open(self.config_file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                
            # Décoder et vérifier l'intégrité
            encrypted_data = base64.b64decode(file_data["data"])
            
            if not self.crypto.verify_hmac(encrypted_data, file_data["integrity"]):
                logger.error("Intégrité du fichier compromise")
                return None
                
            # Déchiffrer
            json_data = self.crypto.decrypt_data(encrypted_data)
            config_data = json.loads(json_data)
            
            return config_data
            
        except Exception as e:
            logger.error(f"Erreur chargement config: {e}")
            return None


class EnhancedHardwareProtection:
    """Protection hardware avancée avec double facteur"""
    
    def __init__(self):
        self.config_manager = EnhancedSecurityConfig()
        self.usb_token = USBSecurityToken()
        
    def get_primary_mac_address(self) -> str:
        """Récupère l'adresse MAC principale"""
        try:
            interfaces = psutil.net_if_addrs()
            
            # Prioriser les interfaces actives
            for interface_name, addresses in interfaces.items():
                if 'loopback' in interface_name.lower() or 'virtual' in interface_name.lower():
                    continue
                    
                for addr in addresses:
                    if addr.family == psutil.AF_LINK and addr.address != "00:00:00:00:00:00":
                        return addr.address.upper().replace("-", ":")
                        
        except Exception as e:
            logger.error(f"Erreur MAC: {e}")
            
        return ""
        
    def verify_dual_factor_auth(self) -> Tuple[bool, str]:
        """Vérification double facteur : USB + MAC"""
        try:
            # 1. Charger la configuration sécurisée
            config = self.config_manager.load_secure_config()
            if not config:
                return False, "Configuration système introuvable"
                
            # 2. Vérifier le token USB
            usb_token = self.usb_token.find_security_token()
            if not usb_token:
                return False, "Token d'accès requis"
                
            if usb_token != config["usb_id"]:
                return False, "Token d'accès invalide"
                
            # 3. Vérifier l'adresse MAC
            current_mac = self.get_primary_mac_address()
            if current_mac != config["authorized_mac"]:
                return False, "Configuration réseau non autorisée"
                
            return True, "Accès autorisé"
            
        except Exception as e:
            logger.error(f"Erreur vérification: {e}")
            return False, "Erreur système"
            
    def simulate_windows_error(self):
        """Affiche une erreur système générique pour masquer le vrai problème"""
        import streamlit as st
        
        st.error("""
        **Erreur Système Windows**
        
        L'application a rencontré une erreur inattendue et ne peut pas continuer.
        
        Code d'erreur: 0x80070005
        
        Veuillez redémarrer votre ordinateur et réessayer.
        """)
        
        st.stop()
        
    def check_system_integrity(self) -> bool:
        """Point d'entrée principal pour la vérification de sécurité"""
        authorized, message = self.verify_dual_factor_auth()
        
        if not authorized:
            # Log discret de la tentative
            logger.warning(f"Tentative d'accès non autorisée: {message}")
            
            # Afficher erreur générique et arrêter
            self.simulate_windows_error()
            return False
            
        return True


def require_enhanced_license(func):
    """Décorateur de protection avancée"""
    def wrapper(*args, **kwargs):
        protection = EnhancedHardwareProtection()
        
        # Vérification silencieuse
        if not protection.check_system_integrity():
            return None  # L'erreur est gérée dans check_system_integrity
            
        return func(*args, **kwargs)
    
    return wrapper


# Utilitaire pour l'installation initiale
class InstallationWizard:
    """Assistant d'installation sécurisée"""
    
    @staticmethod
    def setup_security(usb_drive: str, admin_password: str) -> bool:
        """Configure la sécurité lors de l'installation"""
        try:
            protection = EnhancedHardwareProtection()
            mac_address = protection.get_primary_mac_address()
            
            if not mac_address:
                return False
                
            return protection.config_manager.create_initial_config(
                usb_drive, mac_address, admin_password
            )
            
        except Exception as e:
            logger.error(f"Erreur installation: {e}")
            return False


if __name__ == "__main__":
    """Test et utilitaires de diagnostic"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Protection Hardware OptimPV")
    parser.add_argument('--setup', metavar='USB_DRIVE', 
                       help='Installer la protection (ex: D:\\)')
    parser.add_argument('--check', action='store_true',
                       help='Vérifier la protection')
    parser.add_argument('--status', action='store_true',
                       help='Afficher le statut détaillé')
    
    args = parser.parse_args()
    
    if args.setup:
        password = input("Mot de passe admin: ")
        success = InstallationWizard.setup_security(args.setup, password)
        print(f"Installation: {'✅ Réussie' if success else '❌ Échec'}")
        
    elif args.check:
        protection = EnhancedHardwareProtection()
        authorized, message = protection.verify_dual_factor_auth()
        print(f"Statut: {'✅ Autorisé' if authorized else '❌ Refusé'}")
        
    elif args.status:
        protection = EnhancedHardwareProtection()
        print("=== DIAGNOSTIC SÉCURITÉ ===")
        print(f"MAC détectée: {protection.get_primary_mac_address()}")
        print(f"Token USB: {protection.usb_token.find_security_token()}")
        print(f"Config: {'✅' if protection.config_manager.load_secure_config() else '❌'}")
        
    else:
        # Test rapide
        protection = EnhancedHardwareProtection()
        result = protection.check_system_integrity()
        print(f"Protection: {'✅ Active' if result else '❌ Inactive'}") 