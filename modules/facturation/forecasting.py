"""
Advanced Forecasting Engine for PMO Billing System
Provides cash flow forecasting, seasonal analysis, and ML-based predictions
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
import logging
from dataclasses import dataclass
from enum import Enum
import sqlite3
import warnings
warnings.filterwarnings('ignore')

# Machine Learning and Statistical Analysis
ML_AVAILABLE = False
try:
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler, PolynomialFeatures
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import train_test_split, cross_val_score
    from scipy import stats
    from scipy.signal import seasonal_decompose
    from scipy.optimize import minimize
    ML_AVAILABLE = True
except (ImportError, SyntaxError) as e:
    # Fallback classes and functions
    class LinearRegression:
        def __init__(self):
            self.coef_ = [0.0]
        def fit(self, X, y):
            return self
        def predict(self, X):
            return [0.0] * len(X)
    
    class Ridge:
        def __init__(self, alpha=1.0):
            pass
        def fit(self, X, y):
            return self
        def predict(self, X):
            return [0.0] * len(X)
    
    class RandomForestRegressor:
        def __init__(self, n_estimators=50, random_state=42):
            pass
        def fit(self, X, y):
            return self
        def predict(self, X):
            return [0.0] * len(X)
    
    class StandardScaler:
        def fit_transform(self, X):
            return X
        def transform(self, X):
            return X
    
    def cross_val_score(model, X, y, cv=5):
        return [0.5] * cv
    
    def minimize(func, x0, bounds=None, method=None):
        class Result:
            def __init__(self):
                self.x = [x0] if isinstance(x0, (int, float)) else x0
        return Result()
    
    def seasonal_decompose(ts_data, model='multiplicative', period=12):
        class Decomposition:
            def __init__(self, data):
                self.seasonal = data * 0 + 1.0  # Flat seasonality
                self.trend = data
                self.resid = data * 0
        return Decomposition(ts_data)

from .database import BillingDatabase
from .analytics import AnalyticsEngine

logger = logging.getLogger(__name__)

class ForecastScenario(Enum):
    OPTIMISTIC = "optimistic"
    REALISTIC = "realistic"
    PESSIMISTIC = "pessimistic"

class SeasonalPattern(Enum):
    WINTER = "winter"
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"

@dataclass
class ForecastResult:
    """Forecast result with confidence intervals"""
    period: str
    predicted_value: float
    lower_bound: float
    upper_bound: float
    confidence_level: float
    scenario: ForecastScenario
    contributing_factors: List[str]
    seasonality_factor: float = 1.0
    trend_factor: float = 1.0

@dataclass
class CashFlowForecast:
    """Cash flow forecast with detailed breakdown"""
    period: str
    inflows: Dict[str, float]
    outflows: Dict[str, float]
    net_cash_flow: float
    cumulative_cash_flow: float
    risk_factors: List[str]
    opportunities: List[str]
    confidence_score: float

@dataclass
class SeasonalAnalysis:
    """Seasonal analysis results"""
    metric_name: str
    seasonal_factors: Dict[str, float]  # Month -> factor
    trend_component: List[float]
    residual_variance: float
    seasonality_strength: float
    peak_months: List[str]
    low_months: List[str]

@dataclass
class RiskScenario:
    """Risk scenario analysis"""
    scenario_name: str
    probability: float
    impact_description: str
    financial_impact: float
    mitigation_strategies: List[str]
    trigger_indicators: List[str]

class SolarSeasonalityModel:
    """Solar energy seasonality model for photovoltaic systems"""
    
    def __init__(self, latitude: float = 43.7):  # Default: Nice, France
        """Initialize with geographic coordinates"""
        self.latitude = latitude
        self.seasonal_factors = self._calculate_solar_seasonal_factors()
    
    def _calculate_solar_seasonal_factors(self) -> Dict[int, float]:
        """Calculate monthly solar production factors based on latitude"""
        # Solar declination and day length calculations
        factors = {}
        
        for month in range(1, 13):
            # Approximate day of year for middle of month
            day_of_year = (month - 1) * 30 + 15
            
            # Solar declination angle
            declination = 23.45 * np.sin(np.radians(360 * (284 + day_of_year) / 365))
            
            # Sunrise hour angle
            lat_rad = np.radians(self.latitude)
            decl_rad = np.radians(declination)
            
            try:
                hour_angle = np.arccos(-np.tan(lat_rad) * np.tan(decl_rad))
                # Day length in hours
                day_length = 2 * hour_angle * 12 / np.pi
                
                # Solar elevation factor (simplified)
                elevation_factor = np.sin(lat_rad) * np.sin(decl_rad) + np.cos(lat_rad) * np.cos(decl_rad)
                
                # Combined factor (normalized to summer peak)
                solar_factor = day_length * max(0, elevation_factor)
                factors[month] = solar_factor
                
            except:
                # Fallback for extreme latitudes
                factors[month] = 0.5 + 0.5 * np.cos(np.radians((month - 6) * 30))
        
        # Normalize to average of 1.0
        avg_factor = np.mean(list(factors.values()))
        return {month: factor / avg_factor for month, factor in factors.items()}
    
    def get_seasonal_factor(self, month: int) -> float:
        """Get seasonal factor for given month"""
        return self.seasonal_factors.get(month, 1.0)
    
    def get_annual_pattern(self) -> List[float]:
        """Get full annual pattern"""
        return [self.seasonal_factors[month] for month in range(1, 13)]

class ForecastingEngine:
    """Advanced forecasting engine with ML capabilities"""
    
    def __init__(self, db_path: str = "data/billing.db"):
        """Initialize forecasting engine"""
        self.db = BillingDatabase(db_path)
        self.analytics = AnalyticsEngine(db_path)
        self.solar_model = SolarSeasonalityModel()
        
        # Model storage
        self.models = {}
        self.scalers = {}
        self.seasonal_patterns = {}
        
        # Forecast parameters
        self.confidence_levels = [0.68, 0.95]  # 1σ and 2σ
        self.scenario_adjustments = {
            ForecastScenario.OPTIMISTIC: 1.15,
            ForecastScenario.REALISTIC: 1.0,
            ForecastScenario.PESSIMISTIC: 0.85
        }
    
    def forecast_cash_flow(self,
                          horizon_months: int = 12,
                          project_id: Optional[int] = None,
                          scenarios: List[ForecastScenario] = None) -> Dict[ForecastScenario, List[CashFlowForecast]]:
        """Generate comprehensive cash flow forecasts"""
        
        if scenarios is None:
            scenarios = [ForecastScenario.REALISTIC]
        
        try:
            # Get historical data
            historical_data = self._get_historical_cash_flow_data(project_id)
            
            # Perform seasonal analysis
            seasonal_analysis = self._analyze_seasonality(historical_data, 'net_cash_flow')
            
            forecasts = {}
            
            for scenario in scenarios:
                scenario_forecasts = []
                cumulative_flow = 0
                
                for month_ahead in range(1, horizon_months + 1):
                    forecast_date = date.today() + timedelta(days=30 * month_ahead)
                    
                    # Base forecast
                    base_forecast = self._generate_base_cash_flow_forecast(
                        historical_data, forecast_date, month_ahead
                    )
                    
                    # Apply seasonality
                    seasonal_factor = self._get_seasonal_factor(forecast_date.month, seasonal_analysis)
                    
                    # Apply scenario adjustment
                    scenario_multiplier = self.scenario_adjustments[scenario]
                    
                    # Calculate forecast components
                    inflows = self._forecast_inflows(
                        base_forecast, seasonal_factor, scenario_multiplier, forecast_date
                    )
                    
                    outflows = self._forecast_outflows(
                        base_forecast, seasonal_factor, scenario_multiplier, forecast_date
                    )
                    
                    net_flow = sum(inflows.values()) - sum(outflows.values())
                    cumulative_flow += net_flow
                    
                    # Risk assessment
                    risk_factors = self._assess_cash_flow_risks(forecast_date, scenario, net_flow)
                    opportunities = self._identify_opportunities(forecast_date, scenario, net_flow)
                    
                    # Confidence score
                    confidence = self._calculate_forecast_confidence(month_ahead, historical_data)
                    
                    forecast = CashFlowForecast(
                        period=forecast_date.strftime('%Y-%m'),
                        inflows=inflows,
                        outflows=outflows,
                        net_cash_flow=net_flow,
                        cumulative_cash_flow=cumulative_flow,
                        risk_factors=risk_factors,
                        opportunities=opportunities,
                        confidence_score=confidence
                    )
                    
                    scenario_forecasts.append(forecast)
                
                forecasts[scenario] = scenario_forecasts
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Error generating cash flow forecast: {e}")
            return {}
    
    def forecast_revenue(self,
                        horizon_months: int = 12,
                        project_id: Optional[int] = None,
                        include_confidence_intervals: bool = True) -> List[ForecastResult]:
        """Forecast revenue with machine learning models"""
        
        try:
            # Get historical revenue data
            historical_data = self._get_historical_revenue_data(project_id)
            
            if len(historical_data) < 6:  # Need minimum data
                return self._generate_simple_revenue_forecast(horizon_months)
            
            # Prepare features
            features, targets = self._prepare_revenue_features(historical_data)
            
            # Train ensemble model
            model, scaler = self._train_revenue_model(features, targets)
            
            forecasts = []
            
            for month_ahead in range(1, horizon_months + 1):
                forecast_date = date.today() + timedelta(days=30 * month_ahead)
                
                # Generate features for forecast period
                forecast_features = self._generate_forecast_features(
                    historical_data, forecast_date, month_ahead
                )
                
                # Scale features
                forecast_features_scaled = scaler.transform([forecast_features])
                
                # Generate prediction
                prediction = model.predict(forecast_features_scaled)[0]
                
                # Apply seasonality
                seasonal_factor = self.solar_model.get_seasonal_factor(forecast_date.month)
                adjusted_prediction = prediction * seasonal_factor
                
                # Calculate confidence intervals
                if include_confidence_intervals:
                    confidence_interval = self._calculate_revenue_confidence_interval(
                        model, scaler, forecast_features, prediction, historical_data
                    )
                else:
                    confidence_interval = (adjusted_prediction * 0.9, adjusted_prediction * 1.1)
                
                # Contributing factors
                factors = self._identify_revenue_factors(forecast_features, seasonal_factor)
                
                forecast = ForecastResult(
                    period=forecast_date.strftime('%Y-%m'),
                    predicted_value=adjusted_prediction,
                    lower_bound=confidence_interval[0],
                    upper_bound=confidence_interval[1],
                    confidence_level=0.95,
                    scenario=ForecastScenario.REALISTIC,
                    contributing_factors=factors,
                    seasonality_factor=seasonal_factor,
                    trend_factor=1.0  # Would be calculated from trend analysis
                )
                
                forecasts.append(forecast)
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Error forecasting revenue: {e}")
            return self._generate_simple_revenue_forecast(horizon_months)
    
    def analyze_seasonal_patterns(self,
                                metric: str = 'revenue',
                                project_id: Optional[int] = None) -> SeasonalAnalysis:
        """Analyze seasonal patterns in metrics"""
        
        try:
            # Get historical data
            if metric == 'revenue':
                data = self._get_historical_revenue_data(project_id)
            elif metric == 'energy_production':
                data = self._get_historical_energy_data(project_id)
            elif metric == 'customer_count':
                data = self._get_historical_customer_data(project_id)
            else:
                raise ValueError(f"Unknown metric: {metric}")
            
            if len(data) < 24:  # Need at least 2 years
                return self._generate_simple_seasonal_analysis(metric)
            
            # Perform seasonal decomposition
            ts_data = pd.Series(
                [d['value'] for d in data],
                index=pd.date_range(start=data[0]['date'], periods=len(data), freq='M')
            )
            
            if ML_AVAILABLE:
                decomposition = seasonal_decompose(ts_data, model='multiplicative', period=12)
                
                # Extract seasonal factors by month
                seasonal_factors = {}
                for i, month in enumerate(range(1, 13)):
                    month_data = decomposition.seasonal[decomposition.seasonal.index.month == month]
                    seasonal_factors[f"{month:02d}"] = month_data.mean()
                
                # Calculate seasonality strength
                seasonal_var = np.var(decomposition.seasonal)
                residual_var = np.var(decomposition.resid.dropna())
                seasonality_strength = seasonal_var / (seasonal_var + residual_var)
                
                # Identify peak and low months
                monthly_avg = {f"{m:02d}": v for m, v in seasonal_factors.items()}
                sorted_months = sorted(monthly_avg.items(), key=lambda x: x[1], reverse=True)
                peak_months = [month for month, _ in sorted_months[:3]]
                low_months = [month for month, _ in sorted_months[-3:]]
                
                return SeasonalAnalysis(
                    metric_name=metric,
                    seasonal_factors=seasonal_factors,
                    trend_component=decomposition.trend.dropna().tolist(),
                    residual_variance=residual_var,
                    seasonality_strength=seasonality_strength,
                    peak_months=peak_months,
                    low_months=low_months
                )
            else:
                return self._generate_simple_seasonal_analysis(metric)
                
        except Exception as e:
            logger.error(f"Error analyzing seasonal patterns: {e}")
            return self._generate_simple_seasonal_analysis(metric)
    
    def generate_risk_scenarios(self,
                              horizon_months: int = 12,
                              project_id: Optional[int] = None) -> List[RiskScenario]:
        """Generate risk scenario analysis"""
        
        scenarios = []
        
        try:
            # Get current KPIs for risk assessment
            current_kpis = self.analytics.calculate_comprehensive_kpis(
                date.today() - timedelta(days=30), date.today(), project_id
            )
            
            # Payment default risk
            if current_kpis.overdue_ratio > 10:
                scenarios.append(RiskScenario(
                    scenario_name="Increased Payment Defaults",
                    probability=0.3,
                    impact_description="Higher than normal payment defaults due to economic pressures",
                    financial_impact=-current_kpis.total_revenue * 0.15,
                    mitigation_strategies=[
                        "Implement stricter credit checks",
                        "Offer payment plans to struggling customers",
                        "Increase collection efforts",
                        "Consider bad debt insurance"
                    ],
                    trigger_indicators=[
                        "Overdue ratio > 15%",
                        "Customer complaints increase",
                        "Economic downturn indicators"
                    ]
                ))
            
            # Energy production shortfall
            scenarios.append(RiskScenario(
                scenario_name="Solar Production Shortfall",
                probability=0.2,
                impact_description="Lower than expected solar production due to weather or equipment issues",
                financial_impact=-current_kpis.total_revenue * 0.10,
                mitigation_strategies=[
                    "Diversify energy sources",
                    "Implement predictive maintenance",
                    "Purchase weather insurance",
                    "Adjust pricing models for weather risk"
                ],
                trigger_indicators=[
                    "Multiple cloudy days forecasted",
                    "Equipment performance alerts",
                    "Seasonal production below targets"
                ]
            ))
            
            # Customer churn risk
            if current_kpis.customer_retention_rate < 90:
                scenarios.append(RiskScenario(
                    scenario_name="Customer Churn Acceleration",
                    probability=0.25,
                    impact_description="Increased customer churn due to competitive pressure or service issues",
                    financial_impact=-current_kpis.monthly_recurring_revenue * 6,
                    mitigation_strategies=[
                        "Improve customer service",
                        "Implement loyalty programs",
                        "Regular customer satisfaction surveys",
                        "Competitive pricing analysis"
                    ],
                    trigger_indicators=[
                        "Customer satisfaction scores decline",
                        "Increased competitor activity",
                        "Service complaints rise"
                    ]
                ))
            
            # Regulatory changes
            scenarios.append(RiskScenario(
                scenario_name="Regulatory Changes",
                probability=0.15,
                impact_description="Changes in energy regulations affecting pricing or operations",
                financial_impact=-current_kpis.total_revenue * 0.08,
                mitigation_strategies=[
                    "Monitor regulatory developments",
                    "Engage with industry associations",
                    "Develop compliance procedures",
                    "Lobby for favorable regulations"
                ],
                trigger_indicators=[
                    "Regulatory consultations published",
                    "Government policy changes",
                    "Industry association alerts"
                ]
            ))
            
            # Economic downturn
            scenarios.append(RiskScenario(
                scenario_name="Economic Recession",
                probability=0.2,
                impact_description="General economic downturn affecting customer payment ability",
                financial_impact=-current_kpis.total_revenue * 0.20,
                mitigation_strategies=[
                    "Build cash reserves",
                    "Diversify customer base",
                    "Flexible payment terms",
                    "Cost reduction planning"
                ],
                trigger_indicators=[
                    "GDP growth turns negative",
                    "Unemployment rises",
                    "Customer payment delays increase"
                ]
            ))
            
            return scenarios
            
        except Exception as e:
            logger.error(f"Error generating risk scenarios: {e}")
            return scenarios
    
    def optimize_pricing(self,
                        target_revenue: float,
                        constraint_factors: Dict[str, Any] = None) -> Dict[str, Any]:
        """Optimize pricing to achieve target revenue"""
        
        try:
            # Get current pricing and demand data
            current_data = self._get_current_pricing_data()
            
            if not current_data:
                return {'error': 'Insufficient data for optimization'}
            
            # Define optimization constraints
            constraints = constraint_factors or {
                'min_price': current_data['current_price'] * 0.8,
                'max_price': current_data['current_price'] * 1.3,
                'demand_elasticity': -0.5,  # Price elasticity of demand
                'customer_retention_threshold': 0.9
            }
            
            # Optimization function
            def objective(price):
                # Demand function based on price elasticity
                demand_change = (price / current_data['current_price'] - 1) * constraints['demand_elasticity']
                new_demand = current_data['current_demand'] * (1 + demand_change)
                
                # Revenue calculation
                revenue = price * new_demand
                
                # Penalty for being too far from target
                penalty = abs(revenue - target_revenue) / target_revenue
                
                return penalty
            
            # Constraints for optimization
            bounds = [(constraints['min_price'], constraints['max_price'])]
            
            # Perform optimization
            result = minimize(objective, current_data['current_price'], bounds=bounds, method='L-BFGS-B')
            
            optimal_price = result.x[0]
            
            # Calculate impacts
            demand_change = (optimal_price / current_data['current_price'] - 1) * constraints['demand_elasticity']
            new_demand = current_data['current_demand'] * (1 + demand_change)
            projected_revenue = optimal_price * new_demand
            
            # Risk assessment
            risk_factors = []
            if optimal_price > current_data['current_price'] * 1.1:
                risk_factors.append("Significant price increase may reduce customer satisfaction")
            if abs(demand_change) > 0.1:
                risk_factors.append("Large demand change predicted - monitor closely")
            
            return {
                'optimal_price': round(optimal_price, 4),
                'current_price': current_data['current_price'],
                'price_change_percent': round((optimal_price / current_data['current_price'] - 1) * 100, 2),
                'projected_revenue': round(projected_revenue, 2),
                'target_revenue': target_revenue,
                'demand_impact_percent': round(demand_change * 100, 2),
                'risk_factors': risk_factors,
                'confidence_level': 0.7 if len(risk_factors) == 0 else 0.5
            }
            
        except Exception as e:
            logger.error(f"Error optimizing pricing: {e}")
            return {'error': str(e)}
    
    # Private helper methods
    
    def _get_historical_cash_flow_data(self, project_id: Optional[int]) -> List[Dict[str, Any]]:
        """Get historical cash flow data"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                query = """
                SELECT 
                    strftime('%Y-%m', bp.start_date) as period,
                    SUM(CASE WHEN bp.status = 'paid' THEN bp.total_amount ELSE 0 END) as inflows,
                    SUM(bp.total_amount) * 0.2 as outflows,  -- Estimated 20% operating costs
                    SUM(CASE WHEN bp.status = 'paid' THEN bp.total_amount ELSE 0 END) - SUM(bp.total_amount) * 0.2 as net_cash_flow
                FROM billing_periods bp
                WHERE bp.start_date >= date('now', '-24 months')
                """
                
                if project_id:
                    query += f" AND bp.project_id = {project_id}"
                
                query += " GROUP BY strftime('%Y-%m', bp.start_date) ORDER BY bp.start_date"
                
                cursor = conn.execute(query)
                return [{'date': row[0], 'inflows': row[1], 'outflows': row[2], 'net_cash_flow': row[3]} 
                       for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting historical cash flow data: {e}")
            return []
    
    def _get_historical_revenue_data(self, project_id: Optional[int]) -> List[Dict[str, Any]]:
        """Get historical revenue data"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                query = """
                SELECT 
                    strftime('%Y-%m', bp.start_date) as period,
                    SUM(bp.total_amount) as value
                FROM billing_periods bp
                WHERE bp.start_date >= date('now', '-24 months')
                """
                
                if project_id:
                    query += f" AND bp.project_id = {project_id}"
                
                query += " GROUP BY strftime('%Y-%m', bp.start_date) ORDER BY bp.start_date"
                
                cursor = conn.execute(query)
                return [{'date': row[0], 'value': row[1]} for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting historical revenue data: {e}")
            return []
    
    def _get_historical_energy_data(self, project_id: Optional[int]) -> List[Dict[str, Any]]:
        """Get historical energy production data"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                query = """
                SELECT 
                    printf('%04d-%02d', mp.year, mp.month) as period,
                    SUM(mp.total_production_kwh) as value
                FROM monthly_production mp
                WHERE date(printf('%04d-%02d-01', mp.year, mp.month)) >= date('now', '-24 months')
                """
                
                if project_id:
                    query += f" AND mp.project_id = {project_id}"
                
                query += " GROUP BY mp.year, mp.month ORDER BY mp.year, mp.month"
                
                cursor = conn.execute(query)
                return [{'date': row[0], 'value': row[1]} for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting historical energy data: {e}")
            return []
    
    def _get_historical_customer_data(self, project_id: Optional[int]) -> List[Dict[str, Any]]:
        """Get historical customer count data"""
        # Mock implementation - would need proper tracking
        data = []
        start_date = date.today() - timedelta(days=730)
        
        for i in range(24):
            period_date = start_date + timedelta(days=30 * i)
            # Simulate gradual customer growth
            customer_count = 20 + i + np.random.normal(0, 2)
            data.append({
                'date': period_date.strftime('%Y-%m'),
                'value': max(1, int(customer_count))
            })
        
        return data
    
    def _analyze_seasonality(self, data: List[Dict[str, Any]], metric: str) -> Dict[str, float]:
        """Analyze seasonality in data"""
        if len(data) < 12:
            return {f"{i:02d}": 1.0 for i in range(1, 13)}  # No seasonality
        
        # Group by month
        monthly_data = {}
        for item in data:
            try:
                month = datetime.strptime(item['date'], '%Y-%m').month
                if month not in monthly_data:
                    monthly_data[month] = []
                monthly_data[month].append(item[metric] if metric in item else item['value'])
            except:
                continue
        
        # Calculate monthly averages
        monthly_averages = {}
        for month, values in monthly_data.items():
            monthly_averages[month] = np.mean(values)
        
        # Normalize to overall average
        overall_avg = np.mean(list(monthly_averages.values()))
        if overall_avg > 0:
            seasonal_factors = {f"{month:02d}": avg / overall_avg for month, avg in monthly_averages.items()}
        else:
            seasonal_factors = {f"{month:02d}": 1.0 for month in monthly_averages.keys()}
        
        # Fill missing months with 1.0
        for month in range(1, 13):
            if f"{month:02d}" not in seasonal_factors:
                seasonal_factors[f"{month:02d}"] = 1.0
        
        return seasonal_factors
    
    def _generate_base_cash_flow_forecast(self, 
                                        historical_data: List[Dict[str, Any]], 
                                        forecast_date: date, 
                                        month_ahead: int) -> Dict[str, float]:
        """Generate base cash flow forecast"""
        if not historical_data:
            return {'inflows': 15000, 'outflows': 12000, 'net_flow': 3000}
        
        # Simple trend extrapolation
        recent_data = historical_data[-6:]  # Last 6 months
        
        avg_inflows = np.mean([d['inflows'] for d in recent_data])
        avg_outflows = np.mean([d['outflows'] for d in recent_data])
        
        # Apply slight growth trend
        growth_factor = 1 + (0.02 / 12) * month_ahead  # 2% annual growth
        
        return {
            'inflows': avg_inflows * growth_factor,
            'outflows': avg_outflows * growth_factor,
            'net_flow': (avg_inflows - avg_outflows) * growth_factor
        }
    
    def _get_seasonal_factor(self, month: int, seasonal_analysis: Dict[str, float]) -> float:
        """Get seasonal factor for given month"""
        month_key = f"{month:02d}"
        return seasonal_analysis.get(month_key, 1.0)
    
    def _forecast_inflows(self, 
                         base_forecast: Dict[str, float], 
                         seasonal_factor: float, 
                         scenario_multiplier: float, 
                         forecast_date: date) -> Dict[str, float]:
        """Forecast cash inflows with breakdown"""
        base_inflows = base_forecast['inflows'] * seasonal_factor * scenario_multiplier
        
        # Apply solar seasonality for energy revenue
        solar_factor = self.solar_model.get_seasonal_factor(forecast_date.month)
        
        return {
            'energy_sales': base_inflows * 0.8 * solar_factor,
            'service_fees': base_inflows * 0.15,
            'other_revenue': base_inflows * 0.05
        }
    
    def _forecast_outflows(self, 
                          base_forecast: Dict[str, float], 
                          seasonal_factor: float, 
                          scenario_multiplier: float, 
                          forecast_date: date) -> Dict[str, float]:
        """Forecast cash outflows with breakdown"""
        base_outflows = base_forecast['outflows'] * seasonal_factor * scenario_multiplier
        
        # Higher maintenance costs in winter
        maintenance_factor = 1.2 if forecast_date.month in [11, 12, 1, 2] else 1.0
        
        return {
            'operations': base_outflows * 0.4,
            'maintenance': base_outflows * 0.3 * maintenance_factor,
            'administration': base_outflows * 0.2,
            'debt_service': base_outflows * 0.1
        }
    
    def _assess_cash_flow_risks(self, 
                               forecast_date: date, 
                               scenario: ForecastScenario, 
                               net_flow: float) -> List[str]:
        """Assess cash flow risks for forecast period"""
        risks = []
        
        if net_flow < 1000:
            risks.append("Low net cash flow - monitor liquidity")
        
        if forecast_date.month in [11, 12, 1, 2]:  # Winter months
            risks.append("Seasonal reduction in solar production expected")
        
        if scenario == ForecastScenario.PESSIMISTIC:
            risks.append("Economic headwinds may impact customer payments")
        
        # Add more sophisticated risk detection based on patterns
        return risks
    
    def _identify_opportunities(self, 
                               forecast_date: date, 
                               scenario: ForecastScenario, 
                               net_flow: float) -> List[str]:
        """Identify opportunities for forecast period"""
        opportunities = []
        
        if forecast_date.month in [4, 5, 6, 7, 8]:  # Peak solar months
            opportunities.append("Peak solar production season - optimize pricing")
        
        if scenario == ForecastScenario.OPTIMISTIC:
            opportunities.append("Favorable market conditions for expansion")
        
        if net_flow > 5000:
            opportunities.append("Strong cash position - consider reinvestment")
        
        return opportunities
    
    def _calculate_forecast_confidence(self, 
                                     month_ahead: int, 
                                     historical_data: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for forecast"""
        # Base confidence decreases with time horizon
        base_confidence = max(0.3, 0.9 - (month_ahead - 1) * 0.05)
        
        # Adjust based on data quality
        data_quality_factor = min(1.0, len(historical_data) / 12)
        
        return base_confidence * data_quality_factor
    
    def _prepare_revenue_features(self, historical_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features for revenue forecasting model"""
        features = []
        targets = []
        
        for i, data_point in enumerate(historical_data):
            try:
                date_obj = datetime.strptime(data_point['date'], '%Y-%m')
                
                # Time-based features
                month = date_obj.month
                year = date_obj.year
                quarter = (month - 1) // 3 + 1
                
                # Seasonal features
                month_sin = np.sin(2 * np.pi * month / 12)
                month_cos = np.cos(2 * np.pi * month / 12)
                
                # Solar seasonality
                solar_factor = self.solar_model.get_seasonal_factor(month)
                
                # Trend feature
                trend = i
                
                # Lag features (if enough history)
                lag_1 = historical_data[i-1]['value'] if i > 0 else data_point['value']
                lag_3 = historical_data[i-3]['value'] if i > 2 else data_point['value']
                
                feature_vector = [
                    month, quarter, year % 100,  # Time features
                    month_sin, month_cos,  # Cyclical features
                    solar_factor,  # Solar seasonality
                    trend,  # Trend
                    lag_1, lag_3  # Lag features
                ]
                
                features.append(feature_vector)
                targets.append(data_point['value'])
                
            except Exception as e:
                logger.warning(f"Error processing data point {data_point}: {e}")
                continue
        
        return np.array(features), np.array(targets)
    
    def _train_revenue_model(self, features: np.ndarray, targets: np.ndarray) -> Tuple[Any, Any]:
        """Train revenue forecasting model"""
        if not ML_AVAILABLE:
            # Fallback to simple model
            class SimpleModel:
                def __init__(self, mean_value):
                    self.mean_value = mean_value
                
                def predict(self, X):
                    return np.full(len(X), self.mean_value)
            
            class SimpleScaler:
                def transform(self, X):
                    return X
            
            return SimpleModel(np.mean(targets)), SimpleScaler()
        
        # Scale features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Train ensemble model
        models = [
            LinearRegression(),
            Ridge(alpha=1.0),
            RandomForestRegressor(n_estimators=50, random_state=42),
        ]
        
        best_model = None
        best_score = -float('inf')
        
        for model in models:
            try:
                # Cross-validation
                scores = cross_val_score(model, features_scaled, targets, cv=min(5, len(targets)//2))
                avg_score = np.mean(scores)
                
                if avg_score > best_score:
                    best_score = avg_score
                    best_model = model
            except:
                continue
        
        # Train best model on full data
        if best_model:
            best_model.fit(features_scaled, targets)
        else:
            # Fallback
            best_model = LinearRegression()
            best_model.fit(features_scaled, targets)
        
        return best_model, scaler
    
    def _generate_forecast_features(self, 
                                   historical_data: List[Dict[str, Any]], 
                                   forecast_date: date, 
                                   month_ahead: int) -> List[float]:
        """Generate features for forecasting"""
        month = forecast_date.month
        year = forecast_date.year
        quarter = (month - 1) // 3 + 1
        
        # Seasonal features
        month_sin = np.sin(2 * np.pi * month / 12)
        month_cos = np.cos(2 * np.pi * month / 12)
        
        # Solar seasonality
        solar_factor = self.solar_model.get_seasonal_factor(month)
        
        # Trend feature
        trend = len(historical_data) + month_ahead - 1
        
        # Lag features
        lag_1 = historical_data[-1]['value'] if historical_data else 0
        lag_3 = historical_data[-3]['value'] if len(historical_data) >= 3 else lag_1
        
        return [
            month, quarter, year % 100,
            month_sin, month_cos,
            solar_factor,
            trend,
            lag_1, lag_3
        ]
    
    def _calculate_revenue_confidence_interval(self, 
                                              model: Any, 
                                              scaler: Any, 
                                              features: List[float], 
                                              prediction: float, 
                                              historical_data: List[Dict[str, Any]]) -> Tuple[float, float]:
        """Calculate confidence interval for revenue prediction"""
        # Simple confidence interval based on historical variance
        historical_values = [d['value'] for d in historical_data]
        std_dev = np.std(historical_values)
        
        # 95% confidence interval (2 standard deviations)
        margin = 1.96 * std_dev
        
        return (prediction - margin, prediction + margin)
    
    def _identify_revenue_factors(self, features: List[float], seasonal_factor: float) -> List[str]:
        """Identify contributing factors to revenue forecast"""
        factors = []
        
        # Seasonal effects
        if seasonal_factor > 1.1:
            factors.append("Positive seasonal effect")
        elif seasonal_factor < 0.9:
            factors.append("Negative seasonal effect")
        
        # Trend
        factors.append("Historical trend continuation")
        
        # Solar production
        month = int(features[0])
        if month in [5, 6, 7, 8]:
            factors.append("Peak solar production season")
        elif month in [11, 12, 1, 2]:
            factors.append("Low solar production season")
        
        return factors
    
    def _generate_simple_revenue_forecast(self, horizon_months: int) -> List[ForecastResult]:
        """Generate simple revenue forecast when ML is not available"""
        forecasts = []
        base_revenue = 15000  # Base monthly revenue
        
        for month_ahead in range(1, horizon_months + 1):
            forecast_date = date.today() + timedelta(days=30 * month_ahead)
            
            # Apply solar seasonality
            seasonal_factor = self.solar_model.get_seasonal_factor(forecast_date.month)
            
            # Simple growth trend
            growth_factor = 1 + (0.03 / 12) * month_ahead  # 3% annual growth
            
            predicted_value = base_revenue * seasonal_factor * growth_factor
            
            # Simple confidence interval
            margin = predicted_value * 0.15
            
            forecast = ForecastResult(
                period=forecast_date.strftime('%Y-%m'),
                predicted_value=predicted_value,
                lower_bound=predicted_value - margin,
                upper_bound=predicted_value + margin,
                confidence_level=0.8,
                scenario=ForecastScenario.REALISTIC,
                contributing_factors=["Solar seasonality", "Historical growth trend"],
                seasonality_factor=seasonal_factor,
                trend_factor=growth_factor
            )
            
            forecasts.append(forecast)
        
        return forecasts
    
    def _generate_simple_seasonal_analysis(self, metric: str) -> SeasonalAnalysis:
        """Generate simple seasonal analysis when insufficient data"""
        # Use solar model for energy-related metrics
        if 'energy' in metric or 'production' in metric:
            seasonal_factors = {f"{i:02d}": self.solar_model.get_seasonal_factor(i) for i in range(1, 13)}
            peak_months = ["06", "07", "08"]
            low_months = ["12", "01", "02"]
        else:
            # Flat seasonality for other metrics
            seasonal_factors = {f"{i:02d}": 1.0 for i in range(1, 13)}
            peak_months = []
            low_months = []
        
        return SeasonalAnalysis(
            metric_name=metric,
            seasonal_factors=seasonal_factors,
            trend_component=[],
            residual_variance=0.1,
            seasonality_strength=0.3 if peak_months else 0.0,
            peak_months=peak_months,
            low_months=low_months
        )
    
    def _get_current_pricing_data(self) -> Optional[Dict[str, float]]:
        """Get current pricing and demand data"""
        try:
            # This would typically come from database
            # For now, return mock data
            return {
                'current_price': 0.12,  # €/kWh
                'current_demand': 50000,  # kWh/month
                'price_elasticity': -0.5
            }
        except Exception as e:
            logger.error(f"Error getting pricing data: {e}")
            return None