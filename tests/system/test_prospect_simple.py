#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple du module de cartographie - Vérification des imports et APIs.
"""

import streamlit as st
import sys
import os

# Configuration Streamlit
st.set_page_config(
    page_title="Test Simple Cartographie",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Test Simple - Module Cartographie")

# Test des imports
st.header("1. 📦 Test des Imports Python")

try:
    import pandas as pd
    st.success("✅ pandas importé avec succès")
except ImportError:
    st.error("❌ pandas manquant - Installer avec: pip install pandas")

try:
    import numpy as np
    st.success("✅ numpy importé avec succès")
except ImportError:
    st.error("❌ numpy manquant - Installer avec: pip install numpy")

try:
    import pydeck as pdk
    st.success("✅ pydeck importé avec succès")
except ImportError:
    st.error("❌ pydeck manquant - Installer avec: pip install pydeck")

try:
    import requests
    st.success("✅ requests importé avec succès")
except ImportError:
    st.error("❌ requests manquant - Installer avec: pip install requests")

# Test des APIs
st.header("2. 🌐 Test des APIs")

if st.button("Tester API Enedis"):
    try:
        import requests
        response = requests.get(
            'https://data.enedis.fr/api/explore/v2.1/catalog/datasets/consommation-annuelle-residentielle-par-adresse/records',
            params={'limit': 1, 'where': 'code_departement="06"'},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            if results:
                st.success("✅ API Enedis accessible")
                st.json(results[0])
            else:
                st.warning("⚠️ API accessible mais aucun résultat")
        else:
            st.error(f"❌ API Enedis erreur: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Erreur API Enedis: {e}")

if st.button("Tester API Géo"):
    try:
        import requests
        response = requests.get(
            'https://geo.api.gouv.fr/communes',
            params={
                'codeDepartement': '06',
                'fields': 'nom,code,centre',
                'limit': 1
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data:
                st.success("✅ API Géo accessible")
                st.json(data[0])
            else:
                st.warning("⚠️ API accessible mais aucun résultat")
        else:
            st.error(f"❌ API Géo erreur: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Erreur API Géo: {e}")

# Test du module
st.header("3. 🗺️ Test du Module")

# Ajouter le chemin du dossier parent pour l'import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from modules.prospect_mapping.data_handler import CONFIG
    st.success("✅ Module prospect_mapping.data_handler importé")
    st.write("Configuration:", CONFIG)
except ImportError as e:
    st.error(f"❌ Erreur import data_handler: {e}")

try:
    from modules.prospect_mapping.map_visualizer import MAP_CONFIG
    st.success("✅ Module prospect_mapping.map_visualizer importé")
    st.write("Configuration carte:", MAP_CONFIG)
except ImportError as e:
    st.error(f"❌ Erreur import map_visualizer: {e}")

try:
    from modules.prospect_mapping.ui import show_prospect_map_ui
    st.success("✅ Module prospect_mapping.ui importé")
    
    if st.button("🚀 Lancer l'Interface Complète"):
        st.markdown("---")
        st.markdown("## Interface de Cartographie")
        show_prospect_map_ui()
        
except ImportError as e:
    st.error(f"❌ Erreur import ui: {e}")

# Instructions
st.header("4. 📋 Instructions")
st.info("""
**Pour installer les dépendances manquantes:**
```bash
pip install streamlit pandas numpy pydeck requests
```

**Pour lancer ce test:**
```bash
streamlit run tests/test_prospect_simple.py
```

**Pour lancer l'interface complète:**
```bash
streamlit run tests/test_prospect_mapping_fixed.py
```
""")