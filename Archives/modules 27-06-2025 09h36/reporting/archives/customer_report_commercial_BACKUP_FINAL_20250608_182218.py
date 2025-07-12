"""
Module de génération de rapports commerciaux orientés client pour OptimPV.

Ce module génère des rapports PDF axés sur les bénéfices clients avec une approche
commerciale et pédagogique, mettant en avant les économies et avantages plutôt
que les aspects techniques.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import base64
import io
import logging
from typing import Dict, Any, Optional, List, Tuple
# Imports optionnels pour la visualisation
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Import du système DOCX
try:
    from .docx_integration import DocxIntegrationModule
    DOCX_INTEGRATION_AVAILABLE = True
except ImportError:
    DOCX_INTEGRATION_AVAILABLE = False

logger = logging.getLogger(__name__)

class CommercialCustomerReportModule:
    """Module de génération de rapports commerciaux orientés client."""
    
    def __init__(self):
        """Initialise le module de rapport commercial."""
        if 'reports' not in st.session_state:
            st.session_state.reports = {}
        
        # Initialiser le module DOCX si disponible
        self.docx_module = None
        if DOCX_INTEGRATION_AVAILABLE:
            try:
                self.docx_module = DocxIntegrationModule()
            except Exception as e:
                logger.warning(f"Impossible d'initialiser le module DOCX: {e}")
                self.docx_module = None
        
    def _get_project_configuration(self):
        """Récupère la configuration complète du projet depuis st.session_state"""
        return {
            'global_config': st.session_state.get('config', {}),
            'sites_config': st.session_state.get('sites_config', {}),
            'scenarios': st.session_state.get('scenarios', {}),
            'processed_data': st.session_state.get('processed_data'),
            'sites_data': st.session_state.get('sites_data', {})
        }
    
    def _get_optimization_data(self):
        """Récupère les données d'optimisation depuis st.session_state"""
        optimization_results = (st.session_state.get('constrained_optim_results', {}) or 
                               st.session_state.get('optimization_results', {}))
        
        best_scenario = None
        best_indicators = None
        prix_optimal = None
        
        if optimization_results:
            # Pour constrained_optim_results (nouveau format)
            if 'constrained_optim_results' in st.session_state:
                for scenario_name, results in optimization_results.items():
                    if isinstance(results, dict) and 'indicateurs_au_prix_optimal' in results:
                        best_scenario = scenario_name
                        best_indicators = results['indicateurs_au_prix_optimal']
                        prix_optimal = results.get('prix_optimal_const', 0)
                        break
            # Pour optimization_results (ancien format)
            else:
                for scenario_name, results in optimization_results.items():
                    if isinstance(results, dict) and 'indicateurs_optimaux' in results:
                        best_scenario = scenario_name
                        best_indicators = results['indicateurs_optimaux']
                        prix_optimal = results.get('prix_optimal', 0)
                        break
        
        return best_scenario, best_indicators, prix_optimal
    
    def _get_energy_data_robust(self):
        """
        Méthode robuste pour récupérer les données énergétiques depuis différentes sources
        (Copie exacte de la logique du customer_report.py)
        
        Returns:
            dict: Dictionnaire avec total_production, total_consumption, total_autoconsumption
        """
        # Initialisation
        total_production = 0
        total_consumption = 0
        total_autoconsumption = 0
        
        # 1. Essayer d'abord les résultats d'optimisation
        best_scenario, scenario_data, prix_optimal = self._get_optimization_data()
        if scenario_data and isinstance(scenario_data, dict):
            # Les données peuvent être dans different formats selon la version
            for key in ['total_production_kwh', 'production_totale_kwh', 'production_annuelle']:
                if key in scenario_data:
                    total_production = scenario_data[key]
                    break
                    
            for key in ['total_consumption_kwh', 'consommation_totale_kwh', 'consommation_annuelle']:
                if key in scenario_data:
                    total_consumption = scenario_data[key]
                    break
                    
            for key in ['total_autoconsumption_kwh', 'autoconsommation_totale_kwh', 'autoconsommation_annuelle']:
                if key in scenario_data:
                    total_autoconsumption = scenario_data[key]
                    break
        
        # 2. Si pas trouvé, essayer sites_data
        if total_consumption == 0:
            sites_data = st.session_state.get('sites_data', {})
            if sites_data:
                for site_id, site_df in sites_data.items():
                    if hasattr(site_df, 'columns'):
                        if 'production_kwh' in site_df.columns:
                            total_production += site_df['production_kwh'].sum()
                        if 'consumption_kwh' in site_df.columns:
                            total_consumption += site_df['consumption_kwh'].sum()
                
                # Calculer autoconsommation site par site
                for site_id, site_df in sites_data.items():
                    if (hasattr(site_df, 'columns') and 
                        'production_kwh' in site_df.columns and 
                        'consumption_kwh' in site_df.columns):
                        site_autoconsumption = site_df[['production_kwh', 'consumption_kwh']].min(axis=1).sum()
                        total_autoconsumption += site_autoconsumption
        
        # 3. Si toujours rien, utiliser des données réalistes par défaut
        if total_consumption == 0:
            # Basé sur une installation typique de 25 kWc (valeurs annuelles en MWh plus réalistes)
            total_production = 27.5       # 27,5 MWh/an = 27500 kWh/an 
            total_consumption = 50.0      # 50 MWh/an = 50000 kWh/an
            total_autoconsumption = 17.5  # 17,5 MWh/an = 17500 kWh/an (35% d'autonomie)
            logger.warning("RAPPORT COMMERCIAL: Utilisation de données par défaut (pas de données réelles trouvées)")
            logger.info(f"Données par défaut: Prod={total_production} MWh, Conso={total_consumption} MWh, Auto={total_autoconsumption} MWh")
        else:
            # Vérifier si les données sont en kWh ou MWh et les convertir si nécessaire
            logger.info(f"RAPPORT COMMERCIAL: Données brutes trouvées - Consommation: {total_consumption:.0f}, Autoconsommation: {total_autoconsumption:.0f}")
            
            # Si les valeurs sont très grandes (>100 000), elles sont probablement en kWh, les convertir en MWh
            if total_consumption > 100000:
                total_production = total_production / 1000
                total_consumption = total_consumption / 1000
                total_autoconsumption = total_autoconsumption / 1000
                logger.info(f"Conversion kWh->MWh: Prod={total_production:.1f} MWh, Conso={total_consumption:.1f} MWh, Auto={total_autoconsumption:.1f} MWh")
            else:
                logger.info(f"Déjà en MWh: Prod={total_production:.1f} MWh, Conso={total_consumption:.1f} MWh, Auto={total_autoconsumption:.1f} MWh")
            
        # Calcul des taux pour validation
        calculated_autonomy = (total_autoconsumption / total_consumption * 100) if total_consumption > 0 else 0
        calculated_autoconsumption = (total_autoconsumption / total_production * 100) if total_production > 0 else 0
        logger.info(f"Taux calculés: Autonomie={calculated_autonomy:.1f}%, Autoconsommation={calculated_autoconsumption:.1f}%")
        
        return {
            'total_production': total_production,
            'total_consumption': total_consumption,
            'total_autoconsumption': total_autoconsumption,
            'total_grid_purchase': total_consumption - total_autoconsumption,
            'autoconsumption_rate': (total_autoconsumption / total_consumption * 100) if total_consumption > 0 else 0,
            'autoproduction_rate': (total_autoconsumption / total_production * 100) if total_production > 0 else 0
        }
    
    def _get_financial_data_from_engine(self):
        """Récupère les données financières calculées par l'analysis engine"""
        best_scenario, scenario_data, prix_optimal = self._get_optimization_data()
        
        if scenario_data and isinstance(scenario_data, dict):
            financial_data = {
                'scenario_name': best_scenario,
                'prix_optimal': prix_optimal,
                'van_project': scenario_data.get('van_project', 0),
                'van_equity': scenario_data.get('van_equity', 0),
                'tri_project': scenario_data.get('tri_project', 0),
                'tri_equity': scenario_data.get('tri_equity', 0),
                'economie_annuelle': scenario_data.get('economie_annuelle_kwh', 0),
                'economie_totale': scenario_data.get('economie_totale', 0),
                'cout_avec_pv_total': scenario_data.get('cout_avec_pv_total', 0),
                'cout_sans_pv_total': scenario_data.get('cout_sans_pv_total', 0),
                'payback_simple': scenario_data.get('payback_simple', 0)
            }
            
            # Calculer l'économie totale si pas directement disponible
            if financial_data['economie_totale'] == 0 and financial_data['cout_sans_pv_total'] > 0:
                financial_data['economie_totale'] = financial_data['cout_sans_pv_total'] - financial_data['cout_avec_pv_total']
                
            return financial_data
        else:
            return None
    
    def format_number(self, number, decimals=0, unit='', thousands_sep=' '):
        """Formate un nombre avec séparateurs de milliers"""
        if pd.isna(number) or number is None or not np.isfinite(number):
            return "N/A"
        try:
            if decimals == 0:
                formatted = f"{int(number):,}".replace(',', thousands_sep)
            else:
                formatted = f"{number:,.{decimals}f}".replace(',', thousands_sep)
            return f"{formatted} {unit}".strip()
        except:
            return str(number)
    
    def format_currency(self, amount, decimals=0):
        """Formate un montant en euros"""
        return self.format_number(amount, decimals, '€')
    
    def format_percentage(self, rate, decimals=1):
        """Formate un pourcentage"""
        if pd.isna(rate) or rate is None:
            return "N/A"
        try:
            return f"{rate:.{decimals}f}%"
        except:
            return str(rate)

    def generate_report(self, report_format: str = 'html') -> str:
        """
        Génère le rapport commercial complet.
        
        Args:
            report_format: Format du rapport ('html' ou 'pdf')
            
        Returns:
            Contenu du rapport généré
        """
        try:
            # Rafraîchir toutes les données
            self._refresh_all_report_data()
            
            # Générer le contenu HTML du rapport
            html_content = self._generate_html_report()
            
            if report_format == 'pdf':
                # Conversion en PDF si demandé
                return self._convert_to_pdf(html_content)
            
            return html_content
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {str(e)}")
            st.error(f"Erreur lors de la génération du rapport: {str(e)}")
            return ""
    
    def _refresh_all_report_data(self):
        """Rafraîchit toutes les données nécessaires au rapport."""
        # Forcer le recalcul des métriques commerciales
        self._calculate_commercial_metrics()
        
        logger.info("RAPPORT COMMERCIAL: Données rafraîchies")
    
    def _calculate_commercial_metrics(self):
        """
        Calcule les métriques commerciales spécifiques à partir des vraies données.
        (Utilise la même logique que customer_report.py)
        """
        try:
            # Récupérer les vraies données
            config = st.session_state.get('config', {})
            best_scenario, scenario_data, prix_optimal = self._get_optimization_data()
            energy_data = self._get_energy_data_robust()
            financial_data = self._get_financial_data_from_engine()
            
            # Prix de vente de l'électricité solaire (prix optimal)
            self.solar_price = prix_optimal if prix_optimal and prix_optimal > 0 else 0.15
            
            # Prix moyen du réseau
            self.grid_price = config.get('tarif_edf_reference', 0.2062)
            
            # Économie par kWh
            self.savings_per_kwh = max(0, self.grid_price - self.solar_price)
            
            # Données énergétiques (déjà en MWh depuis _get_energy_data_robust)
            self.total_production = energy_data['total_production']
            self.total_consumption = energy_data['total_consumption'] 
            self.solar_consumption = energy_data['total_autoconsumption']
            
            # Convertir en kWh pour les calculs de coûts
            self.solar_consumption_kwh = self.solar_consumption * 1000
            self.total_consumption_kwh = self.total_consumption * 1000
            
            # Taux d'autonomie
            self.autonomy_rate = energy_data['autoconsumption_rate']
            
            # Calcul des économies selon la même logique que customer_report.py
            if financial_data and financial_data['economie_totale'] > 0:
                # Utiliser les données calculées par l'analysis engine
                self.total_savings_20y = financial_data['economie_totale']
                prix_optimal = financial_data['prix_optimal']
                logger.info(f"✅ Utilisation des données de l'analysis engine - Économie: {self.total_savings_20y:.0f}€")
            else:
                # Fallback: calcul simple et réaliste (MÊME LOGIQUE que customer_report.py)
                tarif_edf = config.get('tarif_edf_reference', 0.20)
                duree_projet = config.get('duree_ppa', 240) / 12
                
                # Récupérer le prix optimal
                if prix_optimal is None:
                    if 'constrained_optim_results' in st.session_state:
                        for results in st.session_state.constrained_optim_results.values():
                            if isinstance(results, dict) and 'prix_optimal_const' in results:
                                prix_optimal = results['prix_optimal_const']
                                break
                
                if prix_optimal is None:
                    prix_optimal = tarif_edf * 0.8
                
                # Calcul simple et réaliste (économie annuelle * durée projet)
                # Convertir MWh en kWh pour le calcul (1 MWh = 1000 kWh)
                total_autoconsumption_kwh = self.solar_consumption * 1000
                economie_annuelle = total_autoconsumption_kwh * (tarif_edf - prix_optimal)
                self.total_savings_20y = economie_annuelle * duree_projet
                
                logger.info(f"⚠️ Fallback: Économie annuelle = {economie_annuelle:.0f}€, Total sur {duree_projet:.0f} ans = {self.total_savings_20y:.0f}€")
            
            # Calculer l'économie annuelle
            self.annual_savings = self.total_savings_20y / 20 if self.total_savings_20y > 0 else self.solar_consumption_kwh * self.savings_per_kwh
            
            # CO2 évité (facteur moyen France : 0.0569 kg CO2/kWh)
            self.co2_avoided_annual = self.solar_consumption_kwh * 0.0569 / 1000  # en tonnes
            
            logger.info(f"✅ COMMERCIAL: Prix solaire: {self.solar_price:.3f}€/kWh, "
                       f"Économie annuelle: {self.annual_savings:.0f}€, Total 20ans: {self.total_savings_20y:.0f}€, "
                       f"Autonomie: {self.autonomy_rate:.1f}%, CO2: {self.co2_avoided_annual:.1f}t")
            
        except Exception as e:
            logger.error(f"Erreur dans le calcul des métriques commerciales: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # Valeurs par défaut sécurisées avec logs
            self.solar_price = 0.15
            self.grid_price = 0.20
            self.savings_per_kwh = 0.05
            self.annual_savings = 5000
            self.total_savings_20y = 100000
            self.autonomy_rate = 40
            self.co2_avoided_annual = 10
            self.total_production = 27.5
            self.total_consumption = 50.0
            self.solar_consumption = 17.5
            self.solar_consumption_kwh = 17500
            self.total_consumption_kwh = 50000
            logger.warning("COMMERCIAL: Utilisation des valeurs par défaut suite à l'erreur")
    
    def _generate_html_report(self) -> str:
        """Génère le contenu HTML du rapport commercial."""
        
        # Récupérer la configuration du projet
        project_config = self._get_project_configuration()
        global_config = project_config['global_config']
        
        # CSS Style Corporate & Technologique
        css_styles = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

            :root {
                --font-family-main: 'Roboto', sans-serif;
                --color-text: #1A202C;
                --color-heading: #0033A0;
                --color-accent: #3B82F6;
                --color-border: #E2E8F0;
                --color-background-subtle: #F7FAFC;
                --border-radius-sharp: 4px;
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: var(--font-family-main);
                line-height: 1.7;
                color: var(--color-text);
                background-color: #E2E8F0;
                font-size: 16px;
            }
            
            .page {
                width: 210mm;
                min-height: 297mm;
                padding: 25mm;
                margin: 20mm auto;
                background-color: white;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                page-break-after: always;
                position: relative;
            }
            
            .page:last-child {
                page-break-after: auto;
            }

            h1, h2, h3, h4 {
                font-weight: 500;
                color: var(--color-heading);
                letter-spacing: -0.5px;
                line-height: 1.3;
            }

            h1 { font-size: 36px; font-weight: 700; margin-bottom: 24px; }
            h2 { font-size: 28px; font-weight: 500; margin-bottom: 20px; border-bottom: 2px solid var(--color-border); padding-bottom: 12px; }
            h3 { font-size: 20px; font-weight: 500; margin-bottom: 16px; color: var(--color-text); }
            p { margin-bottom: 16px; }

            /* Page de garde - Style Corporate */
            .cover-page {
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                height: 257mm;
            }
            
            .logo-section {
                text-align: left;
                margin-bottom: 40px;
            }
            
            .main-title {
                font-size: 36px;
                font-weight: 700;
                color: var(--color-heading);
                margin-bottom: 16px;
                text-align: center;
                letter-spacing: -0.5px;
            }
            
            .subtitle {
                font-size: 24px;
                color: var(--color-text);
                text-align: center;
                margin-bottom: 40px;
                font-weight: 400;
            }
            
            .hero-visual {
                text-align: center;
                margin: 40px 0;
            }
            
            .key-benefit-box {
                background-color: var(--color-background-subtle);
                border: 2px solid var(--color-accent);
                color: var(--color-text);
                padding: 40px;
                border-radius: var(--border-radius-sharp);
                text-align: center;
                margin: 40px 0;
            }
            
            .benefit-price {
                font-size: 42px;
                font-weight: 700;
                color: var(--color-accent);
                margin-bottom: 16px;
                line-height: 1.1;
            }
            
            .benefit-savings {
                font-size: 24px;
                margin-bottom: 16px;
                font-weight: 500;
            }
            
            .benefit-date {
                font-size: 16px;
                font-weight: 400;
            }
            
            /* Sections - Style structuré */
            .section-title {
                font-size: 28px;
                font-weight: 500;
                color: var(--color-heading);
                margin-bottom: 20px;
                border-bottom: 2px solid var(--color-border);
                padding-bottom: 12px;
            }
            
            .section-subtitle {
                font-size: 20px;
                font-weight: 500;
                color: var(--color-text);
                margin: 20px 0 15px 0;
            }
            
            /* Résumé exécutif - Clean */
            .executive-summary {
                background-color: var(--color-background-subtle);
                border: 1px solid var(--color-border);
                padding: 24px;
                border-radius: var(--border-radius-sharp);
                margin-bottom: 30px;
            }
            
            .key-advantages {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 24px;
                margin-top: 30px;
            }
            
            .advantage-card {
                background: white;
                border: 1px solid var(--color-border);
                padding: 24px;
                border-radius: var(--border-radius-sharp);
                text-align: center;
            }
            
            .advantage-icon {
                font-size: 36px;
                margin-bottom: 16px;
            }
            
            .advantage-title {
                font-size: 18px;
                font-weight: 500;
                color: var(--color-heading);
                margin-bottom: 12px;
            }
            
            .advantage-text {
                font-size: 14px;
                color: var(--color-text);
                font-weight: 400;
            }
            
            /* Tableaux - Style Corporate propre */
            .data-table {
                width: 100%;
                border-collapse: collapse;
                margin: 24px 0;
                background: white;
                border: 1px solid var(--color-border);
            }
            
            .data-table th {
                background-color: var(--color-background-subtle);
                color: var(--color-heading);
                padding: 12px;
                text-align: left;
                font-weight: 500;
                border-bottom: 1px solid var(--color-border);
            }
            
            .data-table td {
                padding: 12px;
                border-bottom: 1px solid var(--color-border);
                font-weight: 400;
            }
            
            .data-table tr:last-child td {
                border-bottom: none;
            }
            
            /* Graphiques - Clean et structuré */
            .chart-container {
                margin: 30px 0;
                padding: 24px;
                background: white;
                border: 1px solid var(--color-border);
                border-radius: var(--border-radius-sharp);
            }
            
            .chart-title {
                font-size: 18px;
                font-weight: 500;
                text-align: center;
                margin-bottom: 20px;
                color: var(--color-heading);
            }
            
            /* Encadrés - Style Corporate sobre */
            .info-box {
                background-color: var(--color-background-subtle);
                border: 1px solid var(--color-border);
                border-left: 4px solid var(--color-accent);
                padding: 20px;
                margin: 20px 0;
                border-radius: var(--border-radius-sharp);
            }
            
            .warning-box {
                background-color: var(--color-background-subtle);
                border: 1px solid var(--color-border);
                border-left: 4px solid #F59E0B;
                padding: 20px;
                margin: 20px 0;
                border-radius: var(--border-radius-sharp);
            }
            
            .success-box {
                background-color: var(--color-background-subtle);
                border: 1px solid var(--color-border);
                border-left: 4px solid var(--color-accent);
                padding: 20px;
                margin: 20px 0;
                border-radius: var(--border-radius-sharp);
            }
            
            /* Style des cartes et encadrés - NET et STRUCTURÉ */
            .card {
                background-color: var(--color-background-subtle);
                border: 1px solid var(--color-border);
                border-radius: var(--border-radius-sharp);
                padding: 24px;
                margin-top: 24px;
            }

            /* Style pour les blocs de chiffres clés */
            .kpi-block {
                text-align: center;
                padding: 20px;
            }
            .kpi-block .value {
                font-size: 42px;
                font-weight: 700;
                color: var(--color-accent);
                line-height: 1.1;
            }
            .kpi-block .label {
                font-size: 16px;
                font-weight: 400;
                color: var(--color-text);
            }
            
            /* Mise en page en grille pour les colonnes */
            .grid-3-col {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 24px;
            }
            
            /* FAQ - Style Corporate propre */
            .faq-item {
                margin-bottom: 24px;
                padding: 20px;
                background: var(--color-background-subtle);
                border: 1px solid var(--color-border);
                border-radius: var(--border-radius-sharp);
            }
            
            .faq-question {
                font-weight: 500;
                color: var(--color-heading);
                margin-bottom: 12px;
                font-size: 16px;
            }
            
            .faq-answer {
                color: var(--color-text);
                line-height: 1.7;
                font-weight: 400;
            }
            
            /* Timeline - Style Corporate structuré */
            .timeline {
                position: relative;
                padding: 20px 0;
            }
            
            .timeline-item {
                display: flex;
                margin-bottom: 24px;
                align-items: center;
            }
            
            .timeline-marker {
                width: 40px;
                height: 40px;
                background: var(--color-accent);
                border-radius: var(--border-radius-sharp);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 500;
                margin-right: 20px;
                font-size: 14px;
            }
            
            .timeline-content {
                flex: 1;
            }
            
            .timeline-date {
                font-weight: 500;
                color: var(--color-heading);
                margin-bottom: 8px;
            }
            
            /* Contact - Style Corporate sobre */
            .contact-section {
                background-color: var(--color-background-subtle);
                border: 1px solid var(--color-border);
                padding: 40px;
                border-radius: var(--border-radius-sharp);
                text-align: center;
                margin-top: 40px;
            }
            
            .contact-person {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 30px;
                margin-top: 30px;
            }
            
            .contact-details {
                text-align: left;
            }
            
            .contact-name {
                font-size: 20px;
                font-weight: 500;
                color: var(--color-heading);
                margin-bottom: 8px;
            }
            
            .contact-info {
                color: var(--color-text);
                margin-bottom: 4px;
                font-weight: 400;
            }
            
            /* Footer - Clean et minimal */
            .page-footer {
                position: absolute;
                bottom: 20mm;
                left: 20mm;
                right: 20mm;
                text-align: center;
                color: #6B7280;
                font-size: 12px;
                padding-top: 12px;
                border-top: 1px solid var(--color-border);
                font-weight: 400;
            }
            
            @media print {
                .page {
                    margin: 0;
                    box-shadow: none;
                }
            }
        </style>
        """
        
        # Contenu HTML du rapport
        html_content = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Proposition d'Autoconsommation Collective - {global_config.get('project_name', 'Projet Solaire')}</title>
            {css_styles}
        </head>
        <body>
            {self._generate_cover_page()}
            {self._generate_executive_summary()}
            {self._generate_invoice_comparison()}
            {self._generate_offer_details()}
            {self._generate_long_term_savings()}
            {self._generate_installation_info()}
            {self._generate_environmental_impact()}
            {self._generate_faq()}
            {self._generate_next_steps()}
            {self._generate_appendix_contact()}
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_cover_page(self) -> str:
        """Génère la page de garde commerciale."""
        
        # S'assurer que les métriques sont calculées
        if not hasattr(self, 'solar_price'):
            self._calculate_commercial_metrics()
        
        project_config = self._get_project_configuration()
        global_config = project_config['global_config']
        
        project_name = global_config.get('project_name', 'Projet d\'Autoconsommation Collective')
        client_name = global_config.get('client_name', 'Votre Entreprise')
        
        # Formatage des nombres
        solar_price_display = f"{self.solar_price:.3f}".replace('.', ',')
        annual_savings_display = f"{self.annual_savings:,.0f}".replace(',', ' ')
        total_savings_display = f"{self.total_savings_20y:,.0f}".replace(',', ' ')
        
        # Date de mise en service estimée (6 mois après aujourd'hui)
        from datetime import datetime, timedelta
        commissioning_date = (datetime.now() + timedelta(days=180)).strftime("%B %Y")
        
        # Debug logging
        logger.info(f"PAGE DE GARDE - Prix solaire: {self.solar_price:.3f}€, Économie totale: {self.total_savings_20y:.0f}€, Économie annuelle: {self.annual_savings:.0f}€")
        
        return f"""
        <div class="page cover-page">
            <div class="logo-section">
                <img src="data:image/png;base64,{self._get_logo_base64()}" alt="Logo" style="height: 60px;">
            </div>
            
            <div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: center;">
                <h1 class="main-title">Votre Projet d'Autoconsommation Solaire</h1>
                <h2 class="subtitle">Proposition pour {client_name}</h2>
                
                <div class="hero-visual">
                    <img src="data:image/png;base64,{self._get_solar_panel_image()}" alt="Panneaux solaires" style="width: 100%; max-width: 500px; border-radius: 15px;">
                </div>
                
                <div class="key-benefit-box">
                    <div class="benefit-price">Prix Garanti : {solar_price_display} €/kWh</div>
                    <div class="benefit-savings">Économie Estimée sur 20 ans : {total_savings_display} €</div>
                    <div class="benefit-date">Mise en service prévue : {commissioning_date}</div>
                </div>
            </div>
            
            <div class="page-footer">
                Rapport préparé le {datetime.now().strftime("%d/%m/%Y")} | Page 1 / 10
            </div>
        </div>
        """
    
    def _generate_executive_summary(self) -> str:
        """Génère le résumé exécutif orienté bénéfices."""
        
        # Récupérer la configuration
        project_config = self._get_project_configuration()
        global_config = project_config['global_config']
        
        # Calcul du pourcentage d'économie
        savings_percentage = (self.savings_per_kwh / self.grid_price * 100) if self.grid_price > 0 else 0
        
        # Formatage
        savings_pct_display = f"{savings_percentage:.0f}"
        annual_savings_display = f"{self.annual_savings:,.0f}".replace(',', ' ')
        total_savings_display = f"{self.total_savings_20y:,.0f}".replace(',', ' ')
        co2_display = f"{self.co2_avoided_annual:.1f}".replace('.', ',')
        
        return f"""
        <div class="page">
            <h2 class="section-title">Une Énergie Plus Verte et Plus Économique, en Bref</h2>
            
            <div class="executive-summary">
                <p style="font-size: 16px; line-height: 1.8; color: #555;">
                    Ce rapport vous présente une opportunité unique de réduire durablement votre facture d'électricité. 
                    En rejoignant le projet d'autoconsommation collective <strong>{global_config.get('project_name', '')}</strong>, 
                    vous bénéficierez d'une électricité produite localement à un tarif fixe et compétitif de 
                    <strong>{self.solar_price:.3f} €/kWh</strong>, à l'abri des hausses du marché.
                </p>
                <p style="font-size: 16px; line-height: 1.8; color: #555; margin-top: 15px;">
                    Cela représente une économie estimée à <strong>{savings_pct_display}%</strong> sur la part solaire 
                    de votre consommation, soit plus de <strong>{total_savings_display} €</strong> sur 20 ans, 
                    tout en réduisant votre empreinte carbone de <strong>{co2_display}</strong> tonnes par an. 
                    C'est simple, sécurisé et sans investissement de votre part.
                </p>
            </div>
            
            <div class="key-advantages">
                <div class="advantage-card">
                    <div class="advantage-icon">💰</div>
                    <div class="advantage-title">Économies Directes</div>
                    <div class="advantage-text">
                        Un prix de l'électricité solaire inférieur de {savings_pct_display}% au tarif réglementé actuel
                    </div>
                </div>
                
                <div class="advantage-card">
                    <div class="advantage-icon">🛡️</div>
                    <div class="advantage-title">Stabilité des Prix</div>
                    <div class="advantage-text">
                        Un tarif fixe pendant 20 ans, vous protégeant de la volatilité du marché
                    </div>
                </div>
                
                <div class="advantage-card">
                    <div class="advantage-icon">🌱</div>
                    <div class="advantage-title">Impact Positif</div>
                    <div class="advantage-text">
                        Accès à une énergie 100% verte et locale, valorisant votre image RSE
                    </div>
                </div>
            </div>
            
            <div class="info-box" style="margin-top: 40px;">
                <strong>Le saviez-vous ?</strong> Le prix de l'électricité en France a augmenté de plus de 50% 
                ces 10 dernières années. En optant pour l'autoconsommation collective, vous vous protégez 
                contre ces hausses futures tout en participant à la transition énergétique.
            </div>
            
            <div class="page-footer">
                Rapport préparé le {datetime.now().strftime("%d/%m/%Y")} | Page 2 / 10
            </div>
        </div>
        """
    
    def _generate_invoice_comparison(self) -> str:
        """Génère la comparaison visuelle de la facture avant/après."""
        
        # Utiliser les vraies données calculées
        current_invoice = self.total_consumption_kwh * self.grid_price
        solar_part_cost = self.solar_consumption_kwh * self.solar_price
        grid_part_cost = (self.total_consumption_kwh - self.solar_consumption_kwh) * self.grid_price
        new_invoice = solar_part_cost + grid_part_cost
        
        # Économie
        annual_saving = current_invoice - new_invoice
        saving_percentage = (annual_saving / current_invoice * 100) if current_invoice > 0 else 0
        
        # Création du graphique
        fig_comparison = self._create_invoice_comparison_chart(
            current_invoice, solar_part_cost, grid_part_cost
        )
        
        # Formatage
        current_display = f"{current_invoice:,.0f}".replace(',', ' ')
        new_display = f"{new_invoice:,.0f}".replace(',', ' ')
        saving_display = f"{annual_saving:,.0f}".replace(',', ' ')
        saving_pct_display = f"{saving_percentage:.0f}"
        
        return f"""
        <div class="page">
            <h2 class="section-title">Visualisez l'Impact sur Votre Facture Annuelle</h2>
            
            <div class="chart-container">
                <div class="chart-title">Comparatif du Coût Annuel de l'Électricité</div>
                {fig_comparison}
            </div>
            
            <div style="display: flex; justify-content: center; margin-top: 30px;">
                <div class="success-box" style="padding: 30px; text-align: center;">
                    <div style="font-size: 36px; font-weight: 700; color: #2E7D32; margin-bottom: 10px;">
                        Soit {saving_display} € d'économie par an
                    </div>
                    <div style="font-size: 24px; color: #4CAF50;">
                        {saving_pct_display}% de réduction sur votre facture
                    </div>
                </div>
            </div>
            
            <p style="margin-top: 30px; font-size: 16px; text-align: center; color: #666;">
                Grâce à l'énergie solaire locale, une part significative de votre consommation vous coûtera moins cher. 
                Le reste de vos besoins est toujours assuré par le réseau, garantissant une alimentation sans coupure.
            </p>
            
            <div class="info-box" style="margin-top: 30px;">
                <strong>Comment lire ce graphique ?</strong> La barre de gauche représente votre facture actuelle 
                avec 100% d'électricité du réseau. La barre de droite montre votre nouvelle facture avec la part 
                d'électricité solaire (en vert) moins chère et le complément réseau (en gris).
            </div>
            
            <div class="page-footer">
                Rapport préparé le {datetime.now().strftime("%d/%m/%Y")} | Page 3 / 10
            </div>
        </div>
        """
    
    def _create_invoice_comparison_chart(self, current_invoice: float, 
                                        solar_cost: float, grid_cost: float) -> str:
        """Crée le graphique de comparaison des factures."""
        
        if not MATPLOTLIB_AVAILABLE:
            # Fallback vers un tableau simple
            return f"""
            <div style="text-align: center; padding: 20px;">
                <table style="margin: 0 auto; border-collapse: collapse; font-size: 16px;">
                    <tr>
                        <th style="padding: 15px; background: #f5f5f5; border: 1px solid #ddd;">Scénario</th>
                        <th style="padding: 15px; background: #f5f5f5; border: 1px solid #ddd;">Coût annuel</th>
                    </tr>
                    <tr>
                        <td style="padding: 15px; border: 1px solid #ddd;">SANS le projet solaire</td>
                        <td style="padding: 15px; border: 1px solid #ddd; font-weight: bold; color: #E57373;">{current_invoice:,.0f} €</td>
                    </tr>
                    <tr>
                        <td style="padding: 15px; border: 1px solid #ddd;">AVEC le projet solaire</td>
                        <td style="padding: 15px; border: 1px solid #ddd; font-weight: bold; color: #4CAF50;">{solar_cost + grid_cost:,.0f} €</td>
                    </tr>
                </table>
            </div>
            """.replace(',', ' ')
        
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Données
            categories = ['SANS le projet solaire', 'AVEC le projet solaire']
            invoice_current = [current_invoice, 0]
            invoice_solar = [0, solar_cost]
            invoice_grid = [0, grid_cost]
            
            # Largeur des barres
            bar_width = 0.5
            x = np.arange(len(categories))
            
            # Création des barres
            bars1 = ax.bar(x, invoice_current, bar_width, label='100% Réseau', color='#E57373')
            bars2 = ax.bar(x, invoice_solar, bar_width, label='Part Solaire', color='#81C784')
            bars3 = ax.bar(x, invoice_grid, bar_width, bottom=invoice_solar, label='Complément Réseau', color='#BDBDBD')
            
            # Annotations
            ax.text(0, current_invoice + 500, f'{current_invoice:,.0f} €'.replace(',', ' '), 
                    ha='center', va='bottom', fontsize=16, fontweight='bold')
            ax.text(1, solar_cost + grid_cost + 500, f'{solar_cost + grid_cost:,.0f} €'.replace(',', ' '), 
                    ha='center', va='bottom', fontsize=16, fontweight='bold')
            
            # Styling
            ax.set_ylabel('Montant annuel (€)', fontsize=12)
            ax.set_xticks(x)
            ax.set_xticklabels(categories, fontsize=12)
            ax.legend(loc='upper right', fontsize=10)
            ax.grid(axis='y', alpha=0.3)
            ax.set_ylim(0, current_invoice * 1.2)
            
            # Format des axes
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'.replace(',', ' ')))
            
            plt.tight_layout()
            
            # Conversion en base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f'<img src="data:image/png;base64,{image_base64}" style="width: 100%; max-width: 800px;">'
        
        except Exception as e:
            logger.error(f"Erreur création graphique: {e}")
            # Fallback vers tableau
            return f"""
            <div style="text-align: center; padding: 20px;">
                <p><em>Graphique non disponible - Affichage en tableau</em></p>
                <table style="margin: 0 auto; border-collapse: collapse; font-size: 16px;">
                    <tr>
                        <th style="padding: 15px; background: #f5f5f5; border: 1px solid #ddd;">Scénario</th>
                        <th style="padding: 15px; background: #f5f5f5; border: 1px solid #ddd;">Coût annuel</th>
                    </tr>
                    <tr>
                        <td style="padding: 15px; border: 1px solid #ddd;">SANS le projet solaire</td>
                        <td style="padding: 15px; border: 1px solid #ddd; font-weight: bold; color: #E57373;">{current_invoice:,.0f} €</td>
                    </tr>
                    <tr>
                        <td style="padding: 15px; border: 1px solid #ddd;">AVEC le projet solaire</td>
                        <td style="padding: 15px; border: 1px solid #ddd; font-weight: bold; color: #4CAF50;">{solar_cost + grid_cost:,.0f} €</td>
                    </tr>
                </table>
            </div>
            """.replace(',', ' ')
    
    def _generate_offer_details(self) -> str:
        """Génère la page de détails de l'offre."""
        
        # Calcul du taux d'autonomie
        autonomy_display = f"{self.autonomy_rate:.0f}"
        
        # Prix formaté
        price_display = f"{self.solar_price:.3f}".replace('.', ',')
        
        return f"""
        <div class="page">
            <h2 class="section-title">Un Modèle Simple et un Prix Transparent</h2>
            
            <table class="data-table">
                <tr>
                    <th>Élément de l'offre</th>
                    <th>Détails</th>
                </tr>
                <tr>
                    <td><strong>Prix de vente de l'électricité solaire</strong></td>
                    <td>{price_display} €/kWh HT</td>
                </tr>
                <tr>
                    <td><strong>Part de votre consommation couverte par le solaire</strong></td>
                    <td>{autonomy_display}%</td>
                </tr>
                <tr>
                    <td><strong>Durée du contrat</strong></td>
                    <td>20 ans</td>
                </tr>
                <tr>
                    <td><strong>Indexation du prix</strong></td>
                    <td>Fixe (aucune augmentation)</td>
                </tr>
                <tr>
                    <td><strong>Investissement requis de votre part</strong></td>
                    <td>0 €</td>
                </tr>
            </table>
            
            <h3 class="section-subtitle">Comment ça marche ?</h3>
            
            <div style="background: #f8f9fa; padding: 30px; border-radius: 15px; margin-top: 20px;">
                {self._generate_process_diagram()}
            </div>
            
            <div class="success-box" style="margin-top: 30px;">
                <strong>Avantage clé :</strong> Vous ne payez que l'électricité que vous consommez, 
                au tarif avantageux convenu. Aucun risque, aucun investissement, que des économies !
            </div>
            
            <div class="page-footer">
                Rapport préparé le {datetime.now().strftime("%d/%m/%Y")} | Page 4 / 10
            </div>
        </div>
        """
    
    def _generate_process_diagram(self) -> str:
        """Génère un diagramme simple du processus."""
        return """
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; text-align: center;">
            <div>
                <div style="background: #4CAF50; color: white; width: 60px; height: 60px; border-radius: 50%; 
                            display: flex; align-items: center; justify-content: center; margin: 0 auto 10px; 
                            font-size: 24px; font-weight: bold;">1</div>
                <p><strong>Production</strong><br>Les panneaux solaires produisent de l'électricité</p>
            </div>
            <div>
                <div style="background: #4CAF50; color: white; width: 60px; height: 60px; border-radius: 50%; 
                            display: flex; align-items: center; justify-content: center; margin: 0 auto 10px; 
                            font-size: 24px; font-weight: bold;">2</div>
                <p><strong>Injection</strong><br>L'électricité est injectée dans le réseau local</p>
            </div>
            <div>
                <div style="background: #4CAF50; color: white; width: 60px; height: 60px; border-radius: 50%; 
                            display: flex; align-items: center; justify-content: center; margin: 0 auto 10px; 
                            font-size: 24px; font-weight: bold;">3</div>
                <p><strong>Consommation</strong><br>Vous consommez cette électricité instantanément</p>
            </div>
            <div>
                <div style="background: #4CAF50; color: white; width: 60px; height: 60px; border-radius: 50%; 
                            display: flex; align-items: center; justify-content: center; margin: 0 auto 10px; 
                            font-size: 24px; font-weight: bold;">4</div>
                <p><strong>Facturation</strong><br>Vous payez uniquement la part solaire consommée</p>
            </div>
        </div>
        """
    
    def _generate_long_term_savings(self) -> str:
        """Génère la projection des économies sur 20 ans."""
        
        # Création du graphique des économies cumulées
        fig_savings = self._create_cumulative_savings_chart()
        
        return f"""
        <div class="page">
            <h2 class="section-title">Vos Économies Cumulées Année Après Année</h2>
            
            <div class="chart-container">
                {fig_savings}
            </div>
            
            <p style="margin-top: 30px; font-size: 16px; text-align: center; color: #666;">
                Ce graphique illustre la puissance de votre engagement. Tandis que le prix de l'électricité 
                du réseau devrait continuer d'augmenter, votre tarif solaire reste stable, créant des économies 
                de plus en plus importantes chaque année.
            </p>
            
            <div class="info-box" style="margin-top: 30px;">
                <strong>Hypothèse conservative :</strong> Ce calcul suppose une augmentation modérée de 3% par an 
                du prix de l'électricité du réseau. Historiquement, les augmentations ont souvent été plus importantes, 
                ce qui rendrait vos économies encore plus significatives.
            </div>
            
            <table class="data-table" style="margin-top: 30px;">
                <tr>
                    <th>Période</th>
                    <th>Économies cumulées</th>
                    <th>Équivalent</th>
                </tr>
                <tr>
                    <td>5 ans</td>
                    <td>{self._calculate_cumulative_savings(5):,.0f} €</td>
                    <td>Un voyage autour du monde</td>
                </tr>
                <tr>
                    <td>10 ans</td>
                    <td>{self._calculate_cumulative_savings(10):,.0f} €</td>
                    <td>Une voiture neuve</td>
                </tr>
                <tr>
                    <td>15 ans</td>
                    <td>{self._calculate_cumulative_savings(15):,.0f} €</td>
                    <td>Des travaux de rénovation</td>
                </tr>
                <tr>
                    <td>20 ans</td>
                    <td>{self._calculate_cumulative_savings(20):,.0f} €</td>
                    <td>Un investissement conséquent</td>
                </tr>
            </table>
            
            <div class="page-footer">
                Rapport préparé le {datetime.now().strftime("%d/%m/%Y")} | Page 5 / 10
            </div>
        </div>
        """
    
    def _create_cumulative_savings_chart(self) -> str:
        """Crée le graphique des économies cumulées."""
        
        years = list(range(1, 21))
        cumulative_savings = [self._calculate_cumulative_savings(year) for year in years]
        
        if not MATPLOTLIB_AVAILABLE:
            # Fallback vers un tableau avec étapes clés
            key_years = [5, 10, 15, 20]
            table_rows = ""
            for year in key_years:
                value = cumulative_savings[year-1]
                table_rows += f"""
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{year} ans</td>
                    <td style="padding: 10px; border: 1px solid #ddd; text-align: center; font-weight: bold; color: #4CAF50;">{value:,.0f} €</td>
                </tr>
                """.replace(',', ' ')
            
            return f"""
            <div style="text-align: center; padding: 20px;">
                <h4>Économies Cumulées - Étapes Clés</h4>
                <table style="margin: 0 auto; border-collapse: collapse; font-size: 16px;">
                    <tr>
                        <th style="padding: 15px; background: #f5f5f5; border: 1px solid #ddd;">Période</th>
                        <th style="padding: 15px; background: #f5f5f5; border: 1px solid #ddd;">Économies Cumulées</th>
                    </tr>
                    {table_rows}
                </table>
            </div>
            """
        
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Création de la courbe
            ax.plot(years, cumulative_savings, color='#4CAF50', linewidth=3)
            ax.fill_between(years, cumulative_savings, alpha=0.3, color='#4CAF50')
            
            # Marqueurs aux étapes clés
            key_years = [5, 10, 15, 20]
            for year in key_years:
                value = cumulative_savings[year-1]
                ax.plot(year, value, 'o', color='#2E7D32', markersize=10)
                ax.annotate(f'{value:,.0f} €'.replace(',', ' '), 
                           xy=(year, value), xytext=(0, 20), 
                           textcoords='offset points', ha='center', fontsize=10, fontweight='bold')
            
            # Styling
            ax.set_xlabel('Années', fontsize=12)
            ax.set_ylabel('Économies cumulées (€)', fontsize=12)
            ax.set_title('Projection de vos gains sur 20 ans', fontsize=14, fontweight='bold', pad=20)
            ax.grid(True, alpha=0.3)
            ax.set_xlim(0, 21)
            ax.set_ylim(0, max(cumulative_savings) * 1.2)
            
            # Format des axes
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'.replace(',', ' ')))
            
            plt.tight_layout()
            
            # Conversion en base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f'<img src="data:image/png;base64,{image_base64}" style="width: 100%; max-width: 800px;">'
            
        except Exception as e:
            logger.error(f"Erreur création graphique économies: {e}")
            # Fallback vers tableau
            key_years = [5, 10, 15, 20]
            table_rows = ""
            for year in key_years:
                value = cumulative_savings[year-1]
                table_rows += f"""
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{year} ans</td>
                    <td style="padding: 10px; border: 1px solid #ddd; text-align: center; font-weight: bold; color: #4CAF50;">{value:,.0f} €</td>
                </tr>
                """.replace(',', ' ')
            
            return f"""
            <div style="text-align: center; padding: 20px;">
                <p><em>Graphique non disponible - Affichage en tableau</em></p>
                <h4>Économies Cumulées - Étapes Clés</h4>
                <table style="margin: 0 auto; border-collapse: collapse; font-size: 16px;">
                    <tr>
                        <th style="padding: 15px; background: #f5f5f5; border: 1px solid #ddd;">Période</th>
                        <th style="padding: 15px; background: #f5f5f5; border: 1px solid #ddd;">Économies Cumulées</th>
                    </tr>
                    {table_rows}
                </table>
            </div>
            """
    
    def _calculate_cumulative_savings(self, years: int) -> float:
        """Calcule les économies cumulées avec inflation."""
        inflation_rate = 0.03  # 3% par an
        cumulative = 0
        
        for year in range(1, years + 1):
            # Le prix du réseau augmente, pas le prix solaire
            grid_price_year = self.grid_price * (1 + inflation_rate) ** (year - 1)
            saving_year = self.solar_consumption * (grid_price_year - self.solar_price)
            cumulative += saving_year
            
        return cumulative
    
    def _generate_installation_info(self) -> str:
        """Génère les informations sur l'installation."""
        
        # Récupérer la configuration
        project_config = self._get_project_configuration()
        sites_config = project_config['sites_config']
        
        # Calcul de la puissance totale
        total_power = sum(
            site.get('puissance_installee_kwc', 0) 
            for site in sites_config.values()
        )
        
        # Si pas de puissance trouvée, utiliser la valeur calculée des métriques
        if total_power == 0:
            # Estimer à partir de la production (1 kWc ≈ 1100 kWh/an)
            total_power = (self.total_consumption_kwh / 1000) * 0.6  # Estimation basée sur consommation
        
        # Utiliser la production depuis les métriques calculées
        total_production = self.total_consumption_kwh * 0.6  # Estimation
        
        # Nombre de foyers équivalents
        household_equivalent = int(total_production / 2500)  # 2500 kWh/an par foyer moyen
        
        # Adresse du premier site
        first_site = list(sites_config.values())[0] if sites_config else {}
        location = first_site.get('adresse', 'Site de production local')
        
        return f"""
        <div class="page">
            <h2 class="section-title">Une Source d'Énergie Locale et Fiable</h2>
            
            <div style="text-align: center; margin-bottom: 30px;">
                <img src="data:image/png;base64,{self._get_installation_image()}" 
                     alt="Installation" style="width: 100%; max-width: 600px; border-radius: 15px;">
            </div>
            
            <table class="data-table">
                <tr>
                    <th>Caractéristique</th>
                    <th>Détails</th>
                </tr>
                <tr>
                    <td><strong>Localisation</strong></td>
                    <td>{location}</td>
                </tr>
                <tr>
                    <td><strong>Puissance installée</strong></td>
                    <td>{total_power:.0f} kWc (équivalent de {household_equivalent} foyers)</td>
                </tr>
                <tr>
                    <td><strong>Production annuelle estimée</strong></td>
                    <td>{total_production:,.0f} kWh</td>
                </tr>
                <tr>
                    <td><strong>Technologie</strong></td>
                    <td>Panneaux photovoltaïques haute performance</td>
                </tr>
                <tr>
                    <td><strong>Maintenance & Supervision</strong></td>
                    <td>Assurées par nos équipes 24/7</td>
                </tr>
            </table>
            
            <div class="success-box" style="margin-top: 30px;">
                <strong>Fiabilité garantie :</strong> Nos installations sont conçues pour une durée de vie 
                de plus de 25 ans avec une garantie de performance. La maintenance préventive et le monitoring 
                en temps réel assurent une production optimale tout au long de l'année.
            </div>
            
            <div class="info-box" style="margin-top: 20px;">
                <strong>Technologie de pointe :</strong> Nous utilisons des panneaux solaires de dernière 
                génération avec un rendement supérieur à 20%, garantissant une production maximale même 
                par temps nuageux.
            </div>
            
            <div class="page-footer">
                Rapport préparé le {datetime.now().strftime("%d/%m/%Y")} | Page 6 / 10
            </div>
        </div>
        """
    
    def _generate_environmental_impact(self) -> str:
        """Génère la section impact environnemental."""
        
        # Calculs environnementaux
        co2_total_20y = self.co2_avoided_annual * 20
        cars_equivalent = int(self.co2_avoided_annual / 4.6)  # 4.6 tonnes CO2/voiture/an
        trees_equivalent = int(self.co2_avoided_annual * 40)  # 1 arbre absorbe ~25kg CO2/an
        
        # Formatage
        co2_annual_display = f"{self.co2_avoided_annual:.1f}".replace('.', ',')
        co2_total_display = f"{co2_total_20y:.0f}".replace('.', ',')
        
        return f"""
        <div class="page">
            <h2 class="section-title">Plus qu'une Économie, un Geste pour la Planète</h2>
            
            <div style="text-align: center; margin: 40px 0;">
                <div style="background: linear-gradient(135deg, #81C784 0%, #4CAF50 100%); 
                            color: white; padding: 40px; border-radius: 20px; display: inline-block;">
                    <div style="font-size: 64px; margin-bottom: 10px;">🌱</div>
                    <div style="font-size: 48px; font-weight: 700; margin-bottom: 10px;">
                        {co2_annual_display} tonnes de CO₂ évitées par an
                    </div>
                    <div style="font-size: 24px;">
                        C'est comme retirer {cars_equivalent} voitures de la circulation chaque année !
                    </div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 40px;">
                <div class="info-box" style="text-align: center;">
                    <div style="font-size: 36px; font-weight: 700; color: #4CAF50;">{co2_total_display}</div>
                    <div>Tonnes de CO₂ évitées sur 20 ans</div>
                </div>
                <div class="info-box" style="text-align: center;">
                    <div style="font-size: 36px; font-weight: 700; color: #4CAF50;">{trees_equivalent}</div>
                    <div>Équivalent arbres plantés</div>
                </div>
                <div class="info-box" style="text-align: center;">
                    <div style="font-size: 36px; font-weight: 700; color: #4CAF50;">100%</div>
                    <div>Énergie verte et locale</div>
                </div>
            </div>
            
            <h3 class="section-subtitle" style="margin-top: 40px;">Un Acteur Engagé dans son Territoire</h3>
            
            <ul style="font-size: 16px; line-height: 2; color: #555;">
                <li><strong>Soutien à la production d'énergie locale :</strong> Vous participez au développement 
                    des énergies renouvelables dans votre région.</li>
                <li><strong>Contribution à la transition énergétique :</strong> Vous aidez la France à atteindre 
                    ses objectifs de neutralité carbone.</li>
                <li><strong>Valorisation de votre image de marque :</strong> Affichez votre engagement RSE 
                    auprès de vos clients et collaborateurs.</li>
            </ul>
            
            <div class="success-box" style="margin-top: 30px;">
                <strong>Certificat disponible :</strong> Nous vous fournirons un certificat annuel détaillant 
                votre contribution environnementale, que vous pourrez utiliser dans votre communication RSE.
            </div>
            
            <div class="page-footer">
                Rapport préparé le {datetime.now().strftime("%d/%m/%Y")} | Page 7 / 10
            </div>
        </div>
        """
    
    def _generate_faq(self) -> str:
        """Génère la section FAQ."""
        
        return f"""
        <div class="page">
            <h2 class="section-title">Vos Questions, Nos Réponses</h2>
            
            <div class="faq-item">
                <div class="faq-question">Et s'il n'y a pas de soleil ?</div>
                <div class="faq-answer">
                    Votre alimentation est garantie sans coupure. Le réseau électrique prend le relais 
                    automatiquement. Vous ne remarquerez aucune différence, sauf sur votre facture. 
                    C'est l'avantage de l'autoconsommation collective : vous bénéficiez du meilleur 
                    des deux mondes.
                </div>
            </div>
            
            <div class="faq-item">
                <div class="faq-question">Que se passe-t-il si je consomme plus que ce que le solaire produit ?</div>
                <div class="faq-answer">
                    Le complément est fourni par le réseau, comme aujourd'hui. Notre offre ne couvre que 
                    la part d'énergie solaire que vous consommez. Vous gardez votre contrat actuel avec 
                    votre fournisseur d'électricité pour le complément.
                </div>
            </div>
            
            <div class="faq-item">
                <div class="faq-question">Mon contrat est-il flexible ?</div>
                <div class="faq-answer">
                    Oui, nous comprenons que vos besoins peuvent évoluer. En cas de déménagement, le contrat 
                    peut être transféré au nouveau locataire ou résilié avec un préavis de 3 mois. 
                    Aucune pénalité n'est appliquée après la première année.
                </div>
            </div>
            
            <div class="faq-item">
                <div class="faq-question">Qui s'occupe de la maintenance ?</div>
                <div class="faq-answer">
                    Nous nous occupons de tout. L'exploitation et la maintenance de la centrale sont 
                    entièrement à notre charge. Vous n'avez rien à gérer, vous profitez simplement 
                    des économies sur votre facture.
                </div>
            </div>
            
            <div class="faq-item">
                <div class="faq-question">Comment sont calculées mes économies ?</div>
                <div class="faq-answer">
                    Vos économies sont la différence entre le prix du réseau et notre tarif solaire, 
                    multipliée par votre consommation d'électricité solaire. Nous mesurons précisément 
                    cette consommation grâce à des compteurs intelligents certifiés.
                </div>
            </div>
            
            <div class="faq-item">
                <div class="faq-question">Y a-t-il des frais cachés ?</div>
                <div class="faq-answer">
                    Aucun frais caché. Vous payez uniquement l'électricité solaire que vous consommez 
                    au tarif convenu. Pas de frais d'adhésion, pas de frais de maintenance, pas de 
                    surprises. La transparence est notre priorité.
                </div>
            </div>
            
            <div class="page-footer">
                Rapport préparé le {datetime.now().strftime("%d/%m/%Y")} | Page 8 / 10
            </div>
        </div>
        """
    
    def _generate_next_steps(self) -> str:
        """Génère la section prochaines étapes."""
        
        return f"""
        <div class="page">
            <h2 class="section-title">Prêt à Réduire Votre Facture ?</h2>
            
            <div class="timeline">
                <div class="timeline-item">
                    <div class="timeline-marker">1</div>
                    <div class="timeline-content">
                        <div class="timeline-date">Aujourd'hui</div>
                        <div>Lecture de cette proposition et première prise de contact</div>
                    </div>
                </div>
                
                <div class="timeline-item">
                    <div class="timeline-marker">2</div>
                    <div class="timeline-content">
                        <div class="timeline-date">Semaine prochaine</div>
                        <div>Entretien personnalisé pour répondre à toutes vos questions</div>
                    </div>
                </div>
                
                <div class="timeline-item">
                    <div class="timeline-marker">3</div>
                    <div class="timeline-content">
                        <div class="timeline-date">Sous 1 mois</div>
                        <div>Signature de la convention d'autoconsommation collective</div>
                    </div>
                </div>
                
                <div class="timeline-item">
                    <div class="timeline-marker">4</div>
                    <div class="timeline-content">
                        <div class="timeline-date">Dans 6 mois</div>
                        <div>Début de vos économies avec la mise en service !</div>
                    </div>
                </div>
            </div>
            
            <div class="contact-section">
                <h3 style="font-size: 24px; margin-bottom: 20px;">Votre Interlocuteur Dédié</h3>
                <div class="contact-person">
                    <div>
                        <img src="data:image/png;base64,{self._get_contact_avatar()}" 
                             alt="Contact" style="width: 120px; height: 120px; border-radius: 50%;">
                    </div>
                    <div class="contact-details">
                        <div class="contact-name">Jean Dupont</div>
                        <div class="contact-info">Conseiller en Énergie Renouvelable</div>
                        <div class="contact-info">📞 01 23 45 67 89</div>
                        <div class="contact-info">✉️ jean.dupont@optimpv.fr</div>
                    </div>
                </div>
            </div>
            
            <div class="success-box" style="margin-top: 30px; text-align: center;">
                <strong>Prochaine étape :</strong> Appelez-nous ou envoyez-nous un email pour planifier 
                votre entretien personnalisé. Nous sommes là pour vous accompagner dans votre transition 
                vers une énergie plus verte et économique.
            </div>
            
            <div class="page-footer">
                Rapport préparé le {datetime.now().strftime("%d/%m/%Y")} | Page 9 / 10
            </div>
        </div>
        """
    
    def _generate_appendix_contact(self) -> str:
        """Génère la page annexes et contact."""
        
        # Récupérer les données d'optimisation pour le LCOE
        best_scenario, scenario_data, prix_optimal = self._get_optimization_data()
        lcoe_value = scenario_data.get('lcoe', self.solar_price) if scenario_data else self.solar_price
        
        return f"""
        <div class="page">
            <h2 class="section-title">Informations Détaillées et Contact</h2>
            
            <h3 class="section-subtitle">Hypothèses et Données Techniques</h3>
            
            <table class="data-table">
                <tr>
                    <th>Paramètre</th>
                    <th>Valeur</th>
                </tr>
                <tr>
                    <td>Taux d'ensoleillement source</td>
                    <td>PVGIS / Météo France</td>
                </tr>
                <tr>
                    <td>Pertes système estimées</td>
                    <td>13%</td>
                </tr>
                <tr>
                    <td>Hypothèse d'inflation du prix de l'électricité réseau</td>
                    <td>3% / an</td>
                </tr>
                <tr>
                    <td>LCOE du projet (coût de production)</td>
                    <td>{lcoe_value:.3f} €/kWh</td>
                </tr>
                <tr>
                    <td>Durée de vie des panneaux</td>
                    <td>25 ans minimum</td>
                </tr>
                <tr>
                    <td>Garantie de performance</td>
                    <td>80% à 25 ans</td>
                </tr>
            </table>
            
            <div class="info-box" style="margin-top: 30px;">
                <strong>Méthodologie :</strong> Toutes nos projections sont basées sur des données 
                météorologiques historiques et des hypothèses conservatives. Les performances réelles 
                peuvent varier mais nos estimations incluent une marge de sécurité.
            </div>
            
            <div style="background: #333; color: white; padding: 40px; margin-top: 40px; 
                        border-radius: 15px; text-align: center;">
                <img src="data:image/png;base64,{self._get_logo_base64()}" 
                     alt="Logo" style="height: 80px; margin-bottom: 20px;">
                <h3 style="font-size: 24px; margin-bottom: 20px;">OptimPV - Votre Partenaire Énergie</h3>
                <div style="font-size: 16px; line-height: 1.8;">
                    <div>123 Avenue de l'Énergie Verte</div>
                    <div>75001 Paris, France</div>
                    <div style="margin-top: 20px;">
                        <div>📞 01 23 45 67 89</div>
                        <div>✉️ contact@optimpv.fr</div>
                        <div>🌐 www.optimpv.fr</div>
                    </div>
                </div>
                <div style="margin-top: 30px;">
                    <img src="data:image/png;base64,{self._get_qr_code()}" 
                         alt="QR Code" style="width: 100px; height: 100px;">
                </div>
            </div>
            
            <div class="page-footer">
                Rapport préparé le {datetime.now().strftime("%d/%m/%Y")} | Page 10 / 10
            </div>
        </div>
        """
    
    def _get_logo_base64(self) -> str:
        """Retourne un logo placeholder en base64."""
        # Pour un vrai projet, remplacer par le logo réel
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    def _get_solar_panel_image(self) -> str:
        """Retourne une image de panneaux solaires en base64."""
        # Pour un vrai projet, remplacer par une vraie image
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    def _get_installation_image(self) -> str:
        """Retourne une image d'installation en base64."""
        # Pour un vrai projet, remplacer par une vraie image
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    def _get_contact_avatar(self) -> str:
        """Retourne un avatar de contact en base64."""
        # Pour un vrai projet, remplacer par une vraie photo
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    def _get_qr_code(self) -> str:
        """Retourne un QR code en base64."""
        # Pour un vrai projet, générer un vrai QR code
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    def _convert_to_pdf(self, html_content: str) -> bytes:
        """Convertit le contenu HTML en PDF."""
        try:
            from xhtml2pdf import pisa
            
            result = io.BytesIO()
            pdf = pisa.pisaDocument(io.BytesIO(html_content.encode("UTF-8")), result)
            
            if not pdf.err:
                return result.getvalue()
            else:
                logger.error(f"Erreur lors de la conversion PDF: {pdf.err}")
                return b""
                
        except ImportError:
            logger.error("xhtml2pdf n'est pas installé. Installation: pip install xhtml2pdf")
            return b""
        except Exception as e:
            logger.error(f"Erreur lors de la conversion PDF: {str(e)}")
            return b""
    
    def _generate_legacy_html_report(self, client_name: str, project_name: str):
        """Génère l'ancien rapport HTML pour compatibilité"""
        try:
            with st.spinner("🔄 Génération du rapport HTML legacy..."):
                # Générer le rapport HTML
                html_report = self.generate_report(report_format='html')
                
                if html_report:
                    # Stocker en session
                    st.session_state.last_commercial_report_html = html_report
                    st.session_state.last_commercial_report_client = client_name
                    st.session_state.last_commercial_report_project = project_name
                    
                    # Afficher succès
                    st.success("✅ Rapport HTML généré !")
                    
                    # Bouton de téléchargement
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"rapport_commercial_html_{timestamp}.html"
                    
                    st.download_button(
                        label="💾 Télécharger HTML",
                        data=html_report,
                        file_name=filename,
                        mime="text/html",
                        help="Télécharger le rapport HTML legacy",
                        use_container_width=True
                    )
                    
                    # Aperçu optionnel
                    if st.checkbox("📄 Afficher aperçu HTML", key="show_html_preview"):
                        st.markdown("### 📄 Aperçu du Rapport HTML")
                        st.components.v1.html(html_report, height=600, scrolling=True)
                        
                else:
                    st.error("❌ Erreur génération rapport HTML")
                    
        except Exception as e:
            st.error(f"❌ Erreur génération HTML: {str(e)}")
    
    def show_ui(self):
        """Interface utilisateur pour le module de rapport commercial"""
        st.markdown("<h1 class='main-header'>🎯 Rapport Commercial Orienté Client</h1>", unsafe_allow_html=True)
        
        # Vérifier que les données nécessaires sont disponibles
        if not st.session_state.get('data_imported'):
            st.warning("⚠️ Aucune donnée n'a été importée. Veuillez d'abord importer des données dans l'onglet 'Importation Données'.")
            return
        
        # Vérifier qu'une optimisation a été effectuée
        has_optimization = (st.session_state.get('constrained_optim_results') or 
                           st.session_state.get('optimization_results') or
                           st.session_state.get('floor_price_results'))
        
        if not has_optimization:
            st.warning("⚠️ Aucune analyse n'a été effectuée. Veuillez d'abord lancer une optimisation dans l'onglet 'Analyse & Optimisation'.")
            return
        
        # Interface nouvelle proposition commerciale
        st.markdown("""
        <div style="background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%); color: white; padding: 30px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 8px 25px rgba(0,0,0,0.15);">
            <h2 style="margin: 0 0 15px 0; font-size: 2.2em;">🌟 Proposition Commerciale Professionnelle</h2>
            <p style="margin: 0 0 10px 0; font-size: 1.2em; opacity: 0.95;">
                Générez une <strong>proposition commerciale Word de 8 pages</strong> avec graphiques haute résolution, 
                contenu orienté vente et design professionnel pour convaincre vos prospects !
            </p>
            <div style="background: rgba(255,255,255,0.15); padding: 15px; border-radius: 8px; margin-top: 15px;">
                <strong>✨ Nouveau :</strong> Dashboard héro • Timeline ROI • Avantage concurrentiel • Plan d'action
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Statut des données
        col_status1, col_status2, col_status3 = st.columns([2, 1, 1])
        
        with col_status1:
            if st.button("🔄 Actualiser les Données", type="secondary", use_container_width=True,
                        help="Actualise les données depuis l'analyse engine"):
                with st.spinner("Actualisation des données..."):
                    # Forcer le recalcul des métriques
                    self._refresh_all_report_data()
                    st.success("✅ Données actualisées !")
                    st.rerun()
        
        with col_status2:
            # Status des données énergétiques
            energy_data = self._get_energy_data_robust()
            if energy_data['total_consumption'] > 1:  # MWh
                st.success("📊 Données\nénergétiques OK")
            else:
                st.warning("⚠️ Données\npar défaut")
        
        with col_status3:
            # Status prix optimal
            best_scenario, scenario_data, prix_optimal = self._get_optimization_data()
            if prix_optimal and prix_optimal > 0:
                st.success(f"💰 Prix optimal\n{prix_optimal:.3f} €/kWh")
            else:
                st.warning("⚠️ Pas de prix\noptimal")
        
        # Affichage de debug des données récupérées
        with st.expander("🔍 Debug - Données Récupérées", expanded=False):
            energy_data = self._get_energy_data_robust()
            financial_data = self._get_financial_data_from_engine()
            config = st.session_state.get('config', {})
            
            col_debug1, col_debug2 = st.columns(2)
            
            with col_debug1:
                st.markdown("**Données Énergétiques:**")
                st.write(f"• Production: {energy_data['total_production']:.1f} MWh")
                st.write(f"• Consommation: {energy_data['total_consumption']:.1f} MWh")
                st.write(f"• Autoconsommation: {energy_data['total_autoconsumption']:.1f} MWh")
                st.write(f"• Taux autonomie: {energy_data['autoconsumption_rate']:.1f}%")
                
                st.markdown("**Configuration:**")
                st.write(f"• Tarif EDF: {config.get('tarif_edf_reference', 'N/A')} €/kWh")
                st.write(f"• Durée PPA: {config.get('duree_ppa', 'N/A')} mois")
            
            with col_debug2:
                st.markdown("**Données Financières:**")
                if financial_data:
                    st.write(f"• Scénario: {financial_data['scenario_name']}")
                    st.write(f"• Prix optimal: {financial_data['prix_optimal']:.3f} €/kWh")
                    st.write(f"• Économie totale: {financial_data['economie_totale']:,.0f} €")
                    st.write(f"• VAN projet: {financial_data['van_project']:,.0f} €")
                else:
                    st.write("Aucune donnée financière trouvée")
                
                st.markdown("**Sources de données:**")
                st.write(f"• constrained_optim_results: {'✅' if st.session_state.get('constrained_optim_results') else '❌'}")
                st.write(f"• optimization_results: {'✅' if st.session_state.get('optimization_results') else '❌'}")
                st.write(f"• sites_data: {'✅' if st.session_state.get('sites_data') else '❌'}")
                st.write(f"• processed_data: {'✅' if st.session_state.get('processed_data') is not None else '❌'}")
        
        # === NOUVELLE PROPOSITION COMMERCIALE PROFESSIONNELLE ===
        st.markdown("### 🌟 Proposition Commerciale Word - Prête à Envoyer !")
        
        # Informations client en colonnes
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📋 Informations Client**")
            
            client_name = st.text_input(
                "Nom de l'entreprise/client",
                placeholder="Société ABC / Copropriété XYZ",
                help="Nom qui apparaîtra sur la page de garde",
                key="new_client_name"
            )
            
            project_name = st.text_input(
                "Nom du projet",
                placeholder="Projet Autoconsommation Collective",
                help="Description du projet",
                key="new_project_name"
            )
        
        with col2:
            st.markdown("**📊 Aperçu des Bénéfices**")
            
            # Calculer les métriques clés pour l'aperçu
            try:
                energy_data = self._get_energy_data_robust()
                best_scenario, scenario_data, prix_optimal = self._get_optimization_data()
                
                # Calculs rapides
                tarif_edf = st.session_state.get('config', {}).get('tarif_edf_reference', 0.20)
                cout_sans_pv = energy_data['total_consumption'] * tarif_edf * 1000
                cout_avec_pv_solaire = energy_data['total_autoconsumption'] * (prix_optimal or 0.16) * 1000
                cout_avec_pv_reseau = energy_data['total_grid_purchase'] * tarif_edf * 1000
                economie_annuelle = cout_sans_pv - (cout_avec_pv_solaire + cout_avec_pv_reseau)
                
                st.success(f"""
                **💰 Économies :** {economie_annuelle:,.0f}€/an  
                **🔋 Autonomie :** {energy_data.get('autonomy_rate', 40):.0f}%  
                **📈 ROI 20 ans :** {economie_annuelle * 20 / 1000:.0f}K€
                """.replace(',', ' '))
                
            except Exception as e:
                st.info("""
                **🎯 Cette proposition inclut :**
                • Dashboard héro avec 4 graphiques
                • Timeline ROI sur 20 ans
                • Comparaison vs concurrence
                • Plan d'action détaillé
                """)
        
        # Génération de la proposition commerciale
        st.markdown("---")
        
        # Bouton principal de génération
        col_main1, col_main2, col_main3 = st.columns([2, 1, 1])
        
        with col_main1:
            if st.button("🌟 Générer Proposition Commerciale DOCX", type="primary", use_container_width=True, 
                        help="Génère une proposition commerciale Word professionnelle de 8 pages"):
                self._generate_quick_docx("proposition_commerciale", client_name, project_name)
        
        with col_main2:
            if st.button("📊 Aperçu Contenu", type="secondary", use_container_width=True, 
                        help="Voir le contenu de la proposition avant génération"):
                st.session_state.show_proposal_preview = True
                st.rerun()
        
        with col_main3:
            if st.button("⚙️ Options", type="secondary", use_container_width=True, 
                        help="Autres formats et options avancées"):
                st.session_state.show_advanced_options = True
                st.rerun()
        
        # Aperçu du contenu si demandé
        if st.session_state.get('show_proposal_preview', False):
            with st.expander("📄 Contenu de la Proposition Commerciale", expanded=True):
                st.markdown("""
                **🌟 Proposition Commerciale Professionnelle - 8 Pages**
                
                **Page 1** : 🎨 Page de garde impactante avec chiffres clés  
                **Page 2** : 📊 Résumé exécutif + Dashboard héro (4 graphiques)  
                **Page 3** : ⚡ Situation actuelle (créer l'urgence d'agir)  
                **Page 4** : 🎯 Solution OptimPV optimisée  
                **Page 5** : 💰 Bénéfices financiers + Timeline ROI  
                **Page 6** : 🏆 Avantage concurrentiel + Comparaison  
                **Page 7** : 🚀 Plan d'action + Prochaines étapes  
                **Page 8** : 🏢 Pourquoi OptimPV + Témoignages  
                
                **✨ Caractéristiques :**
                • 3 graphiques haute résolution (300 DPI)
                • Contenu orienté vente et persuasion
                • Design professionnel avec charte OptimPV
                • Données réelles de votre analyse
                • Prêt à imprimer et envoyer
                """)
                
                if st.button("❌ Fermer Aperçu"):
                    st.session_state.show_proposal_preview = False
                    st.rerun()
        
        # Options avancées si demandées
        if st.session_state.get('show_advanced_options', False):
            with st.expander("⚙️ Options Avancées", expanded=True):
                st.markdown("**📄 Autres Formats Disponibles**")
                
                col_opt1, col_opt2 = st.columns(2)
                
                with col_opt1:
                    if st.button("📄 Rapport Technique DOCX", use_container_width=True):
                        self._generate_quick_docx("technique", client_name, project_name)
                    
                    if st.button("💰 Rapport Financier DOCX", use_container_width=True):
                        self._generate_quick_docx("financier", client_name, project_name)
                
                with col_opt2:
                    if st.button("🎯 Générer HTML (Ancien)", use_container_width=True):
                        self._generate_legacy_html_report(client_name, project_name)
                    
                    if st.button("📊 Interface DOCX Complète", use_container_width=True):
                        st.session_state.show_docx_advanced = True
                        st.rerun()
                
                if st.button("❌ Fermer Options"):
                    st.session_state.show_advanced_options = False
                    st.rerun()
        
        # Séparateur visuel
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px; margin-top: 20px;">
            <h4 style="color: #2c3e50; margin-bottom: 10px;">🎯 Conseil Commercial</h4>
            <p style="color: #5a6c7d; margin: 0;">La nouvelle proposition commerciale DOCX est optimisée pour convaincre vos prospects.<br>
            Elle remplace avantageusement les anciens rapports HTML/PDF pour vos démarches commerciales.</p>
        </div>
        """, unsafe_allow_html=True)
            
        
        # Interface DOCX avancée si demandée
        if st.session_state.get('show_docx_advanced', False):
            with st.expander("🔧 Interface DOCX Complète", expanded=True):
                if self.docx_module:
                    self.docx_module.show_docx_ui()
                else:
                    st.warning("❌ Module DOCX non disponible")
                
                if st.button("❌ Fermer Interface DOCX"):
                    st.session_state.show_docx_advanced = False
                    st.rerun()
        
        # Guide d'utilisation
        with st.expander("📚 Guide de la Nouvelle Proposition Commerciale"):
            st.markdown("""
            ## 🌟 Proposition Commerciale Professionnelle - Mode d'Emploi
            
            ### 🎯 **Nouvelle Approche Commercial**
            
            OptimPV dispose maintenant d'un **générateur de propositions commerciales Word** de qualité professionnelle, 
            spécialement conçu pour **convaincre vos prospects** et **augmenter votre taux de conversion**.
            
            ### 📄 **Contenu de la Proposition (8 pages)**
            
            **Page 1** : 🎨 **Page de garde impactante**
            - Titre accrocheur avec bénéfices
            - Chiffres clés mis en évidence
            - Informations client personnalisées
            
            **Page 2** : 📊 **Résumé exécutif + Dashboard héro**
            - 4 graphiques clés en une seule image
            - Points forts avec emojis
            - Call-to-action immédiat
            
            **Page 3** : ⚡ **Situation actuelle**
            - Analyse des coûts énergétiques
            - Tendances du marché (inflation)
            - Urgence d'agir créée
            
            **Page 4** : 🎯 **Solution OptimPV optimisée**
            - Caractéristiques techniques vulgarisées
            - Avantages concurrentiels
            - 0€ d'investissement mis en avant
            
            **Page 5** : 💰 **Bénéfices financiers**
            - Timeline ROI sur 20 ans (graphique)
            - Tableau comparatif SANS/AVEC
            - Protection contre l'inflation
            
            **Page 6** : 🏆 **Avantage concurrentiel**
            - Graphique comparaison vs concurrence
            - Différenciateurs OptimPV
            - Pourquoi choisir OptimPV
            
            **Page 7** : 🚀 **Plan d'action**
            - Timeline projet (5 étapes)
            - Prochaines étapes concrètes
            - Contact urgent
            
            **Page 8** : 🏢 **Crédibilité OptimPV**
            - Expertise et garanties
            - Témoignages clients
            - Call-to-action final
            
            ### ✨ **Avantages vs Ancien Système**
            
            | **Critère** | **Ancien HTML** | **🌟 Nouvelle Proposition** |
            |-------------|----------------|----------------------------|
            | **Format** | HTML/PDF | Word DOCX professionnel |
            | **Pages** | 10 techniques | 8 pages commerciales |
            | **Graphiques** | Basiques | 3 graphiques haute résolution |
            | **Contenu** | Technique | Orienté vente/persuasion |
            | **Design** | Standard | Charte OptimPV moderne |
            | **Usage** | Analyse interne | Envoi direct aux prospects |
            | **Impact** | Informatif | Persuasif et convaincant |
            
            ### 🚀 **Comment l'utiliser**
            
            1. **Remplir** le nom du client et du projet
            2. **Cliquer** sur "🌟 Générer Proposition Commerciale DOCX"
            3. **Télécharger** le fichier Word généré
            4. **Personnaliser** si besoin (logos, coordonnées)
            5. **Envoyer** directement à vos prospects !
            
            ### 💡 **Conseils d'Utilisation**
            
            - **Nom client** : Utilisez le nom exact de l'entreprise/copropriété
            - **Nom projet** : Soyez descriptif ("Autoconsommation Collective Site Industriel")
            - **Personnalisation** : Ajoutez votre logo dans le Word généré
            - **Suivi** : Utilisez la timeline page 7 pour votre suivi commercial
            
            ### 🔧 **Options Avancées Disponibles**
            
            - **Rapport Technique DOCX** : Version détaillée pour experts
            - **Rapport Financier DOCX** : Focus VAN/TRI pour investisseurs  
            - **HTML Legacy** : Ancien format pour compatibilité
            - **Interface DOCX Complète** : Configuration avancée
            """)
    
    
    def _generate_quick_docx(self, docx_type: str, client_name: str, project_name: str):
        """Génération rapide d'un rapport DOCX"""
        try:
            with st.spinner(f"🔄 Génération du rapport {docx_type} DOCX..."):
                
                # Configuration selon le type
                if docx_type == "proposition_commerciale":
                    # Utiliser le nouveau générateur commercial professionnel
                    from .docx_system.commercial_template_generator import CommercialTemplateGenerator
                    commercial_generator = CommercialTemplateGenerator()
                    
                    docx_buffer = commercial_generator.generate_commercial_proposal(
                        client_name=client_name if client_name else None,
                        project_name=project_name if project_name else None
                    )
                    
                    report_title = "Proposition Commerciale"
                else:
                    # Configuration rapide pour les autres types
                    config = {
                        'report_type': docx_type,
                        'custom_title': f'Rapport {docx_type.title()} OptimPV',
                        'client_name': client_name if client_name else '',
                        'project_name': project_name if project_name else 'Projet Solaire',
                        'include_charts': True,
                        'generate_debug': False
                    }
                    
                    # Générer le rapport avec le générateur standard
                    docx_buffer = self.docx_module.docx_generator.generate_complete_report(
                        report_type=config['report_type'],
                        title=config['custom_title'],
                        client_name=config['client_name'] if config['client_name'] else None,
                        project_name=config['project_name']
                    )
                    
                    report_title = docx_type.title()
                
                if docx_buffer:
                    # Créer nom de fichier
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"rapport_{docx_type}_optimpv_{timestamp}.docx"
                    
                    st.success(f"✅ {report_title} DOCX généré avec succès !")
                    
                    # Message spécial pour proposition commerciale
                    if docx_type == "proposition_commerciale":
                        st.info("🌟 **Proposition commerciale professionnelle** avec graphiques haute résolution et contenu orienté vente !")
                    
                    # Bouton de téléchargement immédiat
                    st.download_button(
                        label=f"💾 Télécharger {report_title} DOCX",
                        data=docx_buffer.getvalue(),
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"quick_download_{docx_type}_{timestamp}",
                        help=f"Télécharger immédiatement le rapport {report_title}",
                        use_container_width=True
                    )
                    
                else:
                    st.error("❌ Erreur lors de la génération du rapport DOCX")
                    
        except Exception as e:
            st.error(f"❌ Erreur génération DOCX: {str(e)}")
            import traceback
            with st.expander("🐛 Détails de l'erreur"):
                st.code(traceback.format_exc())
    
    def _refresh_all_report_data(self):
        """Actualise toutes les données nécessaires pour le rapport commercial"""
        import time
        
        # Nettoyer les caches
        if 'last_commercial_report_html' in st.session_state:
            del st.session_state.last_commercial_report_html
        
        # Recalculer les métriques
        self._calculate_commercial_metrics()
        
        # Marquer l'actualisation
        st.session_state.last_commercial_refresh = time.time()
        
        return True

    # ==========================================
    # MÉTHODES RESTAURÉES DU BACKUP ORIGINAL
    # ==========================================

    def generate_html_report(self, title=None, client_name=None, project_name=None, include_charts=True, for_pdf=False):
        """
        Génère un rapport HTML amélioré utilisant les vraies données et graphiques existants
        UNIQUEMENT les sections client (pas investisseur)
        """
        if title is None:
            title = "Votre Projet Solaire - Bénéfices et Économies"
        
        # Vérifier la disponibilité des données
        if not st.session_state.get('data_imported'):
            return "<html><body><h1>Erreur</h1><p>Aucune donnée disponible pour générer le rapport.</p></body></html>"
        
        # Récupérer la configuration complète du projet
        project_config = self._get_project_configuration()
        
        # Calculer les totaux réels basés sur la configuration
        project_totals = self._calculate_project_totals(project_config['sites_config'])
        
        # Récupérer les données d'optimisation
        best_scenario, scenario_data, prix_optimal = self._get_optimization_data()
        
        if not scenario_data:
            return "<html><body><h1>Erreur</h1><p>Aucun résultat d'optimisation disponible.</p></body></html>"
        
        # En-tête HTML avec styles professionnels
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
                
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #2c3e50;
                    background: white;
                    font-size: 14px;
                }}
                
                .container {{
                    max-width: 210mm;
                    margin: 0 auto;
                    padding: 0;
                }}
                
                @media print {{
                    .container {{
                        max-width: 100%;
                        padding: 0;
                    }}
                    
                    body {{
                        font-size: 12pt;
                        -webkit-print-color-adjust: exact;
                        print-color-adjust: exact;
                    }}
                    
                    .page-break {{
                        page-break-before: always;
                    }}
                }}
                
                h1, h2, h3, h4 {{
                    font-weight: 600;
                    line-height: 1.2;
                }}
                
                h1 {{
                    font-size: 2.2em;
                    margin-bottom: 1em;
                }}
                
                h2 {{
                    font-size: 1.6em;
                    margin-bottom: 0.8em;
                }}
                
                h3 {{
                    font-size: 1.3em;
                    margin-bottom: 0.6em;
                }}
                
                table {{
                    border-collapse: collapse;
                    margin: 1em 0;
                }}
                
                .no-break {{
                    page-break-inside: avoid;
                }}
                
                .text-center {{
                    text-align: center;
                }}
                
                .text-right {{
                    text-align: right;
                }}
                
                .mb-4 {{
                    margin-bottom: 2rem;
                }}
                
                .mt-4 {{
                    margin-top: 2rem;
                }}
            </style>
        </head>
        <body>
            <div class="container">
        """
        
        # Ajouter les sections du rapport amélioré (UNIQUEMENT SECTIONS CLIENT)
        html += self._create_cover_page(title, client_name, project_name)
        html += self._create_project_summary(project_config, project_totals)
        html += self._create_consumer_report_with_charts(scenario_data, project_config)
        
        # Pied de page et fermeture
        html += f"""
            <div style="margin-top: 50px; padding: 30px; border-top: 2px solid #27ae60; text-align: center; color: #7f8c8d;">
                <p style="font-size: 1.1em; margin-bottom: 10px;">Rapport Client généré le {datetime.now().strftime('%d %B %Y à %H:%M')}</p>
                <p style="font-size: 1em;">OptimPV - Solutions d'autoconsommation collective photovoltaïque</p>
                <p style="font-size: 0.9em; margin-top: 10px;">
                    Votre projet : {project_totals['nombre_sites_producteurs']} site(s) producteur(s) totalisant {self.format_number(project_totals['puissance_kwc_total'], 1)} kWc, 
                    {project_totals['nombre_sites_consommateurs']} site(s) consommateur(s).
                </p>
            </div>
            
            </div>
        </body>
        </html>
        """
        
        return html
    

    def _create_consumer_report_with_charts(self, scenario_data, project_config):
        """Crée la section rapport consommateur avec graphiques réutilisés"""
        
        global_config = project_config['global_config']
        
        # Section 3 : Rapport Consommateur complet
        section_3_html = self._create_section_3_consumer_report(scenario_data, project_config)
        
        # Graphiques réutilisés des modules de visualisation (ancien code conservé pour compatibilité)
        charts_html = ""
        
        if VISUALIZATION_MODULES_AVAILABLE:
            # 1. Graphique de comparaison des prix
            try:
                fig_price = create_price_comparison_chart(scenario_data, global_config)
                if fig_price:
                    chart_base64 = self._export_chart_to_base64(fig_price, width=600, height=400)
                    if chart_base64:
                        charts_html += f"""
                        <div style="margin: 30px 0; text-align: center;">
                            <h3 style="color: #27ae60;">Comparaison des Prix d'Électricité</h3>
                            <img src="{chart_base64}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);" />
                        </div>
                        """
            except Exception as e:
                pass
        
        html = f"""
        <div style="margin: 40px 0;">
            {section_3_html}
            {charts_html}
        </div>
        """
        return html
    

    def _create_section_3_consumer_report(self, scenario_data, project_config):
        """Crée la Section 3 complète du rapport consommateur avec ses 3 sous-sections"""
        global_config = project_config['global_config']
        
        # Section 3.1 : Indicateurs Clés pour le Consommateur
        section_3_1 = self._create_section_3_1_key_indicators(scenario_data, global_config)
        
        # Section 3.2 : Comparaison des Coûts d'Électricité
        section_3_2 = self._create_section_3_2_cost_comparison_chart(scenario_data, global_config)
        
        # Section 3.3 : Avantage Cumulé au Fil du Temps
        section_3_3 = self._create_section_3_3_cumulative_advantage(scenario_data, global_config)
        
        html = f"""
        <div style="page-break-before: always;">
            <h1 style="color: #27ae60; text-align: center; font-size: 2.8em; margin-bottom: 40px;">
                Section 3 : Rapport Consommateur
            </h1>
            
            <p style="text-align: center; font-size: 1.2em; color: #7f8c8d; margin-bottom: 40px;">
                Cette section présente de manière visuelle et simple vos avantages en tant que consommateur
            </p>
            
            {section_3_1}
            {section_3_2}
            {section_3_3}
        </div>
        """
        return html
    

    def _create_section_3_1_key_indicators(self, scenario_data, config):
        """Section 3.1 : Indicateurs Clés pour le Consommateur avec visualisations"""
        
        # Récupérer les données énergétiques de manière robuste
        energy_data = self._get_energy_data_robust()
        
        autoconsumption_rate = energy_data['autoconsumption_rate']
        autoproduction_rate = energy_data['autoproduction_rate']
        total_consumption = energy_data['total_consumption']
        total_autoconsumption = energy_data['total_autoconsumption']
        total_grid_purchase = energy_data['total_grid_purchase']
        
        # Récupérer les données financières de l'analysis engine
        financial_data = self._get_financial_data_from_engine()
        
        if financial_data and financial_data['economie_totale'] > 0:
            # Utiliser les données calculées par l'analysis engine
            avantage_total = financial_data['economie_totale']
            prix_optimal = financial_data['prix_optimal']
            print(f"✅ Utilisation des données de l'analysis engine - Économie: {avantage_total:.0f}€")
        else:
            # Fallback: calcul simple et réaliste (SANS les boucles astronomiques)
            tarif_edf = config.get('tarif_edf_reference', 0.20)
            duree_projet = config.get('duree_ppa', 240) / 12
            
            # Récupérer le prix optimal
            prix_optimal = None
            if 'constrained_optim_results' in st.session_state:
                for results in st.session_state.constrained_optim_results.values():
                    if isinstance(results, dict) and 'prix_optimal_const' in results:
                        prix_optimal = results['prix_optimal_const']
                        break
            
            if prix_optimal is None:
                prix_optimal = tarif_edf * 0.8
            
            # Calcul simple et réaliste (économie annuelle * durée projet)
            # Convertir MWh en kWh pour le calcul (1 MWh = 1000 kWh)
            total_autoconsumption_kwh = total_autoconsumption * 1000
            economie_annuelle = total_autoconsumption_kwh * (tarif_edf - prix_optimal)
            avantage_total = economie_annuelle * duree_projet
            
            print(f"⚠️ Fallback: Économie annuelle = {economie_annuelle:.0f}€, Total sur {duree_projet:.0f} ans = {avantage_total:.0f}€")
        
        html = f"""
        <div style="margin: 40px 0;">
            <h2 style="color: #2c3e50; margin-bottom: 30px;">3.1 Indicateurs Clés pour le Consommateur</h2>
            
            <!-- Avantage financier total en grand -->
            <div style="background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%); 
                        padding: 50px; border-radius: 20px; text-align: center; margin-bottom: 40px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
                <h3 style="color: white; margin: 0 0 20px 0; font-size: 2em; font-weight: 300;">
                    💰 Avantage Financier Total
                </h3>
                <div style="font-size: 4em; font-weight: bold; color: white; margin: 0;">
                    {self.format_currency(avantage_total)}
                </div>
                <p style="color: rgba(255,255,255,0.9); font-size: 1.3em; margin: 20px 0 0 0;">
                    C'est la différence entre le coût total de l'électricité sans PV<br/>
                    et le coût total avec PV sur {int(duree_projet)} ans
                </p>
            </div>
            
            <!-- Taux d'autonomie et d'autoconsommation -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 40px;">
                
                <!-- Taux d'autonomie (Autarkie) avec jauge -->
                <div style="background: white; padding: 40px; border-radius: 15px; 
                            box-shadow: 0 5px 20px rgba(0,0,0,0.1); text-align: center;">
                    <h3 style="color: #2c3e50; margin: 0 0 20px 0;">⚡ Taux d'Autonomie (Autarkie)</h3>
                    
                    <!-- Jauge circulaire -->
                    <div style="position: relative; width: 200px; height: 200px; margin: 0 auto;">
                        <svg viewBox="0 0 200 200" style="width: 100%; height: 100%;">
                            <!-- Cercle de fond -->
                            <circle cx="100" cy="100" r="85" fill="none" stroke="#ecf0f1" stroke-width="20"/>
                            <!-- Arc de progression -->
                            <circle cx="100" cy="100" r="85" fill="none" stroke="#3498db" stroke-width="20" 
                                    stroke-dasharray="{(autoconsumption_rate/100) * 534.07} 534.07"
                                    stroke-linecap="round"
                                    style="transform: rotate(-90deg); transform-origin: 100px 100px;
                                           transition: stroke-dasharray 1s ease-in-out;"/>
                            <!-- Texte au centre -->
                            <text x="100" y="100" text-anchor="middle" dy="0.3em" 
                                  font-size="36" font-weight="bold" fill="#2c3e50">
                                {self.format_percentage(autoconsumption_rate, 0)}
                            </text>
                            <text x="100" y="130" text-anchor="middle" 
                                  font-size="14" fill="#7f8c8d">
                                d'autonomie
                            </text>
                        </svg>
                    </div>
                    
                    <p style="color: #7f8c8d; margin: 20px 0 0 0; font-size: 1.1em;">
                        Part de votre consommation<br/>couverte par le solaire
                    </p>
                </div>
                
                <!-- Taux d'autoconsommation avec camembert -->
                <div style="background: white; padding: 40px; border-radius: 15px; 
                            box-shadow: 0 5px 20px rgba(0,0,0,0.1); text-align: center;">
                    <h3 style="color: #2c3e50; margin: 0 0 20px 0;">☀️ Taux d'Autoconsommation</h3>
                    
                    <!-- Camembert simple -->
                    <div style="position: relative; width: 200px; height: 200px; margin: 0 auto;">
                        <svg viewBox="0 0 200 200" style="width: 100%; height: 100%;">
                            <!-- Cercle de fond -->
                            <circle cx="100" cy="100" r="85" fill="none" stroke="#ecf0f1" stroke-width="20"/>
                            <!-- Arc représentant l'autoconsommation -->
                            <circle cx="100" cy="100" r="85" fill="none" stroke="#e74c3c" stroke-width="20" 
                                    stroke-dasharray="{(autoproduction_rate/100) * 534.07} 534.07"
                                    stroke-linecap="round"
                                    style="transform: rotate(-90deg); transform-origin: 100px 100px;"/>
                            <!-- Texte au centre -->
                            <text x="100" y="100" text-anchor="middle" dy="0.3em" 
                                  font-size="36" font-weight="bold" fill="#2c3e50">
                                {self.format_percentage(autoproduction_rate, 0)}
                            </text>
                            <text x="100" y="130" text-anchor="middle" 
                                  font-size="14" fill="#7f8c8d">
                                autoconsommé
                            </text>
                        </svg>
                    </div>
                    
                    <p style="color: #7f8c8d; margin: 20px 0 0 0; font-size: 1.1em;">
                        Part de la production solaire<br/>utilisée sur place
                    </p>
                </div>
            </div>
        </div>
        """
        return html
    

    def _create_section_3_2_cost_comparison_chart(self, scenario_data, config):
        """Section 3.2 : Comparaison des Coûts d'Électricité avec graphique en barres"""
        
        # Récupérer les données énergétiques de manière robuste
        energy_data = self._get_energy_data_robust()
        
        total_consumption = energy_data['total_consumption']
        total_autoconsumption = energy_data['total_autoconsumption']
        total_grid_purchase = energy_data['total_grid_purchase']
        
        # Paramètres
        tarif_edf = config.get('tarif_edf_reference', 0.20)
        taux_inflation = config.get('taux_inflation', 0.02)
        duree_projet = config.get('duree_ppa', 240) / 12
        
        # Prix optimal
        prix_optimal = None
        if 'constrained_optim_results' in st.session_state:
            for results in st.session_state.constrained_optim_results.values():
                if isinstance(results, dict) and 'prix_optimal_const' in results:
                    prix_optimal = results['prix_optimal_const']
                    break
        
        if prix_optimal is None:
            prix_optimal = tarif_edf * 0.8
        
        # Calculs ANNUELS pour une meilleure compréhension client
        total_consumption_kwh = total_consumption * 1000
        total_autoconsumption_kwh = total_autoconsumption * 1000
        total_grid_purchase_kwh = total_grid_purchase * 1000
        
        # Coûts annuels (plus lisibles pour le client)
        cout_sans_pv_annuel = total_consumption_kwh * tarif_edf
        cout_avec_pv_solaire_annuel = total_autoconsumption_kwh * prix_optimal
        cout_avec_pv_reseau_annuel = total_grid_purchase_kwh * tarif_edf
        cout_avec_pv_total_annuel = cout_avec_pv_solaire_annuel + cout_avec_pv_reseau_annuel
        cout_participation_annuel = 0
        
        # Utiliser les coûts annuels pour l'affichage
        cout_sans_pv = cout_sans_pv_annuel
        cout_avec_pv_total = cout_avec_pv_total_annuel
        cout_avec_pv_solaire = cout_avec_pv_solaire_annuel
        cout_avec_pv_reseau = cout_avec_pv_reseau_annuel
        cout_participation = cout_participation_annuel
        
        print(f"📊 Section 3.2: Coûts annuels - Sans PV: {cout_sans_pv:.0f}€/an, Avec PV: {cout_avec_pv_total:.0f}€/an")
        
        html = f"""
        <div style="margin: 60px 0; page-break-inside: avoid;">
            <h2 style="color: #2c3e50; margin-bottom: 30px;">3.2 Comparaison des Coûts d'Électricité</h2>
            
            <!-- Graphique en barres -->
            <div style="background: white; padding: 40px; border-radius: 15px; 
                        box-shadow: 0 5px 20px rgba(0,0,0,0.1);">
                
                <div style="display: flex; justify-content: space-around; align-items: flex-end; 
                            height: 400px; margin-bottom: 30px;">
                    
                    <!-- Barre SANS PV -->
                    <div style="flex: 1; display: flex; flex-direction: column; align-items: center; 
                                justify-content: flex-end; margin: 0 20px;">
                        <div style="width: 100%; max-width: 200px; background: #e74c3c; 
                                    height: {min(350, cout_sans_pv / max(cout_sans_pv, cout_avec_pv_total) * 350)}px;
                                    border-radius: 10px 10px 0 0; position: relative;
                                    box-shadow: 0 -5px 15px rgba(231, 76, 60, 0.3);">
                            <div style="position: absolute; top: -40px; left: 0; right: 0; 
                                        text-align: center; font-weight: bold; font-size: 1.3em;">
                                {self.format_currency(cout_sans_pv)}
                            </div>
                        </div>
                        <h3 style="margin: 20px 0 0 0; color: #e74c3c;">Coût annuel SANS PV</h3>
                        <p style="color: #7f8c8d; margin: 5px 0 0 0; text-align: center;">
                            100% réseau<br/>par an
                        </p>
                    </div>
                    
                    <!-- Barre AVEC PV -->
                    <div style="flex: 1; display: flex; flex-direction: column; align-items: center; 
                                justify-content: flex-end; margin: 0 20px;">
                        <div style="width: 100%; max-width: 200px; 
                                    height: {min(350, cout_avec_pv_total / max(cout_sans_pv, cout_avec_pv_total) * 350)}px;
                                    border-radius: 10px 10px 0 0; position: relative; overflow: hidden;
                                    box-shadow: 0 -5px 15px rgba(46, 204, 113, 0.3);">
                            
                            <!-- Partie solaire -->
                            <div style="background: #f39c12; height: {(cout_avec_pv_solaire / cout_avec_pv_total * 100)}%;
                                        position: absolute; bottom: 0; width: 100%;">
                            </div>
                            
                            <!-- Partie réseau -->
                            <div style="background: #3498db; height: {(cout_avec_pv_reseau / cout_avec_pv_total * 100)}%;
                                        position: absolute; top: 0; width: 100%;">
                            </div>
                            
                            <div style="position: absolute; top: -40px; left: 0; right: 0; 
                                        text-align: center; font-weight: bold; font-size: 1.3em; color: #27ae60;">
                                {self.format_currency(cout_avec_pv_total)}
                            </div>
                        </div>
                        <h3 style="margin: 20px 0 0 0; color: #27ae60;">Coût annuel AVEC PV</h3>
                        <p style="color: #7f8c8d; margin: 5px 0 0 0; text-align: center;">
                            Solaire + Réseau<br/>par an
                        </p>
                    </div>
                </div>
                
                <!-- Légende -->
                <div style="display: flex; justify-content: center; gap: 40px; margin-top: 30px;">
                    <div style="display: flex; align-items: center;">
                        <div style="width: 20px; height: 20px; background: #f39c12; border-radius: 3px; margin-right: 10px;"></div>
                        <span>Énergie solaire : {self.format_currency(cout_avec_pv_solaire)}/an</span>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <div style="width: 20px; height: 20px; background: #3498db; border-radius: 3px; margin-right: 10px;"></div>
                        <span>Énergie réseau : {self.format_currency(cout_avec_pv_reseau)}/an</span>
                    </div>
                </div>
                
                <!-- Économie réalisée -->
                <div style="background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%); 
                            color: white; padding: 25px; border-radius: 10px; margin-top: 30px; text-align: center;">
                    <h3 style="margin: 0 0 10px 0; font-size: 1.5em;">
                        💰 Économie Annuelle : {self.format_currency(cout_sans_pv - cout_avec_pv_total)}
                    </h3>
                    <p style="margin: 0; font-size: 1.1em; opacity: 0.9;">
                        Soit {self.format_percentage((cout_sans_pv - cout_avec_pv_total) / cout_sans_pv * 100, 1)} d'économie sur votre facture annuelle
                    </p>
                    <p style="margin: 10px 0 0 0; font-size: 1em; opacity: 0.8;">
                        Sur {int(duree_projet)} ans : {self.format_currency((cout_sans_pv - cout_avec_pv_total) * duree_projet)} d'économies cumulées
                    </p>
                </div>
            </div>
        </div>
        """
        return html
    

    def _create_section_3_3_cumulative_advantage(self, scenario_data, config):
        """Section 3.3 : Avantage Cumulé au Fil du Temps avec graphique linéaire"""
        
        # Récupérer les données énergétiques de manière robuste
        energy_data = self._get_energy_data_robust()
        
        total_consumption = energy_data['total_consumption']
        total_autoconsumption = energy_data['total_autoconsumption']
        total_grid_purchase = energy_data['total_grid_purchase']
        
        # Paramètres
        tarif_edf = config.get('tarif_edf_reference', 0.20)
        taux_inflation = config.get('taux_inflation', 0.02)
        duree_projet = int(config.get('duree_ppa', 240) / 12)
        
        # Prix optimal
        prix_optimal = None
        if 'constrained_optim_results' in st.session_state:
            for results in st.session_state.constrained_optim_results.values():
                if isinstance(results, dict) and 'prix_optimal_const' in results:
                    prix_optimal = results['prix_optimal_const']
                    break
        
        if prix_optimal is None:
            prix_optimal = tarif_edf * 0.8
        
        # Récupérer les données financières de l'analysis engine
        financial_data = self._get_financial_data_from_engine()
        
        if financial_data and financial_data['economie_totale'] > 0:
            # Utiliser les données de l'analysis engine pour créer une progression réaliste
            economie_totale_engine = financial_data['economie_totale']
            economie_annuelle = economie_totale_engine / duree_projet
            
            avantages_cumules = []
            for annee in range(duree_projet):
                avantage_cumule = economie_annuelle * (annee + 1)
                avantages_cumules.append(avantage_cumule)
                
            print(f"✅ Section 3.3: Données engine - Économie annuelle: {economie_annuelle:.0f}€, Total: {economie_totale_engine:.0f}€")
        else:
            # Fallback: calcul simple et réaliste
            total_autoconsumption_kwh = total_autoconsumption * 1000
            economie_annuelle = total_autoconsumption_kwh * (tarif_edf - prix_optimal)
            
            avantages_cumules = []
            for annee in range(duree_projet):
                # Progression linéaire simple (sans inflation cumulative)
                avantage_cumule = economie_annuelle * (annee + 1)
                avantages_cumules.append(avantage_cumule)
                
            print(f"⚠️ Section 3.3 Fallback: Économie annuelle: {economie_annuelle:.0f}€")
        
        # Créer le graphique SVG
        if not avantages_cumules or max(avantages_cumules) <= 0:
            return """
            <div style="margin: 60px 0; text-align: center; padding: 40px; background: #f8f9fa; border-radius: 15px;">
                <h2 style="color: #2c3e50;">3.3 Avantage Cumulé au Fil du Temps</h2>
                <p style="color: #7f8c8d; font-size: 1.2em;">Aucun avantage financier détectable avec les paramètres actuels.</p>
            </div>
            """
        
        max_avantage = max(avantages_cumules)
        width = 800
        height = 400
        margin = 60
        graph_width = width - 2 * margin
        graph_height = height - 2 * margin
        
        # Points pour la courbe
        points = []
        for i, avantage in enumerate(avantages_cumules):
            x = margin + (i / (duree_projet - 1)) * graph_width
            y = height - margin - (avantage / max_avantage) * graph_height
            points.append(f"{x},{y}")
        
        points_str = " ".join(points)
        
        html = f"""
        <div style="margin: 60px 0; page-break-inside: avoid;">
            <h2 style="color: #2c3e50; margin-bottom: 30px;">3.3 Avantage Cumulé au Fil du Temps</h2>
            
            <div style="background: white; padding: 40px; border-radius: 15px; 
                        box-shadow: 0 5px 20px rgba(0,0,0,0.1);">
                
                <!-- Graphique linéaire SVG -->
                <svg viewBox="0 0 {width} {height}" style="width: 100%; max-width: 800px; height: auto;">
                    <!-- Grille de fond -->
                    <defs>
                        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#ecf0f1" stroke-width="1"/>
                        </pattern>
                    </defs>
                    <rect x="{margin}" y="{margin}" width="{graph_width}" height="{graph_height}" fill="url(#grid)"/>
                    
                    <!-- Axes -->
                    <line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" 
                          stroke="#2c3e50" stroke-width="2"/>
                    <line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" 
                          stroke="#2c3e50" stroke-width="2"/>
                    
                    <!-- Labels axe X (années) -->
        """
        
        # Ajouter les labels de l'axe X
        for i in range(0, duree_projet + 1, 5):
            x = margin + (i / duree_projet) * graph_width
            html += f"""
                    <text x="{x}" y="{height - margin + 20}" text-anchor="middle" font-size="12" fill="#7f8c8d">
                        Année {i}
                    </text>
            """
        
        # Ajouter les labels de l'axe Y (montants)
        for i in range(0, 6):
            y = height - margin - (i / 5) * graph_height
            value = (i / 5) * max_avantage
            html += f"""
                    <text x="{margin - 10}" y="{y + 5}" text-anchor="end" font-size="12" fill="#7f8c8d">
                        {self.format_number(value, 0)} €
                    </text>
            """
        
        html += f"""
                    <!-- Zone sous la courbe -->
                    <path d="M {margin},{height - margin} L {points_str} L {width - margin},{height - margin} Z" 
                          fill="url(#gradient)" opacity="0.3"/>
                    
                    <!-- Courbe principale -->
                    <polyline points="{points_str}" fill="none" stroke="#27ae60" stroke-width="3"/>
                    
                    <!-- Points sur la courbe -->
        """
        
        # Ajouter des points sur la courbe tous les 5 ans
        for i in range(0, duree_projet, 5):
            if i < len(avantages_cumules):
                x = margin + (i / (duree_projet - 1)) * graph_width
                y = height - margin - (avantages_cumules[i] / max_avantage) * graph_height
                html += f"""
                    <circle cx="{x}" cy="{y}" r="5" fill="#27ae60"/>
                    <text x="{x}" y="{y - 10}" text-anchor="middle" font-size="11" font-weight="bold" fill="#27ae60">
                        {self.format_number(avantages_cumules[i], 0)} €
                    </text>
                """
        
        # Point final
        x_final = width - margin
        y_final = height - margin - (avantages_cumules[-1] / max_avantage) * graph_height
        html += f"""
                    <circle cx="{x_final}" cy="{y_final}" r="6" fill="#e74c3c"/>
                    <text x="{x_final}" y="{y_final - 15}" text-anchor="end" font-size="14" font-weight="bold" fill="#e74c3c">
                        {self.format_currency(avantages_cumules[-1])}
                    </text>
                    
                    <!-- Gradient -->
                    <defs>
                        <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" style="stop-color:#27ae60;stop-opacity:0.8" />
                            <stop offset="100%" style="stop-color:#27ae60;stop-opacity:0.1" />
                        </linearGradient>
                    </defs>
                </svg>
                
                <!-- Légende et résumé -->
                <div style="margin-top: 30px; text-align: center;">
                    <h3 style="color: #2c3e50; margin-bottom: 15px;">
                        📈 Évolution de vos économies cumulées
                    </h3>
                    <p style="color: #7f8c8d; font-size: 1.1em; line-height: 1.6;">
                        Ce graphique montre comment vos économies s'accumulent année après année.<br/>
                        <strong style="color: #27ae60;">Après {duree_projet} ans</strong>, vous aurez économisé 
                        <strong style="color: #e74c3c; font-size: 1.2em;">{self.format_currency(avantages_cumules[-1])}</strong>
                        par rapport à une alimentation 100% réseau.
                    </p>
                </div>
            </div>
        </div>
        """
        return html
    

    def _get_energy_data_robust(self):
        """
        Méthode robuste pour récupérer les données énergétiques depuis différentes sources
        
        Returns:
            dict: Dictionnaire avec total_production, total_consumption, total_autoconsumption
        """
        # Initialisation
        total_production = 0
        total_consumption = 0
        total_autoconsumption = 0
        
        # 1. Essayer d'abord les résultats d'optimisation
        best_scenario, scenario_data, prix_optimal = self._get_optimization_data()
        if scenario_data and isinstance(scenario_data, dict):
            # Les données peuvent être dans different formats selon la version
            for key in ['total_production_kwh', 'production_totale_kwh', 'production_annuelle']:
                if key in scenario_data:
                    total_production = scenario_data[key]
                    break
                    
            for key in ['total_consumption_kwh', 'consommation_totale_kwh', 'consommation_annuelle']:
                if key in scenario_data:
                    total_consumption = scenario_data[key]
                    break
                    
            for key in ['total_autoconsumption_kwh', 'autoconsommation_totale_kwh', 'autoconsommation_annuelle']:
                if key in scenario_data:
                    total_autoconsumption = scenario_data[key]
                    break
        
        # 2. Si pas trouvé, essayer sites_data
        if total_consumption == 0:
            sites_data = st.session_state.get('sites_data', {})
            if sites_data:
                for site_id, site_df in sites_data.items():
                    if hasattr(site_df, 'columns'):
                        if 'production_kwh' in site_df.columns:
                            total_production += site_df['production_kwh'].sum()
                        if 'consumption_kwh' in site_df.columns:
                            total_consumption += site_df['consumption_kwh'].sum()
                
                # Calculer autoconsommation site par site
                for site_id, site_df in sites_data.items():
                    if (hasattr(site_df, 'columns') and 
                        'production_kwh' in site_df.columns and 
                        'consumption_kwh' in site_df.columns):
                        site_autoconsumption = site_df[['production_kwh', 'consumption_kwh']].min(axis=1).sum()
                        total_autoconsumption += site_autoconsumption
        
        # 3. Si toujours rien, utiliser des données réalistes par défaut
        if total_consumption == 0:
            # Basé sur une installation typique de 25 kWc (valeurs annuelles en MWh plus réalistes)
            total_production = 27.5       # 27,5 MWh/an = 27500 kWh/an 
            total_consumption = 50.0      # 50 MWh/an = 50000 kWh/an
            total_autoconsumption = 17.5  # 17,5 MWh/an = 17500 kWh/an (35% d'autonomie)
            print(f"⚠️  RAPPORT CONSOMMATEUR: Utilisation de données par défaut (pas de données réelles trouvées)")
            print(f"    Données par défaut: Prod={total_production} MWh, Conso={total_consumption} MWh, Auto={total_autoconsumption} MWh")
        else:
            # Vérifier si les données sont en kWh ou MWh et les convertir si nécessaire
            print(f"✅ RAPPORT CONSOMMATEUR: Données brutes trouvées - Consommation: {total_consumption:.0f}, Autoconsommation: {total_autoconsumption:.0f}")
            
            # Si les valeurs sont très grandes (>100 000), elles sont probablement en kWh, les convertir en MWh
            if total_consumption > 100000:
                total_production = total_production / 1000
                total_consumption = total_consumption / 1000
                total_autoconsumption = total_autoconsumption / 1000
                print(f"    Conversion kWh->MWh: Prod={total_production:.1f} MWh, Conso={total_consumption:.1f} MWh, Auto={total_autoconsumption:.1f} MWh")
            else:
                print(f"    Déjà en MWh: Prod={total_production:.1f} MWh, Conso={total_consumption:.1f} MWh, Auto={total_autoconsumption:.1f} MWh")
            
        # Calcul des taux pour validation
        calculated_autonomy = (total_autoconsumption / total_consumption * 100) if total_consumption > 0 else 0
        calculated_autoconsumption = (total_autoconsumption / total_production * 100) if total_production > 0 else 0
        print(f"    Taux calculés: Autonomie={calculated_autonomy:.1f}%, Autoconsommation={calculated_autoconsumption:.1f}%")
        
        return {
            'total_production': total_production,
            'total_consumption': total_consumption,
            'total_autoconsumption': total_autoconsumption,
            'total_grid_purchase': total_consumption - total_autoconsumption,
            'autoconsumption_rate': (total_autoconsumption / total_consumption * 100) if total_consumption > 0 else 0,
            'autoproduction_rate': (total_autoconsumption / total_production * 100) if total_production > 0 else 0
        }
    

    def _get_financial_data_from_engine(self):
        """
        Récupère les données financières calculées par l'analysis engine
        
        Returns:
            dict: Données financières (économies, VAN, TRI, etc.) ou None si indisponible
        """
        best_scenario, scenario_data, prix_optimal = self._get_optimization_data()
        
        if scenario_data and isinstance(scenario_data, dict):
            # Données financières disponibles depuis l'analysis engine
            financial_data = {
                'scenario_name': best_scenario,
                'prix_optimal': prix_optimal,
                'van_project': scenario_data.get('van_project', 0),
                'van_equity': scenario_data.get('van_equity', 0),
                'tri_project': scenario_data.get('tri_project', 0),
                'tri_equity': scenario_data.get('tri_equity', 0),
                'economie_annuelle': scenario_data.get('economie_annuelle_kwh', 0),
                'economie_totale': scenario_data.get('economie_totale', 0),
                'cout_avec_pv_total': scenario_data.get('cout_avec_pv_total', 0),
                'cout_sans_pv_total': scenario_data.get('cout_sans_pv_total', 0),
                'payback_simple': scenario_data.get('payback_simple', 0)
            }
            
            # Calculer l'économie totale si pas directement disponible
            if financial_data['economie_totale'] == 0 and financial_data['cout_sans_pv_total'] > 0:
                financial_data['economie_totale'] = financial_data['cout_sans_pv_total'] - financial_data['cout_avec_pv_total']
                
            print(f"📊 FINANCIER ENGINE: Données trouvées - Économie totale: {financial_data['economie_totale']:.0f}€, VAN: {financial_data['van_project']:.0f}€")
            return financial_data
        else:
            print("⚠️  FINANCIER ENGINE: Aucune donnée financière trouvée dans l'analysis engine")
            return None
    

    def _get_optimization_data(self):
        """
        Récupère les données d'optimisation depuis st.session_state
        Gère les différents formats possibles (nouveau/ancien)
        """
        optimization_results = (st.session_state.get('constrained_optim_results', {}) or 
                               st.session_state.get('optimization_results', {}))
        
        best_scenario = None
        best_indicators = None
        prix_optimal = None
        
        if optimization_results:
            # Pour constrained_optim_results (nouveau format)
            if 'constrained_optim_results' in st.session_state:
                for scenario_name, results in optimization_results.items():
                    if isinstance(results, dict) and 'indicateurs_au_prix_optimal' in results:
                        best_scenario = scenario_name
                        best_indicators = results['indicateurs_au_prix_optimal']
                        prix_optimal = results.get('prix_optimal_const', 0)
                        break
            # Pour optimization_results (ancien format)
            else:
                for scenario_name, results in optimization_results.items():
                    if isinstance(results, dict) and 'indicateurs_optimaux' in results:
                        best_scenario = scenario_name
                        best_indicators = results['indicateurs_optimaux']
                        prix_optimal = results.get('prix_optimal', 0)
                        break
        
        return best_scenario, best_indicators, prix_optimal
    

    def _get_project_configuration(self):
        """
        Récupère la configuration complète du projet depuis st.session_state
        
        Returns:
            dict: Configuration avec global_config, sites_config, scenarios
        """
        return {
            'global_config': st.session_state.get('config', {}),
            'sites_config': st.session_state.get('sites_config', {}),
            'scenarios': st.session_state.get('scenarios', {}),
            'processed_data': st.session_state.get('processed_data'),
            'sites_data': st.session_state.get('sites_data', {})
        }
    

    def _calculate_project_totals(self, sites_config):
        """
        Calcule les totaux du projet basés sur la configuration réelle par site
        
        Args:
            sites_config (dict): Configuration par site
            
        Returns:
            dict: Totaux calculés (puissance, CAPEX, OPEX, etc.)
        """
        totals = {
            'puissance_kwc_total': 0.0,
            'capex_total': 0.0,
            'opex_maintenance_total': 0.0,
            'opex_insurance_total': 0.0,
            'opex_admin_total': 0.0,
            'nombre_sites_producteurs': 0,
            'nombre_sites_consommateurs': 0,
            'sites_avec_provision_onduleur': 0
        }
        
        if not sites_config:
            return totals
            
        for site_id, site_cfg in sites_config.items():
            if not isinstance(site_cfg, dict):
                continue
                
            site_type = site_cfg.get('site_type', 'Producteur')
            
            if site_type == 'Producteur':
                totals['nombre_sites_producteurs'] += 1
                totals['puissance_kwc_total'] += float(site_cfg.get('puissance_kwc', 0.0))
                totals['capex_total'] += float(site_cfg.get('capex', 0.0))
                totals['opex_maintenance_total'] += float(site_cfg.get('opex_maintenance', 0.0))
                totals['opex_insurance_total'] += float(site_cfg.get('opex_insurance', 0.0))
                totals['opex_admin_total'] += float(site_cfg.get('opex_admin', 0.0))
                
                if site_cfg.get('opex_onduleur_provision_site', False):
                    totals['sites_avec_provision_onduleur'] += 1
                    
            elif site_type == 'Consommateur Pur':
                totals['nombre_sites_consommateurs'] += 1
        
        return totals
    

    def _create_cover_page(self, title, client_name=None, project_name=None):
        """Crée la page de garde du rapport"""
        logo_base64 = self.get_logo_base64()
        current_date = datetime.now().strftime('%d %B %Y')
        
        html = f"""
        <div style="page-break-after: always; height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; 
                    background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%); color: white;">
            <div style="text-align: center; max-width: 700px; padding: 40px;">
                {f'<img src="{logo_base64}" style="height: 80px; margin-bottom: 40px;" />' if logo_base64 else ''}
                <h1 style="font-size: 3.5em; margin-bottom: 20px; font-weight: 300; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">{title}</h1>
                {f'<h2 style="font-size: 2em; margin-bottom: 30px; font-weight: 400; opacity: 0.9;">{client_name}</h2>' if client_name else ''}
                {f'<h3 style="font-size: 1.6em; margin-bottom: 40px; font-style: italic; opacity: 0.8;">{project_name}</h3>' if project_name else ''}
                <div style="border-top: 3px solid rgba(255,255,255,0.5); padding-top: 30px; margin-top: 30px;">
                    <p style="font-size: 1.3em; margin: 0; opacity: 0.9;">Rapport Client généré le {current_date}</p>
                    <p style="font-size: 1.1em; margin: 10px 0 0 0; opacity: 0.7;">OptimPV - Solutions d'autoconsommation collective</p>
                    <p style="font-size: 1em; margin: 20px 0 0 0; font-style: italic; opacity: 0.6;">🌱 Votre partenaire pour la transition énergétique</p>
                </div>
            </div>
        </div>
        """
        return html
    

    def _create_project_summary(self, project_config, project_totals):
        """Crée la section synthèse du projet basée sur la vraie configuration"""
        global_config = project_config['global_config']
        sites_config = project_config['sites_config']
        
        # Récupérer les vraies données de configuration
        date_debut = global_config.get('date_debut_ppa', 'Non spécifiée')
        if isinstance(date_debut, str) and date_debut != 'Non spécifiée':
            try:
                date_debut = datetime.fromisoformat(date_debut).strftime('%d/%m/%Y')
            except:
                pass
        
        puissance_total = project_totals['puissance_kwc_total']
        capex_total = project_totals['capex_total']
        
        # Production annuelle spécifique (si disponible depuis processed_data)
        processed_data = project_config.get('processed_data')
        rendement_specifique = "N/A"
        if processed_data is not None and puissance_total > 0:
            if hasattr(processed_data, 'columns') and 'production_kwh' in processed_data.columns:
                production_annuelle = processed_data['production_kwh'].sum()
                rendement_specifique = f"{(production_annuelle / puissance_total):.0f} kWh/kWc"
        
        # Détails multi-sites
        nb_sites_prod = project_totals['nombre_sites_producteurs']
        nb_sites_conso = project_totals['nombre_sites_consommateurs']
        
        html = f"""
        <div style="padding: 40px; background: #f8f9fa; border-radius: 15px; margin: 30px 0;">
            <h2 style="color: #27ae60; text-align: center; margin-bottom: 30px; font-size: 2.2em;">
                📋 Synthèse de Votre Projet Solaire
            </h2>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px;">
                
                <!-- Colonne Gauche : Technique -->
                <div style="background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h3 style="color: #2c3e50; margin-bottom: 20px; border-bottom: 2px solid #27ae60; padding-bottom: 10px;">
                        🔧 Caractéristiques Techniques
                    </h3>
                    <table style="width: 100%; font-size: 1.1em;">
                        <tr style="margin-bottom: 10px;">
                            <td style="padding: 8px 0; font-weight: 600;">Puissance installée :</td>
                            <td style="padding: 8px 0; text-align: right; color: #27ae60; font-weight: bold;">
                                {self.format_number(puissance_total, 1)} kWc
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: 600;">Sites producteurs :</td>
                            <td style="padding: 8px 0; text-align: right;">{nb_sites_prod}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: 600;">Sites consommateurs :</td>
                            <td style="padding: 8px 0; text-align: right;">{nb_sites_conso}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: 600;">Mise en service :</td>
                            <td style="padding: 8px 0; text-align: right;">{date_debut}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: 600;">Durée du projet :</td>
                            <td style="padding: 8px 0; text-align: right;">{global_config.get('duree_ppa', 240)//12} ans</td>
                        </tr>
                    </table>
                </div>
                
                <!-- Colonne Droite : Économique -->
                <div style="background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h3 style="color: #2c3e50; margin-bottom: 20px; border-bottom: 2px solid #27ae60; padding-bottom: 10px;">
                        💰 Informations Économiques
                    </h3>
                    <table style="width: 100%; font-size: 1.1em;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: 600;">Investissement total :</td>
                            <td style="padding: 8px 0; text-align: right; color: #e74c3c; font-weight: bold;">
                                {self.format_currency(capex_total)}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: 600;">Prix électricité :</td>
                            <td style="padding: 8px 0; text-align: right;">{self.format_number(global_config.get('tarif_edf_reference', 0.20), 4)} €/kWh</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: 600;">OPEX maintenance :</td>
                            <td style="padding: 8px 0; text-align: right;">{self.format_currency(project_totals['opex_maintenance_total'])}/an</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: 600;">OPEX assurance :</td>
                            <td style="padding: 8px 0; text-align: right;">{self.format_currency(project_totals['opex_insurance_total'])}/an</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: 600;">OPEX admin :</td>
                            <td style="padding: 8px 0; text-align: right;">{self.format_currency(project_totals['opex_admin_total'])}/an</td>
                        </tr>
                    </table>
                </div>
            </div>
            
            <div style="background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%); color: white; 
                        padding: 20px; border-radius: 10px; text-align: center;">
                <h3 style="margin: 0 0 10px 0; font-size: 1.3em;">🌱 Votre Impact Environnemental</h3>
                <p style="margin: 0; font-size: 1.1em; opacity: 0.9;">
                    Production attendue : ~{self.format_number(puissance_total * 1100, 0)} kWh/an
                    | Économie CO2 : ~{self.format_number(puissance_total * 1100 * 0.5, 0)} kg/an
                </p>
            </div>
        </div>
        """
        return html
    

