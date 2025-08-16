# Implémentation de la Carte Interactive GPS

## Résumé des changements

### 1. Ajout des dépendances
- Ajouté `streamlit-folium>=0.13.0` dans `requirements.txt`
- `geopy` était déjà présent pour le géocodage

### 2. Module de sélection sur carte (`modules/erp_client/ui/map_selector.py`)

#### Fonctionnalités implémentées :
- **Carte interactive avec Folium** :
  - Vue satellite par défaut (ESRI World Imagery)
  - Vue plan disponible (OpenStreetMap)
  - Contrôle de couches pour basculer entre les vues
  
- **Sélection de coordonnées** :
  - Clic sur la carte pour définir la position
  - Popup affichant latitude/longitude au clic
  - Marqueur rouge pour visualiser la position sélectionnée
  - Persistance des coordonnées dans `st.session_state`

- **Géocodage d'adresse** :
  - Recherche automatique via Nominatim
  - Centrage sur l'adresse trouvée avec zoom élevé (17)
  - Gestion des erreurs de géocodage

### 3. Intégration dans le formulaire client (`modules/erp_client/ui/client_form.py`)

#### Modifications :
- Ajout d'une checkbox "Sélectionner sur carte"
- Gestion des coordonnées via `st.session_state` :
  - `temp_latitude` et `temp_longitude` pour le formulaire
  - `selected_coordinates` pour la carte
- Désactivation des champs de saisie manuelle quand la carte est active
- Nettoyage automatique du session state après validation/annulation

### 4. Tests et documentation

- **Test unitaire** : `tests/test_map_selector.py`
- **Test d'intégration visuel** : `test_map_integration.py`
- **Documentation** : `modules/erp_client/ui/MAP_SELECTOR_README.md`

## Utilisation

1. Dans le formulaire client ERP, aller dans "Informations complémentaires"
2. Cocher "📍 Sélectionner sur carte"
3. Si une adresse est renseignée, cliquer sur "🔍 Localiser l'adresse sur la carte"
4. Cliquer sur la carte pour ajuster précisément la position
5. Les coordonnées GPS sont automatiquement mises à jour

## Points d'amélioration futurs

1. **Recherche intégrée** : Ajouter un champ de recherche directement sur la carte
2. **Validation géographique** : Vérifier que les coordonnées sont en France
3. **Mode hors ligne** : Cache des tuiles pour utilisation sans internet
4. **Import en masse** : Géocoder plusieurs adresses simultanément
5. **Zones de service** : Permettre de dessiner des polygones pour définir des zones

## Commandes de test

```bash
# Activer l'environnement virtuel
venv\Scripts\activate.bat

# Installer les dépendances si nécessaire
pip install streamlit-folium

# Lancer le test visuel
streamlit run test_map_integration.py

# Lancer l'application principale
streamlit run app.py
```

## Architecture technique

La solution utilise :
- **Folium** pour la création de cartes interactives
- **streamlit-folium** pour l'intégration dans Streamlit
- **geopy** pour le géocodage des adresses
- **Session state** pour la persistance des données entre les interactions

Les coordonnées sont stockées en WGS84 (standard GPS) et peuvent être utilisées directement pour les calculs de distance et autres opérations géographiques.