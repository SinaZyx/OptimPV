# Tests d'intégrité pour le module ERP Client

Ce dossier contient les tests d'intégrité pour détecter et diagnostiquer les problèmes d'imports dans le module `erp_client`.

## Fichiers disponibles

### 📄 `test_imports_integrity.py`
Test principal qui utilise pytest si disponible, sinon des tests manuels.

**Fonctionnalités :**
- ✅ Vérification de la syntaxe de tous les fichiers Python
- ✅ Détection des imports vers des modules inexistants
- ✅ Identification des classes manquantes (comme `models.pricing`)
- ✅ Recherche automatique des classes dans le projet
- ✅ Suggestions de solutions pour corriger les problèmes

**Usage :**
```bash
# Avec pytest (si installé)
pytest modules/erp_client/tests/test_imports_integrity.py -v

# Exécution directe
python modules/erp_client/tests/test_imports_integrity.py
```

### 📄 `check_imports_simple.py`
Version simplifiée sans dépendances externes pour diagnostiquer rapidement les problèmes.

**Usage :**
```bash
python modules/erp_client/tests/check_imports_simple.py
```

### 📄 `run_integrity_tests.py`
Script avec rapport détaillé et actions recommandées.

**Usage :**
```bash
python modules/erp_client/tests/run_integrity_tests.py
```

## Problèmes détectés

### ❌ Problème principal : Module `models.pricing` manquant

**Fichiers affectés :**
- `ui/commercial_dashboard.py` (ligne 22)
- `ui/commercial_dashboard_v2.py` (ligne 27)

**Import problématique :**
```python
from ..models.pricing import PrixClient, TypeTarif
```

**Diagnostic :**
- ✅ Classe `PrixClient` existe dans `services/pricing_service.py`
- ❌ Classe `TypeTarif` n'existe pas dans le projet
- ❌ Module `models/pricing.py` n'existe pas

## Solutions recommandées

### Option A : Créer le module manquant

1. **Créer le fichier** `modules/erp_client/models/pricing.py`

2. **Déplacer `PrixClient`** depuis `services/pricing_service.py`

3. **Créer la classe `TypeTarif`** :
```python
from enum import Enum
from dataclasses import dataclass

class TypeTarif(Enum):
    """Types de tarifs disponibles."""
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTREPRISE = "entreprise"
    # Ajouter d'autres types selon les besoins
```

### Option B : Corriger les imports

1. **Modifier les imports** dans les fichiers affectés :
```python
# Changer de :
from ..models.pricing import PrixClient, TypeTarif

# Vers :
from ..services.pricing_service import PrixClient
# Et définir TypeTarif dans le même module ou ailleurs
```

2. **Ajouter `TypeTarif`** dans `services/pricing_service.py`

### Option C : Import conditionnel

Ajouter une gestion d'erreur temporaire :
```python
try:
    from ..models.pricing import PrixClient, TypeTarif
except ImportError:
    from ..services.pricing_service import PrixClient
    TypeTarif = None  # À définir plus tard
```

## Autres problèmes détectés

### ⚠️ Dépendance manquante : `streamlit`

**Solution :**
```bash
pip install streamlit
```

### ⚠️ Modules d'interface non trouvés

Certains imports font référence à des modules qui n'existent pas :
- `modules.erp_client.ui.main_window`
- `modules.erp_client.ui.panels.*`
- `modules.erp_client.ui.widgets.*`

**Vérifier** si ces modules doivent être créés ou si les imports doivent être corrigés.

## Exécution des tests

### Test complet avec rapport
```bash
cd /path/to/OptimPV
python modules/erp_client/tests/test_imports_integrity.py
```

### Test rapide
```bash
cd /path/to/OptimPV
python modules/erp_client/tests/check_imports_simple.py
```

## Résultats attendus

Après correction des problèmes :
- ✅ 0 erreur de syntaxe
- ✅ 0 import problématique
- ✅ Tous les modules peuvent être importés
- ✅ Tests d'intégrité réussis

## Mise à jour du README

Ce fichier sera mis à jour au fur et à mesure que les problèmes sont corrigés et que de nouveaux tests sont ajoutés.