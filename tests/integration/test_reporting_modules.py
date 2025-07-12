"""
Tests unitaires pour les modules de reporting refactorisés

Ce fichier teste les nouvelles classes CustomerReportingModule et AdminReportingModule
en utilisant des données mockées pour valider la logique de génération de rapport.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from datetime import datetime
import streamlit as st

# Import des modules à tester
from modules.reporting.customer_report import CustomerReportingModule
from modules.reporting.admin_report import AdminReportingModule


class TestCustomerReportingModule:
    """Tests pour le module de reporting client"""
    
    @pytest.fixture
    def customer_module(self):
        """Fixture pour créer une instance du module client"""
        return CustomerReportingModule()
    
    @pytest.fixture
    def mock_session_state(self):
        """Fixture pour mocker st.session_state avec des données de test"""
        return {
            'config': {
                'project_name': 'Projet Test',
                'puissance_kwc': 100,
                'capex': 150000,
                'opex': 5000,
                'target_dscr': 1.2,
                'constraint_min_project_irr_pct': 8.0,
                'constraint_min_equity_irr_pct': 12.0
            },
            'sites_config': {
                'site_1': {
                    'nom': 'Site de test',
                    'puissance_kwc': 100,
                    'capex': 150000,
                    'opex': 5000,
                    'type': 'producteur'
                }
            },
            'constrained_optim_results': {
                'scenario_optimal': {
                    'indicateurs_au_prix_optimal': {
                        'van_project': 50000,
                        'van_equity': 25000,
                        'tri_project': 12.5,
                        'tri_equity': 15.2,
                        'dscr_avg': 1.35,
                        'lcoe': 0.085,
                        'payback_simple': 8.5
                    },
                    'prix_optimal_const': 0.12,
                    'monthly_data': pd.DataFrame({
                        'date': pd.date_range('2024-01-01', periods=12, freq='MS'),
                        'Revenus_Total': np.random.uniform(8000, 12000, 12),
                        'OPEX': np.random.uniform(400, 600, 12),
                        'EBITDA': np.random.uniform(7000, 11000, 12),
                        'Service_Dette': np.random.uniform(3000, 4000, 12),
                        'FCFE': np.random.uniform(2000, 5000, 12)
                    }).set_index('date')
                }
            },
            'reports': {}
        }
    
    def test_module_initialization(self, customer_module):
        """Test l'initialisation du module client"""
        assert isinstance(customer_module, CustomerReportingModule)
        assert hasattr(customer_module, 'format_number')
        assert hasattr(customer_module, 'format_currency')
        assert hasattr(customer_module, 'generate_html_report')
    
    def test_format_number(self, customer_module):
        """Test le formatage des nombres"""
        assert customer_module.format_number(1234.56, 2, '€') == "1 234.56 €"
        assert customer_module.format_number(1000) == "1 000"
        assert customer_module.format_number(None) == "N/A"
        assert customer_module.format_number(np.nan) == "N/A"
    
    def test_format_currency(self, customer_module):
        """Test le formatage des devises"""
        assert customer_module.format_currency(1234.56) == "1 235 €"
        assert customer_module.format_currency(1234.56, 2) == "1 234.56 €"
    
    def test_format_percentage(self, customer_module):
        """Test le formatage des pourcentages"""
        assert customer_module.format_percentage(12.345) == "12.3%"
        assert customer_module.format_percentage(12.345, 2) == "12.35%"
        assert customer_module.format_percentage(None) == "N/A"
    
    @patch('streamlit.session_state')
    def test_get_optimization_data(self, mock_st_session_state, customer_module, mock_session_state):
        """Test la récupération des données d'optimisation"""
        mock_st_session_state.__getitem__.side_effect = lambda key: mock_session_state.get(key, {})
        mock_st_session_state.get.side_effect = lambda key, default=None: mock_session_state.get(key, default)
        
        scenario, indicators, prix = customer_module._get_optimization_data()
        
        assert scenario == 'scenario_optimal'
        assert indicators is not None
        assert indicators['van_project'] == 50000
        assert prix == 0.12
    
    @patch('streamlit.session_state')
    def test_generate_html_report_success(self, mock_st_session_state, customer_module, mock_session_state):
        """Test la génération réussie d'un rapport HTML client"""
        mock_st_session_state.__getitem__.side_effect = lambda key: mock_session_state.get(key, {})
        mock_st_session_state.get.side_effect = lambda key, default=None: mock_session_state.get(key, default)
        
        html_content = customer_module.generate_html_report(
            title="Rapport Test",
            client_name="Client Test",
            project_name="Projet Test"
        )
        
        assert isinstance(html_content, str)
        assert "Rapport Test" in html_content
        assert "Client Test" in html_content
        assert "<!DOCTYPE html>" in html_content
        assert "VAN Projet" in html_content or "50 000 €" in html_content
    
    @patch('streamlit.session_state')
    def test_generate_html_report_no_data(self, mock_st_session_state, customer_module):
        """Test la génération de rapport sans données"""
        # Session state vide
        mock_st_session_state.__getitem__.side_effect = lambda key: {}
        mock_st_session_state.get.side_effect = lambda key, default=None: {}
        
        html_content = customer_module.generate_html_report()
        
        assert isinstance(html_content, str)
        assert "<!DOCTYPE html>" in html_content
        # Le rapport doit pouvoir être généré même sans données


class TestAdminReportingModule:
    """Tests pour le module de reporting administrateur"""
    
    @pytest.fixture
    def admin_module(self):
        """Fixture pour créer une instance du module admin"""
        return AdminReportingModule()
    
    @pytest.fixture
    def mock_session_state_admin(self):
        """Fixture pour mocker st.session_state avec des données complètes pour l'admin"""
        monthly_data = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=24, freq='MS'),
            'Revenus_Total': np.random.uniform(8000, 12000, 24),
            'OPEX': np.random.uniform(400, 600, 24),
            'EBITDA': np.random.uniform(7000, 11000, 24),
            'Service_Dette': np.random.uniform(3000, 4000, 24),
            'FCFE': np.random.uniform(2000, 5000, 24),
            'Tax_Payment': np.random.uniform(500, 1000, 24),
            'Principal_Rembourse': np.random.uniform(1000, 2000, 24),
            'Amortissement': np.random.uniform(500, 800, 24)
        }).set_index('date')
        
        return {
            'config': {
                'target_dscr': 1.2,
                'constraint_min_project_irr_pct': 8.0,
                'constraint_min_equity_irr_pct': 12.0
            },
            'constrained_optim_results': {
                'scenario_optimal': {
                    'indicateurs_au_prix_optimal': {
                        'van_project': 75000,
                        'van_equity': 35000,
                        'tri_project': 13.2,
                        'tri_equity': 16.8,
                        'dscr_avg': 1.45,
                        'lcoe': 0.078,
                        'payback_simple': 7.8
                    },
                    'monthly_data': monthly_data
                }
            },
            'monte_carlo_results': {
                'simulation_results': pd.DataFrame({
                    'van_project': np.random.normal(75000, 15000, 1000),
                    'tri_project': np.random.normal(13.2, 2.5, 1000),
                    'dscr_avg': np.random.normal(1.45, 0.2, 1000),
                    'payback_simple': np.random.normal(7.8, 1.5, 1000)
                })
            },
            'df_analysis_results_by_size': pd.DataFrame({
                'puissance_kwc': [50, 75, 100, 125, 150, 200],
                'tri_project': [11.2, 12.8, 13.2, 12.9, 12.1, 11.5],
                'lcoe': [0.095, 0.085, 0.078, 0.082, 0.088, 0.092],
                'taux_autoconsommation': [85, 78, 72, 65, 58, 45]
            }),
            'admin_reports': {}
        }
    
    def test_admin_module_initialization(self, admin_module):
        """Test l'initialisation du module admin"""
        assert isinstance(admin_module, AdminReportingModule)
        assert hasattr(admin_module, 'generate_admin_report')
        assert hasattr(admin_module, '_generate_kpi_analysis_html')
        assert hasattr(admin_module, '_generate_financial_analysis_html')
        assert hasattr(admin_module, '_generate_monte_carlo_analysis_html')
        assert hasattr(admin_module, '_generate_lcoe_analysis_html')
    
    def test_admin_format_methods(self, admin_module):
        """Test les méthodes de formatage du module admin"""
        assert admin_module.format_number(1234.56, 2, '€') == "1 234.56 €"
        assert admin_module.format_currency(1234.56) == "1 235 €"
        assert admin_module.format_percentage(12.345) == "12.3%"
    
    @patch('streamlit.session_state')
    def test_generate_kpi_analysis_with_data(self, mock_st_session_state, admin_module, mock_session_state_admin):
        """Test la génération de l'analyse KPI avec données"""
        mock_st_session_state.__getitem__.side_effect = lambda key: mock_session_state_admin.get(key, {})
        mock_st_session_state.get.side_effect = lambda key, default=None: mock_session_state_admin.get(key, default)
        
        project_config = admin_module._get_project_configuration()
        html_content = admin_module._generate_kpi_analysis_html(project_config)
        
        assert isinstance(html_content, str)
        assert "Section 1 : Synthèse des Indicateurs de Performance" in html_content
        assert "VAN Projet" in html_content
        assert "75 000 €" in html_content or "75000" in html_content
        assert "Analyse et Interprétation" in html_content
        assert "Conclusions et Recommandations" in html_content
    
    @patch('streamlit.session_state')
    def test_generate_kpi_analysis_no_data(self, mock_st_session_state, admin_module):
        """Test la génération de l'analyse KPI sans données"""
        empty_state = {'config': {}, 'constrained_optim_results': {}}
        mock_st_session_state.__getitem__.side_effect = lambda key: empty_state.get(key, {})
        mock_st_session_state.get.side_effect = lambda key, default=None: empty_state.get(key, default)
        
        project_config = admin_module._get_project_configuration()
        html_content = admin_module._generate_kpi_analysis_html(project_config)
        
        assert isinstance(html_content, str)
        assert "ATTENTION" in html_content
        assert "Aucun résultat d'optimisation" in html_content
    
    @patch('streamlit.session_state')
    def test_generate_monte_carlo_analysis_with_data(self, mock_st_session_state, admin_module, mock_session_state_admin):
        """Test la génération de l'analyse Monte Carlo avec données"""
        mock_st_session_state.__getitem__.side_effect = lambda key: mock_session_state_admin.get(key, {})
        mock_st_session_state.get.side_effect = lambda key, default=None: mock_session_state_admin.get(key, default)
        
        project_config = admin_module._get_project_configuration()
        html_content = admin_module._generate_monte_carlo_analysis_html(project_config)
        
        assert isinstance(html_content, str)
        assert "Section 3 : Analyse de Robustesse (Monte Carlo)" in html_content
        assert "Robustesse globale du projet" in html_content
        assert "Probabilité" in html_content
    
    @patch('streamlit.session_state')
    def test_generate_monte_carlo_analysis_no_data(self, mock_st_session_state, admin_module):
        """Test la génération de l'analyse Monte Carlo sans données"""
        empty_state = {'monte_carlo_results': {}}
        mock_st_session_state.__getitem__.side_effect = lambda key: empty_state.get(key, {})
        mock_st_session_state.get.side_effect = lambda key, default=None: empty_state.get(key, default)
        
        project_config = admin_module._get_project_configuration()
        html_content = admin_module._generate_monte_carlo_analysis_html(project_config)
        
        assert isinstance(html_content, str)
        assert "ATTENTION" in html_content
        assert "Monte Carlo n'a pas été exécutée" in html_content
    
    @patch('streamlit.session_state')
    def test_generate_lcoe_analysis_with_data(self, mock_st_session_state, admin_module, mock_session_state_admin):
        """Test la génération de l'analyse LCOE avec données"""
        mock_st_session_state.__getitem__.side_effect = lambda key: mock_session_state_admin.get(key, {})
        mock_st_session_state.get.side_effect = lambda key, default=None: mock_session_state_admin.get(key, default)
        
        project_config = admin_module._get_project_configuration()
        html_content = admin_module._generate_lcoe_analysis_html(project_config)
        
        assert isinstance(html_content, str)
        assert "Section 4 : Analyse du LCOE et de la Taille du Projet" in html_content
        assert "Taille optimale identifiée" in html_content
        assert "Dimensionnement optimal" in html_content
    
    @patch('streamlit.session_state')
    def test_generate_lcoe_analysis_no_data(self, mock_st_session_state, admin_module):
        """Test la génération de l'analyse LCOE sans données"""
        empty_state = {'df_analysis_results_by_size': None}
        mock_st_session_state.__getitem__.side_effect = lambda key: empty_state.get(key, {})
        mock_st_session_state.get.side_effect = lambda key, default=None: empty_state.get(key, default)
        
        project_config = admin_module._get_project_configuration()
        html_content = admin_module._generate_lcoe_analysis_html(project_config)
        
        assert isinstance(html_content, str)
        assert "ATTENTION" in html_content
        assert "analyse par taille de projet n'a pas été exécutée" in html_content
    
    @patch('streamlit.session_state')
    def test_generate_full_admin_report(self, mock_st_session_state, admin_module, mock_session_state_admin):
        """Test la génération complète du rapport administrateur"""
        mock_st_session_state.__getitem__.side_effect = lambda key: mock_session_state_admin.get(key, {})
        mock_st_session_state.get.side_effect = lambda key, default=None: mock_session_state_admin.get(key, default)
        
        html_content = admin_module.generate_admin_report(
            title="Rapport Test Admin",
            project_name="Projet Test Admin"
        )
        
        assert isinstance(html_content, str)
        assert "<!DOCTYPE html>" in html_content
        assert "Rapport Test Admin" in html_content
        assert "Section 1 : Synthèse des Indicateurs de Performance" in html_content
        assert "Section 2 : Analyse Financière Détaillée" in html_content
        assert "Section 3 : Analyse de Robustesse (Monte Carlo)" in html_content
        assert "Section 4 : Analyse du LCOE et de la Taille du Projet" in html_content
        assert "page-break" in html_content  # Vérifier le formatage PDF
    
    @patch('streamlit.session_state')
    def test_generate_admin_report_with_errors(self, mock_st_session_state, admin_module):
        """Test la génération du rapport admin avec gestion d'erreurs"""
        # Simuler une erreur en mockant incorrectement
        mock_st_session_state.__getitem__.side_effect = Exception("Session state error")
        
        html_content = admin_module.generate_admin_report()
        
        assert isinstance(html_content, str)
        assert "Erreur lors de la génération du rapport" in html_content
        assert "Session state error" in html_content
    
    def test_css_styles_formatting(self, admin_module):
        """Test que les styles CSS sont bien formatés pour le PDF"""
        css_styles = admin_module._get_admin_css_styles()
        
        assert isinstance(css_styles, str)
        assert "@media print" in css_styles
        assert "page-break-after: always" in css_styles
        assert ".report-section" in css_styles
        assert ".page-break" in css_styles
        assert "font-family" in css_styles
    
    def test_convert_plotly_to_base64_none_input(self, admin_module):
        """Test la conversion Plotly avec input None"""
        result = admin_module._convert_plotly_to_base64(None)
        assert result == ""
    
    def test_logo_base64_fallback(self, admin_module):
        """Test la récupération du logo avec fallback"""
        # Le logo peut ne pas exister dans l'environnement de test
        logo_b64 = admin_module.get_logo_base64()
        assert isinstance(logo_b64, str)  # Peut être vide si le fichier n'existe pas


class TestIntegrationReporting:
    """Tests d'intégration pour les modules de reporting"""
    
    @patch('streamlit.session_state')
    def test_both_modules_compatibility(self, mock_st_session_state):
        """Test que les deux modules peuvent coexister et fonctionner ensemble"""
        mock_data = {
            'config': {'project_name': 'Test Integration'},
            'constrained_optim_results': {},
            'reports': {},
            'admin_reports': {}
        }
        
        mock_st_session_state.__getitem__.side_effect = lambda key: mock_data.get(key, {})
        mock_st_session_state.get.side_effect = lambda key, default=None: mock_data.get(key, default)
        
        customer_module = CustomerReportingModule()
        admin_module = AdminReportingModule()
        
        # Les deux modules doivent pouvoir être instanciés
        assert isinstance(customer_module, CustomerReportingModule)
        assert isinstance(admin_module, AdminReportingModule)
        
        # Les deux doivent pouvoir générer des rapports (même vides)
        customer_html = customer_module.generate_html_report()
        admin_html = admin_module.generate_admin_report()
        
        assert isinstance(customer_html, str)
        assert isinstance(admin_html, str)
        assert "<!DOCTYPE html>" in customer_html
        assert "<!DOCTYPE html>" in admin_html


if __name__ == "__main__":
    # Lancer les tests si le script est exécuté directement
    pytest.main([__file__, "-v"])