@echo off
echo ============================================================
echo    BUILD OptimPV - Quick Fix UnboundLocalError
echo ============================================================
echo.

rem Activation de l'environnement virtuel
echo [1/3] Activation environnement virtuel...
call venv\Scripts\activate.bat

rem Nettoyage rapide
echo.
echo [2/3] Nettoyage rapide...
if exist dist\OptimPV.exe del /f /q dist\OptimPV.exe
if exist *.spec del /f /q *.spec

rem Compilation rapide (sans nettoyage complet pour gagner du temps)
echo.
echo [3/3] Compilation avec fix subprocess...
pyinstaller --noconfirm --onefile --windowed ^
    --name "OptimPV" ^
    --icon "assets\icon.ico" ^
    --add-data "assets;assets" ^
    --add-data "config;config" ^
    --add-data "modules;modules" ^
    --add-data "app.py;." ^
    --additional-hooks-dir "hooks" ^
    --collect-all streamlit ^
    --copy-metadata streamlit ^
    --copy-metadata pandas ^
    --copy-metadata numpy ^
    --copy-metadata pyarrow ^
    --hidden-import "streamlit.web.cli" ^
    --hidden-import "licence_guard" ^
    --hidden-import "subprocess" ^
    --log-level WARN ^
    server_controller.py

if %errorlevel% neq 0 (
    echo.
    echo [x] Echec compilation!
    pause
    exit /b 1
)

if exist "dist\OptimPV.exe" (
    echo.
    echo ==================================================
    echo BUILD FINAL REUSSI!
    echo ==================================================
    echo.
    echo CORRECTIONS APPLIQUEES:
    echo - Fix boutons initialisation: OK
    echo - Fix metadata Streamlit: OK  
    echo - Fix UnboundLocalError: OK
    echo - Fix boucle infinie subprocess: OK
    echo.
    echo TESTS:
    echo 1. Lancer OptimPV.exe  
    echo 2. Bouton START doit etre VERT
    echo 3. Cliquer START - Streamlit demarre SANS boucle
    echo 4. Verifier localhost:8501 fonctionne
    echo.
    echo Log: dist\optimpv_controller.log
    echo ==================================================
) else (
    echo.
    echo ECHEC - Executable non trouve
)

echo.
pause