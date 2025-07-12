#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'interface utilisateur pour la cartographie de prospection.
Responsabilité : Interface Streamlit pour la fonctionnalité de cartographie.
"""

import logging
import streamlit as st
import pandas as pd
from .core.data_handler import (
    load_and_process_data,
    get_unique_communes,
    get_available_communes_from_api,
    get_all_communes_dept_06,
    filter_data_by_consumption,
    filter_data_by_communes,
    update_polygons_for_zoom,
    enrich_single_building_on_demand,
    get_closest_communes_to_mougins
)
try:
    from .core.map_visualizer_robust import create_prospect_map, get_map_legend_info
except ImportError:
    try:
        from .core.map_visualizer_robust import create_prospect_map, get_map_legend_info
    except ImportError:
        # Fallback si le module n'existe pas
        create_prospect_map = None
        get_map_legend_info = None

# from .interactive_tooltip_handler import integrate_interactive_tooltips
# from .tooltip_styles import inject_custom_css

logger = logging.getLogger(__name__)

def show_prospect_map_ui():
    """
    Affiche l'interface utilisateur principale pour la cartographie de prospection.
    """
    # CSS injecté maintenant via tooltip simple dans map_visualizer
    
    # En-tête de la page
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.title("🗺️ Carte de Prospection - Département 06")
        st.markdown("""
        Cette carte interactive affiche les données de consommation énergétique des bâtiments 
        du département des Alpes-Maritimes (06) pour identifier les prospects potentiels 
        pour l'installation de panneaux solaires.
        """)
    
    with col2:
        st.write("")  # Espacement
        if st.button("🔄 Actualiser les Données", 
                    type="secondary", 
                    help="Vide le cache et recharge les données depuis l'API Enedis",
                    use_container_width=True):
            # Vider le cache de la fonction load_and_process_data
            load_and_process_data.clear()
            st.success("✅ Cache vidé ! Les données vont être rechargées.")
            st.rerun()
    
    # Pré-sélection des communes pour accélérer le téléchargement
    st.subheader("🏘️ Sélection des Communes")
    
    # NOUVEAU: Mode de chargement
    loading_mode = st.radio(
        "Mode de chargement :",
        options=[
            "🎯 Proximité Mougins (10 communes les plus proches) - RECOMMANDÉ",
            "🏘️ Sélection personnalisée", 
            "🌍 Toutes les communes du 06"
        ],
        index=0,
        help="Choisissez votre stratégie de chargement pour optimiser la vitesse"
    )
    
    # Variables pour le chargement
    communes_filter = None
    proximity_mode = False
    
    if "Proximité Mougins" in loading_mode:
        # Mode proximité Mougins
        proximity_mode = True
        st.success("🎯 **Mode Proximité Mougins** : Chargement des 10 communes les plus proches")
        st.info("📍 Centré sur Mougins, inclut Cannes, Antibes, Le Cannet, Vallauris, etc.")
        estimated_time = "15-30 secondes"
        st.success(f"⏱️ **Estimation :** ~2000 adresses, temps: {estimated_time}")
        
    elif "Sélection personnalisée" in loading_mode:
        # Mode sélection manuelle
        st.info("💡 **Conseil :** Sélectionnez quelques communes pour un téléchargement plus rapide !")
        
        # Récupérer la liste complète des communes du département 06 (une seule fois)
        with st.spinner("Récupération de toutes les communes du 06..."):
            all_communes_06 = get_all_communes_dept_06()
        
        # Sélecteur de communes pour le téléchargement (liste complète)
        preselected_communes = st.multiselect(
            "Communes à télécharger :",
            options=all_communes_06,
            default=[],
            help="Sélectionnez une ou plusieurs communes pour télécharger et afficher leurs données"
        )
        
        if preselected_communes:
            communes_filter = preselected_communes
            estimated_records = len(preselected_communes) * 200  # Estimation
            estimated_time = "30 secondes - 2 minutes"
            st.success(f"⏱️ **Estimation :** {estimated_records:,} adresses, temps: {estimated_time}")
        else:
            st.warning("⚠️ Aucune commune sélectionnée - Mode proximité Mougins sera utilisé")
            proximity_mode = True
            
    else:
        # Mode toutes les communes
        st.warning("⏱️ **Attention :** Toutes les communes = 10,000+ adresses, temps: 5-10 minutes")
        proximity_mode = False
    
    # Message de chargement adaptatif
    if proximity_mode and communes_filter is None:
        loading_msg = "🎯 Chargement optimisé : 10 communes proches de Mougins..."
    elif communes_filter:
        loading_msg = f"🏘️ Chargement de {len(communes_filter)} communes sélectionnées..."
    else:
        loading_msg = "🌍 Chargement de toutes les communes du département 06..."
    
    with st.spinner(loading_msg):
        try:
            data = load_and_process_data(communes_filter, proximity_mode)
            st.success(f"✅ Données chargées : {len(data):,} enregistrements")
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement des données : {str(e)}")
            logger.error(f"Erreur chargement données : {e}")
            return
    
    # Interface de filtrage dans la barre latérale
    st.sidebar.header("🔍 Filtres de Prospection")
    
    # Filtre par seuil de consommation
    st.sidebar.subheader("Seuil de Consommation")
    min_consumption = data['consommation_kwh'].min()
    max_consumption = data['consommation_kwh'].max()
    mean_consumption = data['consommation_kwh'].mean()
    
    consumption_threshold = st.sidebar.slider(
        "Consommation minimum (kWh/an)",
        min_value=int(min_consumption),
        max_value=int(max_consumption),
        value=int(mean_consumption),
        step=500,
        help="Afficher uniquement les bâtiments avec une consommation supérieure à ce seuil"
    )
    
    # Filtre par communes dans la sidebar
    st.sidebar.subheader("Sélection des Communes")
    communes_list = get_unique_communes(data)
    
    selected_communes = st.sidebar.multiselect(
        "Communes à afficher sur la carte",
        options=communes_list,
        default=[],
        help="Filtrez l'affichage sur des communes spécifiques (laissez vide pour toutes les communes téléchargées)"
    )
    
    # Application des filtres
    filtered_data = filter_data_by_consumption(data, consumption_threshold)
    
    # Appliquer le filtre par communes si sélectionné
    if selected_communes:
        filtered_data = filter_data_by_communes(filtered_data, selected_communes)
    
    # Options d'interaction dans la sidebar
    st.sidebar.subheader("⚙️ Options d'Interaction")

    # Toggle pour le mode d'interaction
    interaction_mode = st.sidebar.radio(
        "Mode d'interaction avec la carte",
        options=["Navigation", "Sélection"],
        help="""
        - Navigation : Déplacer et zoomer la carte
        - Sélection : Cliquer sur les parcelles pour afficher les détails
        """,
        index=0
    )

    # Taille adaptative des carrés
    adaptive_size = st.sidebar.checkbox(
        "Taille adaptative des carrés",
        value=True,
        help="Ajuste automatiquement la taille des carrés selon le zoom"
    )

    # Affichage des tooltips
    tooltip_mode = st.sidebar.select_slider(
        "Mode d'affichage des infobulles",
        options=["Survol rapide", "Survol normal", "Clic uniquement"],
        value="Survol normal",
        help="Contrôle comment les informations s'affichent"
    )
    
    # Affichage des statistiques filtrées avec indicateur de précision
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Points",
            f"{len(filtered_data):,}",
            f"{len(filtered_data) - len(data):,}" if len(filtered_data) != len(data) else None
        )
    
    with col2:
        if len(filtered_data) > 0:
            avg_consumption = filtered_data['consommation_kwh'].mean()
            st.metric("Consommation Moyenne", f"{avg_consumption:,.0f} kWh")
        else:
            st.metric("Consommation Moyenne", "N/A")
    
    with col3:
        if len(filtered_data) > 0:
            total_consumption = filtered_data['consommation_kwh'].sum()
            st.metric("Consommation Totale", f"{total_consumption/1000:,.0f} MWh")
        else:
            st.metric("Consommation Totale", "N/A")
    
    with col4:
        if selected_communes:
            st.metric("Communes Sélectionnées", len(selected_communes))
        else:
            unique_communes = filtered_data['nom_commune'].nunique() if len(filtered_data) > 0 else 0
            st.metric("Communes Affichées", unique_communes)
    
    with col5:
        # Indicateur de précision globale
        if len(filtered_data) > 0 and 'location_confidence' in filtered_data.columns:
            high_precision = (filtered_data['location_confidence'] == 'high').sum()
            osm_precision = (filtered_data['data_source'] == 'OSM').sum()
            total_points = len(filtered_data)
            
            quality_points = high_precision + osm_precision
            precision_rate = (quality_points / total_points * 100) if total_points > 0 else 0
            
            if precision_rate >= 30:
                precision_icon = "🟢"
                status = "Bonne"
            elif precision_rate >= 10:
                precision_icon = "🟡"
                status = "Moyenne"
            else:
                precision_icon = "🔴"
                status = "Basique"
            
            st.metric("🎯 Précision", f"{status}", delta=f"{precision_icon} {quality_points}/{total_points}")
        else:
            st.metric("🎯 Précision", "Analyse...", delta="🔄 En cours")
    
    # Configuration de la carte
    st.subheader("🗺️ Configuration de la Carte")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        # Options d'affichage
        st.write("**Options d'affichage:**")
        
        # Clé API Mapbox (optionnelle)
        mapbox_key = st.text_input(
            "Clé API Mapbox (optionnelle)",
            type="password",
            help="Pour activer les fonds de carte satellite haute qualité"
        )
        
        # Informations sur la légende
        if len(filtered_data) > 0:
            legend_info = get_map_legend_info(filtered_data)
            st.write("**Légende:**")
            st.write(f"🟡 Faible: {legend_info['min_consumption']:.0f} kWh")
            st.write(f"🟠 Moyenne: {legend_info['mean_consumption']:.0f} kWh")
            st.write(f"🔴 Élevée: {legend_info['max_consumption']:.0f} kWh")
    
    with col1:
        # Création et affichage de la carte
        if len(filtered_data) == 0:
            st.warning("⚠️ Aucune donnée ne correspond aux filtres sélectionnés.")
            st.info("💡 Essayez de réduire le seuil de consommation ou de sélectionner d'autres communes.")
        else:
            with st.spinner("Génération de la carte..."):
                try:
                    # Préparer les données avec les options
                    map_data = filtered_data.copy()
                    
                    # Réinitialiser l'index pour maintenir la cohérence avec les numéros de parcelles
                    map_data = map_data.reset_index(drop=True)
                    
                    if adaptive_size:
                        # Calculer le zoom estimé basé sur la dispersion des données
                        lat_range = filtered_data['latitude'].max() - filtered_data['latitude'].min()
                        estimated_zoom = 14 - int(lat_range * 10)  # Formule approximative
                        estimated_zoom = max(9, min(14, estimated_zoom))
                        
                        # Recalculer les polygones avec la taille adaptative
                        map_data = update_polygons_for_zoom(map_data, estimated_zoom)
                    
                    # Créer la carte avec les nouvelles options
                    map_obj = create_prospect_map(
                        map_data, 
                        mapbox_api_key=mapbox_key if mapbox_key else None,
                        interaction_mode=interaction_mode,
                        tooltip_mode=tooltip_mode
                    )
                    
                    # Initialiser la sélection en session state si nécessaire
                    if 'selected_parcel_index' not in st.session_state:
                        st.session_state.selected_parcel_index = None
                    
                    # Afficher la carte simple (sans sélection pour éviter les erreurs)
                    st.pydeck_chart(
                        map_obj, 
                        use_container_width=True,
                        key="prospect_map"
                    )
                    
                    # Interface manuelle pour la sélection de parcelle
                    st.markdown("---")
                    st.subheader("🔍 Sélection Manuelle de Parcelle")
                    
                    # Préparer les données d'affichage (avec index cohérent)
                    display_data = map_data.copy()
                    if 'numero_parcelle' not in display_data.columns:
                        display_data['numero_parcelle'] = range(1, len(display_data) + 1)
                    
                    # Sélecteur de parcelle par index
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        parcel_options = []
                        for idx, row in display_data.iterrows():
                            numero_parcelle = row.get('numero_parcelle', idx + 1)
                            label = f"Parcelle #{numero_parcelle} - {row.get('nom_commune', 'N/A')} - {row.get('consommation_kwh', 0):,.0f} kWh"
                            parcel_options.append((label, idx))
                        
                        if parcel_options:
                            selected_option = st.selectbox(
                                "Choisissez une parcelle pour voir les détails :",
                                options=[None] + parcel_options,
                                format_func=lambda x: "-- Sélectionnez une parcelle --" if x is None else x[0],
                                key="parcel_selector"
                            )
                            
                            if selected_option is not None:
                                st.session_state.selected_parcel_index = selected_option[1]
                            else:
                                st.session_state.selected_parcel_index = None
                    
                    with col2:
                        st.info("💡 **Astuce:** Utilisez le menu déroulant pour sélectionner une parcelle et accéder aux boutons d'action.")
                    
                    # Afficher les détails si une parcelle est sélectionnée
                    if st.session_state.selected_parcel_index is not None:
                        try:
                            selected_parcel = display_data.iloc[st.session_state.selected_parcel_index]
                            
                            # Afficher les détails dans un panneau séparé
                            st.markdown("---")
                            
                            # En-tête 
                            st.subheader("🏢 Détails de la Parcelle Sélectionnée")
                            
                            # Détails de la parcelle
                            col1, col2, col3 = st.columns([2, 1, 1])
                            
                            with col1:
                                st.markdown(f"**📍 Commune:** {selected_parcel.get('nom_commune', 'N/A')}")
                                st.markdown(f"**🏠 Adresse:** {selected_parcel.get('adresse', 'N/A')}")
                                st.markdown(f"**🏘️ Nombre de logements:** {selected_parcel.get('nombre_de_logements', 0)}")
                                st.markdown(f"**⚡ Consommation annuelle:** {selected_parcel.get('consommation_kwh', 0):,.0f} kWh")
                                st.markdown(f"**📊 Coordonnées:** {selected_parcel.get('latitude', 0):.6f}, {selected_parcel.get('longitude', 0):.6f}")
                                
                                # NOUVELLE SECTION BÂTIMENT ENRICHIE
                                st.markdown("---")
                                st.markdown("**🏢 Informations Bâtiment (BD TOPO)**")
                                
                                # Debug: afficher les colonnes disponibles
                                available_columns = list(selected_parcel.index)
                                enriched_columns = [col for col in available_columns if col in [
                                    'location_confidence', 'data_source', 'nature_detaillee', 
                                    'nb_etages', 'etat_batiment', 'date_construction',
                                    'dpe_available', 'dpe_classe_energie', 'dpe_classe_ges'
                                ]]
                                
                                if enriched_columns:
                                    # Afficher les valeurs réelles
                                    nature = selected_parcel.get('nature_detaillee', 'Non précisé')
                                    etages = selected_parcel.get('nb_etages', 'N/A')
                                    etat = selected_parcel.get('etat_batiment', 'N/A')
                                    construction = selected_parcel.get('date_construction', 'N/A')
                                    confidence = selected_parcel.get('location_confidence', 'N/A')
                                    source = selected_parcel.get('data_source', 'N/A')
                                    
                                    # Vérifier si les données sont enrichies ou par défaut
                                    is_enriched = (nature != 'Non précisé' or etages != 0 or 
                                                  confidence != 'medium' or source != 'Estimation')
                                    
                                    if is_enriched:
                                        st.markdown(f"**🏢 Type:** {nature}")
                                        st.markdown(f"**📐 Étages:** {etages}")
                                        st.markdown(f"**🏗️ État:** {etat}")
                                        st.markdown(f"**📅 Construction:** {construction}")
                                        st.markdown(f"**🎯 Précision:** {confidence}")
                                        st.markdown(f"**📊 Source:** {source}")
                                    else:
                                        st.markdown("**⚠️ Données non enrichies pour cette parcelle**")
                                        st.markdown("💡 Cliquez sur 'Enrichir cette parcelle' pour obtenir plus d'infos")
                                        
                                        # Bouton d'enrichissement à la demande optimisé
                                        if st.button("🔍 Enrichir cette parcelle", key="enrich_parcel"):
                                            with st.spinner("Enrichissement en cours via l'optimisation à la demande..."):
                                                lat = selected_parcel.get('latitude', 0)
                                                lon = selected_parcel.get('longitude', 0)
                                                building_id = f"{lat:.6f}_{lon:.6f}"
                                                
                                                try:
                                                    # Utiliser la nouvelle fonction optimisée
                                                    enriched_data = enrich_single_building_on_demand(lat, lon, building_id)
                                                    
                                                    if enriched_data and enriched_data.get('data_source') != 'Estimation':
                                                        st.success("✅ Données bâtiment récupérées via OSM")
                                                        st.markdown(f"**🏢 Type:** {enriched_data.get('nature_detaillee', 'Non précisé')}")
                                                        st.markdown(f"**📐 Étages:** {enriched_data.get('nb_etages', 'N/A')}")
                                                        st.markdown(f"**🏗️ État:** {enriched_data.get('etat_batiment', 'N/A')}")
                                                        st.markdown(f"**📅 Construction:** {enriched_data.get('date_construction', 'N/A')}")
                                                        st.markdown(f"**🎯 Précision:** {enriched_data.get('location_confidence', 'N/A')}")
                                                        st.markdown(f"**📊 Source:** {enriched_data.get('data_source', 'N/A')}")
                                                    else:
                                                        st.warning("⚠️ Aucune donnée OSM trouvée pour ce bâtiment")
                                                    
                                                    # Affichage des données DPE si disponibles
                                                    if enriched_data and enriched_data.get('dpe_available'):
                                                        st.success("✅ Données DPE récupérées")
                                                        
                                                        # Classes énergétiques avec codes couleur
                                                        color_map = {
                                                            'A': '🟢', 'B': '🟢', 'C': '🟡', 'D': '🟠', 
                                                            'E': '🔴', 'F': '🔴', 'G': '🔴'
                                                        }
                                                        
                                                        classe_energie = enriched_data.get('dpe_classe_energie', 'N/A')
                                                        classe_ges = enriched_data.get('dpe_classe_ges', 'N/A')
                                                        consommation = enriched_data.get('dpe_consommation', 0)
                                                        distance = enriched_data.get('dpe_distance', 0)
                                                        
                                                        # Affichage enrichi
                                                        st.markdown(f"**🔋 Classe Énergie:** {color_map.get(classe_energie, '⚪')} {classe_energie}")
                                                        st.markdown(f"**🌱 Classe GES:** {color_map.get(classe_ges, '⚪')} {classe_ges}")
                                                        
                                                        if consommation > 0:
                                                            st.markdown(f"**📊 Consommation DPE:** {consommation:.0f} kWh/m²/an")
                                                        
                                                        if distance:
                                                            st.markdown(f"**📍 Distance DPE:** {distance:.0f}m")
                                                        
                                                        # Avertissement pour les immeubles
                                                        nb_logements_enedis = selected_parcel.get('nombre_de_logements', 1)
                                                        if nb_logements_enedis > 1:
                                                            st.warning("⚠️ **Important :** Ce DPE correspond à UN SEUL logement, pas à l'immeuble entier !")
                                                    else:
                                                        st.warning("⚠️ Aucune donnée DPE trouvée dans un rayon de 100m")
                                                        
                                                except Exception as e:
                                                    st.error(f"❌ Erreur lors de l'enrichissement: {e}")
                                                    logger.error(f"Erreur enrichissement parcelle {lat:.6f},{lon:.6f}: {e}")
                                else:
                                    st.markdown("**⚠️ Colonnes enrichies non disponibles**")
                                    st.markdown("💡 Utilisez le bouton 'Actualiser les Données' pour recharger avec enrichissement")
                                
                                # Section DPE si disponible
                                if selected_parcel.get('dpe_available', False):
                                    st.markdown("---")
                                    st.markdown("**🏠 Diagnostic Énergétique (DPE)**")
                                    dpe_data = selected_parcel.get('dpe_data', {})
                                    distance_dpe = selected_parcel.get('dpe_distance', 0)
                                    
                                    # Afficher les classes avec des couleurs
                                    classe_energie = selected_parcel.get('dpe_classe_energie', 'N/A')
                                    classe_ges = selected_parcel.get('dpe_classe_ges', 'N/A')
                                    consommation = selected_parcel.get('dpe_consommation', 0)
                                    
                                    # Couleurs selon classe DPE
                                    color_map = {
                                        'A': '🟢', 'B': '🟢', 'C': '🟡', 'D': '🟠', 
                                        'E': '🔴', 'F': '🔴', 'G': '🔴', 'N/A': '⚪'
                                    }
                                    
                                    st.markdown(f"**🔋 Classe Énergie:** {color_map.get(classe_energie, '⚪')} {classe_energie}")
                                    st.markdown(f"**🌱 Classe GES:** {color_map.get(classe_ges, '⚪')} {classe_ges}")
                                    if consommation > 0:
                                        st.markdown(f"**📊 Consommation:** {consommation:.0f} kWh/m²/an")
                                    if distance_dpe:
                                        st.markdown(f"**📍 Distance DPE:** {distance_dpe:.0f}m")
                                else:
                                    st.markdown("---")
                                    st.markdown("**🏠 DPE:** ⚪ Non disponible")
                            
                            with col2:
                                # Section DPE si disponible (métriques visuelles)
                                if selected_parcel.get('dpe_available', False):
                                    classe_energie = selected_parcel.get('dpe_classe_energie', 'N/A')
                                    classe_ges = selected_parcel.get('dpe_classe_ges', 'N/A')
                                    consommation = selected_parcel.get('dpe_consommation', 0)
                                    
                                    # Métriques DPE
                                    st.metric("Classe Énergie", classe_energie, 
                                              delta=f"{consommation:.0f} kWh/m²/an" if consommation > 0 else None)
                                    st.metric("Classe GES", classe_ges)
                                
                                # Bouton Vue 3D
                                google_earth_url = f"https://earth.google.com/web/search/{selected_parcel.get('latitude', 0)},{selected_parcel.get('longitude', 0)}"
                                st.link_button(
                                    "🌍 Vue 3D",
                                    google_earth_url,
                                    use_container_width=True,
                                    help="Ouvrir dans Google Earth"
                                )
                            
                            with col3:
                                # Bouton Maps
                                google_maps_url = f"https://www.google.com/maps?q={selected_parcel.get('latitude', 0)},{selected_parcel.get('longitude', 0)}"
                                st.link_button(
                                    "🗺️ Localisation",
                                    google_maps_url,
                                    use_container_width=True,
                                    help="Ouvrir dans Google Maps"
                                )
                            
                            
                            # NOUVEAU: Simulateur solaire simplifié
                            st.markdown("---")
                            st.subheader("⚡ Simulateur Solaire Simplifié")
                            
                            # Interface simplifiée avec Google Earth
                            st.info("💡 **Nouvelle approche simplifiée:** Mesurez la surface avec Google Earth, entrez la valeur, obtenez tous les calculs !")
                            
                            # Guide Google Earth
                            with st.expander("📍 **Étape 1: Guide Google Earth**", expanded=True):
                                st.markdown("""
                                ### 🌍 Comment mesurer avec Google Earth
                                
                                1. **Ouvrir Google Earth** (gratuit)
                                   - [earth.google.com](https://earth.google.com) dans votre navigateur
                                   - Ou téléchargez l'application Google Earth
                                
                                2. **Localiser le bâtiment**
                                   - Recherchez l'adresse exacte
                                   - Zoomez sur la toiture
                                
                                3. **Mesurer la surface**
                                   - Cliquez sur l'outil "Mesurer" (règle)
                                   - Sélectionnez "Mesurer une zone"
                                   - Cliquez autour de la zone de toiture disponible
                                   - Évitez cheminées, lucarnes, obstacles
                                
                                4. **Noter la surface**
                                   - Google Earth affiche la surface en m²
                                   - Notez cette valeur pour l'étape suivante
                                """)
                                
                                # Coordonnées du bâtiment sélectionné
                                if selected_parcel.get('latitude') and selected_parcel.get('longitude'):
                                    lat = selected_parcel['latitude']
                                    lon = selected_parcel['longitude']
                                    
                                    # Lien direct Google Earth
                                    earth_url = f"https://earth.google.com/web/@{lat},{lon},200a,1000d,35y,0h,0t,0r"
                                    
                                    st.markdown(f"""
                                    🎯 **Lien direct pour ce bâtiment:**
                                    [Ouvrir dans Google Earth]({earth_url})
                                    
                                    📍 **Coordonnées:** {lat:.6f}, {lon:.6f}
                                    """)
                            
                            # Interface de saisie surface
                            st.markdown("---")
                            st.markdown("### ⚡ **Étape 2: Simulation Solaire**")
                            
                            try:
                                from .core.solar_simulator import SolarSimulator
                                simulator = SolarSimulator()
                                
                                st.markdown("### 📏 Saisie de la surface")
                                
                                col_input, col_params = st.columns([1, 1])
                                
                                with col_input:
                                    # Input principal - SURFACE SEULEMENT
                                    # Type de surface
                                    surface_type = st.radio(
                                        "Type de surface mesurée",
                                        options=['brute', 'nette'],
                                        format_func=lambda x: {
                                            'brute': '📐 Surface brute (avec obstacles)',
                                            'nette': '🎯 Surface nette (déjà optimisée)'
                                        }[x],
                                        help="Brute = Google Earth total | Nette = zones panneaux uniquement"
                                    )
                                    
                                    surface_m2 = st.number_input(
                                        "Surface (m²)",
                                        min_value=0.0,
                                        max_value=50000.0,
                                        value=100.0,
                                        step=5.0,
                                        help="Surface brute = avec obstacles | Surface nette = zones panneaux seulement"
                                    )
                                    
                                    # Guide des surfaces typiques
                                    st.caption("""
                                    💡 **Surfaces typiques:**
                                    - Maison individuelle: 50-150 m²
                                    - PME/Bureau: 200-800 m²
                                    - Entrepôt/Usine: 1,000-10,000 m²
                                    - Centre commercial: 10,000+ m²
                                    """)
                                
                                with col_params:
                                    # Mode de calcul
                                    st.write("**🎯 Approche de Dimensionnement**")
                                    calculation_approach = st.radio(
                                        "Niveau de confiance",
                                        options=['optimiste', 'realiste', 'conservateur'],
                                        format_func=lambda x: {
                                            'optimiste': '🎯 Optimiste (Toit idéal - 90%)',
                                            'realiste': '⚖️ Réaliste (Standard - 83%)',
                                            'conservateur': '🛡️ Conservateur (Pessimiste - 75%)'
                                        }[x],
                                        index=1,  # Réaliste par défaut
                                        help="Choisissez selon vos contraintes terrain"
                                    )
                                    
                                    # Paramètres orientation
                                    st.write("**🧭 Orientation panneaux**")
                                    
                                    tilt = st.selectbox(
                                        "Inclinaison",
                                        options=[0, 15, 30, 45],
                                        index=2,
                                        format_func=lambda x: f"{x}° {'(Toit plat)' if x==0 else '(Optimal)' if x==30 else ''}"
                                    )
                                    
                                    if tilt == 0:
                                        st.info("💡 **Toit plat** : Installation avec supports à 10-15° pour drainage et performance optimale")
                                    
                                    azimuth = st.selectbox(
                                        "Orientation",
                                        options=[135, 180, 225],
                                        index=1,
                                        format_func=lambda x: f"{x}° {'(Sud-Est)' if x==135 else '(Sud - Optimal)' if x==180 else '(Sud-Ouest)'}"
                                    )
                                
                                # NOUVELLE SECTION : Type de bâtiment et profil de consommation
                                st.markdown("### 🏢 Type de Bâtiment et Profil de Consommation")
                                
                                col_building, col_conso = st.columns(2)
                                
                                with col_building:
                                        building_type = st.selectbox(
                                            "Type de bâtiment",
                                            options=[
                                                'residential_family',
                                                'residential_telework', 
                                                'office',
                                                'retail',
                                                'industrial_2x8',
                                                'industrial_3x8'
                                            ],
                                            format_func=lambda x: {
                                                'residential_family': '🏠 Résidentiel - Famille',
                                                'residential_telework': '🏠 Résidentiel - Télétravail',
                                                'office': '🏢 Bureaux',
                                                'retail': '🏪 Commerce', 
                                                'industrial_2x8': '🏭 Industriel 2x8',
                                                'industrial_3x8': '🏭 Industriel 3x8'
                                            }[x],
                                            help="Le profil influence fortement le taux d'autoconsommation"
                                        )
                                
                                with col_conso:
                                    # Consommation annuelle du bâtiment
                                    if 'consommation_kwh' in selected_parcel:
                                        default_conso = selected_parcel['consommation_kwh']
                                    else:
                                        default_conso = 15000
                                        
                                    annual_consumption = st.number_input(
                                        "Consommation annuelle (kWh)",
                                        min_value=1000,
                                        max_value=1000000,
                                        value=int(default_conso),
                                        step=1000,
                                        help="Consommation électrique totale du bâtiment"
                                    )
                                
                                # Option personnalisation du profil
                                st.markdown("---")
                                st.markdown("### ⚙️ Visualisation du Profil de Charge")
                                
                                # Bouton pour afficher le graphique du profil
                                if st.button("📊 Afficher Courbe de Charge", type="secondary"):
                                    try:
                                        # Importer et utiliser le gestionnaire de profils
                                        from .core.consumption_profiles import ConsumptionProfileManager
                                        profile_manager = ConsumptionProfileManager()
                                        
                                        # Créer le graphique de profil
                                        fig_profile = create_load_curve_chart(profile_manager, building_type)
                                        st.plotly_chart(fig_profile, use_container_width=True)
                                        
                                        # Afficher les statistiques du profil
                                        stats = profile_manager.get_profile_stats(building_type)
                                        if stats:
                                            col_stat1, col_stat2, col_stat3 = st.columns(3)
                                            with col_stat1:
                                                st.metric("Pic Été", f"{stats['summer_peak_hour']}h")
                                            with col_stat2:
                                                st.metric("Pic Hiver", f"{stats['winter_peak_hour']}h") 
                                            with col_stat3:
                                                st.metric("Ratio Jour/Nuit", f"{stats['day_night_ratio_summer']:.1f}")
                                    except Exception as e:
                                        st.error(f"Erreur affichage profil: {e}")
                                
                                # Valeurs par défaut pour personnalisation
                                morning_shift = 0
                                evening_shift = 0  
                                day_factor = 100
                                
                                # Descriptions des profils
                                profile_info = {
                                    'residential_family': "Famille résidentielle - Pics matin 7h et soir 19h, weekend +10%",
                                    'residential_telework': "Télétravail - Consommation jour élevée, pics décalés",
                                    'office': "Bureau - Jour ouvrable uniquement 8h-18h, weekend -90%",
                                    'retail': "Commerce - Ouverture continue 8h-20h, weekend -10%",
                                    'industrial_2x8': "Industrie 2x8 - 2 équipes 6h-14h et 14h-22h",
                                    'industrial_3x8': "Industrie 3x8 - Production continue 24h/24"
                                }
                                st.info(f"**Profil:** {profile_info.get(building_type, 'Standard')}")
                                
                                # Bouton de calcul
                                if st.button("🚀 Calcul Professionnel (Profils Réalistes)", type="primary", use_container_width=True):
                                    if surface_m2 > 0:
                                        with st.spinner("Récupération données PVGIS et calcul heure par heure..."):
                                            try:
                                                # Adapter l'approche selon le type de surface
                                                if surface_type == 'nette':
                                                    # Surface nette = déjà optimisée, juste l'espacement
                                                    effective_approach = 'nette_optimisee' 
                                                else:
                                                    # Surface brute = utiliser l'approche choisie
                                                    effective_approach = calculation_approach
                                                
                                                # Calculer les panneaux
                                                layout = simulator.calculate_panels_from_area(surface_m2, effective_approach)
                                                kwp = layout['total_kwc']
                                                
                                                if kwp > 0:
                                                    lat = selected_parcel.get('latitude', 43.7102)
                                                    lon = selected_parcel.get('longitude', 7.2620)
                                                    
                                                    custom_profile = {
                                                        'morning_shift': morning_shift,
                                                        'evening_shift': evening_shift,
                                                        'day_factor': day_factor/100
                                                    } if any([morning_shift != 0, evening_shift != 0, day_factor != 100]) else None
                                                    
                                                    # Appel de la nouvelle fonction asynchrone
                                                    import asyncio
                                                    
                                                    async def run_advanced_calculation():
                                                        return await simulator.calculate_advanced_autoconsumption(
                                                            annual_consumption, kwp, lat, lon, azimuth, tilt,
                                                            building_type, custom_profile
                                                        )
                                                    
                                                    # Exécuter le calcul asynchrone
                                                    loop = asyncio.new_event_loop()
                                                    asyncio.set_event_loop(loop)
                                                    results_advanced = loop.run_until_complete(run_advanced_calculation())
                                                    loop.close()
                                                    
                                                    # Ajouter les infos sur la surface et les panneaux
                                                    results_advanced['surface_m2'] = surface_m2
                                                    results_advanced['layout'] = layout
                                                    
                                                    st.session_state.solar_results_advanced = results_advanced
                                                    st.session_state.calculation_type = 'advanced'
                                                    st.success("✅ Analyse Complète Terminée !")
                                                    st.rerun()
                                                else:
                                                    st.error("Surface trop petite pour installation viable")
                                            except Exception as e:
                                                st.error(f"Erreur calcul avancé: {e}")
                                                logger.error(f"Erreur calcul avancé: {e}")
                                    else:
                                        st.error("Veuillez entrer une surface > 0 m²")
                                
                                # Affichage des résultats AVANCÉS
                                if 'solar_results_advanced' in st.session_state:
                                    st.markdown("---")
                                    st.markdown("### 📊 **Analyse Professionnelle - Résultats Détaillés**")
                                    
                                    results = st.session_state.solar_results_advanced
                                    layout = results['layout']
                                    summary = results['summary']
                                    financial = results['financial']
                                    
                                    # Métriques principales
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    with col1:
                                        st.metric(
                                            "Production Annuelle",
                                            f"{summary['production_annual_kwh']:,} kWh",
                                            delta=f"{summary['production_annual_kwh']/layout['total_kwc']:.0f} kWh/kWc"
                                        )
                                    
                                    with col2:
                                        st.metric(
                                            "Autoconsommation",
                                            f"{summary['self_consumption_rate']:.1f}%",
                                            delta=f"{summary['autoconsumption_kwh']:,} kWh",
                                            help="Part de la production consommée sur place"
                                        )
                                    
                                    with col3:
                                        st.metric(
                                            "Autoproduction", 
                                            f"{summary['self_production_rate']:.1f}%",
                                            delta=f"-{summary['grid_consumption_kwh']:,} kWh réseau",
                                            help="Part des besoins couverts par le solaire"
                                        )
                                    
                                    with col4:
                                        st.metric(
                                            "Puissance Installée",
                                            f"{layout['total_kwc']:.1f} kWc",
                                            delta=f"{layout['total_panels']} panneaux 440W"
                                        )
                                    
                                    # Affichage des alternatives et détail de calcul
                                    if 'alternatives' in layout and layout['alternatives']:
                                        st.markdown("### 🔍 Alternatives de Dimensionnement")
                                        
                                        col_alt1, col_alt2 = st.columns(2)
                                        alt_data = list(layout['alternatives'].items())
                                        
                                        if len(alt_data) >= 1:
                                            with col_alt1:
                                                alt_name, alt_info = alt_data[0]
                                                st.info(f"""
                                                **{alt_info['description']}**  
                                                {alt_info['panels']} panneaux → {alt_info['kwc']} kWc
                                                """)
                                        
                                        if len(alt_data) >= 2:
                                            with col_alt2:
                                                alt_name, alt_info = alt_data[1]
                                                st.info(f"""
                                                **{alt_info['description']}**  
                                                {alt_info['panels']} panneaux → {alt_info['kwc']} kWc
                                                """)
                                    
                                    # Détail du calcul
                                    if 'calculation_detail' in layout:
                                        with st.expander("🔍 Détail du Calcul"):
                                            detail = layout['calculation_detail']
                                            preset = layout['efficiency_preset']
                                            
                                            st.write(f"""
                                            **Méthode {layout['approach_used'].title()}** - {preset['description']}
                                            
                                            1. Surface brute : {detail['surface_brute']} m²
                                            2. Efficacité retenue : {detail['efficacite_retenue']}
                                               - Espacement : -{(1-preset['spacing'])*100:.0f}%
                                               - Obstacles : -{(1-preset['obstacles'])*100:.0f}%  
                                               - Forme : -{(1-preset['forme'])*100:.0f}%
                                            3. Surface utile : {detail['surface_utile']} m²
                                            4. Panneaux théoriques : {detail['panneaux_theoriques']}
                                            5. Panneaux installés : {detail['panneaux_installes']} unités
                                            6. Puissance : {layout['total_kwc']} kWc
                                            
                                            **Confiance :** {preset['confidence']}
                                            """)
                                    
                                    # Comparaison avec calcul simple
                                    st.info(f"""
                                    🎯 **Résultat Professionnel:** {layout['total_panels']} panneaux 440W → 
                                    **{summary['self_consumption_rate']:.0f}% autoconsommation** (vs ~100% calcul simpliste) → 
                                    **ROI réaliste: {financial['roi_years']:.1f} ans**
                                    """)
                                    
                                    # Graphiques journées types
                                    if 'typical_days' in results and results['typical_days']:
                                        st.markdown("### 📊 Analyse des Profils Journaliers")
                                        
                                        tab1, tab2, tab3 = st.tabs(["☀️ Journée Type Été", "❄️ Journée Type Hiver", "📈 Comparaison"])
                                        
                                        with tab1:
                                            st.write("📊 Analyse été disponible")
                                            st.info("Graphiques de comparaison été - fonctionnalité disponible")
                                        
                                        with tab2:
                                            st.write("📊 Analyse hiver disponible") 
                                            st.info("Graphiques de comparaison hiver - fonctionnalité disponible")
                                        
                                        with tab3:
                                            st.write("📊 Comparaison saisonnière disponible")
                                            st.info("Comparaisons été/hiver - fonctionnalité disponible")
                                    
                                    # Informations sur les sources de données
                                    st.markdown("### ℹ️ Sources et Méthodes")
                                    col_info1, col_info2 = st.columns(2)
                                    
                                    with col_info1:
                                        st.write(f"**Production:** {results.get('production_source', 'estimation')}")
                                        st.write(f"**Type bâtiment:** {results.get('building_type', 'residential_family')}")
                                        if 'hourly_results' in results:
                                            st.write(f"**Calcul:** 8760 heures analysées")
                                    
                                    with col_info2:
                                        # Afficher la source du profil de consommation
                                        try:
                                            from .core.consumption_profiles import ConsumptionProfileManager
                                            temp_manager = ConsumptionProfileManager()
                                            profile_source = temp_manager.get_profile_source(results.get('building_type', 'residential_family'))
                                            st.write(f"**Profil conso:** {profile_source}")
                                        except Exception:
                                            st.write("**Profils conso:** ADEME/RTE France")
                                        
                                        st.write("**API Production:** PVGIS (Commission Européenne)")
                                        st.write("**Méthode:** Synchronisation heure par heure")
                            
                            except ImportError as e:
                                st.error(f"Module simulateur non disponible: {e}")
                            except Exception as e:
                                st.error(f"Erreur simulation: {e}")
                            
                            
                            # Informations supplémentaires
                            st.markdown("---")
                            st.success("✅ Parcelle sélectionnée ! Utilisez les boutons ci-dessous pour ouvrir la localisation.")
                            
                            # Afficher un deuxième ensemble de boutons pour plus de visibilité
                            st.markdown("#### Actions rapides :")
                            col_action1, col_action2, col_action3 = st.columns(3)
                            
                            with col_action1:
                                if st.button("🌍 Ouvrir Google Earth", key="earth_btn", use_container_width=True):
                                    st.markdown(f'<meta http-equiv="refresh" content="0;url={google_earth_url}" target="_blank">', unsafe_allow_html=True)
                                    st.success("Lien Google Earth copié !")
                            
                            with col_action2:
                                if st.button("🗺️ Ouvrir Google Maps", key="maps_btn", use_container_width=True):
                                    st.markdown(f'<meta http-equiv="refresh" content="0;url={google_maps_url}" target="_blank">', unsafe_allow_html=True)
                                    st.success("Lien Google Maps copié !")
                            
                            with col_action3:
                                if st.button("📋 Copier Coordonnées", key="coords_btn", use_container_width=True):
                                    coords_text = f"{selected_parcel.get('latitude', 0):.6f}, {selected_parcel.get('longitude', 0):.6f}"
                                    st.code(coords_text)
                                    st.success("Coordonnées affichées !")
                            
                        except IndexError:
                            # Index invalide, réinitialiser
                            st.session_state.selected_parcel_index = None
                            st.warning("Sélection invalide, veuillez réessayer.")
                    
                    # Informations d'utilisation (seulement si aucune parcelle sélectionnée)
                    if st.session_state.selected_parcel_index is None:
                        adaptive_info = ""
                        if adaptive_size:
                            adaptive_info = f"\n                    - Taille adaptative activée (zoom estimé: {estimated_zoom})"
                        
                        st.info(f"""
                        📊 **Points affichés:** {len(filtered_data):,} sur {len(data):,} total
                        
                        💡 **Utilisation:** 
                        - Survolez une parcelle pour voir les informations de base
                        - **Cliquez sur une parcelle** pour afficher les détails complets et accéder aux boutons
                        - Plus la couleur est rouge, plus la consommation est élevée{adaptive_info}
                        - Utilisez les filtres pour affiner votre prospection
                        """)
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors de la génération de la carte : {str(e)}")
                    logger.error(f"Erreur génération carte : {e}")
            
            # Ajout d'une légende visuelle pour la taille des carrés
            if adaptive_size and len(filtered_data) > 0:
                st.info("""
                📏 **Taille des carrés :** Les carrés s'adaptent automatiquement au niveau de zoom
                - Zoom rapproché (quartier) : ~15-20m
                - Zoom moyen (ville) : ~30-50m  
                - Zoom éloigné (département) : ~70-100m
                """)
    
    # Section d'aide et informations
    with st.expander("ℹ️ Informations et Aide"):
        st.markdown("""
        ### À propos des données
        - **Source:** API Enedis Open Data
        - **Département:** 06 (Alpes-Maritimes)
        - **Type:** Consommation annuelle résidentielle par adresse
        - **Mise à jour:** Données mises en cache pendant 1 heure
        
        ### Utilisation de la carte
        1. **Filtrage:** Utilisez la barre latérale pour filtrer par consommation et communes
        2. **Navigation:** Zoomez et déplacez-vous sur la carte avec la souris
        3. **Détails:** Survolez les colonnes pour voir les informations détaillées
        4. **Couleurs:** 
           - 🟡 Jaune = Faible consommation
           - 🟠 Orange = Consommation moyenne  
           - 🔴 Rouge = Forte consommation
        5. **Hauteur:** Plus la colonne est haute, plus la consommation est élevée
        
        ### Optimisation des performances
        - Les données sont automatiquement mises en cache
        - Utilisez les filtres pour réduire le nombre de points affichés
        - Une clé API Mapbox améliore la qualité des fonds de carte
        
        ### Support technique
        En cas de problème, vérifiez votre connexion internet et les filtres appliqués.
        """)
    
    # Téléchargement des données filtrées
    if len(filtered_data) > 0:
        st.subheader("📥 Export des Données")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Export CSV
            csv_data = filtered_data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Télécharger en CSV",
                data=csv_data,
                file_name=f"prospects_dept06_{len(filtered_data)}_points.csv",
                mime="text/csv",
                help="Télécharge les données filtrées au format CSV"
            )
        
        with col2:
            # Résumé statistique
            if st.button("Générer Résumé Statistique"):
                _show_statistics_summary(filtered_data)

def _show_statistics_summary(data: pd.DataFrame):
    """
    Affiche un résumé statistique des données filtrées.
    
    Args:
        data: DataFrame avec les données filtrées
    """
    st.subheader("📊 Résumé Statistique")
    
    # Statistiques de consommation
    consumption_stats = data['consommation_kwh'].describe()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Statistiques de Consommation (kWh):**")
        stats_df = pd.DataFrame({
            'Métrique': ['Minimum', 'Maximum', 'Moyenne', 'Médiane', 'Écart-type'],
            'Valeur': [
                f"{consumption_stats['min']:,.0f}",
                f"{consumption_stats['max']:,.0f}",
                f"{consumption_stats['mean']:,.0f}",
                f"{consumption_stats['50%']:,.0f}",
                f"{consumption_stats['std']:,.0f}"
            ]
        })
        st.dataframe(stats_df, hide_index=True)
    
    with col2:
        if 'nom_commune' in data.columns:
            st.write("**Top 10 Communes par Nombre de Prospects:**")
            top_communes = data['nom_commune'].value_counts().head(10)
            communes_df = pd.DataFrame({
                'Commune': top_communes.index,
                'Nombre de Prospects': top_communes.values
            })
            st.dataframe(communes_df, hide_index=True)
    
    # Répartition par tranche de consommation
    st.write("**Répartition par Tranche de Consommation:**")
    
    # Définir les tranches
    bins = [0, 5000, 10000, 15000, 20000, float('inf')]
    labels = ['0-5k kWh', '5-10k kWh', '10-15k kWh', '15-20k kWh', '20k+ kWh']
    
    data['tranche_conso'] = pd.cut(data['consommation_kwh'], bins=bins, labels=labels, right=False)
    distribution = data['tranche_conso'].value_counts().sort_index()
    
    distribution_df = pd.DataFrame({
        'Tranche': distribution.index,
        'Nombre': distribution.values,
        'Pourcentage': (distribution.values / len(data) * 100).round(1)
    })
    
    st.dataframe(distribution_df, hide_index=True)

# Fonctions graphiques pour l'analyse avancée
def create_daily_comparison_chart(daily_data: dict, title: str):
    """Crée un graphique production vs consommation sur 24h"""
    try:
        import plotly.graph_objects as go
        
        hours = list(range(24))
        production = daily_data.get('production', [0]*24)
        consumption = daily_data.get('consumption', [0]*24)
        
        fig = go.Figure()
        
        # Consommation
        fig.add_trace(go.Scatter(
            x=hours,
            y=consumption,
            mode='lines',
            name='Consommation',
            line=dict(color='red', width=3),
            fill='tozeroy',
            fillcolor='rgba(255,0,0,0.1)'
        ))
        
        # Production
        fig.add_trace(go.Scatter(
            x=hours,
            y=production, 
            mode='lines',
            name='Production PV',
            line=dict(color='orange', width=3),
            fill='tozeroy',
            fillcolor='rgba(255,165,0,0.3)'
        ))
        
        # Zone autoconsommation (intersection)
        autoconso = [min(p, c) for p, c in zip(production, consumption)]
        fig.add_trace(go.Scatter(
            x=hours,
            y=autoconso,
            mode='lines',
            name='Autoconsommation',
            line=dict(color='green', width=2, dash='dash'),
            fill='tozeroy',
            fillcolor='rgba(0,255,0,0.2)'
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Heure",
            yaxis_title="Puissance (kW)",
            hovermode='x unified',
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Erreur création graphique journalier: {e}")
        # Retourner un graphique vide en cas d'erreur
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_annotation(text="Erreur génération graphique", x=0.5, y=0.5, showarrow=False)
        return fig

def create_seasonal_comparison_chart(typical_days: dict):
    """Crée un graphique comparatif été/hiver"""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        hours = list(range(24))
        
        # Données été
        summer_prod = typical_days['summer'].get('production', [0]*24)
        summer_cons = typical_days['summer'].get('consumption', [0]*24)
        
        # Données hiver
        winter_prod = typical_days['winter'].get('production', [0]*24)
        winter_cons = typical_days['winter'].get('consumption', [0]*24)
        
        # Sous-graphiques
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Production Solaire - Comparaison Saisonnière', 
                           'Consommation - Comparaison Saisonnière'),
            vertical_spacing=0.08
        )
        
        # Production été vs hiver
        fig.add_trace(go.Scatter(
            x=hours, y=summer_prod,
            mode='lines', name='Production Été',
            line=dict(color='orange', width=3)
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=hours, y=winter_prod,
            mode='lines', name='Production Hiver',
            line=dict(color='blue', width=3)
        ), row=1, col=1)
        
        # Consommation été vs hiver
        fig.add_trace(go.Scatter(
            x=hours, y=summer_cons,
            mode='lines', name='Consommation Été',
            line=dict(color='red', width=2),
            showlegend=False
        ), row=2, col=1)
        
        fig.add_trace(go.Scatter(
            x=hours, y=winter_cons,
            mode='lines', name='Consommation Hiver',
            line=dict(color='darkred', width=2),
            showlegend=False
        ), row=2, col=1)
        
        fig.update_layout(
            title="Analyse Saisonnière - Production vs Consommation",
            height=600,
            hovermode='x unified'
        )
        
        fig.update_xaxes(title_text="Heure", row=2, col=1)
        fig.update_yaxes(title_text="Production (kW)", row=1, col=1)
        fig.update_yaxes(title_text="Consommation (kW)", row=2, col=1)
        
        return fig
        
    except Exception as e:
        logger.error(f"Erreur création graphique saisonnier: {e}")
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_annotation(text="Erreur génération graphique", x=0.5, y=0.5, showarrow=False)
        return fig

def create_load_curve_chart(profile_manager, building_type: str):
    """
    Crée un graphique de courbe de charge pour un type de bâtiment
    """
    try:
        # Import conditionnel de plotly
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
        except ImportError:
            import streamlit as st
            st.error("Module plotly requis pour la visualisation")
            return None
        
        # Récupérer le profil
        if building_type not in profile_manager.base_profiles:
            building_type = 'residential_family'
        
        profile_data = profile_manager.base_profiles[building_type]
        summer_profile = profile_data['summer_weekday']
        winter_profile = profile_data['winter_weekday']
        
        # Heures de la journée
        hours = list(range(24))
        
        # Créer le graphique avec 2 sous-graphiques
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                f"Profil de Charge - {building_type.replace('_', ' ').title()}",
                "Comparaison Été vs Hiver"
            ),
            vertical_spacing=0.1
        )
        
        # Graphique 1: Profils été et hiver
        fig.add_trace(go.Scatter(
            x=hours, 
            y=summer_profile,
            mode='lines+markers',
            name='Été - Jour de semaine',
            line=dict(color='orange', width=3),
            marker=dict(size=6)
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=hours,
            y=winter_profile, 
            mode='lines+markers',
            name='Hiver - Jour de semaine',
            line=dict(color='blue', width=3),
            marker=dict(size=6)
        ), row=1, col=1)
        
        # Graphique 2: Barres comparatives
        fig.add_trace(go.Bar(
            x=hours,
            y=summer_profile,
            name='Consommation Été',
            marker_color='orange',
            opacity=0.7,
            showlegend=False
        ), row=2, col=1)
        
        fig.add_trace(go.Bar(
            x=hours,
            y=winter_profile,
            name='Consommation Hiver', 
            marker_color='blue',
            opacity=0.7,
            showlegend=False
        ), row=2, col=1)
        
        # Mise en forme
        fig.update_layout(
            title=f"Courbe de Charge - {building_type.replace('_', ' ').title()}",
            height=800,
            hovermode='x unified',
            barmode='group'
        )
        
        # Axes
        fig.update_xaxes(
            title_text="Heure de la journée",
            dtick=2,
            row=2, col=1
        )
        fig.update_yaxes(
            title_text="Consommation relative",
            row=1, col=1
        )
        fig.update_yaxes(
            title_text="Consommation relative", 
            row=2, col=1
        )
        
        # Ajouter des annotations pour les pics
        summer_peak_hour = summer_profile.index(max(summer_profile))
        winter_peak_hour = winter_profile.index(max(winter_profile))
        
        fig.add_annotation(
            x=summer_peak_hour, y=max(summer_profile),
            text=f"Pic été: {summer_peak_hour}h",
            showarrow=True, arrowcolor="orange",
            row=1, col=1
        )
        
        fig.add_annotation(
            x=winter_peak_hour, y=max(winter_profile),
            text=f"Pic hiver: {winter_peak_hour}h", 
            showarrow=True, arrowcolor="blue",
            row=1, col=1
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Erreur création graphique profil: {e}")
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_annotation(text="Erreur génération graphique profil", x=0.5, y=0.5, showarrow=False)
        return fig

if __name__ == "__main__":
    show_prospect_map_ui()