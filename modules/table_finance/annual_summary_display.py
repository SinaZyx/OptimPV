# modules/annual_summary_display.py

import streamlit as st
import pandas as pd
import numpy as np
from collections import OrderedDict
import io

try:
    from .financial_display_utils import format_value, load_table_map, get_display_name_from_map, get_table_css, calculate_annual_total_from_monthly
except ImportError:
    from .financial_display_utils import format_value, load_table_map, get_display_name_from_map, get_table_css, calculate_annual_total_from_monthly

# Plus besoin de fonction CSS spécifique, on utilise get_table_css() existant

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
        st.metric("Valeur Terminale Nette",
                  format_value(results.get('valeur_residuelle_nette'), '€', 0),
                  help="Valeur résiduelle de l'installation en fin de projet après déduction des coûts de démantèlement. Cette valeur est incluse dans le calcul de la NPV et de l'IRR du projet.")

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

    # Calculer les composantes du compte de résultat en utilisant la fonction commune
    val_vente_surplus_an = calculate_annual_total_from_monthly(monthly_df_raw, 'Revenus_Surplus', selected_year_for_display)
    val_valorisation_autoconso_an = calculate_annual_total_from_monthly(monthly_df_raw, 'Revenus_Autoconsommation', selected_year_for_display)
    val_prime_autoconso_an = calculate_annual_total_from_monthly(monthly_df_raw, 'Prime_Autoconso_Encaissee', selected_year_for_display)
    
    val_turpe_an = calculate_annual_total_from_monthly(monthly_df_raw, 'TURPE', selected_year_for_display)
    val_maintenance_an = calculate_annual_total_from_monthly(monthly_df_raw, 'OPEX_Maintenance_Mensuel', selected_year_for_display)
    val_assurance_an = calculate_annual_total_from_monthly(monthly_df_raw, 'OPEX_Assurance_Mensuel', selected_year_for_display)
    val_admin_an = calculate_annual_total_from_monthly(monthly_df_raw, 'OPEX_Admin_Mensuel', selected_year_for_display)
    val_provision_onduleur_an = calculate_annual_total_from_monthly(monthly_df_raw, 'OPEX_Provision_Onduleur_Mensuel', selected_year_for_display)
    
    val_amort_an = calculate_annual_total_from_monthly(monthly_df_raw, 'Amortissement', selected_year_for_display)
    val_interets_an = calculate_annual_total_from_monthly(monthly_df_raw, 'Interets_Payes', selected_year_for_display)
    val_total_is_decaisse_an = calculate_annual_total_from_monthly(monthly_df_raw, 'Total_IS_Decaisse_Mois', selected_year_for_display)

    # Calculer les produits financiers RÉALISÉS (débloqués et imposables)
    # Les intérêts capitalisés ne doivent pas apparaître dans le P&L
    val_interets_debloques_an = calculate_annual_total_from_monthly(monthly_df_raw, 'Interets_Debloques_Imposables', selected_year_for_display)

    # Calculer les totaux et sous-totaux AVANT le logging
    ca_total = (val_vente_surplus_an or 0) + (val_valorisation_autoconso_an or 0)
    total_produits_exploitation = ca_total + (val_prime_autoconso_an or 0)
    # Les produits financiers ne comprennent que les intérêts RÉALISÉS (débloqués)
    total_produits_avec_financiers = total_produits_exploitation + (val_interets_debloques_an or 0)
    
    # S'assurer que toutes les valeurs sont numériques
    total_charges_variables = float(val_turpe_an or 0) + float(val_maintenance_an or 0) + float(val_assurance_an or 0) + float(val_admin_an or 0) + float(val_provision_onduleur_an or 0)
    marge_couts_variables = total_produits_exploitation - total_charges_variables
    resultat_exploitation = marge_couts_variables - float(val_amort_an or 0)
    
    # CORRIGER ICI - S'assurer que le calcul se fait correctement
    charges_financieres = float(val_interets_an or 0)
    produits_financiers = float(val_interets_debloques_an or 0)
    
    # Calcul explicite du résultat avant impôt
    resultat_avant_impot = resultat_exploitation - charges_financieres + produits_financiers
    
    # Calcul du résultat net
    impot_societes = float(val_total_is_decaisse_an or 0)
    resultat_net_final = resultat_avant_impot - impot_societes
    
    # Ajouter un log de débogage
    print(f"DEBUG CALCULS: Résultat exploitation={resultat_exploitation}, Charges fin={charges_financieres}, Produits fin={produits_financiers}")
    print(f"DEBUG: Résultat avant impôt={resultat_avant_impot}, IS={impot_societes}, Résultat net={resultat_net_final}")

    # === LOGGING TVA PLACEMENT POUR COMPTE DE RÉSULTAT ===
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'engine_module'))
        from core_analyzer import log_tva_placement
        
        # Logger les valeurs clés du compte de résultat
        log_tva_placement(f"COMPTE DE RÉSULTAT - ANNÉE {selected_year_for_display}", {
            "Intérêts_débloqués_imposables": f"{val_interets_debloques_an:,.2f}€" if val_interets_debloques_an else "0.00€",
            "Revenus_exploitation": f"{total_produits_exploitation:,.2f}€",
            "Intérêts_sur_dette": f"{val_interets_an:,.2f}€" if val_interets_an else "0.00€",
            "IS_décaissé": f"{val_total_is_decaisse_an:,.2f}€" if val_total_is_decaisse_an else "0.00€",
            "Résultat_avant_impôt": f"{resultat_avant_impot:,.2f}€",
            "Résultat_net": f"{resultat_net_final:,.2f}€"
        })
        
        # Détail mensuel des intérêts si disponible
        if 'Interets_Placements_Mensuels' in monthly_df_raw.columns:
            monthly_interests = monthly_df_raw[monthly_df_raw.index.year == selected_year_for_display]['Interets_Placements_Mensuels']
            non_zero_interests = monthly_interests[monthly_interests > 0]
            if not non_zero_interests.empty:
                log_tva_placement(f"DÉTAIL INTÉRÊTS MENSUELS - ANNÉE {selected_year_for_display}", {
                    f"Mois_{idx.month}": f"{val:,.2f}€" for idx, val in non_zero_interests.items()
                })
    except Exception as e:
        # Ne pas bloquer l'affichage si le logging échoue
        print(f"Erreur logging: {e}")
    

    def format_percentage(value, total_ref):
        """Formate un pourcentage par rapport au total de référence"""
        if value is None or pd.isna(value):
            return "-"
        if total_ref is None or pd.isna(total_ref) or total_ref == 0:
            return "-"
        pct = (float(value) / float(total_ref)) * 100
        return f"{pct:.0f} %" if abs(pct - round(pct)) < 0.1 else f"{pct:.1f} %"

    # NOUVEAU: Vérifier si les placements de trésorerie sont activés
    placement_tresorerie_active = config_globale_summary.get('placement_tresorerie_active', False)

    # Créer la structure du compte de résultat
    compte_resultat_data = [
        # PRODUITS D'EXPLOITATION
        {
            'type': 'section_header',
            'label': 'PRODUITS D\'EXPLOITATION',
            'value': None,
            'percentage': None,
            'indent': 0
        },
        {
            'type': 'subtotal',
            'label': 'Chiffre d\'affaires',
            'value': ca_total,
            'percentage': None,
            'indent': 1
        },
        {
            'type': 'detail',
            'label': 'Vente surplus réseau',
            'value': val_vente_surplus_an,
            'percentage': None,
            'indent': 2
        },
        {
            'type': 'detail',
            'label': 'Valorisation autoconsommation',
            'value': val_valorisation_autoconso_an,
            'percentage': format_percentage(ca_total, total_produits_exploitation),
            'indent': 2
        },
        {
            'type': 'subtotal',
            'label': 'Subventions d\'exploitation',
            'value': val_prime_autoconso_an,
            'percentage': None,
            'indent': 1
        },
        {
            'type': 'detail',
            'label': 'Prime à l\'autoconsommation',
            'value': val_prime_autoconso_an,
            'percentage': format_percentage(val_prime_autoconso_an, total_produits_exploitation),
            'indent': 2
        },
        {
            'type': 'main_total',
            'label': 'TOTAL PRODUITS D\'EXPLOITATION',
            'value': total_produits_exploitation,
            'percentage': '100 %',
            'indent': 0
        },

        # CHARGES VARIABLES
        {
            'type': 'section_header',
            'label': 'CHARGES VARIABLES',
            'value': total_charges_variables,
            'percentage': format_percentage(total_charges_variables, total_produits_exploitation),
            'indent': 0
        },
        {
            'type': 'detail',
            'label': 'TURPE injection',
            'value': val_turpe_an,
            'percentage': format_percentage(val_turpe_an, total_produits_exploitation),
            'indent': 1
        },
        {
            'type': 'detail',
            'label': 'Maintenance',
            'value': val_maintenance_an,
            'percentage': format_percentage(val_maintenance_an, total_produits_exploitation),
            'indent': 1
        },
        {
            'type': 'detail',
            'label': 'Assurance',
            'value': val_assurance_an,
            'percentage': format_percentage(val_assurance_an, total_produits_exploitation),
            'indent': 1
        },
        {
            'type': 'detail',
            'label': 'Gestion administrative',
            'value': val_admin_an,
            'percentage': format_percentage(val_admin_an, total_produits_exploitation),
            'indent': 1
        },
        {
            'type': 'detail',
            'label': 'Provision remplacement onduleur (cycle futur)',
            'value': val_provision_onduleur_an,
            'percentage': format_percentage(val_provision_onduleur_an, total_produits_exploitation),
            'indent': 1
        },

        # MARGE SUR COÛTS VARIABLES
        {
            'type': 'subtotal',
            'label': 'MARGE SUR COÛTS VARIABLES',
            'value': marge_couts_variables,
            'percentage': format_percentage(marge_couts_variables, total_produits_exploitation),
            'indent': 0
        },

        # DOTATIONS AUX AMORTISSEMENTS
        {
            'type': 'detail',
            'label': 'DOTATIONS AUX AMORTISSEMENTS',
            'value': val_amort_an,
            'percentage': format_percentage(val_amort_an, total_produits_exploitation),
            'indent': 0
        },

        # RÉSULTAT D'EXPLOITATION
        {
            'type': 'subtotal',
            'label': 'RÉSULTAT D\'EXPLOITATION',
            'value': resultat_exploitation,
            'percentage': format_percentage(resultat_exploitation, total_produits_exploitation),
            'indent': 0
        },

        # CHARGES FINANCIÈRES
        {
            'type': 'section_header',
            'label': 'CHARGES FINANCIÈRES',
            'value': val_interets_an,
            'percentage': format_percentage(val_interets_an, total_produits_exploitation),
            'indent': 0
        },
        {
            'type': 'detail',
            'label': 'Intérêts sur emprunts',
            'value': val_interets_an,
            'percentage': format_percentage(val_interets_an, total_produits_exploitation),
            'indent': 1
        },
    ]

    # NOUVEAU: Ajouter la section PRODUITS FINANCIERS seulement si les placements sont activés
    if placement_tresorerie_active:
        # Insérer avant le RÉSULTAT AVANT IMPÔT
        produits_financiers_section = [
            {
                'type': 'section_header',
                'label': 'PRODUITS FINANCIERS',
                'value': val_interets_debloques_an,
                'percentage': format_percentage(val_interets_debloques_an, total_produits_exploitation),
                'indent': 0
            },
            {
                'type': 'detail',
                'label': 'Intérêts réalisés sur placements',
                'value': val_interets_debloques_an,
                'percentage': format_percentage(val_interets_debloques_an, total_produits_exploitation),
                'indent': 1
            }
        ]
        # Insérer avant les derniers éléments (RÉSULTAT AVANT IMPÔT, IS, RÉSULTAT NET)
        compte_resultat_data.extend(produits_financiers_section)

    # Continuer avec le reste de la structure
    compte_resultat_data.extend([
        # RÉSULTAT AVANT IMPÔT
        {
            'type': 'subtotal',
            'label': 'RÉSULTAT AVANT IMPÔT',
            'value': resultat_avant_impot,
            'percentage': format_percentage(resultat_avant_impot, total_produits_exploitation),
            'indent': 0
        },

        # IMPÔT SUR LES SOCIÉTÉS
        {
            'type': 'detail',
            'label': 'Impôt sur les sociétés',
            'value': val_total_is_decaisse_an,
            'percentage': format_percentage(val_total_is_decaisse_an, total_produits_exploitation),
            'indent': 0
        },

        # RÉSULTAT NET
        {
            'type': 'main_total',
            'label': 'RÉSULTAT NET',
            'value': resultat_net_final,
            'percentage': format_percentage(resultat_net_final, total_produits_exploitation),
            'indent': 0
        }
    ])


    # Affichage du compte de résultat avec le même style que les flux de trésorerie
    st.markdown("##### Compte de Résultat Professionnel")
    
    # Utiliser le CSS existant des flux de trésorerie
    css_styles = get_table_css('annual')
    st.markdown(css_styles, unsafe_allow_html=True)

    # Construire le HTML du compte de résultat avec 3 colonnes
    html_content = ["<table class='dataframe-annual-summary'>"]
    
    # En-tête avec 3 colonnes
    html_content.append(f"<thead><tr><th style='text-align:left;'>Compte de Résultat</th><th style='text-align:right;'>Année {selected_year_for_display}</th><th style='text-align:right;'>%</th></tr></thead>")
    html_content.append("<tbody>")
    
    # Générer les lignes du compte de résultat
    for item in compte_resultat_data:
        # Debug pour les lignes critiques
        if item['label'] in ['RÉSULTAT AVANT IMPÔT', 'RÉSULTAT NET']:
            print(f"DEBUG HTML: {item['label']} = {item['value']}")
        
        # Déterminer la classe CSS selon le type
        if item['type'] == 'section_header':
            row_class = "group-header-style"
        elif item['type'] == 'main_total':
            row_class = "main-total-row-style"
        elif item['type'] == 'subtotal':
            row_class = "total-row-style"
        else:
            row_class = ""
            
        indent_class = f"indent-{item['indent']}" if item['indent'] > 0 else ""
        
        # Formater la valeur - S'assurer qu'on gère bien None et NaN
        formatted_value = "-"
        if item['value'] is not None and not pd.isna(item['value']):
            formatted_value = format_value(item['value'], '€', 0)
        
        # Formater le pourcentage
        formatted_percentage = item['percentage'] or "-"
            
        # Ligne avec 3 colonnes
        html_content.append(f"<tr class='{row_class}'>")
        html_content.append(f"<td class='{indent_class}' style='text-align: left; padding-left: {15 + item['indent'] * 20}px;'>{item['label']}</td>")
        html_content.append(f"<td style='text-align: right;'>{formatted_value}</td>")
        html_content.append(f"<td style='text-align: right; font-size: 0.9em; color: #666;'>{formatted_percentage}</td>")
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
        # Créer un DataFrame pour l'export avec 3 colonnes
        export_data = []
        for item in compte_resultat_data:
            # Formater la valeur avec indentation pour Excel
            label_with_indent = "  " * item['indent'] + item['label']
            
            formatted_value = "-"
            if item['value'] is not None and pd.notna(item['value']):
                formatted_value = format_value(item['value'], '€', 0)
            
            export_data.append({
                'Postes': label_with_indent,
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