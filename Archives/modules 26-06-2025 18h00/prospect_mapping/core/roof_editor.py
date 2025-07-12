#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'édition de toiture pour OptimPV.
Responsabilité : Interface de dessin interactif des zones d'installation.
"""

import streamlit as st
import pydeck as pdk
import math
from typing import List, Dict, Optional

class RoofEditor:
    """Éditeur interactif de zones de toiture"""
    
    def __init__(self):
        self.default_zoom = 19
        self.default_pitch = 0  # Vue 2D obligatoire pour dessin
        
    def create_drawing_interface(self, building_data: Dict, mapbox_key: Optional[str] = None) -> Dict:
        """
        Crée l'interface complète de dessin de toiture
        
        Args:
            building_data: Données du bâtiment sélectionné
            mapbox_key: Clé API Mapbox optionnelle
            
        Returns:
            Dict avec résultats du dessin
        """
        # Initialiser session state
        if 'roof_polygon' not in st.session_state:
            st.session_state.roof_polygon = []
        if 'drawing_mode' not in st.session_state:
            st.session_state.drawing_mode = 'polygon'
        if 'panel_layout' not in st.session_state:
            st.session_state.panel_layout = None
        
        # Layout principal
        col_map, col_controls = st.columns([3, 1])
        
        with col_map:
            self._render_drawing_map(building_data, mapbox_key)
        
        with col_controls:
            self._render_drawing_controls(building_data)
        
        return {
            'polygon': st.session_state.roof_polygon,
            'mode': st.session_state.drawing_mode,
            'panel_layout': st.session_state.panel_layout
        }
    
    def _render_drawing_map(self, building_data: Dict, mapbox_key: Optional[str]):
        """Affiche la carte interactive de dessin"""
        
        # Récupérer coordonnées du bâtiment
        lat = building_data.get('latitude', 43.7102)
        lon = building_data.get('longitude', 7.2620)
        
        # Vue initiale centrée sur le bâtiment
        view_state = pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=self.default_zoom,
            pitch=self.default_pitch,
            bearing=0
        )
        
        # Créer les layers
        layers = self._create_drawing_layers(building_data)
        
        # Configuration de la carte avec fond satellite OBLIGATOIRE
        deck_config = {
            'layers': layers,
            'initial_view_state': view_state,
            'tooltip': {
                'html': '<b>Zone d\'installation</b><br/>Cliquez pour ajouter des points',
                'style': {'backgroundColor': 'steelblue', 'color': 'white'}
            }
        }
        
        # PRIORITÉ 1: Style satellite Mapbox si clé disponible
        if mapbox_key:
            deck_config['map_style'] = 'mapbox://styles/mapbox/satellite-v9'
            deck_config['api_keys'] = {'mapbox': mapbox_key}
            satellite_source = "Mapbox Satellite"
        else:
            # PRIORITÉ 2: Fallback sur OpenStreetMap avec tuiles satellite
            # Utiliser un style de base qui fonctionne
            deck_config['map_style'] = 'https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png'
            satellite_source = "CartoDB Voyager"
        
        # Afficher la carte
        st.pydeck_chart(
            pdk.Deck(**deck_config),
            use_container_width=True,
            height=500,
            key="roof_drawing_map"
        )
        
        # Instructions avec info source satellite
        st.info(f"""
        👆 **Mode dessin activé** (Source: {satellite_source}) :
        - Cliquez pour placer les points du polygone
        - Minimum 3 points pour former une zone
        - Restez sur la zone de toiture visible
        """)
        
        # Message d'aide pour les clés satellite
        if not mapbox_key:
            with st.expander("🛰️ Améliorer la qualité satellite"):
                st.markdown("""
                **Pour une vue satellite haute définition :**
                
                1. **Obtenez une clé Mapbox gratuite** : 
                   - Allez sur [mapbox.com](https://www.mapbox.com)
                   - Créez un compte gratuit
                   - Copiez votre "Default public token"
                
                2. **Entrez la clé dans la section "Configuration de la Carte"**
                
                ⚡ **Avantage** : Vue satellite ultra-précise pour dessiner exactement sur les toitures !
                """)
                
                # Formulaire rapide pour saisir la clé
                quick_mapbox = st.text_input(
                    "Clé Mapbox (rapide)", 
                    type="password",
                    placeholder="pk.ey...",
                    help="Sera stockée pour cette session"
                )
                
                if quick_mapbox.startswith('pk.'):
                    st.session_state['mapbox_key'] = quick_mapbox
                    st.success("✅ Clé Mapbox ajoutée ! Actualisez la page.")
                    st.button("🔄 Actualiser", key="refresh_map")
    
    def _create_drawing_layers(self, building_data: Dict) -> List[pdk.Layer]:
        """Crée les layers PyDeck pour le dessin"""
        layers = []
        
        # Layer 1: Empreinte du bâtiment (référence)
        building_footprint = building_data.get('footprint_polygon', [])
        if building_footprint:
            layers.append(
                pdk.Layer(
                    'PolygonLayer',
                    data=[{
                        'polygon': building_footprint,
                        'name': 'building_base'
                    }],
                    get_polygon='polygon',
                    filled=True,
                    get_fill_color=[200, 200, 200, 100],  # Gris semi-transparent
                    get_line_color=[100, 100, 100, 255],  # Contour gris
                    line_width_min_pixels=2,
                    pickable=False
                )
            )
        
        # Layer 2: Zone dessinée par l'utilisateur
        if st.session_state.roof_polygon and len(st.session_state.roof_polygon) >= 3:
            # Fermer le polygone pour l'affichage
            display_polygon = st.session_state.roof_polygon.copy()
            if len(display_polygon) > 2 and display_polygon[0] != display_polygon[-1]:
                display_polygon.append(display_polygon[0])
            
            layers.append(
                pdk.Layer(
                    'PolygonLayer',
                    data=[{
                        'polygon': display_polygon,
                        'name': 'roof_zone'
                    }],
                    get_polygon='polygon',
                    filled=True,
                    get_fill_color=[255, 215, 0, 120],   # Jaune doré semi-transparent
                    get_line_color=[255, 140, 0, 255],   # Orange vif
                    line_width_min_pixels=3,
                    pickable=True
                )
            )
        
        # Layer 3: Points de contrôle
        if st.session_state.roof_polygon:
            point_data = []
            for i, point in enumerate(st.session_state.roof_polygon):
                point_data.append({
                    'position': point,
                    'id': i,
                    'size': 8
                })
            
            layers.append(
                pdk.Layer(
                    'ScatterplotLayer',
                    data=point_data,
                    get_position='position',
                    get_radius='size',
                    get_fill_color=[255, 0, 0, 255],     # Rouge vif
                    get_line_color=[255, 255, 255, 255], # Contour blanc
                    line_width_min_pixels=2,
                    pickable=True
                )
            )
        
        # Layer 4: Panneaux calculés (si disponible)
        if (st.session_state.panel_layout and 
            'panels' in st.session_state.panel_layout and 
            st.session_state.panel_layout['panels']):
            
            panel_data = []
            for panel in st.session_state.panel_layout['panels']:
                panel_data.append({
                    'polygon': panel['corners'],
                    'id': panel['id']
                })
            
            layers.append(
                pdk.Layer(
                    'PolygonLayer',
                    data=panel_data,
                    get_polygon='polygon',
                    filled=True,
                    get_fill_color=[0, 100, 255, 180],   # Bleu panneaux
                    get_line_color=[255, 255, 255, 255], # Contour blanc
                    line_width_min_pixels=1,
                    pickable=True
                )
            )
        
        return layers
    
    def _render_drawing_controls(self, building_data: Dict):
        """Affiche les contrôles de dessin"""
        
        st.write("**🎨 Outils de dessin**")
        
        # Mode de dessin
        mode = st.radio(
            "Mode",
            ["🖊️ Polygone libre", "📐 Rectangle"],
            key="drawing_mode_selector"
        )
        
        st.session_state.drawing_mode = 'rectangle' if 'Rectangle' in mode else 'polygon'
        
        # Boutons d'action pour polygone libre
        if st.session_state.drawing_mode == 'polygon':
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🆕 Nouveau", use_container_width=True):
                    st.session_state.roof_polygon = []
                    st.session_state.panel_layout = None
                    st.rerun()
            
            with col2:
                if st.button("↩️ Retour", use_container_width=True):
                    if st.session_state.roof_polygon:
                        st.session_state.roof_polygon.pop()
                        st.rerun()
            
            # Bouton pour fermer le polygone
            if len(st.session_state.roof_polygon) >= 3:
                if st.button("✅ Terminer polygone", type="primary", use_container_width=True):
                    # Fermer le polygone si pas déjà fermé
                    if (st.session_state.roof_polygon[0] != st.session_state.roof_polygon[-1]):
                        st.session_state.roof_polygon.append(st.session_state.roof_polygon[0])
                    
                    # Calculer layout panneaux
                    self._calculate_panel_layout()
                    st.rerun()
            
            # Saisie manuelle de points
            with st.expander("📝 Ajouter point manuellement"):
                col_lat, col_lon = st.columns(2)
                with col_lat:
                    manual_lat = st.number_input(
                        "Latitude", 
                        value=building_data.get('latitude', 43.7102),
                        format="%.6f",
                        step=0.000001
                    )
                with col_lon:
                    manual_lon = st.number_input(
                        "Longitude", 
                        value=building_data.get('longitude', 7.2620),
                        format="%.6f",
                        step=0.000001
                    )
                
                if st.button("➕ Ajouter point"):
                    st.session_state.roof_polygon.append([manual_lon, manual_lat])
                    st.rerun()
        
        # Mode rectangle
        elif st.session_state.drawing_mode == 'rectangle':
            st.write("**📏 Définir rectangle :**")
            
            # Paramètres du rectangle
            rect_width = st.number_input(
                "Largeur (m)", 
                min_value=3.0, 
                max_value=50.0, 
                value=10.0, 
                step=0.5
            )
            
            rect_height = st.number_input(
                "Hauteur (m)", 
                min_value=3.0, 
                max_value=50.0, 
                value=6.0, 
                step=0.5
            )
            
            rect_rotation = st.slider(
                "Rotation (°)", 
                min_value=0, 
                max_value=360, 
                value=0, 
                step=5
            )
            
            if st.button("✅ Créer rectangle", type="primary", use_container_width=True):
                # Importer le simulateur pour utiliser sa méthode
                from .solar_simulator import SolarSimulator
                simulator = SolarSimulator()
                
                # Générer rectangle centré sur le bâtiment
                center_lon = building_data.get('longitude', 7.2620)
                center_lat = building_data.get('latitude', 43.7102)
                
                rect_polygon = simulator.create_rectangle_polygon(
                    center_lon, center_lat, rect_width, rect_height, rect_rotation
                )
                
                st.session_state.roof_polygon = rect_polygon
                self._calculate_panel_layout()
                st.rerun()
        
        # Affichage des métriques
        if st.session_state.roof_polygon and len(st.session_state.roof_polygon) >= 3:
            st.markdown("---")
            st.write("**📊 Zone définie :**")
            
            # Calculer surface
            from .solar_simulator import SolarSimulator
            simulator = SolarSimulator()
            area_m2 = simulator.calculate_polygon_area(st.session_state.roof_polygon)
            
            st.metric("Surface totale", f"{area_m2:.1f} m²")
            
            # Métriques des panneaux si calculés
            if st.session_state.panel_layout:
                layout = st.session_state.panel_layout
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Panneaux", layout.get('total_panels', 0))
                with col2:
                    st.metric("Puissance", f"{layout.get('total_kwc', 0):.1f} kWc")
                
                # Taux d'occupation
                if area_m2 > 0:
                    panel_area = layout.get('total_panels', 0) * 2.42  # 2.2 × 1.1 m²
                    occupation = (panel_area / area_m2) * 100
                    st.metric("Occupation", f"{occupation:.0f}%")
        
        # Instructions d'aide
        with st.expander("ℹ️ Aide"):
            st.markdown("""
            ### 🎯 Comment dessiner
            
            **Mode Polygone libre :**
            - Cliquez sur la carte pour placer des points
            - Minimum 3 points requis
            - Cliquez "Terminer polygone" quand fini
            
            **Mode Rectangle :**
            - Définissez largeur/hauteur/rotation
            - Cliquez "Créer rectangle"
            - Rectangle centré sur le bâtiment
            
            ### 📐 Conseils
            - Restez sur la zone de toiture visible
            - Évitez cheminées, lucarnes, obstacles
            - Laissez 1m de marge par rapport aux bords
            - Vérifiez l'orientation pour optimiser
            """)
    
    def _calculate_panel_layout(self):
        """Calcule la disposition des panneaux pour la zone dessinée"""
        if not st.session_state.roof_polygon or len(st.session_state.roof_polygon) < 3:
            return
        
        try:
            from .solar_simulator import SolarSimulator
            simulator = SolarSimulator()
            
            # Calculer layout avec orientation par défaut (sud)
            layout = simulator.calculate_panel_layout(
                st.session_state.roof_polygon, 
                azimuth=180
            )
            
            st.session_state.panel_layout = layout
            
        except Exception as e:
            st.error(f"Erreur calcul panneaux: {e}")
            st.session_state.panel_layout = None

def test_roof_editor():
    """Test du module d'édition de toiture"""
    print("TEST ROOF EDITOR")
    print("-" * 30)
    
    editor = RoofEditor()
    
    # Données de test
    building_data = {
        'latitude': 43.7102,
        'longitude': 7.2620,
        'footprint_polygon': [
            [7.2615, 43.7100],
            [7.2625, 43.7100],
            [7.2625, 43.7104],
            [7.2615, 43.7104],
            [7.2615, 43.7100]
        ]
    }
    
    print("Données de test créées")
    print(f"Bâtiment: {building_data['latitude']}, {building_data['longitude']}")
    print(f"Footprint: {len(building_data['footprint_polygon'])} points")
    
    # Test des layers
    layers = editor._create_drawing_layers(building_data)
    print(f"Layers créés: {len(layers)}")
    
    print("✅ Test terminé")

if __name__ == "__main__":
    test_roof_editor()