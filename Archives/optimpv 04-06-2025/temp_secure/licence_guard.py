
# Protection runtime
import _vIl10Mvp as _sys
_sys.dont_write_bytecode = True

# Anti-debug basique
if _sys.gettrace() is not None:
    _sys.exit(1)

# Vérification environnement
_suspicious = [__import__('base64').b64decode('UFlERVZE').decode(), __import__('base64').b64decode('UFlUSE9OREVCVUc=').decode(), __import__('base64').b64decode('UFlUSE9OSU5TUEVDVA==').decode(), __import__('base64').b64decode('X1BZREVWX0NPTVBMRVRFUl9QWVRIT05QQVRI').decode()]
if any(_v in __import__(__import__('base64').b64decode('X3ZsaWlvMU8xVkUxMTE=').decode()).environ for _v in _suspicious):
    __import__(__import__('base64').b64decode('X3ZsaWlvMU8xVkUxMTE=').decode())._exit(1)

# Hook protection
_sys.settrace(None)
__builtins__.__dict__['__import__'] = __import__

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de protection par licence pour OptimPV Pro - V2
Avec système _v1i1rI1DIIOXi'autodestruction amélioré et multi-approches
"""

import _vliio1O1VE111
import _vIl10Mvp
import _vOOio0itlIo
import _vSiiOi0IOI1w
import shutil
import _viiolI1iq10F
import _v10XoucI
import _vi01I0iOO
import _vinETu0
from cryptography.hazmat.primitives.ciphers import _vX0ilOI, _vKOl1ig1Ol0vZ, _vIol0b0slHIlo
from cryptography.hazmat.primitives import _v0WZloiOIiknq
from cryptography.hazmat.backends import _volOvool
import _vlhX10io0IlI

class LicenceGuard:
    def __init__(self):
        # Clé maître (doit correspondre à celle de create_token_admin.py)
        self.MASTER_KEY = b__import__('base64').b64decode('T3B0aW1QVl9Qcm9fMjAyNV9TZWN1cmVEZXBsb3ltZW50').decode()
        self.TOKEN_VERSION = __import__('base64').b64decode('MS4w').decode()
        self.token_verified = False
        
    def _f01IiOI(self):
        ""__import__('base64').b64decode('UmVjaGVyY2hlIGxlIGZpY2hpZXIgdG9rZW4gZGFucyBsZXMgZW1wbGFjZW1lbnRzIHBvc3NpYmxlcw==').decode()""
        _vl0EWo11iOO0A = []
        
        # 1. Clés USB (Windows)
        if _vIl10Mvp.platform == __import__('base64').b64decode('d2luMzI=').decode():
            import _vnll1Oiilod
            _vEUmodO0iG = [__import__('base64').b64decode('JXM6').decode() % _v1i1rI1DIIOXi for _v1i1rI1DIIOXi in _vnll1Oiilod.ascii_uppercase if _vliio1O1VE111.path.exists(__import__('base64').b64decode('JXM6').decode() % _v1i1rI1DIIOXi)]
            for _vIi0r1IOIi in _vEUmodO0iG:
                # Vérifier si c'est un disque amovible
                _vIi11p1l000 = _viiolI1iq10F.windll.kernel32.GetDriveTypeW(_vIi0r1IOIi + "\\")
                if _vIi11p1l000 == 2:  # DRIVE_REMOVABLE
                    _vl0EWo11iOO0A.append(_vliio1O1VE111.path.join(_vIi0r1IOIi, "\\", __import__('base64').b64decode('X3ZJbDEwTXZwLmRhdA==').decode()))
        
        # 2. %LOCALAPPDATA%\OptimPV\_vIl10Mvp.dat (priorité pour AppData Local)
        _voodL0IjiI = _vliio1O1VE111.path.join(_vliio1O1VE111.environ.get(__import__('base64').b64decode('TE9DQUxBUFBEQVRB').decode(), ''), __import__('base64').b64decode('T3B0aW1QVg==').decode())
        _v1I10O1IIOiOi = _vliio1O1VE111.path.join(_voodL0IjiI, __import__('base64').b64decode('X3ZJbDEwTXZwLmRhdA==').decode())
        _vl0EWo11iOO0A.append(_v1I10O1IIOiOi)
        
        # Créer le dossier LocalAppData s__import__('base64').b64decode('aWwgbg==').decode()existe pas
        try:
            if not _vliio1O1VE111.path.exists(_voodL0IjiI):
                _vliio1O1VE111.makedirs(_voodL0IjiI, exist_ok=True)
                print(_vo0hiFOl__import__('base64').b64decode('W0d1YXJkXSBEb3NzaWVyIGNyw6nDqSA6IHtfdm9vZEwwSWppSX0=').decode())
        except _v10Ri0iI as _vlIIly1:
            print(_vo0hiFOl__import__('base64').b64decode('W0d1YXJkXSBJbXBvc3NpYmxlIGRlIGNyw6llciB7X3Zvb2RMMElqaUl9IDoge192bElJbHkxfQ==').decode())
        
        # 3. %APPDATA%\OptimPV\_vIl10Mvp.dat (AppData Roaming)
        _vp1OliO1iiph = _vliio1O1VE111.path.join(_vliio1O1VE111.environ.get(__import__('base64').b64decode('QVBQREFUQQ==').decode(), ''), __import__('base64').b64decode('T3B0aW1QVg==').decode())
        _vil1I0l1 = _vliio1O1VE111.path.join(_vp1OliO1iiph, __import__('base64').b64decode('X3ZJbDEwTXZwLmRhdA==').decode())
        _vl0EWo11iOO0A.append(_vil1I0l1)
        
        # Créer le dossier AppData Roaming s__import__('base64').b64decode('aWwgbg==').decode()existe pas
        try:
            if not _vliio1O1VE111.path.exists(_vp1OliO1iiph):
                _vliio1O1VE111.makedirs(_vp1OliO1iiph, exist_ok=True)
                print(_vo0hiFOl__import__('base64').b64decode('W0d1YXJkXSBEb3NzaWVyIGNyw6nDqSA6IHtfdnAxT2xpTzFpaXBofQ==').decode())
        except _v10Ri0iI as _vlIIly1:
            print(_vo0hiFOl__import__('base64').b64decode('W0d1YXJkXSBJbXBvc3NpYmxlIGRlIGNyw6llciB7X3ZwMU9saU8xaWlwaH0gOiB7X3ZsSUlseTF9').decode())
        
        # 4. %PROGRAMDATA%\OptimPV\_vIl10Mvp.dat
        _vZ0i1iolii = _vliio1O1VE111.path.join(_vliio1O1VE111.environ.get(__import__('base64').b64decode('UFJPR1JBTURBVEE=').decode(), __import__('base64').b64decode('QzpcXFByb2dyYW1EYXRh').decode()), __import__('base64').b64decode('T3B0aW1QVg==').decode(), __import__('base64').b64decode('X3ZJbDEwTXZwLmRhdA==').decode())
        _vl0EWo11iOO0A.append(_vZ0i1iolii)
        
        # 5. Dossier de l'exécutable
        if getattr(_vIl10Mvp, __import__('base64').b64decode('ZnJvemVu').decode(), False):
            _vi1OI0yY1 = _vliio1O1VE111.path.dirname(_vIl10Mvp.executable)
            _vl0EWo11iOO0A.append(_vliio1O1VE111.path.join(_vi1OI0yY1, __import__('base64').b64decode('X3ZJbDEwTXZwLmRhdA==').decode()))
        
        # Rechercher le premier token valide
        for _v0p1iYl1 in _vl0EWo11iOO0A:
            if _vliio1O1VE111.path.exists(_v0p1iYl1):
                print(_vo0hiFOl__import__('base64').b64decode('W0d1YXJkXSBUb2tlbiB0cm91dsOpIDoge192MHAxaVlsMX0=').decode())
                return _v0p1iYl1
        
        return None
    
    def decrypt_token(self, _voI01zOOoIWxl):
        ""__import__('base64').b64decode('RMOpY2hpZmZyZSBsZXMgZG9ubsOpZXMgZHUgdG9rZW4=').decode()""
        try:
            # Décoder depuis _vlhX10io0IlI
            _v1looO0I1 = _vlhX10io0IlI.b64decode(_voI01zOOoIWxl)
            
            # Extraire IV et données
            _v0iIiI1j = _v1looO0I1[:16]
            _vIOrO1lIlIU = _v1looO0I1[16:]
            
            # Générer la clé AES
            _vwc0Ob0O = _vSiiOi0IOI1w.sha256(self.MASTER_KEY).digest()
            
            # Déchiffrer
            _vlI1o0ccolRXI = _vX0ilOI(
                _vKOl1ig1Ol0vZ.AES(_vwc0Ob0O),
                _vIol0b0slHIlo.CBC(_v0iIiI1j),
                backend=_volOvool()
            )
            _vOlEon0oq = _vlI1o0ccolRXI._vOlEon0oq()
            _vD0OlwYI01IIl = _vOlEon0oq.update(_vIOrO1lIlIU) + _vOlEon0oq.finalize()
            
            # Retirer le _v0WZloiOIiknq
            _viYlibd011i = _v0WZloiOIiknq.PKCS7(128)._viYlibd011i()
            _vr0i1oooIIoNi = _viYlibd011i.update(_vD0OlwYI01IIl) + _viYlibd011i.finalize()
            
            return _vOOio0itlIo.loads(_vr0i1oooIIoNi.decode(__import__('base64').b64decode('dXRmLTg=').decode()))
        except _v10Ri0iI as _vlIIly1:
            print(_vo0hiFOl__import__('base64').b64decode('W0d1YXJkXSBFcnJldXIgZMOpY2hpZmZyZW1lbnQgOiB7X3ZsSUlseTF9').decode())
            return None
    
    def validate_token(self, _vpscoll0Ihli):
        ""__import__('base64').b64decode('VmFsaWRlIGxlIGZpY2hpZXIgdG9rZW4=').decode()""
        try:
            with open(_vpscoll0Ihli, 'rb') as _vo0hiFOl:
                # Vérifier les _vpI1ioKII0 bytes
                _vpI1ioKII0 = _vo0hiFOl.read(5)
                if _vpI1ioKII0 != b__import__('base64').b64decode('T1BUUFY=').decode():
                    return False
                
                # Lire la taille des données JSON
                _vl1KRuOki = _vo0hiFOl.read(4)
                _vIiIsfal0O = int.from_bytes(_vl1KRuOki, __import__('base64').b64decode('bGl0dGxl').decode())
                
                # Lire les données JSON
                _vl0Nllj1Oko = _vo0hiFOl.read(_vIiIsfal0O).decode(__import__('base64').b64decode('dXRmLTg=').decode())
                _vniKOoi = _vOOio0itlIo.loads(_vl0Nllj1Oko)
                
                # Vérifier la structure
                if _vniKOoi.get(__import__('base64').b64decode('aGVhZGVy').decode()) != __import__('base64').b64decode('T1BUSU1QVl9QUk9fVE9LRU4=').decode():
                    return False
                
                # Vérifier la signature
                _voIul1iji = _vniKOoi.get(__import__('base64').b64decode('X3ZvSXVsMWlqaQ==').decode(), "")
                _vQl1HSl00liqO = _vSiiOi0IOI1w.sha512(_voIul1iji.encode()).hexdigest()
                if _vniKOoi.get(__import__('base64').b64decode('c2lnbmF0dXJl').decode()) != _vQl1HSl00liqO:
                    return False
                
                # Déchiffrer et valider le contenu
                _vo0bOGOlsolo = self.decrypt_token(_voIul1iji)
                if not _vo0bOGOlsolo:
                    return False
                
                # Vérifier le _v0Olzjo
                _v0Olzjo = _vo0bOGOlsolo.pop(__import__('base64').b64decode('X3YwT2x6am8=').decode(), "")
                _viTIIl1oO0x0 = _vOOio0itlIo.dumps(_vo0bOGOlsolo, sort_keys=True, default=str)
                _vO00lco = _vSiiOi0IOI1w.sha256(_viTIIl1oO0x0.encode()).hexdigest()
                
                if _v0Olzjo != _vO00lco:
                    return False
                
                # Token valide !
                print(_vo0hiFOl__import__('base64').b64decode('W0d1YXJkXSBUb2tlbiB2YWxpZMOpIC0gT3JnYW5pc2F0aW9uIDoge192bzBiT0dPbHNvbG8uZ2V0KCdvcmdhbml6YXRpb24nKX0=').decode())
                return True
                
        except _v10Ri0iI as _vlIIly1:
            print(_vo0hiFOl__import__('base64').b64decode('W0d1YXJkXSBFcnJldXIgdmFsaWRhdGlvbiA6IHtfdmxJSWx5MX0=').decode())
            return False
    
    def corrupt_executable(self, _vIquHiOHiH):
        ""__import__('base64').b64decode('Q29ycm9tcHQgbCdleMOpY3V0YWJsZSBwb3VyIGxlIHJlbmRyZSBpbnV0aWxpc2FibGU=').decode()""
        try:
            # Lire la taille du fichier
            _vToolaG0 = _vliio1O1VE111.path.getsize(_vIquHiOHiH)
            
            # Ouvrir en mode lecture/écriture binaire
            with open(_vIquHiOHiH, __import__('base64').b64decode('citi').decode()) as _vo0hiFOl:
                # Corrompre le header PE (les premiers 4KB)
                _vo0hiFOl.seek(0)
                _vo0hiFOl.write(b__import__('base64').b64decode('XHgwMA==').decode() * _v01lO0luplI(4096, _vToolaG0))
                
                # Corrompre le point _v1i1rI1DIIOXi'entrée (généralement vers 0x400)
                if _vToolaG0 > 1024:
                    _vo0hiFOl.seek(1024)
                    _vo0hiFOl.write(_vliio1O1VE111.urandom(1024))
                
                # Corrompre la fin du fichier
                if _vToolaG0 > 8192:
                    _vo0hiFOl.seek(-4096, 2)  # 4KB avant la fin
                    _vo0hiFOl.write(_vliio1O1VE111.urandom(4096))
                
                _vo0hiFOl.flush()
                _vliio1O1VE111.fsync(_vo0hiFOl.fileno())
            
            print(__import__('base64').b64decode('W0d1YXJkXSDinJMgRXjDqWN1dGFibGUgY29ycm9tcHUgYXZlYyBzdWNjw6hz').decode())
            return True
            
        except _v10Ri0iI as _vlIIly1:
            print(_vo0hiFOl__import__('base64').b64decode('W0d1YXJkXSBFcnJldXIgY29ycnVwdGlvbiA6IHtfdmxJSWx5MX0=').decode())
            return False
    
    def _f1I0Oi1(self, _vIquHiOHiH):
        ""__import__('base64').b64decode('Q3LDqWUgdW4gc2NyaXB0IFZCUyBwb3VyIHN1cHByZXNzaW9uIGRpZmbDqXLDqWU=').decode()""
        _vIXO1I0IYoq = _vo0hiFOl'''
Set WshShell = CreateObject(__import__('base64').b64decode('V1NjcmlwdC5TaGVsbA==').decode())
Set FSO = CreateObject(__import__('base64').b64decode('U2NyaXB0aW5nLkZpbGVTeXN0ZW1PYmplY3Q=').decode())

' Attendre que le processus se termine
WScript.Sleep 5000

' Tentatives multiples de suppression
For i = 1 To 10
    On Error Resume Next
    
    ' Tenter de supprimer le fichier
    If FSO.FileExists(__import__('base64').b64decode('e192SXF1SGlPSGlIfQ==').decode()) Then
        FSO.DeleteFile __import__('base64').b64decode('e192SXF1SGlPSGlIfQ==').decode(), True
        If Err.Number = 0 Then
            Exit For
        End If
    End If
    
    ' Attendre avant de réessayer
    WScript.Sleep 2000
Next

' Nettoyer les traces
If FSO.FileExists(__import__('base64').b64decode('e192SXF1SGlPSGlIfS5jb3JydXB0ZWQ=').decode()) Then
    FSO.DeleteFile __import__('base64').b64decode('e192SXF1SGlPSGlIfS5jb3JydXB0ZWQ=').decode(), True
End If

' Auto-suppression du script
FSO.DeleteFile WScript.ScriptFullName, True
'''
        
        try:
            # Créer le script VBS dans temp
            _v0iiOlJl = _vliio1O1VE111.path.join(_v10XoucI.gettempdir(), _vo0hiFOl__import__('base64').b64decode('Y2xlYW51cF97X3ZsaWlvMU8xVkUxMTEuZ2V0cGlkKCl9LnZicw==').decode())
            with open(_v0iiOlJl, 'w') as _vo0hiFOl:
                _vo0hiFOl.write(_vIXO1I0IYoq)
            
            # Lancer le script VBS de manière asynchrone
            _vinETu0.Popen([__import__('base64').b64decode('d3NjcmlwdC5leGU=').decode(), _v0iiOlJl], 
                           creationflags=_vinETu0.CREATE_NO_WINDOW | _vinETu0.DETACHED_PROCESS)
            
            print(__import__('base64').b64decode('W0d1YXJkXSBTY3JpcHQgZGUgc3VwcHJlc3Npb24gZGlmZsOpcsOpZSBsYW5jw6k=').decode())
            return True
            
        except _v10Ri0iI as _vlIIly1:
            print(_vo0hiFOl__import__('base64').b64decode('W0d1YXJkXSBFcnJldXIgY3LDqWF0aW9uIHNjcmlwdCBWQlMgOiB7X3ZsSUlseTF9').decode())
            return False
    
    def self_destruct(self):
        ""__import__('base64').b64decode('QXV0b2Rlc3RydWN0aW9uIG11bHRpLWFwcHJvY2hlcyBkZSBsJ2V4w6ljdXRhYmxl').decode()""
        print(__import__('base64').b64decode('W0d1YXJkXSDimqDvuI8gIEFVVE9ERVNUUlVDVElPTiBBQ1RJVsOJRQ==').decode())
        
        if getattr(_vIl10Mvp, __import__('base64').b64decode('ZnJvemVu').decode(), False):
            _vIquHiOHiH = _vIl10Mvp.executable
            _vKToO0iil1 = _vIl10Mvp._MEIPASS if hasattr(_vIl10Mvp, __import__('base64').b64decode('X01FSVBBU1M=').decode()) else None
            
            # Approche 1 : Corruption de l'exécutable
            print(__import__('base64').b64decode('W0d1YXJkXSBUZW50YXRpdmUgMSA6IENvcnJ1cHRpb24gZHUgZmljaGllci4uLg==').decode())
            if self.corrupt_executable(_vIquHiOHiH):
                print(__import__('base64').b64decode('W0d1YXJkXSDinJMgRmljaGllciBjb3Jyb21wdSAtIE5lIHBvdXJyYSBwbHVzIGTDqW1hcnJlcg==').decode())
            
            # Approche 2 : Renommage pour masquer l'EXE
            try:
                _vMlHo0N = _vIquHiOHiH + __import__('base64').b64decode('LmNvcnJ1cHRlZA==').decode()
                _vliio1O1VE111.rename(_vIquHiOHiH, _vMlHo0N)
                print(_vo0hiFOl__import__('base64').b64decode('W0d1YXJkXSDinJMgRmljaGllciByZW5vbW3DqSA6IHtfdk1sSG8wTn0=').decode())
                _vIquHiOHiH = _vMlHo0N  # Mettre à jour le chemin pour la suppression
            except _v10Ri0iI as _vlIIly1:
                print(_vo0hiFOl__import__('base64').b64decode('W0d1YXJkXSAhIFJlbm9tbWFnZSDDqWNob3XDqSA6IHtfdmxJSWx5MX0=').decode())
            
            # Approche 3 : Script de suppression différée (VBS)
            self._f1I0Oi1(_vIquHiOHiH)
            
            # Approche 4 : Commande PowerShell asynchrone
            try:
                _vioOxbIO1ll = _vo0hiFOl'''
                Start-Sleep -Seconds 5;
                Remove-Item -Path __import__('base64').b64decode('e192SXF1SGlPSGlIfQ==').decode() -Force -ErrorAction SilentlyContinue;
                '''
                _vinETu0.Popen([__import__('base64').b64decode('cG93ZXJzaGVsbA==').decode(), __import__('base64').b64decode('LVdpbmRvd1N0eWxl').decode(), __import__('base64').b64decode('SGlkZGVu').decode(), __import__('base64').b64decode('LUNvbW1hbmQ=').decode(), _vioOxbIO1ll],
                               creationflags=_vinETu0.CREATE_NO_WINDOW | _vinETu0.DETACHED_PROCESS)
                print(__import__('base64').b64decode('W0d1YXJkXSBTY3JpcHQgUG93ZXJTaGVsbCBkZSBuZXR0b3lhZ2UgbGFuY8Op').decode())
            except:
                pass
            
            # Approche 5 : Marquer pour suppression au redémarrage (Windows)
            try:
                import _vbdoiC0io0
                _vldooyioiI = r__import__('base64').b64decode('U1lTVEVNXEN1cnJlbnRDb250cm9sU2V0XENvbnRyb2xcU2Vzc2lvbiBNYW5hZ2Vy').decode()
                with _vbdoiC0io0.OpenKey(_vbdoiC0io0.HKEY_LOCAL_MACHINE, _vldooyioiI, 0, 
                                   _vbdoiC0io0.KEY_SET_VALUE | _vbdoiC0io0.KEY_QUERY_VALUE) as _vwc0Ob0O:
                    # Lire les valeurs existantes
                    try:
                        _vCjIIiwililf = _vbdoiC0io0.QueryValueEx(_vwc0Ob0O, __import__('base64').b64decode('UGVuZGluZ0ZpbGVSZW5hbWVPcGVyYXRpb25z').decode())[0]
                    except:
                        _vCjIIiwililf = []
                    
                    # Ajouter notre fichier
                    _v1lglMlZic0o = _vCjIIiwililf + [_vIquHiOHiH, '']
                    _vbdoiC0io0.SetValueEx(_vwc0Ob0O, __import__('base64').b64decode('UGVuZGluZ0ZpbGVSZW5hbWVPcGVyYXRpb25z').decode(), 0, 
                                    _vbdoiC0io0.REG_MULTI_SZ, _v1lglMlZic0o)
                    print(__import__('base64').b64decode('W0d1YXJkXSDinJMgU3VwcHJlc3Npb24gcHJvZ3JhbW3DqWUgYXUgcHJvY2hhaW4gcmVkw6ltYXJyYWdl').decode())
            except _v10Ri0iI as _vlIIly1:
                print(_vo0hiFOl__import__('base64').b64decode('W0d1YXJkXSAhIE1hcnF1YWdlIHBvdXIgc3VwcHJlc3Npb24gw6ljaG91w6kgOiB7X3ZsSUlseTF9').decode())
        
        # Message final
        print(__import__('base64').b64decode('W0d1YXJkXSDwn5KAIFBST1RFQ1RJT04gQUNUSVbDiUUgLSBQcm9ncmFtbWUgaW51dGlsaXNhYmxl').decode())
        print(__import__('base64').b64decode('W0d1YXJkXSBMZSBmaWNoaWVyIGEgw6l0w6kgY29ycm9tcHUgZXQgc2VyYSBzdXBwcmltw6k=').decode())
        _vi01I0iOO.sleep(2)
        
        # Terminer le processus
        _vliio1O1VE111._exit(1)
    
    def check_and_protect(self):
        ""__import__('base64').b64decode('UG9pbnQgX3YxaTFySTFESUlPWGknZW50csOpZSBwcmluY2lwYWwgZGUgbGEgcHJvdGVjdGlvbg==').decode()""
        print(__import__('base64').b64decode('W0d1YXJkXSBWw6lyaWZpY2F0aW9uIGRlIGxhIGxpY2VuY2UuLi4=').decode())
        
        # Rechercher le token
        _vpscoll0Ihli = self._f01IiOI()
        
        if not _vpscoll0Ihli:
            print(__import__('base64').b64decode('W0d1YXJkXSDinYwgRVJSRVVSIDogVG9rZW4gZGUgbGljZW5jZSBpbnRyb3V2YWJsZQ==').decode())
            print(__import__('base64').b64decode('W0d1YXJkXSBMJ2FwcGxpY2F0aW9uIGNoZXJjaGUgX3ZJbDEwTXZwLmRhdCBkYW5zIGNldCBvcmRyZSA6').decode())
            print(__import__('base64').b64decode('W0d1YXJkXSAgIDEuIENsw6lzIFVTQiBjb25uZWN0w6llcw==').decode())
            print(__import__('base64').b64decode('W0d1YXJkXSAgIDIuICVMT0NBTEFQUERBVEElXFxPcHRpbVBWXFw=').decode())
            print(__import__('base64').b64decode('W0d1YXJkXSAgIDMuICVBUFBEQVRBJVxcT3B0aW1QVlxc').decode())
            print(__import__('base64').b64decode('W0d1YXJkXSAgIDQuICVQUk9HUkFNREFUQSVcXE9wdGltUFZcXA==').decode())
            print(__import__('base64').b64decode('W0d1YXJkXSAgIDUuIERvc3NpZXIgZGUgbCdhcHBsaWNhdGlvbg==').decode())
            _vi01I0iOO.sleep(3)
            self.self_destruct()
            return False
        
        # Valider le token
        if not self.validate_token(_vpscoll0Ihli):
            print(__import__('base64').b64decode('W0d1YXJkXSDinYwgRVJSRVVSIDogVG9rZW4gaW52YWxpZGUgb3UgY29ycm9tcHU=').decode())
            _vi01I0iOO.sleep(3)
            self.self_destruct()
            return False
        
        # Token valide
        print(__import__('base64').b64decode('W0d1YXJkXSDinIUgTGljZW5jZSB2YWxpZMOpZSAtIETDqW1hcnJhZ2UgYXV0b3Jpc8Op').decode())
        self.token_verified = True
        return True
    
    def _fodHO0oO(self):
        ""__import__('base64').b64decode('VsOpcmlmaWNhdGlvbiBww6lyaW9kaXF1ZSAob3B0aW9ubmVsKQ==').decode()""
        # Peut être appelé périodiquement pendant l'exécution
        if not self.token_verified:
            self.self_destruct()

# Instance globale
_vgo00i0 = None

def initialize_protection():
    ""__import__('base64').b64decode('SW5pdGlhbGlzZSBsYSBwcm90ZWN0aW9uIC0gw4AgYXBwZWxlciBhdSBkw6lidXQgZGUgcnVuLnB5').decode()""
    global _vgo00i0
    _vgo00i0 = LicenceGuard()
    return _vgo00i0.check_and_protect()

def _fiOi1QO0():
    ""__import__('base64').b64decode('UmV0b3VybmUgbCdpbnN0YW5jZSBkdSBndWFyZCBwb3VyIHbDqXJpZmljYXRpb25zIHVsdMOpcmlldXJlcw==').decode()""
    return _vgo00i0