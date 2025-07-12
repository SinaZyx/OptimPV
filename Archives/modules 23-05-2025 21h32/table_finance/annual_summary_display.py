# modules/annual_summary_display.py

import streamlit as st
import pandas as pd
import numpy as np
from collections import OrderedDict
import io

try:
    from .financial_display_utils import format_value, load_table_map, get_display_name_from_map, get_table_css
except ImportError:
    from .financial_display_utils import format_value, load_table_map, get_display_name_from_map, get_table_css

def display_project_summary(results: dict | None):
    # ... (Cette fonction reste inchangée)
    st.markdown("#### Indicateurs Clés Globaux du Projet (sur toute la durée)")
    if not results or not isinstance(results, dict):
        st.warning("Données de résultats invalides pour le récapitulatif global."); return

    col1, col2, col3, col4 = st.columns(4)
    npv_proj_val = results.get('npv_project')
    irr_proj_val = results.get('irr_project')
    with col1:
        st.metric("VAN Projet",
                  format_value(npv_proj_val, '€', 0),
                  help="Valeur Actuelle Nette du projet global (actualisée au WACC après IS) sur toute la durée.")
        st.metric("TRI Projet",
                  format_value(irr_proj_val * 100 if irr_proj_val is not None else None, '%', 1),
                  help="Taux de Rentabilité Interne du projet global (après IS, avant financement) sur toute la durée.")
    lcoe_val = results.get('lcoe')
    payback_proj_val = results.get('payback_project')
    with col2:
        st.metric("LCOE (HT)",
                  format_value(lcoe_val, '€/kWh', 4),
                  help="Coût actualisé 'engineering' de l'énergie produite (€/kWh HT) sur toute la durée.")
        st.metric("Payback Projet",
                  f"{format_value(payback_proj_val, '', 1)} ans",
                  help="Temps pour récupérer l'investissement initial (CAPEX net) par les flux opérationnels après IS.")
    dscr_val = results.get('avg_dscr')
    autoprod_val = results.get('autoproduction_rate')
    with col3:
        st.metric("DSCR Moyen",
                  format_value(dscr_val, '', 2),
                  help="Ratio moyen de couverture du service de la dette (CFADS/Service Dette) sur la durée du prêt.")
        st.metric("Taux Autoprod. Moyen",
                  format_value(autoprod_val * 100 if autoprod_val is not None else None, '%', 1),
                  help="Part de la production totale qui est autoconsommée localement, en moyenne sur la durée. (Autoconso / Production)")
    autoconso_val = results.get('autoconsumption_rate')
    capex_val = results.get('capex_scenario_simule_initial')
    subvention_val = results.get('total_subvention')
    with col4:
        st.metric("Taux Autoconso Moyen",
                  format_value(autoconso_val * 100 if autoconso_val is not None else None, '%', 1),
                  help="Part de la consommation totale des participants qui est couverte par l'énergie autoconsommée, en moyenne sur la durée. (Autoconso / Consommation)")
        st.metric("CAPEX Projet (Brut Scénario)",
                  format_value(capex_val, '€', 0))
        st.metric("Subvention Reçue",
                  format_value(subvention_val, '€', 0))

def display_annual_detailed_summary(results: dict | None, table_map: dict | None, scenario_name_for_key: str = "default_scenario_annual"):
    """
    Affiche la synthèse financière et énergétique annuelle détaillée, avec une seule colonne
    de synthèse annuelle pour un rendu plus professionnel.
    """

    def ansum_handle_year_sb_change_callback(sbox_widget_key_arg, active_year_session_key_arg):
        new_year_from_sb = st.session_state.get(sbox_widget_key_arg)
        if new_year_from_sb is not None and new_year_from_sb != st.session_state.get(active_year_session_key_arg):
            st.session_state[active_year_session_key_arg] = new_year_from_sb

    if not results or not isinstance(results, dict) or 'monthly_data' not in results:
        st.warning("Données mensuelles non disponibles pour la synthèse annuelle détaillée.")
        return
    if table_map is None:
        st.error("Configuration du tableau (table_map) non chargée. Affichage détaillé impossible.")
        return

    monthly_df_raw = results.get('monthly_data')
    if not isinstance(monthly_df_raw, pd.DataFrame) or monthly_df_raw.empty:
        st.warning("DataFrame mensuel pour la synthèse annuelle est invalide ou vide.")
        return

    config_globale_summary = results.get('config_globale_utilisee', st.session_state.get('config', {}))

    df_pivot_source_annual = monthly_df_raw.copy()
    if not isinstance(df_pivot_source_annual.index, pd.DatetimeIndex):
        try:
            df_pivot_source_annual.index = pd.to_datetime(df_pivot_source_annual.index)
        except Exception as e_dt_idx_annual:
            st.error(f"Index des données mensuelles non convertible en datetime: {e_dt_idx_annual}"); return

    df_pivot_source_annual['Year'] = df_pivot_source_annual.index.year
    df_pivot_source_annual['MonthNum'] = df_pivot_source_annual.index.month
    df_pivot_source_annual['MonthName'] = df_pivot_source_annual.index.strftime('%b').str.capitalize()

    available_years_annual = sorted(list(df_pivot_source_annual['Year'].unique()))
    if not available_years_annual:
        st.info("Aucune donnée annuelle à afficher."); return

    session_key_active_year_for_this_scenario = f"active_year_annual_summary_{scenario_name_for_key}"
    if session_key_active_year_for_this_scenario not in st.session_state or \
       st.session_state[session_key_active_year_for_this_scenario] not in available_years_annual:
        st.session_state[session_key_active_year_for_this_scenario] = available_years_annual[0]

    st.markdown("###### Choisissez l'année à visualiser :", unsafe_allow_html=True)
    num_year_buttons_to_show_ui = min(len(available_years_annual), 6)
    num_cols_for_nav = num_year_buttons_to_show_ui
    if len(available_years_annual) > num_year_buttons_to_show_ui:
        num_cols_for_nav += 1
    nav_cols_annual_ui_buttons = st.columns(num_cols_for_nav) if num_cols_for_nav > 0 else [st]

    for i_nav, year_btn_item in enumerate(available_years_annual[:num_year_buttons_to_show_ui]):
        button_key_nav = f"year_btn_disp_{year_btn_item}_{scenario_name_for_key}"
        if nav_cols_annual_ui_buttons[i_nav].button(str(year_btn_item), key=button_key_nav, use_container_width=True):
            if st.session_state.get(session_key_active_year_for_this_scenario) != year_btn_item:
                st.session_state[session_key_active_year_for_this_scenario] = year_btn_item
                st.rerun()

    if len(available_years_annual) > num_year_buttons_to_show_ui:
        other_years_list_for_sb = available_years_annual[num_year_buttons_to_show_ui:]
        selectbox_widget_key = f"other_year_sb_widget_{scenario_name_for_key}"
        current_active_year_for_sb_display = st.session_state.get(session_key_active_year_for_this_scenario)
        idx_to_render_selectbox = 0
        if current_active_year_for_sb_display in other_years_list_for_sb:
            try: idx_to_render_selectbox = other_years_list_for_sb.index(current_active_year_for_sb_display)
            except ValueError: pass
        if other_years_list_for_sb:
            nav_cols_annual_ui_buttons[num_year_buttons_to_show_ui].selectbox(
                "Ou:", options=other_years_list_for_sb, index=idx_to_render_selectbox,
                label_visibility="collapsed", key=selectbox_widget_key,
                on_change=ansum_handle_year_sb_change_callback,
                args=(selectbox_widget_key, session_key_active_year_for_this_scenario)
            )

    selected_year_for_display = st.session_state.get(session_key_active_year_for_this_scenario)
    if selected_year_for_display is None:
        st.error("Erreur critique: Année d'affichage non définie."); return

    st.markdown(f"### Synthèse Annuelle Détaillée : Année {selected_year_for_display}")
    st.markdown("---")

    df_year_selected_data = df_pivot_source_annual[df_pivot_source_annual['Year'] == selected_year_for_display].copy()
    if df_year_selected_data.empty:
        st.info(f"Aucune donnée disponible pour l'année {selected_year_for_display}."); return

    metrics_map_display = {orig_key: get_display_name_from_map(orig_key, table_map, orig_key) for orig_key in table_map.keys()}
    original_cols_in_year_data = [key for key in table_map.keys() if key in df_year_selected_data.columns]
    if not original_cols_in_year_data:
        st.error("Aucun indicateur de table_map trouvé dans les données de l'année sélectionnée."); return

    rename_map_for_year_table = {orig_col: metrics_map_display[orig_col] for orig_col in original_cols_in_year_data}
    df_year_selected_data.rename(columns=rename_map_for_year_table, inplace=True)
    display_names_for_annual_pivot = list(rename_map_for_year_table.values())

    df_melted_annual_view = df_year_selected_data.melt(
        id_vars=['MonthNum', 'MonthName'], value_vars=display_names_for_annual_pivot,
        var_name='Indicateur', value_name='Valeur'
    )
    df_annual_pivoted_table = pd.pivot_table(
        df_melted_annual_view, values='Valeur', index=['Indicateur'],
        columns=['MonthNum', 'MonthName'], aggfunc='sum', fill_value=0
    )

    month_order_for_table = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    actual_month_cols_in_table = [m for m in month_order_for_table if m in df_annual_pivoted_table.columns.get_level_values('MonthName')]
    if not actual_month_cols_in_table:
        st.warning(f"Aucune colonne mensuelle valide après pivot pour l'année {selected_year_for_display}."); return

    df_annual_pivoted_table = df_annual_pivoted_table.reindex(actual_month_cols_in_table, axis=1, level='MonthName')
    if 'MonthNum' in df_annual_pivoted_table.columns.names:
        df_annual_pivoted_table = df_annual_pivoted_table.sort_index(axis=1, level='MonthNum')
    df_annual_pivoted_table.columns = df_annual_pivoted_table.columns.get_level_values('MonthName')

    # --- MODIFICATION ICI : Définir la nouvelle colonne de synthèse annuelle ---
    annual_summary_col_name = f"Synthèse {selected_year_for_display}" # Ou "Année XXXX", "Total / Valeur Annuelle"
    df_annual_pivoted_table[annual_summary_col_name] = np.nan
    # --- FIN MODIFICATION ---

    # Réorganiser les colonnes pour placer la nouvelle colonne de synthèse à la fin
    all_columns = list(df_annual_pivoted_table.columns)
    # --- MODIFICATION ICI : Utiliser la nouvelle colonne de synthèse ---
    special_columns_to_remove = ['Total Annuel', 'Solde fin d\'année', 'Valeur annuelle'] # Anciennes colonnes
    regular_columns = [col for col in all_columns if col not in special_columns_to_remove and col != annual_summary_col_name]
    df_annual_pivoted_table = df_annual_pivoted_table[regular_columns + [annual_summary_col_name]]
    # --- FIN MODIFICATION ---

    # --- MODIFICATION ICI : Logique de remplissage de la colonne de synthèse ---
    def get_annual_value_for_summary_column(df_row, indicator_key_from_map, monthly_cols):
        indicator_props = table_map.get(indicator_key_from_map, {})
        is_additive = indicator_props.get("is_additive", False) # Default to False if not specified

        # Identifier les indicateurs de stock (comme Solde_Dette_Fin_Mois)
        # Pour cela, on peut se baser sur 'is_additive': s'il est false ET que ce n'est pas un ratio connu,
        # on pourrait le considérer comme un stock. Ou mieux, ajouter une propriété "type" dans financial_table_map.json
        # Pour l'instant, traitons Solde_Dette_Fin_Mois explicitement comme un stock.
        is_stock = (indicator_key_from_map == "Solde_Dette_Fin_Mois")

        # Identifier les ratios (ceux dont l'unité est '%')
        is_ratio = (indicator_props.get("unit") == "%")

        if is_stock:
            # Prendre la dernière valeur mensuelle non nulle
            valid_monthly_values = df_row[monthly_cols].dropna()
            return valid_monthly_values.iloc[-1] if not valid_monthly_values.empty else np.nan
        elif is_additive: # Pour les flux et autres éléments additifs
            return pd.to_numeric(df_row[monthly_cols], errors='coerce').sum(skipna=True)
        # Pour les indicateurs non additifs (qui ne sont pas des stocks ou des ratios déjà traités par le code ci-dessous)
        # on pourrait aussi sommer, ou cela indique une configuration à préciser dans financial_table_map.json.
        # Par défaut, si ce n'est ni un stock connu, ni un ratio, ni explicitement additif, on ne met rien pour l'instant.
        # Ou, pour les éléments comme EBIT, EBT, Resultat_Net, OCF_Projet, FCFE,
        # ils seront recalculés ci-dessous à partir de leurs composantes annuelles.
        else:
            return np.nan # Sera rempli plus tard pour les P&L et ratios spécifiques


    # Appliquer la logique de base pour la colonne de synthèse
    for original_key, display_name in metrics_map_display.items():
        if display_name in df_annual_pivoted_table.index:
            df_row_data = df_annual_pivoted_table.loc[display_name]
            annual_value = get_annual_value_for_summary_column(df_row_data, original_key, actual_month_cols_in_table)
            df_annual_pivoted_table.loc[display_name, annual_summary_col_name] = annual_value
    # --- FIN MODIFICATION ---

    # Les fonctions get_annual_total_val doit maintenant lire la nouvelle colonne de synthèse
    def get_annual_total_val(df, display_key, default=np.nan):
        # --- MODIFICATION ICI ---
        if display_key in df.index and annual_summary_col_name in df.columns:
            val = df.loc[display_key, annual_summary_col_name]
            return val if pd.notna(val) and np.isfinite(val) else default
        # Fallback si la colonne n'existe pas ou si la clé n'est pas là (moins probable après la passe précédente)
        elif display_key in df.index and actual_month_cols_in_table:
             monthly_values = df.loc[display_key, actual_month_cols_in_table]
             monthly_sum = pd.to_numeric(monthly_values, errors='coerce').sum(skipna=True)
             return monthly_sum if pd.notna(monthly_sum) and np.isfinite(monthly_sum) else default
        # --- FIN MODIFICATION ---
        return default

    # Récupération des display_names (inchangé)
    dn_revenus_total = get_display_name_from_map('Revenus_Total', table_map)
    dn_opex = get_display_name_from_map('OPEX', table_map)
    dn_turpe = get_display_name_from_map('TURPE', table_map)
    dn_ebitda = get_display_name_from_map('EBITDA', table_map)
    dn_amort = get_display_name_from_map('Amortissement', table_map)
    dn_ebit = get_display_name_from_map('EBIT', table_map)
    dn_interets = get_display_name_from_map('Interets_Payes', table_map)
    dn_ebt = get_display_name_from_map('EBT', table_map)
    dn_tax_payment = get_display_name_from_map('Tax_Payment', table_map) # C'est "Acomptes IS"
    dn_resultat_net = get_display_name_from_map('Resultat_Net', table_map)
    dn_principal = get_display_name_from_map('Principal_Rembourse', table_map)
    dn_fcfe = get_display_name_from_map('FCFE', table_map)
    dn_ocf_projet = get_display_name_from_map('OCF_Projet', table_map)
    # dn_solde_dette a déjà été traité par la logique de get_annual_value_for_summary_column

    # S'assurer que les lignes P&L existent
    pnl_lines_to_ensure_exist = [dn_ebitda, dn_ebit, dn_ebt, dn_resultat_net, dn_fcfe, dn_ocf_projet]
    for line_name in pnl_lines_to_ensure_exist:
        if line_name not in df_annual_pivoted_table.index:
            new_row = pd.Series(name=line_name, index=df_annual_pivoted_table.columns, dtype=float).fillna(0)
            df_annual_pivoted_table = pd.concat([df_annual_pivoted_table, new_row.to_frame().T])

    # Calculs des agrégats annuels pour P&L (remplissent la colonne de synthèse)
    val_revenus_an = get_annual_total_val(df_annual_pivoted_table, dn_revenus_total)
    val_opex_an = get_annual_total_val(df_annual_pivoted_table, dn_opex)
    val_turpe_an = get_annual_total_val(df_annual_pivoted_table, dn_turpe)
    if pd.notna(val_revenus_an) and pd.notna(val_opex_an) and pd.notna(val_turpe_an):
        df_annual_pivoted_table.loc[dn_ebitda, annual_summary_col_name] = val_revenus_an - val_opex_an - val_turpe_an
    else:
        df_annual_pivoted_table.loc[dn_ebitda, annual_summary_col_name] = np.nan

    val_ebitda_an = get_annual_total_val(df_annual_pivoted_table, dn_ebitda) # Relire après calcul
    val_amort_an = get_annual_total_val(df_annual_pivoted_table, dn_amort)
    val_interets_an = get_annual_total_val(df_annual_pivoted_table, dn_interets)
    val_tax_payment_an = get_annual_total_val(df_annual_pivoted_table, dn_tax_payment) # Acomptes IS de l'année
    val_solde_is_n1_an = get_annual_total_val(df_annual_pivoted_table, get_display_name_from_map('Solde_IS_N_1_Paye_Mois', table_map))
    val_total_is_decaisse_an = get_annual_total_val(df_annual_pivoted_table, get_display_name_from_map('Total_IS_Decaisse_Mois', table_map))


    val_principal_an = get_annual_total_val(df_annual_pivoted_table, dn_principal)

    if pd.notna(val_ebitda_an) and pd.notna(val_amort_an):
        df_annual_pivoted_table.loc[dn_ebit, annual_summary_col_name] = val_ebitda_an - val_amort_an
    else: df_annual_pivoted_table.loc[dn_ebit, annual_summary_col_name] = np.nan
    val_ebit_an = get_annual_total_val(df_annual_pivoted_table, dn_ebit)

    if pd.notna(val_ebit_an) and pd.notna(val_interets_an):
        df_annual_pivoted_table.loc[dn_ebt, annual_summary_col_name] = val_ebit_an - val_interets_an
    else: df_annual_pivoted_table.loc[dn_ebt, annual_summary_col_name] = np.nan
    val_ebt_an = get_annual_total_val(df_annual_pivoted_table, dn_ebt)

    # Pour Resultat_Net, utiliser le total IS effectivement décaissé de l'année
    if pd.notna(val_ebt_an) and pd.notna(val_total_is_decaisse_an):
        df_annual_pivoted_table.loc[dn_resultat_net, annual_summary_col_name] = val_ebt_an - val_total_is_decaisse_an
    else:
        df_annual_pivoted_table.loc[dn_resultat_net, annual_summary_col_name] = np.nan

    val_resultat_net_an = get_annual_total_val(df_annual_pivoted_table, dn_resultat_net)

    if pd.notna(val_resultat_net_an) and pd.notna(val_amort_an) and pd.notna(val_principal_an):
        df_annual_pivoted_table.loc[dn_fcfe, annual_summary_col_name] = val_resultat_net_an + val_amort_an - val_principal_an
    else: df_annual_pivoted_table.loc[dn_fcfe, annual_summary_col_name] = np.nan

    tx_impot_calc = config_globale_summary.get('taux_imposition', 25.0) / 100.0
    if pd.notna(val_ebitda_an) and pd.notna(val_amort_an):
        df_annual_pivoted_table.loc[dn_ocf_projet, annual_summary_col_name] = (val_ebitda_an * (1.0 - tx_impot_calc)) + (val_amort_an * tx_impot_calc)
    else: df_annual_pivoted_table.loc[dn_ocf_projet, annual_summary_col_name] = np.nan


    # Calcul des Ratios Annuels (remplissent la colonne de synthèse)
    dn_autoconso_kwh = get_display_name_from_map('Autoconsommation_kWh', table_map)
    dn_conso_kwh = get_display_name_from_map('Consommation_kWh', table_map)
    val_autoconso_an_tbl = get_annual_total_val(df_annual_pivoted_table, dn_autoconso_kwh)
    val_conso_an_tbl = get_annual_total_val(df_annual_pivoted_table, dn_conso_kwh)
    dn_taux_autoconso_tbl = get_display_name_from_map('Taux_Autoconso', table_map, "Taux Autoconso. Annuel (%)")
    if dn_taux_autoconso_tbl not in df_annual_pivoted_table.index: df_annual_pivoted_table.loc[dn_taux_autoconso_tbl] = np.nan
    if pd.notna(val_autoconso_an_tbl) and pd.notna(val_conso_an_tbl) and val_conso_an_tbl > 1e-6:
        ratio_value = (val_autoconso_an_tbl / val_conso_an_tbl) * 100.0
        df_annual_pivoted_table.loc[dn_taux_autoconso_tbl, annual_summary_col_name] = ratio_value
    else:
        df_annual_pivoted_table.loc[dn_taux_autoconso_tbl, annual_summary_col_name] = np.nan

    dn_prod_kwh = get_display_name_from_map('Production_kWh', table_map)
    val_prod_an_tbl = get_annual_total_val(df_annual_pivoted_table, dn_prod_kwh)
    dn_taux_autoprod_tbl = get_display_name_from_map('Taux_Autoprod', table_map, "Taux Autoprod. Annuel (%)")
    if dn_taux_autoprod_tbl not in df_annual_pivoted_table.index: df_annual_pivoted_table.loc[dn_taux_autoprod_tbl] = np.nan
    if pd.notna(val_autoconso_an_tbl) and pd.notna(val_prod_an_tbl) and val_prod_an_tbl > 1e-6:
        ratio_value = (val_autoconso_an_tbl / val_prod_an_tbl) * 100.0
        df_annual_pivoted_table.loc[dn_taux_autoprod_tbl, annual_summary_col_name] = ratio_value
    else:
        df_annual_pivoted_table.loc[dn_taux_autoprod_tbl, annual_summary_col_name] = np.nan

    val_revenus_total_an_tbl = get_annual_total_val(df_annual_pivoted_table, dn_revenus_total)
    dn_marge_ebitda_tbl = get_display_name_from_map('Marge_EBITDA', table_map, "Marge EBITDA Annuelle (%)")
    if dn_marge_ebitda_tbl not in df_annual_pivoted_table.index: df_annual_pivoted_table.loc[dn_marge_ebitda_tbl] = np.nan
    if pd.notna(val_ebitda_an) and pd.notna(val_revenus_total_an_tbl) and abs(val_revenus_total_an_tbl) > 1e-6:
        ratio_value = (val_ebitda_an / val_revenus_total_an_tbl) * 100.0
        df_annual_pivoted_table.loc[dn_marge_ebitda_tbl, annual_summary_col_name] = ratio_value
    else:
        df_annual_pivoted_table.loc[dn_marge_ebitda_tbl, annual_summary_col_name] = np.nan

    # KPIs Annuels (inchangé, mais utilise get_annual_total_val qui lit la nouvelle colonne)
    st.markdown("###### Indicateurs Clés de l'Année Sélectionnée")
    kpi_definitions_annual_list = [
        {"key": "Production_kWh", "label": "Production Annuelle", "unit": "kWh", "icon": "☀️"},
        {"key": "Taux_Autoconso", "label": "Taux Autoconso. Annuel", "unit": "%", "icon": "🔄", "threshold_good": 65.0, "threshold_warn": 50.0},
        {"key": "Revenus_Total", "label": "Revenus Totaux Annuels", "unit": "€", "icon": "💰"},
        {"key": "EBITDA", "label": "EBITDA Annuel", "unit": "€", "icon": "📊"},
        {"key": "FCFE", "label": "FCFE Annuel", "unit": "€", "icon": "💸"},
    ]
    kpi_cols_display = st.columns(len(kpi_definitions_annual_list))
    dn_autoconso_kwh_kpi = get_display_name_from_map('Autoconsommation_kWh', table_map)
    dn_conso_kwh_kpi = get_display_name_from_map('Consommation_kWh', table_map)

    for i_kpi_disp, kpi_info_disp in enumerate(kpi_definitions_annual_list):
        with kpi_cols_display[i_kpi_disp]:
            kpi_display_name_val = get_display_name_from_map(kpi_info_disp["key"], table_map, kpi_info_disp["label"])
            value_for_kpi_card = np.nan
            if kpi_info_disp["key"] == "Taux_Autoconso": # Traitement spécial pour Taux Autoconso
                # La valeur est déjà calculée dans df_annual_pivoted_table dans la colonne annual_summary_col_name
                value_for_kpi_card = get_annual_total_val(df_annual_pivoted_table, dn_taux_autoconso_tbl, np.nan)
            else:
                value_for_kpi_card = get_annual_total_val(df_annual_pivoted_table, kpi_display_name_val, np.nan)

            formatted_kpi_card_val = "Donnée Indisponible"; kpi_card_color = "#555555"
            tooltip_kpi = table_map.get(kpi_info_disp["key"], {}).get("tooltip", kpi_display_name_val)
            if pd.notna(value_for_kpi_card) and np.isfinite(value_for_kpi_card):
                # ... (logique de couleur KPI inchangée)
                positive_is_good = kpi_info_disp.get("positive_is_good", True)
                threshold_good = kpi_info_disp.get("threshold_good")
                threshold_warn = kpi_info_disp.get("threshold_warn")

                if positive_is_good:
                    if threshold_good is not None and value_for_kpi_card >= threshold_good: kpi_card_color = "green"
                    elif threshold_warn is not None and value_for_kpi_card >= threshold_warn: kpi_card_color = "orange"
                    elif threshold_warn is not None and value_for_kpi_card < threshold_warn : kpi_card_color = "red"
                    elif value_for_kpi_card > 1e-6 and (kpi_info_disp["unit"] == "€" or kpi_info_disp["unit"] == "kWh"): kpi_card_color = "green"
                    elif value_for_kpi_card < -1e-6 and (kpi_info_disp["unit"] == "€" or kpi_info_disp["unit"] == "kWh"): kpi_card_color = "red"
                    else: kpi_card_color = "black"
                else:
                    if threshold_good is not None and value_for_kpi_card <= threshold_good: kpi_card_color = "green"
                    elif threshold_warn is not None and value_for_kpi_card <= threshold_warn: kpi_card_color = "orange"
                    else: kpi_card_color = "red"

                info_kpi_map = table_map.get(kpi_info_disp["key"], {})
                decimals_for_kpi_card = info_kpi_map.get("decimals", 0 if kpi_info_disp["unit"] == '€' else (1 if kpi_info_disp["unit"] == '%' else 2))
                formatted_kpi_card_val = format_value(value_for_kpi_card, kpi_info_disp["unit"], decimals_for_kpi_card, default_na="...")
            elif pd.notna(value_for_kpi_card) and not np.isfinite(value_for_kpi_card):
                formatted_kpi_card_val = format_value(value_for_kpi_card, unit=None)
                kpi_card_color = "blue" if value_for_kpi_card > 0 else "purple"
            st.markdown(f"""
            <div title="{tooltip_kpi}" style="text-align: center; padding: 10px; border-radius: 8px; background-color: #f8f9fa; margin-bottom: 5px; height: 130px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #eee;">
                <div style="font-size: 26px; margin-bottom: 5px;">{kpi_info_disp['icon']}</div>
                <div style="font-size: 13px; color: #333; height: 2.6em; line-height: 1.3em; overflow: hidden; margin-bottom: 5px;">{kpi_display_name_val}</div>
                <div style="font-size: 17px; font-weight: bold; color: {kpi_card_color};">{formatted_kpi_card_val}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Affichage du tableau HTML (s'assurer que la nouvelle colonne de synthèse est bien prise en compte)
    st.markdown("###### Détail Mensuel et Synthèse Annuelle :", unsafe_allow_html=True) # Titre mis à jour
    col_opt_detail, col_opt_trend = st.columns(2)
    with col_opt_detail:
        detail_level_selected = st.radio(
            "Niveau de détail du tableau:", ["Complet", "Essentiel"], index=0,
            key=f"detail_level_annual_table_{selected_year_for_display}_{scenario_name_for_key}",
            horizontal=True
        )
    with col_opt_trend:
        show_monthly_trends = st.checkbox(
            "Afficher tendances Δ% vs M-1", value=False,
            key=f"show_trends_annual_table_{selected_year_for_display}_{scenario_name_for_key}"
        )

    df_for_html_final_display = df_annual_pivoted_table.copy()
    if detail_level_selected == "Essentiel":
        essential_original_keys_list = [ # Liste à ajuster au besoin
            'Production_kWh', 'Autoconsommation_kWh', 'Revenus_Total', 'EBITDA',
            'Resultat_Net', 'FCFE', 'Taux_Autoconso', 'Marge_EBITDA', 'Service_Dette', 'Tax_Payment'
        ]
        essential_display_names_selection = [get_display_name_from_map(k, table_map) for k in essential_original_keys_list]
        valid_essential_display_names = [name for name in essential_display_names_selection if name in df_for_html_final_display.index]
        df_for_html_final_display = df_for_html_final_display.loc[valid_essential_display_names]

    if not df_for_html_final_display.empty:
        html_rows_content_list = []
        table_css_styles = get_table_css('annual')
        html_rows_content_list.append(table_css_styles)

        html_cols_header_str = ""
        month_col_idx_for_header = 0
        if hasattr(df_for_html_final_display, 'columns'):
            for col_name_header in df_for_html_final_display.columns:
                class_sep_q = ""
                # --- MODIFICATION ICI : Appliquer une classe spéciale à la colonne de synthèse ---
                class_annual_summary = "annual-summary-col" if col_name_header == annual_summary_col_name else ""
                # --- FIN MODIFICATION ---
                if col_name_header in actual_month_cols_in_table:
                    if (month_col_idx_for_header + 1) % 3 == 0 and month_col_idx_for_header < len(actual_month_cols_in_table) - 1:
                        class_sep_q = "quarter-sep"
                    month_col_idx_for_header += 1
                # --- MODIFICATION ICI : Ajouter la classe annual_summary_col ---
                html_cols_header_str += f"<th class='{class_sep_q} {class_annual_summary}'>{col_name_header}</th>"
                # --- FIN MODIFICATION ---

        html_rows_content_list.append(f"<table class='dataframe-annual-summary'><thead><tr><th style='text-align:left;'>Indicateur</th>{html_cols_header_str}</tr></thead>")
        html_rows_content_list.append("<tbody>")

        current_html_group_name = None
        num_display_cols = len(df_for_html_final_display.columns) + 1 if hasattr(df_for_html_final_display, 'columns') else 1
        display_name_to_info_for_html_final = {info["display_name"]: info for info in table_map.values() if "display_name" in info and info["display_name"] in df_for_html_final_display.index}
        # ... (logique pour default_ratio_infos_annual_table et ordered_display_names_final_html inchangée) ...
        default_ratio_infos_annual_table = {
            get_display_name_from_map('Taux_Autoconso', table_map, "Taux Autoconso. Annuel (%)"): {"unit": "%", "decimals": 1, "group": "Ratios Clés", "tooltip": "Autoconso Annuelle / Consommation Annuelle"},
            get_display_name_from_map('Taux_Autoprod', table_map, "Taux Autoprod. Annuel (%)"): {"unit": "%", "decimals": 1, "group": "Ratios Clés", "tooltip": "Autoconso Annuelle / Production Annuelle"},
            get_display_name_from_map('Marge_EBITDA', table_map, "Marge EBITDA Annuelle (%)"): {"unit": "%", "decimals": 1, "group": "Ratios Clés", "tooltip": "EBITDA Annuel / Revenus Totaux Annuels"},
            get_display_name_from_map('DSCR', table_map, "DSCR Annuel"): {"unit": None, "decimals": 2, "group": "Ratios Clés", "tooltip": "CFADS Annuel / Service Dette Annuel"}
        }
        for ratio_dn, ratio_info_default in default_ratio_infos_annual_table.items():
            if ratio_dn not in display_name_to_info_for_html_final and ratio_dn in df_for_html_final_display.index:
                display_name_to_info_for_html_final[ratio_dn] = ratio_info_default

        ordered_display_names_final_html = []
        temp_grouped_for_order = OrderedDict()

        if hasattr(df_for_html_final_display, 'index'):
            for idx_name_order in df_for_html_final_display.index:
                group_name_order = display_name_to_info_for_html_final.get(idx_name_order, {}).get("group", "99. Divers")
                if group_name_order not in temp_grouped_for_order: temp_grouped_for_order[group_name_order] = []
                if idx_name_order not in temp_grouped_for_order[group_name_order]:
                     temp_grouped_for_order[group_name_order].append(idx_name_order)

        for group_key_order in sorted(temp_grouped_for_order.keys()):
            ordered_display_names_final_html.extend(temp_grouped_for_order[group_key_order])
        ordered_display_names_final_html = list(dict.fromkeys(ordered_display_names_final_html))


        for indicator_display_name_row in ordered_display_names_final_html:
            if indicator_display_name_row not in df_for_html_final_display.index: continue
            row_data_for_html = df_for_html_final_display.loc[indicator_display_name_row]
            row_info_from_map = display_name_to_info_for_html_final.get(indicator_display_name_row, {})
            group_name_from_map = row_info_from_map.get("group", "99. Divers")
            unit_from_map = row_info_from_map.get("unit")
            decimals_from_map = row_info_from_map.get("decimals", 0)
            tooltip_from_map = row_info_from_map.get("tooltip", indicator_display_name_row)

            if group_name_from_map != current_html_group_name:
                html_rows_content_list.append(f"<tr class='group-header-style'><td colspan='{num_display_cols}'>{group_name_from_map}</td></tr>")
                current_html_group_name = group_name_from_map
            row_class_style = "total-row-style" if "Total" in indicator_display_name_row or "Solde" in indicator_display_name_row or "EBITDA" in indicator_display_name_row or "Résultat" in indicator_display_name_row or "DSCR" in indicator_display_name_row or "Marge" in indicator_display_name_row or "Taux" in indicator_display_name_row else ""
            cells_content_str_html = f"<td title='{tooltip_from_map}' style='text-align: left; padding-left:15px;'>{indicator_display_name_row}</td>"

            if hasattr(df_for_html_final_display, 'columns'):
                for i_cell_html, col_name_cell_html in enumerate(df_for_html_final_display.columns):
                    val_cell_html = row_data_for_html[col_name_cell_html]
                    current_decimals = decimals_from_map
                    formatted_val_cell_html = format_value(val_cell_html, unit_from_map, current_decimals, default_na="-")
                    trend_symbol_content_html = ""
                    if show_monthly_trends and col_name_cell_html != annual_summary_col_name and col_name_cell_html in actual_month_cols_in_table: # Ne pas calculer trend sur la colonne de synthèse
                        current_month_idx_for_trend = actual_month_cols_in_table.index(col_name_cell_html)
                        if current_month_idx_for_trend > 0:
                            prev_month_name_for_trend = actual_month_cols_in_table[current_month_idx_for_trend - 1]
                            prev_val_for_trend = row_data_for_html.get(prev_month_name_for_trend)
                            if pd.notna(val_cell_html) and pd.notna(prev_val_for_trend) and isinstance(val_cell_html, (int, float, np.number)) and isinstance(prev_val_for_trend, (int, float, np.number)) and abs(prev_val_for_trend) > 1e-9:
                                pct_change_trend = (val_cell_html - prev_val_for_trend) / abs(prev_val_for_trend) * 100
                                if abs(pct_change_trend) >= 10:
                                    color_trend = "green" if pct_change_trend > 0 else "red"; arrow_trend = "▲" if pct_change_trend > 0 else "▼"
                                    trend_symbol_content_html = f" <span style='color:{color_trend}; font-size: smaller;'>{arrow_trend}{abs(pct_change_trend):.0f}%</span>"
                    class_sep_q_cell = ""
                    # --- MODIFICATION ICI : Appliquer la classe spéciale à la cellule de synthèse ---
                    class_annual_summary_cell = "annual-summary-col" if col_name_cell_html == annual_summary_col_name else ""
                    # --- FIN MODIFICATION ---
                    if col_name_cell_html in actual_month_cols_in_table:
                        month_idx_for_cell_sep = actual_month_cols_in_table.index(col_name_cell_html)
                        if (month_idx_for_cell_sep + 1) % 3 == 0 and month_idx_for_cell_sep < len(actual_month_cols_in_table) - 1:
                            class_sep_q_cell = "quarter-sep"
                    # --- MODIFICATION ICI : style et classe pour la cellule de synthèse ---
                    current_cell_style = "" # Reset style
                    if col_name_cell_html == annual_summary_col_name:
                        current_cell_style = "font-weight: bold;" # Garder le gras, la couleur de fond sera gérée par la classe CSS
                    cells_content_str_html += f"<td class='{class_sep_q_cell} {class_annual_summary_cell}' style='{current_cell_style}'>{formatted_val_cell_html}{trend_symbol_content_html}</td>"
                    # --- FIN MODIFICATION ---
            html_rows_content_list.append(f"<tr class='{row_class_style}'>{cells_content_str_html}</tr>")

        html_rows_content_list.append("</tbody></table>")
        final_html_table_render = "".join(html_rows_content_list)
        st.markdown(final_html_table_render, unsafe_allow_html=True)
    else:
        st.info("Aucun indicateur à afficher pour le niveau de détail sélectionné.")

    # Export (la logique d'export doit maintenant utiliser df_annual_pivoted_table qui contient la colonne de synthèse unique)
    if not df_annual_pivoted_table.empty:
        st.markdown("---")
        st.markdown("###### Exporter les données annuelles détaillées :", unsafe_allow_html=True)
        export_col1_annual, export_col2_annual = st.columns([1,1])
        with export_col1_annual:
            export_format_annual = st.radio(
                "Format d'export:", ["Excel", "CSV"],
                key=f"export_format_annual_{selected_year_for_display}_{scenario_name_for_key}",
                horizontal=True, label_visibility="collapsed"
            )
        with export_col2_annual:
            df_export_annual_table = df_annual_pivoted_table # Utiliser le DataFrame modifié
            if export_format_annual == "Excel":
                buffer_excel_annual = io.BytesIO()
                with pd.ExcelWriter(buffer_excel_annual, engine='xlsxwriter') as writer_excel_annual:
                    df_export_annual_table.to_excel(writer_excel_annual, sheet_name=f'Annee {selected_year_for_display}')
                buffer_excel_annual.seek(0)
                st.download_button(
                    label="📥 Télécharger Excel", data=buffer_excel_annual,
                    file_name=f"Synthese_Annuelle_{selected_year_for_display}_{scenario_name_for_key}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_excel_annual_{selected_year_for_display}_{scenario_name_for_key}"
                )
            else:
                csv_data_annual = df_export_annual_table.to_csv(sep=';', decimal=',', encoding='utf-8-sig')
                st.download_button(
                    label="📥 Télécharger CSV", data=csv_data_annual,
                    file_name=f"Synthese_Annuelle_{selected_year_for_display}_{scenario_name_for_key}.csv",
                    mime="text/csv",
                    key=f"download_csv_annual_{selected_year_for_display}_{scenario_name_for_key}"
                )