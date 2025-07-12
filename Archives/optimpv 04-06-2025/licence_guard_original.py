#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de protection par licence pour OptimPV Pro - V2
Avec système d'autodestruction amélioré et multi-approches
"""

import os
import sys
import json
import hashlib
import shutil
import ctypes
import tempfile
import time
import subprocess
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import base64

class LicenceGuard:
    def __init__(self):
        # Clé maître (doit correspondre à celle de create_token_admin.py)
        self.MASTER_KEY = b"OptimPV_Pro_2025_SecureDeployment"
        self.TOKEN_VERSION = "1.0"
        self.token_verified = False
        
    def find_token_file(self):
        """Recherche le fichier token dans les emplacements possibles"""
        possible_locations = []
        
        # 1. Clés USB (Windows)
        if sys.platform == "win32":
            import string
            drives = ['%s:' % d for d in string.ascii_uppercase if os.path.exists('%s:' % d)]
            for drive in drives:
                # Vérifier si c'est un disque amovible
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive + "\\")
                if drive_type == 2:  # DRIVE_REMOVABLE
                    possible_locations.append(os.path.join(drive, "\\", "sys.dat"))
        
        # 2. %LOCALAPPDATA%\OptimPV\sys.dat (priorité pour AppData Local)
        localappdata_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'OptimPV')
        localappdata_path = os.path.join(localappdata_dir, 'sys.dat')
        possible_locations.append(localappdata_path)
        
        # Créer le dossier LocalAppData s'il n'existe pas
        try:
            if not os.path.exists(localappdata_dir):
                os.makedirs(localappdata_dir, exist_ok=True)
                print(f"[Guard] Dossier créé : {localappdata_dir}")
        except Exception as e:
            print(f"[Guard] Impossible de créer {localappdata_dir} : {e}")
        
        # 3. %APPDATA%\OptimPV\sys.dat (AppData Roaming)
        appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'OptimPV')
        appdata_path = os.path.join(appdata_dir, 'sys.dat')
        possible_locations.append(appdata_path)
        
        # Créer le dossier AppData Roaming s'il n'existe pas
        try:
            if not os.path.exists(appdata_dir):
                os.makedirs(appdata_dir, exist_ok=True)
                print(f"[Guard] Dossier créé : {appdata_dir}")
        except Exception as e:
            print(f"[Guard] Impossible de créer {appdata_dir} : {e}")
        
        # 4. %PROGRAMDATA%\OptimPV\sys.dat
        programdata_path = os.path.join(os.environ.get('PROGRAMDATA', 'C:\\ProgramData'), 'OptimPV', 'sys.dat')
        possible_locations.append(programdata_path)
        
        # 5. Dossier de l'exécutable
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            possible_locations.append(os.path.join(exe_dir, "sys.dat"))
        
        # Rechercher le premier token valide
        for location in possible_locations:
            if os.path.exists(location):
                print(f"[Guard] Token trouvé : {location}")
                return location
        
        return None
    
    def decrypt_token(self, encrypted_data):
        """Déchiffre les données du token"""
        try:
            # Décoder depuis base64
            cipher_data = base64.b64decode(encrypted_data)
            
            # Extraire IV et données
            iv = cipher_data[:16]
            encrypted = cipher_data[16:]
            
            # Générer la clé AES
            key = hashlib.sha256(self.MASTER_KEY).digest()
            
            # Déchiffrer
            cipher = Cipher(
                algorithms.AES(key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(encrypted) + decryptor.finalize()
            
            # Retirer le padding
            unpadder = padding.PKCS7(128).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()
            
            return json.loads(data.decode('utf-8'))
        except Exception as e:
            print(f"[Guard] Erreur déchiffrement : {e}")
            return None
    
    def validate_token(self, token_path):
        """Valide le fichier token"""
        try:
            with open(token_path, 'rb') as f:
                # Vérifier les magic bytes
                magic = f.read(5)
                if magic != b"OPTPV":
                    return False
                
                # Lire la taille des données JSON
                size_bytes = f.read(4)
                json_size = int.from_bytes(size_bytes, 'little')
                
                # Lire les données JSON
                json_data = f.read(json_size).decode('utf-8')
                token_structure = json.loads(json_data)
                
                # Vérifier la structure
                if token_structure.get("header") != "OPTIMPV_PRO_TOKEN":
                    return False
                
                # Vérifier la signature
                payload = token_structure.get("payload", "")
                expected_sig = hashlib.sha512(payload.encode()).hexdigest()
                if token_structure.get("signature") != expected_sig:
                    return False
                
                # Déchiffrer et valider le contenu
                token_data = self.decrypt_token(payload)
                if not token_data:
                    return False
                
                # Vérifier le checksum
                checksum = token_data.pop("checksum", "")
                data_str = json.dumps(token_data, sort_keys=True, default=str)
                calculated_checksum = hashlib.sha256(data_str.encode()).hexdigest()
                
                if checksum != calculated_checksum:
                    return False
                
                # Token valide !
                print(f"[Guard] Token validé - Organisation : {token_data.get('organization')}")
                return True
                
        except Exception as e:
            print(f"[Guard] Erreur validation : {e}")
            return False
    
    def corrupt_executable(self, exe_path):
        """Corrompt l'exécutable pour le rendre inutilisable"""
        try:
            # Lire la taille du fichier
            file_size = os.path.getsize(exe_path)
            
            # Ouvrir en mode lecture/écriture binaire
            with open(exe_path, 'r+b') as f:
                # Corrompre le header PE (les premiers 4KB)
                f.seek(0)
                f.write(b'\x00' * min(4096, file_size))
                
                # Corrompre le point d'entrée (généralement vers 0x400)
                if file_size > 1024:
                    f.seek(1024)
                    f.write(os.urandom(1024))
                
                # Corrompre la fin du fichier
                if file_size > 8192:
                    f.seek(-4096, 2)  # 4KB avant la fin
                    f.write(os.urandom(4096))
                
                f.flush()
                os.fsync(f.fileno())
            
            print("[Guard] ✓ Exécutable corrompu avec succès")
            return True
            
        except Exception as e:
            print(f"[Guard] Erreur corruption : {e}")
            return False
    
    def create_delayed_deletion_script(self, exe_path):
        """Crée un script VBS pour suppression différée"""
        vbs_content = f'''
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' Attendre que le processus se termine
WScript.Sleep 5000

' Tentatives multiples de suppression
For i = 1 To 10
    On Error Resume Next
    
    ' Tenter de supprimer le fichier
    If FSO.FileExists("{exe_path}") Then
        FSO.DeleteFile "{exe_path}", True
        If Err.Number = 0 Then
            Exit For
        End If
    End If
    
    ' Attendre avant de réessayer
    WScript.Sleep 2000
Next

' Nettoyer les traces
If FSO.FileExists("{exe_path}.corrupted") Then
    FSO.DeleteFile "{exe_path}.corrupted", True
End If

' Auto-suppression du script
FSO.DeleteFile WScript.ScriptFullName, True
'''
        
        try:
            # Créer le script VBS dans temp
            vbs_path = os.path.join(tempfile.gettempdir(), f"cleanup_{os.getpid()}.vbs")
            with open(vbs_path, 'w') as f:
                f.write(vbs_content)
            
            # Lancer le script VBS de manière asynchrone
            subprocess.Popen(['wscript.exe', vbs_path], 
                           creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
            
            print("[Guard] Script de suppression différée lancé")
            return True
            
        except Exception as e:
            print(f"[Guard] Erreur création script VBS : {e}")
            return False
    
    def self_destruct(self):
        """Autodestruction multi-approches de l'exécutable"""
        print("[Guard] ⚠️  AUTODESTRUCTION ACTIVÉE")
        
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
            temp_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else None
            
            # Approche 1 : Corruption de l'exécutable
            print("[Guard] Tentative 1 : Corruption du fichier...")
            if self.corrupt_executable(exe_path):
                print("[Guard] ✓ Fichier corrompu - Ne pourra plus démarrer")
            
            # Approche 2 : Renommage pour masquer l'EXE
            try:
                corrupted_name = exe_path + ".corrupted"
                os.rename(exe_path, corrupted_name)
                print(f"[Guard] ✓ Fichier renommé : {corrupted_name}")
                exe_path = corrupted_name  # Mettre à jour le chemin pour la suppression
            except Exception as e:
                print(f"[Guard] ! Renommage échoué : {e}")
            
            # Approche 3 : Script de suppression différée (VBS)
            self.create_delayed_deletion_script(exe_path)
            
            # Approche 4 : Commande PowerShell asynchrone
            try:
                ps_cmd = f'''
                Start-Sleep -Seconds 5;
                Remove-Item -Path "{exe_path}" -Force -ErrorAction SilentlyContinue;
                '''
                subprocess.Popen(['powershell', '-WindowStyle', 'Hidden', '-Command', ps_cmd],
                               creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
                print("[Guard] Script PowerShell de nettoyage lancé")
            except:
                pass
            
            # Approche 5 : Marquer pour suppression au redémarrage (Windows)
            try:
                import winreg
                key_path = r"SYSTEM\CurrentControlSet\Control\Session Manager"
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, 
                                   winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE) as key:
                    # Lire les valeurs existantes
                    try:
                        existing = winreg.QueryValueEx(key, "PendingFileRenameOperations")[0]
                    except:
                        existing = []
                    
                    # Ajouter notre fichier
                    new_entries = existing + [exe_path, '']
                    winreg.SetValueEx(key, "PendingFileRenameOperations", 0, 
                                    winreg.REG_MULTI_SZ, new_entries)
                    print("[Guard] ✓ Suppression programmée au prochain redémarrage")
            except Exception as e:
                print(f"[Guard] ! Marquage pour suppression échoué : {e}")
        
        # Message final
        print("[Guard] 💀 PROTECTION ACTIVÉE - Programme inutilisable")
        print("[Guard] Le fichier a été corrompu et sera supprimé")
        time.sleep(2)
        
        # Terminer le processus
        os._exit(1)
    
    def check_and_protect(self):
        """Point d'entrée principal de la protection"""
        print("[Guard] Vérification de la licence...")
        
        # Rechercher le token
        token_path = self.find_token_file()
        
        if not token_path:
            print("[Guard] ❌ ERREUR : Token de licence introuvable")
            print("[Guard] L'application cherche sys.dat dans cet ordre :")
            print("[Guard]   1. Clés USB connectées")
            print("[Guard]   2. %LOCALAPPDATA%\\OptimPV\\")
            print("[Guard]   3. %APPDATA%\\OptimPV\\")
            print("[Guard]   4. %PROGRAMDATA%\\OptimPV\\")
            print("[Guard]   5. Dossier de l'application")
            time.sleep(3)
            self.self_destruct()
            return False
        
        # Valider le token
        if not self.validate_token(token_path):
            print("[Guard] ❌ ERREUR : Token invalide ou corrompu")
            time.sleep(3)
            self.self_destruct()
            return False
        
        # Token valide
        print("[Guard] ✅ Licence validée - Démarrage autorisé")
        self.token_verified = True
        return True
    
    def periodic_check(self):
        """Vérification périodique (optionnel)"""
        # Peut être appelé périodiquement pendant l'exécution
        if not self.token_verified:
            self.self_destruct()

# Instance globale
_guard = None

def initialize_protection():
    """Initialise la protection - À appeler au début de run.py"""
    global _guard
    _guard = LicenceGuard()
    return _guard.check_and_protect()

def get_guard():
    """Retourne l'instance du guard pour vérifications ultérieures"""
    return _guard