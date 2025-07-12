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
            # (Liste et logique de vérification des clés requises)
            required_keys = [
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
            except (ValueError, TypeError, KeyError) as e:
                raise ValueError(f"Erreur paramètre config: {e}") from e

            # --- Application modificateurs --- 
            capex = capex_base * float(scenario.get("capex_modifier", 1.0)) # CAPEX Total du projet
            opex_annual = opex_base * float(scenario.get("opex_modifier", 1.0))
            adjusted_inflation = taux_inflation * float(scenario.get("inflation_modifier", 1.0))
            degradation_rate = degradation_rate_base * float(scenario.get("degradation_modifier", 1.0))
            production_modifier = float(scenario.get("production_modifier", 1.0))

            # --- Calcul subventions --- 
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
            total_subvention = applicable_sub_rate * puissance_kwc # Puissance et taux lus avant

            # --- Calculs financiers base (Equity) --- 
            equity_ratio = 1.0 - debt_ratio
            debt_amount = capex * debt_ratio
            equity_amount = capex * equity_ratio
            # Capex net subvention utilisé pour amortissement et LCOE
            capex_net_subvention = max(0, capex - total_subvention)
            # Investissement net fonds propres utilisé pour Equity IRR/Payback
            net_equity_investment = equity_amount - total_subvention

            # --- Préparation données énergétiques --- 
            required_data_cols = ['Temps', 'production_kwh', 'consumption_kwh']
            if not all(col in data.columns for col in required_data_cols):
                raise ValueError(f"Colonnes manquantes données traitées: {set(required_data_cols) - set(data.columns)}")
            data['year'] = data['Temps'].dt.year
            ref_year = data['year'].min()
            reference_data = data[data['year'] == ref_year].copy()
            if reference_data.empty: raise ValueError(f"Aucune donnée pour l'année de référence {ref_year}.")
            ref_prod = reference_data['production_kwh'].values
            ref_cons = reference_data['consumption_kwh'].values

            # --- Initialisation tableaux --- 
            years = np.arange(1, simulation_years + 1)
            arrays = {name: np.zeros(simulation_years) for name in [
                "annual_production", "annual_consumption", "annual_autoconsumption", "annual_surplus",
                "revenues", "opex", "depreciation", "ebitda", "ebit", "interest_paid", "ebt",
                "taxes", "net_income", "principal_paid", "debt_service", "free_cash_flow",
                "cumulative_cash_flow", "dscr",
                "operating_cash_flow" # AJOUT: Tableau pour les flux opérationnels projet
            ]}

            # --- Calcul amortissement --- 
            base_amortissable = capex_net_subvention * (1 - valeur_residuelle_pct)
            if amortissement_duree > 0:
                annual_depreciation_amount = base_amortissable / amortissement_duree
                for i in range(min(simulation_years, amortissement_duree)):
                    arrays["depreciation"][i] = annual_depreciation_amount

            # --- Calcul échéancier dette --- 
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
                        principal_this_year = max(0, principal_this_year) # Assurer non négatif
                        arrays["principal_paid"][i] = principal_this_year
                        arrays["debt_service"][i] = arrays["interest_paid"][i] + arrays["principal_paid"][i]
                        remaining_debt -= principal_this_year
                    else:
                        arrays["interest_paid"][i] = 0
                        arrays["principal_paid"][i] = 0
                        arrays["debt_service"][i] = 0

            # --- Boucle principale annuelle ---
            current_tarif_oa = tarif_oa_base
            for idx, year_num in enumerate(years):
                # Calcul indices inflation (démarre année 2)
                inflation_exponent = max(0, year_num - 1) # Exposant = 0 pour année 1, 1 pour année 2, etc.
                inflation_factor = (1 + adjusted_inflation) ** inflation_exponent # <--- Modifié

                # Calcul tarif OA indexé si nécessaire (démarre année 2)
                # La logique existante avec 'idx > 0' est correcte car idx commence à 0
                if oa_indexed and idx > 0: # Indexation commence année 2 (idx=1)
                    current_tarif_oa *= (1 + inflation_rate_oa)

                # Degradation factor (démarre année 2)
                degradation_exponent = max(0, year_num - 1) # Exposant = 0 pour année 1, 1 pour année 2, etc.
                degradation_factor = (1 - degradation_rate) ** degradation_exponent # <--- Modifié

                # Calcul production annuelle dégradée
                annual_prod = ref_prod * degradation_factor * production_modifier # Utilise le facteur dégradé
                arrays["annual_production"][idx] = np.sum(annual_prod)
                arrays["annual_consumption"][idx] = np.sum(ref_cons)

                # Calcul autoconsommation et surplus (basé sur la production dégradée)
                autoconsumption = np.minimum(annual_prod, ref_cons)
                surplus = annual_prod - autoconsumption
                arrays["annual_autoconsumption"][idx] = np.sum(autoconsumption)
                arrays["annual_surplus"][idx] = np.sum(surplus)

                # Calcul prix autoconsommation
                if source_prix_autoc == 'prix_initial':
                    prix_autoc = prix_vente_a_utiliser * inflation_factor # Utilise le facteur inflation
                elif source_prix_autoc == 'tarif_edf':
                    prix_autoc = tarif_edf_ref * inflation_factor # Utilise le facteur inflation
                elif source_prix_autoc == 'tarif_oa':
                    prix_autoc = current_tarif_oa # Utilise le tarif OA (potentiellement indexé)
                else: # Fallback si la clé est invalide, on prend le prix initial
                    prix_autoc = prix_vente_a_utiliser * inflation_factor

                # Calcul revenus
                revenue_surplus = arrays["annual_surplus"][idx] * current_tarif_oa
                revenue_autoconsommation = arrays["annual_autoconsumption"][idx] * prix_autoc
                arrays["revenues"][idx] = revenue_surplus + revenue_autoconsommation

                # Calcul OPEX annuel indexé (démarre année 2)
                arrays["opex"][idx] = opex_annual * inflation_factor # Utilise le facteur inflation

                # --- Calcul P&L ---
                arrays["ebitda"][idx] = arrays["revenues"][idx] - arrays["opex"][idx]
                arrays["ebit"][idx] = arrays["ebitda"][idx] - arrays["depreciation"][idx]
                arrays["ebt"][idx] = arrays["ebit"][idx] - arrays["interest_paid"][idx]
                arrays["taxes"][idx] = max(0, arrays["ebt"][idx] * taux_imposition)
                arrays["net_income"][idx] = arrays["ebt"][idx] - arrays["taxes"][idx]
                # Free Cash Flow Equity (FCFE)
                arrays["free_cash_flow"][idx] = arrays["net_income"][idx] + arrays["depreciation"][idx] - arrays["principal_paid"][idx]
                # Calcul Operating Cash Flow (OCF) Projet
                ebitda_yr = arrays["ebitda"][idx]
                depreciation_yr = arrays["depreciation"][idx]
                arrays["operating_cash_flow"][idx] = (ebitda_yr * (1.0 - taux_imposition)) + (depreciation_yr * taux_imposition)
                # --- FIN Calcul P&L ---

            # --- Calculs finaux (cumul FCFE, dscr, Equity IRR/NPV/ROI/Payback, LCOE) --- 
            if simulation_years > 0:
                arrays["cumulative_cash_flow"][0] = arrays["free_cash_flow"][0]
                for i in range(1, simulation_years):
                    arrays["cumulative_cash_flow"][i] = arrays["cumulative_cash_flow"][i-1] + arrays["free_cash_flow"][i]
            # Calcul DSCR annuel et moyen
            cash_available_for_ds = arrays["ebitda"] - arrays["taxes"]
            debt_service = arrays["debt_service"]
            # Eviter division par zéro si service dette nul
            valid_ds_indices = np.where(abs(debt_service) > 1e-9)[0]
            if len(valid_ds_indices) > 0:
                dscr_annual = np.full(simulation_years, np.nan)
                dscr_annual[valid_ds_indices] = cash_available_for_ds[valid_ds_indices] / debt_service[valid_ds_indices]
                arrays["dscr"] = dscr_annual
                # Calculer la moyenne seulement sur les années où DSCR est calculable
                avg_dscr = np.nanmean(dscr_annual[valid_ds_indices])
            else:
                arrays["dscr"] = np.full(simulation_years, np.nan) # Ou np.inf ? np.nan est plus sûr
                avg_dscr = np.inf # Si pas de dette, DSCR est infini
            # --- Equity IRR/NPV/ROI/Payback --- 
            initial_equity_investment_cf0 = net_equity_investment # Renommé pour clarté
            yearly_fcfe_flows = arrays["free_cash_flow"] # Renommé pour clarté
            equity_cash_flows_for_irr = np.concatenate(([-initial_equity_investment_cf0], yearly_fcfe_flows))
            # Calcul WACC
            wacc = self.calculate_wacc(debt_ratio, taux_interet_dette_pct, taux_imposition_pct, cout_fonds_propres_pct)
            # Calcul NPV Equity
            npv_equity = None
            if wacc is not None:
                try:
                     # npf.npv attend le taux d'abord, puis les flux (y compris T0)
                     npv_equity = npf.npv(wacc, equity_cash_flows_for_irr)
                     if not np.isfinite(npv_equity): npv_equity = None
                except Exception as e_npv:
                     print(f"AVERTISSEMENT MOTEUR (NPV Equity): {e_npv}")
                     npv_equity = None
            else: # Si WACC non calculable (ex: dette 100% ou FP 100% sans coût défini)
                 print("AVERTISSEMENT MOTEUR: WACC non calculable, NPV Equity non calculée.")
            # Calcul IRR Equity
            irr_equity = None
            try:
                irr_equity = npf.irr(equity_cash_flows_for_irr)
                if not np.isfinite(irr_equity): irr_equity = None
            except Exception as e_irr:
                 print(f"AVERTISSEMENT MOTEUR (IRR Equity): {e_irr}")
                 irr_equity = None
            # Calcul ROI Equity
            roi_equity = None
            if npv_equity is not None and abs(initial_equity_investment_cf0) > 1e-9:
                roi_equity = npv_equity / initial_equity_investment_cf0
            # Calcul Payback Equity
            payback_equity = None
            cumulative_fcfe_with_t0 = np.cumsum(equity_cash_flows_for_irr)
            positive_indices_equity = np.where(cumulative_fcfe_with_t0 >= -1e-9)[0] # Tolérance
            if len(positive_indices_equity) > 0:
                first_positive_idx_equity = positive_indices_equity[0]
                if first_positive_idx_equity == 0:
                     payback_equity = 0.0
                else:
                    year_before_positive_1based_equity = first_positive_idx_equity
                    last_negative_cum_cf_equity = cumulative_fcfe_with_t0[first_positive_idx_equity - 1]
                    cash_flow_crossing_year_equity = yearly_fcfe_flows[first_positive_idx_equity - 1]
                    if cash_flow_crossing_year_equity > 1e-9:
                        fraction_equity = max(0.0, min(1.0, -last_negative_cum_cf_equity / cash_flow_crossing_year_equity))
                        payback_equity = (year_before_positive_1based_equity - 1) + fraction_equity
                    elif abs(cumulative_fcfe_with_t0[first_positive_idx_equity]) < 1e-9:
                        payback_equity = float(year_before_positive_1based_equity)
            # --- AJOUT: Calcul Indicateurs Projet (Project IRR/Payback) --- 
            initial_project_investment_cf0 = capex # <-- Utiliser le CAPEX TOTAL ici
            yearly_ocf_flows = arrays["operating_cash_flow"] # Utiliser les OCF calculés plus haut
            # Ajouter le coût de démantèlement à la fin (négatif) et la valeur résiduelle (positive)
            # Attention: OCF est sur `simulation_years`, il faut potentiellement l'étendre
            final_year_index = simulation_years - 1
            if final_year_index >= 0:
                final_ocf = yearly_ocf_flows[final_year_index]
                # Calcul valeur résiduelle et démantèlement
                valeur_residuelle_amount = capex_net_subvention * valeur_residuelle_pct
                cout_demantelement_amount = capex * cout_demantelement_pct # Basé sur CAPEX brut
                # Ajustement du dernier flux OCF
                adjusted_final_ocf = final_ocf + valeur_residuelle_amount - cout_demantelement_amount
                # Créer le tableau de flux projet
                project_cash_flows = np.concatenate((
                    [-initial_project_investment_cf0], 
                    yearly_ocf_flows[:final_year_index], 
                    [adjusted_final_ocf]
                ))
            else: # Si simulation_years=0
                project_cash_flows = np.array([-initial_project_investment_cf0])
            # Calcul Project IRR
            project_irr = None
            try:
                if abs(project_cash_flows[0]) > 1e-9: # Éviter erreur si CAPEX = 0
                    project_irr = npf.irr(project_cash_flows) # Utilise flux PROJET
                    if not np.isfinite(project_irr): project_irr = None
                elif len(project_cash_flows) > 1 and np.any(project_cash_flows[1:] > 1e-9):
                    project_irr = float('inf') # Si invest 0 et flux futurs positifs
            except Exception as e_irr_proj:
                print(f"AVERTISSEMENT MOTEUR (Project IRR): {e_irr_proj}")
                project_irr = None
            # Calcul Project Payback
            project_payback = None
            if simulation_years > 0:
                cumulative_project_cf = np.cumsum(project_cash_flows) # Cumul des flux PROJET
                positive_indices_proj = np.where(cumulative_project_cf >= -1e-9)[0] # Tolérance pour zéro

                if len(positive_indices_proj) > 0:
                    first_positive_idx_proj = positive_indices_proj[0]
                    if first_positive_idx_proj == 0: # Si CAPEX <= 0
                         project_payback = 0.0
                    else:
                        year_before_positive_1based_proj = first_positive_idx_proj
                        last_negative_cum_cf_proj = cumulative_project_cf[first_positive_idx_proj - 1]
                        # Utiliser le flux OCF (ajusté si dernière année) de l'année où ça devient positif
                        if first_positive_idx_proj <= simulation_years: # Index basé sur project_cash_flows (T0 inclus)
                           cash_flow_crossing_year_proj = project_cash_flows[first_positive_idx_proj]
                        else: # Devrait pas arriver si first_positive_idx_proj est valide
                           cash_flow_crossing_year_proj = 0 

                        if cash_flow_crossing_year_proj > 1e-9:
                            fraction_proj = max(0.0, min(1.0, -last_negative_cum_cf_proj / cash_flow_crossing_year_proj))
                            project_payback = (year_before_positive_1based_proj - 1) + fraction_proj
                        # Si le flux est nul mais le cumul devient positif pile à la fin de l'année
                        elif abs(cumulative_project_cf[first_positive_idx_proj]) < 1e-9 :
                            project_payback = float(year_before_positive_1based_proj)
            # --- FIN AJOUT INDICATEURS PROJET --- 
            # Calcul LCOE
            lcoe = None
            if wacc is not None and abs(wacc) > 1e-9: # Nécessite WACC
                 # Flux pour LCOE : Investissement initial Net Subvention, OPEX annuels
                 # Production annuelle (kWh)
                 lcoe_cash_flows = np.concatenate(([-capex_net_subvention], -arrays["opex"]))
                 lcoe_discounted_costs = npf.npv(wacc, lcoe_cash_flows)
                 lcoe_discounted_production = npf.npv(wacc, np.concatenate(([0], arrays["annual_production"])))
                 if abs(lcoe_discounted_production) > 1e-6:
                      lcoe = -lcoe_discounted_costs / lcoe_discounted_production
            # Calcul taux autoconsommation / autoproduction moyens
            total_production = np.sum(arrays["annual_production"])
            total_consumption = np.sum(arrays["annual_consumption"])
            total_autoconsumption = np.sum(arrays["annual_autoconsumption"])
            autoconsumption_rate = (total_autoconsumption / total_consumption) if total_consumption > 1e-6 else 0.0
            autoproduction_rate = (total_autoconsumption / total_production) if total_production > 1e-6 else 0.0
            # --- Construction dictionnaire résultats --- 
            results = {
                "scenario": scenario_name, "prix_revente": prix_vente_a_utiliser,
                "capex": capex, "equity_amount": equity_amount, "debt_amount": debt_amount,
                "total_subvention": total_subvention, "net_equity_investment": net_equity_investment,
                "autoconsumption_rate": autoconsumption_rate, "autoproduction_rate": autoproduction_rate,
                "wacc": wacc, # WACC est toujours utile
                "lcoe": lcoe,

                # Indicateurs Equity (anciennement IRR Projet, Payback etc.)
                "irr": irr_equity, # **RENOMMÉ pour clarté UI: irr = irr_equity**
                "npv": npv_equity, # **RENOMMÉ pour clarté UI: npv = npv_equity**
                "roi": roi_equity, # **RENOMMÉ pour clarté UI: roi = roi_equity**
                "payback_period": payback_equity, # **RENOMMÉ pour clarté UI: payback = payback_equity**

                # Garder les anciens noms pour rétrocompatibilité si nécessaire?
                # "irr_equity": irr_equity,
                # "npv_equity": npv_equity,
                # "roi_equity": roi_equity,
                # "payback_equity": payback_equity,

                # Indicateurs Projet (Nouveaux)
                "irr_project": project_irr,
                "payback_project": project_payback,

                "avg_dscr": avg_dscr,
                "years": years.tolist(),
                "cash_flows_for_irr_npv": equity_cash_flows_for_irr.tolist(), # Garder les flux Equity ici par défaut
                "project_cash_flows_detail": project_cash_flows.tolist(), # Ajouter les flux projet si besoin
                "source_prix_autoconso_utilisee": source_prix_autoc
            }
            # Ajouter les tableaux annuels
            for key, arr in arrays.items(): results[key] = arr.tolist()

            end_time_calc = time.time()
            print(f"MOTEUR: Indicateurs calculés pour '{scenario_name}' en {end_time_calc - start_time_calc:.3f} sec.")
            return results

        except (ValueError, TypeError) as e:
             print(f"ERREUR MOTEUR (calculate_financial_indicators) pour '{scenario_name}': {e}")
             raise e
        except Exception as e:
             print(f"ERREUR MOTEUR INATTENDUE (calculate_financial_indicators): {e}")
             print(traceback.format_exc())
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