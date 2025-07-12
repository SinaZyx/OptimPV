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