"""
Script simple de vérification d'intégrité des imports pour le module erp_client.
N'utilise pas pytest, peut être exécuté directement.
"""

import os
import sys
import ast
import importlib
import traceback
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional


class SimpleImportChecker:
    """Vérificateur d'imports simple pour le module erp_client."""
    
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
    
    def extract_imports_from_file(self, file_path: Path) -> Tuple[Set[str], Set[str]]:
        """
        Extrait tous les imports d'un fichier Python.
        
        Returns:
            - imports: ensemble des modules importés directement
            - from_imports: ensemble des imports "from X import Y"
        """
        imports = set()
        from_imports = set()
        
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
                        for alias in node.names:
                            if alias.name != '*':
                                from_imports.add(f"{node.module}.{alias.name}")
            
        except Exception as e:
            self.errors.append({
                'file': str(file_path),
                'error': f"Erreur lors de l'analyse AST: {str(e)}",
                'type': 'ast_error'
            })
        
        return imports, from_imports
    
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
            # Ajouter le chemin racine du projet au sys.path
            project_root = self.base_path.parent.parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
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
                'details': str(e)
            })
            return False
            
        except Exception as e:
            self.errors.append({
                'file': str(file_path) if file_path else module_name,
                'error': f"Erreur inattendue: {str(e)}",
                'type': 'unexpected_error',
                'module': module_name,
                'details': str(e)
            })
            return False
    
    def convert_path_to_module(self, file_path: Path) -> str:
        """Convertit un chemin de fichier en nom de module."""
        # Obtenir le chemin relatif depuis le dossier racine du projet
        project_root = self.base_path.parent.parent.parent
        rel_path = file_path.relative_to(project_root)
        
        # Convertir en nom de module
        parts = list(rel_path.parts[:-1])  # Enlever le nom du fichier
        if rel_path.stem != '__init__':
            parts.append(rel_path.stem)
        
        return '.'.join(parts)
    
    def run_all_checks(self) -> Dict[str, any]:
        """Exécute tous les checks d'intégrité."""
        print("=== VÉRIFICATION D'INTÉGRITÉ DES IMPORTS ERP_CLIENT ===\n")
        
        results = {
            'total_files': 0,
            'syntax_errors': 0,
            'import_errors': 0,
            'successful_imports': 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'details': {}
        }
        
        python_files = self.get_all_python_files()
        results['total_files'] = len(python_files)
        
        print(f"Fichiers Python trouvés: {len(python_files)}")
        
        # Phase 1: Vérifier la syntaxe de tous les fichiers
        print("\n=== Phase 1: Vérification de la syntaxe ===")
        syntax_ok = 0
        for file_path in python_files:
            rel_path = file_path.relative_to(self.base_path.parent.parent.parent)
            print(f"  Syntaxe: {rel_path} ... ", end="")
            
            if self.check_file_syntax(file_path):
                print("OK")
                syntax_ok += 1
            else:
                print("ERREUR")
                results['syntax_errors'] += 1
        
        print(f"\nRésultat syntaxe: {syntax_ok}/{len(python_files)} fichiers OK")
        
        # Phase 2: Analyser les imports dans chaque fichier
        print("\n=== Phase 2: Analyse des imports ===")
        all_imports = set()
        all_from_imports = set()
        
        for file_path in python_files:
            rel_path = file_path.relative_to(self.base_path.parent.parent.parent)
            imports, from_imports = self.extract_imports_from_file(file_path)
            all_imports.update(imports)
            all_from_imports.update(from_imports)
            print(f"  Imports analysés: {rel_path} ({len(imports)} direct, {len(from_imports)} from)")
        
        print(f"\nTotal imports uniques trouvés: {len(all_imports)} direct, {len(all_from_imports)} from")
        
        # Phase 3: Tester l'import de chaque module
        print("\n=== Phase 3: Test des imports de modules ===")
        for file_path in python_files:
            module_name = self.convert_path_to_module(file_path)
            rel_path = file_path.relative_to(self.base_path.parent.parent.parent)
            
            print(f"  Import test: {module_name} ... ", end="")
            
            if self.try_import_module(module_name, file_path):
                print("OK")
                results['successful_imports'] += 1
            else:
                print("ÉCHEC")
                results['import_errors'] += 1
        
        # Phase 4: Test spécifique des modules critiques
        print("\n=== Phase 4: Test des modules critiques ===")
        critical_modules = [
            'modules.erp_client.database.erp_database',
            'modules.erp_client.models',
            'modules.erp_client.services',
            'modules.erp_client.ui'
        ]
        
        for module in critical_modules:
            print(f"  Module critique: {module} ... ", end="")
            if self.try_import_module(module):
                print("OK")
            else:
                print("ÉCHEC")
        
        return results
    
    def print_detailed_report(self, results: Dict[str, any]):
        """Affiche un rapport détaillé des erreurs."""
        print(f"\n=== RÉSUMÉ FINAL ===")
        print(f"Total de fichiers Python: {results['total_files']}")
        print(f"Erreurs de syntaxe: {results['syntax_errors']}")
        print(f"Erreurs d'import: {results['import_errors']}")
        print(f"Imports réussis: {results['successful_imports']}")
        
        if self.errors:
            print(f"\n=== ERREURS DÉTAILLÉES ({len(self.errors)}) ===")
            
            # Grouper les erreurs par type
            errors_by_type = {}
            for error in self.errors:
                error_type = error.get('type', 'unknown')
                if error_type not in errors_by_type:
                    errors_by_type[error_type] = []
                errors_by_type[error_type].append(error)
            
            # Afficher les erreurs par type
            if 'syntax_error' in errors_by_type:
                print(f"\n--- ERREURS DE SYNTAXE ({len(errors_by_type['syntax_error'])}) ---")
                for error in errors_by_type['syntax_error']:
                    print(f"  Fichier: {error['file']}")
                    print(f"  Erreur: {error['error']}\n")
            
            if 'module_not_found' in errors_by_type:
                print(f"\n--- MODULES INTROUVABLES ({len(errors_by_type['module_not_found'])}) ---")
                for error in errors_by_type['module_not_found']:
                    print(f"  Fichier: {error['file']}")
                    print(f"  Module: {error.get('module', 'inconnu')}")
                    print(f"  Module manquant: {error.get('missing_module', 'inconnu')}")
                    print(f"  Message: {error['error']}\n")
            
            if 'import_error' in errors_by_type:
                print(f"\n--- ERREURS D'IMPORT ({len(errors_by_type['import_error'])}) ---")
                for error in errors_by_type['import_error']:
                    print(f"  Fichier: {error['file']}")
                    print(f"  Module: {error.get('module', 'inconnu')}")
                    print(f"  Erreur: {error['error']}")
                    if 'details' in error and error['details']:
                        print(f"  Détails: {error['details']}")
                    print()
            
            if 'unexpected_error' in errors_by_type:
                print(f"\n--- ERREURS INATTENDUES ({len(errors_by_type['unexpected_error'])}) ---")
                for error in errors_by_type['unexpected_error']:
                    print(f"  Fichier: {error['file']}")
                    print(f"  Module: {error.get('module', 'inconnu')}")
                    print(f"  Erreur: {error['error']}")
                    print(f"  Détails: {error.get('details', 'N/A')}\n")
        
        if self.successful_imports:
            print(f"\n=== IMPORTS RÉUSSIS ({len(self.successful_imports)}) ===")
            for module in sorted(self.successful_imports):
                print(f"  ✓ {module}")
        
        print(f"\n=== RECOMMANDATIONS ===")
        if results['syntax_errors'] > 0:
            print("1. Corriger d'abord toutes les erreurs de syntaxe")
        if results['import_errors'] > 0:
            print("2. Vérifier les dépendances manquantes et les imports incorrects")
        if results['import_errors'] == 0 and results['syntax_errors'] == 0:
            print("✓ Tous les tests d'intégrité ont réussi !")


def main():
    """Fonction principale."""
    # Déterminer le chemin du module erp_client
    script_path = Path(__file__)
    erp_client_path = script_path.parent.parent
    
    print(f"Vérification du module: {erp_client_path}")
    
    # Créer le checker et exécuter les tests
    checker = SimpleImportChecker(erp_client_path)
    results = checker.run_all_checks()
    checker.print_detailed_report(results)
    
    # Code de sortie basé sur les résultats
    if results['syntax_errors'] > 0 or results['import_errors'] > 0:
        print(f"\nÉCHEC: {results['syntax_errors']} erreurs de syntaxe, {results['import_errors']} erreurs d'import")
        return 1
    else:
        print(f"\nSUCCÈS: Tous les tests d'intégrité ont réussi !")
        return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)