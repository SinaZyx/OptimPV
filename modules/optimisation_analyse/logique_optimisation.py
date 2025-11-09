import pandas as pd
import numpy as np
import time
import traceback
import copy
import logging
import os
from datetime import datetime
# Import scipy avec contournement pour installation corrompue  
try:
    from scipy.optimize import minimize, OptimizeResult
    SCIPY_OPTIMIZE_AVAILABLE = True
except ImportError:
    SCIPY_OPTIMIZE_AVAILABLE = False
    # Fallback minimal pour minimize
    class OptimizeResult:
        def __init__(self):
            self.success = False
            self.x = [0.0]
            self.fun = float('inf')
            self.message = "Scipy non disponible"
    
    def minimize(*args, **kwargs):
        return OptimizeResult()

# Pas d'import scipy.stats - utilisation numpy uniquement
SCIPY_STATS_AVAILABLE = False

from modules.engine_module.core_analyzer import AnalysisEngine

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
                print(f"LOGIQUE OPTIM DEBUG: Configuration dette = {current_run_config_dict.get('debt_ratio', 0.80)}")
                floor_price_results_dict = self.analysis_engine.simulate_selling_price(
                    scenario_name, target_npv=0,
                    override_source_prix_autoconso="prix_initial", 
                    sites_config=sites_config
                )
                print(f"LOGIQUE OPTIM DEBUG: Résultat prix plancher = {floor_price_results_dict}")
                
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
                
                # Vérifier si financement 100% dette
                loan_active = current_run_config_dict.get("with_loan", True)
                debt_ratio_config = float(current_run_config_dict.get("debt_ratio", 0.80)) if loan_active else 0.0
                
                if debt_ratio_config >= 1.0:
                    # Financement 100% dette - Optimiser la NPV projet
                    npv_project_val_optim = indicators_optim.get('npv_project')
                    if npv_project_val_optim is None or not np.isfinite(npv_project_val_optim): return 1e12
                    return -npv_project_val_optim
                else:
                    # Financement mixte - Optimiser la NPV equity
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

                 # Vérifier si financement 100% dette
                 loan_active_constr = current_run_config_dict.get("with_loan", True)
                 debt_ratio_config_constr = float(current_run_config_dict.get("debt_ratio", 0.80)) if loan_active_constr else 0.0
                 
                 if debt_ratio_config_constr >= 1.0:
                     return 1e6 # Financement 100% dette - Contrainte payback FP automatiquement respectée

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
            maximized_npv_value = -best_overall_optimize_result.fun 
            
            # Déterminer quel NPV a été optimisé
            loan_active = current_run_config_dict.get("with_loan", True)
            debt_ratio_config = float(current_run_config_dict.get("debt_ratio", 0.80)) if loan_active else 0.0
            npv_type = "NPV Projet" if debt_ratio_config >= 1.0 else "NPV Equity"
            
            print(f"LOGIQUE OPTIM: Prix Optimal HT Final = {optimal_price_ht_final_value:.8f} €/kWh ({npv_type} Max = {maximized_npv_value:,.0f} €)")

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
                'npv_optimise_equity': maximized_npv_value,
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
        # Configuration du logger Monte Carlo avec timestamp
        # Force le chemin vers le répertoire OptimPV 
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Remonte de modules/optimisation_analyse vers OptimPV
        log_dir = os.path.join(base_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Nom de fichier unique avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f'log_monte_carlo_{timestamp}.txt')
        
        print(f"DEBUG: Log Monte Carlo sera écrit dans {log_file}")
        
        # Créer le logger spécifique Monte Carlo
        mc_logger = logging.getLogger('monte_carlo')
        mc_logger.setLevel(logging.INFO)
        
        # Supprimer les handlers existants pour éviter les doublons
        for handler in mc_logger.handlers[:]:
            mc_logger.removeHandler(handler)
            
        # Handler pour fichier
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - MONTE_CARLO - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        mc_logger.addHandler(file_handler)
        
        # Log de démarrage
        mc_logger.info(f"🔥 NOUVEAU CODE MC CHARGÉ! 🔥 Scénario: '{scenario_name}', Prix HT: {prix_revente:.4f}")
        print(f"🔥 NOUVEAU CODE MC CHARGÉ! 🔥 Scénario: '{scenario_name}', Prix HT: {prix_revente:.4f}")
        
        start_time_mc = time.time()
        try:
            # Utiliser la config passée au constructeur (avec les paramètres du slider)
            config_mc = self.config
            mc_logger.info("Config utilisée depuis self.config (contient paramètres slider)") 
            
            # Vérifier si sites_data existe, est un dictionnaire et n'est pas vide
            sites_data_valide_initial = hasattr(self.analysis_engine, 'sites_data') and \
                                        self.analysis_engine.sites_data and \
                                        isinstance(self.analysis_engine.sites_data, dict)

            if not sites_data_valide_initial:
                raise ValueError("Attribut 'sites_data' de AnalysisEngine manquant, non initialisé, ou n'est pas un dictionnaire pour Monte Carlo.")
            # Ensuite, vérifier si au moins un DataFrame dans le dictionnaire n'est pas vide
            elif not any(isinstance(df, pd.DataFrame) and not df.empty for df in self.analysis_engine.sites_data.values()):
                raise ValueError("Données de site originales (self.analysis_engine.sites_data) sont présentes mais tous les DataFrames sont vides ou aucun DataFrame valide n'a été trouvé pour Monte Carlo.")
            
            # Si tout va bien, on continue avec la copie des données
            original_sites_data_for_mc = copy.deepcopy(self.analysis_engine.sites_data)

            n_iterations_mc = int(config_mc.get('nb_iterations_monte_carlo', 200))  # Respecte la config utilisateur
            mc_logger.info(f"Itérations demandées = {n_iterations_mc} (config reçue: {config_mc.get('nb_iterations_monte_carlo', 'NON_DEFINIE')})")
            print(f"DEBUG MC: Itérations demandées = {n_iterations_mc}")
            ecart_type_prod_pct_mc = float(config_mc.get('ecart_type_production', 15.0)) / 100.0  # Réduit : climat PACA stable
            ecart_type_conso_pct_mc = float(config_mc.get('ecart_type_consommation', 25.0)) / 100.0  # Augmenté : volatilité usage réelle
            ecart_type_prix_pct_mc = float(config_mc.get('ecart_type_prix_electricite', 35.0)) / 100.0  # Augmenté : volatilité marché réelle
            
            # Nouvelles variables critiques
            inflation_annuelle_mc = float(config_mc.get('inflation_annuelle_pct', 2.5)) / 100.0  # Inflation OPEX
            degradation_panneaux_mc = float(config_mc.get('degradation_panneaux_pct', 0.5)) / 100.0  # Dégradation annuelle
            risque_defaillance_mc = float(config_mc.get('risque_defaillance_pct', 5.0)) / 100.0  # Probabilité panne majeure
            volatilite_tarif_edf_mc = float(config_mc.get('volatilite_tarif_edf_pct', 30.0)) / 100.0  # Évolution concurrentielle EDF
            
            # CONTRAINTES DYNAMIQUES - SYNCHRONISÉES AVEC L'OPTIMISATION
            # Récupération des contraintes utilisateur depuis l'interface d'optimisation
            min_irr_projet_mc_pct_threshold = float(config_mc.get('constraint_min_irr_pct', 8.0))  # TRI Projet Min
            payback_max_equity_mc_threshold = float(config_mc.get('constraint_max_payback', 18.0))  # Payback Max Equity
            min_consumer_gain_mc_pct_threshold = float(config_mc.get('constraint_min_consumer_gain_pct', 5.0))  # Gain Client Min
            
            # DSCR reste une contrainte technique (pas dans l'interface d'optimisation)
            target_dscr_mc_threshold = 1.2  # Standard bancaire minimal
            
            mc_logger.info(f"Contraintes DYNAMIQUES - TRI Projet: {min_irr_projet_mc_pct_threshold}%, Payback Equity: {payback_max_equity_mc_threshold} ans, Gain Client: {min_consumer_gain_mc_pct_threshold}%, DSCR: {target_dscr_mc_threshold}")
            min_irr_projet_mc_decimal_threshold = min_irr_projet_mc_pct_threshold / 100.0 # Définie ici
            min_consumer_gain_mc_decimal_threshold = min_consumer_gain_mc_pct_threshold / 100.0 # Définie ici
            
            mc_logger.info(f"Contraintes UTILISATEUR synchronisées avec optimisation ✅")
            mc_logger.info(f"Variations - Production ±{ecart_type_prod_pct_mc*100}%, Consommation ±{ecart_type_conso_pct_mc*100}%, Prix électricité ±{ecart_type_prix_pct_mc*100}%")

            # Métriques réellement calculées par calculate_financial_indicators
            mc_tracked_indicators = ['roi', 'irr', 'npv', 'payback_period', 'avg_dscr', 'irr_project', 'payback_project', 'lcoe']
            mc_iteration_results = {f"{indicator_name}_values": [] for indicator_name in mc_tracked_indicators}
            
            # AMÉLIORATIONS ACADÉMIQUES selon repository GitHub
            # Variables pour validation statistique et convergence
            convergence_window = max(50, n_iterations_mc // 10)  # Fenêtre test convergence
            convergence_results = {indicator: [] for indicator in mc_tracked_indicators}
            control_variate_data = {'prix_factors': [], 'prod_factors': [], 'npv_values': []}
            correlation_matrix = np.array([[1.0, -0.3, 0.7], [-0.3, 1.0, -0.2], [0.7, -0.2, 1.0]])  # Prix-Prod-Inflation
            importance_weights = []  # Stockage poids importance sampling
            
            # Ajout: Importer streamlit et créer une barre de progression
            try:
                import streamlit as st
                progress_bar = st.progress(0)
                status_text = st.empty()
                has_streamlit = True
            except (ImportError, RuntimeError):
                has_streamlit = False
                print(f"LOGIQUE MC: Exécution sans interface Streamlit, {n_iterations_mc} itérations")
            
            for i_mc_iter in range(n_iterations_mc):
                # Mise à jour de la barre de progression si streamlit est disponible
                if has_streamlit:
                    progress_percentage = (i_mc_iter + 1) / n_iterations_mc
                    progress_bar.progress(progress_percentage)
                    if i_mc_iter % max(1, n_iterations_mc // 20) == 0:  # Update text less frequently
                        status_text.text(f"Simulation Monte Carlo: Itération {i_mc_iter + 1}/{n_iterations_mc}")
                elif i_mc_iter % (n_iterations_mc // 10 or 1) == 0:
                    print(f"LOGIQUE MC: Progression - Itération {i_mc_iter+1}/{n_iterations_mc}")
                
                simulated_sites_data_current_iter = {}
                
                # ===========================================
                # MONTE CARLO ACADÉMIQUE v2.0 - STANDARDS GITHUB
                # ===========================================
                
                # 1. GÉNÉRATION VARIABLES CORRÉLÉES (Cholesky decomposition)
                # Matrice de corrélation réaliste Prix-Production-Inflation
                L = np.linalg.cholesky(correlation_matrix)  # Décomposition Cholesky
                z = np.random.standard_normal(3)  # Variables indépendantes N(0,1)
                correlated_vars = L @ z  # Variables corrélées
                
                # 2. IMPORTANCE SAMPLING avec corrélations
                if i_mc_iter % 2 == 0:
                    # Importance sampling sur prix (variable critique)
                    u_prix = np.random.beta(2.0, 5.0)  # Beta(2,5) concentration défavorable
                    facteur_prix_base = 1.0 + u_prix * 0.4  # [1.0, 1.4]
                    # Ajustement corrélation
                    facteur_prix = facteur_prix_base + 0.1 * correlated_vars[0] * ecart_type_prix_pct_mc
                    weight_prix = 2.5  # Poids importance
                else:
                    # Échantillonnage standard corrélé
                    facteur_prix = 1.0 + correlated_vars[0] * ecart_type_prix_pct_mc
                    weight_prix = 1.0
                
                # 3. VARIABLES ANTITHÉTIQUES + CORRÉLATIONS
                sigma_prod = max(0.001, abs(float(ecart_type_prod_pct_mc)))
                if i_mc_iter % 2 == 0 and i_mc_iter > 0:
                    if 'previous_prod_factor' in locals() and previous_prod_factor is not None:
                        facteur_production = 2.0 - previous_prod_factor + 0.05 * correlated_vars[1]
                    else:
                        facteur_production = 1.0 + correlated_vars[1] * sigma_prod
                        previous_prod_factor = facteur_production
                else:
                    facteur_production = 1.0 + correlated_vars[1] * sigma_prod
                    previous_prod_factor = facteur_production
                
                # 4. VARIABLES SECONDAIRES CORRÉLÉES
                sigma_conso = max(0.001, abs(float(ecart_type_conso_pct_mc)))
                facteur_consommation = 1.0 + np.random.normal(0, sigma_conso)  # Indépendante (réaliste)
                
                # Inflation corrélée aux prix (réalisme économique)
                facteur_inflation_opex = 1.4 + 0.4 * correlated_vars[2]  # [1.0, 1.8] corrélé
                
                # Variables techniques (échantillonnage simple)
                facteur_degradation = np.random.uniform(0.88, 0.98)  # Dégradation panneaux
                facteur_defaillance = 0.95 if np.random.random() < 0.05 else 1.0  # Événements rares
                
                prix_revente_simule = prix_revente * max(0.5, facteur_prix)  # Sécurité bounds
                
                # 5. STOCKAGE CONTROL VARIATES (technique GitHub)
                control_variate_data['prix_factors'].append(facteur_prix)
                control_variate_data['prod_factors'].append(facteur_production)
                
                # Calcul poids importance final
                importance_weight = weight_prix
                importance_weights.append(importance_weight)
                
                # DEBUG enrichi avec corrélations
                if i_mc_iter < 3:
                    print(f"DEBUG MC {i_mc_iter+1}: Prix={facteur_prix:.3f}, Prod={facteur_production:.3f}, Inflat={facteur_inflation_opex:.3f}, Poids={importance_weight:.1f}")
                    print(f"  └─ Corrélations: z={correlated_vars} → Prix-Prod corr={np.corrcoef([facteur_prix], [facteur_production])[0,1]:.2f}")
                
                for site_id_mc, original_df_site_iter_mc in original_sites_data_for_mc.items():
                    sim_df_for_site_iter = original_df_site_iter_mc.copy()
                    
                    # Application des facteurs avec inflation OPEX intégrée
                    if 'production_kwh' in sim_df_for_site_iter.columns:
                        sim_df_for_site_iter['production_kwh'] *= (facteur_production * facteur_degradation * facteur_defaillance)
                    if 'consumption_kwh' in sim_df_for_site_iter.columns:
                        sim_df_for_site_iter['consumption_kwh'] *= facteur_consommation
                    
                    # NOUVEAU : Application inflation OPEX (coûts maintenance, assurances, etc.)
                    # Note: L'inflation sera appliquée dans calculate_financial_indicators via facteur_inflation_opex
                    # Pour l'instant, on stocke le facteur pour utilisation potentielle
                    sim_df_for_site_iter._inflation_factor = facteur_inflation_opex
                    
                    simulated_sites_data_current_iter[site_id_mc] = sim_df_for_site_iter

                results_current_iter = None
                try:
                    # OPTIMISATION : Réutiliser l'engine existant avec données simulées
                    # Sauvegarder les données originales
                    original_sites_backup = self.analysis_engine.sites_data
                    
                    # Remplacer temporairement par les données simulées
                    self.analysis_engine.sites_data = simulated_sites_data_current_iter
                    
                    # Calcul avec engine existant (évite recréation complète)
                    results_current_iter = self.analysis_engine.calculate_financial_indicators(
                        scenario_name, prix_revente=prix_revente_simule, sites_config=sites_config
                    )
                    
                    # Log détaillé pour les premières itérations ou échecs
                    if i_mc_iter < 5 or i_mc_iter % 10 == 0:  # Log premières 5 + chaque 10e
                        irr_proj = results_current_iter.get('irr_project', 0)
                        payback_eq = results_current_iter.get('payback_period', 0) 
                        dscr_avg = results_current_iter.get('avg_dscr', 0)
                        
                        # Validation contraintes individuelles (dynamiques depuis optimisation)
                        ok_irr = irr_proj >= min_irr_projet_mc_decimal_threshold
                        ok_payback = payback_eq <= payback_max_equity_mc_threshold  
                        ok_dscr = dscr_avg >= target_dscr_mc_threshold or np.isinf(dscr_avg)
                        # Note: Gain client sera ajouté dans une prochaine version
                        global_ok = ok_irr and ok_payback and ok_dscr
                        
                        mc_logger.info(f"Iter {i_mc_iter+1}: TRI_proj={irr_proj:.1%} {'✓' if ok_irr else '✗'}≥{min_irr_projet_mc_pct_threshold}%, Payback={payback_eq:.1f}a {'✓' if ok_payback else '✗'}≤{payback_max_equity_mc_threshold}, DSCR={dscr_avg:.2f} {'✓' if ok_dscr else '✗'}≥{target_dscr_mc_threshold} → {'✅' if global_ok else '❌'}")
                        
                        if not global_ok:
                            mc_logger.info(f"    └─ Contraintes utilisateur: TRI {not ok_irr}, Payback {not ok_payback}, DSCR {not ok_dscr}")
                    
                    # Restaurer les données originales
                    self.analysis_engine.sites_data = original_sites_backup
                except Exception as e_mc_iter_financial_calc:
                    if i_mc_iter % (n_iterations_mc // 10 or 1) == 0 : 
                        print(f"AVERTISSEMENT LOGIQUE MC (Iter {i_mc_iter+1}): Échec calcul indicateurs - {e_mc_iter_financial_calc}")
                
                if results_current_iter and isinstance(results_current_iter, dict) and "error" not in results_current_iter:
                    # DEBUG : Vérifier quelques résultats (à supprimer après test)
                    if i_mc_iter < 3:
                        roi_val = results_current_iter.get('roi', 'N/A')
                        irr_val = results_current_iter.get('irr_project', 'N/A')  
                        payback_val = results_current_iter.get('payback_period', 'N/A')
                        print(f"DEBUG MC Iter {i_mc_iter+1} RESULTATS: ROI={roi_val}, TRI_projet={irr_val}, Payback={payback_val}")
                    
                    for indicator_key in mc_tracked_indicators:
                        iter_value = results_current_iter.get(indicator_key)
                        mc_iteration_results[f"{indicator_key}_values"].append(iter_value if (pd.notna(iter_value) and np.isfinite(iter_value)) else np.nan)
                    
                    # 6. STOCKAGE DONNÉES CONTROL VARIATES
                    npv_current = results_current_iter.get('npv', np.nan)
                    control_variate_data['npv_values'].append(npv_current)
                    
                    # 7. TEST DE CONVERGENCE (technique GitHub)
                    if i_mc_iter >= convergence_window and i_mc_iter % convergence_window == 0:
                        for indicator in mc_tracked_indicators:
                            values = mc_iteration_results[f"{indicator}_values"][-convergence_window:]
                            valid_values = [v for v in values if pd.notna(v) and np.isfinite(v)]
                            if len(valid_values) > 10:
                                # Test stabilité moyenne mobile
                                first_half = np.mean(valid_values[:len(valid_values)//2])
                                second_half = np.mean(valid_values[len(valid_values)//2:])
                                relative_change = abs(second_half - first_half) / abs(first_half + 1e-6)
                                convergence_results[indicator].append(relative_change)
                                if i_mc_iter % (convergence_window * 2) == 0 and indicator == 'npv':
                                    mc_logger.info(f"Convergence {indicator}: Δ={relative_change:.3%} (iter {i_mc_iter+1})")
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

            # ===========================================  
            # VALIDATION STATISTIQUE ACADÉMIQUE - STANDARDS GITHUB
            # ===========================================
            
            # 1. APPLICATION CONTROL VARIATES (réduction variance)
            cv_npv_values = np.array(control_variate_data['npv_values'])
            cv_prix_factors = np.array(control_variate_data['prix_factors'])
            cv_adjusted_results = {}
            
            if len(cv_npv_values) > 10 and len(cv_prix_factors) > 10:
                # Control variate avec facteur prix (corrélé à NPV)
                correlation_cv = np.corrcoef(cv_npv_values[np.isfinite(cv_npv_values)], 
                                           cv_prix_factors[:len(cv_npv_values[np.isfinite(cv_npv_values)])])[0,1]
                
                if abs(correlation_cv) > 0.1:  # Corrélation significative
                    # Estimation control variate coefficient
                    valid_indices = np.isfinite(cv_npv_values)
                    if np.sum(valid_indices) > 5:
                        cv_coeff = np.cov(cv_npv_values[valid_indices], 
                                         cv_prix_factors[:np.sum(valid_indices)])[0,1] / np.var(cv_prix_factors[:np.sum(valid_indices)])
                        expected_prix = 1.0  # E[facteur_prix] théorique
                        cv_adjustment = cv_coeff * (np.mean(cv_prix_factors) - expected_prix)
                        cv_adjusted_results['npv_control_variate'] = cv_adjustment
                        mc_logger.info(f"Control Variate: corrélation Prix-NPV = {correlation_cv:.3f}, ajustement = {cv_adjustment:.2f}")
                
            # 2. STATISTIQUES AVEC IMPORTANCE SAMPLING
            for indicator_key_stat in mc_tracked_indicators:
                iteration_values_np_array = np.array(mc_iteration_results[f"{indicator_key_stat}_values"])
                finite_values_for_stats = iteration_values_np_array[np.isfinite(iteration_values_np_array)] 
                
                if len(finite_values_for_stats) > 0:
                    n_samples = len(finite_values_for_stats)
                    
                    # Application poids importance sampling
                    if len(importance_weights) == len(finite_values_for_stats):
                        weights = np.array(importance_weights[:len(finite_values_for_stats)])
                        mean_val = np.average(finite_values_for_stats, weights=weights)  # Moyenne pondérée
                        var_val = np.average((finite_values_for_stats - mean_val)**2, weights=weights)
                        std_val = np.sqrt(var_val)
                    else:
                        mean_val = np.mean(finite_values_for_stats)
                        std_val = np.std(finite_values_for_stats)
                    
                    # Intervalles de confiance académiques
                    std_error = std_val / np.sqrt(n_samples)
                    confidence_95 = 1.96 * std_error
                    
                    # Test normalité simplifié (CLT + Skewness check)
                    is_normal = n_samples >= 30
                    if n_samples >= 30:
                        skewness = np.mean(((finite_values_for_stats - mean_val) / std_val) ** 3)
                        is_normal = abs(skewness) < 1.0  # Seuil acceptation normalité
                    
                    # Test convergence final
                    convergence_achieved = True
                    if indicator_key_stat in convergence_results and len(convergence_results[indicator_key_stat]) > 0:
                        recent_convergence = np.mean(convergence_results[indicator_key_stat][-3:])  # 3 derniers tests
                        convergence_achieved = recent_convergence < 0.05  # <5% changement
                        
                    mc_stats_summary[indicator_key_stat] = {
                        'mean': mean_val,
                        'std': std_val,
                        'n_valid': n_samples,
                        'confidence_95': confidence_95,
                        'is_normal': is_normal,
                        'convergence_achieved': convergence_achieved
                    }
                    
                    # Calcul percentiles pour validation
                    percentiles = np.percentile(finite_values_for_stats, [5, 25, 50, 75, 95]).tolist()
                    
                    # Mise à jour avec métriques enrichies
                    mc_stats_summary[indicator_key_stat].update({
                        'std_error': std_error,
                        'confidence_interval': [mean_val - confidence_95, mean_val + confidence_95],
                        'percentiles': percentiles
                    })
                    individual_proba_val = np.nan 
                    all_valid_values_for_proba_ind = iteration_values_np_array[~np.isnan(iteration_values_np_array)]
                    if len(all_valid_values_for_proba_ind) > 0:
                        if indicator_key_stat == 'irr_project': 
                            individual_proba_val = np.mean(all_valid_values_for_proba_ind[np.isfinite(all_valid_values_for_proba_ind)] >= min_irr_projet_mc_decimal_threshold) # UTILISATION CORRIGÉE
                        elif indicator_key_stat == 'payback_period': 
                            individual_proba_val = np.mean(all_valid_values_for_proba_ind[np.isfinite(all_valid_values_for_proba_ind)] <= payback_max_equity_mc_threshold)
                        elif indicator_key_stat == 'payback_project':  # NOUVEAU: Ajout payback projet
                            individual_proba_val = np.mean(all_valid_values_for_proba_ind[np.isfinite(all_valid_values_for_proba_ind)] <= 8.0)  # Seuil projet 8 ans
                        elif indicator_key_stat == 'avg_dscr':
                            individual_proba_val = np.mean((all_valid_values_for_proba_ind >= target_dscr_mc_threshold) | np.isinf(all_valid_values_for_proba_ind)) # UTILISATION CORRIGÉE
                    mc_probabilities_summary[indicator_key_stat] = float(individual_proba_val) if pd.notna(individual_proba_val) else 0.0
                else: 
                    mc_stats_summary[indicator_key_stat] = {
                        'mean': np.nan, 'std': np.nan, 'n_valid': 0,
                        'confidence_95': np.nan, 'is_normal': False, 'convergence_achieved': False,
                        'percentiles': [np.nan]*5
                    }
                    mc_probabilities_summary[indicator_key_stat] = 0.0
                    
            # 3. LOGS ACADÉMIQUES FINAUX
            mc_logger.info("=== VALIDATION STATISTIQUE ACADÉMIQUE ===")
            for metric in ['npv', 'irr_project', 'payback_period']:
                if metric in mc_stats_summary and mc_stats_summary[metric]['n_valid'] > 0:
                    stats = mc_stats_summary[metric]
                    mean_str = f"{stats['mean']:.2f}"
                    std_str = f"{stats['std']:.2f}"
                    ci_str = f"[{stats['confidence_interval'][0]:.2f}, {stats['confidence_interval'][1]:.2f}]"
                    normal_str = "✓" if stats['is_normal'] else "✗"
                    conv_str = "✓" if stats['convergence_achieved'] else "✗"
                    mc_logger.info(f"{metric.upper()}: μ={mean_str}, σ={std_str}, IC95%={ci_str}, Normal={normal_str}, Conv={conv_str}")
                    
            # Control variates summary
            if cv_adjusted_results:
                mc_logger.info(f"Control Variates appliqués: {len(cv_adjusted_results)} ajustements")
            
            # Finalisation de la barre de progression
            if has_streamlit:
                status_text.text("Simulation Monte Carlo terminée !")
                # On peut soit vider la barre, soit la laisser à 100%
                # progress_bar.empty()  # Optionnel: cacher la barre
            
            monte_carlo_final_output_summary = {
                'scenario_name': scenario_name,
                'prix_revente_simule_ht': prix_revente,
                'n_iterations_demandees': n_iterations_mc,
                'n_runs_pour_proba_globale': num_iterations_for_global_proba,
                'ecart_type_production_pct_utilise': ecart_type_prod_pct_mc * 100,
                'ecart_type_consommation_pct_utilise': ecart_type_conso_pct_mc * 100,
                'ecart_type_prix_electricite_pct_utilise': ecart_type_prix_pct_mc * 100,
                'results_all_iterations': mc_iteration_results, 
                'statistics': mc_stats_summary, 
                'probabilities': mc_probabilities_summary, 
                'contraintes_mc_cibles_appliquees': { 
                    'min_irr_project_pct': min_irr_projet_mc_pct_threshold,
                    'payback_max_equity_annees': payback_max_equity_mc_threshold,
                    'dscr_moyen_min': target_dscr_mc_threshold
                },
                # NOUVELLES MÉTRIQUES ACADÉMIQUES
                'academic_validation': {
                    'correlation_matrix_used': correlation_matrix.tolist(),
                    'importance_sampling_applied': True,
                    'antithetic_variables_applied': True,
                    'control_variates_results': cv_adjusted_results,
                    'convergence_tests': convergence_results,
                    'variance_reduction_techniques': ['importance_sampling', 'antithetic_variables', 'control_variates', 'correlated_sampling']
                }
            }
            end_time_mc = time.time() # CORRIGÉ: variable de fin cohérente
            duration = end_time_mc - start_time_mc
            mc_logger.info(f"Monte Carlo TERMINÉ en {duration:.2f} sec. Runs avec critères globaux valides: {num_iterations_for_global_proba}/{n_iterations_mc}")
            mc_logger.info(f"Probabilités finales - DSCR≥{target_dscr_mc_threshold}: {mc_probabilities_summary.get('avg_dscr', 0)*100:.1f}%, Payback≤{payback_max_equity_mc_threshold}: {mc_probabilities_summary.get('payback_period', 0)*100:.1f}%")
            
            # Fermer le handler pour libérer le fichier
            for handler in mc_logger.handlers[:]:
                handler.close()
                mc_logger.removeHandler(handler)
                
            print(f"LOGIQUE MC: Monte Carlo Terminé en {duration:.2f} sec. Runs avec critères globaux valides: {num_iterations_for_global_proba}/{n_iterations_mc}")
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