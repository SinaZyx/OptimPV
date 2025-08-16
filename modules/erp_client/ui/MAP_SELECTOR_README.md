# Module de Sélection GPS sur Carte

## Vue d'ensemble

Le module `map_selector.py` fournit une interface interactive permettant aux utilisateurs de sélectionner précisément les coordonnées GPS d'un client en cliquant sur une carte.

## Fonctionnalités

### 1. Sélection Interactive
- **Clic sur carte** : L'utilisateur peut cliquer directement sur la carte pour définir la position
- **Vue satellite** : Affichage par défaut en vue satellite pour mieux identifier les bâtiments
- **Vue plan** : Possibilité de basculer en vue plan (OpenStreetMap)
- **Zoom précis** : Zoom élevé (17) après géocodage pour une sélection précise

### 2. Géocodage Automatique
- Recherche automatique de l'adresse via Nominatim (OpenStreetMap)
- Centrage automatique sur l'adresse trouvée
- Gestion des erreurs de géocodage

### 3. Persistance des Données
- Stockage des coordonnées sélectionnées dans `st.session_state`
- Conservation des valeurs entre les interactions
- Nettoyage automatique après validation/annulation

## Utilisation

### Dans le formulaire client

```python
from .map_selector import render_geocoding_assistant

# Dans le formulaire
if use_map:
    lat, lon = render_geocoding_assistant({
        'adresse': adresse,
        'code_postal': code_postal,
        'ville': ville
    })
```

### Sélecteur simple

```python
from .map_selector import render_coordinate_selector

lat, lon = render_coordinate_selector(
    initial_lat=43.60,
    initial_lon=7.06,
    zoom_start=13
)
```

## Architecture Technique

### Dépendances
- `folium` : Création de cartes interactives
- `streamlit-folium` : Intégration Folium dans Streamlit
- `geopy` : Géocodage des adresses

### Session State
Le module utilise les clés suivantes dans `st.session_state` :
- `selected_coordinates` : Stockage des coordonnées sélectionnées sur la carte
- `temp_latitude` : Latitude temporaire dans le formulaire
- `temp_longitude` : Longitude temporaire dans le formulaire

### Tuiles de Carte
- **Satellite** : ESRI World Imagery (par défaut)
- **Plan** : OpenStreetMap

## Améliorations Futures

1. **Recherche d'adresse intégrée** : Ajouter un champ de recherche directement sur la carte
2. **Polygones de zones** : Permettre de dessiner des zones de service
3. **Import en masse** : Géocoder plusieurs adresses simultanément
4. **Validation des coordonnées** : Vérifier que les coordonnées sont en France
5. **Mode hors ligne** : Cache local des tuiles pour utilisation sans internet

## Tests

Pour tester le module :
```bash
# Test unitaire
python tests/test_map_selector.py

# Test d'intégration visuel
streamlit run test_map_integration.py
```

## Notes de Sécurité

- Les coordonnées GPS sont des données sensibles
- Le géocodage utilise un service externe (Nominatim)
- Respecter les limites de taux de Nominatim (1 requête/seconde)