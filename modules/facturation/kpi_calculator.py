"""
Comprehensive KPI Calculator for PMO Billing System
Provides optimized calculations for all business metrics with caching and benchmarking
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
import logging
import sqlite3
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class KPICategory(Enum):
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    CUSTOMER = "customer"
    ENERGY = "energy"
    RISK = "risk"
    GROWTH = "growth"

class BenchmarkType(Enum):
    INDUSTRY = "industry"
    HISTORICAL = "historical"
    TARGET = "target"
    PEER = "peer"

@dataclass
class KPIDefinition:
    """KPI definition with metadata"""
    name: str
    category: KPICategory
    description: str
    formula: str
    unit: str
    good_threshold: float
    excellent_threshold: float
    format_pattern: str = "{:.2f}"
    is_higher_better: bool = True
    calculation_method: str = "direct"
    dependencies: List[str] = field(default_factory=list)
    update_frequency: str = "daily"  # daily, weekly, monthly
    
@dataclass
class KPIResult:
    """KPI calculation result with context"""
    name: str
    value: float
    formatted_value: str
    category: KPICategory
    calculation_date: datetime
    period_start: date
    period_end: date
    benchmark_comparisons: Dict[BenchmarkType, float] = field(default_factory=dict)
    trend_direction: str = "stable"  # up, down, stable
    performance_rating: str = "fair"  # excellent, good, fair, poor
    contributing_factors: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    
@dataclass
class KPIBenchmark:
    """KPI benchmark data"""
    benchmark_type: BenchmarkType
    value: float
    source: str
    date_collected: date
    confidence_level: float = 0.8

class KPICache:
    """High-performance KPI cache with TTL and dependency tracking"""
    
    def __init__(self):
        self.cache = {}
        self.dependencies = {}
        self.timestamps = {}
        self.hit_count = 0
        self.miss_count = 0
    
    def _generate_key(self, kpi_name: str, start_date: date, end_date: date, project_id: Optional[int]) -> str:
        """Generate cache key"""
        key_data = f"{kpi_name}_{start_date}_{end_date}_{project_id}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str, ttl: int = 3600) -> Optional[Any]:
        """Get cached KPI result"""
        if key not in self.cache:
            self.miss_count += 1
            return None
        
        # Check TTL
        if time.time() - self.timestamps[key] > ttl:
            self.invalidate(key)
            self.miss_count += 1
            return None
        
        self.hit_count += 1
        return self.cache[key]
    
    def set(self, key: str, value: Any, dependencies: List[str] = None) -> None:
        """Set cached KPI result"""
        self.cache[key] = value
        self.timestamps[key] = time.time()
        
        if dependencies:
            self.dependencies[key] = dependencies
    
    def invalidate(self, key: str) -> None:
        """Invalidate cached entry"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
        self.dependencies.pop(key, None)
    
    def invalidate_by_dependency(self, dependency: str) -> int:
        """Invalidate all entries that depend on a given data source"""
        invalidated = 0
        keys_to_remove = []
        
        for key, deps in self.dependencies.items():
            if dependency in deps:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self.invalidate(key)
            invalidated += 1
        
        return invalidated
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'entries': len(self.cache),
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests,
            'memory_usage_kb': sum(len(str(v)) for v in self.cache.values()) / 1024
        }

class KPICalculator:
    """High-performance KPI calculator with benchmarking and optimization"""
    
    def __init__(self, db_path: str = "data/billing.db"):
        """Initialize KPI calculator"""
        self.db_path = db_path
        self.cache = KPICache()
        self.benchmarks = {}
        self.kpi_definitions = self._initialize_kpi_definitions()
        
        # Performance optimization
        self.connection_pool = []
        self.max_connections = 3
        
        # Load benchmarks
        self._load_benchmarks()
    
    def calculate_kpi(self, 
                     kpi_name: str,
                     start_date: date,
                     end_date: date,
                     project_id: Optional[int] = None,
                     use_cache: bool = True,
                     include_benchmarks: bool = True) -> Optional[KPIResult]:
        """Calculate individual KPI with full context"""
        
        if kpi_name not in self.kpi_definitions:
            logger.error(f"Unknown KPI: {kpi_name}")
            return None
        
        # Check cache first
        cache_key = self.cache._generate_key(kpi_name, start_date, end_date, project_id)
        if use_cache:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                return cached_result
        
        try:
            kpi_def = self.kpi_definitions[kpi_name]
            
            # Calculate the KPI value
            value = self._calculate_kpi_value(kpi_name, start_date, end_date, project_id)
            
            if value is None:
                return None
            
            # Format the value
            formatted_value = self._format_kpi_value(value, kpi_def)
            
            # Performance rating
            rating = self._get_performance_rating(kpi_name, value)
            
            # Trend analysis
            trend = self._calculate_trend(kpi_name, value, start_date, end_date, project_id)
            
            # Contributing factors
            factors = self._identify_contributing_factors(kpi_name, value, start_date, end_date, project_id)
            
            # Improvement suggestions
            suggestions = self._generate_improvement_suggestions(kpi_name, value, rating)
            
            # Benchmark comparisons
            benchmark_comparisons = {}
            if include_benchmarks:
                benchmark_comparisons = self._get_benchmark_comparisons(kpi_name, value)
            
            result = KPIResult(
                name=kpi_name,
                value=value,
                formatted_value=formatted_value,
                category=kpi_def.category,
                calculation_date=datetime.now(),
                period_start=start_date,
                period_end=end_date,
                benchmark_comparisons=benchmark_comparisons,
                trend_direction=trend,
                performance_rating=rating,
                contributing_factors=factors,
                improvement_suggestions=suggestions
            )
            
            # Cache the result
            if use_cache:
                self.cache.set(cache_key, result, kpi_def.dependencies)
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating KPI {kpi_name}: {e}")
            return None
    
    def calculate_kpi_batch(self,
                           kpi_names: List[str],
                           start_date: date,
                           end_date: date,
                           project_id: Optional[int] = None,
                           parallel: bool = True) -> Dict[str, KPIResult]:
        """Calculate multiple KPIs in batch (optionally parallel)"""
        
        results = {}
        
        if parallel and len(kpi_names) > 1:
            # Parallel calculation
            with ThreadPoolExecutor(max_workers=min(len(kpi_names), 4)) as executor:
                future_to_kpi = {
                    executor.submit(self.calculate_kpi, kpi_name, start_date, end_date, project_id): kpi_name
                    for kpi_name in kpi_names
                }
                
                for future in as_completed(future_to_kpi):
                    kpi_name = future_to_kpi[future]
                    try:
                        result = future.result()
                        if result:
                            results[kpi_name] = result
                    except Exception as e:
                        logger.error(f"Error calculating KPI {kpi_name} in parallel: {e}")
        else:
            # Sequential calculation
            for kpi_name in kpi_names:
                result = self.calculate_kpi(kpi_name, start_date, end_date, project_id)
                if result:
                    results[kpi_name] = result
        
        return results
    
    def calculate_category_kpis(self,
                               category: KPICategory,
                               start_date: date,
                               end_date: date,
                               project_id: Optional[int] = None) -> Dict[str, KPIResult]:
        """Calculate all KPIs in a specific category"""
        
        category_kpis = [
            name for name, definition in self.kpi_definitions.items()
            if definition.category == category
        ]
        
        return self.calculate_kpi_batch(category_kpis, start_date, end_date, project_id)
    
    def calculate_dashboard_kpis(self,
                                start_date: date,
                                end_date: date,
                                project_id: Optional[int] = None) -> Dict[str, KPIResult]:
        """Calculate key KPIs for dashboard display"""
        
        dashboard_kpis = [
            'total_revenue',
            'monthly_recurring_revenue',
            'collection_rate',
            'days_sales_outstanding',
            'active_customers',
            'customer_retention_rate',
            'energy_sold',
            'average_price_per_kwh',
            'overdue_ratio',
            'operating_cash_flow'
        ]
        
        return self.calculate_kpi_batch(dashboard_kpis, start_date, end_date, project_id, parallel=True)
    
    def get_kpi_definition(self, kpi_name: str) -> Optional[KPIDefinition]:
        """Get KPI definition"""
        return self.kpi_definitions.get(kpi_name)
    
    def get_all_kpi_names(self, category: Optional[KPICategory] = None) -> List[str]:
        """Get all available KPI names, optionally filtered by category"""
        if category:
            return [name for name, definition in self.kpi_definitions.items() 
                   if definition.category == category]
        return list(self.kpi_definitions.keys())
    
    def add_benchmark(self, 
                     kpi_name: str, 
                     benchmark: KPIBenchmark) -> bool:
        """Add benchmark for a KPI"""
        try:
            if kpi_name not in self.benchmarks:
                self.benchmarks[kpi_name] = {}
            
            self.benchmarks[kpi_name][benchmark.benchmark_type] = benchmark
            return True
        except Exception as e:
            logger.error(f"Error adding benchmark for {kpi_name}: {e}")
            return False
    
    def export_kpis_to_external_system(self,
                                      kpi_results: Dict[str, KPIResult],
                                      system_type: str = "json") -> Union[str, Dict[str, Any]]:
        """Export KPI results to external systems"""
        
        if system_type == "json":
            export_data = {}
            for kpi_name, result in kpi_results.items():
                export_data[kpi_name] = {
                    'value': result.value,
                    'formatted_value': result.formatted_value,
                    'category': result.category.value,
                    'period_start': result.period_start.isoformat(),
                    'period_end': result.period_end.isoformat(),
                    'performance_rating': result.performance_rating,
                    'trend_direction': result.trend_direction,
                    'benchmarks': {bt.value: bv for bt, bv in result.benchmark_comparisons.items()}
                }
            
            return json.dumps(export_data, indent=2)
        
        elif system_type == "dataframe":
            rows = []
            for kpi_name, result in kpi_results.items():
                rows.append({
                    'kpi_name': kpi_name,
                    'value': result.value,
                    'formatted_value': result.formatted_value,
                    'category': result.category.value,
                    'period_start': result.period_start,
                    'period_end': result.period_end,
                    'performance_rating': result.performance_rating,
                    'trend_direction': result.trend_direction
                })
            
            return pd.DataFrame(rows)
        
        return kpi_results
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        return self.cache.get_stats()
    
    def clear_cache(self, kpi_name: Optional[str] = None) -> int:
        """Clear cache entries"""
        if kpi_name:
            # Clear specific KPI cache entries
            cleared = 0
            keys_to_remove = [key for key in self.cache.cache.keys() if kpi_name in key]
            for key in keys_to_remove:
                self.cache.invalidate(key)
                cleared += 1
            return cleared
        else:
            # Clear all cache
            count = len(self.cache.cache)
            self.cache.cache.clear()
            self.cache.timestamps.clear()
            self.cache.dependencies.clear()
            return count
    
    # Private calculation methods
    
    def _calculate_kpi_value(self, 
                            kpi_name: str, 
                            start_date: date, 
                            end_date: date, 
                            project_id: Optional[int]) -> Optional[float]:
        """Calculate the actual KPI value"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                
                # Financial KPIs
                if kpi_name == 'total_revenue':
                    return self._calc_total_revenue(conn, start_date, end_date, project_id)
                elif kpi_name == 'monthly_recurring_revenue':
                    return self._calc_mrr(conn, end_date, project_id)
                elif kpi_name == 'average_revenue_per_customer':
                    return self._calc_arpc(conn, start_date, end_date, project_id)
                elif kpi_name == 'revenue_growth_rate':
                    return self._calc_revenue_growth(conn, start_date, end_date, project_id)
                elif kpi_name == 'gross_margin':
                    return self._calc_gross_margin(conn, start_date, end_date, project_id)
                elif kpi_name == 'ebitda':
                    return self._calc_ebitda(conn, start_date, end_date, project_id)
                
                # Operational KPIs
                elif kpi_name == 'collection_rate':
                    return self._calc_collection_rate(conn, start_date, end_date, project_id)
                elif kpi_name == 'days_sales_outstanding':
                    return self._calc_dso(conn, end_date, project_id)
                elif kpi_name == 'payment_cycle_efficiency':
                    return self._calc_payment_efficiency(conn, start_date, end_date, project_id)
                elif kpi_name == 'invoice_processing_time':
                    return self._calc_invoice_processing_time(conn, start_date, end_date, project_id)
                
                # Customer KPIs
                elif kpi_name == 'total_customers':
                    return self._calc_total_customers(conn, project_id)
                elif kpi_name == 'active_customers':
                    return self._calc_active_customers(conn, end_date, project_id)
                elif kpi_name == 'customer_retention_rate':
                    return self._calc_retention_rate(conn, start_date, end_date, project_id)
                elif kpi_name == 'customer_lifetime_value':
                    return self._calc_clv(conn, start_date, end_date, project_id)
                elif kpi_name == 'customer_acquisition_cost':
                    return self._calc_cac(conn, start_date, end_date, project_id)
                elif kpi_name == 'churn_rate':
                    return self._calc_churn_rate(conn, start_date, end_date, project_id)
                
                # Energy KPIs
                elif kpi_name == 'energy_sold':
                    return self._calc_energy_sold(conn, start_date, end_date, project_id)
                elif kpi_name == 'average_price_per_kwh':
                    return self._calc_avg_price_kwh(conn, start_date, end_date, project_id)
                elif kpi_name == 'energy_efficiency_ratio':
                    return self._calc_energy_efficiency(conn, start_date, end_date, project_id)
                elif kpi_name == 'capacity_utilization':
                    return self._calc_capacity_utilization(conn, start_date, end_date, project_id)
                elif kpi_name == 'peak_demand_coverage':
                    return self._calc_peak_demand_coverage(conn, start_date, end_date, project_id)
                
                # Risk KPIs
                elif kpi_name == 'overdue_ratio':
                    return self._calc_overdue_ratio(conn, end_date, project_id)
                elif kpi_name == 'bad_debt_ratio':
                    return self._calc_bad_debt_ratio(conn, start_date, end_date, project_id)
                elif kpi_name == 'concentration_risk':
                    return self._calc_concentration_risk(conn, start_date, end_date, project_id)
                elif kpi_name == 'credit_risk_score':
                    return self._calc_credit_risk_score(conn, end_date, project_id)
                
                # Cash Flow KPIs
                elif kpi_name == 'operating_cash_flow':
                    return self._calc_operating_cash_flow(conn, start_date, end_date, project_id)
                elif kpi_name == 'free_cash_flow':
                    return self._calc_free_cash_flow(conn, start_date, end_date, project_id)
                elif kpi_name == 'cash_conversion_cycle':
                    return self._calc_cash_conversion_cycle(conn, start_date, end_date, project_id)
                elif kpi_name == 'working_capital':
                    return self._calc_working_capital(conn, end_date, project_id)
                
                # Growth KPIs
                elif kpi_name == 'customer_growth_rate':
                    return self._calc_customer_growth_rate(conn, start_date, end_date, project_id)
                elif kpi_name == 'revenue_per_kwh_growth':
                    return self._calc_revenue_per_kwh_growth(conn, start_date, end_date, project_id)
                elif kpi_name == 'market_share':
                    return self._calc_market_share(conn, start_date, end_date, project_id)
                
                else:
                    logger.warning(f"Unknown KPI calculation method: {kpi_name}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error calculating {kpi_name}: {e}")
            return None
    
    # Financial KPI calculations
    def _calc_total_revenue(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        query = "SELECT COALESCE(SUM(total_amount), 0) FROM billing_periods WHERE start_date >= ? AND end_date <= ?"
        params = [start_date, end_date]
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        return conn.execute(query, params).fetchone()[0]
    
    def _calc_mrr(self, conn: sqlite3.Connection, end_date: date, project_id: Optional[int]) -> float:
        start_date = end_date - timedelta(days=90)
        total_revenue = self._calc_total_revenue(conn, start_date, end_date, project_id)
        return total_revenue / 3  # Average over 3 months
    
    def _calc_arpc(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        total_revenue = self._calc_total_revenue(conn, start_date, end_date, project_id)
        customer_count = self._calc_active_customers(conn, end_date, project_id)
        return total_revenue / customer_count if customer_count > 0 else 0.0
    
    def _calc_revenue_growth(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        period_days = (end_date - start_date).days
        prev_start = start_date - timedelta(days=period_days)
        prev_end = start_date
        
        current_revenue = self._calc_total_revenue(conn, start_date, end_date, project_id)
        previous_revenue = self._calc_total_revenue(conn, prev_start, prev_end, project_id)
        
        return ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0.0
    
    def _calc_gross_margin(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        revenue = self._calc_total_revenue(conn, start_date, end_date, project_id)
        # Estimate costs as 25% of revenue (would need actual cost data)
        estimated_costs = revenue * 0.25
        return ((revenue - estimated_costs) / revenue * 100) if revenue > 0 else 0.0
    
    def _calc_ebitda(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        revenue = self._calc_total_revenue(conn, start_date, end_date, project_id)
        # Simplified EBITDA calculation (would need actual cost breakdown)
        estimated_operating_costs = revenue * 0.30
        return revenue - estimated_operating_costs
    
    # Operational KPI calculations
    def _calc_collection_rate(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        query = """
        SELECT 
            COALESCE(SUM(total_amount), 0) as total_billed,
            COALESCE(SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END), 0) as total_collected
        FROM billing_periods WHERE start_date >= ? AND end_date <= ?
        """
        params = [start_date, end_date]
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        
        result = conn.execute(query, params).fetchone()
        total_billed, total_collected = result if result else (0, 0)
        return (total_collected / total_billed * 100) if total_billed > 0 else 0.0
    
    def _calc_dso(self, conn: sqlite3.Connection, end_date: date, project_id: Optional[int]) -> float:
        query = """
        SELECT AVG(julianday(COALESCE(paid_date, date('now'))) - julianday(start_date))
        FROM billing_periods WHERE end_date <= ?
        """
        params = [end_date]
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        
        result = conn.execute(query, params).fetchone()
        return result[0] if result and result[0] else 30.0
    
    def _calc_payment_efficiency(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        query = """
        SELECT 
            COUNT(*) as total_invoices,
            SUM(CASE WHEN paid_date <= payment_due_date THEN 1 ELSE 0 END) as on_time_payments
        FROM billing_periods WHERE start_date >= ? AND end_date <= ? AND status = 'paid'
        """
        params = [start_date, end_date]
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        
        result = conn.execute(query, params).fetchone()
        total, on_time = result if result else (0, 0)
        return (on_time / total * 100) if total > 0 else 0.0
    
    def _calc_invoice_processing_time(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        # Mock calculation - would need actual invoice processing timestamps
        return 2.5  # Average 2.5 days processing time
    
    # Customer KPI calculations
    def _calc_total_customers(self, conn: sqlite3.Connection, project_id: Optional[int]) -> float:
        query = "SELECT COUNT(*) FROM participants WHERE type = 'consumer'"
        params = []
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        return conn.execute(query, params).fetchone()[0]
    
    def _calc_active_customers(self, conn: sqlite3.Connection, end_date: date, project_id: Optional[int]) -> float:
        query = """
        SELECT COUNT(DISTINCT p.id)
        FROM participants p
        JOIN monthly_consumption mc ON p.id = mc.participant_id
        WHERE p.type = 'consumer' AND mc.year = ? AND mc.month = ?
        """
        params = [end_date.year, end_date.month]
        if project_id:
            query += " AND p.project_id = ?"
            params.append(project_id)
        
        return conn.execute(query, params).fetchone()[0]
    
    def _calc_retention_rate(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        start_active = self._calc_active_customers(conn, start_date, project_id)
        end_active = self._calc_active_customers(conn, end_date, project_id)
        return (end_active / start_active * 100) if start_active > 0 else 100.0
    
    def _calc_clv(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        arpc = self._calc_arpc(conn, start_date, end_date, project_id)
        # Simplified CLV: ARPC * 12 months * 10 years retention
        return arpc * 12 * 10
    
    def _calc_cac(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        # Mock calculation - would need actual acquisition cost data
        return 250.0  # €250 per customer acquisition
    
    def _calc_churn_rate(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        retention_rate = self._calc_retention_rate(conn, start_date, end_date, project_id)
        return 100 - retention_rate
    
    # Energy KPI calculations
    def _calc_energy_sold(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
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
        
        return conn.execute(query, params).fetchone()[0]
    
    def _calc_avg_price_kwh(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        total_revenue = self._calc_total_revenue(conn, start_date, end_date, project_id)
        total_energy = self._calc_energy_sold(conn, start_date, end_date, project_id)
        return total_revenue / total_energy if total_energy > 0 else 0.0
    
    def _calc_energy_efficiency(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
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
    
    def _calc_capacity_utilization(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        # Mock calculation - would need actual capacity data
        return 75.5  # 75.5% capacity utilization
    
    def _calc_peak_demand_coverage(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        # Mock calculation - would need peak demand data
        return 92.3  # 92.3% peak demand coverage
    
    # Risk KPI calculations
    def _calc_overdue_ratio(self, conn: sqlite3.Connection, end_date: date, project_id: Optional[int]) -> float:
        query = """
        SELECT 
            COUNT(*) as total_invoices,
            SUM(CASE WHEN payment_due_date < date('now') AND status != 'paid' THEN 1 ELSE 0 END) as overdue_count
        FROM billing_periods WHERE end_date <= ?
        """
        params = [end_date]
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        
        result = conn.execute(query, params).fetchone()
        total, overdue = result if result else (0, 0)
        return (overdue / total * 100) if total > 0 else 0.0
    
    def _calc_bad_debt_ratio(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        query = """
        SELECT 
            COALESCE(SUM(total_amount), 0) as total_billed,
            COALESCE(SUM(CASE WHEN payment_due_date < date('now', '-90 days') AND status != 'paid' THEN total_amount ELSE 0 END), 0) as bad_debt
        FROM billing_periods WHERE start_date >= ? AND end_date <= ?
        """
        params = [start_date, end_date]
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        
        result = conn.execute(query, params).fetchone()
        total_billed, bad_debt = result if result else (0, 0)
        return (bad_debt / total_billed * 100) if total_billed > 0 else 0.0
    
    def _calc_concentration_risk(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        # Calculate customer concentration (top customer % of total revenue)
        query = """
        SELECT MAX(customer_revenue) / SUM(customer_revenue) * 100 as concentration
        FROM (
            SELECT SUM(bp.total_amount) as customer_revenue
            FROM billing_periods bp
            JOIN participants p ON bp.project_id = p.project_id
            WHERE bp.start_date >= ? AND bp.end_date <= ?
        """
        params = [start_date, end_date]
        if project_id:
            query += " AND bp.project_id = ?"
            params.append(project_id)
        query += " GROUP BY p.id)"
        
        result = conn.execute(query, params).fetchone()
        return result[0] if result and result[0] else 0.0
    
    def _calc_credit_risk_score(self, conn: sqlite3.Connection, end_date: date, project_id: Optional[int]) -> float:
        # Composite risk score (lower is better)
        overdue_ratio = self._calc_overdue_ratio(conn, end_date, project_id)
        bad_debt_ratio = self._calc_bad_debt_ratio(conn, end_date - timedelta(days=365), end_date, project_id)
        
        # Weighted risk score (0-100, lower is better)
        risk_score = (overdue_ratio * 0.6) + (bad_debt_ratio * 0.4)
        return min(100, max(0, risk_score))
    
    # Cash Flow KPI calculations
    def _calc_operating_cash_flow(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        collected_revenue = self._calc_total_revenue(conn, start_date, end_date, project_id) * 0.95  # Assume 95% collected
        estimated_costs = collected_revenue * 0.25  # 25% operating costs
        return collected_revenue - estimated_costs
    
    def _calc_free_cash_flow(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        operating_cf = self._calc_operating_cash_flow(conn, start_date, end_date, project_id)
        estimated_capex = operating_cf * 0.05  # 5% capex
        return operating_cf - estimated_capex
    
    def _calc_cash_conversion_cycle(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        dso = self._calc_dso(conn, end_date, project_id)
        # Simplified: just DSO since we don't have inventory or payables
        return dso
    
    def _calc_working_capital(self, conn: sqlite3.Connection, end_date: date, project_id: Optional[int]) -> float:
        # Mock calculation - would need actual balance sheet data
        return 25000.0  # €25,000 working capital
    
    # Growth KPI calculations
    def _calc_customer_growth_rate(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        start_customers = self._calc_active_customers(conn, start_date, project_id)
        end_customers = self._calc_active_customers(conn, end_date, project_id)
        return ((end_customers - start_customers) / start_customers * 100) if start_customers > 0 else 0.0
    
    def _calc_revenue_per_kwh_growth(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        current_price = self._calc_avg_price_kwh(conn, start_date, end_date, project_id)
        
        # Compare with previous period
        period_days = (end_date - start_date).days
        prev_start = start_date - timedelta(days=period_days)
        prev_end = start_date
        previous_price = self._calc_avg_price_kwh(conn, prev_start, prev_end, project_id)
        
        return ((current_price - previous_price) / previous_price * 100) if previous_price > 0 else 0.0
    
    def _calc_market_share(self, conn: sqlite3.Connection, start_date: date, end_date: date, project_id: Optional[int]) -> float:
        # Mock calculation - would need market data
        return 12.5  # 12.5% market share
    
    # Helper methods
    
    def _initialize_kpi_definitions(self) -> Dict[str, KPIDefinition]:
        """Initialize all KPI definitions"""
        return {
            # Financial KPIs
            'total_revenue': KPIDefinition(
                name='Total Revenue',
                category=KPICategory.FINANCIAL,
                description='Total revenue generated during the period',
                formula='SUM(billing_periods.total_amount)',
                unit='€',
                good_threshold=50000,
                excellent_threshold=100000,
                format_pattern='{:,.2f} €',
                dependencies=['billing_periods']
            ),
            'monthly_recurring_revenue': KPIDefinition(
                name='Monthly Recurring Revenue',
                category=KPICategory.FINANCIAL,
                description='Predictable monthly revenue',
                formula='Average monthly revenue over last 3 months',
                unit='€',
                good_threshold=15000,
                excellent_threshold=25000,
                format_pattern='{:,.2f} €',
                dependencies=['billing_periods']
            ),
            'average_revenue_per_customer': KPIDefinition(
                name='Average Revenue Per Customer',
                category=KPICategory.FINANCIAL,
                description='Average revenue generated per customer',
                formula='Total Revenue / Active Customers',
                unit='€',
                good_threshold=1000,
                excellent_threshold=2000,
                format_pattern='{:,.2f} €',
                dependencies=['billing_periods', 'participants']
            ),
            'revenue_growth_rate': KPIDefinition(
                name='Revenue Growth Rate',
                category=KPICategory.GROWTH,
                description='Period-over-period revenue growth',
                formula='(Current Revenue - Previous Revenue) / Previous Revenue * 100',
                unit='%',
                good_threshold=5.0,
                excellent_threshold=15.0,
                format_pattern='{:.1f}%',
                dependencies=['billing_periods']
            ),
            'gross_margin': KPIDefinition(
                name='Gross Margin',
                category=KPICategory.FINANCIAL,
                description='Gross profit margin percentage',
                formula='(Revenue - COGS) / Revenue * 100',
                unit='%',
                good_threshold=70.0,
                excellent_threshold=85.0,
                format_pattern='{:.1f}%',
                dependencies=['billing_periods']
            ),
            'ebitda': KPIDefinition(
                name='EBITDA',
                category=KPICategory.FINANCIAL,
                description='Earnings before interest, taxes, depreciation, and amortization',
                formula='Revenue - Operating Expenses',
                unit='€',
                good_threshold=30000,
                excellent_threshold=60000,
                format_pattern='{:,.2f} €',
                dependencies=['billing_periods']
            ),
            
            # Operational KPIs
            'collection_rate': KPIDefinition(
                name='Collection Rate',
                category=KPICategory.OPERATIONAL,
                description='Percentage of invoices successfully collected',
                formula='Collected Amount / Billed Amount * 100',
                unit='%',
                good_threshold=90.0,
                excellent_threshold=95.0,
                format_pattern='{:.1f}%',
                dependencies=['billing_periods']
            ),
            'days_sales_outstanding': KPIDefinition(
                name='Days Sales Outstanding',
                category=KPICategory.OPERATIONAL,
                description='Average days to collect payment',
                formula='Average payment collection time',
                unit='days',
                good_threshold=30.0,
                excellent_threshold=15.0,
                format_pattern='{:.1f} days',
                is_higher_better=False,
                dependencies=['billing_periods']
            ),
            'payment_cycle_efficiency': KPIDefinition(
                name='Payment Cycle Efficiency',
                category=KPICategory.OPERATIONAL,
                description='Percentage of payments received on time',
                formula='On-time Payments / Total Payments * 100',
                unit='%',
                good_threshold=85.0,
                excellent_threshold=95.0,
                format_pattern='{:.1f}%',
                dependencies=['billing_periods']
            ),
            
            # Customer KPIs
            'total_customers': KPIDefinition(
                name='Total Customers',
                category=KPICategory.CUSTOMER,
                description='Total number of customers',
                formula='COUNT(participants WHERE type=consumer)',
                unit='count',
                good_threshold=25,
                excellent_threshold=50,
                format_pattern='{:.0f}',
                dependencies=['participants']
            ),
            'active_customers': KPIDefinition(
                name='Active Customers',
                category=KPICategory.CUSTOMER,
                description='Number of customers with recent activity',
                formula='COUNT(participants with recent consumption)',
                unit='count',
                good_threshold=20,
                excellent_threshold=40,
                format_pattern='{:.0f}',
                dependencies=['participants', 'monthly_consumption']
            ),
            'customer_retention_rate': KPIDefinition(
                name='Customer Retention Rate',
                category=KPICategory.CUSTOMER,
                description='Percentage of customers retained',
                formula='End Customers / Start Customers * 100',
                unit='%',
                good_threshold=90.0,
                excellent_threshold=95.0,
                format_pattern='{:.1f}%',
                dependencies=['participants', 'monthly_consumption']
            ),
            'customer_lifetime_value': KPIDefinition(
                name='Customer Lifetime Value',
                category=KPICategory.CUSTOMER,
                description='Estimated total value per customer',
                formula='ARPC * Expected Lifetime',
                unit='€',
                good_threshold=10000,
                excellent_threshold=20000,
                format_pattern='{:,.2f} €',
                dependencies=['billing_periods', 'participants']
            ),
            
            # Energy KPIs
            'energy_sold': KPIDefinition(
                name='Energy Sold',
                category=KPICategory.ENERGY,
                description='Total energy sold to customers',
                formula='SUM(monthly_consumption.autoconsumption_kwh)',
                unit='kWh',
                good_threshold=40000,
                excellent_threshold=80000,
                format_pattern='{:,.0f} kWh',
                dependencies=['monthly_consumption']
            ),
            'average_price_per_kwh': KPIDefinition(
                name='Average Price per kWh',
                category=KPICategory.ENERGY,
                description='Average selling price per kilowatt-hour',
                formula='Total Revenue / Energy Sold',
                unit='€/kWh',
                good_threshold=0.10,
                excellent_threshold=0.15,
                format_pattern='{:.4f} €/kWh',
                dependencies=['billing_periods', 'monthly_consumption']
            ),
            'energy_efficiency_ratio': KPIDefinition(
                name='Energy Efficiency Ratio',
                category=KPICategory.ENERGY,
                description='Ratio of consumed to produced energy',
                formula='Autoconsumption / Total Production * 100',
                unit='%',
                good_threshold=70.0,
                excellent_threshold=85.0,
                format_pattern='{:.1f}%',
                dependencies=['monthly_production', 'monthly_consumption']
            ),
            
            # Risk KPIs
            'overdue_ratio': KPIDefinition(
                name='Overdue Ratio',
                category=KPICategory.RISK,
                description='Percentage of overdue invoices',
                formula='Overdue Invoices / Total Invoices * 100',
                unit='%',
                good_threshold=5.0,
                excellent_threshold=2.0,
                format_pattern='{:.1f}%',
                is_higher_better=False,
                dependencies=['billing_periods']
            ),
            'bad_debt_ratio': KPIDefinition(
                name='Bad Debt Ratio',
                category=KPICategory.RISK,
                description='Percentage of revenue written off as bad debt',
                formula='Bad Debt / Total Revenue * 100',
                unit='%',
                good_threshold=2.0,
                excellent_threshold=1.0,
                format_pattern='{:.1f}%',
                is_higher_better=False,
                dependencies=['billing_periods']
            ),
            
            # Cash Flow KPIs
            'operating_cash_flow': KPIDefinition(
                name='Operating Cash Flow',
                category=KPICategory.FINANCIAL,
                description='Cash flow from operations',
                formula='Collected Revenue - Operating Expenses',
                unit='€',
                good_threshold=25000,
                excellent_threshold=50000,
                format_pattern='{:,.2f} €',
                dependencies=['billing_periods']
            ),
            'free_cash_flow': KPIDefinition(
                name='Free Cash Flow',
                category=KPICategory.FINANCIAL,
                description='Cash available after all expenses',
                formula='Operating Cash Flow - Capital Expenditures',
                unit='€',
                good_threshold=20000,
                excellent_threshold=40000,
                format_pattern='{:,.2f} €',
                dependencies=['billing_periods']
            )
        }
    
    def _load_benchmarks(self) -> None:
        """Load industry and historical benchmarks"""
        # Industry benchmarks (would typically come from external sources)
        industry_benchmarks = {
            'collection_rate': 92.5,
            'days_sales_outstanding': 35.0,
            'customer_retention_rate': 88.0,
            'energy_efficiency_ratio': 75.0,
            'overdue_ratio': 8.5,
            'revenue_growth_rate': 7.2
        }
        
        for kpi_name, value in industry_benchmarks.items():
            benchmark = KPIBenchmark(
                benchmark_type=BenchmarkType.INDUSTRY,
                value=value,
                source="Industry Average",
                date_collected=date.today(),
                confidence_level=0.8
            )
            self.add_benchmark(kpi_name, benchmark)
        
        # Target benchmarks
        target_benchmarks = {
            'collection_rate': 95.0,
            'days_sales_outstanding': 25.0,
            'customer_retention_rate': 95.0,
            'energy_efficiency_ratio': 85.0,
            'overdue_ratio': 3.0,
            'revenue_growth_rate': 15.0
        }
        
        for kpi_name, value in target_benchmarks.items():
            benchmark = KPIBenchmark(
                benchmark_type=BenchmarkType.TARGET,
                value=value,
                source="Company Target",
                date_collected=date.today(),
                confidence_level=1.0
            )
            self.add_benchmark(kpi_name, benchmark)
    
    def _format_kpi_value(self, value: float, definition: KPIDefinition) -> str:
        """Format KPI value according to definition"""
        try:
            return definition.format_pattern.format(value)
        except:
            return f"{value:.2f}"
    
    def _get_performance_rating(self, kpi_name: str, value: float) -> str:
        """Get performance rating for KPI value"""
        definition = self.kpi_definitions.get(kpi_name)
        if not definition:
            return "fair"
        
        if definition.is_higher_better:
            if value >= definition.excellent_threshold:
                return "excellent"
            elif value >= definition.good_threshold:
                return "good"
            elif value >= definition.good_threshold * 0.7:
                return "fair"
            else:
                return "poor"
        else:
            if value <= definition.excellent_threshold:
                return "excellent"
            elif value <= definition.good_threshold:
                return "good"
            elif value <= definition.good_threshold * 1.5:
                return "fair"
            else:
                return "poor"
    
    def _calculate_trend(self, kpi_name: str, current_value: float, start_date: date, end_date: date, project_id: Optional[int]) -> str:
        """Calculate trend direction"""
        try:
            # Get previous period value for comparison
            period_days = (end_date - start_date).days
            prev_start = start_date - timedelta(days=period_days)
            prev_end = start_date
            
            prev_value = self._calculate_kpi_value(kpi_name, prev_start, prev_end, project_id)
            
            if prev_value is None or prev_value == 0:
                return "stable"
            
            change_percent = (current_value - prev_value) / prev_value * 100
            
            if abs(change_percent) < 2:
                return "stable"
            elif change_percent > 0:
                return "up"
            else:
                return "down"
                
        except Exception as e:
            logger.error(f"Error calculating trend for {kpi_name}: {e}")
            return "stable"
    
    def _identify_contributing_factors(self, kpi_name: str, value: float, start_date: date, end_date: date, project_id: Optional[int]) -> List[str]:
        """Identify factors contributing to KPI value"""
        factors = []
        
        # General factors based on KPI category
        definition = self.kpi_definitions.get(kpi_name)
        if not definition:
            return factors
        
        if definition.category == KPICategory.FINANCIAL:
            factors.extend(["Market conditions", "Pricing strategy", "Customer base"])
        elif definition.category == KPICategory.OPERATIONAL:
            factors.extend(["Process efficiency", "System performance", "Staff productivity"])
        elif definition.category == KPICategory.CUSTOMER:
            factors.extend(["Service quality", "Customer satisfaction", "Market competition"])
        elif definition.category == KPICategory.ENERGY:
            factors.extend(["Weather conditions", "Equipment performance", "Demand patterns"])
        elif definition.category == KPICategory.RISK:
            factors.extend(["Economic conditions", "Customer creditworthiness", "Market volatility"])
        
        # Specific factors based on performance
        rating = self._get_performance_rating(kpi_name, value)
        if rating == "excellent":
            factors.append("Strong performance across all metrics")
        elif rating == "poor":
            factors.append("Multiple areas need improvement")
        
        return factors[:3]  # Limit to top 3 factors
    
    def _generate_improvement_suggestions(self, kpi_name: str, value: float, rating: str) -> List[str]:
        """Generate improvement suggestions based on KPI performance"""
        suggestions = []
        
        if rating in ["poor", "fair"]:
            if "collection" in kpi_name.lower():
                suggestions.extend([
                    "Implement automated payment reminders",
                    "Review and improve payment terms",
                    "Consider offering payment incentives"
                ])
            elif "customer" in kpi_name.lower():
                suggestions.extend([
                    "Enhance customer service quality",
                    "Implement customer feedback system",
                    "Develop customer loyalty programs"
                ])
            elif "revenue" in kpi_name.lower():
                suggestions.extend([
                    "Review pricing strategy",
                    "Expand customer base",
                    "Optimize service offerings"
                ])
            elif "energy" in kpi_name.lower():
                suggestions.extend([
                    "Optimize energy distribution",
                    "Improve system efficiency",
                    "Consider equipment upgrades"
                ])
            elif "risk" in kpi_name.lower():
                suggestions.extend([
                    "Strengthen risk management procedures",
                    "Improve customer credit assessment",
                    "Diversify customer portfolio"
                ])
        
        return suggestions[:3]  # Limit to top 3 suggestions
    
    def _get_benchmark_comparisons(self, kpi_name: str, value: float) -> Dict[BenchmarkType, float]:
        """Get benchmark comparisons for KPI"""
        comparisons = {}
        
        if kpi_name in self.benchmarks:
            for benchmark_type, benchmark in self.benchmarks[kpi_name].items():
                # Calculate percentage difference from benchmark
                diff_percent = ((value - benchmark.value) / benchmark.value * 100) if benchmark.value != 0 else 0
                comparisons[benchmark_type] = round(diff_percent, 1)
        
        return comparisons