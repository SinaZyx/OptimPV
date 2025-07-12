#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test du système de tooltips interactifs pour le module prospect_mapping.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from modules.prospect_mapping.interactive_tooltip_handler import InteractiveTooltipHandler
from modules.prospect_mapping.tooltip_styles import inject_custom_css

def test_tooltip_interaction():
    """Test l'interaction avec les tooltips."""
    
    st.set_page_config(page_title="Test Tooltips Interactifs", layout="wide")
    st.title("🧪 Test des Tooltips Interactifs")
    
    # Injecter les styles CSS
    inject_custom_css()
    
    # Créer des données de test
    test_data = pd.DataFrame({
        'latitude': [43.7102, 43.5514, 43.5804],
        'longitude': [7.2620, 7.0128, 7.1251],
        'nom_commune': ['Nice', 'Cannes', 'Antibes'],
        'adresse': ['1 Rue de Test', '2 Avenue Test', '3 Boulevard Test'],
        'nombre_de_logements': [10, 25, 15],
        'consommation_kwh': [50000, 125000, 75000],
        'code_commune': ['06088', '06029', '06004'],
        'object_index': [0, 1, 2]
    })
    
    # Initialiser le gestionnaire
    handler = InteractiveTooltipHandler()
    
    # Deux colonnes pour l'interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Simuler la sélection d'une parcelle")
        
        # Sélecteur de parcelle
        selected_index = st.selectbox(
            "Choisissez une parcelle :",
            options=range(len(test_data)),
            format_func=lambda x: f"Parcelle {x} - {test_data.iloc[x]['nom_commune']}"
        )
        
        if st.button("Afficher les détails", type="primary"):
            # Simuler la sélection
            parcel_data = test_data.iloc[selected_index].to_dict()
            st.session_state.selected_parcel = parcel_data
            st.session_state.tooltip_visible = True
            st.rerun()
        
        # Afficher les données brutes
        st.subheader("Données de test")
        st.dataframe(test_data)
    
    with col2:
        st.subheader("Panneau de détails")
        
        # Afficher les détails si une parcelle est sélectionnée
        if st.session_state.get('tooltip_visible') and st.session_state.get('selected_parcel'):
            handler.show_parcel_details(st.session_state.selected_parcel, position="main")
        else:
            st.info("Sélectionnez une parcelle pour voir ses détails")
    
    # Section de test des styles CSS
    st.subheader("Test des styles de tooltip")
    
    # HTML de test pour vérifier l'apparence
    test_tooltip_html = """
    <div class="custom-tooltip-container">
        <h4>🏢 Test de Tooltip</h4>
        <p><b>Commune :</b> Nice</p>
        <p><b>Adresse :</b> 1 Rue de Test</p>
        <p><b>Consommation :</b> 50,000 kWh</p>
        <div style="margin-top: 10px;">
            <a href="#" class="tooltip-action-button" onclick="alert('Clic sur Vue 3D'); return false;">🌍 Vue 3D</a>
            <a href="#" class="tooltip-action-button" onclick="alert('Clic sur Maps'); return false;">🗺️ Maps</a>
        </div>
    </div>
    """
    
    st.markdown(test_tooltip_html, unsafe_allow_html=True)
    
    # Instructions
    st.info("""
    ### Instructions de test :
    
    1. **Test du panneau de détails :**
       - Sélectionnez une parcelle dans la liste déroulante
       - Cliquez sur "Afficher les détails"
       - Vérifiez que les informations s'affichent correctement
       - Testez les boutons "Vue 3D" et "Maps"
       - Cliquez sur le bouton de fermeture (✖)
    
    2. **Test des styles CSS :**
       - Vérifiez que le tooltip de test ci-dessus a le bon style
       - Les boutons doivent réagir au survol
       - Les clics sur les boutons doivent afficher une alerte
    
    3. **Points à vérifier :**
       - ✅ Les informations s'affichent correctement
       - ✅ Les boutons sont cliquables
       - ✅ Le style est cohérent
       - ✅ L'interaction est fluide
    """)

if __name__ == "__main__":
    test_tooltip_interaction()