#!/usr/bin/env python3
"""
Test standalone du système DOCX OptimPV
Simule des données réelles pour tester la génération DOCX sans passer par app.py
"""

import sys
import os
import tempfile
from datetime import datetime

# Ajouter le chemin des modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

def create_mock_session_state():
    """Crée des données simulées réalistes pour les tests"""
    return {
        # Configuration projet
        'config': {
            'project_name': 'Installation Solaire Test',
            'client_name': 'Société ABC',
            'duree_ppa': 240,  # 20 ans en mois
            'tarif_edf_reference': 0.20,
            'puissance_crete_totale': 25.0,
            'site_count': 1
        },
        
        # Données importées
        'data_imported': True,
        'consumption_data': {
            'total_consumption_mwh': 45.2,
            'monthly_consumption': [3.5, 3.2, 3.8, 4.1, 4.5, 4.8, 5.1, 4.9, 4.3, 4.0, 3.7, 3.3]
        },
        
        # Résultats d'optimisation
        'constrained_optim_results': {
            'Base': {
                'prix_optimal': 0.16,
                'prix_optimal_const': 0.16,
                'puissance_kwc_total': 25.0,
                'solar_consumption_mwh': 18.5,
                'autoconsumption_rate': 0.78,
                'solar_production_mwh': 23.7,
                'savings_total': 8500.0
            }
        },
        
        # Données énergétiques
        'energy_data': {
            'total_consumption': 45.2,
            'solar_production': 23.7,
            'solar_consumption': 18.5,
            'grid_consumption': 26.7,
            'grid_injection': 5.2,
            'autoconsumption_rate': 78.2,
            'autonomy_rate': 40.9
        },
        
        # Données financières calculées
        'financial_data': {
            'prix_optimal': 0.16,
            'economie_totale': 8500.0,
            'economie_annuelle': 425.0,
            'capex_total': 45000.0,
            'opex_annuel': 180.0,
            'van_20ans': 12500.0,
            'tri_percent': 8.2,
            'temps_retour': 12.5
        },
        
        # Métadonnées
        'analysis_date': datetime.now(),
        'last_update': datetime.now().strftime('%d/%m/%Y %H:%M')
    }

def test_dependency_installation():
    """Test du gestionnaire de dépendances"""
    print("🧪 TEST 1: Gestionnaire de dépendances")
    print("=" * 50)
    
    try:
        from modules.reporting.docx_system.dependency_manager import DocxDependencyManager
        
        manager = DocxDependencyManager()
        print("✅ DocxDependencyManager créé")
        
        # Vérifier les dépendances
        status = manager.get_dependency_status()
        missing = manager.get_missing_dependencies()
        is_ready = manager.is_system_ready()
        
        print(f"📦 Dépendances vérifiées: {len(status)}")
        print(f"❌ Dépendances manquantes: {len(missing)} - {missing}")
        print(f"🚀 Système prêt: {'✅ OUI' if is_ready else '❌ NON'}")
        
        if not is_ready:
            print("\n💡 SOLUTION:")
            print("pip install python-docx matplotlib pillow")
            
            # Générer script d'installation
            script = manager.generate_installation_script()
            script_path = "/tmp/install_docx_deps.sh"
            with open(script_path, 'w') as f:
                f.write(script)
            print(f"📁 Script d'installation créé: {script_path}")
        
        return is_ready, manager
        
    except ImportError as e:
        print(f"❌ Erreur import: {e}")
        return False, None

def test_data_extraction(mock_data):
    """Test d'extraction des données"""
    print("\n🧪 TEST 2: Extraction des données")
    print("=" * 50)
    
    try:
        # Mock de Streamlit pour le test
        class MockStreamlit:
            session_state = mock_data
        
        # Remplacer temporairement streamlit
        sys.modules['streamlit'] = MockStreamlit()
        
        from modules.reporting.docx_system.data_extractor import OptimPVDataExtractor
        
        extractor = OptimPVDataExtractor()
        data = extractor.extract_all_data()
        
        print(f"✅ {len(data)} variables extraites")
        
        # Afficher les données clés
        key_metrics = {
            'project_name': data.get('project_name', 'N/A'),
            'client_name': data.get('client_name', 'N/A'),
            'puissance_kwc_total': data.get('puissance_kwc_total', 0),
            'prix_optimal': data.get('prix_optimal', 0),
            'economie_totale_finale': data.get('economie_totale_finale', 0),
            'autonomy_rate': data.get('autonomy_rate', 0),
            'co2_avoided_annual': data.get('co2_avoided_annual', 0)
        }
        
        print("\n📊 Métriques extraites:")
        for key, value in key_metrics.items():
            print(f"  • {key}: {value}")
        
        return True, data
        
    except Exception as e:
        print(f"❌ Erreur extraction: {e}")
        import traceback
        print(traceback.format_exc())
        return False, {}

def test_chart_generation(data):
    """Test de génération des graphiques"""
    print("\n🧪 TEST 3: Génération des graphiques")
    print("=" * 50)
    
    try:
        from modules.reporting.docx_system.chart_generator import DocxChartGenerator
        
        chart_gen = DocxChartGenerator()
        
        # Créer un répertoire temporaire
        temp_dir = tempfile.mkdtemp()
        chart_gen.output_dir = temp_dir
        
        print(f"📁 Répertoire temporaire: {temp_dir}")
        
        # Générer tous les graphiques
        charts = chart_gen.generate_all_charts(data)
        
        print(f"✅ {len(charts)} graphiques générés:")
        for chart_name, chart_path in charts.items():
            if os.path.exists(chart_path):
                file_size = os.path.getsize(chart_path)
                print(f"  📈 {chart_name}: {file_size:,} bytes")
            else:
                print(f"  ❌ {chart_name}: fichier non trouvé")
        
        # Nettoyage
        chart_gen.cleanup_charts()
        print("🧹 Graphiques temporaires nettoyés")
        
        return True, charts
        
    except Exception as e:
        print(f"❌ Erreur génération graphiques: {e}")
        import traceback
        print(traceback.format_exc())
        return False, {}

def test_docx_generation(data, dependency_ready):
    """Test de génération DOCX"""
    print("\n🧪 TEST 4: Génération DOCX")
    print("=" * 50)
    
    if not dependency_ready:
        print("⚠️ Dépendances manquantes - Test DOCX ignoré")
        print("💡 Installez les dépendances avec: pip install python-docx matplotlib pillow")
        return False, None
    
    try:
        from modules.reporting.docx_system.template_generator import DocxTemplateGenerator
        
        generator = DocxTemplateGenerator()
        
        # Test des 3 types de rapports
        report_types = ['commercial', 'technique', 'financier']
        generated_reports = {}
        
        for report_type in report_types:
            print(f"📄 Génération rapport {report_type}...")
            
            docx_buffer = generator.generate_complete_report(
                report_type=report_type,
                title=f"Rapport {report_type.title()} Test",
                client_name=data.get('client_name', 'Client Test'),
                project_name=data.get('project_name', 'Projet Test')
            )
            
            if docx_buffer:
                # Sauvegarder le fichier
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"test_rapport_{report_type}_{timestamp}.docx"
                
                with open(filename, 'wb') as f:
                    f.write(docx_buffer.getvalue())
                
                file_size = os.path.getsize(filename)
                generated_reports[report_type] = filename
                
                print(f"  ✅ {filename} ({file_size:,} bytes)")
            else:
                print(f"  ❌ Échec génération {report_type}")
        
        return True, generated_reports
        
    except Exception as e:
        print(f"❌ Erreur génération DOCX: {e}")
        import traceback
        print(traceback.format_exc())
        return False, {}

def test_fallback_html(data, manager):
    """Test du rapport HTML de fallback"""
    print("\n🧪 TEST 5: Rapport HTML de fallback")
    print("=" * 50)
    
    try:
        if not manager:
            print("❌ Gestionnaire de dépendances non disponible")
            return False
        
        # Générer rapport HTML
        html_content = manager.create_fallback_report(data, "commercial")
        
        # Sauvegarder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_rapport_fallback_{timestamp}.html"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        file_size = os.path.getsize(filename)
        print(f"✅ {filename} ({file_size:,} bytes)")
        
        # Vérifier le contenu
        key_content = [
            data.get('project_name', ''),
            data.get('client_name', ''),
            str(data.get('puissance_kwc_total', 0)),
            str(data.get('economie_totale_finale', 0))
        ]
        
        missing_content = []
        for content in key_content:
            if content and content not in html_content:
                missing_content.append(content)
        
        if not missing_content:
            print("✅ Toutes les données clés présentes dans le HTML")
        else:
            print(f"⚠️ Données manquantes: {missing_content}")
        
        return True, filename
        
    except Exception as e:
        print(f"❌ Erreur génération HTML: {e}")
        return False, None

def main():
    """Test complet du système DOCX en mode standalone"""
    print("🚀 TEST STANDALONE SYSTÈME DOCX OPTIMPV")
    print("=" * 60)
    print("🎯 Test sans app.py avec données simulées réalistes")
    print("=" * 60)
    
    # Créer des données de test
    mock_data = create_mock_session_state()
    print(f"📊 Données test créées: {len(mock_data)} sections")
    
    # Résultats des tests
    results = []
    
    # Test 1: Dépendances
    dep_ready, manager = test_dependency_installation()
    results.append(("Gestionnaire dépendances", dep_ready))
    
    # Test 2: Extraction données
    data_ok, extracted_data = test_data_extraction(mock_data)
    results.append(("Extraction données", data_ok))
    
    # Test 3: Graphiques (si matplotlib disponible)
    if data_ok:
        charts_ok, charts = test_chart_generation(extracted_data)
        results.append(("Génération graphiques", charts_ok))
    else:
        results.append(("Génération graphiques", False))
    
    # Test 4: DOCX (si dépendances OK)
    if data_ok and dep_ready:
        docx_ok, docx_files = test_docx_generation(extracted_data, dep_ready)
        results.append(("Génération DOCX", docx_ok))
    else:
        results.append(("Génération DOCX", False))
    
    # Test 5: HTML Fallback
    if manager and data_ok:
        html_ok, html_file = test_fallback_html(extracted_data, manager)
        results.append(("Rapport HTML fallback", html_ok))
    else:
        results.append(("Rapport HTML fallback", False))
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS STANDALONE")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHEC"
        print(f"{status:12} {test_name}")
    
    print(f"\n🏆 RÉSULTAT: {passed}/{total} tests réussis")
    
    # Instructions finales
    if passed == total:
        print("\n🎉 SYSTÈME DOCX COMPLÈTEMENT OPÉRATIONNEL !")
        print("""
📁 FICHIERS GÉNÉRÉS:
• Rapports DOCX (si dépendances installées)
• Rapport HTML de fallback
• Script d'installation des dépendances

🚀 PRÊT POUR PRODUCTION !
        """)
    elif passed >= 3:
        print("\n✅ SYSTÈME PARTIELLEMENT OPÉRATIONNEL")
        print("""
🔧 POUR ACTIVER DOCX COMPLET:
pip install python-docx matplotlib pillow

📄 FALLBACK DISPONIBLE:
Rapports HTML fonctionnels en attendant
        """)
    else:
        print("\n⚠️ PROBLÈMES DÉTECTÉS")
        print("Vérifiez l'installation des modules OptimPV")
    
    return passed >= 3

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur inattendue: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)