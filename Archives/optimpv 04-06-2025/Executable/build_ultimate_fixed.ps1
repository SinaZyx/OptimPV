# Build Simple OptimPV - Sans PyArmor
# PowerShell 5.0+ requis

$ErrorActionPreference = "Stop"
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   BUILD SIMPLE OptimPV - Sans Obfuscation" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Variables
$OutputName = "OptimPV"

# Activer venv
Write-Host "`n[1/3] Activation environnement..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Nettoyer
Write-Host "`n[2/3] Nettoyage..." -ForegroundColor Yellow
Remove-Item "dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "*.spec" -Force -ErrorAction SilentlyContinue

# Créer le fichier spec avec les métadonnées
Write-Host "`n[3/3] Creation du fichier spec avec metadonnees..." -ForegroundColor Yellow

$specContent = @'
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata, collect_data_files, collect_submodules

# Collecter les métadonnées nécessaires
datas = []
datas += copy_metadata('streamlit')
datas += copy_metadata('streamlit-option-menu', recursive=True)
datas += copy_metadata('validators')
datas += copy_metadata('pyarrow')
datas += copy_metadata('altair')
datas += copy_metadata('plotly')
datas += copy_metadata('pandas')
datas += copy_metadata('numpy')
datas += copy_metadata('cryptography')
datas += copy_metadata('rich')
datas += copy_metadata('tzlocal')
datas += copy_metadata('importlib_metadata')
datas += copy_metadata('seaborn')
datas += copy_metadata('matplotlib')
datas += copy_metadata('scipy')

# Collecter les fichiers de données Streamlit
datas += collect_data_files('streamlit')
datas += collect_data_files('streamlit_option_menu')
datas += collect_data_files('seaborn')

# Ajouter les fichiers de l'application
datas += [
    ('app.py', '.'),
    ('licence_guard.py', '.'),
    ('modules', 'modules'),
    ('config', 'config'),
    ('data', 'data'),
    ('assets', 'assets')
]

# Collecter tous les sous-modules
hiddenimports = []
hiddenimports += collect_submodules('streamlit')
hiddenimports += collect_submodules('seaborn')
hiddenimports += [
    'streamlit.web.cli',
    'streamlit.runtime.scriptrunner',
    'streamlit.runtime.state',
    'streamlit_option_menu',
    'licence_guard',
    'cryptography',
    'cryptography.fernet',
    'winreg',
    'pandas',
    'numpy',
    'plotly',
    'plotly.express',
    'plotly.graph_objects',
    'seaborn',
    'seaborn.objects',
    'matplotlib',
    'matplotlib.pyplot',
    'scipy',
    'scipy.stats',
    'modules',
    'modules.reporting',
    'validators.url',
    'validators.domain',
    'validators.email',
    'pyarrow',
    'pyarrow.parquet',
    'importlib_metadata',
    'tzlocal',
    'tzlocal.windows_tz',
]

a = Analysis(
    ['run_secure.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='OptimPV',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'@

# Écrire le fichier spec
$specContent | Out-File -FilePath "OptimPV.spec" -Encoding utf8

# Compilation PyInstaller
Write-Host "`nCompilation avec PyInstaller..." -ForegroundColor Yellow
& pyinstaller "OptimPV.spec" --clean --noconfirm

# Vérification et résumé
if (Test-Path "dist\$OutputName.exe") {
    $exeSize = [math]::Round((Get-Item "dist\$OutputName.exe").Length / 1MB, 2)
    
    Write-Host "`n" + "="*60 -ForegroundColor Green
    Write-Host "BUILD REUSSI !" -ForegroundColor Green
    Write-Host "="*60 -ForegroundColor Green
    Write-Host ""
    Write-Host "Executable : dist\$OutputName.exe" -ForegroundColor Cyan
    Write-Host "Taille : $exeSize MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PROTECTION ACTIVE :" -ForegroundColor Yellow
    Write-Host "[+] Token sys.dat requis" -ForegroundColor Green
    Write-Host "[+] Autodestruction si pas de licence" -ForegroundColor Green
    Write-Host "[+] Mode silencieux (pas de console)" -ForegroundColor Green
    Write-Host "[+] Chiffrement AES-256" -ForegroundColor Green
    Write-Host ""
}
else {
    Write-Host "ECHEC BUILD" -ForegroundColor Red
    exit 1
}