import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
import traceback
import sys
import copy
from scipy.optimize import minimize

# Gestion de la dépendance à numpy_financial
try:
    import numpy_financial as npf
    NPF_IS_REAL = True
except ImportError:
    NPF_IS_REAL = False
    
    def secours_npv(rate, values):
        """Fonction de secours pour NPV si numpy_financial n'est pas disponible."""
        values = np.asarray(values)
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



class AnalysisModule:
    """Module d'analyse économique pour l'optimisation de l'autoconsommation collective."""
    
    def __init__(self):
        """Initialise l'état de session pour ce module."""
        keys_to_initialize = {
            'economic_results': {},
            'optimization_results': {},
            'monte_carlo_results': {},
            'target_price_results': {}, 
            'last_config_state': {},  
            'config_version': 0     
        }
        for key, default_value in keys_to_initialize.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
        
        # Avertir si packages manquants mais une seule fois
        if 'npf_warning_shown' not in st.session_state and not NPF_IS_REAL:
            st.toast("Package numpy_financial manquant, fonctions secours utilisées.", icon="⚠️")
            st.session_state.npf_warning_shown = True

    def calculate_wacc(self, debt_ratio, taux_interet_dette_pct, taux_imposition_pct, cout_fonds_propres_pct):
        """
        Calcule le WACC (Weighted Average Cost of Capital).
        
        Args:
            debt_ratio: Ratio dette/total (entre 0 et 1)
            taux_interet_dette_pct: Taux d'intérêt de la dette en pourcentage
            taux_imposition_pct: Taux d'imposition en pourcentage
            cout_fonds_propres_pct: Coût des fonds propres en pourcentage
            
        Returns:
            float: WACC calculé ou None en cas d'erreur
        """
        try:
            rd = float(taux_interet_dette_pct) / 100.0
            tc = float(taux_imposition_pct) / 100.0
            re = float(cout_fonds_propres_pct) / 100.0
            dr = float(debt_ratio)
            
            if not (0 <= dr <= 1): 
                raise ValueError("Debt ratio doit être entre 0 et 1")
            if not (0 <= tc < 1): 
                raise ValueError("Taux imposition doit être entre 0 et 100%")
                
            cout_dette_apres_impots = rd * (1.0 - tc)
            equity_ratio = 1.0 - dr
            wacc = (dr * cout_dette_apres_impots) + (equity_ratio * re)
            return wacc
        except (TypeError, ValueError) as e:
            st.error(f"Erreur calcul WACC: {e}")
            return None

    def calculate_financial_indicators(self, scenario_name, prix_revente=None, override_source_prix_autoconso=None):
        """
        Calcule les indicateurs financiers pour un scénario donné.
        
        Args:
            scenario_name: Nom du scénario à analyser
            prix_revente: Prix de revente spécifique (si None, utilise celui de la config)
            override_source_prix_autoconso: Si fourni, remplace la valeur de config['source_prix_autoconso']
            
        Returns:
            dict: Dictionnaire contenant tous les indicateurs financiers calculés
        """
        # Décommenter pour activer le timing
        start_time_calc = time.time() 
        # print(f"Calcul indicateurs pour: Scénario='{scenario_name}', Prix={prix_revente}, Override={override_source_prix_autoconso}")

        try:
            # Vérifications initiales
            if 'processed_data' not in st.session_state or st.session_state.processed_data is None or st.session_state.processed_data.empty:
                raise ValueError("Données traitées non disponibles.")

            if not isinstance(st.session_state.get('scenarios'), dict) or scenario_name not in st.session_state.scenarios:
                raise ValueError(f"Scénario '{scenario_name}' invalide.")

            if not isinstance(st.session_state.get('config'), dict):
                raise ValueError("Configuration invalide.")

            data = st.session_state.processed_data.copy()
            scenario = st.session_state.scenarios[scenario_name]
            config = st.session_state.config

            # Validation des paramètres config nécessaires
            required_keys = [
                "date_debut_ppa", "duree_ppa", "taux_inflation", "taux_imposition",
                "prix_vente_initial", "capex", "opex", "degradation_rate", "puissance_kwc",
                "cout_fonds_propres", "with_loan", "tarif_oa", "tarif_edf_reference",
                "tarif_oa_indexe_inflation", "taux_inflation_tarif_oa",
                "amortissement_duree", "valeur_residuelle_pct",
                "cout_demantelement_pct", "source_prix_autoconso",
                # Assurer que les clés de subvention utilisées sont là
                "subvention_rate_le3", "subvention_rate_le9", "subvention_rate_le36",
                "subvention_rate_le100", "subvention_rate_gt100" # Ajouter gt100 utilisé plus bas
            ]
            
            loan_keys = ["debt_ratio", "debt_term_years", "taux_interet_dette", "target_dscr"] 
            
            missing_keys = [k for k in required_keys if config.get(k) is None]
            loan_active = config.get("with_loan", True)
            
            if loan_active:
                missing_keys.extend([k for k in loan_keys if config.get(k) is None])

            if missing_keys: 
                raise ValueError(f"Paramètres manquants: {', '.join(missing_keys)}")

            # Récupération et conversion des paramètres
            try:
                simulation_years = int(config["duree_ppa"] / 12)
                if simulation_years <= 0: 
                    raise ValueError("Durée PPA doit être positive.")
                    
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
                
                # --- Modification ici --- 
                source_prix_autoc_config = config.get("source_prix_autoconso", "prix_initial")
                # Utiliser l'override s'il est fourni, sinon la valeur de la config
                source_prix_autoc = override_source_prix_autoconso if override_source_prix_autoconso is not None else source_prix_autoc_config
                if override_source_prix_autoconso is not None:
                     print(f"DEBUG CALC: source_prix_autoconso surchargé à '{override_source_prix_autoconso}' pour ce calcul.")
                # --- Fin Modification --- 
                
                tarif_edf_ref = float(config.get("tarif_edf_reference", 0.21))
                tarif_oa_base = float(config.get('tarif_oa', 0.0))
                taux_imposition_pct = float(config["taux_imposition"])
                taux_imposition = taux_imposition_pct / 100.0
                amortissement_duree = int(config.get("amortissement_duree", 15))
                
                if amortissement_duree <= 0: 
                    raise ValueError("Durée amortissement doit être positive.")
                    
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
                raise ValueError(f"Erreur paramètre: {e}")

            # Application des modificateurs du scénario
            try:
                capex = capex_base * float(scenario.get("capex_modifier", 1.0))
                opex_annual = opex_base * float(scenario.get("opex_modifier", 1.0))
                adjusted_inflation = taux_inflation * float(scenario.get("inflation_modifier", 1.0))
                degradation_rate = degradation_rate_base * float(scenario.get("degradation_modifier", 1.0))
                production_modifier = float(scenario.get("production_modifier", 1.0))
            except (ValueError, TypeError) as e:
                raise ValueError(f"Erreur modificateurs scénario '{scenario_name}': {e}")

            # Calcul des subventions
            rate_le3 = float(config.get("subvention_rate_le3", 0.0))
            rate_le9 = float(config.get("subvention_rate_le9", 0.0))
            rate_le36 = float(config.get("subvention_rate_le36", 0.0))
            rate_le100 = float(config.get("subvention_rate_le100", 0.0))
            rate_gt100 = float(config.get("subvention_rate_gt100", 0.0))
            
            applicable_sub_rate = 0.0
            if puissance_kwc <= 3: 
                applicable_sub_rate = rate_le3
            elif puissance_kwc <= 9: 
                applicable_sub_rate = rate_le9
            elif puissance_kwc <= 36: 
                applicable_sub_rate = rate_le36
            elif puissance_kwc <= 100: 
                applicable_sub_rate = rate_le100
            else: 
                applicable_sub_rate = rate_gt100
                
            total_subvention = applicable_sub_rate * puissance_kwc

            # Calculs financiers de base
            equity_ratio = 1.0 - debt_ratio
            debt_amount = capex * debt_ratio
            equity_amount = capex * equity_ratio
            capex_net_subvention = max(0, capex - total_subvention) 
            net_equity_investment = equity_amount - total_subvention

            # Préparation des données énergétiques
            required_data_cols = ['Temps', 'production_kwh', 'consumption_kwh']
            if not all(col in data.columns for col in required_data_cols):
                raise ValueError(f"Colonnes manquantes: {set(required_data_cols) - set(data.columns)}")
                
            data['year'] = data['Temps'].dt.year
            reference_data = data[data['year'] == data['year'].min()].copy() 
            
            if reference_data.empty: 
                raise ValueError("Aucune donnée de référence.")
                
            ref_prod = reference_data['production_kwh'].values
            ref_cons = reference_data['consumption_kwh'].values

            # Initialisation des tableaux de résultats annuels
            years = np.arange(1, simulation_years + 1)
            arrays = {name: np.zeros(simulation_years) for name in [
                "annual_production", "annual_consumption", "annual_autoconsumption", "annual_surplus",
                "revenues", "opex", "depreciation", "ebitda", "ebit", "interest_paid", "ebt", 
                "taxes", "net_income", "principal_paid", "debt_service", "free_cash_flow", 
                "cumulative_cash_flow", "dscr" 
            ]}

            # Calcul de l'amortissement annuel
            base_amortissable = capex_net_subvention * (1 - valeur_residuelle_pct)
            if amortissement_duree > 0:
                annual_depreciation_amount = base_amortissable / amortissement_duree
                for i in range(min(simulation_years, amortissement_duree)):
                    arrays["depreciation"][i] = annual_depreciation_amount
            
            # Calcul de l'échéancier de dette
            annual_debt_payment = 0.0
            if loan_active and abs(debt_amount) > 1e-6 and debt_term_years > 0:
                if abs(taux_interet_dette) < 1e-9:
                    annual_debt_payment = debt_amount / debt_term_years if debt_term_years > 0 else 0
                else:
                    try:
                        factor = (1 + taux_interet_dette) ** debt_term_years
                        denom = factor - 1
                        if abs(denom) < 1e-9: 
                            raise ValueError("Dénominateur annuité proche de zéro")
                        annual_debt_payment = debt_amount * taux_interet_dette * factor / denom
                        if not np.isfinite(annual_debt_payment): 
                            raise ValueError("Annuité non finie")
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

            # Boucle principale de calcul annuel
            for idx, year_num in enumerate(years):
                # Production / Consommation / Autoconsommation / Surplus
                degradation_factor = (1 - degradation_rate) ** (year_num - 1)
                current_production = ref_prod * degradation_factor * production_modifier
                current_consumption = ref_cons 
                autoconsumption_hourly = np.minimum(current_production, current_consumption)
                surplus_hourly = current_production - autoconsumption_hourly
                
                arrays["annual_production"][idx] = current_production.sum()
                arrays["annual_consumption"][idx] = current_consumption.sum() 
                arrays["annual_autoconsumption"][idx] = autoconsumption_hourly.sum()
                arrays["annual_surplus"][idx] = surplus_hourly.sum()

                # Revenus
                inflation_factor = (1 + adjusted_inflation) ** (year_num - 1)
                
                if source_prix_autoc == "tarif_edf": 
                    prix_achat_evite = tarif_edf_ref * inflation_factor
                    # Si l'autoconsommation est valorisée à EDF, le surplus reste à OA
                    tarif_oa_year = tarif_oa_base * ((1 + inflation_rate_oa) ** (year_num - 1) if oa_indexed else 1)
                elif source_prix_autoc == "tarif_oa":
                    tarif_oa_year = tarif_oa_base * ((1 + inflation_rate_oa) ** (year_num - 1) if oa_indexed else 1)
                    prix_achat_evite = tarif_oa_year
                else: # Cas "prix_initial" (ou l'override)
                    prix_achat_evite = prix_vente_a_utiliser * inflation_factor 
                    # Dans ce cas aussi, par défaut, le surplus reste à OA
                    tarif_oa_year = tarif_oa_base * ((1 + inflation_rate_oa) ** (year_num - 1) if oa_indexed else 1)
                    
                # --------- AJOUT MODIF ICI ------------- 
                # Si on a spécifiquement demandé d'utiliser "prix_initial" via l'override 
                # (typiquement pour la recherche VAN=0 où on veut P sur toute la production)
                # alors on applique aussi ce prix au surplus.
                if override_source_prix_autoconso == "prix_initial":
                    tarif_oa_year = prix_vente_a_utiliser * inflation_factor 
                    print(f"DEBUG CALC: Override 'prix_initial' actif, tarif OA forcé à {tarif_oa_year:.4f} pour année {year_num}") # Log
                # -------------------------------------
                    
                revenus_autoconsommation = arrays["annual_autoconsumption"][idx] * prix_achat_evite
                revenus_surplus = arrays["annual_surplus"][idx] * tarif_oa_year
                arrays["revenues"][idx] = revenus_autoconsommation + revenus_surplus

                # OPEX et coûts de démantèlement
                arrays["opex"][idx] = opex_annual * inflation_factor 
                if year_num == simulation_years:
                    cout_demantelement_final = capex_base * cout_demantelement_pct 
                    arrays["opex"][idx] += cout_demantelement_final 

                # Calcul du P&L
                arrays["ebitda"][idx] = arrays["revenues"][idx] - arrays["opex"][idx]
                arrays["ebit"][idx] = arrays["ebitda"][idx] - arrays["depreciation"][idx] 
                arrays["ebt"][idx] = arrays["ebit"][idx] - arrays["interest_paid"][idx] 
                arrays["taxes"][idx] = max(0, arrays["ebt"][idx] * taux_imposition)
                arrays["net_income"][idx] = arrays["ebt"][idx] - arrays["taxes"][idx]

                # Calcul du flux de trésorerie
                arrays["free_cash_flow"][idx] = arrays["net_income"][idx] + arrays["depreciation"][idx] - arrays["principal_paid"][idx]

            # Calcul du flux cumulé
            if simulation_years > 0:
                # --- CORRECTION PAYBACK CUMULATIVE FLOW --- 
                # Le CF cumulé doit commencer par FCF1-CF0, FCF1+FCF2-CF0 etc.
                # On le calcule correctement ici
                arrays["cumulative_cash_flow"][0] = arrays["free_cash_flow"][0] - net_equity_investment
                for i in range(1, simulation_years):
                    arrays["cumulative_cash_flow"][i] = arrays["cumulative_cash_flow"][i-1] + arrays["free_cash_flow"][i]
                # --- FIN CORRECTION --- 

            # Calcul du DSCR
            cfads = arrays["ebitda"] - arrays["taxes"]
            dscr = np.full_like(arrays["debt_service"], float('inf')) 
            mask = arrays["debt_service"] > 1e-9
            np.divide(cfads, arrays["debt_service"], out=dscr, where=mask)
            arrays["dscr"] = dscr 

            # Calcul TRI/VAN et autres indicateurs
            # ---- CORRECTION NPV ----
            # Investissement initial (t=0), ne doit pas être actualisé par npf.npv
            initial_investment_cf0 = net_equity_investment 
            # Flux de trésorerie annuels (t=1 à N)
            yearly_flows = arrays["free_cash_flow"] 
            
            # L'IRR a besoin du flux t=0 DANS la série
            cash_flows_for_irr = np.concatenate(([-initial_investment_cf0], yearly_flows))
            
            # La NPV est calculée en séparant le t=0
            # npv = -CF0 + sum(CF_t / (1+rate)^t for t=1 to N)
            npv = 0.0 # Valeur par défaut
            wacc = self.calculate_wacc(debt_ratio, taux_interet_dette_pct, taux_imposition_pct, cout_fonds_propres_pct)
            discount_rate_npv = cout_fonds_propres # On actualise les flux pour les fonds propres au coût des FP
            
            try:
                 # Calcul de la somme des flux actualisés de t=1 à N
                 pv_yearly_flows = npf.npv(discount_rate_npv, yearly_flows)
                 # Gérer le cas où pv_yearly_flows n'est pas fini (ex: rate=-1)
                 pv_yearly_flows = pv_yearly_flows if np.isfinite(pv_yearly_flows) else 0.0 
                 # Calcul final de la NPV
                 npv = -initial_investment_cf0 + pv_yearly_flows
                 npv = npv if np.isfinite(npv) else 0.0 # Assurer que NPV est finie
            except Exception as e_npv:
                 print(f"AVERTISSEMENT: Calcul NPV a échoué - {e_npv}")
                 npv = 0.0 # Ou une autre valeur indiquant l'erreur
            # ---- FIN CORRECTION NPV ----

            # Indicateurs économiques
            irr = None
            # npv est calculé ci-dessus
            roi = 0.0
            payback_period = float('inf')
            avg_dscr = float('inf')
            lcoe = None
            
            # TRI (utilise cash_flows_for_irr qui inclut t=0)
            try:
                irr = npf.irr(cash_flows_for_irr)
                irr = irr if np.isfinite(irr) else None
            except Exception:
                # En cas d'échec de npf.irr, on peut laisser irr à None ou tenter une alternative
                pass 
            
            # WACC et VAN (VAN a déjà été calculée)
            # wacc = self.calculate_wacc(debt_ratio, taux_interet_dette_pct, taux_imposition_pct, cout_fonds_propres_pct)
            # (la variable wacc est utilisée plus bas pour le LCOE)

            # ROI
            if abs(initial_investment_cf0) > 1e-9: 
                roi = npv / initial_investment_cf0 # Utilise la NPV corrigée
                roi = roi if np.isfinite(roi) else 0.0 
            elif initial_investment_cf0 <= 0: # Cas où la subvention couvre tout ou plus
                 # Si investissement nul ou négatif, ROI est conceptuellement infini si NPV>0
                 roi = float('inf') if npv > 0 else (-float('inf') if npv < 0 else 0)

            # Période de récupération (utilise cumulative_cash_flow)
            # Le calcul précédent de cumulative_cash_flow était correct pour le payback
            if simulation_years > 0:
                # On rajoute le point 0 (-CF0) à la série pour la recherche d'index
                cum_cf_corrected_for_payback = np.concatenate(([-initial_investment_cf0], arrays["cumulative_cash_flow"]))
                positive_indices = np.where(cum_cf_corrected_for_payback >= -1e-9)[0] 
                if len(positive_indices) > 0:
                    first_positive_idx = positive_indices[0] 
                    if first_positive_idx == 0:
                        # Remboursé en année 0 (cas très rare, subvention > capex?)
                        payback_period = 0.0
                    else:
                        # Année (base 1) avant de devenir positif
                        year_before_positive_1based = first_positive_idx 
                        last_negative_cum_cf = cum_cf_corrected_for_payback[first_positive_idx - 1]
                        cash_flow_crossing_year = arrays["free_cash_flow"][first_positive_idx - 1] # FCF de l'année t où ça devient positif
                        if cash_flow_crossing_year > 1e-9: 
                            fraction = -last_negative_cum_cf / cash_flow_crossing_year
                            # Assurer que la fraction est raisonnable (0-1)
                            fraction = max(0.0, min(1.0, fraction))
                            payback_period = (year_before_positive_1based - 1) + fraction 
                        else: 
                            # Si le FCF de l'année est nul ou négatif, on ne traverse pas vraiment
                            # On prend l'année entière si la NPV est exactement 0 à cet index
                            if abs(cum_cf_corrected_for_payback[first_positive_idx]) < 1e-9:
                                payback_period = float(year_before_positive_1based) 
                            else:
                                 payback_period = float('inf') 
            
            # DSCR moyen
            if loan_active and debt_term_years > 0:
                dscr_term_indices = np.arange(min(simulation_years, int(debt_term_years)))
                if len(dscr_term_indices) > 0:
                    dscr_in_term = arrays["dscr"][dscr_term_indices]
                    # Filtrer les infinis avant la moyenne
                    dscr_finite_in_term = dscr_in_term[np.isfinite(dscr_in_term)]
                    if len(dscr_finite_in_term) > 0: 
                        avg_dscr = np.mean(dscr_finite_in_term)

            # Taux d'autoconsommation et d'autoproduction
            total_annual_production = arrays["annual_production"].sum()
            total_annual_consumption = arrays["annual_consumption"].sum() 
            total_annual_autoconsumption = arrays["annual_autoconsumption"].sum()
            
            autoconsumption_rate = total_annual_autoconsumption / total_annual_production if total_annual_production > 1e-9 else 0
            autoproduction_rate = total_annual_autoconsumption / total_annual_consumption if total_annual_consumption > 1e-9 else 0

            # LCOE
            if wacc is not None and abs(wacc - (-1.0)) > 1e-9:
                try:
                    # Actualiser la production annuelle avec le WACC
                    discount_factors_prod = (1 + wacc) ** np.arange(1, simulation_years + 1)
                    valid_factors_prod = discount_factors_prod != 0
                    discounted_production = arrays["annual_production"][valid_factors_prod] / discount_factors_prod[valid_factors_prod]
                    total_discounted_production = np.sum(discounted_production)
                    
                    # Actualiser les OPEX annuels avec le WACC
                    discount_factors_opex = (1 + wacc) ** np.arange(1, simulation_years + 1)
                    valid_factors_opex = discount_factors_opex != 0
                    discounted_opex = arrays["opex"][valid_factors_opex] / discount_factors_opex[valid_factors_opex]
                    total_discounted_opex = np.sum(discounted_opex)

                    # --- AJOUT DEBUG LCOE --- 
                    print(f"DEBUG LCOE CALC INPUTS: debt_ratio={debt_ratio:.2f}, capex_net_subvention={capex_net_subvention:.2f}, total_discounted_opex={total_discounted_opex:.2f}, wacc={wacc:.4f}")
                    # --- FIN AJOUT DEBUG --- 

                    # --- CORRECTION LCOE BASE COST ---
                    # Coût total actualisé = CAPEX NET SUBVENTION (t=0) + OPEX actualisés (t=1 à N)
                    total_discounted_costs = capex_net_subvention + total_discounted_opex 
                    # --- FIN CORRECTION ---

                    if abs(total_discounted_production) > 1e-9:
                        lcoe = total_discounted_costs / total_discounted_production
                        if not np.isfinite(lcoe): 
                            lcoe = None
                    else:
                         lcoe = None # Production actualisée nulle
                except Exception as e_lcoe:
                    print(f"Avertissement: Calcul LCOE a échoué - {e_lcoe}")
                    lcoe = None

            # Construction du dictionnaire de résultats
            # Assurer que cash_flows_for_irr_npv contient bien le t=0 pour l'IRR
            results = {
                "scenario": scenario_name,
                "prix_revente": prix_vente_a_utiliser,
                "capex": capex, 
                "equity_amount": equity_amount,
                "debt_amount": debt_amount,
                "total_subvention": total_subvention, 
                "net_equity_investment": net_equity_investment,
                "autoconsumption_rate": autoconsumption_rate,
                "autoproduction_rate": autoproduction_rate,
                "irr": irr,
                "wacc": wacc,
                "npv": npv, # Utilise la NPV corrigée
                "roi": roi if np.isfinite(roi) else None,
                "payback_period": payback_period if np.isfinite(payback_period) else None,
                "avg_dscr": avg_dscr if np.isfinite(avg_dscr) else None,
                "lcoe": lcoe, 
                "years": years.tolist(),
                "cash_flows_for_irr_npv": cash_flows_for_irr.tolist() # Garder le flux t=0 ici pour l'IRR
            }
            
            # Ajouter les tableaux annuels
            for key, arr in arrays.items():
                results[key] = arr.tolist()
                
            # Décommenter pour activer le timing
            print(f"Calcul terminé avec succès en {time.time() - start_time_calc:.2f}s.") 
            return results

        except Exception as e:
            # Log plus détaillé en cas d'erreur
            st.error(f"Erreur majeure dans les calculs pour scénario '{scenario_name}' et prix {prix_revente}: {str(e)}")
            print(f"ERREUR CALC DETAILED: Scénario='{scenario_name}', Prix={prix_revente}, Override={override_source_prix_autoconso}")
            print(f"Exception: {type(e).__name__}: {e}")
            print(traceback.format_exc())
            return None

    # --- Méthode pour simuler prix cible (restaurée) ---
    def simulate_selling_price(self, scenario_name, target_irr=None, target_npv=None):
        """Trouve le prix pour atteindre un TRI ou VAN cible."""
        print(f"DEBUG simulate_selling_price: scenario={scenario_name}, target_irr={target_irr}, target_npv={target_npv}")
        try:
            if target_irr is None and target_npv is None:
                raise ValueError("Veuillez spécifier un TRI ou une VAN cible")

            config = st.session_state.config
            prix_min_config = float(config.get('prix_min_revente', 0.05))
            prix_max_config = float(config.get('prix_max_revente', 0.40))
            if prix_min_config >= prix_max_config:
                 prix_min_config = 0.05
                 prix_max_config = 0.40
                 st.warning(f"Plage de prix invalide dans config, utilisation de [{prix_min_config}, {prix_max_config}]")

            # Nouveau bloc VAN=0 analytique (LCOE)
            if target_npv is not None and abs(target_npv) < 1e-9:
                # 1) on récupère production, OPEX, WACC et CAPEX net-subvention
                base = self.calculate_financial_indicators(
                    scenario_name,
                    prix_revente=config.get('prix_vente_initial'),
                    override_source_prix_autoconso="prix_initial"
                )
                if not base:
                    st.error("Impossible de calculer les bases pour le prix plancher.")
                    return None

                # >>> récupérer dans `base` :
                capex_net   = base['capex'] - base['total_subvention']
                wacc        = base['wacc']
                auto        = base['annual_autoconsumption']  # liste de N années
                surplus     = base['annual_surplus']         # idem
                opex        = base['opex']                   # idem
                # tarif OA (non actualisé) + son inflation
                tarif_oa_0  = config.get('tarif_oa', 0.0) # Utiliser config.get pour sécurité
                infl_oa     = (config.get('taux_inflation_tarif_oa', 0.0)/100) if config.get('tarif_oa_indexe_inflation', False) else 0

                # Ajout vérifications robustesse
                if wacc is None or not isinstance(auto, list) or not isinstance(surplus, list) or not isinstance(opex, list) or not auto or len(auto) != len(surplus) or len(auto) != len(opex):
                    st.error("Données invalides (WACC, auto, surplus, opex) pour le calcul analytique.")
                    return None
                if abs(wacc - (-1.0)) < 1e-9:
                    st.error("WACC invalide (proche de -100%) pour l'actualisation.")
                    return None

                N = len(auto)
                try:
                    dfs = [(1 + wacc) ** (t+1) for t in range(N)]
                    if any(abs(df) < 1e-12 for df in dfs):
                         st.error("Facteur d'actualisation proche de zéro.")
                         return None
                    # Sommes actualisées :
                    discounted_auto       = sum(auto[t]    / dfs[t] for t in range(N))
                    discounted_opex       = sum(opex[t]    / dfs[t] for t in range(N))
                    discounted_surplus_rev= sum(
                        surplus[t] * tarif_oa_0 * (1+infl_oa)**t  # tarif OA évolué
                        / dfs[t]
                        for t in range(N)
                    )
                except (OverflowError, ZeroDivisionError, ValueError) as e:
                     st.error(f"Erreur d'actualisation LCOE: {e}")
                     return None

                # nouveau prix plancher analytique
                if abs(discounted_auto) < 1e-9:
                    st.error("Autoconsommation actualisée nulle, calcul prix plancher impossible.")
                    return None
                prix_plancher = (
                    capex_net
                  + discounted_opex
                  - discounted_surplus_rev
                ) / discounted_auto
                print(f"Prix plancher analytique (formule modifiée) calculé: {prix_plancher:.6f}")

                # 4) on recalcule les indicateurs finaux avec ce prix
                print(f"Recalcul indicateurs au prix plancher = {prix_plancher:.6f}")
                final = self.calculate_financial_indicators(
                    scenario_name,
                    prix_revente=prix_plancher,
                    override_source_prix_autoconso="prix_initial"
                )
                if final:
                    final['prix_revente_optimal_pour_cible'] = prix_plancher
                    final['target_npv_asked'] = 0.0
                    final['target_irr_asked'] = None # Clarification: pas de cible IRR pour ce calcul
                    print("Calcul analytique et recalcul final OK.")
                else:
                     st.error(f"Échec recalcul final au prix plancher {prix_plancher:.6f}")
                     # Retourner un dict minimal avec le prix trouvé si le recalcul échoue
                     return {
                         'prix_revente_optimal_pour_cible': prix_plancher,
                         'target_npv_asked': 0.0,
                         'target_irr_asked': None,
                         'warning': 'Recalcul final indicateurs a échoué'
                     }
                return final

            # --- AUTRES CAS (IRR ou VAN != 0) : Utilisation de minimize ---
            else:
                print("INFO: Cible IRR ou VAN != 0. Utilisation de l'algorithme minimize (L-BFGS-B / Nelder-Mead).")
                # Fonction objectif pour l'optimisation (retourne la différence absolue)
                iteration_count = 0 
                def objective_function(price):
                    nonlocal iteration_count
                    iteration_count += 1
                    
                    # --- Correction TypeError --- 
                    # Assurer que current_price est un scalaire pour le formatage
                    current_price_scalar = price[0] if isinstance(price, (np.ndarray, list)) else price
                    print(f"  [Optim Step {iteration_count}] Testing price: {current_price_scalar:.6f}")
                    # --- Fin Correction --- 
                    
                    # Pas d'override ici, on utilise la config normale
                    results = self.calculate_financial_indicators(scenario_name, prix_revente=current_price_scalar)

                    if not results:
                        print(f"    -> Échec calcul indicateurs pour prix={current_price_scalar} dans objective_function")
                        return 1e10

                    if target_irr is not None:
                        irr_value = results.get('irr')
                        if irr_value is None:
                            print(f"    -> IRR est None pour prix={current_price_scalar}")
                            return 1e9
                        target_irr_decimal = target_irr / 100.0 if target_irr > 1 else target_irr
                        diff = abs(irr_value - target_irr_decimal)
                        print(f"    -> IRR = {irr_value:.6f}, Target = {target_irr_decimal:.6f}, Diff = {diff:.6f}")
                        return diff
                    else: # target_npv est utilisé (mais != 0)
                        npv_value = results.get('npv')
                        if npv_value is None:
                             print(f"    -> NPV est None pour prix={current_price_scalar}")
                             return 1e9
                        diff = abs(npv_value - target_npv)
                        print(f"    -> NPV = {npv_value:,.2f}, Target = {target_npv:,.2f}, Diff = {diff:,.2f}")
                        return diff

                initial_price_guess = config.get('prix_vente_initial', (prix_min_config + prix_max_config) / 2)
                initial_price_guess = max(prix_min_config, min(prix_max_config, initial_price_guess))
                print(f"Starting optimization with initial guess: {initial_price_guess:.6f}")
                
                bounds = [(prix_min_config, prix_max_config)] # Utilise les bornes config
                
                print("Attempting optimization with L-BFGS-B...")
                result = minimize(objective_function, [initial_price_guess], method='L-BFGS-B', bounds=bounds, options={'ftol': 1e-7, 'gtol': 1e-6})
                print(f"L-BFGS-B result raw: {result}")

                optimal_price = None
                if result.success and bounds[0][0] <= result.x[0] <= bounds[0][1]:
                     optimal_price = result.x[0]
                     print(f"Optimisation L-BFGS-B successful. Price found: {optimal_price:.6f}")
                else:
                    print(f"Optimisation L-BFGS-B failed (success={result.success}). Message: {result.message}. Attempting with Nelder-Mead...")
                    iteration_count = 0 
                    def objective_wrapper_nelder(price_scalar):
                         if not (bounds[0][0] <= price_scalar <= bounds[0][1]):
                              print(f"  [Optim Step NM] Price {price_scalar:.6f} out of bounds [{bounds[0][0]}, {bounds[0][1]}]")
                              return 1e12 
                         # --- Correction: Utiliser la version corrigée d'objective_function --- 
                         return objective_function(price_scalar) 
                         # --- Fin Correction --- 

                    print("Attempting optimization with Nelder-Mead...")
                    result_nm = minimize(objective_wrapper_nelder, initial_price_guess, method='Nelder-Mead', options={'xatol': 1e-5, 'fatol': 1e-6})
                    print(f"Nelder-Mead result raw: {result_nm}")

                    if result_nm.success and bounds[0][0] <= result_nm.x[0] <= bounds[0][1]:
                        optimal_price = result_nm.x[0]
                        print(f"Optimisation Nelder-Mead successful. Price found: {optimal_price:.6f}")
                    else:
                        print(f"Optimisation Nelder-Mead failed too (success={result_nm.success}). Message: {result_nm.message}")
                        st.error("Impossible de converger vers un prix cible.")
                        return None

            # --- Fin du bloc minimize --- 

            # Vérification finale si optimal_price a été trouvé
            if optimal_price is None:
                 st.error("Aucun prix optimal trouvé après les tentatives d'optimisation/recherche de racine.")
                 return None

            # Calcul final des indicateurs avec le prix optimal trouvé
            # Pour VAN=0, on rappelle avec l'override pour être sûr d'avoir les bons indicateurs associés au prix plancher
            final_source_override = "prix_initial" if (target_npv is not None and abs(target_npv) < 1e-9) else None
            print(f"Recalculating final indicators with optimal price = {optimal_price:.6f}, source_override={final_source_override}")
            final_results = self.calculate_financial_indicators(scenario_name, 
                                                            prix_revente=optimal_price, 
                                                            override_source_prix_autoconso=final_source_override)
            
            if final_results:
                final_results['prix_revente_optimal_pour_cible'] = optimal_price
                final_results['target_irr_asked'] = target_irr
                final_results['target_npv_asked'] = target_npv
                print("Simulation de prix cible terminée avec succès.")
                return final_results
            else:
                st.error(f"Échec du calcul final des indicateurs avec le prix optimal trouvé {optimal_price}.")
                return None
                
        except Exception as e:
            st.error(f"Erreur majeure lors de la simulation du prix cible : {str(e)}")
            print(f"ERREUR simulate_selling_price: {e}\n{traceback.format_exc()}")
            return None

    def _eval_price_solution(self, scenario_name, prix):
        """
        Évalue les indicateurs financiers pour un prix donné.
        
        Args:
            scenario_name: Nom du scénario
            prix: Prix à évaluer
            
        Returns:
            dict: Résultats des indicateurs ou None si erreur
        """
        try:
            results = self.calculate_financial_indicators(scenario_name, prix_revente=prix)
            if results is None:
                # Si le calcul de base échoue, on ne peut pas évaluer
                print(f"Échec du calcul des indicateurs pour {prix} dans _eval_price_solution")
                return None
            # Ne pas retourner ici, continuer pour calculer le score
            
            # Évaluations des contraintes et du score
            tarif_edf = st.session_state.config.get('tarif_edf_reference', 0.21)
            target_dscr = st.session_state.config.get('target_dscr', 1.2)
            
            # Scores par indicateur (0-1)
            roi_score = min(1.0, max(0, results['roi'] / 0.15)) if results.get('roi') is not None else 0
            irr_score = min(1.0, max(0, results['irr'] / 0.10)) if results.get('irr') is not None else 0
            payback_score = min(1.0, max(0, (25 - results['payback_period']) / 15)) if results.get('payback_period') is not None else 0
            dscr_score = min(1.0, max(0, results['avg_dscr'] / target_dscr)) if results.get('avg_dscr') is not None and target_dscr > 0 else 0
            competitive_score = min(1.0, max(0, (tarif_edf - prix) / tarif_edf)) if tarif_edf > 0 else 0
            
            # Coefficients de pondération (pourrait être passé en argument à l'avenir)
            weights = {
                'roi': 0.25,
                'irr': 0.20,
                'payback': 0.15,
                'dscr': 0.20,
                'competitivity': 0.20
            }
            
            # Score global (0-1)
            global_score = (
                weights['roi'] * roi_score +
                weights['irr'] * irr_score +
                weights['payback'] * payback_score +
                weights['dscr'] * dscr_score +
                weights['competitivity'] * competitive_score
            )
            
            # Stockage des scores dans le résultat
            results['scores'] = {
                'roi': roi_score,
                'irr': irr_score,
                'payback': payback_score,
                'dscr': dscr_score,
                'competitive': competitive_score,
                'score_global': global_score
            }
            
            return results
            
        except Exception as e:
            st.error(f"Erreur inattendue dans _eval_price_solution pour prix {prix}: {e}")
            print(f"ERREUR _eval_price_solution: {e}\n{traceback.format_exc()}")
            return None

    def show_ui(self):
        """Affiche l'interface principale d'analyse (nouvelle version)."""
        # pass # Remplacé par le code ci-dessous
        
        st.markdown("<h2 class='sub-header'>Analyse Énergétique et Financière (UI)</h2>", unsafe_allow_html=True)
        
        # Vérifications préliminaires
        if not st.session_state.get('data_imported', False):
            st.warning("Veuillez importer des données via l'onglet 'Importation Données'.")
            return
        if not st.session_state.get('scenarios'):
            st.error("Aucun scénario défini. Vérifiez la Configuration.")
            return
        available_scenarios = list(st.session_state.scenarios.keys())
        if not available_scenarios:
            st.warning("Aucun scénario défini.")
            return

        # Sélection du scénario (commun à toute l'interface)
        st.sidebar.title("Paramètres d'Analyse")
        # Utiliser une clé d'état distincte pour cette UI
        if 'show_ui_current_scenario' not in st.session_state:
            st.session_state.show_ui_current_scenario = available_scenarios[0]
            
        scenario_index = available_scenarios.index(st.session_state.show_ui_current_scenario) if st.session_state.show_ui_current_scenario in available_scenarios else 0
        
        scenario_name = st.sidebar.selectbox(
            "Choisir le Scénario:",
            options=available_scenarios,
            index=scenario_index,
            key="show_ui_scenario_selector_widget"
        )
        # Mettre à jour l'état si la sélection change
        if scenario_name != st.session_state.show_ui_current_scenario:
            st.session_state.show_ui_current_scenario = scenario_name
            st.rerun()

        st.markdown(f"### Analyse du Scénario : **{scenario_name}**")
        st.markdown("---")
        
        # --- Section 1: Contexte Énergétique et Prix de Référence ---
        st.markdown("#### 1. Contexte Énergétique et Prix de Référence")
        with st.container(border=True):
            # st.info("Implémentation de la Section 1 à venir...") # Remplacé par le code ci-dessous
            
            # Initialiser les états pour les résultats de cette section si nécessaire
            state_key_base = f"show_ui_{scenario_name}" # Clé spécifique à cette UI
            if f"{state_key_base}_base_indicators" not in st.session_state:
                 st.session_state[f"{state_key_base}_base_indicators"] = None
            if f"{state_key_base}_floor_price_results" not in st.session_state:
                 st.session_state[f"{state_key_base}_floor_price_results"] = None

            # Bouton pour (re)lancer les calculs de référence
            if st.button("Calculer/Actualiser Références", key="show_ui_calc_ref"):
                with st.spinner("Calcul des indicateurs de base (Énergie, LCOE)..."):
                    base_indic = self.calculate_financial_indicators(scenario_name)
                    st.session_state[f"{state_key_base}_base_indicators"] = base_indic
                    if not base_indic:
                        st.warning("Échec du calcul des indicateurs de base.")
                
                with st.spinner("Calcul du prix plancher (VAN=0)..."):
                    floor_results = self.simulate_selling_price(scenario_name, target_npv=0)
                    st.session_state[f"{state_key_base}_floor_price_results"] = floor_results
                    if not floor_results:
                        st.warning("Échec du calcul du prix plancher.")
                st.rerun()

            # Récupérer les résultats depuis l'état de session
            base_indicators = st.session_state[f"{state_key_base}_base_indicators"]
            floor_price_results = st.session_state[f"{state_key_base}_floor_price_results"]

            if not base_indicators:
                st.info("Cliquez sur 'Calculer/Actualiser Références' pour afficher les données de cette section.")
            else:
                # --- Affichage --- 
                col1, col2 = st.columns([1, 2]) # Colonne pour Graphique, Colonne pour Prix Réf

                with col1:
                    st.markdown("**Répartition Énergie Annuelle Moyenne**")
                    # Calcul des totaux sur la durée
                    total_autoconsumption = sum(base_indicators.get('annual_autoconsumption', []))
                    total_surplus = sum(base_indicators.get('annual_surplus', []))
                    total_production = total_autoconsumption + total_surplus

                    if total_production > 0:
                        energy_data = pd.DataFrame({
                            'Type': ['Autoconsommation', 'Surplus Vendu'],
                            'Volume (kWh)': [total_autoconsumption, total_surplus],
                            'Pourcentage (%)': [
                                (total_autoconsumption / total_production) * 100,
                                (total_surplus / total_production) * 100
                            ]
                        })
                        
                        # Importer plotly ici si ce n'est pas déjà fait en haut du fichier
                        import plotly.express as px 
                        
                        fig_energy = px.pie(
                            energy_data, 
                            values='Volume (kWh)', 
                            names='Type', 
                            title=f"Total: {total_production:,.0f} kWh",
                            hole=0.4, # Pour un effet donut
                            color_discrete_map={'Autoconsommation':'#1f77b4', 'Surplus Vendu':'#ff7f0e'}
                        )
                        fig_energy.update_traces(
                            textinfo='percent+label', 
                            hovertemplate='<b>%{label}</b><br>Volume: %{value:,.0f} kWh<br>Pourcentage: %{percent:.1%}<extra></extra>'
                        )
                        fig_energy.update_layout(
                            showlegend=False,
                            margin=dict(t=50, b=0, l=0, r=0), # Ajuster marges
                            title_x=0.5 # Centrer titre
                            )
                        st.plotly_chart(fig_energy, use_container_width=True)
                    else:
                        st.info("Pas de production calculée.")

                with col2:
                    st.markdown("**Prix de Référence Clés**")
                    
                    # Extraire les valeurs nécessaires
                    calculated_floor_price = None
                    if floor_price_results and 'prix_revente_optimal_pour_cible' in floor_price_results:
                         calculated_floor_price = floor_price_results['prix_revente_optimal_pour_cible']
                         
                    lcoe = base_indicators.get('lcoe') 
                    edf_tariff = st.session_state.config.get('tarif_edf_reference', 0.21)

                    # Affichage des métriques
                    st.metric("Prix Plancher (VAN=0)", 
                              f"{calculated_floor_price:.4f} €/kWh" if calculated_floor_price is not None else "N/A",
                              help="Prix de vente nécessaire pour atteindre une Valeur Actuelle Nette (VAN) de 0.")
                    st.metric("LCOE", 
                              f"{lcoe:.4f} €/kWh" if lcoe is not None else "N/A",
                              help="Levelized Cost of Energy : Coût actualisé moyen de production d'un kWh sur la durée de vie du projet.")
                    st.metric("Tarif EDF Référence", 
                              f"{edf_tariff:.4f} €/kWh",
                              help="Tarif de référence d'EDF pour comparaison.")
        
        # ... (Futures sections viendront ici)

    def run_standalone_calculations(self, scenario_name):
        """
        Exécute les calculs clés pour la Section 1 et affiche les résultats.
        Utilise les données et la configuration présentes dans st.session_state.
        """
        print(f"\n--- Lancement des calculs pour le scénario : {scenario_name} ---")

        # 1. Vérification des prérequis
        if 'processed_data' not in st.session_state or st.session_state.processed_data is None or st.session_state.processed_data.empty:
            print("ERREUR: Données 'processed_data' non trouvées dans st.session_state.")
            return
        if 'config' not in st.session_state or not st.session_state.config:
            print("ERREUR: Configuration 'config' non trouvée dans st.session_state.")
            return
        if 'scenarios' not in st.session_state or scenario_name not in st.session_state.scenarios:
            print(f"ERREUR: Scénario '{scenario_name}' non trouvé dans st.session_state.scenarios.")
            return

        print("\n1. Calcul des Indicateurs Financiers de Base...")
        base_indicators = self.calculate_financial_indicators(scenario_name)

        if not base_indicators:
            print("   ERREUR: Échec du calcul des indicateurs financiers.")
            return

        # 2. Calcul et Affichage de la Répartition Énergétique
        print("\n2. Répartition Énergétique Annuelle Moyenne :")
        try:
            # Note: Les indicateurs retournés sont déjà des totaux sur la durée
            total_autoconsumption = sum(base_indicators.get('annual_autoconsumption', []))
            total_surplus = sum(base_indicators.get('annual_surplus', []))
            total_production = total_autoconsumption + total_surplus
            num_years = len(base_indicators.get('years', []))

            if total_production > 0 and num_years > 0:
                avg_annual_autoconsumption = total_autoconsumption / num_years
                avg_annual_surplus = total_surplus / num_years
                avg_annual_production = total_production / num_years
                percent_auto = (avg_annual_autoconsumption / avg_annual_production) * 100
                percent_surplus = (avg_annual_surplus / avg_annual_production) * 100

                print(f"   - Production Totale Moyenne: {avg_annual_production:,.2f} kWh/an")
                print(f"   - Autoconsommation Moyenne: {avg_annual_autoconsumption:,.2f} kWh/an ({percent_auto:.1f}%)")
                print(f"   - Surplus Vendu Moyen: {avg_annual_surplus:,.2f} kWh/an ({percent_surplus:.1f}%)")
            elif num_years == 0:
                 print("   ERREUR: Durée de simulation nulle.")
            else:
                print("   - Aucune production calculée.")
        except Exception as e:
            print(f"   ERREUR lors du calcul de la répartition énergétique: {e}")


        # 3. Calcul et Affichage des Prix de Référence
        print("\n3. Prix de Référence Clés :")
        lcoe = base_indicators.get('lcoe')
        edf_tariff = st.session_state.config.get('tarif_edf_reference', None)

        print(f"   - LCOE: {lcoe:.4f} €/kWh" if lcoe is not None else "   - LCOE: N/A")
        print(f"   - Tarif EDF Référence: {edf_tariff:.4f} €/kWh" if edf_tariff is not None else "   - Tarif EDF Référence: N/A")

        print("\n   Calcul du Prix Plancher (VAN=0)...")
        floor_price_results = self.simulate_selling_price(scenario_name, target_npv=0)
        if floor_price_results and 'prix_revente_optimal_pour_cible' in floor_price_results:
            floor_price = floor_price_results['prix_revente_optimal_pour_cible']
            print(f"   - Prix Plancher (VAN=0): {floor_price:.4f} €/kWh")
        else:
            print("   - Prix Plancher (VAN=0): Échec du calcul ou non trouvé.")

        print("\n--- Fin des calculs ---")


# --- Fin de la classe AnalysisModule ---

# Bloc d'exécution pour test standalone
if __name__ == "__main__":
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    import os
    import sys
    import traceback # Ajout import traceback

    # Ajouter le répertoire parent au path pour trouver les autres modules
    # (Nécessaire si exécuté directement depuis le dossier 'modules')
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir) # Insérer à la position 0 pour priorité


    print("Initialisation du test standalone...")

    # --- Mock de Streamlit et st.session_state ---
    class MockSessionState:
        """Classe simple pour mocker st.session_state avec accès attribut et vérification 'in'."""
        def __init__(self):
            # Utilise __dict__ pour stocker l'état, permettant l'accès par attribut
            pass 

        def __contains__(self, key):
            return hasattr(self, key)

        def __setitem__(self, key, value):
            setattr(self, key, value)

        def __getitem__(self, key):
             # Laisse getattr lever AttributeError si la clé n'existe pas
             return getattr(self, key)

        def get(self, key, default=None):
            """Simule la méthode get de st.session_state."""
            return getattr(self, key, default)

    class MockStreamlit:
        def __init__(self):
            self.session_state = MockSessionState()

        def warning(self, msg): print(f"ST.WARNING: {msg}")
        def error(self, msg): print(f"ST.ERROR: {msg}")
        def info(self, msg): print(f"ST.INFO: {msg}")
        def success(self, msg): print(f"ST.SUCCESS: {msg}")
        def toast(self, msg, icon=None): print(f"ST.TOAST [{icon}]: {msg}")
        # get n'est pas directement une méthode de st mais de session_state
        # Mais on le garde ici par sécurité si du code l'appelle sur st
        def get(self, key, default=None):
            return getattr(self.session_state, key, default)
        # Ajouter d'autres méthodes st si nécessaire par les modules

    st = MockStreamlit() # Remplace l'import streamlit pour ce bloc

    # --- Patch sys.modules pour forcer l'utilisation de notre mock st ---
    import sys
    sys.modules['streamlit'] = st
    print("sys.modules['streamlit'] patché pour utiliser le mock.")

    # --- Importer ConfigModule APRÈS avoir patché sys.modules ---
    # (On retente l'approche propre)
    print("Importation de ConfigModule (qui devrait utiliser le st moqué)...")
    try:
        from modules.config import ConfigModule
    except ImportError:
         try:
              from config import ConfigModule # Fallback si lancé depuis modules/
         except ImportError:
             print("ERREUR: Impossible d'importer ConfigModule. Assurez-vous d'être dans le dossier racine.")
             sys.exit(1)

    # --- Initialisation via ConfigModule ---
    print("Initialisation ConfigModule...")
    try:
        # L'instance devrait maintenant écrire dans notre st.session_state moqué
        config_module = ConfigModule()
        print("ConfigModule initialisé.")

        # --- MODIFICATION POUR TEST 100% EQUITY ---
        print("Modification de la config pour test 100% Equity...")
        if hasattr(st.session_state, 'config'):
             st.session_state.config['debt_ratio'] = 0.0
             st.session_state.config['with_loan'] = False
             st.session_state.config['taux_interet_dette'] = 0.0
             # Recalculer OPEX car la méthode auto dépend du CAPEX et puissance (qui n'ont pas changé)
             # et la provision onduleur (inchangée). L'opex doit rester le même qu'avec dette.
             # Si besoin, on pourrait aussi forcer l'opex à une valeur fixe ici pour le test.
             print(f"Config modifiée: debt_ratio={st.session_state.config['debt_ratio']}, with_loan={st.session_state.config['with_loan']}")
        else:
             print("ERREUR: Impossible de modifier la config car elle n'a pas été initialisée.")
             sys.exit(1)
        # --- FIN MODIFICATION --- 

        # --- DEBUG: Vérification post-ConfigModule --- 
        print("Vérification st.session_state après ConfigModule init et modif:")
        print(f"  hasattr(st.session_state, 'config'): {hasattr(st.session_state, 'config')}")
        print(f"  hasattr(st.session_state, 'scenarios'): {hasattr(st.session_state, 'scenarios')}")
        if hasattr(st.session_state, 'config') and isinstance(st.session_state.config, dict):
            print(f"  Type de st.session_state.config: {type(st.session_state.config)}")
            print(f"  Valeurs clés pour test equity: debt_ratio={st.session_state.config.get('debt_ratio')}, with_loan={st.session_state.config.get('with_loan')}") 
        elif hasattr(st.session_state, 'config'):
             print(f"  Type de st.session_state.config: {type(st.session_state.config)} (ATTENTION: Pas un dict!)")
        else:
             print(f"  st.session_state.config n'existe pas.")
        print("---------------------------------------------")
        # --- FIN DEBUG --- 

    except Exception as e:
        print(f"ERREUR lors de l'initialisation de ConfigModule: {e}")
        print(traceback.format_exc())
        sys.exit(1)

    # --- Création de Données Synthétiques 'processed_data' ---
    print("Création des données synthétiques 'processed_data'...")
    try:
        num_hours_year = 8760 # Nombre d'heures dans une année
        # Utiliser une année non bissextile fixe pour la reproductibilité
        start_date = datetime(2023, 1, 1)
        timestamps = pd.date_range(start=start_date, periods=num_hours_year, freq='h') # Utiliser 'h' au lieu de 'H' déprécié

        # Profil simple sinusoïdal pour la production (max en été, min en hiver)
        hours_in_year = np.arange(num_hours_year)
        # Ajustement pour pic en été (autour de l'heure 4380)
        production_kwh = 5 * (1 + np.sin(2 * np.pi * (hours_in_year - num_hours_year * 0.25) / num_hours_year))
        # Ajouter un peu de bruit et s'assurer que c'est positif
        production_kwh = np.maximum(0, production_kwh * np.random.uniform(0.8, 1.2, num_hours_year))

        # Profil de consommation plus plat avec un peu de variation
        consumption_kwh = 2 + np.random.normal(0, 0.5, num_hours_year)
        consumption_kwh = np.maximum(0, consumption_kwh) # Pas de consommation négative

        processed_data_df = pd.DataFrame({
            'Temps': timestamps,
            'production_kwh': production_kwh,
            'consumption_kwh': consumption_kwh
        })
        # Calcul autoconsommation (peut être fait ici ou laissé au module analysis)
        processed_data_df['autoconsumption_kwh'] = np.minimum(processed_data_df['production_kwh'], processed_data_df['consumption_kwh'])

        # Ajouter le DataFrame au session_state moqué
        st.session_state.processed_data = processed_data_df
        print(f"Données synthétiques créées ({len(processed_data_df)} lignes).")
        # print(st.session_state.processed_data.head()) # Décommenter pour débug
    except Exception as e:
         print(f"ERREUR lors de la création des données synthétiques: {e}")
         print(traceback.format_exc())
         sys.exit(1)

    # --- Instanciation et Exécution AnalysisModule ---
    print("Instanciation AnalysisModule...")
    try:
        # L'instance utilisera le st.session_state moqué
        analysis_module = AnalysisModule()
        print("AnalysisModule instancié.")

        # Appel de la fonction de calcul principale
        analysis_module.run_standalone_calculations(scenario_name='Base')

        # --- Test de Sensibilité Manuel NPV vs Prix ---
        print("\n--- Test de Sensibilité Manuel NPV vs Prix ---")
        price1 = 0.17 # Utiliser une valeur fixe pour ce test
        price2 = 0.16 # Utiliser une valeur fixe pour ce test
        print(f"Calcul NPV pour Prix 1 = {price1:.4f}...")
        # Recalculer avec override pour voir la sensibilité du NPV equity
        results1 = analysis_module.calculate_financial_indicators('Base', prix_revente=price1, override_source_prix_autoconso="prix_initial")
        npv1 = results1.get('npv', 'Erreur') if results1 else 'Erreur'
        print(f"Calcul NPV pour Prix 2 = {price2:.4f}...")
        results2 = analysis_module.calculate_financial_indicators('Base', prix_revente=price2, override_source_prix_autoconso="prix_initial")
        npv2 = results2.get('npv', 'Erreur') if results2 else 'Erreur'

        print(f"NPV (equity) à {price1:.4f} = {npv1}") # Préciser NPV equity
        print(f"NPV (equity) à {price2:.4f} = {npv2}") # Préciser NPV equity
        if isinstance(npv1, (int, float)) and isinstance(npv2, (int, float)):
             print(f"Différence NPV (equity): {npv1 - npv2:,.2f}")
        print("---------------------------------------------")
        
        # --- Test NPV @ LCOE (AJOUTÉ) ---
        print("\n--- Test NPV @ Prix = LCOE --- (Doit être proche de 0 si 100% Equity)")
        # Recalculer les indicateurs de base pour obtenir le LCOE avec la config modifiée (100% equity)
        print("Recalcul des indicateurs de base pour obtenir le LCOE (100% equity)...")
        base_indicators_for_lcoe_test = analysis_module.calculate_financial_indicators('Base')
        if base_indicators_for_lcoe_test and base_indicators_for_lcoe_test.get('lcoe') is not None:
            lcoe = base_indicators_for_lcoe_test['lcoe']
            print(f"LCOE calculé (100% equity) : {lcoe:.4f}")
            print(f"Calcul NPV pour Prix = LCOE ({lcoe:.4f})...")
            # Important: Appeler avec override='prix_initial' car LCOE est un prix de vente
            # pour l'énergie produite, donc on suppose que l'autoconsommation
            # est aussi valorisée à ce prix pour la comparaison NPV=0.
            results_lcoe = analysis_module.calculate_financial_indicators('Base', 
                                                                        prix_revente=lcoe, 
                                                                        override_source_prix_autoconso="prix_initial")
            if results_lcoe and results_lcoe.get('npv') is not None:
                npv_at_lcoe = results_lcoe['npv']
                print(f"-> NPV à P=LCOE ({lcoe:.4f}) : {npv_at_lcoe:,.2f}")
                if abs(npv_at_lcoe) < 1: # Tolérance pour quasi-zéro
                     print("  (NPV est proche de zéro, ce qui est attendu car 100% fonds propres)")
                else:
                     print("  (ATTENTION: NPV n'est pas proche de zéro ! Vérifier calcul ou hypothèses)")
            else:
                print("-> Échec du calcul de la NPV au prix LCOE.")
        else:
            print("LCOE non disponible ou calcul indicateurs de base échoué.")
        print("------------------------------")
        # --- FIN TEST NPV @ LCOE ---

    except Exception as e:
        print(f"ERREUR lors de l'exécution de AnalysisModule: {e}")
        print(traceback.format_exc())
        sys.exit(1)

    print("\nTest standalone terminé.")
