# 🏢 Module ERP Client - OptimPV

## 📋 Vue d'ensemble

Le module ERP Client est une solution complète de gestion commerciale intégrée à OptimPV, spécialisée dans la gestion des clients producteurs et consommateurs d'énergie solaire.

## 🎯 Fonctionnalités principales

### 👥 Gestion des clients
- **Création et modification** de fiches clients complètes
- **Types de clients** : Producteurs, Consommateurs, Prosumers
- **Géolocalisation** automatique et manuelle
- **Zones géographiques** personnalisables
- **Historique complet** des modifications

### 💰 Gestion tarifaire
- **Prix personnalisés** par client et période
- **Types de tarifs** : Fixe, Indexé, Dynamique
- **Projections** avec inflation et évolutions
- **Comparaisons** avec tarifs de référence (EDF)
- **Remises** et formules de calcul avancées

### ⚡ Gestion des capacités
- **Capacités de production** par point
- **Allocation** aux clients consommateurs
- **Autoconsommation collective** avec connexions
- **Calculs** de disponibilité et répartition

### 🗺️ Cartographie interactive
- **Visualisation** des clients sur carte
- **Zones d'influence** configurables (2km par défaut)
- **Connexions** d'autoconsommation collective
- **Heatmap** des capacités disponibles

### 📊 Reporting et analyses
- **Tableaux de bord** professionnels
- **KPIs commerciaux** en temps réel
- **Statistiques** clients et prix
- **Exports** et rapports détaillés

## 🏗️ Architecture technique

### Structure des dossiers
```
modules/erp_client/
├── README.md                    # Ce fichier
├── __init__.py                  # Point d'entrée du module
├── database/                    # Couche base de données
│   ├── erp_database.py         # Gestionnaire principal BDD
│   ├── migrations.py           # Migrations de schéma
│   └── schema.sql              # Schéma initial
├── models/                      # Modèles de données
│   ├── client.py               # Modèle Client + TypeClient
│   └── pricing.py              # Modèle Prix + TypeTarif
├── services/                    # Logique métier
│   ├── client_service.py       # Service gestion clients
│   ├── pricing_service.py      # Service gestion prix
│   ├── capacity_service.py     # Service gestion capacités
│   └── inflation_service.py    # Service calculs inflation
├── ui/                         # Interface utilisateur Streamlit
│   ├── main_interface.py       # Interface principale
│   ├── client_form.py          # Formulaires clients
│   ├── client_list.py          # Listes clients basiques
│   ├── client_list_pro.py      # Listes professionnelles
│   ├── client_map.py           # Carte interactive
│   ├── pricing_dashboard.py    # Tableau de bord prix
│   └── capacity_dashboard.py   # Tableau de bord capacités
└── integration/                # Intégrations externes
    ├── core_analyzer_hook.py   # Hook analyseur principal
    └── analysis_connector.py   # Connecteur analyses
```

### Technologies utilisées
- **Backend** : Python 3.8+, SQLite
- **Frontend** : Streamlit
- **Cartographie** : Folium, Pydeck
- **Visualisation** : Plotly, Pandas
- **Géolocalisation** : Geopy

## 🚀 Installation et configuration

### 1. Dépendances requises
```bash
# Dépendances principales (incluses dans requirements.txt)
pip install streamlit pandas plotly folium geopy bcrypt

# Optionnelles pour fonctionnalités avancées
pip install pyproj shapely aiohttp
```

### 2. Initialisation de la base de données
La base de données SQLite est automatiquement créée au premier démarrage dans :
- `data/erp_client.db` (par défaut)
- Configuration personnalisée possible via paramètres

### 3. Configuration des services
```python
# Exemple d'utilisation
from modules.erp_client import ERPClientModule

# Initialisation avec base par défaut
erp = ERPClientModule()

# Ou avec base personnalisée
erp = ERPClientModule(db_path="custom/path/erp.db")
```

## 🔧 Résolution des problèmes courants

### Erreur `ModuleNotFoundError: No module named 'folium'`
```bash
# Solution
pip install folium
```

### Erreur `AttributeError: 'TypeClient' object has no attribute 'capitalize'`
- **Cause** : Utilisation incorrecte des Enum
- **Solution** : Utiliser `.value.capitalize()` au lieu de `.capitalize()`
- ✅ **Corrigé** dans cette version

### Erreur `'PricingService' object has no attribute 'get_average_price'`
- **Cause** : Échec d'import du module (souvent lié à folium)
- **Solution** : Vérifier les dépendances et redémarrer Streamlit
- ✅ **Corrigé** dans cette version

### Problèmes de cache Python
```bash
# Nettoyage du cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
```

## 🗄️ Base de données

### Tables principales
- **`clients`** : Informations clients complètes
- **`prix_clients`** : Historique des prix par client
- **`points_production`** : Points de production d'énergie
- **`points_consommation`** : Points de consommation
- **`autoconso_collective`** : Relations producteur-consommateur
- **`zones_geographiques`** : Définition des zones

### Migrations
Le système de migration automatique gère l'évolution du schéma :
- **Migration #1** : Schéma initial
- **Migration #2** : Ajout métadonnées clients
- **Migration #3** : Gestion des zones géographiques
- **Migration #4** : Autoconsommation collective
- **Migration #5** : Colonne `actif` pour prix

## 🎨 Interface utilisateur

### Onglets disponibles
1. **📋 Clients** : Gestion et liste des clients
2. **💰 Prix** : Tableau de bord tarifaire
3. **⚡ Capacités** : Gestion des productions/consommations
4. **🗺️ Carte** : Visualisation géographique
5. **📊 Reporting** : Analyses et statistiques

### Fonctionnalités UX
- **Recherche avancée** avec filtres multiples
- **Visualisations interactives** avec Plotly
- **Export de données** en Excel/CSV
- **Interface responsive** adaptée aux écrans
- **Notifications** et messages d'état

## 🔐 Sécurité et performance

### Sécurité
- **Validation** des données d'entrée
- **Paramètres préparés** pour les requêtes SQL
- **Gestion des erreurs** robuste
- **Logs** des opérations critiques

### Performance
- **Cache** des requêtes fréquentes
- **Pagination** des listes importantes
- **Chargement asynchrone** des données
- **Optimisation** des requêtes SQL

## 📈 Évolutions futures

### Fonctionnalités prévues
- **API REST** pour intégrations externes
- **Import/Export** massif de clients
- **Facturation automatique** 
- **Tableau de bord mobile**
- **Intégration comptable** (Sage, Cegid)

### Améliorations techniques
- **Base PostgreSQL** pour gros volumes
- **Tests automatisés** complets
- **Documentation API** avec Swagger
- **Monitoring** et métriques avancées

## 🤝 Contribution

### Structure des commits
```
type(scope): description

Exemples :
feat(client): ajout recherche avancée
fix(pricing): correction calcul prix moyen
docs(readme): mise à jour installation
```

### Tests
```bash
# Lancement des tests
pytest tests/erp_client/

# Tests spécifiques
pytest tests/erp_client/test_services.py
```

## 📞 Support

Pour tout problème ou question :
1. **Vérifier** ce README et la documentation
2. **Consulter** les logs d'erreur dans `logs/`
3. **Tester** avec un cache Python propre
4. **Redémarrer** Streamlit complètement

---

*Module ERP Client - Version 2.0 - OptimPV*
*Dernière mise à jour : 11 juillet 2025*