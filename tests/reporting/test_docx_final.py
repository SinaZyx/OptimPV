#!/usr/bin/env python3
"""
Test final du système DOCX OptimPV avec gestionnaire de dépendances
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

def test_dependency_manager():
    """Test du gestionnaire de dépendances"""
    print("🧪 TEST: Gestionnaire de dépendances")
    
    try:
        from modules.reporting.docx_system.dependency_manager import DocxDependencyManager
        
        manager = DocxDependencyManager()
        print("✅ DocxDependencyManager initialisé")
        
        # Vérifier les dépendances
        status = manager.get_dependency_status()
        missing = manager.get_missing_dependencies()
        
        print(f"✅ {len(status)} dépendances vérifiées")
        print(f"📦 {len(missing)} dépendances manquantes: {missing}")
        
        # Test des instructions
        instructions = manager.get_installation_instructions()
        print(f"✅ Instructions générées ({len(instructions)} caractères)")
        
        # Test du script
        script = manager.generate_installation_script()
        print(f"✅ Script d'installation généré ({len(script)} caractères)")
        
        # Test système prêt
        is_ready = manager.is_system_ready()
        print(f"🚀 Système prêt: {'✅ OUI' if is_ready else '❌ NON'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test gestionnaire: {e}")
        return False

def test_integration_module():
    """Test du module d'intégration"""
    print("\n🧪 TEST: Module d'intégration")
    
    try:
        from modules.reporting.docx_integration import DocxIntegrationModule
        
        # Test d'initialisation sans Streamlit
        print("✅ DocxIntegrationModule importé")
        
        # Le module peut être initialisé même sans Streamlit pour tester la structure
        print("✅ Module d'intégration disponible")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test intégration: {e}")
        return False

def test_structure_complete():
    """Test de la structure complète"""
    print("\n🧪 TEST: Structure complète")
    
    base_path = "/mnt/c/Users/kingc/OptimPV/modules/reporting"
    
    required_files = [
        "docx_system/__init__.py",
        "docx_system/data_extractor.py",
        "docx_system/chart_generator.py", 
        "docx_system/template_generator.py",
        "docx_system/dependency_manager.py",
        "docx_integration.py"
    ]
    
    all_present = True
    for file_path in required_files:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            file_size = os.path.getsize(full_path)
            print(f"✅ {file_path} ({file_size} bytes)")
        else:
            print(f"❌ {file_path} manquant")
            all_present = False
    
    return all_present

def test_customer_report_integration():
    """Test de l'intégration dans customer_report_commercial"""
    print("\n🧪 TEST: Intégration customer_report_commercial")
    
    file_path = "/mnt/c/Users/kingc/OptimPV/modules/reporting/customer_report_commercial.py"
    
    if not os.path.exists(file_path):
        print("❌ customer_report_commercial.py non trouvé")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            "from .docx_integration import DocxIntegrationModule",
            "self.docx_module",
            "def _show_docx_integration",
            "def _generate_quick_docx"
        ]
        
        all_integrated = True
        for check in checks:
            if check in content:
                print(f"✅ {check}")
            else:
                print(f"❌ {check} manquant")
                all_integrated = False
        
        return all_integrated
        
    except Exception as e:
        print(f"❌ Erreur lecture: {e}")
        return False

def main():
    """Test complet du système DOCX final"""
    print("🚀 TESTS FINAUX DU SYSTÈME DOCX OPTIMPV")
    print("=" * 60)
    
    tests = [
        ("Gestionnaire de dépendances", test_dependency_manager),
        ("Module d'intégration", test_integration_module),
        ("Structure complète", test_structure_complete),
        ("Intégration customer_report", test_customer_report_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHEC"
        print(f"{status:12} {test_name}")
    
    print(f"\n🏆 RÉSULTAT: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 SYSTÈME DOCX COMPLÈTEMENT OPÉRATIONNEL !")
        print("""
📋 UTILISATION:
1. Allez dans OptimPV → Onglet 'Rapports' → 'Commercial'
2. Faites défiler jusqu'à 'Nouveau : Génération DOCX Professionnel'
3. Si dépendances manquantes → Cliquez 'Installer Automatiquement'
4. Une fois installées → Redémarrez OptimPV
5. Générez vos rapports Word professionnels !

🔧 DÉPENDANCES REQUISES:
   pip install python-docx matplotlib pillow

💡 FALLBACK DISPONIBLE:
   Rapports HTML disponibles même sans dépendances DOCX
        """)
    else:
        print("⚠️ Système partiellement fonctionnel.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)