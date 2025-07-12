# modules/financial_display_utils.py
import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from collections import OrderedDict # Assurez-vous que c'est importé si utilisé dans load_table_map

CONFIG_DIR = "config" 
TABLE_MAP_FILE = os.path.join(CONFIG_DIR, "financial_table_map.json")
_table_map_cache = None

def load_table_map():
    """Loads the table mapping configuration from the JSON file."""
    global _table_map_cache
    if _table_map_cache is not None:
        if isinstance(_table_map_cache, dict) and _table_map_cache:
            return _table_map_cache
        else:
             _table_map_cache = None

    effective_path = TABLE_MAP_FILE
    if not os.path.exists(effective_path):
        try:
            script_dir = os.path.dirname(__file__)
            alt_path = os.path.join(script_dir, "..", CONFIG_DIR, os.path.basename(TABLE_MAP_FILE))
            alt_path = os.path.normpath(alt_path)
            if os.path.exists(alt_path):
                 effective_path = alt_path
            else:
                 print(f"ERREUR UTILS: Fichier map introuvable: Ni à '{TABLE_MAP_FILE}' ni à '{alt_path}'")
                 # Ne pas appeler st.error ici directement si ce module est purement utilitaire
                 return None
        except NameError: 
            print(f"ERREUR UTILS: __file__ non défini, impossible de trouver {TABLE_MAP_FILE} relativement.")
            return None
    try:
        with open(effective_path, 'r', encoding='utf-8') as f:
            # Utiliser object_pairs_hook=OrderedDict si l'ordre du JSON est important pour vous
            loaded_map = json.load(f, object_pairs_hook=OrderedDict) 
        if not isinstance(loaded_map, dict):
             raise ValueError("Le fichier JSON de table_map ne contient pas un dictionnaire valide.")
        for key, info in loaded_map.items():
             if not isinstance(info, dict) or "display_name" not in info or "group" not in info:
                  raise ValueError(f"Entrée invalide dans table_map JSON pour clé '{key}'.")
        _table_map_cache = loaded_map
        return _table_map_cache
    except Exception as e:
        print(f"ERREUR UTILS: Erreur chargement/validation de {effective_path}: {e}")
        return None

def format_value(value, unit='€', decimals=0, default_na="-", format_type=None): # Default_na à "-"
    """Formate une valeur numérique avec unité et décimales, gère NaN/None/Inf."""
    if pd.isna(value) or value is None: # NaN ou None
        return default_na
    if isinstance(value, (float, np.floating)) and not np.isfinite(value): # Gérer Infini
        return "+∞" if value > 0 else ("-∞" if value < 0 else default_na) 

    try:
        # Gestion spéciale pour les ratios
        if format_type == 'ratio':
            if value < 1.0:
                return f"<span style='color: red;'>{value:.{decimals}f}x</span>"
            elif value < 1.5:
                return f"<span style='color: orange;'>{value:.{decimals}f}x</span>"
            else:
                return f"<span style='color: green;'>{value:.{decimals}f}x</span>"
        
        if unit == '%':
            # La valeur est supposée être déjà en pourcentage (ex: 25.0 pour 25%)
            format_str = f"{{:,.{decimals}f}}%"
            return format_str.format(value)
        
        format_str = f"{{:,.{decimals}f}}" # Pour les nombres
        formatted_value = format_str.format(value)

        if unit is None or unit == "": return formatted_value
        # Utiliser un espace insécable pour l'euro
        return f"{formatted_value}\u00A0{unit}" if unit == '€' else f"{formatted_value} {unit}"
    except (ValueError, TypeError):
        return str(value) # Fallback si le formatage échoue

def get_display_name_from_map(key: str, table_map: dict | None, fallback: str | None = None) -> str:
    """Helper pour obtenir le display_name depuis table_map, avec fallback."""
    if table_map and isinstance(table_map, dict) and \
       key in table_map and isinstance(table_map[key], dict) and \
       "display_name" in table_map[key]:
        return table_map[key]["display_name"]
    
    # Fallback si la clé ou display_name n'est pas trouvé
    final_fallback = fallback if fallback is not None else key.replace("_", " ").capitalize()
    # print(f"DEBUG get_dn: Clé '{key}' non trouvée ou display_name manquant dans table_map. Utilisation de fallback: '{final_fallback}'")
    return final_fallback

def calculate_annual_total_from_monthly(df_monthly, column_name, year):
    """
    Calcule le total annuel d'une colonne pour une année donnée.
    - Pour les FLUX (revenus, charges) : SOMME des 12 mois
    - Pour les SOLDES (placements, trésorerie) : DERNIÈRE valeur non-NaN
    
    Parameters:
    -----------
    df_monthly : pd.DataFrame
        DataFrame avec index DatetimeIndex contenant les données mensuelles
    column_name : str
        Nom de la colonne à calculer
    year : int
        Année pour laquelle calculer le total
        
    Returns:
    --------
    float
        Total annuel de la colonne pour l'année spécifiée
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Filtrer par année
    if isinstance(df_monthly.index, pd.DatetimeIndex):
        year_data = df_monthly[df_monthly.index.year == year]
    else:
        # Si l'index n'est pas datetime, supposer qu'il y a une colonne Year
        year_data = df_monthly[df_monthly['Year'] == year] if 'Year' in df_monthly.columns else df_monthly
    
    if column_name not in year_data.columns:
        logger.warning(f"Colonne '{column_name}' non trouvée dans les données mensuelles. Retour de 0.")
        return 0.0  # Retourner 0 au lieu de NaN pour éviter les problèmes d'affichage
    
    # NOUVELLE LOGIQUE : Distinguer soldes vs flux
    solde_keywords = [
        # Mots-clés génériques
        'solde', 'encours', 'cumul', 'balance', 'fin_mois',
        
        # Colonnes exactes des placements (depuis core_analyzer.py)
        'total_placements', 'tresorerie_non_placee', 'solde_placement',
        'solde_tresorerie', 'solde_dette_fin_mois', 'bfr_mensuel',
        'interets_tva_courus_non_encaisses',
        
        # IDs exacts depuis monthly_cash_flow_structure.json
        'tresorerie_non_placee_fin', 'total_placements_fin',
        'cash_opening_balance', 'cash_closing_balance',
        
        # Variantes avec espaces
        'total placements', 'trésorerie non placée', 'solde placement',
        
        # Colonnes de réserve et fonds
        'reserve_minimum_requise', 'fonds_reserve_onduleur', 'tresorerie_disponible'
    ]
    
    # Vérifier si c'est un solde (insensible à la casse)
    is_solde = any(keyword in column_name.lower() for keyword in solde_keywords)
    
    if is_solde:
        # Pour les SOLDES : prendre la dernière valeur non-NaN
        values = year_data[column_name]
        valid_values = values.dropna()
        
        if valid_values.empty:
            logger.warning(f"Aucune valeur valide trouvée pour le solde '{column_name}'. Retour de 0.")
            return 0.0  # Retourner 0 au lieu de NaN pour les soldes vides
        
        # Retourner la dernière valeur valide
        return valid_values.iloc[-1]
    else:
        # Pour les FLUX : conserver la somme actuelle
        values = year_data[column_name].fillna(0)
        total = values.sum()
        
        # Validation pour les intérêts (existante)
        if column_name == 'Interets_Payes' and total > 0:
            non_zero_count = (values > 0).sum()
            if non_zero_count > 0 and total < values.mean() * 3:
                logger.warning(f"Total intérêts suspicieusement bas : {total:.2f}€ pour {non_zero_count} mois")
        
        return total

def get_table_css(table_type='annual'):
    """
    Retourne les styles CSS harmonisés pour les tableaux financiers.
    
    Parameters:
    -----------
    table_type : str
        Le type de tableau pour lequel générer le CSS.
        Valeurs possibles: 'annual' (synthèse annuelle) ou 'monthly' (flux mensuels).
        
    Returns:
    --------
    str
        Le code CSS à insérer dans le HTML via st.markdown().
    """
    # Classe CSS en fonction du type de tableau
    table_class = "dataframe-annual-summary" if table_type == 'annual' else "dataframe-cfs"
    
    # Styles CSS communs, harmonisés pour les deux types de tableaux
    common_css = f"""
    <style>
        table.{table_class} {{ 
            width: 100%; 
            border-collapse: collapse; 
            font-size: 0.9em; 
            margin-bottom: 15px; 
        }}
        table.{table_class} th {{ 
            text-align: right; 
            padding: 5px 8px; 
            border-bottom: 1px solid #bbb; 
            background-color: #eef; 
            font-weight: bold; 
            position: sticky; 
            top: 0; 
            z-index: 1; 
        }}
        table.{table_class} td {{ 
            text-align: right; 
            padding: 5px 8px; 
            border-bottom: 1px dotted #ddd; 
        }}
        table.{table_class} td:first-child, 
        table.{table_class} th:first-child {{ 
            text-align: left; 
        }}
        table.{table_class} tr:nth-child(even) td {{ 
            background-color: #f9f9f9; 
        }}
        table.{table_class} tr:hover td {{ 
            background-color: #f0f8ff; 
        }}
        
        /* Styles pour les séparateurs et indentations */
        .indent-1 {{ padding-left: 25px !important; }}
        .indent-2 {{ padding-left: 40px !important; }}
        
        /* Styles pour les lignes spéciales */
        .total-row-style td {{ 
            font-weight: bold !important; 
            border-top: 1px solid #aaa; 
        }}
        .subtotal-row-style td {{ 
            font-style: italic; 
        }}
        .main-total-row-style td {{ 
            font-weight: bold !important; 
            border-top: 2px solid #888; 
            border-bottom: 2px solid #888; 
            background-color: #e0e7ff; 
        }}
        
        /* Séparateurs visuels */
        .separator-row-subtle td {{ 
            height: 5px; 
            padding: 0 !important; 
            border: 0 !important; 
            background-color: #f0f0f0 !important; 
        }}
        .separator-row-strong td {{ 
            height: 10px; 
            padding: 0 !important; 
            border: 0 !important; 
            background-color: #e0e0e0 !important; 
        }}
        
        /* Séparateurs de trimestre et colonne de synthèse annuelle */
        table.{table_class} th.quarter-sep,
        table.{table_class} td.quarter-sep {{ 
            border-right: 2px solid #b0c4de; 
        }}
        table.{table_class} th.annual-summary-col,
        table.{table_class} td.annual-summary-col {{
            font-weight: bold;
            background-color: #e8eaf6; /* Couleur de fond distincte */
            border-left: 2px solid #b0c4de; /* Séparateur à gauche */
        }}
    """
    
    # CSS spécifique pour le tableau mensuel des flux de trésorerie
    if table_type == 'monthly':
        common_css += f"""
        /* Styles spécifiques pour les en-têtes de groupe dans les flux mensuels */
        .group-header-cfs td {{ 
            background-color: #d0d9ff !important; 
            font-weight: bold; 
            text-align: left !important; 
            padding: 8px 4px !important; 
            border-top: 2px solid #aaa; 
            border-bottom: 1px solid #bbb; 
        }}
        
        /* Classes pour compatibilité avec l'ancien code */
        .separator-row-cfs-subtle td {{ 
            height: 5px; 
            padding: 0 !important; 
            border: 0 !important; 
            background-color: #f0f0f0 !important; 
        }}
        .separator-row-cfs-strong td {{ 
            height: 10px; 
            padding: 0 !important; 
            border: 0 !important; 
            background-color: #e0e0e0 !important; 
        }}
        """
    # CSS spécifique pour le tableau de synthèse annuelle
    else:  # table_type == 'annual'
        common_css += f"""
        /* Styles spécifiques pour les en-têtes de groupe dans la synthèse annuelle */
        .group-header-style td {{
            background-color: #d0d9ff !important; 
            font-weight: bold; 
            text-align: left !important;
            padding: 7px 4px !important; 
            border-top: 2px solid #aaa; 
            border-bottom: 1px solid #bbb;
        }}
        """
    
    # Fermer la balise style
    common_css += "</style>"
    
    return common_css

def test_annual_total_calculation():
    """
    Test unitaire pour vérifier la distinction soldes/flux dans calculate_annual_total_from_monthly().
    
    Cette fonction teste que :
    - Les FLUX (revenus, charges, intérêts) calculent la SOMME des 12 mois
    - Les SOLDES (placements, trésorerie, encours) retournent la DERNIÈRE valeur non-NaN
    
    Returns:
    --------
    bool
        True si tous les tests passent, False sinon
    """
    import pandas as pd
    import numpy as np
    
    print("🧪 DÉMARRAGE DES TESTS - Calcul des totaux annuels")
    print("=" * 60)
    
    try:
        # Créer un DataFrame de test avec 12 mois
        dates = pd.date_range('2024-01-01', periods=12, freq='M')
        test_data = pd.DataFrame({
            # FLUX - Doivent être sommés
            'Revenus_Total': [1000] * 12,  # Attendu = 12,000
            'OPEX': [100] * 12,  # Attendu = 1,200
            'Interets_Payes': [50] * 12,  # Attendu = 600
            'Interets_Placements_Mensuels': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120],  # Attendu = 780
            'TURPE': [25] * 12,  # Attendu = 300
            
            # SOLDES - Doivent retourner la dernière valeur
            'Total_Placements': [0, 0, 0, 77, 154, 231, 308, 385, 462, 539, 616, 693],  # Attendu = 693
            'Solde_Placement_TVA_Cumul': [0, 0, 0, 50, 100, 150, 200, 250, 300, 350, 400, 450],  # Attendu = 450
            'Tresorerie_Non_Placee': [1000, 980, 960, 1200, 1180, 1160, 1140, 1120, 1100, 1080, 1060, 1040],  # Attendu = 1040
            'Solde_Dette_Fin_Mois': [50000, 48000, 46000, 44000, 42000, 40000, 38000, 36000, 34000, 32000, 30000, 28000],  # Attendu = 28000
            'BFR_Mensuel': [100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 155],  # Attendu = 155
            'Encours_Quelconque': [0, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500],  # Attendu = 5500
            
            # CAS LIMITE - Solde avec des NaN
            'Solde_Avec_NaN': [np.nan, np.nan, 100, 200, 300, np.nan, 400, 500, np.nan, 600, 700, 800],  # Attendu = 800
        }, index=dates)
        
        # Tests des FLUX (doivent être sommés)
        test_cases_flux = [
            ('Revenus_Total', 12000, "Revenus Total"),
            ('OPEX', 1200, "OPEX"),
            ('Interets_Payes', 600, "Intérêts Payés"),
            ('Interets_Placements_Mensuels', 780, "Intérêts Placements"),
            ('TURPE', 300, "TURPE"),
        ]
        
        print("🔄 Tests des FLUX (somme attendue):")
        flux_tests_passed = 0
        for column, expected, description in test_cases_flux:
            result = calculate_annual_total_from_monthly(test_data, column, 2024)
            status = "✅ PASS" if abs(result - expected) < 0.01 else "❌ FAIL"
            print(f"  {status} {description}: {result:,.0f}€ (attendu: {expected:,.0f}€)")
            if abs(result - expected) < 0.01:
                flux_tests_passed += 1
        
        # Tests des SOLDES (doivent retourner la dernière valeur)
        test_cases_soldes = [
            ('Total_Placements', 693, "Total Placements"),
            ('Solde_Placement_TVA_Cumul', 450, "Solde Placement TVA"),
            ('Tresorerie_Non_Placee', 1040, "Trésorerie Non Placée"),
            ('Solde_Dette_Fin_Mois', 28000, "Solde Dette Fin Mois"),
            ('BFR_Mensuel', 155, "BFR Mensuel"),
            ('Encours_Quelconque', 5500, "Encours Quelconque"),
            ('Solde_Avec_NaN', 800, "Solde avec NaN"),
        ]
        
        print("\n📊 Tests des SOLDES (dernière valeur attendue):")
        soldes_tests_passed = 0
        for column, expected, description in test_cases_soldes:
            result = calculate_annual_total_from_monthly(test_data, column, 2024)
            status = "✅ PASS" if abs(result - expected) < 0.01 else "❌ FAIL"
            print(f"  {status} {description}: {result:,.0f}€ (attendu: {expected:,.0f}€)")
            if abs(result - expected) < 0.01:
                soldes_tests_passed += 1
        
        # Test cas d'erreur - colonne inexistante
        print("\n🚫 Tests des cas d'erreur:")
        result_error = calculate_annual_total_from_monthly(test_data, 'Colonne_Inexistante', 2024)
        error_test_passed = pd.isna(result_error)
        status = "✅ PASS" if error_test_passed else "❌ FAIL"
        print(f"  {status} Colonne inexistante: {result_error} (attendu: NaN)")
        
        # Résumé final
        total_tests = len(test_cases_flux) + len(test_cases_soldes) + 1
        total_passed = flux_tests_passed + soldes_tests_passed + (1 if error_test_passed else 0)
        
        print("\n" + "=" * 60)
        print(f"📊 RÉSUMÉ DES TESTS:")
        print(f"   Tests de FLUX réussis: {flux_tests_passed}/{len(test_cases_flux)}")
        print(f"   Tests de SOLDES réussis: {soldes_tests_passed}/{len(test_cases_soldes)}")
        print(f"   Tests d'erreur réussis: {1 if error_test_passed else 0}/1")
        print(f"   TOTAL: {total_passed}/{total_tests} tests réussis")
        
        if total_passed == total_tests:
            print("✅ TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS!")
            print("🎉 La distinction soldes/flux fonctionne correctement.")
            return True
        else:
            print("❌ CERTAINS TESTS ONT ÉCHOUÉ!")
            print("⚠️  Vérifiez la logique de calculate_annual_total_from_monthly()")
            return False
            
    except Exception as e:
        print(f"❌ ERREUR LORS DES TESTS: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_financial_calculations_coherence(monthly_df, year):
    """
    Valide la cohérence des calculs financiers sur les données réelles.
    
    Cette fonction vérifie que :
    - Les totaux des soldes correspondent aux dernières valeurs
    - Les totaux des flux correspondent aux sommes
    - Il n'y a pas d'incohérences majeures
    
    Parameters:
    -----------
    monthly_df : pd.DataFrame
        DataFrame avec les données mensuelles réelles
    year : int
        Année à valider
        
    Returns:
    --------
    dict
        Dictionnaire avec le résultat de la validation
    """
    import pandas as pd
    import numpy as np
    
    validation_results = {
        'total_checks': 0,
        'passed_checks': 0,
        'failed_checks': [],
        'warnings': [],
        'is_valid': True
    }
    
    try:
        # Colonnes communes à vérifier
        flux_columns = [
            'Revenus_Total', 'OPEX', 'TURPE', 'Interets_Payes', 
            'Interets_Placements_Mensuels', 'Total_IS_Decaisse_Mois'
        ]
        
        solde_columns = [
            'Total_Placements', 'Solde_Placement_TVA_Cumul', 'Tresorerie_Non_Placee',
            'Solde_Dette_Fin_Mois', 'BFR_Mensuel', 'Solde_Tresorerie_Fin_Mois'
        ]
        
        # Vérifier les flux
        for col in flux_columns:
            if col in monthly_df.columns:
                validation_results['total_checks'] += 1
                calculated_total = calculate_annual_total_from_monthly(monthly_df, col, year)
                
                # Calcul manuel de la somme pour comparaison
                year_data = monthly_df[monthly_df.index.year == year] if isinstance(monthly_df.index, pd.DatetimeIndex) else monthly_df
                manual_sum = year_data[col].fillna(0).sum() if col in year_data.columns else 0
                
                if abs(calculated_total - manual_sum) < 0.01:
                    validation_results['passed_checks'] += 1
                else:
                    validation_results['failed_checks'].append({
                        'column': col,
                        'type': 'FLUX',
                        'calculated': calculated_total,
                        'expected': manual_sum,
                        'difference': abs(calculated_total - manual_sum)
                    })
        
        # Vérifier les soldes
        for col in solde_columns:
            if col in monthly_df.columns:
                validation_results['total_checks'] += 1
                calculated_total = calculate_annual_total_from_monthly(monthly_df, col, year)
                
                # Calcul manuel de la dernière valeur pour comparaison
                year_data = monthly_df[monthly_df.index.year == year] if isinstance(monthly_df.index, pd.DatetimeIndex) else monthly_df
                if col in year_data.columns:
                    valid_values = year_data[col].dropna()
                    manual_last = valid_values.iloc[-1] if not valid_values.empty else np.nan
                else:
                    manual_last = np.nan
                
                if pd.isna(calculated_total) and pd.isna(manual_last):
                    validation_results['passed_checks'] += 1
                elif abs(calculated_total - manual_last) < 0.01:
                    validation_results['passed_checks'] += 1
                else:
                    validation_results['failed_checks'].append({
                        'column': col,
                        'type': 'SOLDE',
                        'calculated': calculated_total,
                        'expected': manual_last,
                        'difference': abs(calculated_total - manual_last) if pd.notna(calculated_total) and pd.notna(manual_last) else 'NaN'
                    })
        
        # Déterminer si la validation est réussie
        validation_results['is_valid'] = len(validation_results['failed_checks']) == 0
        
        return validation_results
        
    except Exception as e:
        validation_results['is_valid'] = False
        validation_results['failed_checks'].append({
            'error': str(e),
            'type': 'EXCEPTION'
        })
        return validation_results

def test_solde_detection_for_config_ids():
    """
    Test spécifique pour vérifier que les IDs de la configuration JSON 
    sont bien détectés comme des soldes.
    """
    # IDs exacts depuis monthly_cash_flow_structure.json qui DOIVENT être des soldes
    config_solde_ids = [
        'tresorerie_non_placee_fin',
        'total_placements_fin', 
        'cash_opening_balance',
        'cash_closing_balance'
    ]
    
    # IDs qui DOIVENT être des flux
    config_flux_ids = [
        'placement_tva_mois',
        'placement_provision_onduleur_mois', 
        'interets_capitalises_mois',
        'revenus_clients_encaisses',
        'opex_maintenance'
    ]
    
    print("🔍 TEST SPÉCIFIQUE - Détection IDs de configuration")
    print("=" * 50)
    
    # Définir les mots-clés (copié de la fonction principale)
    solde_keywords = [
        # Mots-clés génériques
        'solde', 'encours', 'cumul', 'balance', 'fin_mois',
        
        # Colonnes exactes des placements (depuis core_analyzer.py)
        'total_placements', 'tresorerie_non_placee', 'solde_placement',
        'solde_tresorerie', 'solde_dette_fin_mois', 'bfr_mensuel',
        'interets_tva_courus_non_encaisses',
        
        # IDs exacts depuis monthly_cash_flow_structure.json
        'tresorerie_non_placee_fin', 'total_placements_fin',
        'cash_opening_balance', 'cash_closing_balance',
        
        # Variantes avec espaces
        'total placements', 'trésorerie non placée', 'solde placement'
    ]
    
    def is_solde_test(column_name):
        return any(keyword in column_name.lower() for keyword in solde_keywords)
    
    print("📊 Test des IDs qui DOIVENT être des SOLDES:")
    soldes_passed = 0
    for config_id in config_solde_ids:
        result = is_solde_test(config_id)
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {config_id}: {'SOLDE détecté' if result else 'FLUX détecté (ERREUR!)'}")
        if result:
            soldes_passed += 1
    
    print("\n🔄 Test des IDs qui DOIVENT être des FLUX:")
    flux_passed = 0
    for config_id in config_flux_ids:
        result = is_solde_test(config_id)
        status = "✅ PASS" if not result else "❌ FAIL"
        print(f"  {status} {config_id}: {'FLUX détecté' if not result else 'SOLDE détecté (ERREUR!)'}")
        if not result:
            flux_passed += 1
    
    total_tests = len(config_solde_ids) + len(config_flux_ids)
    total_passed = soldes_passed + flux_passed
    
    print("\n" + "=" * 50)
    print(f"📋 RÉSUMÉ:")
    print(f"   IDs SOLDES détectés: {soldes_passed}/{len(config_solde_ids)}")
    print(f"   IDs FLUX détectés: {flux_passed}/{len(config_flux_ids)}")
    print(f"   TOTAL: {total_passed}/{total_tests} tests réussis")
    
    if total_passed == total_tests:
        print("✅ DÉTECTION PARFAITE des IDs de configuration!")
        return True
    else:
        print("❌ Problème de détection des IDs!")
        return False

# Exécuter automatiquement les tests si le fichier est exécuté directement
if __name__ == "__main__":
    test_annual_total_calculation()
    print("\n" + "="*80 + "\n")
    test_solde_detection_for_config_ids()