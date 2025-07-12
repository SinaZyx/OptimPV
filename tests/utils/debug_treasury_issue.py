#!/usr/bin/env python3
"""
Debug du problème d'affichage de trésorerie fixe à 8500€
"""

import sys
import os

# Configuration des imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Analyse des logs uniquement
def analyze_treasury_in_logs():
    """Analyse détaillée des logs pour comprendre le problème de trésorerie"""
    print("=== ANALYSE DU PROBLÈME DE TRÉSORERIE FIXE ===\n")
    
    try:
        with open('log.txt', 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # 1. Recherche de toutes les valeurs liées à la trésorerie
        print("1. RECHERCHE DES VALEURS DE TRÉSORERIE:")
        treasury_patterns = [
            'Tresorerie_Fin_Mois:',
            'Solde_Tresorerie_Fin_Mois',
            'initial_cash_balance',
            'FCFE',
            'flux_treso_nets_mensuels'
        ]
        
        found_values = {}
        for pattern in treasury_patterns:
            found_values[pattern] = []
            for i, line in enumerate(lines):
                if pattern in line:
                    found_values[pattern].append((i, line.strip()))
        
        # Afficher les résultats
        for pattern, matches in found_values.items():
            if matches:
                print(f"\n  {pattern}:")
                for line_num, line in matches[:5]:  # Premières 5 occurrences
                    print(f"    L{line_num}: {line}")
                if len(matches) > 5:
                    print(f"    ... et {len(matches) - 5} autres occurrences")
        
        # 2. Recherche spécifique du problème 8500
        print("\n\n2. RECHERCHE SPÉCIFIQUE DE LA VALEUR 8500:")
        lines_with_8500 = []
        for i, line in enumerate(lines):
            if '8500' in line or '8,500' in line:
                lines_with_8500.append((i, line))
        
        if lines_with_8500:
            print(f"  Trouvé {len(lines_with_8500)} lignes contenant 8500:")
            for line_num, line in lines_with_8500[:10]:
                print(f"    L{line_num}: {line.strip()}")
                # Afficher le contexte
                if line_num > 0 and line_num < len(lines) - 1:
                    print(f"      Avant: {lines[line_num-1].strip()}")
                    print(f"      Après: {lines[line_num+1].strip()}")
        else:
            print("  ⚠️ Aucune ligne ne contient 8500")
        
        # 3. Recherche des calculs de placements
        print("\n\n3. RECHERCHE DES CALCULS DE PLACEMENTS:")
        placement_patterns = [
            'Total_Placements',
            'Solde_Placement_TVA_Cumul',
            'Solde_Placement_Excedents_Cumul',
            'Fonds_Reserve_Onduleur_Total',
            'Reserve_Minimum_Requise'
        ]
        
        for pattern in placement_patterns:
            print(f"\n  {pattern}:")
            count = 0
            for i, line in enumerate(lines):
                if pattern in line and ('€' in line or ':' in line):
                    print(f"    L{i}: {line.strip()}")
                    count += 1
                    if count >= 3:  # Limiter à 3 exemples
                        break
        
        # 4. Analyse du problème Section VI
        print("\n\n4. ANALYSE SECTION VI:")
        section_vi_patterns = [
            'SECTION VI',
            'Section VI',
            'tresorerie_totale_fin',
            'reserve_minimum',
            'ratio_securite',
            'placements.*excedents.*detail'
        ]
        
        import re
        for pattern in section_vi_patterns:
            print(f"\n  Pattern '{pattern}':")
            regex = re.compile(pattern, re.IGNORECASE)
            count = 0
            for i, line in enumerate(lines):
                if regex.search(line):
                    print(f"    L{i}: {line.strip()}")
                    count += 1
                    if count >= 3:
                        break
        
        # 5. Recherche des erreurs récentes
        print("\n\n5. ERREURS ET AVERTISSEMENTS RÉCENTS:")
        error_patterns = ['ERROR', 'ERREUR', 'WARNING', 'ALERTE', 'Exception', 'Traceback']
        recent_errors = []
        
        for i in range(max(0, len(lines) - 500), len(lines)):  # Dernières 500 lignes
            line = lines[i]
            for pattern in error_patterns:
                if pattern in line:
                    recent_errors.append((i, line.strip()))
                    break
        
        if recent_errors:
            print(f"  Trouvé {len(recent_errors)} erreurs/avertissements récents:")
            for line_num, line in recent_errors[-10:]:  # Dernières 10
                print(f"    L{line_num}: {line}")
        else:
            print("  ✅ Aucune erreur récente trouvée")
        
        # 6. Diagnostic final
        print("\n\n6. DIAGNOSTIC DU PROBLÈME:")
        print("  📋 Résumé des constatations:")
        
        if len(lines_with_8500) == 1:
            print("  - La valeur 8500 n'apparaît qu'une seule fois dans les logs")
            print("  - Cela suggère que la trésorerie est initialisée à 8500 mais ne varie pas")
            print("  - Causes possibles:")
            print("    1. FCFE = 0 tout au long de la simulation")
            print("    2. Les flux de trésorerie ne sont pas correctement calculés")
            print("    3. La colonne affichée n'est pas la bonne")
        elif len(lines_with_8500) > 1:
            print(f"  - La valeur 8500 apparaît {len(lines_with_8500)} fois")
            print("  - Cela pourrait indiquer une valeur par défaut utilisée")
        
        print("\n  💡 Recommandations:")
        print("  1. Vérifier que FCFE est bien calculé et non nul")
        print("  2. Vérifier que initial_cash_balance est correctement utilisé")
        print("  3. Vérifier que la formule cumsum() fonctionne correctement")
        print("  4. Vérifier que la bonne colonne est affichée dans le tableau")
        
    except FileNotFoundError:
        print("❌ Fichier log.txt non trouvé")
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_treasury_in_logs()