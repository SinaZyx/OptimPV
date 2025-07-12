import pandas as pd
import numpy as np
from scipy.optimize import brentq
import logging

logger = logging.getLogger(__name__)

# Imports locaux pour npf (sera adapté selon la structure existante)
try:
    from .engine_utils import NpfModuleWrapper
    # Initialisation npf comme dans core_analyzer
    NPF_IS_REAL_CORE = False
    try:
        import numpy_financial as npf_real_core
        NPF_IS_REAL_CORE = True
    except ImportError:
        pass
    npf = NpfModuleWrapper(use_real_npf=NPF_IS_REAL_CORE)
except ImportError:
    # Fallback si engine_utils n'est pas disponible
    npf = None
    logger.warning("engine_utils non disponible, certaines fonctions NPF pourraient échouer")

class EquityCalculations:
    """
    Classe regroupant tous les calculs liés aux fonds propres et indicateurs equity.
    """
    
    def __init__(self):
        self.equity_calculation_details = {}
        self.fcfe_calculation_details = []
    
    def calculate_net_equity_investment_professional(self, capex_total, debt_amount, subvention_montant):
        """
        Calcul correct de l'investissement net en fonds propres
        selon les normes financières professionnelles (IFRS)
        """
        # Fonds propres bruts = CAPEX - Dette
        gross_equity = capex_total - debt_amount
        
        # La subvention réduit l'investissement initial net requis
        net_equity_investment = gross_equity - subvention_montant
        
        # Documentation pour l'audit
        self.equity_calculation_details = {
            'capex_total': capex_total,
            'debt_amount': debt_amount,
            'gross_equity': gross_equity,
            'subvention': subvention_montant,
            'net_equity_investment': net_equity_investment,
            'method': 'Subvention déduite de l\'investissement initial (norme IFRS)'
        }
        
        return net_equity_investment
    
    def calculate_irr_professional(self, cashflows, investment_initial):
        """
        Calcul robuste du TRI avec gestion des cas particuliers
        Utilise la méthode de Newton-Raphson avec garde-fous
        """
        # Construire la série complète : investissement initial + flux
        cf_complete = [-investment_initial] + list(cashflows)
        
        # Fonction VAN
        def npv_func(rate):
            return sum(cf / (1 + rate)**t for t, cf in enumerate(cf_complete))
        
        try:
            # Vérifier d'abord si une solution existe
            npv_at_minus_one = npv_func(-0.99)
            npv_at_plus_ten = npv_func(10.0)
            
            if npv_at_minus_one * npv_at_plus_ten > 0:
                # Pas de changement de signe = pas de TRI ou TRI multiple
                # Calculer le TRI modifié (MIRR) à la place
                mirr_result = self.calculate_mirr(cf_complete, 0.06, 0.06)  # wacc estimé 6%
                return mirr_result, 'MIRR'
            
            # Méthode de Brent (plus robuste que Newton pour les cas extrêmes)
            irr = brentq(npv_func, -0.99, 10.0, xtol=1e-6)
            
            # Vérification de cohérence
            if abs(irr) > 5.0:  # TRI > 500% ou < -500% est suspect
                # Recalculer avec MIRR
                mirr_result = self.calculate_mirr(cf_complete, 0.06, 0.06)
                return mirr_result, 'MIRR'
                
            return irr, 'IRR'
            
        except Exception as e:
            # En cas d'échec, utiliser le MIRR (Modified IRR)
            mirr_result = self.calculate_mirr(cf_complete, 0.06, 0.06)
            return mirr_result, 'MIRR'

    def calculate_mirr(self, cashflows, finance_rate, reinvest_rate):
        """
        Calcul du TRI Modifié (MIRR) - Plus stable pour les flux atypiques
        """
        n = len(cashflows) - 1
        
        if n <= 0:
            return np.nan
        
        # Séparer flux positifs et négatifs
        negative_flows = [cf / (1 + finance_rate)**t 
                         for t, cf in enumerate(cashflows) if cf < 0]
        positive_flows = [cf * (1 + reinvest_rate)**(n-t) 
                         for t, cf in enumerate(cashflows) if cf > 0]
        
        pv_negative = abs(sum(negative_flows))
        fv_positive = sum(positive_flows)
        
        if pv_negative == 0 or fv_positive == 0:
            return np.nan
            
        mirr = (fv_positive / pv_negative)**(1/n) - 1
        return mirr
    
    def calculate_fcfe_professional(self, monthly_results_df, subvention_totale_projet):
        """
        Calcul professionnel des FCFE avec isolation des éléments exceptionnels
        """
        fcfe_list = []
        fcfe_details = []
        
        # IMPORTANT : La prime N'EST PAS un flux, elle réduit l'investissement
        # Donc on la RETIRE des flux
        
        for idx, row in monthly_results_df.iterrows():
            # Composants standards du FCFE CORRIGÉS
            net_income = row.get('Resultat_Net', 0)
            depreciation = row.get('Amortissement', 0)
            delta_wc = -row.get('Delta_BFR_Mensuel', 0)  # Négatif si augmentation BFR
            # Les FCFE excluent le CAPEX initial (déjà comptabilisé dans l'investissement net)
            # Le CAPEX est déjà financé par dette + equity, pas par les cash flows
            debt_principal = -row.get('Principal_Rembourse', 0)
            # CORRECTION : Le tirage de dette initial ne doit PAS être un flux pour les actionnaires
            # car il sert à financer le CAPEX, pas à générer des liquidités pour eux
            debt_issuance = row.get('Debt_Drawn_This_Month', 0)
            if debt_issuance > 0:
                # Si c'est le tirage initial pour financer le CAPEX, ne pas l'inclure
                capex_this_month = row.get('CAPEX_Initial_Mensuel', 0)
                if capex_this_month > 0:
                    debt_issuance = 0  # Annuler le tirage car il finance le CAPEX
            
            # FCFE CORRIGÉ = Net Income + Depreciation - ΔWC - Principal 
            # PAS DE CAPEX ET PAS DE TIRAGE DETTE INITIAL !
            fcfe_operational = net_income + depreciation + delta_wc + debt_principal
            
            # Identifier et isoler les flux exceptionnels
            vat_payment = row.get('VAT_Payment', 0)
            monthly_revenue = row.get('Revenus_Total', 0)
            
            # Un remboursement TVA > 50% du CA mensuel est exceptionnel
            exceptional_vat = 0
            if abs(vat_payment) > abs(monthly_revenue) * 0.5 and vat_payment > 0:
                exceptional_vat = vat_payment
                fcfe_operational -= exceptional_vat  # Retirer du flux opérationnel
            
            # La prime autoconso est déjà déduite de l'investissement initial via net_equity_investment
            # Ne pas la déduire à nouveau des flux FCFE pour éviter une double déduction
            prime_encaissee = row.get('Prime_Autoconso_Encaissee', 0)
            # NOTE: Prime déjà comptabilisée dans l'investissement initial - pas de déduction ici
            
            fcfe_list.append(fcfe_operational)
            
            # Stocker les détails pour l'audit
            fcfe_details.append({
                'month': idx,
                'fcfe_operational': fcfe_operational,
                'exceptional_vat': exceptional_vat,
                'prime_excluded': prime_encaissee,
                'components': {
                    'net_income': net_income,
                    'depreciation': depreciation,
                    'capex_excluded': 'CAPEX retiré pour éviter double comptabilisation',
                    'delta_wc': delta_wc,
                    'principal': debt_principal,
                    'debt_issuance_excluded': 'Tirage dette initial exclu car finance CAPEX'
                }
            })
        
        self.fcfe_calculation_details = fcfe_details
        return np.array(fcfe_list)
    
    def calculate_npv_explicit(self, cashflows, discount_rate):
        """Calcul NPV explicite et vérifiable"""
        npv = cashflows[0]  # Investissement initial (doit être négatif)
        for t, cf in enumerate(cashflows[1:], 1):
            npv += cf / (1 + discount_rate)**t
        return npv

    def calculate_irr_with_verification(self, cashflows):
        """Calcul IRR avec vérification de cohérence"""
        try:
            # Vérifier que l'investissement initial est négatif
            if len(cashflows) == 0:
                return None, "ERREUR: Pas de cash flows"
            if cashflows[0] >= 0:
                return None, f"ERREUR: Investissement initial non négatif ({cashflows[0]})"
            
            # Calculer le TRI
            if npf is None:
                return None, "ERREUR: npf non disponible"
            
            irr = npf.irr(cashflows)
            
            if pd.isna(irr) or not np.isfinite(irr):
                return None, "ERREUR: TRI non calculable (numpy_financial)"
            
            # Vérifier la cohérence en recalculant la NPV au TRI
            npv_at_irr = self.calculate_npv_explicit(cashflows, irr)
            if abs(npv_at_irr) > 1.0:  # Devrait être ~0
                return None, f"ERREUR: NPV au TRI = {npv_at_irr:.2f} (devrait être ~0)"
            
            return irr, "OK"
        except Exception as e:
            return None, f"ERREUR: Exception dans calcul TRI: {str(e)}"
    
    def verify_equity_calculations_coherence(self, irr, npv, payback, investment, discount_rate):
        """
        Vérifie la cohérence mathématique des indicateurs equity
        """
        errors = []
        
        if pd.isna(irr) or pd.isna(npv) or pd.isna(discount_rate):
            return ["Valeurs manquantes dans les calculs"]
        
        # Règle 1 : Si NPV < 0, alors IRR < discount_rate
        if npv < 0 and irr > discount_rate:
            errors.append(f"INCOHÉRENCE: NPV négative ({npv:.0f}€) mais IRR ({irr:.1%}) > taux actualisation ({discount_rate:.1%})")
        
        # Règle 2 : Si NPV > 0, alors IRR > discount_rate
        if npv > 0 and irr < discount_rate:
            errors.append(f"INCOHÉRENCE: NPV positive ({npv:.0f}€) mais IRR ({irr:.1%}) < taux actualisation ({discount_rate:.1%})")
        
        # Règle 3 : Si payback < durée projet et NPV < 0, incohérence détectée
        if pd.notna(payback) and payback < 20 and npv < 0:
            errors.append(f"INCOHÉRENCE: Payback court ({payback:.1f} ans) avec NPV négative ({npv:.0f}€)")
        
        # Règle 4 : IRR extrême
        if abs(irr) > 1.0:  # IRR > 100% ou < -100%
            errors.append(f"AVERTISSEMENT: IRR extrême ({irr:.1%}), calcul potentiellement instable")
        
        return errors