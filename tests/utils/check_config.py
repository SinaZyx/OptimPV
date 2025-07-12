#!/usr/bin/env python3
"""
Vérification de la configuration et des colonnes calculées
"""

import json
import os

def check_monthly_cash_flow_structure():
    """Vérifie la structure du fichier de configuration des flux mensuels"""
    print("=== VÉRIFICATION DE LA CONFIGURATION DES FLUX MENSUELS ===\n")
    
    config_file = "config/monthly_cash_flow_structure.json"
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"✅ Fichier chargé: {config_file}")
        print(f"   Nombre d'éléments: {len(config)}")
        
        # Analyser la section VI
        print("\n📊 ANALYSE DE LA SECTION VI:")
        section_vi_started = False
        section_vi_items = []
        
        for i, item in enumerate(config):
            if item.get('id') == 'section_vi_header' or item.get('display_name', '').startswith('VI.'):
                section_vi_started = True
                print(f"\n   Section VI trouvée à l'index {i}")
            
            if section_vi_started:
                item_type = item.get('type', 'unknown')
                item_id = item.get('id', 'NO_ID')
                display_name = item.get('display_name', 'NO_NAME')
                
                if item_type not in ['visual_separator_subtle', 'visual_separator_strong']:
                    section_vi_items.append({
                        'index': i,
                        'id': item_id,
                        'type': item_type,
                        'display_name': display_name,
                        'source_column': item.get('source_column'),
                        'calculation': item.get('calculation')
                    })
        
        print(f"\n   Items de la Section VI (hors séparateurs):")
        for item in section_vi_items:
            print(f"\n   [{item['index']}] {item['display_name']}")
            print(f"       ID: {item['id']}")
            print(f"       Type: {item['type']}")
            if item['source_column']:
                print(f"       Source: {item['source_column']}")
            if item['calculation']:
                print(f"       Calcul: {item['calculation'][:80]}...")
        
        # Vérifier les problèmes potentiels
        print("\n\n🔍 VÉRIFICATION DES PROBLÈMES POTENTIELS:")
        
        # 1. Trésorerie totale
        tresorerie_item = next((item for item in section_vi_items if item['id'] == 'tresorerie_totale_fin'), None)
        if tresorerie_item:
            print(f"\n1. Trésorerie totale:")
            print(f"   - Source column: {tresorerie_item['source_column']}")
            print(f"   - Type: {tresorerie_item['type']}")
            if tresorerie_item['source_column'] == 'Solde_Tresorerie_Fin_Mois':
                print("   ✅ Source correcte")
            else:
                print("   ❌ PROBLÈME: Source incorrecte!")
        
        # 2. Réserve minimum
        reserve_item = next((item for item in section_vi_items if item['id'] == 'reserve_minimum'), None)
        if reserve_item:
            print(f"\n2. Réserve minimum:")
            print(f"   - Source column: {reserve_item['source_column']}")
            print(f"   - Type: {reserve_item['type']}")
            if reserve_item['source_column'] == 'Reserve_Minimum_Requise':
                print("   ✅ Source correcte")
            else:
                print("   ❌ PROBLÈME: Source incorrecte!")
        
        # 3. Items calculés
        calculated_items = [item for item in section_vi_items if item['type'] == 'calculated']
        print(f"\n3. Items calculés ({len(calculated_items)}):")
        for item in calculated_items:
            print(f"\n   - {item['display_name']}")
            print(f"     Calcul: {item['calculation']}")
            
            # Vérifier si le calcul utilise les bonnes colonnes
            if 'Reserve_Minimum_Requise' in item['calculation']:
                print("     ✅ Utilise Reserve_Minimum_Requise")
            if 'Solde_Tresorerie_Fin_Mois' in item['calculation']:
                print("     ✅ Utilise Solde_Tresorerie_Fin_Mois")
        
        # 4. Vérifier les colonnes référencées
        print("\n\n📋 COLONNES RÉFÉRENCÉES DANS LA SECTION VI:")
        all_columns = set()
        for item in section_vi_items:
            if item['source_column']:
                all_columns.add(item['source_column'])
            if item['calculation']:
                # Extraire les colonnes du calcul lambda
                import re
                matches = re.findall(r"row\.get\('([^']+)'", item['calculation'])
                all_columns.update(matches)
        
        print("   Colonnes utilisées:")
        for col in sorted(all_columns):
            print(f"   - {col}")
        
        print("\n\n💡 RECOMMANDATIONS:")
        print("1. Vérifier que toutes ces colonnes existent dans monthly_results_df")
        print("2. Vérifier que les valeurs ne sont pas hardcodées dans core_analyzer.py")
        print("3. Vérifier que les calculs lambda sont correctement évalués")
        print("4. Vérifier que le type 'data' lit bien depuis le DataFrame")
        
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {config_file}")
    except json.JSONDecodeError as e:
        print(f"❌ Erreur JSON: {e}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_monthly_cash_flow_structure()