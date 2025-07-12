"""
Test d'intégrité des imports pour le module erp_client.
Ce fichier teste tous les imports et vérifie l'intégrité des modules.

Ce test détecte spécifiquement :
- Les erreurs ModuleNotFoundError et ImportError
- Les imports vers des modules inexistants (comme models.pricing)
- Les dépendances manquantes (comme streamlit)
- Les erreurs de syntaxe Python
- L'intégrité de tous les fichiers Python du module

Usage:
    pytest modules/erp_client/tests/test_imports_integrity.py -v
    
    Ou exécution directe:
    python modules/erp_client/tests/test_imports_integrity.py
"""

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

import os
import sys
import ast
import importlib
import traceback
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional


class ImportChecker:
    """Vérificateur d'imports pour le module erp_client."""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.errors: List[Dict[str, str]] = []
        self.warnings: List[Dict[str, str]] = []
        self.successful_imports: List[str] = []
        
    def get_all_python_files(self) -> List[Path]:
        """Récupère tous les fichiers Python du module."""
        python_files = []
        for root, dirs, files in os.walk(self.base_path):
            # Ignorer les dossiers de cache et tests
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.pytest_cache', 'venv', '.venv']]
            
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    python_files.append(Path(root) / file)
        
        return sorted(python_files)
    
    def extract_imports_from_file(self, file_path: Path) -> Tuple[Set[str], Set[str], List[Dict[str, str]]]:
        """
        Extrait tous les imports d'un fichier Python.
        
        Returns:
            - imports: ensemble des modules importés directement
            - from_imports: ensemble des imports "from X import Y"
            - problematic_imports: liste des imports problématiques détectés
        """
        imports = set()
        from_imports = set()
        problematic_imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        from_imports.add(f"{node.module}")
                        
                        # Détecter les imports problématiques spécifiques
                        if node.module == "..models.pricing":
                            problematic_imports.append({
                                'type': 'missing_module',
                                'module': node.module,
                                'line': getattr(node, 'lineno', 'unknown'),
                                'issue': 'Module models.pricing introuvable',
                                'suggestion': 'Créer le module ou corriger l\'import'
                            })
                        
                        for alias in node.names:
                            if alias.name != '*':
                                full_import = f"{node.module}.{alias.name}"
                                from_imports.add(full_import)
                                
                                # Détecter PrixClient et TypeTarif depuis models.pricing
                                if node.module == "..models.pricing" and alias.name in ['PrixClient', 'TypeTarif']:
                                    problematic_imports.append({
                                        'type': 'missing_class',
                                        'module': node.module,
                                        'class': alias.name,
                                        'line': getattr(node, 'lineno', 'unknown'),
                                        'issue': f'Classe {alias.name} importée depuis module inexistant',
                                        'suggestion': f'Définir {alias.name} dans le bon module ou corriger l\'import'
                                    })
            
        except Exception as e:
            self.errors.append({
                'file': str(file_path),
                'error': f"Erreur lors de l'analyse AST: {str(e)}",
                'type': 'ast_error'
            })
        
        return imports, from_imports, problematic_imports
    
    def check_file_syntax(self, file_path: Path) -> bool:
        """Vérifie la syntaxe d'un fichier Python."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                compile(f.read(), str(file_path), 'exec')
            return True
        except SyntaxError as e:
            self.errors.append({
                'file': str(file_path),
                'error': f"Erreur de syntaxe ligne {e.lineno}: {e.msg}",
                'type': 'syntax_error'
            })
            return False
        except Exception as e:
            self.errors.append({
                'file': str(file_path),
                'error': f"Erreur lors de la compilation: {str(e)}",
                'type': 'compile_error'
            })
            return False
    
    def try_import_module(self, module_name: str, file_path: Optional[Path] = None) -> bool:
        """
        Tente d'importer un module et capture les erreurs.
        """
        try:
            # Ajouter le chemin du module erp_client au sys.path
            erp_client_path = self.base_path.parent.parent
            if str(erp_client_path) not in sys.path:
                sys.path.insert(0, str(erp_client_path))
            
            # Essayer d'importer le module
            importlib.import_module(module_name)
            self.successful_imports.append(module_name)
            return True
            
        except ModuleNotFoundError as e:
            error_msg = f"Module introuvable: {e.name}"
            if hasattr(e, 'path'):
                error_msg += f" (cherché dans: {e.path})"
            
            self.errors.append({
                'file': str(file_path) if file_path else module_name,
                'error': error_msg,
                'type': 'module_not_found',
                'module': module_name,
                'missing_module': e.name
            })
            return False
            
        except ImportError as e:
            self.errors.append({
                'file': str(file_path) if file_path else module_name,
                'error': f"Erreur d'import: {str(e)}",
                'type': 'import_error',
                'module': module_name,
                'details': traceback.format_exc()
            })
            return False
            
        except Exception as e:
            self.errors.append({
                'file': str(file_path) if file_path else module_name,
                'error': f"Erreur inattendue: {str(e)}",
                'type': 'unexpected_error',
                'module': module_name,
                'details': traceback.format_exc()
            })
            return False
    
    def convert_path_to_module(self, file_path: Path) -> str:
        """Convertit un chemin de fichier en nom de module."""
        # Obtenir le chemin relatif depuis le dossier parent du module erp_client
        rel_path = file_path.relative_to(self.base_path.parent.parent)
        
        # Convertir en nom de module
        parts = list(rel_path.parts[:-1])  # Enlever le nom du fichier
        if rel_path.stem != '__init__':
            parts.append(rel_path.stem)
        
        return '.'.join(parts)
    
    def check_all_imports(self) -> Dict[str, any]:
        """Vérifie tous les imports du module erp_client."""
        results = {
            'total_files': 0,
            'syntax_errors': 0,
            'import_errors': 0,
            'successful_imports': 0,
            'problematic_imports': 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'details': {},
            'problematic_files': []
        }
        
        python_files = self.get_all_python_files()
        results['total_files'] = len(python_files)
        
        # Phase 1: Vérifier la syntaxe de tous les fichiers
        print("\n=== Phase 1: Vérification de la syntaxe ===")
        for file_path in python_files:
            rel_path = file_path.relative_to(self.base_path)
            print(f"Vérification syntaxe: {rel_path}")
            
            if not self.check_file_syntax(file_path):
                results['syntax_errors'] += 1
        
        # Phase 2: Analyser les imports dans chaque fichier
        print("\n=== Phase 2: Analyse des imports et détection de problèmes ===")
        file_imports = {}
        all_problematic_imports = []
        
        for file_path in python_files:
            rel_path = file_path.relative_to(self.base_path)
            print(f"Analyse des imports: {rel_path}")
            
            imports, from_imports, problematic_imports = self.extract_imports_from_file(file_path)
            
            if problematic_imports:
                results['problematic_imports'] += len(problematic_imports)
                results['problematic_files'].append({
                    'file': str(rel_path),
                    'problems': problematic_imports
                })
                all_problematic_imports.extend(problematic_imports)
                
                print(f"  ⚠️ {len(problematic_imports)} problème(s) détecté(s)")
            
            file_imports[str(rel_path)] = {
                'imports': list(imports),
                'from_imports': list(from_imports),
                'problematic_imports': problematic_imports
            }
        
        results['details']['file_imports'] = file_imports
        results['details']['all_problematic_imports'] = all_problematic_imports
        
        # Phase 3: Tester l'import de chaque module
        print("\n=== Phase 3: Test des imports de modules ===")
        for file_path in python_files:
            module_name = self.convert_path_to_module(file_path)
            rel_path = file_path.relative_to(self.base_path)
            
            print(f"Test import: {module_name} ({rel_path})")
            
            if self.try_import_module(module_name, file_path):
                results['successful_imports'] += 1
            else:
                results['import_errors'] += 1
        
        # Phase 4: Test spécifique des modules UI et services
        print("\n=== Phase 4: Test des modules UI et services ===")
        ui_modules = [
            'modules.erp_client.ui.main_window',
            'modules.erp_client.ui.panels.company_panel',
            'modules.erp_client.ui.panels.contract_panel',
            'modules.erp_client.ui.panels.pricing_panel',
            'modules.erp_client.ui.panels.forecast_panel',
            'modules.erp_client.ui.panels.report_panel',
            'modules.erp_client.ui.widgets.parameter_widget',
            'modules.erp_client.ui.widgets.forecast_config_widget'
        ]
        
        service_modules = [
            'modules.erp_client.services.database_service',
            'modules.erp_client.services.calculation_service',
            'modules.erp_client.services.export_service',
            'modules.erp_client.services.import_service'
        ]
        
        for module in ui_modules + service_modules:
            print(f"Test import spécifique: {module}")
            self.try_import_module(module)
        
        return results


if PYTEST_AVAILABLE:
    class TestImportsIntegrity:
        """Tests pytest pour l'intégrité des imports."""
        
        @pytest.fixture
        def checker(self):
            """Crée une instance du vérificateur d'imports."""
            base_path = Path(__file__).parent.parent
            return ImportChecker(base_path)
        
        def test_all_python_files_have_valid_syntax(self, checker):
            """Test que tous les fichiers Python ont une syntaxe valide."""
            python_files = checker.get_all_python_files()
            syntax_errors = []
            
            for file_path in python_files:
                if not checker.check_file_syntax(file_path):
                    syntax_errors.append(file_path)
            
            if syntax_errors:
                error_msg = "Fichiers avec erreurs de syntaxe:\n"
                for error in checker.errors:
                    if error['type'] == 'syntax_error':
                        error_msg += f"  - {error['file']}: {error['error']}\n"
                
                pytest.fail(error_msg)
        
        def test_all_modules_can_be_imported(self, checker):
            """Test que tous les modules peuvent être importés."""
            results = checker.check_all_imports()
            
            if results['import_errors'] > 0:
                error_msg = f"\nErreurs d'import détectées: {results['import_errors']} sur {results['total_files']} fichiers\n\n"
                
                # Grouper les erreurs par type
                errors_by_type = {}
                for error in results['errors']:
                    error_type = error.get('type', 'unknown')
                    if error_type not in errors_by_type:
                        errors_by_type[error_type] = []
                    errors_by_type[error_type].append(error)
                
                # Afficher les erreurs par type
                if 'module_not_found' in errors_by_type:
                    error_msg += "=== MODULES INTROUVABLES ===\n"
                    for error in errors_by_type['module_not_found']:
                        error_msg += f"  Fichier: {error['file']}\n"
                        error_msg += f"  Module manquant: {error.get('missing_module', 'inconnu')}\n"
                        error_msg += f"  Message: {error['error']}\n\n"
                
                if 'import_error' in errors_by_type:
                    error_msg += "\n=== ERREURS D'IMPORT ===\n"
                    for error in errors_by_type['import_error']:
                        error_msg += f"  Fichier: {error['file']}\n"
                        error_msg += f"  Module: {error.get('module', 'inconnu')}\n"
                        error_msg += f"  Erreur: {error['error']}\n"
                        if 'details' in error:
                            error_msg += f"  Détails:\n{error['details']}\n"
                
                pytest.fail(error_msg)
        
        def test_models_pricing_module_exists(self, checker):
            """Test spécifique pour vérifier que models.pricing existe ou est correctement importé."""
            # Vérifier si le module models/pricing.py existe
            pricing_module_path = checker.base_path / "models" / "pricing.py"
            
            if not pricing_module_path.exists():
                # Chercher les fichiers qui importent depuis models.pricing
                python_files = checker.get_all_python_files()
                files_importing_pricing = []
                
                for file_path in python_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if "from ..models.pricing import" in content or "import ..models.pricing" in content:
                            files_importing_pricing.append(file_path)
                    except:
                        pass
                
                if files_importing_pricing:
                    error_msg = "\n❌ ERREUR CRITIQUE: Module models.pricing introuvable\n\n"
                    error_msg += "📋 Fichiers qui tentent d'importer depuis models.pricing:\n"
                    
                    for file_path in files_importing_pricing:
                        rel_path = file_path.relative_to(checker.base_path)
                        error_msg += f"  - {rel_path}\n"
                        
                        # Montrer les lignes exactes
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                            
                            for i, line in enumerate(lines, 1):
                                if "models.pricing" in line:
                                    error_msg += f"    Ligne {i}: {line.strip()}\n"
                        except:
                            pass
                    
                    error_msg += "\n🔧 SOLUTIONS POSSIBLES:\n"
                    error_msg += "1. Créer le fichier manquant: modules/erp_client/models/pricing.py\n"
                    error_msg += "2. Définir les classes PrixClient et TypeTarif dans ce fichier\n"
                    error_msg += "3. Ou corriger les imports pour utiliser un module existant\n"
                    error_msg += "4. Ou déplacer ces classes vers un module existant (ex: models/client.py)\n\n"
                    
                    # Vérifier si ces classes existent ailleurs
                    error_msg += "🔍 RECHERCHE DES CLASSES DANS LE PROJET:\n"
                    for class_name in ['PrixClient', 'TypeTarif']:
                        found_in = []
                        for file_path in python_files:
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                if f"class {class_name}" in content:
                                    found_in.append(str(file_path.relative_to(checker.base_path)))
                            except:
                                pass
                        
                        if found_in:
                            error_msg += f"  ✅ {class_name} trouvée dans: {', '.join(found_in)}\n"
                        else:
                            error_msg += f"  ❌ {class_name} non trouvée dans le projet\n"
                    
                    pytest.fail(error_msg)


def generate_import_report():
    """Génère un rapport détaillé des imports."""
    base_path = Path(__file__).parent.parent
    checker = ImportChecker(base_path)
    
    print("=== RAPPORT D'INTÉGRITÉ DES IMPORTS ERP_CLIENT ===\n")
    
    results = checker.check_all_imports()
    
    print(f"\n=== RÉSUMÉ ===")
    print(f"Total de fichiers Python: {results['total_files']}")
    print(f"Erreurs de syntaxe: {results['syntax_errors']}")
    print(f"Erreurs d'import: {results['import_errors']}")
    print(f"Imports réussis: {results['successful_imports']}")
    
    if results['errors']:
        print("\n=== ERREURS DÉTAILLÉES ===")
        for i, error in enumerate(results['errors'], 1):
            print(f"\nErreur {i}:")
            print(f"  Type: {error.get('type', 'unknown')}")
            print(f"  Fichier: {error['file']}")
            print(f"  Message: {error['error']}")
            if 'missing_module' in error:
                print(f"  Module manquant: {error['missing_module']}")
    
    return results


def run_manual_tests():
    """Exécute les tests manuellement sans pytest."""
    print("=== TESTS D'INTÉGRITÉ DES IMPORTS ERP_CLIENT ===\n")
    
    base_path = Path(__file__).parent.parent
    checker = ImportChecker(base_path)
    
    # Test 1: Syntaxe des fichiers
    print("🔍 Test 1: Vérification de la syntaxe...")
    python_files = checker.get_all_python_files()
    syntax_errors = 0
    
    for file_path in python_files:
        if not checker.check_file_syntax(file_path):
            syntax_errors += 1
    
    if syntax_errors == 0:
        print("✅ Tous les fichiers ont une syntaxe valide")
    else:
        print(f"❌ {syntax_errors} fichier(s) avec erreurs de syntaxe")
    
    # Test 2: Imports problématiques
    print("\n🔍 Test 2: Détection des imports problématiques...")
    results = checker.check_all_imports()
    
    if results['problematic_imports'] == 0:
        print("✅ Aucun import problématique détecté")
    else:
        print(f"❌ {results['problematic_imports']} import(s) problématique(s) détecté(s)")
        for file_info in results['problematic_files']:
            print(f"\n📁 {file_info['file']}:")
            for problem in file_info['problems']:
                print(f"  ❌ Ligne {problem['line']}: {problem['issue']}")
                print(f"     💡 {problem['suggestion']}")
    
    # Test 3: Module models.pricing spécifique
    print("\n🔍 Test 3: Vérification du module models.pricing...")
    pricing_module_path = base_path / "models" / "pricing.py"
    
    if pricing_module_path.exists():
        print("✅ Module models.pricing trouvé")
    else:
        print("❌ Module models.pricing introuvable")
        
        # Chercher les imports de ce module
        files_importing_pricing = []
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if "models.pricing" in content:
                    files_importing_pricing.append(file_path)
            except:
                pass
        
        if files_importing_pricing:
            print(f"\n⚠️ {len(files_importing_pricing)} fichier(s) tentent d'importer depuis models.pricing:")
            for file_path in files_importing_pricing:
                rel_path = file_path.relative_to(base_path)
                print(f"  - {rel_path}")
            
            print("\n🔧 Solutions recommandées:")
            print("1. Créer modules/erp_client/models/pricing.py")
            print("2. Définir les classes PrixClient et TypeTarif")
            print("3. Ou corriger les imports vers un module existant")
    
    # Test 4: Recherche des classes dans le projet
    print("\n🔍 Test 4: Recherche des classes PrixClient et TypeTarif...")
    for class_name in ['PrixClient', 'TypeTarif']:
        found_in = []
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if f"class {class_name}" in content:
                    found_in.append(str(file_path.relative_to(base_path)))
            except:
                pass
        
        if found_in:
            print(f"✅ {class_name} trouvée dans: {', '.join(found_in)}")
        else:
            print(f"❌ {class_name} non trouvée dans le projet")
    
    # Résumé final
    print(f"\n=== RÉSUMÉ ===")
    print(f"Fichiers analysés: {len(python_files)}")
    print(f"Erreurs de syntaxe: {syntax_errors}")
    print(f"Imports problématiques: {results['problematic_imports']}")
    print(f"Erreurs d'import: {results['import_errors']}")
    
    total_errors = syntax_errors + results['problematic_imports'] + results['import_errors']
    if total_errors == 0:
        print("\n🎉 SUCCÈS: Tous les tests sont passés !")
        return True
    else:
        print(f"\n❌ ÉCHEC: {total_errors} problème(s) détecté(s)")
        return False


if __name__ == "__main__":
    if PYTEST_AVAILABLE:
        print("pytest détecté. Utilisation des tests pytest...")
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "pytest", __file__, "-v"
        ], cwd=Path(__file__).parent.parent.parent)
        sys.exit(result.returncode)
    else:
        print("pytest non disponible. Exécution des tests manuels...")
        success = run_manual_tests()
        sys.exit(0 if success else 1)