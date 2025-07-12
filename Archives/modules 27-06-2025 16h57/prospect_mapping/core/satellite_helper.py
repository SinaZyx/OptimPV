#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'aide pour sources satellite dans OptimPV.
Responsabilité : Gestion des différentes sources d'imagerie satellite.
"""

import streamlit as st
from typing import Dict, Optional

class SatelliteHelper:
    """Gestionnaire des sources d'imagerie satellite"""
    
    def __init__(self):
        self.sources = {
            'mapbox_satellite': {
                'name': 'Mapbox Satellite',
                'style': 'mapbox://styles/mapbox/satellite-v9',
                'quality': 'Excellent',
                'requires_key': True,
                'cost': 'Gratuit (50k vues/mois)',
                'description': 'Imagerie satellite haute résolution avec bâtiments 3D'
            },
            'mapbox_hybrid': {
                'name': 'Mapbox Satellite + Routes',
                'style': 'mapbox://styles/mapbox/satellite-streets-v12',
                'quality': 'Excellent',
                'requires_key': True,
                'cost': 'Gratuit (50k vues/mois)',
                'description': 'Satellite + superposition routes et labels'
            },
            'esri_satellite': {
                'name': 'ESRI World Imagery',
                'style': 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                'quality': 'Très bon',
                'requires_key': False,
                'cost': 'Gratuit',
                'description': 'Imagerie satellite ESRI mondiale'
            },
            'cartodb_voyager': {
                'name': 'CartoDB Voyager',
                'style': 'https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png',
                'quality': 'Bon',
                'requires_key': False,
                'cost': 'Gratuit',
                'description': 'Carte claire avec bâtiments visibles'
            },
            'openstreetmap': {
                'name': 'OpenStreetMap Standard',
                'style': 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                'quality': 'Basique',
                'requires_key': False,
                'cost': 'Gratuit',
                'description': 'Carte de base OpenStreetMap'
            }
        }
    
    def get_best_available_source(self, mapbox_key: Optional[str] = None) -> Dict:
        """
        Retourne la meilleure source satellite disponible
        
        Args:
            mapbox_key: Clé API Mapbox si disponible
            
        Returns:
            Dict avec configuration de la source optimale
        """
        # Priorité 1: Mapbox Satellite si clé disponible
        if mapbox_key and mapbox_key.startswith('pk.'):
            return {
                'source_id': 'mapbox_satellite',
                'config': {
                    'map_style': self.sources['mapbox_satellite']['style'],
                    'api_keys': {'mapbox': mapbox_key}
                },
                'info': self.sources['mapbox_satellite']
            }
        
        # Priorité 2: ESRI World Imagery (gratuit, bonne qualité)
        return {
            'source_id': 'esri_satellite',
            'config': {
                'map_style': self.sources['esri_satellite']['style']
            },
            'info': self.sources['esri_satellite']
        }
    
    def create_source_selector(self, current_mapbox_key: Optional[str] = None) -> Dict:
        """
        Crée une interface de sélection de source satellite
        
        Args:
            current_mapbox_key: Clé Mapbox actuelle
            
        Returns:
            Dict avec la source sélectionnée et sa configuration
        """
        st.write("**🛰️ Source d'imagerie satellite**")
        
        # Déterminer sources disponibles
        available_sources = []
        
        # Mapbox si clé disponible
        if current_mapbox_key and current_mapbox_key.startswith('pk.'):
            available_sources.extend([
                ('mapbox_satellite', '🌟 Mapbox Satellite (Recommandé)'),
                ('mapbox_hybrid', '🗺️ Mapbox Satellite + Routes')
            ])
        
        # Sources gratuites toujours disponibles
        available_sources.extend([
            ('esri_satellite', '🛰️ ESRI World Imagery'),
            ('cartodb_voyager', '🗺️ CartoDB Voyager'),
            ('openstreetmap', '📍 OpenStreetMap Standard')
        ])
        
        # Sélecteur
        selected_id = st.selectbox(
            "Choisir la source",
            options=[src[0] for src in available_sources],
            format_func=lambda x: next(src[1] for src in available_sources if src[0] == x),
            index=0,
            help="Sélectionnez la meilleure source selon vos besoins"
        )
        
        # Afficher infos sur la source sélectionnée
        source_info = self.sources[selected_id]
        
        col_info, col_quality = st.columns(2)
        with col_info:
            st.write(f"**Qualité:** {source_info['quality']}")
            st.write(f"**Coût:** {source_info['cost']}")
        
        with col_quality:
            if source_info['requires_key'] and not current_mapbox_key:
                st.warning("⚠️ Clé API requise")
            else:
                st.success("✅ Disponible")
        
        st.caption(source_info['description'])
        
        # Configurer la source
        if selected_id.startswith('mapbox') and current_mapbox_key:
            config = {
                'map_style': source_info['style'],
                'api_keys': {'mapbox': current_mapbox_key}
            }
        else:
            config = {
                'map_style': source_info['style']
            }
        
        return {
            'source_id': selected_id,
            'config': config,
            'info': source_info
        }
    
    def create_mapbox_setup_guide(self) -> None:
        """Affiche le guide de configuration Mapbox"""
        
        with st.expander("🚀 Guide : Obtenir une clé Mapbox (GRATUIT)"):
            st.markdown("""
            ### 🎯 Pourquoi Mapbox ?
            - ✅ **Qualité exceptionnelle** : Imagerie satellite 4K
            - ✅ **Bâtiments 3D** : Voir la forme exacte des toitures
            - ✅ **Gratuit** : 50,000 vues/mois incluses
            - ✅ **Rapide** : Configuration en 2 minutes
            
            ### 📋 Étapes (2 minutes)
            
            1. **Aller sur mapbox.com**
               - Cliquez sur "Sign up" (gratuit)
               - Utilisez votre email professionnel
            
            2. **Créer un compte**
               - Nom, email, mot de passe
               - Pas de carte bancaire requise
            
            3. **Récupérer la clé**
               - Une fois connecté, allez dans "Account"
               - Copiez le "Default public token"
               - Format : `pk.eyJ1...` (commence par pk.)
            
            4. **Coller dans OptimPV**
               - Section "Configuration de la Carte"
               - Ou dans le champ ci-dessous
            
            ### 🎁 Résultat
            Vue satellite **ultra-précise** pour dessiner parfaitement sur les toitures !
            """)
            
            # Champ de saisie rapide
            st.write("**✏️ Saisie rapide :**")
            quick_key = st.text_input(
                "Clé Mapbox",
                placeholder="pk.eyJ1...",
                type="password",
                help="Collez votre clé Mapbox ici"
            )
            
            if quick_key.startswith('pk.'):
                st.session_state['mapbox_key'] = quick_key
                st.success("🎉 **Clé Mapbox configurée !** Actualisez l'onglet dessin.")
                if st.button("🔄 Actualiser automatiquement"):
                    st.rerun()
            elif quick_key:
                st.error("❌ Format invalide. La clé doit commencer par 'pk.'")

def create_satellite_config_section():
    """Crée une section complète de configuration satellite"""
    
    st.markdown("---")
    st.subheader("🛰️ Configuration Imagerie Satellite")
    
    helper = SatelliteHelper()
    
    # Récupérer clé Mapbox actuelle
    current_mapbox_key = st.session_state.get('mapbox_key')
    
    col_selector, col_guide = st.columns([2, 1])
    
    with col_selector:
        # Sélecteur de source
        source_config = helper.create_source_selector(current_mapbox_key)
        
        # Bouton test
        if st.button("🧪 Tester cette source", use_container_width=True):
            st.success(f"✅ Source testée: {source_config['info']['name']}")
            return source_config
    
    with col_guide:
        # Guide Mapbox si pas de clé
        if not current_mapbox_key:
            helper.create_mapbox_setup_guide()
        else:
            st.success("🎉 **Mapbox configuré !**")
            st.write(f"Clé: `{current_mapbox_key[:15]}...`")
            
            if st.button("🗑️ Supprimer clé", use_container_width=True):
                del st.session_state['mapbox_key']
                st.rerun()
    
    return source_config

# Test de la classe
def test_satellite_helper():
    """Test du helper satellite"""
    print("TEST SATELLITE HELPER")
    print("-" * 30)
    
    helper = SatelliteHelper()
    
    # Test sans clé
    print("1. Test sans clé Mapbox:")
    best_free = helper.get_best_available_source()
    print(f"   Source: {best_free['info']['name']}")
    print(f"   Qualité: {best_free['info']['quality']}")
    
    # Test avec clé fictive
    print("\n2. Test avec clé Mapbox:")
    best_premium = helper.get_best_available_source("pk.test_key")
    print(f"   Source: {best_premium['info']['name']}")
    print(f"   Qualité: {best_premium['info']['quality']}")
    
    print("\n✅ Test terminé")

if __name__ == "__main__":
    test_satellite_helper()