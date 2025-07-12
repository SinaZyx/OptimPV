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
    calculate_lcoe_annual_aggregation,
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
        # La validation des données de site est faite ici, une seule fois à l'initialisation
        self.sites_data = validate_and_prepare_sites_data(sites_data) 

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
        
        try:
            # --- 1. VALIDATION ET RÉCUPÉRATION CONFIGURATIONS ---
            if scenario_name not in self.scenarios:
                raise ValueError(f"Scénario '{scenario_name}' invalide.")
            scenario = self.scenarios[scenario_name]
            global_config = self.config # Utilisation d'une copie pour éviter modif accidentelle

            # Agrégation des paramètres de base (CAPEX, OPEX, Puissance)
            total_capex_base = 0.0
            total_opex_maintenance_base_annual = 0.0
            total_opex_assurance_base_annual = 0.0
            total_opex_admin_base_annual = 0.0
            total_puissance_kwc = 0.0
            total_base_annual_unindexed_inverter_provision = 0.0
            
            # effective_sites_config sera utilisé pour l'agrégation énergétique ET pour les paramètres financiers si fourni
            effective_sites_config = sites_config if sites_config and any(sites_config.values()) else None
            
            if effective_sites_config:
                logger.debug("Utilisation de la configuration par site (sites_config) pour agrégation des paramètres financiers.")
                source_des_inputs = "agreges_par_site"
                self.used_aggregated_config = True
                for site_id, site_cfg in effective_sites_config.items():
                    if not isinstance(site_cfg, dict): continue
                    site_power = float(site_cfg.get('puissance_kwc', 0.0))
                    site_capex = float(site_cfg.get('capex', 0.0))
                    site_type = site_cfg.get('site_type', 'Producteur')
                    
                    if site_type != "Consommateur Pur":
                        total_opex_maintenance_base_annual += float(site_cfg.get('opex_maintenance', 0.0))
                        total_opex_assurance_base_annual += float(site_cfg.get('opex_insurance', 0.0))
                        total_opex_admin_base_annual += float(site_cfg.get('opex_admin', 0.0))
                        if site_cfg.get("opex_onduleur_provision_site", False):
                            cost_unindexed = float(site_cfg.get("opex_onduleur_total_cost_site", 0.0))
                            lifetime = int(site_cfg.get("opex_onduleur_lifetime_site", 0))
                            if cost_unindexed > 0 and lifetime > 0:
                                total_base_annual_unindexed_inverter_provision += cost_unindexed / lifetime
                    total_puissance_kwc += site_power
                    total_capex_base += site_capex
                capex_base_input_agg = total_capex_base
                puissance_kwc_global_agg = total_puissance_kwc
            else:
                logger.debug("Utilisation de la configuration globale (config) pour les inputs financiers principaux.")
                source_des_inputs = "globaux_directs"
                self.used_aggregated_config = False
                capex_base_input_agg = float(global_config.get('capex_scenario', 0.0)) # CAPEX total si pas de config par site
                puissance_kwc_global_agg = float(global_config.get('puissance_kwc_installee', 0.0)) # Puissance totale si pas de config par site
                
                total_opex_maintenance_base_annual = float(global_config.get('opex_maintenance_fallback',0.0))
                total_opex_assurance_base_annual = float(global_config.get('opex_insurance_fallback',0.0))
                total_opex_admin_base_annual = float(global_config.get('opex_admin_fallback',0.0))
                if global_config.get("opex_onduleur_provision_globale", False): # Check si la provision globale est activée
                    cost_unindexed_global = float(global_config.get("opex_onduleur_total_cost_global", 0.0))
                    lifetime_global = int(global_config.get("opex_onduleur_lifetime_global", 0))
                    if cost_unindexed_global > 0 and lifetime_global > 0:
                        total_base_annual_unindexed_inverter_provision = cost_unindexed_global / lifetime_global
            
            # Application des modificateurs de scénario
            capex_brut_total_scenario = capex_base_input_agg * (1 + float(scenario.get('capex_modifier', 0.0)))
            
            opex_modifier_scenario = float(scenario.get("opex_modifier", 1.0)) # Note: ce modif s'appliquera sur la somme des OPEX de base.
            opex_maintenance_scenario_annual = total_opex_maintenance_base_annual * opex_modifier_scenario
            opex_assurance_scenario_annual = total_opex_assurance_base_annual * opex_modifier_scenario
            opex_admin_scenario_annual = total_opex_admin_base_annual * opex_modifier_scenario
            # La provision onduleur est déjà calculée annuellement, son indexation se fera dans la boucle.

            # --- Subvention et CAPEX Net ---
            applicable_sub_rate = 0.0
            if puissance_kwc_global_agg <= 3: applicable_sub_rate = float(global_config.get("subvention_rate_le3",100.0))
            elif puissance_kwc_global_agg <= 9: applicable_sub_rate = float(global_config.get("subvention_rate_le9", 80.0))
            elif puissance_kwc_global_agg <= 36: applicable_sub_rate = float(global_config.get("subvention_rate_le36", 150.0))
            elif puissance_kwc_global_agg <= 100: applicable_sub_rate = float(global_config.get("subvention_rate_le100", 100.0))
            elif puissance_kwc_global_agg <= 500: applicable_sub_rate = float(global_config.get("subvention_rate_le500",80.0))
            else: applicable_sub_rate = float(global_config.get("subvention_rate_gt100", 0.0))
            
            subvention_totale_projet = applicable_sub_rate * puissance_kwc_global_agg
            montant_capex_pour_financement_et_flux = capex_brut_total_scenario # Le financement se base sur le CAPEX Brut
            capex_net_subvention_info = max(0, capex_brut_total_scenario - subvention_totale_projet) # Pour base amortissable

            # --- Paramètres temporels et financiers ---
            duree_construction_cfg = int(global_config.get("duree_construction", 0))
            date_debut_operations_str = global_config.get("date_debut_ppa", datetime.now().date().isoformat())
            date_debut_operations = pd.to_datetime(date_debut_operations_str)
            date_debut_simulation_effective = date_debut_operations - pd.DateOffset(months=duree_construction_cfg)
            duree_exploitation_cfg = int(global_config.get("duree_ppa", 240))
            num_total_simulation_months = duree_construction_cfg + duree_exploitation_cfg
            initial_cash_balance_at_true_t0 = float(global_config.get("initial_cash_balance", 0.0))
            
            # --- Paramètres d'indexation et techniques ---
            degradation_rate_base = float(global_config.get("degradation_rate", 0.005))
            taux_inflation_pct = float(global_config.get("taux_inflation", 2.0))
            adjusted_inflation_annual_base = taux_inflation_pct / 100.0
            oa_indexed = bool(global_config.get("tarif_oa_indexe_inflation", True))
            inflation_rate_oa_pct = float(global_config.get("taux_inflation_tarif_oa", 1.89))
            inflation_rate_oa_annual = inflation_rate_oa_pct / 100.0
            turpe_indexed = bool(global_config.get("turpe_indexe_inflation", True))
            
            # --- Paramètres fiscaux et comptables ---
            taux_imposition_standard_pct = float(global_config.get("taux_imposition", 25.0))
            tax_rate_decimal = taux_imposition_standard_pct / 100.0
            if hasattr(tax_engine, 'STANDARD_TAX_RATE'): tax_engine.STANDARD_TAX_RATE = tax_rate_decimal
            amortissement_duree_years = int(global_config.get("amortissement_duree", 20))
            valeur_residuelle_pct_config = float(global_config.get("valeur_residuelle_pct", 0.0)) # Déjà en décimal ou % ? Docstring dit % CAPEX Net
            cout_demantelement_pct_config = float(global_config.get("cout_demantelement_pct", 0.0)) # % CAPEX Brut
            
            # --- Paramètres de financement ---
            cout_fonds_propres_pct_config = float(global_config.get("cout_fonds_propres", 8.0))
            loan_active = global_config.get("with_loan", True)
            debt_ratio_config = float(global_config.get("debt_ratio", 0.80)) if loan_active else 0.0
            debt_term_years_config = int(global_config.get("debt_term_years", 20)) if loan_active else 0
            taux_interet_dette_pct_config = float(global_config.get("taux_interet_dette", 4.0)) if loan_active else 0.0
            taux_interet_dette_annual = taux_interet_dette_pct_config / 100.0
            capitalize_construction_interest = bool(global_config.get("capitalize_construction_interest", True))

            # --- Paramètres TVA et BFR ---
            vat_rate_operations = float(global_config.get("taux_tva_operations_pct", 20.0)) / 100.0
            vat_rate_capex = float(global_config.get("taux_tva_capex_pct", 20.0)) / 100.0
            vat_capex_recovery_month_offset = int(global_config.get("vat_capex_recovery_delay_months", 3))
            bfr_receivables_days_config = float(global_config.get("bfr_receivables_days", 30.0))
            bfr_payables_days_config = float(global_config.get("bfr_payables_days", 15.0))
            mois_paiement_solde_is = int(global_config.get("mois_paiement_solde_is", 5)) # Mois (1-12)
            
            # --- Tarifs de référence et TURPE de base ---
            source_prix_autoc_config = global_config.get("source_prix_autoconso", "prix_initial")
            tarif_edf_ref_config = float(global_config.get("tarif_edf_reference", 0.21))
            if puissance_kwc_global_agg <= 9: tarif_oa_base = float(global_config.get("tarif_oa_bracket_le9", 0.07))
            elif puissance_kwc_global_agg <= 100: tarif_oa_base = float(global_config.get("tarif_oa_bracket_le100", 0.06))
            else: tarif_oa_base = float(global_config.get("tarif_oa_bracket_gt100", 0.05))

            if puissance_kwc_global_agg <= 36: actual_turpe_tension = "BT<=36kVA"
            elif puissance_kwc_global_agg <= 250: actual_turpe_tension = "BT>36kVA"
            else: actual_turpe_tension = "HTA"
            turpe_prod_contrat_setting = global_config.get("turpe_prod_contrat", "Unique")
            cg_rate = TURPE_PROD_RATES.get(actual_turpe_tension, {}).get("CG", {}).get(turpe_prod_contrat_setting, 0.0)
            cc_keys = list(TURPE_PROD_RATES.get(actual_turpe_tension, {}).get("CC", {}).keys())
            cc_key_to_use = cc_keys[0] if cc_keys else None # Simplification, prendre le premier dispo
            if actual_turpe_tension == "BT<=36kVA" and "Linky" in cc_keys: cc_key_to_use = "Linky" # Spécifique
            cc_rate = TURPE_PROD_RATES.get(actual_turpe_tension, {}).get("CC", {}).get(cc_key_to_use, 0.0) if cc_key_to_use else 0.0
            turpe_annual_base_scenario = cg_rate + cc_rate
            
            # --- Application des modificateurs de scénario ---
            production_modifier_scenario = float(scenario.get("production_modifier", 1.0))
            adjusted_inflation_scenario_rate = adjusted_inflation_annual_base * float(scenario.get("inflation_modifier", 1.0))
            degradation_rate_scenario_effective = degradation_rate_base * float(scenario.get("degradation_modifier", 1.0))
            
            prix_vente_final_a_utiliser = float(prix_revente) if prix_revente is not None else \
                                    float(global_config.get("prix_vente_initial_slider_fallback", 0.10))
            source_prix_autoc_effective = override_source_prix_autoconso if override_source_prix_autoconso is not None else source_prix_autoc_config
            
            # --- 2. PRÉPARATION DATAFRAME RÉSULTATS MENSUELS ---
            # Agrégation des données énergétiques horaires en mensuel pour la référence annuelle
            # self.sites_data est déjà validé et préparé dans __init__
            hourly_data_to_return = aggregate_energy_data(self.sites_data, effective_sites_config) # Utilise config par site si dispo pour type de site
            
            df_agg_for_ref = hourly_data_to_return.set_index('Temps') # Assumant que 'Temps' est déjà datetime
            ref_year = df_agg_for_ref.index.year.min() if not df_agg_for_ref.empty else date_debut_operations.year
            reference_data_ts_hourly = df_agg_for_ref[df_agg_for_ref.index.year == ref_year].copy() if not df_agg_for_ref.empty else pd.DataFrame()

            monthly_index = pd.date_range(start=date_debut_simulation_effective, periods=num_total_simulation_months, freq='ME') # 'ME' pour fin de mois
            monthly_results_df = pd.DataFrame(index=monthly_index)
            
            # Définition unique des colonnes
            monthly_cols = [
                'Is_Construction_Phase', 'Year_Index_Operational', 'Sim_Year_Operational',
                'Inflation_Factor_Operational', 'Degradation_Factor_Operational',
                'Production_kWh', 'Consommation_kWh', 'Autoconsommation_kWh', 'Surplus_kWh',
                'Tarif_OA_Annuel', 'Prix_Autoconso_Annuel',
                'Revenus_Surplus', 'Revenus_Autoconsommation', 'Prime_Autoconso_Encaissee', 'Revenus_Total',
                'OPEX_Maintenance_Mensuel', 'OPEX_Assurance_Mensuel', 'OPEX_Admin_Mensuel', 'OPEX_Provision_Onduleur_Mensuel', 'OPEX', 
                'TURPE', 'Amortissement', 'EBITDA', 'EBIT',
                'Interets_Payes', 'Principal_Rembourse', 'Service_Dette', 'EBT', 
                'Tax_Payment', 'Solde_IS_N_1_Paye_Mois', 'Total_IS_Decaisse_Mois', 'Resultat_Net',
                'VAT_Collectee', 'VAT_Deductible_CAPEX', 'VAT_Deductible_OPEX_TURPE', 'VAT_Due_Mois', 'VAT_Payment',
                'BFR_Mensuel', 'Delta_BFR_Mensuel',
                'CAPEX_Initial_Mensuel', 'Debt_Drawn_This_Month', 'Solde_Dette_Fin_Mois',
                'FCFE', 'OCF_Projet', 'Solde_Tresorerie_Fin_Mois'
            ]
            for col in monthly_cols: monthly_results_df[col] = 0.0
            # Sim_Year sera calculé dans la boucle à partir de l'index opérationnel.

            # --- 3. CALCULS PRÉLIMINAIRES (Financement, Amortissement) ---
            capex_pour_repartition_mensuelle = montant_capex_pour_financement_et_flux / duree_construction_cfg if duree_construction_cfg > 0 else montant_capex_pour_financement_et_flux
            
            debt_amount_total = montant_capex_pour_financement_et_flux * debt_ratio_config if loan_active else 0.0
            net_equity_investment_total = montant_capex_pour_financement_et_flux - debt_amount_total
            EQUITY_INVESTMENT_THRESHOLD = 1.0 
            is_equity_negligible = abs(net_equity_investment_total) < EQUITY_INVESTMENT_THRESHOLD

            # Base amortissable et amortissement annuel de base
            valeur_residuelle_montant_calc = capex_net_subvention_info * valeur_residuelle_pct_config # % du CAPEX NET
            base_amortissable_calc = capex_net_subvention_info - valeur_residuelle_montant_calc
            annual_depreciation_base = base_amortissable_calc / amortissement_duree_years if amortissement_duree_years > 0 else 0.0
            tva_sur_capex_initial = capex_brut_total_scenario * vat_rate_capex # Sur CAPEX Brut

            # --- 4. BOUCLE DE CALCUL MENSUEL ---
            loss_carryforward_balance = 0.0
            annual_tax_calculated_prev_year = 0.0 # Pour IS N-1
            current_quarterly_acompte_is = 0.0
            solde_IS_N_1_annee_precedente_a_payer_en_N = 0.0
            bfr_previous_month_val = 0.0
            vat_credit_carryforward = 0.0

            current_debt_drawn_balance = 0.0
            accumulated_capitalized_interest = 0.0
            loan_amortization_schedule_generated = False
            operation_phase_loan_interests = np.zeros(duree_exploitation_cfg) # Initialisation une fois
            operation_phase_loan_principals = np.zeros(duree_exploitation_cfg) # Initialisation une fois

            # Variables pour le suivi annuel (mises à jour au changement d'année opérationnelle)
            current_operational_year_tracker = -1
            # Initialisation des valeurs indexées annuelles (seront mises à jour dans la boucle)
            opex_maint_indexed_annual_current = opex_maintenance_scenario_annual
            opex_assur_indexed_annual_current = opex_assurance_scenario_annual
            opex_admin_indexed_annual_current = opex_admin_scenario_annual
            inverter_prov_indexed_annual_current = total_base_annual_unindexed_inverter_provision
            turpe_indexed_annual_current = turpe_annual_base_scenario
            depreciation_annual_current = annual_depreciation_base
            oa_rate_annual_current = tarif_oa_base
            prix_autoc_annual_current = 0.0 # Sera défini ci-dessous

            prime_disbursement_schedule = {} # Année d'exploitation (index 0) -> montant
            if subvention_totale_projet > 0:
                if puissance_kwc_global_agg <= 9: prime_disbursement_schedule[0] = subvention_totale_projet
                elif 9 < puissance_kwc_global_agg <= 100:
                    prime_disbursement_schedule[0] = subvention_totale_projet * 0.80
                    for i_prime_year in range(1, 5): prime_disbursement_schedule[i_prime_year] = subvention_totale_projet * 0.05
                else: # > 100 kWc
                    prime_disbursement_schedule[0] = subvention_totale_projet * 0.80 
                    for i_prime_year in range(1, 5): prime_disbursement_schedule[i_prime_year] = subvention_totale_projet * 0.05

            # --- Injections de fonds propres et tirages de dette mensuels ---
            # (Pré-calculés pour toute la durée de construction)
            equity_injected_monthly_series = pd.Series(0.0, index=monthly_results_df.index)
            debt_drawn_monthly_series = pd.Series(0.0, index=monthly_results_df.index)

            if duree_construction_cfg > 0:
                monthly_equity_injection = net_equity_investment_total / duree_construction_cfg if not is_equity_negligible else 0.0
                monthly_debt_drawdown = debt_amount_total / duree_construction_cfg if loan_active else 0.0
                for constr_month_idx in range(duree_construction_cfg):
                    if constr_month_idx < len(equity_injected_monthly_series):
                        equity_injected_monthly_series.iloc[constr_month_idx] = monthly_equity_injection
                        debt_drawn_monthly_series.iloc[constr_month_idx] = monthly_debt_drawdown
            elif duree_construction_cfg == 0 and num_total_simulation_months > 0 : # Pas de construction, tout au premier mois (T0 de l'exploitation)
                 if not is_equity_negligible: equity_injected_monthly_series.iloc[0] = net_equity_investment_total
                 if loan_active: debt_drawn_monthly_series.iloc[0] = debt_amount_total

            # Boucle Principale
            for month_idx, current_month_end_date in enumerate(monthly_results_df.index):
                is_construction_phase = month_idx < duree_construction_cfg
                monthly_results_df.loc[current_month_end_date, 'Is_Construction_Phase'] = 1.0 if is_construction_phase else 0.0
                
                # CAPEX et Tirages de Dette Mensuels
                capex_this_month = capex_pour_repartition_mensuelle if is_construction_phase else 0.0
                if not is_construction_phase and month_idx == duree_construction_cfg and duree_construction_cfg == 0: # Cas: 0 mois de construction
                    capex_this_month = montant_capex_pour_financement_et_flux # Tout le CAPEX au premier mois d'opération
                monthly_results_df.loc[current_month_end_date, 'CAPEX_Initial_Mensuel'] = capex_this_month
                
                # Les tirages de dette sont basés sur la série précalculée
                current_drawdown_for_month_calc = debt_drawn_monthly_series.iloc[month_idx] if month_idx < len(debt_drawn_monthly_series) else 0.0
                monthly_results_df.loc[current_month_end_date, 'Debt_Drawn_This_Month'] = current_drawdown_for_month_calc
                current_debt_drawn_balance += current_drawdown_for_month_calc

                # Calcul des Intérêts et Principal de la Dette
                interest_paid_this_month = 0.0
                principal_repaid_this_month = 0.0
                if loan_active:
                    if is_construction_phase:
                        if current_debt_drawn_balance > 0 and not capitalize_construction_interest:
                            interest_paid_this_month = current_debt_drawn_balance * (taux_interet_dette_annual / 12.0)
                        elif current_debt_drawn_balance > 0 and capitalize_construction_interest:
                            accumulated_capitalized_interest += current_debt_drawn_balance * (taux_interet_dette_annual / 12.0)
                        # Pas de remboursement de principal pendant la construction
                    else: # Phase d'exploitation
                        if not loan_amortization_schedule_generated:
                            final_loan_principal_for_amortization = current_debt_drawn_balance + accumulated_capitalized_interest
                            num_amort_months_schedule = duree_exploitation_cfg # S'assurer que ça couvre bien la durée restante
                            if final_loan_principal_for_amortization > 1e-6 and debt_term_years_config > 0:
                                op_interests_sched, op_principals_sched, _ = calculate_monthly_loan_schedule(
                                    principal=final_loan_principal_for_amortization,
                                    annual_rate=taux_interet_dette_annual,
                                    term_years=debt_term_years_config, # Utiliser la durée configurée
                                    num_months_simulation=num_amort_months_schedule 
                                )
                                operation_phase_loan_interests[:len(op_interests_sched)] = op_interests_sched
                                operation_phase_loan_principals[:len(op_principals_sched)] = op_principals_sched
                            loan_amortization_schedule_generated = True

                        operational_month_idx_for_loan = month_idx - duree_construction_cfg
                        if operational_month_idx_for_loan < len(operation_phase_loan_interests):
                            interest_paid_this_month = operation_phase_loan_interests[operational_month_idx_for_loan]
                            principal_repaid_this_month = operation_phase_loan_principals[operational_month_idx_for_loan]
                        current_debt_drawn_balance -= principal_repaid_this_month
                
                monthly_results_df.loc[current_month_end_date, 'Interets_Payes'] = interest_paid_this_month
                monthly_results_df.loc[current_month_end_date, 'Principal_Rembourse'] = principal_repaid_this_month
                monthly_results_df.loc[current_month_end_date, 'Service_Dette'] = interest_paid_this_month + principal_repaid_this_month
                monthly_results_df.loc[current_month_end_date, 'Solde_Dette_Fin_Mois'] = max(0, current_debt_drawn_balance)

                # Mise à jour annuelle des paramètres indexés et techniques
                year_idx_operational = -1
                sim_year_operational = 0
                inflation_factor_op_current = 1.0
                degradation_factor_op_current = 1.0

                if not is_construction_phase:
                    year_idx_operational = (month_idx - duree_construction_cfg) // 12
                    sim_year_operational = year_idx_operational + 1
                    if year_idx_operational != current_operational_year_tracker:
                        inflation_factor_op_current = (1 + adjusted_inflation_scenario_rate) ** year_idx_operational
                        degradation_factor_op_current = (1 - degradation_rate_scenario_effective) ** year_idx_operational
                        
                        opex_maint_indexed_annual_current = opex_maintenance_scenario_annual * inflation_factor_op_current
                        opex_assur_indexed_annual_current = opex_assurance_scenario_annual * inflation_factor_op_current
                        opex_admin_indexed_annual_current = opex_admin_scenario_annual * inflation_factor_op_current
                        inverter_prov_indexed_annual_current = total_base_annual_unindexed_inverter_provision * inflation_factor_op_current
                        
                        turpe_indexed_annual_current = turpe_annual_base_scenario * (inflation_factor_op_current if turpe_indexed else 1.0)
                        depreciation_annual_current = annual_depreciation_base if year_idx_operational < amortissement_duree_years else 0.0 # Amortissement sur base nette
                        oa_rate_annual_current = tarif_oa_base * ((1 + inflation_rate_oa_annual) ** year_idx_operational if oa_indexed else 1.0)
                        
                        if source_prix_autoc_effective == 'prix_initial': prix_autoc_annual_current = prix_vente_final_a_utiliser * inflation_factor_op_current
                        elif source_prix_autoc_effective == 'tarif_edf': prix_autoc_annual_current = tarif_edf_ref_config * inflation_factor_op_current
                        elif source_prix_autoc_effective == 'tarif_oa': prix_autoc_annual_current = oa_rate_annual_current
                        else: prix_autoc_annual_current = prix_vente_final_a_utiliser * inflation_factor_op_current # Fallback
                        current_operational_year_tracker = year_idx_operational
                
                monthly_results_df.loc[current_month_end_date, 'Year_Index_Operational'] = year_idx_operational
                monthly_results_df.loc[current_month_end_date, 'Sim_Year_Operational'] = sim_year_operational
                monthly_results_df.loc[current_month_end_date, 'Inflation_Factor_Operational'] = inflation_factor_op_current
                monthly_results_df.loc[current_month_end_date, 'Degradation_Factor_Operational'] = degradation_factor_op_current

                # Calculs spécifiques à la phase d'exploitation
                if not is_construction_phase:
                    # Énergie et Revenus
                    prod_kWh_month, cons_kWh_month, autocons_kWh_month, surplus_kWh_month = 0.0, 0.0, 0.0, 0.0
                    current_month_number_loop = current_month_end_date.month
                    if not reference_data_ts_hourly.empty:
                        ref_monthly_slice = reference_data_ts_hourly[reference_data_ts_hourly.index.month == current_month_number_loop]
                        if not ref_monthly_slice.empty:
                            prod_adj_hourly = ref_monthly_slice['production_kwh'] * degradation_factor_op_current * production_modifier_scenario
                            cons_hourly = ref_monthly_slice['consumption_kwh'] # Consommation non modifiée par dégradation/scénario
                            
                            autocons_hourly_calc = np.minimum(prod_adj_hourly.values, cons_hourly.values)
                            surplus_hourly_calc = np.maximum(0, prod_adj_hourly.values - autocons_hourly_calc)
                            
                            prod_kWh_month = prod_adj_hourly.sum()
                            cons_kWh_month = cons_hourly.sum()
                            autocons_kWh_month = autocons_hourly_calc.sum()
                            surplus_kWh_month = surplus_hourly_calc.sum()

                    monthly_results_df.loc[current_month_end_date, 'Production_kWh'] = prod_kWh_month
                    monthly_results_df.loc[current_month_end_date, 'Consommation_kWh'] = cons_kWh_month
                    monthly_results_df.loc[current_month_end_date, 'Autoconsommation_kWh'] = autocons_kWh_month
                    monthly_results_df.loc[current_month_end_date, 'Surplus_kWh'] = surplus_kWh_month
                    
                    monthly_results_df.loc[current_month_end_date, 'Tarif_OA_Annuel'] = oa_rate_annual_current
                    monthly_results_df.loc[current_month_end_date, 'Prix_Autoconso_Annuel'] = prix_autoc_annual_current
                    
                    rev_surplus_monthly = surplus_kWh_month * oa_rate_annual_current
                    rev_autocons_monthly = autocons_kWh_month * prix_autoc_annual_current
                    monthly_results_df.loc[current_month_end_date, 'Revenus_Surplus'] = rev_surplus_monthly
                    monthly_results_df.loc[current_month_end_date, 'Revenus_Autoconsommation'] = rev_autocons_monthly
                    
                    prime_paid_this_month = 0.0
                    if year_idx_operational in prime_disbursement_schedule:
                        if (month_idx - duree_construction_cfg) % 12 == 0: # Premier mois de l'année op.
                            prime_paid_this_month = prime_disbursement_schedule[year_idx_operational]
                    monthly_results_df.loc[current_month_end_date, 'Prime_Autoconso_Encaissee'] = prime_paid_this_month
                    monthly_results_df.loc[current_month_end_date, 'Revenus_Total'] = rev_surplus_monthly + rev_autocons_monthly + prime_paid_this_month
                    
                    # OPEX, TURPE, Amortissement
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Maintenance_Mensuel'] = opex_maint_indexed_annual_current / 12.0
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Assurance_Mensuel'] = opex_assur_indexed_annual_current / 12.0
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Admin_Mensuel'] = opex_admin_indexed_annual_current / 12.0
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Provision_Onduleur_Mensuel'] = inverter_prov_indexed_annual_current / 12.0
                    monthly_results_df.loc[current_month_end_date, 'OPEX'] = (opex_maint_indexed_annual_current + opex_assur_indexed_annual_current + opex_admin_indexed_annual_current + inverter_prov_indexed_annual_current) / 12.0
                    monthly_results_df.loc[current_month_end_date, 'TURPE'] = turpe_indexed_annual_current / 12.0
                    monthly_results_df.loc[current_month_end_date, 'Amortissement'] = depreciation_annual_current / 12.0
                
                # P&L (Suite)
                ebitda_month = (monthly_results_df.loc[current_month_end_date, 'Revenus_Total'] -
                                 monthly_results_df.loc[current_month_end_date, 'OPEX'] - 
                                 monthly_results_df.loc[current_month_end_date, 'TURPE'])
                monthly_results_df.loc[current_month_end_date, 'EBITDA'] = ebitda_month
                ebit_month = ebitda_month - monthly_results_df.loc[current_month_end_date, 'Amortissement']
                monthly_results_df.loc[current_month_end_date, 'EBIT'] = ebit_month
                
                ebt_before_loss_month = ebit_month - interest_paid_this_month # Utilise les intérêts calculés plus tôt
                taxable_ebt_month, loss_carryforward_balance = tax_engine.apply_loss_carryforward_cap(ebt_before_loss_month, loss_carryforward_balance)
                monthly_results_df.loc[current_month_end_date, 'EBT'] = taxable_ebt_month

                # Fiscalité (Paiements IS)
                tax_paid_this_month = 0.0
                if not is_construction_phase: # Pas d'IS pendant construction
                    if current_month_end_date.month in [3, 6, 9, 12]: # Paiement acomptes
                        tax_paid_this_month += current_quarterly_acompte_is
                    if current_month_end_date.month == mois_paiement_solde_is: # Paiement solde N-1
                        tax_paid_this_month += solde_IS_N_1_annee_precedente_a_payer_en_N
                    monthly_results_df.loc[current_month_end_date, 'Solde_IS_N_1_Paye_Mois'] = solde_IS_N_1_annee_precedente_a_payer_en_N
                
                monthly_results_df.loc[current_month_end_date, 'Tax_Payment'] = tax_paid_this_month # IS effectivement décaissé
                monthly_results_df.loc[current_month_end_date, 'Total_IS_Decaisse_Mois'] = tax_paid_this_month

                # Résultat Net (basé sur EBT après reports et IS décaissé)
                # ATTENTION: Pour P&L, RN = EBT (après reports) - IS théorique sur cet EBT.
                # Pour flux de trésorerie, RN = EBT (après reports) - IS effectivement payé.
                # Le FCFE utilise EBT - IS payé + Amort - Principal.
                # Ici, on calcule le RN "comptable" qui est EBT - IS théorique du mois.
                # L'IS théorique n'est pas directement calculé mensuellement ici, on utilise IS payé pour le flux.
                # Pour simplifier et être cohérent avec les flux, on peut définir RN après IS payé.
                # Si besoin d'un RN "comptable" strict, il faudrait un calcul d'IS théorique mensuel.
                # Option Flux de Trésorerie:
                monthly_results_df.loc[current_month_end_date, 'Resultat_Net'] = taxable_ebt_month - tax_paid_this_month

                # Mise à jour calcul IS annuel en fin d'année
                if not is_construction_phase and current_month_end_date.month == 12:
                    current_year_ebt_total = monthly_results_df[monthly_results_df.index.year == current_month_end_date.year]['EBT'].sum()
                    is_calcule_annee_en_cours = tax_engine.calculate_corporate_tax_pme(current_year_ebt_total)
                    
                    # Calcul du solde pour N, basé sur IS N (calculé ci-dessus) et acomptes déjà versés pour N (basés sur N-1)
                    acomptes_verses_pour_annee_N = current_quarterly_acompte_is * tax_engine.ACOMPTE_COUNT
                    solde_IS_N_1_annee_precedente_a_payer_en_N = is_calcule_annee_en_cours - acomptes_verses_pour_annee_N
                    
                    annual_tax_calculated_prev_year = is_calcule_annee_en_cours # Pour le calcul des acomptes de N+1
                    current_quarterly_acompte_is = tax_engine.calculate_quarterly_installment(annual_tax_calculated_prev_year)

                # TVA
                # TVA calculée uniquement sur les revenus taxables (excluant la prime)
                rev_taxable = monthly_results_df.loc[current_month_end_date, 'Revenus_Surplus'] + monthly_results_df.loc[current_month_end_date, 'Revenus_Autoconsommation']
                vat_collected_month = rev_taxable * vat_rate_operations
                vat_deductible_opex_turpe_month = (monthly_results_df.loc[current_month_end_date, 'OPEX'] + monthly_results_df.loc[current_month_end_date, 'TURPE']) * vat_rate_operations
                vat_deductible_capex_month = tva_sur_capex_initial if month_idx == vat_capex_recovery_month_offset else 0.0
                
                net_vat_before_carryforward = vat_collected_month - vat_deductible_opex_turpe_month - vat_deductible_capex_month
                vat_to_settle_this_month = net_vat_before_carryforward + vat_credit_carryforward
                
                vat_payment_this_month = 0.0
                remboursement_credit_tva_actif = bool(global_config.get("remboursement_credit_tva_actif", True))
                seuil_remboursement_tva = float(global_config.get("seuil_remboursement_tva", 500.0))

                if vat_to_settle_this_month > 0:
                    vat_payment_this_month = vat_to_settle_this_month
                    vat_credit_carryforward = 0.0
                else: # Crédit de TVA
                    if remboursement_credit_tva_actif and abs(vat_to_settle_this_month) >= seuil_remboursement_tva:
                        vat_payment_this_month = vat_to_settle_this_month # Remboursement encaissé (flux positif pour entreprise)
                        vat_credit_carryforward = 0.0
                    else:
                        vat_payment_this_month = 0.0 # Pas de décaissement ni d'encaissement
                        vat_credit_carryforward = vat_to_settle_this_month # Report du crédit

                monthly_results_df.loc[current_month_end_date, 'VAT_Collectee'] = vat_collected_month
                monthly_results_df.loc[current_month_end_date, 'VAT_Deductible_CAPEX'] = vat_deductible_capex_month
                monthly_results_df.loc[current_month_end_date, 'VAT_Deductible_OPEX_TURPE'] = vat_deductible_opex_turpe_month
                monthly_results_df.loc[current_month_end_date, 'VAT_Due_Mois'] = vat_to_settle_this_month # Solde avant décision paiement/report
                monthly_results_df.loc[current_month_end_date, 'VAT_Payment'] = vat_payment_this_month # Flux de TVA effectif

                # BFR
                bfr_revenus_mensuels = monthly_results_df.loc[current_month_end_date, 'Revenus_Total']
                bfr_opex_turpe_mensuels = monthly_results_df.loc[current_month_end_date, 'OPEX'] + monthly_results_df.loc[current_month_end_date, 'TURPE']
                
                bfr_creances_clients_mois = (bfr_revenus_mensuels / 30.0) * bfr_receivables_days_config if not is_construction_phase else 0.0
                bfr_dettes_fourn_mois = (bfr_opex_turpe_mensuels / 30.0) * bfr_payables_days_config if not is_construction_phase else 0.0
                
                bfr_current_month = bfr_creances_clients_mois - bfr_dettes_fourn_mois
                delta_bfr_current_month = bfr_current_month - bfr_previous_month_val
                
                monthly_results_df.loc[current_month_end_date, 'BFR_Mensuel'] = bfr_current_month
                monthly_results_df.loc[current_month_end_date, 'Delta_BFR_Mensuel'] = delta_bfr_current_month
                bfr_previous_month_val = bfr_current_month
            # --- FIN DE LA BOUCLE MENSUELLE ---

            # --- 5. CALCULS POST-BOUCLE (FCFE, OCF Projet, Soldes de Trésorerie) ---
            # Récupération des séries finales depuis monthly_results_df
            s_ebt = monthly_results_df['EBT'].fillna(0)
            s_is_decaisse = monthly_results_df['Total_IS_Decaisse_Mois'].fillna(0)
            s_amort = monthly_results_df['Amortissement'].fillna(0)
            s_prime_encaissee = monthly_results_df['Prime_Autoconso_Encaissee'].fillna(0)
            s_vat_payment = monthly_results_df['VAT_Payment'].fillna(0) # C'est le flux de TVA (peut être positif si remboursement)
            s_delta_bfr = monthly_results_df['Delta_BFR_Mensuel'].fillna(0)
            s_capex_brut_decaisse = monthly_results_df['CAPEX_Initial_Mensuel'].fillna(0)
            
            s_debt_drawn = monthly_results_df['Debt_Drawn_This_Month'].fillna(0)
            s_principal_repaid = monthly_results_df['Principal_Rembourse'].fillna(0)
            s_net_debt_issued = s_debt_drawn - s_principal_repaid
            
            # FCFE (sans s_prime_encaissee qui est déjà incluse dans s_ebt)
            monthly_results_df['FCFE'] = (s_ebt - s_is_decaisse + s_amort - s_vat_payment - s_delta_bfr - s_capex_brut_decaisse + s_net_debt_issued)

            # NOPAT (Requis pour OCF Projet)
            s_ebit = monthly_results_df['EBIT'].fillna(0)
            impot_theorique_sur_ebit_mensuel = pd.Series(0.0, index=monthly_results_df.index)
            # Recalculer l'impôt théorique sur EBIT pour NOPAT (plus précis que IS décaissé)
            # Nécessite une nouvelle boucle ou une approche vectorielle si possible
            # Simplification pour l'instant: on pourrait utiliser (EBIT * (1-Taux IS après report))
            # Mais pour être précis, il faut ré-appliquer la logique tax_engine sur EBIT
            loss_carryforward_for_nopat = 0.0
            for idx_nopat, ebit_val_nopat in s_ebit.items():
                taxable_ebit_for_nopat, loss_carryforward_for_nopat = tax_engine.apply_loss_carryforward_cap(ebit_val_nopat, loss_carryforward_for_nopat)
                impot_theorique_sur_ebit_mensuel[idx_nopat] = tax_engine.calculate_corporate_tax_pme(taxable_ebit_for_nopat) #IS sur EBT taxable mensuel
            
            s_nopat = s_ebit - impot_theorique_sur_ebit_mensuel # NOPAT = EBIT * (1-T_eff)
            
            # OCF Projet (sans s_prime_encaissee qui est déjà incluse dans s_nopat)
            monthly_results_df['OCF_Projet'] = (s_nopat + s_amort - s_capex_brut_decaisse - s_delta_bfr - s_vat_payment)
            
            # Solde de Trésorerie
            # equity_injected_monthly_series est déjà calculé et utilisé pour les métriques de FP
            cash_flow_to_equity_holders_monthly = monthly_results_df['FCFE'].fillna(0)
            # Le flux total pour l'entreprise est FCFE + injections de FP (qui sont déjà dans FCFE via -capex_brut et +net_debt)
            # Donc le flux de trésorerie de l'entreprise est FCFE + equity_injected (qui est négatif) - debt_drawn (déjà dans net_debt) + principal_repaid (déjà dans net_debt)
            # Une approche plus simple : Flux de trésorerie = CFO + CFI + CFF (sans inclure equity/debt dans CFO/CFI)
            # Le `Solde_Tresorerie_Fin_Mois` doit refléter le cash que l'entreprise a réellement.
            # C'est la somme de tous les flux nets (exploitation, investissement, financement) affectant la trésorerie.
            # Variation Nette de Trésorerie = FCFE + (Injection Equity - Rachat Equity) + (Nouvelle Dette - Remboursement Principal)
            # Si equity_injected_monthly_series est l'apport des actionnaires (positif pour l'entreprise)
            # FCFE est ce qui reste APRES service de la dette (principal et intérêts) et investissements, pour les actionnaires.
            # Donc, le flux qui modifie la trésorerie de l'entreprise est FCFE + Apport Equity (si pas déjà dans CAPEX)
            
            # Le plus simple : Somme(Revenus Encaissés - Toutes Dépenses Décaissées)
            # monthly_results_df['Flux_Net_Tresorerie_Entreprise'] = monthly_results_df['Revenus_Total'] - monthly_results_df['OPEX'] - monthly_results_df['TURPE'] - monthly_results_df['Total_IS_Decaisse_Mois'] - monthly_results_df['VAT_Payment'] - monthly_results_df['CAPEX_Initial_Mensuel'] - monthly_results_df['Service_Dette'] + monthly_results_df['Debt_Drawn_This_Month'] + equity_injected_monthly_series + monthly_results_df['Prime_Autoconso_Encaissee']
            # Ce calcul est complexe. On s'appuie sur le fait que FCFE est le flux disponible pour les actionnaires APRES tout.
            # Si les actionnaires injectent des fonds, la trésorerie augmente. Si FCFE est positif et non distribué, la trésorerie augmente.
            flux_treso_nets_mensuels = monthly_results_df['FCFE'].fillna(0) + equity_injected_monthly_series.fillna(0)

            monthly_results_df['Solde_Tresorerie_Fin_Mois'] = initial_cash_balance_at_true_t0 + flux_treso_nets_mensuels.cumsum()

            # --- 6. CALCUL DES INDICATEURS FINANCIERS FINAUX (VAN, TRI, etc.) ---
            re_annual = float(cout_fonds_propres_pct_config) # En pourcentage
            wacc_annual_at_pct = calculate_wacc(
                debt_ratio=debt_ratio_config,
                taux_interet_dette_pct=taux_interet_dette_pct_config,
                taux_imposition_pct=taux_imposition_standard_pct,
                cout_fonds_propres_pct=re_annual, # Doit être en % pour la fonction
                wacc_type="after_tax"
            )
            if wacc_annual_at_pct is None: wacc_annual_at_pct = 6.0 # Fallback en %
            
            re_monthly_rate = (1 + re_annual / 100.0)**(1/12) - 1
            wacc_monthly_at_rate = (1 + wacc_annual_at_pct / 100.0)**(1/12) - 1

            # Flux pour les actionnaires (equity): FCFE - injection d'equity (qui est négative au début)
            # equity_injected_monthly_series est l'apport des actionnaires (positif pour l'entreprise, négatif pour l'investisseur s'il sort de sa poche)
            # FCFE est le flux APRES investissement et financement de la dette, disponible pour les actionnaires.
            # Le flux pour le calcul du TRI Equity doit être : [-Injection Equity T0, FCFE T1, FCFE T2, ...]
            # Le FCFE inclut déjà l'impact de l'investissement initial (- s_capex_brut_decaisse + s_net_debt_issued)
            
            equity_cash_flows_for_irr_npv = monthly_results_df['FCFE'].fillna(0).values
            
            project_cash_flows_for_irr_npv = monthly_results_df['OCF_Projet'].fillna(0).values
            # Ajout de la valeur terminale au flux projet
            valeur_residuelle_nette_projet = (capex_net_subvention_info * valeur_residuelle_pct_config) - \
                                             (capex_brut_total_scenario * cout_demantelement_pct_config)
            if len(project_cash_flows_for_irr_npv) > 0:
                project_cash_flows_for_irr_npv[-1] += valeur_residuelle_nette_projet
            
            # NPV et IRR Equity
            npv_equity = npf.npv(re_monthly_rate, equity_cash_flows_for_irr_npv) if pd.notna(re_monthly_rate) else np.nan
            if is_equity_negligible:
                irr_equity = np.nan; roi_equity = np.nan
            else:
                irr_eq_raw = npf.irr(equity_cash_flows_for_irr_npv)
                irr_equity = (1 + irr_eq_raw)**12 - 1 if pd.notna(irr_eq_raw) and np.isfinite(irr_eq_raw) else np.nan
                # npv_equity est maintenant le NPV net pour l'actionnaire
                roi_equity = npv_equity / abs(net_equity_investment_total) if pd.notna(npv_equity) and abs(net_equity_investment_total) > 1e-9 else np.nan
            
            # NPV et IRR Projet
            irr_proj_raw = npf.irr(project_cash_flows_for_irr_npv)
            irr_project = (1 + irr_proj_raw)**12 - 1 if pd.notna(irr_proj_raw) and np.isfinite(irr_proj_raw) else np.nan
            npv_project = npf.npv(wacc_monthly_at_rate, project_cash_flows_for_irr_npv) if pd.notna(wacc_monthly_at_rate) else np.nan
            
            # Payback Periods
            # equity_investment_cash_flow_for_payback est identique à equity_cash_flows_for_irr_npv
            payback_equity_months = calculate_payback_months(equity_cash_flows_for_irr_npv)
            payback_equity_years = payback_equity_months / 12.0 if payback_equity_months is not None else np.nan
            if is_equity_negligible: payback_equity_years = np.nan
            
            payback_project_months = calculate_payback_months(project_cash_flows_for_irr_npv) # OCF_Projet inclut déjà -CAPEX
            payback_project_years = payback_project_months / 12.0 if payback_project_months is not None else np.nan
            
            # LCOE et DSCR
            avg_dscr = calculate_avg_dscr_revised(monthly_results_df, tax_rate_decimal) if loan_active else np.nan
            # lcoe = calculate_lcoe_engineering(wacc_monthly_at_rate, monthly_results_df, valeur_residuelle_nette_projet)

            # LCOE (Calculé sur une base annuelle)
            lcoe = calculate_lcoe_annual_aggregation(
                wacc_annual_discount_rate=wacc_annual_at_pct / 100.0 if pd.notna(wacc_annual_at_pct) else None,
                monthly_df_results=monthly_results_df,
                terminal_value_net_project=valeur_residuelle_nette_projet,
                construction_period_months=duree_construction_cfg
            )
            if lcoe is None: lcoe = np.nan # S'assurer que c'est NaN si le calcul échoue
            
            # Taux Autoconsommation / Autoproduction Globaux
            total_production_an = monthly_results_df['Production_kWh'].sum()
            total_autocons_an = monthly_results_df['Autoconsommation_kWh'].sum()
            total_cons_an = monthly_results_df['Consommation_kWh'].sum()
            autoconsumption_rate = total_autocons_an / total_cons_an if total_cons_an > 1e-6 else 0.0
            autoproduction_rate = total_autocons_an / total_production_an if total_production_an > 1e-6 else 0.0

            # --- 7. FORMATAGE DES RÉSULTATS FINAUX ---
            results_output = {
                "scenario": scenario_name, "prix_revente": prix_vente_final_a_utiliser,
                "source_parametres_simulation": source_des_inputs,
                "capex_base_utilise": capex_base_input_agg, # CAPEX total agrégé avant modif scénario
                "opex_base_utilise_maintenance_annuel": total_opex_maintenance_base_annual, # OPEX total agrégé avant modif scénario
                "opex_base_utilise_assurance_annuel": total_opex_assurance_base_annual,
                "opex_base_utilise_admin_annuel": total_opex_admin_base_annual,
                "puissance_base_utilisee": puissance_kwc_global_agg, # Puissance totale agrégée
                
                "capex_scenario_simule_initial": capex_brut_total_scenario, # Pour info (avant subvention)
                "capex_scenario_final_utilise": capex_brut_total_scenario, # CAPEX Brut total après modif scénario
                "capex_net_subvention_final": capex_net_subvention_info, # CAPEX Brut - Subvention (pour amortissement)
                "subvention_finale_retenue_pour_calculs": subvention_totale_projet,
                
                "opex_scenario_maintenance_annuel_simule": opex_maintenance_scenario_annual, # Après modif scénario
                "opex_scenario_assurance_annuel_simule": opex_assurance_scenario_annual,
                "opex_scenario_admin_annuel_simule": opex_admin_scenario_annual,
                
                "debt_amount": debt_amount_total,
                "net_equity_investment": net_equity_investment_total,
                "total_subvention": subvention_totale_projet, # Redondant avec subvention_finale..., à nettoyer si besoin
                
                "autoconsumption_rate": autoconsumption_rate, "autoproduction_rate": autoproduction_rate,
                "wacc_after_tax_annual": wacc_annual_at_pct / 100.0 if pd.notna(wacc_annual_at_pct) else np.nan, # En décimal
                "cost_of_equity_annual": re_annual / 100.0 if pd.notna(re_annual) else np.nan, # En décimal
                "lcoe": lcoe, 
                "irr": irr_equity, "npv": npv_equity, "roi": roi_equity, "payback_period": payback_equity_years,
                "irr_project": irr_project, "npv_project": npv_project, "payback_project": payback_project_years,
                "avg_dscr": avg_dscr,
                
                "monthly_data": monthly_results_df.copy(), # DataFrame complet
                'hourly_aggregated_data': hourly_data_to_return.copy(), # Données horaires de base agrégées
                
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
            if pd.isna(npv_project) or pd.isna(irr_project): logger.warning("NPV ou IRR Projet est NaN.")
            
            return results_output

        except ValueError as ve: # Capturer les erreurs de valeur (ex: scénario non trouvé)
            logger.error(f"ERREUR MOTEUR (ValueError): Scenario '{scenario_name}', Erreur: {ve}", exc_info=True)
            return {"error": str(ve)}
        except TypeError as te: # Capturer les erreurs de type
            logger.error(f"ERREUR MOTEUR (TypeError): Scenario '{scenario_name}', Erreur: {te}", exc_info=True)
            return {"error": str(te)}
        except Exception as e_unexp: # Capturer toutes les autres erreurs inattendues
            logger.error(f"ERREUR MOTEUR INATTENDUE (calculate_financial_indicators): Scenario '{scenario_name}', Erreur: {e_unexp}", exc_info=True)
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
            # Utiliser des valeurs par défaut robustes pour les bornes de recherche de prix
            prix_min_recherche_default = 0.01
            prix_max_recherche_default = 0.50
            
            prix_min_recherche = float(global_config_sim.get('prix_min_revente', prix_min_recherche_default))
            prix_max_recherche = float(global_config_sim.get('prix_max_revente', prix_max_recherche_default))
            
            if prix_min_recherche >= prix_max_recherche:
                logger.warning(f"Bornes de recherche de prix min ({prix_min_recherche}) >= max ({prix_max_recherche}). Réinitialisation aux valeurs par défaut.")
                prix_min_recherche = prix_min_recherche_default
                prix_max_recherche = prix_max_recherche_default

            optimal_price_found = None
            simulation_cache = {} 

            # --- Définition des fonctions objectifs pour brentq et minimize ---
            def get_metric_from_results(results_dict, target_irr_val, target_npv_val):
                """Helper pour extraire la métrique cible (IRR ou NPV projet) des résultats."""
                if results_dict is None or (isinstance(results_dict, dict) and "error" in results_dict):
                    return np.nan
                if target_irr_val is not None:
                    return results_dict.get('irr_project', np.nan)
                if target_npv_val is not None:
                    return results_dict.get('npv_project', np.nan)
                return np.nan

            def calculate_target_metric_value(price_candidate_val):
                """Calcule ou récupère du cache la valeur de la métrique cible pour un prix donné."""
                price_key = round(price_candidate_val, 8)
                if price_key in simulation_cache:
                    return get_metric_from_results(simulation_cache[price_key], target_irr, target_npv)

                results_sim_calc = self.calculate_financial_indicators(
                    scenario_name, prix_revente=price_candidate_val,
                    override_source_prix_autoconso=override_source_prix_autoconso,
                    sites_config=sites_config
                )
                simulation_cache[price_key] = results_sim_calc
                
                # Log pour débogage
                metric_val_log = get_metric_from_results(results_sim_calc, target_irr, target_npv)
                target_type_log = "NPV Projet" if target_npv is not None else "IRR Projet"
                logger.info(f"SIMULATE_PRICE_DEBUG: Prix testé={price_candidate_val:.4f}, {target_type_log} retourné={metric_val_log}")
                
                return metric_val_log

            def objective_for_brentq_solver(price_candidate_brentq):
                """Fonction objectif pour brentq (metric - target)."""
                actual_metric = calculate_target_metric_value(price_candidate_brentq)
                if not (pd.notna(actual_metric) and np.isfinite(actual_metric)):
                    return np.nan # Ou une grande valeur si brentq ne gère pas NaN
                
                target_value_for_diff = target_irr if target_irr is not None else target_npv
                return actual_metric - target_value_for_diff

            # --- Tentative avec brentq ---
            try:
                val_at_min_bound = objective_for_brentq_solver(prix_min_recherche)
                val_at_max_bound = objective_for_brentq_solver(prix_max_recherche)

                if pd.notna(val_at_min_bound) and pd.notna(val_at_max_bound) and (np.sign(val_at_min_bound) * np.sign(val_at_max_bound) <= 0):
                    if abs(val_at_min_bound) < 1e-7: optimal_price_found = prix_min_recherche
                    elif abs(val_at_max_bound) < 1e-7: optimal_price_found = prix_max_recherche
                    else:
                        optimal_price_found = brentq(objective_for_brentq_solver, prix_min_recherche, prix_max_recherche, xtol=1e-7, rtol=1e-7, maxiter=100)
                    if optimal_price_found is not None: logger.info(f"SIMULATE PRICE: Brentq a trouvé une solution: {optimal_price_found:.8f}")
                else:
                    logger.warning(f"SIMULATE PRICE (Brentq): Pas de changement de signe ou NaN aux bornes. MinVal={val_at_min_bound}, MaxVal={val_at_max_bound}. Passage à 'minimize'.")
            except RuntimeError as e_brentq_rt:
                logger.warning(f"SIMULATE PRICE: Brentq n'a pas convergé ({e_brentq_rt}). Passage à 'minimize'.")
            except Exception as e_brentq_unexp:
                logger.error(f"SIMULATE PRICE: Erreur inattendue avec brentq ({e_brentq_unexp}). Passage à 'minimize'.")

            # --- Tentative avec minimize si brentq échoue ---
            if optimal_price_found is None:
                simulation_cache.clear() # Vider le cache car les appels précédents peuvent avoir échoué partiellement
                
                def objective_for_minimize_solver(price_array_min):
                    """Fonction objectif pour minimize ((metric - target)^2)."""
                    price_candidate_min_val = float(price_array_min[0]) # minimize attend un array
                    # Vérifier si le prix est dans les bornes (L-BFGS-B le fait, mais double sécurité)
                    if not (prix_min_recherche <= price_candidate_min_val <= prix_max_recherche):
                        return 1e12 # Pénalité forte
                        
                    actual_metric_min = calculate_target_metric_value(price_candidate_min_val)
                    if not (pd.notna(actual_metric_min) and np.isfinite(actual_metric_min)):
                        return 1e10 # Pénalité si indicateurs non calculables
                    
                    target_value_for_sq_diff = target_irr if target_irr is not None else target_npv
                    return (actual_metric_min - target_value_for_sq_diff)**2

                # Point de départ pour minimize (milieu de l'intervalle)
                initial_guess_for_minimize = np.clip((prix_min_recherche + prix_max_recherche) / 2.0, prix_min_recherche, prix_max_recherche)
                
                minimize_options = {'ftol': 1e-10, 'gtol': 1e-8, 'maxiter': 150, 'disp': False}
                res_minimize_calc = minimize(
                    objective_for_minimize_solver, [initial_guess_for_minimize], 
                    method='L-BFGS-B', # Gère les bornes
                    bounds=[(prix_min_recherche, prix_max_recherche)], 
                    options=minimize_options
                )
                
                # Évaluer la solution de minimize
                if res_minimize_calc.success and abs(res_minimize_calc.fun) < 1e-6: # Objectif proche de zéro
                    optimal_price_found = res_minimize_calc.x[0]
                    logger.info(f"SIMULATE PRICE: Minimize (L-BFGS-B) a trouvé une solution: {optimal_price_found:.8f}")
                else:
                    logger.warning(f"SIMULATE PRICE: Minimize (L-BFGS-B) n'a pas trouvé de solution satisfaisante. Success: {res_minimize_calc.success}, Fun: {res_minimize_calc.fun:.2e}, Msg: {res_minimize_calc.message}")

            # --- Vérification finale et retour ---
            if optimal_price_found is None:
                raise RuntimeError("Aucun prix optimal déterminé après toutes les tentatives (brentq et minimize). Vérifiez les logs et les bornes de recherche.")
            
            # S'assurer que le prix trouvé est bien dans les bornes initiales
            optimal_price_found = np.clip(optimal_price_found, prix_min_recherche, prix_max_recherche)

            # Recalculer les indicateurs une dernière fois avec le prix optimal trouvé
            simulation_cache.clear() # Vider pour s'assurer d'un calcul frais
            final_results_at_optimal = self.calculate_financial_indicators(
                scenario_name, prix_revente=optimal_price_found,
                override_source_prix_autoconso=override_source_prix_autoconso, sites_config=sites_config
            )

            if final_results_at_optimal and isinstance(final_results_at_optimal, dict) and "error" not in final_results_at_optimal:
                final_results_at_optimal['prix_revente_optimal_pour_cible'] = optimal_price_found
                final_results_at_optimal['target_irr_asked_for_project'] = target_irr
                final_results_at_optimal['target_npv_asked_for_project'] = target_npv
                return final_results_at_optimal
            else:
                error_detail_final = final_results_at_optimal.get("error", "Calcul final des indicateurs échoué") if isinstance(final_results_at_optimal, dict) else "Calcul final des indicateurs échoué"
                raise RuntimeError(f"Échec du recalcul final des indicateurs avec le prix optimal {optimal_price_found:.8f}: {error_detail_final}")

        except ValueError as ve_sim: # Capturer les erreurs de valeur (ex: pas de cible)
            logger.error(f"ERREUR SIMULATION PRIX (ValueError): {ve_sim}", exc_info=True)
            return {"error": str(ve_sim)}
        except RuntimeError as rte_sim: # Capturer RuntimeError (ex: pas de solution)
            logger.error(f"ERREUR SIMULATION PRIX (RuntimeError): {rte_sim}", exc_info=True)
            return {"error": str(rte_sim)}
        except Exception as e_fatal_sim: # Capturer toutes les autres erreurs
            logger.error(f"ERREUR FATALE (simulate_selling_price): {e_fatal_sim}", exc_info=True)
            return {"error": f"Erreur inattendue en simulation de prix: {e_fatal_sim}"}