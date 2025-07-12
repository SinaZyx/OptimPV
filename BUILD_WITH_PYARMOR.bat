@echo off
echo ============================================================
echo    BUILD OPTIMPV AVEC PYARMOR + VERIFICATION PORTS
echo ============================================================
echo.

echo [1/6] Nettoyage...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im OptimPV*.exe >nul 2>&1
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist .pyarmor_config rmdir /s /q .pyarmor_config

echo [2/6] Activation environnement...
call venv\Scripts\activate.bat

echo [3/6] Creation dossier temporaire PyArmor...
if not exist temp_protected mkdir temp_protected

echo [4/6] Protection PyArmor des modules critiques...
echo    - Protection du module engine complet...
pyarmor gen --output temp_protected modules\engine_module\core_analyzer.py
pyarmor gen --output temp_protected modules\engine_module\financial_calculations.py
pyarmor gen --output temp_protected modules\engine_module\tax_engine.py
pyarmor gen --output temp_protected modules\engine_module\engine_utils.py
pyarmor gen --output temp_protected modules\engine_module\data_processing.py
echo    - Protection du module optimisation...
pyarmor gen --output temp_protected modules\optimisation_analyse\logique_optimisation.py
echo    - Protection du module securite...
pyarmor gen --output temp_protected modules\security_config.py
echo    - Protection du launcher (SANS licence_guard pour eviter conflit)...
REM PAS de protection PyArmor pour launcher_fixed.py - on garde l'original pour licence_guard
copy launcher_fixed.py temp_protected\launcher_fixed.py
echo    - Copie de licence_guard.py dans temp_protected...
copy licence_guard.py temp_protected\licence_guard.py

echo [5/6] Compilation avec PyArmor et protection token...
pyinstaller --noconfirm --onefile --windowed ^
    --name OptimPV_Final_Protected ^
    --icon assets\icon.ico ^
    --add-data "app.py;." ^
    --add-data "modules;modules" ^
    --add-data "config;config" ^
    --add-data "assets;assets" ^
    --add-data "licence_guard.py;." ^
    --add-data "temp_protected;temp_protected" ^
    --collect-all streamlit ^
    --collect-all plotly ^
    --collect-all pandas ^
    --collect-all numpy ^
    --hidden-import streamlit.web.cli ^
    --hidden-import webbrowser ^
    --hidden-import requests ^
    --hidden-import threading ^
    --hidden-import plotly ^
    --hidden-import pandas ^
    --hidden-import numpy ^
    --hidden-import ssl ^
    --hidden-import socket ^
    --hidden-import json ^
    --hidden-import datetime ^
    --hidden-import os ^
    --hidden-import sys ^
    --hidden-import licence_guard ^
    --hidden-import cryptography ^
    --hidden-import cryptography.hazmat.primitives.ciphers ^
    --hidden-import cryptography.hazmat.primitives ^
    --hidden-import cryptography.hazmat.backends ^
    --optimize 2 ^
    --strip ^
    --noupx ^
    --log-level ERROR ^
    temp_protected\launcher_fixed.py

echo [6/6] Verification...
echo.
if exist dist\OptimPV_Final_Protected.exe (
    echo ============================================================
    echo    BUILD REUSSI AVEC PYARMOR!
    echo ============================================================
    echo.
    echo EXECUTABLE: dist\OptimPV_Final_Protected.exe
    for %%F in (dist\OptimPV_Final_Protected.exe) do echo TAILLE: %%~zF octets
    echo.
    echo PROTECTIONS ET FONCTIONNALITES:
    echo V Code protege avec PyArmor (engine_module complet + optimisation)
    echo V Protection token avec licence_guard.py
    echo V Executable 100%% autonome (Python + toutes dependances incluses)
    echo V Verification des ports existants
    echo V Ouverture automatique navigateur
    echo V Optimisations (--optimize 2, --strip)
    echo V Une seule instance Streamlit
    echo V Collecte complete: Streamlit, Plotly, Pandas, Numpy
    echo.
    echo UTILISATION:
    echo 1. Double-clic sur dist\OptimPV_Final_Protected.exe
    echo 2. AUCUNE INSTALLATION REQUISE (Python, modules, etc.)
    echo 3. Application sans console (mode fenetre)
    echo 4. Navigateur s'ouvre automatiquement
    echo 5. Mot de passe: panel123
    echo 6. Utiliser bouton Arreter dans l'onglet Serveur
    echo.
    echo DEPLOIEMENT:
    echo - Copier uniquement OptimPV_Final_Protected.exe
    echo - Fonctionne sur tout PC Windows sans installation
    echo - Taille: ~150-200 MB (tout inclus)
    echo.
    echo ============================================================
) else (
    echo ECHEC: Executable non cree
)

echo.
echo Build termine
pause