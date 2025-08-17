# 📦 Création d'EXE - ARCHIVÉ

⚠️ **NOTE IMPORTANTE** : La création d'exe est une mauvaise idée qui complique inutilement le projet. Utilisez plutôt directement Python avec le venv !

## Pourquoi éviter l'exe ?

- ❌ Fichier très lourd (191 MB)
- ❌ Difficile à débugger
- ❌ Problèmes de compatibilité
- ❌ Mise à jour compliquée
- ❌ PyArmor peut causer des conflits

## Solution recommandée

```bash
# Utiliser simplement :
venv\Scripts\activate
streamlit run app.py
```

## Contenu de ce dossier (archivé)

Si vous avez VRAIMENT besoin de créer un exe :

- `BUILD_WITH_PYARMOR.bat` : Script de build principal
- `OptimPV_Final_Protected.spec` : Config PyInstaller
- `dist/` : Exe compilé
- `build/` : Fichiers temporaires
- `temp_protected/` : Modules protégés PyArmor

## Pour créer un exe (non recommandé)

```bash
cd exe_creation
BUILD_WITH_PYARMOR.bat
```

---

💡 **Conseil** : Gardez ce dossier pour référence mais n'utilisez pas l'exe en production !