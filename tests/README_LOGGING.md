# OptimPV - Système de Logging des Tests

## Vue d'ensemble

Le script `run_tests.py` à la racine du projet inclut maintenant un système de logging automatique qui capture **tous les outputs de la console** pendant l'exécution des tests.

## Fichiers de Logs Générés

### 1. Log Principal
- **Fichier** : `/tests/log.txt`
- **Contenu** : Historique cumulé de toutes les sessions de tests
- **Format** : `[YYYY-MM-DD HH:MM:SS] LEVEL: message`

### 2. Logs de Session
- **Dossier** : `/tests/logs/`
- **Fichiers** : `test_session_YYYYMMDD_HHMMSS.log`
- **Contenu** : Log détaillé d'une session spécifique avec horodatage Python

### 3. Rapports HTML (optionnels)
- **Dossier** : `/tests/`
- **Fichiers** : `test_report_YYYYMMDD_HHMMSS.html`
- **Contenu** : Rapport visuel professionnel avec graphiques et statistiques

## Utilisation du Logging

### Activation/Désactivation
```bash
# Logging activé par défaut
python3 run_tests.py --unit-only

# Désactiver le logging
python3 run_tests.py --unit-only --no-logging
```

### Consultation des Logs
```bash
# Afficher les 20 dernières lignes des logs
python3 run_tests.py --show-logs

# Les chemins des logs sont toujours affichés à la fin des tests
```

## Types de Messages Loggés

### Niveaux de Log
- **INFO** : Messages d'information généraux, en-têtes, résumés
- **OUTPUT** : Sortie directe de la console (stdout/stderr capturé)
- **DEBUG** : Détails techniques, résultats de tests détaillés
- **ERROR** : Erreurs d'exécution, catégories non trouvées

### Contenu Capturé
1. **En-têtes et méta-données** : Date, projet, configuration
2. **Progression des tests** : Début/fin de chaque catégorie
3. **Sorties des tests** : Tous les prints, erreurs, traces
4. **Résultats** : Statistiques, temps d'exécution, statuts
5. **Résumé de session** : Bilan global avec statistiques

## Exemples de Contenu

### Log Principal
```
[2025-07-12 00:16:23] INFO: === DÉBUT DE SESSION DE TESTS ===
[2025-07-12 00:16:23] INFO: Projet: /mnt/c/Users/kingc/OptimPV
[2025-07-12 00:16:23] INFO: Pytest disponible: False
[2025-07-12 00:16:23] INFO: 🛠️ Exécution: UTILS
[2025-07-12 00:16:23] OUTPUT: ⚠️ Pytest non disponible, exécution manuelle des tests...
[2025-07-12 00:16:23] DEBUG: Résultat utils: {'status': 'NO_TESTS', 'tests_run': 0, 'passed': 0, 'failed': 0}
```

### Résumé de Session
```
================================================================================
RÉSUMÉ DE SESSION DE TESTS - 2025-07-12 00:16:23
================================================================================
Durée totale: 1.77 secondes
Nombre de catégories testées: 1

STATISTIQUES GLOBALES:
  Tests exécutés: 8
  Tests réussis: 0
  Tests échoués: 8
  Taux de réussite: 0.0%

DÉTAILS PAR CATÉGORIE:
  ERP: FAILED - 0/8 réussis (1.77s)
================================================================================
```

## Avantages du Système

### 1. **Traçabilité Complète**
- Chaque exécution de test est horodatée et tracée
- Historique permanent dans le log principal
- Sessions isolées dans des fichiers séparés

### 2. **Debug Facilité**
- Capture automatique de toutes les erreurs et traces
- Messages colorés en console, propres dans les logs
- Niveaux de détail ajustables (verbose/normal)

### 3. **Analyse Post-Mortem**
- Consultation des logs récents avec `--show-logs`
- Fichiers horodatés pour identifier les sessions problématiques
- Statistiques détaillées pour chaque catégorie

### 4. **Intégration CI/CD**
- Logs structurés facilement parsables
- Rapports HTML pour visualisation
- Codes de sortie appropriés pour automation

## Maintenance

### Nettoyage Automatique
Le système inclut une fonction de nettoyage automatique des anciens logs de session (30 jours par défaut).

### Gestion de l'Espace
- Log principal : croissance contrôlée par rotation
- Logs de session : un fichier par exécution
- Rapports HTML : générés à la demande uniquement

## Bonnes Pratiques

1. **Consulter les logs** après chaque session de test importante
2. **Utiliser --verbose** pour les sessions de debug
3. **Générer des rapports HTML** pour les rapports formels
4. **Archiver les logs critiques** avant les releases
5. **Utiliser --show-logs** pour un aperçu rapide

## Dépannage

### Problèmes de Permissions
```bash
# Vérifier les permissions du dossier tests
ls -la /mnt/c/Users/kingc/OptimPV/tests/
```

### Logs Corrompus
```bash
# Supprimer le log principal pour le recréer
rm /mnt/c/Users/kingc/OptimPV/tests/log.txt
```

### Espace Disque
```bash
# Nettoyer les anciens logs de session
find /mnt/c/Users/kingc/OptimPV/tests/logs/ -name "test_session_*.log" -mtime +30 -delete
```

---

**Note** : Tous les fichiers de logs et rapports sont créés exclusivement dans le dossier `/tests/` pour maintenir une organisation propre du projet.