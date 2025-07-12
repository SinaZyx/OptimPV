# Intégration Cartographique du Module ERP

## Vue d'ensemble

Le module ERP s'intègre parfaitement avec le module de cartographie de prospection d'OptimPV pour offrir une visualisation géographique complète des clients.

## Fonctionnalités

### 1. Affichage des clients ERP sur la carte

- **Marqueurs colorés** selon le type de client :
  - 🟢 **Vert** : Producteurs d'énergie
  - 🔴 **Rouge** : Consommateurs d'énergie
  - 🔵 **Bleu** : Prosumers (producteurs-consommateurs)

- **Infobulles détaillées** au survol :
  - Nom du client
  - Type et code client
  - Adresse complète
  - Zone géographique
  - Prix €/kWh actif

### 2. Filtrage et options d'affichage

- **Sélection par type** : Afficher/masquer producteurs, consommateurs, prosumers
- **Zones de 2km** : Visualiser les périmètres d'autoconsommation collective
- **Intégration transparente** : Les clients ERP s'affichent avec les données Enedis

## Utilisation

### Depuis le module ERP

1. Naviguer vers **ERP Clients** → **Cartographie**
2. Cocher **"Afficher les clients ERP"**
3. Sélectionner les types de clients à afficher
4. La carte se met à jour automatiquement

### Depuis la carte de prospection

Les clients ERP s'affichent automatiquement si :
- Des clients ont des coordonnées GPS
- L'option d'affichage est activée dans le module ERP

## Géolocalisation des clients

### Méthodes disponibles

1. **Saisie manuelle** : Dans le formulaire client
2. **Géocodage automatique** : Basé sur l'adresse
3. **Import en masse** : Via fichier Excel avec colonnes latitude/longitude

### Géocodage d'adresse

Le système utilise Nominatim (OpenStreetMap) pour :
- Convertir les adresses en coordonnées GPS
- Vérifier la cohérence des localisations
- Proposer des corrections si nécessaire

## Cas d'usage

### 1. Planification d'autoconsommation collective

- Identifier les producteurs et consommateurs dans un rayon de 2km
- Optimiser les allocations d'énergie
- Visualiser les flux potentiels

### 2. Prospection commerciale

- Repérer les zones à fort potentiel
- Identifier les clusters de clients
- Planifier les visites commerciales

### 3. Analyse géographique

- Étudier la répartition par zone
- Analyser la densité de clients
- Optimiser les tarifs par secteur

## API et intégration technique

### Structure des données

```python
# Format des marqueurs ERP pour la carte
{
    'id': int,
    'code_client': str,
    'nom': str,
    'type_client': str,
    'latitude': float,
    'longitude': float,
    'adresse': str,
    'ville': str,
    'zone_geographique': str,
    'prix_kwh': float,
    'color': [R, G, B, A],  # Couleur RGBA
    'tooltip': str  # HTML pour l'infobulle
}
```

### Session State

Les données sont partagées via Streamlit session state :
- `st.session_state['erp_client_markers']` : DataFrame des clients à afficher
- `st.session_state['show_erp_clients']` : Boolean d'activation

## Performance

### Optimisations

- **Chargement à la demande** : Seuls les clients avec coordonnées sont transmis
- **Clustering intelligent** : Regroupement automatique si trop de points
- **Cache des géolocalisations** : Évite les requêtes répétées

### Limites recommandées

- Maximum 1000 clients simultanés pour une performance optimale
- Rafraîchissement automatique désactivé au-delà de 500 points
- Utilisation du mode "zones" pour plus de 2000 clients

## Développements futurs

### Court terme
- Export KML/GeoJSON des clients
- Heatmap de densité
- Calcul automatique des distances

### Moyen terme
- Simulation de flux énergétiques
- Optimisation des périmètres
- Intégration temps réel

### Long terme
- Prédiction des besoins par zone
- IA pour suggestions d'implantation
- Jumelage automatique producteur/consommateur