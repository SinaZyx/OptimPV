# modules/engine_module/core_analyzer.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import traceback
import copy
from scipy.optimize import minimize, brentq # brentq est utilisé dans simulate_selling_price
import logging
import sys
import os

# Moteur d'analyse financière pour projets photovoltaïques
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from debug_financial_logger import FinancialDebugLogger
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
from .treasury_placement import log_tva_placement, clear_tva_log, TreasuryPlacementManager
from .equity_calculations import EquityCalculations
from .treasury_validator import validate_treasury_data

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
    
    def verify_equity_calculations_coherence(self, irr, npv, payback, investment, discount_rate):
        """
        Vérifie la cohérence mathématique des indicateurs equity
        """
        return self.equity_calc.verify_equity_calculations_coherence(irr, npv, payback, investment, discount_rate)
    
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
        
        # Créer les instances des nouveaux modules
        self.equity_calc = EquityCalculations()
        self.treasury_manager = TreasuryPlacementManager(config)
        
        logger.info(f"AnalysisEngine initialisé. npf_available: {self.npf_available}")
        logger.info(f"Sites de données après validation: {list(self.sites_data.keys())}")
    
    def _validate_input_data(self, global_config: dict, scenario: dict, prix_revente: float = None):
        """Valide les données d'entrée pour éviter les erreurs de calcul."""
        errors = []
        
        # Vérifier les paramètres financiers critiques avec les NOUVEAUX noms
        required_params = [
            'taux_interet_dette', 'cout_fonds_propres', 'debt_ratio',
            'duree_ppa', 'taux_imposition'
        ]
        
        for param in required_params:
            if param not in global_config:
                errors.append(f"Paramètre manquant: {param}")
                continue
                
            value = global_config[param]
            if value is None or (isinstance(value, (int, float)) and not np.isfinite(value)):
                errors.append(f"Valeur invalide pour {param}: {value}")
        
        # Vérifier les ratios cohérents
        if 'debt_ratio' in global_config:
            debt_ratio = global_config['debt_ratio']
            if not (0 <= debt_ratio <= 1):
                errors.append(f"Ratio de dette invalide: {debt_ratio} (doit être entre 0 et 1)")
        
        # Vérifier le multiplicateur CAPEX du scénario
        capex_mult = scenario.get('capex_multiplier', 1.0)
        if capex_mult <= 0:
            errors.append(f"Multiplicateur CAPEX invalide: {capex_mult}")
        
        # Vérifier la cohérence économique de base
        if 'duree_ppa' in global_config:
            duree = global_config['duree_ppa']
            if duree <= 0:
                errors.append(f"Durée PPA invalide: {duree}")
        
        # Note: CAPEX est maintenant calculé par agrégation des sites, pas dans global_config
        
        # Vérifier le prix de revente si fourni
        if prix_revente is not None:
            if prix_revente <= 0:
                errors.append(f"Prix de revente invalide: {prix_revente}")
        
        # Vérifier la cohérence des données de production
        if not self.sites_data:
            errors.append("Aucune donnée de site disponible")
        else:
            for site_name, site_df in self.sites_data.items():
                if site_df.empty:
                    errors.append(f"Données vides pour le site: {site_name}")
                    continue
                    
                # Vérifier avec tolérance de casse
                required_cols_map = {
                    'Production_kWh': ['Production_kWh', 'production_kwh'],
                    'Consommation_kWh': ['Consommation_kWh', 'consumption_kwh', 'consommation_kwh']
                }
                
                missing_cols = []
                for expected_col, variants in required_cols_map.items():
                    if not any(col in site_df.columns for col in variants):
                        missing_cols.append(expected_col)
                
                if missing_cols:
                    errors.append(f"Colonnes manquantes dans {site_name}: {missing_cols}")
        
        if errors:
            error_msg = "Erreurs de validation des données d'entrée:\n" + "\n".join(f"  - {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)


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
            
            # --- VALIDATION DES DONNÉES D'ENTRÉE ---
            try:
                self._validate_input_data(global_config, scenario, prix_revente)
            except ValueError as ve:
                # Logger l'avertissement mais continuer si non critique
                logger.warning(f"Validation warning: {ve}")
                # Décider si on continue ou non selon la sévérité
                if "critique" in str(ve).lower():
                    raise
            
            # Système de debug pour traçage des calculs financiers
            debug_mode = False  # Activer temporairement
            if debug_mode:
                debug_log = {
                    'timestamp': datetime.now().isoformat(),
                    'scenario': scenario_name,
                    'prix_revente': prix_revente,
                    'calculs_equity': {}
                }

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
            valeur_residuelle_pct_config = float(global_config.get("valeur_residuelle_pct", 0.0)) # % du CAPEX Net (après subvention)
            cout_demantelement_pct_config = float(global_config.get("cout_demantelement_pct", 0.0)) # % CAPEX Brut
            
            # --- Paramètres de financement ---
            cout_fonds_propres_pct_config = float(global_config.get("cout_fonds_propres", 8.0))
            loan_active = global_config.get("with_loan", True)
            debt_ratio_config = float(global_config.get("debt_ratio", 0.80)) if loan_active else 0.0
            debt_term_years_config = int(global_config.get("debt_term_years", 20)) if loan_active else 0
            taux_interet_dette_pct_config = float(global_config.get("taux_interet_dette", 4.0)) if loan_active else 0.0
            taux_interet_dette_annual = taux_interet_dette_pct_config / 100.0
            capitalize_construction_interest = bool(global_config.get("capitalize_construction_interest", False))

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
                'CAPEX_Initial_Mensuel', 'Debt_Drawn_This_Month', 'Equity_Injected_This_Month', 'Solde_Dette_Fin_Mois',
                'Valeur_Residuelle_Brute', 'Cout_Demantelement', 'Valeur_Residuelle_Nette',
                'FCFE', 'OCF_Projet', 'Solde_Tresorerie_Fin_Mois',
                'Remplacement_Onduleur_Effectue', 'Deficit_Financement_Onduleur'
            ]
            for col in monthly_cols: monthly_results_df[col] = 0.0
            # Sim_Year sera calculé dans la boucle à partir de l'index opérationnel.

            # --- 3. CALCULS PRÉLIMINAIRES (Financement, Amortissement) ---
            capex_pour_repartition_mensuelle = montant_capex_pour_financement_et_flux / duree_construction_cfg if duree_construction_cfg > 0 else montant_capex_pour_financement_et_flux
            
            debt_amount_total = montant_capex_pour_financement_et_flux * debt_ratio_config if loan_active else 0.0
            
            # CALCUL PROFESSIONNEL : La subvention réduit l'investissement initial
            net_equity_investment_total = self.equity_calc.calculate_net_equity_investment_professional(
                capex_total=montant_capex_pour_financement_et_flux,
                debt_amount=debt_amount_total,
                subvention_montant=subvention_totale_projet
            )
            
            if debug_mode:
                debug_log['calculs_equity']['net_equity_investment'] = {
                    'capex_total': montant_capex_pour_financement_et_flux,
                    'debt_amount': debt_amount_total,
                    'subvention': subvention_totale_projet,
                    'net_equity_investment_calculated': net_equity_investment_total
                }
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
                # Financement en une seule fois au PREMIER mois de construction
                if not is_equity_negligible:
                    equity_injected_monthly_series.iloc[0] = net_equity_investment_total
                if loan_active:
                    debt_drawn_monthly_series.iloc[0] = debt_amount_total
            elif duree_construction_cfg == 0 and num_total_simulation_months > 0 : # Pas de construction, tout au premier mois (T0 de l'exploitation)
                 if not is_equity_negligible: equity_injected_monthly_series.iloc[0] = net_equity_investment_total
                 if loan_active: debt_drawn_monthly_series.iloc[0] = debt_amount_total

            # Calcul de la valeur résiduelle (variables utilisées dans la boucle)
            # Note: Asymétrie intentionnelle
            # - VR basée sur la valeur comptable de l'actif (CAPEX net après subvention)
            # - Démantèlement basé sur le coût réel de l'installation complète (CAPEX brut)
            # Cette approche est conservative et reflète la réalité économique
            valeur_residuelle_brute = capex_net_subvention_info * valeur_residuelle_pct_config
            cout_demantelement = capex_brut_total_scenario * cout_demantelement_pct_config
            valeur_residuelle_nette_projet = valeur_residuelle_brute - cout_demantelement
            
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
                
                # Les injections de fonds propres sont basées sur la série précalculée
                current_equity_injection_for_month = equity_injected_monthly_series.iloc[month_idx] if month_idx < len(equity_injected_monthly_series) else 0.0
                monthly_results_df.loc[current_month_end_date, 'Equity_Injected_This_Month'] = current_equity_injection_for_month

                # Calcul des Intérêts et Principal de la Dette
                interest_paid_this_month = 0.0
                principal_repaid_this_month = 0.0
                if loan_active:
                    if is_construction_phase:
                        # CORRECTION: Les intérêts sont TOUJOURS payés pendant la construction
                        if current_debt_drawn_balance > 0:
                            interest_paid_this_month = current_debt_drawn_balance * (taux_interet_dette_annual / 12.0)
                            
                            # Capitalisation OPTIONNELLE en PLUS du paiement (pas à la place)
                            if capitalize_construction_interest:
                                accumulated_capitalized_interest += interest_paid_this_month
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
                    # Les revenus totaux NE doivent PAS inclure la prime (qui est une subvention d'exploitation)
                    monthly_results_df.loc[current_month_end_date, 'Revenus_Total'] = rev_surplus_monthly + rev_autocons_monthly
                    
                    # OPEX, TURPE, Amortissement
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Maintenance_Mensuel'] = opex_maint_indexed_annual_current / 12.0
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Assurance_Mensuel'] = opex_assur_indexed_annual_current / 12.0
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Admin_Mensuel'] = opex_admin_indexed_annual_current / 12.0
                    
                    # Gestion des provisions onduleur après remplacement
                    provision_onduleur_mensuelle = inverter_prov_indexed_annual_current / 12.0
                    
                    # Vérifier si un remplacement a déjà eu lieu
                    remplacements_effectues = monthly_results_df.loc[:current_month_end_date, 'Remplacement_Onduleur_Effectue'].sum() if 'Remplacement_Onduleur_Effectue' in monthly_results_df.columns else 0
                    
                    # Si le projet continue après le premier remplacement et qu'on veut provisionner pour le suivant
                    if remplacements_effectues > 0 and (num_total_simulation_months - month_idx) > duree_vie_onduleur * 12:
                        # Continuer les provisions pour le prochain onduleur
                        monthly_results_df.loc[current_month_end_date, 'OPEX_Provision_Onduleur_Mensuel'] = provision_onduleur_mensuelle
                    elif remplacements_effectues == 0:
                        # Provisions normales pour le premier onduleur
                        monthly_results_df.loc[current_month_end_date, 'OPEX_Provision_Onduleur_Mensuel'] = provision_onduleur_mensuelle
                    else:
                        # Arrêter les provisions si on est proche de la fin du projet
                        monthly_results_df.loc[current_month_end_date, 'OPEX_Provision_Onduleur_Mensuel'] = 0.0
                        provision_onduleur_mensuelle = 0.0
                    
                    monthly_results_df.loc[current_month_end_date, 'OPEX'] = (opex_maint_indexed_annual_current + opex_assur_indexed_annual_current + opex_admin_indexed_annual_current + provision_onduleur_mensuelle) / 12.0
                    monthly_results_df.loc[current_month_end_date, 'TURPE'] = turpe_indexed_annual_current / 12.0
                    monthly_results_df.loc[current_month_end_date, 'Amortissement'] = depreciation_annual_current / 12.0
                
                # P&L (Suite)
                ebitda_month = (monthly_results_df.loc[current_month_end_date, 'Revenus_Total'] -
                                 monthly_results_df.loc[current_month_end_date, 'OPEX'] - 
                                 monthly_results_df.loc[current_month_end_date, 'TURPE'])
                monthly_results_df.loc[current_month_end_date, 'EBITDA'] = ebitda_month
                ebit_month = ebitda_month - monthly_results_df.loc[current_month_end_date, 'Amortissement']
                monthly_results_df.loc[current_month_end_date, 'EBIT'] = ebit_month
                
                # EBT inclut les intérêts payés (négatif) et les intérêts reçus (positif)
                interets_recus_mois = monthly_results_df.loc[current_month_end_date, 'Interets_Totaux_Mensuels'] if 'Interets_Totaux_Mensuels' in monthly_results_df.columns else 0.0
                ebt_before_loss_month = ebit_month - interest_paid_this_month + interets_recus_mois # Intérêts payés moins intérêts reçus
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
                # Calculer le mois de récupération TVA depuis le DÉBUT DE L'EXPLOITATION
                if not is_construction_phase:
                    months_since_operation_start = month_idx - duree_construction_cfg
                    vat_deductible_capex_month = tva_sur_capex_initial if months_since_operation_start == vat_capex_recovery_month_offset else 0.0
                else:
                    vat_deductible_capex_month = 0.0  # Pas de récupération TVA pendant la construction
                
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
                # Calculer les revenus taxables (sans la prime) pour la base des créances clients
                revenus_pour_bfr = monthly_results_df.loc[current_month_end_date, 'Revenus_Surplus'] + \
                                   monthly_results_df.loc[current_month_end_date, 'Revenus_Autoconsommation']
                
                bfr_opex_turpe_mensuels = monthly_results_df.loc[current_month_end_date, 'OPEX'] + \
                                          monthly_results_df.loc[current_month_end_date, 'TURPE']
                
                # Les créances clients sont basées sur les revenus soumis à délai de paiement (excluant la prime)
                bfr_creances_clients_mois = (revenus_pour_bfr / 30.0) * bfr_receivables_days_config if not is_construction_phase else 0.0
                bfr_dettes_fourn_mois = (bfr_opex_turpe_mensuels / 30.0) * bfr_payables_days_config if not is_construction_phase else 0.0
                
                bfr_current_month = bfr_creances_clients_mois - bfr_dettes_fourn_mois
                delta_bfr_current_month = bfr_current_month - bfr_previous_month_val
                
                monthly_results_df.loc[current_month_end_date, 'BFR_Mensuel'] = bfr_current_month
                monthly_results_df.loc[current_month_end_date, 'Delta_BFR_Mensuel'] = delta_bfr_current_month
                bfr_previous_month_val = bfr_current_month
                
                # Valeur résiduelle - uniquement au dernier mois du projet
                if month_idx == num_total_simulation_months - 1:
                    monthly_results_df.loc[current_month_end_date, 'Valeur_Residuelle_Brute'] = valeur_residuelle_brute
                    monthly_results_df.loc[current_month_end_date, 'Cout_Demantelement'] = cout_demantelement
                    monthly_results_df.loc[current_month_end_date, 'Valeur_Residuelle_Nette'] = valeur_residuelle_nette_projet
                    logger.info(f"Valeur résiduelle ajoutée au dernier mois ({current_month_end_date}): {valeur_residuelle_nette_projet:.2f}€")
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
            
            # NOTE: Le calcul FCFE est déplacé après la consolidation des intérêts (ligne ~1015)

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
            
            # OCF Projet - Calcul déplacé après la consolidation des intérêts (ligne ~1030)
            
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

            # === GESTION DU FONDS DE RÉSERVE ONDULEUR (SINKING FUND) ===
            # Principe : ségrégation comptable obligatoire des provisions
            # Conforme aux meilleures pratiques comptables (IAS 37)
            if 'OPEX_Provision_Onduleur_Mensuel' in monthly_results_df.columns:
                
                # Créer les colonnes du fonds de réserve
                monthly_results_df['Fonds_Reserve_Onduleur_Constitutions'] = 0.0
                monthly_results_df['Fonds_Reserve_Onduleur_Interets'] = 0.0
                monthly_results_df['Fonds_Reserve_Onduleur_Total'] = 0.0
                monthly_results_df['Fonds_Reserve_Onduleur_Liberation'] = 0.0
                monthly_results_df['Fonds_Reserve_Onduleur_Interets_Imposables'] = 0.0
                monthly_results_df['Interets_Debloques_Imposables'] = 0.0  # Compatibilité ancienne colonne
                monthly_results_df['Tresorerie_Libre'] = 0.0  # Trésorerie hors fonds de réserve
                monthly_results_df['Remplacement_Onduleur_Paye'] = 0.0
                monthly_results_df['Reserve_Minimum_Requise'] = 0.0  # Réserve minimum basée sur coût onduleur
                
                # Variables de suivi du fonds
                capital_cumule = 0.0
                interets_cumules = 0.0
                
                # Récupérer le coût de l'onduleur pour la réserve minimum
                cout_onduleur_initial = 0.0
                if sites_config:
                    for site_id, site_cfg in sites_config.items():
                        if isinstance(site_cfg, dict) and site_cfg.get('site_type') != 'Consommateur Pur':
                            cout_onduleur_initial += float(site_cfg.get("opex_onduleur_total_cost_site", 0.0))
                            if cout_onduleur_initial > 0:
                                break
                else:
                    # Configuration globale
                    if global_config.get("opex_onduleur_provision_globale", False):
                        cout_onduleur_initial = float(global_config.get("opex_onduleur_total_cost_global", 0.0))
                
                logger.info(f"RÉSERVE MINIMUM - Coût onduleur initial: {cout_onduleur_initial:,.0f}€")
                
                # Récupérer la durée de vie onduleur
                duree_vie_onduleur = 15  # Par défaut
                if sites_config:
                    for site_id, site_cfg in sites_config.items():
                        if isinstance(site_cfg, dict) and site_cfg.get('site_type') != 'Consommateur Pur':
                            lifetime = int(site_cfg.get("opex_onduleur_lifetime_site", 0))
                            if lifetime > 0:
                                duree_vie_onduleur = lifetime
                                logger.info(f"Durée vie onduleur détectée: {lifetime} ans pour site {site_id}")
                                break
                
                # Paramètres de placement pour le fonds
                placement_actif = global_config.get("placement_tresorerie_active", False)
                is_optimization = global_config.get("is_optimization_mode", False)
                taux_annuel = float(global_config.get("taux_placement_provision_onduleur", 2.5))
                # Calcul du taux mensuel si les placements sont activés
                taux_mensuel = (1 + taux_annuel/100) ** (1/12) - 1 if placement_actif else 0.0
                
                logger.info(f"FONDS DE RÉSERVE ONDULEUR - Configuration: durée={duree_vie_onduleur} ans, placement_actif={placement_actif}, taux={taux_annuel}% annuel")
                
                # Parcourir tous les mois pour gérer le fonds
                for idx, date_mois in enumerate(monthly_results_df.index):
                    if idx < duree_construction_cfg:
                        continue
                        
                    # Récupérer la provision du mois (toujours constituée)
                    provision_mois = monthly_results_df.loc[date_mois, 'OPEX_Provision_Onduleur_Mensuel']
                    
                    # Vérifier que la provision est valide
                    if pd.isna(provision_mois) or not np.isfinite(provision_mois):
                        provision_mois = 0.0
                    
                    # Ajouter au capital du fonds de réserve
                    capital_cumule += provision_mois
                    
                    # Si placements activés, calculer les intérêts sur le fonds
                    if placement_actif and (capital_cumule + interets_cumules) > 0:
                        interets_mois = (capital_cumule + interets_cumules) * taux_mensuel
                        # Vérifier que les intérêts sont valides
                        if pd.isna(interets_mois) or not np.isfinite(interets_mois):
                            interets_mois = 0.0
                        interets_cumules += interets_mois
                    else:
                        interets_mois = 0.0
                    
                    # Enregistrer l'état du fonds de réserve
                    monthly_results_df.loc[date_mois, 'Fonds_Reserve_Onduleur_Constitutions'] = provision_mois
                    monthly_results_df.loc[date_mois, 'Fonds_Reserve_Onduleur_Interets'] = interets_mois
                    monthly_results_df.loc[date_mois, 'Fonds_Reserve_Onduleur_Total'] = capital_cumule + interets_cumules
                    
                    # Calculer la réserve minimum requise (coût onduleur indexé)
                    if cout_onduleur_initial > 0:
                        years_elapsed = max(0, (idx - duree_construction_cfg) / 12.0)
                        taux_inflation = float(global_config.get("taux_inflation_generale", 2.0))
                        inflation_factor = (1 + taux_inflation / 100) ** years_elapsed
                        reserve_minimum_requise = cout_onduleur_initial * inflation_factor
                    else:
                        reserve_minimum_requise = 0.0
                    
                    monthly_results_df.loc[date_mois, 'Reserve_Minimum_Requise'] = reserve_minimum_requise
                    
                    # Calculer la trésorerie libre (totale - fonds réservé - réserve minimum)
                    tresorerie_totale = monthly_results_df.loc[date_mois, 'Solde_Tresorerie_Fin_Mois']
                    if pd.isna(tresorerie_totale) or not np.isfinite(tresorerie_totale):
                        tresorerie_totale = 0.0
                    
                    # Trésorerie après déduction du fonds de réserve
                    tresorerie_apres_fonds = tresorerie_totale - (capital_cumule + interets_cumules)
                    
                    # Trésorerie disponible après réserve minimum
                    tresorerie_disponible = tresorerie_totale - reserve_minimum_requise
                    if pd.isna(tresorerie_disponible) or not np.isfinite(tresorerie_disponible):
                        tresorerie_disponible = 0.0
                    
                    monthly_results_df.loc[date_mois, 'Tresorerie_Libre'] = tresorerie_apres_fonds
                    monthly_results_df.loc[date_mois, 'Tresorerie_Disponible'] = tresorerie_disponible
                    
                    # Gestion du remplacement onduleur
                    mois_remplacement = duree_construction_cfg + duree_vie_onduleur * 12
                    if idx == mois_remplacement and capital_cumule > 0:
                        # Récupérer le coût réel de l'onduleur
                        cout_reel_onduleur = 0.0
                        if sites_config:
                            for site_id, site_cfg in sites_config.items():
                                if isinstance(site_cfg, dict) and site_cfg.get('site_type') != 'Consommateur Pur':
                                    cost_unindexed = float(site_cfg.get("opex_onduleur_total_cost_site", 0.0))
                                    if cost_unindexed > 0:
                                        cout_reel_onduleur += cost_unindexed
                                        break
                        else:
                            # Configuration globale
                            if global_config.get("opex_onduleur_provision_globale", False):
                                cout_reel_onduleur = float(global_config.get("opex_onduleur_total_cost_global", 0.0))
                        
                        # Indexer le coût au moment du remplacement
                        years_elapsed = (idx - duree_construction_cfg) / 12.0
                        inflation_factor_remplacement = (1 + float(global_config.get("inflation_rate", 2.0)) / 100) ** years_elapsed
                        cout_onduleur_indexe = cout_reel_onduleur * inflation_factor_remplacement
                        
                        # Déblocage du fonds pour remplacement
                        montant_total_fonds = capital_cumule + interets_cumules
                        
                        # IMPORTANT: Séparer la libération du fonds et le paiement de l'onduleur
                        monthly_results_df.loc[date_mois, 'Fonds_Reserve_Onduleur_Liberation'] = montant_total_fonds
                        monthly_results_df.loc[date_mois, 'Remplacement_Onduleur_Paye'] = -cout_onduleur_indexe  # Coût réel indexé
                        
                        # Les intérêts deviennent imposables lors de la libération
                        if interets_cumules > 0:
                            monthly_results_df.loc[date_mois, 'Fonds_Reserve_Onduleur_Interets_Imposables'] = interets_cumules
                            monthly_results_df.loc[date_mois, 'Interets_Debloques_Imposables'] = interets_cumules
                        
                        # Calculer le déficit ou surplus
                        deficit_onduleur = cout_onduleur_indexe - montant_total_fonds
                        
                        logger.info(f"REMPLACEMENT ONDULEUR - Mois {idx + 1}:")
                        logger.info(f"  - Fonds libéré: {montant_total_fonds:,.0f}€ (capital: {capital_cumule:,.0f}€ + intérêts: {interets_cumules:,.0f}€)")
                        logger.info(f"  - Coût onduleur: {cout_onduleur_indexe:,.0f}€ (base: {cout_reel_onduleur:,.0f}€ × inflation: {inflation_factor_remplacement:.3f})")
                        
                        # Alertes selon le déficit/surplus
                        if deficit_onduleur > 0:
                            logger.warning(f"  ⚠️ DÉFICIT: {deficit_onduleur:,.0f}€ à financer sur la trésorerie")
                            if not placement_actif:
                                logger.warning(f"  💡 Conseil: Activer les placements aurait généré ~{cout_reel_onduleur * 0.132:,.0f}€ d'intérêts")
                                logger.warning(f"     réduisant le déficit à ~{deficit_onduleur - cout_reel_onduleur * 0.132:,.0f}€")
                            else:
                                logger.info(f"  ✓ Les intérêts ({interets_cumules:,.0f}€) ont réduit le déficit")
                        else:
                            logger.info(f"  ✅ SURPLUS: {-deficit_onduleur:,.0f}€ grâce aux provisions et intérêts")
                            if placement_actif:
                                logger.info(f"  ✓ Les placements ont permis de dégager un bénéfice")
                        
                        # Enregistrer le déficit/surplus dans une colonne dédiée
                        if 'Deficit_Financement_Onduleur' not in monthly_results_df.columns:
                            monthly_results_df['Deficit_Financement_Onduleur'] = 0.0
                        monthly_results_df.loc[date_mois, 'Deficit_Financement_Onduleur'] = deficit_onduleur
                        
                        # Marquer que le remplacement a eu lieu
                        monthly_results_df.loc[date_mois, 'Remplacement_Onduleur_Effectue'] = 1.0
                        
                        # Réinitialiser pour le cycle suivant
                        capital_cumule = 0.0
                        interets_cumules = 0.0
                        
                        # Mise à jour post-remplacement
                        monthly_results_df.loc[date_mois, 'Fonds_Reserve_Onduleur_Capital'] = capital_cumule
                        monthly_results_df.loc[date_mois, 'Fonds_Reserve_Onduleur_Interets'] = interets_cumules
                        monthly_results_df.loc[date_mois, 'Fonds_Reserve_Onduleur_Total'] = 0.0
                        monthly_results_df.loc[date_mois, 'Tresorerie_Libre'] = tresorerie_totale
                
                logger.info("FONDS DE RÉSERVE ONDULEUR - Implémentation terminée", {
                    "colonnes_créées": ["Fonds_Reserve_Onduleur_Capital", "Fonds_Reserve_Onduleur_Total", "Tresorerie_Libre"],
                    "principe": "Ségrégation comptable professionnelle",
                    "avantage": "Provisions toujours visibles, rémunération conditionnelle"
                })

            # --- GESTION DES PLACEMENTS DE TRÉSORERIE ---
            placement_actif = global_config.get("placement_tresorerie_active", False)

            # Détecter le mode optimisation depuis sites_config ET global_config
            is_optimization = False
            if sites_config and isinstance(sites_config, dict):
                is_optimization = sites_config.get("is_optimization_mode", False)
            if not is_optimization:
                is_optimization = global_config.get("is_optimization_mode", False)

            log_tva_placement("VÉRIFICATION ACTIVATION PLACEMENT", {
                "placement_tresorerie_active": placement_actif,
                "is_optimization_mode": is_optimization,
                "config_keys": list(global_config.keys())[:10] + ["..."]  # Limiter pour la lisibilité
            })

            # Log amélioré pour debug
            log_tva_placement("ÉTAT PLACEMENT TRÉSORERIE", {
                "placement_tresorerie_active": placement_actif,
                "placement_tva_capex": global_config.get("placement_tva_capex", None),
                "placement_tva_exploitation": global_config.get("placement_tva_exploitation", None),
                "action": "Appel placement" if placement_actif else "Placement ignoré"
            })

            if placement_actif:
                # Nettoyer le log au début de chaque nouvelle analyse
                clear_tva_log()
                
                # Créer une copie de global_config avec le flag d'optimisation
                config_for_placement = global_config.copy()
                config_for_placement["is_optimization_mode"] = is_optimization
                
                # Appliquer la logique de placement
                self.treasury_manager._apply_placement_logic(
                    monthly_results_df, 
                    config_for_placement, 
                    num_total_simulation_months,
                    duree_construction_cfg,
                    sites_config
                )
            else:
                log_tva_placement("PLACEMENT TVA DÉSACTIVÉ - Pas d'exécution", {
                    "raison": "placement_tresorerie_active = False"
                })
                
                # S'assurer que les colonnes existent mais sont vides
                # pour éviter des erreurs dans l'affichage
                colonnes_a_zero = [
                    'Total_Placements', 'Tresorerie_Non_Placee',
                    'Interets_Placements_Mensuels', 'Interets_TVA_Courus_Non_Encaisses'
                ]
                for col in colonnes_a_zero:
                    if col not in monthly_results_df.columns:
                        monthly_results_df[col] = 0.0
            
            # AJOUT CRITIQUE : Créer une colonne consolidant TOUS les intérêts mensuels
            # Cette colonne sera utilisée par le calcul FCFE pour intégrer les produits financiers
            if 'Interets_Totaux_Mensuels' not in monthly_results_df.columns:
                monthly_results_df['Interets_Totaux_Mensuels'] = 0.0
            
            # Consolider tous les intérêts : fonds de réserve + placements
            if 'Fonds_Reserve_Onduleur_Interets' in monthly_results_df.columns:
                monthly_results_df['Interets_Totaux_Mensuels'] += monthly_results_df['Fonds_Reserve_Onduleur_Interets'].fillna(0)
            
            # CORRECTION: Éviter la double comptabilisation des intérêts de placement
            # Vérifier si les colonnes individuelles existent
            has_individual_interest_columns = (
                'Interets_Placements_TVA_Mensuels' in monthly_results_df.columns or 
                'Interets_Placements_Excedents_Mensuels' in monthly_results_df.columns
            )
            
            if has_individual_interest_columns:
                # Utiliser UNIQUEMENT les colonnes individuelles (évite double comptage)
                if 'Interets_Placements_TVA_Mensuels' in monthly_results_df.columns:
                    monthly_results_df['Interets_Totaux_Mensuels'] += monthly_results_df['Interets_Placements_TVA_Mensuels'].fillna(0)
                
                if 'Interets_Placements_Excedents_Mensuels' in monthly_results_df.columns:
                    monthly_results_df['Interets_Totaux_Mensuels'] += monthly_results_df['Interets_Placements_Excedents_Mensuels'].fillna(0)
                
                logger.info("Utilisation des colonnes d'intérêts individuelles (TVA, Excédents)")
            else:
                # Fallback : utiliser la colonne consolidée pour compatibilité
                if 'Interets_Placements_Mensuels' in monthly_results_df.columns:
                    monthly_results_df['Interets_Totaux_Mensuels'] += monthly_results_df['Interets_Placements_Mensuels'].fillna(0)
                    logger.info("Utilisation de la colonne d'intérêts consolidée (compatibilité)")
            
            # Log pour vérifier l'impact
            total_interets_generes = monthly_results_df['Interets_Totaux_Mensuels'].sum()
            if total_interets_generes > 0:
                logger.info(f"INTÉRÊTS TOTAUX GÉNÉRÉS: {total_interets_generes:,.0f}€ sur la période")
                logger.info(f"Impact attendu sur LCOE: -{total_interets_generes / monthly_results_df['Production_kWh'].sum() * 100:.3f} c€/kWh")
            
            # CALCUL PROFESSIONNEL DES FCFE avec isolation des flux exceptionnels
            # IMPORTANT: Calculé APRÈS la consolidation des intérêts pour inclure tous les produits financiers
            fcfe_professional = self.equity_calc.calculate_fcfe_professional(monthly_results_df, subvention_totale_projet)
            monthly_results_df['FCFE'] = fcfe_professional
            
            # MISE À JOUR CRITIQUE : Recalculer la trésorerie après les placements et intérêts
            # Les intérêts sont dans FCFE mais les mouvements de placements doivent aussi être pris en compte
            
            # Calculer les flux nets incluant les mouvements de placement
            for idx in monthly_results_df.index:
                month_idx = list(monthly_results_df.index).index(idx)
                
                # Flux de base : FCFE + injections d'equity
                fcfe_base = monthly_results_df.loc[idx, 'FCFE']
                equity_injection = equity_injected_monthly_series.iloc[month_idx] if month_idx < len(equity_injected_monthly_series) else 0
                
                # Ajustements pour les mouvements de placement (qui ne sont pas dans FCFE)
                placement_tva = monthly_results_df.loc[idx, 'Placement_Exces_TVA'] if 'Placement_Exces_TVA' in monthly_results_df.columns else 0
                placement_excedent = monthly_results_df.loc[idx, 'Placement_Excedent_Tresorerie'] if 'Placement_Excedent_Tresorerie' in monthly_results_df.columns else 0
                
                # Flux net de trésorerie = FCFE + equity - nouveaux placements (car ils réduisent la trésorerie)
                flux_net_tresorerie = fcfe_base + equity_injection - placement_tva - placement_excedent
                
                # Calculer le solde cumulé
                if month_idx == 0:
                    monthly_results_df.loc[idx, 'Solde_Tresorerie_Fin_Mois'] = initial_cash_balance_at_true_t0 + flux_net_tresorerie
                else:
                    prev_idx = monthly_results_df.index[month_idx - 1]
                    prev_solde = monthly_results_df.loc[prev_idx, 'Solde_Tresorerie_Fin_Mois']
                    monthly_results_df.loc[idx, 'Solde_Tresorerie_Fin_Mois'] = prev_solde + flux_net_tresorerie
            
            # Log pour tracer l'évolution de la trésorerie
            logger.info(f"MISE À JOUR TRÉSORERIE - Impact des placements:")
            logger.info(f"  Trésorerie initiale: {initial_cash_balance_at_true_t0:,.0f}€")
            logger.info(f"  Trésorerie mois 6: {monthly_results_df['Solde_Tresorerie_Fin_Mois'].iloc[5]:,.0f}€" if len(monthly_results_df) > 5 else "  Pas de mois 6")
            logger.info(f"  Trésorerie mois 12: {monthly_results_df['Solde_Tresorerie_Fin_Mois'].iloc[11]:,.0f}€" if len(monthly_results_df) > 11 else "  Pas de mois 12")
            
            # VALIDATION PROFESSIONNELLE DE LA TRÉSORERIE
            validation_result = validate_treasury_data(monthly_results_df)
            
            if not validation_result['is_valid']:
                logger.error("❌ ERREURS DE VALIDATION TRÉSORERIE:")
                for error in validation_result['errors']:
                    logger.error(f"  - {error}")
            
            if validation_result['warnings']:
                logger.warning("⚠️ AVERTISSEMENTS TRÉSORERIE:")
                for warning in validation_result['warnings']:
                    logger.warning(f"  - {warning}")
            
            if validation_result['summary']:
                summary = validation_result['summary']
                logger.info("📊 RÉSUMÉ TRÉSORERIE:")
                if 'treasury' in summary:
                    t = summary['treasury']
                    logger.info(f"  Trésorerie: {t['initial']:,.0f}€ → {t['final']:,.0f}€ (variation: {t['variation']:,.0f}€)")
                if 'placements' in summary:
                    p = summary['placements']
                    logger.info(f"  Placements finaux: {p['final']:,.0f}€")
                if 'interests' in summary:
                    i = summary['interests']
                    logger.info(f"  Intérêts totaux: {i['total']:,.2f}€ sur {i['months_with_interests']} mois")
            
            # VÉRIFICATION : les flux des premiers mois ne doivent pas inclure le CAPEX
            fcfe_construction = monthly_results_df['FCFE'].iloc[:duree_construction_cfg]
            logger.info(f"FCFE pendant construction : {fcfe_construction.values}")
            logger.info(f"Somme FCFE construction : {fcfe_construction.sum():.2f} (ne doit PAS être -65000)")
            
            # Vérification supplémentaire
            if fcfe_construction.sum() < -50000:
                pass

            # --- 6. CALCUL DES INDICATEURS FINANCIERS FINAUX (VAN, TRI, etc.) ---
            re_annual = float(cout_fonds_propres_pct_config) # En pourcentage
            
            
            wacc_annual_at_pct = calculate_wacc(
                debt_ratio=debt_ratio_config,
                taux_interet_dette_pct=taux_interet_dette_pct_config,
                taux_imposition_pct=taux_imposition_standard_pct,
                cout_fonds_propres_pct=re_annual, # Doit être en % pour la fonction
                wacc_type="after_tax"
            )
            
            if wacc_annual_at_pct is None: 
                logger.warning("WACC calculation returned None, using fallback 6.0%")
                wacc_annual_at_pct = 6.0 # Fallback en %
            
            re_monthly_rate = (1 + re_annual / 100.0)**(1/12) - 1
            wacc_monthly_at_rate = (1 + wacc_annual_at_pct / 100.0)**(1/12) - 1
            
            # OCF Projet - Maintenant calculé APRÈS la consolidation des intérêts
            # Les intérêts de placement sont des flux opérationnels qui améliorent l'OCF
            s_interets_totaux = monthly_results_df['Interets_Totaux_Mensuels'].fillna(0)
            monthly_results_df['OCF_Projet'] = (s_nopat + s_amort - s_capex_brut_decaisse - s_delta_bfr - s_vat_payment + s_interets_totaux)

            # Flux pour les actionnaires (equity): FCFE - injection d'equity (qui est négative au début)
            # equity_injected_monthly_series est l'apport des actionnaires (positif pour l'entreprise, négatif pour l'investisseur s'il sort de sa poche)
            # FCFE est le flux APRES investissement et financement de la dette, disponible pour les actionnaires.
            # Le flux pour le calcul du TRI Equity doit être : [-Injection Equity T0, FCFE T1, FCFE T2, ...]
            # Le FCFE inclut déjà l'impact de l'investissement initial (- s_capex_brut_decaisse + s_net_debt_issued)
            
            equity_cash_flows_for_irr_npv = monthly_results_df['FCFE'].fillna(0).values
            
            # Les FCFE représentent les flux disponibles après service de la dette
            # Il faut l'ajouter comme premier élément négatif
            if abs(net_equity_investment_total) > 1e-6:  # Si investissement non négligeable
                # Respecter le signe économique : si net_equity < 0, l'investisseur reçoit du cash
                # Ne pas utiliser abs() qui forcerait toujours une sortie de cash
                initial_investment = -net_equity_investment_total  # Signe opposé : négatif si investissement, positif si réception
                equity_cash_flows_for_irr_npv = np.concatenate([[initial_investment], equity_cash_flows_for_irr_npv])
            
            if debug_mode:
                cf_equity_24m = list(equity_cash_flows_for_irr_npv[:24])
                debug_log['calculs_equity']['cashflows_24_months'] = cf_equity_24m
                debug_log['calculs_equity']['cashflow_initial'] = equity_cash_flows_for_irr_npv[0]
                debug_log['calculs_equity']['sum_positive_cashflows'] = sum([cf for cf in equity_cash_flows_for_irr_npv if cf > 0])
                debug_log['calculs_equity']['sum_negative_cashflows'] = sum([cf for cf in equity_cash_flows_for_irr_npv if cf < 0])
                debug_log['calculs_equity']['total_cashflows_count'] = len(equity_cash_flows_for_irr_npv)
            
            project_cash_flows_for_irr_npv = monthly_results_df['OCF_Projet'].fillna(0).values
            # Ajout de la valeur terminale au flux projet
            logger.info(f"Valeur résiduelle calculée - Base CAPEX Net: {capex_net_subvention_info:.2f}€, "
                        f"VR brute: {valeur_residuelle_brute:.2f}€, "
                        f"Coût démantèlement: {cout_demantelement:.2f}€, "
                        f"VR nette finale: {valeur_residuelle_nette_projet:.2f}€")
            
            if len(project_cash_flows_for_irr_npv) > 0:
                project_cash_flows_for_irr_npv[-1] += valeur_residuelle_nette_projet
            
            # NPV et IRR Equity avec vérifications explicites
            # Vérifier si financement 100% dette ou plus
            if debt_ratio_config >= 1.0:
                # Financement 100% dette - Aucun calcul de fonds propres applicable
                npv_equity = np.nan
                irr_equity = np.nan
                roi_equity = np.nan
                irr_calculation_method = 'N/A'
                irr_equity_warning = "Financement 100% dette - Indicateurs FP non applicables"
            else:
                # Utiliser le taux d'actualisation mensuel des fonds propres
                if pd.notna(re_monthly_rate):
                    npv_equity = self.equity_calc.calculate_npv_explicit(equity_cash_flows_for_irr_npv, re_monthly_rate)
                else:
                    npv_equity = np.nan
                
                # Seuil minimum pour un calcul de TRI stable (10% du CAPEX ou 5000€ minimum)
                MIN_EQUITY_FOR_IRR_CALC = max(capex_brut_total_scenario * 0.10, 5000)
                irr_equity_warning = None
                
                if is_equity_negligible:
                    irr_equity = np.nan; roi_equity = np.nan
                    irr_calculation_method = 'N/A'
                    irr_equity_warning = "Fonds propres négligeables"
                elif abs(net_equity_investment_total) < MIN_EQUITY_FOR_IRR_CALC:
                    # Si l'investissement net est trop faible, ne pas calculer le TRI
                    irr_equity = np.nan
                    irr_calculation_method = 'N/A'
                    irr_equity_warning = "TRI non calculable : investissement net FP trop faible"
                    roi_equity = npv_equity / abs(net_equity_investment_total) if pd.notna(npv_equity) and abs(net_equity_investment_total) > 1e-9 else np.nan
                else:
                    # CALCUL TRI AVEC VÉRIFICATION EXPLICITE
                    irr_monthly_raw, irr_status = self.equity_calc.calculate_irr_with_verification(equity_cash_flows_for_irr_npv)
                    
                    if irr_status == "OK" and pd.notna(irr_monthly_raw):
                        # Conversion mensuel -> annuel
                        irr_equity = (1 + irr_monthly_raw)**12 - 1
                        irr_calculation_method = 'IRR'
                        irr_equity_warning = None
                    else:
                        # Échec du calcul TRI standard
                        irr_equity = np.nan
                        irr_calculation_method = 'ERROR'
                        irr_equity_warning = irr_status
                    
                    # npv_equity est maintenant le NPV net pour l'actionnaire
                    roi_equity = npv_equity / abs(net_equity_investment_total) if pd.notna(npv_equity) and abs(net_equity_investment_total) > 1e-9 else np.nan
            
            # === CALCUL DES DEUX TRI (PUR vs OPTIMISÉ) ===
            # TRI Projet Pur (déjà calculé)
            irr_projet_pur = irr_equity
            
            # TRI Projet Optimisé (avec impact des placements)
            fcfe_avec_placements = pd.Series(equity_cash_flows_for_irr_npv[1:])  # Sans l'investissement initial
            if 'Interets_Courus_Non_Encaisses' in monthly_results_df.columns:
                # Ajouter la valeur finale des intérêts capitalisés au dernier flux
                interets_finaux = monthly_results_df['Interets_Courus_Non_Encaisses'].iloc[-1]
                if not fcfe_avec_placements.empty and pd.notna(interets_finaux) and interets_finaux > 0:
                    fcfe_avec_placements.iloc[-1] += interets_finaux
                    
            # Reconstituer le flux complet avec l'investissement initial
            if abs(net_equity_investment_total) > 1e-6:
                flux_complet_optimise = np.concatenate([[-net_equity_investment_total], fcfe_avec_placements.values])
            else:
                flux_complet_optimise = fcfe_avec_placements.values
                
            # Calculer le TRI optimisé
            if debt_ratio_config >= 1.0 or is_equity_negligible or abs(net_equity_investment_total) < MIN_EQUITY_FOR_IRR_CALC:
                irr_projet_optimise = np.nan
                gain_tri_placement = 0.0
            else:
                irr_monthly_opt, irr_status_opt = self.equity_calc.calculate_irr_with_verification(flux_complet_optimise)
                if irr_status_opt == "OK" and pd.notna(irr_monthly_opt):
                    irr_projet_optimise = (1 + irr_monthly_opt)**12 - 1
                else:
                    irr_projet_optimise = np.nan
                
                gain_tri_placement = irr_projet_optimise - irr_projet_pur if pd.notna(irr_projet_optimise) and pd.notna(irr_projet_pur) else 0.0
            
            logger.info(f"TRI Pur: {irr_projet_pur:.2%} vs TRI Optimisé: {irr_projet_optimise:.2%}, Gain: {gain_tri_placement:.2%}" if pd.notna(irr_projet_pur) else "TRI non calculable")
            
            if debug_mode:
                debug_log['calculs_equity']['irr_calculated'] = float(irr_equity) if pd.notna(irr_equity) else None
                debug_log['calculs_equity']['irr_method'] = irr_calculation_method
                debug_log['calculs_equity']['irr_status'] = irr_equity_warning
                debug_log['calculs_equity']['npv_calculated'] = float(npv_equity) if pd.notna(npv_equity) else None
                debug_log['calculs_equity']['discount_rate_used'] = float(re_monthly_rate) if pd.notna(re_monthly_rate) else None
                
                # IMPORTANT : Recalculer la VAN manuellement pour vérifier
                if pd.notna(re_monthly_rate) and len(equity_cash_flows_for_irr_npv) > 0:
                    manual_npv = equity_cash_flows_for_irr_npv[0]  # Investissement initial
                    for i, cf in enumerate(equity_cash_flows_for_irr_npv[1:], 1):
                        manual_npv += cf / (1 + re_monthly_rate)**i
                    debug_log['calculs_equity']['npv_manual_check'] = manual_npv
                
                    fcfe_construction_sum = monthly_results_df['FCFE'].iloc[:duree_construction_cfg].sum()
                debug_log['calculs_equity']['fcfe_construction_sum'] = float(fcfe_construction_sum)
                debug_log['calculs_equity']['double_capex_check'] = bool(fcfe_construction_sum < -50000)
                
            # La vérification de cohérence sera faite après le calcul du payback
            
            # NPV et IRR Projet avec protection NaN
            irr_proj_raw = npf.irr(project_cash_flows_for_irr_npv)
            irr_project = (1 + irr_proj_raw)**12 - 1 if pd.notna(irr_proj_raw) and np.isfinite(irr_proj_raw) else np.nan
            
            # CORRECTION: Pour éviter la double comptabilisation fiscale, les flux après impôt (NOPAT)
            # sont actualisés au coût des capitaux propres (sans effet fiscal de la dette)
            # Note: OCF_Projet contient déjà NOPAT (EBIT après impôt) donc on utilise re_monthly_rate
            npv_project_unlevered = npf.npv(re_monthly_rate, project_cash_flows_for_irr_npv) if pd.notna(re_monthly_rate) else np.nan
            
            # Pour compatibilité, on garde aussi le calcul avec WACC (mais avec avertissement)
            npv_project_wacc = npf.npv(wacc_monthly_at_rate, project_cash_flows_for_irr_npv) if pd.notna(wacc_monthly_at_rate) else np.nan
            
            # Utiliser la NPV projet sans double comptabilisation fiscale
            npv_project = npv_project_unlevered
            
            if abs(npv_project_wacc - npv_project_unlevered) > 1000:  # Différence significative
                logger.warning(f"Impact de la correction fiscale - NPV avec WACC: {npv_project_wacc:,.0f}€, NPV corrigée: {npv_project_unlevered:,.0f}€")
            
            # Vérification critique des résultats
            if pd.isna(npv_project) or pd.isna(irr_project):
                logger.warning(f"Calculs projet critiques: NPV={npv_project}, IRR={irr_project}")
                logger.warning(f"WACC monthly rate: {wacc_monthly_at_rate}")
                logger.warning(f"Cash flows length: {len(project_cash_flows_for_irr_npv)}")
                if len(project_cash_flows_for_irr_npv) > 0:
                    logger.warning(f"Cash flows range: [{min(project_cash_flows_for_irr_npv):.0f}, {max(project_cash_flows_for_irr_npv):.0f}]")
            
            # Payback Periods
            # equity_investment_cash_flow_for_payback est identique à equity_cash_flows_for_irr_npv
            if debt_ratio_config >= 1.0:
                # Financement 100% dette - Pas de payback fonds propres
                payback_equity_years = np.nan
            else:
                payback_equity_months = calculate_payback_months(equity_cash_flows_for_irr_npv)
                payback_equity_years = payback_equity_months / 12.0 if payback_equity_months is not None else np.nan
                if is_equity_negligible: payback_equity_years = np.nan
            
            payback_project_months = calculate_payback_months(project_cash_flows_for_irr_npv) # OCF_Projet inclut déjà -CAPEX
            payback_project_years = payback_project_months / 12.0 if payback_project_months is not None else np.nan
            
            # VÉRIFICATION DE COHÉRENCE MATHÉMATIQUE (maintenant que payback_equity_years est défini)
            coherence_errors = self.verify_equity_calculations_coherence(
                irr=irr_equity,
                npv=npv_equity,
                payback=payback_equity_years,
                investment=net_equity_investment_total,
                discount_rate=re_annual / 100.0 if pd.notna(re_annual) else np.nan
            )
            
            if debug_mode:
                debug_log['calculs_equity']['coherence_errors'] = coherence_errors
                debug_log['calculs_equity']['payback_equity_years'] = payback_equity_years
                
                # Sauvegarder le log
            
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
                "irr_equity_warning": irr_equity_warning,  # Avertissement pour TRI instable
                "irr_calculation_method": irr_calculation_method,  # Méthode utilisée (IRR, MIRR, etc.)
                "equity_calculation_details": self.equity_calc.equity_calculation_details,  # Détails du calcul FP
                "fcfe_calculation_details": self.equity_calc.fcfe_calculation_details,  # Détails FCFE
                "equity_coherence_errors": coherence_errors,  # Erreurs de cohérence mathématique
                "IRR_Projet_Pur": irr_projet_pur,
                "IRR_Projet_Optimise": irr_projet_optimise,
                "Gain_TRI_Placement": gain_tri_placement,
                "irr_project": irr_project, "npv_project": npv_project, "payback_project": payback_project_years,
                "avg_dscr": avg_dscr,
                
                "valeur_residuelle_brute": valeur_residuelle_brute,
                "cout_demantelement": cout_demantelement,
                "valeur_residuelle_nette": valeur_residuelle_nette_projet,
                "valeur_residuelle_details": {
                    "base_calcul": "CAPEX_NET",
                    "capex_net_utilise": capex_net_subvention_info,
                    "pourcentage_vr": valeur_residuelle_pct_config,
                    "pourcentage_demantelement": cout_demantelement_pct_config,
                    "valeur_residuelle_brute": valeur_residuelle_brute,
                    "cout_demantelement": cout_demantelement,
                    "valeur_residuelle_nette": valeur_residuelle_nette_projet
                },
                
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
            prix_max_recherche_default = 0.80  # Augmenté pour petits projets
            
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

                # ACTIVATION DU MODE OPTIMISATION POUR LE PLACEMENT TVA
                temp_config = sites_config.copy() if sites_config else {}
                temp_config["is_optimization_mode"] = True
                
                # S'assurer que le flag est aussi propagé dans self.config temporairement
                original_optimization_flag = self.config.get("is_optimization_mode", False)
                self.config["is_optimization_mode"] = True
                
                try:
                    results_sim_calc = self.calculate_financial_indicators(
                        scenario_name, prix_revente=price_candidate_val,
                        override_source_prix_autoconso=override_source_prix_autoconso,
                        sites_config=temp_config
                    )
                finally:
                    # Restaurer le flag original pour ne pas affecter les calculs suivants
                    self.config["is_optimization_mode"] = original_optimization_flag
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

                # Point de départ pour minimize (plus proche du maximum pour petits projets)
                initial_guess_for_minimize = np.clip(prix_min_recherche + 0.7 * (prix_max_recherche - prix_min_recherche), prix_min_recherche, prix_max_recherche)
                
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

            # --- DIAGNOSTIC AUTOMATIQUE ET SOLUTION DE SECOURS ---
            if optimal_price_found is None:
                logger.warning("DIAGNOSTIC AUTOMATIQUE: Optimisation échouée, analyse des causes...")
                
                # Test de diagnostic rapide
                test_prices = [0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 0.70]
                diagnostic_results = []
                
                for test_price in test_prices:
                    try:
                        simulation_cache.clear()
                        test_result = self.calculate_financial_indicators(
                            scenario_name, prix_revente=test_price,
                            override_source_prix_autoconso=override_source_prix_autoconso, 
                            sites_config=sites_config
                        )
                        
                        if test_result and isinstance(test_result, dict) and "error" not in test_result:
                            npv_test = test_result.get('npv_project', float('nan'))
                            irr_test = test_result.get('irr_project', float('nan'))
                            
                            if pd.notna(npv_test) and pd.notna(irr_test):
                                target_value = target_irr if target_irr is not None else target_npv
                                actual_value = irr_test if target_irr is not None else npv_test
                                ecart = abs(actual_value - target_value)
                                
                                diagnostic_results.append({
                                    'prix': test_price,
                                    'npv': npv_test,
                                    'irr': irr_test,
                                    'target': target_value,
                                    'actual': actual_value,
                                    'ecart': ecart,
                                    'valid': True
                                })
                            else:
                                diagnostic_results.append({
                                    'prix': test_price,
                                    'npv': npv_test,
                                    'irr': irr_test,
                                    'valid': False,
                                    'reason': 'NPV ou IRR = NaN'
                                })
                        else:
                            diagnostic_results.append({
                                'prix': test_price,
                                'valid': False,
                                'reason': 'calculate_financial_indicators a échoué'
                            })
                    except Exception as e:
                        diagnostic_results.append({
                            'prix': test_price,
                            'valid': False,
                            'reason': f'Exception: {str(e)[:100]}'
                        })
                
                # Analyser les résultats du diagnostic
                valid_results = [r for r in diagnostic_results if r.get('valid', False)]
                
                if valid_results:
                    # Trouver le prix le plus proche de la cible
                    best_result = min(valid_results, key=lambda x: x['ecart'])
                    optimal_price_found = best_result['prix']
                    
                    logger.warning(f"SOLUTION DE SECOURS: Prix trouvé par diagnostic automatique = {optimal_price_found:.4f}€/kWh")
                    logger.info(f"Détails: NPV={best_result['npv']:.0f}€, IRR={best_result['irr']:.2f}%, Écart cible={best_result['ecart']:.4f}")
                    
                    # Afficher un résumé des tests pour l'utilisateur
                    logger.info("RÉSUMÉ DIAGNOSTIC:")
                    for i, result in enumerate(valid_results[:3]):  # Top 3 résultats
                        logger.info(f"  Prix {result['prix']}€/kWh: NPV={result['npv']:.0f}€, IRR={result['irr']:.1f}%, Écart={result['ecart']:.3f}")
                    
                else:
                    # Diagnostic détaillé des échecs
                    logger.error("DIAGNOSTIC: Aucun prix de test ne fonctionne. Causes identifiées:")
                    for result in diagnostic_results:
                        if not result.get('valid', False):
                            logger.error(f"  Prix {result['prix']}€/kWh: {result.get('reason', 'Échec')}")
                    
                    # ANALYSE DE VIABILITÉ ÉCONOMIQUE
                    logger.error("ANALYSE DE VIABILITÉ ÉCONOMIQUE:")
                    logger.error("Ce projet semble économiquement non viable avec les paramètres actuels.")
                    
                    # Vérifier les paramètres critiques
                    capex_scenario = self.scenarios.get(scenario_name, {}).get('capex_multiplier', 1.0)
                    logger.error(f"  - CAPEX multiplicateur: {capex_scenario}")
                    
                    # Calculer le LCOE minimum théorique
                    try:
                        test_calc = self.calculate_financial_indicators(
                            scenario_name, prix_revente=0.20,
                            override_source_prix_autoconso=override_source_prix_autoconso, 
                            sites_config=sites_config
                        )
                        
                        if test_calc and 'monthly_data' in test_calc:
                            monthly_df = test_calc['monthly_data']
                            if 'CAPEX_Initial_Mensuel' in monthly_df.columns and 'Production_kWh' in monthly_df.columns:
                                total_capex = monthly_df['CAPEX_Initial_Mensuel'].sum()
                                total_production_annual = monthly_df['Production_kWh'].sum()
                                
                                if total_production_annual > 0:
                                    lcoe_minimum = total_capex / (total_production_annual * 20)
                                    logger.error(f"  - LCOE minimum théorique: {lcoe_minimum:.4f}€/kWh")
                                    logger.error(f"  - Production annuelle: {total_production_annual:.0f} kWh")
                                    logger.error(f"  - CAPEX total: {total_capex:.0f}€")
                                    
                                    if lcoe_minimum > prix_max_recherche:
                                        logger.error(f"  → PROBLÈME: LCOE minimum ({lcoe_minimum:.4f}) > prix max recherche ({prix_max_recherche})")
                                        logger.error("  → RECOMMANDATION: Augmentez le prix max de revente ou réduisez le CAPEX")
                                    
                    except Exception as viability_error:
                        logger.error(f"Impossible d'analyser la viabilité: {viability_error}")
                    
                    # Ne pas fournir de solution par défaut - forcer l'utilisateur à corriger
                    raise RuntimeError(
                        f"Aucun prix optimal déterminé après toutes les tentatives (brentq et minimize). "
                        f"Vérifiez les logs et les bornes de recherche. "
                        f"Le projet semble économiquement non viable avec les paramètres actuels."
                    )
            
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


        """
        Applique la logique complète de placement de trésorerie sur les excédents.
        
        CRITICAL: Cette méthode NE DOIT PAS modifier les revenus en mode optimisation LCOE
        pour éviter de perturber l'algorithme de recherche du prix optimal.
        
        Args:
            monthly_results_df: DataFrame avec tous les résultats mensuels
            global_config: Configuration globale avec les paramètres de placement
            num_total_simulation_months: Nombre total de mois de simulation
            duree_construction_cfg: Durée de la phase de construction en mois
            
        Modifie:
            monthly_results_df avec les nouvelles colonnes de placement
        """
        
        # 1. INITIALISATION ET VALIDATION
        # Vérifier que les paramètres requis sont présents
        required_params = [
            "placement_tresorerie_active",
            "pourcentage_tva_a_placer", 
            "taux_placement_exces_tva",
            "taux_placement_provision_onduleur"
        ]
        
        for param in required_params:
            if param not in global_config:
                log_tva_placement(f"ERREUR: Paramètre '{param}' manquant dans global_config")
                return
        
        # 2. DÉTECTION DU MODE OPTIMISATION (CRITIQUE!)
        is_optimization_mode = self._detect_optimization_mode(global_config)
        
        if is_optimization_mode:
            log_tva_placement("MODE OPTIMISATION DÉTECTÉ", {
                "action": "Les intérêts seront calculés mais NE modifieront PAS les revenus",
                "raison": "Éviter de perturber l'algorithme de recherche du prix optimal LCOE"
            })
        
        # 3. CRÉATION DES COLONNES NÉCESSAIRES
        colonnes_placement = [
            'Placement_Exces_TVA',                      # Nouveau placement TVA ce mois
            'Placement_Provision_Onduleur',             # Nouveau placement provision ce mois  
            'Placement_Autres_Excedents',               # Autres placements (réservé pour évolutions)
            'Solde_Placement_TVA_Cumul',               # Solde cumulé TVA (capital + intérêts)
            'Solde_Placement_Provision_Onduleur_Cumul', # Solde cumulé provision (capital + intérêts)
            'Solde_Placement_Autres_Cumul',            # Solde autres (réservé)
            'Interets_Placements_Mensuels',            # Total des intérêts générés ce mois
            'Interets_Courus_Non_Encaisses',           # Cumul des intérêts capitalisés (non encaissés)
            'Total_Placements',                         # Somme de tous les soldes de placement
            'Tresorerie_Non_Placee'                    # Trésorerie libre disponible
        ]
        
        for col in colonnes_placement:
            if col not in monthly_results_df.columns:
                monthly_results_df[col] = 0.0
        
        # 4. RÉCUPÉRATION DES PARAMÈTRES
        pct_tva_a_placer = float(global_config.get("pourcentage_tva_a_placer", 80.0))
        taux_placement_tva_annuel = float(global_config.get("taux_placement_exces_tva", 1.5))
        taux_placement_provision_annuel = float(global_config.get("taux_placement_provision_onduleur", 2.5))
        seuil_remboursement_tva = float(global_config.get("seuil_remboursement_tva", 500.0))
        
        # Conversion en taux mensuels (intérêts composés)
        taux_tva_mensuel = (1 + taux_placement_tva_annuel/100) ** (1/12) - 1
        taux_provision_mensuel = (1 + taux_placement_provision_annuel/100) ** (1/12) - 1
        
        log_tva_placement("PARAMÈTRES DE PLACEMENT", {
            "pourcentage_tva_a_placer": f"{pct_tva_a_placer}%",
            "taux_placement_tva_annuel": f"{taux_placement_tva_annuel}%",
            "taux_placement_provision_annuel": f"{taux_placement_provision_annuel}%",
            "taux_tva_mensuel": f"{taux_tva_mensuel*100:.4f}%",
            "taux_provision_mensuel": f"{taux_provision_mensuel*100:.4f}%",
            "mode_optimisation": is_optimization_mode
        })
        
        # 5. VARIABLES DE SUIVI
        solde_placement_tva = 0.0
        solde_placement_provision = 0.0
        solde_placement_autres = 0.0
        
        # 6. BOUCLE PRINCIPALE SUR CHAQUE MOIS
        for month_idx, date_mois in enumerate(monthly_results_df.index):
            
            # Phase de construction : pas de placement
            if month_idx < duree_construction_cfg:
                continue
                
            # --- A. DÉTECTION DES REMBOURSEMENTS TVA ---
            vat_refund, methode_detection = self._detect_vat_refund(monthly_results_df, date_mois, month_idx)
            
            if vat_refund > 0:
                log_tva_placement(f"MOIS {month_idx + 1} - REMBOURSEMENT TVA DÉTECTÉ", {
                    "montant_remboursement": f"{vat_refund:,.2f}€",
                    "methode_detection": methode_detection,
                    "date": date_mois.strftime('%Y-%m-%d')
                })
            
            # --- B. PLACEMENT DES EXCÉDENTS TVA ---
            montant_a_placer_tva = 0.0
            if vat_refund >= seuil_remboursement_tva:
                montant_a_placer_tva = vat_refund * (pct_tva_a_placer / 100.0)
                monthly_results_df.loc[date_mois, 'Placement_Exces_TVA'] = montant_a_placer_tva
                
                log_tva_placement(f"MOIS {month_idx + 1} - PLACEMENT TVA", {
                    "remboursement_tva": f"{vat_refund:,.2f}€",
                    "pourcentage_place": f"{pct_tva_a_placer}%",
                    "montant_place": f"{montant_a_placer_tva:,.2f}€"
                })
            
            # --- C. PLACEMENT PROVISION ONDULEUR ---
            # Récupérer le montant de provision onduleur du mois
            provision_onduleur_mois = monthly_results_df.loc[date_mois, 'OPEX_Provision_Onduleur_Mensuel'] if 'OPEX_Provision_Onduleur_Mensuel' in monthly_results_df.columns else 0.0
            
            if provision_onduleur_mois > 0:
                monthly_results_df.loc[date_mois, 'Placement_Provision_Onduleur'] = provision_onduleur_mois
                
                log_tva_placement(f"MOIS {month_idx + 1} - PLACEMENT PROVISION ONDULEUR", {
                    "montant_provision": f"{provision_onduleur_mois:,.2f}€"
                })
            
            # --- D. CALCUL DES INTÉRÊTS SUR SOLDES EXISTANTS ---
            interets_tva = 0.0
            interets_provision = 0.0
            interets_autres = 0.0
            
            if solde_placement_tva > 0:
                interets_tva = solde_placement_tva * taux_tva_mensuel
                
            if solde_placement_provision > 0:
                interets_provision = solde_placement_provision * taux_provision_mensuel
                
            interets_totaux = interets_tva + interets_provision + interets_autres
            monthly_results_df.loc[date_mois, 'Interets_Placements_Mensuels'] = interets_totaux
            
            if interets_totaux > 0:
                log_tva_placement(f"MOIS {month_idx + 1} - INTÉRÊTS CALCULÉS", {
                    "interets_tva": f"{interets_tva:,.2f}€",
                    "interets_provision": f"{interets_provision:,.2f}€",
                    "interets_totaux": f"{interets_totaux:,.2f}€",
                    "solde_tva_avant": f"{solde_placement_tva:,.2f}€",
                    "solde_provision_avant": f"{solde_placement_provision:,.2f}€"
                })
            
            # --- E. MISE À JOUR DES SOLDES (capital + intérêts + nouveaux placements) ---
            solde_placement_tva = solde_placement_tva + interets_tva + montant_a_placer_tva
            solde_placement_provision = solde_placement_provision + interets_provision + provision_onduleur_mois
            
            # Enregistrer les soldes cumulés
            monthly_results_df.loc[date_mois, 'Solde_Placement_TVA_Cumul'] = solde_placement_tva
            monthly_results_df.loc[date_mois, 'Solde_Placement_Provision_Onduleur_Cumul'] = solde_placement_provision
            monthly_results_df.loc[date_mois, 'Solde_Placement_Autres_Cumul'] = solde_placement_autres
            
            # Total des placements
            total_placements = solde_placement_tva + solde_placement_provision + solde_placement_autres
            monthly_results_df.loc[date_mois, 'Total_Placements'] = total_placements
            
            # Trésorerie non placée = Solde trésorerie fin (déjà calculé dans core_analyzer)
            monthly_results_df.loc[date_mois, 'Tresorerie_Non_Placee'] = monthly_results_df.loc[date_mois, 'Solde_Tresorerie_Fin_Mois']
            
            # --- F. CAPITALISATION PURE DES INTÉRÊTS (PAS D'AJOUT AUX REVENUS) ---
            # NOUVELLE APPROCHE : Les intérêts sont capitalisés mais ne deviennent pas des revenus mensuels
            # Ceci est plus réaliste fiscalement et comptablement
            
            if interets_totaux > 0:
                # Calculer le cumul des intérêts courus non encaissés
                interets_courus_cumul_precedent = 0.0
                if month_idx > 0:
                    prev_date = monthly_results_df.index[month_idx - 1]
                    interets_courus_cumul_precedent = monthly_results_df.loc[prev_date, 'Interets_Courus_Non_Encaisses']
                
                # Ajouter les nouveaux intérêts au cumul des intérêts courus
                nouveau_cumul_interets = interets_courus_cumul_precedent + interets_totaux
                monthly_results_df.loc[date_mois, 'Interets_Courus_Non_Encaisses'] = nouveau_cumul_interets
                
                log_tva_placement(f"MOIS {month_idx + 1} - INTÉRÊTS CAPITALISÉS (NON ENCAISSÉS)", {
                    "interets_du_mois": f"{interets_totaux:,.2f}€",
                    "cumul_interets_courus": f"{nouveau_cumul_interets:,.2f}€",
                    "approche": "Capitalisation pure - intérêts non comptés comme revenus mensuels",
                    "avantage": "Plus réaliste fiscalement et comptablement"
                })
            else:
                # Pas d'intérêts ce mois, mais on maintient le cumul précédent
                if month_idx > 0:
                    prev_date = monthly_results_df.index[month_idx - 1]
                    cumul_precedent = monthly_results_df.loc[prev_date, 'Interets_Courus_Non_Encaisses']
                    monthly_results_df.loc[date_mois, 'Interets_Courus_Non_Encaisses'] = cumul_precedent
        
        # 7. RÉSUMÉ FINAL
        total_interets = monthly_results_df['Interets_Placements_Mensuels'].sum()
        total_interets_courus = monthly_results_df['Interets_Courus_Non_Encaisses'].iloc[-1] if not monthly_results_df.empty else 0.0
        solde_final_tva = solde_placement_tva
        solde_final_provision = solde_placement_provision
        
        log_tva_placement("RÉSUMÉ FINAL DES PLACEMENTS - CAPITALISATION PURE", {
            "total_interets_calcules": f"{total_interets:,.2f}€",
            "total_interets_courus_non_encaisses": f"{total_interets_courus:,.2f}€",
            "solde_final_placement_tva": f"{solde_final_tva:,.2f}€",
            "solde_final_placement_provision": f"{solde_final_provision:,.2f}€",
            "approche": "Capitalisation pure - intérêts non ajoutés aux revenus",
            "avantage": "Plus réaliste fiscalement et comptablement",
            "mode_execution": "Optimisation LCOE" if is_optimization_mode else "Analyse normale"
        })
        
        # 8. VÉRIFICATION DE COHÉRENCE
        self._verify_placement_coherence(monthly_results_df)