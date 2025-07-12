# modules/analysis_engine.py

import pandas as pd
import numpy as np
from datetime import datetime
import time
import traceback
import sys
import copy
from scipy.optimize import minimize
# Importer brentq SI vous voulez l'option pour NPV_equity=0 plus tard
# from scipy.optimize import brentq 

# Gestion de la dépendance à numpy_financial
try:
    import numpy_financial as npf
    NPF_IS_REAL = True
except ImportError:
    NPF_IS_REAL = False
    print("AVERTISSEMENT MOTEUR: numpy_financial non trouvé. Fonctions secours utilisées.")
    
    def secours_npv(rate, values):
        """Fonction de secours pour NPV si numpy_financial n'est pas disponible."""
        values = np.asarray(values)
        # ... (copier la fonction secours_npv depuis votre code) ...
        if abs(rate - (-1.0)) < 1e-9: 
            return float('-inf') if np.any(values != 0) else 0.0
        if rate < -1.0: 
            return float('-inf') 
        with np.errstate(over='raise', invalid='raise'): 
            try:
                discount_factors = (1 + rate) ** np.arange(len(values))
                if np.any(np.isclose(discount_factors, 0)): 
                    return np.inf 
                pv = values / discount_factors
                if not np.all(np.isfinite(pv)): 
                    return np.inf 
                return np.sum(pv) 
            except (FloatingPointError, OverflowError): 
                return np.inf if rate >= -1.0 else -np.inf 

    # !! AJOUTER VOTRE FONCTION secours_irr ICI SI NÉCESSAIRE !!
    # Exemple placeholder:
    def secours_irr(values, guess=0.1):
        print("ERREUR MOTEUR: Fonction secours_irr non implémentée!")
        # Implémentez la logique avec brentq ou newton ici
        return None 

    class NpfModule:
        """Module de remplacement si numpy_financial n'est pas disponible."""
        @staticmethod
        def npv(rate, values): return secours_npv(rate, values)
        @staticmethod
        def irr(values): return secours_irr(values)
    
    npf = NpfModule()


class AnalysisEngine:
    """Moteur de calcul économique pur pour l'optimisation de l'autoconsommation collective."""
    
    def __init__(self, config: dict, scenarios: dict, processed_data: pd.DataFrame):
        """
        Initialise le moteur avec les données et configurations nécessaires.
        """
        if not isinstance(config, dict): raise TypeError("config doit être un dict")
        if not isinstance(scenarios, dict): raise TypeError("scenarios doit être un dict")
        if not isinstance(processed_data, pd.DataFrame): raise TypeError("processed_data doit être un DataFrame")
        if processed_data.empty: raise ValueError("processed_data ne peut pas être vide")
        
        self.config = config
        self.scenarios = scenarios
        self.processed_data = processed_data
        # Exposer le statut NPF peut être utile pour l'UI
        self.npf_available = NPF_IS_REAL 

    def calculate_wacc(self, debt_ratio, taux_interet_dette_pct, taux_imposition_pct, cout_fonds_propres_pct) -> float | None:
        """Calcule le WACC."""
        try:
            rd = float(taux_interet_dette_pct) / 100.0
            tc = float(taux_imposition_pct) / 100.0
            re = float(cout_fonds_propres_pct) / 100.0
            dr = float(debt_ratio)
            if not (0 <= dr <= 1): raise ValueError("Debt ratio [0-1]")
            if not (0 <= tc < 1): raise ValueError("Taux imposition [0-100[")
            cout_dette_apres_impots = rd * (1.0 - tc)
            equity_ratio = 1.0 - dr
            wacc = (dr * cout_dette_apres_impots) + (equity_ratio * re)
            return wacc
        except (TypeError, ValueError) as e:
            print(f"ERREUR MOTEUR (calculate_wacc): {e}")
            # Retourner None pour indiquer l'échec, l'UI gérera l'affichage de l'erreur
            return None

    def calculate_financial_indicators(self, scenario_name: str, prix_revente: float | None = None, override_source_prix_autoconso: str | None = None) -> dict | None:
        """
        Calcule les indicateurs financiers pour un scénario donné.
        Retourne un dictionnaire de résultats ou None en cas d'erreur majeure.
        Lève ValueError pour les erreurs de paramètres ou de logique.
        """
        start_time_calc = time.time() 
        
        try:
            # Utiliser self.config, self.scenarios, self.processed_data
            if scenario_name not in self.scenarios:
                raise ValueError(f"Scénario '{scenario_name}' invalide.")
            
            data = self.processed_data.copy()
            scenario = self.scenarios[scenario_name]
            config = self.config
            
            # --- Vérification et récupération paramètres ---
            # (Copier la logique de vérification et conversion de votre code précédent)
            # ...
            required_keys = [ # Liste exhaustive des clés attendues
                 "date_debut_ppa", "duree_ppa", "taux_inflation", "taux_imposition",
                 "prix_vente_initial", "capex", "opex", "degradation_rate", "puissance_kwc",
                 "cout_fonds_propres", "with_loan", "tarif_oa", "tarif_edf_reference",
                 "tarif_oa_indexe_inflation", "taux_inflation_tarif_oa",
                 "amortissement_duree", "valeur_residuelle_pct",
                 "cout_demantelement_pct", "source_prix_autoconso",
                 "subvention_rate_le3", "subvention_rate_le9", "subvention_rate_le36",
                 "subvention_rate_le100", "subvention_rate_gt100"
            ]
            loan_keys = ["debt_ratio", "debt_term_years", "taux_interet_dette", "target_dscr"]
            missing_keys = [k for k in required_keys if config.get(k) is None]
            loan_active = config.get("with_loan", True)
            if loan_active: missing_keys.extend([k for k in loan_keys if config.get(k) is None])
            if missing_keys: raise ValueError(f"Paramètres config manquants: {', '.join(missing_keys)}")

            try:
                simulation_years = int(config["duree_ppa"] / 12)
                if simulation_years <= 0: raise ValueError("Durée PPA > 0")
                # ... (toutes les autres conversions float(), int()...)
                capex_base = float(config["capex"])
                opex_base = float(config["opex"])
                puissance_kwc = float(config.get("puissance_kwc", 0.0))
                prix_vente_config = float(config["prix_vente_initial"])
                prix_revente_input = float(prix_revente) if prix_revente is not None else None
                prix_vente_a_utiliser = prix_revente_input if prix_revente_input is not None else prix_vente_config
                degradation_rate_base = float(config["degradation_rate"])
                taux_inflation = float(config["taux_inflation"]) / 100.0
                oa_indexed = config.get("tarif_oa_indexe_inflation", False)
                inflation_rate_oa = float(config.get("taux_inflation_tarif_oa", 1.5)) / 100.0
                source_prix_autoc_config = config.get("source_prix_autoconso", "prix_initial")
                source_prix_autoc = override_source_prix_autoconso if override_source_prix_autoconso is not None else source_prix_autoc_config
                tarif_edf_ref = float(config.get("tarif_edf_reference", 0.21))
                tarif_oa_base = float(config.get('tarif_oa', 0.0))
                taux_imposition_pct = float(config["taux_imposition"])
                taux_imposition = taux_imposition_pct / 100.0
                amortissement_duree = int(config.get("amortissement_duree", 15))
                if amortissement_duree <= 0: raise ValueError("Durée amortissement > 0")
                valeur_residuelle_pct = float(config.get("valeur_residuelle_pct", 0.0)) / 100.0
                cout_demantelement_pct = float(config.get("cout_demantelement_pct", 5.0)) / 100.0
                cout_fonds_propres_pct = float(config.get("cout_fonds_propres", 8.0))
                cout_fonds_propres = cout_fonds_propres_pct / 100.0
                target_dscr = float(config.get('target_dscr', 1.2))
                debt_ratio = float(config.get("debt_ratio", 0.80)) if loan_active else 0.0
                debt_term_years = int(config.get("debt_term_years", 15)) if loan_active else 0
                taux_interet_dette_pct = float(config.get("taux_interet_dette", 0.0)) if loan_active else 0.0
                taux_interet_dette = taux_interet_dette_pct / 100.0
                # reference_year = datetime.fromisoformat(str(config["date_debut_ppa"])).year # Pas forcément utile
            except (ValueError, TypeError, KeyError) as e:
                raise ValueError(f"Erreur paramètre config: {e}") from e


            # --- Application modificateurs ---
            # ...
            capex = capex_base * float(scenario.get("capex_modifier", 1.0))
            opex_annual = opex_base * float(scenario.get("opex_modifier", 1.0))
            adjusted_inflation = taux_inflation * float(scenario.get("inflation_modifier", 1.0))
            degradation_rate = degradation_rate_base * float(scenario.get("degradation_modifier", 1.0))
            production_modifier = float(scenario.get("production_modifier", 1.0))

            # --- Calcul subventions ---
            # ...
            rate_le3 = float(config.get("subvention_rate_le3", 0.0))
            rate_le9 = float(config.get("subvention_rate_le9", 0.0))
            rate_le36 = float(config.get("subvention_rate_le36", 0.0))
            rate_le100 = float(config.get("subvention_rate_le100", 0.0))
            rate_gt100 = float(config.get("subvention_rate_gt100", 0.0))
            applicable_sub_rate = 0.0
            if puissance_kwc <= 3: applicable_sub_rate = rate_le3
            elif puissance_kwc <= 9: applicable_sub_rate = rate_le9
            elif puissance_kwc <= 36: applicable_sub_rate = rate_le36
            elif puissance_kwc <= 100: applicable_sub_rate = rate_le100
            else: applicable_sub_rate = rate_gt100
            total_subvention = applicable_sub_rate * puissance_kwc

            # --- Calculs financiers base ---
            # ...
            equity_ratio = 1.0 - debt_ratio
            debt_amount = capex * debt_ratio
            equity_amount = capex * equity_ratio
            capex_net_subvention = max(0, capex - total_subvention)
            net_equity_investment = equity_amount - total_subvention
            
            # --- Préparation données énergétiques ---
            # ...
            required_data_cols = ['Temps', 'production_kwh', 'consumption_kwh']
            if not all(col in data.columns for col in required_data_cols):
                raise ValueError(f"Colonnes manquantes données traitées: {set(required_data_cols) - set(data.columns)}")
            data['year'] = data['Temps'].dt.year
            # Utiliser l'année la plus ancienne comme référence
            ref_year = data['year'].min()
            reference_data = data[data['year'] == ref_year].copy()
            if reference_data.empty: raise ValueError(f"Aucune donnée pour l'année de référence {ref_year}.")
            ref_prod = reference_data['production_kwh'].values
            ref_cons = reference_data['consumption_kwh'].values

            # --- Initialisation tableaux ---
            # ...
            years = np.arange(1, simulation_years + 1)
            arrays = {name: np.zeros(simulation_years) for name in [
                "annual_production", "annual_consumption", "annual_autoconsumption", "annual_surplus",
                "revenues", "opex", "depreciation", "ebitda", "ebit", "interest_paid", "ebt",
                "taxes", "net_income", "principal_paid", "debt_service", "free_cash_flow",
                "cumulative_cash_flow", "dscr"
            ]}


            # --- Calcul amortissement ---
            # ...
            base_amortissable = capex_net_subvention * (1 - valeur_residuelle_pct)
            if amortissement_duree > 0:
                annual_depreciation_amount = base_amortissable / amortissement_duree
                for i in range(min(simulation_years, amortissement_duree)):
                    arrays["depreciation"][i] = annual_depreciation_amount

            # --- Calcul échéancier dette ---
            # ... (logique complète comme dans votre code) ...
            annual_debt_payment = 0.0
            if loan_active and abs(debt_amount) > 1e-6 and debt_term_years > 0:
                if abs(taux_interet_dette) < 1e-9:
                    annual_debt_payment = debt_amount / debt_term_years
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


            # --- Boucle principale annuelle ---
            for idx, year_num in enumerate(years):
                # ... (calculs production, conso, auto, surplus, revenus, opex, p&l, fcf)
                # --- SANS AUCUN print() ou st. ---
                degradation_factor = (1 - degradation_rate) ** (year_num - 1)
                current_production = ref_prod * degradation_factor * production_modifier
                current_consumption = ref_cons
                autoconsumption_hourly = np.minimum(current_production, current_consumption)
                surplus_hourly = current_production - autoconsumption_hourly

                arrays["annual_production"][idx] = current_production.sum()
                arrays["annual_consumption"][idx] = current_consumption.sum()
                arrays["annual_autoconsumption"][idx] = autoconsumption_hourly.sum()
                arrays["annual_surplus"][idx] = surplus_hourly.sum()

                inflation_factor = (1 + adjusted_inflation) ** (year_num - 1)
                if source_prix_autoc == "tarif_edf":
                    prix_achat_evite = tarif_edf_ref * inflation_factor
                    tarif_oa_year = tarif_oa_base * ((1 + inflation_rate_oa) ** (year_num - 1) if oa_indexed else 1)
                elif source_prix_autoc == "tarif_oa":
                    tarif_oa_year = tarif_oa_base * ((1 + inflation_rate_oa) ** (year_num - 1) if oa_indexed else 1)
                    prix_achat_evite = tarif_oa_year
                else: # "prix_initial"
                    prix_achat_evite = prix_vente_a_utiliser * inflation_factor
                    tarif_oa_year = tarif_oa_base * ((1 + inflation_rate_oa) ** (year_num - 1) if oa_indexed else 1)

                if override_source_prix_autoconso == "prix_initial":
                    tarif_oa_year = prix_vente_a_utiliser * inflation_factor

                revenus_autoconsommation = arrays["annual_autoconsumption"][idx] * prix_achat_evite
                revenus_surplus = arrays["annual_surplus"][idx] * tarif_oa_year
                arrays["revenues"][idx] = revenus_autoconsommation + revenus_surplus

                arrays["opex"][idx] = opex_annual * inflation_factor
                if year_num == simulation_years:
                    cout_demantelement_final = capex_base * cout_demantelement_pct
                    arrays["opex"][idx] += cout_demantelement_final

                arrays["ebitda"][idx] = arrays["revenues"][idx] - arrays["opex"][idx]
                arrays["ebit"][idx] = arrays["ebitda"][idx] - arrays["depreciation"][idx]
                arrays["ebt"][idx] = arrays["ebit"][idx] - arrays["interest_paid"][idx]
                arrays["taxes"][idx] = max(0, arrays["ebt"][idx] * taux_imposition)
                arrays["net_income"][idx] = arrays["ebt"][idx] - arrays["taxes"][idx]
                arrays["free_cash_flow"][idx] = arrays["net_income"][idx] + arrays["depreciation"][idx] - arrays["principal_paid"][idx]

            # --- Calculs finaux (cumul, dscr, irr, npv, roi, payback, lcoe) ---
            # ... (votre code de calcul SANS st.warning/print) ...
            # Utiliser try/except pour npf.irr/npf.npv et retourner None si échec
            if simulation_years > 0:
                arrays["cumulative_cash_flow"][0] = arrays["free_cash_flow"][0] - net_equity_investment
                for i in range(1, simulation_years):
                    arrays["cumulative_cash_flow"][i] = arrays["cumulative_cash_flow"][i-1] + arrays["free_cash_flow"][i]

            cfads = arrays["ebitda"] - arrays["taxes"]
            dscr = np.full_like(arrays["debt_service"], float('inf'))
            mask = arrays["debt_service"] > 1e-9
            np.divide(cfads, arrays["debt_service"], out=dscr, where=mask)
            arrays["dscr"] = dscr

            initial_investment_cf0 = net_equity_investment
            yearly_flows = arrays["free_cash_flow"]
            cash_flows_for_irr = np.concatenate(([-initial_investment_cf0], yearly_flows))

            npv = None # Initialiser à None
            wacc = self.calculate_wacc(debt_ratio, taux_interet_dette_pct, taux_imposition_pct, cout_fonds_propres_pct)
            discount_rate_npv = cout_fonds_propres

            if discount_rate_npv is not None and abs(discount_rate_npv - (-1.0)) > 1e-9 : # Eviter rate=-1
                try:
                     pv_yearly_flows = npf.npv(discount_rate_npv, yearly_flows)
                     pv_yearly_flows = pv_yearly_flows if np.isfinite(pv_yearly_flows) else 0.0
                     npv = -initial_investment_cf0 + pv_yearly_flows
                     if not np.isfinite(npv): npv = None # Si le résultat final n'est pas fini
                except Exception as e_npv:
                     print(f"AVERTISSEMENT MOTEUR (NPV): {e_npv}")
                     npv = None # Echec

            irr = None
            try:
                irr = npf.irr(cash_flows_for_irr)
                if not np.isfinite(irr): irr = None
            except Exception as e_irr:
                 print(f"AVERTISSEMENT MOTEUR (IRR): {e_irr}")
                 irr = None

            roi = None
            if npv is not None: # Seulement si NPV a été calculée
                 if abs(initial_investment_cf0) > 1e-9:
                      roi = npv / initial_investment_cf0
                      if not np.isfinite(roi): roi = None
                 elif initial_investment_cf0 <= 0:
                      roi = float('inf') if npv > 0 else (-float('inf') if npv < 0 else 0)
                      if not np.isfinite(roi): roi = None # Gérer les infinis aussi si besoin

            payback_period = None
            if simulation_years > 0:
                # ... (logique payback comme avant, mais assigner None si infini) ...
                cum_cf_corrected_for_payback = np.concatenate(([-initial_investment_cf0], arrays["cumulative_cash_flow"]))
                positive_indices = np.where(cum_cf_corrected_for_payback >= -1e-9)[0]
                if len(positive_indices) > 0:
                    first_positive_idx = positive_indices[0]
                    if first_positive_idx == 0: payback_period = 0.0
                    else:
                        year_before_positive_1based = first_positive_idx
                        last_negative_cum_cf = cum_cf_corrected_for_payback[first_positive_idx - 1]
                        cash_flow_crossing_year = arrays["free_cash_flow"][first_positive_idx - 1]
                        if cash_flow_crossing_year > 1e-9:
                            fraction = max(0.0, min(1.0, -last_negative_cum_cf / cash_flow_crossing_year))
                            payback_period = (year_before_positive_1based - 1) + fraction
                        elif abs(cum_cf_corrected_for_payback[first_positive_idx]) < 1e-9:
                             payback_period = float(year_before_positive_1based)
            # Si payback_period est toujours None ici, il reste None (au lieu de inf)

            avg_dscr = None
            if loan_active and debt_term_years > 0:
                # ... (logique avg dscr comme avant, assigner None si infini ou non calculable) ...
                dscr_term_indices = np.arange(min(simulation_years, int(debt_term_years)))
                if len(dscr_term_indices) > 0:
                    dscr_in_term = arrays["dscr"][dscr_term_indices]
                    dscr_finite_in_term = dscr_in_term[np.isfinite(dscr_in_term)]
                    if len(dscr_finite_in_term) > 0:
                        avg_dscr = np.mean(dscr_finite_in_term)

            # --- DEBUG LCOE --- 
            print("--- DEBUG LCOE --- Pré-calcul")
            print(f"  WACC: {wacc}")
            print(f"  CAPEX Net Subvention: {capex_net_subvention}")
            # Afficher le début et la fin des tableaux pour éviter trop de log
            if isinstance(arrays['annual_production'], np.ndarray):
                 print(f"  Annual Production (premiers 5): {arrays['annual_production'][:5]}")
                 print(f"  Annual Production (derniers 5): {arrays['annual_production'][-5:]}")
            if isinstance(arrays['opex'], np.ndarray):
                 print(f"  Annual OPEX (premiers 5): {arrays['opex'][:5]}")
                 print(f"  Annual OPEX (derniers 5): {arrays['opex'][-5:]}")
            print("-------------------")
            # --- FIN DEBUG LCOE ---
            
            lcoe = None
            if wacc is not None and abs(wacc - (-1.0)) > 1e-9:
                 # ... (logique LCOE comme avant, assigner None si échec ou infini) ...
                try:
                    dfs_lcoe = (1 + wacc) ** np.arange(1, simulation_years + 1)
                    valid_dfs_lcoe = dfs_lcoe != 0
                    discounted_production = arrays["annual_production"][valid_dfs_lcoe] / dfs_lcoe[valid_dfs_lcoe]
                    total_discounted_production = np.sum(discounted_production)
                    discounted_opex = arrays["opex"][valid_dfs_lcoe] / dfs_lcoe[valid_dfs_lcoe]
                    total_discounted_opex = np.sum(discounted_opex)
                    total_discounted_costs = capex_net_subvention + total_discounted_opex
                    if abs(total_discounted_production) > 1e-9:
                        lcoe = total_discounted_costs / total_discounted_production
                        if not np.isfinite(lcoe): lcoe = None
                except Exception as e_lcoe:
                    print(f"AVERTISSEMENT MOTEUR (LCOE): {e_lcoe}")
                    lcoe = None

            # Calcul taux auto/autoprod
            total_annual_production = arrays["annual_production"].sum()
            total_annual_consumption = arrays["annual_consumption"].sum()
            total_annual_autoconsumption = arrays["annual_autoconsumption"].sum()
            autoconsumption_rate = total_annual_autoconsumption / total_annual_production if total_annual_production > 1e-9 else 0
            autoproduction_rate = total_annual_autoconsumption / total_annual_consumption if total_annual_consumption > 1e-9 else 0
            
            # --- Construction dictionnaire résultats ---
            results = {
                "scenario": scenario_name, "prix_revente": prix_vente_a_utiliser,
                "capex": capex, "equity_amount": equity_amount, "debt_amount": debt_amount,
                "total_subvention": total_subvention, "net_equity_investment": net_equity_investment,
                "autoconsumption_rate": autoconsumption_rate, "autoproduction_rate": autoproduction_rate,
                "irr": irr, "wacc": wacc, "npv": npv,
                "roi": roi, "payback_period": payback_period, "avg_dscr": avg_dscr,
                "lcoe": lcoe, "years": years.tolist(),
                # Retourner aussi les cash flows utilisés peut être utile pour debug/export
                "cash_flows_for_irr_npv": cash_flows_for_irr.tolist(),
                "source_prix_autoconso_utilisee": source_prix_autoc # Ajouter pour clarté/debug
            }
            # Ajouter les tableaux annuels
            for key, arr in arrays.items(): results[key] = arr.tolist()

            # print(f"Calcul Moteur OK: {time.time() - start_time_calc:.3f}s.") # Optionnel
            return results

        except (ValueError, TypeError) as e:
             # Erreur de paramètre ou de logique interne attendue
             print(f"ERREUR MOTEUR (calculate_financial_indicators) pour '{scenario_name}': {e}")
             # print(traceback.format_exc()) # Optionnel pour debug serveur
             # Renvoyer l'erreur pour que l'UI puisse l'afficher ou logger
             raise e 
        except Exception as e:
             # Autre erreur inattendue
             print(f"ERREUR MOTEUR INATTENDUE (calculate_financial_indicators): {e}")
             print(traceback.format_exc()) # Important pour debug serveur
             # Renvoyer une erreur générique ou l'exception originale
             raise RuntimeError(f"Erreur inattendue lors du calcul des indicateurs : {e}") from e

    def simulate_selling_price(self,
                               scenario_name: str,
                               target_irr: float | None = None,
                               target_npv: float | None = None,
                               override_source_prix_autoconso: str | None = None
                              ) -> dict | None:
        """
        Trouve le prix pour atteindre un TRI ou VAN cible.
        Accepte un override pour la source de prix autoconso utilisée PENDANT la recherche.
        Retourne le dictionnaire complet des résultats pour le prix trouvé, ou None/Exception.
        """
        print(f"MOTEUR: simulate_selling_price: scenario={scenario_name}, target_irr={target_irr}, target_npv={target_npv}, override_autoconso={override_source_prix_autoconso}") # Log l'override
        try:
            if target_irr is None and target_npv is None:
                raise ValueError("Veuillez spécifier un TRI ou une VAN cible")

            config = self.config
            prix_min_config = float(config.get('prix_min_revente', 0.05))
            prix_max_config = float(config.get('prix_max_revente', 0.40))
            if prix_min_config >= prix_max_config:
                 prix_min_config = 0.05; prix_max_config = 0.40
                 print(f"AVERTISSEMENT MOTEUR: Plage prix invalide, utilisation [{prix_min_config}, {prix_max_config}]")

            # --- Bloc VAN=0 analytique ---
            if target_npv is not None and abs(target_npv) < 1e-9:
                print("MOTEUR: Cible VAN=0 détectée. Utilisation de la méthode analytique modifiée.")
                # Pour ce calcul analytique, on VEUT utiliser l'override (qui est typiquement "prix_initial")
                print(f"  -> Appel initial indicateurs avec override='{override_source_prix_autoconso}'")
                base = self.calculate_financial_indicators(
                    scenario_name,
                    prix_revente=config.get('prix_vente_initial'), # Prix arbitraire ici suffit
                    override_source_prix_autoconso=override_source_prix_autoconso # <--- PASSER L'OVERRIDE
                )
                if not base: raise ValueError("Calcul bases pour prix plancher échoué.")

                # ... (logique calcul prix_plancher comme avant) ...
                capex_net = base['capex'] - base['total_subvention']
                wacc = base['wacc']
                auto = base.get('annual_autoconsumption')
                surplus = base.get('annual_surplus')
                opex = base.get('opex')
                tarif_oa_0 = config.get('tarif_oa', 0.0)
                infl_oa = (config.get('taux_inflation_tarif_oa', 0.0)/100) if config.get('tarif_oa_indexe_inflation', False) else 0.0

                if wacc is None or not auto or not surplus or not opex or len(auto) != len(surplus) or len(auto) != len(opex):
                    raise ValueError("Données invalides pour calcul analytique (VAN=0).")
                if abs(wacc - (-1.0)) < 1e-9: raise ValueError("WACC invalide (-100%) pour calcul analytique (VAN=0)")

                N = len(auto)
                try:
                    dfs = [(1 + wacc)**(t+1) for t in range(N)]
                    if any(abs(df) < 1e-12 for df in dfs): raise ValueError("Facteur actualisation nul (VAN=0).")
                    discounted_auto = sum(auto[t] / dfs[t] for t in range(N))
                    discounted_opex = sum(opex[t] / dfs[t] for t in range(N))
                    discounted_surplus_rev= sum(surplus[t] * tarif_oa_0 * (1+infl_oa)**t / dfs[t] for t in range(N))
                except (OverflowError, ZeroDivisionError, ValueError) as e:
                     raise ValueError(f"Erreur actualisation (VAN=0): {e}") from e

                if abs(discounted_auto) < 1e-9:
                    raise ValueError("Autoconsommation actualisée nulle, calcul prix plancher P impossible.")

                prix_plancher = (capex_net + discounted_opex - discounted_surplus_rev) / discounted_auto
                optimal_price = prix_plancher
                print(f"MOTEUR: Prix plancher analytique calculé: {prix_plancher:.6f}")

            # --- AUTRES CAS (IRR ou VAN != 0) : Utilisation de minimize ---
            else:
                print("MOTEUR: Cible IRR ou VAN != 0. Utilisation de minimize.")
                iteration_count = 0

                # ---> MODIFICATION IMPORTANTE ICI <---
                # L'objective_function doit utiliser l'override passé à simulate_selling_price
                def objective_function(price):
                    nonlocal iteration_count; iteration_count += 1
                    current_price_scalar = price[0] if isinstance(price, (np.ndarray, list)) else price

                    # Utiliser l'instance fournie pour calculer les indicateurs
                    # EN PASSANT L'OVERRIDE REÇU PAR simulate_selling_price
                    results = self.calculate_financial_indicators(
                        scenario_name,
                        prix_revente=current_price_scalar,
                        override_source_prix_autoconso=override_source_prix_autoconso # <--- PASSER L'OVERRIDE
                    )

                    if not results: return 1e10 # Pénalité si échec calcul

                    if target_irr is not None:
                        # ... (logique calcul diff IRR comme avant) ...
                        irr_value = results.get('irr')
                        if irr_value is None: return 1e9
                        target_irr_decimal = target_irr / 100.0 if abs(target_irr) > 1 else target_irr
                        diff = abs(irr_value - target_irr_decimal)
                        return diff
                    else: # target_npv != 0
                        # ... (logique calcul diff NPV comme avant) ...
                        npv_value = results.get('npv')
                        if npv_value is None: return 1e9
                        diff = abs(npv_value - target_npv)
                        return diff
                # ---> FIN MODIFICATION IMPORTANTE <---

                initial_price_guess = config.get('prix_vente_initial', (prix_min_config + prix_max_config) / 2)
                initial_price_guess = max(prix_min_config, min(prix_max_config, initial_price_guess)) # S'assurer que le guess est dans les bornes
                bounds = [(prix_min_config, prix_max_config)]

                # ... (logique minimize avec L-BFGS-B et fallback Nelder-Mead comme avant) ...
                result = minimize(objective_function, [initial_price_guess], method='L-BFGS-B', bounds=bounds, options={'ftol': 1e-7, 'gtol': 1e-6})

                optimal_price = None
                if result.success and bounds[0][0] <= result.x[0] <= bounds[0][1]:
                     optimal_price = result.x[0]
                else:
                    # ... (logique fallback Nelder-Mead) ...
                    print(f"MOTEUR: L-BFGS-B échec/hors bornes (success={result.success}). Essai Nelder-Mead...")
                    # Wrapper pour Nelder-Mead qui ne prend qu'un scalaire
                    def objective_wrapper_nelder(price_scalar):
                        if not (bounds[0][0] <= price_scalar <= bounds[0][1]): return 1e12
                        return objective_function([price_scalar]) # Appelle l'objective_function qui passe l'override

                    result_nm = minimize(objective_wrapper_nelder, initial_price_guess, method='Nelder-Mead', options={'xatol': 1e-5, 'fatol': 1e-6})
                    if result_nm.success and bounds[0][0] <= result_nm.x[0] <= bounds[0][1]:
                        optimal_price = result_nm.x[0]
                    else:
                         print(f"MOTEUR: Nelder-Mead échec aussi (success={result_nm.success}).")
                         raise RuntimeError("Convergence échouée pour trouver le prix cible.")

            # --- Fin des branches ---
            if optimal_price is None: raise RuntimeError("Aucun prix optimal trouvé.")

            # Recalcul final avec le prix trouvé
            # IMPORTANT : Le recalcul final DOIT aussi utiliser l'override si fourni,
            # car c'est sous CETTE condition que le prix a été trouvé !
            print(f"MOTEUR: Recalcul final indicateurs avec prix = {optimal_price:.6f}, override='{override_source_prix_autoconso}'")
            final_results = self.calculate_financial_indicators(
                scenario_name,
                prix_revente=optimal_price,
                override_source_prix_autoconso=override_source_prix_autoconso # <--- PASSER L'OVERRIDE ICI AUSSI
            )

            if final_results:
                final_results['prix_revente_optimal_pour_cible'] = optimal_price
                final_results['target_irr_asked'] = target_irr
                final_results['target_npv_asked'] = target_npv
                # Ajouter LCOE et Tarif EDF au résultat pour affichage contextuel DANS LE CAS VAN=0
                # 'base' n'existera que si on est passé par la branche VAN=0
                if target_npv is not None and abs(target_npv) < 1e-9 and 'base' in locals():
                     final_results['lcoe_associated'] = base.get('lcoe')
                     final_results['tarif_edf_reference'] = self.config.get('tarif_edf_reference')
                return final_results
            else:
                # Si le recalcul échoue, lever une exception plutôt que de retourner None
                raise RuntimeError(f"Échec recalcul final indicateurs avec prix {optimal_price:.6f}")

        except (ValueError, TypeError, RuntimeError) as e:
            print(f"ERREUR MOTEUR (simulate_selling_price): {e}")
            # print(traceback.format_exc()) # Optionnel pour debug serveur
            raise e # Renvoyer pour que l'UI gère
        except Exception as e:
            print(f"ERREUR MOTEUR INATTENDUE (simulate_selling_price): {e}")
            traceback.print_exc() # Imprimer la trace pour ce cas inattendu
            raise RuntimeError(f"Erreur inattendue lors de la simulation du prix : {e}") from e

# Note: Les fonctions _eval_price_solution, show_ui, run_standalone_calculations
# et le bloc if __name__ == "__main__": ont été retirés de ce fichier moteur.