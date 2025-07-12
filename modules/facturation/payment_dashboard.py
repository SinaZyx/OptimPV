"""
Payment Dashboard Module for OptimPV
Provides KPIs, analytics, and cash flow forecasting for payments
"""

import sqlite3
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
# import pandas as pd  # Désactivé pour éviter les dépendances
from decimal import Decimal

logger = logging.getLogger(__name__)

@dataclass
class DSO:
    """Days Sales Outstanding calculation"""
    period_days: int
    total_receivables: float
    total_sales: float
    dso_days: float
    
@dataclass
class AgingBucket:
    """Aging bucket for receivables"""
    bucket_name: str
    min_days: int
    max_days: Optional[int]
    count: int
    total_amount: float
    percentage: float

@dataclass
class CashFlowForecast:
    """Cash flow forecast item"""
    date: date
    expected_receipts: float
    overdue_amount: float
    confidence_level: str  # high, medium, low
    notes: str

@dataclass
class CollectionMetrics:
    """Collection performance metrics"""
    total_invoiced: float
    total_collected: float
    collection_rate: float
    average_collection_period: float
    bad_debt_rate: float

class PaymentDashboard:
    """Payment dashboard with KPIs and analytics"""
    
    def __init__(self, db_path: str = "data/billing.db"):
        """Initialize payment dashboard"""
        self.db_path = db_path
        
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ===== DSO (Days Sales Outstanding) =====
    
    def calculate_dso(self, period_days: int = 90) -> DSO:
        """
        Calculate Days Sales Outstanding (DSO)
        DSO = (Average Accounts Receivable / Net Credit Sales) × Number of Days
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total receivables (unpaid invoices)
            cursor.execute("""
                SELECT COALESCE(SUM(i.total_amount - COALESCE(p.total_paid, 0)), 0) as total_receivables
                FROM invoices i
                LEFT JOIN (
                    SELECT invoice_id, SUM(amount) as total_paid
                    FROM payments
                    GROUP BY invoice_id
                ) p ON i.id = p.invoice_id
                WHERE i.status IN ('sent', 'overdue', 'partially_paid')
            """)
            total_receivables = cursor.fetchone()[0]
            
            # Get total sales for the period
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0) as total_sales
                FROM invoices
                WHERE issue_date >= ? AND issue_date <= ?
                AND status != 'cancelled'
            """, (start_date.isoformat(), end_date.isoformat()))
            total_sales = cursor.fetchone()[0]
            
            # Calculate DSO
            dso_days = 0.0
            if total_sales > 0:
                dso_days = (total_receivables / total_sales) * period_days
            
            return DSO(
                period_days=period_days,
                total_receivables=total_receivables,
                total_sales=total_sales,
                dso_days=round(dso_days, 1)
            )
    
    def get_dso_trend(self, months: int = 12) -> List[Dict[str, Any]]:
        """Get DSO trend over time"""
        trends = []
        
        for i in range(months):
            end_date = date.today().replace(day=1) - timedelta(days=i*30)
            start_date = end_date - timedelta(days=90)  # 90-day DSO calculation
            
            # Calculate DSO for this period
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Receivables at end of period
                cursor.execute("""
                    SELECT COALESCE(SUM(i.total_amount - COALESCE(p.total_paid, 0)), 0)
                    FROM invoices i
                    LEFT JOIN (
                        SELECT invoice_id, SUM(amount) as total_paid
                        FROM payments
                        WHERE payment_date <= ?
                        GROUP BY invoice_id
                    ) p ON i.id = p.invoice_id
                    WHERE i.issue_date <= ?
                    AND i.status IN ('sent', 'overdue', 'partially_paid', 'paid')
                """, (end_date.isoformat(), end_date.isoformat()))
                receivables = cursor.fetchone()[0]
                
                # Sales for the 90-day period
                cursor.execute("""
                    SELECT COALESCE(SUM(total_amount), 0)
                    FROM invoices
                    WHERE issue_date >= ? AND issue_date <= ?
                    AND status != 'cancelled'
                """, (start_date.isoformat(), end_date.isoformat()))
                sales = cursor.fetchone()[0]
                
                dso = (receivables / sales * 90) if sales > 0 else 0
                
                trends.append({
                    'period': end_date.strftime('%Y-%m'),
                    'dso_days': round(dso, 1),
                    'receivables': receivables,
                    'sales': sales
                })
        
        return list(reversed(trends))
    
    # ===== Aging Analysis =====
    
    def calculate_aging_buckets(self) -> List[AgingBucket]:
        """Calculate aging buckets for receivables"""
        buckets_config = [
            ("0-30 jours", 0, 30),
            ("31-60 jours", 31, 60),
            ("61-90 jours", 61, 90),
            ("91+ jours", 91, None)
        ]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all unpaid invoices with aging
            cursor.execute("""
                SELECT 
                    i.id,
                    i.total_amount,
                    COALESCE(p.total_paid, 0) as total_paid,
                    JULIANDAY('now') - JULIANDAY(i.due_date) as days_overdue
                FROM invoices i
                LEFT JOIN (
                    SELECT invoice_id, SUM(amount) as total_paid
                    FROM payments
                    GROUP BY invoice_id
                ) p ON i.id = p.invoice_id
                WHERE i.status IN ('sent', 'overdue', 'partially_paid')
                AND i.total_amount > COALESCE(p.total_paid, 0)
            """)
            
            unpaid_invoices = cursor.fetchall()
            total_amount = sum(row[0] - row[1] for row in unpaid_invoices)
            
            buckets = []
            
            for bucket_name, min_days, max_days in buckets_config:
                bucket_invoices = []
                
                for invoice in unpaid_invoices:
                    outstanding = invoice[0] - invoice[1]  # total - paid
                    days_overdue = max(0, invoice[3])  # days overdue (0 if not overdue)
                    
                    if max_days is None:
                        if days_overdue >= min_days:
                            bucket_invoices.append(outstanding)
                    else:
                        if min_days <= days_overdue <= max_days:
                            bucket_invoices.append(outstanding)
                
                bucket_amount = sum(bucket_invoices)
                bucket_percentage = (bucket_amount / total_amount * 100) if total_amount > 0 else 0
                
                buckets.append(AgingBucket(
                    bucket_name=bucket_name,
                    min_days=min_days,
                    max_days=max_days,
                    count=len(bucket_invoices),
                    total_amount=bucket_amount,
                    percentage=round(bucket_percentage, 1)
                ))
            
            return buckets
    
    def get_aging_detail(self, min_days: int, max_days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get detailed aging for specific bucket"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    i.id,
                    i.invoice_number,
                    i.issue_date,
                    i.due_date,
                    i.total_amount,
                    COALESCE(p.total_paid, 0) as total_paid,
                    i.total_amount - COALESCE(p.total_paid, 0) as outstanding,
                    JULIANDAY('now') - JULIANDAY(i.due_date) as days_overdue,
                    part.name as participant_name,
                    proj.name as project_name
                FROM invoices i
                LEFT JOIN (
                    SELECT invoice_id, SUM(amount) as total_paid
                    FROM payments
                    GROUP BY invoice_id
                ) p ON i.id = p.invoice_id
                JOIN participants part ON i.participant_id = part.id
                JOIN billing_periods bp ON i.billing_period_id = bp.id
                JOIN projects proj ON bp.project_id = proj.id
                WHERE i.status IN ('sent', 'overdue', 'partially_paid')
                AND i.total_amount > COALESCE(p.total_paid, 0)
            """)
            
            all_invoices = cursor.fetchall()
            filtered_invoices = []
            
            for invoice in all_invoices:
                days_overdue = max(0, invoice[7])
                
                if max_days is None:
                    if days_overdue >= min_days:
                        filtered_invoices.append(dict(invoice))
                else:
                    if min_days <= days_overdue <= max_days:
                        filtered_invoices.append(dict(invoice))
            
            return filtered_invoices
    
    # ===== Collection Rate =====
    
    def calculate_collection_rate(self, period_days: int = 90) -> CollectionMetrics:
        """Calculate collection performance metrics"""
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total invoiced in period
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0)
                FROM invoices
                WHERE issue_date >= ? AND issue_date <= ?
                AND status != 'cancelled'
            """, (start_date.isoformat(), end_date.isoformat()))
            total_invoiced = cursor.fetchone()[0]
            
            # Total collected for invoices issued in period
            cursor.execute("""
                SELECT COALESCE(SUM(p.amount), 0)
                FROM payments p
                JOIN invoices i ON p.invoice_id = i.id
                WHERE i.issue_date >= ? AND i.issue_date <= ?
                AND i.status != 'cancelled'
            """, (start_date.isoformat(), end_date.isoformat()))
            total_collected = cursor.fetchone()[0]
            
            # Collection rate
            collection_rate = (total_collected / total_invoiced * 100) if total_invoiced > 0 else 0
            
            # Average collection period
            cursor.execute("""
                SELECT AVG(JULIANDAY(p.payment_date) - JULIANDAY(i.issue_date)) as avg_collection_days
                FROM payments p
                JOIN invoices i ON p.invoice_id = i.id
                WHERE i.issue_date >= ? AND i.issue_date <= ?
                AND i.status = 'paid'
            """, (start_date.isoformat(), end_date.isoformat()))
            avg_collection_period = cursor.fetchone()[0] or 0
            
            # Bad debt (invoices older than 120 days and still unpaid)
            bad_debt_date = end_date - timedelta(days=120)
            cursor.execute("""
                SELECT COALESCE(SUM(i.total_amount - COALESCE(p.total_paid, 0)), 0)
                FROM invoices i
                LEFT JOIN (
                    SELECT invoice_id, SUM(amount) as total_paid
                    FROM payments
                    GROUP BY invoice_id
                ) p ON i.id = p.invoice_id
                WHERE i.issue_date <= ?
                AND i.status IN ('sent', 'overdue')
                AND i.total_amount > COALESCE(p.total_paid, 0)
            """, (bad_debt_date.isoformat(),))
            bad_debt_amount = cursor.fetchone()[0]
            
            bad_debt_rate = (bad_debt_amount / total_invoiced * 100) if total_invoiced > 0 else 0
            
            return CollectionMetrics(
                total_invoiced=total_invoiced,
                total_collected=total_collected,
                collection_rate=round(collection_rate, 2),
                average_collection_period=round(avg_collection_period, 1),
                bad_debt_rate=round(bad_debt_rate, 2)
            )
    
    # ===== Cash Flow Forecasting =====
    
    def generate_cash_flow_forecast(self, forecast_days: int = 90) -> List[CashFlowForecast]:
        """Generate cash flow forecast based on payment patterns"""
        forecast = []
        today = date.today()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get historical payment patterns
            cursor.execute("""
                SELECT 
                    AVG(JULIANDAY(payment_date) - JULIANDAY(due_date)) as avg_delay,
                    COUNT(*) as payment_count
                FROM invoices
                WHERE status = 'paid' AND payment_date IS NOT NULL
                AND issue_date >= date('now', '-365 days')
            """)
            
            historical_data = cursor.fetchone()
            avg_delay = historical_data[0] or 0
            payment_count = historical_data[1] or 0
            
            # Get unpaid invoices
            cursor.execute("""
                SELECT 
                    i.id,
                    i.due_date,
                    i.total_amount - COALESCE(p.total_paid, 0) as outstanding,
                    JULIANDAY('now') - JULIANDAY(i.due_date) as days_overdue,
                    i.status
                FROM invoices i
                LEFT JOIN (
                    SELECT invoice_id, SUM(amount) as total_paid
                    FROM payments
                    GROUP BY invoice_id
                ) p ON i.id = p.invoice_id
                WHERE i.status IN ('sent', 'overdue', 'partially_paid')
                AND i.total_amount > COALESCE(p.total_paid, 0)
            """)
            
            unpaid_invoices = cursor.fetchall()
            
            # Create daily forecast
            for days_ahead in range(forecast_days + 1):
                forecast_date = today + timedelta(days=days_ahead)
                expected_receipts = 0.0
                overdue_amount = 0.0
                confidence = "high"
                
                for invoice in unpaid_invoices:
                    due_date = datetime.fromisoformat(invoice[1]).date()
                    outstanding = invoice[2]
                    days_overdue = invoice[3]
                    status = invoice[4]
                    
                    # Calculate expected payment date based on historical patterns
                    expected_payment_date = due_date + timedelta(days=avg_delay)
                    
                    # Adjust confidence based on age and status
                    if days_overdue > 60:
                        confidence = "low"
                        probability = 0.3  # 30% chance of payment
                    elif days_overdue > 30:
                        confidence = "medium"
                        probability = 0.6  # 60% chance of payment
                    elif status == 'overdue':
                        confidence = "medium"
                        probability = 0.8  # 80% chance of payment
                    else:
                        probability = 0.9  # 90% chance of payment
                    
                    # Add to forecast if expected on this date
                    if expected_payment_date == forecast_date:
                        expected_receipts += outstanding * probability
                    
                    # Add to overdue if past due
                    if due_date < forecast_date and days_overdue > 0:
                        overdue_amount += outstanding
                
                if expected_receipts > 0 or overdue_amount > 0:
                    forecast.append(CashFlowForecast(
                        date=forecast_date,
                        expected_receipts=round(expected_receipts, 2),
                        overdue_amount=round(overdue_amount, 2),
                        confidence_level=confidence,
                        notes=f"Basé sur {payment_count} paiements historiques"
                    ))
            
            return forecast
    
    def get_weekly_cash_flow_summary(self, weeks: int = 12) -> List[Dict[str, Any]]:
        """Get weekly cash flow summary"""
        forecast = self.generate_cash_flow_forecast(weeks * 7)
        weekly_summary = []
        
        # Group by weeks
        current_week_start = date.today() - timedelta(days=date.today().weekday())
        
        for week in range(weeks):
            week_start = current_week_start + timedelta(weeks=week)
            week_end = week_start + timedelta(days=6)
            
            week_receipts = sum(
                f.expected_receipts for f in forecast 
                if week_start <= f.date <= week_end
            )
            
            week_overdue = sum(
                f.overdue_amount for f in forecast 
                if week_start <= f.date <= week_end
            )
            
            weekly_summary.append({
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'expected_receipts': round(week_receipts, 2),
                'overdue_amount': round(week_overdue, 2),
                'week_number': week + 1
            })
        
        return weekly_summary
    
    # ===== Payment Method Analytics =====
    
    def get_payment_method_analytics(self) -> Dict[str, Any]:
        """Get payment method usage and performance analytics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Payment method distribution
            cursor.execute("""
                SELECT 
                    payment_method,
                    COUNT(*) as count,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount
                FROM payments
                WHERE payment_method IS NOT NULL
                AND payment_date >= date('now', '-365 days')
                GROUP BY payment_method
                ORDER BY total_amount DESC
            """)
            
            method_stats = {}
            total_amount = 0
            total_count = 0
            
            for row in cursor.fetchall():
                method = row[0]
                count = row[1]
                amount = row[2]
                avg_amount = row[3]
                
                total_amount += amount
                total_count += count
                
                method_stats[method] = {
                    'count': count,
                    'total_amount': amount,
                    'average_amount': round(avg_amount, 2),
                    'percentage': 0  # Will be calculated below
                }
            
            # Calculate percentages
            for method in method_stats:
                method_stats[method]['percentage'] = round(
                    (method_stats[method]['total_amount'] / total_amount * 100), 2
                ) if total_amount > 0 else 0
            
            # Payment timing by method
            cursor.execute("""
                SELECT 
                    payment_method,
                    AVG(JULIANDAY(payment_date) - JULIANDAY(i.due_date)) as avg_delay_days
                FROM payments p
                JOIN invoices i ON p.invoice_id = i.id
                WHERE p.payment_method IS NOT NULL
                AND p.payment_date >= date('now', '-365 days')
                GROUP BY payment_method
            """)
            
            timing_stats = {}
            for row in cursor.fetchall():
                timing_stats[row[0]] = round(row[1], 1)
            
            return {
                'payment_method_distribution': method_stats,
                'average_delay_by_method': timing_stats,
                'total_payments': total_count,
                'total_amount': total_amount
            }
    
    # ===== KPI Summary =====
    
    def get_payment_kpis(self) -> Dict[str, Any]:
        """Get comprehensive payment KPIs dashboard"""
        dso = self.calculate_dso()
        aging_buckets = self.calculate_aging_buckets()
        collection_metrics = self.calculate_collection_rate()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Current receivables
            cursor.execute("""
                SELECT COALESCE(SUM(i.total_amount - COALESCE(p.total_paid, 0)), 0)
                FROM invoices i
                LEFT JOIN (
                    SELECT invoice_id, SUM(amount) as total_paid
                    FROM payments
                    GROUP BY invoice_id
                ) p ON i.id = p.invoice_id
                WHERE i.status IN ('sent', 'overdue', 'partially_paid')
            """)
            current_receivables = cursor.fetchone()[0]
            
            # Overdue amount
            cursor.execute("""
                SELECT COALESCE(SUM(i.total_amount - COALESCE(p.total_paid, 0)), 0)
                FROM invoices i
                LEFT JOIN (
                    SELECT invoice_id, SUM(amount) as total_paid
                    FROM payments
                    GROUP BY invoice_id
                ) p ON i.id = p.invoice_id
                WHERE i.status IN ('sent', 'overdue', 'partially_paid')
                AND i.due_date < date('now')
            """)
            overdue_amount = cursor.fetchone()[0]
            
            # This month's collections
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM payments
                WHERE payment_date >= date('now', 'start of month')
            """)
            monthly_collections = cursor.fetchone()[0]
            
            return {
                'dso_days': dso.dso_days,
                'current_receivables': current_receivables,
                'overdue_amount': overdue_amount,
                'overdue_percentage': round((overdue_amount / current_receivables * 100), 2) if current_receivables > 0 else 0,
                'collection_rate': collection_metrics.collection_rate,
                'monthly_collections': monthly_collections,
                'aging_buckets': [
                    {
                        'name': bucket.bucket_name,
                        'amount': bucket.total_amount,
                        'percentage': bucket.percentage,
                        'count': bucket.count
                    } for bucket in aging_buckets
                ],
                'bad_debt_rate': collection_metrics.bad_debt_rate,
                'average_collection_period': collection_metrics.average_collection_period
            }
    
    # ===== Export Functions =====
    
    def export_aging_report(self, format: str = 'dict') -> Dict[str, Any]:
        """Export comprehensive aging report"""
        aging_buckets = self.calculate_aging_buckets()
        
        report_data = {
            'report_date': date.today().isoformat(),
            'total_receivables': sum(bucket.total_amount for bucket in aging_buckets),
            'buckets': []
        }
        
        for bucket in aging_buckets:
            bucket_detail = self.get_aging_detail(bucket.min_days, bucket.max_days)
            
            report_data['buckets'].append({
                'bucket_name': bucket.bucket_name,
                'total_amount': bucket.total_amount,
                'count': bucket.count,
                'percentage': bucket.percentage,
                'invoices': bucket_detail
            })
        
        return report_data
    
    def export_dso_history(self, months: int = 12) -> List[Dict[str, Any]]:
        """Export DSO trend history"""
        return self.get_dso_trend(months)