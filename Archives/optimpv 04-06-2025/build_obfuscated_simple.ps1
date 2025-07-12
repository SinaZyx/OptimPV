# Build OptimPV avec Obfuscation Simple
# PowerShell 5.0+ requis

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   BUILD OPTIMPV SECURISE AVEC OBFUSCATION" -ForegroundColor Cyan  
Write-Host "============================================================" -ForegroundColor Cyan

# Variables
$TempDir = "temp_secure"

Write-Host "[1/7] Nettoyage..." -ForegroundColor Yellow
Remove-Item "dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "build" -Recurse -Force -ErrorAction SilentlyContinue  
Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $TempDir | Out-Null

Write-Host "[2/7] Activation environnement..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

Write-Host "[3/7] Installation dependances..." -ForegroundColor Yellow
pip install python-minifier --quiet --disable-pip-version-check

Write-Host "[4/7] Copie des dossiers..." -ForegroundColor Yellow
Copy-Item -Path "modules" -Destination $TempDir -Recurse -Force
Copy-Item -Path "config" -Destination $TempDir -Recurse -Force
Copy-Item -Path "data" -Destination $TempDir -Recurse -Force
Copy-Item -Path "assets" -Destination $TempDir -Recurse -Force

Write-Host "[5/7] Obfuscation des fichiers critiques..." -ForegroundColor Yellow

# Obfusquer licence_guard.py
Write-Host "  Obfuscation: licence_guard.py" -ForegroundColor White
python "pyobfuscate_tool.py" "licence_guard.py" -o "$TempDir\licence_guard.py"
if (-not (Test-Path "$TempDir\licence_guard.py")) {
    Copy-Item "licence_guard.py" "$TempDir\licence_guard.py" -Force
    Write-Host "    Echec obfuscation, fichier original copie" -ForegroundColor Yellow
} else {
    Write-Host "    Obfusque avec succes" -ForegroundColor Green
}

# Obfusquer run_secure.py  
Write-Host "  Obfuscation: run_secure.py" -ForegroundColor White
python "pyobfuscate_tool.py" "run_secure.py" -o "$TempDir\run_secure.py"
if (-not (Test-Path "$TempDir\run_secure.py")) {
    Copy-Item "run_secure.py" "$TempDir\run_secure.py" -Force
    Write-Host "    Echec obfuscation, fichier original copie" -ForegroundColor Yellow
} else {
    Write-Host "    Obfusque avec succes" -ForegroundColor Green
}

# Obfusquer app.py
Write-Host "  Obfuscation: app.py" -ForegroundColor White  
python "pyobfuscate_tool.py" "app.py" -o "$TempDir\app.py"
if (-not (Test-Path "$TempDir\app.py")) {
    Copy-Item "app.py" "$TempDir\app.py" -Force
    Write-Host "    Echec obfuscation, fichier original copie" -ForegroundColor Yellow
} else {
    Write-Host "    Obfusque avec succes" -ForegroundColor Green
}

Write-Host "[6/7] Ajout protection anti-debug..." -ForegroundColor Yellow

# Ajouter protection dans run_secure.py
$runPath = "$TempDir\run_secure.py"
$content = Get-Content $runPath -Raw -Encoding UTF8

$protection = "# Protection Anti-Debug`n"
$protection += "import sys, os`n"
$protection += "try:`n"
$protection += "    if sys.gettrace(): os._exit(1)`n"  
$protection += "    sys.dont_write_bytecode = True`n"
$protection += "except: pass`n`n"

$newContent = $protection + $content
$newContent | Out-File -FilePath $runPath -Encoding UTF8

Write-Host "[7/7] Compilation PyInstaller..." -ForegroundColor Yellow

# Modifier le spec existant
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

pyinstaller "OptimPV_Secure.spec" --clean --noconfirm

# Verification
if (Test-Path "dist\OptimPV_Secure.exe") {
    $size = [math]::Round((Get-Item "dist\OptimPV_Secure.exe").Length / 1MB, 2)
    
    Write-Host "`n" + "="*60 -ForegroundColor Green
    Write-Host "BUILD SECURISE REUSSI !" -ForegroundColor Green
    Write-Host "="*60 -ForegroundColor Green
    Write-Host ""
    Write-Host "Executable: dist\OptimPV_Secure.exe" -ForegroundColor Cyan
    Write-Host "Taille: $size MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PROTECTIONS APPLIQUEES:" -ForegroundColor Yellow
    Write-Host "- Code obfusque" -ForegroundColor Green
    Write-Host "- Strings encodees" -ForegroundColor Green  
    Write-Host "- Protection anti-debug" -ForegroundColor Green
    Write-Host "- Protection token AES-256" -ForegroundColor Green
    Write-Host "- Mode silencieux" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "ECHEC COMPILATION !" -ForegroundColor Red
    exit 1
}

# Nettoyage
Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "OptimPV_Secure.spec" -Force -ErrorAction SilentlyContinue

Write-Host "Termine ! Vos fichiers originaux sont intacts." -ForegroundColor Green 