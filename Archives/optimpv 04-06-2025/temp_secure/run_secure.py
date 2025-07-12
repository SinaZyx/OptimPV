# Protection Anti-Debug
import sys, os
try:
    if sys.gettrace(): os._exit(1)
    sys.dont_write_bytecode = True
except: pass


# Protection runtime
import _v1K00JOIyn as _sys
_sys.dont_write_bytecode = True

# Anti-debug basique
if _sys.gettrace() is not None:
    _sys.exit(1)

# Vérification environnement
_suspicious = [__import__('base64').b64decode('UFlERVZE').decode(), __import__('base64').b64decode('UFlUSE9OREVCVUc=').decode(), __import__('base64').b64decode('UFlUSE9OSU5TUEVDVA==').decode(), __import__('base64').b64decode('X1BZREVWX0NPTVBMRVRFUl9QWVRIT05QQVRI').decode()]
if any(_v in __import__(__import__('base64').b64decode('X3YwT2lwb21E').decode()).environ for _v in _suspicious):
    __import__(__import__('base64').b64decode('X3YwT2lwb21E').decode())._exit(1)

# Hook protection
_sys.settrace(None)
__builtins__.__dict__['__import__'] = __import__

import _v0OipomD
import _v1K00JOIyn
import _vOIIOo1OO

# Ignorer les _vOIIOo1OO
_vOIIOo1OO.filterwarnings(__import__('base64').b64decode('aWdub3Jl').decode())

# PROTECTION FORCÉE
from licence_guard import initialize_protection

# Vérifier la licence - OBLIGATOIRE
if not initialize_protection():
    _v1K00JOIyn.exit(1)

# Fix scipy
_v0OipomD.environ[__import__('base64').b64decode('U0NJUFlfUElMT1RfREFUQV9ESVI=').decode()] = _v0OipomD._vuQlDO0Iioi0s.dirname(_v1K00JOIyn.executable)

# Imports streamlit
import streamlit
import streamlit.web.cli as _vio1UioM

def _vIoIH0U0oeOo(_vuQlDO0Iioi0s):
    if getattr(_v1K00JOIyn, __import__('base64').b64decode('ZnJvemVu').decode(), False):
        _v0RqIi1TiiO = _v1K00JOIyn._MEIPASS
    else:
        _v0RqIi1TiiO = _v0OipomD._vuQlDO0Iioi0s.dirname(_v0OipomD._vuQlDO0Iioi0s.abspath(__file__))
    return _v0OipomD._vuQlDO0Iioi0s.join(_v0RqIi1TiiO, _vuQlDO0Iioi0s)

if __name__ == "__main__":
    if getattr(_v1K00JOIyn, __import__('base64').b64decode('ZnJvemVu').decode(), False):
        _v0OipomD.chdir(_v1K00JOIyn._MEIPASS)
    
    _v1K00JOIyn.argv = [
        __import__('base64').b64decode('c3RyZWFtbGl0').decode(),
        __import__('base64').b64decode('cnVu').decode(), 
        _vIoIH0U0oeOo(__import__('base64').b64decode('YXBwLnB5').decode()),
        __import__('base64').b64decode('LS1nbG9iYWwuZGV2ZWxvcG1lbnRNb2RlPWZhbHNl').decode(),
        __import__('base64').b64decode('LS1zZXJ2ZXIuaGVhZGxlc3M9dHJ1ZQ==').decode(),
        __import__('base64').b64decode('LS1icm93c2VyLnNlcnZlckFkZHJlc3M9bG9jYWxob3N0').decode(),
        __import__('base64').b64decode('LS1zZXJ2ZXIuZW5hYmxlQ09SUz1mYWxzZQ==').decode(),
        __import__('base64').b64decode('LS1zZXJ2ZXIuZW5hYmxlWHNyZlByb3RlY3Rpb249ZmFsc2U=').decode()
    ]
    
    _v1K00JOIyn.exit(_vio1UioM.main()) 
