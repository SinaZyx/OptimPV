"""Service métier pour la gestion de l'inflation et des projections de prix.

Ce module gère les calculs d'inflation, les projections de prix à long terme
et les analyses comparatives pour optimiser les stratégies tarifaires.
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, date
from dataclasses import dataclass
import math
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class InflationData:
    """Données d'inflation pour une période."""
    year: int
    month: Optional[int]
    rate: float  # Taux en %
    source: str
    category: str  # 'general', 'energie', 'electricite'


class InflationService:
    """Service pour la gestion de l'inflation et des projections économiques."""
    
    # Données d'inflation historiques (à mettre à jour régulièrement)
    # Source: INSEE, Eurostat
    INFLATION_HISTORIQUE = {
        'general': {
            2020: 0.5,
            2021: 1.6,
            2022: 5.2,
            2023: 4.9,
            2024: 2.5  # Estimation
        },
        'energie': {
            2020: -6.8,
            2021: 10.5,
            2022: 23.1,
            2023: 5.7,
            2024: 3.0  # Estimation
        },
        'electricite': {
            2020: 1.5,
            2021: 0.5,
            2022: 4.0,
            2023: 15.0,
            2024: 8.6  # Estimation
        }
    }
    
    # Projections standards
    PROJECTIONS_DEFAUT = {
        'conservateur': {'general': 2.0, 'energie': 3.0, 'electricite': 3.5},
        'modere': {'general': 2.5, 'energie': 4.0, 'electricite': 4.5},
        'pessimiste': {'general': 3.0, 'energie': 5.0, 'electricite': 6.0}
    }
    
    def __init__(self):
        """Initialise le service d'inflation."""
        self.historical_data = self._load_historical_data()
        
    def _load_historical_data(self) -> Dict[str, List[InflationData]]:
        """Charge les données historiques d'inflation."""
        data = {}
        
        for category, rates in self.INFLATION_HISTORIQUE.items():
            data[category] = []
            for year, rate in rates.items():
                data[category].append(
                    InflationData(
                        year=year,
                        month=None,
                        rate=rate,
                        source='INSEE/Eurostat',
                        category=category
                    )
                )
                
        return data
        
    def get_inflation_rate(
        self, 
        year: int, 
        category: str = 'general',
        month: Optional[int] = None
    ) -> Optional[float]:
        """Récupère le taux d'inflation pour une année donnée.
        
        Args:
            year: Année
            category: Catégorie d'inflation
            month: Mois (optionnel)
            
        Returns:
            Taux d'inflation en % ou None
        """
        if category not in self.historical_data:
            logger.warning(f"Catégorie d'inflation inconnue: {category}")
            return None
            
        for data in self.historical_data[category]:
            if data.year == year and data.month == month:
                return data.rate
                
        # Si pas de données mensuelles, retourner l'annuel
        if month is not None:
            return self.get_inflation_rate(year, category, None)
            
        return None
        
    def calculate_cumulative_inflation(
        self,
        start_year: int,
        end_year: int,
        category: str = 'general'
    ) -> float:
        """Calcule l'inflation cumulée entre deux années.
        
        Args:
            start_year: Année de début
            end_year: Année de fin
            category: Catégorie d'inflation
            
        Returns:
            Inflation cumulée en %
        """
        if start_year >= end_year:
            return 0.0
            
        cumulative = 1.0
        
        for year in range(start_year, end_year):
            rate = self.get_inflation_rate(year, category)
            if rate is not None:
                cumulative *= (1 + rate / 100)
            else:
                # Utiliser la moyenne historique si données manquantes
                avg_rate = self._get_average_historical_rate(category)
                cumulative *= (1 + avg_rate / 100)
                
        return (cumulative - 1) * 100
        
    def project_value(
        self,
        initial_value: float,
        years: int,
        inflation_scenario: str = 'modere',
        category: str = 'general',
        custom_rates: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """Projette une valeur dans le futur avec inflation.
        
        Args:
            initial_value: Valeur initiale
            years: Nombre d'années à projeter
            inflation_scenario: Scénario d'inflation
            category: Catégorie d'inflation
            custom_rates: Taux personnalisés par année
            
        Returns:
            Liste des projections annuelles
        """
        projections = []
        current_value = initial_value
        base_year = date.today().year
        
        for year_offset in range(years + 1):
            year = base_year + year_offset
            
            if year_offset == 0:
                # Année de base
                projections.append({
                    'year': year,
                    'value': current_value,
                    'inflation_rate': 0.0,
                    'cumulative_inflation': 0.0,
                    'nominal_increase': 0.0,
                    'real_value': current_value
                })
            else:
                # Déterminer le taux d'inflation
                if custom_rates and year_offset <= len(custom_rates):
                    rate = custom_rates[year_offset - 1]
                else:
                    # Utiliser les données historiques si disponibles
                    hist_rate = self.get_inflation_rate(year, category)
                    if hist_rate is not None:
                        rate = hist_rate
                    else:
                        # Sinon utiliser le scénario
                        rate = self.PROJECTIONS_DEFAUT[inflation_scenario][category]
                        
                # Calculer la nouvelle valeur
                current_value *= (1 + rate / 100)
                cumulative = ((current_value / initial_value) - 1) * 100
                
                projections.append({
                    'year': year,
                    'value': round(current_value, 4),
                    'inflation_rate': rate,
                    'cumulative_inflation': round(cumulative, 2),
                    'nominal_increase': round(current_value - initial_value, 4),
                    'real_value': round(initial_value, 4)  # Valeur en euros constants
                })
                
        return projections
        
    def compare_scenarios(
        self,
        initial_value: float,
        years: int,
        category: str = 'electricite'
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Compare différents scénarios d'inflation.
        
        Args:
            initial_value: Valeur initiale
            years: Nombre d'années
            category: Catégorie d'inflation
            
        Returns:
            Dictionnaire avec projections par scénario
        """
        scenarios = {}
        
        for scenario_name in self.PROJECTIONS_DEFAUT:
            scenarios[scenario_name] = self.project_value(
                initial_value=initial_value,
                years=years,
                inflation_scenario=scenario_name,
                category=category
            )
            
        return scenarios
        
    def calculate_price_evolution_impact(
        self,
        annual_consumption_kwh: float,
        current_price_kwh: float,
        years: int,
        fixed_price_kwh: Optional[float] = None,
        inflation_scenario: str = 'modere'
    ) -> Dict[str, Any]:
        """Calcule l'impact de l'évolution des prix sur la facture.
        
        Args:
            annual_consumption_kwh: Consommation annuelle
            current_price_kwh: Prix actuel du kWh
            years: Nombre d'années
            fixed_price_kwh: Prix fixe alternatif (si applicable)
            inflation_scenario: Scénario d'inflation
            
        Returns:
            Analyse de l'impact financier
        """
        # Projections avec inflation
        price_projections = self.project_value(
            initial_value=current_price_kwh,
            years=years,
            inflation_scenario=inflation_scenario,
            category='electricite'
        )
        
        # Calcul des coûts annuels
        costs_variable = []
        costs_fixed = []
        cumulative_variable = 0
        cumulative_fixed = 0
        
        for projection in price_projections:
            annual_cost_variable = annual_consumption_kwh * projection['value']
            costs_variable.append(annual_cost_variable)
            cumulative_variable += annual_cost_variable
            
            if fixed_price_kwh:
                annual_cost_fixed = annual_consumption_kwh * fixed_price_kwh
                costs_fixed.append(annual_cost_fixed)
                cumulative_fixed += annual_cost_fixed
                
        # Analyse comparative
        analysis = {
            'period_years': years,
            'scenario': inflation_scenario,
            'consumption_kwh_annual': annual_consumption_kwh,
            'price_projections': price_projections,
            'costs_variable': costs_variable,
            'cumulative_cost_variable': round(cumulative_variable, 2),
            'average_cost_variable': round(cumulative_variable / (years + 1), 2)
        }
        
        if fixed_price_kwh:
            savings = cumulative_fixed - cumulative_variable
            analysis.update({
                'fixed_price_kwh': fixed_price_kwh,
                'costs_fixed': costs_fixed,
                'cumulative_cost_fixed': round(cumulative_fixed, 2),
                'average_cost_fixed': round(cumulative_fixed / (years + 1), 2),
                'total_savings': round(savings, 2),
                'savings_percentage': round((savings / cumulative_variable) * 100, 2) if cumulative_variable > 0 else 0,
                'recommendation': 'Prix fixe avantageux' if savings > 0 else 'Prix variable avantageux'
            })
            
        return analysis
        
    def calculate_lcoe_evolution(
        self,
        initial_capex: float,
        annual_opex: float,
        annual_production_kwh: float,
        lifetime_years: int,
        discount_rate: float = 4.0,
        opex_inflation: float = 2.0,
        degradation_rate: float = 0.5
    ) -> Dict[str, Any]:
        """Calcule l'évolution du LCOE avec inflation.
        
        Args:
            initial_capex: Investissement initial
            annual_opex: Coûts opérationnels annuels
            annual_production_kwh: Production annuelle
            lifetime_years: Durée de vie
            discount_rate: Taux d'actualisation (%)
            opex_inflation: Inflation des OPEX (%)
            degradation_rate: Dégradation annuelle (%)
            
        Returns:
            Analyse du LCOE
        """
        # Calculs année par année
        yearly_data = []
        total_discounted_costs = initial_capex
        total_discounted_production = 0
        
        for year in range(1, lifetime_years + 1):
            # OPEX avec inflation
            opex_year = annual_opex * math.pow(1 + opex_inflation / 100, year - 1)
            
            # Production avec dégradation
            production_year = annual_production_kwh * math.pow(1 - degradation_rate / 100, year - 1)
            
            # Facteur d'actualisation
            discount_factor = 1 / math.pow(1 + discount_rate / 100, year)
            
            # Valeurs actualisées
            discounted_opex = opex_year * discount_factor
            discounted_production = production_year * discount_factor
            
            total_discounted_costs += discounted_opex
            total_discounted_production += discounted_production
            
            yearly_data.append({
                'year': year,
                'opex': round(opex_year, 2),
                'production_kwh': round(production_year, 0),
                'discounted_opex': round(discounted_opex, 2),
                'discounted_production': round(discounted_production, 0)
            })
            
        # LCOE final
        lcoe = total_discounted_costs / total_discounted_production if total_discounted_production > 0 else 0
        
        return {
            'lcoe_eur_kwh': round(lcoe, 4),
            'total_capex': initial_capex,
            'total_opex_nominal': round(sum(d['opex'] for d in yearly_data), 2),
            'total_opex_discounted': round(sum(d['discounted_opex'] for d in yearly_data), 2),
            'total_production_nominal': round(sum(d['production_kwh'] for d in yearly_data), 0),
            'total_production_discounted': round(total_discounted_production, 0),
            'yearly_details': yearly_data,
            'assumptions': {
                'lifetime_years': lifetime_years,
                'discount_rate': discount_rate,
                'opex_inflation': opex_inflation,
                'degradation_rate': degradation_rate
            }
        }
        
    def estimate_future_market_prices(
        self,
        base_year: int = None,
        horizon_years: int = 10,
        include_carbon_price: bool = True
    ) -> List[Dict[str, Any]]:
        """Estime les prix de marché futurs de l'électricité.
        
        Args:
            base_year: Année de base
            horizon_years: Horizon de projection
            include_carbon_price: Inclure l'impact du prix carbone
            
        Returns:
            Projections des prix de marché
        """
        if base_year is None:
            base_year = date.today().year
            
        # Prix de base (spot moyen 2024)
        base_price = 0.15  # 150 €/MWh
        
        projections = []
        
        for year_offset in range(horizon_years + 1):
            year = base_year + year_offset
            
            # Facteurs d'évolution
            factors = {
                'inflation': 1.0,
                'renewable_penetration': 1.0,
                'carbon_price': 1.0,
                'demand_growth': 1.0
            }
            
            if year_offset > 0:
                # Inflation énergétique
                factors['inflation'] = math.pow(1.035, year_offset)  # 3.5% par an
                
                # Impact de la pénétration des renouvelables (baisse)
                factors['renewable_penetration'] = math.pow(0.98, year_offset)  # -2% par an
                
                # Impact du prix carbone (hausse)
                if include_carbon_price:
                    carbon_increase = min(year_offset * 5, 50)  # +5€/tCO2 par an, max 50€
                    factors['carbon_price'] = 1 + (carbon_increase * 0.4 / 1000)  # 0.4 tCO2/MWh
                    
                # Croissance de la demande
                factors['demand_growth'] = math.pow(1.01, year_offset)  # +1% par an
                
            # Prix projeté
            projected_price = base_price
            for factor_name, factor_value in factors.items():
                projected_price *= factor_value
                
            projections.append({
                'year': year,
                'price_eur_kwh': round(projected_price, 4),
                'price_eur_mwh': round(projected_price * 1000, 2),
                'factors': factors,
                'variation_vs_base': round((projected_price / base_price - 1) * 100, 2)
            })
            
        return projections
        
    def _get_average_historical_rate(self, category: str) -> float:
        """Calcule le taux d'inflation moyen historique.
        
        Args:
            category: Catégorie d'inflation
            
        Returns:
            Taux moyen
        """
        if category not in self.historical_data:
            return 2.0  # Défaut BCE
            
        rates = [data.rate for data in self.historical_data[category]]
        return sum(rates) / len(rates) if rates else 2.0
        
    def analyze_price_volatility(
        self,
        historical_prices: List[float],
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """Analyse la volatilité des prix historiques.
        
        Args:
            historical_prices: Liste des prix historiques
            confidence_level: Niveau de confiance pour VaR
            
        Returns:
            Analyse de volatilité
        """
        if len(historical_prices) < 2:
            return {'error': 'Données insuffisantes'}
            
        prices = np.array(historical_prices)
        returns = np.diff(prices) / prices[:-1]
        
        # Statistiques de base
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Value at Risk (VaR)
        var = np.percentile(returns, (1 - confidence_level) * 100)
        
        # Volatilité annualisée (supposant données mensuelles)
        annual_volatility = std_return * np.sqrt(12)
        
        return {
            'mean_return': round(mean_return * 100, 2),
            'volatility': round(std_return * 100, 2),
            'annual_volatility': round(annual_volatility * 100, 2),
            'value_at_risk': round(var * 100, 2),
            'confidence_level': confidence_level,
            'sharpe_ratio': round(mean_return / std_return, 2) if std_return > 0 else 0,
            'min_return': round(np.min(returns) * 100, 2),
            'max_return': round(np.max(returns) * 100, 2)
        }