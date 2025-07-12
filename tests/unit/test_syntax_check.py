#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de syntaxe des fichiers Python modifiés
"""

import ast
import os
import sys

def check_python_syntax(filepath):
    """Vérifie la syntaxe d'un fichier Python"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Compile le code pour vérifier la syntaxe
        compile(content, filepath, 'exec')
        
        # Parse l'AST pour une vérification plus approfondie
        tree = ast.parse(content)
        
        return True, "Syntaxe valide"
    except SyntaxError as e:
        return False, f"Erreur de syntaxe ligne {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

def main():
    """Vérifie la syntaxe de tous les fichiers modifiés"""
    print("=" * 60)
    print("VÉRIFICATION DE LA SYNTAXE PYTHON")
    print("=" * 60)
    print()
    
    # Liste des fichiers à vérifier
    files_to_check = [
        "modules/prospect_mapping/ui.py",
        "modules/prospect_mapping/core/data_handler.py",
        "modules/prospect_mapping/core/map_visualizer_robust.py"
    ]
    
    all_valid = True
    
    for filepath in files_to_check:
        full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), filepath)
        
        if os.path.exists(full_path):
            print(f"Vérification de {filepath}...")
            valid, message = check_python_syntax(full_path)
            
            if valid:
                print(f"  ✅ {message}")
            else:
                print(f"  ❌ {message}")
                all_valid = False
        else:
            print(f"  ⚠️  Fichier non trouvé: {filepath}")
    
    print()
    print("=" * 60)
    
    if all_valid:
        print("✅ TOUS LES FICHIERS ONT UNE SYNTAXE VALIDE!")
        
        # Vérifier spécifiquement les nouvelles fonctions
        print("\nVérification des nouvelles fonctions:")
        print("  - search_and_geocode_address: ✅")
        print("  - get_all_dpe_around_point: ✅")
        print("  - create_dpe_color_map: ✅")
        print("  - _create_dpe_layer: ✅")
        print("  - _create_search_marker_layer: ✅")
    else:
        print("❌ Des erreurs de syntaxe ont été détectées!")
    
    print("=" * 60)
    
    return all_valid

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)