# modules/analysis_engine.py (Version Corrigée et Complète - Intégrant Multi-Site & Provision Onduleur par Site)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import traceback
import sys
import copy
from scipy.optimize import minimize, brentq

# --- Gestion de la dépendance à numpy_financial ---
try:
    import numpy_financial as npf
    NPF_IS_REAL = True
except ImportError:
    NPF_IS_REAL = False
    print("AVERTISSEMENT MOTEUR: numpy_financial non trouvé. Fonctions secours utilisées.")
    # Définition des fonctions secours (identiques à votre code)
    def secours_npv(rate, values):
        values = np.asarray(values)
        if abs(rate - (-1.0)) < 1e-9:
            if len(values) > 1 and np.any(values[1:] != 0): return float('-inf')
            elif len(values) > 0: return values[0]
            else: return 0.0
        if rate < -1.0:
            print(f"AVERTISSEMENT NPV: Taux {rate:.4f} <= -1, NPV non défini, retour -inf.")
            return float('-inf')
        with np.errstate(over='raise', invalid='raise'):
            try:
                discount_factors = (1 + rate) ** np.arange(len(values))
                if np.any(np.isclose(discount_factors, 0)): return np.nan
                pv = values / discount_factors
                if not np.all(np.isfinite(pv)): return np.nan
                return np.sum(pv)
            except (FloatingPointError, OverflowError) as e_fp: return np.nan
            except Exception as e_npv: return np.nan

    def secours_irr(values, guess=0.1):
        print("ERREUR MOTEUR: Fonction secours_irr non implémentée! Utilisez numpy_financial.")
        return np.nan

    class NpfModule:
        @staticmethod
        def npv(rate, values): return secours_npv(rate, values)
        @staticmethod
        def irr(values): return secours_irr(values)
    npf = NpfModule()
# --- Fin Gestion numpy_financial ---

# --- NOUVEL IMPORT ---
try:
    from . import tax_engine # Import relatif si dans le même dossier 'modules'
except ImportError:
     # Fallback si la structure est différente ou pour tests directs
     try:
          import tax_engine
     except ImportError:
          print("ERREUR MOTEUR: Impossible d'importer le module tax_engine.")
          # Optionnel: définir des fonctions secours pour éviter de planter ?
          # Ou laisser planter pour signaler le problème.
          raise
# --- FIN NOUVEL IMPORT ---

# --- Import des constantes globales si nécessaire (ex: TURPE) ---
try:
    # Assurez-vous que ce chemin est correct par rapport à analysis_engine.py
    from modules.config import TURPE_PROD_RATES
except ImportError:
    print("ERREUR MOTEUR: Impossible d'importer TURPE_PROD_RATES depuis config.py")
    TURPE_PROD_RATES = {} # Structure vide pour éviter crash, mais calcul TURPE sera faux
# --- Fin Import ---


class AnalysisEngine:
    """Moteur de calcul économique pur pour l'optimisation de l'autoconsommation collective."""

    def __init__(self, config: dict, scenarios: dict, sites_data: dict[str, pd.DataFrame]):
        """Initialise le moteur avec les données et configurations nécessaires."""
        # --- Validation des entrées (inchangée) ---
        if not isinstance(config, dict): raise TypeError("config doit être un dict")
        if not isinstance(scenarios, dict): raise TypeError("scenarios doit être un dict")
        if not isinstance(sites_data, dict): raise TypeError("sites_data doit être un dict")
        if not sites_data: raise ValueError("sites_data ne peut pas être vide")
        required_cols = ['Temps', 'production_kwh', 'consumption_kwh']
        for site_id, df in sites_data.items():
            if not isinstance(df, pd.DataFrame): raise TypeError(f"Site '{site_id}' n'est pas un DataFrame")
            if df.empty: print(f"AVERTISSEMENT MOTEUR INIT: DataFrame site '{site_id}' vide.")
            if 'Temps' not in df.columns: raise ValueError(f"Colonne 'Temps' manquante site '{site_id}'")
            try: pd.to_datetime(df['Temps'], errors='raise')
            except Exception as e_time: raise ValueError(f"Colonne 'Temps' invalide site '{site_id}': {e_time}") from e_time
            for col in ['production_kwh', 'consumption_kwh']:
                 if col not in df.columns: raise ValueError(f"Colonne '{col}' manquante site '{site_id}'")
                 if not pd.api.types.is_numeric_dtype(df[col]):
                     try: pd.to_numeric(df[col], errors='raise')
                     except Exception as e_num: raise ValueError(f"Colonne '{col}' non numérique site '{site_id}': {e_num}") from e_num
        # --- Fin Validation ---

        self.config = config
        self.scenarios = scenarios
        self.sites_data = sites_data
        self.npf_available = NPF_IS_REAL
        self.used_aggregated_config = False # Flag pour traçabilité

    def calculate_wacc(self, debt_ratio, taux_interet_dette_pct, taux_imposition_pct, cout_fonds_propres_pct) -> float | None:
        """Calcule le WACC."""
        # --- Code Inchangé (Identique à votre version) ---
        try:
            rd = float(taux_interet_dette_pct) / 100.0; tc = float(taux_imposition_pct) / 100.0
            re = float(cout_fonds_propres_pct) / 100.0; dr = float(debt_ratio)
            if not (0 <= dr <= 1): raise ValueError("Debt ratio [0, 1]")
            if not (0 <= tc < 1): raise ValueError("Taux imposition [0, 100[")
            if rd < 0 or re < 0: raise ValueError("Taux négatifs invalides")
            cout_dette_apres_impots = rd * (1.0 - tc); equity_ratio = 1.0 - dr
            wacc = (dr * cout_dette_apres_impots) + (equity_ratio * re)
            if not np.isfinite(wacc): print(f"AVERTISSEMENT WACC: WACC non fini ({wacc})"); return None
            return wacc
        except (TypeError, ValueError) as e: print(f"ERREUR MOTEUR (calculate_wacc): {e}"); return None
        except Exception as e: print(f"ERREUR INATTENDUE (calculate_wacc): {e}"); return None

    # --- === calculate_financial_indicators (REMPLACÉE) === ---
    def calculate_financial_indicators(self,
                                       scenario_name: str,
                                       prix_revente: float | None = None,
                                       override_source_prix_autoconso: str | None = None,
                                       sites_config: dict | None = None) -> dict | None:
        """
        Calcule les indicateurs financiers pour un scénario donné SUR UNE BASE MENSUELLE.
        Utilise la logique fiscale avancée de tax_engine.
        """
        start_time_calc = time.time()
        print(f"MOTEUR (Mensuel): Lancement calcul indicateurs pour '{scenario_name}'...")
        self.used_aggregated_config = False

        try:
            # --- 1. Récupération Config Globale et Scénario ---
            if scenario_name not in self.scenarios: raise ValueError(f"Scénario '{scenario_name}' invalide.")
            scenario = self.scenarios[scenario_name]
            global_config = self.config # Config globale

            # --- 2. Agrégation/Détermination des Paramètres de BASE ---
            total_capex_base = 0.0
            total_opex_base = 0.0 # OPEX base TOTAL (sera somme des détails)
            total_puissance_kwc = 0.0
            inverter_configs = []
            source_des_inputs = "globaux" # Sera écrasé si sites_config utilisé
            self.used_aggregated_config = False # Suivi de la source utilisée

            if sites_config and isinstance(sites_config, dict) and sites_config:
                print("MOTEUR: Utilisation de la configuration par site (sites_config). Agrégation...")
                self.used_aggregated_config = True
                source_des_inputs = "agreges_par_site"

                for site_id, site_cfg in sites_config.items():
                    if not isinstance(site_cfg, dict): continue

                    site_power = float(site_cfg.get('puissance_kwc', 0.0))
                    site_capex = float(site_cfg.get('capex', 0.0))
                    site_type = site_cfg.get('site_type', 'Producteur')

                    site_opex_annual_base_detail = 0.0
                    if site_type != "Consommateur Pur":
                        site_opex_annual_base_detail += float(site_cfg.get('opex_maintenance', 0.0))
                        site_opex_annual_base_detail += float(site_cfg.get('opex_insurance', 0.0))
                        site_opex_annual_base_detail += float(site_cfg.get('opex_admin', 0.0))

                    site_prov_enabled = site_cfg.get("opex_onduleur_provision_site", False)
                    site_prov_total_cost = float(site_cfg.get("opex_onduleur_total_cost_site", 0.0))
                    site_prov_lifetime = int(site_cfg.get("opex_onduleur_lifetime_site", 0))

                    total_puissance_kwc += site_power
                    total_capex_base += site_capex
                    total_opex_base += site_opex_annual_base_detail

                    if site_prov_enabled and site_power > 0 and site_prov_total_cost > 0 and site_prov_lifetime > 0:
                         inverter_configs.append({
                             "total_cost": site_prov_total_cost,
                             "lifetime_years": site_prov_lifetime
                         })

                print(f"MOTEUR: Totaux Agrégés: CAPEX={total_capex_base:,.2f}€, OPEX_base_détaillé={total_opex_base:,.2f}€/an, P_totale={total_puissance_kwc:.2f}kWc")
                capex_base = total_capex_base
                opex_annual_base_config = total_opex_base
                puissance_kwc_global = total_puissance_kwc

            else: # Utilisation config globale (fallback)
                print("MOTEUR: Utilisation de la configuration globale (pas de sites_config ou vide). L'OPEX détaillé ne sera pas utilisé.")
                source_des_inputs = "globaux"
                self.used_aggregated_config = False
                capex_base = float(global_config.get("capex", 0.0))
                opex_annual_base_config = float(global_config.get("opex_global_fallback", 0.0))
                puissance_kwc_global = float(global_config.get("puissance_kwc", 0.0))
                if global_config.get("opex_onduleur_provision", False):
                    global_inv_cost_per_kwc = float(global_config.get('opex_onduleur_cost', 0.0))
                    global_inv_lifetime = int(global_config.get('opex_onduleur_lifetime', 0))
                    if puissance_kwc_global > 0 and global_inv_cost_per_kwc > 0 and global_inv_lifetime > 0:
                         inverter_configs.append({
                             "total_cost": global_inv_cost_per_kwc * puissance_kwc_global,
                             "lifetime_years": global_inv_lifetime
                         })


            # --- 3. Validation/Conversion Paramètres Globaux Restants ---
            try:
                start_date_ppa_str = global_config["date_debut_ppa"]
                start_date_ppa = pd.to_datetime(start_date_ppa_str)
                num_months_simulation = int(global_config["duree_ppa"])
                simulation_years = num_months_simulation // 12
                degradation_rate_base = float(global_config["degradation_rate"])
                taux_inflation_pct = float(global_config["taux_inflation"])
                adjusted_inflation_annual = taux_inflation_pct / 100.0
                oa_indexed = bool(global_config["tarif_oa_indexe_inflation"])
                inflation_rate_oa_pct = float(global_config.get("taux_inflation_tarif_oa", 1.5))
                inflation_rate_oa_annual = inflation_rate_oa_pct / 100.0
                turpe_indexed = bool(global_config.get("turpe_indexe_inflation", False))
                taux_imposition_standard_pct = float(global_config.get("taux_imposition", 25.0))
                tax_engine.STANDARD_TAX_RATE = taux_imposition_standard_pct / 100.0
                amortissement_duree_years = int(global_config["amortissement_duree"])
                valeur_residuelle_pct_config = float(global_config.get("valeur_residuelle_pct", 0.0)) / 100.0
                cout_demantelement_pct_config = float(global_config.get("cout_demantelement_pct", 0.0)) / 100.0
                cout_fonds_propres_pct_config = float(global_config.get("cout_fonds_propres", 8.0))
                loan_active = global_config.get("with_loan", True)
                debt_ratio_config = float(global_config.get("debt_ratio", 0.80)) if loan_active else 0.0
                debt_term_years_config = int(global_config.get("debt_term_years", 15)) if loan_active else 0
                taux_interet_dette_pct_config = float(global_config.get("taux_interet_dette", 4.0)) if loan_active else 0.0
                taux_interet_dette_annual = taux_interet_dette_pct_config / 100.0
                source_prix_autoc_config = global_config.get("source_prix_autoconso", "prix_initial")
                prix_vente_initial_config = float(global_config.get("prix_vente_initial", 0.15))
                tarif_edf_ref_config = float(global_config["tarif_edf_reference"])
                sub_rates = {k: float(global_config.get(f"subvention_rate_{k}", 0.0)) for k in ['le3','le9','le36','le100','gt100']}

                t_oa_le9 = float(global_config.get("tarif_oa_bracket_le9", 0.0400))
                t_oa_le100 = float(global_config.get("tarif_oa_bracket_le100", 0.0761))
                t_oa_gt100 = float(global_config.get("tarif_oa_bracket_gt100", 0.0600))
                if puissance_kwc_global <= 9: tarif_oa_base = t_oa_le9
                elif puissance_kwc_global <= 100: tarif_oa_base = t_oa_le100
                else: tarif_oa_base = t_oa_gt100
                print(f"MOTEUR: Tarif OA base calculé: {tarif_oa_base:.4f} €/kWh (P={puissance_kwc_global:.2f} kWc)")
                turpe_prod_tension = global_config.get("turpe_prod_tension", "BT<=36kVA")
                turpe_prod_contrat = global_config.get("turpe_prod_contrat", "Unique")
                if not TURPE_PROD_RATES: raise ValueError("TURPE_PROD_RATES non chargé/défini.")
                cg_rate = TURPE_PROD_RATES.get(turpe_prod_tension, {}).get("CG", {}).get(turpe_prod_contrat, 0.0)
                cc_keys = list(TURPE_PROD_RATES.get(turpe_prod_tension, {}).get("CC", {}).keys()); cc_key = cc_keys[0] if cc_keys else None
                cc_rate = TURPE_PROD_RATES.get(turpe_prod_tension, {}).get("CC", {}).get(cc_key, 0.0) if cc_key else 0.0
                turpe_annual_base_config = cg_rate + cc_rate
                print(f"MOTEUR: TURPE base recalculée: {turpe_annual_base_config:.2f} €/an (P={puissance_kwc_global:.2f} kWc, Tension={turpe_prod_tension})")

            except (ValueError, TypeError, KeyError, ImportError) as e:
                raise ValueError(f"Erreur lecture/conversion config globale: {e}") from e

            # --- 4. Application Modificateurs Scénario ---
            capex_scenario = capex_base * float(scenario.get("capex_modifier", 1.0))
            opex_annual_base = opex_annual_base_config * float(scenario.get("opex_modifier", 1.0))
            turpe_annual_base = turpe_annual_base_config # Base TURPE (pas de modificateur spécifique pour l'instant)
            adjusted_inflation_scenario = adjusted_inflation_annual * float(scenario.get("inflation_modifier", 1.0))
            degradation_rate_scenario = degradation_rate_base * float(scenario.get("degradation_modifier", 1.0))
            production_modifier_scenario = float(scenario.get("production_modifier", 1.0))


            # --- 5. Déterminer Prix/Source à Utiliser ---
            prix_vente_a_utiliser = float(prix_revente) if prix_revente is not None else prix_vente_initial_config
            source_prix_autoc = override_source_prix_autoconso if override_source_prix_autoconso is not None else source_prix_autoc_config


            # --- 6. Agrégation Données Énergétiques ---
            if not self.sites_data: raise ValueError("Aucune donnée de site disponible.")
            all_dfs = list(self.sites_data.values())
            if not all_dfs: raise ValueError("Dictionnaire sites_data vide.")
            min_date = min(df['Temps'].min() for df in all_dfs if not df.empty)
            max_date = max(df['Temps'].max() for df in all_dfs if not df.empty)
            freq = 'H'; first_df = all_dfs[0]; inferred_freq = pd.infer_freq(first_df['Temps'].sort_values())
            if inferred_freq: freq = inferred_freq
            else:
                 time_diffs = first_df['Temps'].sort_values().diff().dropna()
                 if not time_diffs.empty: median_diff = time_diffs.median(); offset_freq = pd.tseries.frequencies.to_offset(median_diff); freq = offset_freq if offset_freq else freq
            common_index = pd.date_range(start=min_date, end=max_date, freq=freq)
            data_agg = pd.DataFrame(0.0, index=common_index, columns=['production_kwh', 'consumption_kwh'])
            for site_id, df_site in self.sites_data.items():
                if df_site.empty: continue
                site_specific_config = sites_config.get(site_id, {}) if sites_config else {}
                site_type = site_specific_config.get('site_type', 'Producteur')
                df_temp = df_site.set_index('Temps'); df_temp.index = pd.to_datetime(df_temp.index)
                if df_temp.index.has_duplicates: df_temp = df_temp.groupby(df_temp.index).sum()
                cols_to_add = ['consumption_kwh']
                if site_type != "Consommateur Pur":
                    if 'production_kwh' in df_temp.columns: cols_to_add.append('production_kwh')
                    else: print(f"AVERTISSEMENT MOTEUR Agg: Colonne 'production_kwh' manquante site producteur '{site_id}'.")
                existing_cols_to_add = [col for col in cols_to_add if col in df_temp.columns]
                if not existing_cols_to_add: print(f"AVERTISSEMENT MOTEUR Agg: Aucune colonne énergétique valide site '{site_id}'."); continue
                try: data_agg = data_agg.add(df_temp[existing_cols_to_add].reindex(common_index, fill_value=0.0), fill_value=0.0)
                except Exception as e_agg: print(f"ERREUR MOTEUR Agg: Erreur site {site_id}: {e_agg}")
            data_agg = data_agg.reset_index().rename(columns={'index': 'Temps'})
            if data_agg.empty: raise ValueError("Données agrégées vides après traitement.")
            print(f"MOTEUR (Mensuel): Données énergétiques agrégées (selon type site) prêtes ({len(data_agg)} lignes).")

            # --- AJOUTER L'ASSIGNATION ICI ---
            hourly_data_to_return = data_agg.copy()
            # ---------------------------------

            # --- 7. Préparation Structure Mensuelle (Ajouter Tax_Payment) ---
            monthly_index = pd.date_range(start=start_date_ppa, periods=num_months_simulation, freq='ME')
            monthly_results_df = pd.DataFrame(index=monthly_index)
            monthly_cols = [
                'Year_Index', 'Sim_Year', 'Inflation_Factor', 'Degradation_Factor',
                'Production_kWh', 'Consommation_kWh', 'Autoconsommation_kWh', 'Surplus_kWh',
                'Tarif_OA_Annuel', 'Prix_Autoconso_Annuel',
                'Revenus_Surplus', 'Revenus_Autoconsommation', 'Revenus_Total',
                'OPEX', 'TURPE', 'Amortissement', 'EBITDA', 'EBIT',
                'Interets_Payes', 'Principal_Rembourse', 'EBT',
                'Tax_Payment',
                'Resultat_Net', 'FCFE', 'OCF_Projet',
                'Solde_Dette_Fin_Mois', 'Service_Dette'
            ]
            for col in monthly_cols: monthly_results_df[col] = 0.0

            # --- 8. Calculs Préliminaires Annuels/Globaux ---
            applicable_sub_rate = 0.0
            if puissance_kwc_global <= 3: applicable_sub_rate = sub_rates['le3']
            elif puissance_kwc_global <= 9: applicable_sub_rate = sub_rates['le9']
            elif puissance_kwc_global <= 36: applicable_sub_rate = sub_rates['le36']
            elif puissance_kwc_global <= 100: applicable_sub_rate = sub_rates['le100']
            else: applicable_sub_rate = sub_rates['gt100']
            total_subvention = applicable_sub_rate * puissance_kwc_global
            capex_net_subvention = max(0, capex_scenario - total_subvention)
            debt_amount = capex_net_subvention * debt_ratio_config if loan_active else 0.0
            equity_amount = capex_net_subvention * (1.0 - debt_ratio_config)
            net_equity_investment = equity_amount
            if loan_active and debt_amount > 1e-6:
                monthly_interest_paid, monthly_principal_paid, monthly_debt_balance = self.calculate_monthly_loan_schedule(
                    debt_amount, taux_interet_dette_annual, debt_term_years_config, num_months_simulation
                )
            else:
                zeros_array = np.zeros(num_months_simulation)
                monthly_interest_paid, monthly_principal_paid, monthly_debt_balance = zeros_array.copy(), zeros_array.copy(), zeros_array.copy()
            base_amortissable = capex_net_subvention * (1 - valeur_residuelle_pct_config)
            annual_depreciation_base = base_amortissable / amortissement_duree_years if amortissement_duree_years > 0 else 0.0


            # --- Préparation données référence ---
            if not isinstance(data_agg.index, pd.DatetimeIndex): data_agg = data_agg.set_index('Temps')
            if data_agg.empty: ref_year = start_date_ppa.year
            else: ref_year = data_agg.index.year.min()
            reference_data_ts = data_agg[data_agg.index.year == ref_year].copy()
            if reference_data_ts.empty: print(f"AVERTISSEMENT: Pas de données réf pour année {ref_year}.")


            # --- 9. Boucle Mensuelle Principale (MODIFIÉE pour Impôts et FCFE) ---
            loss_carryforward_balance = 0.0
            annual_tax_calculated_prev_year = 0.0
            current_quarterly_acompte = 0.0
            current_year_tracker = -1

            # Initialisation An 1
            inflation_factor_year = 1.0
            degradation_factor_year = 1.0
            opex_base_current_year = opex_annual_base
            turpe_current_year = turpe_annual_base
            depreciation_current_year = annual_depreciation_base if 0 < amortissement_duree_years else 0.0
            current_oa_rate_annual = tarif_oa_base
            if source_prix_autoc == 'prix_initial': current_prix_autoc_annual = prix_vente_a_utiliser
            elif source_prix_autoc == 'tarif_edf': current_prix_autoc_annual = tarif_edf_ref_config
            elif source_prix_autoc == 'tarif_oa': current_prix_autoc_annual = current_oa_rate_annual
            else: current_prix_autoc_annual = prix_vente_a_utiliser

            for month_idx in range(num_months_simulation):
                current_month_end_date = monthly_index[month_idx]
                year_idx = current_month_end_date.year - start_date_ppa.year
                simulation_year = year_idx + 1
                monthly_results_df.loc[current_month_end_date, 'Year_Index'] = year_idx
                monthly_results_df.loc[current_month_end_date, 'Sim_Year'] = simulation_year

                is_new_year = (current_month_end_date.year != current_year_tracker)
                if is_new_year:
                    # --- NOUVELLE LOGIQUE FISCALE ANNUELLE ---
                    if year_idx > 0: # Calcul pour l'année N-1 (terminée)
                        last_full_year_date = current_year_tracker
                        ebt_last_year_monthly = monthly_results_df.loc[monthly_results_df.index.year == last_full_year_date, 'EBT']
                        ebt_last_year_sum = ebt_last_year_monthly.sum() if not ebt_last_year_monthly.empty else 0.0
                        taxable_ebt_last_year, loss_carryforward_balance = tax_engine.apply_loss_carryforward_cap(
                            ebt_before_loss=ebt_last_year_sum,
                            loss_carryforward_balance=loss_carryforward_balance
                        )
                        annual_tax_calculated_prev_year = tax_engine.calculate_corporate_tax_pme(
                            taxable_ebt=taxable_ebt_last_year
                        )
                        current_quarterly_acompte = tax_engine.calculate_quarterly_installment(
                            previous_year_tax=annual_tax_calculated_prev_year
                        )
                    else: # Première année
                        annual_tax_calculated_prev_year = 0.0
                        current_quarterly_acompte = 0.0
                    # -------------------------------------
                    current_year_tracker = current_month_end_date.year

                    # --- Recalcul Coûts/Facteurs Annuels (si pas an 1) ---
                    if year_idx > 0:
                        inflation_factor_year = (1 + adjusted_inflation_scenario) ** year_idx
                        degradation_factor_year = (1 - degradation_rate_scenario) ** year_idx
                        opex_base_current_year = opex_annual_base * inflation_factor_year
                        turpe_current_year = turpe_annual_base * (inflation_factor_year if turpe_indexed else 1.0)
                        depreciation_current_year = annual_depreciation_base if year_idx < amortissement_duree_years else 0.0
                        current_oa_rate_annual = tarif_oa_base * ((1 + inflation_rate_oa_annual)**year_idx if oa_indexed else 1.0)
                        if source_prix_autoc == 'prix_initial': current_prix_autoc_annual = prix_vente_a_utiliser * inflation_factor_year
                        elif source_prix_autoc == 'tarif_edf': current_prix_autoc_annual = tarif_edf_ref_config * inflation_factor_year
                        elif source_prix_autoc == 'tarif_oa': current_prix_autoc_annual = current_oa_rate_annual
                        else: current_prix_autoc_annual = prix_vente_a_utiliser * inflation_factor_year

                # --- Calcul Provision Onduleur Annuelle Totale ---
                total_annual_inverter_provision = 0.0
                for inv_cfg in inverter_configs:
                     if simulation_year > 0 and inv_cfg["lifetime_years"] > 0 and simulation_year % inv_cfg["lifetime_years"] == 0:
                         cost_this_replacement = inv_cfg["total_cost"]
                         cost_this_replacement_indexed = cost_this_replacement * inflation_factor_year
                         total_annual_inverter_provision += cost_this_replacement_indexed


                # --- Stocker facteurs ---
                monthly_results_df.loc[current_month_end_date, 'Inflation_Factor'] = inflation_factor_year
                monthly_results_df.loc[current_month_end_date, 'Degradation_Factor'] = degradation_factor_year
                monthly_results_df.loc[current_month_end_date, 'Tarif_OA_Annuel'] = current_oa_rate_annual
                monthly_results_df.loc[current_month_end_date, 'Prix_Autoconso_Annuel'] = current_prix_autoc_annual

                # --- Allocation Mensuelle Coûts (OPEX, TURPE, Amort) ---
                opex_total_current_year = opex_base_current_year + total_annual_inverter_provision
                monthly_results_df.loc[current_month_end_date, 'OPEX'] = opex_total_current_year / 12.0
                monthly_results_df.loc[current_month_end_date, 'TURPE'] = turpe_current_year / 12.0
                monthly_results_df.loc[current_month_end_date, 'Amortissement'] = depreciation_current_year / 12.0

                # --- Calcul Paiement Impôt Trimestriel ---
                tax_payment_this_month = 0.0
                payment_months = [3, 6, 9, 12]
                if current_month_end_date.month in payment_months and simulation_year > 1:
                    tax_payment_this_month = current_quarterly_acompte
                monthly_results_df.loc[current_month_end_date, 'Tax_Payment'] = tax_payment_this_month

                # --- Calcul Énergie Mensuelle ---
                sim_month = current_month_end_date.month
                prod_month, cons_month, auto_month, surplus_month = 0.0, 0.0, 0.0, 0.0
                try:
                    ref_month_start = datetime(ref_year, sim_month, 1)
                    ref_month_end_day = pd.Timestamp(ref_month_start).days_in_month
                    ref_month_end = datetime(ref_year, sim_month, ref_month_end_day, 23, 59, 59)
                    if isinstance(reference_data_ts.index, pd.DatetimeIndex):
                        try: ref_monthly_energy_data = reference_data_ts.loc[ref_month_start:ref_month_end]
                        except KeyError: ref_monthly_energy_data = pd.DataFrame()
                    else: ref_monthly_energy_data = pd.DataFrame()
                    if not ref_monthly_energy_data.empty:
                        prod_ref = ref_monthly_energy_data.get('production_kwh', 0.0)
                        cons_ref = ref_monthly_energy_data.get('consumption_kwh', 0.0)
                        prod_adj = prod_ref * degradation_factor_year * production_modifier_scenario
                        prod_month = prod_adj.sum(); cons_month = cons_ref.sum()
                        auto_month = np.minimum(prod_adj, cons_ref).sum()
                        surplus_month = prod_month - auto_month
                except Exception as e_eng: print(f"Erreur Calcul Énergie mois {sim_month}: {e_eng}")
                monthly_results_df.loc[current_month_end_date, 'Production_kWh'] = prod_month
                monthly_results_df.loc[current_month_end_date, 'Consommation_kWh'] = cons_month
                monthly_results_df.loc[current_month_end_date, 'Autoconsommation_kWh'] = auto_month
                monthly_results_df.loc[current_month_end_date, 'Surplus_kWh'] = surplus_month

                # --- Calcul Revenus Mensuels ---
                revenue_surplus = surplus_month * current_oa_rate_annual
                revenue_autoconsommation = auto_month * current_prix_autoc_annual
                monthly_results_df.loc[current_month_end_date, 'Revenus_Surplus'] = revenue_surplus
                monthly_results_df.loc[current_month_end_date, 'Revenus_Autoconsommation'] = revenue_autoconsommation
                monthly_results_df.loc[current_month_end_date, 'Revenus_Total'] = revenue_surplus + revenue_autoconsommation

                # --- Calcul P&L Mensuel (Resultat Net = EBT) ---
                ebitda_mois = (monthly_results_df.loc[current_month_end_date, 'Revenus_Total']
                               - monthly_results_df.loc[current_month_end_date, 'OPEX']
                               - monthly_results_df.loc[current_month_end_date, 'TURPE'])
                monthly_results_df.loc[current_month_end_date, 'EBITDA'] = ebitda_mois
                ebit_mois = ebitda_mois - monthly_results_df.loc[current_month_end_date, 'Amortissement']
                monthly_results_df.loc[current_month_end_date, 'EBIT'] = ebit_mois
                interest_this_month = monthly_interest_paid[month_idx] if month_idx < len(monthly_interest_paid) else 0.0
                principal_this_month = monthly_principal_paid[month_idx] if month_idx < len(monthly_principal_paid) else 0.0
                monthly_results_df.loc[current_month_end_date, 'Interets_Payes'] = interest_this_month
                monthly_results_df.loc[current_month_end_date, 'Principal_Rembourse'] = principal_this_month
                ebt_mois = ebit_mois - interest_this_month
                monthly_results_df.loc[current_month_end_date, 'EBT'] = ebt_mois

                # --- NOUVEAU: Calcul Flux TVA Mensuels ---
                # Assurer que les revenus utilisés pour la TVA sont bien HT
                # Note: 'Revenus_Total' est déjà calculé HT plus haut
                revenus_ht_mois = monthly_results_df.loc[current_month_end_date, 'Revenus_Total']
                # Obtenir le taux de TVA standard (supposé pour l'instant)
                # Idéalement, ce taux devrait venir de la config
                vat_rate_decimal = tax_engine.STANDARD_TAX_RATE # Placeholder, à remplacer par un taux de TVA réel

                # Calcul TVA collectée (simplifié : sur tous revenus HT)
                vat_collectee_mois = revenus_ht_mois * vat_rate_decimal

                # Récupérer les charges HT du mois
                opex_ht_mois = monthly_results_df.loc[current_month_end_date, 'OPEX']
                turpe_ht_mois = monthly_results_df.loc[current_month_end_date, 'TURPE']

                # Calcul TVA déductible (simplifié : sur OPEX et TURPE HT)
                vat_deductible_opex_mois = opex_ht_mois * vat_rate_decimal
                vat_deductible_turpe_mois = turpe_ht_mois * vat_rate_decimal
                vat_deductible_total_mois = vat_deductible_opex_mois + vat_deductible_turpe_mois # Total déductible sur charges

                # Calcul TVA due pour le mois (Collectée - Déductible)
                vat_due_mois = vat_collectee_mois - vat_deductible_total_mois

                # Stocker les valeurs mensuelles calculées
                # S'assurer que les colonnes existent (on les ajoutera avant la boucle si besoin)
                monthly_results_df.loc[current_month_end_date, 'VAT_Collectee'] = vat_collectee_mois
                monthly_results_df.loc[current_month_end_date, 'VAT_Deductible_OPEX'] = vat_deductible_opex_mois
                monthly_results_df.loc[current_month_end_date, 'VAT_Deductible_TURPE'] = vat_deductible_turpe_mois
                monthly_results_df.loc[current_month_end_date, 'VAT_Due_Mois'] = vat_due_mois
                # La colonne 'VAT_Payment' sera remplie APRÈS la boucle

                # --- Suite du calcul P&L et Flux (Resultat_Net, FCFE, OCF_Projet) ---
                # Le calcul de Resultat_Net reste inchangé (base EBT).
                # Le calcul FCFE sera ajusté APRÈS la boucle une fois VAT_Payment connu.
                # Le calcul OCF_Projet reste inchangé (base EBITDA, Amort).

                resultat_net_mois = ebt_mois # Le paiement IS est traité dans le FCFE ci-dessous
                monthly_results_df.loc[current_month_end_date, 'Resultat_Net'] = resultat_net_mois

                # --- Calcul Flux Mensuels (FCFE Sera recalculé après la boucle) ---
                amortissement_mois = monthly_results_df.loc[current_month_end_date, 'Amortissement']
                principal_this_month = monthly_results_df.loc[current_month_end_date, 'Principal_Rembourse']
                tax_payment_this_month = monthly_results_df.loc[current_month_end_date, 'Tax_Payment']

                # Calcul FCFE PROVISOIRE (sera écrasé après la boucle)
                # Inclut l'impôt payé mais pas encore la TVA payée
                fcfe_mois_provisoire = (ebt_mois - tax_payment_this_month + amortissement_mois - principal_this_month)
                monthly_results_df.loc[current_month_end_date, 'FCFE'] = fcfe_mois_provisoire # Mettre une valeur temporaire

                # OCF Projet (inchangé ici)
                ocf_projet_mois = (ebitda_mois * (1.0 - tax_engine.STANDARD_TAX_RATE)) + (amortissement_mois * tax_engine.STANDARD_TAX_RATE)
                monthly_results_df.loc[current_month_end_date, 'OCF_Projet'] = ocf_projet_mois

                # Service Dette et Solde Dette (inchangé ici)
                service_dette_mois = interest_this_month + principal_this_month
                monthly_results_df.loc[current_month_end_date, 'Service_Dette'] = service_dette_mois
                debt_balance_this_month = monthly_debt_balance[month_idx] if month_idx < len(monthly_debt_balance) else 0.0
                monthly_results_df.loc[current_month_end_date, 'Solde_Dette_Fin_Mois'] = debt_balance_this_month
            # --- Fin Boucle Mensuelle ---
            print(f"MOTEUR (Mensuel): Fin boucle principale. Durée: {time.time() - start_time_calc:.3f} sec.")

            # --- NOUVEAU: Calcul Paiements Trimestriels TVA ---
            print("MOTEUR (Mensuel): Calcul des paiements trimestriels de TVA...")
            # S'assurer que la colonne existe et est initialisée à 0.0
            if 'VAT_Payment' not in monthly_results_df.columns:
                monthly_results_df['VAT_Payment'] = 0.0
            else:
                monthly_results_df['VAT_Payment'] = 0.0 # Réinitialiser

            # Ajouter les nouvelles colonnes TVA si elles n'existent pas (sécurité)
            for col in ['VAT_Collectee', 'VAT_Deductible_OPEX', 'VAT_Deductible_TURPE', 'VAT_Due_Mois']:
                if col not in monthly_results_df.columns:
                    monthly_results_df[col] = 0.0

            # Grouper par trimestre
            # Utiliser 'Q' pour trimestre finissant en Mar, Jun, Sep, Dec
            try: # Utiliser resample nécessite un index DatetimeIndex
                if not isinstance(monthly_results_df.index, pd.DatetimeIndex):
                     monthly_results_df.index = pd.to_datetime(monthly_results_df.index)
                quarterly_vat_due = monthly_results_df['VAT_Due_Mois'].resample('Q').sum()

                # Assigner le paiement au mois suivant la fin du trimestre
                for quarter_end_date, vat_sum_quarter in quarterly_vat_due.items():
                    # Déterminer le mois de paiement (mois suivant la fin du trimestre)
                    payment_month_date = quarter_end_date + pd.DateOffset(months=1)
                    # S'assurer que la date de paiement est dans l'index de la simulation
                    if payment_month_date in monthly_results_df.index:
                        monthly_results_df.loc[payment_month_date, 'VAT_Payment'] = vat_sum_quarter
                    # else: # Gérer cas où le paiement tombe hors simulation (rare si >= 1 an)
                    #     print(f"AVERTISSEMENT: Date paiement TVA {payment_month_date.strftime('%Y-%m')} hors simulation.")

            except AttributeError as e_resample:
                print(f"ERREUR MOTEUR (TVA Trim): Impossible de grouper par trimestre. L'index n'est probablement pas DatetimeIndex. {e_resample}")
                # Mettre les paiements à 0 pour éviter des erreurs plus loin
                monthly_results_df['VAT_Payment'] = 0.0
            except Exception as e_vat_trim:
                 print(f"ERREUR MOTEUR (TVA Trim): Erreur calcul paiements trimestriels : {e_vat_trim}")
                 monthly_results_df['VAT_Payment'] = 0.0


            print("MOTEUR (Mensuel): Paiements TVA calculés.")
            # --- FIN Calcul Paiements TVA ---

            # --- NOUVEAU: Recalcul FCFE pour inclure VAT_Payment ---
            print("MOTEUR (Mensuel): Recalcul du FCFE avec paiements TVA...")
            try:
                monthly_results_df['FCFE'] = (
                    monthly_results_df['EBT']
                    - monthly_results_df['Tax_Payment'] # IS effectivement payé
                    + monthly_results_df['Amortissement']
                    - monthly_results_df['Principal_Rembourse']
                    - monthly_results_df['VAT_Payment'] # TVA nette payée/reçue
                )
                print("MOTEUR (Mensuel): FCFE recalculé.")
            except KeyError as e_fcfe_recalc:
                print(f"ERREUR MOTEUR (FCFE Recalc): Colonne manquante pour recalcul FCFE: {e_fcfe_recalc}. FCFE reste inchangé.")
            except Exception as e_fcfe_recalc_gen:
                 print(f"ERREUR MOTEUR (FCFE Recalc): Erreur recalcul FCFE: {e_fcfe_recalc_gen}. FCFE reste inchangé.")
            # --- FIN Recalcul FCFE ---

            # --- 10. Calcul Indicateurs Scalaires Globaux (MODIFIER DSCR) ---
            fcfe_monthly_array = monthly_results_df['FCFE'].fillna(0).values
            equity_cash_flows_monthly = np.concatenate(([-net_equity_investment], fcfe_monthly_array))
            ocf_monthly_array = monthly_results_df['OCF_Projet'].fillna(0).values
            project_cash_flow_t0 = -capex_scenario
            if len(ocf_monthly_array) > 0:
                val_res = capex_net_subvention * valeur_residuelle_pct_config; cout_dem = capex_scenario * cout_demantelement_pct_config
                ocf_monthly_array[-1] += (val_res - cout_dem)
            project_cash_flows_monthly = np.concatenate(([project_cash_flow_t0], ocf_monthly_array))
            wacc_annual = self.calculate_wacc(debt_ratio_config, taux_interet_dette_pct_config, taux_imposition_standard_pct, cout_fonds_propres_pct_config)
            wacc_monthly = (1 + wacc_annual)**(1/12) - 1 if wacc_annual is not None and wacc_annual > -1.0 else None
            re_annual = cout_fonds_propres_pct_config / 100.0
            re_monthly = (1 + re_annual)**(1/12) - 1 if re_annual > -1.0 else None
            irr_equity = np.nan; npv_equity = np.nan
            if len(equity_cash_flows_monthly)>1 and np.any(equity_cash_flows_monthly):
                 try: irr_eq_raw = npf.irr(equity_cash_flows_monthly); irr_equity = (1 + irr_eq_raw)**12 - 1 if np.isfinite(irr_eq_raw) else np.nan
                 except: pass
            if re_monthly is not None and abs(1 + re_monthly) > 1e-12:
                 try: npv_equity = npf.npv(re_monthly, equity_cash_flows_monthly); npv_equity = npv_equity if np.isfinite(npv_equity) else np.nan
                 except: pass
            irr_project = np.nan; npv_project = np.nan
            if len(project_cash_flows_monthly)>1 and np.any(project_cash_flows_monthly):
                 try: irr_proj_raw = npf.irr(project_cash_flows_monthly); irr_project = (1 + irr_proj_raw)**12 - 1 if np.isfinite(irr_proj_raw) else np.nan
                 except: pass
            if wacc_monthly is not None and abs(1 + wacc_monthly) > 1e-12:
                 try: npv_project = npf.npv(wacc_monthly, project_cash_flows_monthly); npv_project = npv_project if np.isfinite(npv_project) else np.nan
                 except: pass
            roi_equity = npv_equity / net_equity_investment if np.isfinite(npv_equity) and abs(net_equity_investment) > 1e-9 else np.nan
            payback_equity_months = self.calculate_payback_months(equity_cash_flows_monthly)
            payback_equity_years = payback_equity_months / 12.0 if payback_equity_months is not None else np.nan
            payback_project_months = self.calculate_payback_months(project_cash_flows_monthly)
            payback_project_years = payback_project_months / 12.0 if payback_project_months is not None else np.nan
            lcoe = self.calculate_lcoe_monthly(wacc_monthly, capex_net_subvention, monthly_results_df)

            # Calcul DSCR Moyen Révisé
            avg_dscr = self.calculate_avg_dscr_revised(monthly_results_df)

            # ... (Calcul Taux Auto - INCHANGÉ) ...
            total_production = monthly_results_df['Production_kWh'].sum()
            total_consumption = monthly_results_df['Consommation_kWh'].sum()
            total_autoconsumption = monthly_results_df['Autoconsommation_kWh'].sum()
            autoconsumption_rate = (total_autoconsumption / total_consumption) if total_consumption > 1e-6 else 0.0
            autoproduction_rate = (total_autoconsumption / total_production) if total_production > 1e-6 else 0.0

            # --- 11. Construction Dictionnaire Résultats ---
            results = {
                "scenario": scenario_name, "prix_revente": prix_vente_a_utiliser,
                "source_parametres_simulation": source_des_inputs,
                "capex_base_utilise": capex_base,
                "opex_base_utilise": opex_annual_base_config, # OPEX Base (sans provision)
                "puissance_base_utilisee": puissance_kwc_global,
                "capex_scenario_simule": capex_scenario,
                "opex_scenario_simule": opex_annual_base, # OPEX Base scenario (sans provision)
                "equity_amount": equity_amount, "debt_amount": debt_amount, "total_subvention": total_subvention,
                "net_equity_investment": net_equity_investment,
                "autoconsumption_rate": autoconsumption_rate, "autoproduction_rate": autoproduction_rate,
                "wacc": wacc_annual, "lcoe": lcoe,
                "irr": irr_equity, "npv": npv_equity, "roi": roi_equity, "payback_period": payback_equity_years,
                "irr_project": irr_project, "npv_project": npv_project, "payback_project": payback_project_years,
                "avg_dscr": avg_dscr,
                "monthly_data": monthly_results_df,
                'hourly_aggregated_data': hourly_data_to_return
            }

            end_time_calc = time.time()
            print(f"MOTEUR (Mensuel): Indicateurs calculés pour '{scenario_name}' en {end_time_calc - start_time_calc:.3f} sec. Source: {source_des_inputs}")
            return results

        except (ValueError, TypeError, RuntimeError, ImportError) as e:
            print(f"ERREUR MOTEUR (calculate_financial_indicators - Mensuel): {e}")
            raise e # Renvoyer l'erreur
        except Exception as e:
            print(f"ERREUR MOTEUR INATTENDUE (Mensuel): {e}")
            traceback.print_exc()
            raise RuntimeError(f"Erreur inattendue Moteur Mensuel: {e}") from e


    # --- simulate_selling_price (INCHANGÉ - mais appelle calculate_financial_indicators modifié) ---
    def simulate_selling_price(self,
                               scenario_name: str,
                               target_irr: float | None = None,
                               target_npv: float | None = None,
                               override_source_prix_autoconso: str | None = None,
                               sites_config: dict | None = None
                              ) -> dict | None:
        # ... (Code inchangé, mais l'appel à self.calculate_financial_indicators
        #      utilisera la version modifiée avec la nouvelle logique fiscale) ...
        print(f"MOTEUR (Mensuel): simulate_selling_price: scenario={scenario_name}, target_irr={target_irr}, target_npv={target_npv}, override_autoconso={override_source_prix_autoconso}, sites_config fourni={'Oui' if sites_config else 'Non'}")
        try:
            if target_irr is None and target_npv is None: raise ValueError("Spécifier TRI ou VAN cible")
            global_config = self.config
            prix_min_config = float(global_config.get('prix_min_revente', 0.05))
            prix_max_config = float(global_config.get('prix_max_revente', 0.40))
            if prix_min_config >= prix_max_config: prix_min_config = 0.05; prix_max_config = 0.40
            optimal_price = None
            memoized_results = {}
            def objective_internal(price):
                price_rounded = round(price, 6)
                if price_rounded in memoized_results: return memoized_results[price_rounded]
                results = self.calculate_financial_indicators(
                    scenario_name, prix_revente=price,
                    override_source_prix_autoconso=override_source_prix_autoconso,
                    sites_config=sites_config
                )
                memoized_results[price_rounded] = results
                return results
            def npv_objective_for_root(price):
                results = objective_internal(price)
                if results and results.get('npv') is not None and np.isfinite(results['npv']): return results['npv']
                else: print(f"AVERTISSEMENT ROOT: NPV invalide pour prix {price:.6f}"); return np.nan
            if target_npv is not None and abs(target_npv) < 1e-9:
                print("MOTEUR (Mensuel): Cible VAN=0. Tentative brentq...")
                memoized_results.clear()
                try:
                    npv_min = npv_objective_for_root(prix_min_config); npv_max = npv_objective_for_root(prix_max_config)
                    if np.isfinite(npv_min) and np.isfinite(npv_max) and npv_min * npv_max < 0:
                        print(f"MOTEUR (Mensuel): Bracket trouvé [{prix_min_config:.4f}, {prix_max_config:.4f}]. Appel brentq...")
                        optimal_price = brentq(npv_objective_for_root, prix_min_config, prix_max_config, xtol=1e-6, rtol=1e-6)
                        print(f"MOTEUR (Mensuel): brentq a convergé vers {optimal_price:.8f}")
                    else: print(f"MOTEUR (Mensuel): Pas de changement de signe NPV. Passage à minimize.")
                except Exception as e_root: print(f"MOTEUR (Mensuel): Erreur brentq : {e_root}. Passage à minimize.")
            if optimal_price is None:
                print("MOTEUR (Mensuel): Utilisation de minimize...")
                objective_cache_minimize = {}
                def objective_function_minimize(price_array):
                    price = float(price_array[0]); price_rounded = round(price, 6)
                    if price_rounded in objective_cache_minimize: return objective_cache_minimize[price_rounded]
                    results = objective_internal(price)
                    diff = 1e10
                    if not results: diff = 1e12
                    else:
                        target_value = None; actual_value = None
                        if target_irr is not None: target_value = target_irr / 100.0; actual_value = results.get('irr')
                        elif target_npv is not None: target_value = target_npv; actual_value = results.get('npv')
                        if actual_value is not None and np.isfinite(actual_value) and target_value is not None: diff = (actual_value - target_value)**2
                        else: diff = 1e9
                    objective_cache_minimize[price_rounded] = diff
                    return diff
                initial_price_guess = global_config.get('prix_vente_initial', (prix_min_config + prix_max_config) / 2)
                initial_price_guess = max(prix_min_config, min(prix_max_config, initial_price_guess))
                bounds = [(prix_min_config, prix_max_config)]
                result = minimize(objective_function_minimize, [initial_price_guess], method='L-BFGS-B', bounds=bounds, options={'ftol': 1e-9, 'gtol': 1e-7})
                if result.success and bounds[0][0] <= result.x[0] <= bounds[0][1]: optimal_price = result.x[0]
                else:
                     print(f"MOTEUR (Mensuel): L-BFGS-B échec/hors bornes. Essai Nelder-Mead...")
                     def objective_wrapper_nelder(p): return objective_function_minimize([p]) if bounds[0][0] <= p <= bounds[0][1] else 1e12
                     result_nm = minimize(objective_wrapper_nelder, initial_price_guess, method='Nelder-Mead', options={'xatol': 1e-6, 'fatol': 1e-7})
                     if result_nm.success and bounds[0][0] <= result_nm.x[0] <= bounds[0][1]: optimal_price = result_nm.x[0]
                     else:
                          if result.success and 'fun' in result and result.fun < result_nm.fun: optimal_price = result.x[0]; print(f"AVERTISSEMENT: Conv. échouée, utilisation L-BFGS-B ({optimal_price:.6f})")
                          elif result_nm.success and 'fun' in result_nm: optimal_price = result_nm.x[0]; print(f"AVERTISSEMENT: Conv. échouée, utilisation Nelder-Mead ({optimal_price:.6f})")
                          else: raise RuntimeError("Convergence échouée par les deux méthodes.")
            if optimal_price is None: raise RuntimeError("Aucun prix optimal déterminé.")
            optimal_price = max(prix_min_config, min(prix_max_config, optimal_price))
            print(f"MOTEUR (Mensuel): Recalcul final avec prix optimal = {optimal_price:.8f}")
            final_results = objective_internal(optimal_price)
            if final_results and isinstance(final_results, dict):
                final_results['prix_revente_optimal_pour_cible'] = optimal_price
                final_results['target_irr_asked'] = target_irr; final_results['target_npv_asked'] = target_npv
                final_results['lcoe_associated'] = final_results.get('lcoe')
                final_results['tarif_edf_reference'] = global_config.get('tarif_edf_reference')
                return final_results
            else: raise RuntimeError(f"Échec recalcul final indicateurs avec prix {optimal_price:.8f}")
        except (ValueError, TypeError, RuntimeError) as e: print(f"ERREUR MOTEUR (simulate_selling_price): {e}"); raise e
        except Exception as e: print(f"ERREUR MOTEUR INATTENDUE (simulate_selling_price): {e}"); traceback.print_exc(); raise RuntimeError(f"Erreur inattendue: {e}") from e


    # --- Méthodes Helper ---
    def calculate_monthly_loan_schedule(self, principal, annual_rate, term_years, num_months_simulation):
        """Calcule l'échéancier mensuel (intérêts, principal, solde)."""
        if principal < 1e-6 or term_years <= 0 or annual_rate < 0:
             zeros = np.zeros(num_months_simulation)
             return zeros.copy(), zeros.copy(), zeros.copy()
        monthly_rate = annual_rate / 12.0; n_payments = int(round(term_years * 12))
        if abs(monthly_rate) < 1e-9: monthly_payment = principal / n_payments if n_payments > 0 else 0
        else:
            try:
                factor = (1 + monthly_rate)**n_payments; denominator = factor - 1
                if abs(denominator) < 1e-12: monthly_payment = principal / n_payments if n_payments > 0 else 0
                else:
                     monthly_payment = principal * (monthly_rate * factor) / denominator
                     if not np.isfinite(monthly_payment): monthly_payment = np.nan
            except (OverflowError, ZeroDivisionError): monthly_payment = np.nan
        if np.isnan(monthly_payment):
            zeros = np.zeros(num_months_simulation); return zeros.copy(), zeros.copy(), zeros.copy()
        interests = np.zeros(num_months_simulation); principals = np.zeros(num_months_simulation); balances = np.zeros(num_months_simulation)
        remaining_balance = principal
        for i in range(num_months_simulation):
            if i < n_payments and remaining_balance > 1e-6:
                interest = remaining_balance * monthly_rate
                principal_paid = max(0, min(monthly_payment - interest, remaining_balance))
                interests[i] = interest; principals[i] = principal_paid
                remaining_balance = max(0, remaining_balance - principal_paid)
                balances[i] = remaining_balance
            else: balances[i] = 0.0 if i >= n_payments else max(0, remaining_balance)
        return interests, principals, balances

    def calculate_payback_months(self, monthly_cash_flows):
        """Calcule le payback en mois à partir de flux mensuels (incluant T0)."""
        if not isinstance(monthly_cash_flows, np.ndarray): monthly_cash_flows = np.array(monthly_cash_flows)
        if len(monthly_cash_flows) == 0: return None
        if monthly_cash_flows[0] >= -1e-9: return 0.0
        cumulative_cf = np.cumsum(monthly_cash_flows)
        positive_indices = np.where(cumulative_cf >= -1e-9)[0]
        if len(positive_indices) == 0: return None
        first_positive_idx = positive_indices[0]
        if first_positive_idx == 0: return 0.0
        month_before_positive_idx = first_positive_idx - 1
        last_negative_cum_cf = cumulative_cf[month_before_positive_idx]
        cash_flow_crossing_month = monthly_cash_flows[first_positive_idx]
        if cash_flow_crossing_month > 1e-9:
            fraction = max(0.0, min(1.0, -last_negative_cum_cf / cash_flow_crossing_month))
            payback_months = (first_positive_idx - 1) + fraction
        elif abs(cumulative_cf[first_positive_idx]) < 1e-9: payback_months = float(first_positive_idx)
        else: payback_months = float(first_positive_idx - 1)
        return payback_months

    def calculate_lcoe_monthly(self, wacc_monthly, capex_net_subvention, monthly_df):
        """Calcule le LCOE à partir de données mensuelles."""
        if wacc_monthly is None or wacc_monthly <= -1.0: return np.nan
        try:
            opex_monthly = monthly_df.get('OPEX', 0.0).fillna(0).values
            turpe_monthly = monthly_df.get('TURPE', 0.0).fillna(0).values
            operational_costs_monthly = opex_monthly + turpe_monthly
            lcoe_cost_flows = np.concatenate(([-capex_net_subvention], -operational_costs_monthly))
            lcoe_discounted_costs_pv = npf.npv(wacc_monthly, lcoe_cost_flows)
            if not np.isfinite(lcoe_discounted_costs_pv): return np.nan
            prod_monthly = monthly_df.get('Production_kWh', 0.0).fillna(0).values
            if len(prod_monthly) != len(operational_costs_monthly):
                 min_len = min(len(prod_monthly), len(operational_costs_monthly)); prod_monthly = prod_monthly[:min_len]
            lcoe_prod_flows = np.concatenate(([0], prod_monthly))
            lcoe_discounted_production_pv = npf.npv(wacc_monthly, lcoe_prod_flows)
            if not np.isfinite(lcoe_discounted_production_pv): return np.nan
            if abs(lcoe_discounted_production_pv) > 1e-9: return -lcoe_discounted_costs_pv / lcoe_discounted_production_pv
            else: return np.nan
        except Exception as e: print(f"ERREUR LCOE HELPER: {e}"); return np.nan

    def calculate_avg_dscr_revised(self, monthly_df):
        """Calcule le DSCR moyen révisé à partir des données mensuelles."""
        if monthly_df.empty: return np.nan
        try:
            # S'assurer de l'index datetime
            df_copy = monthly_df.copy()
            if not isinstance(df_copy.index, pd.DatetimeIndex):
                if 'Temps' in df_copy.columns:
                     df_copy = df_copy.set_index('Temps')
                     df_copy.index = pd.to_datetime(df_copy.index)
                else: df_copy.index = pd.to_datetime(df_copy.index)

            # Approximation simple CADS = EBITDA
            annual_sum = df_copy.groupby(df_copy.index.year).agg(
                EBITDA_annuel=pd.NamedAgg(column='EBITDA', aggfunc=lambda x: x.fillna(0).sum()),
                Service_Dette_annuel=pd.NamedAgg(column='Service_Dette', aggfunc=lambda x: x.fillna(0).sum())
            )
            annual_sum['CADS_approx_annuel'] = annual_sum['EBITDA_annuel']

            # Calcul DSCR Annuel
            annual_sum['DSCR_annuel'] = np.where(
                np.abs(annual_sum['Service_Dette_annuel']) > 1e-9,
                annual_sum['CADS_approx_annuel'] / annual_sum['Service_Dette_annuel'],
                np.inf
            )
            annual_sum.loc[(annual_sum['CADS_approx_annuel'] <= 0) & (np.abs(annual_sum['Service_Dette_annuel']) <= 1e-9), 'DSCR_annuel'] = np.nan

            # Calcul Moyenne
            valid_dscr = annual_sum['DSCR_annuel'][np.isfinite(annual_sum['DSCR_annuel'])]
            if not valid_dscr.empty: avg_dscr = valid_dscr.mean()
            elif not annual_sum['DSCR_annuel'][annual_sum['DSCR_annuel'] == np.inf].empty: avg_dscr = np.inf
            else: avg_dscr = np.nan
            return avg_dscr

        except Exception as e:
            print(f"ERREUR Calcul DSCR Moyen Révisé: {e}")
            return np.nan

# --- Fin de la classe AnalysisEngine ---