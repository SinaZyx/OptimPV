"""Test ciblé des corrections principales sans dépendances Streamlit.

Teste uniquement les corrections de base qui ne nécessitent pas Streamlit.
"""

import sys
import os
import ast
from pathlib import Path

# Ajouter le projet au path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def test_syntax_only(file_path: str) -> bool:
    """Teste uniquement la syntaxe d'un fichier."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True
    except Exception as e:
        print(f"❌ Erreur syntaxe {file_path}: {e}")
        return False

def test_direct_model_imports():
    """Teste les imports directs des modèles sans passer par __init__.py"""
    print("🔍 Test imports directs des modèles...")
    
    try:
        # Import direct du modèle client
        import importlib.util
        
        client_path = project_root / "modules" / "erp_client" / "models" / "client.py"
        spec = importlib.util.spec_from_file_location("client_module", client_path)
        client_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(client_module)
        
        # Vérifier TypeClient
        TypeClient = client_module.TypeClient
        assert TypeClient.PRODUCTEUR.value == "producteur"
        print("✅ TypeClient enum fonctionne")
        
        # Vérifier Client
        Client = client_module.Client
        client = Client(
            code_client="TEST001",
            nom="Test",
            type_client=TypeClient.PRODUCTEUR
        )
        assert client.type_client == TypeClient.PRODUCTEUR
        print("✅ Classe Client fonctionne avec TypeClient")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur import direct client: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pricing_model():
    """Teste le modèle pricing directement."""
    print("🔍 Test modèle pricing...")
    
    try:
        import importlib.util
        
        pricing_path = project_root / "modules" / "erp_client" / "models" / "pricing.py"
        spec = importlib.util.spec_from_file_location("pricing_module", pricing_path)
        pricing_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pricing_module)
        
        # Vérifier TypeTarif
        TypeTarif = pricing_module.TypeTarif
        assert TypeTarif.FIXE.value == "fixe"
        print("✅ TypeTarif enum fonctionne")
        
        # Vérifier PrixClient
        PrixClient = pricing_module.PrixClient
        from datetime import date, datetime
        prix = PrixClient(
            id=None,
            client_id=1,
            prix_kwh=0.15,
            date_debut=date.today(),
            date_fin=None,
            type_tarif="fixe",  # Utiliser string pour l'instant
            reference_prix=None,
            remise_pourcentage=0.0,
            formule_calcul=None,
            notes=None,
            date_creation=None
        )
        assert prix.type_tarif == "fixe"  # On a utilisé string pour l'instant
        print("✅ Classe PrixClient fonctionne")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur modèle pricing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_facturation_syntax():
    """Teste la syntaxe des fichiers facturation corrigés."""
    print("🔍 Test syntaxe facturation...")
    
    files_to_test = [
        "modules/facturation/qr_payment.py",
        "modules/facturation/pdf_config.py"
    ]
    
    all_ok = True
    for file_path in files_to_test:
        full_path = project_root / file_path
        if full_path.exists():
            if test_syntax_only(str(full_path)):
                print(f"✅ {file_path} syntaxe OK")
            else:
                all_ok = False
        else:
            print(f"⚠️ {file_path} non trouvé")
    
    # Vérifications spécifiques
    try:
        qr_path = project_root / "modules/facturation/qr_payment.py"
        if qr_path.exists():
            with open(qr_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            checks = [
                ("TYPE_CHECKING import", "TYPE_CHECKING" in content),
                ("PilImage fallback", "PilImage = Any" in content),
                ("QRCODE_AVAILABLE check", "if not QRCODE_AVAILABLE:" in content)
            ]
            
            for check_name, check_result in checks:
                if check_result:
                    print(f"✅ {check_name} présent")
                else:
                    print(f"❌ {check_name} manquant")
                    all_ok = False
        
        pdf_path = project_root / "modules/facturation/pdf_config.py"
        if pdf_path.exists():
            with open(pdf_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "from typing import Dict, Any, Optional, List" in content:
                print("✅ Import List ajouté dans pdf_config")
            else:
                print("❌ Import List manquant dans pdf_config")
                all_ok = False
    
    except Exception as e:
        print(f"❌ Erreur vérification: {e}")
        all_ok = False
    
    return all_ok

def main():
    """Fonction principale."""
    print("🧪 TEST DES CORRECTIONS PRINCIPALES")
    print("=" * 50)
    
    tests = [
        ("Modèles client direct", test_direct_model_imports),
        ("Modèle pricing", test_pricing_model),
        ("Syntaxe facturation", test_facturation_syntax)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSÉ" if success else "❌ ÉCHEC"
        print(f"{status}: {test_name}")
    
    if passed == total:
        print(f"\n🎉 {passed}/{total} corrections validées!")
        print("✅ Les corrections principales sont appliquées")
    else:
        print(f"\n⚠️ {total - passed} problème(s) restant(s)")
    
    return passed == total

if __name__ == "__main__":
    main()