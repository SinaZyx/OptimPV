# modules/financial_summary_table.py

import streamlit as st
import pandas as pd
import numpy as np
import io
import json
import os
import traceback
from datetime import datetime
from collections import OrderedDict

# --- Configuration Path ---
CONFIG_DIR = "config"
TABLE_MAP_FILE = os.path.join(CONFIG_DIR, "financial_table_map.json")

# --- Global variable to cache the loaded map ---
_table_map_cache = None

def load_table_map():
    """Loads the table mapping configuration from the JSON file."""
    global _table_map_cache
    # Force reload for debugging or if needed - comment out cache logic temporarily if issues persist
    # _table_map_cache = None # Uncomment this line to always reload the JSON
    if _table_map_cache is not None:
        if isinstance(_table_map_cache, dict) and _table_map_cache:
            # print("DEBUG TABLE: Using cached table map.") # Uncomment if needed
            return _table_map_cache
        else:
             _table_map_cache = None

    effective_path = TABLE_MAP_FILE
    if not os.path.exists(effective_path):
        # Try relative path from script location
        script_dir = os.path.dirname(__file__)
        # Path assumes config is one level up from where financial_summary_table.py is (e.g., root/config, root/modules)
        alt_path = os.path.join(script_dir, "..", CONFIG_DIR, os.path.basename(TABLE_MAP_FILE))
        alt_path = os.path.normpath(alt_path) # Normalize path separators
        # print(f"INFO TABLE: Checking alternative path: {alt_path}") # Debug path
        if os.path.exists(alt_path):
             effective_path = alt_path
        else:
             st.error(f"Fichier de configuration du tableau introuvable: Ni à '{TABLE_MAP_FILE}' ni à '{alt_path}'")
             return None

    try:
        # print(f"TABLE_DEBUG: Chargement de {effective_path}") # Uncomment if needed
        with open(effective_path, 'r', encoding='utf-8') as f:
            loaded_map = json.load(f)
        if not isinstance(loaded_map, dict):
             raise ValueError("Le fichier JSON ne contient pas un dictionnaire valide.")
        for key, info in loaded_map.items():
             if not isinstance(info, dict) or "display_name" not in info or "group" not in info:
                  raise ValueError(f"Entrée invalide dans le JSON pour la clé '{key}'. 'display_name' et 'group' sont requis.")

        _table_map_cache = loaded_map
        # print("TABLE_DEBUG: Mapping chargé avec succès.") # Uncomment if needed
        return _table_map_cache
    except json.JSONDecodeError as e:
        st.error(f"Erreur de décodage JSON dans {effective_path}: {e}")
        return None
    except Exception as e:
        st.error(f"Erreur lors du chargement de {effective_path}: {e}")
        return None

def format_value(value, unit='€', decimals=0, default_na="N/A"):
    """Formate une valeur numérique avec unité et décimales, gère NaN/None/Inf."""
    if pd.isna(value) or value is None or not np.isfinite(value):
        # Gérer explicitement l'infini pour le DSCR moyen si aucune dette
        if isinstance(value, float) and np.isinf(value) and unit is None : # unit is None often used for DSCR
             return "+∞" # Symbole infini
        return default_na
    try:
        # Gérer le cas spécifique des pourcentages
        if unit == '%':
            format_str = f"{{:,.{decimals}f}}%"
            return format_str.format(value)

        # Gérer les autres unités ou l'absence d'unité
        format_str = f"{{:,.{decimals}f}}"
        formatted_value = format_str.format(value)

        if unit is None or unit == "":
             return formatted_value # Pas d'unité
        elif unit == '€':
            return f"{formatted_value} €" # Espace avant €
        elif unit == 'kWh':
             return f"{formatted_value} kWh" # Espace avant kWh
        else:
             return f"{formatted_value} {unit}" # Espace avant l'unité générique

    except (ValueError, TypeError):
        # print(f"AVERTISSEMENT format_value: Impossible de formater {value} avec unit={unit}, decimals={decimals}") # Uncomment if needed
        return str(value) # Fallback

# --- NOUVELLE FONCTION ---
def display_project_summary(results: dict, table_map: dict):
    """Affiche le récapitulatif global du projet."""
    st.markdown("#### Récapitulatif Global du Projet")

    if not results or not isinstance(results, dict):
        st.warning("Données de résultats invalides pour le récapitulatif.")
        return

    # Utiliser .get pour la robustesse, même si config est généralement là
    config_globale = st.session_state.get('config', {})
    monthly_df = results.get('monthly_data')

    # --- Affichage des KPIs Globaux Clés ---
    st.markdown("##### Indicateurs Clés Globaux (sur toute la durée)")
    col1, col2, col3, col4 = st.columns(4)

    # Récupérer les KPIs globaux du dictionnaire 'results'
    npv_proj_glob = results.get('npv_project')
    irr_proj_glob = results.get('irr_project')
    lcoe_glob = results.get('lcoe')
    payback_proj_glob = results.get('payback_project')
    dscr_moyen_glob = results.get('avg_dscr')
    tx_autoprod_moyen_glob = results.get('autoproduction_rate') # Autoconso / Prod
    tx_autoconso_moyen_glob = results.get('autoconsumption_rate') # Autoconso / Conso
    capex_glob = results.get('capex_scenario_simule')
    subvention_glob = results.get('total_subvention')

    with col1:
        st.metric("VAN Projet", format_value(npv_proj_glob, '€', 0), help="Valeur Actuelle Nette du projet global (actualisée au WACC)")
        st.metric("TRI Projet", format_value(irr_proj_glob * 100 if irr_proj_glob is not None else None, '%', 1, default_na="-"), help="Taux de Rentabilité Interne du projet global (avant financement)")
    with col2:
        st.metric("LCOE", format_value(lcoe_glob, '€/kWh', 4, default_na="-"), help="Coût actualisé de l'énergie produite (€/kWh)")
        st.metric("Payback Projet", f"{format_value(payback_proj_glob, '', 1, default_na='-')} ans", help="Temps pour récupérer l'investissement initial par les flux opérationnels")
    with col3:
        st.metric("DSCR Moyen", format_value(dscr_moyen_glob, '', 2, default_na="-"), help="Ratio moyen de couverture du service de la dette")
        st.metric("Taux Autoprod. Moyen", format_value(tx_autoprod_moyen_glob * 100 if tx_autoprod_moyen_glob is not None else None, '%', 1, default_na="-"), help="Moyenne: Autoconso / Production Totale")
    with col4:
        st.metric("Taux Autoconso. Moyen", format_value(tx_autoconso_moyen_glob * 100 if tx_autoconso_moyen_glob is not None else None, '%', 1, default_na="-"), help="Moyenne: Autoconso / Consommation Totale")
        st.metric("CAPEX Projet", format_value(capex_glob, '€', 0), help="Investissement initial brut pour ce scénario")
        st.metric("Subvention Totale", format_value(subvention_glob, '€', 0), help="Prime à l'investissement calculée")

    st.markdown("---")
    st.markdown("##### Agrégats sur la Durée du Projet")

    if monthly_df is None or monthly_df.empty:
        st.warning("Données mensuelles non disponibles pour les agrégats.")
        return

    summary_data = []
    # Inclure tous les groupes (Projet et Equity) pour voir les agrégats
    # Ou filtrer si on veut un récap STRICTEMENT projet
    # project_group_prefixes = ("1.", "2.", "3.") # Décommenter pour filtrer

    # Identifier les indicateurs et leur caractère additif
    metrics_to_aggregate = {}
    for key, info in table_map.items():
        # Vérifier si la colonne existe dans le df mensuel
        # ET si elle appartient aux groupes projet (si on filtre)
        # group_ok = info.get("group", "").startswith(project_group_prefixes) # Décommenter pour filtrer
        group_ok = True # Pour l'instant, agréger tout
        if key in monthly_df.columns and group_ok :
            metrics_to_aggregate[key] = {
                "display_name": info.get("display_name", key),
                "is_additive": info.get("is_additive", False),
                "unit": info.get("unit"),
                "decimals": info.get("decimals", 0),
                "group": info.get("group") # Garder le groupe pour trier le tableau final
            }

    # Calculer les agrégats
    aggregated_values = {}
    for key, info in metrics_to_aggregate.items():
        values = monthly_df[key].dropna()
        agg_value = np.nan # Défaut
        if not values.empty:
            if info["is_additive"]:
                agg_value = values.sum()
            else:
                # Pour les non-additifs (soldes, ratios mensuels non pertinents ici)
                # Prenons la dernière valeur pour les soldes
                if "Solde" in info["display_name"]:
                     agg_value = values.iloc[-1]
                # Pour les ratios, on pourrait calculer une moyenne pondérée ou simple,
                # mais les KPIs globaux (DSCR moyen, Taux moyens) sont déjà affichés.
                # On peut choisir de ne pas afficher d'agrégat pour les ratios ici.
                # else:
                #    agg_value = values.mean() # Exemple: moyenne simple si ce n'est pas un solde

        aggregated_values[info["display_name"]] = {
            "value": agg_value,
            "unit": info["unit"],
            "decimals": info["decimals"],
            "group": info["group"],
            "type": "Total Cumulé" if info["is_additive"] else ("Valeur Finale" if "Solde" in info["display_name"] else "N/A")
        }

    # Organiser les résultats par groupe pour l'affichage
    final_summary_list = []
    # Trier d'abord par groupe, puis potentiellement par nom d'indicateur
    sorted_display_names = sorted(aggregated_values.keys(), key=lambda name: aggregated_values[name]["group"])

    for display_name in sorted_display_names:
        data = aggregated_values[display_name]
        # Ne pas afficher les lignes où la valeur agrégée est NaN (typiquement les ratios non additifs)
        if pd.notna(data["value"]):
            final_summary_list.append({
                "Groupe": data["group"],
                "Indicateur": display_name,
                "Valeur Agrégée": format_value(data["value"], data["unit"], data["decimals"]),
                "Type Agrégat": data["type"]
            })


    if final_summary_list:
        df_summary = pd.DataFrame(final_summary_list)
        st.dataframe(df_summary, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun indicateur projet à agréger trouvé ou calculable.")

# --- Fonction Principale Modifiée ---
def display_financial_summary_table(results: dict | None):
    """Affiche un tableau de synthèse financière amélioré ou un récapitulatif projet."""
    # Section inchangée: Vérifications initiales et chargement table_map
    if results is None or not isinstance(results, dict) or 'monthly_data' not in results:
        st.warning("Données mensuelles non disponibles pour l'affichage.")
        return

    monthly_df_raw = results.get('monthly_data')
    if not isinstance(monthly_df_raw, pd.DataFrame):
        st.warning("DataFrame mensuel invalide.")
        return

    table_map = load_table_map()
    if table_map is None:
        st.error("Impossible d'afficher le tableau sans configuration de mapping valide.")
        return

    # Titre général
    st.markdown("### Analyse Financière") # Titre simplifié

    # --- Initialisation et Gestion de l'État d'Affichage ---
    if 'view_mode' not in st.session_state:
        st.session_state['view_mode'] = 'annual' # Par défaut : vue annuelle

    # Callbacks pour changer de vue
    def set_view_mode(mode):
        st.session_state['view_mode'] = mode

    def set_annual_view(year):
        st.session_state['view_mode'] = 'annual'
        st.session_state['active_year'] = year

    # --- Création des Boutons de Navigation ---
    st.markdown("###### Options d'Affichage", unsafe_allow_html=True)
    nav_cols = st.columns(7) # Ajuster le nombre de colonnes si besoin

    with nav_cols[0]:
        st.button("📈 Récap. Projet", key="btn_recap", on_click=set_view_mode, args=('project_summary',), help="Afficher le résumé global du projet")

    years_in_data = []
    if not monthly_df_raw.empty and isinstance(monthly_df_raw.index, pd.DatetimeIndex):
         years_in_data = sorted(monthly_df_raw.index.year.unique())

    if not years_in_data:
         with nav_cols[1]:
             st.caption("Aucune année")
    else:
        num_year_buttons = min(len(years_in_data), 5) # Limiter à 5 boutons année
        for i in range(num_year_buttons):
            year = years_in_data[i]
            with nav_cols[i+1]: # Commencer à la colonne 1
                 st.button(f"{year}", key=f"year_nav_{year}", on_click=set_annual_view, args=(year,))
        # Ajouter un selectbox si plus de 5 années
        if len(years_in_data) > 5:
             with nav_cols[6]: # Dernière colonne
                  other_years = years_in_data[5:]
                  # Utiliser une clé unique et une fonction de formatage
                  selected_other_year = st.selectbox(
                       "Autres:", options=other_years, index=None, # Pas de sélection par défaut
                       label_visibility="collapsed", # Cacher le label "Autres:"
                       key="select_other_year", format_func=lambda y: str(y),
                       placeholder="Année..."
                  )
                  if selected_other_year is not None:
                       # Mettre à jour l'année active et la vue si une sélection est faite
                       set_annual_view(selected_other_year)
                       # Optionnel: réinitialiser le selectbox après sélection
                       st.session_state['select_other_year'] = None
                       st.rerun() # Forcer le re-rendu pour afficher l'année sélectionnée

    # Bouton "Tout développer" (uniquement en vue annuelle)
    expand_all = False
    if st.session_state.get('view_mode') == 'annual':
         # Placer ce bouton sous la navigation pour ne pas prendre trop de place en largeur
         expand_all = st.checkbox("Afficher toutes les années détaillées", value=False, key="expand_all")

    st.markdown("---") # Séparateur après navigation

    # --- Affichage Conditionnel ---
    if st.session_state['view_mode'] == 'project_summary':
        display_project_summary(results, table_map)

    elif st.session_state['view_mode'] == 'annual':
        if monthly_df_raw.empty:
             st.warning("Données mensuelles vides, impossible d'afficher le détail annuel.")
             return # Sortir proprement

        # --- Début de la logique d'affichage annuel (adaptée) ---
        try:
            # Préparation initiale du DataFrame et Pivot (moins de modifications ici)
            df_pivot_source = monthly_df_raw.copy()
            if not isinstance(df_pivot_source.index, pd.DatetimeIndex):
                 try: df_pivot_source.index = pd.to_datetime(df_pivot_source.index)
                 except Exception as e_date: st.error(f"Erreur conversion index date: {e_date}"); return

            df_pivot_source['Year'] = df_pivot_source.index.year
            df_pivot_source['MonthNum'] = df_pivot_source.index.month
            # Utiliser les 3 premières lettres et capitaliser la première
            df_pivot_source['MonthName'] = df_pivot_source.index.strftime('%b').str.capitalize()

            # --- Mapping et Pivot (Identique) ---
            metrics_map = {orig_key: info.get("display_name", orig_key) for orig_key, info in table_map.items()}
            original_cols_available = list(df_pivot_source.columns)
            original_cols_to_use = [key for key in table_map.keys() if key in original_cols_available]
            missing_keys = list(set(table_map.keys()) - set(original_cols_to_use))
            if missing_keys: st.warning(f"Indicateurs configurés mais non trouvés dans les données: {missing_keys}")
            if not original_cols_to_use: st.error("Aucun indicateur configuré trouvé dans les données."); return

            base_cols = ['Year', 'MonthNum', 'MonthName']
            cols_to_select_present = [col for col in (base_cols + original_cols_to_use) if col in df_pivot_source.columns]
            df_pivot_source_filtered = df_pivot_source[cols_to_select_present].copy()

            rename_map_filtered = {orig_col: metrics_map[orig_col] for orig_col in original_cols_to_use if orig_col in cols_to_select_present}
            df_pivot_source_filtered = df_pivot_source_filtered.rename(columns=rename_map_filtered)

            valid_display_names = list(rename_map_filtered.values())
            df_melted = df_pivot_source_filtered.melt(
                id_vars=['Year', 'MonthNum', 'MonthName'], value_vars=valid_display_names,
                var_name='Indicateur', value_name='Valeur'
            )
            df_pivoted = pd.pivot_table(
                df_melted, values='Valeur', index=['Year', 'Indicateur'],
                columns=['MonthNum', 'MonthName'], aggfunc='sum' # 'sum' est généralement correct pour agréger les mois
            )
            # S'assurer que les mois sont dans le bon ordre (Jan, Fev, ...)
            month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            # Ne garder que les colonnes mois présentes dans les données
            actual_month_columns = [m for m in month_order if m in df_pivoted.columns.get_level_values('MonthName')]
            df_pivoted = df_pivoted.reindex(actual_month_columns, axis=1, level='MonthName')
            # Applatir les colonnes multi-index si une seule année est présente
            if len(years_in_data) == 1:
                 df_pivoted.columns = df_pivoted.columns.get_level_values('MonthName')
            else:
                 # Garder le multi-index mois, trier par numéro de mois
                 df_pivoted = df_pivoted.sort_index(axis=1, level='MonthNum')
                 # Utiliser uniquement MonthName comme nom de colonne
                 df_pivoted.columns = df_pivoted.columns.get_level_values('MonthName')


            # --- Calcul Totaux Annuels Additifs (Identique) ---
            numeric_month_cols = list(df_pivoted.columns) # Utiliser les colonnes actuelles après tri
            df_pivoted['Total Annuel'] = np.nan
            additive_indices_display = [
                info["display_name"] for key, info in table_map.items() if info.get("is_additive", False) and key in original_cols_to_use
            ]
            valid_additive_indices_pivoted = df_pivoted.index.get_level_values('Indicateur').unique().intersection(additive_indices_display)
            # Utiliser skipna=True pour que le total ignore les NaN
            df_pivoted.loc[pd.IndexSlice[:, valid_additive_indices_pivoted], 'Total Annuel'] = df_pivoted.loc[pd.IndexSlice[:, valid_additive_indices_pivoted], numeric_month_cols].sum(axis=1, skipna=True)

            # --- Affichage par Année ---
            config_globale = st.session_state.get('config', {})
            if not years_in_data:
                st.info("Aucune donnée à afficher pour la vue annuelle.")
                return

            # Boucle d'affichage des années
            for year in years_in_data:
                # Utiliser st.session_state.get pour éviter KeyError
                is_active = st.session_state.get('active_year') == year
                with st.expander(f"Année {year}", expanded=(expand_all or is_active)):
                    try:
                        # Sélectionner l'année et supprimer le niveau 'Year' de l'index
                        # Gérer le cas où il n'y a qu'une seule année
                        if isinstance(df_pivoted.index, pd.MultiIndex):
                             df_year = df_pivoted.loc[pd.IndexSlice[year,:],:].droplevel('Year')
                        else: # Si une seule année, l'index n'est plus multi-index
                             df_year = df_pivoted

                        # --- Recalculs et Logique interne de l'expander (identique à votre dernière version) ---
                        # === DEBUT SECTION MODIFIÉE ===
                        # --- Calcul Totaux Annuels Dérivés (Non Additifs) ---
                        try:
                            # Fonction helper interne (identique)
                            def get_annual_total(df, display_key, default=np.nan):
                                if display_key in df.index and 'Total Annuel' in df.columns:
                                    val = df.loc[display_key, 'Total Annuel']
                                    return val if pd.notna(val) and np.isfinite(val) else default
                                return default
 
                            # 1. CALCULER EXPLICITEMENT les totaux annuels des composants P&L clés (non additifs)
                            pnl_keys_to_sum = [
                                'EBITDA (€)', 'EBIT (€)', 'EBT (€)', 'Résultat Net (€)',
                                'OCF Projet (€)', 'Free Cash Flow Equity (€)'
                            ]
                            for key in pnl_keys_to_sum:
                                if key in df_year.index:
                                    # Somme des mois pour cette année, ignorant les NaN
                                    annual_sum_val = df_year.loc[key, numeric_month_cols].sum(skipna=True)
                                    df_year.loc[key, 'Total Annuel'] = annual_sum_val
                                # else: st.warning(f"Clé PNL {key} non trouvée pour calcul total an {year}") # Debug si besoin
 
                            # 2. LIRE les totaux (additifs ou ceux juste calculés) pour les dépendances
                            #    Utilisation de get_annual_total qui gère les NaN/Inf
                            revenus_an = get_annual_total(df_year, 'Revenus Totaux (€)') # Additif
                            ebitda_an = get_annual_total(df_year, 'EBITDA (€)')      # Non-additif, calculé en étape 1
                            amort_an = get_annual_total(df_year, 'Amortissement (€)')  # Additif
                            interets_an = get_annual_total(df_year, 'Intérêts Payés (€)') # Additif
                            impots_prov_an = get_annual_total(df_year, 'Impôts Prov. (€)')# Additif
                            principal_an = get_annual_total(df_year, 'Principal Remb. (€)')# Additif
                            service_dette_an = get_annual_total(df_year, 'Service Dette (€)') # Additif
 
                            # 3. VERIFIER/RAFFINER certains totaux (optionnel mais peut améliorer cohérence)
                            #    Par exemple, recalculer EBIT basé sur EBITDA et Amort annuels
                            if pd.notna(ebitda_an) and pd.notna(amort_an):
                                df_year.loc['EBIT (€)', 'Total Annuel'] = ebitda_an - amort_an
                            #    Recalculer EBT basé sur EBIT et Intérêts annuels
                            ebit_an = get_annual_total(df_year, 'EBIT (€)') # Relire après recalcul potentiel
                            if pd.notna(ebit_an) and pd.notna(interets_an):
                                df_year.loc['EBT (€)', 'Total Annuel'] = ebit_an - interets_an
                            #    Recalculer Résultat Net
                            ebt_an = get_annual_total(df_year, 'EBT (€)') # Relire après recalcul potentiel
                            if pd.notna(ebt_an) and pd.notna(impots_prov_an):
                                df_year.loc['Résultat Net (€)', 'Total Annuel'] = ebt_an - impots_prov_an
                            #    Recalculer FCFE
                            rn_an = get_annual_total(df_year, 'Résultat Net (€)') # Relire
                            if pd.notna(rn_an) and pd.notna(amort_an) and pd.notna(principal_an):
                                 df_year.loc['Free Cash Flow Equity (€)', 'Total Annuel'] = rn_an + amort_an - principal_an
                            #    Recalculer OCF Projet (Formule: EBITDA * (1-T) + Amort * T)
                            tx_impot = config_globale.get('taux_imposition', 25.0) / 100.0
                            if pd.notna(ebitda_an) and pd.notna(amort_an) and pd.notna(tx_impot):
                                 df_year.loc['OCF Projet (€)', 'Total Annuel'] = (ebitda_an * (1.0 - tx_impot)) + (amort_an * tx_impot)
 
                            # 4. Calculer Total Annuel pour Solde Dette Fin (dernière valeur non nulle)
                            if 'Solde Dette Fin (€)' in df_year.index:
                                 last_val = df_year.loc['Solde Dette Fin (€)', numeric_month_cols].dropna().iloc[-1] if not df_year.loc['Solde Dette Fin (€)', numeric_month_cols].dropna().empty else np.nan
                                 df_year.loc['Solde Dette Fin (€)', 'Total Annuel'] = last_val
 
                        except KeyError as ke: st.warning(f"Année {year}: Indicateur clé manquant pour calcul total annuel ({ke}).")
                        except Exception as e_calc_deriv: st.warning(f"Année {year}: Erreur calcul totaux dérivés: {e_calc_deriv}")
                        # === FIN SECTION MODIFIÉE ===

                        # --- Calcul Mensuel + Annuel Ratios ---
                        indicators_ratios_def = [
                            ("Taux Autoconso (%)", lambda auto, prod: (auto / prod * 100) if prod > 1e-6 else 0.0, ['Autoconsommation_kWh', 'Production_kWh']),
                            ("Taux Autoprod (%)", lambda auto, conso: (auto / conso * 100) if conso > 1e-6 else 0.0, ['Autoconsommation_kWh', 'Consommation_kWh']),
                            ("Marge EBITDA (%)", lambda ebitda, revenus: (ebitda / revenus * 100) if revenus > 1e-6 else 0.0, ['EBITDA', 'Revenus_Total']),
                            ("DSCR", lambda ebitda, impots, service: ((ebitda - impots) / service) if service > 1e-6 else np.inf, ['EBITDA', 'Impots_Provisionnes', 'Service_Dette'])
                        ]
                        ratio_group_name = "4. RATIOS CLÉS"

                        for display_name_ratio, calc_lambda, component_keys in indicators_ratios_def:
                            component_display_names = [table_map.get(k, {}).get("display_name", k) for k in component_keys]
                            if display_name_ratio not in df_year.index: df_year.loc[display_name_ratio] = np.nan
                            for month in numeric_month_cols:
                                try:
                                    comp_values = [df_year.loc[disp_name, month] for disp_name in component_display_names if disp_name in df_year.index]
                                    if len(comp_values) == len(component_display_names) and all(pd.notna(v) and np.isfinite(v) for v in comp_values):
                                        df_year.loc[display_name_ratio, month] = calc_lambda(*comp_values)
                                    else: df_year.loc[display_name_ratio, month] = np.nan
                                except (KeyError, IndexError): df_year.loc[display_name_ratio, month] = np.nan
                                except Exception: df_year.loc[display_name_ratio, month] = np.nan
                            try:
                                comp_values_annual = [get_annual_total(df_year, disp_name, np.nan) for disp_name in component_display_names]
                                if all(pd.notna(v) and np.isfinite(v) for v in comp_values_annual):
                                    df_year.loc[display_name_ratio, 'Total Annuel'] = calc_lambda(*comp_values_annual)
                                else: df_year.loc[display_name_ratio, 'Total Annuel'] = np.nan
                            except (KeyError, IndexError): df_year.loc[display_name_ratio, 'Total Annuel'] = np.nan
                            except Exception: df_year.loc[display_name_ratio, 'Total Annuel'] = np.nan

                        # --- Réorganisation Index basée sur les groupes ---
                        grouped_indicators = OrderedDict()
                        display_name_to_info = {info["display_name"]: info for info in table_map.values()}
                        # Définition correcte du dictionnaire
                        default_ratio_infos = {
                            "Taux Autoconso (%)": {"unit": "%", "decimals": 1, "group": "3. PROJET : Service Dette & Ratios Associés", "tooltip": "Autoconso / Production"},
                            "Taux Autoprod (%)": {"unit": "%", "decimals": 1, "group": "3. PROJET : Service Dette & Ratios Associés", "tooltip": "Autoconso / Consommation"},
                            "Marge EBITDA (%)": {"unit": "%", "decimals": 1, "group": "2. PROJET : Coûts & Rentabilité Opérationnelle", "tooltip": "EBITDA / Revenus Totaux"},
                            "DSCR": {"unit": None, "decimals": 2, "group": "3. PROJET : Service Dette & Ratios Associés", "tooltip": "Ratio de Couverture du Service Dette ((EBITDA-Impots)/Service Dette)"}
                        }

                        for name_ratio, info_ratio in default_ratio_infos.items():
                            if name_ratio not in display_name_to_info: display_name_to_info[name_ratio] = info_ratio

                        all_indicator_keys = list(table_map.keys()) + list(default_ratio_infos.keys())
                        processed_display_names = set()

                        for internal_key in all_indicator_keys:
                             display_name = table_map.get(internal_key, {}).get("display_name", internal_key)
                             if display_name in df_year.index and display_name not in processed_display_names:
                                 info = display_name_to_info.get(display_name, {})
                                 group = info.get("group", "9. Autre")
                                 if group not in grouped_indicators: grouped_indicators[group] = []
                                 grouped_indicators[group].append(display_name)
                                 processed_display_names.add(display_name)

                        grouped_indicators = OrderedDict(sorted(grouped_indicators.items()))
                        final_order = [item for group_list in grouped_indicators.values() for item in group_list]
                        df_year_final = df_year.loc[df_year.index.intersection(final_order)].reindex(final_order)

                        # --- Affichage KPIs Annuels ---
                        st.markdown("#### Indicateurs clés de l'année")
                        kpis_display = [
                             {"display_name": "Production (kWh)", "unit": "kWh", "icon": "☀️"},
                             {"display_name": "Taux Autoconso (%)", "unit": "%", "icon": "🔄", "threshold_key": "kpi_threshold_autoconso"},
                             {"display_name": "Revenus Totaux (€)", "unit": "€", "icon": "💰"},
                             {"display_name": "EBITDA (€)", "unit": "€", "icon": "📊"},
                             {"display_name": "DSCR", "unit": None, "icon": "🔒", "threshold_key": "target_dscr"}
                        ]
                        kpi_cols = st.columns(len(kpis_display))
                        for i, kpi in enumerate(kpis_display):
                             with kpi_cols[i]:
                                 kpi_name = kpi["display_name"]
                                 value_kpi = get_annual_total(df_year_final, kpi_name, np.nan)
                                 formatted_kpi = "N/A"; color_kpi = "black"
                                 if pd.notna(value_kpi) and np.isfinite(value_kpi):
                                     seuil_min = config_globale.get(kpi.get("threshold_key", "") + "_min")
                                     seuil_warning = config_globale.get(kpi.get("threshold_key", "") + "_warning")
                                     if kpi["display_name"] == "DSCR" and seuil_min is None: seuil_min = config_globale.get('target_dscr', 1.1)
                                     if kpi["display_name"] == "Taux Autoconso (%)" and seuil_min is None: seuil_min = 30.0; seuil_warning = 50.0

                                     if seuil_min is not None and value_kpi < seuil_min: color_kpi = "red"
                                     elif seuil_warning is not None and value_kpi < seuil_warning: color_kpi = "orange"
                                     elif "(€)" in kpi_name and isinstance(value_kpi, (int, float, np.number)): color_kpi = "green" if value_kpi > 0 else "red"
                                     elif kpi["display_name"] == "DSCR": color_kpi = "green" if value_kpi >= config_globale.get('target_dscr', 1.1) else "red" # Specific DSCR color
                                     else: color_kpi = "green"

                                     info_kpi = display_name_to_info.get(kpi_name, {})
                                     decimals_kpi = info_kpi.get("decimals", 1 if kpi["unit"] == "%" else 2 if kpi["unit"] is None else 0)
                                     formatted_kpi = format_value(value_kpi, kpi["unit"], decimals_kpi)

                                 st.markdown(f'''
                                 <div style="text-align: center; padding: 10px; border-radius: 5px; background-color: #f0f2f6; margin-bottom: 5px; height: 100%;">
                                     <div style="font-size: 24px;">{kpi['icon']}</div>
                                     <div style="font-size: 12px; color: #555; height: 2.5em; overflow: hidden; line-height: 1.2em;">{kpi_name}</div>
                                     <div style="font-size: 16px; font-weight: bold; color: {color_kpi};">{formatted_kpi}</div>
                                 </div>''', unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)

                        # --- Options d'affichage (Détail, Tendances) ---
                        st.markdown("###### Options d'affichage du tableau :", unsafe_allow_html=True)
                        col1_opt, col2_opt = st.columns(2)
                        with col1_opt: detail_level = st.radio("Niveau de détail:", ["Complet", "Essentiel"], index=0, key=f"detail_{year}", horizontal=True)
                        with col2_opt: show_trends = st.checkbox("Afficher tendances Δ%", value=False, key=f"trends_{year}")

                        df_display = df_year_final.copy()
                        if detail_level == "Essentiel":
                             essential_display_names = [
                                 "Production (kWh)", "Autoconso. (kWh)", "Revenus Totaux (€)", "EBITDA (€)",
                                 "Résultat Net (€)", "Free Cash Flow Equity (€)", "DSCR",
                                 "Taux Autoconso (%)", "Marge EBITDA (%)"
                             ]
                             df_display = df_display[df_display.index.isin(essential_display_names)]

                        # --- Construction HTML avec Groupes ---
                        html_rows = []
                        col_names_html = "".join(f"<th>{col}</th>" for col in df_display.columns)
                        html_rows.append(f"<thead><tr><th>Indicateur</th>{col_names_html}</tr></thead>")
                        html_rows.append("<tbody>")
                        current_group = None
                        num_cols = len(df_display.columns) + 1

                        for idx_display_name in df_display.index:
                            row_info = display_name_to_info.get(idx_display_name, {})
                            group_name = row_info.get("group", "9. Autre")
                            unit = row_info.get("unit")
                            decimals = row_info.get("decimals", 0)

                            if group_name != current_group:
                                html_rows.append(f'<tr style="background-color: #e8eaf6; font-weight: bold;"><td colspan="{num_cols}" style="padding: 6px 4px; border-top: 2px solid #aaa; border-bottom: 1px solid #ccc; text-align: left;">{group_name}</td></tr>')
                                current_group = group_name

                            tooltip_text = row_info.get("tooltip", "")
                            cells_html = f'<td title="{tooltip_text}" style="text-align: left;">{idx_display_name}</td>' # Indicateur aligné à gauche

                            for col in df_display.columns:
                                val = df_display.loc[idx_display_name, col]
                                trend_symbol = ""; style = ""; text_align = "right"
                                if show_trends and col != 'Total Annuel' and col != df_display.columns[0]:
                                    try:
                                        prev_col_idx = list(df_display.columns).index(col) - 1
                                        if prev_col_idx >= 0:
                                            prev_col = df_display.columns[prev_col_idx]
                                            prev_val = df_display.loc[idx_display_name, prev_col]
                                            if pd.notna(val) and pd.notna(prev_val) and isinstance(val, (int, float, np.number)) and isinstance(prev_val, (int, float, np.number)) and abs(prev_val) > 1e-9:
                                                 pct_change = (val - prev_val) / abs(prev_val) * 100
                                                 if abs(pct_change) >= 10:
                                                      color = "green" if pct_change > 0 else "red"; arrow = "▲" if pct_change > 0 else "▼" # Flèches alternatives
                                                      trend_symbol = f" <span style='color:{color}; font-size: smaller;'>{arrow}</span>"
                                    except Exception as e_trend: print(f"Trend error: {e_trend}")

                                formatted_val = format_value(val, unit, decimals)
                                if col == 'Total Annuel': style = "font-weight: bold; background-color: #f0f2f6;"
                                cells_html += f'<td style="text-align: {text_align}; {style}">{formatted_val}{trend_symbol}</td>'

                            html_rows.append(f"<tr>{cells_html}</tr>")

                        html_rows.append("</tbody>")
                        # Style CSS pour aligner à gauche la première colonne
                        html_table = f'<style> table.dataframe th {{ text-align: right; padding: 4px 8px; }} table.dataframe td {{ text-align: right; padding: 4px 8px; }} table.dataframe td:first-child, table.dataframe th:first-child {{ text-align: left; }} </style><table class="dataframe" style="width: 100%; border-collapse: collapse;">{"".join(html_rows)}</table>'
                        st.markdown(html_table, unsafe_allow_html=True)


                        # --- Section Export ---
                        st.markdown("---")
                        st.markdown("###### Export des données de l'année :", unsafe_allow_html=True)
                        export_col1, export_col2 = st.columns([1,1])
                        with export_col1: export_format = st.radio("Format:", ["Excel", "CSV"], key=f"export_format_{year}", horizontal=True, label_visibility="collapsed")
                        with export_col2:
                             df_export = df_year_final
                             if export_format == "Excel":
                                  buffer = io.BytesIO()
                                  with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer: df_export.to_excel(writer, sheet_name=f'Annee {year}')
                                  buffer.seek(0)
                                  st.download_button(label="📥 Télécharger Excel", data=buffer, file_name=f"Synthese_Financiere_Annee_{year}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"download_excel_{year}")
                             else:
                                  csv_data = df_export.to_csv(sep=';', decimal=',', encoding='utf-8-sig')
                                  st.download_button(label="📥 Télécharger CSV", data=csv_data, file_name=f"Synthese_Financiere_Annee_{year}.csv", mime="text/csv", key=f"download_csv_{year}")

                    except KeyError as ke:
                         st.error(f"Données manquantes pour l'année {year} dans le tableau pivoté. Vérifiez l'indexation. Détails: {ke}")
                    except Exception as e_expander:
                        st.error(f"Erreur affichage année {year}: {e_expander}")
                        st.exception(traceback.format_exc())

        # --- Fin de la logique d'affichage annuel ---
        except Exception as e_global:
             st.error(f"Erreur globale lors de la préparation ou l'affichage de la vue annuelle: {e_global}")
             st.exception(traceback.format_exc())

    # --- Onglet Données Brutes (Déplacé sous un expander général) ---
    with st.expander("Voir les Données Mensuelles Détaillées"):
        # Titre corrigé ici
        st.markdown("### Tableau des Données Mensuelles (issues de `results['monthly_data']`)")
        if not monthly_df_raw.empty:
            st.dataframe(monthly_df_raw, use_container_width=True)
            st.markdown("#### Résumé Statistique des Données Mensuelles")
            try: st.dataframe(monthly_df_raw.describe(include='all'), use_container_width=True)
            except Exception as e_describe: st.warning(f"Impossible d'afficher le résumé statistique: {e_describe}")
        else:
            st.info("Le DataFrame mensuel brut est vide.")

# --- Fin de la fonction display_financial_summary_table ---