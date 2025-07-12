#!/bin/bash
# BUILD OptimPV - Script Principal de Compilation Linux

echo "============================================================"
echo "   BUILD OptimPV - Version de Production"
echo "============================================================"

# Configuration
MAIN_SCRIPT="server_controller.py"
OUTPUT_NAME="OptimPV"

# Hidden imports essentiels
HIDDEN_IMPORTS=(
    "streamlit.web.cli"
    "streamlit.runtime.scriptrunner"
    "licence_guard"
    "cryptography.fernet"
    "pandas"
    "numpy"
    "seaborn"
    "psutil"
    "tkinter.ttk"
    "multiprocessing"
)

# Activation environnement virtuel
echo -e "\n[1/4] Activation environnement virtuel..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "ERREUR: Environnement virtuel introuvable!"
    exit 1
fi

# Nettoyage
echo -e "\n[2/4] Nettoyage..."
rm -rf dist build *.spec

# Compilation
echo -e "\n[3/4] Compilation avec PyInstaller..."

PYINSTALLER_CMD="pyinstaller --noconfirm --onefile --windowed"
PYINSTALLER_CMD+=" --name \"$OUTPUT_NAME\""
PYINSTALLER_CMD+=" --distpath \"$(pwd)/dist\""

# Icone
if [ -f "assets/icon.ico" ]; then
    PYINSTALLER_CMD+=" --icon \"assets/icon.ico\""
fi

# Donnees essentielles
for dir in assets config modules; do
    if [ -d "$dir" ]; then
        PYINSTALLER_CMD+=" --add-data \"$dir:$dir\""
    fi
done

# Application principale
if [ -f "app.py" ]; then
    PYINSTALLER_CMD+=" --add-data \"app.py:.\""
fi

# Hidden imports
for import in "${HIDDEN_IMPORTS[@]}"; do
    PYINSTALLER_CMD+=" --hidden-import \"$import\""
done

PYINSTALLER_CMD+=" --log-level WARN --clean \"$MAIN_SCRIPT\""

echo "  Compilation en cours..."
eval $PYINSTALLER_CMD

if [ $? -ne 0 ]; then
    echo "  [x] Echec compilation!"
    exit 1
fi

# Verification
echo -e "\n[4/4] Verification..."

FINAL_EXE="dist/$OUTPUT_NAME.exe"
if [ -f "$FINAL_EXE" ]; then
    SIZE=$(du -h "$FINAL_EXE" | cut -f1)
    DATE=$(date "+%Y-%m-%d %H:%M:%S")
    
    # Nettoyage final
    rm -f *.spec
    rm -rf build
    
    echo -e "\n=================================================="
    echo "BUILD REUSSI!"
    echo "=================================================="
    echo ""
    echo "EXECUTABLE PRET:"
    echo "  $FINAL_EXE"
    echo "  Taille: $SIZE"
    echo "  Date: $DATE"
    echo ""
    echo "UTILISATION:"
    echo "  1. Lancer OptimPV.exe"
    echo "  2. Cliquer 'START Serveur'"
    echo "  3. Utiliser l'application dans le navigateur"
    echo ""
    echo "=================================================="
else
    echo -e "\nECHEC - Executable non trouve"
fi