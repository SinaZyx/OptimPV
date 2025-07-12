"""
Dashboard Data Provider for PMO Billing System
Provides real-time data, caching, and alert systems for Streamlit dashboard
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
import logging
import json
import sqlite3
from dataclasses import dataclass, asdict
import streamlit as st
from enum import Enum
import hashlib
import time

from .analytics import AnalyticsEngine, KPIMetrics
from .database import BillingDatabase

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

class MetricType(Enum):
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    COUNT = "count"
    ENERGY = "energy"
    DAYS = "days"
    RATIO = "ratio"

@dataclass
class AlertNotification:
    """Alert notification data structure"""
    id: str
    title: str
    message: str
    level: AlertLevel
    metric_name: str
    current_value: float
    threshold_value: float
    created_at: datetime
    is_active: bool = True
    action_required: bool = False
    suggested_actions: List[str] = None

@dataclass
class DashboardMetric:
    """Dashboard metric with formatting and metadata"""
    name: str
    value: Union[float, int, str]
    previous_value: Optional[Union[float, int]] = None
    delta: Optional[float] = None
    delta_percent: Optional[float] = None
    unit: str = ""
    format_type: MetricType = MetricType.COUNT
    trend: str = "stable"  # up, down, stable
    color: str = "blue"
    description: str = ""
    last_updated: datetime = None

@dataclass
class WidgetData:
    """Widget data for dashboard components"""
    widget_id: str
    title: str
    data: Any
    chart_type: str = "metric"  # metric, chart, table, gauge
    config: Dict[str, Any] = None
    last_updated: datetime = None
    refresh_interval: int = 300  # seconds

class DashboardCache:
    """Intelligent caching system for dashboard data"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache = {}
        self.timestamps = {}
        self.default_ttl = default_ttl
        self.access_count = {}
        self.hit_rate = 0.0
        self.total_requests = 0
        self.cache_hits = 0
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str, ttl: Optional[int] = None) -> Optional[Any]:
        """Get item from cache"""
        self.total_requests += 1
        
        if key not in self.cache:
            return None
        
        # Check TTL
        age = time.time() - self.timestamps[key]
        max_age = ttl or self.default_ttl
        
        if age > max_age:
            self.remove(key)
            return None
        
        self.cache_hits += 1
        self.access_count[key] = self.access_count.get(key, 0) + 1
        self.hit_rate = self.cache_hits / self.total_requests
        
        return self.cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set item in cache"""
        self.cache[key] = value
        self.timestamps[key] = time.time()
        self.access_count[key] = self.access_count.get(key, 0)
    
    def remove(self, key: str) -> None:
        """Remove item from cache"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
        self.access_count.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()
        self.timestamps.clear()
        self.access_count.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'total_items': len(self.cache),
            'total_requests': self.total_requests,
            'cache_hits': self.cache_hits,
            'hit_rate': round(self.hit_rate * 100, 2),
            'most_accessed': max(self.access_count.items(), key=lambda x: x[1]) if self.access_count else None
        }

class DashboardDataProvider:
    """Main dashboard data provider with real-time capabilities"""
    
    def __init__(self, db_path: str = "data/billing.db"):
        """Initialize dashboard data provider"""
        self.db = BillingDatabase(db_path)
        self.analytics = AnalyticsEngine(db_path)
        self.cache = DashboardCache()
        
        # Alert thresholds
        self.alert_thresholds = {
            'collection_rate': {'warning': 85.0, 'error': 75.0},
            'overdue_ratio': {'warning': 10.0, 'error': 20.0},
            'days_sales_outstanding': {'warning': 45.0, 'error': 60.0},
            'cash_flow': {'warning': 5000.0, 'error': 1000.0},
            'bad_debt_ratio': {'warning': 2.0, 'error': 5.0}
        }
        
        # Initialize session state for alerts
        if 'dashboard_alerts' not in st.session_state:
            st.session_state.dashboard_alerts = []
    
    def get_realtime_metrics(self, 
                           project_id: Optional[int] = None,
                           force_refresh: bool = False) -> Dict[str, DashboardMetric]:
        """Get real-time metrics for dashboard"""
        
        cache_key = f"realtime_metrics_{project_id}"
        
        if not force_refresh:
            cached_data = self.cache.get(cache_key, ttl=60)  # 1 minute cache
            if cached_data:
                return cached_data
        
        try:
            # Get current KPIs
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            current_kpis = self.analytics.calculate_comprehensive_kpis(start_date, end_date, project_id)
            
            # Get previous period for comparison
            prev_end = start_date - timedelta(days=1)
            prev_start = prev_end - timedelta(days=30)
            previous_kpis = self.analytics.calculate_comprehensive_kpis(prev_start, prev_end, project_id)
            
            metrics = {}
            
            # Revenue metrics
            metrics['total_revenue'] = self._create_metric(
                "Total Revenue",
                current_kpis.total_revenue,
                previous_kpis.total_revenue,
                MetricType.CURRENCY,
                "Total revenue for the period"
            )
            
            metrics['monthly_recurring_revenue'] = self._create_metric(
                "Monthly Recurring Revenue",
                current_kpis.monthly_recurring_revenue,
                previous_kpis.monthly_recurring_revenue,
                MetricType.CURRENCY,
                "Predictable monthly revenue"
            )
            
            # Operational metrics
            metrics['collection_rate'] = self._create_metric(
                "Collection Rate",
                current_kpis.collection_rate,
                previous_kpis.collection_rate,
                MetricType.PERCENTAGE,
                "Percentage of invoices collected"
            )
            
            metrics['days_sales_outstanding'] = self._create_metric(
                "Days Sales Outstanding",
                current_kpis.days_sales_outstanding,
                previous_kpis.days_sales_outstanding,
                MetricType.DAYS,
                "Average days to collect payment"
            )
            
            # Customer metrics
            metrics['active_customers'] = self._create_metric(
                "Active Customers",
                current_kpis.active_customers,
                previous_kpis.active_customers,
                MetricType.COUNT,
                "Number of active customers"
            )
            
            metrics['customer_retention_rate'] = self._create_metric(
                "Customer Retention",
                current_kpis.customer_retention_rate,
                previous_kpis.customer_retention_rate,
                MetricType.PERCENTAGE,
                "Customer retention rate"
            )
            
            # Energy metrics
            metrics['total_energy_sold'] = self._create_metric(
                "Energy Sold",
                current_kpis.total_energy_sold_kwh,
                previous_kpis.total_energy_sold_kwh,
                MetricType.ENERGY,
                "Total energy sold in kWh"
            )
            
            metrics['average_price_per_kwh'] = self._create_metric(
                "Avg Price per kWh",
                current_kpis.average_price_per_kwh,
                previous_kpis.average_price_per_kwh,
                MetricType.CURRENCY,
                "Average price per kilowatt-hour"
            )
            
            # Risk metrics
            metrics['overdue_ratio'] = self._create_metric(
                "Overdue Ratio",
                current_kpis.overdue_ratio,
                previous_kpis.overdue_ratio,
                MetricType.PERCENTAGE,
                "Percentage of overdue invoices"
            )
            
            metrics['bad_debt_ratio'] = self._create_metric(
                "Bad Debt Ratio",
                current_kpis.bad_debt_ratio,
                previous_kpis.bad_debt_ratio,
                MetricType.PERCENTAGE,
                "Percentage of bad debt"
            )
            
            # Cash flow metrics
            metrics['operating_cash_flow'] = self._create_metric(
                "Operating Cash Flow",
                current_kpis.operating_cash_flow,
                previous_kpis.operating_cash_flow,
                MetricType.CURRENCY,
                "Operating cash flow"
            )
            
            metrics['free_cash_flow'] = self._create_metric(
                "Free Cash Flow",
                current_kpis.free_cash_flow,
                previous_kpis.free_cash_flow,
                MetricType.CURRENCY,
                "Free cash flow"
            )
            
            # Cache the results
            self.cache.set(cache_key, metrics, ttl=60)
            
            # Check for alerts
            self._check_alerts(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting real-time metrics: {e}")
            return {}
    
    def get_widget_data(self, 
                       widget_id: str,
                       config: Optional[Dict[str, Any]] = None,
                       project_id: Optional[int] = None) -> Optional[WidgetData]:
        """Get data for specific dashboard widget"""
        
        cache_key = f"widget_{widget_id}_{project_id}"
        cached_data = self.cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            if widget_id == "revenue_chart":
                data = self._get_revenue_chart_data(project_id, config)
            elif widget_id == "customer_distribution":
                data = self._get_customer_distribution_data(project_id, config)
            elif widget_id == "payment_status":
                data = self._get_payment_status_data(project_id, config)
            elif widget_id == "energy_production":
                data = self._get_energy_production_data(project_id, config)
            elif widget_id == "risk_assessment":
                data = self._get_risk_assessment_data(project_id, config)
            elif widget_id == "cash_flow_forecast":
                data = self._get_cash_flow_forecast_data(project_id, config)
            elif widget_id == "top_customers":
                data = self._get_top_customers_data(project_id, config)
            elif widget_id == "aging_analysis":
                data = self._get_aging_analysis_data(project_id, config)
            else:
                logger.warning(f"Unknown widget ID: {widget_id}")
                return None
            
            widget_data = WidgetData(
                widget_id=widget_id,
                title=data.get('title', widget_id.replace('_', ' ').title()),
                data=data.get('data', {}),
                chart_type=data.get('chart_type', 'metric'),
                config=config or {},
                last_updated=datetime.now(),
                refresh_interval=data.get('refresh_interval', 300)
            )
            
            # Cache with appropriate TTL
            self.cache.set(cache_key, widget_data, ttl=widget_data.refresh_interval)
            
            return widget_data
            
        except Exception as e:
            logger.error(f"Error getting widget data for {widget_id}: {e}")
            return None
    
    def get_active_alerts(self, 
                         level: Optional[AlertLevel] = None,
                         limit: int = 10) -> List[AlertNotification]:
        """Get active alert notifications"""
        
        alerts = st.session_state.get('dashboard_alerts', [])
        
        # Filter by level if specified
        if level:
            alerts = [alert for alert in alerts if alert.level == level]
        
        # Filter active alerts
        active_alerts = [alert for alert in alerts if alert.is_active]
        
        # Sort by creation time (newest first)
        active_alerts.sort(key=lambda x: x.created_at, reverse=True)
        
        return active_alerts[:limit]
    
    def dismiss_alert(self, alert_id: str) -> bool:
        """Dismiss an alert"""
        try:
            alerts = st.session_state.get('dashboard_alerts', [])
            for alert in alerts:
                if alert.id == alert_id:
                    alert.is_active = False
                    return True
            return False
        except Exception as e:
            logger.error(f"Error dismissing alert {alert_id}: {e}")
            return False
    
    def get_performance_summary(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """Get performance summary for executive dashboard"""
        
        cache_key = f"performance_summary_{project_id}"
        cached_data = self.cache.get(cache_key, ttl=300)  # 5 minutes cache
        
        if cached_data:
            return cached_data
        
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            kpis = self.analytics.calculate_comprehensive_kpis(start_date, end_date, project_id)
            segments = self.analytics.segment_customers(project_id)
            
            summary = {
                'financial_health': self._assess_financial_health(kpis),
                'operational_efficiency': self._assess_operational_efficiency(kpis),
                'customer_satisfaction': self._assess_customer_satisfaction(kpis, segments),
                'risk_level': self._assess_risk_level(kpis),
                'growth_potential': self._assess_growth_potential(kpis),
                'recommendations': self._generate_recommendations(kpis, segments)
            }
            
            self.cache.set(cache_key, summary, ttl=300)
            return summary
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        return self.cache.get_stats()
    
    def clear_cache(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries, optionally by pattern"""
        if pattern:
            cleared = 0
            keys_to_remove = [key for key in self.cache.cache.keys() if pattern in key]
            for key in keys_to_remove:
                self.cache.remove(key)
                cleared += 1
            return cleared
        else:
            count = len(self.cache.cache)
            self.cache.clear()
            return count
    
    # Private helper methods
    
    def _create_metric(self, 
                      name: str, 
                      current: float, 
                      previous: float,
                      format_type: MetricType,
                      description: str) -> DashboardMetric:
        """Create a dashboard metric with trend analysis"""
        
        # Calculate delta and trend
        delta = current - previous if previous is not None else 0
        delta_percent = (delta / previous * 100) if previous and previous != 0 else 0
        
        # Determine trend and color
        if abs(delta_percent) < 1:
            trend = "stable"
            color = "blue"
        elif delta_percent > 0:
            trend = "up"
            color = "green" if format_type not in [MetricType.DAYS] else "red"  # DSO going up is bad
        else:
            trend = "down"
            color = "red" if format_type not in [MetricType.DAYS] else "green"  # DSO going down is good
        
        # Special handling for risk metrics
        if 'overdue' in name.lower() or 'bad_debt' in name.lower():
            color = "red" if delta_percent > 0 else "green"
        
        return DashboardMetric(
            name=name,
            value=current,
            previous_value=previous,
            delta=delta,
            delta_percent=delta_percent,
            format_type=format_type,
            trend=trend,
            color=color,
            description=description,
            last_updated=datetime.now()
        )
    
    def _check_alerts(self, metrics: Dict[str, DashboardMetric]) -> None:
        """Check metrics against thresholds and generate alerts"""
        
        current_alerts = st.session_state.get('dashboard_alerts', [])
        
        for metric_name, metric in metrics.items():
            if metric_name in self.alert_thresholds:
                thresholds = self.alert_thresholds[metric_name]
                
                # Check for threshold violations
                alert_level = None
                threshold_value = None
                
                if metric.value >= thresholds.get('error', float('inf')):
                    alert_level = AlertLevel.ERROR
                    threshold_value = thresholds['error']
                elif metric.value >= thresholds.get('warning', float('inf')):
                    alert_level = AlertLevel.WARNING
                    threshold_value = thresholds['warning']
                
                # Create alert if threshold violated
                if alert_level:
                    alert_id = f"{metric_name}_{alert_level.value}_{int(time.time())}"
                    
                    # Check if similar alert already exists
                    existing_alert = any(
                        alert.metric_name == metric_name and 
                        alert.level == alert_level and 
                        alert.is_active 
                        for alert in current_alerts
                    )
                    
                    if not existing_alert:
                        alert = AlertNotification(
                            id=alert_id,
                            title=f"{metric.name} Alert",
                            message=f"{metric.name} is {metric.value:.2f}, exceeding {alert_level.value} threshold of {threshold_value}",
                            level=alert_level,
                            metric_name=metric_name,
                            current_value=metric.value,
                            threshold_value=threshold_value,
                            created_at=datetime.now(),
                            action_required=alert_level == AlertLevel.ERROR,
                            suggested_actions=self._get_suggested_actions(metric_name, alert_level)
                        )
                        
                        current_alerts.append(alert)
        
        st.session_state.dashboard_alerts = current_alerts
    
    def _get_suggested_actions(self, metric_name: str, level: AlertLevel) -> List[str]:
        """Get suggested actions for alerts"""
        
        actions = {
            'collection_rate': [
                "Review outstanding invoices",
                "Contact customers with overdue payments",
                "Consider payment plan options",
                "Review credit policies"
            ],
            'overdue_ratio': [
                "Implement automated reminders",
                "Escalate to collections agency",
                "Review payment terms",
                "Assess customer creditworthiness"
            ],
            'days_sales_outstanding': [
                "Accelerate invoice processing",
                "Offer early payment discounts",
                "Improve payment processing systems",
                "Review customer payment behavior"
            ],
            'cash_flow': [
                "Review cash flow forecasts",
                "Consider short-term financing",
                "Accelerate collections",
                "Delay non-critical expenses"
            ],
            'bad_debt_ratio': [
                "Tighten credit approval process",
                "Increase bad debt provisions",
                "Review customer credit limits",
                "Implement stronger collection procedures"
            ]
        }
        
        return actions.get(metric_name, ["Review metric and take appropriate action"])
    
    def _get_revenue_chart_data(self, project_id: Optional[int], config: Optional[Dict]) -> Dict[str, Any]:
        """Get revenue chart data"""
        
        # Generate mock monthly revenue data
        end_date = date.today()
        start_date = end_date - timedelta(days=365)
        
        dates = pd.date_range(start=start_date, end=end_date, freq='M')
        revenues = np.random.normal(15000, 2000, len(dates))  # Mock data
        revenues = np.maximum(revenues, 5000)  # Ensure positive values
        
        data = {
            'dates': [d.strftime('%Y-%m') for d in dates],
            'revenues': revenues.tolist(),
            'trend': 'increasing' if revenues[-1] > revenues[0] else 'decreasing'
        }
        
        return {
            'title': 'Monthly Revenue Trend',
            'data': data,
            'chart_type': 'line',
            'refresh_interval': 3600  # 1 hour
        }
    
    def _get_customer_distribution_data(self, project_id: Optional[int], config: Optional[Dict]) -> Dict[str, Any]:
        """Get customer distribution data"""
        
        segments = self.analytics.segment_customers(project_id)
        
        if segments:
            data = {
                'labels': [seg.segment_name for seg in segments],
                'values': [seg.customer_count for seg in segments],
                'colors': ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
            }
        else:
            data = {
                'labels': ['Premium', 'Standard', 'Basic'],
                'values': [10, 15, 5],
                'colors': ['#ff9999', '#66b3ff', '#99ff99']
            }
        
        return {
            'title': 'Customer Distribution by Segment',
            'data': data,
            'chart_type': 'pie',
            'refresh_interval': 1800  # 30 minutes
        }
    
    def _get_payment_status_data(self, project_id: Optional[int], config: Optional[Dict]) -> Dict[str, Any]:
        """Get payment status data"""
        
        data = {
            'categories': ['Paid', 'Pending', 'Overdue', 'Cancelled'],
            'values': [75, 15, 8, 2],
            'colors': ['green', 'orange', 'red', 'gray']
        }
        
        return {
            'title': 'Payment Status Distribution',
            'data': data,
            'chart_type': 'bar',
            'refresh_interval': 600  # 10 minutes
        }
    
    def _get_energy_production_data(self, project_id: Optional[int], config: Optional[Dict]) -> Dict[str, Any]:
        """Get energy production data"""
        
        # Mock energy data
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        production = [8500, 9200, 11000, 12500, 13800, 14200]
        consumption = [7000, 7500, 8200, 9000, 9800, 10200]
        
        data = {
            'months': months,
            'production': production,
            'consumption': consumption,
            'efficiency': [(c/p)*100 for p, c in zip(production, consumption)]
        }
        
        return {
            'title': 'Energy Production vs Consumption',
            'data': data,
            'chart_type': 'line',
            'refresh_interval': 3600  # 1 hour
        }
    
    def _get_risk_assessment_data(self, project_id: Optional[int], config: Optional[Dict]) -> Dict[str, Any]:
        """Get risk assessment data"""
        
        risk_predictions = self.analytics.predict_payment_defaults(project_id)
        
        risk_levels = {'Low': 0, 'Medium': 0, 'High': 0}
        for prediction in risk_predictions:
            risk_levels[prediction['risk_level']] += 1
        
        data = {
            'risk_levels': list(risk_levels.keys()),
            'counts': list(risk_levels.values()),
            'total_customers': sum(risk_levels.values())
        }
        
        return {
            'title': 'Customer Risk Assessment',
            'data': data,
            'chart_type': 'gauge',
            'refresh_interval': 1800  # 30 minutes
        }
    
    def _get_cash_flow_forecast_data(self, project_id: Optional[int], config: Optional[Dict]) -> Dict[str, Any]:
        """Get cash flow forecast data"""
        
        # Mock forecast data
        months = pd.date_range(start=date.today(), periods=6, freq='M')
        inflows = [45000, 47000, 48500, 50000, 52000, 54000]
        outflows = [35000, 36000, 37000, 38000, 39000, 40000]
        net_flow = [i - o for i, o in zip(inflows, outflows)]
        
        data = {
            'months': [m.strftime('%Y-%m') for m in months],
            'inflows': inflows,
            'outflows': outflows,
            'net_flow': net_flow
        }
        
        return {
            'title': 'Cash Flow Forecast (6 Months)',
            'data': data,
            'chart_type': 'line',
            'refresh_interval': 3600  # 1 hour
        }
    
    def _get_top_customers_data(self, project_id: Optional[int], config: Optional[Dict]) -> Dict[str, Any]:
        """Get top customers data"""
        
        # Mock top customers data
        customers = [
            {'name': 'Apartment A01', 'revenue': 2500, 'energy': 850},
            {'name': 'Apartment B03', 'revenue': 2200, 'energy': 750},
            {'name': 'Apartment C02', 'revenue': 2000, 'energy': 680},
            {'name': 'Apartment A05', 'revenue': 1800, 'energy': 620},
            {'name': 'Apartment B01', 'revenue': 1600, 'energy': 580}
        ]
        
        return {
            'title': 'Top 5 Customers by Revenue',
            'data': customers,
            'chart_type': 'table',
            'refresh_interval': 1800  # 30 minutes
        }
    
    def _get_aging_analysis_data(self, project_id: Optional[int], config: Optional[Dict]) -> Dict[str, Any]:
        """Get aging analysis data"""
        
        aging_buckets = ['Current', '1-30 Days', '31-60 Days', '61-90 Days', '90+ Days']
        amounts = [45000, 8000, 3000, 1500, 500]
        
        data = {
            'buckets': aging_buckets,
            'amounts': amounts,
            'percentages': [(a/sum(amounts))*100 for a in amounts]
        }
        
        return {
            'title': 'Accounts Receivable Aging',
            'data': data,
            'chart_type': 'bar',
            'refresh_interval': 3600  # 1 hour
        }
    
    def _assess_financial_health(self, kpis: KPIMetrics) -> Dict[str, Any]:
        """Assess financial health"""
        
        score = 0
        max_score = 100
        
        # Revenue growth
        if kpis.revenue_growth_rate > 10:
            score += 25
        elif kpis.revenue_growth_rate > 5:
            score += 15
        elif kpis.revenue_growth_rate > 0:
            score += 10
        
        # Collection efficiency
        if kpis.collection_rate > 95:
            score += 25
        elif kpis.collection_rate > 90:
            score += 20
        elif kpis.collection_rate > 85:
            score += 15
        
        # Cash flow
        if kpis.free_cash_flow > 50000:
            score += 25
        elif kpis.free_cash_flow > 25000:
            score += 20
        elif kpis.free_cash_flow > 10000:
            score += 15
        
        # Risk management
        if kpis.bad_debt_ratio < 1:
            score += 25
        elif kpis.bad_debt_ratio < 3:
            score += 20
        elif kpis.bad_debt_ratio < 5:
            score += 15
        
        health_level = "Excellent" if score >= 80 else "Good" if score >= 60 else "Fair" if score >= 40 else "Poor"
        
        return {
            'score': score,
            'level': health_level,
            'indicators': {
                'revenue_growth': kpis.revenue_growth_rate,
                'collection_rate': kpis.collection_rate,
                'cash_flow': kpis.free_cash_flow,
                'bad_debt': kpis.bad_debt_ratio
            }
        }
    
    def _assess_operational_efficiency(self, kpis: KPIMetrics) -> Dict[str, Any]:
        """Assess operational efficiency"""
        
        efficiency_score = 0
        
        # Payment processing
        if kpis.days_sales_outstanding < 30:
            efficiency_score += 30
        elif kpis.days_sales_outstanding < 45:
            efficiency_score += 20
        elif kpis.days_sales_outstanding < 60:
            efficiency_score += 10
        
        # Collection efficiency
        if kpis.payment_cycle_efficiency > 90:
            efficiency_score += 35
        elif kpis.payment_cycle_efficiency > 80:
            efficiency_score += 25
        elif kpis.payment_cycle_efficiency > 70:
            efficiency_score += 15
        
        # Energy efficiency
        if kpis.energy_efficiency_ratio > 80:
            efficiency_score += 35
        elif kpis.energy_efficiency_ratio > 70:
            efficiency_score += 25
        elif kpis.energy_efficiency_ratio > 60:
            efficiency_score += 15
        
        efficiency_level = "High" if efficiency_score >= 80 else "Medium" if efficiency_score >= 50 else "Low"
        
        return {
            'score': efficiency_score,
            'level': efficiency_level,
            'dso': kpis.days_sales_outstanding,
            'payment_efficiency': kpis.payment_cycle_efficiency,
            'energy_efficiency': kpis.energy_efficiency_ratio
        }
    
    def _assess_customer_satisfaction(self, kpis: KPIMetrics, segments: List) -> Dict[str, Any]:
        """Assess customer satisfaction"""
        
        satisfaction_score = 85  # Base score
        
        # Retention rate impact
        if kpis.customer_retention_rate > 95:
            satisfaction_score += 10
        elif kpis.customer_retention_rate > 90:
            satisfaction_score += 5
        elif kpis.customer_retention_rate < 80:
            satisfaction_score -= 10
        
        # Customer growth
        if len(segments) > 0 and any(seg.customer_count > 0 for seg in segments):
            satisfaction_score += 5
        
        satisfaction_level = "High" if satisfaction_score >= 90 else "Medium" if satisfaction_score >= 75 else "Low"
        
        return {
            'score': min(100, max(0, satisfaction_score)),
            'level': satisfaction_level,
            'retention_rate': kpis.customer_retention_rate,
            'active_customers': kpis.active_customers
        }
    
    def _assess_risk_level(self, kpis: KPIMetrics) -> Dict[str, Any]:
        """Assess overall risk level"""
        
        risk_factors = []
        risk_score = 0
        
        if kpis.overdue_ratio > 15:
            risk_factors.append("High overdue ratio")
            risk_score += 30
        elif kpis.overdue_ratio > 10:
            risk_factors.append("Elevated overdue ratio")
            risk_score += 20
        
        if kpis.bad_debt_ratio > 5:
            risk_factors.append("High bad debt ratio")
            risk_score += 25
        elif kpis.bad_debt_ratio > 3:
            risk_factors.append("Elevated bad debt ratio")
            risk_score += 15
        
        if kpis.concentration_risk > 30:
            risk_factors.append("High customer concentration")
            risk_score += 20
        
        if kpis.days_sales_outstanding > 60:
            risk_factors.append("Extended collection period")
            risk_score += 15
        
        risk_level = "High" if risk_score >= 50 else "Medium" if risk_score >= 25 else "Low"
        
        return {
            'level': risk_level,
            'score': risk_score,
            'factors': risk_factors,
            'overdue_ratio': kpis.overdue_ratio,
            'bad_debt_ratio': kpis.bad_debt_ratio,
            'concentration_risk': kpis.concentration_risk
        }
    
    def _assess_growth_potential(self, kpis: KPIMetrics) -> Dict[str, Any]:
        """Assess growth potential"""
        
        growth_indicators = []
        growth_score = 50  # Base score
        
        if kpis.revenue_growth_rate > 10:
            growth_indicators.append("Strong revenue growth")
            growth_score += 20
        elif kpis.revenue_growth_rate > 5:
            growth_indicators.append("Positive revenue growth")
            growth_score += 10
        
        if kpis.customer_retention_rate > 95:
            growth_indicators.append("Excellent customer retention")
            growth_score += 15
        
        if kpis.average_revenue_per_customer > 1000:
            growth_indicators.append("High customer value")
            growth_score += 15
        
        growth_potential = "High" if growth_score >= 80 else "Medium" if growth_score >= 60 else "Limited"
        
        return {
            'potential': growth_potential,
            'score': min(100, growth_score),
            'indicators': growth_indicators,
            'revenue_growth': kpis.revenue_growth_rate,
            'customer_value': kpis.average_revenue_per_customer
        }
    
    def _generate_recommendations(self, kpis: KPIMetrics, segments: List) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Financial recommendations
        if kpis.collection_rate < 90:
            recommendations.append("Improve collection processes to increase collection rate")
        
        if kpis.days_sales_outstanding > 45:
            recommendations.append("Reduce payment terms or implement early payment incentives")
        
        if kpis.bad_debt_ratio > 3:
            recommendations.append("Strengthen credit assessment and collection procedures")
        
        # Operational recommendations
        if kpis.energy_efficiency_ratio < 70:
            recommendations.append("Optimize energy distribution to improve efficiency")
        
        # Customer recommendations
        if kpis.customer_retention_rate < 90:
            recommendations.append("Implement customer retention programs")
        
        if len(segments) > 0:
            high_risk_segments = [seg for seg in segments if seg.risk_level == "High"]
            if high_risk_segments:
                recommendations.append("Focus on high-risk customer segments with targeted interventions")
        
        # Growth recommendations
        if kpis.revenue_growth_rate < 5:
            recommendations.append("Explore new revenue streams or customer acquisition strategies")
        
        return recommendations[:5]  # Limit to top 5 recommendations