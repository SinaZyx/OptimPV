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
    calculate_lcoe_engineering, # MODIFICATION: On va utiliser cette fonction importée
    calculate_avg_dscr_revised  # MODIFICATION: On va utiliser cette fonction importée
)
from .data_processing import validate_and_prepare_sites_data, aggregate_energy_data
from . import tax_engine

# Importation de TURPE_PROD_RATES depuis config.py (un niveau au-dessus)
try:
    from ..config import TURPE_PROD_RATES
except ImportError:
    logging.getLogger(__name__).error("Impossible d'importer TURPE_PROD_RATES depuis ..config. TURPE sera nul.")
    # Définition locale pour les tests (afin que le test fonctionne même si l'import échoue)
    TURPE_PROD_RATES = {
        "BT<=36kVA": {
            "CG": {"Unique": 21.60, "CARD": 22.80}, 
            "CC": {"Linky": 22.44}
        },
        "BT>36kVA": {
            "CG": {"Unique": 285.96, "CARD": 318.00},
            "CC": {"Mensuelle": 288.84}
        },
        "HTA": {
            "CG": {"Unique": 725.16, "CARD": 725.16},
            "CC": {"Mensuelle": 383.76}
        }
    }


logger = logging.getLogger(__name__)
if not logger.handlers:
    # On s'assure que le logger spécifique au module a un niveau
    # (basicConfig configure le root logger, mais pas forcément les loggers enfants directement)
    logger.setLevel(logging.INFO)

    if not logging.getLogger().handlers: # Si le root logger n'a AUCUN handler
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        # Après basicConfig, le root logger a maintenant au moins un handler (console).
        # Ajoutons notre FileHandler au root logger pour capturer tous les logs.
        root_logger = logging.getLogger() # Récupère le root logger

        # Configuration du FileHandler
        log_file_path = "optim_pv_enginev2.log"
        file_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8') # 'w' pour réécrire à chaque démarrage
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO) # S'assurer que le handler a le bon niveau

        # Vérifier pour éviter d'ajouter plusieurs fois le même handler si ce bloc est ré-exécuté
        # (peu probable avec la garde `if not logging.getLogger().handlers` mais plus robuste)
        already_has_this_file_handler = any(
            isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', '').endswith(log_file_path)
            for h in root_logger.handlers
        )
        if not already_has_this_file_handler:
            root_logger.addHandler(file_handler)
            # Optionnel: logger un message indiquant que le fichier de log est configuré
            # Ce message ira aussi dans le fichier de log lui-même.
            root_logger.info(f"Logging configuré pour écrire également dans le fichier : {log_file_path}")
    else:
        # Si le root logger AVAIT déjà des handlers (par ex. configurés par Streamlit ou ailleurs),
        # basicConfig n'a pas été appelé. Ajoutons quand même notre FileHandler au root logger
        # pour s'assurer que nos logs y vont.
        root_logger = logging.getLogger()
        log_file_path = "optim_pv_enginev2.log"
        
        # Assurons-nous que le root_logger a un niveau s'il n'en avait pas
        if root_logger.level == logging.NOTSET: # NOTSET est 0, le niveau par défaut
            root_logger.setLevel(logging.INFO)

        file_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        already_has_this_file_handler = any(
            isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', '').endswith(log_file_path)
            for h in root_logger.handlers
        )
        if not already_has_this_file_handler:
            root_logger.addHandler(file_handler)
            root_logger.info(f"Logging (déjà configuré par ailleurs) complété pour écrire aussi dans : {log_file_path}")

NPF_IS_REAL_CORE = False
try:
    import numpy_financial as npf_real_core
    NPF_IS_REAL_CORE = True
    logger.info("core_analyzer: numpy_financial (npf_real_core) chargé.")
except ImportError:
    logger.warning("core_analyzer: numpy_financial non trouvé. Fonctions secours via NpfModuleWrapper seront utilisées.")

npf = NpfModuleWrapper(use_real_npf=NPF_IS_REAL_CORE)


# Début de modules/engine_module/core_analyzer.py
# ... (imports et initialisation du logger, NpfModuleWrapper, etc. comme avant) ...

class AnalysisEngine:
    def __init__(self, config: dict, scenarios: dict, sites_data: dict[str, pd.DataFrame]):
        # ... (constructeur inchangé) ...
        if not isinstance(config, dict): raise TypeError("config doit être un dict")
        if not isinstance(scenarios, dict): raise TypeError("scenarios doit être un dict")
        if not isinstance(sites_data, dict): raise TypeError("sites_data doit être un dict")

        self.config = copy.deepcopy(config)
        self.scenarios = copy.deepcopy(scenarios)
        self.sites_data = validate_and_prepare_sites_data(sites_data)

        self.npf_available = NPF_IS_REAL_CORE
        self.used_aggregated_config = False
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

        # ... (initialisation des variables de résultats inchangée) ...
        autoconsumption_rate = np.nan; autoproduction_rate = np.nan
        wacc_annual_at = np.nan; re_annual = np.nan; lcoe = np.nan
        irr_equity = np.nan; npv_equity = np.nan; roi_equity = np.nan; payback_equity_years = np.nan
        irr_project = np.nan; npv_project = np.nan; payback_project_years = np.nan; avg_dscr = np.nan

        try:
            if scenario_name not in self.scenarios:
                raise ValueError(f"Scénario '{scenario_name}' invalide.")
            scenario = self.scenarios[scenario_name]
            global_config = self.config # Utilise la copie faite dans __init__
            
            # ... (agrégation des paramètres de base : CAPEX, OPEX, Puissance - inchangée) ...
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
                # Utiliser les clés spécifiques de la config globale pour CAPEX et Puissance
                capex_base_input = float(global_config.get('capex_scenario', 0.0)) # Clé utilisée dans la fixture base_config
                puissance_kwc_global = float(global_config.get('puissance_kwc_installee', 0.0)) # Clé utilisée dans la fixture base_config
                
                total_opex_maintenance_base_annual = float(global_config.get('opex_maintenance_fallback',0.0))
                total_opex_assurance_base_annual = float(global_config.get('opex_insurance_fallback',0.0))
                total_opex_admin_base_annual = float(global_config.get('opex_admin_fallback',0.0))
                if global_config.get("opex_onduleur_provision_globale", False):
                    cost_unindexed_global = float(global_config.get("opex_onduleur_total_cost_global", 0.0))
                    lifetime_global = int(global_config.get("opex_onduleur_lifetime_global", 0))
                    if cost_unindexed_global > 0 and lifetime_global > 0:
                        total_base_annual_unindexed_inverter_provision = cost_unindexed_global / lifetime_global


            # Application des Modificateurs de Scénario sur CAPEX
            capex_brut_total_scenario = capex_base_input * (1 + float(scenario.get('capex_modifier', 0.0))) # Renommé pour clarté
            # S'assurer que cette variable existe pour compatibilité avec le reste du code
            capex_scenario_simule = capex_brut_total_scenario

            # Calcul Subvention (uniquement €/kWc comme discuté pour la France)
            applicable_sub_rate = 0.0
            if puissance_kwc_global <= 3: applicable_sub_rate = float(global_config.get("subvention_rate_le3",100.0))
            elif puissance_kwc_global <= 9: applicable_sub_rate = float(global_config.get("subvention_rate_le9", 80.0))
            elif puissance_kwc_global <= 36: applicable_sub_rate = float(global_config.get("subvention_rate_le36", 150.0)) # Ajusté à la valeur de votre fixture
            elif puissance_kwc_global <= 100: applicable_sub_rate = float(global_config.get("subvention_rate_le100", 100.0))
            elif puissance_kwc_global <= 500: applicable_sub_rate = float(global_config.get("subvention_rate_le500",80.0)) # Ajusté
            else: applicable_sub_rate = float(global_config.get("subvention_rate_gt100", 0.0))
            subvention_finale_pour_calculs = applicable_sub_rate * puissance_kwc_global
            logger.info(f"Subvention (€/kWc) calculée: {subvention_finale_pour_calculs:.2f} € pour {puissance_kwc_global:.2f} kWc (taux: {applicable_sub_rate} €/kWc)")

            # MODIFICATION 1: CAPEX Net utilisé pour les flux d'investissement et l'amortissement
            capex_net_subvention = max(0, capex_brut_total_scenario - subvention_finale_pour_calculs)
            logger.info(f"CAPEX Scénario Brut: {capex_brut_total_scenario:.2f} €, Subvention: {subvention_finale_pour_calculs:.2f} €, CAPEX Net: {capex_net_subvention:.2f} €")

            # Application modificateurs OPEX (inchangé)
            opex_modifier_scenario = float(scenario.get("opex_modifier", 1.0))
            opex_maintenance_scenario_annual = total_opex_maintenance_base_annual * opex_modifier_scenario
            opex_assurance_scenario_annual = total_opex_assurance_base_annual * opex_modifier_scenario
            opex_admin_scenario_annual = total_opex_admin_base_annual * opex_modifier_scenario
            
            # ... (Lecture et Conversion des Paramètres Globaux - inchangée) ...
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
            valeur_residuelle_pct_config = float(global_config.get("valeur_residuelle_pct", 0.0)) # Attendu en décimal par le code
            cout_demantelement_pct_config = float(global_config.get("cout_demantelement_pct", 0.0)) # Attendu en décimal
            cout_fonds_propres_pct_config = float(global_config.get("cout_fonds_propres", 8.0))
            loan_active = global_config.get("with_loan", True)
            debt_ratio_config = float(global_config.get("debt_ratio", 0.80)) if loan_active else 0.0
            debt_term_years_config = int(global_config.get("debt_term_years", 20)) if loan_active else 0
            taux_interet_dette_pct_config = float(global_config.get("taux_interet_dette", 4.0)) if loan_active else 0.0
            taux_interet_dette_annual = taux_interet_dette_pct_config / 100.0
            vat_rate_operations = float(global_config.get("taux_tva_operations_pct", 20.0)) / 100.0
            vat_rate_capex = float(global_config.get("taux_tva_capex_pct", 20.0)) / 100.0
            vat_capex_recovery_month_offset = int(global_config.get("vat_capex_recovery_delay_months", 3))
            source_prix_autoc_config = global_config.get("source_prix_autoconso", "prix_initial")
            tarif_edf_ref_config = float(global_config.get("tarif_edf_reference", 0.21))

            # Calcul Tarif OA base
            t_oa_le9 = float(global_config.get("tarif_oa_bracket_le9", 0.07)) # Mis à jour selon base_config
            t_oa_le100 = float(global_config.get("tarif_oa_bracket_le100", 0.06)) # Mis à jour
            t_oa_gt100 = float(global_config.get("tarif_oa_bracket_gt100", 0.05)) # Mis à jour
            if puissance_kwc_global <= 9: tarif_oa_base = t_oa_le9
            elif puissance_kwc_global <= 100: tarif_oa_base = t_oa_le100
            else: tarif_oa_base = t_oa_gt100

            # Calcul TURPE base
            if puissance_kwc_global <= 36: actual_turpe_tension = "BT<=36kVA"
            elif puissance_kwc_global <= 250: actual_turpe_tension = "BT>36kVA"
            else: actual_turpe_tension = "HTA"
            turpe_prod_contrat_setting = global_config.get("turpe_prod_contrat", "Unique")
            logger.info(f"MOTEUR - TURPE: P_globale={puissance_kwc_global:.2f}kWc -> Tension déterminée: {actual_turpe_tension}. Contrat choisi: {turpe_prod_contrat_setting}")
            if not TURPE_PROD_RATES: cg_rate = 0.0; cc_rate = 0.0; logger.warning("MOTEUR - TURPE: TURPE_PROD_RATES non chargé ou vide. TURPE sera 0.")
            else:
                cg_rate = TURPE_PROD_RATES.get(actual_turpe_tension, {}).get("CG", {}).get(turpe_prod_contrat_setting, 0.0)
                cc_keys = list(TURPE_PROD_RATES.get(actual_turpe_tension, {}).get("CC", {}).keys())
                cc_key_to_use = None
                if actual_turpe_tension == "BT<=36kVA" and "Linky" in cc_keys: cc_key_to_use = "Linky"
                elif cc_keys: cc_key_to_use = cc_keys[0]
                if cc_key_to_use: cc_rate = TURPE_PROD_RATES.get(actual_turpe_tension, {}).get("CC", {}).get(cc_key_to_use, 0.0); logger.info(f"MOTEUR - TURPE: Utilisation clé CC '{cc_key_to_use}' pour tension '{actual_turpe_tension}'.")
                else: cc_rate = 0.0; logger.info(f"MOTEUR - TURPE: Aucune clé CC applicable trouvée pour tension '{actual_turpe_tension}'. CC mis à 0.")
            turpe_annual_base_config = cg_rate + cc_rate
            logger.info(f"MOTEUR - TURPE: Base annuelle calculée par le moteur: {turpe_annual_base_config:.2f} €/an (CG:{cg_rate}, CC:{cc_rate})")
            turpe_annual_base_scenario = turpe_annual_base_config
            
            production_modifier_scenario = float(scenario.get("production_modifier", 1.0))
            adjusted_inflation_scenario_rate = adjusted_inflation_annual * float(scenario.get("inflation_modifier", 1.0))
            degradation_rate_scenario_effective = degradation_rate_base * float(scenario.get("degradation_modifier", 1.0)) 
            
            prix_vente_final_a_utiliser = float(prix_revente) if prix_revente is not None else \
                                    float(global_config.get("prix_vente_initial_slider_fallback", 0.10))
            source_prix_autoc_effective = override_source_prix_autoconso if override_source_prix_autoconso is not None else source_prix_autoc_config
            
            hourly_data_to_return = aggregate_energy_data(self.sites_data, effective_sites_config)
            
            # ... (Préparation Structure Mensuelle - inchangée) ...
            monthly_index = pd.date_range(start=date_debut_simulation_effective, periods=num_total_simulation_months, freq='ME') # ME pour Month End
            monthly_results_df = pd.DataFrame(index=monthly_index)
            monthly_cols = [
                'Is_Construction_Phase', 'Year_Index', 'Sim_Year', 'Inflation_Factor', 'Degradation_Factor',
                'Year_Index_Operational', 'Sim_Year_Operational', 'Inflation_Factor_Operational', 'Degradation_Factor_Operational',
                'Production_kWh', 'Consommation_kWh', 'Autoconsommation_kWh', 'Surplus_kWh',
                'Tarif_OA_Annuel', 'Prix_Autoconso_Annuel',
                'Revenus_Surplus', 'Revenus_Autoconsommation', 'Revenus_Total',
                'OPEX_Maintenance_Mensuel', 'OPEX_Assurance_Mensuel', 'OPEX_Admin_Mensuel',
                'OPEX_Provision_Onduleur_Mensuel', 'OPEX', 
                'TURPE', 'Amortissement', 'EBITDA', 'EBIT',
                'Interets_Payes', 'Principal_Rembourse', 'EBT',
                'Tax_Payment', 'Solde_IS_N_1_Paye_Mois', 'Total_IS_Decaisse_Mois',
                'Resultat_Net', 'FCFE', 'OCF_Projet',
                'Solde_Dette_Fin_Mois', 'Service_Dette',
                'VAT_Collectee', 'VAT_Deductible_CAPEX', 'VAT_Deductible_OPEX_TURPE', 
                'VAT_Due_Mois', 'VAT_Payment',
                'BFR_Mensuel', 'Delta_BFR_Mensuel',
                'Solde_Tresorerie_Fin_Mois', 'CAPEX_Initial_Mensuel'
            ]
            for col in monthly_cols: monthly_results_df[col] = 0.0

            # MODIFICATION 2: CAPEX_Initial_Mensuel doit refléter le CAPEX *net* de subvention si c'est ce qu'on veut pour LCOE/VAN Projet.
            # L'amortissement se base sur capex_net_subvention (total).
            # La TVA sur CAPEX (pour FCFE) se base sur capex_brut_total_scenario.
            if duree_construction_cfg > 0:
                capex_net_mensuel_pour_flux = capex_net_subvention / duree_construction_cfg
            else: # Tout au premier mois de la simulation (qui pourrait être un mois de construction si duree_construction_cfg=0 mais date_debut_ppa est future)
                capex_net_mensuel_pour_flux = capex_net_subvention

            # Le reste du CAPEX et de la dette
            debt_amount = capex_net_subvention * debt_ratio_config if loan_active else 0.0
            net_equity_investment = capex_net_subvention - debt_amount # Equity nécessaire pour couvrir CAPEX net

            monthly_interest_paid, monthly_principal_paid, monthly_debt_balance = calculate_monthly_loan_schedule(
                debt_amount, taux_interet_dette_annual, debt_term_years_config, num_total_simulation_months
            )
            
            # Amortissement basé sur CAPEX Net
            val_residuelle_montant = capex_net_subvention * valeur_residuelle_pct_config
            base_amortissable = capex_net_subvention - val_residuelle_montant
            annual_depreciation_base = base_amortissable / amortissement_duree_years if amortissement_duree_years > 0 else 0.0
            
            # TVA sur CAPEX basée sur CAPEX Brut
            tva_sur_capex_initial = capex_brut_total_scenario * vat_rate_capex

            df_agg_for_ref = hourly_data_to_return.set_index('Temps')
            if df_agg_for_ref.empty: ref_year = date_debut_operations.year
            else: ref_year = df_agg_for_ref.index.year.min()
            reference_data_ts = df_agg_for_ref[df_agg_for_ref.index.year == ref_year].copy()

            logger.info(f"CORE DEBUG - Type de reference_data_ts.index: {type(reference_data_ts.index)}")
            logger.info(f"CORE DEBUG - isinstance(reference_data_ts.index, pd.DatetimeIndex): {isinstance(reference_data_ts.index, pd.DatetimeIndex)}")
            if hasattr(reference_data_ts.index, 'dtype'):
                logger.info(f"CORE DEBUG - Dtype des valeurs de reference_data_ts.index: {reference_data_ts.index.dtype}")
            else:
                logger.info("CORE DEBUG - reference_data_ts.index n'a pas d'attribut dtype.")
            logger.info(f"CORE DEBUG - Premières 3 lignes de reference_data_ts:\n{reference_data_ts.head(3)}")

            logger.info(f"CORE DEBUG - hourly_data_to_return: Shape={hourly_data_to_return.shape}, Colonnes={hourly_data_to_return.columns.tolist()}")

            # ... (Début de la boucle mensuelle - les affectations à CAPEX_Initial_Mensuel utiliseront capex_net_mensuel_pour_flux) ...
            # ... (LA LOGIQUE INTERNE DE LA BOUCLE MENSUELLE RESTE IDENTIQUE À CELLE QUE VOUS AVEZ FOURNIE PRÉCÉDEMMENT)
            #       Assurez-vous que 'CAPEX_Initial_Mensuel' est rempli avec capex_net_mensuel_pour_flux pendant la construction
            #       Et que OCF_Projet soustrait bien ce CAPEX_Initial_Mensuel (qui est maintenant net).

            loss_carryforward_balance = 0.0; annual_tax_calculated_prev_year = 0.0
            current_quarterly_acompte_is = 0.0; current_year_tracker = -1
            current_operational_year_tracker = -1
            inflation_factor_op_year_current = 1.0; degradation_factor_op_year_current = 1.0
            opex_maint_indexed_annual_op = opex_maintenance_scenario_annual
            opex_assur_indexed_annual_op = opex_assurance_scenario_annual
            opex_admin_indexed_annual_op = opex_admin_scenario_annual
            inverter_prov_indexed_annual_op = total_base_annual_unindexed_inverter_provision
            turpe_indexed_annual_op = turpe_annual_base_scenario
            depreciation_annual_op = annual_depreciation_base
            oa_rate_annual_op = tarif_oa_base
            if source_prix_autoc_effective == 'prix_initial': prix_autoc_annual_op = prix_vente_final_a_utiliser
            elif source_prix_autoc_effective == 'tarif_edf': prix_autoc_annual_op = tarif_edf_ref_config
            elif source_prix_autoc_effective == 'tarif_oa': prix_autoc_annual_op = oa_rate_annual_op
            else: prix_autoc_annual_op = prix_vente_final_a_utiliser
            solde_IS_N_1_annee_precedente_a_payer_en_N = 0.0
            mois_paiement_solde_is = int(global_config.get("mois_paiement_solde_is", 5))
            bfr_receivables_days_config = float(global_config.get("bfr_receivables_days", 30.0))
            bfr_payables_days_config = float(global_config.get("bfr_payables_days", 15.0))
            bfr_previous_month_val = 0.0
            vat_credit_carryforward = 0.0

            for month_idx in range(num_total_simulation_months):
                current_month_end_date = monthly_index[month_idx]
                year_idx_sim_total = current_month_end_date.year - date_debut_simulation_effective.year
                monthly_results_df.loc[current_month_end_date, 'Year_Index'] = year_idx_sim_total
                monthly_results_df.loc[current_month_end_date, 'Sim_Year'] = year_idx_sim_total + 1
                is_construction_phase = month_idx < duree_construction_cfg
                monthly_results_df.loc[current_month_end_date, 'Is_Construction_Phase'] = 1.0 if is_construction_phase else 0.0
                
                if is_construction_phase:
                    # MODIFICATION DANS LA BOUCLE: Utiliser capex_net_mensuel_pour_flux
                    monthly_results_df.loc[current_month_end_date, 'CAPEX_Initial_Mensuel'] = capex_net_mensuel_pour_flux
                else:
                    monthly_results_df.loc[current_month_end_date, 'CAPEX_Initial_Mensuel'] = 0.0 # Pas de CAPEX d'investissement après construction

                year_idx_op = -1; sim_year_num_op = 0
                if not is_construction_phase:
                    operational_month_idx = month_idx - duree_construction_cfg
                    year_idx_op = operational_month_idx // 12
                    sim_year_num_op = year_idx_op + 1
                    if year_idx_op != current_operational_year_tracker:
                        inflation_factor_op_year_current = (1 + adjusted_inflation_scenario_rate) ** year_idx_op
                        degradation_factor_op_year_current = (1 - degradation_rate_scenario_effective) ** year_idx_op
                        opex_maint_indexed_annual_op = opex_maintenance_scenario_annual * inflation_factor_op_year_current
                        opex_assur_indexed_annual_op = opex_assurance_scenario_annual * inflation_factor_op_year_current
                        opex_admin_indexed_annual_op = opex_admin_scenario_annual * inflation_factor_op_year_current
                        inverter_prov_indexed_annual_op = total_base_annual_unindexed_inverter_provision * inflation_factor_op_year_current
                        turpe_indexed_annual_op = turpe_annual_base_scenario * (inflation_factor_op_year_current if turpe_indexed else 1.0)
                        depreciation_annual_op = annual_depreciation_base if year_idx_op < amortissement_duree_years else 0.0
                        oa_rate_annual_op = tarif_oa_base * ((1 + inflation_rate_oa_annual)**year_idx_op if oa_indexed else 1.0)
                        if source_prix_autoc_effective == 'prix_initial': prix_autoc_annual_op = prix_vente_final_a_utiliser * inflation_factor_op_year_current
                        elif source_prix_autoc_effective == 'tarif_edf': prix_autoc_annual_op = tarif_edf_ref_config * inflation_factor_op_year_current
                        elif source_prix_autoc_effective == 'tarif_oa': prix_autoc_annual_op = oa_rate_annual_op
                        else: prix_autoc_annual_op = prix_vente_final_a_utiliser * inflation_factor_op_year_current
                        current_operational_year_tracker = year_idx_op
                monthly_results_df.loc[current_month_end_date, 'Year_Index_Operational'] = year_idx_op
                monthly_results_df.loc[current_month_end_date, 'Sim_Year_Operational'] = sim_year_num_op
                monthly_results_df.loc[current_month_end_date, 'Inflation_Factor_Operational'] = inflation_factor_op_year_current
                monthly_results_df.loc[current_month_end_date, 'Degradation_Factor_Operational'] = degradation_factor_op_year_current
                if is_construction_phase:
                    monthly_results_df.loc[current_month_end_date, ['Production_kWh', 'Consommation_kWh', 'Autoconsommation_kWh', 'Surplus_kWh', 'Revenus_Surplus', 'Revenus_Autoconsommation', 'Revenus_Total', 'OPEX_Maintenance_Mensuel', 'OPEX_Assurance_Mensuel', 'OPEX_Admin_Mensuel', 'OPEX_Provision_Onduleur_Mensuel', 'OPEX', 'TURPE', 'Amortissement']] = 0.0
                else: # Phase d'exploitation
                    monthly_results_df.loc[current_month_end_date, 'Tarif_OA_Annuel'] = oa_rate_annual_op
                    monthly_results_df.loc[current_month_end_date, 'Prix_Autoconso_Annuel'] = prix_autoc_annual_op
                    prod_m, cons_m, auto_m, surplus_m = 0.0, 0.0, 0.0, 0.0

                    logger.info(f"CORE LOOP - Mois Sim: {current_month_end_date.strftime('%Y-%m')}, Mois Op Cible: {current_month_end_date.month}")

                    logger.info(f"CORE DEBUG (AVANT INSTANCEOF) - Scenario: {scenario_name}, Type reference_data_ts.index: {type(reference_data_ts.index)}")
                    logger.info(f"CORE DEBUG (AVANT INSTANCEOF) - Scenario: {scenario_name}, Résultat isinstance(reference_data_ts.index, pd.DatetimeIndex): {isinstance(reference_data_ts.index, pd.DatetimeIndex)}")
                    if hasattr(reference_data_ts.index, 'dtype'):
                        logger.info(f"CORE DEBUG (AVANT INSTANCEOF) - Scenario: {scenario_name}, Dtype reference_data_ts.index: {reference_data_ts.index.dtype}")
                    logger.info(f"CORE DEBUG (AVANT INSTANCEOF) - Scenario: {scenario_name}, reference_data_ts.empty: {reference_data_ts.empty}")
                    logger.info(f"CORE DEBUG (AVANT INSTANCEOF) - Scenario: {scenario_name}, Extrait index: {reference_data_ts.index[:5] if not reference_data_ts.empty else 'N/A'}")

                    if not reference_data_ts.empty and isinstance(reference_data_ts.index, pd.DatetimeIndex):
                        ref_monthly_energy_slice = reference_data_ts[reference_data_ts.index.month == current_month_end_date.month]
                        logger.info(f"CORE DEBUG - Mois: {current_month_end_date.month} - ref_monthly_energy_slice shape: {ref_monthly_energy_slice.shape}, sum prod: {ref_monthly_energy_slice['production_kwh'].sum() if not ref_monthly_energy_slice.empty and 'production_kwh' in ref_monthly_energy_slice.columns else ('Vide' if ref_monthly_energy_slice.empty else 'No prod col or empty')}")
                        
                        if ref_monthly_energy_slice.empty:
                            logger.error(f"⚠️ ALERTE CRITIQUE: Production totale quasi nulle ({ref_monthly_energy_slice['production_kwh'].sum() if not ref_monthly_energy_slice.empty and 'production_kwh' in ref_monthly_energy_slice.columns else ('Vide' if ref_monthly_energy_slice.empty else 'No prod col or empty')}) dans reference_data_ts!")
                            # Afficher plus de détails sur les sites et données source
                            logger.info(f"CORE DEBUG - Sites disponibles: {list(self.sites_data.keys())}")
                            for site_id, site_df in self.sites_data.items():
                                if not site_df.empty and 'production_kwh' in site_df.columns:
                                    prod_sum_site = site_df['production_kwh'].sum()
                                    logger.info(f"CORE DEBUG - Site {site_id}: Somme production={prod_sum_site:.2f} kWh")
                        else:
                            prod_ref_s = pd.Series(ref_monthly_energy_slice.get('production_kwh', 0.0)); cons_ref_s = pd.Series(ref_monthly_energy_slice.get('consumption_kwh', 0.0))
                            logger.info(f"CORE LOOP - prod_ref_s - Somme: {prod_ref_s.sum():.2f}, 5 premières: {prod_ref_s.head().tolist()}")
                            
                            prod_adj_s = prod_ref_s * degradation_factor_op_year_current * production_modifier_scenario
                            logger.info(f"CORE DEBUG INTERNE BOUCLE - Mois: {current_month_end_date.month} - degradation: {degradation_factor_op_year_current:.4f}, prod_modif: {production_modifier_scenario:.2f}")
                            if hasattr(prod_ref_s, 'sum'):
                                logger.info(f"CORE DEBUG INTERNE BOUCLE - Mois: {current_month_end_date.month} - prod_ref_s sum: {prod_ref_s.sum():.2f}")
                                logger.info(f"CORE DEBUG INTERNE BOUCLE - Mois: {current_month_end_date.month} - prod_ref_s contient des NaNs: {prod_ref_s.isnull().values.any()}") # Vérifie les NaN dans la série
                            else:
                                logger.info(f"CORE DEBUG INTERNE BOUCLE - Mois: {current_month_end_date.month} - prod_ref_s n'est pas une Series ou est vide.")

                            if hasattr(prod_adj_s, 'sum'):
                                logger.info(f"CORE DEBUG INTERNE BOUCLE - Mois: {current_month_end_date.month} - prod_adj_s sum: {prod_adj_s.sum():.2f}")
                                logger.info(f"CORE DEBUG INTERNE BOUCLE - Mois: {current_month_end_date.month} - prod_adj_s contient des NaNs: {prod_adj_s.isnull().values.any()}") # Vérifie les NaN dans la série
                                if prod_adj_s.isnull().values.any():
                                    logger.info(f"CORE DEBUG INTERNE BOUCLE - Mois: {current_month_end_date.month} - Extrait de prod_adj_s avec NaNs:\n{prod_adj_s[prod_adj_s.isnull()].head()}")
                            else:
                                logger.info(f"CORE DEBUG INTERNE BOUCLE - Mois: {current_month_end_date.month} - prod_adj_s n'est pas une Series ou est vide.")
                            
                            # Logs détaillés AVANT la création de df_hourly_month
                            logger.info(f"CORE PRE-DF - Mois {current_month_end_date.month} --- DÉTAILS AVANT CRÉATION df_hourly_month ---")
                            for var_name, var_val in [('prod_adj_s', prod_adj_s), ('cons_ref_s', cons_ref_s)]:
                                logger.info(f"CORE PRE-DF - Mois {current_month_end_date.month} - Variable: {var_name}, Type: {type(var_val)}")
                                if hasattr(var_val, 'shape'):
                                    logger.info(f"CORE PRE-DF - Mois {current_month_end_date.month} -   {var_name} shape: {var_val.shape}")
                                if hasattr(var_val, 'index'):
                                    logger.info(f"CORE PRE-DF - Mois {current_month_end_date.month} -   {var_name} index head(3):\n{var_val.index[:3]}")
                                if hasattr(var_val, 'head'):
                                    logger.info(f"CORE PRE-DF - Mois {current_month_end_date.month} -   {var_name} values head(3):\n{var_val.head(3)}")
                                if hasattr(var_val, 'isnull') and hasattr(var_val.isnull(), 'any'):
                                    logger.info(f"CORE PRE-DF - Mois {current_month_end_date.month} -   {var_name} contient NaNs: {var_val.isnull().any()}")
                                if hasattr(var_val, 'sum'):
                                    logger.info(f"CORE PRE-DF - Mois {current_month_end_date.month} -   {var_name} sum: {var_val.sum()}")
                            logger.info(f"CORE PRE-DF - Mois {current_month_end_date.month} --- FIN DÉTAILS AVANT CRÉATION df_hourly_month ---")

                            try:
                                # --- DÉBUT DE LA CORRECTION DU CALCUL D'AUTOCONSOMMATION ---                            # Créer un DataFrame temporaire pour aligner les données horaires du mois                            
                                df_hourly_month = pd.DataFrame({                                
                                    'production': prod_adj_s,  # Série horaire de production pour le mois                                
                                    'consumption': cons_ref_s  # Série horaire de consommation pour le mois                            
                                })
                                # Log AVANT fillna
                                logger.info(f"CORE DEBUG DF_HOURLY - AVANT FILLNA - Mois {current_month_end_date.month} - df_hourly_month['production'] sum: {df_hourly_month['production'].sum() if not df_hourly_month.empty else 'Vide'}")
                                if not df_hourly_month.empty:
                                    logger.info(f"CORE DEBUG DF_HOURLY - AVANT FILLNA - Mois {current_month_end_date.month} - df_hourly_month['production'] contient NaNs: {df_hourly_month['production'].isnull().values.any()}")
                                    logger.info(f"CORE DEBUG DF_HOURLY - AVANT FILLNA - Mois {current_month_end_date.month} - Extrait df_hourly_month['production']:\n{df_hourly_month['production'].head()}")

                                # Remplir les NaN potentiels si les séries n'avaient pas exactement les mêmes pas de temps                            
                                df_hourly_month.fillna(0, inplace=True)                            
                                
                                # Log APRES fillna
                                logger.info(f"CORE DEBUG DF_HOURLY - APRES FILLNA - Mois {current_month_end_date.month} - df_hourly_month['production'] sum: {df_hourly_month['production'].sum() if not df_hourly_month.empty else 'Vide'}")
                                if not df_hourly_month.empty:
                                    logger.info(f"CORE DEBUG DF_HOURLY - APRES FILLNA - Mois {current_month_end_date.month} - Extrait df_hourly_month['production']:\n{df_hourly_month['production'].head()}")

                                # Calculer l'autoconsommation HORAIRE                            
                                autoconsommation_horaire = np.minimum(df_hourly_month['production'], df_hourly_month['consumption'])                            # Calculer le surplus HORAIRE (production non autoconsommée)                            
                                surplus_horaire = df_hourly_month['production'] - autoconsommation_horaire                            # S'assurer que le surplus n'est pas négatif (à cause d'arrondis flottants par exemple)                            
                                surplus_horaire = np.maximum(0, surplus_horaire)                            # Maintenant, sommer ces valeurs horaires pour obtenir les totaux MENSUELS                            
                                prod_m = df_hourly_month['production'].sum()  # Production totale du mois                            
                                cons_m = df_hourly_month['consumption'].sum()  # Consommation totale du mois                            
                                auto_m = autoconsommation_horaire.sum()  # Autoconsommation mensuelle basée sur la somme des autoconsommations horaires                            
                                surplus_m = surplus_horaire.sum()  # Surplus mensuel basé sur la somme des surplus horaires
                            
                            except Exception as e_df_creation: # Changé pour Exception pour être plus large
                                logger.error(f"ERREUR CRITIQUE LORS DE LA CRÉATION/UTILISATION DE df_hourly_month au mois {current_month_end_date.month}! Exception: {type(e_df_creation).__name__} - {str(e_df_creation)}", exc_info=True)
                                # Les variables prod_m, cons_m etc. conserveront leur initialisation à 0.0 car elles sont définies avant le try
                                # Nul besoin de les réassigner explicitement ici si elles sont déjà à 0.0.
                                # Si elles n'étaient pas initialisées avant, il faudrait le faire ici :
                                # prod_m, cons_m, auto_m, surplus_m = 0.0, 0.0, 0.0, 0.0
                                pass # Permet de continuer la boucle pour le mois suivant, prod_m sera 0 pour ce mois.

                            # --- FIN DE LA CORRECTION DU CALCUL D'AUTOCONSOMMATION ---
                    monthly_results_df.loc[current_month_end_date, 'Production_kWh'] = prod_m; monthly_results_df.loc[current_month_end_date, 'Consommation_kWh'] = cons_m
                    monthly_results_df.loc[current_month_end_date, 'Autoconsommation_kWh'] = auto_m; monthly_results_df.loc[current_month_end_date, 'Surplus_kWh'] = surplus_m
                    rev_surplus = surplus_m * oa_rate_annual_op; rev_auto = auto_m * prix_autoc_annual_op
                    monthly_results_df.loc[current_month_end_date, 'Revenus_Surplus'] = rev_surplus; monthly_results_df.loc[current_month_end_date, 'Revenus_Autoconsommation'] = rev_auto
                    monthly_results_df.loc[current_month_end_date, 'Revenus_Total'] = rev_surplus + rev_auto
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Maintenance_Mensuel'] = opex_maint_indexed_annual_op / 12.0
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Assurance_Mensuel'] = opex_assur_indexed_annual_op / 12.0
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Admin_Mensuel'] = opex_admin_indexed_annual_op / 12.0
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Provision_Onduleur_Mensuel'] = inverter_prov_indexed_annual_op / 12.0
                    monthly_results_df.loc[current_month_end_date, 'OPEX'] = (opex_maint_indexed_annual_op + opex_assur_indexed_annual_op + opex_admin_indexed_annual_op + inverter_prov_indexed_annual_op) / 12.0
                    monthly_results_df.loc[current_month_end_date, 'TURPE'] = turpe_indexed_annual_op / 12.0
                    monthly_results_df.loc[current_month_end_date, 'Amortissement'] = depreciation_annual_op / 12.0
                
                # Suite des calculs P&L mensuels
                ebitda_m = (monthly_results_df.loc[current_month_end_date, 'Revenus_Total'] - monthly_results_df.loc[current_month_end_date, 'OPEX'] - monthly_results_df.loc[current_month_end_date, 'TURPE'])
                monthly_results_df.loc[current_month_end_date, 'EBITDA'] = ebitda_m
                ebit_m = ebitda_m - monthly_results_df.loc[current_month_end_date, 'Amortissement']
                monthly_results_df.loc[current_month_end_date, 'EBIT'] = ebit_m
                interest_m = monthly_interest_paid[month_idx] if month_idx < len(monthly_interest_paid) else 0.0
                principal_m = monthly_principal_paid[month_idx] if month_idx < len(monthly_principal_paid) else 0.0
                monthly_results_df.loc[current_month_end_date, 'Interets_Payes'] = interest_m
                monthly_results_df.loc[current_month_end_date, 'Principal_Rembourse'] = principal_m
                monthly_results_df.loc[current_month_end_date, 'Service_Dette'] = interest_m + principal_m
                ebt_m_before_loss = ebit_m - interest_m
                taxable_ebt_m, loss_carryforward_balance = tax_engine.apply_loss_carryforward_cap(ebt_m_before_loss, loss_carryforward_balance)
                monthly_results_df.loc[current_month_end_date, 'EBT'] = taxable_ebt_m
                result_net_m = taxable_ebt_m # IS sera décaissé plus tard
                monthly_results_df.loc[current_month_end_date, 'Resultat_Net'] = result_net_m
                total_tax_paid_this_month = 0.0
                if current_month_end_date.month in [3, 6, 9, 12]: total_tax_paid_this_month += current_quarterly_acompte_is
                if current_month_end_date.month == mois_paiement_solde_is:
                    total_tax_paid_this_month += solde_IS_N_1_annee_precedente_a_payer_en_N
                    monthly_results_df.loc[current_month_end_date, 'Solde_IS_N_1_Paye_Mois'] = solde_IS_N_1_annee_precedente_a_payer_en_N
                monthly_results_df.loc[current_month_end_date, 'Tax_Payment'] = total_tax_paid_this_month
                monthly_results_df.loc[current_month_end_date, 'Total_IS_Decaisse_Mois'] = total_tax_paid_this_month
                if current_month_end_date.month == 12:
                    ebt_annual_for_tax = monthly_results_df[monthly_results_df.index.year == current_month_end_date.year]['EBT'].sum()
                    annual_tax_calculated_this_year = tax_engine.calculate_corporate_tax_pme(ebt_annual_for_tax)
                    solde_IS_N_1_annee_precedente_a_payer_en_N = annual_tax_calculated_prev_year - (tax_engine.calculate_quarterly_installment(annual_tax_calculated_prev_year) * 4)
                    annual_tax_calculated_prev_year = annual_tax_calculated_this_year
                    current_quarterly_acompte_is = tax_engine.calculate_quarterly_installment(annual_tax_calculated_prev_year)
                # TVA
                rev_total_m = monthly_results_df.loc[current_month_end_date, 'Revenus_Total']
                opex_m = monthly_results_df.loc[current_month_end_date, 'OPEX']; turpe_m = monthly_results_df.loc[current_month_end_date, 'TURPE']
                # Utiliser le CAPEX brut mensuel pour le calcul de la TVA déductible sur CAPEX
                capex_brut_mensuel_pour_tva = 0.0
                if is_construction_phase:
                    capex_brut_mensuel_pour_tva = capex_brut_total_scenario / duree_construction_cfg if duree_construction_cfg > 0 else capex_brut_total_scenario
                
                vat_collectee = rev_total_m * vat_rate_operations
                vat_ded_opex_turpe = (opex_m + turpe_m) * vat_rate_operations
                vat_ded_capex_mois = 0.0
                # La récupération de la TVA sur CAPEX se fait sur le total, au Xème mois
                if month_idx == vat_capex_recovery_month_offset : # Assurez-vous que cet offset est 0-indexé ou ajustez
                    vat_ded_capex_mois = tva_sur_capex_initial # tva_sur_capex_initial est calculé sur le CAPEX brut total
                
                vat_due_this_month = vat_collectee - vat_ded_opex_turpe - vat_ded_capex_mois + vat_credit_carryforward
                vat_payment_this_month = 0.0
                if vat_due_this_month > 0: vat_payment_this_month = vat_due_this_month; vat_credit_carryforward = 0.0
                else: vat_credit_carryforward = vat_due_this_month
                monthly_results_df.loc[current_month_end_date, 'VAT_Collectee'] = vat_collectee
                monthly_results_df.loc[current_month_end_date, 'VAT_Deductible_CAPEX'] = vat_ded_capex_mois
                monthly_results_df.loc[current_month_end_date, 'VAT_Deductible_OPEX_TURPE'] = vat_ded_opex_turpe
                monthly_results_df.loc[current_month_end_date, 'VAT_Due_Mois'] = vat_due_this_month
                monthly_results_df.loc[current_month_end_date, 'VAT_Payment'] = vat_payment_this_month
                # BFR
                bfr_receivables_this_month = (rev_total_m / 30.0) * bfr_receivables_days_config if not is_construction_phase else 0.0
                bfr_payables_this_month = ((opex_m + turpe_m) / 30.0) * bfr_payables_days_config if not is_construction_phase else 0.0
                bfr_current_month_val = bfr_receivables_this_month - bfr_payables_this_month
                delta_bfr_this_month = bfr_current_month_val - bfr_previous_month_val
                monthly_results_df.loc[current_month_end_date, 'BFR_Mensuel'] = bfr_current_month_val
                monthly_results_df.loc[current_month_end_date, 'Delta_BFR_Mensuel'] = delta_bfr_this_month
                bfr_previous_month_val = bfr_current_month_val
                monthly_results_df.loc[current_month_end_date, 'Solde_Dette_Fin_Mois'] = monthly_debt_balance[month_idx] if month_idx < len(monthly_debt_balance) else 0.0

            # FIN DE LA BOUCLE FOR MONTH_IDX
            logger.info(f"DEBUG POST-BOUCLE - Scenario: {scenario_name}, PrixRevente: {prix_vente_final_a_utiliser} - Sum Production_kWh: {monthly_results_df['Production_kWh'].sum():.2f}, Sum Consommation_kWh: {monthly_results_df['Consommation_kWh'].sum():.2f}, Sum Autoconsommation_kWh: {monthly_results_df['Autoconsommation_kWh'].sum():.2f}")

            # ... (Recalcul FCFE et OCF Projet post-boucle - inchangé) ...
            amortissement_mensuel = monthly_results_df['Amortissement'].fillna(0)
            principal_rembourse_mensuel = monthly_results_df['Principal_Rembourse'].fillna(0)
            ebt_mensuel = monthly_results_df['EBT'].fillna(0)
            is_decaisse_total_mensuel = monthly_results_df['Total_IS_Decaisse_Mois'].fillna(0)
            vat_payment_mensuel = monthly_results_df['VAT_Payment'].fillna(0)
            delta_bfr_mensuel_series = monthly_results_df['Delta_BFR_Mensuel'].fillna(0)
            # CAPEX_Initial_Mensuel est maintenant NET pour les flux OCF Projet et LCOE
            capex_net_mensuel_series = monthly_results_df['CAPEX_Initial_Mensuel'].fillna(0)


            debt_drawn_monthly_series = pd.Series(0.0, index=monthly_results_df.index)
            equity_injected_monthly_series = pd.Series(0.0, index=monthly_results_df.index)
            if duree_construction_cfg > 0:
                # Les dépenses CAPEX nettes sont déjà dans capex_net_mensuel_pour_flux
                # On se base sur le capex_net_subvention pour déterminer la part dette/equity
                # Et on répartit ces montants de dette/equity au prorata des dépenses capex nettes mensuelles
                total_capex_net_pendant_construction = monthly_results_df.loc[monthly_results_df['Is_Construction_Phase']==1, 'CAPEX_Initial_Mensuel'].sum()

                if abs(total_capex_net_pendant_construction - capex_net_subvention) > 1e-2 : # Tolérance pour flottants
                    logger.warning(f"Somme CAPEX_Initial_Mensuel ({total_capex_net_pendant_construction:.2f}) pendant construction ne correspond pas à capex_net_subvention ({capex_net_subvention:.2f}). Ajustement pro-rata pour dette/equity.")
                
                # Répartir la dette et l'equity au prorata des dépenses mensuelles de CAPEX net
                for idx_constr in monthly_results_df[monthly_results_df['Is_Construction_Phase']==1].index:
                    capex_net_ce_mois = monthly_results_df.loc[idx_constr, 'CAPEX_Initial_Mensuel']
                    if capex_net_subvention > 1e-6 : # Eviter division par zéro
                        ratio_ce_mois = capex_net_ce_mois / capex_net_subvention
                        debt_drawn_monthly_series.loc[idx_constr] = debt_amount * ratio_ce_mois
                        equity_injected_monthly_series.loc[idx_constr] = net_equity_investment * ratio_ce_mois
                    # Si capex_net_subvention est nul (projet sans CAPEX net), dette et equity tirées sont nulles.

            else: # Pas de construction, tout au premier mois
                debt_drawn_monthly_series.iloc[0] = debt_amount
                equity_injected_monthly_series.iloc[0] = net_equity_investment
            
            net_debt_issued_monthly_series = debt_drawn_monthly_series - principal_rembourse_mensuel
            
            # FCFE: Resultat Net + Amort - Var BFR - CAPEX Net (payé par equity/dette) + Dette Nette Emise - Remb Principal
            # Ou EBT - IS_payé + Amort - Var BFR - CAPEX_Net + Dette Nette Emise
            monthly_results_df['FCFE'] = (ebt_mensuel - is_decaisse_total_mensuel + amortissement_mensuel - 
                                         vat_payment_mensuel - delta_bfr_mensuel_series - 
                                         capex_net_mensuel_series + net_debt_issued_monthly_series)

            ebitda_mensuel_series = monthly_results_df['EBITDA'].fillna(0)
            # OCF Projet: EBITDA*(1-T) + Amort*T - Investissement Net (CAPEX_Initial_Mensuel est déjà net)
            monthly_results_df['OCF_Projet'] = ((ebitda_mensuel_series * (1.0 - tax_rate_decimal)) + 
                                               (amortissement_mensuel * tax_rate_decimal) - 
                                               capex_net_mensuel_series) # capex_net_mensuel_series est le CAPEX net
            
            initial_cash_balance_at_true_t0 = 0.0 
            total_company_net_cash_flow_monthly = monthly_results_df['FCFE'].fillna(0) + equity_injected_monthly_series.fillna(0)
            cumulative_total_company_net_cash_flow = total_company_net_cash_flow_monthly.cumsum()
            monthly_results_df['Solde_Tresorerie_Fin_Mois'] = initial_cash_balance_at_true_t0 + cumulative_total_company_net_cash_flow


            # ... (Calculs financiers finaux : WACC, NPV, IRR, Payback, LCOE, DSCR - inchangés) ...
            re_annual = float(cout_fonds_propres_pct_config)
            wacc_annual_at = calculate_wacc(
                debt_ratio=debt_ratio_config,
                taux_interet_dette_pct=taux_interet_dette_pct_config, 
                taux_imposition_pct=taux_imposition_standard_pct,
                cout_fonds_propres_pct=re_annual,
                wacc_type="after_tax"
            )
            if wacc_annual_at is None: 
                logger.warning("Calcul du WACC a échoué, utilisation d'un fallback dangereux de 6.0%")
                wacc_annual_at = 6.0 
            
            # Conversion des taux annuels en taux mensuels équivalents
            re_monthly = (1 + re_annual/100)**(1/12) - 1
            wacc_monthly_at = (1 + wacc_annual_at/100)**(1/12) - 1

            # Préparation des flux pour NPV/IRR
            fcfe_monthly_array = monthly_results_df['FCFE'].fillna(0).values
            
            # Correction: Le FCFE est directement le flux de trésorerie de l'actionnaire.
            # Un FCFE négatif pendant la construction représente l'injection d'equity nécessaire.
            # Un FCFE positif pendant l'exploitation est le retour disponible pour l'actionnaire.
            equity_cash_flows_monthly = fcfe_monthly_array.copy()

            ocf_monthly_array = monthly_results_df['OCF_Projet'].fillna(0).values
            # OCF_Projet dans la boucle mensuelle inclut déjà `-capex_mensuel_series`.
            # Il ne faut donc PAS soustraire `capex_net_subvention` ici de nouveau.
            project_cash_flows_monthly = ocf_monthly_array.copy() 

            val_residuelle_montant_fin = capex_net_subvention * (valeur_residuelle_pct_config) # pct en décimal
            cout_demantelement_montant_fin = capex_brut_total_scenario * (cout_demantelement_pct_config) # pct en décimal
            terminal_value_net_projet = val_residuelle_montant_fin - cout_demantelement_montant_fin
            if len(project_cash_flows_monthly) > 0:
                project_cash_flows_monthly[-1] += terminal_value_net_projet
            
            # NPV, IRR, ROI Equity
            irr_eq_raw = npf.irr(equity_cash_flows_monthly)
            irr_equity = (1 + irr_eq_raw)**12 - 1 if pd.notna(irr_eq_raw) and np.isfinite(irr_eq_raw) else np.nan
            npv_equity = npf.npv(re_monthly, equity_cash_flows_monthly) if pd.notna(re_monthly) else np.nan
            roi_equity = npv_equity / abs(net_equity_investment) if pd.notna(npv_equity) and abs(net_equity_investment) > 1e-9 else np.nan
            
            # NPV, IRR Projet
            irr_proj_raw = npf.irr(project_cash_flows_monthly)
            irr_project = (1 + irr_proj_raw)**12 - 1 if pd.notna(irr_proj_raw) and np.isfinite(irr_proj_raw) else np.nan
            npv_project = npf.npv(wacc_monthly_at, project_cash_flows_monthly) if pd.notna(wacc_monthly_at) else np.nan
            
            # Payback periods (utilisation de la fonction de engine_utils)
            payback_equity_months = calculate_payback_months(equity_cash_flows_monthly)
            payback_equity_years = payback_equity_months / 12.0 if payback_equity_months is not None else np.nan
            payback_project_months = calculate_payback_months(project_cash_flows_monthly) # OCF_Projet inclut déjà -CAPEX
            payback_project_years = payback_project_months / 12.0 if payback_project_months is not None else np.nan
            
            # MODIFICATION: Ajouter des logs pour déboguer la production nulle
            total_production = monthly_results_df['Production_kWh'].sum()
            total_autoconsumption = monthly_results_df['Autoconsommation_kWh'].sum()
            total_consumption = monthly_results_df['Consommation_kWh'].sum()
            logger.info(f"CORE DEBUG - Production totale: {total_production:.2f} kWh")
            logger.info(f"CORE DEBUG - Consommation totale: {total_consumption:.2f} kWh")
            logger.info(f"CORE DEBUG - Autoconsommation totale: {total_autoconsumption:.2f} kWh")
            
            # Vérifier hourly_data_to_return
            if hourly_data_to_return.empty:
                logger.error("CORE DEBUG - hourly_data_to_return est VIDE!")
            else:
                logger.info(f"CORE DEBUG - hourly_data_to_return: Shape={hourly_data_to_return.shape}, Colonnes={hourly_data_to_return.columns.tolist()}")
                total_prod_hourly = hourly_data_to_return['production_kwh'].sum() if 'production_kwh' in hourly_data_to_return.columns else 0.0
                logger.info(f"CORE DEBUG - Somme production dans hourly_data_to_return: {total_prod_hourly:.2f} kWh")
                if total_prod_hourly < 1.0:
                    logger.error(f"⚠️ ALERTE CRITIQUE: Production totale quasi nulle ({total_prod_hourly:.2f}) dans hourly_data_to_return!")
                    # Afficher plus de détails sur les sites et données source
                    logger.info(f"CORE DEBUG - Sites disponibles: {list(self.sites_data.keys())}")
                    for site_id, site_df in self.sites_data.items():
                        if not site_df.empty and 'production_kwh' in site_df.columns:
                            prod_sum_site = site_df['production_kwh'].sum()
                            logger.info(f"CORE DEBUG - Site {site_id}: Somme production={prod_sum_site:.2f} kWh")
            
            # Vérifier reference_data_ts
            if reference_data_ts.empty:
                logger.error("CORE DEBUG - reference_data_ts est VIDE!")
            else:
                logger.info(f"CORE DEBUG - reference_data_ts: Shape={reference_data_ts.shape}, Colonnes={reference_data_ts.columns.tolist()}")
                total_prod_ref = reference_data_ts['production_kwh'].sum() if 'production_kwh' in reference_data_ts.columns else 0.0
                logger.info(f"CORE DEBUG - Somme production dans reference_data_ts: {total_prod_ref:.2f} kWh")
                if total_prod_ref < 1.0:
                    logger.error(f"⚠️ ALERTE CRITIQUE: Production totale quasi nulle ({total_prod_ref:.2f}) dans reference_data_ts!")
            
            # MODIFICATION 2: Utilisation de la fonction importée pour DSCR et LCOE
            avg_dscr = calculate_avg_dscr_revised(monthly_results_df, tax_rate_decimal) if loan_active else np.nan
            lcoe = calculate_lcoe_engineering(wacc_monthly_at, monthly_results_df, terminal_value_net_projet)
            # FIN MODIFICATION 2
            
            total_production = monthly_results_df['Production_kWh'].sum()
            total_autoconsumption = monthly_results_df['Autoconsommation_kWh'].sum()
            total_consumption = monthly_results_df['Consommation_kWh'].sum()
            autoconsumption_rate = total_autoconsumption / total_consumption if total_consumption > 1e-6 else 0.0
            autoproduction_rate = total_autoconsumption / total_production if total_production > 1e-6 else 0.0

            # Assemblage des résultats
            results = {
                "scenario": scenario_name, 
                "prix_revente": prix_vente_final_a_utiliser,
                "source_parametres_simulation": source_des_inputs,
                "capex_base_utilise": capex_base_input,
                "opex_base_utilise_maintenance_annuel": total_opex_maintenance_base_annual,
                "opex_base_utilise_assurance_annuel": total_opex_assurance_base_annual,
                "opex_base_utilise_admin_annuel": total_opex_admin_base_annual,
                "opex_base_utilise_total_hors_onduleur": (total_opex_maintenance_base_annual + total_opex_assurance_base_annual + total_opex_admin_base_annual),
                "puissance_base_utilisee": puissance_kwc_global,
                "capex_scenario_simule_initial": capex_scenario_simule,
                "capex_scenario_final_utilise": capex_brut_total_scenario,
                "capex_net_subvention_final": capex_net_subvention,
                "subvention_finale_retenue_pour_calculs": subvention_finale_pour_calculs,
                "opex_scenario_maintenance_annuel_simule": opex_maintenance_scenario_annual,
                "opex_scenario_assurance_annuel_simule": opex_assurance_scenario_annual,
                "opex_scenario_admin_annuel_simule": opex_admin_scenario_annual,
                "opex_scenario_total_hors_onduleur_simule": (opex_maintenance_scenario_annual + opex_assurance_scenario_annual + opex_admin_scenario_annual),
                "debt_amount": debt_amount, 
                "total_subvention": subvention_finale_pour_calculs,
                "net_equity_investment": net_equity_investment, 
                "tva_sur_capex_initial_pour_fcfe_t0": tva_sur_capex_initial,
                "autoconsumption_rate": autoconsumption_rate, 
                "autoproduction_rate": autoproduction_rate,
                "wacc_after_tax_annual": wacc_annual_at / 100.0 if pd.notna(wacc_annual_at) else np.nan,
                "cost_of_equity_annual": re_annual / 100.0 if pd.notna(re_annual) else np.nan,
                "wacc_after_tax_annual_pct_calculated": wacc_annual_at,  # Nouvelle clé: WACC en % pour débogage
                "cost_of_equity_annual_pct_input": re_annual,  # Nouvelle clé: coût des FP en % pour débogage
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

    # MODIFICATION: Les méthodes calculate_lcoe_engineering et calculate_avg_dscr_revised
    # sont maintenant importées et ne doivent plus être définies ici.
    # SUPPRIMER les définitions de self.calculate_lcoe_engineering et self.calculate_avg_dscr_revised
    # qui étaient présentes dans l'ancien analysis_engine.py

    def simulate_selling_price(self,
                               scenario_name: str,
                               target_irr: float | None = None,
                               target_npv: float | None = None,
                               override_source_prix_autoconso: str | None = None,
                               sites_config: dict | None = None
                              ) -> dict | None:
        # La logique de cette méthode reste la même, elle appelle self.calculate_financial_indicators
        # qui est maintenant refactorisée.
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
                if target_val_brentq is None : return np.nan
                return actual_metric_value - target_val_brentq

            try:
                val_min_bound = objective_for_brentq(prix_min_recherche)
                val_max_bound = objective_for_brentq(prix_max_recherche)
                if pd.notna(val_min_bound) and pd.notna(val_max_bound) and (np.sign(val_min_bound) * np.sign(val_max_bound) <= 0):
                    optimal_price_found = brentq(objective_for_brentq, prix_min_recherche, prix_max_recherche, xtol=1e-7, rtol=1e-7, maxiter=150)
                else: logger.warning(f"SIMULATE PRICE: Brentq - no sign change or NaN (Min={val_min_bound}, Max={val_max_bound}).")
            except Exception as e_brentq: logger.error(f"SIMULATE PRICE: Erreur brentq : {e_brentq}.")

            if optimal_price_found is None:
                simulation_cache.clear()
                def objective_for_minimize(price_array):
                    price_candidate = float(price_array[0])
                    if not (prix_min_recherche <= price_candidate <= prix_max_recherche): return 1e12
                    actual_metric_value = get_target_metric_value(price_candidate)
                    if not (pd.notna(actual_metric_value) and np.isfinite(actual_metric_value)): return 1e10
                    target_val_minimize = target_irr if target_irr is not None else target_npv
                    if target_val_minimize is None: return 1e11
                    return (actual_metric_value - target_val_minimize)**2

                initial_guess = max(prix_min_recherche, min(prix_max_recherche, (prix_min_recherche + prix_max_recherche) / 2.0))
                methods_to_try = [('L-BFGS-B', {'ftol': 1e-10, 'gtol': 1e-8, 'maxiter': 200}), ('Nelder-Mead', {'xatol': 1e-7, 'fatol': 1e-9, 'maxiter': 300}), ('SLSQP', {'ftol': 1e-9, 'maxiter': 150})]
                best_res_minimize = None
                for method_name, options in methods_to_try:
                    logger.info(f"SIMULATE PRICE: Tentative avec minimize ({method_name})...")
                    simulation_cache.clear()
                    current_bounds = [(prix_min_recherche, prix_max_recherche)] if method_name != 'Nelder-Mead' else None
                    res_minimize_current = minimize(objective_for_minimize, [initial_guess], method=method_name, bounds=current_bounds, options=options)
                    if res_minimize_current.success and abs(res_minimize_current.fun) < 1e-7:
                        optimal_price_found = res_minimize_current.x[0]; break
                    elif best_res_minimize is None or (res_minimize_current.success and 'fun' in res_minimize_current and res_minimize_current.fun < best_res_minimize.fun):
                        best_res_minimize = res_minimize_current
                if optimal_price_found is None and best_res_minimize is not None and best_res_minimize.success:
                    optimal_price_found = best_res_minimize.x[0]

            if optimal_price_found is None: raise RuntimeError("Aucun prix optimal déterminé après toutes les tentatives.")
            optimal_price_found = max(prix_min_recherche, min(prix_max_recherche, optimal_price_found))

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
                error_msg = final_results_with_optimal_price.get("error", "Calcul final échoué") if isinstance(final_results_with_optimal_price, dict) else "Calcul final échoué"
                raise RuntimeError(f"Échec recalcul final avec prix {optimal_price_found:.8f}: {error_msg}")
        except Exception as e:
            logger.error(f"ERREUR FATALE (simulate_selling_price): {e}", exc_info=True)
            return {"error": str(e)}