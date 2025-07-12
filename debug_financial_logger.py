import logging
import numpy as np
import pandas as pd
from datetime import datetime
import json
from typing import Any, Dict, List, Optional

class FinancialDebugLogger:
    """
    Système de logs avancé pour débugger les calculs financiers d'OptimPV
    """
    
    def __init__(self, log_file: str = "financial_debug.log"):
        self.log_file = log_file
        self.setup_logger()
        self.calculation_context = {}
        
    def setup_logger(self):
        """Configure le logger avec un format détaillé"""
        self.logger = logging.getLogger('financial_debug')
        self.logger.setLevel(logging.DEBUG)
        
        # Éviter les handlers multiples
        if self.logger.handlers:
            self.logger.handlers.clear()
            
        # Handler pour fichier
        file_handler = logging.FileHandler(self.log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Handler pour console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Format détaillé
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)8s | %(funcName)20s:%(lineno)3d | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def log_calculation_start(self, scenario_name: str, context: Dict[str, Any]):
        """Démarre une nouvelle session de calcul"""
        self.calculation_context = context
        self.logger.info("="*80)
        self.logger.info(f"DÉBUT CALCUL FINANCIER - Scénario: {scenario_name}")
        self.logger.info("="*80)
        
        # Log des paramètres principaux
        for key, value in context.items():
            if isinstance(value, (int, float, str, bool)):
                self.logger.info(f"PARAM | {key}: {value}")
    
    def log_cash_flows(self, name: str, cash_flows: np.ndarray, prefix: str = ""):
        """Log détaillé des flux de trésorerie"""
        if cash_flows is None or len(cash_flows) == 0:
            self.logger.warning(f"FLUX {prefix}{name}: VIDE ou None")
            return
            
        self.logger.info(f"FLUX {prefix}{name} - {len(cash_flows)} périodes")
        self.logger.debug(f"  Somme totale: {np.sum(cash_flows):,.2f}")
        self.logger.debug(f"  T0 (investissement): {cash_flows[0]:,.2f}")
        
        if len(cash_flows) > 1:
            self.logger.debug(f"  Flux opérationnels moyens: {np.mean(cash_flows[1:]):,.2f}")
            self.logger.debug(f"  Flux min/max: {np.min(cash_flows[1:]):,.2f} / {np.max(cash_flows[1:]):,.2f}")
        
        # Log les premiers et derniers flux
        n_show = min(6, len(cash_flows))
        for i in range(n_show):
            self.logger.debug(f"    Période {i:2d}: {cash_flows[i]:,.2f}")
        
        if len(cash_flows) > n_show:
            self.logger.debug(f"    ... ({len(cash_flows) - n_show} périodes intermédiaires)")
            for i in range(max(n_show, len(cash_flows) - 3), len(cash_flows)):
                self.logger.debug(f"    Période {i:2d}: {cash_flows[i]:,.2f}")
    
    def log_cumulative_analysis(self, name: str, cash_flows: np.ndarray):
        """Analyse cumulative pour identifier les points de récupération"""
        if cash_flows is None or len(cash_flows) == 0:
            return
            
        cumulative = np.cumsum(cash_flows)
        self.logger.info(f"ANALYSE CUMULATIVE {name}")
        
        # Trouve le point de récupération
        positive_indices = np.where(cumulative >= -1e-9)[0]
        if len(positive_indices) > 0:
            recovery_month = positive_indices[0]
            self.logger.info(f"  Récupération détectée au mois {recovery_month}")
            self.logger.debug(f"  Cumul avant récupération: {cumulative[recovery_month-1]:,.2f}")
            self.logger.debug(f"  Flux du mois de récupération: {cash_flows[recovery_month]:,.2f}")
            self.logger.debug(f"  Cumul après récupération: {cumulative[recovery_month]:,.2f}")
        else:
            self.logger.warning(f"  Pas de récupération détectée sur {len(cash_flows)} périodes")
            self.logger.debug(f"  Cumul final: {cumulative[-1]:,.2f}")
    
    def log_irr_calculation(self, name: str, cash_flows: np.ndarray, irr_result: float):
        """Log détaillé du calcul de TRI"""
        self.logger.info(f"CALCUL TRI {name}")
        
        if cash_flows is None or len(cash_flows) == 0:
            self.logger.error(f"  ERREUR: Flux vides pour {name}")
            return
            
        # Vérifications de base
        has_negative = np.any(cash_flows < 0)
        has_positive = np.any(cash_flows > 0)
        
        self.logger.debug(f"  Flux négatifs présents: {has_negative}")
        self.logger.debug(f"  Flux positifs présents: {has_positive}")
        
        if not (has_negative and has_positive):
            self.logger.warning(f"  ALERTE: Flux mono-directionnels - TRI non calculable")
        
        # Résultat du TRI
        if pd.isna(irr_result) or not np.isfinite(irr_result):
            self.logger.error(f"  TRI INVALIDE: {irr_result}")
        else:
            irr_monthly = irr_result
            irr_annual = (1 + irr_monthly)**12 - 1
            self.logger.info(f"  TRI mensuel brut: {irr_monthly:.6f}")
            self.logger.info(f"  TRI annuel: {irr_annual:.4%}")
            
            if irr_annual < -0.5:  # TRI < -50%
                self.logger.warning(f"  ALERTE: TRI très négatif ({irr_annual:.1%})")
    
    def log_npv_calculation(self, name: str, cash_flows: np.ndarray, discount_rate: float, npv_result: float):
        """Log détaillé du calcul de VAN"""
        self.logger.info(f"CALCUL VAN {name}")
        
        if pd.isna(discount_rate):
            self.logger.error(f"  ERREUR: Taux d'actualisation invalide")
            return
            
        self.logger.debug(f"  Taux d'actualisation: {discount_rate:.6f}")
        
        if pd.isna(npv_result) or not np.isfinite(npv_result):
            self.logger.error(f"  VAN INVALIDE: {npv_result}")
        else:
            self.logger.info(f"  VAN: {npv_result:,.2f} €")
    
    def log_payback_calculation(self, name: str, payback_months: Optional[float]):
        """Log détaillé du calcul de payback"""
        self.logger.info(f"CALCUL PAYBACK {name}")
        
        if payback_months is None:
            self.logger.warning(f"  PAYBACK: Non récupérable")
        elif payback_months == 0.0:
            self.logger.info(f"  PAYBACK: Immédiat (<1 mois)")
        else:
            years = payback_months / 12.0
            self.logger.info(f"  PAYBACK: {payback_months:.1f} mois = {years:.1f} ans")
    
    def log_inconsistency_alert(self, irr_annual: float, payback_years: float):
        """Détecte et log les incohérences entre TRI et Payback"""
        self.logger.info("VÉRIFICATION COHÉRENCE TRI/PAYBACK")
        
        # Règles de cohérence
        inconsistent = False
        
        if pd.isna(irr_annual) or pd.isna(payback_years):
            self.logger.warning("  Impossible de vérifier: valeurs manquantes")
            return
            
        if irr_annual < -0.5 and payback_years < 2.0:
            inconsistent = True
            self.logger.error(f"  INCOHÉRENCE MAJEURE:")
            self.logger.error(f"    TRI très négatif ({irr_annual:.1%}) mais payback rapide ({payback_years:.1f} ans)")
            
        if irr_annual > 0.1 and payback_years > 15.0:
            inconsistent = True
            self.logger.error(f"  INCOHÉRENCE:")
            self.logger.error(f"    TRI élevé ({irr_annual:.1%}) mais payback long ({payback_years:.1f} ans)")
        
        if not inconsistent:
            self.logger.info("  Cohérence TRI/Payback: OK")
    
    def log_calculation_summary(self, results: Dict[str, Any]):
        """Résumé final des calculs"""
        self.logger.info("="*80)
        self.logger.info("RÉSUMÉ FINAL DES INDICATEURS")
        self.logger.info("="*80)
        
        # Indicateurs fonds propres
        npv_equity = results.get('npv_equity', np.nan)
        irr_equity = results.get('irr_equity', np.nan)
        payback_equity = results.get('payback_equity_years', np.nan)
        
        self.logger.info("FONDS PROPRES:")
        self.logger.info(f"  VAN: {npv_equity:,.2f} €")
        self.logger.info(f"  TRI: {irr_equity:.2%}")
        self.logger.info(f"  Payback: {payback_equity:.1f} ans")
        
        # Indicateurs projet
        npv_project = results.get('npv_project', np.nan)
        irr_project = results.get('irr_project', np.nan)
        payback_project = results.get('payback_project_years', np.nan)
        
        self.logger.info("PROJET:")
        self.logger.info(f"  VAN: {npv_project:,.2f} €")
        self.logger.info(f"  TRI: {irr_project:.2%}")
        self.logger.info(f"  Payback: {payback_project:.1f} ans")
        
        # Vérification finale
        self.log_inconsistency_alert(irr_equity, payback_equity)
        
        self.logger.info("="*80)
        self.logger.info("FIN DU CALCUL")
        self.logger.info("="*80)

# Fonction utilitaire pour activer le debug
def activate_financial_debug():
    """Active le système de debug financier"""
    return FinancialDebugLogger()