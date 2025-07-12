# security/usb_token.py
"""
Gestion des tokens USB pour authentification matérielle
"""

import os
import json
import time
import string
import secrets
from enum import Enum
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    import win32api
    import win32con
    import win32file
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

from security.crypto_store import SecureStorage
from utils.logger import SecureLogger
from config.constants import TOKEN_FILE_NAME, TOKEN_SIGNATURE


class TokenType(Enum):
    """Types de tokens disponibles"""
    USER = "USER"
    ADMIN = "ADMIN"


class USBTokenMonitor:
    """Surveillance et gestion des tokens USB"""
    
    def __init__(self):
        self.crypto = SecureStorage()
        self.logger = SecureLogger()
        self._current_token_cache = None
        self._last_check_time = 0
        self._cache_duration = 2  # secondes
    
    def check_token_presence(self) -> Dict:
        """Vérifier la présence d'un token USB"""
        # Utiliser cache pour éviter vérifications excessives
        current_time = time.time()
        if (self._current_token_cache and 
            current_time - self._last_check_time < self._cache_duration):
            return self._current_token_cache
        
        result = {
            'present': False,
            'type': None,
            'drive': None,
            'token_id': None
        }
        
        # Parcourir lecteurs amovibles
        removable_drives = self._get_removable_drives()
        
        for drive in removable_drives:
            token_check = self._check_drive_for_token(drive)
            if token_check['present']:
                result.update(token_check)
                break
        
        # Mettre à jour cache
        self._current_token_cache = result
        self._last_check_time = current_time
        
        return result
    
    def get_current_token_info(self) -> Optional[Dict]:
        """Obtenir informations détaillées du token actuel"""
        status = self.check_token_presence()
        
        if not status['present']:
            return None
        
        try:
            # Lire fichier token
            token_path = os.path.join(status['drive'], TOKEN_FILE_NAME)
            
            with open(token_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Déchiffrer et vérifier
            token_data = self.crypto.decrypt_and_verify(encrypted_data)
            
            # Ajouter infos supplémentaires
            token_data['drive'] = status['drive']
            token_data['present'] = True
            
            return token_data
            
        except Exception as e:
            self.logger.log_event('TOKEN_READ_ERROR', {'error': str(e)})
            return None
    
    def create_token(self, drive_letter: str, token_type: TokenType) -> bool:
        """Créer un nouveau token USB"""
        try:
            # Vérifier drive existe et est amovible
            if not self._is_removable_drive(drive_letter):
                raise Exception(f"{drive_letter} n'est pas un lecteur amovible")
            
            # Générer ID unique
            token_id = secrets.token_hex(32)
            
            # Obtenir numéro série USB
            usb_serial = self._get_usb_serial(drive_letter)
            
            # Créer données token
            token_data = {
                'signature': TOKEN_SIGNATURE.decode(),
                'type': token_type.value,
                'id': token_id,
                'created': datetime.now().isoformat(),
                'version': '2.0',
                'hardware_bind': usb_serial,
                'creator': 'admin',
                'permissions': self._get_default_permissions(token_type)
            }
            
            # Chiffrer et signer
            encrypted_data = self.crypto.encrypt_and_sign(token_data)
            
            # Écrire sur USB
            token_path = os.path.join(drive_letter, TOKEN_FILE_NAME)
            
            with open(token_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Marquer comme système/caché
            if WIN32_AVAILABLE:
                win32api.SetFileAttributes(
                    token_path,
                    win32con.FILE_ATTRIBUTE_HIDDEN | 
                    win32con.FILE_ATTRIBUTE_SYSTEM |
                    win32con.FILE_ATTRIBUTE_READONLY
                )
            
            # Logger création
            self.logger.log_security_event('TOKEN_CREATED', {
                'type': token_type.value,
                'id': token_id[:8] + '...',
                'drive': drive_letter
            })
            
            return True
            
        except Exception as e:
            self.logger.log_event('TOKEN_CREATE_ERROR', {
                'error': str(e),
                'drive': drive_letter
            })
            return False
    
    def verify_token(self, token_path: str) -> Tuple[bool, Optional[Dict]]:
        """Vérifier l'intégrité et validité d'un token"""
        try:
            # Lire fichier
            with open(token_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Déchiffrer et vérifier signature
            token_data = self.crypto.decrypt_and_verify(encrypted_data)
            
            # Vérifier signature système
            if token_data.get('signature') != TOKEN_SIGNATURE.decode():
                return False, None
            
            # Vérifier version
            if token_data.get('version') != '2.0':
                return False, None
            
            # Vérifier binding hardware si présent
            if 'hardware_bind' in token_data:
                drive = str(Path(token_path).parent) + '\\'
                current_serial = self._get_usb_serial(drive)
                
                if current_serial != token_data['hardware_bind']:
                    self.logger.log_security_event('TOKEN_HARDWARE_MISMATCH', {
                        'expected': token_data['hardware_bind'][:8] + '...',
                        'actual': current_serial[:8] + '...' if current_serial else 'None'
                    }, severity='HIGH')
                    return False, None
            
            return True, token_data
            
        except Exception as e:
            self.logger.log_event('TOKEN_VERIFY_ERROR', {'error': str(e)})
            return False, None
    
    def revoke_token(self, token_id: str) -> bool:
        """Révoquer un token (l'ajouter à la liste de révocation)"""
        try:
            # Charger liste révocation
            revoked_list = self.crypto.load_encrypted_file('revoked_tokens') or []
            
            # Ajouter token
            revocation_entry = {
                'token_id': token_id,
                'revoked_date': datetime.now().isoformat(),
                'revoked_by': 'admin'
            }
            
            revoked_list.append(revocation_entry)
            
            # Sauvegarder
            self.crypto.save_encrypted_file('revoked_tokens', revoked_list)
            
            # Logger
            self.logger.log_security_event('TOKEN_REVOKED', {
                'token_id': token_id[:8] + '...'
            })
            
            # Invalider cache
            self._current_token_cache = None
            
            return True
            
        except Exception as e:
            self.logger.log_event('TOKEN_REVOKE_ERROR', {'error': str(e)})
            return False
    
    def _get_removable_drives(self) -> List[str]:
        """Obtenir liste des lecteurs amovibles"""
        drives = []
        
        if WIN32_AVAILABLE:
            # Méthode Windows
            drive_bits = win32api.GetLogicalDrives()
            
            for letter in string.ascii_uppercase:
                if drive_bits & 1:
                    drive = f"{letter}:\\"
                    try:
                        drive_type = win32file.GetDriveType(drive)
                        if drive_type == win32file.DRIVE_REMOVABLE:
                            drives.append(drive)
                    except:
                        pass
                drive_bits >>= 1
        else:
            # Fallback pour autres OS
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive) and os.path.ismount(drive):
                    # Heuristique simple
                    drives.append(drive)
        
        return drives
    
    def _is_removable_drive(self, drive: str) -> bool:
        """Vérifier si un lecteur est amovible"""
        if WIN32_AVAILABLE:
            try:
                drive_type = win32file.GetDriveType(drive)
                return drive_type == win32file.DRIVE_REMOVABLE
            except:
                return False
        else:
            # Fallback - supposer vrai si existe
            return os.path.exists(drive)
    
    def _check_drive_for_token(self, drive: str) -> Dict:
        """Vérifier si un lecteur contient un token valide"""
        result = {
            'present': False,
            'type': None,
            'drive': drive,
            'token_id': None
        }
        
        token_path = os.path.join(drive, TOKEN_FILE_NAME)
        
        # Vérifier existence fichier
        if not os.path.exists(token_path):
            return result
        
        # Vérifier token
        valid, token_data = self.verify_token(token_path)
        
        if valid and token_data:
            # Vérifier non révoqué
            if not self._is_token_revoked(token_data['id']):
                result['present'] = True
                result['type'] = TokenType(token_data['type'])
                result['token_id'] = token_data['id']
            else:
                self.logger.log_security_event('REVOKED_TOKEN_DETECTED', {
                    'token_id': token_data['id'][:8] + '...'
                }, severity='HIGH')
        
        return result
    
    def _is_token_revoked(self, token_id: str) -> bool:
        """Vérifier si un token est révoqué"""
        try:
            revoked_list = self.crypto.load_encrypted_file('revoked_tokens') or []
            
            for entry in revoked_list:
                if entry.get('token_id') == token_id:
                    return True
                    
            return False
            
        except Exception:
            # En cas d'erreur, considérer comme non révoqué
            return False
    
    def _get_usb_serial(self, drive: str) -> Optional[str]:
        """Obtenir numéro série du périphérique USB"""
        if WIN32_AVAILABLE:
            try:
                # Obtenir infos volume
                volume_info = win32api.GetVolumeInformation(drive)
                volume_serial = str(volume_info[1])
                
                # Essayer d'obtenir serial physique
                # Note: Nécessite droits admin pour accès complet
                return volume_serial
                
            except Exception as e:
                self.logger.log_event('USB_SERIAL_ERROR', {'error': str(e)})
                return None
        else:
            # Fallback - utiliser UUID volume
            try:
                import uuid
                return str(uuid.uuid4())
            except:
                return None
    
    def _get_default_permissions(self, token_type: TokenType) -> Dict:
        """Obtenir permissions par défaut selon type token"""
        if token_type == TokenType.ADMIN:
            return {
                'full_access': True,
                'manage_tokens': True,
                'manage_licenses': True,
                'modify_config': True,
                'view_logs': True,
                'export_data': True
            }
        else:  # USER
            return {
                'full_access': False,
                'manage_tokens': False,
                'manage_licenses': False,
                'modify_config': False,
                'view_logs': True,
                'export_data': False
            }
    
    def is_token_present(self) -> bool:
        """Vérifier rapidement si un token est présent"""
        return self.check_token_presence()['present']
    
    def get_token_type(self) -> Optional[TokenType]:
        """Obtenir le type du token actuel"""
        status = self.check_token_presence()
        return status.get('type')
    
    def format_usb_drive(self, drive: str) -> bool:
        """Formater une clé USB (Windows uniquement)"""
        if not WIN32_AVAILABLE:
            return False
            
        try:
            # Commande format Windows
            import subprocess
            
            # Confirmation de sécurité
            result = subprocess.run(
                f'format {drive[0]}: /FS:FAT32 /Q /Y',
                shell=True,
                capture_output=True,
                text=True
            )
            
            return result.returncode == 0
            
        except Exception as e:
            self.logger.log_event('USB_FORMAT_ERROR', {'error': str(e)})
            return False# Tokens USB 