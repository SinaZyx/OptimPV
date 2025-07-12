# modules/monthly_cash_flow_display.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io

try:
    from .financial_display_utils import format_value
except ImportError: 
    from financial_display_utils import format_value

def display_cash_flow_statement_restructured(results: dict | None, selected_year: int):
    """Affiche le tableau des flux de trésorerie mensuels structuré (FTE, FTI, FTF) pour une année."""
    
    if results is None or not isinstance(results, dict) or 'monthly_data' not in results:
        st.warning("Données de résultats ou données mensuelles non disponibles pour les flux de trésorerie.")
        return
    monthly_df_raw = results.get('monthly_data')
    if not isinstance(monthly_df_raw, pd.DataFrame) or monthly_df_raw.empty:
        st.warning("DataFrame mensuel ('monthly_data') invalide ou vide.")
        return

    df_monthly = monthly_df_raw.copy()
    if not isinstance(df_monthly.index, pd.DatetimeIndex):
        try: df_monthly.index = pd.to_datetime(df_monthly.index)
        except Exception as e_dt_conv:
            st.error(f"Impossible de convertir l'index en DatetimeIndex pour CFS: {e_dt_conv}"); return

    df_year_filtered_cfs = df_monthly[df_monthly.index.year == selected_year].copy()
    if df_year_filtered_cfs.empty:
        st.info(f"Aucune donnée mensuelle pour l'année {selected_year} pour le tableau de flux.")
        return

    months_display_order = [d.strftime('%b').capitalize() for d in pd.date_range(start=f'{selected_year}-01-01', periods=12, freq='MS')]
    
    cf_statement_index = [
        "Revenus Clients (HT)", 
        # Section OPEX Détaillée
        "separator_opex_start", 
        "(-) OPEX - Maintenance (HT)",
        "(-) OPEX - Assurance (HT)",
        "(-) OPEX - Gestion Admin. (HT)",
        "(-) OPEX - Provision Onduleur (HT)", 
        "(-) Total Dépenses d'Exploitation (OPEX HT)", 
        "separator_opex_end", 
        "(-) TURPE (HT)",
        "(=) EBITDA", 
        "(-) Impôt sur les Sociétés (Acomptes)", 
        "(+/-) TVA Nette Payée/(Reçue)",
        "FLUX DE TRÉSORERIE D'EXPLOITATION (FTE)",
        "separator_1", 
        "(-) CAPEX Initial (Brut)", "(+/-) Valeur Résiduelle Nette (Fin Projet)",
        "FLUX DE TRÉSORERIE D'INVESTISSEMENT (FTI)",
        "separator_2", 
        "(+) Apport en Fonds Propres", "(+) Subvention d'Investissement Reçue", "(+) Levée de Dette",
        "(-) Intérêts sur Dette Payés", "(-) Remboursement Principal Dette",
        "FLUX DE TRÉSORERIE DE FINANCEMENT (FTF)",
        "separator_3", 
        "VARIATION NETTE DE TRÉSORERIE",
        "Solde Trésorerie Début Période",
        "SOLDE TRÉSORERIE FIN PÉRIODE"
    ]
    cf_data = pd.DataFrame(0.0, index=cf_statement_index, columns=months_display_order + ['Total Année'])

    for month_date_obj in df_year_filtered_cfs.index:
        month_str_col = month_date_obj.strftime('%b').capitalize()
        if month_str_col in cf_data.columns:
            row_data = df_year_filtered_cfs.loc[month_date_obj]
            cf_data.loc["Revenus Clients (HT)", month_str_col] = row_data.get('Revenus_Total', 0)
            
            cf_data.loc["(-) OPEX - Maintenance (HT)", month_str_col] = -row_data.get('OPEX_Maintenance_Mensuel', 0) 
            cf_data.loc["(-) OPEX - Assurance (HT)", month_str_col] = -row_data.get('OPEX_Assurance_Mensuel', 0)   
            cf_data.loc["(-) OPEX - Gestion Admin. (HT)", month_str_col] = -row_data.get('OPEX_Admin_Mensuel', 0) 
            cf_data.loc["(-) OPEX - Provision Onduleur (HT)", month_str_col] = -row_data.get('OPEX_Provision_Onduleur_Mensuel', 0) 
            
            opex_detail_items = [
                "(-) OPEX - Maintenance (HT)", "(-) OPEX - Assurance (HT)", 
                "(-) OPEX - Gestion Admin. (HT)", "(-) OPEX - Provision Onduleur (HT)"
            ] 
            cf_data.loc["(-) Total Dépenses d'Exploitation (OPEX HT)", month_str_col] = cf_data.loc[opex_detail_items, month_str_col].sum(skipna=True)

            cf_data.loc["(-) TURPE (HT)", month_str_col] = -row_data.get('TURPE', 0)
            cf_data.loc["(=) EBITDA", month_str_col] = row_data.get('EBITDA', 0)
            cf_data.loc["(-) Impôt sur les Sociétés (Acomptes)", month_str_col] = -row_data.get('Tax_Payment', 0)
            cf_data.loc["(+/-) TVA Nette Payée/(Reçue)", month_str_col] = -row_data.get('VAT_Payment', 0) 
            cf_data.loc["(-) Intérêts sur Dette Payés", month_str_col] = -row_data.get('Interets_Payes', 0)
            cf_data.loc["(-) Remboursement Principal Dette", month_str_col] = -row_data.get('Principal_Rembourse', 0)

    config_globale_cfs = results.get('config_globale_utilisee', st.session_state.get('config', {}))
    start_date_project_cfs = pd.to_datetime(config_globale_cfs.get("date_debut_ppa", datetime.now().date().isoformat()))
    
    if selected_year == start_date_project_cfs.year:
        first_month_of_project_str = start_date_project_cfs.strftime('%b').capitalize()
        if first_month_of_project_str in cf_data.columns:
            cf_data.loc["(-) CAPEX Initial (Brut)", first_month_of_project_str] = -results.get('capex_scenario_simule', 0)
            cf_data.loc["(+) Apport en Fonds Propres", first_month_of_project_str] = results.get('net_equity_investment', 0)
            cf_data.loc["(+) Subvention d'Investissement Reçue", first_month_of_project_str] = results.get('total_subvention', 0)
            cf_data.loc["(+) Levée de Dette", first_month_of_project_str] = results.get('debt_amount', 0)

    fte_items_calc = [
        "(=) EBITDA", 
        "(-) Impôt sur les Sociétés (Acomptes)", 
        "(+/-) TVA Nette Payée/(Reçue)"
    ]
    fti_items_calc = ["(-) CAPEX Initial (Brut)", "(+/-) Valeur Résiduelle Nette (Fin Projet)"]
    ftf_items_calc = ["(+) Apport en Fonds Propres", 
                      "(+) Subvention d'Investissement Reçue",
                      "(+) Levée de Dette",
                      "(-) Intérêts sur Dette Payés", 
                      "(-) Remboursement Principal Dette"]

    for m_col in months_display_order:
        cf_data.loc["FLUX DE TRÉSORERIE D'EXPLOITATION (FTE)", m_col] = cf_data.loc[fte_items_calc, m_col].sum(skipna=True)
        cf_data.loc["FLUX DE TRÉSORERIE D'INVESTISSEMENT (FTI)", m_col] = cf_data.loc[fti_items_calc, m_col].sum(skipna=True)
        cf_data.loc["FLUX DE TRÉSORERIE DE FINANCEMENT (FTF)", m_col] = cf_data.loc[ftf_items_calc, m_col].sum(skipna=True)
        cf_data.loc["VARIATION NETTE DE TRÉSORERIE", m_col] = (
            cf_data.loc["FLUX DE TRÉSORERIE D'EXPLOITATION (FTE)", m_col] +
            cf_data.loc["FLUX DE TRÉSORERIE D'INVESTISSEMENT (FTI)", m_col] +
            cf_data.loc["FLUX DE TRÉSORERIE DE FINANCEMENT (FTF)", m_col]
        )

    opening_balance_year_display = 0.0 
    for m_col in months_display_order:
        cf_data.loc["Solde Trésorerie Début Période", m_col] = opening_balance_year_display
        cf_data.loc["SOLDE TRÉSORERIE FIN PÉRIODE", m_col] = opening_balance_year_display + cf_data.loc["VARIATION NETTE DE TRÉSORERIE", m_col]
        opening_balance_year_display = cf_data.loc["SOLDE TRÉSORERIE FIN PÉRIODE", m_col]
    
    for idx_row_total in cf_data.index:
        if not idx_row_total.startswith("separator") and \
           idx_row_total not in ["Solde Trésorerie Début Période", "SOLDE TRÉSORERIE FIN PÉRIODE", 
                                  "(=) EBITDA", 
                                  "FLUX DE TRÉSORERIE D'EXPLOITATION (FTE)",
                                  "FLUX DE TRÉSORERIE D'INVESTISSEMENT (FTI)",
                                  "FLUX DE TRÉSORERIE DE FINANCEMENT (FTF)",
                                  "VARIATION NETTE DE TRÉSORERIE"]:
            cf_data.loc[idx_row_total, 'Total Année'] = cf_data.loc[idx_row_total, months_display_order].sum(skipna=True)

    lines_to_sum_monthly_for_annual = [
        "(=) EBITDA", "FLUX DE TRÉSORERIE D'EXPLOITATION (FTE)", 
        "FLUX DE TRÉSORERIE D'INVESTISSEMENT (FTI)", 
        "FLUX DE TRÉSORERIE DE FINANCEMENT (FTF)", 
        "VARIATION NETTE DE TRÉSORERIE"
    ]
    for line_name in lines_to_sum_monthly_for_annual:
        if line_name in cf_data.index: 
             cf_data.loc[line_name, 'Total Année'] = cf_data.loc[line_name, months_display_order].sum(skipna=True)

    if months_display_order: 
        cf_data.loc["Solde Trésorerie Début Période", 'Total Année'] = cf_data.loc["Solde Trésorerie Début Période", months_display_order[0]]
        cf_data.loc["SOLDE TRÉSORERIE FIN PÉRIODE", 'Total Année'] = cf_data.loc["SOLDE TRÉSORERIE FIN PÉRIODE", months_display_order[-1]]
    
    html_output = f"""<style>
        table.dataframe-cfs {{ width:100%; border-collapse: collapse; font-size: 0.9em; }}
        table.dataframe-cfs th {{ text-align:right; padding: 4px 6px; border-bottom: 1px solid #ccc; background-color: #f3f3f3;}}
        table.dataframe-cfs td {{ text-align:right; padding: 4px 6px; border-bottom: 1px dotted #eee; }}
        table.dataframe-cfs td:first-child, table.dataframe-cfs th:first-child {{ text-align:left; }}
        .group-header-cfs td {{background-color: #e8eaf6; font-weight: bold; text-align: left !important; padding: 6px 4px !important; border-top: 2px solid #ccc; border-bottom: 1px solid #ccc;}}
        .total-row-cfs td {{font-weight: bold; border-top: 1px solid #ddd;}}
        .separator-row-cfs td {{height: 0.3em; padding:0 !important; background-color: #fafafa; border:none !important;}}
        .separator-opex-style td {{ 
            height: 0.1em; padding:1px !important; background-color: #f0f0f0; border:none !important;
            border-top: 1px dashed #ccc !important; border-bottom: 1px dashed #ccc !important;
        }}
        table.dataframe-cfs td.opex-detail {{ padding-left: 25px !important; font-style: italic; }} 
    </style>
    <table class='dataframe-cfs'><thead><tr><th>Indicateur</th>"""
    for col_name in cf_data.columns: html_output += f"<th>{col_name}</th>"
    html_output += "</tr></thead><tbody>"

    current_section_header_cfs = ""
    section_map_cfs = {
        "Revenus Clients (HT)": "I. Flux de Trésorerie d'Exploitation (FTE)",
        "separator_opex_start": "I. Flux de Trésorerie d'Exploitation (FTE)", 
        "(-) CAPEX Initial (Brut)": "II. Flux de Trésorerie d'Investissement (FTI)",
        "(+) Apport en Fonds Propres": "III. Flux de Trésorerie de Financement (FTF)",
        "VARIATION NETTE DE TRÉSORERIE": "IV. Réconciliation de Trésorerie"
    }

    for index_name_cfs in cf_data.index:
        row_values_cfs = cf_data.loc[index_name_cfs]
        
        if index_name_cfs in section_map_cfs and section_map_cfs[index_name_cfs] != current_section_header_cfs:
            current_section_header_cfs = section_map_cfs[index_name_cfs]
            colspan_val = len(cf_data.columns) + 1
            html_output += f"<tr class='group-header-cfs'><td colspan='{colspan_val}'>{current_section_header_cfs}</td></tr>"

        if index_name_cfs.startswith("separator_opex"):
            html_output += f"<tr class='separator-opex-style'><td colspan='{len(cf_data.columns)+1}'></td></tr>"; continue
        elif index_name_cfs.startswith("separator"): 
            html_output += f"<tr class='separator-row-cfs'><td colspan='{len(cf_data.columns)+1}'></td></tr>"; continue

        row_class_cfs = ""
        if index_name_cfs.startswith("FLUX DE TRÉSORERIE") or \
           index_name_cfs.startswith("VARIATION NETTE") or \
           index_name_cfs.startswith("SOLDE TRÉSORERIE FIN") or \
           index_name_cfs.startswith("(-) Total Dépenses d'Exploitation"): 
            row_class_cfs = "total-row-cfs"
        
        cell_style_cfs = "font-style: italic;" if index_name_cfs.startswith("(=) EBITDA") else ""
        
        td_class_cfs = ""
        if index_name_cfs.startswith("(-) OPEX - ") and not index_name_cfs.startswith("(-) Total Dépenses d'Exploitation"):
            td_class_cfs = "opex-detail"

        html_output += f"<tr class='{row_class_cfs}'>"
        html_output += f"<td class='{td_class_cfs}' style='text-align:left; {cell_style_cfs}'>{index_name_cfs}</td>"
        for val_cfs in row_values_cfs:
            formatted_val_cfs = format_value(val_cfs, '€', 0, "-") if isinstance(val_cfs, (int, float, np.number)) else val_cfs
            html_output += f"<td style='{cell_style_cfs}'>{formatted_val_cfs}</td>"
        html_output += "</tr>"

    html_output += "</tbody></table>"
    st.markdown(html_output, unsafe_allow_html=True)
    
    if not cf_data.empty:
        st.markdown("---")
        st.markdown("###### Exporter les flux de trésorerie mensuels :", unsafe_allow_html=True)
        scenario_name_for_file = results.get('scenario_name', 'FluxTresorerie')
        year_for_file = selected_year
        export_col1_cfs, export_col2_cfs = st.columns([1,1])
        with export_col1_cfs:
            export_format_cfs = st.radio(
                "Format d'export:", ["Excel", "CSV"],
                key=f"export_format_cfs_{year_for_file}_{scenario_name_for_file}",
                horizontal=True, label_visibility="collapsed"
            )
        with export_col2_cfs:
            df_to_export_cfs = cf_data.copy()
            if export_format_cfs == "Excel":
                buffer_excel_cfs = io.BytesIO()
                with pd.ExcelWriter(buffer_excel_cfs, engine='xlsxwriter') as writer_excel_cfs:
                    df_to_export_cfs.to_excel(writer_excel_cfs, sheet_name=f'Flux_Tresorerie_{year_for_file}')
                buffer_excel_cfs.seek(0)
                st.download_button(
                    label="📥 Télécharger Excel", data=buffer_excel_cfs,
                    file_name=f"Flux_Tresorerie_{scenario_name_for_file}_{year_for_file}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_excel_cfs_{year_for_file}_{scenario_name_for_file}"
                )
            else: # CSV
                csv_data_cfs = df_to_export_cfs.to_csv(sep=';', decimal=',', encoding='utf-8-sig')
                st.download_button(
                    label="📥 Télécharger CSV", data=csv_data_cfs,
                    file_name=f"Flux_Tresorerie_{scenario_name_for_file}_{year_for_file}.csv",
                    mime="text/csv",
                    key=f"download_csv_cfs_{year_for_file}_{scenario_name_for_file}"
                )
    
    st.caption("""
        *Notes :* Les flux initiaux (CAPEX, Financement) sont au Mois 1 de la 1ère année. 
        EBITDA = Revenus HT - Total OPEX HT - TURPE HT.
        La Valeur Résiduelle Nette est actuellement incluse dans le dernier OCF (et donc FTE) via AnalysisEngine.
    """)