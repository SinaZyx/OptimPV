"""
Routes API pour la gestion des paiements
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status
from datetime import date, datetime
import sys
import os

# Ajouter le chemin des modules
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
if modules_path not in sys.path:
    sys.path.append(modules_path)

from ..schemas.payment_schemas import (
    PaymentCreate, PaymentUpdate, PaymentResponse, PaymentSummary,
    PaymentListFilters, PaymentStatistics, BankTransactionCreate,
    BankTransactionResponse, PaymentReconciliation, PaymentScheduleCreate,
    PaymentScheduleResponse, BulkPaymentCreate
)
from ..schemas.response_schemas import (
    APIResponse, PaginatedResponse, CreatedResponse, UpdatedResponse,
    DeletedResponse, BulkOperationResponse
)

from modules.facturation.database import BillingDatabase

router = APIRouter()

def get_database():
    """Dependency pour obtenir une instance de la base de données"""
    return BillingDatabase()

@router.get("/", response_model=PaginatedResponse[PaymentSummary])
async def get_payments(
    page: int = Query(1, ge=1, description="Numéro de page"),
    per_page: int = Query(20, ge=1, le=100, description="Éléments par page"),
    invoice_id: Optional[int] = Query(None, description="Filtrer par facture"),
    participant_id: Optional[int] = Query(None, description="Filtrer par participant"),
    payment_method: Optional[str] = Query(None, description="Filtrer par méthode de paiement"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    payment_date_from: Optional[date] = Query(None, description="Date de paiement minimale"),
    payment_date_to: Optional[date] = Query(None, description="Date de paiement maximale"),
    search: Optional[str] = Query(None, description="Recherche dans référence ou transaction"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer la liste des paiements avec pagination et filtres
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Construction de la requête avec filtres
            query = """
                SELECT 
                    p.*,
                    i.invoice_number,
                    pt.name as participant_name,
                    pr.name as project_name
                FROM payments p
                JOIN invoices i ON p.invoice_id = i.id
                JOIN participants pt ON i.participant_id = pt.id
                JOIN billing_periods bp ON i.billing_period_id = bp.id
                JOIN projects pr ON bp.project_id = pr.id
                WHERE 1=1
            """
            params = []
            
            # Appliquer les filtres
            if invoice_id:
                query += " AND p.invoice_id = ?"
                params.append(invoice_id)
            
            if participant_id:
                query += " AND i.participant_id = ?"
                params.append(participant_id)
            
            if payment_method:
                query += " AND p.payment_method = ?"
                params.append(payment_method)
            
            if status:
                # Note: Le statut n'existe pas encore dans la table payments actuelle
                # On peut l'ajouter ou simuler avec 'completed' par défaut
                pass
            
            if payment_date_from:
                query += " AND p.payment_date >= ?"
                params.append(payment_date_from.isoformat())
            
            if payment_date_to:
                query += " AND p.payment_date <= ?"
                params.append(payment_date_to.isoformat())
            
            if search:
                query += " AND (p.transaction_id LIKE ? OR p.notes LIKE ?)"
                search_term = f"%{search}%"
                params.extend([search_term, search_term])
            
            query += " ORDER BY p.payment_date DESC, p.created_at DESC"
            
            cursor.execute(query, params)
            payments_data = [dict(row) for row in cursor.fetchall()]
        
        # Convertir en modèles de résumé
        payment_summaries = []
        for payment in payments_data:
            summary = PaymentSummary(
                id=payment['id'],
                invoice_number=payment['invoice_number'],
                participant_name=payment['participant_name'],
                amount=payment['amount'],
                payment_date=datetime.fromisoformat(payment['payment_date']).date(),
                payment_method=payment['payment_method'],
                status='completed'  # Par défaut, ajouter une vraie gestion du statut plus tard
            )
            payment_summaries.append(summary)
        
        # Pagination
        total = len(payment_summaries)
        start = (page - 1) * per_page
        end = start + per_page
        payments_page = payment_summaries[start:end]
        
        return PaginatedResponse(
            status="success",
            message=f"{len(payments_page)} paiements récupérés",
            data=payments_page,
            pagination={
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page,
                "has_next": end < total,
                "has_prev": page > 1
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des paiements: {str(e)}"
        )

@router.get("/{payment_id}", response_model=APIResponse[PaymentResponse])
async def get_payment(
    payment_id: int,
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer un paiement spécifique par son ID
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    p.*,
                    i.invoice_number,
                    i.total_amount as invoice_total,
                    pt.name as participant_name,
                    pr.name as project_name,
                    (i.total_amount - COALESCE(SUM(p2.amount), 0)) as remaining_invoice_amount
                FROM payments p
                JOIN invoices i ON p.invoice_id = i.id
                JOIN participants pt ON i.participant_id = pt.id
                JOIN billing_periods bp ON i.billing_period_id = bp.id
                JOIN projects pr ON bp.project_id = pr.id
                LEFT JOIN payments p2 ON i.id = p2.invoice_id
                WHERE p.id = ?
                GROUP BY p.id
            """, (payment_id,))
            
            payment_data = cursor.fetchone()
            if not payment_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Paiement avec l'ID {payment_id} non trouvé"
                )
            
            payment_dict = dict(payment_data)
            
            # Enrichir les données
            payment_dict.update({
                'status': 'completed',  # Par défaut
                'remaining_invoice_amount': payment_dict.get('remaining_invoice_amount', 0)
            })
        
        # Convertir en modèle Pydantic
        payment = PaymentResponse(**payment_dict)
        
        return APIResponse(
            status="success",
            message="Paiement récupéré avec succès",
            data=payment
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du paiement: {str(e)}"
        )

@router.post("/", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment: PaymentCreate,
    db: BillingDatabase = Depends(get_database)
):
    """
    Enregistrer un nouveau paiement
    """
    try:
        # Vérifier que la facture existe
        invoice_data = db.get_invoice(payment.invoice_id)
        if not invoice_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Facture avec l'ID {payment.invoice_id} non trouvée"
            )
        
        # Vérifier que la facture n'est pas déjà entièrement payée
        existing_payments = db.get_invoice_payments(payment.invoice_id)
        total_paid = sum(p['amount'] for p in existing_payments)
        remaining_amount = invoice_data['total_amount'] - total_paid
        
        if payment.amount > remaining_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Le montant du paiement ({payment.amount}€) dépasse le montant restant à payer ({remaining_amount}€)"
            )
        
        # Convertir le modèle Pydantic en dictionnaire
        payment_data = payment.dict()
        
        # Enregistrer le paiement
        payment_id = db.record_payment(payment_data)
        
        return CreatedResponse(
            message="Paiement enregistré avec succès",
            id=payment_id,
            location=f"/api/v1/payments/{payment_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'enregistrement du paiement: {str(e)}"
        )

@router.put("/{payment_id}", response_model=UpdatedResponse)
async def update_payment(
    payment_id: int,
    payment: PaymentUpdate,
    db: BillingDatabase = Depends(get_database)
):
    """
    Mettre à jour un paiement existant
    """
    try:
        # Vérifier que le paiement existe
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
            existing_payment = cursor.fetchone()
            
            if not existing_payment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Paiement avec l'ID {payment_id} non trouvé"
                )
            
            existing_payment_dict = dict(existing_payment)
        
        # Préparer les données de mise à jour
        update_data = payment.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucune donnée à mettre à jour"
            )
        
        # Si le montant est modifié, vérifier la cohérence
        if 'amount' in update_data:
            invoice_data = db.get_invoice(existing_payment_dict['invoice_id'])
            existing_payments = db.get_invoice_payments(existing_payment_dict['invoice_id'])
            # Exclure ce paiement du calcul
            other_payments_total = sum(p['amount'] for p in existing_payments if p['id'] != payment_id)
            remaining_amount = invoice_data['total_amount'] - other_payments_total
            
            if update_data['amount'] > remaining_amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Le nouveau montant ({update_data['amount']}€) dépasse le montant restant à payer ({remaining_amount}€)"
                )
        
        # Construire la requête SQL de mise à jour
        set_clauses = []
        values = []
        for key, value in update_data.items():
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        values.append(payment_id)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE payments 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """, values)
            
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Paiement non trouvé"
                )
            
            # Mettre à jour le statut de la facture si nécessaire
            if 'amount' in update_data:
                invoice_id = existing_payment_dict['invoice_id']
                # Recalculer le total payé et mettre à jour le statut de la facture
                cursor.execute("""
                    SELECT 
                        i.total_amount,
                        COALESCE(SUM(p.amount), 0) as total_paid
                    FROM invoices i
                    LEFT JOIN payments p ON i.id = p.invoice_id
                    WHERE i.id = ?
                    GROUP BY i.id
                """, (invoice_id,))
                
                result = cursor.fetchone()
                if result:
                    total_amount = result[0]
                    total_paid = result[1]
                    
                    if total_paid >= total_amount:
                        new_status = 'paid'
                    elif total_paid > 0:
                        new_status = 'partial_paid'
                    else:
                        new_status = 'sent'
                    
                    cursor.execute("UPDATE invoices SET status = ? WHERE id = ?", (new_status, invoice_id))
        
        return UpdatedResponse(
            message="Paiement mis à jour avec succès",
            updated_fields=list(update_data.keys())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour du paiement: {str(e)}"
        )

@router.delete("/{payment_id}", response_model=DeletedResponse)
async def delete_payment(
    payment_id: int,
    db: BillingDatabase = Depends(get_database)
):
    """
    Supprimer un paiement
    """
    try:
        # Vérifier que le paiement existe et récupérer l'invoice_id
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT invoice_id FROM payments WHERE id = ?", (payment_id,))
            payment = cursor.fetchone()
            
            if not payment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Paiement avec l'ID {payment_id} non trouvé"
                )
            
            invoice_id = payment['invoice_id']
            
            # Supprimer le paiement
            cursor.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
            
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Paiement non trouvé"
                )
            
            # Mettre à jour le statut de la facture
            cursor.execute("""
                SELECT 
                    i.total_amount,
                    COALESCE(SUM(p.amount), 0) as total_paid
                FROM invoices i
                LEFT JOIN payments p ON i.id = p.invoice_id
                WHERE i.id = ?
                GROUP BY i.id
            """, (invoice_id,))
            
            result = cursor.fetchone()
            if result:
                total_amount = result[0]
                total_paid = result[1]
                
                if total_paid >= total_amount:
                    new_status = 'paid'
                elif total_paid > 0:
                    new_status = 'partial_paid'
                else:
                    new_status = 'sent'
                
                cursor.execute("UPDATE invoices SET status = ?, payment_date = NULL WHERE id = ?", (new_status, invoice_id))
        
        return DeletedResponse(
            message="Paiement supprimé avec succès"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression du paiement: {str(e)}"
        )

@router.get("/statistics/summary", response_model=APIResponse[PaymentStatistics])
async def get_payment_statistics(
    project_id: Optional[int] = Query(None, description="Filtrer par projet"),
    year: Optional[int] = Query(None, description="Filtrer par année"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer les statistiques des paiements
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Construction de la requête avec filtres
            base_query = """
                FROM payments p
                JOIN invoices i ON p.invoice_id = i.id
                JOIN billing_periods bp ON i.billing_period_id = bp.id
                WHERE 1=1
            """
            params = []
            
            if project_id:
                base_query += " AND bp.project_id = ?"
                params.append(project_id)
            
            if year:
                base_query += " AND strftime('%Y', p.payment_date) = ?"
                params.append(str(year))
            
            # Statistiques générales
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_payments,
                    COALESCE(SUM(p.amount), 0) as total_amount,
                    COALESCE(AVG(p.amount), 0) as average_amount
                {base_query}
            """, params)
            
            stats_data = dict(cursor.fetchone())
            
            # Répartition par méthode de paiement
            cursor.execute(f"""
                SELECT 
                    p.payment_method,
                    COUNT(*) as count
                {base_query}
                GROUP BY p.payment_method
            """, params)
            
            payments_by_method = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Paiements par mois (12 derniers mois)
            cursor.execute(f"""
                SELECT 
                    strftime('%Y-%m', p.payment_date) as month,
                    COUNT(*) as count,
                    SUM(p.amount) as amount
                {base_query}
                AND p.payment_date >= date('now', '-12 months')
                GROUP BY strftime('%Y-%m', p.payment_date)
                ORDER BY month
            """, params)
            
            monthly_payments = [
                {"month": row[0], "count": row[1], "amount": row[2]}
                for row in cursor.fetchall()
            ]
            
            # TODO: Calculer l'efficacité de recouvrement réelle
            collection_efficiency = 85.0  # Exemple
            
            statistics = PaymentStatistics(
                total_payments=stats_data['total_payments'],
                total_amount=stats_data['total_amount'],
                average_payment_amount=stats_data['average_amount'],
                payments_by_method=payments_by_method,
                payments_by_status={"completed": stats_data['total_payments']},  # Simplifié
                monthly_payments=monthly_payments,
                collection_efficiency=collection_efficiency
            )
        
        return APIResponse(
            status="success",
            message="Statistiques des paiements récupérées avec succès",
            data=statistics
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul des statistiques: {str(e)}"
        )

@router.post("/bulk", response_model=BulkOperationResponse)
async def bulk_create_payments(
    bulk_data: BulkPaymentCreate,
    db: BillingDatabase = Depends(get_database)
):
    """
    Enregistrer plusieurs paiements en une seule opération
    """
    try:
        created_payments = []
        errors = []
        
        for i, payment in enumerate(bulk_data.payments):
            try:
                # Valider la facture
                invoice_data = db.get_invoice(payment.invoice_id)
                if not invoice_data:
                    errors.append({
                        "index": i,
                        "invoice_id": payment.invoice_id,
                        "error": "Facture non trouvée"
                    })
                    continue
                
                # Valider le montant si demandé
                if bulk_data.validate_amounts:
                    existing_payments = db.get_invoice_payments(payment.invoice_id)
                    total_paid = sum(p['amount'] for p in existing_payments)
                    remaining_amount = invoice_data['total_amount'] - total_paid
                    
                    if payment.amount > remaining_amount:
                        errors.append({
                            "index": i,
                            "invoice_id": payment.invoice_id,
                            "error": f"Montant trop élevé: {payment.amount}€ > {remaining_amount}€ restant"
                        })
                        continue
                
                # Enregistrer le paiement
                payment_data = payment.dict()
                payment_id = db.record_payment(payment_data)
                created_payments.append(payment_id)
                
            except Exception as e:
                errors.append({
                    "index": i,
                    "invoice_id": payment.invoice_id,
                    "error": str(e)
                })
        
        return BulkOperationResponse(
            message=f"Enregistrement en lot terminé: {len(created_payments)} paiements créés, {len(errors)} erreurs",
            total_processed=len(bulk_data.payments),
            successful=len(created_payments),
            failed=len(errors),
            errors=errors if errors else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'enregistrement en lot des paiements: {str(e)}"
        )

@router.get("/invoice/{invoice_id}", response_model=APIResponse[List[PaymentResponse]])
async def get_invoice_payments(
    invoice_id: int,
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer tous les paiements d'une facture
    """
    try:
        # Vérifier que la facture existe
        invoice_data = db.get_invoice(invoice_id)
        if not invoice_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Facture avec l'ID {invoice_id} non trouvée"
            )
        
        # Récupérer les paiements
        payments_data = db.get_invoice_payments(invoice_id)
        
        # Enrichir avec les informations de la facture
        payments = []
        for payment in payments_data:
            payment_dict = dict(payment)
            payment_dict.update({
                'invoice_number': invoice_data['invoice_number'],
                'status': 'completed',  # Par défaut
                'remaining_invoice_amount': None  # Sera calculé si nécessaire
            })
            payments.append(PaymentResponse(**payment_dict))
        
        return APIResponse(
            status="success",
            message=f"{len(payments)} paiements récupérés pour la facture",
            data=payments
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des paiements de la facture: {str(e)}"
        )