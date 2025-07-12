# Tests de Debug pour le Système de Storage

## 🚨 Problèmes Identifiés

### Problème 1: État des projets incorrect
- **Symptôme**: Les projets affichent "Monte Carlo fait" alors que c'est faux
- **Cause**: `calculate_completeness_score()` vérifiait seulement la présence des clés, pas leur contenu
- **Solution**: ✅ Corrigé - Maintenant vérifie `bool(st.session_state.get('key'))`

### Problème 2: Comparaison économique échoue
- **Symptôme**: "Aucune analyse économique" alors que l'analyse a été faite
- **Cause**: Les fichiers JSON existent mais sont probablement vides `{}`
- **Solution**: ✅ Ajout de logs de debug pour identifier le problème

### Problème 3: Incohérence dans la détection d'état
- **Cause**: Logiques différentes dans `calculate_completeness_score()` vs `save_current_project()`
- **Solution**: ✅ Harmonisé toutes les vérifications

## 🔧 Corrections Appliquées

### 1. `calculate_completeness_score()` (ligne ~719)
**AVANT:**
```python
'economic_analysis': 'economic_results' in st.session_state,
```

**APRÈS:**
```python
'economic_analysis': 'economic_results' in st.session_state and bool(st.session_state.get('economic_results')),
```

### 2. Logs de debug ajoutés dans `compare_projects_advanced()`
- Debug du chargement des fichiers JSON
- Affichage du contenu et des clés chargées
- Identification des fichiers vides vs manquants

### 3. Logs de debug dans `_show_economic_comparison()`
- Debug des données reçues pour la comparaison
- Affichage du type et contenu des variables

## 🔍 Outils de Debug Créés

### 1. `test_storage_debug.py`
Diagnostic complet du système de storage (simulation).

### 2. `debug_storage_analysis.py`
Analyse théorique des problèmes identifiés.

### 3. `verify_project_files.py`
**Utilitaire principal** pour vérifier vos projets existants:
```bash
python3 tests/verify_project_files.py
```

Cet outil va :
- ✅ Lister tous vos projets
- ✅ Vérifier la présence des fichiers
- ✅ Analyser le contenu des fichiers JSON
- ✅ Détecter les incohérences manifest ↔ fichiers
- ✅ Identifier les fichiers vides

## 🎯 Comment Diagnostiquer Vos Projets

### Étape 1: Vérifier les fichiers existants
```bash
cd /mnt/c/Users/kingc/OptimPV
python3 tests/verify_project_files.py
```

### Étape 2: Activer les logs en direct
Les logs de debug sont maintenant activés dans `storage.py`. Quand vous faites une comparaison, vous verrez dans la console:
```
DEBUG - DEBUG: Chargé economic1 de projet_123: True - Clés: ['base', 'optimiste']
DEBUG - DEBUG COMPARAISON ÉCONOMIE:
DEBUG -   economic1 bool: True, type: <class 'dict'>, contenu: {'base': {...}}
```

### Étape 3: Interpréter les résultats

**Si vous voyez:**
- `economic1 bool: False` → Le fichier est vide ou manquant
- `economic1 bool: True` mais comparaison échoue → Problème dans la logique de comparaison
- Manifest dit `has_economic_results: True` mais fichier vide → Incohérence dans la sauvegarde

## 🚀 Test des Corrections

### Test 1: Vérifier l'état des projets
1. Ouvrez l'interface Hub de Projets
2. Les badges des modules devraient maintenant être corrects
3. Monte Carlo devrait afficher ❌ si pas fait

### Test 2: Vérifier la comparaison
1. Comparez deux projets avec analyses économiques
2. L'onglet Économie devrait maintenant fonctionner
3. Vérifiez les logs dans la console pour le debug

### Test 3: Sauvegarder un nouveau projet
1. Faites une analyse économique complète
2. Sauvegardez le projet
3. Vérifiez avec `verify_project_files.py` que tout est cohérent

## 📋 Checklist de Vérification

- [ ] Les badges d'état des projets sont corrects
- [ ] La comparaison économique fonctionne
- [ ] La comparaison d'optimisation fonctionne
- [ ] Monte Carlo s'affiche ❌ si pas fait
- [ ] Les nouveaux projets sauvegardés sont cohérents

## 🆘 Si les Problèmes Persistent

1. **Examinez les logs de debug** dans la console Streamlit
2. **Lancez `verify_project_files.py`** pour voir l'état de vos fichiers
3. **Sauvegardez un nouveau projet test** pour voir si la sauvegarde fonctionne
4. **Comparez le nouveau projet** avec un ancien pour identifier la différence

Les logs de debug vous donneront maintenant une visibilité complète sur ce qui se passe dans le système de storage.