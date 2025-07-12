#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration de Build pour OptimPV
===================================

Script pour préparer la compilation en exécutable.
"""

import os
import shutil
from pathlib import Path

def prepare_for_build():
    """Prépare le projet pour la compilation"""
    
    print("🔧 PRÉPARATION POUR LA COMPILATION")
    print("=" * 50)
    
    # 1. Créer le dossier de build
    build_dir = Path("build_ready")
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    
    print(f"📁 Dossier de build créé: {build_dir}")
    
    # 2. Copier les fichiers essentiels
    essential_files = [
        "app.py",
        "requirements.txt",
        "network_admin_config.json"
    ]
    
    essential_dirs = [
        "modules",
        "config", 
        "data",
        "Interface serveur"
    ]
    
    print("📋 Copie des fichiers essentiels...")
    for file in essential_files:
        if Path(file).exists():
            shutil.copy2(file, build_dir / file)
            print(f"  ✅ {file}")
        else:
            print(f"  ⚠️  {file} (non trouvé)")
    
    print("📋 Copie des dossiers essentiels...")
    for dir_name in essential_dirs:
        src_dir = Path(dir_name)
        if src_dir.exists():
            shutil.copytree(src_dir, build_dir / dir_name)
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ⚠️  {dir_name}/ (non trouvé)")
    
    # 3. Créer le fichier principal pour l'exe
    main_exe_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OptimPV - Point d'entrée principal pour l'exécutable
===================================================
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire courant au path
current_dir = Path(__file__).parent if hasattr(Path(__file__), 'parent') else Path('.')
sys.path.insert(0, str(current_dir))

# Ajouter le dossier modules
modules_dir = current_dir / "modules"
if modules_dir.exists():
    sys.path.insert(0, str(modules_dir))

def main():
    """Point d'entrée principal"""
    
    # Détecter si on veut le panel de contrôle ou l'app principale
    if len(sys.argv) > 1 and sys.argv[1] == "--control-panel":
        # Lancer le panel de contrôle
        from Interface.serveur.server_control.launchers.exe_control_panel_launcher import main as control_main
        control_main()
    else:
        # Lancer l'application principale
        from Interface.serveur.launcher import main as app_main
        app_main()

if __name__ == "__main__":
    main()
'''
    
    with open(build_dir / "main.py", "w", encoding="utf-8") as f:
        f.write(main_exe_content)
    
    print("  ✅ main.py (point d'entrée)")
    
    # 4. Créer le script de build Nuitka
    nuitka_script = f'''@echo off
title OptimPV - Compilation Nuitka
echo.
echo ===============================================
echo    COMPILATION OPTIMPV AVEC NUITKA
echo ===============================================
echo.

REM Installer Nuitka si nécessaire
pip install nuitka

REM Compilation avec Nuitka
python -m nuitka ^
    --standalone ^
    --onefile ^
    --windows-console-mode=attach ^
    --windows-icon-from-ico=icon.ico ^
    --include-data-dir=modules=modules ^
    --include-data-dir=config=config ^
    --include-data-dir=data=data ^
    --include-data-dir="Interface serveur"="Interface serveur" ^
    --include-data-file=network_admin_config.json=network_admin_config.json ^
    --include-package=streamlit ^
    --include-package=psutil ^
    --include-package=requests ^
    --include-package=pandas ^
    --include-package=numpy ^
    --include-package=plotly ^
    --output-filename=OptimPV.exe ^
    main.py

echo.
echo ===============================================
echo Compilation terminee !
echo Executable: OptimPV.exe
echo ===============================================
pause
'''
    
    with open(build_dir / "build_nuitka.bat", "w", encoding="utf-8") as f:
        f.write(nuitka_script)
    
    print("  ✅ build_nuitka.bat")
    
    # 5. Créer le script de build PyInstaller
    pyinstaller_script = f'''@echo off
title OptimPV - Compilation PyInstaller
echo.
echo ===============================================
echo    COMPILATION OPTIMPV AVEC PYINSTALLER
echo ===============================================
echo.

REM Installer PyInstaller si nécessaire
pip install pyinstaller

REM Compilation avec PyInstaller
pyinstaller ^
    --onefile ^
    --windowed ^
    --icon=icon.ico ^
    --add-data "modules;modules" ^
    --add-data "config;config" ^
    --add-data "data;data" ^
    --add-data "Interface serveur;Interface serveur" ^
    --add-data "network_admin_config.json;." ^
    --hidden-import=streamlit ^
    --hidden-import=psutil ^
    --hidden-import=requests ^
    --hidden-import=pandas ^
    --hidden-import=numpy ^
    --hidden-import=plotly ^
    --name=OptimPV ^
    main.py

echo.
echo ===============================================
echo Compilation terminee !
echo Executable: dist/OptimPV.exe
echo ===============================================
pause
'''
    
    with open(build_dir / "build_pyinstaller.bat", "w", encoding="utf-8") as f:
        f.write(pyinstaller_script)
    
    print("  ✅ build_pyinstaller.bat")
    
    # 6. Créer un README pour la compilation
    readme_content = '''# OptimPV - Compilation en Exécutable

## 📦 Préparation terminée !

### 🔧 Options de compilation :

#### Option 1 - Nuitka (Recommandé)
```bash
cd build_ready
build_nuitka.bat
```

#### Option 2 - PyInstaller
```bash
cd build_ready  
build_pyinstaller.bat
```

### 📋 Fichiers inclus :
- ✅ Application principale (app.py)
- ✅ Modules Python (modules/)
- ✅ Configuration (config/, data/)
- ✅ Interface serveur complète
- ✅ Panel de contrôle adapté pour exe

### 🚀 Utilisation de l'exe :

#### Lancer l'application principale :
```bash
OptimPV.exe
```

#### Lancer le panel de contrôle :
```bash
OptimPV.exe --control-panel
```

### ⚠️ Notes importantes :
- L'exe embarque Python et toutes les dépendances
- Pas besoin d'installation Python sur la machine cible
- Le serveur se lance automatiquement dans l'exe
- La clé USB fonctionne normalement avec l'exe
'''
    
    with open(build_dir / "README_BUILD.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("  ✅ README_BUILD.md")
    
    print("\n" + "=" * 50)
    print("✅ PRÉPARATION TERMINÉE !")
    print("=" * 50)
    print(f"📁 Dossier prêt: {build_dir.absolute()}")
    print("🔧 Étapes suivantes :")
    print("   1. cd build_ready")
    print("   2. build_nuitka.bat (ou build_pyinstaller.bat)")
    print("   3. Tester l'exe généré")
    print("=" * 50)

if __name__ == "__main__":
    prepare_for_build() 