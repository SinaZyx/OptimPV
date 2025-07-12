import streamlit as st
import sys
import os

# Ajouter le chemin du dossier parent pour l'import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.prospect_mapping import map_visualizer

st.title("Aperçu Visualisation Cartographie Prospect")

# Exemple d'utilisation :
# On suppose qu'il existe une fonction principale à tester, par exemple display_map ou main
if hasattr(map_visualizer, 'main'):
    map_visualizer.main()
elif hasattr(map_visualizer, 'display_map'):
    map_visualizer.display_map()
else:
    st.warning("Aucune fonction principale trouvée dans map_visualizer.py. Veuillez adapter ce script selon l'API réelle.") 