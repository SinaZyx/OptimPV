# Documentation - Autocomplétion d'Adresse

## Vue d'ensemble

La fonctionnalité d'autocomplétion d'adresse permet aux utilisateurs de saisir rapidement et précisément des adresses françaises dans les formulaires de l'application OptimPV. Elle utilise l'API officielle du gouvernement français pour garantir des données fiables et à jour.

## Caractéristiques

### 🚀 Fonctionnalités principales

- **Autocomplétion en temps réel** : Suggestions après 3 caractères tapés
- **Remplissage automatique** : Code postal, ville et coordonnées GPS
- **Zone géographique** : Détection automatique selon le code postal
- **Score de pertinence** : Les résultats sont triés par pertinence
- **Cache intelligent** : Mise en cache des résultats pour de meilleures performances

### 🔧 Caractéristiques techniques

- **API gratuite** : Aucune clé API requise
- **Sans limite** : Pas de quota d'utilisation
- **Données officielles** : Base Adresse Nationale (BAN)
- **Temps de réponse** : < 500ms en moyenne
- **Disponibilité** : 99.9% de disponibilité

## Utilisation

### Dans le formulaire client

1. **Commencer à taper** : L'utilisateur tape au moins 3 caractères dans le champ de recherche
2. **Sélectionner** : Choisir parmi les suggestions proposées
3. **Validation automatique** : Les champs sont remplis automatiquement :
   - Adresse
   - Code postal
   - Ville
   - Coordonnées GPS (latitude/longitude)
   - Zone géographique

### Widget d'autocomplétion

```python
from modules.erp_client.ui.components.address_autocomplete_widget import render_address_autocomplete

# Utilisation basique
adresse, code_postal, ville, lat, lon = render_address_autocomplete(
    key_prefix="mon_formulaire",
    initial_address="10 rue de la Paix",
    initial_postcode="75002",
    initial_city="Paris"
)

# Avec callback
def on_selection(suggestion):
    st.success(f"Adresse sélectionnée: {suggestion.display_label}")

adresse, cp, ville, lat, lon = render_address_autocomplete(
    key_prefix="form",
    on_address_selected=on_selection
)
```

### Service d'autocomplétion

```python
from modules.erp_client.services.address_autocomplete import get_address_service

service = get_address_service()

# Recherche d'adresses
suggestions = service.search_addresses("10 rue de la paix paris", limit=5)

# Géocodage inverse
address = service.get_address_details(latitude=48.8566, longitude=2.3522)

# Zone depuis code postal
zone = service.parse_zone_from_postcode("75001")  # → "Île-de-France"
```

## API Utilisée

### api-adresse.data.gouv.fr

L'API Adresse est le point d'accès unique et officiel aux adresses françaises. Elle est :

- **Maintenue par** : Etalab et la Direction Interministérielle du Numérique
- **Source des données** : Base Adresse Nationale (BAN)
- **Mise à jour** : Quotidienne
- **Documentation** : https://adresse.data.gouv.fr/api-doc/adresse

### Endpoints utilisés

1. **Recherche** : `/search/`
   - Paramètres : `q` (requête), `limit`, `type=housenumber`
   - Retourne : Liste de suggestions avec scores

2. **Géocodage inverse** : `/reverse/`
   - Paramètres : `lat`, `lon`
   - Retourne : Adresse la plus proche

## Zones géographiques

Le système détecte automatiquement la zone géographique basée sur le département :

- **Île-de-France** : 75, 77, 78, 91, 92, 93, 94, 95
- **PACA** : 04, 05, 06, 13, 83, 84
- **Occitanie** : 09, 11, 12, 30, 31, 32, 34, 46, 48, 65, 66, 81, 82
- **Auvergne-Rhône-Alpes** : 01, 03, 07, 15, 26, 38, 42, 43, 63, 69, 73, 74
- **Nouvelle-Aquitaine** : 16, 17, 19, 23, 24, 33, 40, 47, 64, 79, 86, 87
- Etc.

## Performances

- **Cache Streamlit** : 1 heure (3600 secondes)
- **Timeout API** : 5 secondes
- **Requêtes parallèles** : Supportées
- **Taille moyenne réponse** : < 5 KB

## Gestion des erreurs

Le système gère gracieusement :

- **Timeout réseau** : Retour liste vide
- **API indisponible** : Message d'erreur utilisateur
- **Pas de résultats** : Message informatif
- **Erreurs de parsing** : Logs détaillés

## Tests

Pour tester la fonctionnalité :

```bash
streamlit run test_address_autocomplete.py
```

## Améliorations futures possibles

1. **Filtrage par région** : Limiter les résultats à une région spécifique
2. **Historique** : Sauvegarder les adresses récemment utilisées
3. **Validation postale** : Vérifier la validité de l'adresse
4. **Intégration carte** : Afficher les suggestions sur une carte
5. **Export** : Exporter les adresses au format standardisé