#!/usr/bin/env python3
"""
Utilitaire d'organisation et de nettoyage des tests OptimPV
==========================================================

Ce script aide à organiser, nettoyer et gérer les tests.
"""

import os
import shutil
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

def organize_test_reports():
    """Organise les rapports de tests par date."""
    
    # Dossiers source et destination
    system_dir = Path(__file__).parent.parent / "system"
    reports_dir = system_dir / "test_reports"
    screenshots_dir = system_dir / "test_screenshots"
    
    if not reports_dir.exists():
        reports_dir.mkdir(parents=True)
        print("📁 Dossier test_reports créé")
    
    # Organiser par mois
    for report_file in reports_dir.glob("navigation_test_*.html"):
        try:
            # Extraire la date du nom de fichier
            date_str = report_file.stem.split('_')[-2]  # YYYYMMDD
            date_obj = datetime.strptime(date_str, "%Y%m%d")
            
            # Créer le dossier mois
            month_dir = reports_dir / f"{date_obj.year}-{date_obj.month:02d}"
            month_dir.mkdir(exist_ok=True)
            
            # Déplacer le fichier
            new_path = month_dir / report_file.name
            if not new_path.exists():
                shutil.move(str(report_file), str(new_path))
                print(f"📋 Déplacé: {report_file.name} → {month_dir.name}/")
                
                # Déplacer aussi le JSON correspondant
                json_file = report_file.with_suffix('.json')
                if json_file.exists():
                    json_new_path = month_dir / json_file.name
                    if not json_new_path.exists():
                        shutil.move(str(json_file), str(json_new_path))
                        
        except (ValueError, IndexError):
            print(f"⚠️ Nom de fichier non reconnu: {report_file.name}")
    
    # Organiser les captures d'écran
    if screenshots_dir.exists():
        for screenshot_dir in screenshots_dir.iterdir():
            if screenshot_dir.is_dir():
                try:
                    date_str = screenshot_dir.name  # YYYYMMDD_HHMMSS
                    date_obj = datetime.strptime(date_str.split('_')[0], "%Y%m%d")
                    
                    month_dir = screenshots_dir / f"{date_obj.year}-{date_obj.month:02d}"
                    month_dir.mkdir(exist_ok=True)
                    
                    new_path = month_dir / screenshot_dir.name
                    if not new_path.exists():
                        shutil.move(str(screenshot_dir), str(new_path))
                        print(f"📸 Déplacé: {screenshot_dir.name} → screenshots/{month_dir.name}/")
                        
                except (ValueError, IndexError):
                    print(f"⚠️ Dossier screenshots non reconnu: {screenshot_dir.name}")

def cleanup_old_reports(days_to_keep: int = 30):
    """Nettoie les anciens rapports de tests."""
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    deleted_count = 0
    
    system_dir = Path(__file__).parent.parent / "system"
    reports_dir = system_dir / "test_reports"
    screenshots_dir = system_dir / "test_screenshots"
    
    # Nettoyer les rapports
    if reports_dir.exists():
        for item in reports_dir.rglob("*"):
            if item.is_file():
                try:
                    # Extraire la date du nom
                    if "navigation_test_" in item.name:
                        date_str = item.stem.split('_')[-2]
                        file_date = datetime.strptime(date_str, "%Y%m%d")
                        
                        if file_date < cutoff_date:
                            item.unlink()
                            deleted_count += 1
                            print(f"🗑️ Supprimé: {item.name}")
                            
                except (ValueError, IndexError):
                    pass
    
    # Nettoyer les captures d'écran
    if screenshots_dir.exists():
        for item in screenshots_dir.rglob("*"):
            if item.is_dir() and len(item.name) == 15:  # YYYYMMDD_HHMMSS
                try:
                    date_str = item.name.split('_')[0]
                    dir_date = datetime.strptime(date_str, "%Y%m%d")
                    
                    if dir_date < cutoff_date:
                        shutil.rmtree(str(item))
                        deleted_count += 1
                        print(f"🗑️ Supprimé dossier: {item.name}")
                        
                except (ValueError, IndexError):
                    pass
    
    print(f"✅ Nettoyage terminé: {deleted_count} éléments supprimés")

def generate_test_summary():
    """Génère un résumé des tests récents."""
    
    system_dir = Path(__file__).parent.parent / "system"
    reports_dir = system_dir / "test_reports"
    
    if not reports_dir.exists():
        print("❌ Aucun rapport de test trouvé")
        return
    
    # Collecter les rapports JSON récents
    reports = []
    for json_file in reports_dir.rglob("navigation_test_*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['file_path'] = str(json_file)
                reports.append(data)
        except Exception as e:
            print(f"⚠️ Erreur lecture {json_file}: {e}")
    
    if not reports:
        print("❌ Aucun rapport JSON valide trouvé")
        return
    
    # Trier par date
    reports.sort(key=lambda x: x.get('start_time', ''), reverse=True)
    
    # Générer le résumé
    summary = {
        'generated_at': datetime.now().isoformat(),
        'total_reports': len(reports),
        'recent_reports': reports[:10],  # 10 plus récents
        'success_rate': 0,
        'common_errors': {},
        'pages_tested': set(),
        'tabs_tested': set()
    }
    
    # Analyser les données
    total_tests = 0
    total_failures = 0
    
    for report in reports:
        total_tests += 1
        total_failures += report.get('failure_count', 0)
        
        # Collecter les pages et onglets
        summary['pages_tested'].update(report.get('pages_tested', []))
        summary['tabs_tested'].update(report.get('tabs_tested', []))
        
        # Analyser les erreurs communes
        for error in report.get('errors', []):
            error_type = error.get('error_type', 'Unknown')
            summary['common_errors'][error_type] = summary['common_errors'].get(error_type, 0) + 1
    
    # Calculer le taux de succès
    if total_tests > 0:
        summary['success_rate'] = (total_tests - total_failures) / total_tests * 100
    
    # Convertir les sets en listes pour JSON
    summary['pages_tested'] = list(summary['pages_tested'])
    summary['tabs_tested'] = list(summary['tabs_tested'])
    
    # Sauvegarder le résumé
    summary_file = reports_dir / "test_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    # Afficher le résumé
    print("📊 === RÉSUMÉ DES TESTS ===")
    print(f"Nombre total de rapports: {summary['total_reports']}")
    print(f"Taux de succès global: {summary['success_rate']:.1f}%")
    print(f"Pages testées: {len(summary['pages_tested'])}")
    print(f"Onglets testés: {len(summary['tabs_tested'])}")
    
    if summary['common_errors']:
        print("\n❌ Erreurs les plus fréquentes:")
        sorted_errors = sorted(summary['common_errors'].items(), key=lambda x: x[1], reverse=True)
        for error_type, count in sorted_errors[:5]:
            print(f"  • {error_type}: {count} occurrences")
    
    print(f"\n💾 Résumé sauvé: {summary_file}")

def create_test_structure():
    """Crée la structure complète des dossiers de tests."""
    
    base_dir = Path(__file__).parent.parent
    
    # Structure des dossiers
    structure = [
        "system/test_reports",
        "system/test_screenshots", 
        "integration/reports",
        "unit/coverage",
        "utils/logs",
        "fixtures/sample_data",
        "performance/benchmarks"
    ]
    
    for folder in structure:
        folder_path = base_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Créé: tests/{folder}")
    
    # Créer des fichiers .gitkeep pour maintenir la structure
    for folder in structure:
        gitkeep = base_dir / folder / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

def main():
    """Fonction principale."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Organisateur de tests OptimPV")
    parser.add_argument("--organize", action="store_true", help="Organiser les rapports par date")
    parser.add_argument("--cleanup", type=int, metavar="DAYS", help="Nettoyer les rapports de plus de N jours")
    parser.add_argument("--summary", action="store_true", help="Générer un résumé des tests")
    parser.add_argument("--setup", action="store_true", help="Créer la structure des dossiers")
    parser.add_argument("--all", action="store_true", help="Exécuter toutes les actions")
    
    args = parser.parse_args()
    
    if args.all:
        args.setup = True
        args.organize = True
        args.summary = True
        args.cleanup = 30
    
    if args.setup:
        print("🏗️ Création de la structure des tests...")
        create_test_structure()
    
    if args.organize:
        print("📋 Organisation des rapports...")
        organize_test_reports()
    
    if args.cleanup:
        print(f"🧹 Nettoyage des rapports de plus de {args.cleanup} jours...")
        cleanup_old_reports(args.cleanup)
    
    if args.summary:
        print("📊 Génération du résumé...")
        generate_test_summary()
    
    if not any([args.organize, args.cleanup, args.summary, args.setup, args.all]):
        parser.print_help()

if __name__ == "__main__":
    main()