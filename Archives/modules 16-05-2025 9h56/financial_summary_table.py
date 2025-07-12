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

# --- Configuration Path & load_table_map (INCHANGÉ) ---
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
        script_dir = os.path.dirname(__file__)
        alt_path = os.path.join(script_dir, "..", CONFIG_DIR, os.path.basename(TABLE_MAP_FILE))
        alt_path = os.path.normpath(alt_path)
        if os.path.exists(alt_path):
             effective_path = alt_path
        else:
             # Ne pas planter l'app, retourner None et laisser la fonction appelante gérer
             print(f"ERREUR FST: Fichier de configuration du tableau introuvable: Ni à '{TABLE_MAP_FILE}' ni à '{alt_path}'")
             # st.error(...) # Optionnel: Afficher l'erreur dans l'UI
             return None

    try:
        with open(effective_path, 'r', encoding='utf-8') as f:
            loaded_map = json.load(f)
        if not isinstance(loaded_map, dict):
             raise ValueError("Le fichier JSON ne contient pas un dictionnaire valide.")
        for key, info in loaded_map.items():
             if not isinstance(info, dict) or "display_name" not in info or "group" not in info:
                  raise ValueError(f"Entrée invalide dans le JSON pour la clé '{key}'. 'display_name' et 'group' sont requis.")

        _table_map_cache = loaded_map
        return _table_map_cache
    except json.JSONDecodeError as e:
        print(f"ERREUR FST: Erreur de décodage JSON dans {effective_path}: {e}")
        st.error(f"Erreur de format JSON dans {effective_path}: {e}") # Afficher l'erreur
        return None
    except Exception as e:
        print(f"ERREUR FST: Erreur lors du chargement de {effective_path}: {e}")
        st.error(f"Erreur lors du chargement de {effective_path}: {e}") # Afficher l'erreur
        return None

# --- format_value (INCHANGÉ) ---
def format_value(value, unit='€', decimals=0, default_na="N/A"):
    """Formate une valeur numérique avec unité et décimales, gère NaN/None/Inf."""
    if pd.isna(value) or value is None or not np.isfinite(value):
        if isinstance(value, float) and np.isinf(value) and unit is None :
             return "+∞"
        return default_na
    try:
        if unit == '%':
            format_str = f"{{:,.{decimals}f}}%"
            return format_str.format(value)
        format_str = f"{{:,.{decimals}f}}"
        formatted_value = format_str.format(value)
        if unit is None or unit == "": return formatted_value
        elif unit == '€': return f"{formatted_value} €"
        elif unit == 'kWh': return f"{formatted_value} kWh"
        else: return f"{formatted_value} {unit}"
    except (ValueError, TypeError):
        return str(value)

# --- display_project_summary (INCHANGÉ) ---
def display_project_summary(results: dict, table_map: dict):
    """Affiche le récapitulatif global du projet."""
    st.markdown("#### Récapitulatif Global du Projet")

    if not results or not isinstance(results, dict):
        st.warning("Données de résultats invalides pour le récapitulatif.")
        return

    config_globale = st.session_state.get('config', {})
    monthly_df = results.get('monthly_data')

    st.markdown("##### Indicateurs Clés Globaux (sur toute la durée)")
    col1, col2, col3, col4 = st.columns(4)

    npv_proj_glob = results.get('npv_project')
    irr_proj_glob = results.get('irr_project')
    lcoe_glob = results.get('lcoe')
    payback_proj_glob = results.get('payback_project')
    dscr_moyen_glob = results.get('avg_dscr')
    tx_autoprod_moyen_glob = results.get('autoproduction_rate')
    tx_autoconso_moyen_glob = results.get('autoconsumption_rate')
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
        taux_autoconso_pct = tx_autoconso_moyen_glob * 100 if tx_autoconso_moyen_glob is not None else None
        formatted_value_autoconso = format_value(taux_autoconso_pct, '%', 1, default_na="-")
        seuil_alerte_autoconso = 55.0
        is_low = False
        help_text_autoconso = "Moyenne: Autoconso / Consommation Totale."
        if taux_autoconso_pct is not None and np.isfinite(taux_autoconso_pct):
            if taux_autoconso_pct < seuil_alerte_autoconso:
                is_low = True
                help_text_autoconso += f" Un taux inférieur à {seuil_alerte_autoconso}% suggère une faible adéquation entre les profils de production et de consommation. Optimisation possible via stockage ou pilotage des charges."
        st.metric("Taux Autoconso. Moyen", formatted_value_autoconso, help=help_text_autoconso)
        if is_low:
            st.warning(f"Taux potentiellement bas (< {seuil_alerte_autoconso}%)", icon="⚠️")
        st.metric("CAPEX Projet", format_value(capex_glob, '€', 0), help="Investissement initial brut pour ce scénario")
        st.metric("Subvention Totale", format_value(subvention_glob, '€', 0), help="Prime à l'investissement calculée")

    st.markdown("---")
    st.markdown("##### Agrégats sur la Durée du Projet")

    if monthly_df is None or monthly_df.empty:
        st.warning("Données mensuelles non disponibles pour les agrégats.")
        return

    summary_data = []
    metrics_to_aggregate = {}
    for key, info in table_map.items():
        group_ok = True
        if key in monthly_df.columns and group_ok :
            metrics_to_aggregate[key] = {
                "display_name": info.get("display_name", key),
                "is_additive": info.get("is_additive", False),
                "unit": info.get("unit"),
                "decimals": info.get("decimals", 0),
                "group": info.get("group")
            }

    aggregated_values = {}
    for key, info in metrics_to_aggregate.items():
        values = monthly_df[key].dropna()
        agg_value = np.nan
        if not values.empty:
            if info["is_additive"]:
                agg_value = values.sum()
            else:
                if "Solde" in info["display_name"]:
                     agg_value = values.iloc[-1]
        aggregated_values[info["display_name"]] = {
            "value": agg_value,
            "unit": info["unit"],
            "decimals": info["decimals"],
            "group": info["group"],
            "type": "Total Cumulé" if info["is_additive"] else ("Valeur Finale" if "Solde" in info["display_name"] else "N/A")
        }

    final_summary_list = []
    sorted_display_names = sorted(aggregated_values.keys(), key=lambda name: aggregated_values[name]["group"])

    for display_name in sorted_display_names:
        data = aggregated_values[display_name]
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

# --- display_cash_flow_statement (INCHANGÉ - fourni précédemment) ---
def display_cash_flow_statement(results: dict | None):
    """Affiche le tableau des flux de trésorerie mensuels pour une année."""
    st.markdown("#### État des Flux de Trésorerie Mensuels")

    if results is None or not isinstance(results, dict) or 'monthly_data' not in results:
        st.warning("Données mensuelles non disponibles pour les flux de trésorerie.")
        return

    monthly_df_raw = results.get('monthly_data')
    if not isinstance(monthly_df_raw, pd.DataFrame) or monthly_df_raw.empty:
        st.warning("DataFrame mensuel invalide ou vide.")
        return

    df_monthly = monthly_df_raw.copy()
    if not isinstance(df_monthly.index, pd.DatetimeIndex):
        try:
            df_monthly.index = pd.to_datetime(df_monthly.index)
        except Exception as e:
            st.error(f"Impossible de convertir l'index en DatetimeIndex: {e}")
            return

    available_years = sorted(df_monthly.index.year.unique())
    if not available_years:
        st.warning("Aucune année disponible dans les données.")
        return

    # Utiliser une clé unique pour le selectbox de l'année
    selected_year = st.selectbox("Choisir l'année à afficher :", available_years, index=0, key="year_select_cashflow")

    df_year_filtered = df_monthly[df_monthly.index.year == selected_year].copy()

    cf_index = [
        "COLLECTIONS", "Apport Fonds Propres", "Levée de Dette", "Revenus Client", "Total Collections",
        "DISBURSEMENTS", "Investissements (CAPEX Initial)", "OPEX Total", "Paiement IS (Acomptes)", "Remboursement Prêt (Principal + Intérêts)", "Total Décaissements",
        "Variation Trésorerie", "Solde Trésorerie Début", "Solde Trésorerie Fin"
    ]
    months = list(range(1, 13))
    cf_statement_df = pd.DataFrame(0.0, index=cf_index, columns=months)

    equity_inflow = results.get('net_equity_investment', 0)
    debt_inflow = results.get('debt_amount', 0)
    initial_capex_outflow = results.get('capex_scenario_simule', 0)

    cf_statement_df.loc["Apport Fonds Propres", 1] = equity_inflow
    cf_statement_df.loc["Levée de Dette", 1] = debt_inflow
    cf_statement_df.loc["Investissements (CAPEX Initial)", 1] = -initial_capex_outflow

    for month in months:
        month_data = df_year_filtered[df_year_filtered.index.month == month]
        if not month_data.empty:
            month_row = month_data.iloc[0]
            cf_statement_df.loc["Revenus Client", month] = month_row.get('Revenus_Total', 0)
            cf_statement_df.loc["OPEX Total", month] = -month_row.get('OPEX', 0)
            # CORRECTION ICI: Utiliser Tax_Payment pour les décaissements IS
            cf_statement_df.loc["Paiement IS (Acomptes)", month] = -month_row.get('Tax_Payment', 0)
            cf_statement_df.loc["Remboursement Prêt (Principal + Intérêts)", month] = -month_row.get('Service_Dette', 0)

    prev_month_balance = 0.0
    for month in months:
        cf_statement_df.loc["Total Collections", month] = cf_statement_df.loc[["Apport Fonds Propres", "Levée de Dette", "Revenus Client"], month].sum()
        # CORRECTION ICI: Utiliser la bonne ligne pour IS
        cf_statement_df.loc["Total Décaissements", month] = cf_statement_df.loc[["Investissements (CAPEX Initial)", "OPEX Total", "Paiement IS (Acomptes)", "Remboursement Prêt (Principal + Intérêts)"], month].sum()
        variation = cf_statement_df.loc["Total Collections", month] + cf_statement_df.loc["Total Décaissements", month]
        cf_statement_df.loc["Variation Trésorerie", month] = variation
        cf_statement_df.loc["Solde Trésorerie Début", month] = prev_month_balance
        cf_statement_df.loc["Solde Trésorerie Fin", month] = prev_month_balance + variation
        prev_month_balance = cf_statement_df.loc["Solde Trésorerie Fin", month]

    cf_display_df = cf_statement_df.applymap(lambda x: format_value(x, '€', 0, default_na="-"))
    st.dataframe(cf_display_df, use_container_width=True)

    st.caption("""
        *Notes :* Flux initiaux en Mois 1. TVA, dividendes, CAPEX futurs non inclus.
    """)

# --- Fonction Principale MODIFIÉE pour intégrer la correction ---
def display_financial_summary_table(results: dict | None):
    """Affiche la synthèse financière et les flux de trésorerie dans des onglets."""

    # --- Vérifications initiales ---
    if results is None or not isinstance(results, dict) or 'monthly_data' not in results:
        st.warning("Données mensuelles non disponibles pour l'affichage.")
        return
    monthly_df_raw = results.get('monthly_data')
    if not isinstance(monthly_df_raw, pd.DataFrame):
        st.warning("DataFrame mensuel invalide.")
        return

    # --- Charger table_map au début ---
    table_map = load_table_map()
    if table_map is None:
        st.error("Impossible d'afficher le tableau: échec chargement de financial_table_map.json.")
        return

    # --- Définition Dynamique des Ratios (Utilise table_map) ---
    # Fonction helper pour obtenir le display_name ou la clé si non trouvé
    def get_dn(key, fallback=None):
        """Gets display name from table_map, returns key or fallback if not found."""
        # Retourne la clé si display_name manque ou si table_map est None
        name = table_map.get(key, {}).get("display_name") if table_map else key
        return name if name else (fallback if fallback else key)

    try:
        # Clés originales utilisées dans les calculs des ratios
        key_autoconso = 'Autoconsommation_kWh'
        key_prod = 'Production_kWh'
        key_conso = 'Consommation_kWh'
        key_ebitda = 'EBITDA'
        key_revenus = 'Revenus_Total'
        key_tax_payment = 'Tax_Payment'
        key_service_dette = 'Service_Dette'

        # Définir les ratios en utilisant les display_names récupérés dynamiquement
        indicators_ratios_def = [
            # (Nom Affichage Ratio, Fonction Lambda, [Nom Affichage Composant 1, Nom Affichage Composant 2, ...])
            (get_dn("Taux_Autoconso", "Taux Autoconso (%)"), lambda auto, prod: (auto / prod * 100) if prod > 1e-6 else 0.0, [get_dn(key_autoconso), get_dn(key_prod)]),
            (get_dn("Taux_Autoprod", "Taux Autoprod (%)"), lambda auto, conso: (auto / conso * 100) if conso > 1e-6 else 0.0, [get_dn(key_autoconso), get_dn(key_conso)]),
            (get_dn("Marge_EBITDA", "Marge EBITDA (%)"), lambda ebitda, revenus: (ebitda / revenus * 100) if abs(revenus) > 1e-6 else 0.0, [get_dn(key_ebitda), get_dn(key_revenus)]),
            (get_dn("DSCR"), lambda ebitda, tax_paid, service: ((ebitda - tax_paid) / service) if abs(service) > 1e-6 else np.inf, [get_dn(key_ebitda), get_dn(key_tax_payment), get_dn(key_service_dette)])
        ]

        # Informations par défaut pour les ratios (utilisant les display_names dynamiques)
        default_ratio_infos = {
            get_dn("Taux_Autoconso", "Taux Autoconso (%)"): {"unit": "%", "decimals": 1, "group": "3. PROJET : Service Dette & Ratios Associés", "tooltip": "Autoconso / Production"},
            get_dn("Taux_Autoprod", "Taux Autoprod (%)"): {"unit": "%", "decimals": 1, "group": "3. PROJET : Service Dette & Ratios Associés", "tooltip": "Autoconso / Consommation"},
            get_dn("Marge_EBITDA", "Marge EBITDA (%)"): {"unit": "%", "decimals": 1, "group": "2. PROJET : Coûts & Rentabilité Opérationnelle", "tooltip": "EBITDA / Revenus Totaux"},
            get_dn("DSCR"): {"unit": None, "decimals": 2, "group": "3. PROJET : Service Dette & Ratios Associés", "tooltip": "Ratio de Couverture du Service Dette ((EBITDA-Paiements IS)/Service Dette)"}
        }

    except KeyError as e:
        st.error(f"Erreur: Clé '{e}' manquante dans table_map lors de la définition des ratios. Vérifiez votre fichier financial_table_map.json.")
        return
    except Exception as e:
        st.error(f"Erreur lors de la définition des ratios: {e}")
        return
    # --- Fin Définition Ratios ---

    # --- Création des Onglets ---
    tab_synthese, tab_tresorerie = st.tabs(["📊 Synthèse Financière Annuelle", "🏦 Flux de Trésorerie Mensuels"])

    # --- Onglet 1: Synthèse Financière (Logique adaptée pour utiliser ratios dynamiques) ---
    with tab_synthese:
        if 'view_mode' not in st.session_state: st.session_state['view_mode'] = 'annual'
        if 'active_year' not in st.session_state: st.session_state['active_year'] = None

        def set_annual_view(year):
            st.session_state['view_mode'] = 'annual'
            st.session_state['active_year'] = year

        st.markdown("###### Options d'Affichage Annuel", unsafe_allow_html=True)
        nav_cols_list = []
        years_in_data = []
        if not monthly_df_raw.empty and isinstance(monthly_df_raw.index, pd.DatetimeIndex):
            years_in_data = sorted(monthly_df_raw.index.year.unique())

        if not years_in_data:
            st.caption("Aucune année disponible.")
        else:
            num_year_buttons = min(len(years_in_data), 6)
            nav_cols = st.columns(num_year_buttons + 1)
            for i in range(num_year_buttons):
                 year = years_in_data[i]
                 with nav_cols[i]:
                      st.button(f"{year}", key=f"year_nav_{year}_synthese", on_click=set_annual_view, args=(year,))
            if len(years_in_data) > num_year_buttons:
                 with nav_cols[num_year_buttons]:
                      other_years = years_in_data[num_year_buttons:]
                      selected_other_year = st.selectbox("Autres:", options=other_years, index=None,
                                                         label_visibility="collapsed", key="select_other_year_synthese",
                                                         format_func=lambda y: str(y), placeholder="Année...")
                      if selected_other_year is not None:
                           set_annual_view(selected_other_year)
                           st.session_state['select_other_year_synthese'] = None
                           st.rerun()

        if monthly_df_raw.empty:
            st.warning("Données mensuelles vides, impossible d'afficher le détail annuel.")
        else:
            try:
                # --- Préparation & Pivot ---
                df_pivot_source = monthly_df_raw.copy()
                if not isinstance(df_pivot_source.index, pd.DatetimeIndex):
                    df_pivot_source.index = pd.to_datetime(df_pivot_source.index)

                df_pivot_source['Year'] = df_pivot_source.index.year
                df_pivot_source['MonthNum'] = df_pivot_source.index.month
                df_pivot_source['MonthName'] = df_pivot_source.index.strftime('%b').str.capitalize()

                # Utiliser get_dn pour le mapping, garde la clé originale si display_name manque
                metrics_map = {orig_key: get_dn(orig_key, orig_key) for orig_key in table_map.keys()}
                original_cols_available = list(df_pivot_source.columns)
                original_cols_to_use = [key for key in table_map.keys() if key in original_cols_available]

                if not original_cols_to_use: st.error("Aucun indicateur configuré trouvé dans les données."); return

                base_cols = ['Year', 'MonthNum', 'MonthName']
                cols_to_select_present = [col for col in (base_cols + original_cols_to_use) if col in df_pivot_source.columns]
                df_pivot_source_filtered = df_pivot_source[cols_to_select_present].copy()

                # Appliquer le mapping au renommage
                rename_map_filtered = {orig_col: metrics_map[orig_col] for orig_col in original_cols_to_use if orig_col in cols_to_select_present}
                df_pivot_source_filtered = df_pivot_source_filtered.rename(columns=rename_map_filtered)
                valid_display_names = list(rename_map_filtered.values()) # Noms après renommage

                df_melted = df_pivot_source_filtered.melt(
                    id_vars=['Year', 'MonthNum', 'MonthName'], value_vars=valid_display_names,
                    var_name='Indicateur', value_name='Valeur'
                )
                df_pivoted = pd.pivot_table(
                    df_melted, values='Valeur', index=['Year', 'Indicateur'],
                    columns=['MonthNum', 'MonthName'], aggfunc='sum'
                )
                month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                actual_month_columns = [m for m in month_order if m in df_pivoted.columns.get_level_values('MonthName')]
                if not actual_month_columns: # Si aucun mois trouvé (données vides?)
                     st.warning("Aucune donnée mensuelle trouvée après pivot.")
                     # Retourner ici pour éviter les erreurs suivantes
                     # (ou gérer plus bas si on veut afficher l'expander vide)
                     return

                df_pivoted = df_pivoted.reindex(actual_month_columns, axis=1, level='MonthName')
                if len(years_in_data) == 1:
                    df_pivoted.columns = df_pivoted.columns.get_level_values('MonthName')
                else:
                    df_pivoted = df_pivoted.sort_index(axis=1, level='MonthNum')
                    df_pivoted.columns = df_pivoted.columns.get_level_values('MonthName')

                # --- Calcul Totaux Annuels Additifs ---
                numeric_month_cols = list(df_pivoted.columns)
                df_pivoted['Total Annuel'] = np.nan
                # Utiliser les display_names récupérés via get_dn
                additive_indices_display = [
                    get_dn(key) for key, info in table_map.items()
                    if info.get("is_additive", False) and key in original_cols_to_use
                ]
                valid_additive_indices_pivoted = df_pivoted.index.get_level_values('Indicateur').unique().intersection(additive_indices_display)
                if not valid_additive_indices_pivoted.empty:
                     df_pivoted.loc[pd.IndexSlice[:, valid_additive_indices_pivoted], 'Total Annuel'] = df_pivoted.loc[pd.IndexSlice[:, valid_additive_indices_pivoted], numeric_month_cols].sum(axis=1, skipna=True)
                else:
                     print("DEBUG FST: Aucun indice additif trouvé dans les données pivotées.")

                # --- Affichage par Année ---
                st.markdown("---")
                expand_all = st.checkbox("Afficher toutes les années détaillées", value=False, key="expand_all_synthese")

                # Dictionnaire pour stocker les infos des ratios (unité, décimales, groupe, tooltip)
                # Créer AVANT la boucle pour y accéder facilement
                display_name_to_info = {info["display_name"]: info for info in table_map.values() if "display_name" in info}
                # Ajouter les infos des ratios par défaut (après les avoir définies avec les bons noms)
                for ratio_name, ratio_info in default_ratio_infos.items():
                    if ratio_name not in display_name_to_info:
                         display_name_to_info[ratio_name] = ratio_info

                for year in years_in_data:
                    is_active = st.session_state.get('active_year') == year
                    with st.expander(f"Détail Année {year}", expanded=(expand_all or is_active)):
                        try:
                            if isinstance(df_pivoted.index, pd.MultiIndex):
                                # Vérifier si l'année existe avant de sélectionner
                                if year in df_pivoted.index.get_level_values('Year'):
                                     df_year = df_pivoted.loc[pd.IndexSlice[year,:],:].droplevel('Year')
                                else:
                                     st.warning(f"Aucune donnée pivotée trouvée pour l'année {year}.")
                                     continue # Passer à l'année suivante
                            else: df_year = df_pivoted

                            # S'assurer que numeric_month_cols est défini pour cette portée
                            numeric_month_cols_year = [col for col in df_year.columns if col != 'Total Annuel']

                            # --- Calcul Totaux Annuels Dérivés (utilise get_dn) ---
                            config_globale = st.session_state.get('config', {})
                            try:
                                # Fonction helper interne
                                def get_annual_total(df, display_key, default=np.nan):
                                    # Essayer d'abord la colonne 'Total Annuel' précalculée pour les additifs
                                    if display_key in df.index and 'Total Annuel' in df.columns:
                                        val_precalc = df.loc[display_key, 'Total Annuel']
                                        if pd.notna(val_precalc): # Si un total est précalculé (additif), l'utiliser
                                            return val_precalc if np.isfinite(val_precalc) else default

                                    # Sinon (non-additif ou NaN dans Total Annuel), recalculer la somme mensuelle
                                    if display_key in df.index:
                                        monthly_sum = df.loc[display_key, numeric_month_cols_year].sum(skipna=True)
                                        return monthly_sum if pd.notna(monthly_sum) and np.isfinite(monthly_sum) else default
                                    return default # Si la clé n'existe pas

                                # Recalculer explicitement les totaux annuels PNL
                                pnl_keys_to_recalc = [
                                    (get_dn('EBITDA'), 'EBITDA (€)'), (get_dn('EBIT'), 'EBIT (€)'), (get_dn('EBT'), 'EBT (€)'),
                                    (get_dn('Resultat_Net'), 'Résultat Net (€)'), (get_dn('OCF_Projet'), 'OCF Projet (€)'),
                                    (get_dn('FCFE'), 'Free Cash Flow Equity (€)')
                                ]
                                for key_dn, display_fallback in pnl_keys_to_recalc:
                                    if key_dn in df_year.index:
                                        # Utiliser get_annual_total pour recalculer la somme mensuelle
                                        annual_sum_val = get_annual_total(df_year, key_dn, np.nan)
                                        df_year.loc[key_dn, 'Total Annuel'] = annual_sum_val

                                # Rafraîchir les dépendances après recalcul PNL
                                ebitda_an = get_annual_total(df_year, get_dn(key_ebitda))
                                amort_an = get_annual_total(df_year, get_dn('Amortissement')) # Clé originale: Amortissement
                                interets_an = get_annual_total(df_year, get_dn('Interets_Payes')) # Clé originale: Interets_Payes
                                # Utiliser le total annuel de Paiement IS (qui EST additif)
                                impots_paiement_an = get_annual_total(df_year, get_dn(key_tax_payment))
                                principal_an = get_annual_total(df_year, get_dn('Principal_Rembourse')) # Clé originale: Principal_Rembourse

                                # Recalculs dérivés (utiliser les totaux recalculés/vérifiés)
                                if pd.notna(ebitda_an) and pd.notna(amort_an): df_year.loc[get_dn('EBIT'), 'Total Annuel'] = ebitda_an - amort_an # Recalcul EBIT
                                ebit_an = get_annual_total(df_year, get_dn('EBIT')) # Relire EBIT
                                if pd.notna(ebit_an) and pd.notna(interets_an): df_year.loc[get_dn('EBT'), 'Total Annuel'] = ebit_an - interets_an # Recalcul EBT
                                ebt_an = get_annual_total(df_year, get_dn('EBT')) # Relire EBT
                                if pd.notna(ebt_an): df_year.loc[get_dn('Resultat_Net'), 'Total Annuel'] = ebt_an # Résultat Net = EBT
                                rn_an = get_annual_total(df_year, get_dn('Resultat_Net')) # Relire RN
                                if pd.notna(ebt_an) and pd.notna(amort_an) and pd.notna(principal_an) and pd.notna(impots_paiement_an):
                                     # FCFE = EBT - Paiement IS + Amort - Principal
                                     df_year.loc[get_dn('FCFE'), 'Total Annuel'] = ebt_an - impots_paiement_an + amort_an - principal_an

                                # OCF Projet = EBITDA * (1-T) + Amort * T
                                tx_impot = config_globale.get('taux_imposition', 25.0) / 100.0
                                if pd.notna(ebitda_an) and pd.notna(amort_an) and pd.notna(tx_impot):
                                    df_year.loc[get_dn('OCF_Projet'), 'Total Annuel'] = (ebitda_an * (1.0 - tx_impot)) + (amort_an * tx_impot)

                                # Solde Dette Fin
                                key_solde_dette_dn = get_dn('Solde_Dette_Fin_Mois')
                                if key_solde_dette_dn in df_year.index:
                                     last_val = df_year.loc[key_solde_dette_dn, numeric_month_cols_year].dropna().iloc[-1] if not df_year.loc[key_solde_dette_dn, numeric_month_cols_year].dropna().empty else np.nan
                                     df_year.loc[key_solde_dette_dn, 'Total Annuel'] = last_val

                            except Exception as e_calc_deriv:
                                st.warning(f"Année {year}: Erreur calcul totaux dérivés: {e_calc_deriv}", icon="⚠️")

                            # --- Calcul des Ratios Annuels (utilise indicators_ratios_def dynamique) ---
                            for display_name_ratio, calc_lambda, component_display_names in indicators_ratios_def:
                                if display_name_ratio not in df_year.index:
                                     df_year.loc[display_name_ratio] = np.nan

                                try:
                                    # Utiliser get_annual_total pour les composants
                                    comp_values_annual = [get_annual_total(df_year, disp_name, np.nan) for disp_name in component_display_names]

                                    if all(pd.notna(v) and np.isfinite(v) for v in comp_values_annual):
                                        ratio_val = calc_lambda(*comp_values_annual)
                                        if display_name_ratio == get_dn("DSCR"):
                                            # Recalculer explicitement CADS/Service pour DSCR pour gestion inf/NaN
                                            cads_val = get_annual_total(df_year, get_dn(key_ebitda), 0) - get_annual_total(df_year, get_dn(key_tax_payment), 0)
                                            service_val = get_annual_total(df_year, get_dn(key_service_dette), 0)
                                            if abs(service_val) < 1e-9: ratio_val = np.inf if cads_val > 0 else np.nan
                                            elif cads_val <= 0: ratio_val = np.nan
                                        df_year.loc[display_name_ratio, 'Total Annuel'] = ratio_val
                                    else:
                                        df_year.loc[display_name_ratio, 'Total Annuel'] = np.nan

                                except Exception as e_ratio_calc:
                                     print(f"ERREUR FST: Calcul ratio '{display_name_ratio}' année {year}: {e_ratio_calc}")
                                     df_year.loc[display_name_ratio, 'Total Annuel'] = np.nan

                            # --- Réorganisation et Affichage HTML ---
                            grouped_indicators = OrderedDict()
                            processed_display_names = set()
                            for display_name, info in display_name_to_info.items():
                                 if display_name in df_year.index and display_name not in processed_display_names:
                                      group = info.get("group", "9. Autre")
                                      if group not in grouped_indicators: grouped_indicators[group] = []
                                      grouped_indicators[group].append(display_name)
                                      processed_display_names.add(display_name)

                            grouped_indicators = OrderedDict(sorted(grouped_indicators.items()))
                            final_order = [item for group_list in grouped_indicators.values() for item in group_list]
                            missing_from_order = [idx for idx in df_year.index if idx not in final_order]
                            if missing_from_order:
                                 final_order.extend(missing_from_order)

                            df_year_final = df_year.reindex(final_order).dropna(how='all')

                            # --- KPIs Annuels ---
                            st.markdown("###### Indicateurs clés de l'année")
                            kpis_display_corrected = [
                                {"key": key_prod, "display_name_fallback": "Production (kWh)", "unit": "kWh", "icon": "☀️"},
                                {"key": "Taux_Autoconso", "display_name_fallback": "Taux Autoconso (%)", "unit": "%", "icon": "🔄", "threshold_key": "kpi_threshold_autoconso"},
                                {"key": key_revenus, "display_name_fallback": "Revenus Totaux (€)", "unit": "€", "icon": "💰"},
                                {"key": key_ebitda, "display_name_fallback": "EBITDA (€)", "unit": "€", "icon": "📊"},
                                {"key": "FCFE", "display_name_fallback": "FCFE (€)", "unit": "€", "icon": "💸"}
                            ]
                            kpi_cols = st.columns(len(kpis_display_corrected))
                            for i, kpi in enumerate(kpis_display_corrected):
                                 with kpi_cols[i]:
                                      kpi_name_dn = get_dn(kpi["key"], kpi["display_name_fallback"])
                                      value_kpi = get_annual_total(df_year_final, kpi_name_dn, np.nan)
                                      formatted_kpi = "N/A"; color_kpi = "black"
                                      if pd.notna(value_kpi) and np.isfinite(value_kpi):
                                          seuil_min = config_globale.get(kpi.get("threshold_key", "") + "_min")
                                          seuil_warning = config_globale.get(kpi.get("threshold_key", "") + "_warning")
                                          if kpi["key"] == "DSCR" and seuil_min is None: seuil_min = config_globale.get('target_dscr', 1.1)
                                          if kpi["key"] == "Taux_Autoconso" and seuil_min is None: seuil_min = 50.0; seuil_warning = 65.0

                                          if seuil_min is not None and value_kpi < seuil_min: color_kpi = "red"
                                          elif seuil_warning is not None and value_kpi < seuil_warning: color_kpi = "orange"
                                          elif "(€)" in kpi_name_dn and isinstance(value_kpi, (int, float, np.number)): color_kpi = "green" if value_kpi > 0 else "red"
                                          elif kpi["key"] == "DSCR": color_kpi = "green" if value_kpi >= config_globale.get('target_dscr', 1.1) else ("orange" if value_kpi > 0 else "red")
                                          else: color_kpi = "green"

                                          info_kpi = display_name_to_info.get(kpi_name_dn, {})
                                          decimals_kpi = info_kpi.get("decimals", 1 if kpi["unit"] == "%" else 2 if kpi["unit"] is None else 0)
                                          formatted_kpi = format_value(value_kpi, kpi["unit"], decimals_kpi)

                                      # Afficher les KPIs
                                      st.markdown(f'''
                                      <div style="text-align: center; padding: 10px; border-radius: 5px; background-color: #f0f2f6; margin-bottom: 5px; height: 100%;">
                                          <div style="font-size: 24px;">{kpi['icon']}</div>
                                          <div style="font-size: 12px; color: #555; height: 2.5em; overflow: hidden; line-height: 1.2em;">{kpi_name_dn}</div>
                                          <div style="font-size: 16px; font-weight: bold; color: {color_kpi};">{formatted_kpi}</div>
                                      </div>''', unsafe_allow_html=True)
                            st.markdown("<br>", unsafe_allow_html=True)

                            # --- Affichage Tableau HTML ---
                            st.markdown("###### Détail mensuel et total annuel :", unsafe_allow_html=True)
                            col1_opt, col2_opt = st.columns(2)
                            with col1_opt: detail_level = st.radio("Niveau de détail:", ["Complet", "Essentiel"], index=0, key=f"detail_{year}_synthese", horizontal=True)
                            with col2_opt: show_trends = st.checkbox("Afficher tendances Δ%", value=False, key=f"trends_{year}_synthese")

                            df_display = df_year_final.copy()
                            if detail_level == "Essentiel":
                                essential_keys = [key_prod, key_autoconso, key_revenus, key_ebitda, 'Resultat_Net', 'FCFE', 'DSCR', 'Taux_Autoconso', 'Marge_EBITDA']
                                essential_display_names = [get_dn(k) for k in essential_keys]
                                # Filtrer sur les noms d'affichage qui existent réellement dans l'index
                                df_display = df_display[df_display.index.isin(essential_display_names)]

                            if not df_display.empty:
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
                                    cells_html = f'<td title="{tooltip_text}" style="text-align: left;">{idx_display_name}</td>'

                                    for col in df_display.columns:
                                        val = df_display.loc[idx_display_name, col]
                                        trend_symbol = ""; style = ""; text_align = "right"
                                        if show_trends and col != 'Total Annuel' and col in numeric_month_cols_year and numeric_month_cols_year.index(col) > 0:
                                            try:
                                                prev_col_idx = numeric_month_cols_year.index(col) - 1
                                                prev_col = numeric_month_cols_year[prev_col_idx]
                                                prev_val = df_display.loc[idx_display_name, prev_col]
                                                if pd.notna(val) and pd.notna(prev_val) and isinstance(val, (int, float, np.number)) and isinstance(prev_val, (int, float, np.number)) and abs(prev_val) > 1e-9:
                                                     pct_change = (val - prev_val) / abs(prev_val) * 100
                                                     if abs(pct_change) >= 10:
                                                          color = "green" if pct_change > 0 else "red"; arrow = "▲" if pct_change > 0 else "▼"
                                                          trend_symbol = f" <span style='color:{color}; font-size: smaller;'>{arrow}</span>"
                                            except Exception as e_trend: print(f"Trend error: {e_trend}")

                                        formatted_val = format_value(val, unit, decimals)
                                        if col == 'Total Annuel': style = "font-weight: bold; background-color: #f0f2f6;"
                                        cells_html += f'<td style="text-align: {text_align}; {style}">{formatted_val}{trend_symbol}</td>'

                                    html_rows.append(f"<tr>{cells_html}</tr>")

                                html_rows.append("</tbody>")
                                html_table = f'<style> table.dataframe th {{ text-align: right; padding: 4px 8px; }} table.dataframe td {{ text-align: right; padding: 4px 8px; }} table.dataframe td:first-child, table.dataframe th:first-child {{ text-align: left; }} </style><table class="dataframe" style="width: 100%; border-collapse: collapse;">{"".join(html_rows)}</table>'
                                st.markdown(html_table, unsafe_allow_html=True)
                            else:
                                st.info("Aucun indicateur à afficher pour ce niveau de détail.")

                            # --- Section Export Annuel ---
                            st.markdown("---")
                            st.markdown("###### Export des données de l'année :", unsafe_allow_html=True)
                            export_col1, export_col2 = st.columns([1,1])
                            with export_col1: export_format = st.radio("Format:", ["Excel", "CSV"], key=f"export_format_{year}_synthese", horizontal=True, label_visibility="collapsed")
                            with export_col2:
                                 df_export = df_year_final
                                 if export_format == "Excel":
                                      buffer = io.BytesIO()
                                      with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer: df_export.to_excel(writer, sheet_name=f'Annee {year}')
                                      buffer.seek(0)
                                      st.download_button(label="📥 Télécharger Excel", data=buffer, file_name=f"Synthese_Financiere_Annee_{year}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"download_excel_{year}_synthese")
                                 else:
                                      csv_data = df_export.to_csv(sep=';', decimal=',', encoding='utf-8-sig')
                                      st.download_button(label="📥 Télécharger CSV", data=csv_data, file_name=f"Synthese_Financiere_Annee_{year}.csv", mime="text/csv", key=f"download_csv_{year}_synthese")

                        except KeyError as ke:
                             st.error(f"Données manquantes pour l'année {year}. Clé non trouvée: {ke}. Vérifiez `table_map.json` et les colonnes de `monthly_data`.")
                        except Exception as e_expander:
                            st.error(f"Erreur affichage année {year}: {e_expander}")
                            traceback.print_exc()

            except Exception as e_global:
                 st.error(f"Erreur globale lors de la préparation ou l'affichage de la vue annuelle: {e_global}")
                 traceback.print_exc()

    # --- Onglet 2: Flux de Trésorerie (Appelle la fonction dédiée) ---
    with tab_tresorerie:
        display_cash_flow_statement(results)

    # --- Expander Données Brutes ---
    with st.expander("Voir les Données Mensuelles Détaillées (Base de Calcul)"):
        st.markdown("### Tableau des Données Mensuelles (`results['monthly_data']`)")
        if not monthly_df_raw.empty:
            st.dataframe(monthly_df_raw, use_container_width=True)
            st.markdown("#### Résumé Statistique des Données Mensuelles")
            try: st.dataframe(monthly_df_raw.describe(include='all'), use_container_width=True)
            except Exception as e_describe: st.warning(f"Impossible d'afficher le résumé statistique: {e_describe}")
        else:
            st.info("Le DataFrame mensuel brut est vide.")

# --- Fin de la fonction display_financial_summary_table ---