# Tests du Module ERP Client

Ce répertoire contient tous les tests unitaires et d'intégration pour le module ERP Client d'OptimPV.

## Structure des Tests

```
test_erp_client/
├── __init__.py                 # Package de tests
├── test_database.py           # Tests de la base de données
├── test_models.py             # Tests des modèles de données
├── test_services.py           # Tests des services métier
├── test_ui_integration.py     # Tests d'intégration UI
├── test_module_integration.py # Tests d'intégration avec autres modules
├── test_end_to_end.py        # Test de scénario complet
├── run_all_tests.py          # Script pour exécuter tous les tests
└── README.md                 # Ce fichier
```

## Description des Tests

### 1. Tests de Base de Données (`test_database.py`)
- Initialisation et création des tables
- Opérations CRUD sur toutes les tables
- Contraintes et intégrité référentielle
- Transactions et rollback
- Sauvegarde et restauration

### 2. Tests des Modèles (`test_models.py`)
- **Client** : Validation, conversions, métadonnées
- **PrixClient** : Calculs de prix, validations de dates
- **Autoconsommation** : Points de production/consommation, allocations

### 3. Tests des Services (`test_services.py`)
- **ClientService** : CRUD, recherche, statistiques
- **PricingService** : Gestion des tarifs, projections
- **CapacityService** : Allocations, alertes, optimisations
- **GeolocationService** : Géocodage, calcul de distances

### 4. Tests d'Intégration UI (`test_ui_integration.py`)
- Interface Streamlit principale
- Formulaires de création/édition
- Tableaux de bord et visualisations
- Export de données

### 5. Tests d'Intégration Modules (`test_module_integration.py`)
- **Facturation** : Synchronisation bidirectionnelle
- **Cartographie** : Affichage des clients et opérations
- **Analyses Financières** : Projections et ROI

### 6. Test de Bout en Bout (`test_end_to_end.py`)
Scénario complet simulant :
- Création de 5 clients (producteur, consommateurs, prosumer)
- Configuration des tarifs
- Création d'infrastructures (1150 kWc total)
- Allocations d'autoconsommation
- Analyses financières et optimisations

## Exécution des Tests

### Tous les tests
```bash
python tests/test_erp_client/run_all_tests.py
```

### Par catégorie
```bash
# Tests unitaires uniquement
python tests/test_erp_client/run_all_tests.py unit

# Tests d'intégration
python tests/test_erp_client/run_all_tests.py integration

# Test end-to-end
python tests/test_erp_client/run_all_tests.py e2e

# Tests rapides
python tests/test_erp_client/run_all_tests.py quick
```

### Test individuel
```bash
# Avec pytest directement
pytest tests/test_erp_client/test_models.py -v

# Test spécifique
pytest tests/test_erp_client/test_services.py::TestClientService::test_create_client -v
```

## Couverture de Code

Pour générer un rapport de couverture :

```bash
# Installer coverage
pip install coverage

# Exécuter avec couverture
coverage run -m pytest tests/test_erp_client/
coverage report
coverage html  # Génère un rapport HTML dans htmlcov/
```

## Fixtures et Mocks

### Fixtures communes
- `temp_db_dir` : Répertoire temporaire pour les BDD de test
- `db` : Instance ERPDatabase de test
- `client_service`, `pricing_service`, `capacity_service` : Services configurés

### Mocks utilisés
- Connexions base de données externes (billing.db)
- Géolocalisation (geopy)
- Interface Streamlit (pour tests UI)

## Données de Test

Les tests utilisent des données réalistes :
- Clients dans la région de Nice
- Tarifs entre 0.12€ et 0.18€/kWh
- Capacités de production de 100 à 500 kWc
- Consommations annuelles de 50 à 300 MWh

## Assertions Principales

1. **Intégrité des données** : Toutes les contraintes DB respectées
2. **Logique métier** : Calculs corrects (prix, allocations, projections)
3. **Intégration** : Communication correcte entre modules
4. **Performance** : Tests complétés en < 30 secondes

## Maintenance

- Ajouter des tests pour toute nouvelle fonctionnalité
- Maintenir la couverture > 80%
- Documenter les cas de test complexes
- Utiliser des noms de test descriptifs

## Dépendances de Test

```
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
```

## Résultats Attendus

Tous les tests doivent passer avec :
- 0 erreurs
- 0 échecs
- Temps total < 30 secondes
- Couverture > 80%