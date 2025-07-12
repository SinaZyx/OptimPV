#!/usr/bin/env python3
"""
Tests de debug pour le système de storage
Diagnostic des problèmes de sauvegarde/chargement
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime

# Ajouter le dossier parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_session_state_content():
    """Simule et affiche le contenu du session_state"""
    print("=== DEBUG SESSION STATE ===")
    
    # Simuler des données typiques
    mock_session_state = {
        'data_imported': True,
        'config': {'puissance_kwc': 100, 'capex': 150000},
        'scenarios': {'base': {'name': 'Base'}, 'optimiste': {'name': 'Optimiste'}},
        'production_data': pd.DataFrame({'Temps': pd.date_range('2024-01-01', periods=100, freq='H'), 'Production': range(100)}),
        'economic_results': {
            'base': {'roi': 0.15, 'van': 45000, 'tri': 0.12},
            'optimiste': {'roi': 0.18, 'van': 55000, 'tri': 0.15}
        },
        'optimization_results': {
            'base': {
                'scenario_name': 'base',
                'prix_optimal': 0.15,
                'indicateurs_optimaux': {'roi': 0.15, 'van': 45000, 'tri': 0.12}
            }
        },
        # Pas de monte_carlo_results volontairement
        'nav_Rapports': 'some_nav_value',  # Navigation qui ne doit pas être sauvegardée
        'ui_state': 'some_ui_value'  # UI qui ne doit pas être sauvegardée
    }
    
    print("Contenu simulé du session_state:")
    for key, value in mock_session_state.items():
        print(f"  {key}: {type(value).__name__}")
        if isinstance(value, dict):
            print(f"    -> {list(value.keys())}")
    
    return mock_session_state

def debug_completeness_calculation(session_state):
    """Debug le calcul du score de complétude"""
    print("\n=== DEBUG COMPLETENESS CALCULATION ===")
    
    components = {
        'data_imported': 'production_data' in session_state,
        'config_set': 'config' in session_state,
        'scenarios_defined': 'scenarios' in session_state,
        'economic_analysis': 'economic_results' in session_state,
        'optimization_done': 'optimization_results' in session_state,
        'monte_carlo_done': 'monte_carlo_results' in session_state
    }
    
    print("Détection des composants:")
    for comp, status in components.items():
        emoji = "✅" if status else "❌"
        print(f"  {emoji} {comp}: {status}")
    
    completed = sum(components.values())
    total = len(components)
    score = (completed / total) * 100
    
    print(f"\nScore calculé: {completed}/{total} = {score:.1f}%")
    return components, score

def debug_exclusion_filtering(session_state):
    """Debug le filtrage des clés exclues"""
    print("\n=== DEBUG EXCLUSION FILTERING ===")
    
    excluded_keys = {
        '_streamlit_internal', 'auth_status', 'password_verified',
        'project_history', 'temp_data', 'ui_state', 'storage_ui_state'
    }
    
    excluded_prefixes = {'nav_', 'ui_', '_st'}
    
    print("Clés qui seraient sauvegardées:")
    saved_keys = []
    excluded_keys_found = []
    
    for key in session_state.keys():
        should_exclude = (
            key.startswith('_') or
            key in excluded_keys or
            any(key.startswith(prefix) for prefix in excluded_prefixes)
        )
        
        if should_exclude:
            excluded_keys_found.append(key)
        else:
            saved_keys.append(key)
    
    print("  Clés SAUVEGARDÉES:")
    for key in saved_keys:
        print(f"    ✅ {key}")
    
    print("  Clés EXCLUES:")
    for key in excluded_keys_found:
        print(f"    ❌ {key}")
    
    return saved_keys, excluded_keys_found

def debug_manifest_creation(session_state, components, score):
    """Debug la création du manifest"""
    print("\n=== DEBUG MANIFEST CREATION ===")
    
    manifest = {
        'name': 'Test Project',
        'description': 'Projet de test',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'storage_version': '2.0',
        'completeness': {
            'score': score,
            'components': components
        },
        'has_config': 'config' in session_state,
        'has_scenarios': 'scenarios' in session_state,
        'has_production_data': 'production_data' in session_state,
        'has_economic_results': 'economic_results' in session_state and bool(session_state.get('economic_results')),
        'has_optimization_results': 'optimization_results' in session_state and bool(session_state.get('optimization_results')),
        'has_monte_carlo_results': 'monte_carlo_results' in session_state and bool(session_state.get('monte_carlo_results'))
    }
    
    print("Manifest généré:")
    for key, value in manifest.items():
        if key in ['created_at', 'updated_at']:
            continue  # Skip dates pour la lisibilité
        print(f"  {key}: {value}")
    
    return manifest

def debug_comparison_data_loading():
    """Debug le chargement des données pour la comparaison"""
    print("\n=== DEBUG COMPARISON DATA LOADING ===")
    
    # Simuler les données chargées depuis les fichiers
    project1_data = {
        'manifest': {
            'name': 'Projet 1',
            'has_economic_results': True,
            'has_optimization_results': True,
            'has_monte_carlo_results': False,
            'completeness': {
                'components': {
                    'economic_analysis': True,
                    'optimization_done': True,
                    'monte_carlo_done': False
                }
            }
        },
        'economic_results': {'base': {'roi': 0.15}},
        'optimization_results': {'base': {'prix_optimal': 0.15}},
        'monte_carlo_results': {}
    }
    
    project2_data = {
        'manifest': {
            'name': 'Projet 2', 
            'has_economic_results': True,
            'has_optimization_results': False,
            'has_monte_carlo_results': False,
            'completeness': {
                'components': {
                    'economic_analysis': True,
                    'optimization_done': False,
                    'monte_carlo_done': False
                }
            }
        },
        'economic_results': {'base': {'roi': 0.12}},
        'optimization_results': {},
        'monte_carlo_results': {}
    }
    
    print("Projet 1 - Données chargées:")
    print(f"  has_economic_results: {project1_data['manifest']['has_economic_results']}")
    print(f"  economic_results vide: {not bool(project1_data['economic_results'])}")
    print(f"  has_optimization_results: {project1_data['manifest']['has_optimization_results']}")
    print(f"  optimization_results vide: {not bool(project1_data['optimization_results'])}")
    
    print("\nProjet 2 - Données chargées:")
    print(f"  has_economic_results: {project2_data['manifest']['has_economic_results']}")
    print(f"  economic_results vide: {not bool(project2_data['economic_results'])}")
    print(f"  has_optimization_results: {project2_data['manifest']['has_optimization_results']}")
    print(f"  optimization_results vide: {not bool(project2_data['optimization_results'])}")
    
    # Test de la logique de comparaison
    print("\nLogique de comparaison:")
    print("======================")
    
    # Test économie
    economic1 = project1_data['economic_results']
    economic2 = project2_data['economic_results'] 
    print(f"Économie - Peut comparer: {bool(economic1 and economic2)}")
    
    # Test optimisation
    opt1 = project1_data['optimization_results']
    opt2 = project2_data['optimization_results']
    print(f"Optimisation - Peut comparer: {bool(opt1 and opt2)}")
    
    # Test Monte Carlo
    mc1 = project1_data['monte_carlo_results']
    mc2 = project2_data['monte_carlo_results']
    print(f"Monte Carlo - Peut comparer: {bool(mc1 and mc2)}")
    
    return project1_data, project2_data

def debug_file_structure():
    """Debug la structure des fichiers de projet"""
    print("\n=== DEBUG FILE STRUCTURE ===")
    
    projects_dir = '/mnt/c/Users/kingc/OptimPV/projects'
    
    if not os.path.exists(projects_dir):
        print(f"❌ Dossier projects n'existe pas: {projects_dir}")
        return
    
    project_dirs = [d for d in os.listdir(projects_dir) if os.path.isdir(os.path.join(projects_dir, d))]
    
    print(f"Projets trouvés: {len(project_dirs)}")
    
    for project_id in project_dirs[:3]:  # Limiter aux 3 premiers
        project_path = os.path.join(projects_dir, project_id)
        print(f"\n📁 Projet: {project_id}")
        
        # Vérifier les fichiers
        files = os.listdir(project_path)
        expected_files = [
            'manifest.json',
            'session_state_complete.json', 
            'config.json',
            'scenarios.json',
            'economic_results.json',
            'optimization_results.json',
            'monte_carlo_results.json'
        ]
        
        for expected_file in expected_files:
            exists = expected_file in files
            emoji = "✅" if exists else "❌"
            print(f"  {emoji} {expected_file}")
            
            if exists and expected_file == 'manifest.json':
                # Lire le manifest pour debug
                try:
                    with open(os.path.join(project_path, expected_file), 'r') as f:
                        manifest = json.load(f)
                    print(f"    -> has_economic_results: {manifest.get('has_economic_results', 'N/A')}")
                    print(f"    -> has_optimization_results: {manifest.get('has_optimization_results', 'N/A')}")
                    print(f"    -> has_monte_carlo_results: {manifest.get('has_monte_carlo_results', 'N/A')}")
                    
                    completeness = manifest.get('completeness', {}).get('components', {})
                    print(f"    -> economic_analysis: {completeness.get('economic_analysis', 'N/A')}")
                    print(f"    -> optimization_done: {completeness.get('optimization_done', 'N/A')}")
                    print(f"    -> monte_carlo_done: {completeness.get('monte_carlo_done', 'N/A')}")
                except Exception as e:
                    print(f"    ❌ Erreur lecture manifest: {e}")

def run_all_debug_tests():
    """Lance tous les tests de debug"""
    print("🔍 DIAGNOSTIC COMPLET DU SYSTÈME DE STORAGE")
    print("=" * 50)
    
    # 1. Simuler session_state
    session_state = debug_session_state_content()
    
    # 2. Tester calcul complétude
    components, score = debug_completeness_calculation(session_state)
    
    # 3. Tester filtrage exclusions
    saved_keys, excluded_keys = debug_exclusion_filtering(session_state)
    
    # 4. Tester création manifest
    manifest = debug_manifest_creation(session_state, components, score)
    
    # 5. Tester logique de comparaison
    project1_data, project2_data = debug_comparison_data_loading()
    
    # 6. Vérifier structure fichiers réels
    debug_file_structure()
    
    print("\n" + "=" * 50)
    print("🎯 RÉSUMÉ DU DIAGNOSTIC")
    print("=" * 50)
    print("✅ Tests de simulation terminés")
    print("📋 Vérifiez les incohérences détectées ci-dessus")
    print("🔧 Les problèmes identifiés nécessitent des corrections")

if __name__ == "__main__":
    run_all_debug_tests()