import pandas as pd
import numpy as np
import time
import traceback
import copy
from scipy.optimize import minimize, OptimizeResult

try:
    from modules.engine_module.core_analyzer import AnalysisEngine
except ImportError as e:
    print(f"ERREUR LOGIQUE: Import AnalysisEngine échoué : {e}")
    # Définir une classe factice si l'import échoue
    class AnalysisEngine:
        def __init__(self, *args, **kwargs):
            print("ERREUR CRITIQUE: AnalysisEngine n'a pas pu être chargé. Utilisation d'une version factice.")
            self.scenarios = {}
            self.config = {}
            self.sites_data = {}
        def calculate_financial_indicators(self, *args, **kwargs):
            print("ERREUR: La méthode calculate_financial_indicators de AnalysisEngine factice est appelée.")
            # Renvoyer un dict avec une clé 'error' pour une gestion cohérente par l'appelant
            return {"error": "AnalysisEngine non chargé ou défaillant"}
        def simulate_selling_price(self, *args, **kwargs):
            print("ERREUR: La méthode simulate_selling_price de AnalysisEngine factice est appelée.")
            return {"error": "AnalysisEngine non chargé ou défaillant"}

class OptimizationLogic:
    """Logique pour l'optimisation du prix et l'analyse de sensibilité."""

    def __init__(self, config: dict, analysis_engine: AnalysisEngine):
        if not isinstance(config, dict):
            raise TypeError("config doit être un dictionnaire")
        if not isinstance(analysis_engine, AnalysisEngine): # Vérifie si c'est une instance de la classe (ou de la classe factice)
            raise TypeError("analysis_engine doit être une instance de AnalysisEngine.")
            
        self.config = config 
        self.analysis_engine = analysis_engine
        # self.indicators_cache = {} # Ce cache n'est pas utilisé dans les versions récentes des méthodes

    def find_optimal_price_constrained(self,
                                       scenario_name: str,
                                       tri_projet_min_pct_constraint: float, 
                                       sites_config: dict | None = None
                                      ) -> dict | None:
        print(f"LOGIQUE OPTIM: Lancement Optimisation sous Contraintes. Scénario: '{scenario_name}'")
        start_time_optim_process = time.time()

        try:
            # Utiliser une copie de la config pour cette exécution spécifique
            current_run_config_dict = copy.deepcopy(self.config) 

            # --- 1. Récupération des paramètres et calcul des bornes de prix HT ---
            try:
                min_irr_projet_pct_target = float(tri_projet_min_pct_constraint)
                min_irr_projet_decimal_target = min_irr_projet_pct_target / 100.0
                max_payback_equity_years_target = float(current_run_config_dict.get('constraint_max_payback', 18.0))
                min_consumer_gain_pct_target = float(current_run_config_dict.get('constraint_min_consumer_gain_pct', 5.0))
                tarif_edf_ref_TTC_config = float(current_run_config_dict.get('tarif_edf_reference', 0.21))
                
                taux_tva_revenus_pct_config = float(current_run_config_dict.get('taux_tva_operations_pct', 20.0)) 
                taux_tva_revenus_decimal_val = taux_tva_revenus_pct_config / 100.0
                if not (0 <= taux_tva_revenus_decimal_val < 1): # Taux TVA doit être >=0 et <100%
                    raise ValueError(f"Taux de TVA sur revenus ({taux_tva_revenus_pct_config}%) invalide.")

                prix_max_revente_ht_config_safety_net = float(current_run_config_dict.get('prix_max_revente', 0.40))

                print("LOGIQUE OPTIM: Calcul préalable du Prix Plancher HT (VAN Projet = 0)...")
                floor_price_results_dict = self.analysis_engine.simulate_selling_price(
                    scenario_name, target_npv=0,
                    override_source_prix_autoconso="prix_initial", 
                    sites_config=sites_config
                )
                
                prix_min_optim_ht_val = None
                lcoe_estime_for_ui_display = None

                if floor_price_results_dict and isinstance(floor_price_results_dict, dict) and \
                   "error" not in floor_price_results_dict and \
                   floor_price_results_dict.get('prix_revente_optimal_pour_cible') is not None and \
                   np.isfinite(floor_price_results_dict.get('prix_revente_optimal_pour_cible')):
                    prix_min_optim_ht_val = floor_price_results_dict['prix_revente_optimal_pour_cible']
                    lcoe_estime_for_ui_display = floor_price_results_dict.get('lcoe') 
                    print(f"LOGIQUE OPTIM: Prix plancher HT (VAN Projet=0) trouvé: {prix_min_optim_ht_val:.4f} €/kWh. (LCOE associé: {lcoe_estime_for_ui_display:.4f} €/kWh)")
                else:
                    error_msg_floor_price = floor_price_results_dict.get("error", "calcul non concluant ou valeur invalide") if isinstance(floor_price_results_dict, dict) else "calcul non concluant"
                    print(f"LOGIQUE OPTIM: Calcul prix plancher VAN Projet=0 échoué ({error_msg_floor_price}). Tentative avec LCOE engineering.")
                    
                    # Fallback: Calculer le LCOE engineering
                    # Note: Il faut un prix de revente pour calculer tous les indicateurs, y compris le LCOE.
                    # On utilise un prix de fallback pour cet appel.
                    temp_indicators_for_lcoe = self.analysis_engine.calculate_financial_indicators(
                        scenario_name,
                        prix_revente=current_run_config_dict.get("prix_vente_initial_slider_fallback", 0.15), 
                        sites_config=sites_config
                    )
                    if temp_indicators_for_lcoe and isinstance(temp_indicators_for_lcoe, dict) and \
                       "error" not in temp_indicators_for_lcoe and \
                       temp_indicators_for_lcoe.get('lcoe') is not None and \
                       np.isfinite(temp_indicators_for_lcoe.get('lcoe')):
                        lcoe_estime_for_ui_display = temp_indicators_for_lcoe['lcoe']
                        prix_min_optim_ht_val = lcoe_estime_for_ui_display # Utiliser LCOE comme borne inf
                        print(f"AVERTISSEMENT LOGIQUE OPTIM: Utilisation du LCOE engineering estimé {lcoe_estime_for_ui_display:.4f} €/kWh comme borne inférieure HT.")
                    else:
                        lcoe_error_msg_fallback = temp_indicators_for_lcoe.get("error", "LCOE non calculable") if isinstance(temp_indicators_for_lcoe, dict) else "LCOE non calculable"
                        raise ValueError(f"Calcul de la borne inférieure HT (Prix Plancher VAN Projet=0 ou LCOE) impossible: {lcoe_error_msg_fallback}.")

                # Calcul de la borne supérieure HT en respectant le gain client TTC
                prix_vente_TTC_max_pour_client = tarif_edf_ref_TTC_config * (1.0 - min_consumer_gain_pct_target / 100.0)
                if abs(1.0 + taux_tva_revenus_decimal_val) < 1e-9: # Dénominateur (1+TVA)
                    raise ValueError("Taux de TVA sur revenus configuré incorrect (provoque division par zéro).")
                prix_max_ht_selon_gain_client = prix_vente_TTC_max_pour_client / (1.0 + taux_tva_revenus_decimal_val)
                prix_max_optim_ht_val = min(prix_max_revente_ht_config_safety_net, prix_max_ht_selon_gain_client)

                if prix_min_optim_ht_val >= prix_max_optim_ht_val:
                    if abs(prix_min_optim_ht_val - prix_max_optim_ht_val) < 1e-5: 
                         prix_max_optim_ht_val = prix_min_optim_ht_val + 1e-5 
                    else:
                        raise ValueError(
                            f"Plage de recherche de prix HT invalide ou négative: MinHT={prix_min_optim_ht_val:.4f}, MaxHT={prix_max_optim_ht_val:.4f}.")
                print(f"LOGIQUE OPTIM: Bornes recherche prix HT finales: [{prix_min_optim_ht_val:.4f}, {prix_max_optim_ht_val:.4f}] €/kWh")

            except (ValueError, TypeError, KeyError, RuntimeError) as e_params_prep:
                traceback.print_exc()
                raise ValueError(f"Erreur préparation paramètres/bornes d'optimisation: {e_params_prep}") from e_params_prep

            memoized_indicators_optim = {} 
            def get_indicators_for_optim(price_ht_candidate: float, scenario_name_opt: str) -> dict | None:
                 price_key_optim = round(price_ht_candidate, 8) 
                 cache_key_optim = (scenario_name_opt, price_key_optim)
                 if cache_key_optim in memoized_indicators_optim: return memoized_indicators_optim[cache_key_optim]
                 
                 if not hasattr(self.analysis_engine, 'calculate_financial_indicators') or \
                    not callable(self.analysis_engine.calculate_financial_indicators):
                     memoized_indicators_optim[cache_key_optim] = {"error": "AnalysisEngine non opérationnel"}
                     return {"error": "AnalysisEngine non opérationnel"}
                 try:
                      results_for_price = self.analysis_engine.calculate_financial_indicators(
                          scenario_name_opt, prix_revente=price_ht_candidate, sites_config=sites_config
                      )
                      memoized_indicators_optim[cache_key_optim] = results_for_price
                      return results_for_price
                 except Exception as e_calc_indic_optim:
                      memoized_indicators_optim[cache_key_optim] = {"error": str(e_calc_indic_optim)}
                      return {"error": str(e_calc_indic_optim)}
            
            def objective_function_maximize_npv_equity(price_ht_array_optim):
                price_ht_optim = float(price_ht_array_optim[0])
                indicators_optim = get_indicators_for_optim(price_ht_optim, scenario_name)
                if indicators_optim is None or (isinstance(indicators_optim, dict) and "error" in indicators_optim): return 1e12 
                npv_equity_val_optim = indicators_optim.get('npv') 
                if npv_equity_val_optim is None or not np.isfinite(npv_equity_val_optim): return 1e12 
                return -npv_equity_val_optim 

            constraints_for_scipy = []
            def tri_projet_optim_constraint(price_ht_array_constr):
                 price_ht_constr = float(price_ht_array_constr[0])
                 indicators_constr = get_indicators_for_optim(price_ht_constr, scenario_name)
                 if indicators_constr is None or (isinstance(indicators_constr, dict) and "error" in indicators_constr): return -1e6
                 irr_proj_val_constr = indicators_constr.get('irr_project')
                 if irr_proj_val_constr is None or not np.isfinite(irr_proj_val_constr): return -1e6
                 return irr_proj_val_constr - min_irr_projet_decimal_target
            constraints_for_scipy.append({'type': 'ineq', 'fun': tri_projet_optim_constraint})

            EQUITY_INVESTMENT_THRESHOLD_OPTIM = 1.0

            def payback_equity_optim_constraint(price_ht_array_constr):
                 price_ht_constr = float(price_ht_array_constr[0])
                 indicators_constr = get_indicators_for_optim(price_ht_constr, scenario_name)
                 if indicators_constr is None or (isinstance(indicators_constr, dict) and "error" in indicators_constr):
                     return -1e6 # Indicateurs non calculables, contrainte non respectée

                 net_equity_inv_constr = indicators_constr.get('net_equity_investment', 0.0)

                 if abs(net_equity_inv_constr) < EQUITY_INVESTMENT_THRESHOLD_OPTIM:
                     return 1e6 # Apport FP négligeable, contrainte de payback FP considérée comme respectée

                 payback_eq_val_constr = indicators_constr.get('payback_period')
                 
                 if payback_eq_val_constr is None or not np.isfinite(payback_eq_val_constr):
                      return -1e6 if max_payback_equity_years_target != float('inf') else 1e6 
                 
                 return max_payback_equity_years_target - payback_eq_val_constr
            constraints_for_scipy.append({'type': 'ineq', 'fun': payback_equity_optim_constraint})
            
            final_bounds_for_scipy = [(prix_min_optim_ht_val, prix_max_optim_ht_val)]
            num_starts_for_optim = int(current_run_config_dict.get('optim_num_starts', 3))
            best_overall_optimize_result: OptimizeResult | None = None
            smallest_objective_value_achieved = float('inf')
            
            if abs(final_bounds_for_scipy[0][1] - final_bounds_for_scipy[0][0]) < 1e-5:
                effective_start_points_ht = [final_bounds_for_scipy[0][0]]
            else:
                effective_start_points_ht = np.linspace(final_bounds_for_scipy[0][0], final_bounds_for_scipy[0][1], num_starts_for_optim)

            print(f"LOGIQUE OPTIM: Lancement SLSQP avec {len(effective_start_points_ht)} points de départ...")
            memoized_indicators_optim.clear() 

            for i_optim_start, start_price_ht_optim_iter in enumerate(effective_start_points_ht):
                 print(f"  -> Départ {i_optim_start+1}/{len(effective_start_points_ht)} : Prix HT initial = {start_price_ht_optim_iter:.6f}")
                 try:
                     current_iter_optimize_result = minimize(
                         objective_function_maximize_npv_equity, [float(start_price_ht_optim_iter)], 
                         method='SLSQP', bounds=final_bounds_for_scipy, constraints=constraints_for_scipy, 
                         options={'ftol': 1e-9, 'disp': False, 'maxiter': 200} 
                     )
                     if current_iter_optimize_result.success and current_iter_optimize_result.fun < smallest_objective_value_achieved:
                          candidate_price_ht = float(current_iter_optimize_result.x[0])
                          constraints_verified_for_candidate = True
                          for constraint_check_dict in constraints_for_scipy:
                               if constraint_check_dict['fun']([candidate_price_ht]) < -1e-6: 
                                    constraints_verified_for_candidate = False; break
                          if constraints_verified_for_candidate:
                               smallest_objective_value_achieved = current_iter_optimize_result.fun
                               best_overall_optimize_result = current_iter_optimize_result 
                               print(f"     -> Succès! Nouveau meilleur obj.={smallest_objective_value_achieved:.4e}, prix HT={candidate_price_ht:.6f}")
                     elif not current_iter_optimize_result.success:
                          print(f"     -> Échec SLSQP (Départ {i_optim_start+1}): {current_iter_optimize_result.message}")
                 except Exception as e_minimize_optim_loop:
                     print(f"     -> Erreur SLSQP (Départ {i_optim_start+1}): {e_minimize_optim_loop}")
            
            if best_overall_optimize_result is None or not hasattr(best_overall_optimize_result, 'x') or not best_overall_optimize_result.success:
                 msg_no_valid_optim_solution = "Optimisation échouée: Aucune solution valide respectant contraintes."
                 if prix_min_optim_ht_val > prix_max_optim_ht_val - 1e-4 :
                     msg_no_valid_optim_solution += f" Plage recherche HT invalide/étroite: [{prix_min_optim_ht_val:.4f}-{prix_max_optim_ht_val:.4f}]."
                 return {'error': msg_no_valid_optim_solution, 'details': best_overall_optimize_result.message if best_overall_optimize_result else "Pas de résultat"}

            optimal_price_ht_final_value = float(best_overall_optimize_result.x[0])
            optimal_price_ht_final_value = max(final_bounds_for_scipy[0][0], min(final_bounds_for_scipy[0][1], optimal_price_ht_final_value))
            maximized_npv_equity_value = -best_overall_optimize_result.fun 
            print(f"LOGIQUE OPTIM: Prix Optimal HT Final = {optimal_price_ht_final_value:.8f} €/kWh (NPV Equity Max = {maximized_npv_equity_value:,.0f} €)")

            print(f"LOGIQUE OPTIM: Recalcul final indicateurs au prix HT optimal {optimal_price_ht_final_value:.8f}...")
            memoized_indicators_optim.clear() 
            final_indicators_at_optimal_price = get_indicators_for_optim(optimal_price_ht_final_value, scenario_name)
            
            if final_indicators_at_optimal_price is None or (isinstance(final_indicators_at_optimal_price, dict) and "error" in final_indicators_at_optimal_price):
                final_error_msg = final_indicators_at_optimal_price.get("error", "inconnu") if isinstance(final_indicators_at_optimal_price, dict) else "inconnu"
                raise RuntimeError(f"Erreur recalcul final indicateurs au prix HT optimal: {final_error_msg}")

            optimization_summary_dict = {
                'scenario_name': scenario_name,
                'prix_optimal_const': optimal_price_ht_final_value,
                'methode': 'Optimisation Contraintes (SLSQP multi-start)',
                'contraintes_appliquees': { 
                    'min_irr_projet_pct_cible': min_irr_projet_pct_target, 
                    'max_payback_equity_annees_cible': max_payback_equity_years_target,
                    'min_consumer_gain_pct_cible_ttc': min_consumer_gain_pct_target,
                    'tarif_edf_ref_ttc_config_utilise': tarif_edf_ref_TTC_config,
                    'taux_tva_revenus_pct_utilise': taux_tva_revenus_pct_config,
                    'borne_inf_prix_ht_calculee': prix_min_optim_ht_val,
                    'borne_sup_prix_ht_calculee': prix_max_optim_ht_val 
                },
                'npv_optimise_equity': maximized_npv_equity_value,
                'lcoe_estime_initial_pour_borne_inf': lcoe_estime_for_ui_display,
                'indicateurs_au_prix_optimal': final_indicators_at_optimal_price,
                'optimisation_details': {
                    'success': best_overall_optimize_result.success,
                    'message': best_overall_optimize_result.message,
                    'status': best_overall_optimize_result.status if hasattr(best_overall_optimize_result, 'status') else 'N/A',
                    'nfev': best_overall_optimize_result.nfev if hasattr(best_overall_optimize_result, 'nfev') else 'N/A',
                    'nit': best_overall_optimize_result.nit if hasattr(best_overall_optimize_result, 'nit') else 'N/A'
                }
            }
            end_time_optim_process_final = time.time()
            print(f"LOGIQUE OPTIM: Exécution find_optimal_price_constrained en {end_time_optim_process_final - start_time_optim_process:.2f} sec.")
            return optimization_summary_dict

        except (ValueError, TypeError, RuntimeError) as e_main_optim_logic:
            print(f"ERREUR LOGIQUE (find_optimal_price_constrained): {e_main_optim_logic}")
            traceback.print_exc() 
            return {'error': f"Erreur logique optimisation: {str(e_main_optim_logic)}"}
        except Exception as e_unexp_optim_logic:
            print(f"ERREUR LOGIQUE INATTENDUE (find_optimal_price_constrained): {e_unexp_optim_logic}")
            traceback.print_exc()
            return {'error': f"Erreur inattendue durant l'optimisation: {str(e_unexp_optim_logic)}"}

    def run_monte_carlo_simulation(self, scenario_name: str, prix_revente: float, sites_config: dict | None = None) -> dict | None:
        print(f"LOGIQUE MC: Lancement Monte Carlo. Scénario: '{scenario_name}', Prix HT: {prix_revente:.4f}")
        start_time_mc = time.time() # CORRIGÉ: variable de début de temps
        try:
            config_mc = self.config 
            
            if not hasattr(self.analysis_engine, 'sites_data') or not self.analysis_engine.sites_data or not any(self.analysis_engine.sites_data.values()):
                 raise ValueError("Données de site originales (self.analysis_engine.sites_data) non disponibles ou vides pour Monte Carlo.")
            
            original_sites_data_for_mc = copy.deepcopy(self.analysis_engine.sites_data)

            n_iterations_mc = int(config_mc.get('nb_iterations_monte_carlo', 1000))
            ecart_type_prod_pct_mc = float(config_mc.get('ecart_type_production', 10.0)) / 100.0
            ecart_type_conso_pct_mc = float(config_mc.get('ecart_type_consommation', 5.0)) / 100.0
            
            # CORRECTION ET DÉFINITION EXPLICITE DES SEUILS MC
            target_dscr_mc_threshold = float(config_mc.get('target_dscr', 1.2)) 
            payback_max_equity_mc_threshold = float(config_mc.get('constraint_max_payback', 18.0))
            min_irr_projet_mc_pct_threshold = float(config_mc.get('constraint_min_project_irr_pct', 8.0))
            min_irr_projet_mc_decimal_threshold = min_irr_projet_mc_pct_threshold / 100.0 # Définie ici
            
            print(f"LOGIQUE MC: Cibles - TRI Projet >= {min_irr_projet_mc_pct_threshold}%, Payback Equity <= {payback_max_equity_mc_threshold} ans, DSCR Moyen >= {target_dscr_mc_threshold}")

            mc_tracked_indicators = ['roi', 'irr', 'npv', 'payback_period', 'avg_dscr', 'irr_project', 'payback_project', 'lcoe']
            mc_iteration_results = {f"{indicator_name}_values": [] for indicator_name in mc_tracked_indicators}
            
            for i_mc_iter in range(n_iterations_mc):
                simulated_sites_data_current_iter = {}
                for site_id_mc, original_df_site_iter_mc in original_sites_data_for_mc.items():
                    sim_df_for_site_iter = original_df_site_iter_mc.copy() 
                    prod_variation_factor = max(0, np.random.normal(1, ecart_type_prod_pct_mc))
                    cons_variation_factor = max(0, np.random.normal(1, ecart_type_conso_pct_mc))
                    if 'production_kwh' in sim_df_for_site_iter.columns:
                        sim_df_for_site_iter['production_kwh'] *= prod_variation_factor
                    if 'consumption_kwh' in sim_df_for_site_iter.columns:
                        sim_df_for_site_iter['consumption_kwh'] *= cons_variation_factor
                    simulated_sites_data_current_iter[site_id_mc] = sim_df_for_site_iter

                results_current_iter = None
                try:
                    temp_mc_analysis_engine = AnalysisEngine(
                        self.config, self.analysis_engine.scenarios, simulated_sites_data_current_iter
                    )
                    results_current_iter = temp_mc_analysis_engine.calculate_financial_indicators(
                        scenario_name, prix_revente=prix_revente, sites_config=sites_config
                    )
                except Exception as e_mc_iter_financial_calc:
                    if i_mc_iter % (n_iterations_mc // 10 or 1) == 0 : 
                        print(f"AVERTISSEMENT LOGIQUE MC (Iter {i_mc_iter+1}): Échec calcul indicateurs - {e_mc_iter_financial_calc}")
                
                if results_current_iter and isinstance(results_current_iter, dict) and "error" not in results_current_iter:
                    for indicator_key in mc_tracked_indicators:
                        iter_value = results_current_iter.get(indicator_key)
                        mc_iteration_results[f"{indicator_key}_values"].append(iter_value if (pd.notna(iter_value) and np.isfinite(iter_value)) else np.nan)
                else: 
                    for indicator_key in mc_tracked_indicators:
                        mc_iteration_results[f"{indicator_key}_values"].append(np.nan)
            
            mc_stats_summary = {}
            mc_probabilities_summary = {}
            
            all_irr_proj_mc_values = np.array(mc_iteration_results.get("irr_project_values", []))
            all_payback_equity_mc_values = np.array(mc_iteration_results.get("payback_period_values", []))
            all_dscr_mc_values = np.array(mc_iteration_results.get("avg_dscr_values", []))

            global_criteria_valid_mask = (
                ~np.isnan(all_irr_proj_mc_values) & np.isfinite(all_irr_proj_mc_values) &
                ~np.isnan(all_payback_equity_mc_values) & np.isfinite(all_payback_equity_mc_values) &
                ~np.isnan(all_dscr_mc_values) 
            )
            num_iterations_for_global_proba = np.sum(global_criteria_valid_mask)

            if num_iterations_for_global_proba > 0:
                irr_proj_for_global_proba = all_irr_proj_mc_values[global_criteria_valid_mask]
                payback_equity_for_global_proba = all_payback_equity_mc_values[global_criteria_valid_mask]
                dscr_for_global_proba = all_dscr_mc_values[global_criteria_valid_mask] 
                
                global_success_irr = irr_proj_for_global_proba >= min_irr_projet_mc_decimal_threshold # UTILISATION CORRIGÉE
                global_success_payback = payback_equity_for_global_proba <= payback_max_equity_mc_threshold
                global_success_dscr = (dscr_for_global_proba >= target_dscr_mc_threshold) | np.isinf(dscr_for_global_proba) # UTILISATION CORRIGÉE
                
                num_overall_global_successes = np.sum(global_success_irr & global_success_payback & global_success_dscr)
                mc_probabilities_summary['global'] = num_overall_global_successes / num_iterations_for_global_proba if num_iterations_for_global_proba > 0 else 0.0
            else:
                mc_probabilities_summary['global'] = 0.0

            for indicator_key_stat in mc_tracked_indicators:
                iteration_values_np_array = np.array(mc_iteration_results[f"{indicator_key_stat}_values"])
                finite_values_for_stats = iteration_values_np_array[np.isfinite(iteration_values_np_array)] 
                
                if len(finite_values_for_stats) > 0:
                    mc_stats_summary[indicator_key_stat] = {
                        'mean': np.mean(finite_values_for_stats), 'std': np.std(finite_values_for_stats),
                        'p': np.percentile(finite_values_for_stats, [5, 25, 50, 75, 95]).tolist(),
                        'n_valid_finite': len(finite_values_for_stats)
                    }
                    individual_proba_val = np.nan 
                    all_valid_values_for_proba_ind = iteration_values_np_array[~np.isnan(iteration_values_np_array)]
                    if len(all_valid_values_for_proba_ind) > 0:
                        if indicator_key_stat == 'irr_project': 
                            individual_proba_val = np.mean(all_valid_values_for_proba_ind[np.isfinite(all_valid_values_for_proba_ind)] >= min_irr_projet_mc_decimal_threshold) # UTILISATION CORRIGÉE
                        elif indicator_key_stat == 'payback_period': 
                            individual_proba_val = np.mean(all_valid_values_for_proba_ind[np.isfinite(all_valid_values_for_proba_ind)] <= payback_max_equity_mc_threshold)
                        elif indicator_key_stat == 'avg_dscr':
                            individual_proba_val = np.mean((all_valid_values_for_proba_ind >= target_dscr_mc_threshold) | np.isinf(all_valid_values_for_proba_ind)) # UTILISATION CORRIGÉE
                    mc_probabilities_summary[indicator_key_stat] = float(individual_proba_val) if pd.notna(individual_proba_val) else 0.0
                else: 
                    mc_stats_summary[indicator_key_stat] = {'mean': np.nan, 'std': np.nan, 'p': [np.nan]*5, 'n_valid_finite': 0}
                    mc_probabilities_summary[indicator_key_stat] = 0.0
            
            monte_carlo_final_output_summary = {
                'scenario_name': scenario_name,
                'prix_revente_simule_ht': prix_revente,
                'n_iterations_demandees': n_iterations_mc,
                'n_runs_pour_proba_globale': num_iterations_for_global_proba,
                'ecart_type_production_pct_utilise': ecart_type_prod_pct_mc * 100,
                'ecart_type_consommation_pct_utilise': ecart_type_conso_pct_mc * 100,
                'results_all_iterations': mc_iteration_results, 
                'statistics': mc_stats_summary, 
                'probabilities': mc_probabilities_summary, 
                'contraintes_mc_cibles_appliquees': { 
                    'min_irr_project_pct': min_irr_projet_mc_pct_threshold,
                    'payback_max_equity_annees': payback_max_equity_mc_threshold,
                    'dscr_moyen_min': target_dscr_mc_threshold
                }
            }
            end_time_mc = time.time() # CORRIGÉ: variable de fin cohérente
            print(f"LOGIQUE MC: Monte Carlo Terminé en {end_time_mc - start_time_mc:.2f} sec. Runs avec critères globaux valides: {num_iterations_for_global_proba}/{n_iterations_mc}")
            return monte_carlo_final_output_summary

        except (ValueError, TypeError, RuntimeError) as e_mc_main_logic:
            print(f"ERREUR LOGIQUE (run_monte_carlo): {e_mc_main_logic}")
            traceback.print_exc()
            return {'error': f"Erreur logique Monte Carlo: {str(e_mc_main_logic)}"}
        except Exception as e_mc_unexp_logic:
            print(f"ERREUR LOGIQUE INATTENDUE (run_monte_carlo): {e_mc_unexp_logic}")
            traceback.print_exc()
            return {'error': f"Erreur inattendue Monte Carlo: {str(e_mc_unexp_logic)}"}

# --- Fin classe OptimizationLogic ---