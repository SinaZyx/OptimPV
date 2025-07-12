#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de l'interface complète du module de cartographie de prospection.
"""

import streamlit as st
import sys
import os

# Configuration Streamlit
st.set_page_config(
    page_title="Test Cartographie Prospection",
    page_icon="🗺️",
    layout="wide"
)

# Ajouter le chemin du dossier parent pour l'import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # Import de l'interface complète du module de cartographie
    from modules.prospect_mapping.ui import show_prospect_map_ui
    
    # Titre de test
    st.markdown("# 🧪 Test du Module de Cartographie de Prospection")
    st.markdown("---")
    
    # Lancer l'interface complète
    show_prospect_map_ui()
    
except ImportError as e:
    st.error(f"❌ Erreur d'import: {e}")
    st.info("Vérifiez que tous les modules requis sont installés:")
    st.code("""
pip install streamlit pandas numpy pydeck requests
    """)
    
except Exception as e:
    st.error(f"❌ Erreur d'exécution: {e}")
    st.exception(e)