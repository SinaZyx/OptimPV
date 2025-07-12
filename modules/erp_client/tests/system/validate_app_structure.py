#!/usr/bin/env python3
"""
Validation de la structure de l'application OptimPV
=================================================

Ce script valide la structure de l'application sans Selenium,
vérifie les imports et analyse la configuration des modules.
"""

import os
import sys
import json
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Ajouter le chemin racine au sys.path
app_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(app_root))

class AppStructureValidator:
    """Validateur de structure d'application."""
    
    def __init__(self):
        self.app_root = app_root
        self.errors = []
        self.warnings = []
        self.success_checks = []
        
    def log_error(self, message: str):
        """Enregistre une erreur."""
        self.errors.append(f"❌ {message}")
        print(f"❌ {message}")
    
    def log_warning(self, message: str):
        """Enregistre un avertissement."""
        self.warnings.append(f"⚠️ {message}")
        print(f"⚠️ {message}")
    
    def log_success(self, message: str):
        """Enregistre un succès."""
        self.success_checks.append(f"✅ {message}")
        print(f"✅ {message}")
    
    def check_file_exists(self, relative_path: str, description: str = "") -> bool:
        """Vérifie qu'un fichier existe."""
        file_path = self.app_root / relative_path
        if file_path.exists():
            self.log_success(f"Fichier trouvé: {relative_path} {description}")
            return True
        else:
            self.log_error(f"Fichier manquant: {relative_path} {description}")
            return False
    
    def check_python_import(self, module_path: str, description: str = "") -> bool:
        """Vérifie qu'un module Python peut être importé."""
        try:
            # Convertir le chemin en nom de module
            module_name = module_path.replace("/", ".").replace(".py", "")
            if module_name.startswith("."):
                module_name = module_name[1:]
            
            spec = importlib.util.find_spec(module_name)
            if spec is not None:
                self.log_success(f"Module importable: {module_path} {description}")
                return True
            else:
                self.log_warning(f"Module non trouvé: {module_path} {description}")
                return False
        except Exception as e:
            self.log_error(f"Erreur import {module_path}: {str(e)} {description}")
            return False
    
    def validate_core_files(self) -> bool:
        """Valide la présence des fichiers core."""
        print("\n🔍 === VALIDATION FICHIERS CORE ===")
        
        core_files = [
            ("app.py", "Application principale Streamlit"),
            ("modules/__init__.py", "Module principal"),
            ("modules/config.py", "Configuration"),
            ("modules/data_import.py", "Import de données"),
            ("modules/storage.py", "Stockage"),
            ("modules/reporting.py", "Rapports"),
            ("modules/visualization/__init__.py", "Visualisation"),
            ("modules/erp_client/__init__.py", "Module ERP"),
            ("modules/erp_client/ui/main_interface.py", "Interface ERP principale"),
        ]
        
        all_good = True
        for file_path, description in core_files:
            if not self.check_file_exists(file_path, f"({description})"):
                all_good = False
        
        return all_good
    
    def validate_erp_structure(self) -> bool:
        """Valide la structure du module ERP."""
        print("\n🏢 === VALIDATION MODULE ERP ===")
        
        erp_files = [
            ("modules/erp_client/models/__init__.py", "Modèles de données"),
            ("modules/erp_client/models/client.py", "Modèle Client"),
            ("modules/erp_client/models/pricing.py", "Modèle Prix"),
            ("modules/erp_client/services/__init__.py", "Services"),
            ("modules/erp_client/services/client_service.py", "Service Client"),
            ("modules/erp_client/services/pricing_service.py", "Service Prix"),
            ("modules/erp_client/database/erp_database.py", "Base de données ERP"),
            ("modules/erp_client/ui/client_form.py", "Formulaire client"),
            ("modules/erp_client/ui/client_list.py", "Liste clients"),
            ("modules/erp_client/ui/pricing_dashboard.py", "Dashboard prix"),
            ("modules/erp_client/ui/commercial_dashboard.py", "Dashboard commercial"),
        ]
        
        all_good = True
        for file_path, description in erp_files:
            if not self.check_file_exists(file_path, f"({description})"):
                all_good = False
        
        return all_good
    
    def validate_imports(self) -> bool:
        """Valide les imports critiques."""
        print("\n📦 === VALIDATION IMPORTS ===")
        
        # Tester l'import de l'application principale
        try:
            # Changer vers le répertoire de l'application
            original_cwd = os.getcwd()
            os.chdir(self.app_root)
            
            # Import minimal de streamlit
            try:
                import streamlit
                self.log_success("Streamlit importé avec succès")
            except ImportError:
                self.log_error("Streamlit non installé ou non importable")
                return False
            
            # Test d'import des modules
            try:
                from modules.config import ConfigModule
                self.log_success("ConfigModule importé")
            except Exception as e:
                self.log_error(f"Erreur import ConfigModule: {e}")
            
            try:
                from modules.data_import import DataImportModule
                self.log_success("DataImportModule importé")
            except Exception as e:
                self.log_error(f"Erreur import DataImportModule: {e}")
            
            try:
                from modules.erp_client import render_erp_module
                self.log_success("Module ERP importé")
            except Exception as e:
                self.log_error(f"Erreur import module ERP: {e}")
            
            try:
                from modules.storage import StorageModule
                self.log_success("StorageModule importé")
            except Exception as e:
                self.log_error(f"Erreur import StorageModule: {e}")
            
        except Exception as e:
            self.log_error(f"Erreur générale lors des tests d'import: {e}")
            return False
        finally:
            os.chdir(original_cwd)
        
        return True
    
    def analyze_streamlit_pages(self) -> Dict:
        """Analyse la structure des pages Streamlit."""
        print("\n📄 === ANALYSE PAGES STREAMLIT ===")
        
        app_file = self.app_root / "app.py"
        if not app_file.exists():
            self.log_error("app.py non trouvé")
            return {}
        
        try:
            with open(app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Chercher les pages définies
            pages_found = []
            
            # Patterns pour détecter les pages
            import re
            
            # Chercher les boutons de navigation
            nav_pattern = r'button.*f["\'].*?([^"\']+)["\'].*nav_'
            nav_matches = re.findall(nav_pattern, content)
            for match in nav_matches:
                if match not in pages_found:
                    pages_found.append(match)
            
            # Chercher les conditions de page
            page_pattern = r'current_page\s*==\s*["\']([^"\']+)["\']'
            page_matches = re.findall(page_pattern, content)
            for match in page_matches:
                if match not in pages_found:
                    pages_found.append(match)
            
            self.log_success(f"Pages détectées: {len(pages_found)}")
            for page in pages_found:
                print(f"   📄 {page}")
            
            # Chercher les onglets ERP
            tab_pattern = r'["\']([^"\']*(?:Dashboard|Clients|Nouveau|Tarification|Autoconsommation|Cartographie|Analytics)[^"\']*)["\']'
            tab_matches = re.findall(tab_pattern, content)
            erp_tabs = [tab for tab in tab_matches if any(keyword in tab for keyword in ['Dashboard', 'Clients', 'Nouveau', 'Tarification', 'Autoconsommation', 'Cartographie', 'Analytics'])]
            
            if erp_tabs:
                self.log_success(f"Onglets ERP détectés: {len(erp_tabs)}")
                for tab in erp_tabs:
                    print(f"   📋 {tab}")
            
            return {
                'pages': pages_found,
                'erp_tabs': erp_tabs,
                'total_lines': len(content.split('\n'))
            }
            
        except Exception as e:
            self.log_error(f"Erreur analyse app.py: {e}")
            return {}
    
    def check_dependencies(self) -> bool:
        """Vérifie les dépendances critiques."""
        print("\n📦 === VÉRIFICATION DÉPENDANCES ===")
        
        critical_deps = [
            ('streamlit', 'Interface utilisateur'),
            ('pandas', 'Manipulation de données'),
            ('plotly', 'Graphiques interactifs'),
            ('sqlite3', 'Base de données (builtin)'),
        ]
        
        optional_deps = [
            ('folium', 'Cartes interactives'),
            ('requests', 'Requêtes HTTP'),
            ('openpyxl', 'Fichiers Excel'),
        ]
        
        all_critical = True
        
        # Dépendances critiques
        for dep, description in critical_deps:
            try:
                __import__(dep)
                self.log_success(f"Dépendance critique: {dep} ({description})")
            except ImportError:
                self.log_error(f"Dépendance critique manquante: {dep} ({description})")
                all_critical = False
        
        # Dépendances optionnelles
        for dep, description in optional_deps:
            try:
                __import__(dep)
                self.log_success(f"Dépendance optionnelle: {dep} ({description})")
            except ImportError:
                self.log_warning(f"Dépendance optionnelle manquante: {dep} ({description})")
        
        return all_critical
    
    def generate_validation_report(self) -> Dict:
        """Génère un rapport de validation."""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'app_root': str(self.app_root),
            'total_checks': len(self.success_checks) + len(self.warnings) + len(self.errors),
            'success_count': len(self.success_checks),
            'warning_count': len(self.warnings),
            'error_count': len(self.errors),
            'success_checks': self.success_checks,
            'warnings': self.warnings,
            'errors': self.errors,
            'overall_status': 'PASSED' if len(self.errors) == 0 else 'FAILED'
        }
        
        return report
    
    def run_full_validation(self) -> Dict:
        """Lance la validation complète."""
        print("🔍 === VALIDATION STRUCTURE APPLICATION OPTIMPV ===")
        print(f"Répertoire racine: {self.app_root}")
        
        # Validation étape par étape
        self.validate_core_files()
        self.validate_erp_structure()
        self.validate_imports()
        self.analyze_streamlit_pages()
        self.check_dependencies()
        
        # Génération du rapport
        report = self.generate_validation_report()
        
        # Résumé final
        print(f"\n📊 === RÉSUMÉ VALIDATION ===")
        print(f"✅ Succès: {report['success_count']}")
        print(f"⚠️ Avertissements: {report['warning_count']}")
        print(f"❌ Erreurs: {report['error_count']}")
        print(f"🎯 Statut global: {report['overall_status']}")
        
        # Sauvegarder le rapport
        reports_dir = Path(__file__).parent / "test_reports"
        reports_dir.mkdir(exist_ok=True)
        
        report_file = reports_dir / f"structure_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Rapport sauvé: {report_file}")
        
        return report


def main():
    """Fonction principale."""
    validator = AppStructureValidator()
    report = validator.run_full_validation()
    
    # Code de retour basé sur le résultat
    return 0 if report['overall_status'] == 'PASSED' else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)