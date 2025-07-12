# Module de Stockage OptimPV - Version 2.0

## 📁 Architecture Modulaire

Le module de stockage a été refactorisé en 6 modules spécialisés pour une meilleure organisation et maintenabilité :

### 🏗️ Structure des Modules

```
modules/storage/
├── __init__.py              # Point d'entrée principal
├── core.py                  # Classe principale StorageModule
├── project_manager.py       # Gestion complète des projets
├── comparison.py            # Comparaison avancée entre projets
├── data_utils.py           # Utilitaires de données et validation
├── ui_components.py        # Composants d'interface utilisateur
├── visualization.py        # Graphiques et visualisations
├── migration.py            # Aide à la migration
└── README.md              # Cette documentation
```

## 🚀 Usage

### Import Principal
```python
from modules.storage import StorageModule

# Créer une instance
storage = StorageModule()

# Afficher l'interface
storage.show_ui()
```

### Import de Modules Spécifiques
```python
# Pour les fonctionnalités avancées
from modules.storage.project_manager import ProjectManager
from modules.storage.comparison import ProjectComparison
from modules.storage.visualization import ComparisonVisualization
```

## 📋 Fonctionnalités par Module

### 🏗️ Core (`core.py`)
- Classe principale `StorageModule`
- Initialisation du système
- Orchestration des autres modules
- Méthodes déléguées pour compatibilité

### 📁 Project Manager (`project_manager.py`)
- ✅ Sauvegarde de projets avec validation
- 📥 Chargement avec vérification d'intégrité
- 🗑️ Suppression sécurisée
- 📤 Export/Import au format ZIP
- 📋 Duplication de projets
- 🔐 Génération de checksums
- 📝 README automatique

### ⚖️ Comparison (`comparison.py`)
- 🔍 Comparaison avancée entre projets
- 📊 Analyse des différences de configuration
- 💰 Comparaison des performances économiques
- ⚡ Analyse des résultats d'optimisation
- 🎯 Seuils intelligents de comparaison

### 🛠️ Data Utils (`data_utils.py`)
- 📊 Calcul de scores de complétude
- ✅ Validation de données
- 🔄 Sérialisation JSON avancée
- 📏 Calcul de tailles de données
- 🔍 Détection de modules actifs

### 🖥️ UI Components (`ui_components.py`)
- 🎨 Interface utilisateur principale
- 🔍 Filtres et recherche
- 📋 Cartes de projets
- 💾 Dialogues de sauvegarde
- ⭐ Gestion des favoris

### 📈 Visualization (`visualization.py`)
- 🎯 Graphiques radar de comparaison
- 📊 Tableaux de comparaison détaillés
- 📈 Courbes d'optimisation
- 🎲 Distributions Monte Carlo
- 💰 Flux financiers mensuels

## 🔄 Migration

### Depuis l'Ancienne Version
L'ancien fichier `storage.py` (2326 lignes) a été automatiquement sauvegardé dans `storage_backup.py`.

### Compatibilité Descendante
```python
# ✅ Fonctionne toujours
from modules.storage import StorageModule
storage = StorageModule()

# ⚠️ Déprécié mais supporté
import modules.storage as storage
storage.show_storage_ui()
```

## 📊 Améliorations de Performance

### Avant (Monolithique)
- 📄 1 fichier de 2326 lignes
- 🐌 Chargement complet à chaque import
- 🔄 Difficile à maintenir
- 🧪 Tests complexes

### Après (Modulaire)
- 📁 6 modules spécialisés
- ⚡ Chargement à la demande
- 🛠️ Maintenance facilitée
- 🧪 Tests unitaires par module
- 📦 Réutilisabilité améliorée

## 🎯 Fonctionnalités Clés

### 💾 Sauvegarde Avancée
- Capture complète du `session_state`
- Validation automatique des données
- Génération de checksums d'intégrité
- Sauvegarde des visualisations
- Métriques de complétude et qualité

### 🔍 Comparaison Intelligente
- Seuils spécifiques par paramètre (CAPEX: 1000€, puissance: 0.1kWc)
- Analyse automatique des différences
- Graphiques de comparaison interactifs
- Conclusion automatique

### 📊 Interface Moderne
- Cartes de projets visuelles
- Filtres et recherche avancés
- Mode comparaison interactif
- Gestion des favoris
- Statistiques en temps réel

## 🔧 Configuration

### Variables d'Environnement
```bash
# Désactiver les messages de migration
export STORAGE_MIGRATION_SHOWN=1
```

### Paramètres par Défaut
```python
# Seuils de comparaison (data_utils.py)
tolerance_map = {
    'capex_scenario': 1000,      # 1000€ pour CAPEX
    'puissance_kwc_installee': 0.1,  # 0.1 kWc pour puissance
    'prix_revente': 0.001,       # 0.001€/kWh pour prix
    # ...
}
```

## 📝 Développement

### Ajouter une Nouvelle Fonctionnalité
1. Identifier le module approprié
2. Ajouter la méthode dans le module
3. Exposer via `core.py` si nécessaire
4. Mettre à jour `__init__.py`
5. Documenter dans ce README

### Tests
```bash
# Tester un module spécifique
python -m pytest tests/storage/test_project_manager.py

# Tester toute la suite
python -m pytest tests/storage/
```

## 🐛 Dépannage

### Import Errors
```python
# ❌ Erreur commune
from storage import StorageModule  # Module non trouvé

# ✅ Correct
from modules.storage import StorageModule
```

### Migration Issues
Si vous rencontrez des problèmes avec l'ancienne version :
1. Vérifiez que `storage_backup.py` existe
2. Utilisez les nouveaux imports
3. Contactez l'équipe si problème persistant

## 📈 Versions

- **v1.0** : Fichier monolithique `storage.py`
- **v2.0** : Architecture modulaire refactorisée
- **v2.1** : Améliorations de performance (à venir)

## 🤝 Contribution

Pour contribuer au module de stockage :
1. Respecter l'architecture modulaire
2. Ajouter des tests pour toute nouvelle fonctionnalité
3. Documenter les changements
4. Suivre les conventions de nommage existantes

---

*Documentation générée automatiquement - OptimPV Storage Module v2.0*