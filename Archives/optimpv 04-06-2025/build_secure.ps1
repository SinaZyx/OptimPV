# Build OptimPV Sécurisé avec Obfuscation
# PowerShell 5.0+ requis

$ErrorActionPreference = "Stop"
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   BUILD OPTIMPV SÉCURISÉ - AVEC OBFUSCATION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Variables
$TempDir = "temp_secure"

# Nettoyer
Write-Host "`n[1/6] Nettoyage..." -ForegroundColor Yellow
Remove-Item "dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $TempDir | Out-Null

# Activer venv
Write-Host "`n[2/6] Activation environnement..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Installer python-minifier si pas présent
Write-Host "`n[3/6] Vérification dépendances..." -ForegroundColor Yellow
pip install python-minifier --quiet --disable-pip-version-check

# Copier les fichiers sources
Write-Host "`n[4/6] Copie et obfuscation des fichiers..." -ForegroundColor Yellow

# Copier les dossiers
Copy-Item -Path "modules" -Destination $TempDir -Recurse -Force
Copy-Item -Path "config" -Destination $TempDir -Recurse -Force
Copy-Item -Path "data" -Destination $TempDir -Recurse -Force
Copy-Item -Path "assets" -Destination $TempDir -Recurse -Force

# Obfusquer les fichiers critiques
$filesToObfuscate = @("licence_guard.py", "run_secure.py", "app.py")

foreach ($file in $filesToObfuscate) {
    Write-Host "  Obfuscation: $file" -ForegroundColor White
    
    # Obfusquer avec notre outil
    python "pyobfuscate_tool.py" $file "$TempDir\$file" --aggressive
    
    if (Test-Path "$TempDir\$file") {
        Write-Host "    ✓ Obfusqué avec succès" -ForegroundColor Green
    } else {
        Write-Host "    ! Échec, copie du fichier original" -ForegroundColor Yellow
        Copy-Item $file "$TempDir\$file" -Force
    }
}

# Ajouter protection anti-debug au fichier run_secure
Write-Host "`n[5/6] Ajout protection anti-debug..." -ForegroundColor Yellow

$runSecurePath = "$TempDir\run_secure.py"
$originalContent = Get-Content $runSecurePath -Raw -Encoding UTF8

# Ajouter protection anti-debug
$antiDebugLines = @(
    "# Protection Anti-Debug et Anti-Analyse",
    "import sys, os",
    "try:",
    "    if sys.gettrace() or any(v in os.environ for v in ['PYDEVD','PYTHONDEBUG','PYTHONINSPECT']):",
    "        os._exit(1)",
    "    sys.dont_write_bytecode = True",
    "except: pass",
    ""
)

$protectedContent = ($antiDebugLines -join "`n") + $originalContent
$protectedContent | Out-File -FilePath $runSecurePath -Encoding UTF8

# Creer fichier spec optimise
Write-Host "`n[6/6] Compilation avec PyInstaller..." -ForegroundColor Yellow

# Utiliser le fichier spec existant mais modifier le chemin
$specContent = Get-Content "OptimPV.spec" -Raw
$specContent = $specContent.Replace("['run_secure.py']", "['$TempDir\run_secure.py']")
$specContent = $specContent.Replace("('app.py', '.')", "('$TempDir\app.py', '.')")
$specContent = $specContent.Replace("('licence_guard.py', '.')", "('$TempDir\licence_guard.py', '.')")
$specContent = $specContent.Replace("('modules', 'modules')", "('$TempDir\modules', 'modules')")
$specContent = $specContent.Replace("('config', 'config')", "('$TempDir\config', 'config')")
$specContent = $specContent.Replace("('data', 'data')", "('$TempDir\data', 'data')")
$specContent = $specContent.Replace("('assets', 'assets')", "('$TempDir\assets', 'assets')")
$specContent = $specContent.Replace("name='OptimPV'", "name='OptimPV_Secure'")

$specContent | Out-File -FilePath "OptimPV_Secure.spec" -Encoding UTF8

# Compilation
pyinstaller "OptimPV_Secure.spec" --clean --noconfirm

# Vérification
if (Test-Path "dist\OptimPV_Secure.exe") {
    $exeSize = [math]::Round((Get-Item "dist\OptimPV_Secure.exe").Length / 1MB, 2)
    
    Write-Host "`n" + "="*60 -ForegroundColor Green
    Write-Host "BUILD SÉCURISÉ RÉUSSI !" -ForegroundColor Green
    Write-Host "="*60 -ForegroundColor Green
    Write-Host ""
    Write-Host "Executable : dist\OptimPV_Secure.exe" -ForegroundColor Cyan
    Write-Host "Taille : $exeSize MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PROTECTIONS APPLIQUEES :" -ForegroundColor Yellow
    Write-Host "[+] Code obfusque (variables/fonctions renommees)" -ForegroundColor Green
    Write-Host "[+] Strings encodees Base64+XOR" -ForegroundColor Green
    Write-Host "[+] Protection anti-debug integree" -ForegroundColor Green
    Write-Host "[+] Protection token AES-256" -ForegroundColor Green
    Write-Host "[+] Autodestruction si pas de licence" -ForegroundColor Green
    Write-Host "[+] Mode silencieux (pas de console)" -ForegroundColor Green
    Write-Host ""
    Write-Host "POUR TESTER :" -ForegroundColor Yellow
    Write-Host "1. python create_token_admin.py" -ForegroundColor White
    Write-Host "2. Placer sys.dat dans un emplacement" -ForegroundColor White
    Write-Host "3. Lancer OptimPV_Secure.exe" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "ÉCHEC DE LA COMPILATION !" -ForegroundColor Red
    exit 1
}

# Nettoyage
Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "OptimPV_Secure.spec" -Force -ErrorAction SilentlyContinue

Write-Host "Termine ! Vos fichiers originaux sont intacts." -ForegroundColor Green 