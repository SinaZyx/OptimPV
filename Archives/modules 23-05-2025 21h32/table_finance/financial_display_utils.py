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

def format_value(value, unit='€', decimals=0, default_na="-"): # Default_na à "-"
    """Formate une valeur numérique avec unité et décimales, gère NaN/None/Inf."""
    if pd.isna(value) or value is None: # NaN ou None
        return default_na
    if isinstance(value, (float, np.floating)) and not np.isfinite(value): # Gérer Infini
        return "+∞" if value > 0 else ("-∞" if value < 0 else default_na) 

    try:
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