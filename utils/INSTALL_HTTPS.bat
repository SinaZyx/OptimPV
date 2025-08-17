@echo off
echo ======================================
echo Installation HTTPS pour OptimPV
echo ======================================
echo.
echo CHOISISSEZ VOTRE METHODE :
echo.
echo [1] SIMPLE - Certificat auto-signe (test local)
echo [2] PRODUCTION - Avec vrai domaine
echo.
choice /C 12 /N /M "Votre choix (1 ou 2) : "

if errorlevel 2 goto PRODUCTION
if errorlevel 1 goto LOCAL

:LOCAL
echo.
echo Installation pour TEST LOCAL...
echo.

:: Créer certificat auto-signé avec OpenSSL (si installé)
where openssl >nul 2>&1
if %errorlevel%==0 (
    echo Creation du certificat SSL...
    mkdir ssl 2>nul
    openssl req -x509 -newkey rsa:4096 -keyout ssl\key.pem -out ssl\cert.pem -days 365 -nodes -subj "/CN=localhost"
    echo Certificat cree dans ssl\
) else (
    echo OpenSSL non trouve - Installation manuelle requise
    echo Telechargez OpenSSL : https://slproweb.com/products/Win32OpenSSL.html
)

:: Créer script Python pour proxy HTTPS simple
echo Creation du serveur proxy HTTPS...
(
echo import ssl
echo import http.server
echo import socketserver
echo import urllib.request
echo import socket
echo.
echo class ProxyHTTPRequestHandler^(http.server.SimpleHTTPRequestHandler^):
echo     def do_GET^(self^):
echo         # Proxy vers Streamlit
echo         url = f"http://localhost:8501{self.path}"
echo         try:
echo             with urllib.request.urlopen^(url^) as response:
echo                 self.send_response^(200^)
echo                 self.send_header^('Content-type', response.headers.get^('Content-Type', 'text/html'^)^)
echo                 self.end_headers^(^)
echo                 self.wfile.write^(response.read^(^)^)
echo         except Exception as e:
echo             self.send_error^(502, f"Proxy error: {e}"^)
echo.
echo     def do_POST^(self^):
echo         self.do_GET^(^)
echo.
echo # Configuration SSL
echo context = ssl.create_default_context^(ssl.Purpose.CLIENT_AUTH^)
echo context.load_cert_chain^('ssl/cert.pem', 'ssl/key.pem'^)
echo.
echo # Démarrer serveur HTTPS
echo with socketserver.TCPServer^(^("", 443^), ProxyHTTPRequestHandler^) as httpd:
echo     httpd.socket = context.wrap_socket^(httpd.socket, server_side=True^)
echo     print^("Serveur HTTPS démarré sur https://localhost"^)
echo     print^("Assurez-vous que Streamlit tourne sur http://localhost:8501"^)
echo     httpd.serve_forever^(^)
) > https_proxy.py

echo.
echo ======================================
echo Installation terminee !
echo ======================================
echo.
echo Pour demarrer :
echo 1. Lancez OptimPV : streamlit run app.py
echo 2. Dans un autre terminal : python https_proxy.py
echo 3. Accedez a : https://localhost
echo.
pause
exit

:PRODUCTION
echo.
echo Pour la PRODUCTION avec un vrai domaine :
echo.
echo 1. Installez IIS avec :
echo    - URL Rewrite Module
echo    - Application Request Routing (ARR)
echo.
echo 2. Obtenez un certificat SSL :
echo    - Let's Encrypt avec win-acme
echo    - Ou certificat commercial
echo.
echo 3. Utilisez le script PowerShell :
echo    setup_https_windows.ps1
echo.
pause
exit