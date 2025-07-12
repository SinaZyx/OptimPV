#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'interface utilisateur pour la cartographie de prospection.
Responsabilité : Interface Streamlit pour la fonctionnalité de cartographie.
"""

import logging
import streamlit as st
import pandas as pd
from .data_handler import (
    load_and_process_data,
    get_unique_communes,
    get_available_communes_from_api,
    get_all_communes_dept_06,
    filter_data_by_consumption,
    filter_data_by_communes,
    update_polygons_for_zoom
)
try:
    from .map_visualizer_robust import create_prospect_map, get_map_legend_info
except ImportError:
    try:
        from .map_visualizer_simple import create_prospect_map, get_map_legend_info
    except ImportError:
        from .map_visualizer import create_prospect_map, get_map_legend_info

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
    st.info("💡 **Conseil :** Sélectionnez d'abord quelques communes pour un téléchargement plus rapide !")
    
    # Récupérer la liste complète des communes du département 06 (une seule fois)
    with st.spinner("Récupération de toutes les communes du 06..."):
        all_communes_06 = get_all_communes_dept_06()
    
    # Sélecteur de communes pour le téléchargement (liste complète)
    preselected_communes = st.multiselect(
        "Communes à télécharger (laissez vide pour toutes) :",
        options=all_communes_06,
        default=[],
        help="Sélectionnez une ou plusieurs communes pour télécharger et afficher leurs données"
    )
    
    # Estimation du temps de téléchargement
    if preselected_communes:
        estimated_records = len(preselected_communes) * 200  # Estimation
        estimated_time = "30 secondes - 2 minutes"
        st.success(f"⏱️ **Estimation :** {estimated_records:,} adresses, temps: {estimated_time}")
    else:
        st.warning("⏱️ **Attention :** Toutes les communes = 10,000+ adresses, temps: 5-10 minutes")
    
    # Chargement des données avec filtre
    communes_filter = preselected_communes if preselected_communes else None
    loading_msg = f"Chargement des données Enedis{' pour ' + ', '.join(preselected_communes) if preselected_communes else ' (toutes communes)'}..."
    
    with st.spinner(loading_msg):
        try:
            data = load_and_process_data(communes_filter)
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
    
    # Affichage des statistiques filtrées
    col1, col2, col3, col4 = st.columns(4)
    
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
                            
                            with col2:
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
                            
                            # Informations supplémentaires
                            st.success("✅ Parcelle sélectionnée ! Utilisez les boutons ci-dessus pour ouvrir la localisation.")
                            
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