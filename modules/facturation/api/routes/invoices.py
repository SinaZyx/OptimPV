"""
Routes API pour la gestion des factures
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status
from datetime import date, datetime, timedelta
import sys
import os

# Ajouter le chemin des modules
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
if modules_path not in sys.path:
    sys.path.append(modules_path)

from ..schemas.invoice_schemas import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceSummary,
    InvoiceListFilters, InvoiceStatistics, BulkInvoiceCreate,
    CreditNoteCreate, CreditNoteResponse, InvoiceItemResponse
)
from ..schemas.response_schemas import (
    APIResponse, PaginatedResponse, CreatedResponse, UpdatedResponse,
    DeletedResponse, BulkOperationResponse
)

from modules.facturation.database import BillingDatabase
from modules.facturation.invoice_numbering import InvoiceNumberingManager

router = APIRouter()

def get_database():
    """Dependency pour obtenir une instance de la base de données"""
    return BillingDatabase()

def get_invoice_numbering():
    """Dependency pour obtenir le gestionnaire de numérotation"""
    return InvoiceNumberingManager()

@router.get("/", response_model=PaginatedResponse[InvoiceSummary])
async def get_invoices(
    page: int = Query(1, ge=1, description="Numéro de page"),
    per_page: int = Query(20, ge=1, le=100, description="Éléments par page"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    participant_id: Optional[int] = Query(None, description="Filtrer par participant"),
    project_id: Optional[int] = Query(None, description="Filtrer par projet"),
    overdue_only: Optional[bool] = Query(None, description="Factures en retard uniquement"),
    issue_date_from: Optional[date] = Query(None, description="Date d'émission minimale"),
    issue_date_to: Optional[date] = Query(None, description="Date d'émission maximale"),
    search: Optional[str] = Query(None, description="Recherche dans numéro ou participant"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer la liste des factures avec pagination et filtres
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Construction de la requête avec filtres
            query = """
                SELECT 
                    i.*,
                    p.name as participant_name,
                    pr.name as project_name,
                    COALESCE(SUM(pay.amount), 0) as paid_amount
                FROM invoices i
                JOIN participants p ON i.participant_id = p.id
                JOIN billing_periods bp ON i.billing_period_id = bp.id
                JOIN projects pr ON bp.project_id = pr.id
                LEFT JOIN payments pay ON i.id = pay.invoice_id
                WHERE 1=1
            """
            params = []
            
            # Appliquer les filtres
            if status:
                query += " AND i.status = ?"
                params.append(status)
            
            if participant_id:
                query += " AND i.participant_id = ?"
                params.append(participant_id)
            
            if project_id:
                query += " AND bp.project_id = ?"
                params.append(project_id)
            
            if issue_date_from:
                query += " AND i.issue_date >= ?"
                params.append(issue_date_from.isoformat())
            
            if issue_date_to:
                query += " AND i.issue_date <= ?"
                params.append(issue_date_to.isoformat())
            
            if search:
                query += " AND (i.invoice_number LIKE ? OR p.name LIKE ?)"
                search_term = f"%{search}%"
                params.extend([search_term, search_term])
            
            if overdue_only:
                today = date.today().isoformat()
                query += " AND i.due_date < ? AND i.status != 'paid'"
                params.append(today)
            
            query += " GROUP BY i.id ORDER BY i.created_at DESC"
            
            cursor.execute(query, params)
            invoices_data = [dict(row) for row in cursor.fetchall()]
        
        # Calculer les informations dérivées
        invoice_summaries = []
        today = date.today()
        
        for invoice in invoices_data:
            due_date = datetime.fromisoformat(invoice['due_date']).date()
            days_overdue = max(0, (today - due_date).days) if invoice['status'] != 'paid' else 0
            
            summary = InvoiceSummary(
                id=invoice['id'],
                invoice_number=invoice['invoice_number'],
                participant_name=invoice['participant_name'],
                issue_date=datetime.fromisoformat(invoice['issue_date']).date(),
                due_date=due_date,
                total_amount=invoice['total_amount'],
                status=invoice['status'],
                days_overdue=days_overdue
            )
            invoice_summaries.append(summary)
        
        # Pagination
        total = len(invoice_summaries)
        start = (page - 1) * per_page
        end = start + per_page
        invoices_page = invoice_summaries[start:end]
        
        return PaginatedResponse(
            status="success",
            message=f"{len(invoices_page)} factures récupérées",
            data=invoices_page,
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
            detail=f"Erreur lors de la récupération des factures: {str(e)}"
        )

@router.get("/{invoice_id}", response_model=APIResponse[InvoiceResponse])
async def get_invoice(
    invoice_id: int,
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer une facture spécifique par son ID
    """
    try:
        # Récupérer la facture avec ses éléments
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Récupérer la facture
            cursor.execute("""
                SELECT 
                    i.*,
                    p.name as participant_name,
                    pr.name as project_name,
                    COALESCE(SUM(pay.amount), 0) as paid_amount
                FROM invoices i
                JOIN participants p ON i.participant_id = p.id
                JOIN billing_periods bp ON i.billing_period_id = bp.id
                JOIN projects pr ON bp.project_id = pr.id
                LEFT JOIN payments pay ON i.id = pay.invoice_id
                WHERE i.id = ?
                GROUP BY i.id
            """, (invoice_id,))
            
            invoice_data = cursor.fetchone()
            if not invoice_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Facture avec l'ID {invoice_id} non trouvée"
                )
            
            invoice_dict = dict(invoice_data)
            
            # Récupérer les éléments de la facture
            cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
            items_data = [dict(row) for row in cursor.fetchall()]
            
            # Convertir les éléments en modèles Pydantic
            items = [InvoiceItemResponse(**item) for item in items_data]
            
            # Calculer les informations dérivées
            paid_amount = invoice_dict.get('paid_amount', 0)
            total_amount = invoice_dict['total_amount']
            remaining_amount = max(0, total_amount - paid_amount)
            
            due_date = datetime.fromisoformat(invoice_dict['due_date']).date()
            today = date.today()
            days_overdue = max(0, (today - due_date).days) if invoice_dict['status'] != 'paid' else 0
            is_overdue = days_overdue > 0 and invoice_dict['status'] != 'paid'
            
            # Enrichir les données
            invoice_dict.update({
                'items': items,
                'remaining_amount': remaining_amount,
                'days_overdue': days_overdue,
                'is_overdue': is_overdue
            })
        
        # Convertir en modèle Pydantic
        invoice = InvoiceResponse(**invoice_dict)
        
        return APIResponse(
            status="success",
            message="Facture récupérée avec succès",
            data=invoice
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de la facture: {str(e)}"
        )

@router.post("/", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice: InvoiceCreate,
    db: BillingDatabase = Depends(get_database),
    numbering: InvoiceNumberingManager = Depends(get_invoice_numbering)
):
    """
    Créer une nouvelle facture
    """
    try:
        # Vérifier que le participant et la période de facturation existent
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM participants WHERE id = ?", (invoice.participant_id,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Participant avec l'ID {invoice.participant_id} non trouvé"
                )
            
            cursor.execute("SELECT id FROM billing_periods WHERE id = ?", (invoice.billing_period_id,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Période de facturation avec l'ID {invoice.billing_period_id} non trouvée"
                )
        
        # Calculer les totaux
        subtotal = sum(item.total_price for item in invoice.items)
        tax_amount = subtotal * invoice.tax_rate
        total_amount = subtotal + tax_amount
        
        # Générer le numéro de facture
        invoice_number = numbering.generate_invoice_number()
        
        # Préparer les données de la facture
        invoice_data = {
            'billing_period_id': invoice.billing_period_id,
            'participant_id': invoice.participant_id,
            'invoice_number': invoice_number,
            'issue_date': invoice.issue_date,
            'due_date': invoice.due_date,
            'subtotal': subtotal,
            'tax_rate': invoice.tax_rate,
            'tax_amount': tax_amount,
            'total_amount': total_amount,
            'status': 'draft'
        }
        
        # Créer la facture
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insérer la facture
            cursor.execute("""
                INSERT INTO invoices (
                    billing_period_id, participant_id, invoice_number,
                    issue_date, due_date, subtotal, tax_rate, tax_amount,
                    total_amount, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_data['billing_period_id'],
                invoice_data['participant_id'],
                invoice_data['invoice_number'],
                invoice_data['issue_date'],
                invoice_data['due_date'],
                invoice_data['subtotal'],
                invoice_data['tax_rate'],
                invoice_data['tax_amount'],
                invoice_data['total_amount'],
                invoice_data['status']
            ))
            
            invoice_id = cursor.lastrowid
            
            # Insérer les éléments de la facture
            for item in invoice.items:
                cursor.execute("""
                    INSERT INTO invoice_items (
                        invoice_id, description, quantity, unit_price,
                        total_price, item_type
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    invoice_id,
                    item.description,
                    item.quantity,
                    item.unit_price,
                    item.total_price,
                    item.item_type
                ))
        
        return CreatedResponse(
            message="Facture créée avec succès",
            id=invoice_id,
            location=f"/api/v1/invoices/{invoice_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la facture: {str(e)}"
        )

@router.put("/{invoice_id}", response_model=UpdatedResponse)
async def update_invoice(
    invoice_id: int,
    invoice: InvoiceUpdate,
    db: BillingDatabase = Depends(get_database)
):
    """
    Mettre à jour une facture existante
    """
    try:
        # Vérifier que la facture existe et n'est pas payée
        invoice_data = db.get_invoice(invoice_id)
        if not invoice_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Facture avec l'ID {invoice_id} non trouvée"
            )
        
        if invoice_data['status'] == 'paid':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Impossible de modifier une facture payée"
            )
        
        # Préparer les données de mise à jour
        update_data = invoice.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucune donnée à mettre à jour"
            )
        
        # Construire la requête SQL de mise à jour
        set_clauses = []
        values = []
        for key, value in update_data.items():
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        values.append(invoice_id)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE invoices 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """, values)
            
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Facture non trouvée"
                )
        
        return UpdatedResponse(
            message="Facture mise à jour avec succès",
            updated_fields=list(update_data.keys())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour de la facture: {str(e)}"
        )

@router.patch("/{invoice_id}/status", response_model=UpdatedResponse)
async def update_invoice_status(
    invoice_id: int,
    new_status: str = Query(..., description="Nouveau statut de la facture"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Mettre à jour le statut d'une facture
    """
    try:
        # Valider le statut
        valid_statuses = ['draft', 'sent', 'paid', 'overdue', 'cancelled']
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Statut invalide. Statuts valides: {', '.join(valid_statuses)}"
            )
        
        # Mettre à jour le statut
        success = db.update_invoice_status(invoice_id, new_status)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Facture avec l'ID {invoice_id} non trouvée"
            )
        
        return UpdatedResponse(
            message=f"Statut de la facture mis à jour vers '{new_status}'",
            updated_fields=['status']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour du statut: {str(e)}"
        )

@router.delete("/{invoice_id}", response_model=DeletedResponse)
async def delete_invoice(
    invoice_id: int,
    force: bool = Query(False, description="Forcer la suppression même avec des paiements"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Supprimer une facture
    """
    try:
        # Vérifier que la facture existe
        invoice_data = db.get_invoice(invoice_id)
        if not invoice_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Facture avec l'ID {invoice_id} non trouvée"
            )
        
        # Vérifier les dépendances si force=False
        if not force:
            payments = db.get_invoice_payments(invoice_id)
            if payments:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Impossible de supprimer la facture: elle a des paiements associés. Utilisez force=true pour forcer la suppression."
                )
        
        # Supprimer la facture (et ses dépendances si force=True)
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            if force:
                # Supprimer les dépendances dans l'ordre
                cursor.execute("DELETE FROM payments WHERE invoice_id = ?", (invoice_id,))
            
            cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
            cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Facture non trouvée"
                )
        
        return DeletedResponse(
            message="Facture supprimée avec succès"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression de la facture: {str(e)}"
        )

@router.get("/statistics/summary", response_model=APIResponse[InvoiceStatistics])
async def get_invoice_statistics(
    project_id: Optional[int] = Query(None, description="Filtrer par projet"),
    year: Optional[int] = Query(None, description="Filtrer par année"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer les statistiques des factures
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Construction de la requête avec filtres
            base_query = """
                FROM invoices i
                JOIN billing_periods bp ON i.billing_period_id = bp.id
                WHERE 1=1
            """
            params = []
            
            if project_id:
                base_query += " AND bp.project_id = ?"
                params.append(project_id)
            
            if year:
                base_query += " AND strftime('%Y', i.issue_date) = ?"
                params.append(str(year))
            
            # Statistiques générales
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_invoices,
                    COALESCE(SUM(i.total_amount), 0) as total_amount,
                    COUNT(CASE WHEN i.status = 'paid' THEN 1 END) as paid_invoices,
                    COALESCE(SUM(CASE WHEN i.status = 'paid' THEN i.total_amount ELSE 0 END), 0) as paid_amount,
                    COUNT(CASE WHEN i.status IN ('sent', 'draft') THEN 1 END) as pending_invoices,
                    COALESCE(SUM(CASE WHEN i.status IN ('sent', 'draft') THEN i.total_amount ELSE 0 END), 0) as pending_amount,
                    COUNT(CASE WHEN i.due_date < date('now') AND i.status != 'paid' THEN 1 END) as overdue_invoices,
                    COALESCE(SUM(CASE WHEN i.due_date < date('now') AND i.status != 'paid' THEN i.total_amount ELSE 0 END), 0) as overdue_amount
                {base_query}
            """, params)
            
            stats_data = dict(cursor.fetchone())
            
            # Calculer les ratios
            total_amount = stats_data['total_amount'] or 0
            paid_amount = stats_data['paid_amount'] or 0
            collection_rate = (paid_amount / total_amount * 100) if total_amount > 0 else 0
            
            # TODO: Calculer le délai moyen de paiement
            average_payment_delay = 0.0
            
            statistics = InvoiceStatistics(
                total_invoices=stats_data['total_invoices'],
                total_amount=total_amount,
                paid_invoices=stats_data['paid_invoices'],
                paid_amount=paid_amount,
                pending_invoices=stats_data['pending_invoices'],
                pending_amount=stats_data['pending_amount'],
                overdue_invoices=stats_data['overdue_invoices'],
                overdue_amount=stats_data['overdue_amount'],
                collection_rate=collection_rate,
                average_payment_delay=average_payment_delay
            )
        
        return APIResponse(
            status="success",
            message="Statistiques des factures récupérées avec succès",
            data=statistics
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul des statistiques: {str(e)}"
        )

@router.post("/bulk", response_model=BulkOperationResponse)
async def bulk_create_invoices(
    bulk_data: BulkInvoiceCreate,
    db: BillingDatabase = Depends(get_database),
    numbering: InvoiceNumberingManager = Depends(get_invoice_numbering)
):
    """
    Créer plusieurs factures en une seule opération (facturation automatique)
    """
    try:
        # Vérifier que la période de facturation existe
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM billing_periods WHERE id = ?", (bulk_data.billing_period_id,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Période de facturation avec l'ID {bulk_data.billing_period_id} non trouvée"
                )
        
        created_invoices = []
        errors = []
        
        # Calculer la date d'échéance
        due_date = bulk_data.issue_date + timedelta(days=bulk_data.payment_terms_days)
        
        for participant_id in bulk_data.participant_ids:
            try:
                # Vérifier que le participant existe
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM participants WHERE id = ?", (participant_id,))
                    participant = cursor.fetchone()
                    if not participant:
                        errors.append({
                            "participant_id": participant_id,
                            "error": "Participant non trouvé"
                        })
                        continue
                
                # TODO: Calculer la consommation réelle pour la période
                # Pour l'instant, on utilise un montant fixe
                autoconsumption_kwh = 100.0  # Exemple
                subtotal = autoconsumption_kwh * bulk_data.autoconsumption_price_per_kwh
                tax_amount = subtotal * bulk_data.tax_rate
                total_amount = subtotal + tax_amount
                
                # Générer le numéro de facture
                invoice_number = numbering.generate_invoice_number()
                
                # Créer la facture
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO invoices (
                            billing_period_id, participant_id, invoice_number,
                            issue_date, due_date, subtotal, tax_rate, tax_amount,
                            total_amount, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        bulk_data.billing_period_id,
                        participant_id,
                        invoice_number,
                        bulk_data.issue_date,
                        due_date,
                        subtotal,
                        bulk_data.tax_rate,
                        tax_amount,
                        total_amount,
                        'draft'
                    ))
                    
                    invoice_id = cursor.lastrowid
                    
                    # Ajouter un élément de facture pour l'autoconsommation
                    cursor.execute("""
                        INSERT INTO invoice_items (
                            invoice_id, description, quantity, unit_price,
                            total_price, item_type
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        invoice_id,
                        f"Autoconsommation {autoconsumption_kwh} kWh",
                        autoconsumption_kwh,
                        bulk_data.autoconsumption_price_per_kwh,
                        subtotal,
                        'autoconsumption'
                    ))
                    
                    created_invoices.append(invoice_id)
                
            except Exception as e:
                errors.append({
                    "participant_id": participant_id,
                    "error": str(e)
                })
        
        return BulkOperationResponse(
            message=f"Facturation en lot terminée: {len(created_invoices)} factures créées, {len(errors)} erreurs",
            total_processed=len(bulk_data.participant_ids),
            successful=len(created_invoices),
            failed=len(errors),
            errors=errors if errors else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la facturation en lot: {str(e)}"
        )

@router.post("/{invoice_id}/credit-note", response_model=CreatedResponse)
async def create_credit_note(
    invoice_id: int,
    credit_note: CreditNoteCreate,
    db: BillingDatabase = Depends(get_database),
    numbering: InvoiceNumberingManager = Depends(get_invoice_numbering)
):
    """
    Créer un avoir pour une facture
    """
    try:
        # Vérifier que la facture existe
        invoice_data = db.get_invoice(invoice_id)
        if not invoice_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Facture avec l'ID {invoice_id} non trouvée"
            )
        
        # Vérifier que le montant de l'avoir ne dépasse pas le montant de la facture
        if credit_note.amount > invoice_data['total_amount']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le montant de l'avoir ne peut pas dépasser le montant de la facture"
            )
        
        # Utiliser le taux de TVA de la facture si non spécifié
        tax_rate = credit_note.tax_rate if credit_note.tax_rate is not None else invoice_data['tax_rate']
        
        # Calculer les montants
        total_amount = credit_note.amount
        subtotal = total_amount / (1 + tax_rate)
        tax_amount = total_amount - subtotal
        
        # Générer le numéro d'avoir
        credit_note_number = numbering.generate_credit_note_number()
        
        # Créer l'avoir
        credit_note_data = {
            'invoice_id': invoice_id,
            'credit_note_number': credit_note_number,
            'issue_date': date.today(),
            'reason': credit_note.reason,
            'subtotal': subtotal,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            'total_amount': total_amount,
            'status': 'draft'
        }
        
        credit_note_id = db.create_credit_note(credit_note_data)
        
        return CreatedResponse(
            message="Avoir créé avec succès",
            id=credit_note_id,
            location=f"/api/v1/invoices/{invoice_id}/credit-notes/{credit_note_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de l'avoir: {str(e)}"
        )

@router.get("/{invoice_id}/credit-notes", response_model=APIResponse[List[CreditNoteResponse]])
async def get_invoice_credit_notes(
    invoice_id: int,
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer les avoirs d'une facture
    """
    try:
        # Vérifier que la facture existe
        invoice_data = db.get_invoice(invoice_id)
        if not invoice_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Facture avec l'ID {invoice_id} non trouvée"
            )
        
        # Récupérer les avoirs
        credit_notes_data = db.get_credit_notes_for_invoice(invoice_id)
        credit_notes = [CreditNoteResponse(**cn) for cn in credit_notes_data]
        
        return APIResponse(
            status="success",
            message=f"{len(credit_notes)} avoirs récupérés",
            data=credit_notes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des avoirs: {str(e)}"
        )