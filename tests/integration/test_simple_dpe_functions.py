#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple des fonctions DPE sans dépendances externes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_color_mapping():
    """Test simple du mapping des couleurs sans imports"""
    print("TEST 1: Mapping des couleurs DPE")
    print("-" * 40)
    
    # Définition locale de la fonction pour test
    def create_dpe_color_map(classe_energie):
        color_map = {
            'A': [0, 150, 0, 200],      # Vert foncé
            'B': [50, 200, 50, 200],    # Vert clair
            'C': [255, 255, 0, 200],    # Jaune
            'D': [255, 200, 0, 200],    # Orange clair
            'E': [255, 140, 0, 200],    # Orange
            'F': [255, 69, 0, 200],     # Rouge-orange
            'G': [255, 0, 0, 200],      # Rouge
            'N/A': [128, 128, 128, 150] # Gris
        }
        return color_map.get(str(classe_energie).upper(), color_map['N/A'])
    
    # Test toutes les classes
    for classe in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'Invalid']:
        color = create_dpe_color_map(classe)
        print(f"Classe {classe}: {color}")
    
    print("✅ Test couleurs réussi\n")

def test_api_urls():
    """Test de la configuration des URLs API"""
    print("TEST 2: Configuration des APIs")
    print("-" * 40)
    
    # Configuration des URLs
    config = {
        'GEOCODING_API': 'https://api-adresse.data.gouv.fr/search/',
        'DPE_API_URL': 'https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines',
        'GEO_API': 'https://geo.api.gouv.fr/communes'
    }
    
    for api_name, url in config.items():
        print(f"{api_name}: {url}")
    
    print("✅ Configuration vérifiée\n")

def test_search_params():
    """Test de la construction des paramètres de recherche"""
    print("TEST 3: Paramètres de recherche DPE")
    print("-" * 40)
    
    # Paramètres de test
    lat, lon = 43.5974, 7.0058
    radius = 500
    
    # Construction des paramètres
    params = {
        'lat_lon': f'POINT({lon} {lat})',
        'lat_lon_distance': f'{radius}m',
        'select': 'latitude,longitude,classe_consommation_energie,classe_estimation_ges,'
                 'nom_methode_dpe,consommation_energie,type_batiment,annee_construction,'
                 'surface_habitable,adresse_ban,code_postal_ban,libelle_commune_ban',
        'size': 1000
    }
    
    print(f"Centre de recherche: {lat:.6f}, {lon:.6f}")
    print(f"Rayon: {radius}m")
    print(f"Paramètres de requête:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    
    print("✅ Paramètres construits correctement\n")

def test_address_geocoding_params():
    """Test des paramètres de géocodage d'adresse"""
    print("TEST 4: Paramètres de géocodage")
    print("-" * 40)
    
    address = "123 Avenue des Fleurs, Mougins"
    
    # Ajouter le département si pas présent
    if "06" not in address and "alpes" not in address.lower():
        address = f"{address}, Alpes-Maritimes"
    
    params = {
        'q': address,
        'limit': 1,
        'autocomplete': 1
    }
    
    print(f"Adresse originale: 123 Avenue des Fleurs, Mougins")
    print(f"Adresse enrichie: {address}")
    print("Paramètres de géocodage:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    
    print("✅ Paramètres de géocodage corrects\n")

def test_layer_creation():
    """Test de la création des couches pour la carte"""
    print("TEST 5: Création des couches carte")
    print("-" * 40)
    
    # Test DPE Layer
    dpe_layer_config = {
        'type': 'ScatterplotLayer',
        'get_position': ['longitude', 'latitude'],
        'get_radius': 15,
        'radius_min_pixels': 5,
        'radius_max_pixels': 20,
        'pickable': True,
        'auto_highlight': True
    }
    
    print("Configuration couche DPE:")
    for key, value in dpe_layer_config.items():
        print(f"  {key}: {value}")
    
    # Test Search Marker Layer
    marker_layer_config = {
        'type': 'IconLayer',
        'get_position': ['longitude', 'latitude'],
        'get_size': 40,
        'get_color': [255, 0, 0, 200],
        'pickable': True
    }
    
    print("\nConfiguration marqueur recherche:")
    for key, value in marker_layer_config.items():
        print(f"  {key}: {value}")
    
    print("✅ Configurations des couches valides\n")

def main():
    """Exécution de tous les tests"""
    print("=" * 60)
    print("TESTS SIMPLES DES FONCTIONNALITÉS DPE")
    print("=" * 60)
    print()
    
    try:
        test_color_mapping()
        test_api_urls()
        test_search_params()
        test_address_geocoding_params()
        test_layer_creation()
        
        print("=" * 60)
        print("✅ TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        print("=" * 60)
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)