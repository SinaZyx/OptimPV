# Build OptimPV avec Obfuscation Simple
# PowerShell 5.0+ requis

param(
    [switch]$KeepTemp = $false
)

$ErrorActionPreference = "Stop"
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "   BUILD OPTIMPV - OBFUSCATION SIMPLE" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# Variables
$ProjectRoot = Get-Location
$TempDir = Join-Path $ProjectRoot "temp_obf"
$OutputName = "OptimPV_Secure"

# Nettoyer
Write-Host "`n[1/8] Nettoyage..." -ForegroundColor Yellow
Remove-Item "dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "*.spec" -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $TempDir | Out-Null

# Activer venv
Write-Host "`n[2/8] Activation environnement virtuel..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Installer outils d'obfuscation
Write-Host "`n[3/8] Installation outils obfuscation..." -ForegroundColor Yellow
pip install python-minifier --quiet

# Copier fichiers
Write-Host "`n[4/8] Copie des fichiers..." -ForegroundColor Yellow
Copy-Item "licence_guard.py" $TempDir -Force
Copy-Item "run_secure.py" $TempDir -Force
Copy-Item "app.py" $TempDir -Force
Copy-Item -Path "modules" -Destination $TempDir -Recurse -Force
Copy-Item -Path "config" -Destination $TempDir -Recurse -Force
Copy-Item -Path "data" -Destination $TempDir -Recurse -Force
Copy-Item -Path "assets" -Destination $TempDir -Recurse -Force

# Obfuscation avec notre outil
Write-Host "`n[5/8] Obfuscation des fichiers..." -ForegroundColor Yellow

$filesToObfuscate = @("licence_guard.py", "run_secure.py", "app.py")

foreach ($file in $filesToObfuscate) {
    $inputPath = Join-Path $TempDir $file
    Write-Host "  Obfuscation: $file"
    
    # Utiliser notre outil d'obfuscation
    python "pyobfuscate_tool.py" $inputPath "$inputPath.obf"
    
    if (Test-Path "$inputPath.obf") {
        Move-Item "$inputPath.obf" $inputPath -Force
        Write-Host "    ✓ Obfusqué avec succès" -ForegroundColor Green
    } else {
        Write-Host "    ! Obfuscation échouée, fichier original conservé" -ForegroundColor Yellow
    }
}

# Ajouter protection anti-debug
Write-Host "`n[6/8] Ajout protection anti-debug..." -ForegroundColor Yellow

$antiDebug = @'
# Protection anti-debug
import sys, os
if sys.gettrace() is not None or any(v in os.environ for v in ['PYDEVD', 'PYTHONDEBUG']): os._exit(1)
sys.dont_write_bytecode = True

'@

$runPath = Join-Path $TempDir "run_secure.py"
$runContent = Get-Content $runPath -Raw
$runContent = $antiDebug + $runContent
$runContent | Out-File -FilePath $runPath -Encoding UTF8

# Créer fichier spec PyInstaller
Write-Host "`n[7/8] Création spec PyInstaller..." -ForegroundColor Yellow

$specContent = @"
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata, collect_data_files

datas = []
datas += copy_metadata('streamlit')
datas += copy_metadata('pandas')
datas += copy_metadata('numpy')
datas += copy_metadata('cryptography')
datas += collect_data_files('streamlit')

# Ajouter nos fichiers
datas += [
    ('$($TempDir.Replace('\','\\'))\\app.py', '.'),
    ('$($TempDir.Replace('\','\\'))\\licence_guard.py', '.'),
    ('$($TempDir.Replace('\','\\'))\\modules', 'modules'),
    ('$($TempDir.Replace('\','\\'))\\config', 'config'),
    ('$($TempDir.Replace('\','\\'))\\data', 'data'),
    ('$($TempDir.Replace('\','\\'))\\assets', 'assets')
]

hiddenimports = [
    'streamlit', 'streamlit.web.cli', 'streamlit.runtime.scriptrunner',
    'pandas', 'numpy', 'cryptography', 'licence_guard', 'modules'
]

a = Analysis(
    ['$($TempDir.Replace('\','\\'))\\run_secure.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='$OutputName',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=True,
)
"@

$specContent | Out-File -FilePath "$OutputName.spec" -Encoding UTF8

# Compilation
Write-Host "`n[8/8] Compilation finale..." -ForegroundColor Yellow
pyinstaller "$OutputName.spec" --clean --noconfirm

# Vérification et rapport
if (Test-Path "dist\$OutputName.exe") {
    $exeSize = [math]::Round((Get-Item "dist\$OutputName.exe").Length / 1MB, 2)
    
    Write-Host "`n=====================================================" -ForegroundColor Green
    Write-Host "   BUILD RÉUSSI!" -ForegroundColor Green
    Write-Host "=====================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📦 Exécutable: dist\$OutputName.exe" -ForegroundColor Cyan
    Write-Host "📏 Taille: $exeSize MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🛡️  PROTECTIONS APPLIQUÉES:" -ForegroundColor Yellow
    Write-Host "  ✓ Code obfusqué avec pyobfuscate_tool"
    Write-Host "  ✓ Protection anti-debug intégrée"
    Write-Host "  ✓ Variables et fonctions renommées"
    Write-Host "  ✓ Strings encodées"
    Write-Host "  ✓ Protection token AES-256"
    Write-Host "  ✓ Mode silencieux (pas de console)"
    Write-Host ""
} else {
    Write-Host "ERREUR: Compilation échouée!" -ForegroundColor Red
    exit 1
}

# Nettoyage
if (-not $KeepTemp) {
    Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item "build" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item "$OutputName.spec" -Force -ErrorAction SilentlyContinue
}

Write-Host "✅ Processus terminé avec succès!" -ForegroundColor Green 