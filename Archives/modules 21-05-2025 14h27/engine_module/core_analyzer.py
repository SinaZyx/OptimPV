# modules/engine_module/core_analyzer.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import traceback
import copy
from scipy.optimize import minimize, brentq # brentq est utilisé dans simulate_selling_price
import logging

# Imports depuis les nouveaux modules internes à engine_module
from .engine_utils import NpfModuleWrapper, calculate_payback_months
from .financial_calculations import (
    calculate_wacc,
    calculate_monthly_loan_schedule,
    calculate_lcoe_engineering,
    calculate_avg_dscr_revised
)
from .data_processing import validate_and_prepare_sites_data, aggregate_energy_data
from . import tax_engine

# Importation de TURPE_PROD_RATES depuis config.py (un niveau au-dessus)
try:
    from ..config import TURPE_PROD_RATES
except ImportError:
    logging.getLogger(__name__).error("Impossible d'importer TURPE_PROD_RATES depuis ..config. TURPE sera nul.")
    TURPE_PROD_RATES = {
        "BT<=36kVA": {"CG": {"Unique": 21.60, "CARD": 22.80}, "CC": {"Linky": 22.44}},
        "BT>36kVA": {"CG": {"Unique": 285.96, "CARD": 318.00}, "CC": {"Mensuelle": 288.84}},
        "HTA": {"CG": {"Unique": 725.16, "CARD": 725.16}, "CC": {"Mensuelle": 383.76}}
    }

logger = logging.getLogger(__name__)
# ... (Configuration du logger, inchangée, vous pouvez la garder telle quelle) ...

NPF_IS_REAL_CORE = False
try:
    import numpy_financial as npf_real_core
    NPF_IS_REAL_CORE = True
    logger.info("core_analyzer: numpy_financial (npf_real_core) chargé.")
except ImportError:
    logger.warning("core_analyzer: numpy_financial non trouvé. Fonctions secours via NpfModuleWrapper seront utilisées.")

npf = NpfModuleWrapper(use_real_npf=NPF_IS_REAL_CORE)

class AnalysisEngine:
    def __init__(self, config: dict, scenarios: dict, sites_data: dict[str, pd.DataFrame]):
        if not isinstance(config, dict): raise TypeError("config doit être un dict")
        if not isinstance(scenarios, dict): raise TypeError("scenarios doit être un dict")
        if not isinstance(sites_data, dict): raise TypeError("sites_data doit être un dict")

        self.config = copy.deepcopy(config)
        self.scenarios = copy.deepcopy(scenarios)
        self.sites_data = validate_and_prepare_sites_data(sites_data) # Validate sites_data on init

        self.npf_available = NPF_IS_REAL_CORE
        self.used_aggregated_config = False # Sera défini dans calculate_financial_indicators
        logger.info(f"AnalysisEngine initialisé. npf_available: {self.npf_available}")
        logger.info(f"Sites de données après validation: {list(self.sites_data.keys())}")


    def calculate_financial_indicators(self,
                                       scenario_name: str,
                                       prix_revente: float | None = None,
                                       override_source_prix_autoconso: str | None = None,
                                       sites_config: dict | None = None) -> dict | None:
        start_time_calc = time.time()
        logger.info(f"CALC INDICATORS: Scénario='{scenario_name}', PrixReventeInput={prix_revente}, OverrideSourcePrixAutoc={override_source_prix_autoconso}")
        self.used_aggregated_config = False

        autoconsumption_rate = np.nan; autoproduction_rate = np.nan
        wacc_annual_at = np.nan; re_annual = np.nan; lcoe = np.nan
        irr_equity = np.nan; npv_equity = np.nan; roi_equity = np.nan; payback_equity_years = np.nan
        irr_project = np.nan; npv_project = np.nan; payback_project_years = np.nan; avg_dscr = np.nan

        try:
            if scenario_name not in self.scenarios:
                raise ValueError(f"Scénario '{scenario_name}' invalide.")
            scenario = self.scenarios[scenario_name]
            global_config = self.config

            logger.info(f"CONFIG UTILISÉE - loan_active: {global_config.get('with_loan')}")
            logger.info(f"CONFIG UTILISÉE - debt_ratio: {global_config.get('debt_ratio')}")

            total_capex_base = 0.0
            total_opex_maintenance_base_annual = 0.0
            total_opex_assurance_base_annual = 0.0
            total_opex_admin_base_annual = 0.0
            total_puissance_kwc = 0.0
            total_base_annual_unindexed_inverter_provision = 0.0
            source_des_inputs = "globaux_fallback"
            effective_sites_config = sites_config if sites_config and any(sites_config.values()) else None
            
            if effective_sites_config:
                logger.debug("Utilisation de la configuration par site (sites_config) pour agrégation.")
                self.used_aggregated_config = True
                source_des_inputs = "agreges_par_site"
                for site_id, site_cfg in effective_sites_config.items():
                    if not isinstance(site_cfg, dict): continue
                    site_power = float(site_cfg.get('puissance_kwc', 0.0))
                    site_capex = float(site_cfg.get('capex', 0.0))
                    site_type = site_cfg.get('site_type', 'Producteur')
                    
                    if site_type != "Consommateur Pur":
                        total_opex_maintenance_base_annual += float(site_cfg.get('opex_maintenance', 0.0))
                        total_opex_assurance_base_annual += float(site_cfg.get('opex_insurance', 0.0))
                        total_opex_admin_base_annual += float(site_cfg.get('opex_admin', 0.0))
                    
                    total_puissance_kwc += site_power
                    total_capex_base += site_capex

                    if site_type != "Consommateur Pur" and site_cfg.get("opex_onduleur_provision_site", False):
                        cost_unindexed = float(site_cfg.get("opex_onduleur_total_cost_site", 0.0))
                        lifetime = int(site_cfg.get("opex_onduleur_lifetime_site", 0))
                        if cost_unindexed > 0 and lifetime > 0:
                            total_base_annual_unindexed_inverter_provision += cost_unindexed / lifetime
                capex_base_input = total_capex_base
                puissance_kwc_global = total_puissance_kwc
            else:
                logger.debug("Utilisation de la configuration globale (config) pour les inputs principaux.")
                source_des_inputs = "globaux_directs"
                self.used_aggregated_config = False
                capex_base_input = float(global_config.get('capex_scenario', 0.0)) 
                puissance_kwc_global = float(global_config.get('puissance_kwc_installee', 0.0))
                
                total_opex_maintenance_base_annual = float(global_config.get('opex_maintenance_fallback',0.0))
                total_opex_assurance_base_annual = float(global_config.get('opex_insurance_fallback',0.0))
                total_opex_admin_base_annual = float(global_config.get('opex_admin_fallback',0.0))
                if global_config.get("opex_onduleur_provision_globale", False):
                    cost_unindexed_global = float(global_config.get("opex_onduleur_total_cost_global", 0.0))
                    lifetime_global = int(global_config.get("opex_onduleur_lifetime_global", 0))
                    if cost_unindexed_global > 0 and lifetime_global > 0:
                        total_base_annual_unindexed_inverter_provision = cost_unindexed_global / lifetime_global
            
            capex_brut_total_scenario = capex_base_input * (1 + float(scenario.get('capex_modifier', 0.0)))
            capex_scenario_simule = capex_brut_total_scenario # Gardé pour la sortie resultats['capex_scenario_simule_initial']

            applicable_sub_rate = 0.0
            if puissance_kwc_global <= 3: applicable_sub_rate = float(global_config.get("subvention_rate_le3",100.0))
            elif puissance_kwc_global <= 9: applicable_sub_rate = float(global_config.get("subvention_rate_le9", 80.0))
            elif puissance_kwc_global <= 36: applicable_sub_rate = float(global_config.get("subvention_rate_le36", 150.0))
            elif puissance_kwc_global <= 100: applicable_sub_rate = float(global_config.get("subvention_rate_le100", 100.0))
            elif puissance_kwc_global <= 500: applicable_sub_rate = float(global_config.get("subvention_rate_le500",80.0))
            else: applicable_sub_rate = float(global_config.get("subvention_rate_gt100", 0.0))
            subvention_finale_pour_calculs = applicable_sub_rate * puissance_kwc_global
            
            capex_net_subvention = max(0, capex_brut_total_scenario - subvention_finale_pour_calculs)

            opex_modifier_scenario = float(scenario.get("opex_modifier", 1.0)) # Note: dans votre code c'était scenario.get("opex_modifier", 1.0), ici j'utilise le même que pour capex. Ajustez si besoin.
            opex_maintenance_scenario_annual = total_opex_maintenance_base_annual * opex_modifier_scenario
            opex_assurance_scenario_annual = total_opex_assurance_base_annual * opex_modifier_scenario
            opex_admin_scenario_annual = total_opex_admin_base_annual * opex_modifier_scenario
            
            duree_construction_cfg = int(global_config.get("duree_construction", 0))
            date_debut_operations_str = global_config.get("date_debut_ppa", datetime.now().date().isoformat())
            date_debut_operations = pd.to_datetime(date_debut_operations_str)
            date_debut_simulation_effective = date_debut_operations - pd.DateOffset(months=duree_construction_cfg)
            duree_exploitation_cfg = int(global_config.get("duree_ppa", 240))
            num_total_simulation_months = duree_construction_cfg + duree_exploitation_cfg
            
            degradation_rate_base = float(global_config.get("degradation_rate", 0.005))
            taux_inflation_pct = float(global_config.get("taux_inflation", 2.0))
            adjusted_inflation_annual = taux_inflation_pct / 100.0
            oa_indexed = bool(global_config.get("tarif_oa_indexe_inflation", True))
            inflation_rate_oa_pct = float(global_config.get("taux_inflation_tarif_oa", 1.89))
            inflation_rate_oa_annual = inflation_rate_oa_pct / 100.0
            turpe_indexed = bool(global_config.get("turpe_indexe_inflation", True))
            
            taux_imposition_standard_pct = float(global_config.get("taux_imposition", 25.0))
            tax_rate_decimal = taux_imposition_standard_pct / 100.0
            if hasattr(tax_engine, 'STANDARD_TAX_RATE'): tax_engine.STANDARD_TAX_RATE = tax_rate_decimal
            
            amortissement_duree_years = int(global_config.get("amortissement_duree", 20))
            valeur_residuelle_pct_config = float(global_config.get("valeur_residuelle_pct", 0.0))
            cout_demantelement_pct_config = float(global_config.get("cout_demantelement_pct", 0.0))
            
            cout_fonds_propres_pct_config = float(global_config.get("cout_fonds_propres", 8.0))
            loan_active = global_config.get("with_loan", True)
            debt_ratio_config = float(global_config.get("debt_ratio", 0.80)) if loan_active else 0.0
            debt_term_years_config = int(global_config.get("debt_term_years", 20)) if loan_active else 0
            taux_interet_dette_pct_config = float(global_config.get("taux_interet_dette", 4.0)) if loan_active else 0.0
            taux_interet_dette_annual = taux_interet_dette_pct_config / 100.0
            capitalize_construction_interest = bool(global_config.get("capitalize_construction_interest", True)) # NOUVEAU PARAMÈTRE

            vat_rate_operations = float(global_config.get("taux_tva_operations_pct", 20.0)) / 100.0
            vat_rate_capex = float(global_config.get("taux_tva_capex_pct", 20.0)) / 100.0
            vat_capex_recovery_month_offset = int(global_config.get("vat_capex_recovery_delay_months", 3))
            
            source_prix_autoc_config = global_config.get("source_prix_autoconso", "prix_initial")
            tarif_edf_ref_config = float(global_config.get("tarif_edf_reference", 0.21))

            if puissance_kwc_global <= 9: tarif_oa_base = float(global_config.get("tarif_oa_bracket_le9", 0.07))
            elif puissance_kwc_global <= 100: tarif_oa_base = float(global_config.get("tarif_oa_bracket_le100", 0.06))
            else: tarif_oa_base = float(global_config.get("tarif_oa_bracket_gt100", 0.05))

            if puissance_kwc_global <= 36: actual_turpe_tension = "BT<=36kVA"
            elif puissance_kwc_global <= 250: actual_turpe_tension = "BT>36kVA"
            else: actual_turpe_tension = "HTA"
            turpe_prod_contrat_setting = global_config.get("turpe_prod_contrat", "Unique")
            cg_rate = TURPE_PROD_RATES.get(actual_turpe_tension, {}).get("CG", {}).get(turpe_prod_contrat_setting, 0.0)
            cc_keys = list(TURPE_PROD_RATES.get(actual_turpe_tension, {}).get("CC", {}).keys())
            cc_key_to_use = None
            if actual_turpe_tension == "BT<=36kVA" and "Linky" in cc_keys: cc_key_to_use = "Linky"
            elif cc_keys: cc_key_to_use = cc_keys[0]
            cc_rate = TURPE_PROD_RATES.get(actual_turpe_tension, {}).get("CC", {}).get(cc_key_to_use, 0.0) if cc_key_to_use else 0.0
            turpe_annual_base_scenario = cg_rate + cc_rate
            
            production_modifier_scenario = float(scenario.get("production_modifier", 1.0))
            adjusted_inflation_scenario_rate = adjusted_inflation_annual * float(scenario.get("inflation_modifier", 1.0))
            degradation_rate_scenario_effective = degradation_rate_base * float(scenario.get("degradation_modifier", 1.0))
            
            prix_vente_final_a_utiliser = float(prix_revente) if prix_revente is not None else \
                                    float(global_config.get("prix_vente_initial_slider_fallback", 0.10))
            source_prix_autoc_effective = override_source_prix_autoconso if override_source_prix_autoconso is not None else source_prix_autoc_config
            
            hourly_data_to_return = aggregate_energy_data(self.sites_data, effective_sites_config)
            
            monthly_index = pd.date_range(start=date_debut_simulation_effective, periods=num_total_simulation_months, freq='ME')
            monthly_results_df = pd.DataFrame(index=monthly_index)
            monthly_cols = [
                'Is_Construction_Phase', 'Year_Index', 'Sim_Year', 
                'Year_Index_Operational', 'Sim_Year_Operational', 'Inflation_Factor_Operational', 'Degradation_Factor_Operational',
                'Production_kWh', 'Consommation_kWh', 'Autoconsommation_kWh', 'Surplus_kWh',
                'Tarif_OA_Annuel', 'Prix_Autoconso_Annuel',
                'Revenus_Surplus', 'Revenus_Autoconsommation', 'Revenus_Total',
                'OPEX_Maintenance_Mensuel', 'OPEX_Assurance_Mensuel', 'OPEX_Admin_Mensuel',
                'OPEX_Provision_Onduleur_Mensuel', 'OPEX', 
                'TURPE', 'Amortissement', 'EBITDA', 'EBIT',
                'Interets_Payes', 'Principal_Rembourse', 'EBT', 'Debt_Drawn_This_Month', # Ajout Debt_Drawn_This_Month
                'Tax_Payment', 'Solde_IS_N_1_Paye_Mois', 'Total_IS_Decaisse_Mois',
                'Resultat_Net', 'FCFE', 'OCF_Projet',
                'Solde_Dette_Fin_Mois', 'Service_Dette',
                'VAT_Collectee', 'VAT_Deductible_CAPEX', 'VAT_Deductible_OPEX_TURPE', 
                'VAT_Due_Mois', 'VAT_Payment',
                'BFR_Mensuel', 'Delta_BFR_Mensuel',
                'Solde_Tresorerie_Fin_Mois', 'CAPEX_Initial_Mensuel'
            ]
            for col in monthly_cols: monthly_results_df[col] = 0.0

            if duree_construction_cfg > 0:
                capex_net_mensuel_pour_flux = capex_net_subvention / duree_construction_cfg if capex_net_subvention > 0 else 0.0
            else:
                capex_net_mensuel_pour_flux = capex_net_subvention

            debt_amount = capex_net_subvention * debt_ratio_config if loan_active else 0.0
            logger.info(f"CALCUL NET_EQUITY - capex_net_subvention: {capex_net_subvention}")
            logger.info(f"CALCUL NET_EQUITY - debt_ratio_config: {debt_ratio_config}")
            logger.info(f"CALCUL NET_EQUITY - debt_amount: {debt_amount}")
            net_equity_investment = capex_net_subvention - debt_amount
            logger.info(f"CALCUL NET_EQUITY - net_equity_investment: {net_equity_investment}")
            EQUITY_INVESTMENT_THRESHOLD = 1.0 
            is_equity_negligible = abs(net_equity_investment) < EQUITY_INVESTMENT_THRESHOLD
            logger.info(f"CALCUL NET_EQUITY - is_equity_negligible: {is_equity_negligible}")

            current_debt_drawn_balance = 0.0
            accumulated_capitalized_interest = 0.0
            loan_amortization_schedule_generated = False
            operation_phase_loan_interests = np.zeros(duree_exploitation_cfg)
            operation_phase_loan_principals = np.zeros(duree_exploitation_cfg)
            
            val_residuelle_montant = capex_net_subvention * valeur_residuelle_pct_config
            base_amortissable = capex_net_subvention - val_residuelle_montant
            annual_depreciation_base = base_amortissable / amortissement_duree_years if amortissement_duree_years > 0 else 0.0
            tva_sur_capex_initial = capex_brut_total_scenario * vat_rate_capex

            df_agg_for_ref = hourly_data_to_return.set_index('Temps')
            ref_year = df_agg_for_ref.index.year.min() if not df_agg_for_ref.empty else date_debut_operations.year
            reference_data_ts = df_agg_for_ref[df_agg_for_ref.index.year == ref_year].copy() if not df_agg_for_ref.empty else pd.DataFrame()


            loss_carryforward_balance = 0.0; annual_tax_calculated_prev_year = 0.0
            current_quarterly_acompte_is = 0.0
            current_operational_year_tracker = -1
            opex_maint_indexed_annual_op = opex_maintenance_scenario_annual
            opex_assur_indexed_annual_op = opex_assurance_scenario_annual
            opex_admin_indexed_annual_op = opex_admin_scenario_annual
            inverter_prov_indexed_annual_op = total_base_annual_unindexed_inverter_provision
            turpe_indexed_annual_op = turpe_annual_base_scenario
            depreciation_annual_op = annual_depreciation_base
            oa_rate_annual_op = tarif_oa_base
            # ... (initialisation prix_autoc_annual_op)
            if source_prix_autoc_effective == 'prix_initial': prix_autoc_annual_op = prix_vente_final_a_utiliser
            elif source_prix_autoc_effective == 'tarif_edf': prix_autoc_annual_op = tarif_edf_ref_config
            elif source_prix_autoc_effective == 'tarif_oa': prix_autoc_annual_op = oa_rate_annual_op
            else: prix_autoc_annual_op = prix_vente_final_a_utiliser # Fallback

            solde_IS_N_1_annee_precedente_a_payer_en_N = 0.0
            mois_paiement_solde_is = int(global_config.get("mois_paiement_solde_is", 5))
            bfr_receivables_days_config = float(global_config.get("bfr_receivables_days", 30.0))
            bfr_payables_days_config = float(global_config.get("bfr_payables_days", 15.0))
            bfr_previous_month_val = 0.0
            vat_credit_carryforward = 0.0 # Initialisé avant la boucle

            for month_idx in range(num_total_simulation_months):
                current_month_end_date = monthly_index[month_idx]
                is_construction_phase = month_idx < duree_construction_cfg
                monthly_results_df.loc[current_month_end_date, 'Is_Construction_Phase'] = 1.0 if is_construction_phase else 0.0
                
                monthly_results_df.loc[current_month_end_date, 'CAPEX_Initial_Mensuel'] = capex_net_mensuel_pour_flux if is_construction_phase else 0.0

                current_drawdown_for_month = 0.0
                if is_construction_phase and loan_active:
                    capex_this_month_for_debt_draw = monthly_results_df.loc[current_month_end_date, 'CAPEX_Initial_Mensuel']
                    if capex_net_subvention > 1e-6:
                        proportion_of_total_capex = capex_this_month_for_debt_draw / capex_net_subvention
                        current_drawdown_for_month = debt_amount * proportion_of_total_capex
                    elif debt_amount > 0 and duree_construction_cfg > 0: # Si CAPEX total est nul mais dette existe (improbable)
                        current_drawdown_for_month = debt_amount / duree_construction_cfg
                elif not is_construction_phase and month_idx == duree_construction_cfg and debt_amount > 0 and duree_construction_cfg == 0 and loan_active: 
                    # Cas spécifique: pas de durée de construction, tout le CAPEX et la dette au premier mois d'opération
                    current_drawdown_for_month = debt_amount
                
                current_debt_drawn_balance += current_drawdown_for_month
                monthly_results_df.loc[current_month_end_date, 'Debt_Drawn_This_Month'] = current_drawdown_for_month

                interest_m_calc = 0.0
                principal_m_calc = 0.0

                if loan_active:
                    if is_construction_phase:
                        if current_debt_drawn_balance > 0:
                            interest_m_calc = current_debt_drawn_balance * (taux_interet_dette_annual / 12.0)
                        if capitalize_construction_interest:
                            accumulated_capitalized_interest += interest_m_calc
                            # interest_m_calc pour Interets_Payes sera 0 car capitalisé
                        # principal_m_calc reste 0.0
                    else: # Phase d'exploitation
                        if not loan_amortization_schedule_generated:
                            final_loan_principal_for_amortization = current_debt_drawn_balance + accumulated_capitalized_interest
                            loan_term_for_amortization_years = debt_term_years_config
                            num_amort_months = duree_exploitation_cfg 

                            if final_loan_principal_for_amortization > 1e-6 and loan_term_for_amortization_years > 0:
                                op_interests_sched, op_principals_sched, _ = calculate_monthly_loan_schedule(
                                    principal=final_loan_principal_for_amortization,
                                    annual_rate=taux_interet_dette_annual,
                                    term_years=loan_term_for_amortization_years,
                                    num_months_simulation=num_amort_months 
                                )
                                operation_phase_loan_interests[:len(op_interests_sched)] = op_interests_sched
                                operation_phase_loan_principals[:len(op_principals_sched)] = op_principals_sched
                            loan_amortization_schedule_generated = True

                        operational_month_idx = month_idx - duree_construction_cfg
                        if operational_month_idx < len(operation_phase_loan_interests):
                            interest_m_calc = operation_phase_loan_interests[operational_month_idx]
                            principal_m_calc = operation_phase_loan_principals[operational_month_idx]
                        
                        current_debt_drawn_balance -= principal_m_calc 
                
                # Affecter les valeurs calculées au DataFrame
                monthly_results_df.loc[current_month_end_date, 'Interets_Payes'] = interest_m_calc if not (is_construction_phase and capitalize_construction_interest) else 0.0
                monthly_results_df.loc[current_month_end_date, 'Principal_Rembourse'] = principal_m_calc
                monthly_results_df.loc[current_month_end_date, 'Service_Dette'] = monthly_results_df.loc[current_month_end_date, 'Interets_Payes'] + principal_m_calc
                monthly_results_df.loc[current_month_end_date, 'Solde_Dette_Fin_Mois'] = max(0, current_debt_drawn_balance)

                # ... (Suite de la boucle mensuelle pour P&L, Energie, Fiscalité, BFR - largely inchangé)
                # Mettre à jour les sections Energie, OPEX, Amortissement, P&L
                year_idx_op_loop = -1; sim_year_num_op_loop = 0
                if not is_construction_phase:
                    op_month_idx_loop = month_idx - duree_construction_cfg
                    year_idx_op_loop = op_month_idx_loop // 12
                    sim_year_num_op_loop = year_idx_op_loop + 1
                    if year_idx_op_loop != current_operational_year_tracker:
                        # ... (mises à jour des facteurs d'inflation, dégradation, opex, turpe, amortissement, tarifs annuels) ...
                        # (Ce bloc est important et doit être correctement maintenu comme dans votre version précédente)
                        inflation_factor_op_year_current = (1 + adjusted_inflation_scenario_rate) ** year_idx_op_loop
                        degradation_factor_op_year_current = (1 - degradation_rate_scenario_effective) ** year_idx_op_loop
                        opex_maint_indexed_annual_op = opex_maintenance_scenario_annual * inflation_factor_op_year_current
                        opex_assur_indexed_annual_op = opex_assurance_scenario_annual * inflation_factor_op_year_current
                        opex_admin_indexed_annual_op = opex_admin_scenario_annual * inflation_factor_op_year_current
                        inverter_prov_indexed_annual_op = total_base_annual_unindexed_inverter_provision * inflation_factor_op_year_current
                        turpe_indexed_annual_op = turpe_annual_base_scenario * (inflation_factor_op_year_current if turpe_indexed else 1.0)
                        depreciation_annual_op = annual_depreciation_base if year_idx_op_loop < amortissement_duree_years else 0.0
                        oa_rate_annual_op = tarif_oa_base * ((1 + inflation_rate_oa_annual)**year_idx_op_loop if oa_indexed else 1.0)
                        if source_prix_autoc_effective == 'prix_initial': prix_autoc_annual_op = prix_vente_final_a_utiliser * inflation_factor_op_year_current
                        elif source_prix_autoc_effective == 'tarif_edf': prix_autoc_annual_op = tarif_edf_ref_config * inflation_factor_op_year_current
                        elif source_prix_autoc_effective == 'tarif_oa': prix_autoc_annual_op = oa_rate_annual_op
                        else: prix_autoc_annual_op = prix_vente_final_a_utiliser * inflation_factor_op_year_current
                        current_operational_year_tracker = year_idx_op_loop

                monthly_results_df.loc[current_month_end_date, 'Year_Index_Operational'] = year_idx_op_loop
                monthly_results_df.loc[current_month_end_date, 'Sim_Year_Operational'] = sim_year_num_op_loop
                monthly_results_df.loc[current_month_end_date, 'Inflation_Factor_Operational'] = inflation_factor_op_year_current if not is_construction_phase else 1.0
                monthly_results_df.loc[current_month_end_date, 'Degradation_Factor_Operational'] = degradation_factor_op_year_current if not is_construction_phase else 1.0

                if is_construction_phase:
                    monthly_results_df.loc[current_month_end_date, ['Production_kWh', 'Consommation_kWh', 'Autoconsommation_kWh', 'Surplus_kWh', 'Revenus_Surplus', 'Revenus_Autoconsommation', 'Revenus_Total', 'OPEX_Maintenance_Mensuel', 'OPEX_Assurance_Mensuel', 'OPEX_Admin_Mensuel', 'OPEX_Provision_Onduleur_Mensuel', 'OPEX', 'TURPE', 'Amortissement']] = 0.0
                else:
                    # ... (calcul Energie: Production, Consommation, Autoconsommation, Surplus - comme avant) ...
                    monthly_results_df.loc[current_month_end_date, 'Tarif_OA_Annuel'] = oa_rate_annual_op
                    monthly_results_df.loc[current_month_end_date, 'Prix_Autoconso_Annuel'] = prix_autoc_annual_op
                    prod_m_calc, cons_m_calc, auto_m_calc, surplus_m_calc = 0.0, 0.0, 0.0, 0.0
                    df_hourly_month_calc = pd.DataFrame(columns=['production', 'consumption'])
                    try:
                        current_month_number_calc = current_month_end_date.month
                        if not reference_data_ts.empty and isinstance(reference_data_ts.index, pd.DatetimeIndex):
                            ref_monthly_energy_slice_calc = reference_data_ts[reference_data_ts.index.month == current_month_number_calc]
                        else: ref_monthly_energy_slice_calc = pd.DataFrame(columns=['production_kwh', 'consumption_kwh'])
                        if not ref_monthly_energy_slice_calc.empty:
                            prod_ref_s_calc = ref_monthly_energy_slice_calc['production_kwh']
                            cons_ref_s_calc = ref_monthly_energy_slice_calc['consumption_kwh']
                            prod_adj_s_calc = prod_ref_s_calc * degradation_factor_op_year_current * production_modifier_scenario
                            df_hourly_month_calc = pd.DataFrame({'production': prod_adj_s_calc, 'consumption': cons_ref_s_calc}).fillna(0)
                            autoconsommation_horaire_np_calc = np.minimum(df_hourly_month_calc['production'].values, df_hourly_month_calc['consumption'].values)
                            surplus_horaire_np_calc = np.maximum(0, df_hourly_month_calc['production'].values - autoconsommation_horaire_np_calc)
                            prod_m_calc = df_hourly_month_calc['production'].values.sum()
                            cons_m_calc = df_hourly_month_calc['consumption'].values.sum()
                            auto_m_calc = autoconsommation_horaire_np_calc.sum()
                            surplus_m_calc = surplus_horaire_np_calc.sum()
                    except Exception as e_autoc_loop: logger.error(f"ERREUR AUTOCONSO MENSUELLE {current_month_end_date.month}: {e_autoc_loop}", exc_info=True)
                    monthly_results_df.loc[current_month_end_date, 'Production_kWh'] = prod_m_calc
                    monthly_results_df.loc[current_month_end_date, 'Consommation_kWh'] = cons_m_calc
                    monthly_results_df.loc[current_month_end_date, 'Autoconsommation_kWh'] = auto_m_calc
                    monthly_results_df.loc[current_month_end_date, 'Surplus_kWh'] = surplus_m_calc
                    rev_surplus_m = surplus_m_calc * oa_rate_annual_op; rev_auto_m = auto_m_calc * prix_autoc_annual_op
                    monthly_results_df.loc[current_month_end_date, 'Revenus_Surplus'] = rev_surplus_m
                    monthly_results_df.loc[current_month_end_date, 'Revenus_Autoconsommation'] = rev_auto_m
                    monthly_results_df.loc[current_month_end_date, 'Revenus_Total'] = rev_surplus_m + rev_auto_m
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Maintenance_Mensuel'] = opex_maint_indexed_annual_op / 12.0
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Assurance_Mensuel'] = opex_assur_indexed_annual_op / 12.0
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Admin_Mensuel'] = opex_admin_indexed_annual_op / 12.0
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Provision_Onduleur_Mensuel'] = inverter_prov_indexed_annual_op / 12.0
                    monthly_results_df.loc[current_month_end_date, 'OPEX'] = (opex_maint_indexed_annual_op + opex_assur_indexed_annual_op + opex_admin_indexed_annual_op + inverter_prov_indexed_annual_op) / 12.0
                    monthly_results_df.loc[current_month_end_date, 'TURPE'] = turpe_indexed_annual_op / 12.0
                    monthly_results_df.loc[current_month_end_date, 'Amortissement'] = depreciation_annual_op / 12.0
                
                ebitda_m_loop = (monthly_results_df.loc[current_month_end_date, 'Revenus_Total'] - 
                                 monthly_results_df.loc[current_month_end_date, 'OPEX'] - 
                                 monthly_results_df.loc[current_month_end_date, 'TURPE'])
                monthly_results_df.loc[current_month_end_date, 'EBITDA'] = ebitda_m_loop
                ebit_m_loop = ebitda_m_loop - monthly_results_df.loc[current_month_end_date, 'Amortissement']
                monthly_results_df.loc[current_month_end_date, 'EBIT'] = ebit_m_loop
                
                # Utiliser les intérêts calculés plus haut (interest_m_calc)
                ebt_m_before_loss_loop = ebit_m_loop - monthly_results_df.loc[current_month_end_date, 'Interets_Payes']
                taxable_ebt_m_loop, loss_carryforward_balance = tax_engine.apply_loss_carryforward_cap(ebt_m_before_loss_loop, loss_carryforward_balance)
                monthly_results_df.loc[current_month_end_date, 'EBT'] = taxable_ebt_m_loop
                monthly_results_df.loc[current_month_end_date, 'Resultat_Net'] = taxable_ebt_m_loop # Base pour IS, sera ajusté par IS décaissé pour FCFE

                total_tax_paid_this_month_loop = 0.0
                if current_month_end_date.month in [3, 6, 9, 12]: total_tax_paid_this_month_loop += current_quarterly_acompte_is
                if current_month_end_date.month == mois_paiement_solde_is:
                    total_tax_paid_this_month_loop += solde_IS_N_1_annee_precedente_a_payer_en_N
                    monthly_results_df.loc[current_month_end_date, 'Solde_IS_N_1_Paye_Mois'] = solde_IS_N_1_annee_precedente_a_payer_en_N
                monthly_results_df.loc[current_month_end_date, 'Tax_Payment'] = total_tax_paid_this_month_loop
                monthly_results_df.loc[current_month_end_date, 'Total_IS_Decaisse_Mois'] = total_tax_paid_this_month_loop

                if current_month_end_date.month == 12:
                    ebt_annual_for_tax_loop = monthly_results_df[monthly_results_df.index.year == current_month_end_date.year]['EBT'].sum()
                    annual_tax_calculated_this_year_loop = tax_engine.calculate_corporate_tax_pme(ebt_annual_for_tax_loop)
                    solde_IS_N_1_annee_precedente_a_payer_en_N = annual_tax_calculated_prev_year - (tax_engine.calculate_quarterly_installment(annual_tax_calculated_prev_year) * tax_engine.ACOMPTE_COUNT)
                    annual_tax_calculated_prev_year = annual_tax_calculated_this_year_loop
                    current_quarterly_acompte_is = tax_engine.calculate_quarterly_installment(annual_tax_calculated_prev_year)
                
                # TVA (avec logique de remboursement)
                rev_total_m_vat = monthly_results_df.loc[current_month_end_date, 'Revenus_Total']
                opex_m_vat = monthly_results_df.loc[current_month_end_date, 'OPEX']
                turpe_m_vat = monthly_results_df.loc[current_month_end_date, 'TURPE']
                vat_collectee_m_vat = rev_total_m_vat * vat_rate_operations
                vat_ded_opex_turpe_m_vat = (opex_m_vat + turpe_m_vat) * vat_rate_operations
                vat_ded_capex_m_vat = 0.0
                if month_idx == vat_capex_recovery_month_offset: vat_ded_capex_m_vat = tva_sur_capex_initial
                tva_nette_du_mois_avant_report_vat = vat_collectee_m_vat - vat_ded_opex_turpe_m_vat - vat_ded_capex_m_vat
                solde_tva_a_regulariser_vat = tva_nette_du_mois_avant_report_vat + vat_credit_carryforward
                vat_payment_this_month_final_vat = 0.0
                nouveau_vat_credit_carryforward_pour_mois_suivant_vat = 0.0
                remboursement_credit_tva_actif_cfg = bool(global_config.get("remboursement_credit_tva_actif", True))
                seuil_declenchement_remboursement_tva_cfg = float(global_config.get("seuil_remboursement_tva", 500.0))
                if solde_tva_a_regulariser_vat > 0:
                    vat_payment_this_month_final_vat = solde_tva_a_regulariser_vat
                    nouveau_vat_credit_carryforward_pour_mois_suivant_vat = 0.0
                else:
                    if remboursement_credit_tva_actif_cfg and abs(solde_tva_a_regulariser_vat) >= seuil_declenchement_remboursement_tva_cfg:
                        vat_payment_this_month_final_vat = solde_tva_a_regulariser_vat
                        nouveau_vat_credit_carryforward_pour_mois_suivant_vat = 0.0
                    else:
                        vat_payment_this_month_final_vat = 0.0
                        nouveau_vat_credit_carryforward_pour_mois_suivant_vat = solde_tva_a_regulariser_vat
                vat_credit_carryforward = nouveau_vat_credit_carryforward_pour_mois_suivant_vat
                monthly_results_df.loc[current_month_end_date, 'VAT_Collectee'] = vat_collectee_m_vat
                monthly_results_df.loc[current_month_end_date, 'VAT_Deductible_CAPEX'] = vat_ded_capex_m_vat
                monthly_results_df.loc[current_month_end_date, 'VAT_Deductible_OPEX_TURPE'] = vat_ded_opex_turpe_m_vat
                monthly_results_df.loc[current_month_end_date, 'VAT_Due_Mois'] = solde_tva_a_regulariser_vat
                monthly_results_df.loc[current_month_end_date, 'VAT_Payment'] = vat_payment_this_month_final_vat

                # BFR
                bfr_rev_total_m = monthly_results_df.loc[current_month_end_date, 'Revenus_Total'] # Utiliser la valeur déjà dans le df
                bfr_opex_m = monthly_results_df.loc[current_month_end_date, 'OPEX']
                bfr_turpe_m = monthly_results_df.loc[current_month_end_date, 'TURPE']
                bfr_receivables_this_month_loop = (bfr_rev_total_m / 30.0) * bfr_receivables_days_config if not is_construction_phase else 0.0
                bfr_payables_this_month_loop = ((bfr_opex_m + bfr_turpe_m) / 30.0) * bfr_payables_days_config if not is_construction_phase else 0.0
                bfr_current_month_val_loop = bfr_receivables_this_month_loop - bfr_payables_this_month_loop
                delta_bfr_this_month_loop = bfr_current_month_val_loop - bfr_previous_month_val
                monthly_results_df.loc[current_month_end_date, 'BFR_Mensuel'] = bfr_current_month_val_loop
                monthly_results_df.loc[current_month_end_date, 'Delta_BFR_Mensuel'] = delta_bfr_this_month_loop
                bfr_previous_month_val = bfr_current_month_val_loop
            # FIN DE LA BOUCLE MENSUELLE

            # --- CALCULS POST-BOUCLE ---
            
            # Séries pour FCFE et OCF_Projet
            amortissement_mensuel_series_post = monthly_results_df['Amortissement'].fillna(0)
            principal_rembourse_mensuel_post = monthly_results_df['Principal_Rembourse'].fillna(0) # Vient de la nouvelle logique de dette
            ebt_mensuel_post = monthly_results_df['EBT'].fillna(0)
            is_decaisse_total_mensuel_post = monthly_results_df['Total_IS_Decaisse_Mois'].fillna(0)
            vat_payment_mensuel_post = monthly_results_df['VAT_Payment'].fillna(0) # Vient de la nouvelle logique TVA
            delta_bfr_mensuel_series_post = monthly_results_df['Delta_BFR_Mensuel'].fillna(0)
            capex_net_mensuel_series_post = monthly_results_df['CAPEX_Initial_Mensuel'].fillna(0)
            
            # Recalculer debt_drawn_monthly_series et equity_injected_monthly_series proprement
            # car elles dépendent de CAPEX_Initial_Mensuel qui est rempli dans la boucle
            debt_drawn_monthly_series_post = pd.Series(0.0, index=monthly_results_df.index)
            equity_injected_monthly_series_post = pd.Series(0.0, index=monthly_results_df.index)

            if duree_construction_cfg > 0:
                for idx_constr_post in monthly_results_df[monthly_results_df['Is_Construction_Phase']==1].index:
                    capex_net_ce_mois_post = monthly_results_df.loc[idx_constr_post, 'CAPEX_Initial_Mensuel']
                    if capex_net_subvention > 1e-6 :
                        ratio_ce_mois_post = capex_net_ce_mois_post / capex_net_subvention
                        if loan_active: debt_drawn_monthly_series_post.loc[idx_constr_post] = debt_amount * ratio_ce_mois_post
                        equity_injected_monthly_series_post.loc[idx_constr_post] = net_equity_investment * ratio_ce_mois_post
            elif loan_active : # Pas de construction, tout au premier mois
                debt_drawn_monthly_series_post.iloc[0] = debt_amount
                equity_injected_monthly_series_post.iloc[0] = net_equity_investment
            
            # S'assurer que 'Debt_Drawn_This_Month' est cohérent avec debt_drawn_monthly_series_post
            monthly_results_df['Debt_Drawn_This_Month'] = debt_drawn_monthly_series_post

            net_debt_issued_monthly_series_post = debt_drawn_monthly_series_post - principal_rembourse_mensuel_post
            
            monthly_results_df['FCFE'] = (
                ebt_mensuel_post 
                - is_decaisse_total_mensuel_post 
                + amortissement_mensuel_series_post 
                - vat_payment_mensuel_post 
                - delta_bfr_mensuel_series_post 
                - capex_net_mensuel_series_post # CAPEX est une sortie, donc on le soustrait s'il est positif
                + net_debt_issued_monthly_series_post
            )

            ebitda_mensuel_series_post = monthly_results_df['EBITDA'].fillna(0)
            ebit_mensuel_series_post = monthly_results_df['EBIT'].fillna(0)
            
            impot_sur_ebit_mensuel_series_post = pd.Series(0.0, index=monthly_results_df.index)
            ebit_annuel_series_post = ebit_mensuel_series_post.groupby(ebit_mensuel_series_post.index.year).sum()
            loss_carryforward_balance_for_ebit_calc_post = 0.0

            for year_post in ebit_annuel_series_post.index:
                current_year_ebit_post = ebit_annuel_series_post.loc[year_post]
                taxable_ebit_for_year_post, loss_carryforward_balance_for_ebit_calc_post = tax_engine.apply_loss_carryforward_cap(
                    current_year_ebit_post, loss_carryforward_balance_for_ebit_calc_post
                )
                impot_theorique_annuel_sur_ebit_post = tax_engine.calculate_corporate_tax_pme(taxable_ebit_for_year_post)
                if impot_theorique_annuel_sur_ebit_post > 0:
                    ebit_mensuels_annee_en_cours_post = ebit_mensuel_series_post[ebit_mensuel_series_post.index.year == year_post]
                    total_ebit_positif_annee_post = ebit_mensuels_annee_en_cours_post[ebit_mensuels_annee_en_cours_post > 0].sum()
                    for month_date_post in ebit_mensuels_annee_en_cours_post.index:
                        if total_ebit_positif_annee_post > 1e-6:
                            prorata_post = ebit_mensuels_annee_en_cours_post.loc[month_date_post] / total_ebit_positif_annee_post if ebit_mensuels_annee_en_cours_post.loc[month_date_post] > 0 else 0
                            impot_sur_ebit_mensuel_series_post.loc[month_date_post] = impot_theorique_annuel_sur_ebit_post * prorata_post
                        elif len(ebit_mensuels_annee_en_cours_post[ebit_mensuels_annee_en_cours_post > 0]) > 0:
                            impot_sur_ebit_mensuel_series_post.loc[month_date_post] = (impot_theorique_annuel_sur_ebit_post / len(ebit_mensuels_annee_en_cours_post[ebit_mensuels_annee_en_cours_post > 0])) if ebit_mensuels_annee_en_cours_post.loc[month_date_post] > 0 else 0
                        else:
                            impot_sur_ebit_mensuel_series_post.loc[month_date_post] = impot_theorique_annuel_sur_ebit_post / 12.0
            
            nopat_mensuel_post = ebit_mensuel_series_post - impot_sur_ebit_mensuel_series_post
            
            monthly_results_df['OCF_Projet'] = (
                nopat_mensuel_post
                + amortissement_mensuel_series_post
                - capex_net_mensuel_series_post
                - delta_bfr_mensuel_series_post
                - vat_payment_mensuel_post 
            )
            
            initial_cash_balance_at_true_t0 = float(global_config.get("initial_cash_balance", 0.0)) # PARAMÉTRÉ
            total_company_net_cash_flow_monthly = monthly_results_df['FCFE'].fillna(0) + equity_injected_monthly_series_post.fillna(0)
            cumulative_total_company_net_cash_flow = total_company_net_cash_flow_monthly.cumsum()
            monthly_results_df['Solde_Tresorerie_Fin_Mois'] = initial_cash_balance_at_true_t0 + cumulative_total_company_net_cash_flow

            # Calculs financiers finaux (WACC, NPV, IRR, LCOE, DSCR)
            re_annual = float(cout_fonds_propres_pct_config)
            wacc_annual_at = calculate_wacc(
                debt_ratio=debt_ratio_config,
                taux_interet_dette_pct=taux_interet_dette_pct_config,
                taux_imposition_pct=taux_imposition_standard_pct,
                cout_fonds_propres_pct=re_annual,
                wacc_type="after_tax"
            )
            if wacc_annual_at is None: wacc_annual_at = 6.0 # Fallback
            
            re_monthly = (1 + re_annual/100)**(1/12) - 1
            wacc_monthly_at = (1 + wacc_annual_at/100)**(1/12) - 1

            equity_cash_flows_monthly_final = monthly_results_df['FCFE'].fillna(0).values # Utiliser FCFE directement
            project_cash_flows_monthly_final = monthly_results_df['OCF_Projet'].fillna(0).values # Utiliser OCF_Projet directement

            val_residuelle_montant_fin_calc = capex_net_subvention * valeur_residuelle_pct_config
            cout_demantelement_montant_fin_calc = capex_brut_total_scenario * cout_demantelement_pct_config
            terminal_value_net_projet_calc = val_residuelle_montant_fin_calc - cout_demantelement_montant_fin_calc
            
            if len(project_cash_flows_monthly_final) > 0:
                project_cash_flows_monthly_final[-1] += terminal_value_net_projet_calc
            
            # NPV, IRR Equity (avec gestion is_equity_negligible)
            npv_equity = npf.npv(re_monthly, equity_cash_flows_monthly_final) if pd.notna(re_monthly) else np.nan
            if is_equity_negligible:
                irr_equity = np.nan
                roi_equity = np.nan
            else:
                irr_eq_raw_calc = npf.irr(equity_cash_flows_monthly_final)
                irr_equity = (1 + irr_eq_raw_calc)**12 - 1 if pd.notna(irr_eq_raw_calc) and np.isfinite(irr_eq_raw_calc) else np.nan
                roi_equity = npv_equity / abs(net_equity_investment) if pd.notna(npv_equity) and abs(net_equity_investment) > 1e-9 else np.nan
            
            # NPV, IRR Projet
            irr_proj_raw_calc = npf.irr(project_cash_flows_monthly_final)
            irr_project = (1 + irr_proj_raw_calc)**12 - 1 if pd.notna(irr_proj_raw_calc) and np.isfinite(irr_proj_raw_calc) else np.nan
            npv_project = npf.npv(wacc_monthly_at, project_cash_flows_monthly_final) if pd.notna(wacc_monthly_at) else np.nan
            
            # Payback Equity (avec gestion is_equity_negligible)
            # Le "equity_cash_flows_monthly_final" est la série des FCFE.
            # Pour le payback equity, il faut une série qui représente l'investissement initial de l'actionnaire (négatif)
            # puis les FCFE. Si l'investissement est réparti, c'est (FCFE - injection d'equity).
            # On va construire cette série spécifiquement pour le payback.
            equity_investment_cash_flow_for_payback = -equity_injected_monthly_series_post + monthly_results_df['FCFE'].fillna(0)

            payback_equity_months_calc = calculate_payback_months(equity_investment_cash_flow_for_payback.values)
            if is_equity_negligible:
                payback_equity_years = np.nan
            else:
                payback_equity_years = payback_equity_months_calc / 12.0 if payback_equity_months_calc is not None else np.nan
                if payback_equity_months_calc == 0.0 and abs(net_equity_investment) > EQUITY_INVESTMENT_THRESHOLD :
                     pass # Reste 0.0

            payback_project_months_calc = calculate_payback_months(project_cash_flows_monthly_final) # OCF_Projet inclut déjà -CAPEX
            payback_project_years = payback_project_months_calc / 12.0 if payback_project_months_calc is not None else np.nan
            
            avg_dscr = calculate_avg_dscr_revised(monthly_results_df, tax_rate_decimal) if loan_active else np.nan
            lcoe = calculate_lcoe_engineering(wacc_monthly_at, monthly_results_df, terminal_value_net_projet_calc)
            
            total_production_final = monthly_results_df['Production_kWh'].sum()
            total_autoconsumption_final = monthly_results_df['Autoconsommation_kWh'].sum()
            total_consumption_final = monthly_results_df['Consommation_kWh'].sum()
            autoconsumption_rate = total_autoconsumption_final / total_consumption_final if total_consumption_final > 1e-6 else 0.0
            autoproduction_rate = total_autoconsumption_final / total_production_final if total_production_final > 1e-6 else 0.0

            results = {
                "scenario": scenario_name, "prix_revente": prix_vente_final_a_utiliser,
                "source_parametres_simulation": source_des_inputs,
                "capex_base_utilise": capex_base_input,
                "opex_base_utilise_maintenance_annuel": total_opex_maintenance_base_annual,
                "opex_base_utilise_assurance_annuel": total_opex_assurance_base_annual,
                "opex_base_utilise_admin_annuel": total_opex_admin_base_annual,
                "puissance_base_utilisee": puissance_kwc_global,
                "capex_scenario_simule_initial": capex_scenario_simule, # Gardé pour la sortie
                "capex_scenario_final_utilise": capex_brut_total_scenario,
                "capex_net_subvention_final": capex_net_subvention,
                "subvention_finale_retenue_pour_calculs": subvention_finale_pour_calculs,
                "opex_scenario_maintenance_annuel_simule": opex_maintenance_scenario_annual,
                "opex_scenario_assurance_annuel_simule": opex_assurance_scenario_annual,
                "opex_scenario_admin_annuel_simule": opex_admin_scenario_annual,
                "debt_amount": debt_amount, "total_subvention": subvention_finale_pour_calculs,
                "net_equity_investment": net_equity_investment, 
                "tva_sur_capex_initial_pour_fcfe_t0": tva_sur_capex_initial, # Note: c'est le total, pas le flux t0 FCFE
                "autoconsumption_rate": autoconsumption_rate, "autoproduction_rate": autoproduction_rate,
                "wacc_after_tax_annual": wacc_annual_at / 100.0 if pd.notna(wacc_annual_at) else np.nan,
                "cost_of_equity_annual": re_annual / 100.0 if pd.notna(re_annual) else np.nan,
                "lcoe": lcoe, 
                "irr": irr_equity, "npv": npv_equity, "roi": roi_equity, "payback_period": payback_equity_years,
                "irr_project": irr_project, "npv_project": npv_project, "payback_project": payback_project_years,
                "avg_dscr": avg_dscr,
                "monthly_data": monthly_results_df.copy(),
                'hourly_aggregated_data': hourly_data_to_return.copy(),
                "config_globale_utilisee": copy.deepcopy(global_config), 
                "config_scenario_utilise": copy.deepcopy(scenario),
                "config_sites_utilisee": copy.deepcopy(effective_sites_config) if effective_sites_config else {"mode": "global_fallback"},
                "date_debut_simulation_effective": date_debut_simulation_effective.strftime('%Y-%m-%d'),
                "date_debut_operations": date_debut_operations.strftime('%Y-%m-%d'),
                "duree_construction_mois": duree_construction_cfg,
                "duree_exploitation_mois": duree_exploitation_cfg,
            }
            end_time_calc = time.time()
            logger.info(f"Indicateurs calculés pour '{scenario_name}' en {end_time_calc - start_time_calc:.3f} sec. Source: {source_des_inputs}")
            return results

        except (ValueError, TypeError, RuntimeError, ImportError) as e:
            logger.error(f"ERREUR MOTEUR (calculate_financial_indicators): Scenario '{scenario_name}', Erreur: {e}", exc_info=True)
            return {"error": str(e)}
        except Exception as e_unexp:
            logger.error(f"ERREUR MOTEUR INATTENDUE (Calculate_financial_indicators): Scenario '{scenario_name}', Erreur: {e_unexp}", exc_info=True)
            return {"error": f"Erreur inattendue: {e_unexp}"}

    def simulate_selling_price(self,
                               scenario_name: str,
                               target_irr: float | None = None,
                               target_npv: float | None = None,
                               override_source_prix_autoconso: str | None = None,
                               sites_config: dict | None = None
                              ) -> dict | None:
        logger.info(f"SIMULATE PRICE: Scénario='{scenario_name}', Target IRR={target_irr}, Target NPV={target_npv}")
        try:
            if target_irr is None and target_npv is None:
                raise ValueError("Spécifier soit un TRI cible (target_irr) soit une VAN cible (target_npv).")

            global_config_sim = self.config
            prix_min_recherche = float(global_config_sim.get('prix_min_revente', 0.01))
            prix_max_recherche = float(global_config_sim.get('prix_max_revente', 0.50))
            if prix_min_recherche >= prix_max_recherche:
                prix_min_recherche = 0.01; prix_max_recherche = 0.50

            optimal_price_found = None
            simulation_cache = {} 

            def get_target_metric_value(price_candidate):
                price_key = round(price_candidate, 8)
                if price_key in simulation_cache:
                    cached_results = simulation_cache[price_key]
                    if cached_results is None or (isinstance(cached_results, dict) and "error" in cached_results) : return np.nan
                    if target_irr is not None: return cached_results.get('irr_project', np.nan)
                    if target_npv is not None: return cached_results.get('npv_project', np.nan)
                    return np.nan

                results_sim = self.calculate_financial_indicators(
                    scenario_name, prix_revente=price_candidate,
                    override_source_prix_autoconso=override_source_prix_autoconso,
                    sites_config=sites_config
                )
                simulation_cache[price_key] = results_sim
                if results_sim is None or (isinstance(results_sim, dict) and "error" in results_sim): return np.nan
                if target_irr is not None: return results_sim.get('irr_project', np.nan)
                if target_npv is not None: return results_sim.get('npv_project', np.nan)
                return np.nan

            def objective_for_brentq(price_candidate):
                actual_metric_value = get_target_metric_value(price_candidate)
                if not (pd.notna(actual_metric_value) and np.isfinite(actual_metric_value)): return np.nan
                target_val_brentq = target_irr if target_irr is not None else target_npv
                if target_val_brentq is None : return np.nan # Should not happen due to initial check
                return actual_metric_value - target_val_brentq

            try:
                val_min_bound = objective_for_brentq(prix_min_recherche)
                val_max_bound = objective_for_brentq(prix_max_recherche)

                if pd.notna(val_min_bound) and pd.notna(val_max_bound) and (np.sign(val_min_bound) * np.sign(val_max_bound) <= 0):
                    if abs(val_min_bound) < 1e-9 : optimal_price_found = prix_min_recherche
                    elif abs(val_max_bound) < 1e-9 : optimal_price_found = prix_max_recherche
                    else:
                         optimal_price_found = brentq(objective_for_brentq, prix_min_recherche, prix_max_recherche, xtol=1e-7, rtol=1e-7, maxiter=150)
                else:
                    logger.warning(f"SIMULATE PRICE (Brentq): Pas de changement de signe ou NaN aux bornes. MinVal={val_min_bound}, MaxVal={val_max_bound}. Tentative avec minimize.")
            
            except RuntimeError as e_brentq_runtime: # Brentq peut lever RuntimeError s'il ne converge pas
                logger.warning(f"SIMULATE PRICE: Brentq n'a pas convergé: {e_brentq_runtime}. Tentative avec minimize.")
            except Exception as e_brentq_other:
                logger.error(f"SIMULATE PRICE: Erreur inattendue avec brentq: {e_brentq_other}. Tentative avec minimize.")

            if optimal_price_found is None:
                simulation_cache.clear() 
                def objective_for_minimize(price_array):
                    price_candidate_min = float(price_array[0])
                    if not (prix_min_recherche <= price_candidate_min <= prix_max_recherche): return 1e12 # Pénalité forte hors bornes
                    
                    actual_metric_value_min = get_target_metric_value(price_candidate_min)
                    if not (pd.notna(actual_metric_value_min) and np.isfinite(actual_metric_value_min)): return 1e10 
                    
                    target_val_minimize = target_irr if target_irr is not None else target_npv
                    if target_val_minimize is None: return 1e11 # Ne devrait pas arriver
                    return (actual_metric_value_min - target_val_minimize)**2

                initial_guess_minimize = max(prix_min_recherche, min(prix_max_recherche, (prix_min_recherche + prix_max_recherche) / 2.0))
                
                # Utiliser L-BFGS-B qui gère les bornes directement et est souvent robuste
                res_minimize = minimize(
                    objective_for_minimize, 
                    [initial_guess_minimize], 
                    method='L-BFGS-B', 
                    bounds=[(prix_min_recherche, prix_max_recherche)], 
                    options={'ftol': 1e-10, 'gtol': 1e-8, 'maxiter': 200}
                )
                
                if res_minimize.success and abs(res_minimize.fun) < 1e-7 : # Vérifier si l'objectif est proche de zéro
                    optimal_price_found = res_minimize.x[0]
                    logger.info(f"SIMULATE PRICE: Minimize (L-BFGS-B) a trouvé une solution: {optimal_price_found:.8f}")
                else:
                    logger.warning(f"SIMULATE PRICE: Minimize (L-BFGS-B) n'a pas trouvé de solution satisfaisante. Success: {res_minimize.success}, Fun: {res_minimize.fun}, Msg: {res_minimize.message}")


            if optimal_price_found is None:
                raise RuntimeError("Aucun prix optimal déterminé après toutes les tentatives (brentq et minimize). Vérifiez les logs et les bornes de recherche.")
            
            optimal_price_found = max(prix_min_recherche, min(prix_max_recherche, optimal_price_found)) # S'assurer qu'il reste dans les bornes

            simulation_cache.clear()
            final_results_with_optimal_price = self.calculate_financial_indicators(
                scenario_name, prix_revente=optimal_price_found,
                override_source_prix_autoconso=override_source_prix_autoconso, sites_config=sites_config
            )

            if final_results_with_optimal_price and isinstance(final_results_with_optimal_price, dict) and "error" not in final_results_with_optimal_price:
                final_results_with_optimal_price['prix_revente_optimal_pour_cible'] = optimal_price_found
                final_results_with_optimal_price['target_irr_asked_for_project'] = target_irr
                final_results_with_optimal_price['target_npv_asked_for_project'] = target_npv
                return final_results_with_optimal_price
            else:
                error_msg_final = final_results_with_optimal_price.get("error", "Calcul final échoué") if isinstance(final_results_with_optimal_price, dict) else "Calcul final échoué"
                raise RuntimeError(f"Échec recalcul final avec prix {optimal_price_found:.8f}: {error_msg_final}")

        except Exception as e_fatal_sim_price:
            logger.error(f"ERREUR FATALE (simulate_selling_price): {e_fatal_sim_price}", exc_info=True)
            return {"error": str(e_fatal_sim_price)}