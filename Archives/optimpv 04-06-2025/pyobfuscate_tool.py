#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Outil d'obfuscation Python avancé pour OptimPV
Combine plusieurs techniques gratuites
"""

import os
import sys
import re
import ast
import base64
import random
import string
import hashlib
import marshal
import zlib
import struct
import time
from typing import Dict, List, Set, Tuple

class PyObfuscate:
    """Obfuscateur Python multi-techniques"""
    
    def __init__(self, aggressive=True):
        self.aggressive = aggressive
        self.mappings = {
            'vars': {},
            'funcs': {},
            'classes': {},
            'imports': {}
        }
        self.strings_table = []
        self.protected = {
            # Streamlit
            'st', 'session_state', 'sidebar', 'columns', 'button', 'selectbox',
            'markdown', 'write', 'error', 'success', 'warning', 'info', 'spinner',
            'expander', 'container', 'empty', 'placeholder', 'chat_message',
            # Python essentiels - MODULES SYSTÈME
            'sys', 'os', 'time', 'datetime', 'json', 'base64', 'random', 'string',
            'hashlib', 'marshal', 'zlib', 'struct', 'math', 'collections', 'itertools',
            're', 'ast', 'typing', 'pathlib', 'platform', 'subprocess', 'threading',
            'multiprocessing', 'socket', 'urllib', 'http', 'email', 'xml', 'csv',
            'sqlite3', 'logging', 'warnings', 'traceback', 'gc', 'weakref',
            # Python builtins
            '__init__', '__main__', '__name__', '__file__', '__doc__', '__all__',
            'self', 'cls', 'args', 'kwargs', 'super', '__class__', '__dict__',
            # Builtins critiques
            'print', 'open', 'len', 'range', 'enumerate', 'zip', 'map', 'filter',
            'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple',
            'type', 'isinstance', 'hasattr', 'getattr', 'setattr',
            # Modules tiers communs
            'pandas', 'numpy', 'scipy', 'matplotlib', 'plotly', 'seaborn',
            'requests', 'urllib3', 'cryptography', 'streamlit', 'altair',
            # Nos classes/fonctions protégées
            'LicenceGuard', 'initialize_protection', 'check_and_protect',
            'validate_token', 'decrypt_token', 'self_destruct', 'corrupt_executable'
        }
        
    def generate_obf_name(self, prefix='_'):
        """Génère un nom obfusqué unique"""
        # Utilise des caractères qui se ressemblent visuellement
        confusing_chars = 'O0oIl1i'
        length = random.randint(10, 20) if self.aggressive else random.randint(6, 12)
        
        # Commence par un underscore ou lettre
        name = prefix
        
        # Ajoute des caractères confus
        for _ in range(length):
            if random.random() < 0.7:
                name += random.choice(confusing_chars)
            else:
                name += random.choice(string.ascii_letters)
        
        # S'assure que le nom est unique
        while name in self.mappings['vars'].values() or \
              name in self.mappings['funcs'].values() or \
              name in self.mappings['classes'].values():
            name += random.choice(string.ascii_letters)
        
        return name
    
    def encode_string_advanced(self, s: str) -> str:
        """Encode une string avec plusieurs couches"""
        if not s or len(s) < 3:
            return f'"{s}"'
        
        # Stocker dans la table des strings
        idx = len(self.strings_table)
        self.strings_table.append(s)
        
        if self.aggressive:
            # Méthode 1: Double encodage Base64 + XOR
            key = random.randint(1, 255)
            # Encoder en base64
            b64 = base64.b64encode(s.encode()).decode()
            # XOR chaque caractère
            xored = ''.join(chr(ord(c) ^ key) for c in b64)
            # Hex final
            hexed = xored.encode('latin-1').hex()
            
            # Décodeur runtime
            decoder = (
                f"__import__('base64').b64decode("
                f"''.join(chr(ord(c)^{key}) for c in "
                f"bytes.fromhex('{hexed}').decode('latin-1'))"
                f").decode()"
            )
            return decoder
        else:
            # Méthode simple: Base64
            b64 = base64.b64encode(s.encode()).decode()
            return f"__import__('base64').b64decode('{b64}').decode()"
    
    def obfuscate_number(self, num: int) -> str:
        """Obfusque un nombre avec des expressions"""
        if not self.aggressive:
            return str(num)
        
        if num == 0:
            return "(len([]))"
        elif num == 1:
            return "(int(True))"
        elif num == 2:
            return "(int(True)+int(True))"
        elif num < 10:
            # Utilise len() d'une string
            return f"(len('{random.choice(string.ascii_letters) * num}'))"
        else:
            # Expression mathématique complexe
            parts = []
            remaining = num
            
            while remaining > 0:
                if remaining >= 100:
                    part = random.randint(50, 100)
                elif remaining >= 10:
                    part = random.randint(5, remaining // 2)
                else:
                    part = remaining
                
                parts.append(part)
                remaining -= part
            
            expression = "+".join(str(p) for p in parts)
            return f"({expression})"
    
    def add_anti_analysis(self, code: str) -> str:
        """Ajoute du code anti-analyse"""
        anti_analysis = '''
# Protection runtime
import sys as _sys
_sys.dont_write_bytecode = True

# Anti-debug basique
if _sys.gettrace() is not None:
    _sys.exit(1)

# Vérification environnement
_suspicious = ['PYDEVD', 'PYTHONDEBUG', 'PYTHONINSPECT', '_PYDEV_COMPLETER_PYTHONPATH']
if any(_v in __import__('os').environ for _v in _suspicious):
    __import__('os')._exit(1)

# Hook protection
_sys.settrace(None)
__builtins__.__dict__['__import__'] = __import__

'''
        return anti_analysis + code
    
    def inject_junk_code(self, code: str) -> str:
        """Injecte du code poubelle valide mais inutile"""
        if not self.aggressive:
            return code
        
        junk_templates = [
            # Lambdas inutiles
            "_{var} = lambda: None",
            "_{var} = lambda x: x",
            
            # Compréhensions vides
            "[None for _ in range(0)]",
            "{i:i for i in range(0)}",
            
            # Conditions toujours fausses
            "if False: pass",
            "if not True: _{var} = None",
            
            # Opérations no-op
            "_{var} = {{}} or {{}}",
            "_{var} = [] + []",
            "_{var} = '' + ''",
            
            # Try/except vides
            "try: pass\nexcept: pass",
        ]
        
        lines = code.split('\n')
        result = []
        
        for line in lines:
            result.append(line)
            
            # Injecter du junk avec probabilité
            if random.random() < 0.15 and line.strip() and not line.strip().startswith('#'):
                indent = len(line) - len(line.lstrip())
                junk = random.choice(junk_templates)
                
                # Remplacer {var} par un nom aléatoire
                var_name = self.generate_obf_name('_jnk')
                junk = junk.replace('{var}', var_name)
                
                # Ajouter l'indentation
                for junk_line in junk.split('\n'):
                    result.append(' ' * indent + junk_line)
        
        return '\n'.join(result)
    
    def control_flow_obfuscation(self, code: str) -> str:
        """Obfusque le flux de contrôle"""
        if not self.aggressive:
            return code
        
        # Remplacer if simple par des expressions ternaires complexes
        code = re.sub(
            r'if\s+(.+?):\s*(\w+)\s*=\s*(.+?)\s*else:\s*\2\s*=\s*(.+)',
            lambda m: f"{m.group(2)} = ({m.group(3)}) if ({m.group(1)}) else ({m.group(4)})",
            code
        )
        
        return code
    
    def marshal_compile(self, code: str) -> str:
        """Compile et marshal le code pour protection supplémentaire"""
        try:
            # Compiler en bytecode
            compiled = compile(code, '<obfuscated>', 'exec', optimize=2)
            
            # Marshal + compress
            marshalled = marshal.dumps(compiled)
            compressed = zlib.compress(marshalled, 9)
            
            # Encoder en base64
            encoded = base64.b64encode(compressed).decode()
            
            # Créer le loader
            loader = f'''
import marshal, zlib, base64
exec(marshal.loads(zlib.decompress(base64.b64decode("{encoded}"))))
'''
            return loader
        except:
            # Si erreur, retourner le code original
            return code
    
    def obfuscate_file(self, filepath: str, output_path: str = None):
        """Obfusque un fichier Python complet"""
        print(f"[*] Obfuscation de: {os.path.basename(filepath)}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            original_code = f.read()
        
        # Parse AST pour analyse
        try:
            tree = ast.parse(original_code)
            self.analyze_ast(tree)
        except SyntaxError as e:
            print(f"    [!] Erreur syntaxe: {e}")
            print("    [*] Utilisation obfuscation basique")
            obfuscated = self.basic_obfuscate(original_code)
        else:
            # Obfuscation complète
            obfuscated = self.full_obfuscate(original_code, tree)
        
        # Sauvegarder
        if output_path is None:
            output_path = filepath.replace('.py', '_obf.py')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(obfuscated)
        
        # Stats
        original_size = len(original_code)
        obfuscated_size = len(obfuscated)
        ratio = (obfuscated_size / original_size) * 100
        
        print(f"    [✓] Taille: {original_size} → {obfuscated_size} bytes ({ratio:.1f}%)")
        print(f"    [✓] Sauvé: {output_path}")
        
        return output_path
    
    def analyze_ast(self, tree):
        """Analyse l'AST pour identifier les éléments à obfusquer"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if node.id not in self.protected and not node.id.startswith('__'):
                    if node.id not in self.mappings['vars']:
                        self.mappings['vars'][node.id] = self.generate_obf_name('_v')
            
            elif isinstance(node, ast.FunctionDef):
                if node.name not in self.protected and not node.name.startswith('__'):
                    if node.name not in self.mappings['funcs']:
                        self.mappings['funcs'][node.name] = self.generate_obf_name('_f')
            
            elif isinstance(node, ast.ClassDef):
                if node.name not in self.protected:
                    if node.name not in self.mappings['classes']:
                        self.mappings['classes'][node.name] = self.generate_obf_name('_c')
    
    def full_obfuscate(self, code: str, tree) -> str:
        """Obfuscation complète avec toutes les techniques"""
        
        # 1. Anti-analyse
        code = self.add_anti_analysis(code)
        
        # 2. Remplacer les noms (variables, fonctions, classes)
        for category, mapping in self.mappings.items():
            for original, obfuscated in mapping.items():
                # Regex pour remplacer uniquement les mots complets
                pattern = r'\b' + re.escape(original) + r'\b'
                code = re.sub(pattern, obfuscated, code)
        
        # 3. Encoder les strings
        def encode_string_match(match):
            quote = match.group(1)
            content = match.group(2)
            
            # Ne pas encoder les docstrings et strings spéciales
            if content.startswith('__') or len(content) < 3:
                return match.group(0)
            
            return self.encode_string_advanced(content)
        
        # Patterns pour strings
        code = re.sub(r"('|\")(.*?)\1", encode_string_match, code)
        
        # 4. Obfusquer les nombres
        code = re.sub(r'\b(\d+)\b', lambda m: self.obfuscate_number(int(m.group(1))), code)
        
        # 5. Injection de code poubelle
        code = self.inject_junk_code(code)
        
        # 6. Obfuscation du flux de contrôle
        code = self.control_flow_obfuscation(code)
        
        # 7. Compilation marshal (si activé et pas trop gros)
        if self.aggressive and len(code) < 100000:  # Max 100KB pour marshal
            code = self.marshal_compile(code)
        
        return code
    
    def basic_obfuscate(self, code: str) -> str:
        """Obfuscation basique pour code avec erreurs de syntaxe"""
        # Supprimer commentaires
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        
        # Supprimer lignes vides
        code = '\n'.join(line for line in code.split('\n') if line.strip())
        
        # Compression zlib + base64
        compressed = zlib.compress(code.encode(), 9)
        encoded = base64.b64encode(compressed).decode()
        
        return f"exec(__import__('zlib').decompress(__import__('base64').b64decode('{encoded}')))"


def main():
    """CLI pour l'obfuscateur"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Obfuscateur Python OptimPV')
    parser.add_argument('input', help='Fichier ou dossier à obfusquer')
    parser.add_argument('-o', '--output', help='Fichier/dossier de sortie')
    parser.add_argument('-r', '--recursive', action='store_true', help='Obfusquer récursivement')
    parser.add_argument('-a', '--aggressive', action='store_true', help='Obfuscation agressive')
    parser.add_argument('-k', '--keep-original', action='store_true', help='Garder les originaux')
    
    args = parser.parse_args()
    
    obfuscator = PyObfuscate(aggressive=args.aggressive)
    
    if os.path.isfile(args.input):
        # Obfusquer un seul fichier
        output = args.output or args.input.replace('.py', '_obf.py')
        obfuscator.obfuscate_file(args.input, output)
    
    elif os.path.isdir(args.input):
        # Obfusquer un dossier
        output_dir = args.output or args.input + '_obf'
        os.makedirs(output_dir, exist_ok=True)
        
        pattern = '**/*.py' if args.recursive else '*.py'
        
        import glob
        for py_file in glob.glob(os.path.join(args.input, pattern), recursive=args.recursive):
            rel_path = os.path.relpath(py_file, args.input)
            output_path = os.path.join(output_dir, rel_path)
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            obfuscator.obfuscate_file(py_file, output_path)
    
    print("\n[✓] Obfuscation terminée!")


if __name__ == "__main__":
    main()
