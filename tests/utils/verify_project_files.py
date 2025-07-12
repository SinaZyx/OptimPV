#!/usr/bin/env python3
"""
Utilitaire pour vérifier l'état réel des fichiers de projets
"""

import os
import json
from pathlib import Path

def verify_projects_directory():
    """Vérifie les projets dans le dossier projects/"""
    projects_dir = Path('/mnt/c/Users/kingc/OptimPV/projects')
    
    if not projects_dir.exists():
        print("❌ Le dossier projects/ n'existe pas")
        return
    
    project_dirs = [d for d in projects_dir.iterdir() if d.is_dir()]
    
    if not project_dirs:
        print("📭 Aucun projet trouvé dans projects/")
        return
    
    print(f"🔍 Analyse de {len(project_dirs)} projet(s)")
    print("=" * 60)
    
    for project_dir in project_dirs:
        print(f"\n📁 Projet: {project_dir.name}")
        print("-" * 40)
        
        # Vérifier les fichiers
        files_to_check = {
            'manifest.json': 'Manifest du projet',
            'session_state_complete.json': 'État complet de session',
            'config.json': 'Configuration',
            'scenarios.json': 'Scénarios',
            'economic_results.json': 'Résultats économiques',
            'optimization_results.json': 'Résultats optimisation',
            'monte_carlo_results.json': 'Résultats Monte Carlo'
        }
        
        for filename, description in files_to_check.items():
            file_path = project_dir / filename
            exists = file_path.exists()
            
            if exists:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    if filename == 'manifest.json':
                        # Analyser le manifest
                        print(f"✅ {description}")
                        print(f"   Nom: {data.get('name', 'N/A')}")
                        print(f"   Version: {data.get('storage_version', 'N/A')}")
                        
                        # Vérifier les flags has_*
                        flags = {
                            'has_economic_results': data.get('has_economic_results', False),
                            'has_optimization_results': data.get('has_optimization_results', False),
                            'has_monte_carlo_results': data.get('has_monte_carlo_results', False)
                        }
                        
                        for flag, value in flags.items():
                            emoji = "✅" if value else "❌"
                            print(f"   {emoji} {flag}: {value}")
                        
                        # Vérifier completeness
                        completeness = data.get('completeness', {}).get('components', {})
                        if completeness:
                            print(f"   Complétude:")
                            for comp, status in completeness.items():
                                emoji = "✅" if status else "❌"
                                print(f"     {emoji} {comp}: {status}")
                    
                    else:
                        # Analyser le contenu des autres fichiers
                        is_empty = not bool(data)
                        size_info = f"({len(data)} entrées)" if isinstance(data, dict) else f"({type(data).__name__})"
                        
                        if is_empty:
                            print(f"⚠️  {description} - VIDE {size_info}")
                        else:
                            print(f"✅ {description} - OK {size_info}")
                            
                            # Afficher les clés pour les dictionnaires
                            if isinstance(data, dict) and data:
                                keys = list(data.keys())[:3]  # Premières 3 clés
                                if len(data) > 3:
                                    keys_str = f"{', '.join(keys)}..."
                                else:
                                    keys_str = ', '.join(keys)
                                print(f"   Clés: {keys_str}")
                
                except json.JSONDecodeError:
                    print(f"❌ {description} - FICHIER CORROMPU")
                except Exception as e:
                    print(f"❌ {description} - ERREUR: {e}")
            else:
                print(f"❌ {description} - MANQUANT")
        
        print()

def check_manifest_vs_files_consistency():
    """Vérifie la cohérence entre manifest et fichiers réels"""
    projects_dir = Path('/mnt/c/Users/kingc/OptimPV/projects')
    
    if not projects_dir.exists():
        return
    
    print("\n🔍 VÉRIFICATION DE COHÉRENCE MANIFEST ↔ FICHIERS")
    print("=" * 55)
    
    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue
            
        manifest_path = project_dir / 'manifest.json'
        if not manifest_path.exists():
            continue
            
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        except:
            continue
            
        print(f"\n📁 {project_dir.name}")
        
        # Vérifications cohérence
        checks = [
            ('economic_results.json', 'has_economic_results'),
            ('optimization_results.json', 'has_optimization_results'),
            ('monte_carlo_results.json', 'has_monte_carlo_results')
        ]
        
        for filename, manifest_flag in checks:
            file_path = project_dir / filename
            manifest_says = manifest.get(manifest_flag, False)
            
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    file_has_data = bool(data)
                except:
                    file_has_data = False
            else:
                file_has_data = False
            
            # Vérifier cohérence
            if manifest_says == file_has_data:
                emoji = "✅"
                status = "COHÉRENT"
            else:
                emoji = "❌"
                status = "INCOHÉRENT"
            
            print(f"   {emoji} {filename}: Manifest={manifest_says}, Fichier={file_has_data} - {status}")

def main():
    print("🔍 VÉRIFICATION DES PROJETS SAUVEGARDÉS")
    print("=" * 40)
    
    verify_projects_directory()
    check_manifest_vs_files_consistency()
    
    print("\n🎯 RÉSUMÉ")
    print("=" * 10)
    print("Cette analyse permet d'identifier les incohérences entre :")
    print("1. Les flags dans manifest.json")
    print("2. Le contenu réel des fichiers de données")
    print("3. Les composants de complétude")

if __name__ == "__main__":
    main()