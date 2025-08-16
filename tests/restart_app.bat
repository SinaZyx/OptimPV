@echo off
echo === Redemarrage d'OptimPV avec Folium ===
echo.
echo Fermeture des instances existantes...
taskkill /F /IM streamlit.exe 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *streamlit*" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

echo.
echo Verification de Folium...
python -c "import folium; print('Folium OK - Version:', folium.__version__)"

echo.
echo Lancement d'OptimPV...
streamlit run app.py

pause