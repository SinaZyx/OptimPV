#!/usr/bin/env python3
"""
Test pour vérifier que le module prospect_mapping se charge correctement
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_import_ui():
    """Test que le module ui.py peut être importé sans erreur"""
    try:
        from modules.prospect_mapping import ui
        print("✅ Import ui.py réussi")
        return True
    except Exception as e:
        print(f"❌ Erreur import ui.py: {e}")
        return False

def test_import_main_function():
    """Test que la fonction principale peut être importée"""
    try:
        from modules.prospect_mapping.ui import show_prospect_map_ui
        print("✅ Import show_prospect_map_ui réussi")
        return True
    except Exception as e:
        print(f"❌ Erreur import show_prospect_map_ui: {e}")
        return False

def test_import_module():
    """Test que le module prospect_mapping peut être importé via __init__.py"""
    try:
        from modules.prospect_mapping import render_ui
        print("✅ Import render_ui via __init__.py réussi")
        return True
    except Exception as e:
        print(f"❌ Erreur import render_ui: {e}")
        return False

def test_syntax_check():
    """Test de vérification syntaxique"""
    try:
        import py_compile
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'modules', 'prospect_mapping', 'ui.py')
        py_compile.compile(ui_path, doraise=True)
        print("✅ Syntaxe ui.py valide")
        return True
    except Exception as e:
        print(f"❌ Erreur syntaxe ui.py: {e}")
        return False

def run_all_tests():
    """Exécute tous les tests"""
    print("🧪 Tests du module prospect_mapping")
    print("=" * 50)
    
    tests = [
        test_syntax_check,
        test_import_ui,
        test_import_main_function,
        test_import_module
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Erreur test {test.__name__}: {e}")
            results.append(False)
        print()
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"📊 Résultats: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés !")
        return True
    else:
        print("⚠️ Certains tests ont échoué")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)