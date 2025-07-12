"""
Routes API pour la génération de rapports et analytics
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from datetime import date, datetime, timedelta
import sys
import os
import io
import csv
import json

# Ajouter le chemin des modules
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
if modules_path not in sys.path:
    sys.path.append(modules_path)

from ..schemas.response_schemas import (
    APIResponse, ExportResponse
)

from modules.facturation.database import BillingDatabase

router = APIRouter()

def get_database():
    """Dependency pour obtenir une instance de la base de données"""
    return BillingDatabase()

@router.get("/dashboard", response_model=APIResponse[Dict[str, Any]])
async def get_dashboard_data(
    project_id: Optional[int] = Query(None, description="Filtrer par projet"),
    period_months: int = Query(12, ge=1, le=60, description="Période en mois"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer les données du tableau de bord
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Calculer la date de début de période
            end_date = date.today()
            start_date = end_date - timedelta(days=period_months * 30)
            
            # Filtrage par projet
            project_filter = ""
            params = [start_date.isoformat(), end_date.isoformat()]
            if project_id:
                project_filter = " AND bp.project_id = ?"
                params.append(project_id)
            
            # Métriques principales
            cursor.execute(f"""
                SELECT 
                    COUNT(DISTINCT pr.id) as total_projects,
                    COUNT(DISTINCT pt.id) as total_participants,
                    COUNT(DISTINCT i.id) as total_invoices,
                    COALESCE(SUM(i.total_amount), 0) as total_invoiced,
                    COALESCE(SUM(p.amount), 0) as total_collected,
                    COUNT(DISTINCT CASE WHEN i.status = 'overdue' THEN i.id END) as overdue_invoices,
                    COALESCE(SUM(CASE WHEN i.status = 'overdue' THEN i.total_amount ELSE 0 END), 0) as overdue_amount
                FROM projects pr
                LEFT JOIN billing_periods bp ON pr.id = bp.project_id
                LEFT JOIN invoices i ON bp.id = i.billing_period_id 
                    AND i.issue_date BETWEEN ? AND ?
                LEFT JOIN participants pt ON pr.id = pt.project_id
                LEFT JOIN payments p ON i.id = p.invoice_id
                WHERE 1=1 {project_filter}
            """, params)
            
            metrics = dict(cursor.fetchone())
            
            # Calculs dérivés
            collection_rate = 0
            if metrics['total_invoiced'] > 0:
                collection_rate = (metrics['total_collected'] / metrics['total_invoiced']) * 100
            
            # Évolution mensuelle
            cursor.execute(f"""
                SELECT 
                    strftime('%Y-%m', i.issue_date) as month,
                    COUNT(i.id) as invoice_count,
                    COALESCE(SUM(i.total_amount), 0) as invoiced_amount,
                    COALESCE(SUM(p.amount), 0) as collected_amount
                FROM invoices i
                JOIN billing_periods bp ON i.billing_period_id = bp.id
                LEFT JOIN payments p ON i.id = p.invoice_id 
                    AND p.payment_date BETWEEN ? AND ?
                WHERE i.issue_date BETWEEN ? AND ? {project_filter}
                GROUP BY strftime('%Y-%m', i.issue_date)
                ORDER BY month
            """, params + params)
            
            monthly_evolution = [
                {
                    "month": row[0],
                    "invoice_count": row[1],
                    "invoiced_amount": row[2],
                    "collected_amount": row[3]
                }
                for row in cursor.fetchall()
            ]
            
            # Top participants par chiffre d'affaires
            cursor.execute(f"""
                SELECT 
                    pt.name,
                    COUNT(i.id) as invoice_count,
                    COALESCE(SUM(i.total_amount), 0) as total_amount,
                    COALESCE(SUM(p.amount), 0) as paid_amount
                FROM participants pt
                JOIN projects pr ON pt.project_id = pr.id
                LEFT JOIN billing_periods bp ON pr.id = bp.project_id
                LEFT JOIN invoices i ON bp.id = i.billing_period_id 
                    AND pt.id = i.participant_id
                    AND i.issue_date BETWEEN ? AND ?
                LEFT JOIN payments p ON i.id = p.invoice_id
                WHERE 1=1 {project_filter}
                GROUP BY pt.id, pt.name
                HAVING total_amount > 0
                ORDER BY total_amount DESC
                LIMIT 10
            """, params)
            
            top_participants = [
                {
                    "name": row[0],
                    "invoice_count": row[1],
                    "total_amount": row[2],
                    "paid_amount": row[3],
                    "collection_rate": (row[3] / row[2] * 100) if row[2] > 0 else 0
                }
                for row in cursor.fetchall()
            ]
            
            # Répartition par statut de facture
            cursor.execute(f"""
                SELECT 
                    i.status,
                    COUNT(*) as count,
                    COALESCE(SUM(i.total_amount), 0) as amount
                FROM invoices i
                JOIN billing_periods bp ON i.billing_period_id = bp.id
                WHERE i.issue_date BETWEEN ? AND ? {project_filter}
                GROUP BY i.status
            """, params)
            
            status_distribution = {
                row[0]: {"count": row[1], "amount": row[2]}
                for row in cursor.fetchall()
            }
            
            dashboard_data = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "months": period_months
                },
                "metrics": {
                    "total_projects": metrics['total_projects'],
                    "total_participants": metrics['total_participants'],
                    "total_invoices": metrics['total_invoices'],
                    "total_invoiced": metrics['total_invoiced'],
                    "total_collected": metrics['total_collected'],
                    "collection_rate": round(collection_rate, 2),
                    "overdue_invoices": metrics['overdue_invoices'],
                    "overdue_amount": metrics['overdue_amount']
                },
                "monthly_evolution": monthly_evolution,
                "top_participants": top_participants,
                "status_distribution": status_distribution,
                "updated_at": datetime.now().isoformat()
            }
        
        return APIResponse(
            status="success",
            message="Données du tableau de bord récupérées avec succès",
            data=dashboard_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération du tableau de bord: {str(e)}"
        )

@router.get("/aging", response_model=APIResponse[Dict[str, Any]])
async def get_aging_report(
    project_id: Optional[int] = Query(None, description="Filtrer par projet"),
    as_of_date: Optional[date] = Query(None, description="Date de référence (par défaut: aujourd'hui)"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Rapport de balance âgée des créances
    """
    try:
        if not as_of_date:
            as_of_date = date.today()
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Filtrage par projet
            project_filter = ""
            params = [as_of_date.isoformat()]
            if project_id:
                project_filter = " AND bp.project_id = ?"
                params.append(project_id)
            
            # Factures impayées avec âge
            cursor.execute(f"""
                SELECT 
                    i.id,
                    i.invoice_number,
                    pt.name as participant_name,
                    pr.name as project_name,
                    i.issue_date,
                    i.due_date,
                    i.total_amount,
                    COALESCE(SUM(p.amount), 0) as paid_amount,
                    i.total_amount - COALESCE(SUM(p.amount), 0) as balance,
                    julianday(?) - julianday(i.due_date) as days_overdue
                FROM invoices i
                JOIN billing_periods bp ON i.billing_period_id = bp.id
                JOIN projects pr ON bp.project_id = pr.id
                JOIN participants pt ON i.participant_id = pt.id
                LEFT JOIN payments p ON i.id = p.invoice_id
                WHERE i.status IN ('sent', 'overdue')
                    AND i.total_amount > COALESCE(SUM(p.amount), 0)
                    {project_filter}
                GROUP BY i.id
                HAVING balance > 0
                ORDER BY days_overdue DESC, balance DESC
            """, params)
            
            unpaid_invoices = []
            aging_buckets = {
                "current": {"count": 0, "amount": 0},      # 0-30 jours
                "30_60": {"count": 0, "amount": 0},        # 31-60 jours
                "60_90": {"count": 0, "amount": 0},        # 61-90 jours
                "90_plus": {"count": 0, "amount": 0}       # 90+ jours
            }
            
            total_balance = 0
            
            for row in cursor.fetchall():
                invoice_data = {
                    "id": row[0],
                    "invoice_number": row[1],
                    "participant_name": row[2],
                    "project_name": row[3],
                    "issue_date": row[4],
                    "due_date": row[5],
                    "total_amount": row[6],
                    "paid_amount": row[7],
                    "balance": row[8],
                    "days_overdue": int(row[9]) if row[9] else 0
                }
                
                unpaid_invoices.append(invoice_data)
                balance = invoice_data["balance"]
                total_balance += balance
                days_overdue = invoice_data["days_overdue"]
                
                # Classer dans les buckets d'âge
                if days_overdue <= 0:
                    aging_buckets["current"]["count"] += 1
                    aging_buckets["current"]["amount"] += balance
                elif days_overdue <= 60:
                    aging_buckets["30_60"]["count"] += 1
                    aging_buckets["30_60"]["amount"] += balance
                elif days_overdue <= 90:
                    aging_buckets["60_90"]["count"] += 1
                    aging_buckets["60_90"]["amount"] += balance
                else:
                    aging_buckets["90_plus"]["count"] += 1
                    aging_buckets["90_plus"]["amount"] += balance
            
            # Calcul des pourcentages
            for bucket in aging_buckets.values():
                bucket["percentage"] = (bucket["amount"] / total_balance * 100) if total_balance > 0 else 0
            
            aging_report = {
                "as_of_date": as_of_date.isoformat(),
                "summary": {
                    "total_invoices": len(unpaid_invoices),
                    "total_balance": total_balance,
                    "aging_buckets": aging_buckets
                },
                "invoices": unpaid_invoices
            }
        
        return APIResponse(
            status="success",
            message="Rapport de balance âgée généré avec succès",
            data=aging_report
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération du rapport de balance âgée: {str(e)}"
        )

@router.get("/cash-flow", response_model=APIResponse[Dict[str, Any]])
async def get_cash_flow_report(
    start_date: date = Query(..., description="Date de début"),
    end_date: date = Query(..., description="Date de fin"),
    project_id: Optional[int] = Query(None, description="Filtrer par projet"),
    granularity: str = Query("monthly", regex="^(daily|weekly|monthly)$", description="Granularité"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Rapport de flux de trésorerie
    """
    try:
        if end_date <= start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La date de fin doit être postérieure à la date de début"
            )
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Filtrage par projet
            project_filter = ""
            params = [start_date.isoformat(), end_date.isoformat()]
            if project_id:
                project_filter = " AND bp.project_id = ?"
                params.extend([project_id, project_id])
            
            # Format de date selon la granularité
            date_format = {
                "daily": "%Y-%m-%d",
                "weekly": "%Y-W%W",
                "monthly": "%Y-%m"
            }[granularity]
            
            # Flux entrants (paiements reçus)
            cursor.execute(f"""
                SELECT 
                    strftime('{date_format}', p.payment_date) as period,
                    COALESCE(SUM(p.amount), 0) as inflow
                FROM payments p
                JOIN invoices i ON p.invoice_id = i.id
                JOIN billing_periods bp ON i.billing_period_id = bp.id
                WHERE p.payment_date BETWEEN ? AND ? {project_filter}
                GROUP BY strftime('{date_format}', p.payment_date)
                ORDER BY period
            """, params)
            
            inflows = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Flux sortants (factures émises)
            cursor.execute(f"""
                SELECT 
                    strftime('{date_format}', i.issue_date) as period,
                    COALESCE(SUM(i.total_amount), 0) as outflow
                FROM invoices i
                JOIN billing_periods bp ON i.billing_period_id = bp.id
                WHERE i.issue_date BETWEEN ? AND ? {project_filter}
                GROUP BY strftime('{date_format}', i.issue_date)
                ORDER BY period
            """, params)
            
            outflows = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Combiner les périodes
            all_periods = sorted(set(inflows.keys()) | set(outflows.keys()))
            
            cash_flow_data = []
            cumulative_balance = 0
            
            for period in all_periods:
                inflow = inflows.get(period, 0)
                outflow = outflows.get(period, 0)
                net_flow = inflow - outflow
                cumulative_balance += net_flow
                
                cash_flow_data.append({
                    "period": period,
                    "inflow": inflow,
                    "outflow": outflow,
                    "net_flow": net_flow,
                    "cumulative_balance": cumulative_balance
                })
            
            # Statistiques de résumé
            total_inflow = sum(inflows.values())
            total_outflow = sum(outflows.values())
            net_total = total_inflow - total_outflow
            
            cash_flow_report = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "granularity": granularity
                },
                "summary": {
                    "total_inflow": total_inflow,
                    "total_outflow": total_outflow,
                    "net_total": net_total,
                    "periods_count": len(cash_flow_data)
                },
                "cash_flow": cash_flow_data
            }
        
        return APIResponse(
            status="success",
            message="Rapport de flux de trésorerie généré avec succès",
            data=cash_flow_report
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération du rapport de flux de trésorerie: {str(e)}"
        )

@router.get("/export/invoices")
async def export_invoices(
    format: str = Query("csv", regex="^(csv|xlsx|json)$", description="Format d'export"),
    start_date: Optional[date] = Query(None, description="Date de début"),
    end_date: Optional[date] = Query(None, description="Date de fin"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    project_id: Optional[int] = Query(None, description="Filtrer par projet"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Exporter les factures dans différents formats
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Construction de la requête avec filtres
            query = """
                SELECT 
                    i.id,
                    i.invoice_number,
                    i.issue_date,
                    i.due_date,
                    i.subtotal,
                    i.tax_rate,
                    i.tax_amount,
                    i.total_amount,
                    i.status,
                    i.payment_date,
                    pt.name as participant_name,
                    pt.type as participant_type,
                    pr.name as project_name,
                    pr.client_name,
                    COALESCE(SUM(p.amount), 0) as paid_amount,
                    i.total_amount - COALESCE(SUM(p.amount), 0) as balance
                FROM invoices i
                JOIN billing_periods bp ON i.billing_period_id = bp.id
                JOIN projects pr ON bp.project_id = pr.id
                JOIN participants pt ON i.participant_id = pt.id
                LEFT JOIN payments p ON i.id = p.invoice_id
                WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND i.issue_date >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND i.issue_date <= ?"
                params.append(end_date.isoformat())
            
            if status:
                query += " AND i.status = ?"
                params.append(status)
            
            if project_id:
                query += " AND bp.project_id = ?"
                params.append(project_id)
            
            query += " GROUP BY i.id ORDER BY i.issue_date DESC"
            
            cursor.execute(query, params)
            invoices = [dict(row) for row in cursor.fetchall()]
        
        if format == "csv":
            # Export CSV
            output = io.StringIO()
            if invoices:
                writer = csv.DictWriter(output, fieldnames=invoices[0].keys())
                writer.writeheader()
                writer.writerows(invoices)
            
            response = StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8')),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=invoices_{datetime.now().strftime('%Y%m%d')}.csv"}
            )
            return response
            
        elif format == "json":
            # Export JSON
            json_data = json.dumps(invoices, indent=2, default=str)
            response = StreamingResponse(
                io.BytesIO(json_data.encode('utf-8')),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=invoices_{datetime.now().strftime('%Y%m%d')}.json"}
            )
            return response
            
        elif format == "xlsx":
            # Export Excel (nécessiterait openpyxl)
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Export Excel non encore implémenté"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'export: {str(e)}"
        )

@router.get("/export/payments")
async def export_payments(
    format: str = Query("csv", regex="^(csv|xlsx|json)$", description="Format d'export"),
    start_date: Optional[date] = Query(None, description="Date de début"),
    end_date: Optional[date] = Query(None, description="Date de fin"),
    payment_method: Optional[str] = Query(None, description="Filtrer par méthode"),
    project_id: Optional[int] = Query(None, description="Filtrer par projet"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Exporter les paiements dans différents formats
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Construction de la requête avec filtres
            query = """
                SELECT 
                    p.id,
                    p.amount,
                    p.payment_date,
                    p.payment_method,
                    p.transaction_id,
                    p.notes,
                    i.invoice_number,
                    i.total_amount as invoice_total,
                    pt.name as participant_name,
                    pr.name as project_name,
                    pr.client_name
                FROM payments p
                JOIN invoices i ON p.invoice_id = i.id
                JOIN billing_periods bp ON i.billing_period_id = bp.id
                JOIN projects pr ON bp.project_id = pr.id
                JOIN participants pt ON i.participant_id = pt.id
                WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND p.payment_date >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND p.payment_date <= ?"
                params.append(end_date.isoformat())
            
            if payment_method:
                query += " AND p.payment_method = ?"
                params.append(payment_method)
            
            if project_id:
                query += " AND bp.project_id = ?"
                params.append(project_id)
            
            query += " ORDER BY p.payment_date DESC"
            
            cursor.execute(query, params)
            payments = [dict(row) for row in cursor.fetchall()]
        
        if format == "csv":
            # Export CSV
            output = io.StringIO()
            if payments:
                writer = csv.DictWriter(output, fieldnames=payments[0].keys())
                writer.writeheader()
                writer.writerows(payments)
            
            response = StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8')),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=payments_{datetime.now().strftime('%Y%m%d')}.csv"}
            )
            return response
            
        elif format == "json":
            # Export JSON
            json_data = json.dumps(payments, indent=2, default=str)
            response = StreamingResponse(
                io.BytesIO(json_data.encode('utf-8')),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=payments_{datetime.now().strftime('%Y%m%d')}.json"}
            )
            return response
            
        elif format == "xlsx":
            # Export Excel (nécessiterait openpyxl)
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Export Excel non encore implémenté"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'export: {str(e)}"
        )