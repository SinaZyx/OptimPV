import pandas as pd
import numpy as np
import time
import traceback
import copy
from scipy.optimize import minimize, OptimizeResult

try:
    from modules.analysis_engine import AnalysisEngine
except ImportError as e:
    print(f"ERREUR LOGIQUE: Import AnalysisEngine échoué : {e}")
    # Définir une classe factice si l'import échoue
    class AnalysisEngine:
        def __init__(self, *args, **kwargs):
            print("ERREUR: AnalysisEngine n'a pas pu être chargé.")
            self.scenarios = {}
            self.config = {}
            self.sites_data = {}
        def calculate_financial_indicators(self, *args, **kwargs):
            print("ERREUR: calculate_financial_indicators non disponible.")
            return None
        def simulate_selling_price(self, *args, **kwargs):
            print("ERREUR: simulate_selling_price non disponible.")
            return None

class OptimizationLogic:
    """Logique pour l'optimisation du prix et l'analyse de sensibilité."""

    def __init__(self, config: dict, analysis_engine: AnalysisEngine):
        if not isinstance(config, dict):
            raise TypeError("config doit être un dict")
        if not isinstance(analysis_engine, AnalysisEngine):
            raise TypeError("analysis_engine doit être une instance de AnalysisEngine")
        self.config = config
        self.analysis_engine = analysis_engine
        self.indicators_cache = {} # Cache simplifié

    # --- find_optimal_price_constrained (MODIFIÉ) ---
    def find_optimal_price_constrained(self,
                                       scenario_name: str,
                                       tri_projet_min_pct_constraint: float,
                                       sites_config: dict | None = None # <-- AJOUTER ARGUMENT
                                      ) -> dict | None:
        """
        Optimise le prix de revente pour maximiser la NPV Equity,
        tout en respectant les contraintes fournies.
        Utilise sites_config pour les calculs internes via analysis_engine.
        """
        print(f"LOGIQUE: Lancement Optimisation sous Contraintes pour Scénario: {scenario_name}")
        start_time_optim = time.time()

        try:
            config = self.config # Config globale pour certains params

            # --- 1. Récupérer paramètres et contraintes (inchangé) ---
            try:
                min_irr_pct = float(tri_projet_min_pct_constraint)
                min_irr = min_irr_pct / 100.0
                max_payback = float(config.get('constraint_max_payback', 18.0))
                min_consumer_gain_pct = float(config.get('constraint_min_consumer_gain_pct', 5.0))
                tarif_edf_ref = float(config.get('tarif_edf_reference', 0.22))
                prix_max_config = float(config.get('prix_max_revente', tarif_edf_ref))

                # --- Calcul Prix Plancher (borne inf) ---
                print("LOGIQUE: Calcul préalable du Prix Plancher (VAN=0)...")
                # --- MODIFIÉ : Passer sites_config à l'appel ---
                floor_results = self.analysis_engine.simulate_selling_price(
                    scenario_name,
                    target_npv=0,
                    override_source_prix_autoconso="prix_initial",
                    sites_config=sites_config # <-- PASSER sites_config ICI
                )
                # --- FIN MODIFICATION ---

                if not floor_results or floor_results.get('prix_revente_optimal_pour_cible') is None:
                    print("LOGIQUE: Calcul fallback LCOE car prix plancher VAN=0 échoué.")
                    # --- MODIFIÉ : Passer sites_config aussi au fallback ---
                    lcoe_fallback_results = self.analysis_engine.calculate_financial_indicators(
                        scenario_name,
                        prix_revente=config.get("prix_vente_initial", 0.15),
                        sites_config=sites_config # <-- PASSER sites_config ICI AUSSI
                    )
                    # --- FIN MODIFICATION ---
                    lcoe_estime = lcoe_fallback_results.get('lcoe') if lcoe_fallback_results else None
                    if lcoe_estime is None: raise ValueError("Calcul LCOE (borne inf) impossible.")
                    prix_min_optim = lcoe_estime
                    print(f"AVERTISSEMENT LOGIQUE: Prix plancher VAN=0 échoué, utilisation LCOE={lcoe_estime:.4f} comme borne inf.")
                else:
                    prix_min_optim = floor_results['prix_revente_optimal_pour_cible']
                    lcoe_estime = floor_results.get('lcoe_associated') or floor_results.get('lcoe', prix_min_optim)
                    print(f"LOGIQUE: Prix plancher VAN=0 trouvé: {prix_min_optim:.4f} € (LCOE estimé: {lcoe_estime:.4f} €)")

                prix_max_theorique_conso = tarif_edf_ref * (1.0 - min_consumer_gain_pct / 100.0)
                prix_max_optim = min(prix_max_config, prix_max_theorique_conso)
                if prix_min_optim >= prix_max_optim:
                    if abs(prix_min_optim - prix_max_optim) < 1e-4: prix_max_optim = prix_min_optim + 1e-4
                    else: raise ValueError(f"Plage recherche invalide [{prix_min_optim:.4f}, {prix_max_optim:.4f}] après contrainte gain client.")
                print(f"LOGIQUE: Bornes recherche prix: [{prix_min_optim:.4f}, {prix_max_optim:.4f}]")

            except (ValueError, TypeError, KeyError, RuntimeError) as e:
                raise ValueError(f"Erreur récupération paramètres/contraintes/bornes: {e}") from e

            # --- 2. Objectif et Contraintes pour scipy.optimize ---
            memoized_indicators = {} # Nouveau cache interne pour cette optimisation
            # --- NOUVELLE FONCTION HELPER INTERNE ---
            def get_indicators_with_site_config(price: float, scenario: str) -> dict | None:
                 # Utiliser une clé plus robuste (float peut avoir des imprécisions)
                 price_key = round(price, 8) # Arrondir pour la clé de cache
                 cache_key = (scenario, price_key)
                 if cache_key in memoized_indicators:
                     return memoized_indicators[cache_key]
                 try:
                      # APPEL INTERNE AVEC sites_config
                      results = self.analysis_engine.calculate_financial_indicators(
                          scenario,
                          prix_revente=price,
                          sites_config=sites_config # <-- PASSER sites_config
                      )
                      memoized_indicators[cache_key] = results
                      return results
                 except Exception as e:
                      # Décommenter si besoin de tracer les erreurs internes
                      # print(f"ERREUR LOGIQUE (get_indicators_with_site_config) prix {price:.4f}: {e}")
                      memoized_indicators[cache_key] = None # Cache l'échec aussi
                      return None
            # --- FIN NOUVELLE FONCTION HELPER ---

            # Utiliser la nouvelle fonction interne dans les objectifs/contraintes
            def objective_function(price_array):
                price = price_array[0]
                indicators = get_indicators_with_site_config(price, scenario_name)
                if indicators is None or indicators.get('npv') is None or not np.isfinite(indicators['npv']):
                    # print(f"DEBUG: Objectif - NPV invalide pour prix {price:.4f}")
                    return 1e12 # Forte pénalité si NPV invalide
                # print(f"DEBUG: Objectif - Prix {price:.4f}, NPV {-indicators['npv']:.2f}")
                return -indicators['npv']

            constraints = []
            def irr_constraint(price_array):
                 price = price_array[0]
                 indicators = get_indicators_with_site_config(price, scenario_name)
                 if indicators is None or indicators.get('irr_project') is None:
                     # print(f"DEBUG: Contrainte IRR - indicateurs invalides pour prix {price:.4f}")
                     return -1e6 # Considéré comme non respecté si non calculable
                 irr_val = indicators['irr_project']
                 if not np.isfinite(irr_val):
                     # print(f"DEBUG: Contrainte IRR - IRR non fini pour prix {price:.4f}")
                     return -1e6 # Non respecté si IRR infini/NaN
                 constraint_value = irr_val - min_irr
                 # print(f"DEBUG: Contrainte IRR - Prix {price:.4f}, IRR={irr_val:.4f}, Cible={min_irr:.4f}, Val={constraint_value:.4f}")
                 return constraint_value # >= 0 pour être valide
            constraints.append({'type': 'ineq', 'fun': irr_constraint})

            def payback_constraint(price_array):
                 price = price_array[0]
                 indicators = get_indicators_with_site_config(price, scenario_name)
                 if indicators is None or indicators.get('payback_period') is None:
                     # print(f"DEBUG: Contrainte Payback - indicateurs invalides pour prix {price:.4f}")
                     return -1e6 # Non respecté si non calculable
                 payback = indicators['payback_period']
                 # Vérifier durée simu (par exemple, si le payback est calculé sur la durée)
                 duree_simu = len(indicators.get('monthly_data', []))
                 if not np.isfinite(payback) or (duree_simu > 0 and payback > (duree_simu / 12.0) + 1e-6):
                      # print(f"DEBUG: Contrainte Payback - Payback={payback} non fini ou > durée simu pour prix {price:.4f}")
                      return -1e6 # Non respecté si infini, NaN, ou > durée
                 constraint_value = max_payback - payback
                 # print(f"DEBUG: Contrainte Payback - Prix {price:.4f}, Payback={payback:.2f}, Cible={max_payback:.2f}, Val={constraint_value:.2f}")
                 return constraint_value # >= 0 pour être valide
            constraints.append({'type': 'ineq', 'fun': payback_constraint})

            if tarif_edf_ref > 1e-6:
                 min_gain_abs = tarif_edf_ref * (min_consumer_gain_pct / 100.0)
                 def consumer_gain_constraint(price_array):
                      price = price_array[0]
                      current_gain_abs = tarif_edf_ref - price # Gain absolu
                      constraint_value = current_gain_abs - min_gain_abs
                      # print(f"DEBUG: Contrainte Gain - Prix {price:.4f}, GainAbs={current_gain_abs:.4f}, CibleGain={min_gain_abs:.4f}, Val={constraint_value:.4f}")
                      return constraint_value # >= 0 pour être valide
                 constraints.append({'type': 'ineq', 'fun': consumer_gain_constraint})

            bounds = [(prix_min_optim, prix_max_optim)]

            # --- 3. Exécuter l'optimisation (logique multi-start inchangée) ---
            num_starts = 3; best_result: OptimizeResult | None = None; min_objective_value = float('inf')
            start_points = np.linspace(prix_min_optim, prix_max_optim, num_starts)
            print(f"LOGIQUE: Lancement optimisation SLSQP avec {num_starts} points de départ...")
            memoized_indicators.clear() # Vider cache avant boucle minimize
            for i, start_price in enumerate(start_points):
                 start_price_clean = float(start_price) # S'assurer que c'est un float Python
                 print(f"  -> Départ {i+1}/{num_starts} : Prix initial = {start_price_clean:.6f}")
                 try:
                     result = minimize( objective_function, [start_price_clean], method='SLSQP', bounds=bounds, constraints=constraints, options={'ftol': 1e-8, 'disp': False, 'maxiter': 150} )
                     # Vérifier si le résultat est meilleur ET satisfait les contraintes
                     if result.success and result.fun < min_objective_value:
                          final_price_candidate = float(result.x[0])
                          # Vérification stricte des bornes
                          if not (bounds[0][0] - 1e-9 <= final_price_candidate <= bounds[0][1] + 1e-9):
                               print(f"     -> Rejeté (hors bornes): {final_price_candidate:.6f}")
                               continue
                          # Vérification explicite des contraintes
                          constraints_satisfied = True
                          for constraint in constraints:
                               constraint_value = constraint['fun']([final_price_candidate])
                               if constraint_value < -1e-6: # Tolérance numérique
                                    print(f"     -> Rejeté (contrainte non satisfaite à {final_price_candidate:.6f}, val={constraint_value:.4g})")
                                    constraints_satisfied = False
                                    break
                          if constraints_satisfied:
                               print(f"     -> Succès! Nouveau meilleur: obj={result.fun:.4f}, prix={final_price_candidate:.6f}")
                               min_objective_value = result.fun
                               best_result = result # Garder la meilleure solution valide
                     elif not result.success:
                          print(f"     -> Échec convergence (Départ {i+1}): {result.message}")
                 except Exception as e_minimize:
                     print(f"     -> Erreur pendant minimize (Départ {i+1}): {e_minimize}")

            # --- 4. Analyser le résultat (inchangé mais utilise best_result trouvé) ---
            if best_result is None:
                 msg = "Optimisation échouée: Aucune solution valide respectant les contraintes n'a été trouvée."
                 print(f"ERREUR LOGIQUE: {msg}")
                 raise RuntimeError(msg)
            elif not best_result.success:
                 print(f"AVERTISSEMENT LOGIQUE: L'optimiseur a terminé sans succès formel ({best_result.message}), mais une solution respectant les contraintes a été trouvée. Utilisation de cette solution.")

            optimal_price = float(best_result.x[0])
            # S'assurer que le prix est strictement dans les bornes pour éviter erreurs flottants
            optimal_price = max(bounds[0][0], min(bounds[0][1], optimal_price))
            final_npv = -best_result.fun # Objective était -NPV
            print(f"LOGIQUE: Optimisation terminée ! Prix Optimal Final = {optimal_price:.8f} € (NPV Max = {final_npv:,.0f} €)")

            # Recalcul final explicite avec le prix optimal trouvé et sites_config
            # Utilise la fonction helper interne qui gère le cache et sites_config
            print(f"LOGIQUE: Recalcul final des indicateurs au prix {optimal_price:.8f}...")
            final_indicators = get_indicators_with_site_config(optimal_price, scenario_name)
            if not final_indicators:
                # Tenter de recalculer sans cache si le premier a échoué?
                memoized_indicators.pop((scenario_name, round(optimal_price, 8)), None)
                final_indicators = get_indicators_with_site_config(optimal_price, scenario_name)
                if not final_indicators:
                    raise RuntimeError("Erreur recalcul final indicateurs au prix optimal")

            optimization_summary = {
                'scenario_name': scenario_name,
                'prix_optimal_const': optimal_price,
                'methode': 'Optimisation Contraintes (SLSQP)',
                'contraintes_appliquees': {
                    'min_irr_pct': min_irr_pct * 100, # Reconvertir en % pour UI
                    'max_payback': max_payback,
                    'min_consumer_gain_pct': min_consumer_gain_pct,
                    'borne_inf_prix': prix_min_optim,
                    'borne_sup_prix': prix_max_optim
                },
                'npv_optimise': final_npv,
                'lcoe_estime': lcoe_estime,
                'prix_plancher_producteur': prix_min_optim,
                'tarif_edf_reference': tarif_edf_ref,
                'indicateurs_au_prix_optimal': final_indicators,
                'optimisation_details': {
                    'success': best_result.success,
                    'message': best_result.message,
                    'status': best_result.status,
                    'nfev': best_result.nfev, # Nb eval func objectif
                    'njev': best_result.njev if hasattr(best_result, 'njev') else 0, # Nb eval jacobien
                    'nit': best_result.nit # Nb iterations
                }
            }
            end_time_optim = time.time()
            print(f"LOGIQUE: Optimisation terminée en {end_time_optim - start_time_optim:.2f} secondes.")
            return optimization_summary

        except (ValueError, TypeError, RuntimeError) as e:
            print(f"ERREUR LOGIQUE (find_optimal_price_constrained): {e}")
            # Renvoyer une structure d'erreur pour l'UI
            return {'error': f"Erreur logique: {e}"}
        except Exception as e:
            print(f"ERREUR LOGIQUE INATTENDUE (find_optimal_price_constrained): {e}")
            traceback.print_exc()
            return {'error': f"Erreur inattendue optimisation: {e}"}


    # --- run_monte_carlo_simulation (MODIFIÉ) ---
    def run_monte_carlo_simulation(self, scenario_name: str, prix_revente: float, sites_config: dict | None = None) -> dict | None: # <-- AJOUTER ARGUMENT
        """ Exécute une simulation Monte Carlo. Passe sites_config aux calculs internes. """
        print(f"LOGIQUE: Lancement Monte Carlo pour Scénario: {scenario_name} au prix {prix_revente:.4f}")
        start_time_mc = time.time()
        try:
            config = self.config
            # Utiliser self.analysis_engine.sites_data qui devrait être l'original
            if not hasattr(self.analysis_engine, 'sites_data') or not self.analysis_engine.sites_data:
                raise ValueError("Données de site originales non disponibles pour Monte Carlo.")
            original_sites_data = self.analysis_engine.sites_data # Données de référence

            n_iterations = int(config.get('nb_iterations_monte_carlo', 1000))
            ecart_type_production_pct = float(config.get('ecart_type_production', 10.0)) / 100.0
            ecart_type_consommation_pct = float(config.get('ecart_type_consommation', 5.0)) / 100.0
            # Utiliser les contraintes de la config GLOBALE pour les seuils MC
            target_dscr_mc = float(config.get('target_dscr', 1.2)) # Utiliser target_dscr de la config
            payback_max_mc = float(config.get('constraint_max_payback', 18.0))
            # Quelle cible IRR pour MC? Projet? Equity? Utilisons projet pour l'instant
            min_irr_target_pct = float(config.get('constraint_min_project_irr_pct', 8.0))
            min_irr_target = min_irr_target_pct / 100.0
            print(f"LOGIQUE (MC): Cibles - IRR Projet >= {min_irr_target_pct}%, Payback <= {payback_max_mc} ans, DSCR >= {target_dscr_mc}")

            tracked_indicators = ['roi', 'irr', 'npv', 'payback_period', 'avg_dscr', 'irr_project', 'payback_project', 'lcoe']
            results_mc = {f"{ind}_values": [] for ind in tracked_indicators}
            n_valid_runs = 0

            for i in range(n_iterations):
                simulated_sites_data_iter = {}
                for site_id, original_df_site in original_sites_data.items():
                    simulated_df_site = original_df_site.copy()
                    # Appliquer variation normale centrée sur 1
                    prod_factor = max(0, np.random.normal(1, ecart_type_production_pct))
                    cons_factor = max(0, np.random.normal(1, ecart_type_consommation_pct))
                    if 'production_kwh' in simulated_df_site.columns:
                        simulated_df_site['production_kwh'] *= prod_factor
                    if 'consumption_kwh' in simulated_df_site.columns:
                        simulated_df_site['consumption_kwh'] *= cons_factor
                    simulated_sites_data_iter[site_id] = simulated_df_site

                results_iter = None
                try:
                    # --- MODIFIÉ : Passer sites_config à l'engine temporaire ---
                    # Créer une instance TEMPORAIRE du moteur avec données simulées
                    # Note: Utiliser copy.deepcopy peut être lourd pour la config/scenarios
                    # Si config/scenarios ne sont pas modifiés par calculate_financial_indicators,
                    # on peut les passer directement.
                    temp_engine_iter = AnalysisEngine(
                        self.config, # Passer config originale (non modifiée a priori)
                        self.analysis_engine.scenarios, # Passer scenarios originaux
                        simulated_sites_data_iter # DONNÉES VARIÉES
                    )
                    # Appel à calculate_financial_indicators SUR CETTE INSTANCE TEMPORAIRE
                    # en passant le sites_config original (non varié)
                    results_iter = temp_engine_iter.calculate_financial_indicators(
                        scenario_name,
                        prix_revente=prix_revente,
                        sites_config=sites_config # <-- PASSER sites_config ici
                    )
                    # --- FIN MODIFICATION ---
                except Exception as iter_e:
                    # Limiter l'affichage des erreurs pour ne pas spammer la console
                    if i % 100 == 0 or i == n_iterations - 1:
                        print(f"AVERTISSEMENT LOGIQUE (MC Iter {i+1}): Échec calcul indicateurs - {iter_e}")

                # Stockage résultats MC
                valid_run_this_iter = False
                if results_iter and isinstance(results_iter, dict):
                    all_valid_for_iter = True; temp_results_for_iter = {}
                    for ind in tracked_indicators:
                        val = results_iter.get(ind)
                        # Vérifier si la valeur est valide (non-None, finie)
                        is_valid_val = val is not None and np.isfinite(val)
                        temp_results_for_iter[ind] = val if is_valid_val else np.nan
                        if not is_valid_val: all_valid_for_iter = False
                    # Ajouter toutes les valeurs (même NaN) pour garder la taille
                    for ind in tracked_indicators: results_mc[f"{ind}_values"].append(temp_results_for_iter[ind])
                    valid_run_this_iter = all_valid_for_iter
                else:
                     # Si results_iter est None, ajouter NaN pour tous les indicateurs
                     for ind in tracked_indicators: results_mc[f"{ind}_values"].append(np.nan)
                if valid_run_this_iter: n_valid_runs += 1

            # --- Traitement statistique (inchangé) ---
            stats = {}; probabilities = {}; all_values = {}
            print(f"LOGIQUE (MC): Traitement statistique sur {n_valid_runs} runs valides / {n_iterations} total.")
            for ind in tracked_indicators:
                values_with_nan = np.array(results_mc[f"{ind}_values"]) # Array complet
                all_values[f"{ind}_values"] = values_with_nan.tolist() # Sauvegarde pour retour
                valid_values = values_with_nan[~np.isnan(values_with_nan)] # Filtrer NaN pour stats
                if len(valid_values) > 0:
                    stats[ind] = {
                        'mean': np.mean(valid_values),
                        'std': np.std(valid_values),
                        'p': np.percentile(valid_values, [5, 25, 50, 75, 95]).tolist(),
                        'n_valid': len(valid_values)
                    }
                    # Calcul probabilités basé sur cibles MC
                    prob = np.nan
                    if ind == 'irr_project': prob = np.mean(valid_values >= min_irr_target)
                    elif ind == 'payback_period': prob = np.mean(valid_values <= payback_max_mc)
                    elif ind == 'avg_dscr':
                         # Gérer le cas np.inf pour DSCR (sans dette)
                         dscr_finite = valid_values[np.isfinite(valid_values)]
                         prob = np.mean(dscr_finite >= target_dscr_mc) if len(dscr_finite) > 0 else 1.0 # 100% si que infini
                    probabilities[ind] = float(prob) if pd.notna(prob) else 0.0
                else:
                    stats[ind] = {'mean': np.nan, 'std': np.nan, 'p': [np.nan]*5, 'n_valid': 0}
                    probabilities[ind] = 0.0

            # Proba globale (basée sur les itérations où TOUS les indicateurs clés sont valides)
            global_success_indicators = ['irr_project', 'payback_period', 'avg_dscr']
            mask_all_valid = np.ones(n_iterations, dtype=bool)
            for ind in global_success_indicators:
                mask_all_valid &= ~np.isnan(np.array(results_mc[f"{ind}_values"]))

            num_fully_valid_iterations = np.sum(mask_all_valid)
            if num_fully_valid_iterations > 0:
                # Extraire les valeurs valides pour ces itérations
                irr_proj_valid = np.array(results_mc["irr_project_values"])[mask_all_valid]
                payback_eq_valid = np.array(results_mc["payback_period_values"])[mask_all_valid]
                dscr_valid = np.array(results_mc["avg_dscr_values"])[mask_all_valid]
                # Comparer aux seuils
                irr_ok = irr_proj_valid >= min_irr_target
                payback_ok = payback_eq_valid <= payback_max_mc
                # Gérer DSCR infini
                dscr_finite_ok = dscr_valid[np.isfinite(dscr_valid)] >= target_dscr_mc
                # La probabilité est la moyenne des succès
                probabilities['global'] = np.mean(irr_ok & payback_ok & dscr_finite_ok) if len(dscr_finite_ok) > 0 else 0.0
                # Cas particulier: si tous les DSCR sont infinis (pas de dette), la contrainte est respectée
                if np.all(np.isinf(dscr_valid)): probabilities['global'] = np.mean(irr_ok & payback_ok)
            else:
                probabilities['global'] = 0.0

            # --- Dictionnaire retour (inchangé) ---
            monte_carlo_summary = { # Structure de retour inchangée
                'scenario_name': scenario_name,
                'prix_revente_simule': prix_revente,
                'n_iterations': n_iterations,
                'n_valid_runs': num_fully_valid_iterations, # Nb runs où TOUT était valide
                'ecart_type_production_pct': ecart_type_production_pct*100,
                'ecart_type_consommation_pct': ecart_type_consommation_pct*100,
                'results': all_values, # Retourne toutes les valeurs (avec NaN)
                'statistics': stats, # Stats calculées sur valeurs valides
                'probabilities': probabilities, # Probas calculées sur valeurs valides
                'contraintes_mc': {
                    'min_irr_project_pct': min_irr_target_pct,
                    'payback_max': payback_max_mc,
                    'dscr_min': target_dscr_mc
                }
            }
            end_time_mc = time.time()
            print(f"LOGIQUE: Monte Carlo Terminé en {end_time_mc - start_time_mc:.2f} sec. Runs complets valides: {num_fully_valid_iterations}/{n_iterations}")
            return monte_carlo_summary

        except (ValueError, TypeError, RuntimeError) as e:
            print(f"ERREUR LOGIQUE (run_monte_carlo): {e}")
            return {'error': f"Erreur logique MC: {e}"}
        except Exception as e:
            print(f"ERREUR LOGIQUE INATTENDUE (run_monte_carlo): {e}")
            traceback.print_exc()
            return {'error': f"Erreur inattendue MC: {e}"}

# --- Fin classe ---