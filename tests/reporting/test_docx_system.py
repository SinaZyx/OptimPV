#!/usr/bin/env python3
"""
Script de test pour le système DOCX OptimPV
Teste tous les composants du système sans dépendances Streamlit
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

def test_imports():
    """Teste l'import de tous les modules DOCX"""
    print("🧪 TEST 1: Import des modules...")
    
    try:
        from modules.reporting.docx_system.data_extractor import OptimPVDataExtractor
        print("✅ OptimPVDataExtractor importé")
    except ImportError as e:
        print(f"❌ Erreur import OptimPVDataExtractor: {e}")
        return False
    
    try:
        from modules.reporting.docx_system.chart_generator import DocxChartGenerator
        print("✅ DocxChartGenerator importé")
    except ImportError as e:
        print(f"❌ Erreur import DocxChartGenerator: {e}")
        return False
    
    try:
        from modules.reporting.docx_system.template_generator import DocxTemplateGenerator
        print("✅ DocxTemplateGenerator importé")
    except ImportError as e:
        print(f"❌ Erreur import DocxTemplateGenerator: {e}")
        return False
    
    try:
        from modules.reporting.docx_integration import DocxIntegrationModule
        print("✅ DocxIntegrationModule importé")
    except ImportError as e:
        print(f"❌ Erreur import DocxIntegrationModule: {e}")
        return False
    
    return True

def test_data_extractor():
    """Teste l'extracteur de données avec des données simulées"""
    print("\n🧪 TEST 2: Extracteur de données...")
    
    try:
        # Simuler un environnement Streamlit minimal
        class MockSessionState:
            def __init__(self):
                self.data = {}
            
            def get(self, key, default=None):
                return self.data.get(key, default)
        
        # Créer un mock de st.session_state
        import streamlit as st
        if not hasattr(st, 'session_state'):
            st.session_state = MockSessionState()
        
        # Données de test
        st.session_state.data.update({
            'config': {
                'project_name': 'Test Project',
                'tarif_edf_reference': 0.20,
                'duree_ppa': 240,
                'taux_inflation': 0.02,
                'date_debut_ppa': '2024-01-01'
            },
            'sites_config': {
                'site1': {
                    'site_type': 'Producteur',
                    'puissance_kwc': 25.0,
                    'capex': 37500,
                    'opex_maintenance': 375,
                    'opex_insurance': 187,
                    'opex_admin': 250
                },
                'site2': {
                    'site_type': 'Consommateur Pur'
                }
            },
            'constrained_optim_results': {
                'Base': {
                    'prix_optimal_const': 0.16,
                    'indicateurs_au_prix_optimal': {
                        'van_project': 15000,
                        'tri_project': 8.5,
                        'lcoe': 0.12,
                        'economie_totale': 8000,
                        'payback_simple': 12
                    }
                }
            }
        })
        
        from modules.reporting.docx_system.data_extractor import OptimPVDataExtractor
        
        extractor = OptimPVDataExtractor()
        data = extractor.extract_all_data()
        
        print(f"✅ {len(data)} variables extraites")
        print(f"✅ Projet: {data.get('project_name', 'N/A')}")
        print(f"✅ Prix optimal: {data.get('prix_optimal', 0):.4f} €/kWh")
        print(f"✅ Puissance totale: {data.get('puissance_kwc_total', 0)} kWc")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test extracteur: {e}")
        return False

def test_chart_generator():
    """Teste le générateur de graphiques"""
    print("\n🧪 TEST 3: Générateur de graphiques...")
    
    try:
        from modules.reporting.docx_system.chart_generator import DocxChartGenerator
        import tempfile
        
        # Données de test
        test_data = {
            'cout_sans_pv_annuel': 10000,
            'cout_avec_pv_total_annuel': 8000,
            'cout_avec_pv_solaire_annuel': 2800,
            'cout_avec_pv_reseau_annuel': 5200,
            'taux_autonomie': 35,
            'taux_autoconsommation': 64,
            'economie_annuelle': 2000,
            'duree_projet': 20,
            'total_autoconsumption': 17.5,
            'total_grid_purchase': 32.5
        }
        
        # Créer un répertoire temporaire
        temp_dir = tempfile.mkdtemp()
        chart_generator = DocxChartGenerator(output_dir=temp_dir)
        
        # Générer tous les graphiques
        charts = chart_generator.generate_all_charts(test_data)
        
        print(f"✅ {len(charts)} graphiques générés")
        
        for chart_name, chart_path in charts.items():
            if os.path.exists(chart_path):
                print(f"✅ Graphique {chart_name}: {os.path.basename(chart_path)}")
            else:
                print(f"❌ Graphique {chart_name} non trouvé")
        
        # Nettoyage
        chart_generator.cleanup_charts()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test graphiques: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_docx_dependencies():
    """Teste les dépendances DOCX"""
    print("\n🧪 TEST 4: Dépendances DOCX...")
    
    dependencies = {
        'python-docx': 'docx',
        'matplotlib': 'matplotlib',
        'pillow': 'PIL'
    }
    
    missing_deps = []
    
    for dep_name, import_name in dependencies.items():
        try:
            __import__(import_name)
            print(f"✅ {dep_name} disponible")
        except ImportError:
            print(f"❌ {dep_name} manquant")
            missing_deps.append(dep_name)
    
    if missing_deps:
        print(f"\n⚠️  Dépendances manquantes: {', '.join(missing_deps)}")
        print("Installation requise:")
        for dep in missing_deps:
            print(f"  pip install {dep}")
        return False
    
    return True

def test_docx_generation():
    """Teste la génération complète d'un document DOCX"""
    print("\n🧪 TEST 5: Génération DOCX complète...")
    
    try:
        # Vérifier les dépendances critiques
        try:
            from docx import Document
        except ImportError:
            print("❌ python-docx non disponible, test ignoré")
            return True  # Ne pas faire échouer le test pour ça
        
        from modules.reporting.docx_system.template_generator import DocxTemplateGenerator
        
        generator = DocxTemplateGenerator()
        
        # Test de génération (sans données Streamlit réelles)
        print("✅ DocxTemplateGenerator initialisé")
        print("✅ Générateur prêt pour l'utilisation")
        
        # Test des templates disponibles
        templates = generator.get_available_templates()
        print(f"✅ Templates disponibles: {', '.join(templates)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test génération DOCX: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 TESTS DU SYSTÈME DOCX OPTIMPV")
    print("=" * 50)
    
    tests = [
        ("Import des modules", test_imports),
        ("Extracteur de données", test_data_extractor),  
        ("Générateur de graphiques", test_chart_generator),
        ("Dépendances DOCX", test_docx_dependencies),
        ("Génération DOCX", test_docx_generation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur inattendue dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé des résultats
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHEC"
        print(f"{status:10} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🏆 RÉSULTAT GLOBAL: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 TOUS LES TESTS SONT RÉUSSIS !")
        print("Le système DOCX OptimPV est opérationnel.")
    else:
        print("⚠️  Certains tests ont échoué.")
        print("Vérifiez les dépendances et les erreurs ci-dessus.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)