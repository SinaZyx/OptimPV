#!/usr/bin/env python3
"""
Test rapide de l'interface DOCX OptimPV
Pour tester rapidement sans passer par toute l'application
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

def main():
    print("🚀 TEST RAPIDE INTERFACE DOCX")
    print("=" * 50)
    
    # Simuler streamlit pour éviter les erreurs
    class MockStreamlit:
        class session_state:
            @staticmethod
            def get(key, default=None):
                # Données simulées pour les tests
                mock_data = {
                    'data_imported': True,
                    'config': {
                        'project_name': 'Test Solaire Rapide',
                        'client_name': 'Client Test',
                        'duree_ppa': 240,
                        'tarif_edf_reference': 0.20,
                        'puissance_crete_totale': 25.0
                    },
                    'constrained_optim_results': {
                        'Base': {
                            'prix_optimal': 0.16,
                            'prix_optimal_const': 0.16,
                            'puissance_kwc_total': 25.0,
                            'solar_consumption_mwh': 18.5,
                            'autoconsumption_rate': 0.78,
                            'solar_production_mwh': 23.7
                        }
                    },
                    'energy_data': {
                        'total_consumption': 45.2,
                        'solar_production': 23.7,
                        'solar_consumption': 18.5,
                        'autoconsumption_rate': 78.2
                    },
                    'financial_data': {
                        'prix_optimal': 0.16,
                        'economie_totale': 8500.0,
                        'economie_annuelle': 425.0
                    }
                }
                return mock_data.get(key, default)
        
        @staticmethod
        def warning(msg):
            print(f"⚠️ {msg}")
        
        @staticmethod
        def error(msg):
            print(f"❌ {msg}")
        
        @staticmethod
        def success(msg):
            print(f"✅ {msg}")
        
        @staticmethod
        def info(msg):
            print(f"ℹ️ {msg}")
        
        @staticmethod
        def markdown(msg):
            print(msg)
    
    # Remplacer streamlit
    sys.modules['streamlit'] = MockStreamlit()
    
    try:
        print("1. 🔍 Test import du module d'intégration...")
        from modules.reporting.docx_integration import DocxIntegrationModule
        print("   ✅ Module importé avec succès")
        
        print("\n2. 🏗️ Test initialisation...")
        docx_module = DocxIntegrationModule()
        print("   ✅ Module initialisé")
        
        print("\n3. 📊 Test statut du système...")
        status = docx_module.get_system_status()
        print(f"   📋 Statut obtenu: {len(status)} propriétés")
        
        for key, value in status.items():
            icon = "✅" if value else "❌"
            print(f"     {icon} {key}: {value}")
        
        print("\n4. 🎯 Test simulation interface...")
        
        if status.get('available', False):
            if status.get('dependencies_ready', False):
                print("   🎉 Interface complète DOCX disponible")
                print("   📄 L'utilisateur peut générer des rapports DOCX")
            else:
                print("   🔧 Interface d'installation disponible")
                print("   📦 L'utilisateur peut installer les dépendances")
        else:
            print("   ❌ Système DOCX non disponible")
        
        print("\n5. 🧪 Test gestionnaire de dépendances...")
        if docx_module.dependency_manager:
            missing = docx_module.dependency_manager.get_missing_dependencies()
            print(f"   📦 Dépendances manquantes: {len(missing)}")
            for dep in missing:
                print(f"     ❌ {dep}")
            
            if not missing:
                print("   ✅ Toutes les dépendances sont installées !")
        else:
            print("   ❌ Gestionnaire de dépendances non disponible")
        
        print("\n" + "=" * 50)
        print("📊 RÉSUMÉ DU TEST RAPIDE")
        print("=" * 50)
        
        if status.get('available', False):
            if status.get('dependencies_ready', False):
                print("🎉 SYSTÈME DOCX OPÉRATIONNEL")
                print("   • Interface complète disponible")
                print("   • Génération DOCX possible")
                print("   • Toutes les fonctionnalités actives")
            else:
                print("✅ SYSTÈME DOCX PARTIELLEMENT OPÉRATIONNEL")
                print("   • Interface d'installation disponible")
                print("   • Installation automatique possible")
                print("   • Rapport HTML de fallback disponible")
                print("\n💡 POUR ACTIVER COMPLÈTEMENT:")
                print("   ./install_docx_dependencies.sh")
        else:
            print("❌ PROBLÈME SYSTÈME DOCX")
            print("   • Vérifiez l'installation des modules")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        print("\n🐛 Détails:")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🎯 Test rapide sans app.py - Données simulées")
    print("🔄 Simule l'environnement OptimPV pour tester DOCX")
    print("")
    
    try:
        success = main()
        
        if success:
            print("\n🚀 INSTRUCTIONS POUR TESTER DANS OPTIMPV:")
            print("1. Lancez OptimPV: python app.py")
            print("2. Allez dans Rapports → Commercial")
            print("3. Cherchez la section 'Génération DOCX'")
            print("4. Si dépendances manquantes → Cliquez 'Installer'")
            print("5. Une fois installées → Générez vos rapports DOCX !")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrompu")
        sys.exit(1)