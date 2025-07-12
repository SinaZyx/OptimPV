# security/crypto_store.py
"""
Stockage sécurisé avec chiffrement AES-256-GCM
"""

import os
import json
import base64
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hmac
from cryptography.fernet import Fernet

from utils.hardware_id import get_hardware_fingerprint
from config.constants import SECURE_CONFIG_DIR


class SecureStorage:
    """Gestionnaire de stockage sécurisé avec chiffrement"""
    
    def __init__(self):
        self.backend = default_backend()
        self.master_key = self._derive_master_key()
        self.fernet = Fernet(base64.urlsafe_b64encode(self.master_key[:32]))
        self._ensure_secure_directory()
    
    def _ensure_secure_directory(self):
        """S'assurer que le répertoire sécurisé existe"""
        SECURE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Restreindre permissions (Windows)
        if os.name == 'nt':
            try:
                import win32api
                import win32con
                
                # Cacher le répertoire
                win32api.SetFileAttributes(
                    str(SECURE_CONFIG_DIR),
                    win32con.FILE_ATTRIBUTE_HIDDEN
                )
            except:
                pass
    
    def _derive_master_key(self) -> bytes:
        """Dériver clé maître basée sur identifiants hardware"""
        # Sources d'entropie
        hardware_id = get_hardware_fingerprint()
        
        # Salt unique par installation
        salt_file = SECURE_CONFIG_DIR / ".salt"
        
        if salt_file.exists():
            with open(salt_file, 'rb') as f:
                salt = f.read()
        else:
            # Créer nouveau salt
            salt = os.urandom(32)
            with open(salt_file, 'wb') as f:
                f.write(salt)
            
            # Cacher fichier salt
            if os.name == 'nt':
                try:
                    import win32api
                    import win32con
                    win32api.SetFileAttributes(
                        str(salt_file),
                        win32con.FILE_ATTRIBUTE_HIDDEN | 
                        win32con.FILE_ATTRIBUTE_SYSTEM
                    )
                except:
                    pass
        
        # Dériver clé avec PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        
        key = kdf.derive(hardware_id.encode())
        return key
    
    def encrypt_data(self, data: Union[str, bytes, dict, list]) -> bytes:
        """Chiffrer données avec AES-256-GCM"""
        # Convertir en bytes si nécessaire
        if isinstance(data, (dict, list)):
            plaintext = json.dumps(data, ensure_ascii=False).encode()
        elif isinstance(data, str):
            plaintext = data.encode()
        elif isinstance(data, bytes):
            plaintext = data
        else:
            # Pour autres types, essayer JSON
            try:
                plaintext = json.dumps(data, ensure_ascii=False).encode()
            except (TypeError, ValueError):
                # Si non sérialisable JSON, convertir en string
                plaintext = str(data).encode()
        
        # Générer nonce aléatoire
        nonce = os.urandom(12)
        
        # Créer cipher
        cipher = Cipher(
            algorithms.AES(self.master_key[:32]),
            modes.GCM(nonce),
            backend=self.backend
        )
        
        encryptor = cipher.encryptor()
        
        # Ajouter données associées (timestamp)
        associated_data = datetime.now().isoformat().encode()
        encryptor.authenticate_additional_data(associated_data)
        
        # Chiffrer
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        
        # Format: nonce + tag + associated_data_length + associated_data + ciphertext
        return (
            nonce +
            encryptor.tag +
            len(associated_data).to_bytes(2, 'big') +
            associated_data +
            ciphertext
        )
    
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Déchiffrer données AES-256-GCM"""
        # Parser structure
        nonce = encrypted_data[:12]
        tag = encrypted_data[12:28]
        ad_length = int.from_bytes(encrypted_data[28:30], 'big')
        associated_data = encrypted_data[30:30+ad_length]
        ciphertext = encrypted_data[30+ad_length:]
        
        # Créer cipher
        cipher = Cipher(
            algorithms.AES(self.master_key[:32]),
            modes.GCM(nonce, tag),
            backend=self.backend
        )
        
        decryptor = cipher.decryptor()
        decryptor.authenticate_additional_data(associated_data)
        
        # Déchiffrer
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return plaintext
    
    def encrypt_and_sign(self, data: Any) -> bytes:
        """Chiffrer et signer données"""
        # Chiffrer
        encrypted = self.encrypt_data(data)
        
        # Calculer HMAC
        h = hmac.HMAC(self.master_key, hashes.SHA256(), backend=self.backend)
        h.update(encrypted)
        signature = h.finalize()
        
        # Format: signature + encrypted_data
        return signature + encrypted
    
    def decrypt_and_verify(self, signed_data: bytes) -> Any:
        """Vérifier signature et déchiffrer"""
        # Parser
        signature = signed_data[:32]
        encrypted_data = signed_data[32:]
        
        # Vérifier HMAC
        h = hmac.HMAC(self.master_key, hashes.SHA256(), backend=self.backend)
        h.update(encrypted_data)
        h.verify(signature)
        
        # Déchiffrer
        plaintext = self.decrypt_data(encrypted_data)
        
        # Parser JSON si possible
        try:
            return json.loads(plaintext.decode())
        except:
            return plaintext
    
    def save_encrypted_file(self, filename: str, data: Any):
        """Sauvegarder données chiffrées dans fichier"""
        filepath = SECURE_CONFIG_DIR / f"{filename}.enc"
        
        # Backup si existe
        if filepath.exists():
            backup_path = filepath.with_suffix('.enc.bak')
            filepath.rename(backup_path)
        
        try:
            # Chiffrer et signer
            encrypted_data = self.encrypt_and_sign(data)
            
            # Écrire
            with open(filepath, 'wb') as f:
                f.write(encrypted_data)
            
            # Supprimer backup si succès
            if filepath.with_suffix('.enc.bak').exists():
                filepath.with_suffix('.enc.bak').unlink()
                
        except Exception:
            # Restaurer backup si échec
            if filepath.with_suffix('.enc.bak').exists():
                filepath.with_suffix('.enc.bak').rename(filepath)
            raise
    
    def load_encrypted_file(self, filename: str) -> Optional[Any]:
        """Charger données chiffrées depuis fichier"""
        filepath = SECURE_CONFIG_DIR / f"{filename}.enc"
        
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'rb') as f:
                encrypted_data = f.read()
            
            return self.decrypt_and_verify(encrypted_data)
            
        except Exception as e:
            # Log mais ne pas faire crasher
            print(f"Erreur chargement {filename}: {e}")
            return None
    
    def save_encrypted_value(self, key: str, value: Any):
        """Sauvegarder une valeur simple chiffrée"""
        # Charger dictionnaire existant
        values = self.load_encrypted_file('secure_values') or {}
        
        # Mettre à jour
        values[key] = {
            'value': value,
            'updated': datetime.now().isoformat()
        }
        
        # Sauvegarder
        self.save_encrypted_file('secure_values', values)
    
    def load_encrypted_value(self, key: str) -> Optional[Any]:
        """Charger une valeur simple chiffrée"""
        values = self.load_encrypted_file('secure_values') or {}
        
        if key in values:
            return values[key]['value']
        
        return None
    
    def delete_encrypted_file(self, filename: str) -> bool:
        """Supprimer fichier chiffré de manière sécurisée"""
        filepath = SECURE_CONFIG_DIR / f"{filename}.enc"
        
        if not filepath.exists():
            return False
        
        try:
            # Écraser avec données aléatoires
            size = filepath.stat().st_size
            
            with open(filepath, 'wb') as f:
                for _ in range(3):  # 3 passes
                    f.seek(0)
                    f.write(os.urandom(size))
                    f.flush()
                    os.fsync(f.fileno())
            
            # Supprimer
            filepath.unlink()
            return True
            
        except Exception:
            return False
    
    def export_encrypted_backup(self, backup_path: str):
        """Exporter backup chiffré de toutes les données"""
        backup_data = {
            'version': '2.0',
            'timestamp': datetime.now().isoformat(),
            'files': {}
        }
        
        # Collecter tous les fichiers chiffrés
        for enc_file in SECURE_CONFIG_DIR.glob('*.enc'):
            filename = enc_file.stem
            data = self.load_encrypted_file(filename)
            if data is not None:
                backup_data['files'][filename] = data
        
        # Chiffrer avec mot de passe supplémentaire
        # (implémenter si nécessaire)
        
        # Sauvegarder
        with open(backup_path, 'wb') as f:
            encrypted = self.encrypt_and_sign(backup_data)
            f.write(encrypted)
    
    def import_encrypted_backup(self, backup_path: str) -> bool:
        """Importer backup chiffré"""
        try:
            with open(backup_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Déchiffrer et vérifier
            backup_data = self.decrypt_and_verify(encrypted_data)
            
            # Vérifier version
            if backup_data.get('version') != '2.0':
                return False
            
            # Restaurer fichiers
            for filename, data in backup_data['files'].items():
                self.save_encrypted_file(filename, data)
            
            return True
            
        except Exception:
            return False
    
    # Méthodes utilitaires pour Fernet (compatibilité)
    
    def encrypt_string(self, plaintext: str) -> str:
        """Chiffrer string et retourner base64"""
        encrypted = self.fernet.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_string(self, encrypted: str) -> str:
        """Déchiffrer string depuis base64"""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted.encode())
        decrypted = self.fernet.decrypt(encrypted_bytes)
        return decrypted.decode()# Stockage et gestion des clés cryptographiques 