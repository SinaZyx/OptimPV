# modules/engine_module/financial_calculations.py
import numpy as np
import pandas as pd
import logging

try:
    from .engine_utils import NpfModuleWrapper  # Import relatif pour usage comme module
except ImportError:
    try:
        # Fallback pour usage direct ou test
        from engine_utils import NpfModuleWrapper
    except ImportError:
        # Dernier fallback - définir une classe minimale si nécessaire
        class NpfModuleWrapper:
            def __init__(self, use_real_npf=False):
                self.use_real_npf = use_real_npf
            def npv(self, *args, **kwargs): return np.nan
            def irr(self, *args, **kwargs): return np.nan

logger = logging.getLogger(__name__)

# Initialiser npf à partir de engine_utils
# Déterminer NPF_IS_REAL au démarrage du module financial_calculations
NPF_IS_REAL_FC = False
try:
    import numpy_financial as npf_real_fc
    NPF_IS_REAL_FC = True
    logger.info("financial_calculations: numpy_financial (npf_real_fc) chargé.")
except ImportError:
    logger.warning("financial_calculations: numpy_financial non trouvé. Fonctions secours via NpfModuleWrapper seront utilisées.")

npf = NpfModuleWrapper(use_real_npf=NPF_IS_REAL_FC)


def calculate_wacc(debt_ratio: float,
                  taux_interet_dette_pct: float,
                  taux_imposition_pct: float,
                  cout_fonds_propres_pct: float,
                  wacc_type: str = "after_tax") -> float | None:
    try:
        rd = float(taux_interet_dette_pct) / 100.0
        tc = float(taux_imposition_pct) / 100.0
        re = float(cout_fonds_propres_pct) / 100.0  # Coût des fonds propres en décimal
        dr = float(debt_ratio)  # Debt ratio en décimal (ex: 0.8 pour 80%)

        if not (0 <= dr <= 1):
            logger.error(f"Debt ratio invalide: {dr}. Doit être entre 0 et 1.")
            return None
        if not (0 <= tc < 1):  # tc ne peut pas être 1 (100%) pour la formule standard du bouclier fiscal
            logger.error(f"Taux d'imposition invalide: {tc}. Doit être entre 0 et <1.")
            return None
        if pd.isna(rd) or pd.isna(re):  # Vérifier si les taux sont valides
            logger.error(f"Taux d'intérêt dette (rd={rd}) ou coût fonds propres (re={re}) non valide (NaN).")
            return None

        cout_dette_apres_impots = rd * (1.0 - tc)
        equity_ratio = 1.0 - dr
        
        # Calcul direct du WACC après impôts
        wacc_at = (dr * cout_dette_apres_impots) + (equity_ratio * re)

        if not (pd.notna(wacc_at) and np.isfinite(wacc_at)):
            logger.warning(f"WACC après-taxe calculé non fini ou NaN ({wacc_at}). Params: dr={dr}, rd={rd}, tc={tc}, re={re}")
            return None

        if wacc_type == "pre_tax":
            if abs(1.0 - tc) < 1e-9:  # tc est effectivement 100%
                logger.info("Taux d'imposition à 100%, WACC pré-taxe calculé sans effet fiscal direct sur la dette.")
                wacc_pt = (dr * rd) + (equity_ratio * re)
            else:
                wacc_pt = wacc_at / (1.0 - tc)
            
            if not (pd.notna(wacc_pt) and np.isfinite(wacc_pt)):
                logger.warning(f"WACC pré-taxe calculé non fini ou NaN ({wacc_pt})")
                return None
            return wacc_pt * 100.0  # Renvoyer en pourcentage
        
        return wacc_at * 100.0  # Renvoyer en pourcentage pour WACC after-tax

    except Exception as e:
        logger.error(f"Erreur inattendue dans calculate_wacc: {e}", exc_info=True)
        return None

def calculate_monthly_loan_schedule(principal: float, annual_rate: float, term_years: int, num_months_simulation: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if principal < 1e-6 or term_years <= 0:
        zeros_array = np.zeros(num_months_simulation)
        return zeros_array.copy(), zeros_array.copy(), zeros_array.copy()
    
    monthly_rate = annual_rate / 12.0
    n_payments_loan_term = int(round(term_years * 12))

    monthly_payment = 0.0
    if n_payments_loan_term > 0:
        if abs(monthly_rate) < 1e-9: 
            monthly_payment = principal / n_payments_loan_term
        else:
            try:
                factor = (1 + monthly_rate)**n_payments_loan_term
                denominator = factor - 1
                if abs(denominator) < 1e-12: 
                    monthly_payment = principal / n_payments_loan_term
                else:
                    monthly_payment = principal * (monthly_rate * factor) / denominator
                if not (pd.notna(monthly_payment) and np.isfinite(monthly_payment)):
                    monthly_payment = np.nan 
            except (OverflowError, ZeroDivisionError):
                monthly_payment = np.nan
    
    if pd.isna(monthly_payment): 
        logger.warning(f"Calcul échéance impossible (P={principal}, TauxAn={annual_rate}, DuréeAn={term_years}). Prêt ignoré.")
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
            principal_payment_for_month = max(0, principal_payment_for_month)
            if principal_payment_for_month > current_balance - 1e-5:
                principal_payment_for_month = current_balance 
            
            interests_paid_monthly[i] = interest_for_month
            principals_paid_monthly[i] = principal_payment_for_month
            current_balance -= principal_payment_for_month
            debt_balance_eom[i] = max(0, current_balance) 
        else: 
            debt_balance_eom[i] = max(0, current_balance) if i < n_payments_loan_term else 0.0
    return interests_paid_monthly, principals_paid_monthly, debt_balance_eom

def calculate_lcoe_annual_aggregation(
    wacc_annual_discount_rate: float | None,
    monthly_df_results: pd.DataFrame,
    terminal_value_net_project: float,
    construction_period_months: int
) -> float | None:
    """
    Calcule le LCOE (Levelized Cost of Energy) en agrégeant les flux sur une base annuelle
    et en utilisant un taux d'actualisation annuel.

    Args:
        wacc_annual_discount_rate: Taux d'actualisation annuel effectif (ex: 0.06 pour 6%).
        monthly_df_results: DataFrame avec les résultats mensuels détaillés.
                            Doit contenir 'Is_Construction_Phase', 'CAPEX_Initial_Mensuel',
                            'OPEX', 'TURPE', 'Production_kWh' et un DatetimeIndex.
        terminal_value_net_project: Valeur résiduelle nette du projet à la fin.
        construction_period_months: Durée de la phase de construction en mois.

    Returns:
        LCOE en €/kWh ou None si le calcul échoue.
    """
    if wacc_annual_discount_rate is None or not (pd.notna(wacc_annual_discount_rate) and wacc_annual_discount_rate > -1.0):
        logger.warning("LCOE Annual: Taux WACC annuel invalide ou non fourni. LCOE sera NaN.")
        return np.nan

    if not isinstance(monthly_df_results.index, pd.DatetimeIndex):
        logger.error("LCOE Annual: L'index de monthly_df_results doit être un DatetimeIndex.")
        return np.nan

    required_cols = ['Is_Construction_Phase', 'CAPEX_Initial_Mensuel', 'OPEX', 'TURPE', 'Production_kWh']
    for col in required_cols:
        if col not in monthly_df_results.columns:
            logger.error(f"LCOE Annual: Colonne '{col}' manquante dans monthly_df_results.")
            return np.nan

    try:
        # 1. Isoler les phases
        df_construction = monthly_df_results[monthly_df_results['Is_Construction_Phase'] == 1.0]
        df_exploitation = monthly_df_results[monthly_df_results['Is_Construction_Phase'] == 0.0]

        if df_exploitation.empty:
            logger.warning("LCOE Annual: Aucune donnée pour la phase d'exploitation.")
            return np.nan

        # 2. Calcul du CAPEX Total à T0
        total_capex_undiscounted = df_construction['CAPEX_Initial_Mensuel'].sum()
        if construction_period_months == 0 and not df_exploitation.empty:
            first_exploitation_month_capex = df_exploitation['CAPEX_Initial_Mensuel'].iloc[0]
            total_capex_undiscounted += first_exploitation_month_capex
        

        # 3. Agréger les coûts opérationnels et la production annuellement
        opex_annual = df_exploitation['OPEX'].resample('Y').sum()
        turpe_annual = df_exploitation['TURPE'].resample('Y').sum()
        production_annual_kwh = df_exploitation['Production_kWh'].resample('Y').sum()
        
        num_exploitation_years = len(production_annual_kwh)

        if num_exploitation_years == 0:
            if not df_exploitation.empty:
                 opex_total_exploitation = df_exploitation['OPEX'].sum()
                 turpe_total_exploitation = df_exploitation['TURPE'].sum()
                 production_total_exploitation_kwh = df_exploitation['Production_kWh'].sum()
                 if production_total_exploitation_kwh > 1e-6 :
                      num_exploitation_years = 1
                      opex_annual = pd.Series([opex_total_exploitation])
                      turpe_annual = pd.Series([turpe_total_exploitation])
                      production_annual_kwh = pd.Series([production_total_exploitation_kwh])
                      logger.info(f"LCOE Annual: Exploitation < 1 an, agrégation manuelle: OPEX={opex_total_exploitation}, TURPE={turpe_total_exploitation}, Prod={production_total_exploitation_kwh}")
                 else:
                      logger.warning("LCOE Annual: Aucune production significative trouvée pour la phase d'exploitation (même < 1 an).")
                      return np.nan
            else:
                logger.warning("LCOE Annual: Phase d'exploitation vide, impossible d'agréger annuellement.")
                return np.nan

        # 4. Créer le vecteur des coûts annuels
        annual_costs_for_lcoe = np.zeros(num_exploitation_years + 1)
        annual_costs_for_lcoe[0] = total_capex_undiscounted

        for i in range(num_exploitation_years):
            annual_costs_for_lcoe[i + 1] = (opex_annual.iloc[i] if i < len(opex_annual) else 0) + \
                                           (turpe_annual.iloc[i] if i < len(turpe_annual) else 0)
        
        if num_exploitation_years > 0:
            annual_costs_for_lcoe[-1] -= terminal_value_net_project
        

        # 5. Créer le vecteur de production annuelle
        annual_production_for_lcoe = np.zeros(num_exploitation_years + 1)
        if num_exploitation_years > 0 :
            annual_production_for_lcoe[1:] = production_annual_kwh.values


        # 6. Calculer NPV des coûts et de la production
        npv_total_costs_annual = npf.npv(wacc_annual_discount_rate, annual_costs_for_lcoe)
        if not (pd.notna(npv_total_costs_annual) and np.isfinite(npv_total_costs_annual)):
            logger.warning(f"LCOE Annual: NPV des coûts annuels non valide ({npv_total_costs_annual}). WACC Annuel: {wacc_annual_discount_rate}")
            return np.nan

        npv_total_production_annual = npf.npv(wacc_annual_discount_rate, annual_production_for_lcoe)
        if not (pd.notna(npv_total_production_annual) and np.isfinite(npv_total_production_annual)):
            logger.warning(f"LCOE Annual: NPV de la production annuelle non valide ({npv_total_production_annual}). WACC Annuel: {wacc_annual_discount_rate}")
            return np.nan
            

        # 7. Calculer LCOE
        if abs(npv_total_production_annual) > 1e-9:
            lcoe_result_annual = npv_total_costs_annual / npv_total_production_annual
            logger.info(f"LCOE Annual Calculé: {lcoe_result_annual:.4f} €/kWh")
            return lcoe_result_annual
        else:
            logger.warning("LCOE Annual: NPV de la production annuelle nulle ou quasi-nulle. Impossible de calculer le LCOE.")
            return np.nan

    except Exception as e:
        logger.error(f"Erreur dans calculate_lcoe_annual_aggregation: {e}", exc_info=True)
        return np.nan

def calculate_lcoe_engineering(wacc_monthly_discount_rate: float | None, 
                               monthly_df_results: pd.DataFrame, 
                               terminal_value_net_project: float) -> float | None:
    """
    Calcule le LCOE (Levelized Cost of Energy) à partir des coûts et de la production sur une base MENSUELLE.
    Calcule le LCOE sur base mensuelle avec actualisation des flux de coûts et production.
    
    Args:
        wacc_monthly_discount_rate: Taux d'actualisation mensuel (ex: 0.005 pour 0.5%).
        monthly_df_results: DataFrame avec les colonnes 'CAPEX_Initial_Mensuel', 'OPEX', 'TURPE', 'Production_kWh'
        terminal_value_net_project: Valeur résiduelle nette du projet à la fin
        
    Returns:
        LCOE en €/kWh ou None si le calcul échoue
    """
    if wacc_monthly_discount_rate is None or not (pd.notna(wacc_monthly_discount_rate) and wacc_monthly_discount_rate > -1.0):
        logger.warning("LCOE Eng: Taux WACC invalide ou non fourni. LCOE sera NaN.")
        return np.nan
        
    # IMPORTANT: logging pour débogage
    total_prod_original = monthly_df_results['Production_kWh'].sum() if 'Production_kWh' in monthly_df_results.columns else 0.0
    
    try:
        # IMPORTANT: Créer une NOUVELLE copie du DataFrame pour éviter de modifier l'original
        # Copy deep=True pour être absolument sûr
        df_copy = monthly_df_results.copy(deep=True)
        
        # Vérifier que la copie a bien fonctionné
        total_prod_copy = df_copy['Production_kWh'].sum() if 'Production_kWh' in df_copy.columns else 0.0
        
        # Extraire les VALEURS des séries en .copy() pour créer de nouveaux tableaux NumPy
        capex_values = df_copy.get('CAPEX_Initial_Mensuel', pd.Series(0.0, index=df_copy.index)).fillna(0).values.copy()
        opex_values = df_copy.get('OPEX', pd.Series(0.0, index=df_copy.index)).fillna(0).values.copy()
        turpe_values = df_copy.get('TURPE', pd.Series(0.0, index=df_copy.index)).fillna(0).values.copy()
        
        # Créer un nouveau tableau NumPy pour les coûts
        total_costs = capex_values + opex_values + turpe_values
        
        # Ajuster le dernier élément pour la valeur résiduelle
        if len(total_costs) > 0:
            total_costs[-1] -= terminal_value_net_project
        
        # Calculer la VAN des coûts
        npv_total_costs = npf.npv(wacc_monthly_discount_rate, total_costs)
        if not (pd.notna(npv_total_costs) and np.isfinite(npv_total_costs)):
            logger.warning("LCOE Eng: NPV des coûts non valide.")
            return np.nan
        
        # Obtenir les valeurs de production (copie explicite)
        prod_values = df_copy.get('Production_kWh', pd.Series(0.0, index=df_copy.index)).fillna(0).values.copy()
        
        # Vérifier qu'on n'a pas altéré l'original à ce stade
        total_prod_mid = monthly_df_results['Production_kWh'].sum() if 'Production_kWh' in monthly_df_results.columns else 0.0
        
        # Calculer la VAN de la production
        npv_total_production = npf.npv(wacc_monthly_discount_rate, prod_values)
        if not (pd.notna(npv_total_production) and np.isfinite(npv_total_production)):
            logger.warning("LCOE Eng: NPV de la production non valide.")
            return np.nan
        
        # Calculer le LCOE
        if abs(npv_total_production) > 1e-9:
            lcoe_result = npv_total_costs / npv_total_production
            
            # Vérification finale que l'original est intact
            total_prod_final = monthly_df_results['Production_kWh'].sum() if 'Production_kWh' in monthly_df_results.columns else 0.0
            
            if abs(total_prod_original - total_prod_final) > 0.01:
                logger.error(f"⚠️ Intégrité des données compromise! Production modifiée: {total_prod_original:.2f} -> {total_prod_final:.2f}")
                
            return lcoe_result
        else:
            logger.warning("LCOE Eng: NPV de la production nulle ou quasi-nulle.")
            return np.nan
            
    except Exception as e:
        logger.error(f"Erreur dans calculate_lcoe_engineering: {e}", exc_info=True)
        return np.nan

def calculate_avg_dscr_revised(monthly_df_results: pd.DataFrame, corporate_tax_rate_decimal: float) -> float | None:
    """
    Calcule le DSCR (Debt Service Coverage Ratio) moyen sur la durée du projet.
    
    Args:
        monthly_df_results: DataFrame avec les colonnes 'EBITDA', 'Tax_Payment', 'Service_Dette'
        corporate_tax_rate_decimal: Taux d'imposition (non utilisé directement mais gardé pour compatibilité)
        
    Returns:
        DSCR moyen ou None si le calcul échoue
    """
    # corporate_tax_rate_decimal n'est plus directement utilisé ici, car Tax_Payment est fourni.
    if monthly_df_results.empty:
        logger.warning("DSCR: Données mensuelles vides pour DSCR.")
        return np.nan
    
    # Logging pour débogage  
    total_prod_original = monthly_df_results['Production_kWh'].sum() if 'Production_kWh' in monthly_df_results.columns else 0.0
    
    try:
        # Créer une copie explicite pour éviter de modifier l'original
        df_copy = monthly_df_results.copy(deep=True)
        
        # Vérifier que la copie a bien fonctionné
        total_prod_copy = df_copy['Production_kWh'].sum() if 'Production_kWh' in df_copy.columns else 0.0
        
        if not isinstance(df_copy.index, pd.DatetimeIndex):
            try: 
                df_copy.index = pd.to_datetime(df_copy.index)
            except Exception as e_idx:
                logger.error(f"DSCR: Index non convertible en DatetimeIndex: {e_idx}")
                return np.nan
        
        required_cols_dscr = ['EBITDA', 'Tax_Payment', 'Service_Dette']
        for col_dscr in required_cols_dscr:
            if col_dscr not in df_copy.columns:
                logger.warning(f"DSCR: Colonne '{col_dscr}' manquante pour agrégation.")
                df_copy[col_dscr] = 0.0 # Ajouter la colonne avec des zéros pour éviter les erreurs

        try:
            ebitda_annual = df_copy['EBITDA'].fillna(0).resample('Y').sum()
            is_paid_annual = df_copy['Tax_Payment'].fillna(0).resample('Y').sum()
            debt_service_annual = df_copy['Service_Dette'].fillna(0).resample('Y').sum()
        except Exception as e_resample:
            logger.error(f"DSCR: Erreur lors du resample annuel: {e_resample}")
            return np.nan

        if ebitda_annual.empty and is_paid_annual.empty and debt_service_annual.empty:
            logger.warning("DSCR: Aucune donnée annuelle après resampling.")
            return np.nan

        annual_summary = pd.DataFrame({
            'EBITDA_annuel': ebitda_annual,
            'IS_Paid_annuel': is_paid_annual,
            'Service_Dette_annuel': debt_service_annual
        }).fillna(0)
        
        if annual_summary.empty: 
            logger.warning("DSCR: DataFrame annuel vide.")
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
        
        dscr_for_avg = annual_summary['DSCR_annuel'].loc[annual_summary['Service_Dette_annuel'] > 1e-9]
        dscr_finite_values = dscr_for_avg.loc[np.isfinite(dscr_for_avg)]
        
        # Vérification finale que l'original est intact
        total_prod_final = monthly_df_results['Production_kWh'].sum() if 'Production_kWh' in monthly_df_results.columns else 0.0
        
        if abs(total_prod_original - total_prod_final) > 0.01:
            logger.error(f"⚠️ Intégrité des données compromise! Production modifiée: {total_prod_original:.2f} -> {total_prod_final:.2f}")
        
        if not dscr_finite_values.empty:
            avg_dscr = dscr_finite_values.mean()
        elif not dscr_for_avg.loc[dscr_for_avg == np.inf].empty: 
            avg_dscr = np.inf
        else: 
            avg_dscr = np.nan
        return avg_dscr
    except Exception as e:
        logger.error(f"Erreur dans calculate_avg_dscr_revised: {e}", exc_info=True)
        return np.nan