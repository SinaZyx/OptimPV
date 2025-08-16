# 📚 Guide de Maintenance - Widget d'Autocomplétion d'Adresse

## 🎯 Vue d'ensemble

Le widget d'autocomplétion d'adresse est un composant professionnel conçu pour être maintenu facilement dans le temps. Il respecte les contraintes de Streamlit tout en offrant une expérience utilisateur moderne.

## 🏗️ Architecture

### Structure des fichiers
```
modules/erp_client/
├── services/
│   └── address_autocomplete.py          # Service métier (API)
├── ui/
│   └── components/
│       ├── address_autocomplete_widget.py    # Ancienne version (déprécié)
│       └── address_autocomplete_widget_v2.py # Nouvelle version (recommandée)
└── docs/
    └── GUIDE_MAINTENANCE_AUTOCOMPLETE.md    # Ce fichier
```

### Composants principaux

#### 1. **AddressAutocompleteService** (`services/address_autocomplete.py`)
- Gère les appels API vers api-adresse.data.gouv.fr
- Cache les résultats pour optimiser les performances
- Méthodes principales :
  - `search_addresses()` : Recherche d'adresses
  - `reverse_geocode()` : Géocodage inverse
  - `extract_zone_from_postal_code()` : Extraction de zone
  - `parse_zone_from_postcode()` : Parsing de région

#### 2. **AddressAutocompleteWidget** (`ui/components/address_autocomplete_widget_v2.py`)
- Widget UI compatible avec `st.form()`
- Architecture orientée objet pour la maintenabilité
- Classes principales :
  - `AddressFieldType` : Enum des types de champs
  - `AddressData` : Structure de données immutable
  - `AddressAutocompleteWidget` : Widget principal

## 🔧 Guide de modification

### Ajouter un nouveau champ d'adresse

1. Modifier l'enum `AddressFieldType` :
```python
class AddressFieldType(Enum):
    STREET = "street"
    POSTAL_CODE = "postal_code"
    CITY = "city"
    COUNTRY = "country"
    REGION = "region"  # Nouveau champ
    FULL_ADDRESS = "full_address"
```

2. Mettre à jour la dataclass `AddressData` :
```python
@dataclass
class AddressData:
    street: str = ""
    postal_code: str = ""
    city: str = ""
    region: str = ""  # Nouveau champ
    country: str = "France"
    # ...
```

### Modifier l'API d'autocomplétion

Pour changer d'API (ex: Google Places, Mapbox) :

1. Créer un nouveau service dans `services/` :
```python
class GooglePlacesAutocompleteService:
    def search_addresses(self, query: str) -> List[Dict]:
        # Implémentation Google Places
        pass
```

2. Modifier le widget pour accepter différents services :
```python
def __init__(self, service=None):
    self.service = service or AddressAutocompleteService()
```

### Personnaliser l'interface

Modifier la configuration par défaut :
```python
def _get_default_config(self) -> Dict[str, Any]:
    return {
        'min_search_length': 3,      # Caractères min pour recherche
        'max_suggestions': 5,         # Nombre max de suggestions
        'show_coordinates': True,     # Afficher GPS
        'search_delay_ms': 300,       # Délai avant recherche
        # Ajouter vos options ici
    }
```

## 🐛 Résolution des problèmes courants

### Erreur "st.button() can't be used in st.form()"

**Problème** : Utilisation de boutons dans un formulaire Streamlit

**Solution** : Utiliser uniquement :
- `st.form_submit_button()`
- `st.selectbox()`, `st.radio()`, `st.checkbox()`
- Pas de `st.button()` dans les formulaires

### Problème de cache

**Problème** : Résultats obsolètes

**Solution** : Vider le cache
```python
# Dans le service
@st.cache_data(ttl=3600)  # Modifier le TTL si nécessaire
```

### Performance lente

**Problème** : Trop d'appels API

**Solutions** :
1. Augmenter `min_search_length`
2. Augmenter `search_delay_ms`
3. Implémenter un debounce côté client

## 📊 Tests

### Tests unitaires
```bash
python tests/test_erp_client/test_address_autocomplete.py
```

### Tests d'intégration
```bash
python tests/test_erp_client/test_new_features_integration.py
```

### Test manuel
```bash
streamlit run test_address_autocomplete.py
```

## 🔄 Mise à jour des dépendances

### API gouvernementale
- URL : https://api-adresse.data.gouv.fr
- Documentation : https://adresse.data.gouv.fr/api-doc/adresse
- Pas de clé API requise
- Limite : Respect du fair use

### Packages Python
```bash
pip install --upgrade streamlit
pip install --upgrade requests
```

## 📈 Évolutions futures

### Court terme
1. Ajouter un debounce JavaScript
2. Implémenter la sauvegarde des adresses favorites
3. Ajouter la validation d'adresse postale

### Moyen terme
1. Support multi-pays
2. Intégration avec d'autres APIs (Google, Mapbox)
3. Mode hors ligne avec base locale

### Long terme
1. IA pour correction d'adresses
2. Prédiction basée sur l'historique
3. Intégration avec services de livraison

## 🚨 Points d'attention

1. **Compatibilité Streamlit** : Toujours tester dans un `st.form()`
2. **RGPD** : Les adresses sont des données personnelles
3. **Performance** : Surveiller le nombre d'appels API
4. **Accessibilité** : Maintenir les labels et aides contextuelles

## 📞 Support

- Documentation Streamlit : https://docs.streamlit.io
- API Adresse : https://adresse.data.gouv.fr/api-doc
- Issues : Créer un ticket dans le système de tracking

---

*Dernière mise à jour : 12/07/2025*  
*Version : 2.0.0*