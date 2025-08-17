============================================================
    FICHIERS IMPORTANTS - OPTIMPV
============================================================

FICHIERS PRINCIPAUX:
- app.py                    : Application principale OptimPV
- launcher_fixed.py         : Launcher avec anti-boucle et détection de ports
- licence_guard.py          : Système de protection par licence
- run_secure.py             : Script de lancement sécurisé
- server_controller.py      : Contrôleur serveur pour OptimPV
- create_token_admin.py     : Création de tokens admin

SCRIPTS DE BUILD:
- BUILD_WITH_PYARMOR.bat    : Build avec protection PyArmor
- BUILD_QUICK_FIX.bat       : Build rapide sans PyArmor

FICHIERS PYARMOR:
- pyarmor-regcode-9306.txt  : Code de licence PyArmor
- pyarmor-regfile-9306.zip  : Fichier de licence PyArmor

EXECUTABLE FINAL:
- dist\OptimPV_Final_Protected.exe : Version finale avec toutes protections

DOSSIERS IMPORTANTS:
- modules\     : Modules de l'application
- config\      : Configuration
- assets\      : Ressources (icône, etc.)
- dist\        : Executables compilés
- build\       : Fichiers de build temporaires
- projects\    : Projets sauvegardés
- tests\       : Tests unitaires

============================================================
    GUIDE DE COMPILATION ET ARCHITECTURE - OPTIMPV
============================================================

COMMENT COMPILER OPTIMPV:

1. COMPILATION AVEC PYARMOR (Recommandé pour production):
   > BUILD_WITH_PYARMOR.bat
   
   Ce script fait:
   - Protection PyArmor des modules critiques
   - Création d'un executable unique avec toutes les dépendances
   - Intégration de la vérification des ports
   - Ouverture automatique du navigateur

2. COMPILATION RAPIDE (Pour tests):
   > BUILD_QUICK_FIX.bat
   
   Compilation sans PyArmor mais avec toutes les fonctionnalités

============================================================
    PROBLÈMES RÉSOLUS ET SOLUTIONS TECHNIQUES
============================================================

1. BOUCLES INFINIES STREAMLIT:
   Problème: subprocess.Popen() créait des instances infinies
   Solution: Utilisation de os.execv() dans launcher_fixed.py
   
2. CONFLIT PYARMOR + STREAMLIT:
   Problème: PyArmor bloquait l'exécution dynamique de Streamlit
   Solution: Protection sélective uniquement des modules critiques:
   - core_analyzer.py (moteur d'analyse)
   - financial_calculations.py (calculs financiers)
   - storage.py (gestion données)
   - launcher_fixed.py (launcher principal)

3. ERREURS D'IMPORT (RGBColor, Document):
   Problème: Classes docx non définies quand python-docx absent
   Solution: Classes mock dans tous les fichiers docx_system:
   - professional_template_engine.py
   - premium_commercial_generator.py
   - template_based_generator.py
   - visual_components.py

4. MODE DÉVELOPPEMENT STREAMLIT:
   Problème: --server.port ne fonctionne pas en mode dev
   Solution: Ajout de --global.developmentMode false

5. DÉTECTION DES PORTS:
   Ajout: Vérification si OptimPV tourne déjà
   - Si oui: ouvre juste le navigateur
   - Si non: lance nouvelle instance

============================================================
    ARCHITECTURE DE LA SOLUTION
============================================================

launcher_fixed.py:
  |
  +-> Détecte le mode (PyInstaller ou dev)
  |
  +-> Vérifie les ports existants (8501-8505)
  |     |
  |     +-> Port utilisé? -> Ouvre navigateur seulement
  |     +-> Port libre? -> Continue
  |
  +-> Mode PyInstaller:
  |     |
  |     +-> Change répertoire vers _MEIPASS
  |     +-> Import streamlit.web.cli
  |     +-> Lance avec stcli.main()
  |
  +-> Mode développement:
        |
        +-> Utilise os.execv() (pas de subprocess!)

============================================================
    COMPORTEMENT DE L'APPLICATION
============================================================

1. PREMIER LANCEMENT:
   - Lance OptimPV sur port disponible
   - Ouvre navigateur après 3 secondes
   - Affiche console avec instructions

2. DEUXIÈME LANCEMENT:
   - Détecte instance existante
   - Ouvre navigateur vers instance
   - Possibilité de fermer cette console

3. CONSOLE PRINCIPALE:
   - NE PAS FERMER (arrête OptimPV)
   - Affiche logs et statut
   - Ctrl+C pour arrêt propre

============================================================
    DÉTAILS TECHNIQUES DE COMPILATION
============================================================

ÉTAPES BUILD_WITH_PYARMOR.bat:

1. Nettoyage (taskkill processus existants)
2. Activation environnement virtuel (venv)
3. Protection PyArmor:
   pyarmor gen --output temp_protected modules\engine_module\core_analyzer.py
   pyarmor gen --output temp_protected modules\engine_module\financial_calculations.py
   pyarmor gen --output temp_protected modules\storage.py
   pyarmor gen --output temp_protected launcher_fixed.py

4. PyInstaller avec options:
   --onefile : Un seul executable
   --console : Garde la console visible
   --add-data : Inclut app.py, modules, config, assets
   --collect-all streamlit : Toutes dépendances Streamlit
   --hidden-import : Imports nécessaires

RÉSULTAT: dist\OptimPV_Final_Protected.exe (~173 MB)

============================================================
    LOGGING ET DEBUG
============================================================

Fichier de log: optimpv_launcher.log

Contient:
- Informations système (Python path, _MEIPASS, etc.)
- Détection des ports
- Étapes de lancement
- Erreurs éventuelles

Utile pour diagnostiquer les problèmes de déploiement.

============================================================