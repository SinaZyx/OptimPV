#!/usr/bin/env python3
"""
Vérification des méthodes requises dans les services
==================================================

Script pour vérifier que toutes les méthodes appelées dans l'UI
existent bien dans les services.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set

class MethodVerifier:
    """Vérificateur de méthodes."""
    
    def __init__(self):
        self.service_methods = {}
        self.ui_calls = {}
        self.missing_methods = []
        
    def extract_methods_from_service(self, file_path: str, class_name: str) -> Set[str]:
        """Extrait les méthodes d'un service."""
        methods = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            methods.add(item.name)
                            
        except Exception as e:
            print(f"Erreur lecture {file_path}: {e}")
            
        return methods
    
    def extract_method_calls_from_ui(self, file_path: str, service_var: str) -> Set[str]:
        """Extrait les appels de méthodes depuis un fichier UI."""
        calls = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Recherche simple par regex pour les appels de service
            import re
            pattern = rf'{service_var}\.(\w+)\('
            matches = re.findall(pattern, content)
            calls.update(matches)
            
        except Exception as e:
            print(f"Erreur lecture {file_path}: {e}")
            
        return calls
    
    def verify_all_methods(self) -> Dict[str, any]:
        """Vérifie toutes les méthodes nécessaires."""
        
        base_path = Path(__file__).parent.parent.parent
        services_path = base_path / "services"
        ui_path = base_path / "ui"
        
        print("🔍 === VÉRIFICATION DES MÉTHODES ===\n")
        
        # Services à vérifier
        services = {
            'ClientService': 'client_service.py',
            'PricingService': 'pricing_service.py', 
            'CapacityService': 'capacity_service.py',
            'InflationService': 'inflation_service.py'
        }
        
        # Extraire les méthodes des services
        for service_name, file_name in services.items():
            file_path = services_path / file_name
            if file_path.exists():
                methods = self.extract_methods_from_service(str(file_path), service_name)
                self.service_methods[service_name] = methods
                print(f"✅ {service_name}: {len(methods)} méthodes trouvées")
            else:
                print(f"❌ {service_name}: fichier {file_name} non trouvé")
                self.service_methods[service_name] = set()
        
        print()
        
        # Fichiers UI à vérifier
        ui_files = {
            'client_list_pro.py': [
                ('client_service', 'ClientService'),
                ('pricing_service', 'PricingService'),
                ('capacity_service', 'CapacityService')
            ],
            'pricing_dashboard.py': [
                ('pricing_service', 'PricingService'),
                ('inflation_service', 'InflationService')
            ],
            'commercial_dashboard.py': [
                ('client_service', 'ClientService'),
                ('pricing_service', 'PricingService'),
                ('capacity_service', 'CapacityService')
            ],
            'autoconso_dashboard.py': [
                ('capacity_service', 'CapacityService'),
                ('client_service', 'ClientService')
            ]
        }
        
        # Vérifier les appels dans les fichiers UI
        all_verified = True
        
        for ui_file, service_mappings in ui_files.items():
            ui_file_path = ui_path / ui_file
            
            if not ui_file_path.exists():
                print(f"⚠️ Fichier UI {ui_file} non trouvé")
                continue
                
            print(f"📄 Vérification {ui_file}:")
            
            for service_var, service_class in service_mappings:
                calls = self.extract_method_calls_from_ui(str(ui_file_path), service_var)
                available_methods = self.service_methods.get(service_class, set())
                
                missing = calls - available_methods
                
                if missing:
                    all_verified = False
                    print(f"  ❌ {service_class}: méthodes manquantes: {', '.join(missing)}")
                    for method in missing:
                        self.missing_methods.append({
                            'ui_file': ui_file,
                            'service': service_class,
                            'method': method
                        })
                else:
                    print(f"  ✅ {service_class}: toutes les méthodes ({len(calls)}) présentes")
                    
                if calls:
                    print(f"     Appels détectés: {', '.join(sorted(calls))}")
        
        print()
        
        # Vérifications spécifiques connues
        specific_checks = [
            ('PricingService', 'get_average_price', 'Calcul prix moyen pour statistiques'),
            ('CapacityService', 'get_total_capacity', 'Capacité totale pour métriques'),
            ('ClientService', 'get_statistics', 'Statistiques générales clients'),
            ('CapacityService', 'get_dashboard_stats', 'Stats dashboard autoconsommation')
        ]
        
        print("🎯 Vérifications spécifiques:")
        for service, method, description in specific_checks:
            if method in self.service_methods.get(service, set()):
                print(f"  ✅ {service}.{method}() - {description}")
            else:
                print(f"  ❌ {service}.{method}() - {description}")
                all_verified = False
                self.missing_methods.append({
                    'ui_file': 'specific_check',
                    'service': service,
                    'method': method
                })
        
        return {
            'all_verified': all_verified,
            'missing_methods': self.missing_methods,
            'service_methods': {k: len(v) for k, v in self.service_methods.items()},
            'total_missing': len(self.missing_methods)
        }
    
    def generate_report(self, results: Dict) -> str:
        """Génère un rapport de vérification."""
        
        report = "RAPPORT DE VÉRIFICATION DES MÉTHODES\n"
        report += "=" * 50 + "\n\n"
        
        if results['all_verified']:
            report += "🎉 TOUTES LES MÉTHODES SONT PRÉSENTES!\n\n"
        else:
            report += f"❌ {results['total_missing']} MÉTHODES MANQUANTES\n\n"
            
            report += "Méthodes manquantes:\n"
            for missing in self.missing_methods:
                report += f"  - {missing['service']}.{missing['method']}() "
                report += f"(appelé dans {missing['ui_file']})\n"
            report += "\n"
        
        report += "Méthodes par service:\n"
        for service, count in results['service_methods'].items():
            report += f"  - {service}: {count} méthodes\n"
        
        return report

def main():
    """Fonction principale."""
    verifier = MethodVerifier()
    results = verifier.verify_all_methods()
    
    print("\n📊 === RÉSUMÉ ===")
    if results['all_verified']:
        print("🎉 Toutes les méthodes requises sont présentes!")
        print("✅ L'application devrait fonctionner correctement après installation des dépendances.")
    else:
        print(f"❌ {results['total_missing']} méthodes manquantes détectées")
        print("⚠️ Corrections nécessaires avant utilisation")
    
    # Sauvegarder le rapport
    report = verifier.generate_report(results)
    
    reports_dir = Path(__file__).parent / "test_reports"
    reports_dir.mkdir(exist_ok=True)
    
    report_file = reports_dir / "method_verification.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 Rapport sauvé: {report_file}")
    
    return 0 if results['all_verified'] else 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)