# modules/analysis_engine.py

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
    print("INFO MOTEUR: numpy_financial chargé avec succès.")
except ImportError:
    NPF_IS_REAL = False
    print("AVERTISSEMENT MOTEUR: numpy_financial non trouvé. Fonctions secours utilisées. Précision limitée pour IRR.")
    
    def secours_npv(rate, values):
        values = np.asarray(values, dtype=float) 
        if values.size == 0:
            return 0.0
        if np.isclose(rate, -1.0):
            if values.size > 0 and np.any(values[1:]):
                 return float('-inf') if values[0] >= 0 else float('inf')
            return values[0] if values.size > 0 else 0.0
        if rate < -1.0:
            return np.nan 

        pv_sum = 0.0
        for i, value in enumerate(values):
            if value == 0: continue
            try:
                discount_factor_inv = (1 + rate) ** i
                if abs(discount_factor_inv) < sys.float_info.epsilon: # Proche de zéro
                    return np.nan if abs(value) > sys.float_info.epsilon else 0.0
                pv = value / discount_factor_inv
                if not np.isfinite(pv): return np.nan
                pv_sum += pv
            except (OverflowError, FloatingPointError): return np.nan
        return pv_sum

    def secours_irr(values, guess=0.1, tol=1e-7, max_iter=100):
        values = np.asarray(values, dtype=float)
        if values.size < 2 or np.all(np.isclose(values,0)): return np.nan # Besoin d'au moins 2 flux, et pas tous nuls
        
        f_npv_for_irr = lambda r: secours_npv(r, values)
        rate_intervals = [(-0.9999, 0.5), (0.0, 1.0), (-0.5, 0.0), (0.5, 5.0), (1.0, 100.0), (-0.9, -0.01)]
        
        for r_min, r_max in rate_intervals:
            try:
                npv_min = f_npv_for_irr(r_min)
                npv_max = f_npv_for_irr(r_max)
                if pd.notna(npv_min) and pd.notna(npv_max) and (np.sign(npv_min) * np.sign(npv_max) <= 0): # Signes opposés ou un est zéro
                    if np.isclose(npv_min, 0.0): return r_min
                    if np.isclose(npv_max, 0.0): return r_max
                    if npv_min * npv_max < 0: # Strictement opposés
                        return brentq(f_npv_for_irr, r_min, r_max, xtol=tol, rtol=tol, maxiter=max_iter)
            except (RuntimeError, ValueError): 
                continue
            except Exception: 
                continue
        # print("AVERTISSEMENT MOTEUR: Fonction secours_irr limitée, n'a pas convergé.")
        return np.nan

    class NpfModule:
        @staticmethod
        def npv(rate, values): return secours_npv(rate, values)
        @staticmethod
        def irr(values): return secours_irr(values)
    npf = NpfModule()

# --- Tax Engine Import ---
try:
    from . import tax_engine 
except ImportError:
    try:
        import tax_engine 
    except ImportError:
        print("ERREUR MOTEUR CRITIQUE: Impossible d'importer le module tax_engine.")
        class DummyTaxEngine:
            STANDARD_TAX_RATE = 0.25
            def apply_loss_carryforward_cap(self, ebt_before_loss, loss_carryforward_balance): return ebt_before_loss, loss_carryforward_balance
            def calculate_corporate_tax_pme(self, taxable_ebt): return taxable_ebt * self.STANDARD_TAX_RATE if taxable_ebt > 0 else 0.0
            def calculate_quarterly_installment(self, previous_year_tax): return previous_year_tax / 4.0 if previous_year_tax >=3000 else 0.0
        tax_engine = DummyTaxEngine()
        print("AVERTISSEMENT MOTEUR: tax_engine factice utilisé. Les calculs fiscaux seront incorrects.")

# --- TURPE Import ---
try:
    from modules.config import TURPE_PROD_RATES 
except ImportError:
    print("ERREUR MOTEUR: Impossible d'importer TURPE_PROD_RATES. TURPE sera nul.")
    TURPE_PROD_RATES = {}

class AnalysisEngine:
    def __init__(self, config: dict, scenarios: dict, sites_data: dict[str, pd.DataFrame]):
        if not isinstance(config, dict): raise TypeError("config doit être un dict")
        if not isinstance(scenarios, dict): raise TypeError("scenarios doit être un dict")
        if not isinstance(sites_data, dict): raise TypeError("sites_data doit être un dict")
        
        self.config = copy.deepcopy(config)
        self.scenarios = copy.deepcopy(scenarios)
        self.sites_data = {} # Initialiser vide, puis remplir avec validation
        
        required_cols = ['Temps', 'production_kwh', 'consumption_kwh']
        for site_id, df_site_init in sites_data.items(): # Utiliser sites_data passé en argument
            if not isinstance(df_site_init, pd.DataFrame):
                print(f"AVERTISSEMENT INIT: Données du site '{site_id}' non DataFrame, ignorées.")
                continue
            
            df_copy = df_site_init.copy() # Travailler sur une copie pour la validation/conversion

            if not df_copy.empty:
                if 'Temps' not in df_copy.columns:
                    raise ValueError(f"Colonne 'Temps' manquante pour le site '{site_id}'.")
                try:
                    if not pd.api.types.is_datetime64_any_dtype(df_copy['Temps']):
                        df_copy['Temps'] = pd.to_datetime(df_copy['Temps'], errors='raise')
                    # Vérifier NaT après conversion
                    if df_copy['Temps'].isnull().any():
                        raise ValueError(f"Conversion de 'Temps' en datetime a produit des NaT pour le site '{site_id}'.")
                except Exception as e_time: 
                    raise ValueError(f"Format de la colonne 'Temps' invalide pour le site '{site_id}': {e_time}")

                for col in ['production_kwh', 'consumption_kwh']:
                    if col not in df_copy.columns:
                        print(f"AVERTISSEMENT INIT: Colonne '{col}' manquante site '{site_id}'. Ajout avec zéros.")
                        df_copy[col] = 0.0 # Ajouter colonne avec zéros si manquante
                    try:
                        # Forcer la conversion en numérique, remplacer erreurs par NaN puis par 0
                        df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce').fillna(0.0)
                    except Exception as e_num: 
                        raise ValueError(f"Impossible de convertir la colonne '{col}' en numérique pour le site '{site_id}': {e_num}")
                self.sites_data[site_id] = df_copy # Stocker la version validée et copiée
            else:
                self.sites_data[site_id] = df_copy # Stocker le DataFrame vide

        self.npf_available = NPF_IS_REAL
        self.used_aggregated_config = False
    
    def calculate_wacc(self, debt_ratio, taux_interet_dette_pct, taux_imposition_pct, cout_fonds_propres_pct, wacc_type="after_tax") -> float | None:
        try:
            rd = float(taux_interet_dette_pct) / 100.0
            tc = float(taux_imposition_pct) / 100.0 
            re = float(cout_fonds_propres_pct) / 100.0
            dr = float(debt_ratio)

            if not (0 <= dr <= 1): raise ValueError("Debt ratio doit être entre 0 et 1")
            if not (0 <= tc < 1): raise ValueError("Taux imposition (pour bouclier fiscal dette) doit être entre 0 et 100[")
            if rd < 0 or re < 0: raise ValueError("Taux d'intérêt ou coût fonds propres négatifs invalides")

            equity_ratio = 1.0 - dr
            cout_dette_apres_impots = rd * (1.0 - tc)
            wacc_at = (dr * cout_dette_apres_impots) + (equity_ratio * re)

            if not (pd.notna(wacc_at) and np.isfinite(wacc_at)): # Vérifier si wacc_at est valide avant de l'utiliser
                 print(f"AVERTISSEMENT WACC: WACC après-taxe non fini ou NaN ({wacc_at})")
                 return None

            if wacc_type == "pre_tax":
                if abs(1.0 - tc) < 1e-9: 
                    print("AVERTISSEMENT WACC: Taux d'imposition à 100%, WACC pré-taxe approximé sans effet fiscal direct.")
                    wacc_pt = (dr * rd) + (equity_ratio * re) 
                else:
                    wacc_pt = wacc_at / (1.0 - tc)
                
                if not (pd.notna(wacc_pt) and np.isfinite(wacc_pt)): print(f"AVERTISSEMENT WACC: WACC pré-taxe non fini ({wacc_pt})"); return None
                return wacc_pt
            else: # after_tax
                return wacc_at
        except (TypeError, ValueError) as e: print(f"ERREUR MOTEUR (calculate_wacc): {e}"); return None
        except Exception as e: print(f"ERREUR INATTENDUE (calculate_wacc): {e}"); traceback.print_exc(); return None

    def calculate_financial_indicators(self,
                                       scenario_name: str,
                                       prix_revente: float | None = None,
                                       override_source_prix_autoconso: str | None = None,
                                       sites_config: dict | None = None) -> dict | None:
        start_time_calc = time.time()
        print(f"MOTEUR (Mensuel): Lancement calcul indicateurs pour '{scenario_name}'...")
        # Réinitialiser le flag à chaque appel
        self.used_aggregated_config = False 

        try:
            # --- 1. Récupération Config Globale et Scénario ---
            if scenario_name not in self.scenarios: raise ValueError(f"Scénario '{scenario_name}' invalide.")
            scenario = self.scenarios[scenario_name]
            global_config = self.config # Utilise la copie faite dans __init__

            # --- 2. Agrégation/Détermination des Paramètres de BASE (CAPEX, OPEX sans onduleur, Puissance) ---
            total_capex_base = 0.0
            total_opex_base_detail_no_inverter = 0.0
            total_puissance_kwc = 0.0
            inverter_provisions_annual_details = [] # {cost_unindexed, replacement_year_index}
            source_des_inputs = "globaux_fallback" # Par défaut si sites_config est non concluant

            effective_sites_config = sites_config if sites_config and any(sites_config.values()) else None
            
            if effective_sites_config:
                print("MOTEUR: Utilisation de la configuration par site (sites_config) pour agrégation.")
                self.used_aggregated_config = True # Flag pour indiquer que sites_config a été utilisé
                source_des_inputs = "agreges_par_site"
                for site_id, site_cfg in effective_sites_config.items():
                    if not isinstance(site_cfg, dict): continue
                    site_power = float(site_cfg.get('puissance_kwc', 0.0))
                    site_capex = float(site_cfg.get('capex', 0.0))
                    site_type = site_cfg.get('site_type', 'Producteur')
                    
                    site_opex_current_base_no_inv = 0.0
                    if site_type != "Consommateur Pur":
                        site_opex_current_base_no_inv += float(site_cfg.get('opex_maintenance', 0.0))
                        site_opex_current_base_no_inv += float(site_cfg.get('opex_insurance', 0.0))
                        site_opex_current_base_no_inv += float(site_cfg.get('opex_admin', 0.0))
                    
                    total_puissance_kwc += site_power
                    total_capex_base += site_capex
                    total_opex_base_detail_no_inverter += site_opex_current_base_no_inv

                    if site_type != "Consommateur Pur" and site_cfg.get("opex_onduleur_provision_site", False):
                        cost_unindexed = float(site_cfg.get("opex_onduleur_total_cost_site", 0.0))
                        lifetime = int(site_cfg.get("opex_onduleur_lifetime_site", 0))
                        duree_ppa_config = int(global_config.get("duree_ppa", 240)) # Utiliser la durée ppa de la config globale
                        if cost_unindexed > 0 and lifetime > 0 and duree_ppa_config > 0 :
                            for yr_op in range(1, (duree_ppa_config // 12) + 1): # Années d'opération
                                if yr_op % lifetime == 0: # Remplacement à la fin de cette année d'opération
                                     inverter_provisions_annual_details.append({
                                        "cost_unindexed": cost_unindexed,
                                        "replacement_year_index": yr_op -1 # 0-indexed year of operation
                                    })
                capex_base_input = total_capex_base
                opex_annual_base_input_no_inverter = total_opex_base_detail_no_inverter
                puissance_kwc_global = total_puissance_kwc
                print(f"MOTEUR: Agrégats de sites_config: CAPEX={capex_base_input:,.2f}€, OPEX_base_détail_sans_ond={opex_annual_base_input_no_inverter:,.2f}€/an, P_totale={puissance_kwc_global:.2f}kWc")

            else: # Fallback sur la config globale
                print("MOTEUR: Pas de sites_config valide. Utilisation des paramètres globaux (fallback).")
                # Ces valeurs de fallback devraient être clairement identifiées ou rendues obligatoires dans sites_config
                capex_base_input = float(global_config.get("capex_fallback_global", 0.0)) 
                opex_annual_base_input_no_inverter = float(global_config.get("opex_global_base_sans_onduleur_fallback", 0.0))
                puissance_kwc_global = float(global_config.get("puissance_kwc_fallback_global", 0.0))
                # Logique de provision onduleur globale (si sites_config n'est pas utilisé)
                if global_config.get("opex_onduleur_provision", False) and puissance_kwc_global > 0 :
                    cost_per_kwc_global_inv = float(global_config.get('opex_onduleur_cost', 130.0)) 
                    lifetime_global_inv = int(global_config.get('opex_onduleur_lifetime', 15))
                    duree_ppa_config = int(global_config.get("duree_ppa", 240))
                    if cost_per_kwc_global_inv > 0 and lifetime_global_inv > 0 and duree_ppa_config > 0:
                        cost_unindexed_global_inv = cost_per_kwc_global_inv * puissance_kwc_global
                        for yr_op in range(1, (duree_ppa_config // 12) + 1):
                             if yr_op % lifetime_global_inv == 0:
                                inverter_provisions_annual_details.append({
                                    "cost_unindexed": cost_unindexed_global_inv,
                                    "replacement_year_index": yr_op - 1
                                })
            
            # --- 3. Lecture et Conversion des Paramètres Globaux de `global_config` ---
            start_date_ppa_str = global_config.get("date_debut_ppa", datetime.now().date().isoformat())
            start_date_ppa = pd.to_datetime(start_date_ppa_str)
            num_months_simulation = int(global_config.get("duree_ppa", 240))
            if num_months_simulation <=0: raise ValueError("duree_ppa doit être positive.")

            degradation_rate_base = float(global_config.get("degradation_rate", 0.005)) # Doit être en décimal (ex: 0.005 pour 0.5%)
            taux_inflation_pct = float(global_config.get("taux_inflation", 2.0))
            adjusted_inflation_annual = taux_inflation_pct / 100.0
            
            oa_indexed = bool(global_config.get("tarif_oa_indexe_inflation", True))
            inflation_rate_oa_pct = float(global_config.get("taux_inflation_tarif_oa", 1.89)) # Taux spécifique OA
            inflation_rate_oa_annual = inflation_rate_oa_pct / 100.0
            
            turpe_indexed = bool(global_config.get("turpe_indexe_inflation", True)) # Indexé sur inflation générale par défaut
            
            taux_imposition_standard_pct = float(global_config.get("taux_imposition", 25.0))
            tax_rate_decimal = taux_imposition_standard_pct / 100.0
            if hasattr(tax_engine, 'STANDARD_TAX_RATE'): tax_engine.STANDARD_TAX_RATE = tax_rate_decimal

            amortissement_duree_years = int(global_config.get("amortissement_duree", 20))
            if amortissement_duree_years <=0: raise ValueError("Durée d'amortissement doit être positive.")
            
            valeur_residuelle_pct_config = float(global_config.get("valeur_residuelle_pct", 0.0)) # Ex: 0.0 ou 5.0 pour 5%
            cout_demantelement_pct_config = float(global_config.get("cout_demantelement_pct", 0.0)) # Ex: 0.0 ou 2.0 pour 2%

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
            
            # Calcul Subvention Globale
            applicable_sub_rate = 0.0
            if puissance_kwc_global <= 3: applicable_sub_rate = float(global_config.get("subvention_rate_le3",100.0))
            elif puissance_kwc_global <= 9: applicable_sub_rate = float(global_config.get("subvention_rate_le9", 80.0))
            elif puissance_kwc_global <= 36: applicable_sub_rate = float(global_config.get("subvention_rate_le36", 190.0))
            elif puissance_kwc_global <= 100: applicable_sub_rate = float(global_config.get("subvention_rate_le100", 100.0))
            elif puissance_kwc_global <= 500: applicable_sub_rate = float(global_config.get("subvention_rate_le500",0.0))
            else: applicable_sub_rate = float(global_config.get("subvention_rate_gt100", 0.0))
            total_subvention = applicable_sub_rate * puissance_kwc_global

            # Calcul Tarif OA base
            t_oa_le9 = float(global_config.get("tarif_oa_bracket_le9", 0.0400))
            t_oa_le100 = float(global_config.get("tarif_oa_bracket_le100", 0.0761))
            t_oa_gt100 = float(global_config.get("tarif_oa_bracket_gt100", 0.0600))
            if puissance_kwc_global <= 9: tarif_oa_base = t_oa_le9
            elif puissance_kwc_global <= 100: tarif_oa_base = t_oa_le100
            else: tarif_oa_base = t_oa_gt100
            print(f"MOTEUR: Tarif OA base calculé: {tarif_oa_base:.4f} €/kWh (P_globale={puissance_kwc_global:.2f} kWc)")

            # Calcul TURPE base
            if puissance_kwc_global <= 36: actual_turpe_tension = "BT<=36kVA"
            elif puissance_kwc_global <= 250: actual_turpe_tension = "BT>36kVA"
            else: actual_turpe_tension = "HTA"
            turpe_prod_contrat = global_config.get("turpe_prod_contrat", "Unique")
            if not TURPE_PROD_RATES: print("AVERTISSEMENT MOTEUR: TURPE_PROD_RATES non chargé. TURPE sera 0."); cg_rate = 0.0; cc_rate = 0.0
            else:
                cg_rate = TURPE_PROD_RATES.get(actual_turpe_tension, {}).get("CG", {}).get(turpe_prod_contrat, 0.0)
                cc_keys = list(TURPE_PROD_RATES.get(actual_turpe_tension, {}).get("CC", {}).keys())
                cc_key_default = "Linky" if "Linky" in cc_keys else (cc_keys[0] if cc_keys else None)
                cc_rate = TURPE_PROD_RATES.get(actual_turpe_tension, {}).get("CC", {}).get(cc_key_default, 0.0) if cc_key_default else 0.0
            turpe_annual_base_config = cg_rate + cc_rate
            print(f"MOTEUR: TURPE base recalculé: {turpe_annual_base_config:.2f} €/an (P_globale={puissance_kwc_global:.2f} kWc, Tension={actual_turpe_tension})")

            # --- 4. Application Modificateurs Scénario ---
            capex_scenario = capex_base_input * float(scenario.get("capex_modifier", 1.0))
            opex_scenario_base_no_inverter = opex_annual_base_input_no_inverter * float(scenario.get("opex_modifier", 1.0))
            turpe_annual_base_scenario = turpe_annual_base_config # Pas de modificateur scenario sur TURPE actuellement
            
            # Modificateurs sur taux (inflation, dégradation)
            # Si le modificateur d'inflation est 0.75, et inflation de base est 2%, nouvelle inflation = 1.5%
            # C'est le taux qui est modifié, pas le facteur (1+taux)
            adjusted_inflation_scenario_rate = adjusted_inflation_annual * float(scenario.get("inflation_modifier", 1.0))
            degradation_rate_scenario_effective = degradation_rate_base * float(scenario.get("degradation_modifier", 1.0)) 
            production_modifier_scenario = float(scenario.get("production_modifier", 1.0))

            # --- 5. Déterminer Prix de Vente et Source de Valorisation Autoconso ---
            prix_vente_final_a_utiliser = float(prix_revente) if prix_revente is not None else \
                                    float(global_config.get("prix_vente_initial_slider_fallback", 0.15)) # Fallback
            source_prix_autoc_effective = override_source_prix_autoconso if override_source_prix_autoconso is not None else source_prix_autoc_config
            
            # --- 6. Agrégation Données Énergétiques ---
            if not self.sites_data or not any(not df.empty for df in self.sites_data.values()):
                # Créer un DataFrame vide avec les colonnes nécessaires si aucune donnée de site
                print("AVERTISSEMENT MOTEUR: Aucune donnée de site énergétique. Simulation avec production/consommation nulles.")
                empty_hourly_index = pd.date_range(start=start_date_ppa, periods=num_months_simulation * 30 * 24, freq='H') # Approximation grossière
                data_agg = pd.DataFrame(0.0, index=empty_hourly_index, columns=['production_kwh', 'consumption_kwh'])
                data_agg = data_agg.reset_index().rename(columns={'index': 'Temps'})
            else:
                # (Votre logique d'agrégation améliorée de la réponse précédente va ici)
                all_dfs = [df for df in self.sites_data.values() if not df.empty]
                min_date_list = [df['Temps'].min() for df in all_dfs]
                max_date_list = [df['Temps'].max() for df in all_dfs]
                if not min_date_list or not max_date_list: raise ValueError("Impossible de déterminer les dates min/max des données de site valides.")
                min_date = min(min_date_list)
                max_date = max(max_date_list)
                
                freq = 'H' 
                first_df_non_empty_for_freq = all_dfs[0]
                temp_times = pd.to_datetime(first_df_non_empty_for_freq['Temps'], errors='coerce').dropna().sort_values()

                if not temp_times.empty:
                    inferred_freq = pd.infer_freq(temp_times)
                    if inferred_freq: freq = inferred_freq
                    else: 
                        time_diffs = temp_times.diff().dropna()
                        if not time_diffs.empty:
                            median_diff = time_diffs.median()
                            offset_freq = pd.tseries.frequencies.to_offset(median_diff)
                            if offset_freq: freq = offset_freq
                
                common_index = pd.date_range(start=min_date, end=max_date, freq=freq)
                if common_index.empty and (not data_agg.empty if 'data_agg' in locals() else True) : # Si common_index est vide et data_agg n'a pas été initialisé pour 0 données
                    raise ValueError(f"Impossible de créer un common_index (freq={freq}, min={min_date}, max={max_date}). Vérifiez les données de temps des sites.")

                data_agg = pd.DataFrame(0.0, index=common_index, columns=['production_kwh', 'consumption_kwh'])
                
                for site_id, df_site_raw in self.sites_data.items():
                    if df_site_raw.empty: continue
                    
                    site_cfg_local = effective_sites_config.get(site_id, {}) if effective_sites_config else {}
                    site_type = site_cfg_local.get('site_type', 'Producteur')
                    
                    df_temp = df_site_raw.copy()
                    df_temp['Temps'] = pd.to_datetime(df_temp['Temps'])
                    df_temp = df_temp.set_index('Temps')
                    if df_temp.index.has_duplicates: df_temp = df_temp.groupby(df_temp.index).sum()
                    
                    # Assurer la présence des colonnes et mettre à 0 si consommateur pur
                    if 'consumption_kwh' not in df_temp.columns: df_temp['consumption_kwh'] = 0.0
                    if site_type == "Consommateur Pur":
                        df_temp['production_kwh'] = 0.0
                    elif 'production_kwh' not in df_temp.columns:
                         df_temp['production_kwh'] = 0.0
                    
                    # Reindexer et additionner
                    df_temp_reindexed = df_temp[['production_kwh', 'consumption_kwh']].reindex(common_index, fill_value=0.0)
                    data_agg = data_agg.add(df_temp_reindexed, fill_value=0.0)
                
                data_agg = data_agg.reset_index().rename(columns={'index': 'Temps'})
            hourly_data_to_return = data_agg.copy() # Copie pour le retour

            # --- 7. Préparation Structure Mensuelle ---
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
                'Solde_Dette_Fin_Mois', 'Service_Dette',
                'VAT_Collectee', 'VAT_Deductible_CAPEX', 'VAT_Deductible_OPEX_TURPE', 
                'VAT_Due_Mois', 'VAT_Payment'
            ]
            for col in monthly_cols: monthly_results_df[col] = 0.0

            # --- 8. Calculs Préliminaires Annuels/Globaux ---
            capex_net_subvention = max(0, capex_scenario - total_subvention)
            debt_amount = capex_net_subvention * debt_ratio_config if loan_active else 0.0
            net_equity_investment = capex_net_subvention - debt_amount

            if loan_active and debt_amount > 1e-6:
                monthly_interest_paid, monthly_principal_paid, monthly_debt_balance = self.calculate_monthly_loan_schedule(
                    debt_amount, taux_interet_dette_annual, debt_term_years_config, num_months_simulation
                )
            else:
                zeros_array = np.zeros(num_months_simulation)
                monthly_interest_paid, monthly_principal_paid, monthly_debt_balance = zeros_array.copy(), zeros_array.copy(), zeros_array.copy()
            
            val_residuelle_montant = capex_net_subvention * (valeur_residuelle_pct_config / 100.0)
            base_amortissable = capex_net_subvention - val_residuelle_montant
            annual_depreciation_base = base_amortissable / amortissement_duree_years if amortissement_duree_years > 0 else 0.0
            
            tva_sur_capex_initial = capex_scenario * vat_rate_capex # Basé sur CAPEX brut du scénario

            # --- Préparation données énergétiques de référence (première année des données agrégées) ---
            df_agg_for_ref = hourly_data_to_return.set_index('Temps') # Utiliser les données agrégées finales
            if df_agg_for_ref.empty: ref_year = start_date_ppa.year # Fallback si aucune donnée
            else: ref_year = df_agg_for_ref.index.year.min()
            reference_data_ts = df_agg_for_ref[df_agg_for_ref.index.year == ref_year].copy()
            if reference_data_ts.empty: print(f"AVERTISSEMENT: Pas de données de référence pour l'année {ref_year} dans les données agrégées.")

            # --- 9. Boucle Mensuelle Principale ---
            loss_carryforward_balance = 0.0
            annual_tax_calculated_prev_year = 0.0
            current_quarterly_acompte_is = 0.0
            current_year_tracker = -1 # Pour détecter changement d'année

            inflation_factor_year_current = 1.0
            degradation_factor_year_current = 1.0
            opex_current_year_no_inverter_indexed_val = opex_scenario_base_no_inverter 
            turpe_current_year_indexed_val = turpe_annual_base_scenario
            depreciation_current_year_val = annual_depreciation_base if 0 < amortissement_duree_years else 0.0
            current_oa_rate_annual_val = tarif_oa_base
            
            if source_prix_autoc_effective == 'prix_initial': current_prix_autoc_annual_val = prix_vente_final_a_utiliser
            elif source_prix_autoc_effective == 'tarif_edf': current_prix_autoc_annual_val = tarif_edf_ref_config
            elif source_prix_autoc_effective == 'tarif_oa': current_prix_autoc_annual_val = current_oa_rate_annual_val
            else: current_prix_autoc_annual_val = prix_vente_final_a_utiliser

            vat_credit_carryforward = 0.0

            for month_idx in range(num_months_simulation):
                current_month_end_date = monthly_index[month_idx]
                year_idx = current_month_end_date.year - start_date_ppa.year # 0-indexed année d'opération
                simulation_year_num = year_idx + 1 # 1-indexed année d'opération
                
                monthly_results_df.loc[current_month_end_date, 'Year_Index'] = year_idx
                monthly_results_df.loc[current_month_end_date, 'Sim_Year'] = simulation_year_num

                if current_month_end_date.year != current_year_tracker: # Début d'une nouvelle année calendaire
                    if year_idx > 0: # Si ce n'est pas la toute première année de simulation
                        # Calcul IS pour l'année N-1 (terminée)
                        last_calendar_year_val = current_year_tracker # Année calendaire qui vient de se terminer
                        ebt_last_calendar_year_monthly = monthly_results_df.loc[monthly_results_df.index.year == last_calendar_year_val, 'EBT']
                        ebt_last_calendar_year_sum = ebt_last_calendar_year_monthly.sum() if not ebt_last_calendar_year_monthly.empty else 0.0
                        
                        taxable_ebt_last_year, loss_carryforward_balance = tax_engine.apply_loss_carryforward_cap(
                            ebt_before_loss=ebt_last_calendar_year_sum,
                            loss_carryforward_balance=loss_carryforward_balance
                        )
                        annual_tax_calculated_prev_year = tax_engine.calculate_corporate_tax_pme(
                            taxable_ebt=taxable_ebt_last_year
                        )
                        current_quarterly_acompte_is = tax_engine.calculate_quarterly_installment(
                            previous_year_tax=annual_tax_calculated_prev_year
                        )
                        
                        # Mise à jour des facteurs et coûts annuels indexés
                        inflation_factor_year_current = (1 + adjusted_inflation_scenario_rate) ** year_idx
                        degradation_factor_year_current = (1 - degradation_rate_scenario_effective) ** year_idx
                        
                        opex_current_year_no_inverter_indexed_val = opex_scenario_base_no_inverter * inflation_factor_year_current
                        turpe_current_year_indexed_val = turpe_annual_base_scenario * (inflation_factor_year_current if turpe_indexed else 1.0)
                        depreciation_current_year_val = annual_depreciation_base if year_idx < amortissement_duree_years else 0.0
                        
                        current_oa_rate_annual_val = tarif_oa_base * ((1 + inflation_rate_oa_annual)**year_idx if oa_indexed else 1.0)
                        if source_prix_autoc_effective == 'prix_initial': current_prix_autoc_annual_val = prix_vente_final_a_utiliser * inflation_factor_year_current
                        elif source_prix_autoc_effective == 'tarif_edf': current_prix_autoc_annual_val = tarif_edf_ref_config * inflation_factor_year_current
                        elif source_prix_autoc_effective == 'tarif_oa': current_prix_autoc_annual_val = current_oa_rate_annual_val
                        else: current_prix_autoc_annual_val = prix_vente_final_a_utiliser * inflation_factor_year_current
                    
                    current_year_tracker = current_month_end_date.year

                # Coût de remplacement onduleur pour l'année en cours, indexé
                current_year_total_inverter_replacement_cost_indexed = 0.0
                for inv_detail in inverter_provisions_annual_details:
                    if inv_detail["replacement_year_index"] == year_idx:
                        current_year_total_inverter_replacement_cost_indexed += inv_detail["cost_unindexed"] * inflation_factor_year_current
                
                opex_total_for_current_year_indexed = opex_current_year_no_inverter_indexed_val + current_year_total_inverter_replacement_cost_indexed

                # Affectation des valeurs annuelles (réparties mensuellement)
                monthly_results_df.loc[current_month_end_date, 'Inflation_Factor'] = inflation_factor_year_current
                monthly_results_df.loc[current_month_end_date, 'Degradation_Factor'] = degradation_factor_year_current
                monthly_results_df.loc[current_month_end_date, 'Tarif_OA_Annuel'] = current_oa_rate_annual_val
                monthly_results_df.loc[current_month_end_date, 'Prix_Autoconso_Annuel'] = current_prix_autoc_annual_val
                monthly_results_df.loc[current_month_end_date, 'OPEX'] = opex_total_for_current_year_indexed / 12.0
                monthly_results_df.loc[current_month_end_date, 'TURPE'] = turpe_current_year_indexed_val / 12.0
                monthly_results_df.loc[current_month_end_date, 'Amortissement'] = depreciation_current_year_val / 12.0

                # Paiement acompte IS
                tax_payment_is_this_month = 0.0
                payment_months_is = [3, 6, 9, 12]
                # Acomptes IS à partir de la 2ème année d'opération (simulation_year_num > 1)
                # car ils se basent sur l'IS N-1 (ou N-2 pour le premier).
                if current_month_end_date.month in payment_months_is and simulation_year_num > 0: # (year_idx >=0)
                    if simulation_year_num == 1 and year_idx == 0 : # Pas d'acompte la première année de simulation si pas d'historique N-1/N-2
                         tax_payment_is_this_month = 0.0
                    else:
                         tax_payment_is_this_month = current_quarterly_acompte_is
                monthly_results_df.loc[current_month_end_date, 'Tax_Payment'] = tax_payment_is_this_month
                
                # Calcul Énergie Mensuelle
                sim_month_calendar = current_month_end_date.month
                prod_m, cons_m, auto_m, surplus_m = 0.0, 0.0, 0.0, 0.0
                try:
                    ref_year_int = int(ref_year)
                    ref_month_start_dt = datetime(ref_year_int, sim_month_calendar, 1)
                    ref_month_end_day_count = pd.Timestamp(ref_month_start_dt).days_in_month
                    ref_month_end_dt = datetime(ref_year_int, sim_month_calendar, ref_month_end_day_count, 23, 59, 59)

                    if not reference_data_ts.empty and isinstance(reference_data_ts.index, pd.DatetimeIndex):
                        ref_monthly_energy_slice = reference_data_ts.loc[ref_month_start_dt:ref_month_end_dt]
                        if not ref_monthly_energy_slice.empty:
                            prod_ref_s = pd.Series(ref_monthly_energy_slice.get('production_kwh', 0.0))
                            cons_ref_s = pd.Series(ref_monthly_energy_slice.get('consumption_kwh', 0.0))
                            prod_adj_s = prod_ref_s * degradation_factor_year_current * production_modifier_scenario
                            prod_m = prod_adj_s.sum(); cons_m = cons_ref_s.sum()
                            auto_m = np.minimum(prod_adj_s, cons_ref_s).sum()
                            surplus_m = max(0, prod_m - auto_m)
                except Exception as e_eng_month: print(f"Erreur Calcul Énergie mois {sim_month_calendar} an {simulation_year_num}: {e_eng_month}")
                
                monthly_results_df.loc[current_month_end_date, 'Production_kWh'] = prod_m
                monthly_results_df.loc[current_month_end_date, 'Consommation_kWh'] = cons_m
                monthly_results_df.loc[current_month_end_date, 'Autoconsommation_kWh'] = auto_m
                monthly_results_df.loc[current_month_end_date, 'Surplus_kWh'] = surplus_m

                # Calcul Revenus Mensuels (HT)
                rev_surplus = surplus_m * current_oa_rate_annual_val
                rev_auto = auto_m * current_prix_autoc_annual_val
                monthly_results_df.loc[current_month_end_date, 'Revenus_Surplus'] = rev_surplus
                monthly_results_df.loc[current_month_end_date, 'Revenus_Autoconsommation'] = rev_auto
                monthly_results_df.loc[current_month_end_date, 'Revenus_Total'] = rev_surplus + rev_auto

                # P&L Mensuel (jusqu'à EBT)
                ebitda_m = (monthly_results_df.loc[current_month_end_date, 'Revenus_Total'] - 
                              monthly_results_df.loc[current_month_end_date, 'OPEX'] - 
                              monthly_results_df.loc[current_month_end_date, 'TURPE'])
                monthly_results_df.loc[current_month_end_date, 'EBITDA'] = ebitda_m
                ebit_m = ebitda_m - monthly_results_df.loc[current_month_end_date, 'Amortissement']
                monthly_results_df.loc[current_month_end_date, 'EBIT'] = ebit_m
                
                interest_m = monthly_interest_paid[month_idx] if month_idx < len(monthly_interest_paid) else 0.0
                principal_m = monthly_principal_paid[month_idx] if month_idx < len(monthly_principal_paid) else 0.0
                monthly_results_df.loc[current_month_end_date, 'Interets_Payes'] = interest_m
                monthly_results_df.loc[current_month_end_date, 'Principal_Rembourse'] = principal_m
                ebt_m = ebit_m - interest_m
                monthly_results_df.loc[current_month_end_date, 'EBT'] = ebt_m
                
                # Résultat Net (provisoire, basé sur acomptes IS payés ce mois)
                monthly_results_df.loc[current_month_end_date, 'Resultat_Net'] = ebt_m - tax_payment_is_this_month

                # Flux TVA Mensuels
                revenus_ht_m = monthly_results_df.loc[current_month_end_date, 'Revenus_Total']
                vat_collectee_m = revenus_ht_m * vat_rate_operations
                monthly_results_df.loc[current_month_end_date, 'VAT_Collectee'] = vat_collectee_m

                opex_ht_m = monthly_results_df.loc[current_month_end_date, 'OPEX']
                turpe_ht_m = monthly_results_df.loc[current_month_end_date, 'TURPE']
                vat_deductible_opex_turpe_m = (opex_ht_m + turpe_ht_m) * vat_rate_operations
                monthly_results_df.loc[current_month_end_date, 'VAT_Deductible_OPEX_TURPE'] = vat_deductible_opex_turpe_m
                
                vat_deductible_capex_m = 0.0
                if month_idx == vat_capex_recovery_month_offset:
                    vat_deductible_capex_m = tva_sur_capex_initial
                monthly_results_df.loc[current_month_end_date, 'VAT_Deductible_CAPEX'] = vat_deductible_capex_m

                vat_due_avant_report_m = vat_collectee_m - vat_deductible_opex_turpe_m - vat_deductible_capex_m
                vat_a_utiliser_du_report_m = min(vat_credit_carryforward, max(0, -vat_due_avant_report_m))
                vat_due_apres_report_m = vat_due_avant_report_m + vat_a_utiliser_du_report_m
                vat_credit_carryforward -= vat_a_utiliser_du_report_m
                if vat_due_apres_report_m < 0:
                    vat_credit_carryforward += abs(vat_due_apres_report_m)
                    vat_due_apres_report_m = 0.0
                monthly_results_df.loc[current_month_end_date, 'VAT_Due_Mois'] = vat_due_apres_report_m

                # Service et Solde Dette
                monthly_results_df.loc[current_month_end_date, 'Service_Dette'] = interest_m + principal_m
                monthly_results_df.loc[current_month_end_date, 'Solde_Dette_Fin_Mois'] = monthly_debt_balance[month_idx] if month_idx < len(monthly_debt_balance) else 0.0
            
            # --- FIN BOUCLE MENSUELLE ---
            # (Le reste de la méthode est identique à ma réponse précédente :
            #  Calcul Paiements TVA Trimestriels, Finalisation FCFE/OCF, Calcul Indicateurs Scalaires, Dictionnaire results)
            #  Je vais le recopier pour la complétude.

            print(f"MOTEUR (Mensuel): Fin boucle principale. Durée: {time.time() - start_time_calc:.3f} sec.")
            
            monthly_results_df['VAT_Payment'] = 0.0 
            try:
                if not isinstance(monthly_results_df.index, pd.DatetimeIndex):
                    monthly_results_df.index = pd.to_datetime(monthly_results_df.index)
                quarterly_vat_to_pay_or_receive = monthly_results_df['VAT_Due_Mois'].resample('QE').sum()
                for quarter_end_date, vat_sum_for_payment in quarterly_vat_to_pay_or_receive.items():
                    payment_month_date = quarter_end_date + pd.DateOffset(months=1) 
                    if payment_month_date in monthly_results_df.index:
                        monthly_results_df.loc[payment_month_date, 'VAT_Payment'] = vat_sum_for_payment
            except Exception as e_vat_trim_payment:
                print(f"ERREUR MOTEUR (VAT Trim Payment): {e_vat_trim_payment}"); traceback.print_exc()
                monthly_results_df['VAT_Payment'] = 0.0
            print("MOTEUR (Mensuel): Paiements/Remboursements TVA calculés.")
            
            amortissement_mensuel = monthly_results_df['Amortissement'].fillna(0)
            principal_rembourse_mensuel = monthly_results_df['Principal_Rembourse'].fillna(0)
            ebt_mensuel = monthly_results_df['EBT'].fillna(0)
            tax_payment_is_mensuel = monthly_results_df['Tax_Payment'].fillna(0) 
            vat_payment_mensuel = monthly_results_df['VAT_Payment'].fillna(0)   
            monthly_results_df['FCFE'] = (ebt_mensuel - tax_payment_is_mensuel + amortissement_mensuel - principal_rembourse_mensuel - vat_payment_mensuel)
            ebitda_mensuel_series = monthly_results_df['EBITDA'].fillna(0)
            monthly_results_df['OCF_Projet'] = (ebitda_mensuel_series * (1.0 - tax_rate_decimal)) + (amortissement_mensuel * tax_rate_decimal)
            print("MOTEUR (Mensuel): FCFE et OCF Projet finalisés.")

            fcfe_monthly_array = monthly_results_df['FCFE'].fillna(0).values
            equity_cash_flow_t0 = -net_equity_investment - tva_sur_capex_initial 
            equity_cash_flows_monthly = np.concatenate(([equity_cash_flow_t0], fcfe_monthly_array))
            
            ocf_monthly_array_base = monthly_results_df['OCF_Projet'].fillna(0).values 
            project_cash_flow_t0 = -capex_net_subvention 
            
            val_residuelle_montant_fin = capex_net_subvention * (valeur_residuelle_pct_config / 100.0)
            cout_demantelement_montant_fin = capex_scenario * (cout_demantelement_pct_config / 100.0)
            terminal_value_net_projet = val_residuelle_montant_fin - cout_demantelement_montant_fin
            
            project_cash_flows_monthly_list = [project_cash_flow_t0]
            if len(ocf_monthly_array_base) > 0:
                temp_ocf = ocf_monthly_array_base.copy()
                temp_ocf[-1] += terminal_value_net_projet 
                project_cash_flows_monthly_list.extend(temp_ocf)
            project_cash_flows_monthly = np.array(project_cash_flows_monthly_list)
            
            wacc_annual_at = self.calculate_wacc(debt_ratio_config, taux_interet_dette_pct_config, tax_rate_decimal * 100, cout_fonds_propres_pct_config, wacc_type="after_tax")
            wacc_monthly_at = (1 + wacc_annual_at)**(1/12) - 1 if wacc_annual_at is not None and wacc_annual_at > -1.0 else None
            re_annual = cout_fonds_propres_pct_config / 100.0
            re_monthly = (1 + re_annual)**(1/12) - 1 if re_annual > -1.0 else None

            irr_equity, npv_equity = np.nan, np.nan
            if len(equity_cash_flows_monthly) > 1 and np.any(np.abs(equity_cash_flows_monthly) > 1e-9):
                try:
                    irr_eq_raw = npf.irr(equity_cash_flows_monthly)
                    irr_equity = (1 + irr_eq_raw)**12 - 1 if pd.notna(irr_eq_raw) and np.isfinite(irr_eq_raw) else np.nan
                except Exception: pass
            if re_monthly is not None and abs(1 + re_monthly) > 1e-12:
                try:
                    npv_equity = npf.npv(re_monthly, equity_cash_flows_monthly)
                    npv_equity = npv_equity if pd.notna(npv_equity) and np.isfinite(npv_equity) else np.nan
                except Exception: pass
            
            irr_project, npv_project = np.nan, np.nan
            if len(project_cash_flows_monthly) > 1 and np.any(np.abs(project_cash_flows_monthly) > 1e-9):
                try:
                    irr_proj_raw = npf.irr(project_cash_flows_monthly)
                    irr_project = (1 + irr_proj_raw)**12 - 1 if pd.notna(irr_proj_raw) and np.isfinite(irr_proj_raw) else np.nan
                except Exception: pass
            if wacc_monthly_at is not None and abs(1 + wacc_monthly_at) > 1e-12:
                try:
                    npv_project = npf.npv(wacc_monthly_at, project_cash_flows_monthly)
                    npv_project = npv_project if pd.notna(npv_project) and np.isfinite(npv_project) else np.nan
                except Exception: pass
            
            roi_equity = npv_equity / abs(net_equity_investment) if pd.notna(npv_equity) and abs(net_equity_investment) > 1e-9 else np.nan
            payback_equity_years = self.calculate_payback_months(equity_cash_flows_monthly) / 12.0 if self.calculate_payback_months(equity_cash_flows_monthly) is not None else np.nan
            payback_project_years = self.calculate_payback_months(project_cash_flows_monthly) / 12.0 if self.calculate_payback_months(project_cash_flows_monthly) is not None else np.nan
            
            wacc_annual_pt = self.calculate_wacc(debt_ratio_config, taux_interet_dette_pct_config, tax_rate_decimal * 100, cout_fonds_propres_pct_config, wacc_type="pre_tax")
            wacc_monthly_pt = (1 + wacc_annual_pt)**(1/12) - 1 if wacc_annual_pt is not None and wacc_annual_pt > -1.0 else None
            lcoe_discount_rate_monthly = wacc_monthly_pt if wacc_monthly_pt is not None else wacc_monthly_at
            
            lcoe = self.calculate_lcoe_engineering(lcoe_discount_rate_monthly, capex_net_subvention, monthly_results_df, terminal_value_net_projet)
            avg_dscr = self.calculate_avg_dscr_revised(monthly_results_df, tax_rate_decimal)

            total_production_sum = monthly_results_df['Production_kWh'].sum()
            total_consumption_sum = monthly_results_df['Consommation_kWh'].sum()
            total_autoconsumption_sum = monthly_results_df['Autoconsommation_kWh'].sum()
            autoconsumption_rate = (total_autoconsumption_sum / total_consumption_sum) if total_consumption_sum > 1e-6 else 0.0
            autoproduction_rate = (total_autoconsumption_sum / total_production_sum) if total_production_sum > 1e-6 else 0.0

            results = {
                "scenario": scenario_name, "prix_revente": prix_vente_final_a_utiliser,
                "source_parametres_simulation": source_des_inputs,
                "capex_base_utilise": capex_base_input,
                "opex_base_utilise_no_inverter": opex_annual_base_input_no_inverter,
                "puissance_base_utilisee": puissance_kwc_global,
                "capex_scenario_simule": capex_scenario, 
                "capex_net_subvention_simule": capex_net_subvention, 
                "opex_scenario_base_no_inverter_simule": opex_scenario_base_no_inverter,
                "equity_amount_theorique_sur_net": capex_net_subvention * (1.0 - debt_ratio_config), 
                "debt_amount": debt_amount, 
                "total_subvention": total_subvention,
                "net_equity_investment": net_equity_investment, 
                "tva_sur_capex_initial_pour_fcfe_t0": tva_sur_capex_initial,
                "autoconsumption_rate": autoconsumption_rate, 
                "autoproduction_rate": autoproduction_rate,
                "wacc_after_tax_annual": wacc_annual_at, 
                "cost_of_equity_annual": re_annual,    
                "lcoe": lcoe, 
                "irr": irr_equity, "npv": npv_equity, "roi": roi_equity, "payback_period": payback_equity_years,
                "irr_project": irr_project, "npv_project": npv_project, "payback_project": payback_project_years,
                "avg_dscr": avg_dscr,
                "monthly_data": monthly_results_df.copy(), 
                'hourly_aggregated_data': hourly_data_to_return.copy(),
                "config_globale_utilisee": copy.deepcopy(global_config), 
                "config_scenario_utilise": copy.deepcopy(scenario),
                "config_sites_utilisee": copy.deepcopy(effective_sites_config) if effective_sites_config else {"mode": "global_fallback"}
            }
            end_time_calc = time.time()
            print(f"MOTEUR (Mensuel): Indicateurs calculés pour '{scenario_name}' en {end_time_calc - start_time_calc:.3f} sec. Source: {source_des_inputs}")
            return results

        except (ValueError, TypeError, RuntimeError, ImportError) as e:
            print(f"ERREUR MOTEUR (calculate_financial_indicators - Mensuel): Scenario '{scenario_name}', PrixRevente: {prix_revente}, Erreur: {e}")
            traceback.print_exc()
            return {"error": str(e)} # Renvoyer un dictionnaire d'erreur
        except Exception as e_unexp: 
            print(f"ERREUR MOTEUR INATTENDUE (Mensuel Calculate_financial_indicators): Scenario '{scenario_name}', PrixRevente: {prix_revente}, Erreur: {e_unexp}")
            traceback.print_exc()
            return {"error": f"Erreur inattendue: {e_unexp}"} # Renvoyer un dictionnaire d'erreur

    def calculate_lcoe_engineering(self, 
                                 wacc_monthly_discount_rate: float | None, 
                                 capex_net_subvention: float, 
                                 monthly_df_results: pd.DataFrame, 
                                 terminal_value_net_project: float):
        if wacc_monthly_discount_rate is None or not (pd.notna(wacc_monthly_discount_rate) and wacc_monthly_discount_rate > -1.0):
            print("AVERTISSEMENT LCOE Eng: Taux WACC invalide ou non fourni. LCOE sera NaN.")
            return np.nan
        try:
            opex_mensuel_ht_lcoe = monthly_df_results.get('OPEX', pd.Series(0.0, index=monthly_df_results.index)).fillna(0).values
            turpe_mensuel_ht_lcoe = monthly_df_results.get('TURPE', pd.Series(0.0, index=monthly_df_results.index)).fillna(0).values
            operational_costs_monthly_for_lcoe = opex_mensuel_ht_lcoe + turpe_mensuel_ht_lcoe

            cost_flows_lcoe_list = [-capex_net_subvention]
            cost_flows_lcoe_list.extend(-operational_costs_monthly_for_lcoe)
            cost_flows_lcoe = np.array(cost_flows_lcoe_list)
            
            if len(cost_flows_lcoe) > 1 : 
                cost_flows_lcoe[-1] -= terminal_value_net_project 
            
            npv_total_costs = npf.npv(wacc_monthly_discount_rate, cost_flows_lcoe)
            if not (pd.notna(npv_total_costs) and np.isfinite(npv_total_costs)):
                print("AVERTISSEMENT LCOE Eng: NPV des coûts non valide.")
                return np.nan

            prod_monthly_series = monthly_df_results.get('Production_kWh', pd.Series(0.0, index=monthly_df_results.index)).fillna(0)
            prod_monthly_values = prod_monthly_series.values 
            
            lcoe_prod_flows = np.concatenate(([0.0], prod_monthly_values)) # Production commence à T1
            npv_total_production = npf.npv(wacc_monthly_discount_rate, lcoe_prod_flows)

            if not (pd.notna(npv_total_production) and np.isfinite(npv_total_production)):
                print("AVERTISSEMENT LCOE Eng: NPV de la production non valide.")
                return np.nan
            
            if abs(npv_total_production) > 1e-9: 
                calculated_lcoe = -npv_total_costs / npv_total_production 
                return calculated_lcoe
            else:
                print("AVERTISSEMENT LCOE Eng: NPV de la production nulle ou quasi-nulle.")
                return np.nan
        except Exception as e:
            print(f"ERREUR MOTEUR (calculate_lcoe_engineering): {e}")
            traceback.print_exc()
            return np.nan

    def calculate_avg_dscr_revised(self, monthly_df_results: pd.DataFrame, corporate_tax_rate_decimal: float):
        if monthly_df_results.empty:
            print("AVERTISSEMENT DSCR: Données mensuelles vides pour DSCR.")
            return np.nan
        try:
            df_copy = monthly_df_results.copy()
            if not isinstance(df_copy.index, pd.DatetimeIndex):
                try: df_copy.index = pd.to_datetime(df_copy.index)
                except Exception as e_idx:
                    print(f"ERREUR DSCR: Index non convertible en DatetimeIndex: {e_idx}"); return np.nan
            
            # Vérifier que les colonnes nécessaires existent avant resample
            required_cols_dscr = ['EBITDA', 'Tax_Payment', 'Service_Dette']
            for col_dscr in required_cols_dscr:
                if col_dscr not in df_copy.columns:
                    print(f"ERREUR DSCR: Colonne '{col_dscr}' manquante pour agrégation.")
                    return np.nan
            
            try: # Envelopper resample dans un try-except plus spécifique
                ebitda_annual = df_copy['EBITDA'].fillna(0).resample('YE').sum()
                is_paid_annual = df_copy['Tax_Payment'].fillna(0).resample('YE').sum()
                debt_service_annual = df_copy['Service_Dette'].fillna(0).resample('YE').sum()
            except Exception as e_resample:
                print(f"ERREUR DSCR: Erreur lors du resample annuel: {e_resample}")
                return np.nan

            if ebitda_annual.empty and is_paid_annual.empty and debt_service_annual.empty:
                print("AVERTISSEMENT DSCR: Aucune donnée annuelle après resampling (simulation < 1 an?).")
                return np.nan

            annual_summary = pd.DataFrame({
                'EBITDA_annuel': ebitda_annual,
                'IS_Paid_annuel': is_paid_annual,
                'Service_Dette_annuel': debt_service_annual
            }).fillna(0) # Remplir les NaN potentiels après concaténation si les séries ont des longueurs différentes
            
            if annual_summary.empty : 
                print("AVERTISSEMENT DSCR: DataFrame annuel vide.")
                return np.nan

            annual_summary['CFADS_annuel'] = annual_summary['EBITDA_annuel'] - annual_summary['IS_Paid_annuel']
            
            annual_summary['DSCR_annuel'] = np.where(
                np.abs(annual_summary['Service_Dette_annuel']) > 1e-9,
                annual_summary['CFADS_annuel'] / annual_summary['Service_Dette_annuel'],
                np.inf 
            )
            annual_summary.loc[
                (annual_summary['CFADS_annuel'] <= 1e-9) & (np.abs(annual_summary['Service_Dette_annuel']) <= 1e-9),
                'DSCR_annuel'
            ] = np.nan
            
            dscr_for_avg = annual_summary['DSCR_annuel'][annual_summary['Service_Dette_annuel'] > 1e-9] # Moyenne seulement si service dette > 0
            dscr_finite_values = dscr_for_avg[np.isfinite(dscr_for_avg)]
            
            if not dscr_finite_values.empty:
                avg_dscr = dscr_finite_values.mean()
            elif not dscr_for_avg[dscr_for_avg == np.inf].empty : 
                avg_dscr = np.inf
            else: 
                avg_dscr = np.nan
            return avg_dscr
        except Exception as e:
            print(f"ERREUR MOTEUR (calculate_avg_dscr_revised): {e}")
            traceback.print_exc()
            return np.nan

    def simulate_selling_price(self, 
                               scenario_name: str,
                               target_irr: float | None = None, 
                               target_npv: float | None = None, 
                               override_source_prix_autoconso: str | None = None,
                               sites_config: dict | None = None
                              ) -> dict | None:
        print(f"MOTEUR (SIMULATE PRICE): Scénario='{scenario_name}', Target IRR={target_irr}, Target NPV={target_npv}")
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

            def get_target_metric_value(price_candidate): # Nested function
                price_key = round(price_candidate, 8) 
                if price_key in simulation_cache:
                    cached_results = simulation_cache[price_key]
                    if cached_results is None or (isinstance(cached_results, dict) and "error" in cached_results) : return np.nan 
                    if target_irr is not None: return cached_results.get('irr_project', np.nan)
                    if target_npv is not None: return cached_results.get('npv_project', np.nan)
                    return np.nan

                results_sim = self.calculate_financial_indicators( # Call to the main method
                    scenario_name, prix_revente=price_candidate,
                    override_source_prix_autoconso=override_source_prix_autoconso,
                    sites_config=sites_config
                )
                simulation_cache[price_key] = results_sim 
                
                if results_sim is None or (isinstance(results_sim, dict) and "error" in results_sim): return np.nan
                
                if target_irr is not None: return results_sim.get('irr_project', np.nan)
                if target_npv is not None: return results_sim.get('npv_project', np.nan)
                return np.nan

            def objective_for_brentq(price_candidate): # Nested function
                actual_metric_value = get_target_metric_value(price_candidate)
                if not (pd.notna(actual_metric_value) and np.isfinite(actual_metric_value)):
                    return np.nan 
                
                target_val_brentq = target_irr if target_irr is not None else target_npv
                if target_val_brentq is None : return np.nan # Should not happen if initial check passed
                return actual_metric_value - target_val_brentq

            try:
                val_min_bound = objective_for_brentq(prix_min_recherche)
                val_max_bound = objective_for_brentq(prix_max_recherche)

                if pd.notna(val_min_bound) and pd.notna(val_max_bound) and (np.sign(val_min_bound) * np.sign(val_max_bound) <= 0): # sign check
                    print(f"MOTEUR (SIMULATE PRICE): Brentq bracket OK [{val_min_bound:.4f}, {val_max_bound:.4f}]")
                    optimal_price_found = brentq(objective_for_brentq, prix_min_recherche, prix_max_recherche, xtol=1e-7, rtol=1e-7, maxiter=150)
                else: print(f"MOTEUR (SIMULATE PRICE): Brentq - no sign change or NaN (Min={val_min_bound}, Max={val_max_bound}).")
            except Exception as e_brentq: print(f"MOTEUR (SIMULATE PRICE): Erreur brentq : {e_brentq}.")

            if optimal_price_found is None:
                simulation_cache.clear() 
                def objective_for_minimize(price_array): # Nested function
                    price_candidate = float(price_array[0])
                    if not (prix_min_recherche <= price_candidate <= prix_max_recherche): return 1e12 
                    actual_metric_value = get_target_metric_value(price_candidate)
                    if not (pd.notna(actual_metric_value) and np.isfinite(actual_metric_value)): return 1e10 
                    target_val_minimize = target_irr if target_irr is not None else target_npv
                    if target_val_minimize is None: return 1e11 # Should not happen
                    return (actual_metric_value - target_val_minimize)**2

                initial_guess = max(prix_min_recherche, min(prix_max_recherche, (prix_min_recherche + prix_max_recherche) / 2.0))
                
                methods_to_try = [
                    ('L-BFGS-B', {'ftol': 1e-10, 'gtol': 1e-8, 'maxiter': 200}),
                    ('Nelder-Mead', {'xatol': 1e-7, 'fatol': 1e-9, 'maxiter': 300}),
                    ('SLSQP', {'ftol': 1e-9, 'maxiter': 150}) # SLSQP peut aussi être utile pour les problèmes bornés
                ]
                best_res_minimize = None

                for method_name, options in methods_to_try:
                    print(f"MOTEUR (SIMULATE PRICE): Tentative avec minimize ({method_name})...")
                    simulation_cache.clear() # Vider le cache pour chaque méthode, car elles explorent différemment
                    current_bounds = [(prix_min_recherche, prix_max_recherche)] if method_name != 'Nelder-Mead' else None # Nelder-Mead ne prend pas 'bounds' directement
                    
                    res_minimize_current = minimize(
                        objective_for_minimize, [initial_guess], method=method_name, 
                        bounds=current_bounds, options=options
                    )
                    if res_minimize_current.success and abs(res_minimize_current.fun) < 1e-7: # Seuil de succès plus strict
                        optimal_price_found = res_minimize_current.x[0]
                        print(f"MOTEUR (SIMULATE PRICE): {method_name} a convergé vers {optimal_price_found:.8f} (obj={res_minimize_current.fun:.2e})")
                        break # Sortir si une bonne solution est trouvée
                    elif best_res_minimize is None or \
                         (res_minimize_current.success and 'fun' in res_minimize_current and res_minimize_current.fun < best_res_minimize.fun):
                        best_res_minimize = res_minimize_current
                        print(f"MOTEUR (SIMULATE PRICE): {method_name} résultat partiel/meilleur: obj={res_minimize_current.fun:.2e}, prix={res_minimize_current.x[0]:.6f}")
                
                if optimal_price_found is None and best_res_minimize is not None and best_res_minimize.success:
                    optimal_price_found = best_res_minimize.x[0]
                    print(f"AVERTISSEMENT: Convergence stricte non atteinte, utilisation du meilleur résultat de minimize ({optimal_price_found:.6f}, obj={best_res_minimize.fun:.2e})")
            
            if optimal_price_found is None: raise RuntimeError("Aucun prix optimal déterminé après toutes les tentatives.")
            optimal_price_found = max(prix_min_recherche, min(prix_max_recherche, optimal_price_found))
            
            print(f"MOTEUR (SIMULATE PRICE): Recalcul final des indicateurs avec prix optimal = {optimal_price_found:.8f}")
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
            print(f"ERREUR FATALE (simulate_selling_price): {e}")
            traceback.print_exc()
            return {"error": str(e)}


    def calculate_monthly_loan_schedule(self, principal, annual_rate, term_years, num_months_simulation):
        if principal < 1e-6 or term_years <= 0:
            zeros_array = np.zeros(num_months_simulation)
            return zeros_array.copy(), zeros_array.copy(), zeros_array.copy()
        
        monthly_rate = annual_rate / 12.0
        n_payments_loan_term = int(round(term_years * 12))

        monthly_payment = 0.0
        if n_payments_loan_term > 0: # Éviter division par zéro si durée nulle
            if abs(monthly_rate) < 1e-9: 
                monthly_payment = principal / n_payments_loan_term
            else:
                try:
                    factor = (1 + monthly_rate)**n_payments_loan_term
                    denominator = factor - 1
                    if abs(denominator) < 1e-12: 
                        monthly_payment = principal / n_payments_loan_term # Fallback si taux + durée -> facteur ~1
                    else:
                        monthly_payment = principal * (monthly_rate * factor) / denominator
                    if not (pd.notna(monthly_payment) and np.isfinite(monthly_payment)):
                        monthly_payment = np.nan 
                except (OverflowError, ZeroDivisionError):
                    monthly_payment = np.nan
        
        if pd.isna(monthly_payment): 
            print(f"AVERTISSEMENT ECHEANCIER: Calcul échéance impossible (P={principal}, TauxAn={annual_rate}, DuréeAn={term_years}). Prêt ignoré.")
            zeros_array = np.zeros(num_months_simulation)
            return zeros_array.copy(), zeros_array.copy(), zeros_array.copy()

        interests_paid_monthly = np.zeros(num_months_simulation)
        principals_paid_monthly = np.zeros(num_months_simulation)
        debt_balance_eom = np.zeros(num_months_simulation)
        current_balance = principal

        for i in range(num_months_simulation):
            if i < n_payments_loan_term and current_balance > 1e-6: 
                interest_for_month = current_balance * monthly_rate
                principal_payment_for_month = monthly_payment - interest_for_month
                
                # S'assurer qu'on ne rembourse pas plus que le solde (surtout pour la dernière échéance)
                # Et que le principal remboursé n'est pas négatif si l'intérêt est > paiement (ne devrait pas arriver avec paiement bien calculé)
                principal_payment_for_month = max(0, principal_payment_for_month)
                if principal_payment_for_month > current_balance - 1e-5: # Tolérance pour le dernier paiement
                    principal_payment_for_month = current_balance 
                    # Recalculer l'intérêt pour la dernière mensualité si le principal est ajusté au solde
                    # Ceci est pertinent si le paiement mensuel calculé initialement était légèrement off
                    # Mais avec la formule standard, cela ne devrait pas être nécessaire.
                    # On garde l'intérêt basé sur le solde avant ce paiement.
                
                interests_paid_monthly[i] = interest_for_month
                principals_paid_monthly[i] = principal_payment_for_month
                current_balance -= principal_payment_for_month
                debt_balance_eom[i] = max(0, current_balance) 
            else: 
                interests_paid_monthly[i] = 0.0
                principals_paid_monthly[i] = 0.0
                debt_balance_eom[i] = max(0, current_balance) if i < n_payments_loan_term else 0.0 # Le solde est nul après la fin du prêt
        return interests_paid_monthly, principals_paid_monthly, debt_balance_eom

    def calculate_payback_months(self, monthly_cash_flows_with_t0: np.ndarray):
        if not isinstance(monthly_cash_flows_with_t0, np.ndarray):
            monthly_cash_flows_with_t0 = np.array(monthly_cash_flows_with_t0, dtype=float)
        
        if len(monthly_cash_flows_with_t0) < 1: return None # Nécessite au moins le flux T0
        if monthly_cash_flows_with_t0[0] >= -1e-9: return 0.0 
        if len(monthly_cash_flows_with_t0) == 1: return None # Seulement T0 négatif, pas de flux suivants

        cumulative_cf = np.cumsum(monthly_cash_flows_with_t0)
        positive_indices = np.where(cumulative_cf >= -1e-9)[0]
        
        if len(positive_indices) == 0: return None 
        first_positive_idx = positive_indices[0]
        
        if first_positive_idx == 0: return 0.0 
        
        month_before_payback_t_idx = first_positive_idx - 1 
        last_negative_cumulative_cf = cumulative_cf[month_before_payback_t_idx]
        cash_flow_of_payback_month = monthly_cash_flows_with_t0[first_positive_idx]

        if abs(cash_flow_of_payback_month) < 1e-9: 
            return float(month_before_payback_t_idx) if last_negative_cumulative_cf >= -1e-9 else None
        else:
            fraction_of_month = -last_negative_cumulative_cf / cash_flow_of_payback_month
            # first_positive_idx est l'index dans le tableau des flux (T0, T1, T2...).
            # Si T0 est l'investissement, first_positive_idx=1 signifie payback au cours du premier mois après T0.
            # Nombre de mois complets avant = first_positive_idx - 1.
            payback_in_months = (first_positive_idx - 1) + fraction_of_month
            
        return max(0, payback_in_months) # Assurer non-négatif, bien que T0>=0 gère le cas 0.