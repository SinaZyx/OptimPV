# Tests du Système de Placement de Trésorerie

Ce dossier contient tous les tests relatifs au système de placement de trésorerie d'OptimPV, organisés par catégorie.

## 📋 Organisation des Tests

### 🔧 Tests Fonctionnels Core

#### `test_placement_engine.py` 
**Objectif**: Test du moteur de placement principal  
**Contenu**:
- Test des fonctions de logging (log_tva_placement, clear_tva_log)
- Test de la classe AnalysisEngine et ses méthodes
- Test de la détection du mode optimisation
- Test de la détection des remboursements TVA
- Simulation de la logique de placement basique

**Utilisation**: `python3 tests/test_placement_engine.py`

#### `test_core_analyzer.py`
**Objectif**: Test du moteur d'analyse principal  
**Contenu**: Tests de base du core analyzer

**Utilisation**: `python3 tests/test_core_analyzer.py`

### 💰 Tests de Désactivation des Placements

#### `test_placement_deactivation.py` ⭐
**Objectif**: Test complet de la désactivation des placements  
**Contenu**:
- Test avec placement activé vs désactivé
- Vérification que les colonnes restent à zéro quand désactivé
- Test des affichages conditionnels
- Simulation complète avec différents scénarios

**Utilisation**: `python3 tests/test_placement_deactivation.py`

#### `test_placement_simple.py` ⭐
**Objectif**: Test simplifié sans dépendances externes  
**Contenu**:
- Test de la logique conditionnelle des IDs de placement
- Test du filtrage des en-têtes de section
- Test de la section PRODUITS FINANCIERS conditionnelle
- Vérification de l'implémentation de la désactivation

**Utilisation**: `python3 tests/test_placement_simple.py`

### 📊 Tests des Comptes de Résultat

#### `test_compte_resultat.py`
**Objectif**: Test des calculs du compte de résultat  
**Contenu**:
- Test avec données réelles simulées
- Vérification des calculs RÉSULTAT AVANT IMPÔT et RÉSULTAT NET
- Test de la gestion des valeurs nulles/manquantes

**Utilisation**: `python3 tests/test_compte_resultat.py`

#### `test_resultat_avant_impot.py`
**Objectif**: Test spécifique du calcul résultat avant impôt  
**Contenu**:
- Test des formules de calcul
- Vérification de l'ordre des opérations
- Test des cas limites

**Utilisation**: `python3 tests/test_resultat_avant_impot.py`

#### `test_resultat_final.py` ⭐
**Objectif**: Test final des résultats avec colonnes manquantes  
**Contenu**:
- Test avec colonnes manquantes (cas réel)
- Vérification que calculate_annual_total_from_monthly retourne 0 au lieu de NaN
- Test de la structure d'affichage HTML

**Utilisation**: `python3 tests/test_resultat_final.py`

#### `test_colonnes_compte_resultat.py`
**Objectif**: Test des noms de colonnes du compte de résultat  
**Contenu**:
- Vérification des colonnes requises
- Test des variations possibles des noms
- Test de la fonction calculate_annual_total_from_monthly

**Utilisation**: `python3 tests/test_colonnes_compte_resultat.py`

### 📈 Tests des Tableaux Années Critiques

#### `test_tableau_annees_critiques.py` ⭐
**Objectif**: Test complet des tableaux pour années importantes  
**Contenu**:
- Simulation 20 ans de données financières
- Test première année d'exploitation (placement TVA CAPEX)
- Test année de remplacement onduleur (déblocage provisions)
- Vérification de la cohérence des calculs
- Export des résultats en CSV

**Utilisation**: `python3 tests/test_tableau_annees_critiques.py` (nécessite pandas)

#### `test_tableau_simple.py` ⭐
**Objectif**: Test simplifié des années critiques sans dépendances  
**Contenu**:
- Test logique première année d'exploitation
- Test logique année de remplacement onduleur (15 ans)
- Test cohérence inter-années
- Vérifications affichage tableaux
- Calculs théoriques vs attendus

**Utilisation**: `python3 tests/test_tableau_simple.py`

#### `resume_test_annees_critiques.py`
**Objectif**: Analyse des logs réels pour validation  
**Contenu**:
- Extraction données des logs OptimPV
- Vérification cohérence calculs réels
- Analyse impact compte de résultat
- Recommandations basées sur données réelles

**Utilisation**: `python3 tests/resume_test_annees_critiques.py`

### 🔍 Tests de Validation

#### `validation_placement_engine.py`
**Objectif**: Validation de l'implémentation complète  
**Contenu**:
- Vérification que toutes les fonctionnalités sont implémentées
- Check des fonctionnalités critiques
- Validation conformité aux spécifications

**Utilisation**: `python3 tests/validation_placement_engine.py`

#### `validation_correction_totaux_annuels.py`
**Objectif**: Validation des corrections des totaux annuels  

#### `validation_corrections_finales.py`
**Objectif**: Validation des corrections finales  

#### `validation_finale_simple.py`
**Objectif**: Validation finale simplifiée  

#### `validation_option1_capitalisation.py`
**Objectif**: Validation option capitalisation  

## 🚀 Tests Recommandés par Priorité

### Priorité 1 - Tests Essentiels ⭐
1. `test_placement_simple.py` - Validation logique désactivation
2. `test_resultat_final.py` - Validation compte de résultat
3. `test_tableau_simple.py` - Validation années critiques

### Priorité 2 - Tests Complets
1. `test_placement_deactivation.py` - Test complet désactivation
2. `test_placement_engine.py` - Test moteur placement
3. `validation_placement_engine.py` - Validation implémentation

### Priorité 3 - Tests Spécialisés
1. `test_compte_resultat.py` - Tests compte de résultat
2. `test_colonnes_compte_resultat.py` - Tests colonnes
3. `resume_test_annees_critiques.py` - Analyse logs réels

## 📝 Commandes Rapides

```bash
# Lancer tous les tests simples (sans dépendances)
python3 tests/test_placement_simple.py
python3 tests/test_tableau_simple.py
python3 tests/test_resultat_final.py

# Validation complète
python3 tests/validation_placement_engine.py

# Tests avec dépendances (nécessite environnement Python complet)
python3 tests/test_placement_deactivation.py
python3 tests/test_tableau_annees_critiques.py
```

## 🔧 Dépendances

**Tests sans dépendances** (fonctionnent avec Python standard):
- `test_placement_simple.py`
- `test_tableau_simple.py`
- `test_resultat_final.py`
- `validation_placement_engine.py`

**Tests avec dépendances** (nécessitent pandas, numpy):
- `test_placement_deactivation.py`
- `test_tableau_annees_critiques.py`
- `test_placement_engine.py`

## 📊 Couverture des Tests

- ✅ Logique de placement TVA
- ✅ Désactivation conditionnelle
- ✅ Calculs compte de résultat
- ✅ Affichage tableaux financiers
- ✅ Déblocage provisions onduleur
- ✅ Cohérence inter-années
- ✅ Gestion colonnes manquantes
- ✅ Impact fiscal des placements

## 🎯 Résultats Attendus

Tous les tests marqués ⭐ doivent passer avec succès pour valider l'implémentation du système de placement de trésorerie.

---

*Documentation mise à jour le 04/07/2025*