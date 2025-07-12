# Tests de Navigation Automatisés - OptimPV

Ce dossier contient les tests automatisés pour vérifier le bon fonctionnement de l'interface utilisateur OptimPV.

## 🎯 Objectif

Détecter automatiquement les erreurs dans l'application Streamlit en simulant la navigation d'un utilisateur réel à travers tous les onglets et modules.

## 📁 Structure

```
system/
├── test_full_navigation.py    # Script principal de test
├── run_navigation_tests.py    # Lanceur simplifié
├── requirements.txt           # Dépendances
├── README.md                 # Cette documentation
└── reports/                  # Rapports générés
    ├── navigation_test_*.html
    └── navigation_test_*.json
```

## 🚀 Installation

1. **Installer les dépendances:**
```bash
pip install -r requirements.txt
```

2. **Configurer le webdriver (automatique):**
Le script configure automatiquement ChromeDriver ou GeckoDriverManager.

## 🔧 Utilisation

### Méthode Simple (Recommandée)

```bash
# Test rapide
python run_navigation_tests.py --quick

# Test complet avec captures d'écran
python run_navigation_tests.py --full

# Test avec navigateur visible (debug)
python run_navigation_tests.py --visible

# Installer dépendances + test
python run_navigation_tests.py --install-deps --full
```

### Méthode Avancée

```bash
# Test personnalisé
python test_full_navigation.py --headless --screenshots --timeout=90

# Test sans démarrer Streamlit (si déjà lancé)
python test_full_navigation.py --no-start-streamlit --headless
```

## 📊 Tests Effectués

### Pages Principales
- ✅ Accueil
- ✅ Configuration  
- ✅ Importation Données
- ✅ ERP Clients (test approfondi)
- ✅ Facturation PMO
- ✅ Carte de Prospection
- ✅ Historique
- ✅ Serveur

### Module ERP (Test Spécialisé)
- ✅ Dashboard Commercial
- ✅ Gestion Clients
- ✅ Formulaire Nouveau Client
- ✅ Dashboard Tarification
- ✅ Autoconsommation Collective
- ✅ Cartographie Clients
- ✅ Analytics & Statistiques

### Interactions Testées
- Navigation entre onglets
- Chargement des pages sans erreur
- Présence des formulaires
- Fonctionnement des boutons
- Affichage des graphiques
- Cartes interactives
- Champs de saisie

## 📋 Rapports Générés

Après chaque test, deux rapports sont créés dans `test_reports/`:

1. **Rapport HTML** (`navigation_test_YYYYMMDD_HHMMSS.html`)
   - Interface graphique complète
   - Résumé visuel des résultats
   - Détail de chaque erreur
   - Captures d'écran (si activées)

2. **Rapport JSON** (`navigation_test_YYYYMMDD_HHMMSS.json`)
   - Format machine-readable
   - Intégration CI/CD
   - Analyse programmatique

## 🔍 Types d'Erreurs Détectées

- **StreamlitError**: Erreurs d'affichage Streamlit
- **NavigationError**: Problèmes de navigation
- **ERPModuleError**: Erreurs spécifiques au module ERP
- **FormInteractionError**: Problèmes de formulaires
- **ElementNotFound**: Éléments UI manquants
- **AuthenticationError**: Problèmes de connexion

## ⚠️ Prérequis

- Python 3.7+
- Streamlit application fonctionnelle
- Chrome ou Firefox installé
- Port 8501 disponible (ou modifier la configuration)

## 🔧 Configuration

Variables modifiables dans `test_full_navigation.py`:

```python
BASE_URL = "http://localhost:8501"      # URL de l'application
STREAMLIT_PORT = 8501                   # Port Streamlit
DEFAULT_TIMEOUT = 60                    # Timeout par défaut
MAX_WAIT_FOR_ELEMENT = 10               # Attente éléments UI
```

## 🐛 Résolution de Problèmes

### Problème: Driver non trouvé
```bash
# Solution: Installer webdriver-manager
pip install webdriver-manager
```

### Problème: Streamlit ne démarre pas
```bash
# Vérifier que l'application fonctionne manuellement
streamlit run app.py --server.port 8501
```

### Problème: Timeout lors des tests
```bash
# Augmenter le timeout
python test_full_navigation.py --timeout=120
```

### Problème: Erreurs d'authentification
- Vérifier le mot de passe par défaut ("panel123")
- Modifier la méthode `authenticate()` si nécessaire

## 📈 Intégration CI/CD

Exemple d'intégration dans une pipeline:

```yaml
- name: Navigation Tests
  run: |
    cd modules/erp_client/tests/system
    python run_navigation_tests.py --quick
    # Vérifier le code de retour (0 = succès, 1 = erreurs)
```

## 🔄 Maintenance

- Mettre à jour les sélecteurs CSS si l'UI change
- Ajouter de nouveaux tests pour les nouvelles fonctionnalités
- Ajuster les timeouts selon les performances
- Maintenir la liste des pages à tester

## 📞 Support

En cas de problème avec les tests:
1. Vérifier les logs dans le rapport HTML
2. Lancer un test avec `--visible` pour debug visuel
3. Vérifier que l'application fonctionne manuellement
4. Consulter les captures d'écran des erreurs