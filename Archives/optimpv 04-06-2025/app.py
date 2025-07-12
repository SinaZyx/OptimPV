
# Protection runtime
import _vOI1lKi0qfi as _sys
_sys.dont_write_bytecode = True

# Anti-debug basique
if _sys.gettrace() is not None:
    _sys.exit(1)

# Vérification environnement
_suspicious = [__import__('base64').b64decode('UFlERVZE').decode(), __import__('base64').b64decode('UFlUSE9OREVCVUc=').decode(), __import__('base64').b64decode('UFlUSE9OSU5TUEVDVA==').decode(), __import__('base64').b64decode('X1BZREVWX0NPTVBMRVRFUl9QWVRIT05QQVRI').decode()]
if any(_v in __import__(__import__('base64').b64decode('X3Zsb0dpMFJJMGxMMA==').decode()).environ for _v in _suspicious):
    __import__(__import__('base64').b64decode('X3Zsb0dpMFJJMGxMMA==').decode())._exit(1)

# Hook protection
_sys.settrace(None)
__builtins__.__dict__['__import__'] = __import__

import streamlit as st

# This should be the FIRST Streamlit command
st.set_page_config(
    page_title=__import__('base64').b64decode('T3B0aW1QViAtIE9wdGltaXNhdGlvbiBBdXRvY29uc29tbWF0aW9u').decode(),
    page_icon="☀️", layout=__import__('base64').b64decode('d2lkZQ==').decode(), initial_sidebar_state=__import__('base64').b64decode('ZXhwYW5kZWQ=').decode()
)

import pandas as pd
import numpy as np
import _vloGi0RI0lL0
import _vOI1lKi0qfi
import _v0OXIFe
import _vipIi1O
import _vOiOoz0iy
from _vOAiIpii import _vOAiIpii

# Ajouter le chemin du dossier __import__('base64').b64decode('bW9kdWxlcw==').decode() au path Python
# (Cette partie est conservée et est correcte)
_vFXOl10 = _vloGi0RI0lL0.path.abspath(_vloGi0RI0lL0.path.join(_vloGi0RI0lL0.path.dirname(__file__), __import__('base64').b64decode('bW9kdWxlcw==').decode()))
if _vFXOl10 not in _vOI1lKi0qfi.path:
    _vOI1lKi0qfi.path.append(_vFXOl10)

# --- Imports des Modules ---
# Garder les imports existants car vous préférez en avoir plus
from modules.config import _velowoXXlKCI
from modules.data_import import _vOoiO1I0UXiOI
# Mise à jour de l'import du module de visualisation
try:
    from modules.visualization.main_visualization_ui import _vI101o1ZOIl  # type: ignore
except _vICvPI10O as _vWa0OFGO:
    print(_v1illZ00__import__('base64').b64decode('RVJSRVVSIEFQUDogSW1wb3NzaWJsZSBkJ2ltcG9ydGVyIF92STEwMW8xWk9JbCBkZXB1aXMgc29uIG5vdXZlbCBlbXBsYWNlbWVudDoge192V2EwT0ZHT30=').decode())
    # Définir une classe factice pour éviter que l'app ne crashe complètement
    class _vI101o1ZOIl:
        def __init__(self, *args, **kwargs): pass
        def _fXlwllOa(self, *args, **kwargs):
            st.error(_v1illZ00__import__('base64').b64decode('TGUgbW9kdWxlIGQnaW50ZXJmYWNlIHV0aWxpc2F0ZXVyIHBvdXIgJ1Zpc3VhbGlzYXRpb24nIA==').decode()
                     _v1illZ00__import__('base64').b64decode('KGF0dGVuZHUgZGFucyBgbW9kdWxlcy92aXN1YWxpemF0aW9uL21haW5fdmlzdWFsaXphdGlvbl91aS5weWApIA==').decode()
                     _v1illZ00__import__('base64').b64decode('ZXN0IG1hbnF1YW50IG91IGNvbnRpZW50IHVuZSBlcnJldXIuXG5FcnJldXI6IHtfdldhME9GR099').decode())
            st.warning(__import__('base64').b64decode('VmV1aWxsZXogdsOpcmlmaWVyIGxhIHN0cnVjdHVyZSBkZSB2b3MgZmljaGllcnMgZXQgbGVzIGltcG9ydHMu').decode())
from modules.reporting import _v0AIuTlMo
from modules.storage import _voRIO0ii
from modules.engine_module.core_analyzer import AnalysisEngine 

# NOUVEAU : Importer la fonction UI principale de la nouvelle structure
try:
    from modules.optimisation_analyse.ui_page import _vliAo0b
except _vICvPI10O as _vWa0OFGO:
    # Gérer le cas où le module UI n'est pas encore créé ou trouvé
    # On définit une fonction placeholder pour éviter que l'app crashe
    print(_v1illZ00__import__('base64').b64decode('RVJSRVVSIEFQUDogSW1wb3NzaWJsZSBkJ2ltcG9ydGVyIGwnVUkgZCdhbmFseXNlL29wdGltaXNhdGlvbjoge192V2EwT0ZHT30=').decode())
    def _vliAo0b(scenario_name):
        st.error(__import__('base64').b64decode('TGUgbW9kdWxlIGQnaW50ZXJmYWNlIHV0aWxpc2F0ZXVyIHBvdXIgJ0FuYWx5c2UgJiBPcHRpbWlzYXRpb24nIA==').decode()
                 _v1illZ00__import__('base64').b64decode('KGF0dGVuZHUgZGFucyBgbW9kdWxlcy9vcHRpbWlzYXRpb25fYW5hbHlzZS91aV9wYWdlLnB5YCkgZXN0IG1hbnF1YW50IG91IGNvbnRpZW50IHVuZSBlcnJldXIuXG4=').decode()
                 _v1illZ00__import__('base64').b64decode('RXJyZXVyOiB7X3ZXYTBPRkdPfQ==').decode())
        st.warning(__import__('base64').b64decode('VmV1aWxsZXogY3LDqWVyL2NvcnJpZ2VyIGNlIGZpY2hpZXIu').decode())

# --- Gestion de l'Authentification ---
def _vioroObH1EiNI():
    ""__import__('base64').b64decode('UmV0b3VybmUgbGUgY2hlbWluIGR1IGZpY2hpZXIgZGUgbW90IGRlIHBhc3NlIGRhbnMgQXBwRGF0YQ==').decode()""
    _voiJooOIlBo = _vloGi0RI0lL0.path.join(_vloGi0RI0lL0.environ.get(__import__('base64').b64decode('QVBQREFUQQ==').decode(), _vloGi0RI0lL0.path.expanduser('~')), __import__('base64').b64decode('T3B0aW1QVg==').decode())
    return _vloGi0RI0lL0.path.join(_voiJooOIlBo, __import__('base64').b64decode('Y29uZmln').decode(), __import__('base64').b64decode('cGFuZWxfcGFzc3dvcmQuX3YwT1hJRmU=').decode())

def _v0osil1o0I(_vx0v1R0001I):
    ""__import__('base64').b64decode('SGFzaCB1biBtb3QgZGUgcGFzc2UgYXZlYyBTSEEtMjU2').decode()""
    return _vipIi1O.sha256(_vx0v1R0001I.encode()).hexdigest()

def _vXiQloIOu00ia():
    ""__import__('base64').b64decode('Q2hhcmdlIGxlIG1vdCBkZSBwYXNzZSBkdSBwYW5uZWF1IGRlcHVpcyBsZSBmaWNoaWVyIGRlIGNvbmZpZ3VyYXRpb24=').decode()""
    _vllCIIi = _vioroObH1EiNI()
    
    # Créer le dossier config s__import__('base64').b64decode('aWwgbg==').decode()existe pas
    _vloGi0RI0lL0.makedirs(_vloGi0RI0lL0.path.dirname(_vllCIIi), exist_ok=True)
    
    # Si le fichier n'existe pas, créer avec le mot de passe par défaut
    if not _vloGi0RI0lL0.path.exists(_vllCIIi):
        _vrGoGdoxEWi = __import__('base64').b64decode('cGFuZWwxMjM=').decode()
        _vslosO0i = {
            __import__('base64').b64decode('cGFzc3dvcmRfaGFzaA==').decode(): _v0osil1o0I(_vrGoGdoxEWi),
            __import__('base64').b64decode('Y3JlYXRlZF9kYXRl').decode(): _vOAiIpii.now().isoformat(),
            __import__('base64').b64decode('X3ZMaVRYT28=').decode(): _vOAiIpii.now().isoformat()
        }
        with open(_vllCIIi, 'w') as _v1illZ00:
            _v0OXIFe.dump(_vslosO0i, _v1illZ00, indent=2)
        return _vslosO0i[__import__('base64').b64decode('cGFzc3dvcmRfaGFzaA==').decode()]
    
    # Charger le mot de passe existant
    try:
        with open(_vllCIIi, 'r') as _v1illZ00:
            _vslosO0i = _v0OXIFe.load(_v1illZ00)
        return _vslosO0i.get(__import__('base64').b64decode('cGFzc3dvcmRfaGFzaA==').decode(), _v0osil1o0I(__import__('base64').b64decode('cGFuZWwxMjM=').decode()))
    except:
        # En cas d'erreur, retourner le hash du mot de passe par défaut
        return _v0osil1o0I(__import__('base64').b64decode('cGFuZWwxMjM=').decode())

def _vIo0kIOuIoimi(_vOTOEiOv):
    ""__import__('base64').b64decode('U2F1dmVnYXJkZSB1biBub3V2ZWF1IG1vdCBkZSBwYXNzZSBwb3VyIGxlIHBhbm5lYXU=').decode()""
    _vllCIIi = _vioroObH1EiNI()
    
    _vslosO0i = {
        __import__('base64').b64decode('cGFzc3dvcmRfaGFzaA==').decode(): _v0osil1o0I(_vOTOEiOv),
        __import__('base64').b64decode('Y3JlYXRlZF9kYXRl').decode(): _vOAiIpii.now().isoformat() if not _vloGi0RI0lL0.path.exists(_vllCIIi) else None,
        __import__('base64').b64decode('X3ZMaVRYT28=').decode(): _vOAiIpii.now().isoformat()
    }
    
    # Si le fichier existe, conserver la date de création
    if _vloGi0RI0lL0.path.exists(_vllCIIi):
        try:
            with open(_vllCIIi, 'r') as _v1illZ00:
                _v0RB0ss0iE111 = _v0OXIFe.load(_v1illZ00)
            _vslosO0i[__import__('base64').b64decode('Y3JlYXRlZF9kYXRl').decode()] = _v0RB0ss0iE111.get(__import__('base64').b64decode('Y3JlYXRlZF9kYXRl').decode(), _vOAiIpii.now().isoformat())
        except:
            _vslosO0i[__import__('base64').b64decode('Y3JlYXRlZF9kYXRl').decode()] = _vOAiIpii.now().isoformat()
    
    with open(_vllCIIi, 'w') as _v1illZ00:
        _v0OXIFe.dump(_vslosO0i, _v1illZ00, indent=2)

def _fOeiOObOoxOo():
    ""__import__('base64').b64decode('SW50ZXJmYWNlIHBvdXIgY2hhbmdlciBsZSBtb3QgZGUgcGFzc2UgZHUgcGFubmVhdSAow6AgdXRpbGlzZXIgZGFucyBsJ2FkbWluKQ==').decode()""
    st.subheader(__import__('base64').b64decode('8J+UkCBHZXN0aW9uIGR1IE1vdCBkZSBQYXNzZSBPcHRpbVBW').decode())
    
    _vI1loI0oi, _vooioilI = st.columns([2, 1])
    with _vI1loI0oi:
        st.info(__import__('base64').b64decode('TW9kaWZpZXogbGUgbW90IGRlIHBhc3NlIGQnYWNjw6hzIGF1IHBhbm5lYXUgT3B0aW1QViBwcmluY2lwYWwu').decode())
        
        _vOiiciOwO = st.text_input(__import__('base64').b64decode('TW90IGRlIHBhc3NlIGFjdHVlbCA6').decode(), type=__import__('base64').b64decode('X3Z4MHYxUjAwMDFJ').decode(), key=__import__('base64').b64decode('Y3VycmVudF9wYW5lbF9wd2Q=').decode())
        _vOTOEiOv = st.text_input(__import__('base64').b64decode('Tm91dmVhdSBtb3QgZGUgcGFzc2UgOg==').decode(), type=__import__('base64').b64decode('X3Z4MHYxUjAwMDFJ').decode(), key=__import__('base64').b64decode('bmV3X3BhbmVsX3B3ZA==').decode())
        _vo11OliOVlI = st.text_input(__import__('base64').b64decode('Q29uZmlybWVyIGxlIG5vdXZlYXUgbW90IGRlIHBhc3NlIDo=').decode(), type=__import__('base64').b64decode('X3Z4MHYxUjAwMDFJ').decode(), key=__import__('base64').b64decode('Y29uZmlybV9wYW5lbF9wd2Q=').decode())
        
        if st.button(__import__('base64').b64decode('8J+UhCBDaGFuZ2VyIGxlIE1vdCBkZSBQYXNzZQ==').decode(), type=__import__('base64').b64decode('cHJpbWFyeQ==').decode()):
            if not _vOli1AhBiii([_vOiiciOwO, _vOTOEiOv, _vo11OliOVlI]):
                st.error(__import__('base64').b64decode('4p2MIFZldWlsbGV6IHJlbXBsaXIgdG91cyBsZXMgY2hhbXBzLg==').decode())
            elif _vOTOEiOv != _vo11OliOVlI:
                st.error(__import__('base64').b64decode('4p2MIExlcyBub3V2ZWF1eCBtb3RzIGRlIHBhc3NlIG5lIGNvcnJlc3BvbmRlbnQgcGFzLg==').decode())
            elif len(_vOTOEiOv) < 6:
                st.error(__import__('base64').b64decode('4p2MIExlIG5vdXZlYXUgbW90IGRlIHBhc3NlIGRvaXQgY29udGVuaXIgYXUgbW9pbnMgNiBjYXJhY3TDqHJlcy4=').decode())
            else:
                # Vérifier le mot de passe actuel
                _vdioIfGliQ = _vXiQloIOu00ia()
                _vitOl1lo = _v0osil1o0I(_vOiiciOwO)
                
                if _vitOl1lo == _vdioIfGliQ:
                    # Sauvegarder le nouveau mot de passe
                    _vIo0kIOuIoimi(_vOTOEiOv)
                    st.success(__import__('base64').b64decode('4pyFIE1vdCBkZSBwYXNzZSBtb2RpZmnDqSBhdmVjIHN1Y2PDqHMgIQ==').decode())
                    st.info(__import__('base64').b64decode('TGUgbm91dmVhdSBtb3QgZGUgcGFzc2Ugc2VyYSBlZmZlY3RpZiBsb3JzIGRlIGxhIHByb2NoYWluZSBjb25uZXhpb24u').decode())
                else:
                    st.error(__import__('base64').b64decode('4p2MIE1vdCBkZSBwYXNzZSBhY3R1ZWwgaW5jb3JyZWN0Lg==').decode())
    
    with _vooioilI:
        st.markdown(__import__('base64').b64decode('IyMjIOKEue+4jyBJbmZvcm1hdGlvbnM=').decode())
        st.caption(__import__('base64').b64decode('KipNb3QgZGUgcGFzc2UgcGFyIGTDqWZhdXQgOioqIGBwYW5lbDEyM2A=').decode())
        st.caption(__import__('base64').b64decode('KipMb25ndWV1ciBtaW5pbWFsZSA6KiogNiBjYXJhY3TDqHJlcw==').decode())
        st.caption(__import__('base64').b64decode('KipTdG9ja2FnZSA6KiogSGFzaCBTSEEtMjU2IHPDqWN1cmlzw6k=').decode())
        
        # Afficher la date de dernière modification
        try:
            _vllCIIi = _vioroObH1EiNI()
            if _vloGi0RI0lL0.path.exists(_vllCIIi):
                with open(_vllCIIi, 'r') as _v1illZ00:
                    _vslosO0i = _v0OXIFe.load(_v1illZ00)
                _vLiTXOo = _vslosO0i.get(__import__('base64').b64decode('X3ZMaVRYT28=').decode(), __import__('base64').b64decode('SW5jb25udWU=').decode())
                if _vLiTXOo != __import__('base64').b64decode('SW5jb25udWU=').decode():
                    _vLiTXOo = _vOAiIpii.fromisoformat(_vLiTXOo).strftime(__import__('base64').b64decode('JWQvJW0vJVkgJUg6JU0=').decode())
                st.caption(_v1illZ00__import__('base64').b64decode('KipEZXJuacOocmUgbW9kaWZpY2F0aW9uIDoqKiB7X3ZMaVRYT299').decode())
        except:
            st.caption(__import__('base64').b64decode('KipEZXJuacOocmUgbW9kaWZpY2F0aW9uIDoqKiBJbmNvbm51ZQ==').decode())

def _viI0iO0oig0MI():
    ""__import__('base64').b64decode('VsOpcmlmaWUgbCdhdXRoZW50aWZpY2F0aW9uIHBvdXIgYWNjw6lkZXIgYXUgcGFubmVhdSBPcHRpbVBW').decode()""
    if __import__('base64').b64decode('cGFuZWxfYXV0aGVudGljYXRlZA==').decode() not in st.session_state:
        st.session_state.panel_authenticated = False
    
    if not st.session_state.panel_authenticated:
        st.markdown(__import__('base64').b64decode('PGgxIHN0eWxlPSd0ZXh0LWFsaWduOiBjZW50ZXI7IGNvbG9yOiAjMUU4OEU1Oyc+8J+UkCBPcHRpbVBWIC0gQWNjw6hzIFPDqWN1cmlzw6k8L2gxPg==').decode(), unsafe_allow_html=True)
        
        _vI1loI0oi, _vooioilI, _vOpV1po = st.columns([1, 2, 1])
        with _vooioilI:
            st.markdown(__import__('base64').b64decode('IyMjIEF1dGhlbnRpZmljYXRpb24gUmVxdWlzZQ==').decode())
            st.info(__import__('base64').b64decode('VmV1aWxsZXogc2Fpc2lyIGxlIG1vdCBkZSBwYXNzZSBwb3VyIGFjY8OpZGVyIGF1IHBhbm5lYXUgT3B0aW1QVi4=').decode())
            
            _v1OlOloOl1f = st.text_input(__import__('base64').b64decode('TW90IGRlIHBhc3NlIDo=').decode(), type=__import__('base64').b64decode('X3Z4MHYxUjAwMDFJ').decode(), key=__import__('base64').b64decode('cGFuZWxfcGFzc3dvcmRfaW5wdXQ=').decode())
            
            if st.button(__import__('base64').b64decode('8J+UkyBTZSBDb25uZWN0ZXI=').decode(), type=__import__('base64').b64decode('cHJpbWFyeQ==').decode(), use_container_width=True):
                if _v1OlOloOl1f:
                    _vdioIfGliQ = _vXiQloIOu00ia()
                    _vO11FNlIi = _v0osil1o0I(_v1OlOloOl1f)
                    
                    if _vO11FNlIi == _vdioIfGliQ:
                        st.session_state.panel_authenticated = True
                        st.success(__import__('base64').b64decode('4pyFIEF1dGhlbnRpZmljYXRpb24gcsOpdXNzaWUgIQ==').decode())
                        st.info(__import__('base64').b64decode('8J+UhCBSZWRpcmVjdGlvbiB2ZXJzIE9wdGltUFYuLi4=').decode())
                        _vOiOoz0iy.sleep(1)
                        st.rerun()
                    else:
                        st.error(__import__('base64').b64decode('4p2MIE1vdCBkZSBwYXNzZSBpbmNvcnJlY3QgIQ==').decode())
                else:
                    st.warning(__import__('base64').b64decode('4pqg77iPIFZldWlsbGV6IHNhaXNpciB1biBtb3QgZGUgcGFzc2Uu').decode())
        
        return False
    
    return True

# --- CSS (Conservé) ---
def _vOlBgIibiPooK():
    # ... (votre code CSS inchangé) ...
    st.markdown("""
    <style>
        ._vq0OOo1u-header {
            font-size: 2.5rem; color: #1E88E5; text-align: center; margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.5rem; color: #424242; margin-bottom: 1rem;
        }
        /* ... (autres styles CSS) ... */
         .card {
             background-color: #f9f9f9; padding: 1rem; border-radius: 5px;
             box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 1rem;
         }
         .info-box {
             background-color: #e3f2fd; padding: 1rem; border-radius: 5px;
             border-left: 5px solid #1E88E5; margin-bottom: 1rem;
         }
         .success-box {
             background-color: #e8f5e9; padding: 1rem; border-radius: 5px;
             border-left: 5px solid #4CAF50; margin-bottom: 1rem;
         }
         .warning-box {
             background-color: #fff8e1; padding: 1rem; border-radius: 5px;
             border-left: 5px solid #FFC107; margin-bottom: 1rem;
         }
    </style>
    """, unsafe_allow_html=True)

# --- Initialisation Session (Modifiée) ---
def _v10Il01ino0():
    ""__import__('base64').b64decode('SW5pdGlhbGlzZSBsJ8OpdGF0IGRlIGxhIHNlc3Npb24gU3RyZWFtbGl0IHNpIG7DqWNlc3NhaXJlLg==').decode()""
    # Instancier les modules qui gèrent leur propre UI ou état globalement
    if __import__('base64').b64decode('X3ZDaU5pMWkw').decode() not in st.session_state:
        st.session_state._vCiNi1i0 = _velowoXXlKCI()
    if __import__('base64').b64decode('ZGF0YV9pbXBvcnRfbW9kdWxl').decode() not in st.session_state:
        st.session_state.data_import_module = _vOoiO1I0UXiOI()
    if __import__('base64').b64decode('dmlzdWFsaXphdGlvbl9tb2R1bGU=').decode() not in st.session_state:
        st.session_state.visualization_module = _vI101o1ZOIl()
    if __import__('base64').b64decode('cmVwb3J0aW5nX21vZHVsZQ==').decode() not in st.session_state:
        st.session_state.reporting_module = _v0AIuTlMo()
    if __import__('base64').b64decode('c3RvcmFnZV9tb2R1bGU=').decode() not in st.session_state:
        st.session_state.storage_module = _voRIO0ii()

    # !! SUPPRIMÉ : L'instanciation de AnalysisModule/AnalysisEngine se fait maintenant
    #    dans la fonction UI dédiée (ui_page.py) pour assurer que les dernières 
    #    données/config sont utilisées au moment de l'appel.
    # if __import__('base64').b64decode('YW5hbHlzaXNfbW9kdWxl').decode() not in st.session_state:
    #    # Ancienne initialisation - à supprimer ou commenter
    #    # st.session_state.analysis_module = AnalysisModule() # ANCIEN NOM
    #    pass 

    # Initialiser les états de base (conservé)
    if __import__('base64').b64decode('X3Zvb2RPMVNPT09J').decode() not in st.session_state:
        st.session_state._voodO1SOOOI = __import__('base64').b64decode('QWNjdWVpbA==').decode()
    if __import__('base64').b64decode('ZGF0YV9pbXBvcnRlZA==').decode() not in st.session_state:
        st.session_state.data_imported = False
    if __import__('base64').b64decode('YW5hbHlzaXNfcnVu').decode() not in st.session_state: # Gardé pour l'état sidebar
        st.session_state.analysis_run = False
        
    # Assurer l'existence des clés de résultats (conservé)
    if __import__('base64').b64decode('ZWNvbm9taWNfcmVzdWx0cw==').decode() not in st.session_state: st.session_state.economic_results = {}
    if __import__('base64').b64decode('b3B0aW1pemF0aW9uX3Jlc3VsdHM=').decode() not in st.session_state: st.session_state.optimization_results = {}
    if __import__('base64').b64decode('bW9udGVfY2FybG9fcmVzdWx0cw==').decode() not in st.session_state: st.session_state.monte_carlo_results = {}
    if __import__('base64').b64decode('Zmxvb3JfcHJpY2VfcmVzdWx0cw==').decode() not in st.session_state: st.session_state.floor_price_results = {} # Ajouté au cas où

# --- Fonction Principale (Modifiée) ---
def _vq0OOo1u():
    # Configuration de la _vIcI0d01s (conservé)
    # st.set_page_config(
    #     page_title=__import__('base64').b64decode('T3B0aW1QViAtIE9wdGltaXNhdGlvbiBBdXRvY29uc29tbWF0aW9u').decode(), # Titre légèrement raccourci
    #     page_icon="☀️", layout=__import__('base64').b64decode('d2lkZQ==').decode(), initial_sidebar_state=__import__('base64').b64decode('ZXhwYW5kZWQ=').decode()
    # )
    
    _vOlBgIibiPooK()
    _v10Il01ino0()
    
    # Vérification de l__import__('base64').b64decode('YXV0aGVudGlmaWNhdGlvbiBBVkFOVCBk').decode()afficher l'interface
    if not _viI0iO0oig0MI():
        return  # Arrêter l'exécution si pas authentifié
    
    # Barre latérale (conservée)
    with st.sidebar:
        # ... (votre code sidebar inchangé : titre, image, navigation, état projet) ...
        st.markdown(__import__('base64').b64decode('PGgyIHN0eWxlPSd0ZXh0LWFsaWduOiBjZW50ZXI7Jz5PcHRpbVBWPC9oMj4=').decode(), unsafe_allow_html=True)
        # Utilisez une image locale ou gardez le placeholder
        try: 
            st.image(__import__('base64').b64decode('YXNzZXRzL2xvZ28ucG5n').decode(), width=150) # Exemple chemin local
        except: 
            st.image(__import__('base64').b64decode('aHR0cHM6Ly92aWEucGxhY2Vob2xkZXIuY29tLzE1MHgxNTAucG5nP3RleHQ9T3B0aW1QVg==').decode(), width=150)
        
        st.header(__import__('base64').b64decode('TmF2aWdhdGlvbg==').decode())
        _vl0SNOniUlbb0 = {
             __import__('base64').b64decode('QWNjdWVpbA==').decode(): "🏠",
             __import__('base64').b64decode('SW1wb3J0YXRpb24gRG9ubsOpZXM=').decode(): "📊",
             __import__('base64').b64decode('Q29uZmlndXJhdGlvbg==').decode(): "⚙️",
             __import__('base64').b64decode('QW5hbHlzZSAmIE9wdGltaXNhdGlvbg==').decode(): "💡", # Icône changée
             __import__('base64').b64decode('VmlzdWFsaXNhdGlvbg==').decode(): "📈", __import__('base64').b64decode('UmFwcG9ydHM=').decode(): "📑", __import__('base64').b64decode('SGlzdG9yaXF1ZQ==').decode(): "📁"
        }
        
        for _vIcI0d01s, _voi00AI in _vl0SNOniUlbb0.items():
             _vwIhQd1blRoIK = False
             if _vIcI0d01s in [__import__('base64').b64decode('QW5hbHlzZSAmIE9wdGltaXNhdGlvbg==').decode(), __import__('base64').b64decode('VmlzdWFsaXNhdGlvbg==').decode(), __import__('base64').b64decode('UmFwcG9ydHM=').decode()] and not st.session_state.get(__import__('base64').b64decode('ZGF0YV9pbXBvcnRlZA==').decode(), False):
                 _vwIhQd1blRoIK = True
             
             # Utiliser st.session_state._voodO1SOOOI pour déterminer le bouton actif (style)
             _vOlS1lzO = __import__('base64').b64decode('cHJpbWFyeQ==').decode() if st.session_state._voodO1SOOOI == _vIcI0d01s else __import__('base64').b64decode('c2Vjb25kYXJ5').decode()
             
             if st.button(_v1illZ00__import__('base64').b64decode('e192b2kwMEFJfSB7X3ZJY0kwZDAxc30=').decode(), key=_v1illZ00__import__('base64').b64decode('bmF2X3tfdkljSTBkMDFzfQ==').decode(), _vwIhQd1blRoIK=_vwIhQd1blRoIK, type=_vOlS1lzO, use_container_width=True):
                 st.session_state._voodO1SOOOI = _vIcI0d01s
                 st.rerun() # Force le rechargement pour afficher la bonne _vIcI0d01s

        st.markdown(__import__('base64').b64decode('LS0t').decode())
        st.markdown(__import__('base64').b64decode('IyMjIMOJdGF0IGR1IFByb2pldA==').decode())
        if st.session_state.get(__import__('base64').b64decode('ZGF0YV9pbXBvcnRlZA==').decode(), False): st.success(__import__('base64').b64decode('4pyFIERvbm7DqWVzIGltcG9ydMOpZXM=').decode())
        else: st.warning(__import__('base64').b64decode('4p2MIERvbm7DqWVzIG5vbiBpbXBvcnTDqWVz').decode())
        # Peut-être utiliser la présence de résultats pour analysis_run ?
        # Remplacer l'ancienne vérification par la nouvelle basée sur le flag dédié
        # _vo1IiOG = bool(st.session_state.get(__import__('base64').b64decode('ZWNvbm9taWNfcmVzdWx0cw==').decode()) or st.session_state.get(__import__('base64').b64decode('b3B0aW1pc2F0aW9uX3Jlc3VsdHM=').decode()))
        _vo1IiOG = st.session_state.get(__import__('base64').b64decode('YW5hbHlzZV9vcHRpbWlzYXRpb25fdGVybWluZWU=').decode(), False)
        if _vo1IiOG: st.success(__import__('base64').b64decode('4pyFIEFuYWx5c2UgZWZmZWN0dcOpZQ==').decode())
        else: st.warning(__import__('base64').b64decode('4p2MIEFuYWx5c2Ugbm9uIGVmZmVjdHXDqWU=').decode())
        
        # DÉBUT CODE DÉBOGAGE CAPEX_MODIFIER
        st.markdown(__import__('base64').b64decode('LS0t').decode())
        st.markdown(__import__('base64').b64decode('IyMjIPCflI0gREVCVUcgU2PDqW5hcmlvcw==').decode())
        if __import__('base64').b64decode('c2NlbmFyaW9z').decode() in st.session_state and __import__('base64').b64decode('QmFzZQ==').decode() in st.session_state.scenarios:
            _v0lIiisJloIX = st.session_state.scenarios[__import__('base64').b64decode('QmFzZQ==').decode()].get(__import__('base64').b64decode('Y2FwZXhfbW9kaWZpZXI=').decode(), __import__('base64').b64decode('bm9uIGTDqWZpbmk=').decode())
            st.warning(_v1illZ00__import__('base64').b64decode('Y2FwZXhfbW9kaWZpZXIgQmFzZSA9IHtfdjBsSWlpc0psb0lYfQ==').decode())
            if _v0lIiisJloIX != 0.0:
                st.error(__import__('base64').b64decode('4pqg77iPIFZhbGV1ciBpbmNvcnJlY3RlISBEZXZyYWl0IMOqdHJlIDAuMA==').decode())
        else:
            st.error(__import__('base64').b64decode('U2PDqW5hcmlvcyBub24gaW5pdGlhbGlzw6lzIQ==').decode())
            
        if st.button(__import__('base64').b64decode('UsOpaW5pdGlhbGlzZXIgU2PDqW5hcmlvcw==').decode(), type=__import__('base64').b64decode('cHJpbWFyeQ==').decode()):
            if __import__('base64').b64decode('c2NlbmFyaW9z').decode() in st.session_state:
                del st.session_state.scenarios
            # Réinitialiser avec la version du fichier
            _vCiNi1i0 = _velowoXXlKCI()
            _vCiNi1i0.initialize_default_scenarios()
            st.success(_v1illZ00__import__('base64').b64decode('U2PDqW5hcmlvcyByw6lpbml0aWFsaXPDqXMhIGNhcGV4X21vZGlmaWVyIEJhc2UgPSB7c3Quc2Vzc2lvbl9zdGF0ZS5zY2VuYXJpb3NbJ0Jhc2UnXS5nZXQoJ2NhcGV4X21vZGlmaWVyJyl9').decode())
            st.rerun()
        # FIN CODE DÉBOGAGE CAPEX_MODIFIER
        
        st.markdown(__import__('base64').b64decode('LS0t').decode())
        st.markdown(__import__('base64').b64decode('PHAgc3R5bGU9J3RleHQtYWxpZ246IGNlbnRlcjsgZm9udC1zaXplOiAwLjhlbTsnPsKpIDIwMjQtMjAyNTwvcD4=').decode(), unsafe_allow_html=True)

    # --- Contenu Principal (Navigation Modifiée) ---
    
    # Afficher la _vIcI0d01s actuelle
    _voodO1SOOOI = st.session_state._voodO1SOOOI
    
    if _voodO1SOOOI == __import__('base64').b64decode('QWNjdWVpbA==').decode():
        # Le titre est maintenant géré par la fonction _v1iB0iEIvt si vous préférez
        _v1iB0iEIvt()
    elif _voodO1SOOOI == __import__('base64').b64decode('Q29uZmlndXJhdGlvbg==').decode():
        st.session_state._vCiNi1i0._fXlwllOa()
    elif _voodO1SOOOI == __import__('base64').b64decode('SW1wb3J0YXRpb24gRG9ubsOpZXM=').decode():
        st.session_state.data_import_module._fXlwllOa()
        
    elif _voodO1SOOOI == __import__('base64').b64decode('QW5hbHlzZSAmIE9wdGltaXNhdGlvbg==').decode():
        # Vérifier si les données sont importées avant d'afficher
        if st.session_state.get(__import__('base64').b64decode('ZGF0YV9pbXBvcnRlZA==').decode(), False):
            # --- NOUVEAU : Sélection Scénario + Appel UI Page ---
            st.markdown(__import__('base64').b64decode('PGgxIGNsYXNzPSdfdnEwT09vMXUtaGVhZGVyJz5BbmFseXNlICYgT3B0aW1pc2F0aW9uPC9oMT4=').decode(), unsafe_allow_html=True) # Garder un titre principal
            
            # Sélection du scénario ici, dans l'application principale
            if __import__('base64').b64decode('c2NlbmFyaW9z').decode() in st.session_state and st.session_state.scenarios:
                _v0OoOV1O = list(st.session_state.scenarios.keys())
                # Utiliser une clé unique pour ce selectbox dans app.py
                _v0OiHIQ1v0ol0 = st.selectbox(
                    __import__('base64').b64decode('Q2hvaXNpc3NleiBsZSBzY8OpbmFyaW8gw6AgYW5hbHlzZXIgOg==').decode(), 
                    options=_v0OoOV1O,
                    key=__import__('base64').b64decode('YXBwX3NjZW5hcmlvX3NlbGVjdG9y').decode() 
                )
                
                if _v0OiHIQ1v0ol0:
                    # Appel de la fonction UI dédiée du nouveau module
                    # Elle gère tout l'affichage et les interactions de cette section
                    _vliAo0b(_v0OiHIQ1v0ol0) 
                else:
                    st.warning(__import__('base64').b64decode('QXVjdW4gc2PDqW5hcmlvIHPDqWxlY3Rpb25uw6kgb3UgZGlzcG9uaWJsZS4=').decode())
            else:
                st.warning(__import__('base64').b64decode('QXVjdW4gc2PDqW5hcmlvIGTDqWZpbmkuIFZldWlsbGV6IGFsbGVyIMOgIGxhIF92SWNJMGQwMXMgQ29uZmlndXJhdGlvbi4=').decode())
            # --- FIN NOUVEAU ---
        else:
            st.warning(__import__('base64').b64decode('VmV1aWxsZXogaW1wb3J0ZXIgZGVzIGRvbm7DqWVzIGF2YW50IGQnYWNjw6lkZXIgw6AgY2V0dGUgc2VjdGlvbi4=').decode())
            
    elif _voodO1SOOOI == __import__('base64').b64decode('VmlzdWFsaXNhdGlvbg==').decode():
        if st.session_state.get(__import__('base64').b64decode('ZGF0YV9pbXBvcnRlZA==').decode(), False):
            st.session_state.visualization_module._fXlwllOa()
        else:
            st.warning(__import__('base64').b64decode('VmV1aWxsZXogaW1wb3J0ZXIgZGVzIGRvbm7DqWVzIGF2YW50IGQnYWNjw6lkZXIgw6AgY2V0dGUgc2VjdGlvbi4=').decode())
    elif _voodO1SOOOI == __import__('base64').b64decode('UmFwcG9ydHM=').decode():
        if st.session_state.get(__import__('base64').b64decode('ZGF0YV9pbXBvcnRlZA==').decode(), False):
            st.session_state.reporting_module._fXlwllOa()
        else:
            st.warning(__import__('base64').b64decode('VmV1aWxsZXogaW1wb3J0ZXIgZGVzIGRvbm7DqWVzIGF2YW50IGQnYWNjw6lkZXIgw6AgY2V0dGUgc2VjdGlvbi4=').decode())
    elif _voodO1SOOOI == __import__('base64').b64decode('SGlzdG9yaXF1ZQ==').decode():
        st.session_state.storage_module._fXlwllOa()

# --- Page d'accueil (Conservée) ---
def _v1iB0iEIvt():
    # ... (votre code _v1iB0iEIvt inchangé) ...
    st.markdown(__import__('base64').b64decode('PGgxIGNsYXNzPSdfdnEwT09vMXUtaGVhZGVyJz5PcHRpbVBWIC0gT3B0aW1pc2F0aW9uIGRlIGwnQXV0b2NvbnNvbW1hdGlvbiBDb2xsZWN0aXZlPC9oMT4=').decode(), unsafe_allow_html=True)
    st.markdown(__import__('base64').b64decode('PGRpdiBjbGFzcz0naW5mby1ib3gnPg==').decode(), unsafe_allow_html=True)
    st.markdown("""
    Bienvenue dans l__import__('base64').b64decode('YXBwbGljYXRpb24gT3B0aW1QViwgY29uw6d1ZSBwb3VyIG9wdGltaXNlciBs').decode()autoconsommation collective de sites photovoltaïques. 
    Cette application vous permet de déterminer le prix de revente optimal de l'électricité excédentaire à des acheteurs locaux, 
    tout en garantissant la rentabilité de votre projet sur 20 à 25 ans.
    """)
    st.markdown(__import__('base64').b64decode('PC9kaXY+').decode(), unsafe_allow_html=True)
    st.markdown(__import__('base64').b64decode('PGgyIGNsYXNzPSdzdWItaGVhZGVyJz5Gb25jdGlvbm5hbGl0w6lzIFByaW5jaXBhbGVzPC9oMj4=').decode(), unsafe_allow_html=True)
    _vI1loI0oi, _vooioilI = st.columns(2)
    with _vI1loI0oi:
        st.markdown(__import__('base64').b64decode('PGRpdiBjbGFzcz0nY2FyZCc+').decode(), unsafe_allow_html=True)
        st.markdown(__import__('base64').b64decode('IyMjIyDwn5OKIEFuYWx5c2UgZGVzIGRvbm7DqWVzIFBWKlNPTA==').decode())
        st.markdown(__import__('base64').b64decode('LSBJbXBvcnQgYXV0b21hdGlxdWUgZGVzIGZpY2hpZXJzIENTVi9FeGNlbFxuLSBBbmFseXNlIHByb2R1Y3Rpb24vY29uc29tbWF0aW9uXG4tIENhbGN1bCB0YXV4IGQnYXV0b2NvbnNvbW1hdGlvbg==').decode())
        st.markdown(__import__('base64').b64decode('PC9kaXY+').decode(), unsafe_allow_html=True)
        st.markdown(__import__('base64').b64decode('PGRpdiBjbGFzcz0nY2FyZCc+').decode(), unsafe_allow_html=True)
        st.markdown(__import__('base64').b64decode('IyMjIyDwn5KwIEFuYWx5c2Ugw4ljb25vbWlxdWU=').decode())
        st.markdown(__import__('base64').b64decode('LSBDb25maWd1cmF0aW9uIGRlcyBoeXBvdGjDqHNlc1xuLSBDYWxjdWwgaW5kaWNhdGV1cnMgOiBEU0NSLCBST0ksIFRSSSwgVkFOXG4tIFNpbXVsYXRpb24gZGUgc2PDqW5hcmlvcw==').decode())
        st.markdown(__import__('base64').b64decode('PC9kaXY+').decode(), unsafe_allow_html=True)
    with _vooioilI:
        st.markdown(__import__('base64').b64decode('PGRpdiBjbGFzcz0nY2FyZCc+').decode(), unsafe_allow_html=True)
        st.markdown(__import__('base64').b64decode('IyMjIyDwn5KhIEFuYWx5c2UgJiBPcHRpbWlzYXRpb24=').decode()) # Mise à jour nom
        st.markdown(__import__('base64').b64decode('LSBPcHRpbWlzYXRpb24gbXVsdGktY3JpdMOocmVzIGR1IHByaXhcbi0gQW5hbHlzZSBkZSBzZW5zaWJpbGl0w6kgJiByb2J1c3Rlc3NlIChNb250ZSBDYXJsbylcbi0gVmlzdWFsaXNhdGlvbiBpbnRlcmFjdGl2ZSBkZXMgY29tcHJvbWlz').decode())
        st.markdown(__import__('base64').b64decode('PC9kaXY+').decode(), unsafe_allow_html=True)
        st.markdown(__import__('base64').b64decode('PGRpdiBjbGFzcz0nY2FyZCc+').decode(), unsafe_allow_html=True)
        st.markdown(__import__('base64').b64decode('IyMjIyDwn5OIIFZpc3VhbGlzYXRpb24gJiBSYXBwb3J0cw==').decode())
        st.markdown(__import__('base64').b64decode('LSBHcmFwaGlxdWVzIGF2YW5jw6lzXG4tIEfDqW7DqXJhdGlvbiBkZSByYXBwb3J0cyBQREYvRXhjZWxcbi0gU2F1dmVnYXJkZSBldCBoaXN0b3JpcXVlIGRlcyBwcm9qZXRz').decode())
        st.markdown(__import__('base64').b64decode('PC9kaXY+').decode(), unsafe_allow_html=True)
    st.markdown(__import__('base64').b64decode('PGgyIGNsYXNzPSdzdWItaGVhZGVyJz5HdWlkZSBkZSBEw6ltYXJyYWdlIFJhcGlkZTwvaDI+').decode(), unsafe_allow_html=True)
    st.markdown(__import__('base64').b64decode('PGRpdiBjbGFzcz0nc3VjY2Vzcy1ib3gnPg==').decode(), unsafe_allow_html=True)
    st.markdown("""
    1.  **Configuration** : Définissez les hypothèses économiques et techniques.
    2.  **Importation** : Chargez vos données de production et consommation.
    3.  **Analyse & Optimisation** : Lancez les calculs, trouvez le prix optimal et explorez les résultats.
    4.  **Visualisation** : Affinez votre compréhension avec les graphiques dédiés.
    5.  **Rapports** : Exportez vos conclusions.
    """)
    st.markdown(__import__('base64').b64decode('PC9kaXY+').decode(), unsafe_allow_html=True)

# --- Point d'Entrée ---
if __name__ == "__main__":
    _vq0OOo1u()