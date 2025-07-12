@echo off
echo Correction de l'installation de scipy...
echo.

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

echo 1. Desinstallation de scipy...
pip uninstall -y scipy

echo.
echo 2. Nettoyage du cache pip...
pip cache purge

echo.
echo 3. Reinstallation de scipy...
pip install scipy==1.10.1

echo.
echo 4. Verification de l'installation...
python -c "import scipy; print(f'scipy version: {scipy.__version__}')"

echo.
echo Correction terminee !
pause