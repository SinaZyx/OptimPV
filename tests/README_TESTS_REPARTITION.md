# Tests du Module de Répartition des Clés

## Vue d'ensemble

Ce dossier contient une suite complète de tests pour le module de gestion des clés de répartition. Les tests sont organisés en 5 catégories principales pour assurer une couverture complète du système.

## Structure des tests

### 1. Tests des modèles de données (`test_repartition_models.py`)
- **Objectif** : Valider les structures de données de base
- **Tests inclus** :
  - Création et validation des clés de répartition
  - Gestion des périodes temporelles
  - Règles dynamiques et conditions
  - Sérialisation/désérialisation
  - Templates de répartition

### 2. Tests des validateurs (`test_repartition_validators.py`)
- **Objectif** : Vérifier la logique de validation
- **Tests inclus** :
  - Validation de la somme des clés (= 100%)
  - Vérification des valeurs individuelles
  - Couverture des sites
  - Cohérence temporelle
  - Ratio consommation/allocation

### 3. Tests des calculs (`test_repartition_calculations.py`)
- **Objectif** : Valider les algorithmes de calcul
- **Tests inclus** :
  - Application des clés statiques
  - Gestion des clés temporelles
  - Règles dynamiques (priorités, seuils, horaires)
  - Optimisation de la répartition
  - Calcul des métriques

### 4. Tests du gestionnaire principal (`test_repartition_manager.py`)
- **Objectif** : Tester le composant central
- **Tests inclus** :
  - Initialisation et configuration
  - Gestion des clés et validation
  - Templates et optimisation
  - Import/export de configuration
  - Gestion de l'historique
  - Mise à jour dynamique des sites
  - Cas limites et erreurs

### 5. Tests d'intégration (`test_repartition_integration.py`)
- **Objectif** : Valider le système complet
- **Scénarios testés** :
  - Scénario 1 : Répartition statique sur une année
  - Scénario 2 : Optimisation basée sur la consommation
  - Scénario 3 : Variations saisonnières
  - Scénario 4 : Règles dynamiques avec priorités
  - Scénario 5 : Workflow complet avec stockage
  - Scénario 6 : Validation et gestion d'erreurs

## Exécution des tests

### Prérequis
```bash
# Installer les dépendances
pip install -r requirements.txt
```

### Exécuter tous les tests
```bash
# Depuis le dossier racine du projet
python tests/run_all_repartition_tests.py
```

### Exécuter une catégorie spécifique
```bash
# Tests des modèles uniquement
python tests/run_all_repartition_tests.py models

# Tests des validateurs
python tests/run_all_repartition_tests.py validators

# Tests des calculs
python tests/run_all_repartition_tests.py calculations

# Tests du manager
python tests/run_all_repartition_tests.py manager

# Tests d'intégration
python tests/run_all_repartition_tests.py integration
```

### Exécuter un fichier de test individuel
```bash
# Exemple pour les tests de modèles
python -m unittest tests.test_repartition_models -v
```

## Couverture des tests

Les tests couvrent :
- ✅ Création et validation des structures de données
- ✅ Logique de validation complète
- ✅ Algorithmes de calcul et optimisation
- ✅ Gestion d'état et persistance
- ✅ Cas d'usage réels et workflows complets
- ✅ Gestion des erreurs et cas limites

## Structure des données de test

Les tests utilisent des configurations réalistes :
- **4 sites** avec profils différents :
  - Résidentiel (consommation matin/soir)
  - PME (consommation heures bureau)
  - Commerce (8h-20h)
  - École (jours ouvrés, fermée été)
- **Production solaire** avec variations journalières et saisonnières
- **Données sur 1 an** en résolution horaire

## Résultats attendus

Lors de l'exécution complète, vous devriez voir :
- Nombre total de tests exécutés
- Détails par catégorie
- Temps d'exécution
- Rapport de succès/échecs
- Métriques de performance pour les scénarios d'intégration

## Dépannage

### Erreur "No module named 'streamlit'"
Le module `key_manager.py` importe Streamlit. Pour exécuter les tests :
1. Installer Streamlit : `pip install streamlit`
2. Ou utiliser les tests simplifiés : `python tests/test_repartition_simple.py`

### Erreur de chemin d'import
Assurez-vous d'exécuter les tests depuis le dossier racine du projet, pas depuis le dossier `tests/`.

## Maintenance

### Ajouter de nouveaux tests
1. Identifier la catégorie appropriée
2. Ajouter la méthode de test dans le fichier correspondant
3. Suivre la convention de nommage `test_*`
4. Documenter le cas testé

### Mettre à jour les tests existants
1. Modifier le test concerné
2. Vérifier l'impact sur les tests d'intégration
3. Mettre à jour ce README si nécessaire

## Exemples de sortie

```
=== Scénario 1 : Répartition statique équitable ===
Validation : Clés valides - Somme = 100.00%
Production totale : 1825000 kWh
Taux d'autoconsommation global : 68.5%

Résultats par participant :
  Résidence Les Mimosas:
    - Énergie allouée : 456250 kWh
    - Consommation : 438000 kWh
    - Taux d'autoconsommation : 96.0%
  ...
```

## Notes importantes

1. Les tests d'intégration créent des fichiers temporaires qui sont automatiquement nettoyés
2. Certains tests utilisent des données aléatoires mais avec des seeds fixes pour la reproductibilité
3. Les tests de performance peuvent prendre plus de temps sur de grandes périodes de données
4. Les validations incluent des tolérances pour les calculs en virgule flottante (généralement 0.01%)

## Contact

Pour toute question sur les tests, consulter la documentation du module de répartition ou contacter l'équipe de développement.