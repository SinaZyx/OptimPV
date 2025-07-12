# modules/monthly_cash_flow_display.py
import streamlit as st
import pandas as pd
import numpy as np
import io
import json
from datetime import datetime
import logging

# Configuration du système de logging
logger = logging.getLogger(__name__)  # Logger spécifique à ce module
if not logger.handlers:  # Éviter d'ajouter des handlers multiples
    # Configuration de base si le logger racine n'est pas configuré
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

# Assurez-vous que financial_display_utils est accessible
try:
    from .financial_display_utils import format_value, load_table_map, get_table_css
except ImportError:
    # Fallback si l'import direct échoue (utile pour certains environnements de test)
    from .financial_display_utils import format_value, load_table_map, get_table_css


# --- Helper Function to Load JSON Configuration (inchangée) ---
def load_json_config(file_path="config/monthly_cash_flow_structure.json"):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Fichier de configuration des flux de trésorerie introuvable : {file_path}")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Erreur de décodage JSON dans {file_path}: {e}")
        return None
    except Exception as e:
        st.error(f"Erreur inattendue lors du chargement de {file_path}: {e}")
        return None

def display_cash_flow_statement_restructured(results: dict | None, selected_year: int):
    """
    Affiche le tableau des flux de trésorerie mensuels (par année)
    en utilisant une structure définie dans un fichier JSON. (Version Révisée)
    """
    if not results or not isinstance(results, dict) or 'monthly_data' not in results:
        st.warning("Données mensuelles ('monthly_data') non disponibles pour les flux de trésorerie.")
        return

    monthly_df_full = results.get('monthly_data')
    if not isinstance(monthly_df_full, pd.DataFrame) or monthly_df_full.empty:
        st.warning("DataFrame mensuel pour les flux de trésorerie est invalide ou vide.")
        return

    config_structure = load_json_config()
    if not config_structure:
        st.warning("Impossible de charger la structure du tableau des flux de trésorerie. Affichage annulé.")
        return

    # --- NOUVEAU BLOC : VALIDATION COMPLÈTE DE LA CONFIGURATION ---
    is_config_structure_valid = True
    for idx, item_cfg_check in enumerate(config_structure):
        # Vérifier que l'élément est un dictionnaire
        if not isinstance(item_cfg_check, dict):
            msg = f"Erreur dans 'monthly_cash_flow_structure.json': L'élément à l'index {idx} n'est pas un dictionnaire. Reçu: {type(item_cfg_check)}."
            logger.error(msg)
            st.error(msg)
            is_config_structure_valid = False
            break
            
        # Les séparateurs visuels et section_header sont des cas spéciaux qui peuvent ne pas avoir d'ID
        item_type_check = item_cfg_check.get('type', '')
        print(f"DEBUG VALIDATION - Index: {idx}, Type: '{item_type_check}', Item: {item_cfg_check}")
        
        # IMPORTANT: Harmonisation avec PASSE 2 - Ignorer les mêmes types
        if item_type_check in ["visual_separator_subtle", "visual_separator_strong", "section_header"]:
            continue
            
        # Vérifier la présence de la clé 'id' pour les éléments non-séparateurs
        if 'id' not in item_cfg_check:
            print(f"ERREUR VALIDATION - ID MANQUANT - Index: {idx}, Item: {item_cfg_check}")
            label_approx = item_cfg_check.get('display_name', 'Libellé Non Défini')
            msg = f"Erreur dans 'monthly_cash_flow_structure.json': L'élément à l'index {idx} (libellé approx: '{label_approx}') n'a pas de clé 'id'."
            logger.error(msg)
            st.error(msg)
            is_config_structure_valid = False
            break
            
        # Vérifier que l'ID est une chaîne valide et non vide
        current_id = item_cfg_check['id']
        if not isinstance(current_id, str) or not current_id.strip():
            print(f"ERREUR VALIDATION - ID INVALIDE - Index: {idx}, ID: '{current_id}'")
            label_approx = item_cfg_check.get('display_name', 'Libellé Non Défini')
            msg = f"Erreur dans 'monthly_cash_flow_structure.json': L'élément à l'index {idx} (libellé approx: '{label_approx}') a un 'id' invalide (vide ou non-string): '{current_id}'."
            logger.error(msg)
            st.error(msg)
            is_config_structure_valid = False
            break
            
    if not is_config_structure_valid:
        st.warning("L'affichage des flux de trésorerie est annulé en raison d'erreurs de configuration dans 'monthly_cash_flow_structure.json'. Veuillez corriger le fichier et rafraîchir.")
        return
    # --- FIN DU BLOC DE VALIDATION ---

    try:
        if not isinstance(monthly_df_full.index, pd.DatetimeIndex):
            monthly_df_full.index = pd.to_datetime(monthly_df_full.index)
    except Exception as e:
        st.error(f"Erreur lors de la conversion de l'index des données mensuelles en DatetimeIndex: {e}")
        return

    df_year_filtered = monthly_df_full[monthly_df_full.index.year == selected_year].copy()
    if df_year_filtered.empty:
        st.info(f"Aucune donnée mensuelle disponible pour l'année {selected_year}.")
        return

    month_order_template = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    months_in_year_data = df_year_filtered.index.strftime('%b').str.capitalize().tolist()
    # Assurer l'ordre et la présence des mois
    months_display_order = [m for m in month_order_template if m in months_in_year_data]
    if not months_display_order:
        st.warning(f"Aucun mois valide trouvé pour l'affichage en {selected_year}.")
        return
    num_months_to_display = len(months_display_order)

    # Initialisation de la structure pour stocker les données traitées
    processed_data_for_table = {}
    # Boucle avec vérification robuste de chaque élément
    for index, item_cfg_init in enumerate(config_structure):
        # Vérifier que l'élément est un dictionnaire
        if not isinstance(item_cfg_init, dict):
            erreur_msg = f"Élément invalide à l'index {index} dans 'monthly_cash_flow_structure.json'. Attendu: dictionnaire, Reçu: {type(item_cfg_init)}. Contenu: {item_cfg_init}"
            logger.error(erreur_msg)
            st.error(f"Erreur de configuration critique : {erreur_msg}. Veuillez corriger le fichier JSON.")
            return # Arrêter si la structure est incorrecte
            
        # Les séparateurs visuels peuvent ne pas avoir d'ID, donc on les ignore de façon sécurisée
        item_type = item_cfg_init.get('type', '')
        if item_type in ["visual_separator_subtle", "visual_separator_strong"]:
            continue
            
        # Vérifier la présence de la clé 'id'
        if 'id' not in item_cfg_init:
            # Essayer d'afficher le 'display_name' pour aider à localiser l'erreur
            display_name_problem = item_cfg_init.get('display_name', 'Non spécifié (ID manquant)')
            erreur_msg = f"La clé 'id' est manquante pour l'élément à l'index {index} dans 'monthly_cash_flow_structure.json' (libellé approximatif : '{display_name_problem}')."
            logger.error(erreur_msg)
            st.error(f"Erreur de configuration critique : {erreur_msg}. Veuillez corriger le fichier JSON. L'affichage est annulé.")
            return # Arrêter car l'ID est crucial

        item_id_init = item_cfg_init['id']
        
        # Vérifier que l'ID est une chaîne non vide
        if not item_id_init or not isinstance(item_id_init, str) or item_id_init.strip() == "":
            display_name_problem = item_cfg_init.get('display_name', 'Non spécifié')
            erreur_msg = f"L'ID '{item_id_init}' pour l'élément à l'index {index} (libellé: '{display_name_problem}') est invalide (vide, non-string, ou que des espaces)."
            logger.error(erreur_msg)
            st.error(f"Erreur de configuration critique : {erreur_msg}. L'affichage est annulé.")
            return

        # Avertissement pour ID dupliqué (non bloquant mais important)
        if item_id_init in processed_data_for_table:
            warning_msg = f"Avertissement : L'ID '{item_id_init}' (libellé: {item_cfg_init.get('display_name', 'N/A')}) est utilisé plusieurs fois dans 'monthly_cash_flow_structure.json'. La dernière définition pour cet ID sera utilisée."
            logger.warning(warning_msg)
            st.warning(warning_msg)

        processed_data_for_table[item_id_init] = {
            'raw_monthly_for_calc': [0.0] * num_months_to_display, # Pour les calculs internes (avec signe comptable)
            'monthly_for_display': [0.0] * num_months_to_display, # Pour l'affichage final
            'annual_total': 0.0
        }

    # Informations sur le projet pour les flux spécifiques (début/fin)
    # Supposons que `results` contient une clé `config_globale_utilisee` ou similaire
    config_globale = results.get('config_globale_utilisee', st.session_state.get('config', {}))
    
    # NOUVEAU: Lire les dates complètes y compris construction
    date_debut_simulation_str = results.get('date_debut_simulation_effective', 
                                          config_globale.get('date_debut_simulation', datetime.now().date().isoformat()))
    date_debut_operations_str = results.get('date_debut_operations',
                                          config_globale.get('date_debut_ppa', datetime.now().date().isoformat()))
    
    # Convertir en objets datetime
    date_debut_simulation = pd.to_datetime(date_debut_simulation_str)
    date_debut_operations = pd.to_datetime(date_debut_operations_str)
    
    # Récupérer les durées
    duree_construction_mois = results.get('duree_construction_mois', 
                                        int(config_globale.get('duree_construction', 0)))
    duree_exploitation_mois = results.get('duree_exploitation_mois',
                                        int(config_globale.get('duree_ppa', 240)))
    
    # Date de fin de projet calculée à partir de la date de début des opérations et de la durée d'exploitation
    project_end_date = date_debut_operations + pd.DateOffset(months=duree_exploitation_mois - 1) if duree_exploitation_mois > 0 else date_debut_operations

    # NOUVEAU: Log pour faciliter le débogage temporel
    logger.info(f"CFS Display: Année sélectionnée = {selected_year}")
    logger.info(f"CFS Display: Phase construction: {date_debut_simulation.strftime('%Y-%m-%d')} -> {(date_debut_operations - pd.DateOffset(days=1)).strftime('%Y-%m-%d')} ({duree_construction_mois} mois)")
    logger.info(f"CFS Display: Phase exploitation: {date_debut_operations.strftime('%Y-%m-%d')} -> {project_end_date.strftime('%Y-%m-%d')} ({duree_exploitation_mois} mois)")
    
    # Vérifiez les valeurs relatives au CAPEX
    capex_scenario_key = "capex_scenario_final_utilise"  # Clé utilisée dans config
    capex_initial_mensuel_key = "CAPEX_Initial_Mensuel"  # Nouvelle colonne dans les données mensuelles
    
    valeur_capex_brute = results.get(capex_scenario_key, "Clé non trouvée !")
    logger.info(f"CFS Display: Valeur totale CAPEX ({capex_scenario_key}) dans 'results': {valeur_capex_brute}")
    
    # Vérifier si la colonne CAPEX_Initial_Mensuel existe dans les données mensuelles
    capex_mensuel_disponible = capex_initial_mensuel_key in monthly_df_full.columns
    logger.info(f"CFS Display: Colonne '{capex_initial_mensuel_key}' disponible dans données mensuelles: {capex_mensuel_disponible}")

    # Si l'année sélectionnée est dans la phase de construction, vérifier les montants de CAPEX
    if selected_year >= date_debut_simulation.year and selected_year <= date_debut_operations.year:
        capex_mensuel_annee = monthly_df_full[monthly_df_full.index.year == selected_year].get(capex_initial_mensuel_key, pd.Series(0))
        logger.info(f"CFS Display: Montants CAPEX mensuels pour {selected_year}: somme={capex_mensuel_annee.sum():.2f}, mois avec CAPEX={len(capex_mensuel_annee[capex_mensuel_annee > 0])}")

    # --- PASSE 1: Extraction des Données de Base ---
    # (Pour les items de type "data", "data_results_first_month", "data_results_last_month")
    for item_cfg in config_structure:
        # Ignorer les séparateurs visuels qui n'ont pas d'ID
        item_type = item_cfg.get('type', 'data')
        if item_type in ["visual_separator_subtle", "visual_separator_strong"]:
            continue
            
        # Après la validation complète au début, tous les éléments non-séparateurs devraient avoir un ID valide
        item_id = item_cfg['id']
        sign_multiplier = float(item_cfg.get('sign', 1.0)) # Le signe défini dans le JSON
        default_if_missing = item_cfg.get('default_if_missing', 0.0)

        # Vérifier que l'ID existe dans notre dictionnaire processed_data_for_table
        if item_id not in processed_data_for_table:
            warning_msg = f"Avertissement: ID '{item_id}' manquant dans processed_data_for_table. Cet élément sera ignoré."
            logger.warning(warning_msg)
            continue

        current_item_data = processed_data_for_table[item_id] # Référence directe

        if item_type == 'data':
            source_col = item_cfg.get('source_column')
            if source_col:
                for month_idx, month_date_obj in enumerate(df_year_filtered.index):
                    if month_idx < num_months_to_display: # Double sécurité
                        try:
                            raw_value = df_year_filtered.loc[month_date_obj, source_col]
                            value_with_sign = float(raw_value) * sign_multiplier
                        except (KeyError, ValueError, TypeError):
                            value_with_sign = float(default_if_missing) * sign_multiplier
                        current_item_data['raw_monthly_for_calc'][month_idx] = value_with_sign
                        current_item_data['monthly_for_display'][month_idx] = value_with_sign # Initialement identique
            # print(f"DEBUG PASSE 1 (data) - {item_id}: raw={current_item_data['raw_monthly_for_calc'][:3]}, display={current_item_data['monthly_for_display'][:3]}")


        elif item_type == 'data_results_first_month':
            # --- AJOUT: LOGS DE DÉBOGAGE POUR LES ITEMS data_results_first_month ---
            logger.info(f"CFS Display: Traitement item '{item_id}' type='{item_type}'. Selected_year={selected_year}")
            
            # NOUVEAU: Adaptations pour le CAPEX dans la phase de construction
            if item_id == "capex_initial_decaissement":
                # Si la colonne CAPEX_Initial_Mensuel existe, utiliser ces valeurs
                if capex_mensuel_disponible and capex_initial_mensuel_key in df_year_filtered.columns:
                    logger.info(f"CFS Display: Utilisation des valeurs mensuelles de CAPEX pour {selected_year}")
                    capex_values = df_year_filtered[capex_initial_mensuel_key].values
                    for month_idx, month_date_obj in enumerate(df_year_filtered.index):
                        if month_idx < num_months_to_display:
                            capex_value = capex_values[month_idx] if month_idx < len(capex_values) else 0.0
                            value_with_sign = float(capex_value) * sign_multiplier
                            current_item_data['raw_monthly_for_calc'][month_idx] = value_with_sign
                            current_item_data['monthly_for_display'][month_idx] = value_with_sign
                else:
                    # Sinon, utiliser l'ancienne méthode qui positionne tout le CAPEX au premier mois
                    if selected_year == date_debut_simulation.year:
                        results_key = item_cfg.get('results_key')
                        if results_key:
                            value_from_results = results.get(results_key, default_if_missing)
                            logger.info(f"CFS Display: Valeur totale CAPEX from '{results_key}': {value_from_results}")
                            
                            # Placer au premier mois de construction
                            first_month_idx = date_debut_simulation.month - 1  # 0-indexed
                            if 0 <= first_month_idx < num_months_to_display:
                                value_with_sign = float(value_from_results) * sign_multiplier
                                current_item_data['raw_monthly_for_calc'][first_month_idx] = value_with_sign
                                current_item_data['monthly_for_display'][first_month_idx] = value_with_sign
                                logger.info(f"CFS Display: Valeur CAPEX '{value_with_sign}' affectée au mois index {first_month_idx}")
                            else:
                                logger.warning(f"CFS Display: first_month_idx ({first_month_idx}) hors limites pour CAPEX")
                    else:
                        logger.info(f"CFS Display: Année {selected_year} ≠ année début simulation {date_debut_simulation.year}, pas de CAPEX")
            else:
                # Pour les autres types de data_results_first_month (apport en fonds propres, dette)
                if selected_year == date_debut_simulation.year:
                    results_key = item_cfg.get('results_key')
                    if results_key:
                        value_from_results = results.get(results_key, default_if_missing)
                        logger.info(f"CFS Display: Valeur depuis results pour '{results_key}': {value_from_results}")
                        
                        # Premier mois de la simulation (construction)
                        first_month_idx = date_debut_simulation.month - 1  # 0-indexed
                        if 0 <= first_month_idx < num_months_to_display:
                            value_with_sign = float(value_from_results) * sign_multiplier
                            current_item_data['raw_monthly_for_calc'][first_month_idx] = value_with_sign
                            current_item_data['monthly_for_display'][first_month_idx] = value_with_sign
                            logger.info(f"CFS Display: Valeur '{value_with_sign}' affectée au mois index {first_month_idx} pour {item_id}")
                        else:
                            logger.warning(f"CFS Display: first_month_idx ({first_month_idx}) hors limites pour {item_id}")
                else:
                    logger.info(f"CFS Display: Année {selected_year} ≠ année début simulation {date_debut_simulation.year}, pas de flux initial pour {item_id}")

        elif item_type == 'data_results_last_month':
            if selected_year == project_end_date.year:
                results_key = item_cfg.get('results_key')
                if results_key:
                    value_from_results = results.get(results_key, default_if_missing)
                    last_month_op_idx = project_end_date.month -1 # 0-indexed
                    if 0 <= last_month_op_idx < num_months_to_display:
                        value_with_sign = float(value_from_results) * sign_multiplier
                        current_item_data['raw_monthly_for_calc'][last_month_op_idx] = value_with_sign
                        current_item_data['monthly_for_display'][last_month_op_idx] = value_with_sign

    # --- VALIDATION : Vérifier que Service_Dette = Intérêts + Principal ---
    if 'Interets_Payes' in monthly_df_full.columns and 'Principal_Rembourse' in monthly_df_full.columns and 'Service_Dette' in monthly_df_full.columns:
        service_dette_calc = monthly_df_full['Interets_Payes'] + monthly_df_full['Principal_Rembourse']
        service_dette_actual = monthly_df_full['Service_Dette']
        diff = abs(service_dette_calc - service_dette_actual).sum()
        if diff > 0.01:
            logger.warning(f"⚠️ Incohérence détectée : Service_Dette ≠ Intérêts + Principal (diff={diff:.2f})")

    # --- PASSE 2: Calcul des Lignes "subtotal" et "calculated_total" ---
    # Boucle itérative pour gérer les dépendances (ex: un total qui dépend d'un sous-total)
    max_iterations = len(config_structure) # Au pire, une itération par item
    for iter_num in range(max_iterations):
        changed_in_this_iteration = False
        for item_idx, item_cfg in enumerate(config_structure):
            # Ignorer les séparateurs visuels et section_header
            item_type = item_cfg.get('type', '')
            
            # Debug avant l'accès potentiellement problématique
            # print(f"DEBUG PASSE 2 (iter {iter_num}) - Index: {item_idx}, Type: '{item_type}', Item avant accès ID: {item_cfg}")
            
            if item_type in ["visual_separator_subtle", "visual_separator_strong", "section_header"]:
                continue
                
            # À ce stade, tous les éléments doivent avoir un ID valide (vérifié dans la validation initiale)
            try:
                item_id = item_cfg['id']
            except KeyError:
                error_msg = f"ERREUR CRITIQUE: Accès à ID échoué - Index: {item_idx}, Type: '{item_type}', Item: {item_cfg}"
                print(error_msg)
                logger.error(error_msg)
                st.error(error_msg)
                return  # Arrêter immédiatement si ID manquant
            
            # Seuls ces types sont calculés en fonction d'autres composants
            if item_type in ['subtotal', 'calculated_total']:
                components_to_sum_ids = item_cfg.get('components', [])
                if not components_to_sum_ids:
                    continue # Pas de composants à sommer

                newly_calculated_monthly_values = [0.0] * num_months_to_display
                all_components_found_and_valid = True

                for month_idx in range(num_months_to_display):
                    current_sum_for_month = 0.0
                    for comp_id in components_to_sum_ids:
                        component_data = processed_data_for_table.get(comp_id)
                        if component_data and month_idx < len(component_data['raw_monthly_for_calc']):
                            # IMPORTANT: Toujours sommer les 'raw_monthly_for_calc' qui ont le signe comptable correct
                            current_sum_for_month += float(component_data['raw_monthly_for_calc'][month_idx])
                        else:
                            # Si un composant n'est pas (encore) trouvé ou n'a pas de données pour ce mois,
                            # on ne peut pas calculer ce total de manière fiable dans CETTE itération.
                            # On pourrait logger une alerte ici. Pour l'instant, on continue avec 0 pour ce composant.
                            # print(f"AVERTISSEMENT PASSE 2 - {item_id}: Composant '{comp_id}' manquant ou données mensuelles incomplètes pour le mois {month_idx}.")
                            all_components_found_and_valid = False # Marquer pour potentiellement réessayer
                            current_sum_for_month += 0.0 # S'assurer que la somme continue

                    newly_calculated_monthly_values[month_idx] = current_sum_for_month
                
                # Vérifier si les valeurs ont changé avant de mettre à jour
                # (pour `changed_in_this_iteration` et éviter des écritures inutiles)
                current_item_data = processed_data_for_table[item_id]
                if current_item_data['raw_monthly_for_calc'] != newly_calculated_monthly_values:
                    current_item_data['raw_monthly_for_calc'] = newly_calculated_monthly_values[:]
                    current_item_data['monthly_for_display'] = newly_calculated_monthly_values[:] # Le display suit le calcul ici
                    changed_in_this_iteration = True
                    # if item_id == "opex_total": # Debug spécifique pour opex_total
                    #     print(f"DEBUG PASSE 2 (iter {iter_num}) - {item_id}: Mis à jour raw/display à: {newly_calculated_monthly_values[:3]}")


        if not changed_in_this_iteration and iter_num > 0: # Si plus rien n'a changé (et ce n'est pas la 1ère itération)
            break # Convergence atteinte

    # --- PASSE 3: Calcul des Soldes de Trésorerie (logique de cascade) ---
    opening_balance_year_val = 0.0
    solde_treso_engine_col_name = 'Solde_Tresorerie_Fin_Mois' # Colonne de référence

    if solde_treso_engine_col_name not in monthly_df_full.columns:
        st.warning(f"Colonne '{solde_treso_engine_col_name}' non trouvée. Solde d'ouverture de l'année pourrait être incorrect sauf pour la 1ère année.")
    elif selected_year > date_debut_simulation.year:
        prev_year_data_for_balance = monthly_df_full[monthly_df_full.index.year == selected_year - 1]
        if not prev_year_data_for_balance.empty:
            try:
                opening_balance_year_val = float(prev_year_data_for_balance[solde_treso_engine_col_name].iloc[-1])
            except (IndexError, ValueError, TypeError):
                st.warning(f"Impossible de lire le solde de trésorerie de fin {selected_year -1}. Solde d'ouverture mis à 0.")
        else:
             st.warning(f"Aucune donnée pour l'année {selected_year -1}. Solde d'ouverture mis à 0.")


    current_opening_balance_iter = opening_balance_year_val
    net_cash_variation_id = next((item['id'] for item in config_structure if item.get('type') == 'calculated_total' and item.get('calculation_logic') == 'sum_main_flux'), None) # Adaptez si 'purpose' était utilisé
    opening_balance_row_id = next((item['id'] for item in config_structure if item.get('type') == 'calculated_balance_item' and item.get('calculation_logic') == 'opening_balance'), None) # Adaptez si besoin
    closing_balance_row_id = next((item['id'] for item in config_structure if item.get('type') == 'calculated_balance_item' and item.get('calculation_logic') == 'closing_balance'), None) # Adaptez

    if net_cash_variation_id and opening_balance_row_id and closing_balance_row_id:
        for month_idx in range(num_months_to_display):
            # Solde d'Ouverture
            processed_data_for_table[opening_balance_row_id]['raw_monthly_for_calc'][month_idx] = current_opening_balance_iter
            processed_data_for_table[opening_balance_row_id]['monthly_for_display'][month_idx] = current_opening_balance_iter
            
            # Variation Nette de ce mois (doit être déjà calculée dans Passe 2)
            variation_this_month = processed_data_for_table.get(net_cash_variation_id, {}).get('raw_monthly_for_calc', [0.0]*num_months_to_display)[month_idx]
            
            # Solde de Clôture
            closing_balance_this_month = current_opening_balance_iter + variation_this_month
            processed_data_for_table[closing_balance_row_id]['raw_monthly_for_calc'][month_idx] = closing_balance_this_month
            processed_data_for_table[closing_balance_row_id]['monthly_for_display'][month_idx] = closing_balance_this_month
            
            current_opening_balance_iter = closing_balance_this_month # Pour le mois suivant
    else:
        st.warning("IDs pour variation nette ou soldes de trésorerie non trouvés/correctement configurés. Calcul des soldes de trésorerie ignoré.")

    # --- ÉTAPE 4: Calcul de la Colonne "Total Année" ---
    for item_cfg_annual in config_structure:
        # Vérifier d'abord le type de l'élément
        item_type_annual = item_cfg_annual.get('type')
        
        # Ignorer les types qui n'ont pas besoin d'ID
        if item_type_annual in ["section_header", "visual_separator_subtle", "visual_separator_strong"]:
            continue
            
        # Maintenant, récupérer l'ID de manière sécurisée
        item_id_annual = item_cfg_annual.get('id')
        
        # Vérifier que l'ID est présent et non vide
        if not item_id_annual:
            logger.warning(f"AVERTISSEMENT: Élément sans 'id' ou avec 'id' vide trouvé dans la configuration annuelle: {item_cfg_annual}")
            continue # Ignorer cet élément
        
        if item_id_annual not in processed_data_for_table:
            continue

        # Utiliser 'raw_monthly_for_calc' pour la somme annuelle (contient les signes comptables)
        monthly_values_for_annual_sum = processed_data_for_table[item_id_annual].get('raw_monthly_for_calc', [])

        # Gestion spécifique pour les soldes (ouverture = 1er mois, clôture = dernier mois de l'année affichée)
        if item_type_annual == 'calculated_balance_item' and item_cfg_annual.get('calculation_logic') == 'opening_balance':
            processed_data_for_table[item_id_annual]['annual_total'] = monthly_values_for_annual_sum[0] if monthly_values_for_annual_sum else 0.0
        elif item_type_annual == 'calculated_balance_item' and item_cfg_annual.get('calculation_logic') == 'closing_balance':
            processed_data_for_table[item_id_annual]['annual_total'] = monthly_values_for_annual_sum[-1] if monthly_values_for_annual_sum else 0.0
        else: # Pour 'data', 'subtotal', 'calculated_total', etc.
            processed_data_for_table[item_id_annual]['annual_total'] = sum(filter(None, monthly_values_for_annual_sum)) # sum ignore None, mais filtrons explicitement

    # --- AJOUT: VÉRIFICATION DES VALEURS FINALES DE CAPEX ---
    capex_id = "capex_initial_decaissement"
    if capex_id in processed_data_for_table:
        capex_values = processed_data_for_table[capex_id]['raw_monthly_for_calc']
        capex_total = processed_data_for_table[capex_id]['annual_total']
        logger.info(f"CFS Display: Valeurs finales CAPEX: total={capex_total:.2f}, nb_mois_avec_capex={len([v for v in capex_values if v != 0])}")
        
        # Si aucun CAPEX n'est affiché alors qu'on est dans l'année de construction, log d'avertissement
        if capex_total == 0 and selected_year == date_debut_simulation.year:
            logger.warning(f"CFS Display: CAPEX est zéro pour l'année de début de construction {selected_year}. Vérifier config/données.")
    else:
        logger.warning(f"CFS Display: ID '{capex_id}' introuvable dans processed_data_for_table.")
        
    # NOUVEAU: Afficher un indicateur si on est en phase de construction
    if selected_year >= date_debut_simulation.year and selected_year < date_debut_operations.year:
        st.info(f"Phase de construction: {selected_year} (le projet démarre son exploitation en {date_debut_operations.year})")
    elif selected_year == date_debut_operations.year and date_debut_simulation.year != date_debut_operations.year:
        # Si l'année contient à la fois de la construction et de l'exploitation
        month_debut_op = date_debut_operations.month
        st.info(f"Phase mixte: Construction (Jan à {month_debut_op-1}) puis Exploitation (à partir de {month_debut_op})")

    # --- ÉTAPE 5: Génération du Tableau HTML (similaire à avant, mais utilise `monthly_for_display`) ---
    scenario_name_for_file = results.get("scenario", "default").replace(" ", "_")
    st.markdown(f"#### Flux de Trésorerie Mensuels ({selected_year}) - Scénario: {results.get('scenario', 'N/A')}")
    
    # (La partie CSS et la structure du tableau HTML restent très similaires à votre code existant)
    # Assurez-vous d'utiliser `processed_data_for_table[item_id]['monthly_for_display']` pour les valeurs mensuelles
    # et `processed_data_for_table[item_id]['annual_total']` pour le total annuel dans la boucle de génération HTML.
    # La logique de formatage avec `display_name.strip().startswith("(-)")` pour `abs(val)` reste pertinente.

    table_html_parts = []
    # ... (Copiez votre CSS ici) ...
    table_css_styles = get_table_css('monthly')
    table_html_parts.append(table_css_styles)
    
    header_row_html = "<th>Indicateur</th>" + "".join([f"<th>{col_name}</th>" for col_name in months_display_order + ['Total Année']])
    table_html_parts.append(f"<table class='dataframe-cfs'><thead><tr>{header_row_html}</tr></thead><tbody>")

    for item_cfg_display in config_structure:
        # Gérer les éléments spéciaux (section_header et séparateurs visuels) qui n'ont pas besoin d'ID
        item_type_display = item_cfg_display.get('type', 'data')
        display_name_html = item_cfg_display.get('display_name', '')
        style_class_html = item_cfg_display.get('style_class', '')
        indent_level_html = item_cfg_display.get('indent', 0)
        
        if indent_level_html > 0: style_class_html += f" indent-{indent_level_html}"

        if item_type_display == "section_header":
            colspan_val_html = num_months_to_display + 1 + 1 # Mois + Total Année + Indicateur
            table_html_parts.append(f"<tr class='group-header-cfs {style_class_html}'><td colspan='{colspan_val_html}'>{display_name_html}</td></tr>")
            continue  # Passer à l'élément suivant
            
        if item_type_display in ["visual_separator_subtle", "visual_separator_strong"]:
            colspan_val_html = num_months_to_display + 1 + 1
            sep_class_html = "separator-row-cfs-subtle" if "subtle" in item_type_display else "separator-row-cfs-strong"
            table_html_parts.append(f"<tr class='{sep_class_html} {style_class_html}'><td colspan='{colspan_val_html}'></td></tr>")
            continue  # Passer à l'élément suivant
            
        # Pour les éléments normaux (data, subtotal, etc.), vérifier la présence d'ID
        if 'id' not in item_cfg_display:
            continue  # Ignorer silencieusement (le problème aura déjà été signalé dans les phases précédentes)
            
        item_id_display = item_cfg_display['id']
        
        # Restaurer la valeur par défaut originale pour display_name_html
        display_name_html = item_cfg_display.get('display_name', item_id_display)
        
        # Vérifier que l'ID existe dans les données traitées
        if item_id_display not in processed_data_for_table:
            continue  # Ignorer silencieusement (le problème aura déjà été signalé dans les phases précédentes)
            
        row_cells_html_list = [f"<td style='text-align:left;' class='{style_class_html}'>{display_name_html}</td>"]
        
        # Utiliser 'monthly_for_display' pour l'affichage des valeurs mensuelles
        monthly_values_to_render = processed_data_for_table[item_id_display]['monthly_for_display']
        annual_total_to_render = processed_data_for_table[item_id_display]['annual_total']

        is_special_balance_or_total = item_type_display in ['cash_balance_opening', 'cash_balance_closing', 'calculated_balance_item'] or \
                                      item_cfg_display.get('purpose') in ['fte_total', 'fti_total', 'ftf_total', 'net_cash_variation'] or \
                                      item_type_display == "main-total" # ou une classe spécifique si vous l'utilisez pour cela

        for val_month_render in monthly_values_to_render:
            val_to_format_render = val_month_render
            # Si le libellé commence par "(-)" et que ce n'est pas un solde/total spécial,
            # et que la valeur est négative, afficher la valeur absolue.
            if display_name_html.strip().startswith("(-)") and \
               not is_special_balance_or_total and \
               isinstance(val_month_render, (int, float)) and val_month_render < 0:
                val_to_format_render = abs(val_month_render)
            
            formatted_val_html = format_value(val_to_format_render, '', 0, "-")
            row_cells_html_list.append(f"<td>{formatted_val_html}</td>")
        
        annual_val_to_format_render = annual_total_to_render
        if display_name_html.strip().startswith("(-)") and \
           not is_special_balance_or_total and \
           isinstance(annual_total_to_render, (int, float)) and annual_total_to_render < 0:
            annual_val_to_format_render = abs(annual_total_to_render)

        formatted_annual_html = format_value(annual_val_to_format_render, '', 0, "-")
        row_cells_html_list.append(f"<td>{formatted_annual_html}</td>")
        table_html_parts.append(f"<tr class='{style_class_html}'>{''.join(row_cells_html_list)}</tr>")

    table_html_parts.append("</tbody></table>")
    st.markdown("".join(table_html_parts), unsafe_allow_html=True)

    # --- Export Functionality (similaire, mais s'assurer qu'elle utilise les bonnes données) ---
    export_data_list_final = []
    export_index_names_final = []
    for item_cfg_export_final in config_structure:
        # Vérifier d'abord le type de l'élément
        item_type_export_final = item_cfg_export_final.get('type', 'data')
        
        # Ignorer les types qui n'ont pas d'ID ou qui ne sont pas pertinents pour l'export
        if item_type_export_final in ["section_header", "visual_separator_subtle", "visual_separator_strong"]:
            continue
            
        # Utiliser .get() pour récupérer l'ID de manière sécurisée
        item_id_export_final = item_cfg_export_final.get('id')
        
        # Vérifier que l'ID est présent et non vide
        if not item_id_export_final:
            logger.warning(f"AVERTISSEMENT EXPORT: Élément sans 'id' ou avec 'id' vide trouvé dans config_structure: {item_cfg_export_final}")
            continue # Ignorer cet élément pour l'export
            
        # Vérifier que l'ID existe dans les données traitées
        if item_id_export_final in processed_data_for_table:
            export_index_names_final.append(item_cfg_export_final.get('display_name', item_id_export_final))
            # Pour l'export, utiliser 'raw_monthly_for_calc' car ce sont les valeurs "comptables"
            row_data_export_final = processed_data_for_table[item_id_export_final]['raw_monthly_for_calc'] + \
                                   [processed_data_for_table[item_id_export_final]['annual_total']]
            export_data_list_final.append(row_data_export_final)

    if export_data_list_final:
        df_export_final = pd.DataFrame(export_data_list_final, index=export_index_names_final, columns=months_display_order + ['Total Année'])
        
        # Ajout du nom de l'index pour éviter "Unnamed: 0" dans l'export
        df_export_final.index.name = "Indicateur"
        
        st.markdown("###### Exporter les flux de trésorerie mensuels :", unsafe_allow_html=True)
        # ... (votre code d'export Excel/CSV peut rester ici, s'il utilise df_export_final) ...
        export_col1, export_col2 = st.columns([1,1])
        export_format_final = "Excel" 
        with export_col1:
            export_format_final = st.radio(
                "Format:", ["Excel", "CSV"], index=0,
                key=f"export_format_cf_revised_{selected_year}_{scenario_name_for_file}", horizontal=True, label_visibility="collapsed"
            )
        with export_col2:
            if export_format_final == "Excel":
                excel_buffer_final = io.BytesIO()
                with pd.ExcelWriter(excel_buffer_final, engine='xlsxwriter') as writer_final:
                    df_export_final.to_excel(writer_final, sheet_name=f'Flux_Mois_{selected_year}')
                excel_buffer_final.seek(0)
                st.download_button(label="📥 Télécharger Excel", data=excel_buffer_final,
                                   file_name=f"Flux_Tresorerie_Mensuels_Rev_{scenario_name_for_file}_{selected_year}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   key=f"dl_excel_cf_revised_{selected_year}_{scenario_name_for_file}")
            else: # CSV
                csv_data_final = df_export_final.to_csv(sep=';', decimal=',', encoding='utf-8-sig')
                st.download_button(label="📥 Télécharger CSV", data=csv_data_final,
                                   file_name=f"Flux_Tresorerie_Mensuels_Rev_{scenario_name_for_file}_{selected_year}.csv",
                                   mime="text/csv",
                                   key=f"dl_csv_cf_revised_{selected_year}_{scenario_name_for_file}")
    else:
        st.info("Aucune donnée à exporter pour les flux de trésorerie (version révisée).")
        
    # ... (vos notes de bas de page) ...
    service_dette_total = monthly_df_full['Service_Dette'].sum() if 'Service_Dette' in monthly_df_full.columns else 0
    st.markdown(f"""
    <div style='font-size: 0.8em; color: #555; margin-top:15px;'>
    <strong>Notes :</strong>
    <ul>
        <li>FTE : Flux de Trésorerie d'Exploitation (inclut les intérêts de la dette)</li>
        <li>FTI : Flux de Trésorerie d'Investissement</li>
        <li>FTF : Flux de Trésorerie de Financement (inclut le remboursement du principal)</li>
        <li><strong>Service de la dette total</strong> : Principal + Intérêts = {service_dette_total:,.0f}€ sur la période</li>
        <li>Les valeurs OPEX et TURPE sont affichées HT. Les impôts sont les impôts sur les sociétés décaissés (acomptes/solde).</li>
        <li>La variation de BFR d'exploitation est une estimation et peut nécessiter une analyse plus fine.</li>
        <li>Le solde de trésorerie d'ouverture de la première année de simulation est supposé être à zéro (ou basé sur le capex initial et financement).</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)