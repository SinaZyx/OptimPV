"""
Module de gestion des données pour les rapports commerciaux OptimPV.
Récupère et traite toutes les données nécessaires depuis les analyses.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import logging

# Import des modules financiers existants
try:
    from ..table_finance.financial_summary_table import load_table_map
    from ..table_finance.financial_display_utils import format_value
    TABLE_FINANCE_AVAILABLE = True
except ImportError:
    TABLE_FINANCE_AVAILABLE = False

logger = logging.getLogger(__name__)

class CommercialDataHandler:
    """Gestionnaire des données pour les rapports commerciaux."""
    
    def __init__(self):
        """Initialise le gestionnaire de données."""
        pass
    
    def get_all_project_data(self) -> Dict[str, Any]:
        """
        Récupère toutes les données du projet depuis les analyses OptimPV.
        Utilise les modules financiers existants pour une extraction complète.
        
        Returns:
            Dict contenant toutes les données formatées pour la proposition commerciale
        """
        try:
            # Récupérer les données de base
            project_config = self._get_project_configuration()
            optimization_data = self._get_optimization_data()
            energy_data = self._get_energy_data_robust()
            financial_data = self._get_complete_financial_data()
            
            # Extraction des valeurs principales
            client_name = project_config.get('global_config', {}).get('client_name', 'Client OptimPV')
            
            # Données financières complètes depuis l'optimisation
            best_scenario_name, best_indicators, prix_optimal = optimization_data
            
            # Utiliser les données financières complètes si disponibles
            if financial_data and financial_data.get('is_valid'):
                solar_price = prix_optimal if prix_optimal else financial_data.get('prix_optimal', 15.0)
                annual_savings = financial_data.get('economie_annuelle', 0)
                total_savings_20y = financial_data.get('economie_totale', annual_savings * 20)
                
                # Indicateurs financiers clés
                van_project = financial_data.get('van_project', 0)
                tri_project = financial_data.get('tri_project', 0)
                lcoe = financial_data.get('lcoe', 0)
                payback = financial_data.get('payback_simple', 0)
                dscr_moyen = financial_data.get('dscr_moyen', 0)
                
            elif best_indicators:
                solar_price = prix_optimal if prix_optimal else 15.0
                
                # Extraire depuis best_indicators avec nouvelles clés
                annual_savings = best_indicators.get('avantage_economique_annuel', 
                                best_indicators.get('economie_annuelle_kwh', 0))
                total_savings_20y = annual_savings * 20
                
                # Indicateurs financiers
                van_project = best_indicators.get('npv_project', best_indicators.get('van_project', 0))
                tri_project = best_indicators.get('irr_project', best_indicators.get('tri_project', 0))
                lcoe = best_indicators.get('lcoe', 0)
                payback = best_indicators.get('payback_project', best_indicators.get('payback_simple', 0))
                dscr_moyen = best_indicators.get('avg_dscr', best_indicators.get('dscr_moyen', 0))
                
            else:
                # Valeurs par défaut raisonnables
                solar_price = 15.0
                annual_savings = 7500
                total_savings_20y = 150000
                van_project = 85000
                tri_project = 0.08
                lcoe = 0.12
                payback = 12
                dscr_moyen = 1.4
                
            # Données énergétiques améliorées
            total_production = energy_data.get('total_production', 110000)  # kWh/an plus réaliste
            total_consumption = energy_data.get('total_consumption', 50000)  # kWh/an plus réaliste
            total_autoconsumption = energy_data.get('total_autoconsumption', 17500)
            autoconsumption_rate = energy_data.get('autoconsumption_rate', 35)  # %
            autoproduction_rate = energy_data.get('autoproduction_rate', 16)  # %
            
            # Calculs techniques
            power_kwc = self._estimate_power_from_production(total_production)
            solar_coverage = autoconsumption_rate  # Utiliser le taux d'autoconsommation
            
            # Calculs économiques
            grid_price = project_config.get('global_config', {}).get('prix_electricite_reseau', 18.5)
            if not grid_price:
                grid_price = 18.5  # Prix moyen 2025
            
            savings_percentage = ((grid_price - solar_price) / grid_price) * 100 if grid_price > 0 else 20
            
            # Calculs environnementaux
            co2_factor = 0.167  # kg CO2/kWh (facteur réseau français)
            co2_avoided_annual = (total_autoconsumption * co2_factor) / 1000  # tonnes/an
            co2_avoided_20y = co2_avoided_annual * 20
            
            # Calculs de coûts
            cout_annuel_actuel = total_consumption * grid_price / 100  # Conversion ct → €
            cout_electricite_solaire = total_autoconsumption * solar_price / 100
            cout_electricite_reseau = (total_consumption - total_autoconsumption) * grid_price / 100
            cout_annuel_avec_solaire = cout_electricite_solaire + cout_electricite_reseau
            
            # Template enrichi
            template = self._get_enhanced_solar_template()
            template["cover"]["client_name"] = client_name
            template["cover"]["price_guaranteed"] = f"{solar_price:.1f}"
            template["cover"]["savings_20years"] = f"{int(total_savings_20y):,}".replace(",", " ")
            
            # Données consolidées complètes
            consolidated_data = {
                # Validité et métadonnées
                'is_valid': True,
                'data_source': 'financial_tables' if financial_data else 'optimization_engine',
                'extraction_timestamp': datetime.now().isoformat(),
                
                # Informations client et projet
                'client_name': client_name,
                'project_name': project_config.get('global_config', {}).get('project_name', 'Projet Autoconsommation Collective'),
                'localisation': project_config.get('global_config', {}).get('localisation', '[Localisation du projet]'),
                'best_scenario': best_scenario_name,  # Nom du meilleur scénario
                
                # Données financières principales
                'prix_optimal': solar_price,
                'solar_price': solar_price,  # Alias pour compatibilité UI
                'prix_reseau': grid_price,
                'economie_annuelle': annual_savings,
                'annual_savings': annual_savings,  # Alias pour compatibilité UI
                'economie_totale': total_savings_20y,
                'total_savings_20y': total_savings_20y,  # Alias pour compatibilité UI
                'economie_percentage': savings_percentage,
                'savings_percentage': savings_percentage,  # Alias pour compatibilité UI
                
                # Indicateurs financiers avancés
                'van_project': van_project,
                'tri_project': tri_project * 100 if tri_project < 1 else tri_project,  # Convertir en %
                'lcoe': lcoe,
                'payback_simple': payback,
                'dscr_moyen': dscr_moyen,
                
                # Données énergétiques complètes
                'puissance_kwc': power_kwc,
                'power_kwc': power_kwc,  # Alias pour compatibilité UI
                'production_annuelle': total_production,
                'total_production': total_production,  # Alias pour compatibilité UI
                'consommation_annuelle': total_consumption,
                'total_consumption': total_consumption,  # Alias pour compatibilité UI
                'autoconsommation_annuelle': total_autoconsumption,
                'taux_autoconsommation': autoconsumption_rate,
                'taux_autoproduction': autoproduction_rate,
                'taux_couverture': solar_coverage,
                'part_solaire': solar_coverage,
                'solar_coverage': solar_coverage,  # Alias pour compatibilité UI
                
                # Données économiques détaillées
                'cout_annuel_actuel': cout_annuel_actuel,
                'cout_annuel_avec_solaire': cout_annuel_avec_solaire,
                'reduction_percentage': (annual_savings / cout_annuel_actuel * 100) if cout_annuel_actuel > 0 else 15,
                
                # Données environnementales
                'co2_avoided_annual': co2_avoided_annual,
                'co2_avoided': co2_avoided_annual,  # Alias pour compatibilité UI
                'co2_avoided_total': co2_avoided_20y,
                'cars_equivalent': int(co2_avoided_annual / 2.3),  # Équivalent voitures (2.3t CO2/voiture/an)
                
                # Estimations d'installation
                'equivalent_foyers': int(power_kwc / 3),  # 3 kWc par foyer moyen
                'surface_panneaux': int(power_kwc * 5),  # 5 m² par kWc
                
                # Données techniques pour contrat
                'duree_contrat': 20,
                'indexation': project_config.get('global_config', {}).get('indexation', 'Fixe'),
                'date_mise_service': self._estimate_service_date(),
                
                # Contact commercial (à personnaliser)
                'contact_name': 'Votre Contact Commercial',
                'contact_title': 'Responsable Développement',
                'contact_phone': '01 23 45 67 89',
                'contact_email': 'contact@optimpv.fr',
                
                # Données brutes pour debug
                'template': template,
                'best_scenario_debug': best_scenario_name,
                'best_indicators': best_indicators,
                'energy_data': energy_data,
                'financial_data': financial_data,
                'project_config': project_config
            }
            
            logger.info(f"Données complètes récupérées pour {client_name} - Source: {consolidated_data['data_source']}")
            return consolidated_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données: {e}")
            return self._get_fallback_data(str(e))
    
    def _get_complete_financial_data(self) -> Dict[str, Any]:
        """
        Récupère les données financières complètes depuis les résultats d'analyses.
        Utilise les modules table_finance pour une extraction précise.
        
        Returns:
            Dict contenant les indicateurs financiers détaillés
        """
        try:
            # Essayer d'abord les résultats d'optimisation avec contraintes
            optimization_results = (st.session_state.get('constrained_optim_results', {}) or 
                                   st.session_state.get('optimization_results', {}))
            
            if not optimization_results:
                return {'is_valid': False, 'error': 'Aucun résultat d\'optimisation trouvé'}
            
            # Prendre le premier scénario disponible ou le meilleur
            best_scenario_name = None
            best_results = None
            
            for scenario_name, results in optimization_results.items():
                if isinstance(results, dict):
                    # Nouveau format (constrained_optim_results)
                    if 'indicateurs_au_prix_optimal' in results:
                        best_scenario_name = scenario_name
                        best_results = results['indicateurs_au_prix_optimal']
                        prix_optimal = results.get('prix_optimal_const', 0)
                        break
                    # Ancien format (optimization_results)
                    elif 'indicateurs_optimaux' in results:
                        best_scenario_name = scenario_name
                        best_results = results['indicateurs_optimaux']
                        prix_optimal = results.get('prix_optimal', 0)
                        break
            
            if not best_results:
                return {'is_valid': False, 'error': 'Aucun indicateur financier trouvé'}
            
            # Extraire les données financières avec les nouvelles clés
            financial_data = {
                'is_valid': True,
                'scenario_name': best_scenario_name,
                'prix_optimal': prix_optimal,
                
                # Indicateurs financiers principaux
                'van_project': best_results.get('npv_project', 0),
                'van_equity': best_results.get('npv', 0),
                'tri_project': best_results.get('irr_project', 0),
                'tri_equity': best_results.get('irr', 0),
                'lcoe': best_results.get('lcoe', 0),
                'payback_simple': best_results.get('payback_project', 0),
                'payback_equity': best_results.get('payback_period', 0),
                'roi_equity': best_results.get('roi', 0),
                'dscr_moyen': best_results.get('avg_dscr', 0),
                
                # Données énergétiques
                'taux_autoconsommation': best_results.get('autoconsumption_rate', 0),
                'taux_autoproduction': best_results.get('autoproduction_rate', 0),
                
                # Données mensuelles (DataFrame)
                'monthly_data': best_results.get('monthly_data'),
                
                # Données de configuration utilisées
                'config_globale': best_results.get('config_globale_utilisee', {}),
                'config_scenario': best_results.get('config_scenario_utilise', {}),
            }
            
            # Calculer les économies si les données mensuelles sont disponibles
            monthly_df = financial_data.get('monthly_data')
            if monthly_df is not None and isinstance(monthly_df, pd.DataFrame):
                financial_data.update(self._extract_monthly_aggregates(monthly_df))
            
            logger.info(f"Données financières complètes extraites pour scénario: {best_scenario_name}")
            return financial_data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des données financières: {e}")
            return {'is_valid': False, 'error': str(e)}
    
    def _extract_monthly_aggregates(self, monthly_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extrait les agrégats annuels depuis les données mensuelles.
        Utilise le mapping des colonnes financières.
        
        Args:
            monthly_df: DataFrame des données mensuelles
            
        Returns:
            Dict des agrégats calculés
        """
        try:
            aggregates = {}
            
            # Mapping des colonnes importantes (selon financial_table_map.json)
            column_mapping = {
                'Production_kWh': 'production_annuelle',
                'Consommation_kWh': 'consommation_annuelle', 
                'Autoconsommation_kWh': 'autoconsommation_annuelle',
                'Revenus_Total': 'revenus_annuels',
                'EBITDA': 'ebitda_annuel',
                'OCF_Projet': 'cash_flow_annuel',
                'FCFE': 'cash_flow_equity_annuel'
            }
            
            # Calculer les sommes annuelles
            for col_name, agg_key in column_mapping.items():
                if col_name in monthly_df.columns:
                    annual_sum = monthly_df[col_name].sum()
                    aggregates[agg_key] = annual_sum
                    
                    # Calculs spéciaux pour économies
                    if col_name == 'Revenus_Total':
                        # Estimation économie annuelle (à affiner selon logique métier)
                        prix_reseau_moyen = 18.5  # ct/kWh
                        autoconso_kwh = aggregates.get('autoconsommation_annuelle', 0)
                        cout_sans_solaire = autoconso_kwh * prix_reseau_moyen / 100
                        economie_annuelle = cout_sans_solaire - annual_sum
                        aggregates['economie_annuelle'] = max(0, economie_annuelle)
                        aggregates['economie_totale'] = aggregates['economie_annuelle'] * 20
            
            # Calculer les ratios si les données sont disponibles
            production = aggregates.get('production_annuelle', 0)
            consommation = aggregates.get('consommation_annuelle', 0)
            autoconsommation = aggregates.get('autoconsommation_annuelle', 0)
            
            if production > 0 and consommation > 0:
                aggregates['taux_autoconsommation_calc'] = (autoconsommation / consommation) * 100
                aggregates['taux_autoproduction_calc'] = (autoconsommation / production) * 100
                aggregates['taux_couverture_solaire'] = min(100, (production / consommation) * 100)
            
            return aggregates
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des agrégats mensuels: {e}")
            return {}
    
    def _estimate_power_from_production(self, production_kwh: float) -> float:
        """
        Estime la puissance installée depuis la production annuelle.
        
        Args:
            production_kwh: Production annuelle en kWh
            
        Returns:
            Puissance estimée en kWc
        """
        # Facteur de productivité moyen en France : 1100 kWh/kWc/an
        productivity_factor = 1100
        return production_kwh / productivity_factor
    
    def _estimate_service_date(self) -> str:
        """Estime une date de mise en service réaliste."""
        current_date = datetime.now()
        # Ajouter 6-9 mois pour développement et construction
        if current_date.month <= 6:
            return f"T4 {current_date.year}"
        else:
            return f"T2 {current_date.year + 1}"
    
    def _get_enhanced_solar_template(self) -> Dict[str, Any]:
        """
        Retourne un template enrichi pour les propositions commerciales.
        
        Returns:
            Template structuré pour les rapports
        """
        return {
            "cover": {
                "title": "Proposition d'Autoconsommation Collective",
                "subtitle": "Votre Projet d'Énergie Solaire Locale",
                "client_name": "[NOM DU CLIENT]",
                "price_guaranteed": "15.0",
                "savings_20years": "150 000",
                "service_date": "T2 2025"
            },
            "executive_summary": {
                "introduction": "Ce rapport présente une solution d'autoconsommation collective...",
                "key_benefits": [
                    "Prix garanti et stable",
                    "Économies immédiates",
                    "Énergie 100% verte et locale"
                ]
            },
            "financial_overview": {
                "annual_savings": 0,
                "total_savings": 0,
                "payback_period": 0,
                "roi": 0
            },
            "technical_specs": {
                "power_kwc": 0,
                "annual_production": 0,
                "coverage_rate": 0,
                "technology": "Panneaux photovoltaïques haute performance"
            },
            "environmental_impact": {
                "co2_avoided_annual": 0,
                "co2_avoided_total": 0,
                "equivalent_cars": 0
            },
            "faq": [
                {
                    "question": "Et s'il n'y a pas de soleil ?",
                    "answer": "Votre alimentation est garantie sans coupure. Le réseau électrique prend le relais automatiquement."
                },
                {
                    "question": "Que se passe-t-il si je consomme plus que ce que le solaire produit ?",
                    "answer": "Le complément est fourni par le réseau, comme aujourd'hui. Notre offre ne couvre que la part d'énergie solaire."
                },
                {
                    "question": "Qui s'occupe de la maintenance ?",
                    "answer": "Nous nous occupons de tout. L'exploitation et la maintenance sont entièrement à notre charge."
                }
            ]
        }
    
    def _get_fallback_data(self, error_message: str) -> Dict[str, Any]:
        """
        Retourne des données par défaut en cas d'erreur.
        
        Args:
            error_message: Message d'erreur à inclure
            
        Returns:
            Données de fallback
        """
        return {
            'is_valid': False,
            'error': error_message,
            'client_name': 'Client OptimPV',
            'prix_optimal': 15.0,
            'solar_price': 15.0,
            'economie_annuelle': 7500,
            'annual_savings': 7500,
            'economie_totale': 150000,
            'total_savings_20y': 150000,
            'savings_percentage': 20.0,
            'puissance_kwc': 100,
            'power_kwc': 100,
            'production_annuelle': 110000,
            'total_production': 110000,
            'consommation_annuelle': 50000,
            'total_consumption': 50000,
            'autoconsommation_annuelle': 17500,
            'solar_coverage': 35.0,
            'co2_avoided': 7.5,
            'best_scenario': 'Scénario par défaut',
            'template': self._get_enhanced_solar_template()
        }
    
    def _get_project_configuration(self) -> Dict[str, Any]:
        """Récupère la configuration complète du projet depuis st.session_state"""
        return {
            'global_config': st.session_state.get('config', {}),
            'sites_config': st.session_state.get('sites_config', {}),
            'scenarios': st.session_state.get('scenarios', {}),
            'processed_data': st.session_state.get('processed_data'),
            'sites_data': st.session_state.get('sites_data', {})
        }
    
    def _get_optimization_data(self) -> Tuple[Optional[str], Optional[Dict], Optional[float]]:
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
    
    def _get_energy_data_robust(self) -> Dict[str, float]:
        """
        Méthode robuste pour récupérer les données énergétiques depuis différentes sources
        
        Returns:
            dict: Dictionnaire avec total_production, total_consumption, total_autoconsumption
        """
        # Initialisation
        total_production = 0
        total_consumption = 0
        total_autoconsumption = 0
        
        try:
            # Essayer de récupérer depuis processed_data
            processed_data = st.session_state.get('processed_data')
            if processed_data is not None and not processed_data.empty:
                if 'Production_kWh' in processed_data.columns:
                    total_production = processed_data['Production_kWh'].sum()
                if 'Consommation_kWh' in processed_data.columns:
                    total_consumption = processed_data['Consommation_kWh'].sum()
                if 'Autoconsommation_kWh' in processed_data.columns:
                    total_autoconsumption = processed_data['Autoconsommation_kWh'].sum()
            
            # Si pas de données, essayer depuis sites_data
            if total_production == 0:
                sites_data = st.session_state.get('sites_data', {})
                for site_name, site_data in sites_data.items():
                    if isinstance(site_data, dict):
                        total_production += site_data.get('production_annuelle', 0)
                        total_consumption += site_data.get('consommation_annuelle', 0)
            
            # Valeurs par défaut si aucune donnée
            if total_production == 0:
                total_production = 850000  # 850 kWc * 1000 kWh/kWc
            if total_consumption == 0:
                total_consumption = 1000000  # 1 GWh par défaut
                
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération des données énergétiques: {e}")
            # Valeurs par défaut en cas d'erreur
            total_production = 850000
            total_consumption = 1000000
            total_autoconsumption = min(total_production, total_consumption)
        
        return {
            'total_production': total_production,
            'total_consumption': total_consumption,
            'total_autoconsumption': total_autoconsumption
        }
    
    def _get_solar_template(self) -> Dict[str, Any]:
        """Template de base pour la proposition solaire"""
        return {
            "cover": {
                "title": "VOTRE PROJET D'AUTOCONSOMMATION SOLAIRE",
                "client_name": "[NOM DU CLIENT]",
                "price_guaranteed": "12,5",
                "savings_20years": "125 000",
                "commissioning_date": "Septembre 2025",
                "report_date": datetime.now().strftime("%d %B %Y")
            },
            
            "executive_summary": """
            <p>Ce rapport vous présente une opportunité unique de <strong>réduire durablement votre facture d'électricité</strong>. 
            En rejoignant le projet d'autoconsommation collective, vous bénéficierez 
            d'une électricité produite localement à un <strong>tarif fixe et compétitif</strong>, 
            à l'abri des hausses du marché.</p>
            
            <p>Cela représente une <strong>économie significative</strong> sur la part solaire de votre consommation, 
            tout en réduisant votre empreinte carbone.</p>
            
            <p><em>C'est simple, sécurisé et sans investissement de votre part.</em></p>
            """,
            
            "faq": [
                {
                    "question": "Et s'il n'y a pas de soleil ?",
                    "answer": "Votre alimentation est garantie sans coupure. Le réseau électrique prend le relais automatiquement."
                },
                {
                    "question": "Que se passe-t-il si je consomme plus que ce que le solaire produit ?",
                    "answer": "Le complément est fourni par le réseau, comme aujourd'hui. Notre offre ne couvre que la part d'énergie solaire."
                },
                {
                    "question": "Qui s'occupe de la maintenance ?",
                    "answer": "Nous nous occupons de tout. L'exploitation et la maintenance sont entièrement à notre charge."
                }
            ]
        }
    
    def get_client_name(self) -> str:
        """Récupère le nom du client depuis la configuration"""
        config = st.session_state.get('config', {})
        return config.get('client_name', 'Client OptimPV')
    
    def is_data_valid(self) -> bool:
        """Vérifie si les données nécessaires sont disponibles"""
        has_data = st.session_state.get('data_imported', False)
        has_optimization = (st.session_state.get('constrained_optim_results') or 
                          st.session_state.get('optimization_results') or
                          st.session_state.get('floor_price_results'))
        return has_data and has_optimization