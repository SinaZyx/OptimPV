#!/usr/bin/env python3
"""
Test de navigation par simulation OptimPV
========================================

Ce script simule la navigation dans l'application sans Selenium,
en testant directement les fonctions et méthodes de chaque module.
"""

import os
import sys
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from unittest.mock import Mock, patch, MagicMock

# Ajouter le chemin racine au sys.path
app_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(app_root))

class MockStreamlit:
    """Mock de Streamlit pour les tests."""
    
    def __init__(self):
        self.session_state = {}
        self.components = []
    
    def title(self, text): 
        self.components.append(f"TITLE: {text}")
        
    def header(self, text): 
        self.components.append(f"HEADER: {text}")
        
    def subheader(self, text): 
        self.components.append(f"SUBHEADER: {text}")
        
    def text(self, text): 
        self.components.append(f"TEXT: {text}")
        
    def markdown(self, text, **kwargs): 
        self.components.append(f"MARKDOWN: {text[:100]}...")
        
    def error(self, text): 
        self.components.append(f"ERROR: {text}")
        
    def warning(self, text): 
        self.components.append(f"WARNING: {text}")
        
    def success(self, text): 
        self.components.append(f"SUCCESS: {text}")
        
    def info(self, text): 
        self.components.append(f"INFO: {text}")
        
    def button(self, text, **kwargs): 
        self.components.append(f"BUTTON: {text}")
        return False
        
    def selectbox(self, label, options, **kwargs):
        self.components.append(f"SELECTBOX: {label}")
        return options[0] if options else None
        
    def text_input(self, label, **kwargs):
        self.components.append(f"INPUT: {label}")
        return "test_value"
        
    def number_input(self, label, **kwargs):
        self.components.append(f"NUMBER_INPUT: {label}")
        return 123
        
    def tabs(self, tab_names):
        self.components.append(f"TABS: {tab_names}")
        return [Mock() for _ in tab_names]
        
    def columns(self, spec):
        if isinstance(spec, int):
            cols = [Mock() for _ in range(spec)]
        else:
            cols = [Mock() for _ in spec]
        for col in cols:
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
        return cols
        
    def expander(self, title, **kwargs):
        mock_exp = Mock()
        mock_exp.__enter__ = Mock(return_value=mock_exp)
        mock_exp.__exit__ = Mock(return_value=None)
        self.components.append(f"EXPANDER: {title}")
        return mock_exp
        
    def sidebar(self):
        return self
        
    def container(self):
        return self
        
    def metric(self, label, value, delta=None):
        self.components.append(f"METRIC: {label} = {value}")
        
    def plotly_chart(self, fig, **kwargs):
        self.components.append(f"PLOTLY_CHART: {type(fig).__name__}")
        
    def dataframe(self, df, **kwargs):
        self.components.append(f"DATAFRAME: {len(df) if hasattr(df, '__len__') else 'unknown'} rows")
        
    def map(self, data, **kwargs):
        self.components.append(f"MAP: {len(data) if hasattr(data, '__len__') else 'unknown'} points")
        
    def rerun(self):
        self.components.append("RERUN")
        
    def set_page_config(self, **kwargs):
        self.components.append(f"PAGE_CONFIG: {kwargs}")

class NavigationSimulator:
    """Simulateur de navigation de l'application."""
    
    def __init__(self):
        self.mock_st = MockStreamlit()
        self.errors = []
        self.warnings = []
        self.successes = []
        self.tested_functions = []
        
        # Mock streamlit globalement
        sys.modules['streamlit'] = self.mock_st
        
    def log_error(self, component: str, error: str, traceback_str: str = ""):
        """Enregistre une erreur."""
        error_entry = {
            'component': component,
            'error': error,
            'traceback': traceback_str,
            'timestamp': datetime.now().isoformat()
        }
        self.errors.append(error_entry)
        print(f"❌ [{component}] {error}")
        
    def log_warning(self, component: str, warning: str):
        """Enregistre un avertissement."""
        warning_entry = {
            'component': component,
            'warning': warning,
            'timestamp': datetime.now().isoformat()
        }
        self.warnings.append(warning_entry)
        print(f"⚠️ [{component}] {warning}")
        
    def log_success(self, component: str, message: str):
        """Enregistre un succès."""
        success_entry = {
            'component': component,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.successes.append(success_entry)
        print(f"✅ [{component}] {message}")
    
    def test_config_module(self) -> bool:
        """Test le module de configuration."""
        print("\n⚙️ === TEST MODULE CONFIGURATION ===")
        
        try:
            from modules.config import ConfigModule
            
            # Initialiser le module
            config = ConfigModule()
            
            # Tester la méthode show_ui
            if hasattr(config, 'show_ui'):
                config.show_ui()
                self.log_success("ConfigModule", "Interface UI chargée sans erreur")
            else:
                self.log_warning("ConfigModule", "Méthode show_ui non trouvée")
            
            self.tested_functions.append("modules.config.ConfigModule")
            return True
            
        except Exception as e:
            self.log_error("ConfigModule", f"Erreur lors du test: {str(e)}", traceback.format_exc())
            return False
    
    def test_data_import_module(self) -> bool:
        """Test le module d'import de données."""
        print("\n📊 === TEST MODULE IMPORT DONNÉES ===")
        
        try:
            from modules.data_import import DataImportModule
            
            # Initialiser le module
            data_import = DataImportModule()
            
            # Tester la méthode show_ui
            if hasattr(data_import, 'show_ui'):
                data_import.show_ui()
                self.log_success("DataImportModule", "Interface UI chargée sans erreur")
            else:
                self.log_warning("DataImportModule", "Méthode show_ui non trouvée")
            
            self.tested_functions.append("modules.data_import.DataImportModule")
            return True
            
        except Exception as e:
            self.log_error("DataImportModule", f"Erreur lors du test: {str(e)}", traceback.format_exc())
            return False
    
    def test_storage_module(self) -> bool:
        """Test le module de stockage."""
        print("\n💾 === TEST MODULE STOCKAGE ===")
        
        try:
            from modules.storage import StorageModule
            
            # Initialiser le module
            storage = StorageModule()
            
            # Tester la méthode show_ui
            if hasattr(storage, 'show_ui'):
                storage.show_ui()
                self.log_success("StorageModule", "Interface UI chargée sans erreur")
            else:
                self.log_warning("StorageModule", "Méthode show_ui non trouvée")
            
            self.tested_functions.append("modules.storage.StorageModule")
            return True
            
        except Exception as e:
            self.log_error("StorageModule", f"Erreur lors du test: {str(e)}", traceback.format_exc())
            return False
    
    def test_erp_module(self) -> bool:
        """Test le module ERP."""
        print("\n🏢 === TEST MODULE ERP ===")
        
        try:
            from modules.erp_client import render_erp_module
            
            # Mock session state pour ERP
            self.mock_st.session_state = {
                'erp_services': None,
                'current_page': 'ERP Clients',
                'current_tab': 'Dashboard Commercial'
            }
            
            # Tester la fonction principale
            render_erp_module()
            self.log_success("ERPModule", "Interface principale chargée sans erreur")
            
            self.tested_functions.append("modules.erp_client.render_erp_module")
            return True
            
        except Exception as e:
            self.log_error("ERPModule", f"Erreur lors du test: {str(e)}", traceback.format_exc())
            return False
    
    def test_erp_services(self) -> bool:
        """Test les services ERP individuellement."""
        print("\n🔧 === TEST SERVICES ERP ===")
        
        services_tested = 0
        services_failed = 0
        
        # Test ClientService
        try:
            from modules.erp_client.services.client_service import ClientService
            client_service = ClientService()
            
            # Tester quelques méthodes
            if hasattr(client_service, 'get_all'):
                clients = client_service.get_all()
                self.log_success("ClientService", f"get_all() retourne {len(clients) if clients else 0} clients")
            
            if hasattr(client_service, 'get_statistics'):
                stats = client_service.get_statistics()
                self.log_success("ClientService", f"get_statistics() retourne {type(stats).__name__}")
            
            services_tested += 1
            
        except Exception as e:
            self.log_error("ClientService", f"Erreur: {str(e)}", traceback.format_exc())
            services_failed += 1
        
        # Test PricingService
        try:
            from modules.erp_client.services.pricing_service import PricingService
            pricing_service = PricingService()
            
            if hasattr(pricing_service, 'get_all_prices'):
                prices = pricing_service.get_all_prices()
                self.log_success("PricingService", f"get_all_prices() fonctionne")
            
            services_tested += 1
            
        except Exception as e:
            self.log_error("PricingService", f"Erreur: {str(e)}", traceback.format_exc())
            services_failed += 1
        
        # Test CapacityService
        try:
            from modules.erp_client.services.capacity_service import CapacityService
            capacity_service = CapacityService()
            
            if hasattr(capacity_service, 'get_dashboard_stats'):
                stats = capacity_service.get_dashboard_stats()
                self.log_success("CapacityService", f"get_dashboard_stats() fonctionne")
            
            services_tested += 1
            
        except Exception as e:
            self.log_error("CapacityService", f"Erreur: {str(e)}", traceback.format_exc())
            services_failed += 1
        
        print(f"   📊 Services testés: {services_tested}, Échecs: {services_failed}")
        return services_failed == 0
    
    def test_erp_ui_components(self) -> bool:
        """Test les composants UI du module ERP."""
        print("\n🎨 === TEST COMPOSANTS UI ERP ===")
        
        ui_components = [
            ('modules.erp_client.ui.client_form', 'render_client_form'),
            ('modules.erp_client.ui.client_list', 'render_client_list'),
            ('modules.erp_client.ui.pricing_dashboard', 'render_pricing_dashboard'),
            ('modules.erp_client.ui.commercial_dashboard', 'render_commercial_dashboard'),
            ('modules.erp_client.ui.autoconso_dashboard', 'render_autoconso_dashboard'),
        ]
        
        successful_components = 0
        
        for module_name, function_name in ui_components:
            try:
                module = __import__(module_name, fromlist=[function_name])
                ui_function = getattr(module, function_name)
                
                # Mock les paramètres nécessaires
                mock_services = {
                    'client': Mock(),
                    'pricing': Mock(),
                    'capacity': Mock(),
                    'inflation': Mock()
                }
                
                # Tester la fonction avec des mocks
                if function_name == 'render_client_form':
                    ui_function(client_service=mock_services['client'])
                elif function_name == 'render_client_list':
                    ui_function(client_service=mock_services['client'])
                elif function_name == 'render_pricing_dashboard':
                    ui_function(
                        client_service=mock_services['client'],
                        pricing_service=mock_services['pricing'],
                        inflation_service=mock_services['inflation']
                    )
                elif function_name == 'render_commercial_dashboard':
                    ui_function(
                        client_service=mock_services['client'],
                        pricing_service=mock_services['pricing'],
                        capacity_service=mock_services['capacity']
                    )
                elif function_name == 'render_autoconso_dashboard':
                    ui_function(
                        capacity_service=mock_services['capacity'],
                        client_service=mock_services['client']
                    )
                
                self.log_success(f"UI-{function_name}", "Composant chargé sans erreur")
                successful_components += 1
                
            except Exception as e:
                self.log_error(f"UI-{function_name}", f"Erreur: {str(e)}", traceback.format_exc())
        
        print(f"   🎨 Composants UI testés: {successful_components}/{len(ui_components)}")
        return successful_components == len(ui_components)
    
    def test_visualization_module(self) -> bool:
        """Test le module de visualisation."""
        print("\n📈 === TEST MODULE VISUALISATION ===")
        
        try:
            # Test du module moderne si disponible
            try:
                from modules.visualization import ModernVisualizationUI, MODERN_UI_AVAILABLE
                
                if MODERN_UI_AVAILABLE:
                    viz = ModernVisualizationUI()
                    self.log_success("VisualizationModule", "Interface moderne disponible")
                    
                    # Tester l'interface
                    if hasattr(viz, 'show_ui'):
                        viz.show_ui()
                        self.log_success("VisualizationModule", "show_ui() moderne fonctionne")
                else:
                    self.log_warning("VisualizationModule", "Interface moderne non disponible")
                
            except ImportError:
                # Fallback vers l'interface classique
                from modules.visualization.main_visualization_ui import VisualizationModule
                viz = VisualizationModule()
                
                if hasattr(viz, 'show_ui'):
                    viz.show_ui()
                    self.log_success("VisualizationModule", "Interface classique fonctionne")
            
            self.tested_functions.append("modules.visualization")
            return True
            
        except Exception as e:
            self.log_error("VisualizationModule", f"Erreur: {str(e)}", traceback.format_exc())
            return False
    
    def test_prospect_mapping(self) -> bool:
        """Test le module de cartographie de prospection."""
        print("\n🗺️ === TEST MODULE CARTOGRAPHIE ===")
        
        try:
            from modules.prospect_mapping import render_ui as show_prospect_map_ui
            
            # Tester la fonction d'interface
            show_prospect_map_ui()
            self.log_success("ProspectMapping", "Interface de cartographie chargée")
            
            self.tested_functions.append("modules.prospect_mapping")
            return True
            
        except Exception as e:
            self.log_error("ProspectMapping", f"Erreur: {str(e)}", traceback.format_exc())
            return False
    
    def test_facturation_module(self) -> bool:
        """Test le module de facturation."""
        print("\n💰 === TEST MODULE FACTURATION ===")
        
        try:
            from modules.facturation import show_facturation_page
            
            # Tester la fonction d'interface
            show_facturation_page()
            self.log_success("FacturationModule", "Interface de facturation chargée")
            
            self.tested_functions.append("modules.facturation")
            return True
            
        except Exception as e:
            self.log_error("FacturationModule", f"Erreur: {str(e)}", traceback.format_exc())
            return False
    
    def simulate_navigation(self) -> Dict:
        """Simule la navigation complète dans l'application."""
        print("🧪 === SIMULATION NAVIGATION OPTIMPV ===")
        
        start_time = datetime.now()
        
        # Tests des modules principaux
        test_results = {
            'config_module': self.test_config_module(),
            'data_import_module': self.test_data_import_module(),
            'storage_module': self.test_storage_module(),
            'erp_module': self.test_erp_module(),
            'erp_services': self.test_erp_services(),
            'erp_ui_components': self.test_erp_ui_components(),
            'visualization_module': self.test_visualization_module(),
            'prospect_mapping': self.test_prospect_mapping(),
            'facturation_module': self.test_facturation_module(),
        }
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Génération du rapport final
        report = {
            'timestamp': start_time.isoformat(),
            'duration': duration,
            'test_results': test_results,
            'errors': self.errors,
            'warnings': self.warnings,
            'successes': self.successes,
            'tested_functions': self.tested_functions,
            'streamlit_components': len(self.mock_st.components),
            'success_rate': sum(test_results.values()) / len(test_results) * 100,
            'overall_status': 'PASSED' if all(test_results.values()) else 'PARTIAL'
        }
        
        return report
    
    def generate_report_html(self, report: Dict, output_path: str):
        """Génère un rapport HTML."""
        
        html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport de Test Navigation Simulation - OptimPV</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; padding: 30px; }}
        .metric {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .success {{ border-left: 5px solid #27ae60; }}
        .warning {{ border-left: 5px solid #f39c12; }}
        .error {{ border-left: 5px solid #e74c3c; }}
        .section {{ padding: 30px; border-top: 1px solid #ecf0f1; }}
        pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Rapport Navigation Simulation - OptimPV</h1>
            <p>Test par simulation des modules sans interface graphique</p>
            <p>Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <div class="metric success">
                <h3>{len(report['successes'])}</h3>
                <p>Tests Réussis</p>
            </div>
            <div class="metric warning">
                <h3>{len(report['warnings'])}</h3>
                <p>Avertissements</p>
            </div>
            <div class="metric error">
                <h3>{len(report['errors'])}</h3>
                <p>Erreurs</p>
            </div>
            <div class="metric">
                <h3>{report['success_rate']:.1f}%</h3>
                <p>Taux de Succès</p>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Résultats par Module</h2>
            <ul>
                {''.join([f'<li>{"✅" if passed else "❌"} {module}: {"PASSED" if passed else "FAILED"}</li>' for module, passed in report["test_results"].items()])}
            </ul>
        </div>
        
        <div class="section">
            <h2>✅ Succès ({len(report['successes'])})</h2>
            {''.join([f'<div class="success"><strong>{s["component"]}:</strong> {s["message"]}</div>' for s in report["successes"]])}
        </div>
        
        <div class="section">
            <h2>❌ Erreurs ({len(report['errors'])})</h2>
            {''.join([f'<div class="error"><strong>{e["component"]}:</strong> {e["error"]}<br><small>{e["timestamp"]}</small></div>' for e in report["errors"]])}
        </div>
        
        <div class="section">
            <h2>📋 Fonctions Testées</h2>
            <ul>
                {''.join([f'<li>{func}</li>' for func in report["tested_functions"]])}
            </ul>
        </div>
    </div>
</body>
</html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📋 Rapport HTML généré: {output_path}")


def main():
    """Fonction principale."""
    print("🚀 === TEST NAVIGATION PAR SIMULATION ===")
    
    # Changer vers le répertoire de l'application
    original_cwd = os.getcwd()
    os.chdir(app_root)
    
    try:
        # Créer le simulateur et lancer les tests
        simulator = NavigationSimulator()
        report = simulator.simulate_navigation()
        
        # Génération des rapports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reports_dir = Path(__file__).parent / "test_reports"
        reports_dir.mkdir(exist_ok=True)
        
        json_path = reports_dir / f"navigation_simulation_{timestamp}.json"
        html_path = reports_dir / f"navigation_simulation_{timestamp}.html"
        
        # Rapport JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Rapport HTML
        simulator.generate_report_html(report, str(html_path))
        
        # Résumé final
        print(f"\n📊 === RÉSUMÉ FINAL ===")
        print(f"✅ Succès: {len(report['successes'])}")
        print(f"⚠️ Avertissements: {len(report['warnings'])}")
        print(f"❌ Erreurs: {len(report['errors'])}")
        print(f"🎯 Taux de succès: {report['success_rate']:.1f}%")
        print(f"⏱️ Durée: {report['duration']:.1f}s")
        print(f"🔧 Fonctions testées: {len(report['tested_functions'])}")
        print(f"📋 Statut: {report['overall_status']}")
        
        return 0 if report['overall_status'] == 'PASSED' else 1
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        traceback.print_exc()
        return 1
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)