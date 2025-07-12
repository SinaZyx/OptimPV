#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hook PyInstaller pour Streamlit
===============================

Ce hook résout les problèmes de métadonnées et d'imports avec Streamlit dans PyInstaller.
"""

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules, copy_metadata

# Collecter tous les modules Streamlit
datas, binaries, hiddenimports = collect_all('streamlit')

# Ajouter des imports cachés spécifiques
hiddenimports += [
    'streamlit.web.cli',
    'streamlit.runtime',
    'streamlit.runtime.caching',
    'streamlit.runtime.state',
    'streamlit.components.v1',
    'streamlit.delta_generator',
    'streamlit.elements',
    'streamlit.web.server',
    'streamlit.web.bootstrap',
    'streamlit.logger',
    'streamlit.config',
    'streamlit.secrets',
    'streamlit.version',
    'tornado',
    'tornado.web',
    'tornado.websocket',
    'tornado.ioloop',
    'altair',
    'click',
    'toml',
    'validators',
    'watchdog',
    'blinker',
    'cachetools',
    'gitpython',
    'pyarrow',
    'pydeck',
    'pympler',
    'rich',
    'tzlocal',
    'importlib.metadata',
    'pkg_resources',
]

# Collecter les données de configuration Streamlit
try:
    import streamlit
    import os
    
    # Ajouter le dossier static de Streamlit
    streamlit_static = os.path.join(os.path.dirname(streamlit.__file__), 'static')
    if os.path.exists(streamlit_static):
        datas += collect_data_files('streamlit.static')
    
    # Ajouter les templates
    streamlit_templates = os.path.join(os.path.dirname(streamlit.__file__), 'web', 'templates')
    if os.path.exists(streamlit_templates):
        datas += [(streamlit_templates, 'streamlit/web/templates')]
        
except ImportError:
    pass

# === AJOUT IMPORTANT POUR RÉSOUDRE PackageNotFoundError ===
# Collecter explicitement les métadonnées pour Streamlit
# Cela devrait résoudre l'erreur "No package metadata was found for streamlit"
datas += copy_metadata('streamlit')

# Collecter aussi les métadonnées des dépendances principales de Streamlit
# qui pourraient être nécessaires
try:
    datas += copy_metadata('tornado')
except:
    pass
try:
    datas += copy_metadata('altair')
except:
    pass
try:
    datas += copy_metadata('plotly')
except:
    pass
# === FIN DE L'AJOUT IMPORTANT ===

# Collecter les sous-modules
hiddenimports += collect_submodules('streamlit')
hiddenimports += collect_submodules('tornado')
hiddenimports += collect_submodules('altair')
hiddenimports += collect_submodules('plotly')

# Supprimer les doublons
hiddenimports = list(set(hiddenimports)) 