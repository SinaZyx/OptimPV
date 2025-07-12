# modules/engine_module/engine_utils.py
import numpy as np
import pandas as pd
from scipy.optimize import brentq
import sys
import logging

logger = logging.getLogger(__name__)

# Fonctions NPV/IRR de secours (précédemment dans analysis_engine.py)
def secours_npv(rate, values):
    """Fonction de secours pour numpy_financial.npv avec stabilité numérique améliorée."""
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return 0.0
    if np.isclose(rate, -1.0):
        if values.size > 0 and np.any(values[1:]):
            return float('-inf') if values[0] >= 0 else float('inf')
        return values[0] if values.size > 0 else 0.0
    if rate < -1.0:
        return np.nan

    try:
        pv_sum = 0.0
        log1p_rate = np.log1p(rate)
        for i, value in enumerate(values):
            if value == 0:
                continue
            try:
                log_discount_factor = -i * log1p_rate
                if log_discount_factor > 709:
                    pv = 0.0
                elif log_discount_factor < -709:
                    if abs(value) < sys.float_info.epsilon:
                        pv = 0.0
                    else:
                        return np.nan
                else:
                    discount_factor = np.exp(log_discount_factor)
                    pv = value * discount_factor
                if not np.isfinite(pv):
                    return np.nan
                pv_sum += pv
            except (OverflowError, FloatingPointError):
                return np.nan
        return pv_sum
    except Exception:
        pv_sum = 0.0
        for i, value in enumerate(values):
            if value == 0: continue
            try:
                discount_factor_inv = (1 + rate) ** i
                if abs(discount_factor_inv) < sys.float_info.epsilon:
                    return np.nan if abs(value) > sys.float_info.epsilon else 0.0
                pv = value / discount_factor_inv
                if not np.isfinite(pv): return np.nan
                pv_sum += pv
            except (OverflowError, FloatingPointError): return np.nan
        return pv_sum

def secours_irr(values, guess=0.1, tol=1e-7, max_iter=100):
    values = np.asarray(values, dtype=float)
    if values.size < 2 or np.all(np.isclose(values,0)): return np.nan
    
    f_npv_for_irr = lambda r: secours_npv(r, values)
    rate_intervals = [(-0.9999, 0.5), (0.0, 1.0), (-0.5, 0.0), (0.5, 5.0), (1.0, 100.0), (-0.9, -0.01)]
    
    for r_min, r_max in rate_intervals:
        try:
            npv_min = f_npv_for_irr(r_min)
            npv_max = f_npv_for_irr(r_max)
            if pd.notna(npv_min) and pd.notna(npv_max) and (np.sign(npv_min) * np.sign(npv_max) <= 0):
                if np.isclose(npv_min, 0.0): return r_min
                if np.isclose(npv_max, 0.0): return r_max
                if npv_min * npv_max < 0:
                    return brentq(f_npv_for_irr, r_min, r_max, xtol=tol, rtol=tol, maxiter=max_iter)
        except (RuntimeError, ValueError): 
            continue
        except Exception: 
            continue
    logger.warning("Fonction secours_irr limitée, n'a pas convergé.")
    return np.nan

class NpfModuleWrapper: # Renommé pour éviter confusion si numpy_financial est chargé
    def __init__(self, use_real_npf=True):
        self.use_real_npf = use_real_npf
        if self.use_real_npf:
            try:
                import numpy_financial as npf_real
                self.npf_real = npf_real
                logger.info("numpy_financial (npf_real) chargé avec succès dans NpfModuleWrapper.")
            except ImportError:
                self.use_real_npf = False
                logger.warning("NpfModuleWrapper: numpy_financial non trouvé. Fonctions secours utilisées.")
        
        if not self.use_real_npf:
             logger.info("NpfModuleWrapper: Utilisation des fonctions secours pour NPV/IRR.")


    def npv(self, rate, values):
        if self.use_real_npf:
            try:
                return self.npf_real.npv(rate, values)
            except Exception as e:
                logger.warning(f"Erreur avec npf_real.npv ({e}), fallback sur secours_npv.")
                return secours_npv(rate, values)
        return secours_npv(rate, values)

    def irr(self, values):
        if self.use_real_npf:
            try:
                return self.npf_real.irr(values)
            except Exception as e: # numpy_financial.irr peut lever des erreurs variées
                logger.warning(f"Erreur avec npf_real.irr ({e}), fallback sur secours_irr.")
                return secours_irr(values)
        return secours_irr(values)

def calculate_payback_months(monthly_cash_flows_with_t0: np.ndarray) -> float | None:
    """
    Calcule la période de récupération en mois.
    Le premier élément de monthly_cash_flows_with_t0 est le flux à T0 (investissement initial, négatif).
    """
    if not isinstance(monthly_cash_flows_with_t0, np.ndarray):
        monthly_cash_flows_with_t0 = np.array(monthly_cash_flows_with_t0, dtype=float)
    
    if len(monthly_cash_flows_with_t0) < 1: return None 
    if monthly_cash_flows_with_t0[0] >= -1e-9: return 0.0 
    if len(monthly_cash_flows_with_t0) == 1: return None

    cumulative_cf = np.cumsum(monthly_cash_flows_with_t0)
    positive_indices = np.where(cumulative_cf >= -1e-9)[0] # Indices où le cumulatif devient positif ou nul
    
    if len(positive_indices) == 0: return None # Jamais récupéré
    first_positive_idx = positive_indices[0]
    
    if first_positive_idx == 0: return 0.0 # Récupéré immédiatement (si T0 était >=0)
    
    # Mois avant la récupération (index dans le tableau des flux mensuels, T0 est à index 0)
    month_before_payback_t_idx = first_positive_idx - 1 
    last_negative_cumulative_cf = cumulative_cf[month_before_payback_t_idx]
    cash_flow_of_payback_month = monthly_cash_flows_with_t0[first_positive_idx]

    if abs(cash_flow_of_payback_month) < 1e-9: 
        # Si le cash-flow du mois de récupération est nul,
        # le payback est à la fin du mois précédent si le cumul était déjà positif
        return float(month_before_payback_t_idx) if last_negative_cumulative_cf >= -1e-9 else None
    else:
        # Fraction du mois nécessaire pour couvrir le reste
        fraction_of_month = -last_negative_cumulative_cf / cash_flow_of_payback_month
        # Le payback est le nombre de mois complets AVANT la récupération + la fraction du mois de récupération.
        # Puisque T0 est l'investissement, first_positive_idx représente le nombre de périodes *après* T0.
        # Donc, `first_positive_idx -1` est le nombre de périodes complètes avant le payback,
        # et `fraction_of_month` est la fraction de la `first_positive_idx`-ième période.
        # Le payback est donc (mois_complets_avant - 1 pour T0) + fraction
        payback_in_months = (first_positive_idx - 1) + fraction_of_month # Ajusté pour T0 étant l'investissement
        
    return max(0, payback_in_months) # Assurer non-négatif