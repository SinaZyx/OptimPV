"""
Advanced Analytics Engine for PMO Billing System
Provides comprehensive KPI calculations, predictive analytics, and business intelligence
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass
# Machine Learning and Statistical Analysis
ML_AVAILABLE = False
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    ML_AVAILABLE = True
except (ImportError, SyntaxError) as e:
    # Fallback classes for when sklearn is not available or has issues
    class LinearRegression:
        def __init__(self):
            self.coef_ = [0.0]
        def fit(self, X, y):
            return self
        def predict(self, X):
            return [0.0] * len(X)
    
    class StandardScaler:
        def fit_transform(self, X):
            return X
        def transform(self, X):
            return X
    
    class KMeans:
        def __init__(self, n_clusters=3, random_state=42):
            self.n_clusters = n_clusters
        def fit_predict(self, X):
            # Simple fallback clustering
            return [i % self.n_clusters for i in range(len(X))]
import sqlite3
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

@dataclass
class KPIMetrics:
    """Structured KPI metrics container"""
    # Financial KPIs
    total_revenue: float = 0.0
    monthly_recurring_revenue: float = 0.0
    average_revenue_per_customer: float = 0.0
    revenue_growth_rate: float = 0.0
    
    # Operational KPIs
    collection_rate: float = 0.0
    days_sales_outstanding: float = 0.0
    payment_cycle_efficiency: float = 0.0
    
    # Customer KPIs
    customer_count: int = 0
    active_customers: int = 0
    customer_retention_rate: float = 0.0
    customer_lifetime_value: float = 0.0
    
    # Energy KPIs
    total_energy_sold_kwh: float = 0.0
    average_price_per_kwh: float = 0.0
    energy_efficiency_ratio: float = 0.0
    
    # Cash Flow KPIs
    operating_cash_flow: float = 0.0
    free_cash_flow: float = 0.0
    cash_conversion_cycle: float = 0.0
    
    # Risk KPIs
    overdue_ratio: float = 0.0
    bad_debt_ratio: float = 0.0
    concentration_risk: float = 0.0

@dataclass
class CustomerSegment:
    """Customer segmentation data"""
    segment_name: str
    customer_count: int
    avg_monthly_revenue: float
    payment_behavior_score: float
    risk_level: str
    characteristics: List[str]

@dataclass
class PredictiveInsight:
    """Predictive analytics insight"""
    metric_name: str
    current_value: float
    predicted_value: float
    confidence_interval: Tuple[float, float]
    trend_direction: str
    risk_factors: List[str]
    recommendations: List[str]

class AnalyticsEngine:
    """Advanced analytics engine for billing system"""
    
    def __init__(self, db_path: str = "data/billing.db"):
        """Initialize analytics engine"""
        self.db_path = db_path
        self.scaler = StandardScaler()
        self.kmeans_model = None
        self._cache = {}
        self._cache_timestamp = {}
        self.cache_duration = timedelta(minutes=30)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid"""
        if key not in self._cache_timestamp:
            return False
        return datetime.now() - self._cache_timestamp[key] < self.cache_duration
    
    def _set_cache(self, key: str, value: Any) -> None:
        """Set cache entry"""
        self._cache[key] = value
        self._cache_timestamp[key] = datetime.now()
    
    def _get_cache(self, key: str) -> Any:
        """Get cache entry"""
        return self._cache.get(key)
    
    def calculate_comprehensive_kpis(self, 
                                   start_date: Optional[date] = None,
                                   end_date: Optional[date] = None,
                                   project_id: Optional[int] = None) -> KPIMetrics:
        """Calculate comprehensive KPI metrics"""
        cache_key = f"kpis_{start_date}_{end_date}_{project_id}"
        
        if self._is_cache_valid(cache_key):
            return self._get_cache(cache_key)
        
        # Default date range if not provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=365)
        
        try:
            with self._get_connection() as conn:
                kpis = KPIMetrics()
                
                # Financial KPIs
                kpis.total_revenue = self._calculate_total_revenue(conn, start_date, end_date, project_id)
                kpis.monthly_recurring_revenue = self._calculate_mrr(conn, end_date, project_id)
                kpis.average_revenue_per_customer = self._calculate_arpc(conn, start_date, end_date, project_id)
                kpis.revenue_growth_rate = self._calculate_revenue_growth(conn, start_date, end_date, project_id)
                
                # Operational KPIs
                kpis.collection_rate = self._calculate_collection_rate(conn, start_date, end_date, project_id)
                kpis.days_sales_outstanding = self._calculate_dso(conn, end_date, project_id)
                kpis.payment_cycle_efficiency = self._calculate_payment_efficiency(conn, start_date, end_date, project_id)
                
                # Customer KPIs
                kpis.customer_count = self._get_total_customers(conn, project_id)
                kpis.active_customers = self._get_active_customers(conn, end_date, project_id)
                kpis.customer_retention_rate = self._calculate_retention_rate(conn, start_date, end_date, project_id)
                kpis.customer_lifetime_value = self._calculate_clv(conn, start_date, end_date, project_id)
                
                # Energy KPIs
                kpis.total_energy_sold_kwh = self._calculate_total_energy_sold(conn, start_date, end_date, project_id)
                kpis.average_price_per_kwh = self._calculate_avg_energy_price(conn, start_date, end_date, project_id)
                kpis.energy_efficiency_ratio = self._calculate_energy_efficiency(conn, start_date, end_date, project_id)
                
                # Cash Flow KPIs
                kpis.operating_cash_flow = self._calculate_operating_cash_flow(conn, start_date, end_date, project_id)
                kpis.free_cash_flow = self._calculate_free_cash_flow(conn, start_date, end_date, project_id)
                kpis.cash_conversion_cycle = self._calculate_cash_conversion_cycle(conn, start_date, end_date, project_id)
                
                # Risk KPIs
                kpis.overdue_ratio = self._calculate_overdue_ratio(conn, end_date, project_id)
                kpis.bad_debt_ratio = self._calculate_bad_debt_ratio(conn, start_date, end_date, project_id)
                kpis.concentration_risk = self._calculate_concentration_risk(conn, start_date, end_date, project_id)
                
                self._set_cache(cache_key, kpis)
                return kpis
                
        except Exception as e:
            logger.error(f"Error calculating KPIs: {e}")
            return KPIMetrics()
    
    def predict_payment_defaults(self, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Predict potential payment defaults using machine learning"""
        try:
            with self._get_connection() as conn:
                # Get historical payment data
                query = """
                SELECT 
                    p.id, p.name, p.allocation_percentage,
                    AVG(mc.consumption_kwh) as avg_consumption,
                    COUNT(bp.id) as invoice_count,
                    AVG(julianday(bp.payment_due_date) - julianday(bp.start_date)) as avg_payment_delay,
                    SUM(CASE WHEN bp.payment_due_date < date('now') AND bp.status != 'paid' THEN 1 ELSE 0 END) as overdue_count
                FROM participants p
                LEFT JOIN monthly_consumption mc ON p.id = mc.participant_id
                LEFT JOIN billing_periods bp ON p.project_id = bp.project_id
                WHERE p.type = 'consumer'
                """
                
                if project_id:
                    query += f" AND p.project_id = {project_id}"
                
                query += " GROUP BY p.id"
                
                df = pd.read_sql_query(query, conn)
                
                if df.empty:
                    return []
                
                # Feature engineering
                df['overdue_rate'] = df['overdue_count'] / df['invoice_count'].replace(0, 1)
                df['consumption_stability'] = df['avg_consumption'] / df['allocation_percentage']
                
                # Simple risk scoring
                risk_scores = []
                for _, row in df.iterrows():
                    score = 0
                    
                    # Payment history factor
                    if row['overdue_rate'] > 0.3:
                        score += 40
                    elif row['overdue_rate'] > 0.1:
                        score += 20
                    
                    # Consumption pattern factor
                    if row['consumption_stability'] < 0.5:
                        score += 30
                    elif row['consumption_stability'] < 0.8:
                        score += 15
                    
                    # Payment delay factor
                    if row['avg_payment_delay'] > 30:
                        score += 30
                    elif row['avg_payment_delay'] > 15:
                        score += 15
                    
                    risk_level = "High" if score >= 70 else "Medium" if score >= 40 else "Low"
                    
                    risk_scores.append({
                        'participant_id': int(row['id']),
                        'participant_name': row['name'],
                        'risk_score': score,
                        'risk_level': risk_level,
                        'overdue_rate': round(row['overdue_rate'] * 100, 1),
                        'avg_payment_delay': round(row['avg_payment_delay'], 1),
                        'prediction_confidence': min(95, 60 + (row['invoice_count'] * 2))
                    })
                
                return sorted(risk_scores, key=lambda x: x['risk_score'], reverse=True)
                
        except Exception as e:
            logger.error(f"Error predicting payment defaults: {e}")
            return []
    
    def segment_customers(self, project_id: Optional[int] = None) -> List[CustomerSegment]:
        """Segment customers by payment behavior and consumption patterns"""
        try:
            with self._get_connection() as conn:
                # Get customer data for segmentation
                query = """
                SELECT 
                    p.id, p.name, p.allocation_percentage,
                    AVG(mc.consumption_kwh) as avg_consumption,
                    COUNT(bp.id) as invoice_count,
                    SUM(bp.total_amount) as total_revenue,
                    AVG(julianday(bp.payment_due_date) - julianday(bp.start_date)) as avg_payment_delay
                FROM participants p
                LEFT JOIN monthly_consumption mc ON p.id = mc.participant_id
                LEFT JOIN billing_periods bp ON p.project_id = bp.project_id
                WHERE p.type = 'consumer'
                """
                
                if project_id:
                    query += f" AND p.project_id = {project_id}"
                
                query += " GROUP BY p.id HAVING invoice_count > 0"
                
                df = pd.read_sql_query(query, conn)
                
                if df.empty or len(df) < 3:
                    return []
                
                # Prepare features for clustering
                features = ['allocation_percentage', 'avg_consumption', 'total_revenue', 'avg_payment_delay']
                X = df[features].fillna(0)
                
                # Normalize features
                X_scaled = self.scaler.fit_transform(X)
                
                # Perform clustering
                n_clusters = min(4, len(df))
                self.kmeans_model = KMeans(n_clusters=n_clusters, random_state=42)
                clusters = self.kmeans_model.fit_predict(X_scaled)
                
                df['cluster'] = clusters
                
                # Analyze segments
                segments = []
                for cluster_id in range(n_clusters):
                    cluster_data = df[df['cluster'] == cluster_id]
                    
                    # Calculate segment characteristics
                    avg_revenue = cluster_data['total_revenue'].mean()
                    avg_delay = cluster_data['avg_payment_delay'].mean()
                    avg_consumption = cluster_data['avg_consumption'].mean()
                    
                    # Determine segment profile
                    if avg_revenue > df['total_revenue'].mean():
                        if avg_delay < df['avg_payment_delay'].mean():
                            segment_name = "Premium Customers"
                            risk_level = "Low"
                            characteristics = ["High revenue", "Prompt payment", "Reliable"]
                        else:
                            segment_name = "High-Value Late Payers"
                            risk_level = "Medium"
                            characteristics = ["High revenue", "Payment delays", "Needs attention"]
                    else:
                        if avg_delay < df['avg_payment_delay'].mean():
                            segment_name = "Reliable Small Customers"
                            risk_level = "Low"
                            characteristics = ["Moderate revenue", "Prompt payment", "Stable"]
                        else:
                            segment_name = "At-Risk Customers"
                            risk_level = "High"
                            characteristics = ["Low revenue", "Payment issues", "High risk"]
                    
                    # Payment behavior score
                    payment_score = max(0, 100 - (avg_delay * 2))
                    
                    segments.append(CustomerSegment(
                        segment_name=segment_name,
                        customer_count=len(cluster_data),
                        avg_monthly_revenue=avg_revenue / 12,  # Approximate monthly
                        payment_behavior_score=round(payment_score, 1),
                        risk_level=risk_level,
                        characteristics=characteristics
                    ))
                
                return segments
                
        except Exception as e:
            logger.error(f"Error segmenting customers: {e}")
            return []
    
    def generate_trend_analysis(self, 
                              metric_name: str,
                              start_date: Optional[date] = None,
                              end_date: Optional[date] = None,
                              project_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate trend analysis for specific metrics"""
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=365)
        
        try:
            with self._get_connection() as conn:
                trend_data = self._get_metric_time_series(conn, metric_name, start_date, end_date, project_id)
                
                if not trend_data:
                    return {}
                
                # Convert to time series
                df = pd.DataFrame(trend_data)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                
                # Calculate trend statistics
                values = df['value'].values
                if len(values) < 2:
                    return {}
                
                # Linear regression for trend
                X = np.arange(len(values)).reshape(-1, 1)
                model = LinearRegression().fit(X, values)
                trend_slope = model.coef_[0]
                
                # Calculate statistics
                current_value = values[-1]
                previous_value = values[-2] if len(values) > 1 else current_value
                period_change = ((current_value - previous_value) / previous_value * 100) if previous_value != 0 else 0
                
                # Trend direction
                if trend_slope > 0.01:
                    trend_direction = "Increasing"
                elif trend_slope < -0.01:
                    trend_direction = "Decreasing"
                else:
                    trend_direction = "Stable"
                
                # Volatility
                volatility = np.std(values) / np.mean(values) * 100 if np.mean(values) != 0 else 0
                
                return {
                    'metric_name': metric_name,
                    'current_value': current_value,
                    'previous_value': previous_value,
                    'period_change_percent': round(period_change, 2),
                    'trend_direction': trend_direction,
                    'trend_slope': round(trend_slope, 4),
                    'volatility_percent': round(volatility, 2),
                    'data_points': len(values),
                    'time_series': df.to_dict('records')
                }
                
        except Exception as e:
            logger.error(f"Error generating trend analysis: {e}")
            return {}
    
    def generate_predictive_insights(self, 
                                   horizon_months: int = 6,
                                   project_id: Optional[int] = None) -> List[PredictiveInsight]:
        """Generate predictive insights for key metrics"""
        insights = []
        
        # Key metrics to predict
        metrics = ['revenue', 'collection_rate', 'customer_count', 'energy_sold']
        
        for metric in metrics:
            try:
                # Get historical data
                end_date = date.today()
                start_date = end_date - timedelta(days=730)  # 2 years of data
                
                trend_data = self.generate_trend_analysis(metric, start_date, end_date, project_id)
                
                if not trend_data or len(trend_data.get('time_series', [])) < 12:
                    continue
                
                # Simple linear prediction
                current_value = trend_data['current_value']
                trend_slope = trend_data['trend_slope']
                volatility = trend_data['volatility_percent']
                
                # Predict future value
                predicted_value = current_value + (trend_slope * horizon_months)
                
                # Confidence interval based on volatility
                confidence_range = (volatility / 100) * predicted_value * 0.5
                confidence_interval = (
                    max(0, predicted_value - confidence_range),
                    predicted_value + confidence_range
                )
                
                # Risk factors
                risk_factors = []
                if volatility > 20:
                    risk_factors.append("High volatility in historical data")
                if trend_slope < 0:
                    risk_factors.append("Declining trend observed")
                if trend_data['data_points'] < 24:
                    risk_factors.append("Limited historical data")
                
                # Recommendations
                recommendations = []
                if metric == 'revenue' and trend_slope < 0:
                    recommendations.extend([
                        "Review pricing strategy",
                        "Analyze customer churn",
                        "Consider service improvements"
                    ])
                elif metric == 'collection_rate' and predicted_value < current_value:
                    recommendations.extend([
                        "Improve payment reminder process",
                        "Review payment terms",
                        "Consider automated collections"
                    ])
                elif metric == 'customer_count' and trend_slope < 0:
                    recommendations.extend([
                        "Analyze customer satisfaction",
                        "Review retention strategies",
                        "Consider customer incentives"
                    ])
                
                insights.append(PredictiveInsight(
                    metric_name=metric.replace('_', ' ').title(),
                    current_value=round(current_value, 2),
                    predicted_value=round(predicted_value, 2),
                    confidence_interval=(round(confidence_interval[0], 2), round(confidence_interval[1], 2)),
                    trend_direction=trend_data['trend_direction'],
                    risk_factors=risk_factors,
                    recommendations=recommendations
                ))
                
            except Exception as e:
                logger.error(f"Error generating prediction for {metric}: {e}")
                continue
        
        return insights
    
    # Private helper methods for KPI calculations
    
    def _calculate_total_revenue(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        """Calculate total revenue for period"""
        query = """
        SELECT COALESCE(SUM(total_amount), 0) as total_revenue
        FROM billing_periods bp
        WHERE bp.start_date >= ? AND bp.end_date <= ?
        """
        params = [start_date, end_date]
        
        if project_id:
            query += " AND bp.project_id = ?"
            params.append(project_id)
        
        result = conn.execute(query, params).fetchone()
        return result[0] if result else 0.0
    
    def _calculate_mrr(self, conn: sqlite3.Connection, end_date: date, project_id: Optional[int]) -> float:
        """Calculate Monthly Recurring Revenue"""
        # Get average monthly revenue from last 3 months
        start_date = end_date - timedelta(days=90)
        total_revenue = self._calculate_total_revenue(conn, start_date, end_date, project_id)
        return total_revenue / 3  # Average over 3 months
    
    def _calculate_arpc(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        """Calculate Average Revenue Per Customer"""
        total_revenue = self._calculate_total_revenue(conn, start_date, end_date, project_id)
        customer_count = self._get_total_customers(conn, project_id)
        return total_revenue / customer_count if customer_count > 0 else 0.0
    
    def _calculate_revenue_growth(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        """Calculate revenue growth rate"""
        # Compare current period with previous period
        period_days = (end_date - start_date).days
        prev_start = start_date - timedelta(days=period_days)
        prev_end = start_date
        
        current_revenue = self._calculate_total_revenue(conn, start_date, end_date, project_id)
        previous_revenue = self._calculate_total_revenue(conn, prev_start, prev_end, project_id)
        
        if previous_revenue > 0:
            return ((current_revenue - previous_revenue) / previous_revenue) * 100
        return 0.0
    
    def _calculate_collection_rate(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        """Calculate collection rate"""
        query = """
        SELECT 
            COALESCE(SUM(total_amount), 0) as total_billed,
            COALESCE(SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END), 0) as total_collected
        FROM billing_periods bp
        WHERE bp.start_date >= ? AND bp.end_date <= ?
        """
        params = [start_date, end_date]
        
        if project_id:
            query += " AND bp.project_id = ?"
            params.append(project_id)
        
        result = conn.execute(query, params).fetchone()
        total_billed, total_collected = result if result else (0, 0)
        
        return (total_collected / total_billed * 100) if total_billed > 0 else 0.0
    
    def _calculate_dso(self, conn: sqlite3.Connection, end_date: date, project_id: Optional[int]) -> float:
        """Calculate Days Sales Outstanding"""
        query = """
        SELECT AVG(julianday(COALESCE(paid_date, date('now'))) - julianday(start_date)) as avg_days
        FROM billing_periods bp
        WHERE bp.end_date <= ?
        """
        params = [end_date]
        
        if project_id:
            query += " AND bp.project_id = ?"
            params.append(project_id)
        
        result = conn.execute(query, params).fetchone()
        return result[0] if result and result[0] else 30.0
    
    def _calculate_payment_efficiency(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        """Calculate payment cycle efficiency"""
        # Ratio of on-time payments
        query = """
        SELECT 
            COUNT(*) as total_invoices,
            SUM(CASE WHEN paid_date <= payment_due_date THEN 1 ELSE 0 END) as on_time_payments
        FROM billing_periods bp
        WHERE bp.start_date >= ? AND bp.end_date <= ? AND bp.status = 'paid'
        """
        params = [start_date, end_date]
        
        if project_id:
            query += " AND bp.project_id = ?"
            params.append(project_id)
        
        result = conn.execute(query, params).fetchone()
        total, on_time = result if result else (0, 0)
        
        return (on_time / total * 100) if total > 0 else 0.0
    
    def _get_total_customers(self, conn: sqlite3.Connection, project_id: Optional[int]) -> int:
        """Get total customer count"""
        query = "SELECT COUNT(*) FROM participants WHERE type = 'consumer'"
        params = []
        
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        
        result = conn.execute(query, params).fetchone()
        return result[0] if result else 0
    
    def _get_active_customers(self, conn: sqlite3.Connection, end_date: date, project_id: Optional[int]) -> int:
        """Get active customer count"""
        # Customers with recent consumption data
        query = """
        SELECT COUNT(DISTINCT p.id)
        FROM participants p
        JOIN monthly_consumption mc ON p.id = mc.participant_id
        WHERE p.type = 'consumer' 
        AND mc.year = ? AND mc.month = ?
        """
        params = [end_date.year, end_date.month]
        
        if project_id:
            query += " AND p.project_id = ?"
            params.append(project_id)
        
        result = conn.execute(query, params).fetchone()
        return result[0] if result else 0
    
    def _calculate_retention_rate(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        """Calculate customer retention rate"""
        # Simplified: customers active at start and end of period
        start_active = self._get_active_customers(conn, start_date, project_id)
        end_active = self._get_active_customers(conn, end_date, project_id)
        
        return (end_active / start_active * 100) if start_active > 0 else 100.0
    
    def _calculate_clv(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        """Calculate Customer Lifetime Value"""
        arpc = self._calculate_arpc(conn, start_date, end_date, project_id)
        # Simple CLV: ARPC * 12 months * assumed lifetime of 10 years
        return arpc * 12 * 10
    
    def _calculate_total_energy_sold(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        """Calculate total energy sold"""
        query = """
        SELECT COALESCE(SUM(mc.autoconsumption_kwh), 0)
        FROM monthly_consumption mc
        JOIN participants p ON mc.participant_id = p.id
        WHERE mc.year >= ? AND mc.year <= ?
        """
        params = [start_date.year, end_date.year]
        
        if project_id:
            query += " AND p.project_id = ?"
            params.append(project_id)
        
        result = conn.execute(query, params).fetchone()
        return result[0] if result else 0.0
    
    def _calculate_avg_energy_price(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        """Calculate average energy price"""
        total_revenue = self._calculate_total_revenue(conn, start_date, end_date, project_id)
        total_energy = self._calculate_total_energy_sold(conn, start_date, end_date, project_id)
        
        return total_revenue / total_energy if total_energy > 0 else 0.0
    
    def _calculate_energy_efficiency(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        """Calculate energy efficiency ratio"""
        query = """
        SELECT 
            COALESCE(SUM(mp.autoconsumption_kwh), 0) as total_autoconso,
            COALESCE(SUM(mp.total_production_kwh), 0) as total_production
        FROM monthly_production mp
        WHERE mp.year >= ? AND mp.year <= ?
        """
        params = [start_date.year, end_date.year]
        
        if project_id:
            query += " AND mp.project_id = ?"
            params.append(project_id)
        
        result = conn.execute(query, params).fetchone()
        autoconso, production = result if result else (0, 0)
        
        return (autoconso / production * 100) if production > 0 else 0.0
    
    def _calculate_operating_cash_flow(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        """Calculate operating cash flow"""
        # Simplified: collected revenue minus estimated operating costs
        query = """
        SELECT COALESCE(SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END), 0)
        FROM billing_periods bp
        WHERE bp.start_date >= ? AND bp.end_date <= ?
        """
        params = [start_date, end_date]
        
        if project_id:
            query += " AND bp.project_id = ?"
            params.append(project_id)
        
        result = conn.execute(query, params).fetchone()
        collected_revenue = result[0] if result else 0.0
        
        # Assume 20% operating costs
        return collected_revenue * 0.8
    
    def _calculate_free_cash_flow(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        """Calculate free cash flow"""
        operating_cf = self._calculate_operating_cash_flow(conn, start_date, end_date, project_id)
        # Assume minimal capex for ongoing operations
        return operating_cf * 0.95
    
    def _calculate_cash_conversion_cycle(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        """Calculate cash conversion cycle"""
        dso = self._calculate_dso(conn, end_date, project_id)
        # Simplified: just DSO since we don't have inventory or payables
        return dso
    
    def _calculate_overdue_ratio(self, conn: sqlite3.Connection, end_date: date, project_id: Optional[int]) -> float:
        """Calculate overdue ratio"""
        query = """
        SELECT 
            COUNT(*) as total_invoices,
            SUM(CASE WHEN payment_due_date < date('now') AND status != 'paid' THEN 1 ELSE 0 END) as overdue_count
        FROM billing_periods bp
        WHERE bp.end_date <= ?
        """
        params = [end_date]
        
        if project_id:
            query += " AND bp.project_id = ?"
            params.append(project_id)
        
        result = conn.execute(query, params).fetchone()
        total, overdue = result if result else (0, 0)
        
        return (overdue / total * 100) if total > 0 else 0.0
    
    def _calculate_bad_debt_ratio(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        """Calculate bad debt ratio"""
        # Invoices overdue by more than 90 days
        query = """
        SELECT 
            COALESCE(SUM(total_amount), 0) as total_billed,
            COALESCE(SUM(CASE WHEN payment_due_date < date('now', '-90 days') AND status != 'paid' THEN total_amount ELSE 0 END), 0) as bad_debt
        FROM billing_periods bp
        WHERE bp.start_date >= ? AND bp.end_date <= ?
        """
        params = [start_date, end_date]
        
        if project_id:
            query += " AND bp.project_id = ?"
            params.append(project_id)
        
        result = conn.execute(query, params).fetchone()
        total_billed, bad_debt = result if result else (0, 0)
        
        return (bad_debt / total_billed * 100) if total_billed > 0 else 0.0
    
    def _calculate_concentration_risk(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        """Calculate customer concentration risk"""
        # Revenue from top customer as % of total
        query = """
        SELECT 
            p.name,
            SUM(bp.total_amount) as customer_revenue
        FROM billing_periods bp
        JOIN participants p ON bp.project_id = p.project_id
        WHERE bp.start_date >= ? AND bp.end_date <= ?
        """
        params = [start_date, end_date]
        
        if project_id:
            query += " AND bp.project_id = ?"
            params.append(project_id)
        
        query += " GROUP BY p.id ORDER BY customer_revenue DESC LIMIT 1"
        
        result = conn.execute(query, params).fetchone()
        top_customer_revenue = result[1] if result else 0.0
        
        total_revenue = self._calculate_total_revenue(conn, start_date, end_date, project_id)
        
        return (top_customer_revenue / total_revenue * 100) if total_revenue > 0 else 0.0
    
    def _get_metric_time_series(self, conn: sqlite3.Connection, metric_name: str, start_date: date, end_date: date, project_id: Optional[int]) -> List[Dict[str, Any]]:
        """Get time series data for a specific metric"""
        # Simplified implementation - returns monthly data points
        data = []
        current = start_date.replace(day=1)
        
        while current <= end_date:
            next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
            period_end = min(next_month - timedelta(days=1), end_date)
            
            if metric_name == 'revenue':
                value = self._calculate_total_revenue(conn, current, period_end, project_id)
            elif metric_name == 'collection_rate':
                value = self._calculate_collection_rate(conn, current, period_end, project_id)
            elif metric_name == 'customer_count':
                value = self._get_active_customers(conn, period_end, project_id)
            elif metric_name == 'energy_sold':
                value = self._calculate_total_energy_sold(conn, current, period_end, project_id)
            else:
                value = 0.0
            
            data.append({
                'date': current.isoformat(),
                'value': value
            })
            
            current = next_month
        
        return data