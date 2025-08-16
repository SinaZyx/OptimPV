"""Interface de carte pour visualiser les clients ERP et leurs relations.

Ce module fournit une carte interactive dédiée aux clients ERP avec :
- Visualisation des clients par type (producteur, consommateur, prosumer)
- Cercles de zone d'influence (2km par défaut)
- Lignes de connexion pour l'autoconsommation collective
- Heatmap de capacité disponible
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
from typing import List, Dict, Optional, Tuple
import math

try:
    import folium
    from folium import plugins
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    # Créer des classes Mock pour les type hints
    class MockFolium:
        class Map:
            pass
        class FeatureGroup:
            pass
    folium = MockFolium()
    plugins = None

from ..services.client_service import ClientService
from ..services.capacity_service import CapacityService
from ..models.client import TypeClient


def render_client_map(
    client_service: ClientService,
    capacity_service: CapacityService
):
    """Affiche la carte interactive des clients ERP.
    
    Args:
        client_service: Service de gestion des clients
        capacity_service: Service de gestion des capacités
    """
    st.header("🗺️ Carte des Clients ERP")
    
    # Vérifier si folium est disponible
    if not FOLIUM_AVAILABLE:
        st.error("📦 Module 'folium' requis pour la carte interactive")
        st.info("💡 Installer avec: `pip install folium`")
        st.stop()
    
    # Options d'affichage
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        show_producers = st.checkbox("⚡ Producteurs", value=True)
        
    with col2:
        show_consumers = st.checkbox("🏠 Consommateurs", value=True)
        
    with col3:
        show_prosumers = st.checkbox("🔄 Prosumers", value=True)
        
    with col4:
        show_zones = st.checkbox("⭕ Zones 2km", value=False)
    
    # Options supplémentaires
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        show_connections = st.checkbox("🔗 Connexions", value=True)
        
    with col6:
        show_capacity = st.checkbox("🌡️ Capacité", value=False)
        
    with col7:
        zone_radius = st.number_input(
            "Rayon zone (km)",
            min_value=0.5,
            max_value=10.0,
            value=2.0,
            step=0.5
        )
        
    with col8:
        if st.button("🔄 Actualiser", key="refresh_client_map"):
            st.rerun()
    
    # Créer la carte
    map_obj = create_client_map(
        client_service,
        capacity_service,
        show_producers,
        show_consumers,
        show_prosumers,
        show_zones,
        show_connections,
        show_capacity,
        zone_radius
    )
    
    # Afficher la carte
    if map_obj:
        st.components.v1.html(
            map_obj._repr_html_(),
            height=600
        )
        
        # Légende
        render_map_legend()
        
        # Statistiques de la carte
        render_map_statistics(client_service, capacity_service)
    else:
        st.warning("Aucun client avec coordonnées GPS à afficher sur la carte.")


def create_client_map(
    client_service: ClientService,
    capacity_service: CapacityService,
    show_producers: bool,
    show_consumers: bool,
    show_prosumers: bool,
    show_zones: bool,
    show_connections: bool,
    show_capacity: bool,
    zone_radius: float
) -> Optional[folium.Map]:
    """Crée la carte Folium avec tous les éléments.
    
    Returns:
        Objet carte Folium ou None si aucune donnée
    """
    # Vérifier si folium est disponible
    if not FOLIUM_AVAILABLE:
        return None
        
    # Récupérer tous les clients avec coordonnées
    all_clients = client_service.get_all()
    clients_with_coords = [c for c in all_clients if c.has_coordinates]
    
    if not clients_with_coords:
        return None
    
    # Filtrer par type
    clients_to_show = []
    if show_producers:
        clients_to_show.extend([c for c in clients_with_coords if c.type_client == TypeClient.PRODUCTEUR])
    if show_consumers:
        clients_to_show.extend([c for c in clients_with_coords if c.type_client == TypeClient.CONSOMMATEUR])
    if show_prosumers:
        clients_to_show.extend([c for c in clients_with_coords if c.type_client == TypeClient.PROSUMER])
    
    if not clients_to_show:
        return None
    
    # Calculer le centre de la carte
    avg_lat = sum(c.latitude for c in clients_to_show) / len(clients_to_show)
    avg_lon = sum(c.longitude for c in clients_to_show) / len(clients_to_show)
    
    # Créer la carte avec un style moderne
    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=11,
        tiles=None,
        prefer_canvas=True
    )
    
    # Ajouter différents fonds de carte
    folium.TileLayer(
        'cartodbpositron',
        name='Clair',
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        'cartodbdark_matter',
        name='Sombre',
        control=False
    ).add_to(m)
    
    folium.TileLayer(
        'OpenStreetMap',
        name='OpenStreetMap',
        control=False
    ).add_to(m)
    
    # Groupes de calques
    producer_group = folium.FeatureGroup(name="⚡ Producteurs", show=show_producers)
    consumer_group = folium.FeatureGroup(name="🏠 Consommateurs", show=show_consumers)
    prosumer_group = folium.FeatureGroup(name="🔄 Prosumers", show=show_prosumers)
    zone_group = folium.FeatureGroup(name="⭕ Zones d'influence", show=show_zones)
    connection_group = folium.FeatureGroup(name="🔗 Connexions autoconso", show=show_connections)
    
    # Ajouter les marqueurs clients
    for client in clients_to_show:
        add_client_marker(
            m, client, client_service, capacity_service,
            producer_group, consumer_group, prosumer_group,
            zone_group, zone_radius
        )
    
    # Ajouter les connexions d'autoconsommation
    if show_connections:
        add_autoconso_connections(m, capacity_service, connection_group)
    
    # Ajouter la heatmap de capacité
    if show_capacity:
        add_capacity_heatmap(m, capacity_service)
    
    # Ajouter les groupes à la carte
    producer_group.add_to(m)
    consumer_group.add_to(m)
    prosumer_group.add_to(m)
    zone_group.add_to(m)
    connection_group.add_to(m)
    
    # Ajouter le contrôle des calques
    folium.LayerControl(position='topright').add_to(m)
    
    # Ajouter une échelle
    plugins.MeasureControl(position='bottomleft').add_to(m)
    
    # Ajouter un mini-carte
    minimap = plugins.MiniMap(
        toggle_display=True,
        position='bottomright'
    )
    minimap.add_to(m)
    
    return m


def add_client_marker(
    map_obj: folium.Map,
    client,
    client_service: ClientService,
    capacity_service: CapacityService,
    producer_group: folium.FeatureGroup,
    consumer_group: folium.FeatureGroup,
    prosumer_group: folium.FeatureGroup,
    zone_group: folium.FeatureGroup,
    zone_radius: float
):
    """Ajoute un marqueur pour un client sur la carte."""
    # Vérifier si folium est disponible
    if not FOLIUM_AVAILABLE:
        return
        
    # Déterminer la couleur et l'icône selon le type
    if client.type_client == TypeClient.PRODUCTEUR:
        color = 'green'
        icon = 'bolt'
        group = producer_group
    elif client.type_client == TypeClient.CONSOMMATEUR:
        color = 'blue'
        icon = 'home'
        group = consumer_group
    else:  # PROSUMER
        color = 'purple'
        icon = 'sync'
        group = prosumer_group
    
    # Récupérer les informations supplémentaires
    if client.type_client in [TypeClient.PRODUCTEUR, TypeClient.PROSUMER]:
        prod_points = capacity_service.get_production_points_by_client(client.id)
        total_capacity = sum(p.capacite_kwc for p in prod_points)
        available_capacity = sum(p.capacite_disponible_kwc for p in prod_points)
    else:
        total_capacity = 0
        available_capacity = 0
    
    if client.type_client in [TypeClient.CONSOMMATEUR, TypeClient.PROSUMER]:
        cons_points = capacity_service.get_consumption_points_by_client(client.id)
        total_consumption = sum(p.consommation_annuelle_kwh for p in cons_points) / 1000  # MWh
    else:
        total_consumption = 0
    
    # Créer le popup HTML
    popup_html = f"""
    <div style="font-family: Arial; width: 300px;">
        <h4 style="margin: 0; color: {color};">
            <i class="fa fa-{icon}"></i> {client.nom}
        </h4>
        <hr style="margin: 5px 0;">
        <p><strong>Code:</strong> {client.code_client}</p>
        <p><strong>Type:</strong> {client.type_client.value}</p>
        <p><strong>Adresse:</strong> {client.adresse_complete}</p>
    """
    
    if client.email:
        popup_html += f"<p><strong>Email:</strong> {client.email}</p>"
    
    if client.telephone:
        popup_html += f"<p><strong>Tél:</strong> {client.telephone}</p>"
    
    if total_capacity > 0:
        popup_html += f"""
        <hr style="margin: 5px 0;">
        <p><strong>⚡ Production:</strong></p>
        <p>• Capacité totale: {total_capacity:.1f} kWc</p>
        <p>• Capacité disponible: {available_capacity:.1f} kWc</p>
        <p>• Utilisation: {((total_capacity - available_capacity) / total_capacity * 100):.0f}%</p>
        """
    
    if total_consumption > 0:
        popup_html += f"""
        <hr style="margin: 5px 0;">
        <p><strong>🏠 Consommation:</strong></p>
        <p>• Consommation annuelle: {total_consumption:.0f} MWh</p>
        <p>• Points de livraison: {len(cons_points)}</p>
        """
    
    popup_html += """
    </div>
    """
    
    # Créer le marqueur
    marker = folium.Marker(
        location=[client.latitude, client.longitude],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"{client.nom} ({client.code_client})",
        icon=folium.Icon(
            color=color,
            icon=icon,
            prefix='fa'
        )
    )
    
    marker.add_to(group)
    
    # Ajouter la zone d'influence si demandé
    if zone_group:
        # Cercle semi-transparent
        circle = folium.Circle(
            location=[client.latitude, client.longitude],
            radius=zone_radius * 1000,  # Convertir km en mètres
            popup=f"Zone {zone_radius}km - {client.nom}",
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.1,
            weight=2,
            opacity=0.5
        )
        circle.add_to(zone_group)


def add_autoconso_connections(
    map_obj: folium.Map,
    capacity_service: CapacityService,
    connection_group: folium.FeatureGroup
):
    """Ajoute les lignes de connexion pour l'autoconsommation collective."""
    # Vérifier si folium est disponible
    if not FOLIUM_AVAILABLE:
        return
        
    # Récupérer toutes les allocations actives
    allocations = capacity_service.get_all_active_allocations()
    
    for alloc in allocations:
        # Récupérer les coordonnées des points
        prod_point = capacity_service.get_production_point(alloc.point_production_id)
        cons_point = capacity_service.get_consumption_point(alloc.point_consommation_id)
        
        if (prod_point and cons_point and 
            prod_point.latitude and prod_point.longitude and
            cons_point.latitude and cons_point.longitude):
            
            # Créer la ligne de connexion
            line = folium.PolyLine(
                locations=[
                    [prod_point.latitude, prod_point.longitude],
                    [cons_point.latitude, cons_point.longitude]
                ],
                color='orange',
                weight=2 + (alloc.pourcentage_allocation / 50),  # Épaisseur selon %
                opacity=0.6,
                popup=f"""
                <div>
                    <h4>Allocation Autoconsommation</h4>
                    <p><strong>Production:</strong> {prod_point.nom}</p>
                    <p><strong>Consommation:</strong> {cons_point.reference_interne}</p>
                    <p><strong>Allocation:</strong> {alloc.pourcentage_allocation}%</p>
                    <p><strong>Capacité:</strong> {alloc.capacite_allouee_kwc:.1f} kWc</p>
                    <p><strong>Depuis:</strong> {alloc.date_debut.strftime('%d/%m/%Y')}</p>
                </div>
                """,
                tooltip=f"{alloc.pourcentage_allocation}% - {alloc.capacite_allouee_kwc:.0f} kWc"
            )
            
            line.add_to(connection_group)
            
            # Ajouter une flèche pour indiquer la direction
            # Calculer le point milieu
            mid_lat = (prod_point.latitude + cons_point.latitude) / 2
            mid_lon = (prod_point.longitude + cons_point.longitude) / 2
            
            # Ajouter un marqueur directionnel
            folium.RegularPolygonMarker(
                location=[mid_lat, mid_lon],
                fill_color='orange',
                number_of_sides=3,
                radius=8,
                rotation=calculate_bearing(
                    prod_point.latitude, prod_point.longitude,
                    cons_point.latitude, cons_point.longitude
                ),
                popup=f"{alloc.pourcentage_allocation}%"
            ).add_to(connection_group)


def add_capacity_heatmap(map_obj: folium.Map, capacity_service: CapacityService):
    """Ajoute une heatmap de la capacité disponible."""
    # Vérifier si folium est disponible
    if not FOLIUM_AVAILABLE:
        return
    # Récupérer tous les points de production
    prod_points = capacity_service.get_all_production_points()
    
    # Préparer les données pour la heatmap
    heat_data = []
    for point in prod_points:
        if point.latitude and point.longitude and point.actif:
            # Intensité basée sur la capacité disponible
            intensity = point.capacite_disponible_kwc / 100  # Normaliser
            heat_data.append([point.latitude, point.longitude, intensity])
    
    if heat_data:
        # Créer la heatmap
        plugins.HeatMap(
            heat_data,
            name="🌡️ Heatmap Capacité",
            min_opacity=0.2,
            max_zoom=13,
            radius=25,
            blur=15,
            gradient={
                0.0: 'blue',
                0.5: 'lime',
                0.8: 'yellow', 
                1.0: 'red'
            }
        ).add_to(map_obj)


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcule l'angle de direction entre deux points GPS."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlon = lon2 - lon1
    
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    
    bearing = math.atan2(x, y)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing


def render_map_legend():
    """Affiche la légende de la carte."""
    with st.expander("📋 Légende", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Types de clients:**
            - 🟢 **Vert** : Producteurs
            - 🔵 **Bleu** : Consommateurs  
            - 🟣 **Violet** : Prosumers
            
            **Connexions:**
            - 🟠 **Orange** : Autoconsommation collective
            - Épaisseur = % d'allocation
            """)
            
        with col2:
            st.markdown("""
            **Zones:**
            - ⭕ Cercles : Zone d'influence (2km par défaut)
            - 🌡️ Heatmap : Capacité disponible
            
            **Interactivité:**
            - Cliquer sur un marqueur pour plus d'infos
            - Utiliser les contrôles pour basculer les calques
            """)


def render_map_statistics(client_service: ClientService, capacity_service: CapacityService):
    """Affiche les statistiques de la carte."""
    st.markdown("### 📊 Statistiques de la zone")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Statistiques clients
    stats = client_service.get_statistics()
    
    with col1:
        st.metric(
            "Clients totaux",
            stats['total_clients'],
            f"{stats['clients_actifs']} actifs"
        )
        
    with col2:
        # Capacité totale
        prod_points = capacity_service.get_all_production_points()
        total_capacity = sum(p.capacite_kwc for p in prod_points if p.actif)
        available_capacity = sum(p.capacite_disponible_kwc for p in prod_points if p.actif)
        
        st.metric(
            "Capacité totale",
            f"{total_capacity:.0f} kWc",
            f"{available_capacity:.0f} kWc disponibles"
        )
        
    with col3:
        # Allocations actives
        allocations = capacity_service.get_all_active_allocations()
        total_allocated = sum(a.capacite_allouee_kwc for a in allocations)
        
        st.metric(
            "Allocations actives",
            len(allocations),
            f"{total_allocated:.0f} kWc alloués"
        )
        
    with col4:
        # Distance moyenne
        clients_with_coords = [c for c in client_service.get_all() if c.has_coordinates]
        if len(clients_with_coords) > 1:
            # Calculer la distance moyenne entre clients
            from ..services.geolocation_service import GeolocationService
            geo_service = GeolocationService()
            
            distances = []
            for i in range(len(clients_with_coords)):
                for j in range(i + 1, len(clients_with_coords)):
                    dist = geo_service.calculate_distance(
                        clients_with_coords[i].latitude,
                        clients_with_coords[i].longitude,
                        clients_with_coords[j].latitude,
                        clients_with_coords[j].longitude
                    )
                    distances.append(dist)
            
            avg_distance = sum(distances) / len(distances) if distances else 0
            
            st.metric(
                "Distance moyenne",
                f"{avg_distance:.1f} km",
                "entre clients"
            )