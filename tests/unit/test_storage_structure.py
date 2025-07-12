#!/usr/bin/env python3
"""
Test de la nouvelle structure modulaire du système de stockage OptimPV
"""

import sys
import traceback

def test_imports():
    """Test des imports de la nouvelle structure"""
    print("🧪 Test de la nouvelle structure modulaire du stockage OptimPV\n")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Import principal
    tests_total += 1
    try:
        from modules.storage import StorageModule, show_storage_ui
        print("✅ Import principal réussi : StorageModule, show_storage_ui")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Erreur import principal : {e}")
    
    # Test 2: Import des modules individuels
    modules_to_test = [
        'modules.storage.core',
        'modules.storage.project_manager', 
        'modules.storage.comparison',
        'modules.storage.data_utils',
        'modules.storage.ui_components',
        'modules.storage.visualization'
    ]
    
    for module_name in modules_to_test:
        tests_total += 1
        try:
            __import__(module_name)
            print(f"✅ Import module réussi : {module_name}")
            tests_passed += 1
        except Exception as e:
            print(f"❌ Erreur import {module_name} : {e}")
    
    # Test 3: Instanciation de StorageModule
    tests_total += 1
    try:
        # Mock streamlit pour éviter les erreurs
        import unittest.mock as mock
        with mock.patch('streamlit.session_state', {}):
            storage = StorageModule()
            print("✅ Instanciation StorageModule réussie")
            tests_passed += 1
    except Exception as e:
        print(f"❌ Erreur instanciation StorageModule : {e}")
    
    # Test 4: Vérification des méthodes principales
    tests_total += 1
    try:
        with mock.patch('streamlit.session_state', {}):
            storage = StorageModule()
            
            # Vérifier que les méthodes existent
            methods_to_check = [
                'save_current_project',
                'load_project', 
                'compare_projects_advanced',
                'get_active_modules',
                'calculate_completeness_score'
            ]
            
            for method_name in methods_to_check:
                if hasattr(storage, method_name):
                    print(f"  ✓ Méthode trouvée : {method_name}")
                else:
                    raise AttributeError(f"Méthode manquante : {method_name}")
            
            print("✅ Toutes les méthodes principales sont disponibles")
            tests_passed += 1
    except Exception as e:
        print(f"❌ Erreur vérification méthodes : {e}")
    
    # Test 5: Vérification de la compatibilité descendante
    tests_total += 1
    try:
        from modules.storage_legacy import StorageModule as LegacyStorageModule
        print("✅ Compatibilité descendante préservée")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Erreur compatibilité descendante : {e}")
    
    # Résumé
    print(f"\n📊 Résultats des tests : {tests_passed}/{tests_total} réussis")
    
    if tests_passed == tests_total:
        print("🎉 Tous les tests sont passés ! La refactorisation est réussie.")
        return True
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
        return False

def test_file_structure():
    """Test de la structure des fichiers"""
    import os
    
    print("\n📁 Vérification de la structure des fichiers")
    
    base_path = "modules/storage"
    expected_files = [
        "__init__.py",
        "core.py", 
        "project_manager.py",
        "comparison.py",
        "data_utils.py",
        "ui_components.py",
        "visualization.py",
        "migration.py",
        "README.md"
    ]
    
    files_found = 0
    for file_name in expected_files:
        file_path = os.path.join(base_path, file_name)
        if os.path.exists(file_path):
            size_kb = os.path.getsize(file_path) / 1024
            print(f"✅ {file_name} ({size_kb:.1f} KB)")
            files_found += 1
        else:
            print(f"❌ {file_name} - MANQUANT")
    
    print(f"\n📊 Fichiers trouvés : {files_found}/{len(expected_files)}")
    
    # Vérifier que l'ancien fichier a été sauvegardé
    if os.path.exists("modules/storage_backup.py"):
        backup_size_kb = os.path.getsize("modules/storage_backup.py") / 1024
        print(f"✅ Sauvegarde de l'ancien fichier : storage_backup.py ({backup_size_kb:.1f} KB)")
    else:
        print("⚠️  Sauvegarde de l'ancien fichier non trouvée")
    
    return files_found == len(expected_files)

def main():
    """Fonction principale de test"""
    print("=" * 60)
    print("🔬 TEST DE LA REFACTORISATION DU MODULE DE STOCKAGE")
    print("=" * 60)
    
    try:
        # Test de la structure des fichiers
        structure_ok = test_file_structure()
        
        # Test des imports et fonctionnalités
        imports_ok = test_imports()
        
        print("\n" + "=" * 60)
        if structure_ok and imports_ok:
            print("🎉 REFACTORISATION RÉUSSIE !")
            print("📁 Le fichier storage.py a été décomposé avec succès en 6 modules.")
            print("📊 De 2326 lignes monolithiques à une architecture modulaire claire.")
            print("🚀 Vous pouvez maintenant utiliser : from modules.storage import StorageModule")
            return 0
        else:
            print("❌ PROBLÈMES DÉTECTÉS")
            print("🔧 Vérifiez les erreurs ci-dessus et corrigez-les.")
            return 1
            
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE : {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())