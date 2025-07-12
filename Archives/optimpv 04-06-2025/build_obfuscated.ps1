# Build OptimPV avec Obfuscation Gratuite Multi-Couches
# PowerShell 5.0+ requis

param(
    [switch]$SkipVenv = $false,
    [switch]$SkipDependencies = $false,
    [switch]$KeepTemp = $false,
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"
$StartTime = Get-Date

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "   BUILD OPTIMPV - OBFUSCATION GRATUITE" -ForegroundColor Cyan
Write-Host "   Protection + Obfuscation Multi-Couches" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# Variables
$ProjectRoot = Get-Location
$VenvPath = Join-Path $ProjectRoot "venv"
$TempDir = Join-Path $ProjectRoot "temp_obfuscated"
$OutputName = "OptimPV_Secure"

# Nettoyer
Write-Host "`n[1/12] Nettoyage..." -ForegroundColor Yellow
Remove-Item "dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $TempDir | Out-Null

# Activer venv
if (-not $SkipVenv) {
    Write-Host "`n[2/12] Activation environnement virtuel..." -ForegroundColor Yellow
    if (-not (Test-Path $VenvPath)) {
        python -m venv $VenvPath
    }
    & "$VenvPath\Scripts\Activate.ps1"
}

# Installer dépendances
if (-not $SkipDependencies) {
    Write-Host "`n[3/12] Installation dépendances..." -ForegroundColor Yellow
    pip install --upgrade pip
    
    # Dépendances application
    pip install streamlit pandas numpy scipy seaborn matplotlib plotly scikit-learn openpyxl cryptography
    
    # Outils d'obfuscation gratuits
    pip install python-minifier
    pip install Cython
}

# Créer l'obfuscateur Python personnalisé
Write-Host "`n[4/12] Création obfuscateur personnalisé..." -ForegroundColor Yellow

$obfuscatorScript = @'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Obfuscateur Python personnalisé pour OptimPV"""

import os
import re
import ast
import base64
import random
import string
import hashlib
import marshal
import zlib
from typing import Dict, List, Set

class AdvancedObfuscator:
    def __init__(self):
        self.var_mapping = {}
        self.func_mapping = {}
        self.class_mapping = {}
        self.string_cache = {}
        self.protected_names = {
            # Streamlit
            'st', 'session_state', 'sidebar', 'columns', 'button', 'selectbox',
            'markdown', 'write', 'error', 'success', 'warning', 'info',
            # Python builtins
            '__init__', '__main__', '__name__', '__file__', '__doc__',
            'self', 'cls', 'args', 'kwargs', 'print', 'open', 'len',
            # Nos modules
            'LicenceGuard', 'initialize_protection', 'check_and_protect',
            'self_destruct', 'validate_token', 'decrypt_token'
        }
        
    def generate_name(self, prefix=''):
        """Génère un nom aléatoire difficile à lire"""
        # Mix de l, I, 1, O, 0 pour confusion visuelle
        chars = 'lI10O' + string.ascii_letters
        length = random.randint(8, 15)
        name = prefix + ''.join(random.choice(chars) for _ in range(length))
        return name
    
    def encode_string(self, s):
        """Encode une chaîne avec plusieurs couches"""
        # Couche 1: Base64
        b64 = base64.b64encode(s.encode()).decode()
        
        # Couche 2: XOR avec clé
        key = random.randint(1, 255)
        xored = ''.join(chr(ord(c) ^ key) for c in b64)
        
        # Couche 3: Hex
        hexed = xored.encode().hex()
        
        # Décoder au runtime
        decoder = f"''.join(chr(ord(c)^{key}) for c in bytes.fromhex('{hexed}').decode())"
        return f"__import__('base64').b64decode({decoder}).decode()"
    
    def obfuscate_numbers(self, code):
        """Remplace les nombres par des expressions"""
        def replace_number(match):
            num = int(match.group())
            if num == 0:
                return "(len([]))"
            elif num == 1:
                return "(int(True))"
            elif num < 10:
                return f"(len('{random.choice(string.ascii_letters)*num}'))"
            else:
                # Expression mathématique
                a = random.randint(1, num//2)
                b = num - a
                return f"({a}+{b})"
        
        return re.sub(r'\b\d+\b', replace_number, code)
    
    def add_junk_code(self, code):
        """Ajoute du code inutile mais valide"""
        junk_snippets = [
            "if False: exec('')",
            "[None for _ in range(0)]",
            "lambda:None",
            "{}.get('', '')",
            "'' if True else ''",
        ]
        
        lines = code.split('\n')
        result = []
        
        for line in lines:
            result.append(line)
            # Ajouter du junk occasionnellement
            if random.random() < 0.1 and line.strip() and not line.strip().startswith('#'):
                indent = len(line) - len(line.lstrip())
                junk = random.choice(junk_snippets)
                result.append(' ' * indent + junk)
        
        return '\n'.join(result)
    
    def obfuscate_file(self, filepath):
        """Obfusque un fichier Python"""
        print(f"  Obfuscation: {os.path.basename(filepath)}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            original_code = f.read()
        
        # Parse AST pour identifier les variables/fonctions
        try:
            tree = ast.parse(original_code)
        except:
            print(f"    ! Erreur parsing AST, obfuscation basique")
            return self.basic_obfuscate(original_code)
        
        # Collecter les noms à obfusquer
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id not in self.protected_names:
                if node.id not in self.var_mapping:
                    self.var_mapping[node.id] = self.generate_name('v_')
            elif isinstance(node, ast.FunctionDef) and node.name not in self.protected_names:
                if node.name not in self.func_mapping:
                    self.func_mapping[node.name] = self.generate_name('f_')
            elif isinstance(node, ast.ClassDef) and node.name not in self.protected_names:
                if node.name not in self.class_mapping:
                    self.class_mapping[node.name] = self.generate_name('c_')
        
        # Appliquer les transformations
        obfuscated = original_code
        
        # 1. Remplacer les noms
        for old, new in {**self.var_mapping, **self.func_mapping, **self.class_mapping}.items():
            # Utiliser regex pour remplacer uniquement les mots entiers
            pattern = r'\b' + re.escape(old) + r'\b'
            obfuscated = re.sub(pattern, new, obfuscated)
        
        # 2. Encoder les strings
        def encode_match(match):
            s = match.group(1) or match.group(2)
            if len(s) > 3 and not s.startswith('__'):
                return self.encode_string(s)
            return match.group(0)
        
        obfuscated = re.sub(r"'([^']*)'|\"([^\"]*)\"", encode_match, obfuscated)
        
        # 3. Obfusquer les nombres
        obfuscated = self.obfuscate_numbers(obfuscated)
        
        # 4. Ajouter du code inutile
        obfuscated = self.add_junk_code(obfuscated)
        
        # 5. Ajouter header de protection
        protection_header = '''# -*- coding: utf-8 -*-
# Protected by OptimPV Security System
__all__ = []
__version__ = '0.0.0'
import sys as _s;_s.dont_write_bytecode=True
'''
        
        return protection_header + obfuscated
    
    def basic_obfuscate(self, code):
        """Obfuscation basique si AST échoue"""
        # Remplacer les commentaires
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        
        # Compresser les espaces
        code = re.sub(r'\n\s*\n', '\n', code)
        
        # Ajouter compression
        compressed = zlib.compress(code.encode())
        b64 = base64.b64encode(compressed).decode()
        
        return f'''import zlib,base64;exec(zlib.decompress(base64.b64decode("{b64}")))'''

def main():
    import sys
    if len(sys.argv) < 3:
        print("Usage: obfuscator.py <input_file> <output_file>")
        return
    
    obf = AdvancedObfuscator()
    result = obf.obfuscate_file(sys.argv[1])
    
    with open(sys.argv[2], 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"    ✓ Obfusqué: {os.path.basename(sys.argv[2])}")

if __name__ == "__main__":
    main()
'@

$obfuscatorScript | Out-File -FilePath "$TempDir\obfuscator.py" -Encoding UTF8

# Copier les fichiers sources
Write-Host "`n[5/12] Copie des fichiers sources..." -ForegroundColor Yellow
Copy-Item "licence_guard.py" $TempDir -Force
Copy-Item "run_secure.py" $TempDir -Force
Copy-Item "app.py" $TempDir -Force
Copy-Item -Path "modules" -Destination $TempDir -Recurse -Force
Copy-Item -Path "config" -Destination $TempDir -Recurse -Force
Copy-Item -Path "data" -Destination $TempDir -Recurse -Force
Copy-Item -Path "assets" -Destination $TempDir -Recurse -Force
Copy-Item -Path "hooks" -Destination $TempDir -Recurse -Force -ErrorAction SilentlyContinue

# Obfuscation multi-couches
Write-Host "`n[6/12] Obfuscation des fichiers critiques..." -ForegroundColor Yellow

# Liste des fichiers à obfusquer
$filesToObfuscate = @(
    "licence_guard.py",
    "run_secure.py",
    "app.py"
)

# Obfusquer chaque fichier
foreach ($file in $filesToObfuscate) {
    $inputPath = Join-Path $TempDir $file
    $outputPath = Join-Path $TempDir ($file -replace '\.py$', '_obf.py')
    
    Write-Host "  Obfuscation: $file"
    
    # Étape 1: Notre obfuscateur personnalisé
    python "$TempDir\obfuscator.py" $inputPath $outputPath
    
    # Étape 2: python-minifier
    try {
        $minified = & python -m python_minifier $outputPath --rename-globals --remove-literal-statements
        $minified | Out-File -FilePath $inputPath -Encoding UTF8
        Remove-Item $outputPath -Force
    }
    catch {
        Write-Host "    ! python-minifier échoué, utilisation version obfusquée simple" -ForegroundColor Yellow
        Move-Item $outputPath $inputPath -Force
    }
}

# Obfusquer les modules
Write-Host "`n[7/12] Obfuscation des modules..." -ForegroundColor Yellow
$moduleFiles = Get-ChildItem -Path "$TempDir\modules" -Filter "*.py" -Recurse

foreach ($moduleFile in $moduleFiles) {
    Write-Host "  Module: $($moduleFile.Name)"
    
    try {
        # Minifier seulement (pas d'obfuscation lourde pour les modules)
        $content = Get-Content $moduleFile.FullName -Raw
        $minified = & python -m python_minifier $moduleFile.FullName --remove-literal-statements
        $minified | Out-File -FilePath $moduleFile.FullName -Encoding UTF8
    }
    catch {
        Write-Host "    ! Minification échouée, fichier conservé" -ForegroundColor Yellow
    }
}

# Compilation Cython optionnelle pour modules critiques
Write-Host "`n[8/12] Compilation Cython (optionnel)..." -ForegroundColor Yellow
$cythonSetup = @'
from setuptools import setup
from Cython.Build import cythonize
import sys

modules = ["licence_guard.py"]
setup(
    ext_modules = cythonize(modules, 
                           compiler_directives={'language_level': "3"})
)
'@

try {
    $cythonSetup | Out-File -FilePath "$TempDir\setup_cython.py" -Encoding UTF8
    Push-Location $TempDir
    python setup_cython.py build_ext --inplace 2>$null
    Pop-Location
    
    # Si compilation réussie, utiliser le .pyd
    if (Test-Path "$TempDir\licence_guard*.pyd") {
        Write-Host "  ✓ Module licence_guard compilé en Cython" -ForegroundColor Green
        Remove-Item "$TempDir\licence_guard.py" -Force
    }
}
catch {
    Write-Host "  ! Compilation Cython échouée, conservation Python" -ForegroundColor Yellow
}

# Ajouter anti-debug
Write-Host "`n[9/12] Ajout protections anti-debug..." -ForegroundColor Yellow

$antiDebugCode = @'
# Anti-debug protection
import sys, os

def anti_debug():
    # Détection debugger
    if sys.gettrace() is not None:
        os._exit(1)
    
    # Variables environnement suspects
    debug_vars = ['PYDEVD', 'PYTHONDEBUG', 'PYTHONINSPECT']
    if any(var in os.environ for var in debug_vars):
        os._exit(1)
    
    # Trace hooks
    sys.settrace(None)
    
    # Désactiver bytecode
    sys.dont_write_bytecode = True

anti_debug()
'@

# Injecter anti-debug dans run.py
$runContent = Get-Content "$TempDir\run_secure.py" -Raw
$runContent = $antiDebugCode + "`n" + $runContent
$runContent | Out-File -FilePath "$TempDir\run_secure.py" -Encoding UTF8

# Créer spec PyInstaller
Write-Host "`n[10/12] Préparation PyInstaller..." -ForegroundColor Yellow

$specContent = @"
# -*- mode: python ; coding: utf-8 -*-
import sys
sys.setrecursionlimit(5000)

block_cipher = None

a = Analysis(
    ['$TempDir/run_secure.py'],
    pathex=['$TempDir'],
    binaries=[],
    datas=[
        ('$TempDir/app.py', '.'),
        ('$TempDir/licence_guard.py', '.'),
        ('$TempDir/modules', 'modules'),
        ('$TempDir/config', 'config'),
        ('$TempDir/data', 'data'),
        ('$TempDir/assets', 'assets'),
    ],
    hiddenimports=[
        'streamlit', 'streamlit.web.cli', 'streamlit.runtime.scriptrunner',
        'pandas', 'numpy', 'scipy', 'scipy.stats', 'seaborn',
        'matplotlib', 'plotly', 'sklearn', 'openpyxl', 'cryptography',
        'licence_guard', 'modules', 'zlib', 'base64', 'marshal'
    ],
    hookspath=['$TempDir/hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'IPython'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Optimisations
a.datas = [x for x in a.datas if not x[0].endswith('.pyc')]
a.binaries = [x for x in a.binaries if not any(exc in x[0] for exc in ['qt5', 'qt6'])]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='$OutputName',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
"@

$specContent | Out-File -FilePath "$OutputName.spec" -Encoding UTF8

# Compilation PyInstaller
Write-Host "`n[11/12] Compilation finale..." -ForegroundColor Yellow
pyinstaller "$OutputName.spec" --clean --noconfirm

# Vérification
if (-not (Test-Path "dist\$OutputName.exe")) {
    Write-Host "ERREUR: Compilation échouée!" -ForegroundColor Red
    exit 1
}

# Post-traitement
Write-Host "`n[12/12] Post-traitement..." -ForegroundColor Yellow

# Compression UPX supplémentaire
try {
    $upxPath = Join-Path $ProjectRoot "upx.exe"
    if (Test-Path $upxPath) {
        & $upxPath --ultra-brute "dist\$OutputName.exe" 2>$null
        Write-Host "  ✓ Compression UPX maximale appliquée" -ForegroundColor Green
    }
}
catch {}

# Nettoyage
if (-not $KeepTemp) {
    Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item "build" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item "$OutputName.spec" -Force -ErrorAction SilentlyContinue
}

# Rapport final
$EndTime = Get-Date
$Duration = [math]::Round(($EndTime - $StartTime).TotalMinutes, 1)
$FinalSize = [math]::Round((Get-Item "dist\$OutputName.exe").Length / 1MB, 2)

Write-Host "`n=====================================================" -ForegroundColor Green
Write-Host "   BUILD TERMINÉ AVEC SUCCÈS!" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📦 Exécutable: dist\$OutputName.exe" -ForegroundColor Cyan
Write-Host "📏 Taille: $FinalSize MB" -ForegroundColor Cyan
Write-Host "⏱️  Durée: $Duration minutes" -ForegroundColor Cyan
Write-Host ""
Write-Host "🛡️  PROTECTIONS APPLIQUÉES:" -ForegroundColor Yellow
Write-Host "  ✓ Obfuscation multi-couches"
Write-Host "  ✓ Strings encodées (Base64+XOR)"
Write-Host "  ✓ Variables/fonctions renommées"
Write-Host "  ✓ Code junk ajouté"
Write-Host "  ✓ Anti-debug intégré"
Write-Host "  ✓ Minification python-minifier"
Write-Host "  ✓ Protection token AES-256"
Write-Host "  ✓ Autodestruction si pas de licence"
Write-Host ""
Write-Host "📝 TEST:" -ForegroundColor Yellow
Write-Host "  1. Créer token: python create_token_admin.py"
Write-Host "  2. Placer sys.dat dans %PROGRAMDATA%\OptimPV\"
Write-Host "  3. Lancer $OutputName.exe"
Write-Host ""

# Son de notification
[System.Media.SystemSounds]::Asterisk.Play()
