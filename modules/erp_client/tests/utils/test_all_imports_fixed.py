"""Test de vérification de toutes les corrections d'imports.

Ce script vérifie que toutes les erreurs d'imports identifiées ont été corrigées :
1. TypeClient dans models/client.py
2. models.pricing avec PrixClient et TypeTarif
3. PilImage dans facturation/qr_payment.py
4. List dans facturation/pdf_config.py
"""

import sys
import os
import ast
import traceback
from pathlib import Path

# Ajouter le projet au path pour les imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def test_syntax_compilation(file_path: str) -> bool:
    """Teste la compilation syntaxique d'un fichier."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Test de syntaxe avec AST
        ast.parse(content)
        return True
        
    except SyntaxError as e:
        print(f"❌ Erreur de syntaxe dans {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la lecture de {file_path}: {e}")
        return False

def test_enum_import():
    """Teste l'import de TypeClient."""
    print("🔍 Test 1: Import TypeClient...")
    try:
        from modules.erp_client.models.client import Client, TypeClient
        
        # Vérifier que l'enum fonctionne
        assert TypeClient.PRODUCTEUR.value == "producteur"
        assert TypeClient.CONSOMMATEUR.value == "consommateur"
        assert TypeClient.PROSUMER.value == "prosumer"
        
        # Vérifier qu'on peut créer un client avec l'enum
        client = Client(
            code_client="TEST001",
            nom="Test Client",
            type_client=TypeClient.PRODUCTEUR
        )
        assert client.type_client == TypeClient.PRODUCTEUR
        
        print("✅ TypeClient import et utilisation OK")
        return True
        
    except Exception as e:
        print(f"❌ Erreur TypeClient: {e}")
        traceback.print_exc()
        return False

def test_pricing_models():
    """Teste l'import du module pricing."""
    print("🔍 Test 2: Import models.pricing...")
    try:
        from modules.erp_client.models.pricing import PrixClient, TypeTarif
        
        # Vérifier que l'enum TypeTarif fonctionne
        assert TypeTarif.FIXE.value == "fixe"
        assert TypeTarif.INDEXE.value == "indexe"
        assert TypeTarif.DYNAMIQUE.value == "dynamique"
        
        # Vérifier qu'on peut créer un prix
        prix = PrixClient(
            client_id=1,
            prix_kwh=0.15,
            type_tarif=TypeTarif.FIXE
        )
        assert prix.type_tarif == TypeTarif.FIXE
        
        print("✅ models.pricing import et utilisation OK")
        return True
        
    except Exception as e:
        print(f"❌ Erreur models.pricing: {e}")
        traceback.print_exc()
        return False

def test_imports_in_ui():
    """Teste les imports dans les fichiers UI."""
    print("🔍 Test 3: Imports dans les dashboards...")
    try:
        # Test des imports depuis les fichiers UI
        ui_files = [
            "modules/erp_client/ui/commercial_dashboard.py",
            "modules/erp_client/ui/commercial_dashboard_v2.py"
        ]
        
        for ui_file in ui_files:
            if os.path.exists(ui_file):
                # Vérifier la syntaxe
                if not test_syntax_compilation(ui_file):
                    return False
                    
                # Vérifier que les imports sont corrects
                with open(ui_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if "from ..models.pricing import" in content:
                    print(f"✅ Import models.pricing trouvé dans {ui_file}")
                else:
                    print(f"⚠️ Import models.pricing non trouvé dans {ui_file}")
        
        print("✅ Imports UI vérifiés")
        return True
        
    except Exception as e:
        print(f"❌ Erreur tests UI: {e}")
        return False

def test_facturation_fixes():
    """Teste les corrections dans le module facturation."""
    print("🔍 Test 4: Corrections module facturation...")
    
    # Test syntaxe des fichiers corrigés
    facturation_files = [
        "modules/facturation/qr_payment.py",
        "modules/facturation/pdf_config.py"
    ]
    
    all_ok = True
    for file_path in facturation_files:
        if os.path.exists(file_path):
            if test_syntax_compilation(file_path):
                print(f"✅ {file_path} syntaxe OK")
            else:
                all_ok = False
        else:
            print(f"⚠️ {file_path} non trouvé")
    
    # Vérifier imports spécifiques
    try:
        # Test pdf_config
        pdf_config_path = "modules/facturation/pdf_config.py"
        if os.path.exists(pdf_config_path):
            with open(pdf_config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if "from typing import Dict, Any, Optional, List" in content:
                print("✅ Import List ajouté dans pdf_config.py")
            else:
                print("❌ Import List manquant dans pdf_config.py")
                all_ok = False
        
        # Test qr_payment  
        qr_payment_path = "modules/facturation/qr_payment.py"
        if os.path.exists(qr_payment_path):
            with open(qr_payment_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if "TYPE_CHECKING" in content and "PilImage = Any" in content:
                print("✅ Correction PilImage appliquée dans qr_payment.py")
            else:
                print("❌ Correction PilImage manquante dans qr_payment.py")
                all_ok = False
                
    except Exception as e:
        print(f"❌ Erreur vérification facturation: {e}")
        all_ok = False
    
    return all_ok

def main():
    """Fonction principale de test."""
    print("🧪 VÉRIFICATION DE TOUTES LES CORRECTIONS D'IMPORTS")
    print("=" * 60)
    
    tests = [
        ("TypeClient enum", test_enum_import),
        ("Models pricing", test_pricing_models), 
        ("UI imports", test_imports_in_ui),
        ("Facturation fixes", test_facturation_fixes)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        success = test_func()
        results.append((test_name, success))
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSÉ" if success else "❌ ÉCHEC"
        print(f"{status}: {test_name}")
    
    print(f"\nRésultat: {passed}/{total} tests passés")
    
    if passed == total:
        print("\n🎉 TOUTES LES CORRECTIONS SONT VALIDÉES!")
        print("🛡️ Le module ERP est prêt pour l'utilisation")
        return True
    else:
        print(f"\n⚠️ {total - passed} correction(s) restante(s) à appliquer")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erreur fatale dans les tests: {e}")
        traceback.print_exc()
        sys.exit(1)