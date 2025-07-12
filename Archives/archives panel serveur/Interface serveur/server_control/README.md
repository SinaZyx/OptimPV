# OptimPV - Server Control Panel
## 🖥️ Panneau de Contrôle Serveur

Ce dossier contient tous les fichiers nécessaires pour le **panneau de contrôle serveur OptimPV**.

---

## 📂 Structure des Dossiers

```
server_control/
├── core/                    # 🧠 Fichiers principaux
│   └── server_control_panel.py    # Interface Streamlit principale
├── launchers/               # 🚀 Scripts de lancement
│   ├── control_panel_launcher.py  # Lanceur Python
│   └── OptimPV_Control_Panel.bat  # Script Windows
├── build/                   # 🏗️ Compilation et Build
│   ├── build_server_control.py    # Build complet avec Nuitka
│   └── build_simple.py           # Build de test simplifié
├── scripts/                 # 🔧 Scripts utilitaires
│   ├── diagnostic_serveur.py      # Diagnostic système
│   └── test_demarrage_serveur.py  # Test fonctionnel
└── docs/                    # 📖 Documentation
    └── RESUME_PANNEAU_CONTROLE.md # Documentation complète
```

---

## 🚀 Utilisation Rapide

### **Lancement Standard**
```bash
# Depuis le dossier racine OptimPV
python server_control/launchers/control_panel_launcher.py

# Ou avec le script Windows
.\server_control\launchers\OptimPV_Control_Panel.bat
```

### **Test et Diagnostic**
```bash
# Diagnostic complet du système
python server_control/scripts/diagnostic_serveur.py

# Test de la fonction de démarrage
python server_control/scripts/test_demarrage_serveur.py
```

### **Compilation**
```bash
# Build complet pour production
python server_control/build/build_server_control.py

# Build de test simplifié
python server_control/build/build_simple.py
```

---

## 📋 Description des Fichiers

### **Core (🧠 Fichiers principaux)**

| Fichier | Description |
|---------|-------------|
| `server_control_panel.py` | Interface Streamlit principale avec 3 onglets : Contrôle Serveur, Logs & Monitoring, Administration |

### **Launchers (🚀 Scripts de lancement)**

| Fichier | Description |
|---------|-------------|
| `control_panel_launcher.py` | Lanceur Python principal pour le panneau de contrôle |
| `OptimPV_Control_Panel.bat` | Script Windows avec interface console pour lancement one-click |

### **Build (🏗️ Compilation et Build)**

| Fichier | Description |
|---------|-------------|
| `build_server_control.py` | Script de build complet avec Nuitka, optimisations, et packaging |
| `build_simple.py` | Build de test minimaliste pour validation rapide |

### **Scripts (🔧 Scripts utilitaires)**

| Fichier | Description |
|---------|-------------|
| `diagnostic_serveur.py` | Diagnostic complet : environnement, dépendances, test serveur |
| `test_demarrage_serveur.py` | Test fonctionnel de la méthode de démarrage du serveur |

### **Docs (📖 Documentation)**

| Fichier | Description |
|---------|-------------|
| `RESUME_PANNEAU_CONTROLE.md` | Documentation technique complète du système |

---

## ⚡ Workflow Recommandé

### **1. Développement**
```bash
# 1. Tester le système
python server_control/scripts/diagnostic_serveur.py

# 2. Lancer le panneau de contrôle
python server_control/launchers/control_panel_launcher.py

# 3. Valider les fonctions
python server_control/scripts/test_demarrage_serveur.py
```

### **2. Production**
```bash
# 1. Build de l'exécutable
python server_control/build/build_server_control.py

# 2. Distribuer OptimPV_Server_Control.exe
```

---

## 🔧 Configuration

Le panneau de contrôle utilise les configurations existantes :
- **Configuration réseau** : `network_admin_config.json` (à la racine)
- **Authentification admin** : admin / admin123 (⚠️ à changer!)
- **Ports** : 
  - Panneau de contrôle : 8503
  - Serveur OptimPV : 8501 (configurable)

---

## 🌐 Accès

| Interface | URL | Utilisation |
|-----------|-----|-------------|
| **Panneau de Contrôle** | http://127.0.0.1:8503 | Gestion du serveur OptimPV |
| **Application OptimPV** | http://127.0.0.1:8501 | Application principale (via panneau) |

---

## 📞 Support

- **Documentation complète** : `docs/RESUME_PANNEAU_CONTROLE.md`
- **Diagnostic automatique** : `scripts/diagnostic_serveur.py`
- **Test fonctionnel** : `scripts/test_demarrage_serveur.py`

---

## 🎯 Fonctionnalités

✅ **Contrôle serveur** : Démarrage/arrêt du serveur OptimPV  
✅ **Monitoring** : Logs en temps réel et métriques système  
✅ **Administration** : Configuration réseau sécurisée  
✅ **Accès direct** : Bouton vers l'application OptimPV  
✅ **Build automatisé** : Compilation en exécutable autonome  
✅ **Diagnostic intégré** : Validation complète du système  

---

*OptimPV Solutions - Optimisation Photovoltaïque* 