import streamlit as st
import pandas as pd
import numpy as np
import io
import json
import os
from datetime import datetime
from collections import OrderedDict

# --- Configuration Path ---
CONFIG_DIR = "config"
TABLE_MAP_FILE = os.path.join(CONFIG_DIR, "financial_table_map.json")

# --- Global variable to cache the loaded map ---
# (Avoids reloading the file on every Streamlit rerun within the same session)
_table_map_cache = None

def load_table_map():
    """Loads the table mapping configuration from the JSON file."""
    global _table_map_cache
    if _table_map_cache is not None:
        return _table_map_cache

    if not os.path.exists(TABLE_MAP_FILE):
        st.error(f"Fichier de configuration du tableau introuvable: {TABLE_MAP_FILE}")
        return None
    try:
        with open(TABLE_MAP_FILE, 'r', encoding='utf-8') as f:
            _table_map_cache = json.load(f)
        # Simple validation
        if not isinstance(_table_map_cache, dict):
             raise ValueError("Le fichier JSON ne contient pas un dictionnaire valide.")
        # You could add more validation here (check required keys per indicator)
        return _table_map_cache
    except json.JSONDecodeError as e:
        st.error(f"Erreur de décodage JSON dans {TABLE_MAP_FILE}: {e}")
        return None
    except Exception as e:
        st.error(f"Erreur lors du chargement de {TABLE_MAP_FILE}: {e}")
        return None

def format_value(value, unit='€', decimals=0):
    """Formate une valeur numérique avec unité et décimales, gère NaN/None."""
    if pd.isna(value) or not isinstance(value, (int, float, np.number)) or not np.isfinite(value):
        # Pour les ratios en %, on pourrait vouloir afficher 0% au lieu de N/A si les composants sont nuls
        # Mais pour l'instant, gardons N/A pour indiquer un calcul impossible ou une donnée manquante.
        return "N/A"
    try:
        format_str = f"{{:,.{decimals}f}}"
        formatted_value = format_str.format(value)
        if unit == '%': return f"{formatted_value}%"
        elif unit == '€': return f"{formatted_value} €"
        elif unit == 'kWh': return f"{formatted_value} kWh"
        elif unit is None: return formatted_value # Pour DSCR par ex.
        else: return f"{formatted_value} {unit}"
    except (ValueError, TypeError):
        print(f"AVERTISSEMENT format_value: Impossible de formater {value} avec unit={unit}, decimals={decimals}")
        return str(value)

def display_financial_summary_table(results: dict | None):
    """Affiche un tableau de synthèse financière amélioré basé sur une config JSON."""
    if results is None or not isinstance(results, dict) or 'monthly_data' not in results:
        st.warning("Données mensuelles non disponibles.")
        return

    monthly_df_raw = results.get('monthly_data')
    if not isinstance(monthly_df_raw, pd.DataFrame) or monthly_df_raw.empty:
        st.warning("Données mensuelles vides ou invalides.")
        return

    # --- Charger la configuration du tableau ---
    table_map = load_table_map()
    if table_map is None:
        return # Arrêter si la config ne peut être chargée

    st.markdown("## Tableau Financier")
    tab1, tab2 = st.tabs(["💰 Synthèse Financière", "📋 Données Brutes"])

    with tab1:
        try:
            df_pivot_source = monthly_df_raw.copy()
            if not isinstance(df_pivot_source.index, pd.DatetimeIndex):
                 df_pivot_source.index = pd.to_datetime(df_pivot_source.index)

            df_pivot_source['Year'] = df_pivot_source.index.year
            df_pivot_source['MonthNum'] = df_pivot_source.index.month
            df_pivot_source['MonthName'] = df_pivot_source.index.strftime('%b').str.lower()

            # --- Construire dynamiquement depuis table_map ---
            metrics_map = {orig_key: info.get("display_name", orig_key) for orig_key, info in table_map.items()}
            original_cols_to_find = list(table_map.keys())

            # Filtrer/Renommer/Pivoter (Logique similaire, utilise maintenant les clés de table_map)
            pivot_cols_exist = [col for col in original_cols_to_find if col in df_pivot_source.columns]
            missing_engine_cols = list(set(original_cols_to_find) - set(pivot_cols_exist))
            if missing_engine_cols:
                 st.warning(f"Colonnes du moteur d'analyse manquantes ou non mappées dans JSON: {missing_engine_cols}")

            if not pivot_cols_exist: st.error("Aucune colonne mappée trouvée dans les données brutes."); return

            base_cols = ['Year', 'MonthNum', 'MonthName']
            cols_to_select = base_cols + pivot_cols_exist
            df_pivot_source_filtered = df_pivot_source[cols_to_select].copy()
            rename_map_filtered = {orig_col: metrics_map[orig_col] for orig_col in pivot_cols_exist}
            df_pivot_source_filtered = df_pivot_source_filtered.rename(columns=rename_map_filtered)

            # Utiliser les noms d'affichage valides pour le melt
            valid_display_names = [metrics_map[orig_col] for orig_col in pivot_cols_exist]
            df_melted = df_pivot_source_filtered.melt(
                id_vars=['Year', 'MonthNum', 'MonthName'], value_vars=valid_display_names,
                var_name='Indicateur', value_name='Valeur'
            )
            df_pivoted = pd.pivot_table(
                df_melted, values='Valeur', index=['Year', 'Indicateur'],
                columns=['MonthNum', 'MonthName'], aggfunc='sum' # Garder 'sum' ici, on corrige après
            )
            df_pivoted = df_pivoted.sort_index(axis=1, level='MonthNum')
            month_columns_ordered = df_pivoted.columns.get_level_values('MonthName').tolist()
            df_pivoted.columns = month_columns_ordered

            # --- Calcul Totaux Annuels Additifs (utilisant is_additive du JSON) ---
            numeric_month_cols = df_pivoted.columns
            df_pivoted['Total Annuel'] = np.nan
            additive_indices_display = [
                info["display_name"] for info in table_map.values() if info.get("is_additive", False)
            ]
            if isinstance(df_pivoted.index, pd.MultiIndex):
                indicator_level = df_pivoted.index.get_level_values('Indicateur')
                valid_additive_indices = indicator_level.unique().intersection(additive_indices_display)
                idx_slice = pd.IndexSlice[:, valid_additive_indices]
                cols_slice = numeric_month_cols
                df_pivoted.loc[idx_slice, 'Total Annuel'] = df_pivoted.loc[idx_slice, cols_slice].sum(axis=1)
            else: st.warning("Index non MultiIndex pour totaux additifs.")
            # --- Fin Calcul totaux additifs ---

            # --- Boucle par Année ---
            years_in_data = sorted(df_pivoted.index.get_level_values('Year').unique()) if isinstance(df_pivoted.index, pd.MultiIndex) else []
            config_globale = st.session_state.get('config', {}) # Pour seuils KPI
            # ... (Navigation rapide, Checkbox Tout Développer) ...
            col_nav1, col_nav2 = st.columns([3,1]) # Mettre les boutons dans une colonne
            with col_nav1:
                st.markdown("### Navigation rapide")
                num_cols_nav = max(1, min(len(years_in_data), 5))
                year_cols = st.columns(num_cols_nav)
                for i, year_nav in enumerate(years_in_data):
                     col_idx = i % num_cols_nav
                     with year_cols[col_idx]:
                          if st.button(f"{year_nav}", key=f"year_nav_{year_nav}"):
                               st.session_state['active_year'] = year_nav
                               st.rerun()
            with col_nav2:
                 expand_all = st.checkbox("Tout développer", value=False, key="expand_all")


            for year in years_in_data:
                is_active = st.session_state.get('active_year') == year
                with st.expander(f"Année {year}", expanded=expand_all or is_active):
                    try:
                        df_year = df_pivoted.loc[year].copy()

                        # --- Calcul Totaux Annuels Dérivés (Non Additifs) ---
                        try:
                             def get_annual_total(df, display_key, default=np.nan):
                                 if display_key in df.index and 'Total Annuel' in df.columns:
                                     val = df.loc[display_key, 'Total Annuel']
                                     return val if pd.notna(val) else default
                                 return default

                             # Initialiser les lignes si elles manquent (utilise les noms d'affichage comme clés)
                             for info in table_map.values():
                                 display_name = info.get("display_name")
                                 if display_name and display_name not in df_year.index:
                                     df_year.loc[display_name] = np.nan

                             # Recalculer EBITDA Annuel par somme
                             ebitda_display_name = table_map.get("EBITDA", {}).get("display_name", "EBITDA (€)")
                             if ebitda_display_name in df_year.index:
                                 df_year.loc[ebitda_display_name, 'Total Annuel'] = df_year.loc[ebitda_display_name, numeric_month_cols].sum()

                             # Calculs dérivés (utilise les noms d'affichage)
                             ebitda_an = get_annual_total(df_year, ebitda_display_name)
                             amort_an = get_annual_total(df_year, table_map.get("Amortissement", {}).get("display_name", "Amortissement (€)"))
                             interets_an = get_annual_total(df_year, table_map.get("Interets_Payes", {}).get("display_name", "Intérêts Payés (€)"))
                             impots_prov_an = get_annual_total(df_year, table_map.get("Impots_Provisionnes", {}).get("display_name", "Impôts Prov. (€)"))
                             principal_an = get_annual_total(df_year, table_map.get("Principal_Rembourse", {}).get("display_name", "Principal Remb. (€)"))
                             tx_impot = config_globale.get('taux_imposition', 25.0) / 100.0

                             ebit_display = table_map.get("EBIT", {}).get("display_name", "EBIT (€)")
                             if pd.notna(ebitda_an) and pd.notna(amort_an): df_year.loc[ebit_display, 'Total Annuel'] = ebitda_an - amort_an
                             else: df_year.loc[ebit_display, 'Total Annuel'] = np.nan

                             ebt_display = table_map.get("EBT", {}).get("display_name", "EBT (€)")
                             ebit_an = get_annual_total(df_year, ebit_display)
                             if pd.notna(ebit_an) and pd.notna(interets_an): df_year.loc[ebt_display, 'Total Annuel'] = ebit_an - interets_an
                             else: df_year.loc[ebt_display, 'Total Annuel'] = np.nan

                             rn_display = table_map.get("Resultat_Net", {}).get("display_name", "Résultat Net (€)")
                             ebt_an = get_annual_total(df_year, ebt_display)
                             if pd.notna(ebt_an) and pd.notna(impots_prov_an): df_year.loc[rn_display, 'Total Annuel'] = ebt_an - impots_prov_an
                             else: df_year.loc[rn_display, 'Total Annuel'] = np.nan

                             ocf_display = table_map.get("OCF_Projet", {}).get("display_name", "OCF Projet (€)")
                             if pd.notna(ebitda_an) and pd.notna(amort_an): df_year.loc[ocf_display, 'Total Annuel'] = (ebitda_an * (1.0 - tx_impot)) + (amort_an * tx_impot)
                             else: df_year.loc[ocf_display, 'Total Annuel'] = np.nan

                             fcfe_display = table_map.get("FCFE", {}).get("display_name", "Free Cash Flow Equity (€)")
                             rn_an = get_annual_total(df_year, rn_display)
                             if pd.notna(rn_an) and pd.notna(amort_an) and pd.notna(principal_an): df_year.loc[fcfe_display, 'Total Annuel'] = rn_an + amort_an - principal_an
                             else: df_year.loc[fcfe_display, 'Total Annuel'] = np.nan

                             solde_dette_display = table_map.get("Solde_Dette_Fin_Mois", {}).get("display_name", "Solde Dette Fin (€)")
                             if solde_dette_display in df_year.index:
                                 last_month_col = numeric_month_cols[-1]
                                 for month in reversed(numeric_month_cols):
                                      if pd.notna(df_year.loc[solde_dette_display, month]) and df_year.loc[solde_dette_display, month] != 0: last_month_col = month; break
                                 df_year.loc[solde_dette_display, 'Total Annuel'] = df_year.loc[solde_dette_display, last_month_col]

                        except Exception as e_calc_deriv:
                             st.warning(f"Année {year}: Erreur calcul totaux dérivés: {e_calc_deriv}")
                        # --- Fin Calcul Totaux Dérivés ---

                        # --- Calcul Mensuel + Annuel Ratios ---
                        indicators_to_process = [
                            ("Taux d'autoconsommation (%)", lambda auto, prod: (auto / prod * 100) if prod > 1e-6 else 0.0, [table_map.get("Autoconsommation_kWh", {}).get("display_name", "Autoconso. (kWh)"), table_map.get("Production_kWh", {}).get("display_name", "Production (kWh)")]),
                            ("Taux d'autoproduction (%)", lambda auto, conso: (auto / conso * 100) if conso > 1e-6 else 0.0, [table_map.get("Autoconsommation_kWh", {}).get("display_name", "Autoconso. (kWh)"), table_map.get("Consommation_kWh", {}).get("display_name", "Consommation (kWh)")]),
                            ("Marge EBITDA (%)", lambda ebitda, revenus: (ebitda / revenus * 100) if revenus > 1e-6 else 0.0, [table_map.get("EBITDA", {}).get("display_name", "EBITDA (€)"), table_map.get("Revenus_Total", {}).get("display_name", "Revenus Totaux (€)")]),
                            ("DSCR", lambda ebitda, impots, service: ((ebitda - impots) / service) if service > 1e-6 else np.inf, [table_map.get("EBITDA", {}).get("display_name", "EBITDA (€)"), table_map.get("Impots_Provisionnes", {}).get("display_name", "Impôts Prov. (€)"), table_map.get("Service_Dette", {}).get("display_name", "Service Dette (€)")])
                        ]

                        for name, calc_lambda, components in indicators_to_process:
                            if name not in df_year.index: df_year.loc[name] = np.nan
                            # Calcul Mensuel
                            for month in numeric_month_cols:
                                try:
                                    comp_values = [df_year.loc[comp, month] for comp in components]
                                    if all(pd.notna(v) for v in comp_values): df_year.loc[name, month] = calc_lambda(*comp_values)
                                    else: df_year.loc[name, month] = np.nan
                                except KeyError: df_year.loc[name, month] = np.nan
                                except Exception: df_year.loc[name, month] = np.nan
                            # Calcul Annuel
                            try:
                                comp_values_annual = [get_annual_total(df_year, comp, np.nan) for comp in components]
                                if all(pd.notna(v) for v in comp_values_annual): df_year.loc[name, 'Total Annuel'] = calc_lambda(*comp_values_annual)
                                else: df_year.loc[name, 'Total Annuel'] = np.nan
                            except KeyError: df_year.loc[name, 'Total Annuel'] = np.nan
                            except Exception: df_year.loc[name, 'Total Annuel'] = np.nan
                        # --- Fin Calcul Ratios ---

                        # --- Réorganisation de l'index basée sur les groupes du JSON ---
                        grouped_indicators = OrderedDict()
                        for info in table_map.values():
                            group = info.get("group", "Autre")
                            display_name = info.get("display_name")
                            if display_name and display_name in df_year.index: # Vérifier existence avant ajout
                                if group not in grouped_indicators: grouped_indicators[group] = []
                                grouped_indicators[group].append(display_name)
                        
                        # Ajouter les ratios calculés à la fin (s'ils ne sont pas déjà dans table_map)
                        ratio_group_name = "4. RATIOS CLÉS (%)" # Groupe spécifique pour ratios
                        ratios_exist = False
                        for name, _, _ in indicators_to_process:
                             if name in df_year.index and name not in [item for sublist in grouped_indicators.values() for item in sublist]:
                                  if not ratios_exist:
                                       grouped_indicators[ratio_group_name] = []
                                       ratios_exist = True
                                  grouped_indicators[ratio_group_name].append(name)

                        final_order = [item for sublist in grouped_indicators.values() for item in sublist]
                        df_year_final = df_year.reindex(final_order)
                        # --- Fin Réorganisation ---

                        # --- Affichage KPIs (utilise get_annual_total et config pour seuils) ---
                        st.markdown("#### Indicateurs clés")
                        kpis = [
                             {"name": "Production", "display_key": table_map.get("Production_kWh", {}).get("display_name", "Production (kWh)"), "unit": "kWh", "icon": "☀️"},
                             {"name": "Taux Autoconso.", "display_key": "Taux d'autoconsommation (%)", "unit": "%", "icon": "🔄", "threshold_key": "kpi_threshold_autoconso"},
                             {"name": "Revenus", "display_key": table_map.get("Revenus_Total", {}).get("display_name", "Revenus Totaux (€)"), "unit": "€", "icon": "💰"},
                             {"name": "EBITDA", "display_key": table_map.get("EBITDA", {}).get("display_name", "EBITDA (€)"), "unit": "€", "icon": "📊", "threshold_key": "kpi_threshold_marge_ebitda"},
                             {"name": "DSCR", "display_key": "DSCR", "unit": None, "icon": "🔒", "threshold_key": "target_dscr"}
                        ]
                        kpi_cols = st.columns(len(kpis))
                        for i, kpi in enumerate(kpis):
                             with kpi_cols[i]:
                                 value_kpi = get_annual_total(df_year_final, kpi["display_key"], np.nan)
                                 formatted_kpi = "N/A"; color_kpi = "black"
                                 if pd.notna(value_kpi) and isinstance(value_kpi, (int, float, np.number)) and np.isfinite(value_kpi):
                                     seuil_min = config_globale.get(kpi.get("threshold_key", "") + "_min", None)
                                     seuil_warning = config_globale.get(kpi.get("threshold_key", "") + "_warning", None)
                                     # Logique seuils par défaut/spécifiques
                                     if kpi["display_key"] == "DSCR": seuil_min = seuil_min if seuil_min is not None else config_globale.get('target_dscr', 1.1); seuil_warning = seuil_warning if seuil_warning is not None else seuil_min + 0.1
                                     elif kpi["display_key"] == "Taux d'autoconsommation (%)": seuil_min = seuil_min if seuil_min is not None else 30.0; seuil_warning = seuil_warning if seuil_warning is not None else 50.0
                                     
                                     # Logique couleur
                                     if seuil_min is not None and value_kpi < seuil_min: color_kpi = "red"
                                     elif seuil_warning is not None and value_kpi < seuil_warning: color_kpi = "orange"
                                     elif "(€)" in kpi["display_key"]: color_kpi = "green" if value_kpi > 0 else "red"
                                     else: color_kpi = "green"
                                     
                                     # Formatage valeur
                                     if kpi["unit"] == "%": formatted_kpi = f"{value_kpi:.1f}%"
                                     elif kpi["unit"] == "€": formatted_kpi = f"{value_kpi:,.0f} €"
                                     elif kpi["unit"] == "kWh": formatted_kpi = f"{value_kpi:,.0f} kWh"
                                     elif kpi["unit"] is None: formatted_kpi = "Inf." if value_kpi == np.inf else f"{value_kpi:.2f}"
                                     else: formatted_kpi = f"{value_kpi:.2f}"
                                 # Affichage Markdown KPI
                                 st.markdown(f'''<div style="text-align: center; padding: 10px; border-radius: 5px; background-color: #f5f5f5;"><div style="font-size: 24px;">{kpi['icon']}</div><div style="font-size: 14px; color: #666;">{kpi['name']}</div><div style="font-size: 18px; font-weight: bold; color: {color_kpi};">{formatted_kpi}</div></div>''', unsafe_allow_html=True)
                        # --- Fin Section KPIs ---

                        # --- Options d'affichage & Formatage/Affichage HTML ---
                        st.markdown("#### Options d'affichage")
                        col1_opt, col2_opt = st.columns(2)
                        with col1_opt: detail_level = st.radio("Niveau de détail:", ["Complet", "Essentiel"], index=0, key=f"detail_{year}")
                        with col2_opt: show_trends = st.checkbox("Afficher tendances Δ%", value=False, key=f"trends_{year}")

                        df_display = df_year_final.copy()
                        if detail_level == "Essentiel":
                             essential_keys_internal = [ # Utiliser clés moteur si possible pour robustesse
                                 "Production_kWh", "Autoconsommation_kWh", "Revenus_Total",
                                 "EBITDA", "Resultat_Net", "FCFE"
                             ]
                             essential_display = [table_map.get(k, {}).get("display_name") for k in essential_keys_internal]
                             essential_display += ["DSCR", "Taux d'autoconsommation (%)", "Marge EBITDA (%)"] # Ajouter ratios clés
                             essential_display = [d for d in essential_display if d is not None and d in df_display.index]

                             df_display = df_display.loc[essential_display]

                        # --- NOUVEAU : Construction Manuelle du HTML avec Groupes ---
                        html_rows = []
                        col_names_html = "".join(f"<th>{col}</th>" for col in df_display.columns)
                        html_rows.append(f"<thead><tr><th>Indicateur</th>{col_names_html}</tr></thead>")
                        html_rows.append("<tbody>")

                        current_group = None
                        # Récupérer les infos de mapping pour les lignes à afficher
                        display_map_info = {info["display_name"]: info for info in table_map.values() if info.get("display_name") in df_display.index}
                        # Ajouter info par défaut pour ratios non mappés
                        default_ratio_info = {"unit": "%", "decimals": 1, "group": "4. RATIOS CLÉS (%)"} # Assigner un groupe par défaut
                        default_dscr_info = {"unit": None, "decimals": 2, "group": "4. RATIOS CLÉS (%)"} # Assigner un groupe par défaut

                        num_cols = len(df_display.columns) + 1 # +1 pour la colonne Indicateur

                        for idx in df_display.index: # Itérer sur l'index ordonné
                            row_info = display_map_info.get(idx)
                            group_name = None
                            # Déterminer le groupe et les infos de formatage
                            if row_info:
                                group_name = row_info.get("group", "Autre")
                                unit = row_info.get("unit")
                                decimals = row_info.get("decimals", 0)
                            else: # Gérer ratios non dans le JSON map
                                if '%' in idx: row_info = default_ratio_info; group_name = row_info["group"]
                                elif idx == 'DSCR': row_info = default_dscr_info; group_name = row_info["group"]
                                else: row_info = {"unit": None, "decimals": 0}; group_name = "Autre" # Fallback
                                unit = row_info.get("unit")
                                decimals = row_info.get("decimals", 0)

                            # Vérifier si le groupe a changé
                            if group_name != current_group:
                                # Ajouter la ligne de séparation/titre de groupe
                                html_rows.append(f'<tr style="background-color: #e8eaf6; font-weight: bold;"><td colspan="{num_cols}" style="padding: 6px 4px; border-top: 1px solid #ccc;">{group_name}</td></tr>')
                                current_group = group_name

                            # Construire la ligne de données
                            cells_html = f"<td>{idx}</td>" # Colonne Indicateur
                            for col in df_display.columns:
                                val = df_display.loc[idx, col]
                                trend_symbol = ""
                                # Logique Tendance (avec f-string corrigé)
                                if show_trends and col != 'Total Annuel' and col != df_display.columns[0]:
                                     try:
                                         prev_col_idx = list(df_display.columns).index(col) - 1
                                         if prev_col_idx >= 0:
                                              prev_col = df_display.columns[prev_col_idx]
                                              prev_val = df_display.loc[idx, prev_col]
                                              if pd.notna(val) and pd.notna(prev_val) and isinstance(val, (int, float, np.number)) and isinstance(prev_val, (int, float, np.number)) and abs(prev_val) > 1e-9: # Éviter division par zéro
                                                   pct_change = (val - prev_val) / abs(prev_val) * 100
                                                   if abs(pct_change) >= 10:
                                                        color = "green" if pct_change > 0 else "red"; arrow = "↑" if pct_change > 0 else "↓"
                                                        trend_symbol = f" <span style='color:{color}; font-size: smaller;'>{arrow}</span>" # Flèche plus petite
                                     except: pass

                                formatted_val = format_value(val, unit, decimals)
                                # Style spécial pour Total Annuel
                                style = ""
                                text_align = "right" # Défaut alignement à droite
                                if col == 'Total Annuel':
                                    style = "font-weight: bold; background-color: #e6f2ff;"

                                cells_html += f'<td style="text-align: {text_align}; {style}">{formatted_val}{trend_symbol}</td>'

                            html_rows.append(f"<tr>{cells_html}</tr>")
                        # Fin boucle sur les indicateurs (idx)

                        html_rows.append("</tbody>")
                        # Assembler le tableau HTML final
                        html_table = f'<table class="dataframe" style="width: 100%; border-collapse: collapse;">{"".join(html_rows)}</table>'

                        st.markdown("---") # Séparateur avant le tableau
                        st.markdown(html_table, unsafe_allow_html=True)
                        # --- FIN NOUVELLE CONSTRUCTION HTML ---


                        # --- Section Export (inchangée, replacée après l'affichage) ---
                        st.markdown("---") # Séparateur
                        st.markdown("#### Export des données de l'année")
                        export_col1, export_col2 = st.columns(2)
                        with export_col1:
                            export_format = st.radio(
                                "Format:", ["Excel (formaté)", "CSV (brut)"],
                                key=f"export_format_{year}", label_visibility="collapsed"
                            )
                        with export_col2:
                            df_export = df_year_final # Utiliser df_year_final
                            if export_format == "Excel (formaté)":
                                buffer = io.BytesIO()
                                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                                    df_export.to_excel(writer, sheet_name=f'Annee {year}')
                                buffer.seek(0)
                                st.download_button(
                                    label="📥 Télécharger Excel", data=buffer,
                                    file_name=f"Synthese_Financiere_Annee_{year}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key=f"download_excel_{year}"
                                )
                            else: # CSV
                                csv_data = df_export.to_csv(sep=';', decimal=',').encode('utf-8')
                                st.download_button(
                                    label="📥 Télécharger CSV", data=csv_data,
                                    file_name=f"Synthese_Financiere_Annee_{year}.csv",
                                    mime="text/csv",
                                    key=f"download_csv_{year}"
                                )
                        # --- Fin Section Export ---

                    except Exception as e_expander:
                        st.error(f"Erreur affichage année {year}: {e_expander}")
                        import traceback
                        st.exception(traceback.format_exc())

        except Exception as e_global:
             st.error(f"Erreur globale affichage synthèse: {e_global}")
             import traceback
             st.exception(traceback.format_exc())

    # --- Onglet Données Brutes (Inchangé) ---
    with tab2:
        st.markdown("### Données Mensuelles Brutes")
        st.dataframe(monthly_df_raw, use_container_width=True)
        st.markdown("#### Résumé Statistique (Vérification NaN)")
        try: st.dataframe(monthly_df_raw.describe(include='all'), use_container_width=True)
        except Exception as e_describe: st.warning(f"Impossible résumé statistique: {e_describe}")