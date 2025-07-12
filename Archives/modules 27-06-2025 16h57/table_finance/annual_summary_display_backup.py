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
    Affiche le compte de résultat professionnel avec structure hiérarchique et pourcentages.
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

    st.markdown(f"### 📊 Compte de Résultat : Année {selected_year_for_display}")
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

    # Colonne unique pour le compte de résultat
    annual_summary_col_name = f"Année {selected_year_for_display}"
    df_annual_pivoted_table[annual_summary_col_name] = np.nan

    # Réorganiser les colonnes pour placer la nouvelle colonne de synthèse à la fin
    all_columns = list(df_annual_pivoted_table.columns)
    # Garder uniquement la colonne de synthèse annuelle (plus de détail mensuel)
    df_annual_pivoted_table = df_annual_pivoted_table[[annual_summary_col_name]]

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

    # === NOUVELLE STRUCTURE : COMPTE DE RÉSULTAT ===
    
    # Calcul du total des produits d'exploitation pour les pourcentages
    val_revenus_total_an = get_annual_total_val(df_annual_pivoted_table, dn_revenus_total)
    val_prime_autoconso_an = get_annual_total_val(df_annual_pivoted_table, get_display_name_from_map('Prime_Autoconso_Encaissee', table_map, 'Prime Autoconsommation'))
    
    # Calculer les composantes du CA
    val_vente_surplus_an = get_annual_total_val(df_annual_pivoted_table, get_display_name_from_map('Revenus_Surplus', table_map, 'Vente surplus réseau'))
    val_valorisation_autoconso_an = get_annual_total_val(df_annual_pivoted_table, get_display_name_from_map('Revenus_Autoconsommation', table_map, 'Valorisation autoconsommation'))
    
    # Calculer les charges variables détaillées
    val_maintenance_an = get_annual_total_val(df_annual_pivoted_table, get_display_name_from_map('OPEX_Maintenance_Mensuel', table_map, 'Maintenance'))
    val_assurance_an = get_annual_total_val(df_annual_pivoted_table, get_display_name_from_map('OPEX_Assurance_Mensuel', table_map, 'Assurance'))
    val_admin_an = get_annual_total_val(df_annual_pivoted_table, get_display_name_from_map('OPEX_Admin_Mensuel', table_map, 'Gestion administrative'))
    val_provision_onduleur_an = get_annual_total_val(df_annual_pivoted_table, get_display_name_from_map('OPEX_Provision_Onduleur_Mensuel', table_map, 'Provision remplacement onduleur'))
    
    # Total produits d'exploitation pour calcul des pourcentages
    total_produits_exploitation = (val_revenus_total_an or 0) + (val_prime_autoconso_an or 0)
    
    def format_percentage(value, total_ref):
        """Formate un pourcentage par rapport au total de référence"""
        if pd.isna(value) or pd.isna(total_ref) or total_ref == 0:
            return "-"
        pct = (value / total_ref) * 100
        return f"{pct:.0f} %" if pct == int(pct) else f"{pct:.1f} %"
    
    # Créer la structure du compte de résultat
    compte_resultat_data = []
    
    # PRODUITS D'EXPLOITATION
    compte_resultat_data.append({
        'type': 'section_header',
        'label': 'PRODUITS D\'EXPLOITATION',
        'value': None,
        'percentage': None,
        'indent': 0
    })
    
    # Chiffre d'affaires
    compte_resultat_data.append({
        'type': 'subtotal',
        'label': 'Chiffre d\'affaires',
        'value': val_revenus_total_an,
        'percentage': None,
        'indent': 1
    })
    
    compte_resultat_data.append({
        'type': 'detail',
        'label': 'Vente surplus réseau',
        'value': val_vente_surplus_an,
        'percentage': None,
        'indent': 2
    })
    
    compte_resultat_data.append({
        'type': 'detail',
        'label': 'Valorisation autoconsommation',
        'value': val_valorisation_autoconso_an,
        'percentage': format_percentage(val_revenus_total_an, total_produits_exploitation),
        'indent': 2
    })
    
    # Subventions d'exploitation
    compte_resultat_data.append({
        'type': 'subtotal',
        'label': 'Subventions d\'exploitation',
        'value': val_prime_autoconso_an,
        'percentage': None,
        'indent': 1
    })
    
    compte_resultat_data.append({
        'type': 'detail',
        'label': 'Prime à l\'autoconsommation',
        'value': val_prime_autoconso_an,
        'percentage': format_percentage(val_prime_autoconso_an, total_produits_exploitation),
        'indent': 2
    })
    
    # TOTAL PRODUITS D'EXPLOITATION
    compte_resultat_data.append({
        'type': 'main_total',
        'label': 'TOTAL PRODUITS D\'EXPLOITATION',
        'value': total_produits_exploitation,
        'percentage': '100 %',
        'indent': 0
    })
    # CHARGES VARIABLES
    total_charges_variables = (val_turpe_an or 0) + (val_maintenance_an or 0) + (val_assurance_an or 0) + (val_admin_an or 0) + (val_provision_onduleur_an or 0)
    
    compte_resultat_data.append({
        'type': 'section_header',
        'label': 'CHARGES VARIABLES',
        'value': total_charges_variables,
        'percentage': format_percentage(total_charges_variables, total_produits_exploitation),
        'indent': 0
    })
    
    compte_resultat_data.append({
        'type': 'detail',
        'label': 'TURPE injection',
        'value': val_turpe_an,
        'percentage': format_percentage(val_turpe_an, total_produits_exploitation),
        'indent': 1
    })
    
    compte_resultat_data.append({
        'type': 'detail',
        'label': 'Maintenance',
        'value': val_maintenance_an,
        'percentage': format_percentage(val_maintenance_an, total_produits_exploitation),
        'indent': 1
    })
    
    compte_resultat_data.append({
        'type': 'detail',
        'label': 'Assurance',
        'value': val_assurance_an,
        'percentage': format_percentage(val_assurance_an, total_produits_exploitation),
        'indent': 1
    })
    
    compte_resultat_data.append({
        'type': 'detail',
        'label': 'Gestion administrative',
        'value': val_admin_an,
        'percentage': format_percentage(val_admin_an, total_produits_exploitation),
        'indent': 1
    })
    
    compte_resultat_data.append({
        'type': 'detail',
        'label': 'Provision remplacement onduleur',
        'value': val_provision_onduleur_an,
        'percentage': format_percentage(val_provision_onduleur_an, total_produits_exploitation),
        'indent': 1
    })
    
    # MARGE SUR COÛTS VARIABLES
    marge_couts_variables = total_produits_exploitation - total_charges_variables
    compte_resultat_data.append({
        'type': 'subtotal',
        'label': 'MARGE SUR COÛTS VARIABLES',
        'value': marge_couts_variables,
        'percentage': format_percentage(marge_couts_variables, total_produits_exploitation),
        'indent': 0
    })
    
    # DOTATIONS AUX AMORTISSEMENTS
    compte_resultat_data.append({
        'type': 'detail',
        'label': 'DOTATIONS AUX AMORTISSEMENTS',
        'value': val_amort_an,
        'percentage': format_percentage(val_amort_an, total_produits_exploitation),
        'indent': 0
    })
    
    # RÉSULTAT D'EXPLOITATION
    resultat_exploitation = marge_couts_variables - (val_amort_an or 0)
    compte_resultat_data.append({
        'type': 'subtotal',
        'label': 'RÉSULTAT D\'EXPLOITATION',
        'value': resultat_exploitation,
        'percentage': format_percentage(resultat_exploitation, total_produits_exploitation),
        'indent': 0
    })
    
    # CHARGES FINANCIÈRES
    compte_resultat_data.append({
        'type': 'section_header',
        'label': 'CHARGES FINANCIÈRES',
        'value': val_interets_an,
        'percentage': format_percentage(val_interets_an, total_produits_exploitation),
        'indent': 0
    })
    
    compte_resultat_data.append({
        'type': 'detail',
        'label': 'Intérêts sur emprunts',
        'value': val_interets_an,
        'percentage': format_percentage(val_interets_an, total_produits_exploitation),
        'indent': 1
    })
    
    # RÉSULTAT AVANT IMPÔT
    resultat_avant_impot = resultat_exploitation - (val_interets_an or 0)
    compte_resultat_data.append({
        'type': 'subtotal',
        'label': 'RÉSULTAT AVANT IMPÔT',
        'value': resultat_avant_impot,
        'percentage': format_percentage(resultat_avant_impot, total_produits_exploitation),
        'indent': 0
    })
    
    # IMPÔT SUR LES SOCIÉTÉS
    compte_resultat_data.append({
        'type': 'detail',
        'label': 'Impôt sur les sociétés',
        'value': val_total_is_decaisse_an,
        'percentage': format_percentage(val_total_is_decaisse_an, total_produits_exploitation),
        'indent': 0
    })
    
    # RÉSULTAT NET
    resultat_net_final = resultat_avant_impot - (val_total_is_decaisse_an or 0)
    compte_resultat_data.append({
        'type': 'main_total',
        'label': 'RÉSULTAT NET',
        'value': resultat_net_final,
        'percentage': format_percentage(resultat_net_final, total_produits_exploitation),
        'indent': 0
    })

    # Affichage du compte de résultat
    st.markdown("##### Compte de Résultat Professionnel")
    
    # Générer le CSS pour le compte de résultat
    css_styles = get_compte_resultat_css()
    st.markdown(css_styles, unsafe_allow_html=True)

    # Construire le HTML du compte de résultat
    html_content = ["<table class='compte-resultat'>"]
    
    # En-tête
    html_content.append(f"<thead><tr><th style='text-align:left;'>Compte de Résultat</th><th style='text-align:right;'>Année {selected_year_for_display}</th></tr></thead>")
    html_content.append("<tbody>")
    
    # Générer les lignes du compte de résultat
    for item in compte_resultat_data:
        row_class = f"cr-{item['type']}"
        indent_class = f"indent-{item['indent']}" if item['indent'] > 0 else ""
        
        # Formater la valeur
        formatted_value = "-"
        if item['value'] is not None and pd.notna(item['value']):
            formatted_value = format_value(item['value'], '€', 0)
            
        # Ligne principale
        html_content.append(f"<tr class='{row_class}'>")
        html_content.append(f"<td class='{indent_class}'>{item['label']}</td>")
        html_content.append(f"<td class='text-right'>{formatted_value}</td>")
        html_content.append("</tr>")
        
        # Ligne de pourcentage si elle existe
        if item['percentage'] is not None:
            html_content.append("<tr class='cr-percentage'>")
            html_content.append("<td></td>")
            html_content.append(f"<td class='text-right percentage'>{item['percentage']}</td>")
            html_content.append("</tr>")
    
    html_content.append("</tbody></table>")
    
    # Afficher le tableau
    final_html = "".join(html_content)
    st.markdown(final_html, unsafe_allow_html=True)

    # === EXPORT ===
    st.markdown("---")
    st.markdown("###### Exporter le compte de résultat")
    
    export_col1, export_col2 = st.columns([1,1])
    with export_col1:
        export_format = st.radio(
            "Format d'export:", ["Excel", "CSV"],
            key=f"export_format_cr_{selected_year_for_display}_{scenario_name_for_key}",
            horizontal=True, label_visibility="collapsed"
        )
    with export_col2:
        # Créer un DataFrame pour l'export
        export_data = []
        for item in compte_resultat_data:
            formatted_value = "-"
            if item['value'] is not None and pd.notna(item['value']):
                formatted_value = format_value(item['value'], '€', 0)
            
            export_data.append({
                'Postes': item['label'],
                f'Année {selected_year_for_display}': formatted_value,
                'Pourcentage': item['percentage'] or "-"
            })
        
        df_export_cr = pd.DataFrame(export_data)
        
        if export_format == "Excel":
            buffer_excel = io.BytesIO()
            with pd.ExcelWriter(buffer_excel, engine='xlsxwriter') as writer:
                df_export_cr.to_excel(writer, sheet_name=f'Compte_Resultat_{selected_year_for_display}', index=False)
            buffer_excel.seek(0)
            st.download_button(
                label="📅 Télécharger Excel", data=buffer_excel,
                file_name=f"Compte_Resultat_{selected_year_for_display}_{scenario_name_for_key}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"download_excel_cr_{selected_year_for_display}_{scenario_name_for_key}"
            )
        else:
            csv_data = df_export_cr.to_csv(sep=';', decimal=',', encoding='utf-8-sig', index=False)
            st.download_button(
                label="📅 Télécharger CSV", data=csv_data,
                file_name=f"Compte_Resultat_{selected_year_for_display}_{scenario_name_for_key}.csv",
                mime="text/csv",
                key=f"download_csv_cr_{selected_year_for_display}_{scenario_name_for_key}"
            )
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