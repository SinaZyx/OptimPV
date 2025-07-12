# Build Final OptimPV avec Protection Token
# PowerShell 5.0+ requis

param(
    [switch]$SkipClean = $false,
    [switch]$SkipUPX = $false
)

$ErrorActionPreference = "Stop"
$StartTime = Get-Date

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "   BUILD FINAL OptimPV avec Protection Token" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# Variables
$ProjectRoot = Get-Location
$VenvPath = Join-Path $ProjectRoot "venv"
$OutputName = "OptimPV_Protected"

# Nettoyage
if (-not $SkipClean) {
    Write-Host "`n[1/6] Nettoyage..." -ForegroundColor Yellow
    Remove-Item "dist" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item "build" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item "*.spec" -Force -ErrorAction SilentlyContinue
}

# Activer venv
Write-Host "`n[2/6] Activation environnement..." -ForegroundColor Yellow
& "$VenvPath\Scripts\Activate.ps1"

# Vérifier les fichiers de protection
Write-Host "`n[3/6] Vérification protection..." -ForegroundColor Yellow
$requiredFiles = @("licence_guard.py", "run.py", "app.py")
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ ERREUR: $file manquant" -ForegroundColor Red
        exit 1
    }
}
Write-Host "✅ Fichiers de protection présents" -ForegroundColor Green

# Fix scipy
Write-Host "`n[4/6] Fix scipy..." -ForegroundColor Yellow
if (Test-Path "patch_scipy.py") {
    python patch_scipy.py
    Write-Host "✅ Scipy patché" -ForegroundColor Green
}

# Build PyInstaller
Write-Host "`n[5/6] Compilation PyInstaller..." -ForegroundColor Yellow

pyinstaller --onefile `
    --name $OutputName `
    --hidden-import=streamlit `
    --hidden-import=streamlit.web.cli `
    --hidden-import=pandas `
    --hidden-import=numpy `
    --hidden-import=scipy `
    --hidden-import=scipy.stats `
    --hidden-import=seaborn `
    --hidden-import=matplotlib `
    --hidden-import=plotly `
    --hidden-import=sklearn `
    --hidden-import=openpyxl `
    --hidden-import=cryptography `
    --hidden-import=cryptography.hazmat.primitives.ciphers `
    --hidden-import=cryptography.hazmat.primitives.padding `
    --hidden-import=licence_guard `
    --hidden-import=modules `
    --hidden-import=modules.config `
    --hidden-import=modules.data_import `
    --hidden-import=modules.visualization `
    --hidden-import=modules.reporting `
    --hidden-import=modules.storage `
    --hidden-import=modules.engine_module `
    --hidden-import=modules.optimisation_analyse `
    --add-data="app.py;." `
    --add-data="licence_guard.py;." `
    --add-data="modules;modules" `
    --add-data="config;config" `
    --add-data="data;data" `
    --add-data="assets;assets" `
    --exclude-module=tkinter `
    --exclude-module=PyQt5 `
    --exclude-module=PyQt6 `
    --exclude-module=PySide2 `
    --exclude-module=PySide6 `
    --exclude-module=create_token_admin `
    --exclude-module=test_token `
    --exclude-module=debug_token `
    --windowed `
    --clean `
    --noconfirm `
    run.py

# Vérification
if (Test-Path "dist\$OutputName.exe") {
    $exeSize = [math]::Round((Get-Item "dist\$OutputName.exe").Length / 1MB, 2)
    Write-Host "✅ Exécutable créé: $exeSize MB" -ForegroundColor Green
    
    # Compression UPX
    if (-not $SkipUPX) {
        Write-Host "`n[6/6] Compression UPX..." -ForegroundColor Yellow
        
        # Télécharger UPX si nécessaire
        $upxPath = "upx.exe"
        if (-not (Test-Path $upxPath)) {
            Write-Host "  Téléchargement UPX..."
            $upxUrl = "https://github.com/upx/upx/releases/download/v4.0.2/upx-4.0.2-win64.zip"
            $upxZip = "upx.zip"
            
            try {
                Invoke-WebRequest -Uri $upxUrl -OutFile $upxZip
                Expand-Archive -Path $upxZip -DestinationPath "." -Force
                Move-Item "upx-*\upx.exe" $upxPath -Force
                Remove-Item $upxZip -Force
                Remove-Item "upx-*" -Recurse -Force
                Write-Host "  ✅ UPX téléchargé" -ForegroundColor Green
            }
            catch {
                Write-Host "  ⚠️ Impossible de télécharger UPX" -ForegroundColor Yellow
            }
        }
        
        if (Test-Path $upxPath) {
            Write-Host "  Compression en cours..."
            $sizeBefore = $exeSize
            
            try {
                & .\upx.exe --best --lzma "dist\$OutputName.exe" 2>$null
                $sizeAfter = [math]::Round((Get-Item "dist\$OutputName.exe").Length / 1MB, 2)
                $reduction = [math]::Round((($sizeBefore - $sizeAfter) / $sizeBefore) * 100, 1)
                Write-Host "  ✅ Compressé: $sizeBefore MB → $sizeAfter MB (-$reduction%)" -ForegroundColor Green
            }
            catch {
                Write-Host "  ⚠️ Erreur compression UPX" -ForegroundColor Yellow
            }
        }
    }
    
    # Résumé final
    $EndTime = Get-Date
    $Duration = [math]::Round(($EndTime - $StartTime).TotalMinutes, 1)
    $FinalSize = [math]::Round((Get-Item "dist\$OutputName.exe").Length / 1MB, 2)
    
    Write-Host "`n" + "="*60 -ForegroundColor Green
    Write-Host "✅ BUILD RÉUSSI !" -ForegroundColor Green
    Write-Host "="*60 -ForegroundColor Green
    Write-Host ""
    Write-Host "📦 Exécutable : dist\$OutputName.exe" -ForegroundColor Cyan
    Write-Host "📏 Taille finale : $FinalSize MB" -ForegroundColor Cyan
    Write-Host "⏱️  Durée : $Duration minutes" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🔐 PROTECTION ACTIVE :" -ForegroundColor Yellow
    Write-Host "  ✅ Token sys.dat requis au démarrage" -ForegroundColor White
    Write-Host "  ✅ Autodestruction si token manquant/invalide" -ForegroundColor White
    Write-Host "  ✅ Recherche multi-emplacements (USB, PROGRAMDATA, racine)" -ForegroundColor White
    Write-Host "  ✅ Chiffrement AES-256 + validation SHA-256/SHA-512" -ForegroundColor White
    Write-Host ""
    Write-Host "📝 ÉTAPES SUIVANTES :" -ForegroundColor Red
    Write-Host "  1️⃣ Créer le token : python create_token_admin.py" -ForegroundColor Cyan
    Write-Host "  2️⃣ Placer sys.dat sur clé USB ou dans PROGRAMDATA\OptimPV\" -ForegroundColor Cyan
    Write-Host "  3️⃣ Tester l'exécutable" -ForegroundColor Cyan
    Write-Host ""
    
    # Son de notification
    try {
        [System.Media.SystemSounds]::Asterisk.Play()
    } catch {}
    
} else {
    Write-Host "❌ ÉCHEC BUILD - Exécutable non créé" -ForegroundColor Red
    exit 1
} 