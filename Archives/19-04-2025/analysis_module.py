import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.optimize import minimize, newton
import time
from io import BytesIO
import io
import traceback 
import uuid # Pour les clés uniques de graphiques
import sys # Ajout de l'import manquant pour sys.modules

# Import xlsxwriter pour l'export avancé
try:
    import xlsxwriter
    from xlsxwriter.utility import xl_col_to_name
    XLSXWRITER_AVAILABLE = True
except ImportError:
    XLSXWRITER_AVAILABLE = False
    # Le warning sera affiché dans l'UI si nécessaire

# --- Gestion de la dépendance à numpy_financial ---
try:
    import numpy_financial as npf
    print("Numpy Financial trouvé.")
except ImportError:
    print("Numpy Financial non trouvé, utilisation des fonctions secours.")
    # st.warning affiché dans l'UI si nécessaire
    
    def secours_npv(rate, values):
        values = np.asarray(values)
        if abs(rate - (-1.0)) < 1e-9: return float('-inf') if np.any(values != 0) else 0.0
        if rate < -1.0: return float('-inf') 
        with np.errstate(over='raise', invalid='raise'): # Gérer aussi les 'invalid' (ex: 0/0)
             try:
                 discount_factors = (1 + rate) ** np.arange(len(values))
                 if np.any(np.isclose(discount_factors, 0)): return np.inf # Retourner infini si dénominateur nul
                 pv = values / discount_factors
                 if not np.all(np.isfinite(pv)): return np.inf # Retourner infini si NaN/inf
                 return np.sum(pv) # Utiliser np.sum pour meilleure gestion
             except (FloatingPointError, OverflowError): 
                 # Donner un signe à l'infini peut aider certains solveurs
                 return np.inf if rate >= -1.0 else -np.inf 

    def secours_irr(values, guess=0.1):
        values = np.asarray(values)
        if np.all(values >= 0) or np.all(values <= 0) or values[0] >= 0:
             return None 
        
        def objective(rate):
             res_npv = secours_npv(rate, values)
             if not np.isfinite(res_npv): return np.sign(res_npv) * 1e12 
             return res_npv

        from scipy.optimize import brentq 
        try:
            return brentq(objective, -0.9999, 10.0, maxiter=100, xtol=1e-6, rtol=1e-6) # Augmenter la précision
        except (ValueError, RuntimeError): 
             from scipy.optimize import newton
             for g in [guess, 0.05, 0.2, 0.0, -0.1]: 
                  try: return newton(objective, g, tol=1e-6, maxiter=100) # Augmenter la précision
                  except (RuntimeError, OverflowError): continue 
             return None 
        except Exception: 
             return None

    class NpfModule:
        @staticmethod
        def npv(rate, values): return secours_npv(rate, values)
        @staticmethod
        def irr(values): return secours_irr(values)
    
    npf = NpfModule()

# --- Classe Principale Fusionnée ---
class AnalysisModule:
    def __init__(self):
        """Initialise l'état de session pour ce module."""
        keys_to_initialize = {
            'economic_results': {},
            'optimization_results': {},
            'monte_carlo_results': {}
        }
        for key, default_value in keys_to_initialize.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
        
        # Afficher le warning numpy_financial une seule fois si nécessaire
        if 'npf_warning_shown' not in st.session_state and not hasattr(npf, '__module__') or npf.__module__ != 'numpy_financial':
             st.warning("Le package numpy_financial n'est pas installé. Utilisation de fonctions de secours pour IRR et NPV (peut être moins précis ou échouer dans certains cas). Installez avec : pip install numpy-financial")
             st.session_state.npf_warning_shown = True
             
        # Afficher le warning xlsxwriter une seule fois si nécessaire
        if 'xlsxwriter_warning_shown' not in st.session_state and not XLSXWRITER_AVAILABLE:
             st.warning("La bibliothèque 'xlsxwriter' n'est pas installée. L'export Excel avancé avec formules ne sera pas disponible. Installez-la avec : pip install xlsxwriter")
             st.session_state.xlsxwriter_warning_shown = True


    # --- Méthodes de Calcul Économique ---

    def calculate_wacc(self, debt_ratio, taux_interet_dette_pct, taux_imposition_pct, cout_fonds_propres_pct):
        """Calcule le WACC. Prend les taux en pourcentage."""
        try:
            rd = float(taux_interet_dette_pct) / 100.0
            tc = float(taux_imposition_pct) / 100.0
            re = float(cout_fonds_propres_pct) / 100.0
            dr = float(debt_ratio)
            
            if not (0 <= dr <= 1): raise ValueError("Debt ratio hors bornes [0, 1]")
            if not (0 <= tc < 1): raise ValueError("Taux imposition hors bornes [0, 1)")
            
            cout_dette_apres_impots = rd * (1.0 - tc)
            equity_ratio = 1.0 - dr
            wacc = (dr * cout_dette_apres_impots) + (equity_ratio * re)
            return wacc
        except (TypeError, ValueError) as e:
             st.error(f"Erreur de calcul WACC: Vérifiez les types/valeurs des taux. ({e})")
             return None # Retourner None en cas d'erreur

    def calculate_financial_indicators(self, scenario_name, prix_revente=None):
        """Calcule les indicateurs financiers pour un scénario (version détaillée)."""
        print(f"--- Calcul indicateurs détaillé : Scénario='{scenario_name}', Prix={prix_revente} ---")
        start_time_calc = time.time()
        try:
            # --- Vérifications Initiales Robustes ---
            if 'processed_data' not in st.session_state or st.session_state.processed_data is None or st.session_state.processed_data.empty:
                raise ValueError("Données traitées non disponibles.")
            if not isinstance(st.session_state.get('scenarios'), dict) or scenario_name not in st.session_state.scenarios:
                raise ValueError(f"Scénario '{scenario_name}' invalide.")
            if not isinstance(st.session_state.get('config'), dict):
                 raise ValueError("Configuration invalide.")

            data = st.session_state.processed_data.copy()
            scenario = st.session_state.scenarios[scenario_name]
            config = st.session_state.config

            # --- Validation et récupération des paramètres config ---
            required_keys = [
                "date_debut_ppa", "duree_ppa", "taux_inflation", "taux_imposition",
                "prix_vente_initial", "capex", "opex", "degradation_rate",
                "cout_fonds_propres", "with_loan", "tarif_oa", "tarif_edf_reference",
                "tarif_oa_indexe_inflation", "taux_inflation_tarif_oa",
                "subvention_calculee", "amortissement_duree", "valeur_residuelle_pct",
                "cout_demantelement_pct", "source_prix_autoconso"
            ]
            loan_keys = ["debt_ratio", "debt_term_years", "taux_interet_dette", "target_dscr"] 
            
            missing_keys = [k for k in required_keys if config.get(k) is None]
            loan_active = config.get("with_loan", True)
            if loan_active:
                 missing_keys.extend([k for k in loan_keys if config.get(k) is None])

            if missing_keys: raise ValueError(f"Clés config manquantes: {', '.join(missing_keys)}")

            # --- Récupération et Typage des Paramètres ---
            try:
                 simulation_years = int(config["duree_ppa"] / 12)
                 if simulation_years <= 0: raise ValueError("Durée PPA doit être positive.")
                 capex_base = float(config["capex"])
                 opex_base = float(config["opex"]) # OPEX final (incluant provision)
                 prix_vente_config = float(config["prix_vente_initial"])
                 prix_revente_input = float(prix_revente) if prix_revente is not None else None
                 prix_vente_a_utiliser = prix_revente_input if prix_revente_input is not None else prix_vente_config
                 degradation_rate_base = float(config["degradation_rate"])
                 total_subvention = float(config.get("subvention_calculee", 0.0))
                 taux_inflation = float(config["taux_inflation"]) / 100.0
                 oa_indexed = config.get("tarif_oa_indexe_inflation", False)
                 inflation_rate_oa = float(config.get("taux_inflation_tarif_oa", 1.5)) / 100.0
                 source_prix_autoc = config.get("source_prix_autoconso", "prix_initial")
                 tarif_edf_ref = float(config.get("tarif_edf_reference", 0.21))
                 tarif_oa_base = float(config.get('tarif_oa', 0.0))
                 taux_imposition_pct = float(config["taux_imposition"])
                 taux_imposition = taux_imposition_pct / 100.0
                 amortissement_duree = int(config.get("amortissement_duree", 15))
                 if amortissement_duree <= 0: raise ValueError("Durée amortissement doit être positive.")
                 valeur_residuelle_pct = float(config.get("valeur_residuelle_pct", 0.0)) / 100.0
                 cout_demantelement_pct = float(config.get("cout_demantelement_pct", 5.0)) / 100.0
                 cout_fonds_propres_pct = float(config.get("cout_fonds_propres", 8.0))
                 cout_fonds_propres = cout_fonds_propres_pct / 100.0
                 target_dscr = float(config.get('target_dscr', 1.2))
                 debt_ratio = float(config.get("debt_ratio", 0.80)) if loan_active else 0.0
                 debt_term_years = int(config.get("debt_term_years", 15)) if loan_active else 0
                 taux_interet_dette_pct = float(config.get("taux_interet_dette", 0.0)) if loan_active else 0.0
                 taux_interet_dette = taux_interet_dette_pct / 100.0
                 reference_year = datetime.fromisoformat(str(config["date_debut_ppa"])).year
            except (ValueError, TypeError, KeyError) as e:
                 raise ValueError(f"Erreur paramètre config/scenario: {e}")

            # --- Application Modificateurs Scénario ---
            try:
                 capex = capex_base * float(scenario.get("capex_modifier", 1.0))
                 opex_annual = opex_base * float(scenario.get("opex_modifier", 1.0))
                 adjusted_inflation = taux_inflation * float(scenario.get("inflation_modifier", 1.0))
                 degradation_rate = degradation_rate_base * float(scenario.get("degradation_modifier", 1.0))
                 production_modifier = float(scenario.get("production_modifier", 1.0))
            except (ValueError, TypeError) as e:
                 raise ValueError(f"Erreur modificateurs scénario '{scenario_name}': {e}")

            # Ajustements finaux
            equity_ratio = 1.0 - debt_ratio
            debt_amount = capex * debt_ratio
            equity_amount = capex * equity_ratio
            capex_net_subvention = max(0, capex - total_subvention) # Assurer non négatif
            net_equity_investment = equity_amount - total_subvention # Peut être négatif si grosse subvention

            # --- Préparation données énergétiques (Étape 1) ---
            required_data_cols = ['Temps', 'production_kwh', 'consumption_kwh']
            if not all(col in data.columns for col in required_data_cols):
                 raise ValueError(f"Colonnes manquantes: {set(required_data_cols) - set(data.columns)}")
            data['year'] = data['Temps'].dt.year
            reference_data = data[data['year'] == data['year'].min()].copy() 
            if reference_data.empty: raise ValueError("Aucune donnée de référence.")
            ref_prod = reference_data['production_kwh'].values
            ref_cons = reference_data['consumption_kwh'].values

            # --- Initialisation Tableaux Annuels ---
            years = np.arange(1, simulation_years + 1)
            arrays = {name: np.zeros(simulation_years) for name in [
                "annual_production", "annual_consumption", "annual_autoconsumption", "annual_surplus",
                "revenues", "opex", "depreciation", "ebitda", "ebit", "interest_paid", "ebt", 
                "taxes", "net_income", "principal_paid", "debt_service", "free_cash_flow", # CFE
                "cumulative_cash_flow", # CFE Cumulé Net
                "dscr" 
            ]}

            # --- Calcul Amortissement Annuel (Étape 8 partiel) ---
            base_amortissable = capex_net_subvention * (1 - valeur_residuelle_pct)
            if amortissement_duree > 0:
                 annual_depreciation_amount = base_amortissable / amortissement_duree
                 for i in range(min(simulation_years, amortissement_duree)):
                     arrays["depreciation"][i] = annual_depreciation_amount
            
            # --- Calcul Échéancier Dette (Étape 6) ---
            annual_debt_payment = 0.0
            if loan_active and abs(debt_amount) > 1e-6 and debt_term_years > 0:
                if abs(taux_interet_dette) < 1e-9:
                    annual_debt_payment = debt_amount / debt_term_years if debt_term_years > 0 else 0
                else:
                    try:
                        factor = (1 + taux_interet_dette) ** debt_term_years
                        denom = factor - 1
                        if abs(denom) < 1e-9: raise ValueError("Dénominateur annuité proche de zéro")
                        annual_debt_payment = debt_amount * taux_interet_dette * factor / denom
                        if not np.isfinite(annual_debt_payment): raise ValueError("Annuité non finie")
                    except (OverflowError, ValueError) as e_annuity:
                         raise ValueError(f"Erreur calcul annuité: {e_annuity}") from e_annuity

                remaining_debt = debt_amount
                for i in range(simulation_years):
                    if i < debt_term_years and remaining_debt > 1e-6:
                        arrays["interest_paid"][i] = remaining_debt * taux_interet_dette
                        principal_this_year = min(annual_debt_payment - arrays["interest_paid"][i], remaining_debt)
                        arrays["principal_paid"][i] = max(0, principal_this_year) 
                        remaining_debt -= arrays["principal_paid"][i]
                        remaining_debt = max(0, remaining_debt)
                        arrays["debt_service"][i] = arrays["interest_paid"][i] + arrays["principal_paid"][i]

            # --- Boucle Annuelle Principale ---
            print(f"DEBUG CALC: Démarrage boucle {simulation_years} années...")
            for idx, year_num in enumerate(years):
                # Étape 1 & 2
                degradation_factor = (1 - degradation_rate) ** (year_num - 1)
                current_production = ref_prod * degradation_factor * production_modifier
                current_consumption = ref_cons 
                autoconsumption_hourly = np.minimum(current_production, current_consumption)
                surplus_hourly = current_production - autoconsumption_hourly
                arrays["annual_production"][idx] = current_production.sum()
                arrays["annual_consumption"][idx] = current_consumption.sum() 
                arrays["annual_autoconsumption"][idx] = autoconsumption_hourly.sum()
                arrays["annual_surplus"][idx] = surplus_hourly.sum()

                # Étape 3
                inflation_factor = (1 + adjusted_inflation) ** (year_num - 1)
                if source_prix_autoc == "tarif_edf": prix_achat_evite = tarif_edf_ref * inflation_factor
                elif source_prix_autoc == "tarif_oa":
                     tarif_oa_year = tarif_oa_base * ((1 + inflation_rate_oa) ** (year_num - 1) if oa_indexed else 1)
                     prix_achat_evite = tarif_oa_year
                else: prix_achat_evite = prix_vente_a_utiliser * inflation_factor 
                revenus_autoconsommation = arrays["annual_autoconsumption"][idx] * prix_achat_evite
                tarif_oa_year = tarif_oa_base * ((1 + inflation_rate_oa) ** (year_num - 1) if oa_indexed else 1)
                revenus_surplus = arrays["annual_surplus"][idx] * tarif_oa_year
                arrays["revenues"][idx] = revenus_autoconsommation + revenus_surplus

                # Étape 4
                arrays["opex"][idx] = opex_annual * inflation_factor 
                if year_num == simulation_years:
                     cout_demantelement_final = capex_base * cout_demantelement_pct 
                     arrays["opex"][idx] += cout_demantelement_final 

                # Calculs Intermédiaires
                arrays["ebitda"][idx] = arrays["revenues"][idx] - arrays["opex"][idx]
                arrays["ebit"][idx] = arrays["ebitda"][idx] - arrays["depreciation"][idx]
                arrays["ebt"][idx] = arrays["ebit"][idx] - arrays["interest_paid"][idx] 

                # Étape 8
                arrays["taxes"][idx] = max(0, arrays["ebt"][idx] * taux_imposition)
                arrays["net_income"][idx] = arrays["ebt"][idx] - arrays["taxes"][idx]

                # Étape 9 (CFE)
                arrays["free_cash_flow"][idx] = arrays["net_income"][idx] + arrays["depreciation"][idx] - arrays["principal_paid"][idx]

            print("DEBUG CALC: Boucle annuelle terminée.")

            # --- Calculs Finaux ---
            print("DEBUG CALC: Calcul indicateurs finaux...")
            # CFE Cumulé Net
            if simulation_years > 0:
                arrays["cumulative_cash_flow"][0] = arrays["free_cash_flow"][0] - net_equity_investment 
                for i in range(1, simulation_years):
                    arrays["cumulative_cash_flow"][i] = arrays["cumulative_cash_flow"][i-1] + arrays["free_cash_flow"][i]

            # DSCR (basé sur EBITDA - Taxes)
            cfads = arrays["ebitda"] - arrays["taxes"]
            dscr = np.full_like(arrays["debt_service"], float('inf')) 
            mask = arrays["debt_service"] > 1e-9
            np.divide(cfads, arrays["debt_service"], out=dscr, where=mask)
            arrays["dscr"] = dscr # Stocker le tableau complet

            # Cash Flow Stream pour TRI/VAN
            cash_flows = np.concatenate(([-net_equity_investment], arrays["free_cash_flow"]))
            
            # Étape 10: KPI
            irr = None; npv = 0.0; roi = 0.0; payback_period = float('inf'); avg_dscr = float('inf')
            try: irr = npf.irr(cash_flows); irr = irr if np.isfinite(irr) else None
            except Exception: pass 
            
            wacc = self.calculate_wacc(debt_ratio, taux_interet_dette_pct, taux_imposition_pct, cout_fonds_propres_pct)
            try: npv = npf.npv(cout_fonds_propres, cash_flows); npv = npv if np.isfinite(npv) else 0.0 # Actualisé au coût FP
            except Exception: pass 

            if abs(net_equity_investment) > 1e-9: roi = npv / net_equity_investment; roi = roi if np.isfinite(roi) else 0.0 
            elif net_equity_investment <=0: roi = float('inf') if npv > 0 else (-float('inf') if npv < 0 else 0)

            if simulation_years > 0:
                cum_cf_corrected = np.concatenate(([-net_equity_investment], arrays["cumulative_cash_flow"]))
                positive_indices = np.where(cum_cf_corrected >= -1e-9)[0] 
                if len(positive_indices) > 0:
                    first_positive_idx = positive_indices[0] 
                    if first_positive_idx == 0: payback_period = 0.0
                    else: 
                         year_before_positive_1based = first_positive_idx 
                         last_negative_cum_cf = cum_cf_corrected[first_positive_idx - 1]
                         cash_flow_crossing_year = arrays["free_cash_flow"][first_positive_idx - 1] 
                         if cash_flow_crossing_year > 1e-9: fraction = -last_negative_cum_cf / cash_flow_crossing_year; payback_period = (year_before_positive_1based - 1) + fraction 
                         else: payback_period = float('inf') 
            
            if loan_active and debt_term_years > 0:
                 dscr_term_indices = np.arange(min(simulation_years, int(debt_term_years)))
                 if len(dscr_term_indices) > 0:
                      dscr_in_term = arrays["dscr"][dscr_term_indices]
                      dscr_finite_in_term = dscr_in_term[np.isfinite(dscr_in_term)]
                      if len(dscr_finite_in_term) > 0: avg_dscr = np.mean(dscr_finite_in_term)

            # Taux auto conso/prod
            total_annual_production = arrays["annual_production"].sum()
            total_annual_consumption = arrays["annual_consumption"].sum() 
            total_annual_autoconsumption = arrays["annual_autoconsumption"].sum()
            autoconsumption_rate = total_annual_autoconsumption / total_annual_production if total_annual_production > 1e-9 else 0
            autoproduction_rate = total_annual_autoconsumption / total_annual_consumption if total_annual_consumption > 1e-9 else 0

            # --- Dictionnaire de Résultats Final ---
            results = { "scenario": scenario_name, "prix_revente": prix_vente_a_utiliser,
                        "capex": capex, "equity_amount": equity_amount, "debt_amount": debt_amount,
                        "total_subvention": total_subvention, "net_equity_investment": net_equity_investment,
                        "autoconsumption_rate": autoconsumption_rate, "autoproduction_rate": autoproduction_rate,
                        "irr": irr, "wacc": wacc, "npv": npv, 
                        "roi": roi if np.isfinite(roi) else None,
                        "payback_period": payback_period if np.isfinite(payback_period) else None,
                        "avg_dscr": avg_dscr if np.isfinite(avg_dscr) else None,
                        "years": years.tolist(),
                        "cash_flows_for_irr_npv": cash_flows.tolist(), # CFE Stream Net
                        # Ajouter les séries annuelles détaillées
                        **{key: arr.tolist() for key, arr in arrays.items()} 
                       }
            print(f"DEBUG CALC: Calcul terminé avec succès en {time.time() - start_time_calc:.2f}s.")
            return results

        except Exception as e:
            st.error(f"Erreur majeure inattendue dans calculs : {str(e)}")
            st.error(traceback.format_exc())
            print(f"ERREUR CALC: Exception majeure - {e}\n{traceback.format_exc()}")
            return None

# --- Méthodes d'Optimisation ---
    
    def _eval_roi(self, roi):
        """Évalue le ROI par rapport à un objectif."""
        if roi <= 0:
            return 0
        elif roi >= 0.15:  # ROI max pris en compte (15%)
            return 1
        else:
            return roi / 0.15
    
    def _eval_irr(self, irr):
        """Évalue le TRI par rapport à un objectif."""
        if irr is None or irr <= 0:
            return 0
        elif irr >= 0.12:  # TRI max pris en compte (12%)
            return 1
        else:
            return irr / 0.12
    
    def _eval_payback(self, payback):
        """Évalue la période de récupération par rapport à un objectif."""
        if payback == float('inf') or payback >= 25:
            return 0
        elif payback <= 5:  # Payback idéal (5 ans)
            return 1
        else:
            return 1 - (payback - 5) / 20
    
    def _eval_dscr(self, dscr):
        """Évalue le DSCR par rapport à un objectif."""
        target_dscr = st.session_state.config.get('target_dscr', 1.2)
        if dscr < target_dscr:
            return 0
        elif dscr >= 2:  # DSCR max pris en compte (2)
            return 1
        else:
            return (dscr - target_dscr) / (2 - target_dscr)
    
    def _eval_competitive(self, prix):
        """Évalue la compétitivité du prix par rapport au tarif EDF."""
        tarif_edf = st.session_state.config.get('tarif_edf_reference', 0.21)
        if prix >= tarif_edf:
            return 0
        else:
            return 1 - prix / tarif_edf
    
    def optimize_selling_price(self, scenario_name):
        """
        Optimise le prix de revente pour un scénario donné.
        
        Args:
            scenario_name: Nom du scénario à optimiser
            
        Returns:
            dict: Dictionnaire contenant les résultats de l'optimisation
        """
        print(f"DEBUG OPT: Lancement optimize_selling_price pour {scenario_name}")
        config = st.session_state.config
        prix_min = config.get('prix_min_revente', 0.10)
        prix_max = config.get('prix_max_revente', 0.25)
        pas = config.get('pas_optimisation', 0.01)

        if prix_min >= prix_max:
             st.error("Prix minimum de revente doit être inférieur au prix maximum.")
             return None

        prix_a_tester = np.arange(prix_min, prix_max + pas, pas)
        if len(prix_a_tester) == 0:
             st.error("Plage de prix invalide ou pas trop grand.")
             return None
             
        print(f"DEBUG OPT: Prix à tester: {prix_a_tester}")

        resultats = {}
        progress_bar = st.progress(0)
        total_prices = len(prix_a_tester)

        for i, prix in enumerate(prix_a_tester):
            print(f"DEBUG OPT: Calcul pour prix={prix:.4f}")
            # Appel à LA MÊME CLASSE pour le calcul
            res_calc = self.calculate_financial_indicators(scenario_name, prix_revente=prix) 
            resultats[prix] = res_calc # Stocker même si None pour analyse score
            progress_bar.progress((i + 1) / total_prices)
            
        # Scoring
        prix_optimal = None
        indicateurs_optimaux = None
        score_max = -float('inf')
        
        target_dscr = config.get('target_dscr', 1.2)
        tarif_edf = config.get('tarif_edf_reference', 0.21)
        
        # Poids pour le score global
        weights = {'roi': 0.25, 'irr': 0.20, 'payback': 0.15, 'dscr': 0.20, 'competitive': 0.20}

        print("DEBUG OPT: Début scoring...")
        for prix, res in resultats.items():
            if res is None: continue # Ignorer les calculs échoués

            scores = {}
            scores['roi'] = self._eval_roi(res.get('roi', 0))
            scores['irr'] = self._eval_irr(res.get('irr', None))
            scores['payback'] = self._eval_payback(res.get('payback_period', float('inf')))
            scores['dscr'] = self._eval_dscr(res.get('avg_dscr', 0))
            scores['competitive'] = self._eval_competitive(prix)
            score_global = sum(weights[k] * scores[k] for k in weights)
            
            print(f"DEBUG OPT: Prix={prix:.4f}, Score={score_global:.4f}, Scores={scores}")
            
            res['scores'] = scores # Ajouter les scores aux résultats pour ce prix
            res['scores']['score_global'] = score_global # Ajouter le score global

            if score_global > score_max:
                score_max = score_global
                prix_optimal = prix
                indicateurs_optimaux = res # Contient déjà les scores

        print(f"DEBUG OPT: Optimisation terminée. Prix optimal={prix_optimal}, Score max={score_max}")

        if prix_optimal is None:
             st.warning("Aucun prix optimal trouvé (tous les calculs ont peut-être échoué).")
             return None

        resultats_optimisation = {
            'scenario_name': scenario_name,
            'prix_optimal': prix_optimal,
            'indicateurs_optimaux': indicateurs_optimaux, # Contient les indicateurs ET les scores
            'tous_resultats': resultats, # Contient tous les résultats par prix testé
            'prix_testes': list(prix_a_tester)
        }
        return resultats_optimisation

    def run_monte_carlo_simulation(self, scenario_name, prix_revente=None):
        """
        Exécute une simulation Monte Carlo pour évaluer la robustesse.
        
        Args:
            scenario_name: Nom du scénario à utiliser
            prix_revente: Prix de revente à utiliser (si None, utilise le prix optimal)
            
        Returns:
            dict: Dictionnaire contenant les résultats de la simulation Monte Carlo
        """
        print(f"DEBUG MC: Lancement run_monte_carlo_simulation pour {scenario_name}")
        config = st.session_state.config
        
        n_iterations = config.get('nb_iterations_monte_carlo', 1000)
        ecart_type_production = config.get('ecart_type_production', 10.0) / 100.0
        ecart_type_consommation = config.get('ecart_type_consommation', 5.0) / 100.0
        target_dscr = config.get('target_dscr', 1.2)

        if prix_revente is None:
            if scenario_name in st.session_state.get('optimization_results', {}):
                prix_revente = st.session_state.optimization_results[scenario_name].get('prix_optimal')
                if prix_revente is None: # Si l'optimisation n'a pas trouvé de prix
                     prix_revente = config.get('prix_vente_initial', 0.17)
                     st.warning(f"Prix optimal non trouvé pour {scenario_name}, utilisation du prix initial {prix_revente:.4f} €/kWh pour Monte Carlo.")
                else:
                    st.info(f"Utilisation du prix optimal trouvé ({prix_revente:.4f} €/kWh) pour Monte Carlo.")
            else:
                prix_revente = config.get('prix_vente_initial', 0.17)
                st.info(f"Aucun résultat d'optimisation pour {scenario_name}, utilisation du prix initial {prix_revente:.4f} €/kWh pour Monte Carlo.")
        else:
             st.info(f"Utilisation du prix personnalisé ({prix_revente:.4f} €/kWh) pour Monte Carlo.")

        roi_values, irr_values, npv_values, payback_values, dscr_values = [], [], [], [], []
        
        if 'processed_data' not in st.session_state or st.session_state.processed_data is None:
             st.error("Données traitées non disponibles pour la simulation Monte Carlo.")
             return None
             
        original_data = st.session_state.processed_data.copy()
        
        # Sauvegarder l'état original de processed_data dans session_state pour restauration
        st.session_state['_original_processed_data_mc'] = original_data

        progress_bar = st.progress(0)
        status_text = st.empty()

        print(f"DEBUG MC: Démarrage boucle de {n_iterations} itérations.")
        try:
            for i in range(n_iterations):
                status_text.text(f"Iteration {i+1}/{n_iterations}")
                simulated_data = original_data.copy()
                
                # Variations aléatoires
                prod_variation = np.random.normal(1, ecart_type_production)
                cons_variation = np.random.normal(1, ecart_type_consommation)
                simulated_data['production_kwh'] = (simulated_data['production_kwh'] * prod_variation).clip(lower=0)
                simulated_data['consumption_kwh'] = (simulated_data['consumption_kwh'] * cons_variation).clip(lower=0)
                
                # Mettre à jour l'autoconsommation avec les nouvelles valeurs
                simulated_data['autoconsumption_kwh'] = simulated_data.apply(
                    lambda row: min(row['production_kwh'], row['consumption_kwh']), axis=1
                )
                
                # Recalculer le surplus
                simulated_data['surplus_kwh'] = simulated_data['production_kwh'] - simulated_data['autoconsumption_kwh']
                
                # Remplacer temporairement les données pour le calcul
                st.session_state.processed_data = simulated_data
                
                # Appel à LA MÊME CLASSE pour le calcul
                results = self.calculate_financial_indicators(scenario_name, prix_revente=prix_revente)
                
                if results:
                    roi_values.append(results.get('roi', 0)) # Utiliser 0 si clé absente
                    irr_values.append(results.get('irr', 0) if results.get('irr') is not None else 0)
                    npv_values.append(results.get('npv', 0))
                    payback_values.append(results.get('payback_period', float('inf')))
                    dscr_values.append(results.get('avg_dscr', 0))
                else: # Si le calcul échoue pour une itération
                     roi_values.append(0)
                     irr_values.append(0)
                     npv_values.append(0)
                     payback_values.append(float('inf'))
                     dscr_values.append(0)

                progress_bar.progress((i + 1) / n_iterations)
        
        finally: # Assurer la restauration des données originales même en cas d'erreur
             # Restaurer les données originales
             if '_original_processed_data_mc' in st.session_state:
                 st.session_state.processed_data = st.session_state['_original_processed_data_mc']
                 del st.session_state['_original_processed_data_mc'] # Nettoyer la clé temporaire
             status_text.text("Calcul des statistiques...")
             print("DEBUG MC: Boucle terminée, restauration des données originales.")

        # Calcul des statistiques (après la boucle)
        roi_values = np.array(roi_values)
        irr_values = np.array(irr_values)
        npv_values = np.array(npv_values)
        payback_values = np.array([p if p != float('inf') else 30 for p in payback_values]) # Remplacer inf par 30 pour stats
        dscr_values = np.array([d if d != float('inf') else 5 for d in dscr_values]) # Remplacer inf par 5 pour stats
        
        # Calcul des probabilités
        roi_min = 0.05; irr_min = 0.04; payback_max = 15; dscr_min_mc = target_dscr
        prob_roi = np.mean(roi_values >= roi_min)
        prob_irr = np.mean(irr_values >= irr_min)
        prob_payback = np.mean(payback_values <= payback_max)
        prob_dscr = np.mean(dscr_values >= dscr_min_mc)
        prob_global = np.mean((roi_values >= roi_min) & (irr_values >= irr_min) & 
                              (payback_values <= payback_max) & (dscr_values >= dscr_min_mc))

        monte_carlo_results = {
            'scenario_name': scenario_name, 
            'prix_revente': prix_revente, 
            'n_iterations': n_iterations,
            'ecart_type_production': ecart_type_production, 
            'ecart_type_consommation': ecart_type_consommation,
            'roi_values': roi_values.tolist(), 
            'irr_values': irr_values.tolist(), 
            'npv_values': npv_values.tolist(),
            'payback_values': payback_values.tolist(), 
            'dscr_values': dscr_values.tolist(),
            'statistics': {
                'roi': {'mean': np.mean(roi_values), 'std': np.std(roi_values), 
                        'percentiles': np.percentile(roi_values, [5, 25, 50, 75, 95]).tolist()},
                'irr': {'mean': np.mean(irr_values), 'std': np.std(irr_values), 
                        'percentiles': np.percentile(irr_values, [5, 25, 50, 75, 95]).tolist()},
                'npv': {'mean': np.mean(npv_values), 'std': np.std(npv_values), 
                        'percentiles': np.percentile(npv_values, [5, 25, 50, 75, 95]).tolist()},
                'payback': {'mean': np.mean(payback_values), 'std': np.std(payback_values), 
                            'percentiles': np.percentile(payback_values, [5, 25, 50, 75, 95]).tolist()},
                'dscr': {'mean': np.mean(dscr_values), 'std': np.std(dscr_values), 
                         'percentiles': np.percentile(dscr_values, [5, 25, 50, 75, 95]).tolist()}
            },
            'probabilities': {
                'roi': prob_roi, 'irr': prob_irr, 'payback': prob_payback, 
                'dscr': prob_dscr, 'global': prob_global
            }
        }
        status_text.text("Simulation Monte Carlo terminée.")
        print("DEBUG MC: Fin run_monte_carlo_simulation")
        return monte_carlo_results

    def simulate_selling_price(self, scenario_name, target_irr=None, target_npv=None):
        """
        Simule différents prix pour atteindre un TRI ou une VAN cible
        
        Args:
            scenario_name: Nom du scénario à simuler
            target_irr: TRI cible en pourcentage
            target_npv: VAN cible en euros
            
        Returns:
            dict: Résultats avec le prix optimal
        """
        if target_irr is None and target_npv is None:
            st.error("Veuillez spécifier soit un TRI cible, soit une VAN cible.")
            return None
            
        if target_irr is not None and target_npv is not None:
            st.warning("Veuillez spécifier soit un TRI cible, soit une VAN cible, mais pas les deux.")
            return None
        
        # Convertir le TRI cible en décimal si fourni
        target_irr_decimal = None
        if target_irr is not None:
            target_irr_decimal = target_irr / 100.0  # Convertir de pourcentage en décimal
            
        # Fonction objectif pour l'optimisation
        def objective(prix_revente):
            results = self.calculate_financial_indicators(scenario_name, prix_revente[0])
            if results is None:
                return float('inf')
                
            if target_irr_decimal is not None:
                if results['irr'] is None:
                    return float('inf')
                return abs(results['irr'] - target_irr_decimal)
            else:
                return abs(results['npv'] - target_npv)
        
        # Point de départ
        config = st.session_state.config
        x0 = [config.get('prix_vente_initial', 0.15)]
        
        # Bornes pour le prix de revente
        bounds = [(0.05, 0.5)]  # Plage de prix raisonnable
        
        # Optimisation
        from scipy.optimize import minimize
        result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')
        
        if not result.success:
            st.error("L'optimisation n'a pas convergé. Impossible de trouver un prix de revente optimal.")
            # Essayer une méthode plus robuste
            result = minimize(objective, x0, bounds=bounds, method='Nelder-Mead')
            if not result.success:
                return None
            
        # Calculer les indicateurs avec le prix optimal
        prix_optimal = result.x[0]
        results = self.calculate_financial_indicators(scenario_name, prix_optimal)
        
        if results is None:
            st.error("Erreur lors du calcul des indicateurs avec le prix optimal.")
            return None
            
        # Ajouter le prix optimal aux résultats
        results['prix_revente_optimal'] = prix_optimal
        results['target_irr'] = target_irr
        results['target_npv'] = target_npv
        
        return results
    
    def compare_scenarios(self, scenario_names):
        """
        Compare les indicateurs financiers pour plusieurs scénarios
        
        Args:
            scenario_names: Liste des noms de scénarios à comparer
            
        Returns:
            dict: Dictionnaire contenant les comparaisons
        """
        results = {}
        
        for scenario_name in scenario_names:
            results[scenario_name] = self.calculate_financial_indicators(scenario_name)
        
        return results
    
    def sensitivity_analysis(self, scenario_name, parameter, values):
        """
        Réalise une analyse de sensibilité sur un paramètre
        
        Args:
            scenario_name: Scénario de base
            parameter: Paramètre à faire varier
            values: Liste des valeurs à tester
            
        Returns:
            dict: Résultats pour chaque valeur
        """
        results = {}
        
        # Créer une copie de la configuration
        config_original = dict(st.session_state.config)
        
        try:
            # Pour chaque valeur à tester
            for value in values:
                # Configuration temporaire avec la valeur modifiée
                config_temp = dict(config_original)
                
                # Modifier le paramètre approprié
                if parameter == 'prix_revente':
                    # Cas spécial: utilisez directement le paramètre prix_revente
                    results[value] = self.calculate_financial_indicators(scenario_name, prix_revente=value)
                    continue
                elif parameter == 'inflation':
                    config_temp['taux_inflation'] = value
                elif parameter == 'opex':
                    config_temp['opex'] = value
                elif parameter == 'capex':
                    config_temp['capex'] = value
                elif parameter == 'debt_ratio':
                    config_temp['debt_ratio'] = value
                elif parameter == 'debt_term_years':
                    config_temp['debt_term_years'] = value
                elif parameter == 'degradation_rate':
                    config_temp['degradation_rate'] = value
                elif parameter == 'target_dscr':
                    config_temp['target_dscr'] = value
                else:
                    st.error(f"Paramètre inconnu : {parameter}")
                    continue
                
                # Mettre à jour la configuration temporairement
                st.session_state.config = config_temp
                
                # Calculer les indicateurs financiers
                results[value] = self.calculate_financial_indicators(scenario_name)
                
            return results
        finally:
            # Toujours restaurer la configuration originale
            st.session_state.config = config_original
    
    # --- Méthodes d'Affichage ---
    
    def display_financial_results(self, results, key_prefix=""):
        """
        Affiche les résultats financiers d'un scénario
        
        Args:
            results: Dictionnaire contenant les résultats financiers
            key_prefix: Préfixe pour les clés Streamlit
        """
        # Récupérer le nom du scénario pour créer des clés uniques
        scenario_name = results['scenario']
        
        # Générer un ID unique pour éviter les conflits de clés
        unique_id = int(time.time() * 1000) % 10000
        
        st.markdown("### Résultats de l'Analyse Financière")
        
        # Utiliser des métriques Streamlit au lieu du HTML personnalisé
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Rentabilité**")
            st.metric("ROI", f"{results['roi']*100:.2f}%" if results['roi'] is not None else "N/A")
            
            irr_value = f"{results['irr']*100:.2f}%" if results['irr'] is not None else "N/A"
            st.metric("TRI (IRR)", irr_value)
        
        with col2:
            st.markdown("**Viabilité**")
            st.metric("DSCR moyen", f"{results['avg_dscr']:.2f}" if results['avg_dscr'] is not None else "N/A")
            
            payback_value = f"{results['payback_period']:.2f} ans" if results['payback_period'] is not None and results['payback_period'] != float('inf') else "N/A"
            st.metric("Retour sur investissement", payback_value)
        
        with col3:
            st.markdown("**Performance**")
            st.metric("VAN (NPV)", f"{results['npv']:,.0f} €")
            st.metric("Prix de revente", f"{results['prix_revente']:.4f} €/kWh")
        
        # Paramètres financiers en expandable section
        with st.expander("Détails des paramètres financiers"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Ratio Dette/Total", f"{results.get('debt_ratio', 0)*100:.1f}%")
                st.metric("CAPEX", f"{results['capex']:,.2f} €")
            
            with col2:
                st.metric("Durée du prêt", f"{results.get('debt_term_years', 0)} ans")
                st.metric("Dette", f"{results['debt_amount']:,.2f} €")
            
            with col3:
                st.metric("Fonds propres", f"{results['equity_amount']:,.2f} €")
                if 'total_subvention' in results:
                    st.metric("Subvention", f"{results['total_subvention']:,.2f} €")
                st.metric("WACC", f"{results['wacc']*100:.2f}%" if results.get('wacc') is not None else "N/A")
            
            with col4:
                st.metric("Taux Dégradation", f"{results.get('degradation_rate', 0)*100:.2f}% par an")
                st.metric("Autoconsommation", f"{results['autoconsumption_rate']*100:.2f}%")
        
        # Créer un DataFrame pour faciliter la création de graphiques
        df_financial = pd.DataFrame({
            "Année": results['years'],
            "Revenus": results['revenues'],
            "OPEX": results['opex'],
            "EBITDA": results['ebitda'],
            "Service de la Dette": results['debt_service'],
            "Free Cash Flow": results['free_cash_flow'],
            "Flux Cumulé": results['cumulative_cash_flow'],
            "DSCR": results['dscr']
        })
        
        # Option de filtrage par année
        années_min = int(min(df_financial['Année']))
        années_max = int(max(df_financial['Année']))
        années_range = st.slider(
            "Plage d'années à afficher",
            min_value=années_min, 
            max_value=années_max,
            value=(années_min, min(années_min + 10, années_max)),
            key=f"{key_prefix}year_range_{unique_id}"
        )
        
        # Filtrer les données selon la plage sélectionnée
        df_filtered = df_financial[(df_financial['Année'] >= années_range[0]) & (df_financial['Année'] <= années_range[1])]
        
        # Onglets regroupés
        tab1, tab2 = st.tabs(["Vue d'ensemble financière", "Analyse détaillée"])
        
        with tab1:
            # Graphique combiné principal
            st.markdown("### Principaux flux financiers")
            
            fig = go.Figure()
            
            # Barres pour revenus et OPEX
            fig.add_trace(go.Bar(
                x=df_filtered['Année'],
                y=df_filtered['Revenus'],
                name='Revenus',
                marker_color='green'
            ))
            
            fig.add_trace(go.Bar(
                x=df_filtered['Année'],
                y=df_filtered['OPEX'],
                name='OPEX',
                marker_color='red'
            ))
            
            # Lignes pour EBITDA et Free Cash Flow
            fig.add_trace(go.Scatter(
                x=df_filtered['Année'],
                y=df_filtered['EBITDA'],
                name='EBITDA',
                mode='lines+markers',
                line=dict(color='blue', width=3),
                marker=dict(size=8)
            ))
            
            fig.add_trace(go.Scatter(
                x=df_filtered['Année'],
                y=df_filtered['Free Cash Flow'],
                name='Free Cash Flow',
                mode='lines+markers',
                line=dict(color='purple', width=2),
                marker=dict(size=6)
            ))
            
            # Flux cumulé sur axe secondaire
            fig.add_trace(go.Scatter(
                x=df_filtered['Année'],
                y=df_filtered['Flux Cumulé'],
                name='Flux Cumulé',
                mode='lines+markers',
                line=dict(color='orange', width=2),
                marker=dict(size=6),
                yaxis="y2"
            ))
            
            # Ligne zéro
            fig.add_shape(
                type="line",
                x0=df_filtered['Année'].min(),
                y0=0,
                x1=df_filtered['Année'].max(),
                y1=0,
                line=dict(color="black", width=2, dash="dash")
            )
            
            fig.update_layout(
                title="Évolution des flux financiers",
                xaxis_title="Année",
                yaxis_title="Montant (€)",
                yaxis2=dict(
                    title="Flux Cumulé (€)",
                    overlaying="y",
                    side="right"
                ),
                barmode='group',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}combined_chart_{scenario_name}_{unique_id}")
            
            # DSCR dans un graphique séparé
            st.markdown("### DSCR (Ratio de couverture du service de la dette)")
            
            fig_dscr = go.Figure()
            fig_dscr.add_trace(go.Scatter(
                x=df_filtered['Année'],
                y=df_filtered['DSCR'],
                name='DSCR',
                mode='lines+markers',
                line=dict(color='blue', width=3),
                marker=dict(size=8)
            ))
            
            # Ligne DSCR cible
            target_dscr = st.session_state.config.get('target_dscr', 1.2)
            fig_dscr.add_shape(
                type="line",
                x0=df_filtered['Année'].min(),
                y0=target_dscr,
                x1=df_filtered['Année'].max(),
                y1=target_dscr,
                line=dict(color="red", width=2, dash="dash")
            )
            
            fig_dscr.add_annotation(
                x=df_filtered['Année'].max(),
                y=target_dscr,
                text=f"DSCR Cible = {target_dscr}",
                showarrow=False,
                yshift=10,
                font=dict(color="red")
            )
            
            fig_dscr.update_layout(
                xaxis_title="Année",
                yaxis_title="DSCR",
                height=400  # Hauteur réduite
            )
            
            st.plotly_chart(fig_dscr, use_container_width=True, key=f"{key_prefix}dscr_chart_{scenario_name}_{unique_id}")
            
            # Tableau détaillé accessible via un expandeur
            with st.expander("Tableau détaillé des flux financiers"):
                st.dataframe(df_financial, key=f"{key_prefix}financial_df_{scenario_name}_{unique_id}")
        
        with tab2:
            # Analyse plus détaillée dans cet onglet
            st.markdown("### Analyse Détaillée des Flux Financiers")
            
            # Créer des onglets pour différentes visualisations détaillées
            detail_tab1, detail_tab2, detail_tab3 = st.tabs(["Production & Consommation", "Indicateurs Annuels", "Comparaison Amortissement & Dette"])
            
            with detail_tab1:
                # Graphique de la production, consommation et autoconsommation
                st.markdown("#### Données Énergétiques Annuelles")
                
                # Créer un DataFrame pour les données de production
                df_energy = pd.DataFrame({
                    "Année": results['years'],
                    "Production (kWh)": results['annual_production'],
                    "Consommation (kWh)": results['annual_consumption'],
                    "Autoconsommation (kWh)": results['annual_autoconsumption'],
                    "Surplus (kWh)": results['annual_surplus']
                })
                
                fig_energy = go.Figure()
                
                # Ajouter les traces au graphique
                fig_energy.add_trace(go.Bar(
                    x=df_energy['Année'],
                    y=df_energy['Production (kWh)'],
                    name='Production',
                    marker_color='gold'
                ))
                
                fig_energy.add_trace(go.Bar(
                    x=df_energy['Année'],
                    y=df_energy['Consommation (kWh)'],
                    name='Consommation',
                    marker_color='blue'
                ))
                
                fig_energy.add_trace(go.Bar(
                    x=df_energy['Année'],
                    y=df_energy['Autoconsommation (kWh)'],
                    name='Autoconsommation',
                    marker_color='green'
                ))
                
                fig_energy.add_trace(go.Bar(
                    x=df_energy['Année'],
                    y=df_energy['Surplus (kWh)'],
                    name='Surplus',
                    marker_color='orange'
                ))
                
                fig_energy.update_layout(
                    title="Production, Consommation et Autoconsommation Annuelles",
                    xaxis_title="Année",
                    yaxis_title="Énergie (kWh)",
                    barmode='group',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig_energy, use_container_width=True, key=f"{key_prefix}energy_chart_{scenario_name}_{unique_id}")
                
                with st.expander("Taux d'autoconsommation et d'autoproduction"):
                    # Calculer les taux annuels
                    df_energy['Taux Autoconsommation (%)'] = df_energy['Autoconsommation (kWh)'] / df_energy['Production (kWh)'] * 100
                    df_energy['Taux Autoproduction (%)'] = df_energy['Autoconsommation (kWh)'] / df_energy['Consommation (kWh)'] * 100
                    
                    # Graphique des taux
                    fig_rates = go.Figure()
                    
                    fig_rates.add_trace(go.Scatter(
                        x=df_energy['Année'],
                        y=df_energy['Taux Autoconsommation (%)'],
                        name="Taux d'autoconsommation",
                        mode='lines+markers',
                        line=dict(color='green', width=2),
                        marker=dict(size=8)
                    ))
                    
                    fig_rates.add_trace(go.Scatter(
                        x=df_energy['Année'],
                        y=df_energy['Taux Autoproduction (%)'],
                        name="Taux d'autoproduction",
                        mode='lines+markers',
                        line=dict(color='blue', width=2),
                        marker=dict(size=8)
                    ))
                    
                    fig_rates.update_layout(
                        title="Évolution des Taux d'Autoconsommation et d'Autoproduction",
                        xaxis_title="Année",
                        yaxis_title="Taux (%)",
                        yaxis=dict(range=[0, 100]),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    
                    st.plotly_chart(fig_rates, use_container_width=True, key=f"{key_prefix}rates_chart_{scenario_name}_{unique_id}")
            
            with detail_tab2:
                # Indicateurs financiers annuels
                st.markdown("#### Évolution des Indicateurs Financiers Annuels")
                
                # Sélection des indicateurs à afficher
                indicators = st.multiselect(
                    "Sélectionner les indicateurs à afficher",
                    options=["Revenus", "OPEX", "EBITDA", "Free Cash Flow", "Flux Cumulé", "DSCR", "Impôts"],
                    default=["Revenus", "EBITDA", "Free Cash Flow"],
                    key=f"{key_prefix}indicators_select_{unique_id}"
                )
                
                if indicators:
                    # Créer un DataFrame avec les indicateurs sélectionnés
                    df_indicators = pd.DataFrame({"Année": results['years']})
                    
                    # Ajouter les indicateurs sélectionnés
                    if "Revenus" in indicators:
                        df_indicators["Revenus"] = results['revenues']
                    
                    if "OPEX" in indicators:
                        df_indicators["OPEX"] = results['opex']
                    
                    if "EBITDA" in indicators:
                        df_indicators["EBITDA"] = results['ebitda']
                    
                    if "Free Cash Flow" in indicators:
                        df_indicators["Free Cash Flow"] = results['free_cash_flow']
                    
                    if "Flux Cumulé" in indicators:
                        df_indicators["Flux Cumulé"] = results['cumulative_cash_flow']
                    
                    if "DSCR" in indicators:
                        df_indicators["DSCR"] = results['dscr']
                    
                    if "Impôts" in indicators:
                        df_indicators["Impôts"] = results['taxes']
                    
                    # Graphique des indicateurs sélectionnés
                    fig_indicators = go.Figure()
                    
                    # Couleurs pour les différents indicateurs
                    colors = {
                        "Revenus": "green",
                        "OPEX": "red",
                        "EBITDA": "blue",
                        "Free Cash Flow": "purple",
                        "Flux Cumulé": "orange",
                        "DSCR": "black",
                        "Impôts": "brown"
                    }
                    
                    # Ajouter les traces au graphique
                    for indicator in indicators:
                        # Si l'indicateur est DSCR, utiliser un axe secondaire
                        if indicator == "DSCR":
                            fig_indicators.add_trace(go.Scatter(
                                x=df_indicators['Année'],
                                y=df_indicators[indicator],
                                name=indicator,
                                mode='lines+markers',
                                line=dict(color=colors[indicator], width=2),
                                marker=dict(size=6),
                                yaxis="y2"
                            ))
                        else:
                            fig_indicators.add_trace(go.Scatter(
                                x=df_indicators['Année'],
                                y=df_indicators[indicator],
                                name=indicator,
                                mode='lines+markers',
                                line=dict(color=colors[indicator], width=2),
                                marker=dict(size=6)
                            ))
                    
                    # Mise en page du graphique
                    layout = {
                        "title": "Évolution des Indicateurs Financiers",
                        "xaxis_title": "Année",
                        "yaxis_title": "Montant (€)",
                        "legend": dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        "hovermode": "x unified"
                    }
                    
                    # Ajouter un axe secondaire si DSCR est sélectionné
                    if "DSCR" in indicators:
                        layout["yaxis2"] = {
                            "title": "DSCR",
                            "overlaying": "y",
                            "side": "right"
                        }
                    
                    fig_indicators.update_layout(**layout)
                    
                    # Ajouter une ligne zéro
                    fig_indicators.add_shape(
                        type="line",
                        x0=df_indicators['Année'].min(),
                        y0=0,
                        x1=df_indicators['Année'].max(),
                        y1=0,
                        line=dict(color="black", width=1, dash="dash")
                    )
                    
                    st.plotly_chart(fig_indicators, use_container_width=True, key=f"{key_prefix}indicators_chart_{scenario_name}_{unique_id}")
                    
                else:
                    st.info("Veuillez sélectionner au moins un indicateur à afficher.")
            
            with detail_tab3:
                # Comparaison Amortissement et Service de la Dette
                st.markdown("#### Amortissement et Service de la Dette")
                
                # Créer un DataFrame
                df_debt = pd.DataFrame({
                    "Année": results['years'],
                    "Amortissement": results['depreciation'],
                    "Intérêts": results['interest_paid'],
                    "Principal": results['principal_paid'],
                    "Service de la Dette Total": results['debt_service']
                })
                
                # Graphique
                fig_debt = go.Figure()
                
                # Barres empilées pour le service de la dette
                fig_debt.add_trace(go.Bar(
                    x=df_debt['Année'],
                    y=df_debt['Intérêts'],
                    name='Intérêts',
                    marker_color='#FF9800'
                ))
                
                fig_debt.add_trace(go.Bar(
                    x=df_debt['Année'],
                    y=df_debt['Principal'],
                    name='Principal',
                    marker_color='#2196F3'
                ))
                
                # Ligne pour l'amortissement
                fig_debt.add_trace(go.Scatter(
                    x=df_debt['Année'],
                    y=df_debt['Amortissement'],
                    name='Amortissement',
                    mode='lines+markers',
                    line=dict(color='#4CAF50', width=2, dash='dash'),
                    marker=dict(size=8)
                ))
                
                fig_debt.update_layout(
                    title="Comparaison Amortissement et Service de la Dette",
                    xaxis_title="Année",
                    yaxis_title="Montant (€)",
                    barmode='stack',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig_debt, use_container_width=True, key=f"{key_prefix}debt_chart_{scenario_name}_{unique_id}")

            # Afficher un tableau de résumé des indicateurs clés
            with st.expander("Résumé des indicateurs clés"):
                # Créer un DataFrame pour les indicateurs clés
                df_summary = pd.DataFrame({
                    "Indicateur": [
                        "ROI", "TRI (IRR)", "VAN (NPV)", "Période de récupération", 
                        "DSCR moyen", "CAPEX", "Fonds propres", "Dette", 
                        "Taux d'autoconsommation", "Taux d'autoproduction"
                    ],
                    "Valeur": [
                        f"{results['roi']*100:.2f}%" if results['roi'] is not None else "N/A",
                        f"{results['irr']*100:.2f}%" if results['irr'] is not None else "N/A",
                        f"{results['npv']:,.2f} €",
                        f"{results['payback_period']:.2f} ans" if results['payback_period'] is not None and results['payback_period'] != float('inf') else "N/A",
                        f"{results['avg_dscr']:.2f}" if results['avg_dscr'] is not None else "N/A",
                        f"{results['capex']:,.2f} €",
                        f"{results['equity_amount']:,.2f} €",
                        f"{results['debt_amount']:,.2f} €",
                        f"{results['autoconsumption_rate']*100:.2f}%",
                        f"{results['autoproduction_rate']*100:.2f}%"
                    ]
                })
                
                st.dataframe(df_summary, use_container_width=True, key=f"{key_prefix}summary_{scenario_name}_{unique_id}")
        

    def display_optimization_results(self, results):
        """
        Affiche les résultats de l'optimisation
        
        Args:
            results: Dictionnaire contenant les résultats de l'optimisation
        """
        st.markdown("### Résultats de l'Optimisation du Prix de Revente")
        
        # Extraire les données
        scenario_name = results['scenario_name']
        prix_optimal = results['prix_optimal']
        indicateurs = results['indicateurs_optimaux']
        
        # Afficher le prix optimal
        st.markdown(f"<div style='background-color: #e8f5e9; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>Le prix de revente optimal pour le scénario <b>{scenario_name}</b> est de <b>{prix_optimal:.4f} €/kWh</b></div>", unsafe_allow_html=True)
        
        # Afficher les indicateurs financiers clés
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("ROI", f"{indicateurs['roi']*100:.2f}%" if indicateurs['roi'] is not None else "N/A")
            if 'scores' in indicateurs:
                st.markdown(f"Score: {indicateurs['scores']['roi']:.2f}")
        
        with col2:
            st.metric("TRI (IRR)", f"{indicateurs['irr']*100:.2f}%" if indicateurs['irr'] is not None else "Non calculable")
            if 'scores' in indicateurs:
                st.markdown(f"Score: {indicateurs['scores']['irr']:.2f}")
        
        with col3:
            payback_label = f"{indicateurs['payback_period']:.2f} ans" if indicateurs['payback_period'] is not None and indicateurs['payback_period'] != float('inf') else "Jamais"
            st.metric("Période de Récupération", payback_label)
            if 'scores' in indicateurs:
                st.markdown(f"Score: {indicateurs['scores']['payback']:.2f}")
        
        with col4:
            st.metric("DSCR moyen", f"{indicateurs['avg_dscr']:.2f}" if indicateurs['avg_dscr'] is not None else "N/A")
            if 'scores' in indicateurs:
                st.markdown(f"Score: {indicateurs['scores']['dscr']:.2f}")
        
        # Afficher le score global si disponible
        if 'scores' in indicateurs and 'score_global' in indicateurs['scores']:
            st.markdown(f"<div style='background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>Score global d'optimisation: <b>{indicateurs['scores']['score_global']:.4f}</b></div>", unsafe_allow_html=True)
        
        # Afficher un graphique des résultats en fonction du prix
        st.markdown("### Indicateurs Financiers en Fonction du Prix de Revente")
        
        # Créer un DataFrame avec les résultats pour chaque prix
        data = []
        for prix, res in results['tous_resultats'].items():
            if res is not None:
                data.append({
                    "Prix (€/kWh)": prix,
                    "ROI (%)": res['roi'] * 100 if res['roi'] is not None else 0,
                    "TRI (%)": res['irr'] * 100 if res['irr'] is not None else 0,
                    "VAN (€)": res['npv'],
                    "Période de Récupération (ans)": res['payback_period'] if res['payback_period'] is not None and res['payback_period'] != float('inf') else 30,
                    "DSCR moyen": res['avg_dscr'] if res['avg_dscr'] is not None else 0
                })
        
        df_results = pd.DataFrame(data)
        
        # Graphique ROI et TRI en fonction du prix
        fig1 = go.Figure()
        
        fig1.add_trace(go.Scatter(
            x=df_results["Prix (€/kWh)"],
            y=df_results["ROI (%)"],
            name='ROI (%)',
            mode='lines+markers',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))
        
        fig1.add_trace(go.Scatter(
            x=df_results["Prix (€/kWh)"],
            y=df_results["TRI (%)"],
            name='TRI (%)',
            mode='lines+markers',
            line=dict(color='green', width=2),
            marker=dict(size=6)
        ))
        
        # Ajouter une ligne verticale pour le prix optimal
        fig1.add_shape(
            type="line",
            x0=prix_optimal,
            y0=0,
            x1=prix_optimal,
            y1=df_results[["ROI (%)", "TRI (%)"]].max().max() * 1.1,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            )
        )
        
        # Ajouter une annotation pour le prix optimal
        fig1.add_annotation(
            x=prix_optimal,
            y=df_results[["ROI (%)", "TRI (%)"]].max().max() * 1.05,
            text=f"Prix optimal: {prix_optimal:.4f} €/kWh",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="red",
            font=dict(
                size=12,
                color="red"
            ),
            align="center"
        )
        
        fig1.update_layout(
            title="ROI et TRI en fonction du Prix de Revente",
            xaxis_title="Prix de Revente (€/kWh)",
            yaxis_title="Pourcentage (%)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig1, use_container_width=True, key=f"optim_roi_tri_{scenario_name}")
        
        # Graphique VAN et Période de Récupération en fonction du prix
        fig2 = go.Figure()
        
        # Première courbe: VAN
        fig2.add_trace(go.Scatter(
            x=df_results["Prix (€/kWh)"],
            y=df_results["VAN (€)"],
            name='VAN (€)',
            mode='lines+markers',
            line=dict(color='purple', width=2),
            marker=dict(size=6),
            yaxis="y"
        ))
        
        # Seconde courbe: Période de Récupération
        fig2.add_trace(go.Scatter(
            x=df_results["Prix (€/kWh)"],
            y=df_results["Période de Récupération (ans)"],
            name='Période de Récupération (ans)',
            mode='lines+markers',
            line=dict(color='orange', width=2),
            marker=dict(size=6),
            yaxis="y2"
        ))
        
        # Ajouter une ligne verticale pour le prix optimal
        fig2.add_shape(
            type="line",
            x0=prix_optimal,
            y0=0,
            x1=prix_optimal,
            y1=df_results["VAN (€)"].max() * 1.1,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            )
        )
        
        fig2.update_layout(
            title="VAN et Période de Récupération en fonction du Prix de Revente",
            xaxis_title="Prix de Revente (€/kWh)",
            yaxis=dict(
                title="VAN (€)",
                side="left"
            ),
            yaxis2=dict(
                title="Période de Récupération (ans)",
                side="right",
                overlaying="y"
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig2, use_container_width=True, key=f"optim_van_payback_{scenario_name}")
        
        # Graphique DSCR en fonction du prix
        fig3 = go.Figure()
        
        fig3.add_trace(go.Scatter(
            x=df_results["Prix (€/kWh)"],
            y=df_results["DSCR moyen"],
            name='DSCR moyen',
            mode='lines+markers',
            line=dict(color='red', width=2),
            marker=dict(size=6)
        ))
        
        # Ajouter une ligne horizontale pour le DSCR cible
        target_dscr = st.session_state.config.get('target_dscr', 1.2)
        fig3.add_shape(
            type="line",
            x0=df_results["Prix (€/kWh)"].min(),
            y0=target_dscr,
            x1=df_results["Prix (€/kWh)"].max(),
            y1=target_dscr,
            line=dict(
                color="green",
                width=2,
                dash="dash",
            )
        )
        
        # Ajouter une ligne verticale pour le prix optimal
        fig3.add_shape(
            type="line",
            x0=prix_optimal,
            y0=0,
            x1=prix_optimal,
            y1=df_results["DSCR moyen"].max() * 1.1,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            )
        )
        
        fig3.update_layout(
            title="DSCR moyen en fonction du Prix de Revente",
            xaxis_title="Prix de Revente (€/kWh)",
            yaxis_title="DSCR moyen"
        )
        
        st.plotly_chart(fig3, use_container_width=True, key=f"optim_dscr_{scenario_name}")
        
        # Afficher le tableau des résultats
        with st.expander("Tableau détaillé des résultats"):
            st.dataframe(df_results.sort_values("Prix (€/kWh)"), use_container_width=True)
        
        # Afficher une analyse comparative avec le tarif EDF
        st.markdown("### Analyse Comparative avec le Tarif EDF")
        
        # Récupérer le tarif EDF
        tarif_edf = st.session_state.config.get('tarif_edf_reference', 0.21)
        
        # Calculer l'écart avec le tarif EDF
        ecart_edf = tarif_edf - prix_optimal
        ecart_pct = (ecart_edf / tarif_edf) * 100
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Tarif EDF de référence", f"{tarif_edf:.4f} €/kWh")
            st.metric("Prix de revente optimal", f"{prix_optimal:.4f} €/kWh")
        
        with col2:
            st.metric("Écart absolu", f"{ecart_edf:.4f} €/kWh")
            st.metric("Écart relatif", f"{ecart_pct:.2f}%")
        
        if prix_optimal < tarif_edf:
            st.success(f"✅ Le prix de revente optimal ({prix_optimal:.4f} €/kWh) est compétitif par rapport au tarif EDF ({tarif_edf:.4f} €/kWh).")
            st.markdown(f"Avantage concurrentiel: **{ecart_pct:.2f}%** de moins que le tarif EDF.")
        else:
            st.error(f"❌ Le prix de revente optimal ({prix_optimal:.4f} €/kWh) n'est pas compétitif par rapport au tarif EDF ({tarif_edf:.4f} €/kWh).")
            st.markdown(f"Désavantage concurrentiel: **{-ecart_pct:.2f}%** de plus que le tarif EDF.")

    def display_monte_carlo_results(self, results):
        """
        Affiche les résultats de la simulation Monte Carlo
        
        Args:
            results: Dictionnaire contenant les résultats de la simulation
        """
        st.markdown("### Résultats de la Simulation Monte Carlo")
        
        # Extraire les données
        scenario_name = results['scenario_name']
        prix_revente = results['prix_revente']
        n_iterations = results['n_iterations']
        ecart_type_production = results['ecart_type_production']
        ecart_type_consommation = results['ecart_type_consommation']
        
        # Statistiques
        stats = results['statistics']
        probas = results['probabilities']
        
        # Afficher les paramètres de la simulation
        st.markdown(f"<div style='background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>Simulation pour le scénario <b>{scenario_name}</b> avec un prix de revente de <b>{prix_revente:.4f} €/kWh</b></div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Nombre d'itérations", f"{n_iterations}")
        
        with col2:
            st.metric("Écart-type Production", f"{ecart_type_production*100:.1f}%")
        
        with col3:
            st.metric("Écart-type Consommation", f"{ecart_type_consommation*100:.1f}%")
        
        # Afficher les probabilités de succès
        st.markdown("### Probabilités de Succès")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("ROI > 5%", f"{probas['roi']*100:.1f}%")
        
        with col2:
            st.metric("TRI > 4%", f"{probas['irr']*100:.1f}%")
        
        with col3:
            st.metric("Récupération < 15 ans", f"{probas['payback']*100:.1f}%")
        
        with col4:
            st.metric(f"DSCR > {st.session_state.config.get('target_dscr', 1.2)}", f"{probas['dscr']*100:.1f}%")
        
        # Afficher la probabilité de succès global
        st.markdown(f"<div style='background-color: #e8f5e9; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>Probabilité de succès global (tous critères respectés): <b>{probas['global']*100:.1f}%</b></div>", unsafe_allow_html=True)
        
        # Afficher les distributions des indicateurs
        st.markdown("### Distributions des Indicateurs Financiers")
        
        # Créer des onglets pour les différentes distributions
        tab1, tab2, tab3, tab4 = st.tabs(["ROI", "TRI", "VAN et Période de Récupération", "DSCR"])
        
        with tab1:
            # Distribution du ROI
            fig = go.Figure()
            
            # Histogramme
            fig.add_trace(go.Histogram(
                x=[r*100 for r in results['roi_values']],  # Convertir en pourcentage
                name='Distribution',
                opacity=0.7,
                marker_color='blue',
                nbinsx=30
            ))
            
            # Ligne verticale pour la moyenne
            fig.add_shape(
                type="line",
                x0=stats['roi']['mean'] * 100,
                y0=0,
                x1=stats['roi']['mean'] * 100,
                y1=n_iterations / 10,  # Approximation de la hauteur
                line=dict(
                    color="red",
                    width=2,
                    dash="dash",
                )
            )
            
            # Ligne verticale pour la valeur minimale acceptable
            fig.add_shape(
                type="line",
                x0=5,  # 5%
                y0=0,
                x1=5,
                y1=n_iterations / 10,
                line=dict(
                    color="green",
                    width=2,
                    dash="dash",
                )
            )
            
            # Annotations
            fig.add_annotation(
                x=stats['roi']['mean'] * 100,
                y=n_iterations / 10,
                text=f"Moyenne: {stats['roi']['mean']*100:.2f}%",
                showarrow=True,
                arrowhead=2,
                arrowcolor="red",
                font=dict(color="red")
            )
            
            fig.add_annotation(
                x=5,
                y=n_iterations / 20,
                text="Minimum: 5%",
                showarrow=True,
                arrowhead=2,
                arrowcolor="green",
                font=dict(color="green")
            )
            
            fig.update_layout(
                title="Distribution du ROI",
                xaxis_title="ROI (%)",
                yaxis_title="Fréquence",
                bargap=0.05
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistiques du ROI
            st.markdown("#### Statistiques du ROI")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Moyenne", f"{stats['roi']['mean']*100:.2f}%")
                st.metric("Écart-type", f"{stats['roi']['std']*100:.2f}%")
            
            with col2:
                st.metric("Médiane (P50)", f"{stats['roi']['percentiles'][2]*100:.2f}%")
                st.metric("Probabilité ROI > 5%", f"{probas['roi']*100:.1f}%")
            
            with col3:
                st.metric("P05", f"{stats['roi']['percentiles'][0]*100:.2f}%")
                st.metric("P95", f"{stats['roi']['percentiles'][4]*100:.2f}%")
        
        with tab2:
            # Distribution du TRI
            fig = go.Figure()
            
            # Histogramme
            fig.add_trace(go.Histogram(
                x=[r*100 for r in results['irr_values']],  # Convertir en pourcentage
                name='Distribution',
                opacity=0.7,
                marker_color='green',
                nbinsx=30
            ))
            
            # Ligne verticale pour la moyenne
            fig.add_shape(
                type="line",
                x0=stats['irr']['mean'] * 100,
                y0=0,
                x1=stats['irr']['mean'] * 100,
                y1=n_iterations / 10,
                line=dict(
                    color="red",
                    width=2,
                    dash="dash",
                )
            )
            
            # Ligne verticale pour la valeur minimale acceptable
            fig.add_shape(
                type="line",
                x0=4,  # 4%
                y0=0,
                x1=4,
                y1=n_iterations / 10,
                line=dict(
                    color="green",
                    width=2,
                    dash="dash",
                )
            )
            
            # Annotations
            fig.add_annotation(
                x=stats['irr']['mean'] * 100,
                y=n_iterations / 10,
                text=f"Moyenne: {stats['irr']['mean']*100:.2f}%",
                showarrow=True,
                arrowhead=2,
                arrowcolor="red",
                font=dict(color="red")
            )
            
            fig.add_annotation(
                x=4,
                y=n_iterations / 20,
                text="Minimum: 4%",
                showarrow=True,
                arrowhead=2,
                arrowcolor="green",
                font=dict(color="green")
            )
            
            fig.update_layout(
                title="Distribution du TRI (IRR)",
                xaxis_title="TRI (%)",
                yaxis_title="Fréquence",
                bargap=0.05
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistiques du TRI
            st.markdown("#### Statistiques du TRI")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Moyenne", f"{stats['irr']['mean']*100:.2f}%")
                st.metric("Écart-type", f"{stats['irr']['std']*100:.2f}%")
            
            with col2:
                st.metric("Médiane (P50)", f"{stats['irr']['percentiles'][2]*100:.2f}%")
                st.metric("Probabilité TRI > 4%", f"{probas['irr']*100:.1f}%")
            
            with col3:
                st.metric("P05", f"{stats['irr']['percentiles'][0]*100:.2f}%")
                st.metric("P95", f"{stats['irr']['percentiles'][4]*100:.2f}%")
        
        with tab3:
            # Onglet VAN et Période de Récupération
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribution de la VAN
                fig = go.Figure()
                
                # Histogramme
                fig.add_trace(go.Histogram(
                    x=results['npv_values'],
                    name='Distribution',
                    opacity=0.7,
                    marker_color='purple',
                    nbinsx=30
                ))
                
                # Ligne verticale pour la moyenne
                fig.add_shape(
                    type="line",
                    x0=stats['npv']['mean'],
                    y0=0,
                    x1=stats['npv']['mean'],
                    y1=n_iterations / 10,
                    line=dict(
                        color="red",
                        width=2,
                        dash="dash",
                    )
                )
                
                # Ligne verticale pour la valeur minimale acceptable (VAN > 0)
                fig.add_shape(
                    type="line",
                    x0=0,
                    y0=0,
                    x1=0,
                    y1=n_iterations / 10,
                    line=dict(
                        color="green",
                        width=2,
                        dash="dash",
                    )
                )
                
                # Annotations
                fig.add_annotation(
                    x=stats['npv']['mean'],
                    y=n_iterations / 10,
                    text=f"Moyenne: {stats['npv']['mean']:,.2f} €",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="red",
                    font=dict(color="red")
                )
                
                fig.update_layout(
                    title="Distribution de la VAN",
                    xaxis_title="VAN (€)",
                    yaxis_title="Fréquence",
                    bargap=0.05
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistiques de la VAN
                st.markdown("#### Statistiques de la VAN")
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.metric("Moyenne", f"{stats['npv']['mean']:,.2f} €")
                    st.metric("Médiane (P50)", f"{stats['npv']['percentiles'][2]:,.2f} €")
                
                with col_b:
                    st.metric("Écart-type", f"{stats['npv']['std']:,.2f} €")
                    st.metric("Probabilité VAN > 0", f"{np.mean(np.array(results['npv_values']) > 0)*100:.1f}%")
            
            with col2:
                # Distribution de la Période de Récupération
                fig = go.Figure()
                
                # Histogramme
                fig.add_trace(go.Histogram(
                    x=results['payback_values'],
                    name='Distribution',
                    opacity=0.7,
                    marker_color='orange',
                    nbinsx=30
                ))
                
                # Ligne verticale pour la moyenne
                fig.add_shape(
                    type="line",
                    x0=stats['payback']['mean'],
                    y0=0,
                    x1=stats['payback']['mean'],
                    y1=n_iterations / 10,
                    line=dict(
                        color="red",
                        width=2,
                        dash="dash",
                    )
                )
                
                # Ligne verticale pour la valeur maximale acceptable
                fig.add_shape(
                    type="line",
                    x0=15,  # 15 ans
                    y0=0,
                    x1=15,
                    y1=n_iterations / 10,
                    line=dict(
                        color="green",
                        width=2,
                        dash="dash",
                    )
                )
                
                # Annotations
                fig.add_annotation(
                    x=stats['payback']['mean'],
                    y=n_iterations / 10,
                    text=f"Moyenne: {stats['payback']['mean']:.2f} ans",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="red",
                    font=dict(color="red")
                )
                
                fig.add_annotation(
                    x=15,
                    y=n_iterations / 20,
                    text="Maximum: 15 ans",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="green",
                    font=dict(color="green")
                )
                
                fig.update_layout(
                    title="Distribution de la Période de Récupération",
                    xaxis_title="Période de Récupération (ans)",
                    yaxis_title="Fréquence",
                    bargap=0.05
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistiques de la Période de Récupération
                st.markdown("#### Statistiques de la Période de Récupération")
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.metric("Moyenne", f"{stats['payback']['mean']:.2f} ans")
                    st.metric("Médiane (P50)", f"{stats['payback']['percentiles'][2]:.2f} ans")
                
                with col_b:
                    st.metric("Écart-type", f"{stats['payback']['std']:.2f} ans")
                    st.metric("Probabilité < 15 ans", f"{probas['payback']*100:.1f}%")
        
        with tab4:
            # Distribution du DSCR
            fig = go.Figure()
            
            # Histogramme
            fig.add_trace(go.Histogram(
                x=results['dscr_values'],
                name='Distribution',
                opacity=0.7,
                marker_color='red',
                nbinsx=30
            ))
            
            # Ligne verticale pour la moyenne
            fig.add_shape(
                type="line",
                x0=stats['dscr']['mean'],
                y0=0,
                x1=stats['dscr']['mean'],
                y1=n_iterations / 10,
                line=dict(
                    color="red",
                    width=2,
                    dash="dash",
                )
            )
            
            # Ligne verticale pour la valeur minimale acceptable
            target_dscr = st.session_state.config.get('target_dscr', 1.2)
            fig.add_shape(
                type="line",
                x0=target_dscr,
                y0=0,
                x1=target_dscr,
                y1=n_iterations / 10,
                line=dict(
                    color="green",
                    width=2,
                    dash="dash",
                )
            )
            
            # Annotations
            fig.add_annotation(
                x=stats['dscr']['mean'],
                y=n_iterations / 10,
                text=f"Moyenne: {stats['dscr']['mean']:.2f}",
                showarrow=True,
                arrowhead=2,
                arrowcolor="red",
                font=dict(color="red")
            )
            
            fig.add_annotation(
                x=target_dscr,
                y=n_iterations / 20,
                text=f"Minimum: {target_dscr}",
                showarrow=True,
                arrowhead=2,
                arrowcolor="green",
                font=dict(color="green")
            )
            
            fig.update_layout(
                title="Distribution du DSCR moyen",
                xaxis_title="DSCR moyen",
                yaxis_title="Fréquence",
                bargap=0.05
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistiques du DSCR
            st.markdown("#### Statistiques du DSCR")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Moyenne", f"{stats['dscr']['mean']:.2f}")
                st.metric("Écart-type", f"{stats['dscr']['std']:.2f}")
            
            with col2:
                st.metric("Médiane (P50)", f"{stats['dscr']['percentiles'][2]:.2f}")
                st.metric(f"Probabilité DSCR > {target_dscr}", f"{probas['dscr']*100:.1f}%")
            
            with col3:
                st.metric("P05", f"{stats['dscr']['percentiles'][0]:.2f}")
                st.metric("P95", f"{stats['dscr']['percentiles'][4]:.2f}")
        
        # Interprétation des résultats
        st.markdown("### Interprétation des Résultats")
        
        if probas['global'] >= 0.9:
            st.success(f"✅ Le projet est très robuste avec une probabilité de succès global de {probas['global']*100:.1f}%. Le prix de revente de {prix_revente:.4f} €/kWh est recommandé.")
        elif probas['global'] >= 0.75:
            st.info(f"ℹ️ Le projet est robuste avec une probabilité de succès global de {probas['global']*100:.1f}%. Le prix de revente de {prix_revente:.4f} €/kWh est acceptable.")
        elif probas['global'] >= 0.5:
            st.warning(f"⚠️ Le projet présente une robustesse modérée avec une probabilité de succès global de {probas['global']*100:.1f}%. Le prix de revente de {prix_revente:.4f} €/kWh est risqué.")
        else:
            st.error(f"❌ Le projet n'est pas robuste avec une probabilité de succès global de seulement {probas['global']*100:.1f}%. Le prix de revente de {prix_revente:.4f} €/kWh est insuffisant.")
        
        # Recommandations
        st.markdown("#### Recommandations")
        
        if probas['roi'] < 0.8:
            st.markdown("- ⚠️ Le ROI présente un risque significatif. Envisagez d'augmenter le prix de revente ou de réduire les coûts.")
        
        if probas['irr'] < 0.8:
            st.markdown("- ⚠️ Le TRI présente un risque significatif. Envisagez d'améliorer la structure de financement.")
        
        if probas['payback'] < 0.8:
            st.markdown("- ⚠️ La période de récupération présente un risque significatif. Le retour sur investissement pourrait prendre plus de temps que prévu.")
        
        if probas['dscr'] < 0.8:
            st.markdown("- ⚠️ Le DSCR présente un risque significatif. Le service de la dette pourrait être compromis en cas de performance inférieure aux attentes.")
        
        if all(p >= 0.8 for p in [probas['roi'], probas['irr'], probas['payback'], probas['dscr']]):
            st.markdown("- ✅ Tous les indicateurs présentent une bonne robustesse. Le projet semble viable avec le prix de revente actuel.")

    def display_scenarios_comparison(self, results):
        """
        Affiche la comparaison des scénarios
        
        Args:
            results: Dictionnaire contenant les résultats pour chaque scénario
        """
        st.markdown("### Comparaison des Scénarios")
        
        # Créer un DataFrame pour comparer les indicateurs clés
        comparison_data = []
        
        for scenario_name, scenario_results in results.items():
            if scenario_results is None:
                continue
                
            comparison_data.append({
                "Scénario": scenario_name,
                "ROI (%)": scenario_results['roi'] * 100 if scenario_results['roi'] is not None else None,
                "TRI (%)": scenario_results['irr'] * 100 if scenario_results['irr'] is not None else None,
                "VAN (€)": scenario_results['npv'],
                "Période de Récupération (ans)": scenario_results['payback_period'] if scenario_results['payback_period'] is not None and scenario_results['payback_period'] != float('inf') else None,
                "DSCR moyen": scenario_results['avg_dscr'] if scenario_results['avg_dscr'] is not None else None,
                "Taux d'Autoconsommation (%)": scenario_results['autoconsumption_rate'] * 100,
                "Production Annuelle (kWh)": scenario_results['annual_production'][-1],
                "Surplus Annuel (kWh)": scenario_results['annual_surplus'][-1],
                "WACC (%)": scenario_results['wacc'] * 100 if scenario_results.get('wacc') is not None else None
            })
        
        df_comparison = pd.DataFrame(comparison_data)
        
        # Afficher le tableau de comparaison
        # Essayer d'utiliser le style.highlight_max/min s'il est disponible
        try:
            styled_df = df_comparison.style.highlight_max(subset=['ROI (%)', 'TRI (%)', 'VAN (€)', 'DSCR moyen']).highlight_min(subset=['Période de Récupération (ans)', 'WACC (%)'])
            st.dataframe(styled_df, use_container_width=True)
        except:
            # Fallback si style.highlight n'est pas disponible
            st.dataframe(df_comparison, use_container_width=True)
        
        # Créer des graphiques de comparaison
        st.markdown("### Graphiques Comparatifs")
        
        # Comparaison des ROI, TRI, VAN
        fig1 = go.Figure()
        
        fig1.add_trace(go.Bar(
            x=[r["Scénario"] for r in comparison_data],
            y=[r["ROI (%)"] if r["ROI (%)"] is not None else 0 for r in comparison_data],
            name='ROI (%)',
            marker_color='blue'
        ))
        
        fig1.add_trace(go.Bar(
            x=[r["Scénario"] for r in comparison_data],
            y=[r["TRI (%)"] if r["TRI (%)"] is not None else 0 for r in comparison_data],
            name='TRI (%)',
            marker_color='green'
        ))
        
        fig1.update_layout(
            title="Comparaison des ROI et TRI par Scénario",
            xaxis_title="Scénario",
            yaxis_title="Pourcentage (%)",
            barmode='group',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Créer une clé unique basée sur les noms des scénarios
        scenario_key = "_".join(sorted(results.keys()))
        
        # Afficher le graphique
        st.plotly_chart(fig1, use_container_width=True, key=f"scenarios_roi_tri_chart_{scenario_key}")
        
        # Comparaison des VAN
        fig2 = go.Figure()
        
        fig2.add_trace(go.Bar(
            x=[r["Scénario"] for r in comparison_data],
            y=[r["VAN (€)"] for r in comparison_data],
            name='VAN (€)',
            marker_color='purple'
        ))
        
        fig2.update_layout(
            title="Comparaison des VAN par Scénario",
            xaxis_title="Scénario",
            yaxis_title="VAN (€)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Afficher le graphique
        st.plotly_chart(fig2, use_container_width=True, key=f"scenarios_van_chart_{scenario_key}")
        
        # Comparaison des flux cumulés
        fig3 = go.Figure()
        
        for scenario_name, scenario_results in results.items():
            if scenario_results is None:
                continue
                
            fig3.add_trace(go.Scatter(
                x=scenario_results['years'],
                y=scenario_results['cumulative_cash_flow'],
                name=scenario_name,
                mode='lines+markers'
            ))
        
        # Ajouter une ligne horizontale à zéro
        fig3.add_shape(
            type="line",
            x0=min([min(r['years']) for r in results.values() if r is not None]),
            y0=0,
            x1=max([max(r['years']) for r in results.values() if r is not None]),
            y1=0,
            line=dict(
                color="black",
                width=2,
                dash="dash",
            )
        )
        
        fig3.update_layout(
            title="Comparaison des Flux Cumulés par Scénario",
            xaxis_title="Année",
            yaxis_title="Flux Cumulé (€)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Afficher le graphique
        st.plotly_chart(fig3, use_container_width=True, key=f"scenarios_cash_flow_chart_{scenario_key}")

    def display_sensitivity_analysis(self, results, parameter, unit):
        """
        Affiche les résultats de l'analyse de sensibilité
        
        Args:
            results: Dictionnaire contenant les résultats pour chaque valeur
            parameter: Paramètre qui a été varié
            unit: Unité du paramètre
        """
        st.markdown("### Résultats de l'Analyse de Sensibilité")
        
        # Extraire les valeurs testées et les résultats correspondants
        values = list(results.keys())
        
        # Créer un DataFrame pour faciliter la création de graphiques
        df_sensitivity = pd.DataFrame({
            "Valeur": values,
            "ROI (%)": [results[v]['roi'] * 100 if results[v] is not None and results[v]['roi'] is not None else 0 for v in values],
            "TRI (%)": [results[v]['irr'] * 100 if results[v] is not None and results[v]['irr'] is not None else 0 for v in values],
            "VAN (€)": [results[v]['npv'] if results[v] is not None else 0 for v in values],
            "Période de Récupération (ans)": [results[v]['payback_period'] if results[v] is not None and results[v]['payback_period'] is not None and results[v]['payback_period'] != float('inf') else 30 for v in values],
            "DSCR moyen": [results[v]['avg_dscr'] if results[v] is not None and results[v]['avg_dscr'] is not None and results[v]['avg_dscr'] != float('inf') else 5 for v in values],
            "WACC (%)": [results[v]['wacc'] * 100 if results[v] is not None and results[v].get('wacc') is not None else 0 for v in values]
        })
        
        # Afficher le tableau des résultats
        st.dataframe(df_sensitivity.sort_values("Valeur"), use_container_width=True)
        
        # Créer des graphiques de sensibilité
        st.markdown("### Graphiques de Sensibilité")
        
        # Créer une clé unique pour les graphiques basée sur le paramètre et ses valeurs
        analysis_key = f"{parameter}_{min(values)}_{max(values)}"
        
        # Graphique ROI et TRI en fonction du paramètre
        fig1 = go.Figure()
        
        fig1.add_trace(go.Scatter(
            x=df_sensitivity["Valeur"],
            y=df_sensitivity["ROI (%)"],
            name='ROI (%)',
            mode='lines+markers',
            line=dict(color='blue', width=3),
            marker=dict(size=8)
        ))
        
        fig1.add_trace(go.Scatter(
            x=df_sensitivity["Valeur"],
            y=df_sensitivity["TRI (%)"],
            name='TRI (%)',
            mode='lines+markers',
            line=dict(color='green', width=3),
            marker=dict(size=8)
        ))
        
        fig1.update_layout(
            title=f"Sensibilité des ROI et TRI au {parameter} ({unit})",
            xaxis_title=f"{parameter} ({unit})",
            yaxis_title="Pourcentage (%)"
        )
        
        st.plotly_chart(fig1)
        
    def show_ui(self):
        """Affiche l'interface utilisateur principale pour l'analyse et l'optimisation."""
        st.markdown("<h2 class='sub-header'>Analyse Économique et Optimisation</h2>", unsafe_allow_html=True)

        # Vérifier si les données sont importées
        if not st.session_state.get('data_imported', False):
            st.warning("Veuillez d'abord importer des données via l'onglet 'Importation Données'.")
            return

        # Sélection du scénario de base pour toutes les analyses de cet onglet
        # S'assurer que st.session_state.scenarios existe et n'est pas vide
        if not st.session_state.get('scenarios'):
            st.error("Aucun scénario défini. Veuillez vérifier la configuration.")
            return
            
        available_scenarios = list(st.session_state.scenarios.keys())
        if not available_scenarios:
            st.warning("Aucun scénario disponible. Veuillez en définir un dans la configuration.")
            return

        scenario_name = st.selectbox(
            "Choisir le Scénario à Analyser/Optimiser:",
            options=available_scenarios,
            index=0,
            key="analysis_main_scenario"
        )
        
        st.markdown("---")

        # Onglets internes pour les différentes actions
        tab_analyse, tab_objectif, tab_optim_score, tab_montecarlo, tab_compare, tab_sensi = st.tabs([
            "📈 Analyse Détaillée", 
            "🎯 Prix/Objectif", 
            "🏆 Meilleur Prix (Score)", 
            "🎲 Monte Carlo", 
            "🆚 Comparaison Scénarios", 
            "🔬 Sensibilité"
        ])

        # Onglet 1: Analyse Détaillée (anciennement Analyse de Base)
        with tab_analyse:
            st.markdown("#### Analyse Financière Détaillée du Scénario")
            st.info(f"Affichage des indicateurs et flux pour le scénario **{scenario_name}** avec le prix de vente initial défini dans la configuration.")
            
            prix_initial = st.session_state.config.get('prix_vente_initial', 0.17) # Lire depuis config
            
            # Bouton pour (re)lancer le calcul de base
            if st.button(f"Lancer/Relancer l'Analyse de Base ({prix_initial:.3f} €/kWh)", key="run_base_analysis"):
                with st.spinner(f"Calcul pour {scenario_name}..."):
                    results_base = self.calculate_financial_indicators(scenario_name) # Utilise prix_initial par défaut
                    if results_base:
                        st.session_state.economic_results[scenario_name] = results_base
                        st.success("Analyse terminée.")
                        st.session_state.analysis_run = True # Mettre à jour le flag
                    else:
                        st.error("Le calcul de l'analyse de base a échoué.")
            
            # Afficher les résultats s'ils existent pour ce scénario
            if scenario_name in st.session_state.economic_results:
                st.markdown(f"**Résultats pour le scénario '{scenario_name}' (Prix: {st.session_state.economic_results[scenario_name]['prix_revente']:.4f} €/kWh)**")
                
                # Appeler la méthode d'affichage des résultats financiers
                self.display_financial_results(st.session_state.economic_results[scenario_name], key_prefix=f"base_{scenario_name}_")
                
                # La section d'export Excel a été supprimée.

            else:
                st.info("Lancez l'analyse de base pour voir les résultats détaillés.")

        # Onglet 2: Prix pour Objectif (anciennement Simulation Prix Revente)
        with tab_objectif:
            st.markdown("#### Trouver le Prix de Vente pour un Objectif Spécifique")
            st.info(f"Calcul du prix de vente nécessaire pour atteindre un TRI ou une VAN cible pour le scénario **{scenario_name}**.")

            target_type = st.radio("Objectif de simulation", ["TRI Cible", "VAN Cible"], key="target_type_goal")
            
            if target_type == "TRI Cible":
                target_irr = st.number_input("TRI Cible (%)", min_value=0.0, max_value=30.0, value=8.0, step=0.5, key="target_irr_value_goal")
                target_npv = None
            else:
                target_irr = None
                target_npv = st.number_input("VAN Cible (€)", min_value=-1000000.0, max_value=10000000.0, value=0.0, step=1000.0, key="target_npv_value_goal")

            if st.button("Trouver le prix pour l'objectif", key="calc_goal_seek"):
                with st.spinner("Recherche du prix en cours..."):
                    # Appel à simulate_selling_price
                    results_goal = self.simulate_selling_price(scenario_name, target_irr=target_irr, target_npv=target_npv)
                    
                    if results_goal:
                        st.success(f"Prix trouvé pour atteindre l'objectif !")
                        # Afficher les résultats pour ce prix trouvé
                        self.display_financial_results(results_goal, key_prefix=f"goal_{scenario_name}_")
                        # Afficher aussi le message de rentabilité
                        self.assess_profitability(results_goal)
                    else:
                        st.error("Impossible de trouver un prix pour atteindre cet objectif (non convergence ou erreur).")

        # Onglet 3: Meilleur Prix (Score) (anciennement Optimisation Prix)
        with tab_optim_score:
            st.markdown("#### Trouver le Meilleur Prix de Vente (Basé sur Score Global)")
            st.info(f"Recherche du prix de vente (entre Min et Max configurés) qui maximise un score combinant plusieurs indicateurs financiers pour le scénario **{scenario_name}**.")
            
            with st.expander("Options de la recherche par score"):
                col1, col2 = st.columns(2)
                with col1:
                    prix_min = st.number_input("Prix minimum à tester (€/kWh)", min_value=0.01, max_value=0.5, value=st.session_state.config.get('prix_min_revente', 0.15), step=0.01, key="score_opt_min")
                with col2:
                    prix_max = st.number_input("Prix maximum à tester (€/kWh)", min_value=prix_min, max_value=0.5, value=st.session_state.config.get('prix_max_revente', 0.21), step=0.01, key="score_opt_max")
                pas = st.number_input("Pas de test (€/kWh)", min_value=0.001, max_value=0.05, value=st.session_state.config.get('pas_optimisation', 0.01), step=0.001, key="score_opt_step", format="%.3f")
                
                # Mise à jour temporaire pour cette exécution si l'utilisateur modifie ici
                st.session_state.config['prix_min_revente'] = prix_min
                st.session_state.config['prix_max_revente'] = prix_max
                st.session_state.config['pas_optimisation'] = pas
                
                st.markdown("**Pondérations du score (doivent sommer à 1.0)**")
                # Ajouter sliders ou inputs pour les poids w_roi, w_irr etc. si besoin de les rendre configurables
                st.write("Poids actuels (codés en dur): ROI=0.25, TRI=0.20, Payback=0.15, DSCR=0.20, Compétitivité=0.20")

            if st.button("Trouver le meilleur prix (Score)", key="run_score_optimization"):
                with st.spinner("Optimisation par score en cours..."):
                    # Appel à optimize_selling_price
                    results_opt = self.optimize_selling_price(scenario_name)
                    if results_opt:
                        st.session_state.optimization_results[scenario_name] = results_opt
                        st.success("Optimisation par score terminée !")
                        # Afficher les résultats d'optimisation
                        self.display_optimization_results(results_opt)
                    else:
                        st.error("L'optimisation a échoué. Veuillez vérifier vos paramètres.")

            # Afficher les résultats si déjà calculés pour ce scénario
            if scenario_name in st.session_state.optimization_results:
                st.markdown(f"**Résultats de l'optimisation par score déjà calculés pour '{scenario_name}'**")
                self.display_optimization_results(st.session_state.optimization_results[scenario_name])

        # Onglet 4: Monte Carlo
        with tab_montecarlo:
            st.markdown("#### Analyse de Robustesse (Simulation Monte Carlo)")
            st.info(f"Évaluation de la sensibilité des résultats financiers aux variations aléatoires de production et de consommation pour le scénario **{scenario_name}**.")

            # Options Monte Carlo
            with st.expander("Options de la simulation"):
                n_iter = st.number_input("Nombre d'itérations", min_value=100, max_value=10000, value=st.session_state.config.get('nb_iterations_monte_carlo', 1000), step=100, key="mc_iter_input")
                std_prod = st.slider("Écart-type Production (%)", min_value=0.0, max_value=30.0, value=st.session_state.config.get('ecart_type_production', 10.0), step=1.0, key="mc_std_prod")
                std_cons = st.slider("Écart-type Consommation (%)", min_value=0.0, max_value=30.0, value=st.session_state.config.get('ecart_type_consommation', 5.0), step=1.0, key="mc_std_cons")
                
                prix_mc_source = st.radio("Prix de vente pour la simulation", 
                                        ["Utiliser le prix optimal trouvé (si dispo)", "Utiliser un prix personnalisé"], 
                                        key="mc_price_source_radio")
                
                prix_mc_perso = None
                if prix_mc_source == "Utiliser un prix personnalisé":
                    prix_mc_perso = st.number_input("Prix personnalisé (€/kWh)", min_value=0.01, max_value=0.5, value=st.session_state.config.get('prix_vente_initial', 0.17), step=0.001, format="%.3f", key="mc_price_input")
                
                # Mise à jour config (temporaire pour ce run)
                st.session_state.config['nb_iterations_monte_carlo'] = n_iter
                st.session_state.config['ecart_type_production'] = std_prod
                st.session_state.config['ecart_type_consommation'] = std_cons

            if st.button("Lancer la Simulation Monte Carlo", key="run_mc_button"):
                prix_final_mc = prix_mc_perso # Sera None si "Prix optimal" choisi
                if prix_mc_source == "Utiliser le prix optimal trouvé (si dispo)":
                    if scenario_name in st.session_state.optimization_results:
                        prix_final_mc = st.session_state.optimization_results[scenario_name].get('prix_optimal')
                    if prix_final_mc is None: # Si pas d'optimisation ou pas de prix optimal trouvé
                        st.warning(f"Prix optimal non disponible pour '{scenario_name}'. Utilisation du prix initial de la configuration.")
                        prix_final_mc = st.session_state.config.get('prix_vente_initial', 0.17)
                
                if prix_final_mc is None: # Devrait seulement arriver si prix perso n'est pas entré
                    st.error("Veuillez entrer un prix personnalisé ou vous assurer qu'un prix optimal a été calculé.")
                else:
                    with st.spinner(f"Lancement de {n_iter} itérations Monte Carlo..."):
                        results_mc = self.run_monte_carlo_simulation(scenario_name, prix_revente=prix_final_mc)
                    if results_mc:
                        st.session_state.monte_carlo_results[scenario_name] = results_mc
                        st.success("Simulation Monte Carlo terminée !")
                        # Afficher les résultats MC
                        self.display_monte_carlo_results(results_mc)
                    else:
                        st.error("La simulation Monte Carlo a échoué. Veuillez vérifier vos paramètres.")

            # Afficher les résultats MC si déjà calculés
            if scenario_name in st.session_state.monte_carlo_results:
                st.markdown(f"**Résultats Monte Carlo déjà calculés pour '{scenario_name}'**")
                self.display_monte_carlo_results(st.session_state.monte_carlo_results[scenario_name])

        # Onglet 5: Comparaison Scénarios
        with tab_compare:
            st.markdown("#### Comparaison des Indicateurs Clés entre Scénarios")
            
            scenarios_with_results_comp = [s for s in st.session_state.scenarios.keys() if s in st.session_state.economic_results]
            
            if len(scenarios_with_results_comp) < 2:
                st.info("Lancez au moins l'Analyse de Base pour deux scénarios différents pour pouvoir les comparer.")
            else:
                scenarios_to_compare_comp = st.multiselect(
                    "Sélectionnez les scénarios à comparer:",
                    options=scenarios_with_results_comp,
                    default=scenarios_with_results_comp[:min(3, len(scenarios_with_results_comp))],
                    key="compare_scenarios_multi"
                )
                if scenarios_to_compare_comp:
                    results_comp = {s: st.session_state.economic_results[s] for s in scenarios_to_compare_comp}
                    # Afficher la comparaison
                    self.display_scenarios_comparison(results_comp)
                else:
                    st.info("Sélectionnez au moins deux scénarios pour les comparer.")

        # Onglet 6: Analyse de Sensibilité
        with tab_sensi:
            st.markdown("#### Analyse de Sensibilité sur un Paramètre")
            
            param_sensi = st.selectbox(
                "Paramètre à faire varier:",
                options=["prix_revente", "inflation", "opex", "capex", "debt_ratio", "debt_term_years", "degradation_rate"],
                format_func=lambda x: { "prix_revente": "Prix de vente (€/kWh)", "inflation": "Taux d'inflation (%)", "opex": "OPEX (€/an)", "capex": "CAPEX (€)", "debt_ratio": "Ratio Dette/Total", "debt_term_years": "Durée du prêt (années)", "degradation_rate": "Taux de dégradation annuel (%)" }[x],
                key="sensitivity_param_select"
            )
            
            # Définir les valeurs par défaut pour le range du paramètre
            config = st.session_state.config
            if param_sensi == "prix_revente": 
                default_range = (0.12, 0.22)
                unit_sensi = "€/kWh"
                n_steps = 11
            elif param_sensi == "inflation": 
                default_range = (1.0, 4.0)
                unit_sensi = "%"
                n_steps = 11
            elif param_sensi == "opex": 
                default_range = (config.get("opex", 4500)*0.8, config.get("opex", 4500)*1.2)
                unit_sensi = "€/an"
                n_steps = 9
            elif param_sensi == "capex": 
                default_range = (config.get("capex", 85000)*0.8, config.get("capex", 85000)*1.2)
                unit_sensi = "€"
                n_steps = 9
            elif param_sensi == "debt_ratio": 
                default_range = (0.6, 0.9)
                unit_sensi = ""
                n_steps = 7
            elif param_sensi == "debt_term_years": 
                default_range = (10, 20)
                unit_sensi = "ans"
                n_steps = 11
            elif param_sensi == "degradation_rate": 
                default_range = (0.003, 0.008)
                unit_sensi = ""
                n_steps = 6
            else: 
                default_range = (0, 1)
                unit_sensi = ""
                n_steps = 5

            val_min, val_max = st.slider(f"Plage de valeurs pour '{param_sensi}' ({unit_sensi})", 
                                        min_value=float(default_range[0]), 
                                        max_value=float(default_range[1]), 
                                        value=default_range, 
                                        step=(default_range[1]-default_range[0])/20,
                                        key="sensitivity_range_slider")

            values_sensi = np.linspace(val_min, val_max, n_steps)

            if st.button("Lancer l'Analyse de Sensibilité", key="run_sensitivity"):
                with st.spinner(f"Analyse de sensibilité pour {param_sensi} sur {scenario_name}..."):
                    results_sensi = self.sensitivity_analysis(scenario_name, param_sensi, values_sensi)
                if results_sensi:
                    st.success("Analyse de sensibilité terminée.")
                    # Afficher les résultats
                    self.display_sensitivity_analysis(results_sensi, param_sensi, unit_sensi)
                else:
                    st.error("L'analyse de sensibilité a échoué. Veuillez vérifier vos paramètres.")