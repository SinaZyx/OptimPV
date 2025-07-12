"""
Test du système DOCX pour OptimPV
=================================

Tests pour vérifier le bon fonctionnement du système de génération de rapports DOCX.
"""

import sys
import os
import tempfile
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from modules.reporting.docx_system import DocxGenerator, TemplateManager, DataMapper, ChartInserter
    DOCX_SYSTEM_AVAILABLE = True
    print("✅ Système DOCX importé avec succès")
except ImportError as e:
    DOCX_SYSTEM_AVAILABLE = False
    print(f"❌ Erreur d'import du système DOCX: {e}")
    print("Pour installer les dépendances: pip install python-docx")

def create_test_data():
    """Crée des données de test réalistes"""
    
    project_config = {
        'global_config': {
            'duree_ppa': 240,  # 20 ans
            'tarif_edf_reference': 0.20,
            'taux_inflation': 0.02,
            'date_debut_ppa': '2025-01-01'
        },
        'sites_config': {
            'site_prod_1': {
                'site_type': 'Producteur',
                'puissance_kwc': 25.5,
                'capex': 45000,
                'opex_maintenance': 600,
                'opex_insurance': 200,
                'opex_admin': 150
            },
            'site_conso_1': {
                'site_type': 'Consommateur Pur'
            },
            'site_conso_2': {
                'site_type': 'Consommateur Pur'
            }
        }
    }
    
    financial_data = {
        'economie_totale': 65000,
        'prix_optimal': 0.16,
        'van_project': 25000,
        'tri_project': 8.5,
        'payback_simple': 12.3,
        'cout_sans_pv_total': 110000,
        'cout_avec_pv_total': 45000
    }
    
    energy_data = {
        'total_production': 28.5,  # MWh
        'total_consumption': 52.0,  # MWh
        'total_autoconsumption': 18.5,  # MWh
        'total_grid_purchase': 33.5,  # MWh
        'autoconsumption_rate': 35.6,  # %
        'autoproduction_rate': 64.9   # %
    }
    
    return project_config, financial_data, energy_data

def test_docx_generator():
    """Test du générateur DOCX principal"""
    print("\n🧪 Test du générateur DOCX...")
    
    if not DOCX_SYSTEM_AVAILABLE:
        print("❌ Système DOCX non disponible - test ignoré")
        return False
    
    try:
        # Créer le générateur
        generator = DocxGenerator()
        print("✅ DocxGenerator créé")
        
        # Créer un document de base
        doc = generator.create_base_document()
        print("✅ Document de base créé")
        
        # Tester l'ajout d'en-tête/pied de page
        generator.add_header_footer(doc, "Test OptimPV")
        print("✅ En-tête et pied de page ajoutés")
        
        # Tester la page de garde
        generator.add_cover_page(doc, "Rapport de Test", "Client Test", "Projet Test")
        print("✅ Page de garde ajoutée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test générateur: {e}")
        return False

def test_template_manager():
    """Test du gestionnaire de templates"""
    print("\n🧪 Test du gestionnaire de templates...")
    
    if not DOCX_SYSTEM_AVAILABLE:
        print("❌ Système DOCX non disponible - test ignoré")
        return False
    
    try:
        # Créer le gestionnaire
        manager = TemplateManager()
        print("✅ TemplateManager créé")
        
        # Lister les templates
        templates = manager.list_templates()
        print(f"✅ Templates trouvés: {templates}")
        
        # Récupérer un template
        if templates:
            template = manager.get_template(templates[0])
            if template:
                print(f"✅ Template '{templates[0]}' récupéré")
            else:
                print(f"⚠️ Template '{templates[0]}' non récupérable")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test template manager: {e}")
        return False

def test_data_mapper():
    """Test du mappeur de données"""
    print("\n🧪 Test du mappeur de données...")
    
    if not DOCX_SYSTEM_AVAILABLE:
        print("❌ Système DOCX non disponible - test ignoré")
        return False
    
    try:
        # Créer le mappeur
        mapper = DataMapper()
        print("✅ DataMapper créé")
        
        # Créer des données de test
        project_config, financial_data, energy_data = create_test_data()
        
        # Créer un mapping de données
        data_map = mapper._create_data_mapping(
            project_config, financial_data, energy_data,
            "Test Title", "Test Client", "Test Project"
        )
        
        print(f"✅ Mapping créé avec {len(data_map)} entrées")
        
        # Vérifier quelques clés importantes
        important_keys = ['POWER_KWC', 'TOTAL_SAVINGS', 'OPTIMAL_PRICE', 'ANNUAL_PRODUCTION']
        for key in important_keys:
            if key in data_map:
                print(f"✅ {key}: {data_map[key]}")
            else:
                print(f"⚠️ {key} manquant dans le mapping")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test data mapper: {e}")
        return False

def test_chart_inserter():
    """Test de l'inserteur de graphiques"""
    print("\n🧪 Test de l'inserteur de graphiques...")
    
    if not DOCX_SYSTEM_AVAILABLE:
        print("❌ Système DOCX non disponible - test ignoré")
        return False
    
    try:
        # Créer l'inserteur
        inserter = ChartInserter()
        print("✅ ChartInserter créé")
        
        # Tester la création d'un graphique simple
        test_data = {'A': 10, 'B': 20, 'C': 15}
        fig = inserter.create_simple_bar_chart(test_data, "Test Chart", "Catégories", "Valeurs")
        
        if fig:
            print("✅ Graphique en barres créé")
        else:
            print("⚠️ Graphique en barres non créé (plotly non disponible)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test chart inserter: {e}")
        return False

def test_full_report_generation():
    """Test de génération complète d'un rapport"""
    print("\n🧪 Test de génération complète de rapport...")
    
    if not DOCX_SYSTEM_AVAILABLE:
        print("❌ Système DOCX non disponible - test ignoré")
        return False
    
    try:
        # Créer le générateur
        generator = DocxGenerator()
        
        # Créer des données de test
        project_config, financial_data, energy_data = create_test_data()
        
        # Générer le rapport complet
        doc = generator.generate_customer_report(
            project_config=project_config,
            financial_data=financial_data,
            energy_data=energy_data,
            title="Rapport Test OptimPV",
            client_name="Client de Test",
            project_name="Installation Test 25 kWc"
        )
        
        print("✅ Rapport complet généré")
        
        # Sauvegarder dans un fichier temporaire pour vérification
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
            doc.save(tmp_file.name)
            file_size = os.path.getsize(tmp_file.name)
            print(f"✅ Rapport sauvegardé: {tmp_file.name} ({file_size} bytes)")
            
            # Nettoyer
            try:
                os.unlink(tmp_file.name)
            except:
                pass
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de génération complète: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_with_customer_report():
    """Test d'intégration avec le module customer_report"""
    print("\n🧪 Test d'intégration avec customer_report...")
    
    try:
        from modules.reporting.customer_report import CustomerReportingModule
        
        # Créer le module
        customer_module = CustomerReportingModule()
        print("✅ CustomerReportingModule créé")
        
        # Vérifier la disponibilité DOCX
        if hasattr(customer_module, 'docx_generator') and customer_module.docx_generator:
            print("✅ Générateur DOCX disponible dans CustomerReportingModule")
            
            # Tester la génération DOCX (sans vraies données de session)
            doc = customer_module.generate_docx_report(
                title="Test Integration",
                client_name="Test Client",
                project_name="Test Project"
            )
            
            if doc:
                print("✅ Génération DOCX via CustomerReportingModule réussie")
            else:
                print("⚠️ Génération DOCX retournée None (données manquantes)")
            
        else:
            print("⚠️ Générateur DOCX non disponible dans CustomerReportingModule")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test d'intégration: {e}")
        return False

def main():
    """Fonction principale des tests"""
    print("🚀 Démarrage des tests du système DOCX OptimPV")
    print("=" * 60)
    
    tests = [
        test_docx_generator,
        test_template_manager,
        test_data_mapper,
        test_chart_inserter,
        test_full_report_generation,
        test_integration_with_customer_report
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Erreur fatale dans {test.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 Résumé des tests:")
    
    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests
    
    print(f"✅ Tests réussis: {passed_tests}/{total_tests}")
    print(f"❌ Tests échoués: {failed_tests}/{total_tests}")
    
    if failed_tests == 0:
        print("\n🎉 Tous les tests sont passés ! Le système DOCX est opérationnel.")
    else:
        print(f"\n⚠️ {failed_tests} test(s) ont échoué. Vérifiez les erreurs ci-dessus.")
        
        if not DOCX_SYSTEM_AVAILABLE:
            print("\n💡 Pour activer le système DOCX, installez les dépendances:")
            print("   pip install python-docx")
            print("   pip install plotly pillow  # Pour les graphiques")
    
    return failed_tests == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)