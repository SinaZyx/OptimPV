# BUILD OptimPV - Script Principal de Compilation
# PowerShell 5.0+ required

$ErrorActionPreference = "Stop"
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   BUILD OptimPV - Version de Production" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# ===== CONFIGURATION =====
$MainScript = "server_controller.py"
$OutputName = "OptimPV"
$VenvPath = ".\venv\Scripts\Activate.ps1"

# Hidden imports essentiels
$HiddenImports = @(
    "streamlit.web.cli",
    "streamlit.runtime.scriptrunner",
    "licence_guard",
    "cryptography.fernet",
    "pandas",
    "numpy",
    "seaborn",
    "psutil",
    "tkinter.ttk",
    "multiprocessing"
)

# ===== STEP 1: ACTIVATION ENVIRONNEMENT =====
Write-Host "`n[1/4] Activation environnement virtuel..." -ForegroundColor Yellow
if (Test-Path $VenvPath) {
    & $VenvPath
} else {
    Write-Host "ERREUR: Environnement virtuel introuvable!" -ForegroundColor Red
    exit 1
}

# ===== STEP 2: NETTOYAGE =====
Write-Host "`n[2/4] Nettoyage..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force -ErrorAction SilentlyContinue }
if (Test-Path "build") { Remove-Item "build" -Recurse -Force -ErrorAction SilentlyContinue }
if (Test-Path "*.spec") { Remove-Item "*.spec" -Force -ErrorAction SilentlyContinue }

# ===== STEP 3: COMPILATION =====
Write-Host "`n[3/4] Compilation avec PyInstaller..." -ForegroundColor Yellow

$CurrentDir = Get-Location
$PyInstallerCmd = "pyinstaller --noconfirm --onefile --windowed"
$PyInstallerCmd += " --name `"$OutputName`""
$PyInstallerCmd += " --distpath `"$CurrentDir\dist`""

# Icone
if (Test-Path "assets\icon.ico") {
    $PyInstallerCmd += " --icon `"assets\icon.ico`""
}

# Donnees essentielles
foreach ($dir in @("assets", "config", "modules")) {
    if (Test-Path $dir) {
        $PyInstallerCmd += " --add-data `"$dir;$dir`""
    }
}

# Application Streamlit principale
if (Test-Path "app.py") {
    $PyInstallerCmd += " --add-data `"app.py;.`""
}

# Imports caches
foreach ($import in $HiddenImports) {
    $PyInstallerCmd += " --hidden-import `"$import`""
}

$PyInstallerCmd += " --log-level WARN --clean"
$PyInstallerCmd += " `"$MainScript`""

Write-Host "  Compilation en cours..." -ForegroundColor Cyan
Invoke-Expression $PyInstallerCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "  [x] Echec compilation!" -ForegroundColor Red
    exit 1
}

# ===== STEP 4: VERIFICATION =====
Write-Host "`n[4/4] Verification..." -ForegroundColor Yellow

$FinalExePath = "dist\$OutputName.exe"
if (Test-Path $FinalExePath) {
    $exeInfo = Get-Item $FinalExePath
    $exeSize = [math]::Round($exeInfo.Length / 1MB, 2)
    $exeDate = $exeInfo.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
    
    # Nettoyage final
    Remove-Item "*.spec" -Force -ErrorAction SilentlyContinue
    if (Test-Path "build") { Remove-Item "build" -Recurse -Force -ErrorAction SilentlyContinue }
    
    Write-Host "`n" + "="*50 -ForegroundColor Green
    Write-Host "BUILD REUSSI!" -ForegroundColor Green
    Write-Host "="*50 -ForegroundColor Green
    Write-Host ""
    Write-Host "EXECUTABLE PRET:" -ForegroundColor Cyan
    Write-Host "  $FinalExePath" -ForegroundColor White
    Write-Host "  Taille: $exeSize MB" -ForegroundColor White
    Write-Host "  Date: $exeDate" -ForegroundColor White
    Write-Host ""
    Write-Host "UTILISATION:" -ForegroundColor Cyan
    Write-Host "  1. Lancer OptimPV.exe" -ForegroundColor White
    Write-Host "  2. Cliquer 'START Serveur'" -ForegroundColor White
    Write-Host "  3. Utiliser l'application dans le navigateur" -ForegroundColor White
    Write-Host ""
    Write-Host "="*50 -ForegroundColor Green
}
else {
    Write-Host "`nECHEC - Executable non trouve" -ForegroundColor Red
}