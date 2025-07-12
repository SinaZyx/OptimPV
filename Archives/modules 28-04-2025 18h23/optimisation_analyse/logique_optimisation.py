# modules/optimisation_analyse/logique_optimisation.py

import pandas as pd
import numpy as np
import time
import traceback
import sys
import copy
from scipy.optimize import minimize, OptimizeResult # Ajout de OptimizeResult

try:
    from modules.analysis_engine import AnalysisEngine
except ImportError:
    print("ERREUR LOGIQUE: Impossible d'importer AnalysisEngine.")
    raise

class OptimizationLogic:
    """Logique pour l'optimisation sous contraintes et l'analyse de robustesse."""

    def __init__(self, config: dict, analysis_engine: AnalysisEngine):
        """
        Initialise avec la configuration et une instance du moteur d'analyse.
        """
        if not isinstance(config, dict): raise TypeError("config doit être un dict")
        if not isinstance(analysis_engine, AnalysisEngine): raise TypeError("analysis_engine doit être une instance de AnalysisEngine")

        self.config = config
        self.analysis_engine = analysis_engine
        # Garder une trace des derniers indicateurs calculés pour éviter recalculs redondants
        self._last_price_checked = None
        self._last_indicators = None
        self.indicators_cache = {}

    def _get_indicators(self, price: float, scenario_name: str) -> dict | None:
        """Wrapper pour obtenir les indicateurs, avec mise en cache simple."""
        cache_key = (scenario_name, price)
        if cache_key in self.indicators_cache:
            return self.indicators_cache[cache_key]

        try:
            results = self.analysis_engine.calculate_financial_indicators(scenario_name, prix_revente=price)
            self.indicators_cache[cache_key] = results
            return results
        except Exception as e:
            # Ne pas stocker en cas d'erreur
            self.indicators_cache[cache_key] = None
            print(f"ERREUR LOGIQUE (interne _get_indicators) pour prix {price:.4f}: {e}")
            # Important de ne pas propager l'exception ici pour que l'optimiseur continue,
            # mais de retourner None pour indiquer l'échec.
            return None


    def find_optimal_price_constrained(self,
                                       scenario_name: str,
                                       tri_projet_min_pct_constraint: float # <-- NOUVEL ARGUMENT
                                      ) -> dict | None:
        """
        Optimise le prix de revente pour maximiser la NPV Equity,
        tout en respectant les contraintes fournies.

        Args:
            scenario_name: Nom du scénario.
            tri_projet_min_pct_constraint: La contrainte de TRI Projet minimum en % (ex: 10.0).

        Returns:
            Dictionnaire avec le prix optimal, méthode, contraintes utilisées
            et indicateurs financiers, ou None/Exception en cas d'échec.
        """
        print(f"LOGIQUE: Lancement Optimisation sous Contraintes pour Scénario: {scenario_name}")
        start_time_optim = time.time()
        # Vider le cache interne AVANT l'exécution (important si l'instance persiste)
        self.indicators_cache.clear() 

        try:
            config = self.config # Garder accès à la config pour AUTRES paramètres

            # --- 1. Récupérer les paramètres et contraintes ---
            try:
                # --- MODIFIÉ : Utiliser l'argument pour le seuil TRI Projet ---
                min_irr_pct = float(tri_projet_min_pct_constraint) # Utilise l'argument passé
                min_irr = min_irr_pct / 100.0
                print(f"DEBUG CONSTRAINTE: Seuil min_irr (Projet) utilisé = {min_irr:.4f} ({min_irr_pct}%)") # Vérifier la valeur reçue
                # --- FIN MODIFICATION ---

                # Lire les AUTRES contraintes depuis la config
                max_payback = float(config.get('constraint_max_payback', 18.0))
                min_consumer_gain_pct = float(config.get('constraint_min_consumer_gain_pct', 5.0))
                if not (0 <= min_consumer_gain_pct < 100): raise ValueError("Gain conso % [0, 100[")

                tarif_edf_ref = float(config.get('tarif_edf_reference', 0.22))
                prix_max_config = float(config.get('prix_max_revente', tarif_edf_ref))

                # --- Calcul Prix Plancher (borne inf) --- 
                print("LOGIQUE: Calcul préalable du Prix Plancher (VAN=0)...")
                # Utiliser analysis_engine directement ici
                floor_results = self.analysis_engine.simulate_selling_price(
                    scenario_name, target_npv=0, override_source_prix_autoconso="prix_initial"
                )
                if not floor_results or floor_results.get('prix_revente_optimal_pour_cible') is None:
                    # Fallback sur LCOE si prix plancher échoue
                    lcoe_fallback_results = self.analysis_engine.calculate_financial_indicators(scenario_name, prix_revente=config.get("prix_vente_initial", 0.15))
                    lcoe_estime = lcoe_fallback_results.get('lcoe')
                    if lcoe_estime is None: raise ValueError("Calcul du prix plancher/LCOE (borne inf) impossible.")
                    prix_min_optim = lcoe_estime
                    print(f"AVERTISSEMENT LOGIQUE: Prix plancher VAN=0 échoué, utilisation LCOE={lcoe_estime:.4f} comme borne inf.")
                else:
                    prix_min_optim = floor_results['prix_revente_optimal_pour_cible']
                    lcoe_estime = floor_results.get('lcoe_associated') # Utiliser le LCOE associé au prix plancher si dispo
                    if lcoe_estime is None: lcoe_estime = floor_results.get('lcoe') # Fallback sur l'autre LCOE
                    if lcoe_estime is None: lcoe_estime = prix_min_optim # Fallback ultime
                    print(f"LOGIQUE: Prix plancher VAN=0 trouvé: {prix_min_optim:.4f} € (LCOE estimé: {lcoe_estime:.4f} €)")

                # --- Calcul Prix Max (borne sup) ---
                prix_max_theorique_conso = tarif_edf_ref * (1.0 - min_consumer_gain_pct / 100.0)
                prix_max_optim = min(prix_max_config, prix_max_theorique_conso)

                # Vérification finale des bornes
                if prix_min_optim >= prix_max_optim:
                    if abs(prix_min_optim - prix_max_optim) < 1e-4:
                         prix_max_optim = prix_min_optim + 1e-4
                         print(f"AVERTISSEMENT: Plage de prix quasi-nulle, élargie à [{prix_min_optim:.4f}, {prix_max_optim:.4f}] ")
                    else:
                         raise ValueError(f"Plage recherche invalide [{prix_min_optim:.4f}, {prix_max_optim:.4f}] après prise en compte contrainte gain client.")

                print(f"LOGIQUE: Bornes recherche prix: [{prix_min_optim:.4f}, {prix_max_optim:.4f}]")
                print(f"LOGIQUE: Contraintes: TRI Projet >= {min_irr_pct}%, Payback Equity <= {max_payback}, Gain Client >= {min_consumer_gain_pct}% ({prix_max_theorique_conso:.4f} € max)")

            except (ValueError, TypeError, KeyError, RuntimeError) as e:
                # Ajouter RuntimeError ici pour attraper les erreurs de calcul de prix plancher
                raise ValueError(f"Erreur récupération paramètres/contraintes/bornes: {e}") from e

            # --- 2. Définir Objectif et Contraintes pour scipy.optimize.minimize ---

            # Objectif: Minimiser l'opposé de la NPV (car on veut maximiser NPV)
            def objective_function(price_array):
                price = price_array[0]
                # Utilisation de _get_indicators interne pour caching
                indicators = self._get_indicators(price, scenario_name)
                if indicators is None or indicators.get('npv') is None:
                    return 1e12 # Grosse pénalité si calcul échoue
                return -indicators['npv'] # Retourne -NPV

            # Contraintes (format scipy : fonction >= 0 pour type 'ineq')
            constraints = []

            # --- La fonction irr_constraint utilise maintenant 'min_irr' qui a été défini à partir de l'argument ---
            def irr_constraint(price_array):
                 price = price_array[0]
                 indicators = self._get_indicators(price, scenario_name)
                 if indicators is None or indicators.get('irr_project') is None:
                     # Commenter les prints répétitifs par défaut pour alléger la sortie
                     # print(f"DEBUG irr_constraint({price:.4f}): Indicateurs ou irr_project non trouvés, retourne -1e6") 
                     return -1e6
                 irr_val = indicators['irr_project']
                 
                 # Commenter les prints répétitifs par défaut
                 # is_satisfied = irr_val >= min_irr
                 # constraint_value = irr_val - min_irr
                 # print(f"DEBUG irr_constraint({price:.4f}): irr_proj={irr_val:.4f}, min_irr={min_irr:.4f}, diff={constraint_value:.4f}, satisfied={is_satisfied}")
                 
                 if not np.isfinite(irr_val):
                     return 1e6 if np.isfinite(min_irr) else 0
                 # Retourner directement la différence
                 return irr_val - min_irr
            constraints.append({'type': 'ineq', 'fun': irr_constraint, 'name': 'TRI Projet'})

            # --- Contrainte Payback Equity (utilise max_payback lu depuis config) ---
            def payback_constraint(price_array):
                price = price_array[0]
                indicators = self._get_indicators(price, scenario_name)
                if indicators is None or indicators.get('payback_period') is None: return -1e6
                payback = indicators['payback_period']
                duree_simu = len(indicators.get('years', []))
                # Si payback non fini ou > durée, contrainte non respectée
                if not np.isfinite(payback) or (duree_simu > 0 and payback > duree_simu + 1e-6): # Ajouter tolérance durée
                     return -1e6 if np.isfinite(max_payback) else 0
                return max_payback - payback
            constraints.append({'type': 'ineq', 'fun': payback_constraint, 'name': 'Payback Equity'})

            # --- Contrainte Gain Client (utilise tarif_edf_ref et min_consumer_gain_pct lus depuis config) ---
            if tarif_edf_ref > 1e-6:
                 min_gain_abs = tarif_edf_ref * (min_consumer_gain_pct / 100.0)
                 def consumer_gain_constraint(price_array):
                      price = price_array[0]
                      current_gain_abs = tarif_edf_ref - price
                      return current_gain_abs - min_gain_abs
                 constraints.append({'type': 'ineq', 'fun': consumer_gain_constraint, 'name': 'Gain Client'})

            # Bornes pour le prix
            bounds = [(prix_min_optim, prix_max_optim)]

            # --- 3. Exécuter l'optimisation --- 
            num_starts = 3
            best_result: OptimizeResult | None = None
            min_objective_value = float('inf')
            start_points = [prix_min_optim, prix_max_optim, (prix_min_optim + prix_max_optim) / 2.0]

            print(f"LOGIQUE: Lancement optimisation avec {len(start_points)} points de départ...")
            for i, start_price in enumerate(start_points):
                print(f"  -> Départ {i+1}/{len(start_points)} : Prix initial = {start_price:.4f}")
                # Le cache est vidé au début, pas besoin de le refaire ici
                
                result = minimize(
                    objective_function,
                    [start_price],
                    method='SLSQP',
                    bounds=bounds,
                    constraints=constraints,
                    options={'ftol': 1e-7, 'disp': False}
                )
                # Commenter le print de résultat détaillé par défaut
                # print(f"  Résultat Départ {i+1}: Success={result.success}, Status={result.status}, Obj={result.fun:.4f}, Prix={result.x[0]:.4f}, Msg={result.message}")

                if result.success and result.fun < min_objective_value:
                    final_price_candidate = result.x[0]
                    if not (bounds[0][0] - 1e-9 <= final_price_candidate <= bounds[0][1] + 1e-9): # Ajouter tolérance bornes
                        # print(f"  -> Résultat Départ {i+1} écarté car PRIX ({final_price_candidate:.4f}) HORS BORNES [{bounds[0][0]:.4f}, {bounds[0][1]:.4f}]")
                        continue

                    constraints_satisfied = True
                    # Commenter la vérification détaillée des contraintes par défaut
                    # print(f"  Vérification contraintes pour Prix={final_price_candidate:.4f}:")
                    for constraint in constraints:
                        constraint_name = constraint.get('name', 'Inconnue')
                        constraint_value = constraint['fun']([final_price_candidate])
                        # print(f"    -> Contrainte '{constraint_name}': Value={constraint_value:.6f}")
                        if constraint_value < -1e-6:
                            # print(f"  ATTENTION: Contrainte '{constraint_name}' NON SATISFAITE pour prix {final_price_candidate:.4f}, Val={constraint_value:.6f}")
                            constraints_satisfied = False
                            break
                    
                    if constraints_satisfied:
                        min_objective_value = result.fun
                        best_result = result
                        # print(f"  -> Nouveau meilleur résultat trouvé !")
                    # else:
                    #     print(f"  -> Résultat écarté car contraintes non vérifiées explicitement.")

            # --- 4. Analyser le résultat et construire la sortie --- 
            if best_result is None or not best_result.success:
                 if best_result is not None:
                     msg = f"Optimisation échouée (Status={best_result.status}): {best_result.message}"
                 else:
                     msg = "Optimisation échouée : Aucune solution respectant les contraintes n'a pu être trouvée."
                 raise RuntimeError(msg)

            optimal_price = best_result.x[0]
            final_npv = -best_result.fun

            print(f"LOGIQUE: Optimisation réussie ! Prix Optimal = {optimal_price:.6f} €/kWh (NPV Max = {final_npv:,.0f} €)")
            print(f"LOGIQUE: Temps total optimisation: {time.time() - start_time_optim:.3f}s")

            final_indicators = self._get_indicators(optimal_price, scenario_name)
            if not final_indicators:
                 raise RuntimeError(f"Erreur critique : Impossible de recalculer les indicateurs au prix optimal trouvé {optimal_price:.4f}")

            optimization_summary = {
                'scenario_name': scenario_name,
                'prix_optimal_const': optimal_price,
                'methode': 'Optimisation sous Contraintes',
                'contraintes_appliquees': {
                    'min_irr_pct': min_irr_pct, # Utiliser la variable locale définie depuis l'argument
                    'max_payback': max_payback, # Lu depuis config
                    'min_consumer_gain_pct': min_consumer_gain_pct # Lu depuis config
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
                    'nfev': best_result.nfev,
                    'njev': best_result.njev,
                    'nit': best_result.nit
                }
            }
            return optimization_summary

        except (ValueError, TypeError, RuntimeError) as e:
            print(f"ERREUR LOGIQUE (find_optimal_price_constrained): {e}")
            raise e 
        except Exception as e:
            print(f"ERREUR LOGIQUE INATTENDUE (find_optimal_price_constrained): {e}")
            traceback.print_exc()
            raise RuntimeError(f"Erreur inattendue lors de l'optimisation sous contraintes: {e}") from e


    def run_monte_carlo_simulation(self, scenario_name: str, prix_revente: float) -> dict | None:
        """
        Exécute une simulation Monte Carlo.
        Applique des variations aléatoires aux données de chaque site individuellement.
        Prend le prix de revente optimal (trouvé précédemment) en argument explicite.
        Retourne un dictionnaire de résultats ou un dictionnaire {'error': ...} en cas d'échec.
        """
        print(f"LOGIQUE: Lancement Monte Carlo pour Scénario: {scenario_name} au prix {prix_revente:.4f}")
        start_time_mc = time.time()
        try:
            config = self.config
            # --- MODIFICATION : Vérifier self.analysis_engine.sites_data ---
            if not hasattr(self.analysis_engine, 'sites_data') or not self.analysis_engine.sites_data:
                raise ValueError("Données de site non disponibles dans analysis_engine pour Monte Carlo.")
            # --- FIN MODIFICATION ---

            # Lire params MC depuis config
            n_iterations = int(config.get('nb_iterations_monte_carlo', 1000))
            ecart_type_production_pct = float(config.get('ecart_type_production', 10.0))
            ecart_type_consommation_pct = float(config.get('ecart_type_consommation', 5.0))

            ecart_type_production = ecart_type_production_pct / 100.0
            ecart_type_consommation = ecart_type_consommation_pct / 100.0

            # Récupérer les seuils MC depuis config AVANT la boucle
            mc_constraint_keys = ['constraint_min_dscr', 'constraint_max_payback', 'constraint_min_project_irr_pct']
            missing_mc_keys = [k for k in mc_constraint_keys if config.get(k) is None]
            if missing_mc_keys:
                print(f"AVERTISSEMENT MONTE CARLO: Clés de contraintes MC manquantes dans config: {missing_mc_keys}. Utilisation de valeurs par défaut.")
            
            target_dscr_mc = float(config.get('constraint_min_dscr', 1.15))
            payback_max_mc = float(config.get('constraint_max_payback', 18.0))
            min_irr_target_pct = float(config.get('constraint_min_project_irr_pct', 8.0))
            min_irr_target = min_irr_target_pct / 100.0

            # Indicateurs à suivre
            tracked_indicators = ['roi', 'irr', 'npv', 'payback_period', 'avg_dscr', 'irr_project', 'payback_project', 'lcoe']
            results_mc = {f"{ind}_values": [] for ind in tracked_indicators}

            # --- MODIFICATION : Utiliser le dictionnaire original des sites ---
            original_sites_data = self.analysis_engine.sites_data
            # --- FIN MODIFICATION ---

            n_valid_runs = 0
            for i in range(n_iterations):
                # --- MODIFICATION : Créer un dictionnaire de données simulées pour cette itération ---
                simulated_sites_data_iter = {}
                for site_id, original_df_site in original_sites_data.items():
                    simulated_df_site = original_df_site.copy()
                    # Appliquer variations
                    prod_variation = np.random.normal(1, ecart_type_production)
                    cons_variation = np.random.normal(1, ecart_type_consommation)
                    # Vérifier si les colonnes existent avant de les modifier
                    if 'production_kwh' in simulated_df_site.columns:
                        simulated_df_site['production_kwh'] = (simulated_df_site['production_kwh'] * prod_variation).clip(lower=0)
                    if 'consumption_kwh' in simulated_df_site.columns:
                         simulated_df_site['consumption_kwh'] = (simulated_df_site['consumption_kwh'] * cons_variation).clip(lower=0)
                    
                    simulated_sites_data_iter[site_id] = simulated_df_site
                # --- FIN MODIFICATION ---

                # Créer une instance temporaire du moteur AVEC LES DONNÉES SIMULÉES PAR SITE
                results_iter = None # Initialiser à None pour cette itération
                try:
                    # Utilisation de deepcopy pour éviter effets de bord sur config/scenarios
                    temp_engine_iter = AnalysisEngine(
                        copy.deepcopy(self.config),
                        copy.deepcopy(self.analysis_engine.scenarios),
                        simulated_sites_data_iter # <-- Passer le dictionnaire simulé
                    )
                    # L'agrégation se fera à l'intérieur de calculate_financial_indicators
                    results_iter = temp_engine_iter.calculate_financial_indicators(scenario_name, prix_revente=prix_revente)
                except Exception as iter_e:
                    # Log plus discret en mode normal, sauf si besoin de debug
                    if i % 100 == 0 or i == n_iterations - 1: # Log moins fréquent
                        print(f"AVERTISSEMENT MOTEUR (MC Iter {i}): Échec calcul indicateurs - {iter_e}")
                    # Pas besoin de stocker l'erreur ici, results_iter reste None

                # Stocker les résultats (ou NaN si échec)
                valid_run_this_iter = False
                if results_iter and isinstance(results_iter, dict):
                    all_valid_for_iter = True # Flag pour vérifier si tous les indicateurs sont valides
                    temp_results_for_iter = {} # Dict temporaire pour stocker les valeurs de cette itération
                    for ind in tracked_indicators:
                        val = results_iter.get(ind)
                        if val is None or not np.isfinite(val):
                            val = np.nan
                        temp_results_for_iter[ind] = val
                        if np.isnan(val):
                            all_valid_for_iter = False
                    
                    # Ajouter les valeurs au dictionnaire principal results_mc
                    for ind in tracked_indicators:
                        results_mc[f"{ind}_values"].append(temp_results_for_iter[ind])
                    
                    valid_run_this_iter = all_valid_for_iter
                else: # En cas d'échec de calculate_financial_indicators (results_iter is None)
                     for ind in tracked_indicators: 
                         results_mc[f"{ind}_values"].append(np.nan)

                if valid_run_this_iter: 
                    n_valid_runs += 1


            # --- Traitement statistique (sur les valeurs valides uniquement) ---
            stats = {}
            probabilities = {}
            all_values = {} # Pour retourner les listes complètes avec NaN

            for ind in tracked_indicators:
                values_with_nan = np.array(results_mc[f"{ind}_values"])
                all_values[f"{ind}_values"] = values_with_nan.tolist() # Stocker la liste complète
                valid_values = values_with_nan[~np.isnan(values_with_nan)] # Filtrer NaN pour stats

                if len(valid_values) > 0:
                    stats[ind] = {
                        'mean': np.mean(valid_values),
                        'std': np.std(valid_values),
                        'p': np.percentile(valid_values, [5, 25, 50, 75, 95]).tolist()
                    }
                    # Calcul des probabilités
                    if ind == 'roi': prob = np.mean(valid_values >= 0.05) # Ex: ROI >= 5%
                    elif ind == 'irr': prob = np.mean(valid_values >= min_irr_target) # Utiliser la cible IRR
                    elif ind == 'npv': prob = np.mean(valid_values >= 0) # Ex: NPV >= 0
                    elif ind == 'payback_period': prob = np.mean(valid_values <= payback_max_mc) # Payback <= Cible
                    elif ind == 'avg_dscr': prob = np.mean(valid_values >= target_dscr_mc) # DSCR >= Cible
                    elif ind == 'irr_project': prob = np.mean(valid_values >= 0.06) # Exemple seuil IRR Projet
                    elif ind == 'payback_project': prob = np.mean(valid_values <= 20) # Exemple seuil Payback Projet
                    else: prob = np.nan
                    probabilities[ind] = prob if not np.isnan(prob) else 0.0
                else:
                    stats[ind] = {'mean': np.nan, 'std': np.nan, 'p': [np.nan]*5}
                    probabilities[ind] = 0.0

            # Probabilité de succès global (basée sur les contraintes MC principales)
            global_success_indicators = ['irr', 'payback_period', 'avg_dscr']
            # Créer un masque pour les itérations où TOUS les indicateurs clés sont valides (non-NaN)
            valid_mask = np.ones(n_iterations, dtype=bool)
            for ind in global_success_indicators:
                valid_mask &= ~np.isnan(np.array(results_mc[f"{ind}_values"]))
            
            num_fully_valid_iterations = np.sum(valid_mask)

            if num_fully_valid_iterations > 0:
                # Appliquer les conditions sur les données valides de ces itérations uniquement
                irr_values_valid = np.array(results_mc["irr_values"])[valid_mask]
                payback_values_valid = np.array(results_mc["payback_period_values"])[valid_mask]
                dscr_values_valid = np.array(results_mc["avg_dscr_values"])[valid_mask]
                
                irr_ok = irr_values_valid >= min_irr_target
                payback_ok = payback_values_valid <= payback_max_mc
                dscr_ok = dscr_values_valid >= target_dscr_mc
                
                # Calculer la moyenne du succès combiné sur les itérations valides
                probabilities['global'] = np.mean(irr_ok & payback_ok & dscr_ok)
            else:
                probabilities['global'] = 0.0

            monte_carlo_summary = {
                'scenario_name': scenario_name, 'prix_revente_simule': prix_revente,
                'n_iterations': n_iterations, 'n_valid_runs': num_fully_valid_iterations, # Utiliser le compte des itérations entièrement valides
                'ecart_type_production_pct': ecart_type_production_pct,
                'ecart_type_consommation_pct': ecart_type_consommation_pct,
                'results': all_values, # Listes complètes avec NaN
                'statistics': stats,
                'probabilities': probabilities,
                'contraintes_mc': { # Rappeler les seuils utilisés pour les probas
                     'min_irr_pct': min_irr_target_pct,
                     'payback_max': payback_max_mc,
                     'dscr_min': target_dscr_mc
                }
            }
            print(f"LOGIQUE: Monte Carlo Terminé pour {scenario_name}. Temps: {time.time() - start_time_mc:.3f}s. Runs valides: {num_fully_valid_iterations}/{n_iterations}")
            return monte_carlo_summary

        except (ValueError, TypeError, RuntimeError) as e:
             print(f"ERREUR LOGIQUE (run_monte_carlo): {e}")
             # traceback.print_exc() # Debug
             # Retourner un dictionnaire d'erreur
             return {'error': f"Erreur logique Monte Carlo: {e}"}
        except Exception as e:
             print(f"ERREUR LOGIQUE INATTENDUE (run_monte_carlo): {e}")
             traceback.print_exc()
             # Retourner un dictionnaire d'erreur
             return {'error': f"Erreur inattendue Monte Carlo: {e}"}