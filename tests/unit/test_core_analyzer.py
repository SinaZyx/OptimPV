#!/usr/bin/env python3
"""
Script de test pour vérifier le bon fonctionnement de core_analyzer.py après division.
"""

def test_core_analyzer_import():
    """Test d'import de core_analyzer"""
    try:
        from modules.engine_module.core_analyzer import AnalysisEngine
        print("✅ Import AnalysisEngine réussi")
        return True
    except Exception as e:
        print(f"❌ Erreur import AnalysisEngine: {e}")
        return False

def test_core_analyzer_instantiation():
    """Test d'instanciation d'AnalysisEngine"""
    try:
        from modules.engine_module.core_analyzer import AnalysisEngine
        
        # Configuration minimale pour le test
        test_config = {"capex_scenario": 100000, "puissance_kwc_installee": 10}
        test_scenarios = {"test": {"capex_modifier": 0.0}}
        test_sites_data = {"site1": {"Temps": [], "production_kwh": [], "consumption_kwh": []}}
        
        # Créer une instance
        engine = AnalysisEngine(test_config, test_scenarios, test_sites_data)
        print("✅ Instanciation AnalysisEngine réussie")
        print(f"   - equity_calc: {type(engine.equity_calc).__name__}")
        print(f"   - treasury_manager: {type(engine.treasury_manager).__name__}")
        return True
    except Exception as e:
        print(f"❌ Erreur instanciation AnalysisEngine: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 TEST CORE_ANALYZER APRÈS DIVISION")
    print("=" * 50)
    
    test1 = test_core_analyzer_import()
    test2 = test_core_analyzer_instantiation() if test1 else False
    
    print("\n" + "=" * 50)
    if test1 and test2:
        print("🎉 TOUS LES TESTS PASSÉS - core_analyzer.py est fonctionnel!")
    else:
        print("❌ ÉCHEC - core_analyzer.py a des problèmes") 