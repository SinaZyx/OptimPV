"""
Tests unitaires pour les calculs financiers professionnels d'OptimPV
Teste particulièrement les cas extrêmes de calcul du TRI
"""

import numpy as np
import pandas as pd
import pytest
import sys
import os

# Ajouter le chemin vers les modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from modules.engine_module.core_analyzer import AnalysisEngine


class TestIRRCalculationProfessional:
    
    def setup_method(self):
        """Initialiser l'engine pour les tests"""
        self.engine = AnalysisEngine(
            config={}, 
            scenarios={}, 
            sites_data={}
        )
    
    def test_calculate_net_equity_investment_professional(self):
        """Test du calcul professionnel de l'investissement net"""
        # Cas normal
        net_equity = self.engine.calculate_net_equity_investment_professional(
            capex_total=50000,
            debt_amount=30000,
            subvention_montant=3600
        )
        
        # Fonds propres nets = (50000 - 30000) - 3600 = 16400
        assert net_equity == 16400
        assert hasattr(self.engine, 'equity_calculation_details')
        assert self.engine.equity_calculation_details['gross_equity'] == 20000
        
    def test_irr_extreme_cases(self):
        """Test les cas extrêmes de calcul du TRI"""
        
        # Cas 1 : Investissement faible avec gros flux initial (situation du bug)
        investment = 9400  # Situation réelle du problème
        cashflows = [17800, 1200, 1200, 1200, 1200]  # Premier flux très élevé
        
        irr, method = self.engine.calculate_irr_professional(cashflows, investment)
        
        # Doit utiliser MIRR car flux atypiques
        assert method == 'MIRR' or not np.isnan(irr)
        if not np.isnan(irr):
            assert -1.0 < irr < 10.0, f"TRI irréaliste : {irr}"
    
    def test_mirr_calculation(self):
        """Test du calcul MIRR"""
        # Cas avec flux qui changent de signe
        cashflows = [-10000, 15000, -5000, 8000, 3000]
        
        mirr = self.engine.calculate_mirr(cashflows, 0.06, 0.06)
        
        assert not np.isnan(mirr)
        assert -0.5 < mirr < 2.0, f"MIRR irréaliste : {mirr}"
    
    def test_fcfe_professional_calculation(self):
        """Test du calcul FCFE professionnel avec isolation des flux exceptionnels"""
        
        # Créer un DataFrame de test avec flux exceptionnels
        monthly_data = pd.DataFrame({
            'Resultat_Net': [1000, 1000, 1000],
            'Amortissement': [500, 500, 500],
            'Delta_BFR_Mensuel': [0, 0, 0],
            'CAPEX_Initial_Mensuel': [0, 0, 0],
            'Principal_Rembourse': [200, 200, 200],
            'VAT_Payment': [100, 12000, 100],  # Flux TVA exceptionnel au mois 2
            'Revenus_Total': [3000, 3000, 3000],
            'Prime_Autoconso_Encaissee': [0, 3600, 0]  # Prime au mois 2
        })
        
        fcfe_array = self.engine.calculate_fcfe_professional(monthly_data, 3600)
        
        # Vérifier que la prime et la TVA exceptionnelle sont exclues
        assert hasattr(self.engine, 'fcfe_calculation_details')
        details = self.engine.fcfe_calculation_details
        
        # Mois 2 (index 1) doit avoir des exclusions
        month_2_details = details[1]
        assert month_2_details['exceptional_vat'] > 0
        assert month_2_details['prime_excluded'] > 0
        
        # FCFE du mois 2 doit être nettoyé
        expected_fcfe_month_2 = 1000 + 500 - 200  # Sans TVA exceptionnelle ni prime
        assert abs(fcfe_array[1] - expected_fcfe_month_2) < 1e-6
    
    def test_professional_irr_vs_standard(self):
        """Compare les résultats TRI professionnel vs standard"""
        
        # Cas où le TRI standard échoue
        investment = 1000
        cashflows = [5000, -1000, 2000, 1000]  # Flux qui changent de signe
        
        # Méthode professionnelle
        irr_pro, method_pro = self.engine.calculate_irr_professional(cashflows, investment)
        
        # Méthode standard numpy_financial (pour comparaison)
        try:
            import numpy_financial as npf
            cf_complete = [-investment] + list(cashflows)
            irr_std = npf.irr(cf_complete)
        except:
            irr_std = np.nan
        
        # La méthode professionnelle doit donner un résultat même si standard échoue
        if np.isnan(irr_std):
            assert not np.isnan(irr_pro) or method_pro == 'MIRR'
    
    def test_edge_case_zero_investment(self):
        """Test cas limite : investissement nul"""
        
        net_equity = self.engine.calculate_net_equity_investment_professional(
            capex_total=10000,
            debt_amount=7000,
            subvention_montant=3000  # Subvention = fonds propres bruts
        )
        
        assert net_equity == 0
        
        # Le calcul TRI doit gérer ce cas
        cashflows = [1000, 1000, 1000]
        irr, method = self.engine.calculate_irr_professional(cashflows, abs(net_equity))
        
        # Doit retourner NaN car pas d'investissement
        assert np.isnan(irr)
    
    def test_negative_equity_case(self):
        """Test cas limite : fonds propres nets négatifs (sur-subvention)"""
        
        net_equity = self.engine.calculate_net_equity_investment_professional(
            capex_total=10000,
            debt_amount=5000,
            subvention_montant=6000  # Subvention > fonds propres bruts
        )
        
        assert net_equity == -1000  # Négatif
        
        # Documenter ce cas particulier
        assert self.engine.equity_calculation_details['net_equity_investment'] == -1000


def test_irr_extreme_cases():
    """Test les cas extrêmes de calcul du TRI"""
    engine = AnalysisEngine({}, {}, {})
    
    # Cas 1 : Investissement faible avec gros flux initial
    investment = 1000
    cashflows = [5000, 100, 100, 100, 100]
    irr, method = engine.calculate_irr_professional(cashflows, investment)
    assert -1.0 < irr < 10.0 or method == 'MIRR', f"TRI irréaliste : {irr}"
    
    # Cas 2 : Flux qui changent de signe
    cashflows2 = [1000, -500, 1000, -200, 500]
    irr2, method2 = engine.calculate_irr_professional(cashflows2, 1000)
    # Devrait utiliser MIRR
    assert method2 == 'MIRR' or (not np.isnan(irr2) and 0 < irr2 < 1.0)


if __name__ == "__main__":
    # Exécuter les tests
    test_irr_extreme_cases()
    print("✅ Tests de base passés avec succès")
    
    # Pour pytest complet, utiliser : pytest test_irr_calculation_professional.py -v