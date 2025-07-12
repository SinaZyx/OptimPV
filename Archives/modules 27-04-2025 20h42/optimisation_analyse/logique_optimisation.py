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


    def find_optimal_price_constrained(self, scenario_name: str) -> dict | None:
        """
        Optimise le prix de revente pour maximiser la NPV du producteur,
        tout en respectant les contraintes définies dans la configuration.

        Args:
            scenario_name: Nom du scénario.

        Returns:
            Dictionnaire avec le prix optimal, méthode, contraintes utilisées
            et indicateurs financiers, ou None/Exception en cas d'échec.
        """
        print(f"LOGIQUE: Lancement Optimisation sous Contraintes pour Scénario: {scenario_name}")
        start_time_optim = time.time()
        # Réinitialiser le cache interne
        self._last_price_checked = None
        self._last_indicators = None

        try:
            config = self.config # Utiliser la config membre

            # --- 1. Récupérer les paramètres et contraintes depuis config ---
            try:
                # --- DEBUT MODIFICATION: Lire TRI min au lieu de DSCR min ---
                min_irr_pct = float(config.get('constraint_min_irr_pct', 8.0)) # Lire TRI min en %
                min_irr = min_irr_pct / 100.0 # Convertir en décimal pour calculs
                max_payback = float(config.get('constraint_max_payback', 18.0))
                min_consumer_gain_pct = float(config.get('constraint_min_consumer_gain_pct', 5.0))
                # --- FIN MODIFICATION ---
                if not (0 <= min_consumer_gain_pct < 100): raise ValueError("Gain conso % [0, 100[")

                tarif_edf_ref = float(config.get('tarif_edf_reference', 0.22))

                # Bornes de recherche pour le prix
                # a) Borne inférieure : Prix Plancher (VAN=0)
                print("LOGIQUE: Calcul préalable du Prix Plancher (VAN=0)...")
                floor_results = self.analysis_engine.simulate_selling_price(
                    scenario_name, target_npv=0, override_source_prix_autoconso="prix_initial"
                )
                if not floor_results or floor_results.get('prix_revente_optimal_pour_cible') is None:
                    lcoe_estime_fallback = self.analysis_engine.calculate_financial_indicators(scenario_name, prix_revente=config.get("prix_vente_initial", 0.15)).get('lcoe')
                    if lcoe_estime_fallback is None: raise ValueError("Calcul du prix plancher/LCOE (borne inf) impossible.")
                    prix_min_optim = lcoe_estime_fallback
                    lcoe_estime = lcoe_estime_fallback
                    print(f"AVERTISSEMENT LOGIQUE: Prix plancher VAN=0 échoué, utilisation LCOE={lcoe_estime:.4f} comme borne inf.")
                else:
                    prix_min_optim = floor_results['prix_revente_optimal_pour_cible']
                    lcoe_estime = floor_results.get('lcoe_associated', prix_min_optim)

                # b) Borne supérieure : Tarif EDF (ou légèrement moins)
                # Prix max doit aussi assurer le gain client min
                prix_max_theorique_conso = tarif_edf_ref * (1.0 - min_consumer_gain_pct / 100.0)
                # On prend le minimum entre le max config et le max conso pour la borne sup
                prix_max_config = float(config.get('prix_max_revente', tarif_edf_ref)) # Utiliser EDF par défaut si non défini
                prix_max_optim = min(prix_max_config, prix_max_theorique_conso)

                # Vérification finale des bornes
                if prix_min_optim >= prix_max_optim:
                    # Tenter d'élargir légèrement si la plage est nulle ou inversée à cause des arrondis
                    if abs(prix_min_optim - prix_max_optim) < 1e-4:
                         prix_max_optim = prix_min_optim + 1e-4
                         print(f"AVERTISSEMENT: Plage de prix quasi-nulle, élargie à [{prix_min_optim:.4f}, {prix_max_optim:.4f}] ")
                    else:
                         raise ValueError(f"Plage recherche invalide [{prix_min_optim:.4f}, {prix_max_optim:.4f}] après prise en compte contrainte gain client.")

                # --- DEBUT MODIFICATION: Afficher contrainte TRI ---
                print(f"LOGIQUE: Bornes recherche prix: [{prix_min_optim:.4f}, {prix_max_optim:.4f}]")
                print(f"LOGIQUE: Contraintes: TRI >= {min_irr_pct}%, Payback <= {max_payback}, Gain Client >= {min_consumer_gain_pct}% ({prix_max_theorique_conso:.4f} € max)")
                # --- FIN MODIFICATION ---

            except (ValueError, TypeError, KeyError) as e:
                raise ValueError(f"Erreur récupération paramètres/contraintes: {e}") from e

            # --- 2. Définir Objectif et Contraintes pour scipy.optimize.minimize ---

            # Objectif: Minimiser l'opposé de la NPV (car on veut maximiser NPV)
            def objective_function(price_array):
                price = price_array[0]
                indicators = self._get_indicators(price, scenario_name)
                if indicators is None or indicators.get('npv') is None:
                    return 1e12 # Grosse pénalité si calcul échoue
                return -indicators['npv'] # Retourne -NPV

            # Contraintes (format scipy : fonction >= 0 pour type 'ineq')
            constraints = []

            # Contrainte TRI >= min_irr  =>  TRI - min_irr >= 0
            def irr_constraint(price_array):
                price = price_array[0]
                indicators = self._get_indicators(price, scenario_name)
                # Si IRR non calculable ou indicateurs échouent, considérer contrainte non respectée (-1e6 < 0)
                if indicators is None or indicators.get('irr') is None: return -1e6
                irr_val = indicators['irr']
                if not np.isfinite(irr_val):
                    # Si IRR est infini, la contrainte est largement respectée (retourner grand positif)
                    return 1e6 if np.isfinite(min_irr) else 0 # (sauf si min_irr est aussi infini... peu probable)
                # La fonction doit retourner >= 0 si la contrainte est respectée
                return irr_val - min_irr
            constraints.append({'type': 'ineq', 'fun': irr_constraint})

            # Contrainte Payback <= max_payback => max_payback - Payback >= 0
            def payback_constraint(price_array):
                price = price_array[0]
                indicators = self._get_indicators(price, scenario_name)
                # Si Payback non calculable (infini) ou indicateurs échouent, contrainte non respectée
                if indicators is None or indicators.get('payback_period') is None: return -1e6
                payback = indicators['payback_period']
                # Gérer payback "infini" (ou très grand > durée simu)
                duree_simu = len(indicators.get('years', []))
                if not np.isfinite(payback) or payback > duree_simu:
                    # Si le payback est infini/trop long, la contrainte n'est pas respectée si max_payback est fini
                     return -1e6 if np.isfinite(max_payback) else 0
                return max_payback - payback
            constraints.append({'type': 'ineq', 'fun': payback_constraint})

            # Contrainte Gain Client >= min_gain_pct => (Tarif_EDF - Prix) / Tarif_EDF >= min_gain_pct / 100
            # => (Tarif_EDF - Prix) - (Tarif_EDF * min_gain_pct / 100) >= 0
            # Attention: ne fonctionne que si Tarif_EDF > 0
            if tarif_edf_ref > 1e-6:
                 min_gain_abs = tarif_edf_ref * (min_consumer_gain_pct / 100.0)
                 def consumer_gain_constraint(price_array):
                      price = price_array[0]
                      current_gain_abs = tarif_edf_ref - price
                      return current_gain_abs - min_gain_abs
                 constraints.append({'type': 'ineq', 'fun': consumer_gain_constraint})

            # Bornes pour le prix
            bounds = [(prix_min_optim, prix_max_optim)]

            # --- 3. Exécuter l'optimisation ---
            # Essayer plusieurs points de départ pour robustesse
            num_starts = 3
            best_result: OptimizeResult | None = None
            min_objective_value = float('inf')

            # Points de départ : min, max, milieu
            start_points = [
                prix_min_optim,
                prix_max_optim,
                (prix_min_optim + prix_max_optim) / 2.0
            ]
            # Ajouter quelques points aléatoires si besoin
            # if num_starts > 3:
            #     random_starts = np.random.uniform(prix_min_optim, prix_max_optim, num_starts - 3)
            #     start_points.extend(random_starts)

            print(f"LOGIQUE: Lancement optimisation avec {len(start_points)} points de départ...")
            for i, start_price in enumerate(start_points):
                print(f"  -> Départ {i+1}/{len(start_points)} : Prix initial = {start_price:.4f}")
                # Réinitialiser le cache pour chaque essai majeur
                self._last_price_checked = None
                self._last_indicators = None
                result = minimize(
                    objective_function,
                    [start_price], # Doit être un array/liste
                    method='SLSQP', # Bon choix pour contraintes et bornes
                    bounds=bounds,
                    constraints=constraints,
                    options={'ftol': 1e-7, 'disp': False} # ftol = tolérance sur objectif
                )
                print(f"  Résultat Départ {i+1}: Success={result.success}, Status={result.status}, Obj={result.fun:.4f}, Prix={result.x[0]:.4f}, Msg={result.message}")


                # Vérifier si ce résultat est meilleur et valide
                if result.success and result.fun < min_objective_value:
                     # Re-vérifier explicitement les contraintes au point trouvé (SLSQP le fait mais double check)
                     final_price_candidate = result.x[0]
                     constraints_satisfied = True
                     for constraint in constraints:
                          constraint_value = constraint['fun']([final_price_candidate])
                          # Ajouter une tolérance pour les comparaisons flottantes
                          if constraint_value < -1e-6: # Si une contrainte n'est pas >= 0 (avec tolérance)
                              print(f"  ATTENTION: Contrainte non satisfaite pour prix {final_price_candidate:.4f}, Val={constraint_value:.4f}")
                              constraints_satisfied = False
                              break # Inutile de vérifier les autres

                     if constraints_satisfied:
                          min_objective_value = result.fun
                          best_result = result
                          print(f"  -> Nouveau meilleur résultat trouvé !")
                     else:
                          print(f"  -> Résultat écarté car contraintes non vérifiées explicitement.")


            # --- 4. Analyser le résultat et construire la sortie ---
            if best_result is None or not best_result.success:
                 # Essayer de donner une raison plus précise
                 if best_result is not None: # Si on a eu un résultat mais non success
                     msg = f"Optimisation échouée (Status={best_result.status}): {best_result.message}"
                 else: # Si aucune run n'a même produit un résultat potentiellement valide
                     msg = "Optimisation échouée : Aucune solution respectant les contraintes n'a pu être trouvée."
                 raise RuntimeError(msg)

            optimal_price = best_result.x[0]
            final_npv = -best_result.fun # Récupérer la NPV max

            print(f"LOGIQUE: Optimisation réussie ! Prix Optimal = {optimal_price:.6f} €/kWh (NPV Max = {final_npv:,.0f} €)")
            print(f"LOGIQUE: Temps total optimisation: {time.time() - start_time_optim:.3f}s")

            # Récupérer les indicateurs finaux au prix optimal (devraient être en cache)
            final_indicators = self._get_indicators(optimal_price, scenario_name)
            if not final_indicators:
                 # Devrait être très rare si l'optimisation a réussi
                 raise RuntimeError(f"Erreur critique : Impossible de recalculer les indicateurs au prix optimal trouvé {optimal_price:.4f}")

            # Construire le dictionnaire de résultats
            optimization_summary = {
                'scenario_name': scenario_name,
                'prix_optimal_const': optimal_price,
                'methode': 'Optimisation sous Contraintes',
                'contraintes_appliquees': {
                    'min_irr_pct': min_irr_pct,
                    'max_payback': max_payback,
                    'min_consumer_gain_pct': min_consumer_gain_pct
                },
                'npv_optimise': final_npv,
                'lcoe_estime': lcoe_estime, # Info contextuelle
                'prix_plancher_producteur': prix_min_optim, # Info contextuelle
                'tarif_edf_reference': tarif_edf_ref, # Info contextuelle
                'indicateurs_au_prix_optimal': final_indicators,
                'optimisation_details': { # Pour debug / info avancée
                    'success': best_result.success,
                    'message': best_result.message,
                    'status': best_result.status,
                    'nfev': best_result.nfev, # Nb évaluations fonction objectif
                    'njev': best_result.njev, # Nb évaluations jacobien (gradient)
                    'nit': best_result.nit   # Nb itérations
                }
            }
            return optimization_summary

        except (ValueError, TypeError, RuntimeError) as e:
            print(f"ERREUR LOGIQUE (find_optimal_price_constrained): {e}")
            # traceback.print_exc() # Décommenter pour debug serveur
            raise e # Renvoyer pour que l'UI gère
        except Exception as e:
            print(f"ERREUR LOGIQUE INATTENDUE (find_optimal_price_constrained): {e}")
            traceback.print_exc()
            raise RuntimeError(f"Erreur inattendue lors de l'optimisation sous contraintes: {e}") from e


    def run_monte_carlo_simulation(self, scenario_name: str, prix_revente: float) -> dict | None:
        """
        Exécute une simulation Monte Carlo (légère ou complète selon config).
        Prend le prix de revente optimal (trouvé précédemment) en argument explicite.
        """
        print(f"LOGIQUE: Lancement Monte Carlo pour Scénario: {scenario_name} au prix {prix_revente:.4f}")
        start_time_mc = time.time()
        try:
            config = self.config
            if self.analysis_engine.processed_data is None or self.analysis_engine.processed_data.empty:
                raise ValueError("Données traitées non disponibles dans analysis_engine pour Monte Carlo.")

            # Lire params MC depuis config (peut être ajusté pour "léger")
            # Par exemple, on pourrait avoir 'mc_iterations_light' et 'mc_iterations_full'
            n_iterations = int(config.get('nb_iterations_monte_carlo', 1000)) # Garder 1000 pour l'instant
            ecart_type_production_pct = float(config.get('ecart_type_production', 10.0))
            ecart_type_consommation_pct = float(config.get('ecart_type_consommation', 5.0))
            target_dscr_mc = float(config.get('constraint_min_dscr', 1.15)) # Utiliser la contrainte DSCR comme cible
            payback_max_mc = float(config.get('constraint_max_payback', 18.0)) # Utiliser la contrainte Payback

            ecart_type_production = ecart_type_production_pct / 100.0
            ecart_type_consommation = ecart_type_consommation_pct / 100.0

            # Indicateurs à suivre
            tracked_indicators = ['roi', 'irr', 'npv', 'payback_period', 'avg_dscr']
            results_mc = {f"{ind}_values": [] for ind in tracked_indicators}

            original_data = self.analysis_engine.processed_data.copy()
            # Utiliser une seule instance temporaire peut être suffisant si on nettoie bien
            # Mais recréer peut être plus sûr (à évaluer si performance est un pb)
            # temp_engine = AnalysisEngine(self.config, self.analysis_engine.scenarios, None) # Initialiser sans data

            n_valid_runs = 0
            for i in range(n_iterations):
                simulated_data = original_data.copy()
                # Appliquer variations
                prod_variation = np.random.normal(1, ecart_type_production)
                cons_variation = np.random.normal(1, ecart_type_consommation)
                simulated_data['production_kwh'] = (simulated_data['production_kwh'] * prod_variation).clip(lower=0)
                simulated_data['consumption_kwh'] = (simulated_data['consumption_kwh'] * cons_variation).clip(lower=0)

                # Créer une instance temporaire ou mettre à jour les données de l'instance unique
                # Ici, on recrée pour la sécurité, comme avant.
                try:
                    temp_engine_iter = AnalysisEngine(
                         # Passer une copie profonde de config/scenarios si on craint modifs ?
                         # Normalement, l'engine ne devrait pas modifier config/scenarios.
                         copy.deepcopy(self.config), # Plus sûr
                         copy.deepcopy(self.analysis_engine.scenarios), # Plus sûr
                         simulated_data
                    )
                    results_iter = temp_engine_iter.calculate_financial_indicators(scenario_name, prix_revente=prix_revente)
                except Exception as iter_e:
                    # Si une itération échoue, on la compte comme NaN mais on continue
                    print(f"AVERTISSEMENT MOTEUR (MC Iter {i}): Échec calcul indicateurs - {iter_e}")
                    results_iter = None # Marque l'échec

                # Stocker les résultats (ou NaN si échec)
                valid_run_this_iter = False
                if results_iter and isinstance(results_iter, dict):
                     for ind in tracked_indicators:
                          val = results_iter.get(ind, np.nan)
                          # Gérer explicitement les infinis potentiels (payback, dscr)
                          if ind == 'payback_period' and (val is None or not np.isfinite(val)): val = np.nan
                          if ind == 'avg_dscr' and (val is None or not np.isfinite(val)): val = np.nan
                          results_mc[f"{ind}_values"].append(val)
                     valid_run_this_iter = all(not np.isnan(results_mc[f"{ind}_values"][-1]) for ind in tracked_indicators) # Vérifier si tous sont valides
                else:
                     for ind in tracked_indicators: results_mc[f"{ind}_values"].append(np.nan)

                if valid_run_this_iter: n_valid_runs += 1


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
                    elif ind == 'irr': prob = np.mean(valid_values >= 0.04) # Ex: IRR >= 4%
                    elif ind == 'npv': prob = np.mean(valid_values >= 0) # Ex: NPV >= 0
                    elif ind == 'payback_period': prob = np.mean(valid_values <= payback_max_mc) # Payback <= Cible
                    elif ind == 'avg_dscr': prob = np.mean(valid_values >= target_dscr_mc) # DSCR >= Cible
                    else: prob = np.nan
                    probabilities[ind] = prob
                else:
                    # Si aucune valeur valide, mettre stats/proba à NaN ou 0
                    stats[ind] = {'mean': np.nan, 'std': np.nan, 'p': [np.nan]*5}
                    probabilities[ind] = 0.0 # Ou np.nan ? 0.0 semble plus sûr pour 'Probabilité de succès'

            # Probabilité de succès global (toutes contraintes MC respectées)
            # Utiliser les listes complètes (avec NaN) et np.nanmean pour ignorer NaN dans le calcul global
            # Ou filtrer pour ne garder que les itérations où TOUT est valide. Ici on filtre.
            valid_indices = ~np.isnan(np.array(results_mc["roi_values"])) & \
                            ~np.isnan(np.array(results_mc["irr_values"])) & \
                            ~np.isnan(np.array(results_mc["npv_values"])) & \
                            ~np.isnan(np.array(results_mc["payback_period_values"])) & \
                            ~np.isnan(np.array(results_mc["avg_dscr_values"]))

            if np.sum(valid_indices) > 0:
                roi_ok = np.array(results_mc["roi_values"])[valid_indices] >= 0.05
                irr_ok = np.array(results_mc["irr_values"])[valid_indices] >= 0.04
                npv_ok = np.array(results_mc["npv_values"])[valid_indices] >= 0
                payback_ok = np.array(results_mc["payback_period_values"])[valid_indices] <= payback_max_mc
                dscr_ok = np.array(results_mc["avg_dscr_values"])[valid_indices] >= target_dscr_mc
                probabilities['global'] = np.mean(roi_ok & irr_ok & npv_ok & payback_ok & dscr_ok)
            else:
                probabilities['global'] = 0.0


            monte_carlo_summary = {
                'scenario_name': scenario_name, 'prix_revente_simule': prix_revente,
                'n_iterations': n_iterations, 'n_valid_runs': n_valid_runs,
                'ecart_type_production_pct': ecart_type_production_pct,
                'ecart_type_consommation_pct': ecart_type_consommation_pct,
                'results': all_values, # Listes complètes avec NaN
                'statistics': stats,
                'probabilities': probabilities,
                'contraintes_mc': { # Rappeler les seuils utilisés pour les probas
                     'payback_max': payback_max_mc,
                     'dscr_min': target_dscr_mc
                }
            }
            print(f"LOGIQUE: Monte Carlo Terminé pour {scenario_name}. Temps: {time.time() - start_time_mc:.3f}s.")
            return monte_carlo_summary

        except (ValueError, TypeError, RuntimeError) as e:
             print(f"ERREUR LOGIQUE (run_monte_carlo): {e}")
             # traceback.print_exc() # Debug
             raise e # Renvoyer pour UI
        except Exception as e:
             print(f"ERREUR LOGIQUE INATTENDUE (run_monte_carlo): {e}")
             traceback.print_exc()
             raise RuntimeError(f"Erreur inattendue lors de Monte Carlo: {e}") from e