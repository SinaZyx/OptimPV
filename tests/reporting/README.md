# Tests du Module Reporting OptimPV

## 📁 Structure des Tests

### Tests DOCX
- `test_docx_system.py` - Test de structure et création des fichiers
- `test_docx_final.py` - Test complet du système DOCX 
- `test_docx_simple.py` - Test simple sans dépendances complexes
- `test_docx_standalone.py` - Test avec données simulées sans app.py
- `test_interface_rapide.py` - Test rapide de l'interface utilisateur
- `GUIDE_TEST_DOCX.md` - Guide complet pour tester le système DOCX

### Tests Existants
- `test_reporting_modules.py` - Tests des modules de reporting de base
- `test_reporting_improved_preview.py` - Tests du reporting amélioré
- `test_reporting_preview.py` - Tests de prévisualisation

## 🚀 Lancer les Tests

### Test Rapide du Système DOCX
```bash
cd tests/reporting
python3 test_docx_simple.py
```

### Test Complet avec Données Simulées
```bash
python3 test_docx_standalone.py
```

### Test de l'Interface
```bash
python3 test_interface_rapide.py
```

## 📊 Résultats Attendus

- ✅ Structure complète : 6 fichiers DOCX (107KB+ de code)
- ✅ Gestionnaire de dépendances fonctionnel
- ✅ Intégration dans customer_report_commercial.py
- ✅ Script d'installation automatique créé
- ✅ Interface utilisateur opérationnelle