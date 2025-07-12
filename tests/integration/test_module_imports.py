#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test d'importation des modules pour vérifier l'intégration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test que tous les modules peuvent être importés sans erreur"""
    print("TEST D'IMPORTATION DES MODULES")
    print("=" * 60)
    
    modules_to_test = [
        ("data_handler", "modules.prospect_mapping.core.data_handler"),
        ("map_visualizer", "modules.prospect_mapping.core.map_visualizer_robust"),
        ("ui", "modules.prospect_mapping.ui"),
    ]
    
    success_count = 0
    error_count = 0
    
    for module_name, module_path in modules_to_test:
        try:
            print(f"\nImport de {module_name}...")
            exec(f"import {module_path}")
            print(f"✅ {module_name} importé avec succès")
            
            # Vérifier les fonctions spécifiques
            if module_name == "data_handler":
                from modules.prospect_mapping.core.data_handler import (
                    search_and_geocode_address,
                    get_all_dpe_around_point,
                    create_dpe_color_map
                )
                print("  - search_and_geocode_address: ✅")
                print("  - get_all_dpe_around_point: ✅")
                print("  - create_dpe_color_map: ✅")
                
            elif module_name == "map_visualizer":
                from modules.prospect_mapping.core.map_visualizer_robust import create_prospect_map
                print("  - create_prospect_map: ✅")
                
            success_count += 1
            
        except ImportError as e:
            print(f"❌ Erreur d'import pour {module_name}: {e}")
            error_count += 1
        except Exception as e:
            print(f"❌ Erreur inattendue pour {module_name}: {e}")
            error_count += 1
    
    print("\n" + "=" * 60)
    print(f"Résultats: {success_count} succès, {error_count} erreurs")
    
    if error_count == 0:
        print("✅ TOUS LES MODULES SONT IMPORTABLES!")
    else:
        print("❌ Des erreurs ont été détectées")
    
    return error_count == 0

def test_function_signatures():
    """Test que les fonctions ont les bonnes signatures"""
    print("\n\nTEST DES SIGNATURES DE FONCTIONS")
    print("=" * 60)
    
    try:
        from modules.prospect_mapping.core.data_handler import (
            search_and_geocode_address,
            get_all_dpe_around_point,
            create_dpe_color_map
        )
        
        # Test search_and_geocode_address
        import inspect
        sig = inspect.signature(search_and_geocode_address)
        params = list(sig.parameters.keys())
        print(f"\nsearch_and_geocode_address({', '.join(params)})")
        assert 'address' in params, "Paramètre 'address' manquant"
        print("✅ Signature correcte")
        
        # Test get_all_dpe_around_point
        sig = inspect.signature(get_all_dpe_around_point)
        params = list(sig.parameters.keys())
        print(f"\nget_all_dpe_around_point({', '.join(params)})")
        assert 'latitude' in params, "Paramètre 'latitude' manquant"
        assert 'longitude' in params, "Paramètre 'longitude' manquant"
        assert 'radius_m' in params, "Paramètre 'radius_m' manquant"
        print("✅ Signature correcte")
        
        # Test create_dpe_color_map
        sig = inspect.signature(create_dpe_color_map)
        params = list(sig.parameters.keys())
        print(f"\ncreate_dpe_color_map({', '.join(params)})")
        assert 'classe_energie' in params, "Paramètre 'classe_energie' manquant"
        print("✅ Signature correcte")
        
        print("\n✅ Toutes les signatures sont correctes!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test des signatures: {e}")
        return False

def main():
    """Exécution de tous les tests"""
    print("\n" + "=" * 60)
    print("TESTS D'INTÉGRATION DES MODULES DPE")
    print("=" * 60 + "\n")
    
    # Test imports
    imports_ok = test_imports()
    
    # Test signatures uniquement si les imports sont OK
    signatures_ok = True
    if imports_ok:
        signatures_ok = test_function_signatures()
    
    print("\n" + "=" * 60)
    if imports_ok and signatures_ok:
        print("✅ TOUS LES TESTS D'INTÉGRATION SONT PASSÉS!")
    else:
        print("❌ Des erreurs ont été détectées dans l'intégration")
    print("=" * 60)
    
    return imports_ok and signatures_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)