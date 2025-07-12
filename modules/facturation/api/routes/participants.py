"""
Routes API pour la gestion des participants
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status
import sys
import os

# Ajouter le chemin des modules
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
if modules_path not in sys.path:
    sys.path.append(modules_path)

from ..schemas.participant_schemas import (
    ParticipantCreate, ParticipantUpdate, ParticipantResponse, ParticipantSummary,
    ParticipantListFilters, ParticipantStatistics, MonthlyConsumptionCreate,
    MonthlyConsumptionResponse, BulkParticipantCreate, BulkParticipantOperation
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

@router.get("/", response_model=PaginatedResponse[ParticipantSummary])
async def get_participants(
    page: int = Query(1, ge=1, description="Numéro de page"),
    per_page: int = Query(20, ge=1, le=100, description="Éléments par page"),
    project_id: Optional[int] = Query(None, description="Filtrer par projet"),
    type: Optional[str] = Query(None, description="Filtrer par type (producer/consumer)"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    name: Optional[str] = Query(None, description="Recherche par nom"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer la liste des participants avec pagination et filtres
    """
    try:
        # Récupérer tous les participants ou par projet
        if project_id:
            participants = db.get_participants(project_id)
        else:
            # Récupérer tous les participants de tous les projets
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.*, pr.name as project_name
                    FROM participants p
                    JOIN projects pr ON p.project_id = pr.id
                    ORDER BY p.created_at DESC
                """)
                participants = [dict(row) for row in cursor.fetchall()]
        
        # Appliquer les filtres
        if type:
            participants = [p for p in participants if p.get('type') == type]
        if status:
            participants = [p for p in participants if p.get('status', 'active') == status]
        if name:
            participants = [p for p in participants if name.lower() in p.get('name', '').lower()]
        
        # Pagination
        total = len(participants)
        start = (page - 1) * per_page
        end = start + per_page
        participants_page = participants[start:end]
        
        # Enrichir avec des statistiques
        participant_summaries = []
        for participant in participants_page:
            # TODO: Calculer les vraies statistiques
            summary = ParticipantSummary(
                id=participant['id'],
                name=participant['name'],
                type=participant['type'],
                status=participant.get('status', 'active'),
                project_name=participant.get('project_name', ''),
                allocation_percentage=participant.get('allocation_percentage'),
                total_invoiced=0.0,  # À calculer
                pending_amount=0.0,  # À calculer
                last_activity=None  # À calculer
            )
            participant_summaries.append(summary)
        
        return PaginatedResponse(
            status="success",
            message=f"{len(participant_summaries)} participants récupérés",
            data=participant_summaries,
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
            detail=f"Erreur lors de la récupération des participants: {str(e)}"
        )

@router.get("/{participant_id}", response_model=APIResponse[ParticipantResponse])
async def get_participant(
    participant_id: int,
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer un participant spécifique par son ID
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, pr.name as project_name
                FROM participants p
                JOIN projects pr ON p.project_id = pr.id
                WHERE p.id = ?
            """, (participant_id,))
            
            participant_data = cursor.fetchone()
            if not participant_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Participant avec l'ID {participant_id} non trouvé"
                )
            
            participant_dict = dict(participant_data)
            
            # TODO: Calculer les montants facturés et payés
            participant_dict.update({
                'total_invoiced_amount': 0.0,
                'total_paid_amount': 0.0,
                'pending_amount': 0.0,
                'last_invoice_date': None,
                'last_payment_date': None,
                'status': participant_dict.get('status', 'active')
            })
        
        # Convertir en modèle Pydantic
        participant = ParticipantResponse(**participant_dict)
        
        return APIResponse(
            status="success",
            message="Participant récupéré avec succès",
            data=participant
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du participant: {str(e)}"
        )

@router.post("/", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_participant(
    participant: ParticipantCreate,
    db: BillingDatabase = Depends(get_database)
):
    """
    Créer un nouveau participant
    """
    try:
        # Vérifier que le projet existe
        project = db.get_project(participant.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Projet avec l'ID {participant.project_id} non trouvé"
            )
        
        # Convertir le modèle Pydantic en dictionnaire
        participant_data = participant.dict(exclude_unset=True)
        
        # Créer le participant dans la base de données
        participant_id = db.create_participant(participant_data)
        
        return CreatedResponse(
            message="Participant créé avec succès",
            id=participant_id,
            location=f"/api/v1/participants/{participant_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du participant: {str(e)}"
        )

@router.put("/{participant_id}", response_model=UpdatedResponse)
async def update_participant(
    participant_id: int,
    participant: ParticipantUpdate,
    db: BillingDatabase = Depends(get_database)
):
    """
    Mettre à jour un participant existant
    """
    try:
        # Vérifier que le participant existe
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM participants WHERE id = ?", (participant_id,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Participant avec l'ID {participant_id} non trouvé"
                )
        
        # Préparer les données de mise à jour
        update_data = participant.dict(exclude_unset=True)
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
        
        values.append(participant_id)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE participants 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """, values)
            
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Participant non trouvé"
                )
        
        return UpdatedResponse(
            message="Participant mis à jour avec succès",
            updated_fields=list(update_data.keys())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour du participant: {str(e)}"
        )

@router.delete("/{participant_id}", response_model=DeletedResponse)
async def delete_participant(
    participant_id: int,
    force: bool = Query(False, description="Forcer la suppression même avec des factures"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Supprimer un participant
    """
    try:
        # Vérifier que le participant existe
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM participants WHERE id = ?", (participant_id,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Participant avec l'ID {participant_id} non trouvé"
                )
        
        # Vérifier les dépendances si force=False
        if not force:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM invoices WHERE participant_id = ?", (participant_id,))
                invoice_count = cursor.fetchone()['count']
                
                if invoice_count > 0:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Impossible de supprimer le participant: il a des factures associées. Utilisez force=true pour forcer la suppression."
                    )
        
        # Supprimer le participant (et ses dépendances si force=True)
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            if force:
                # Supprimer les dépendances dans l'ordre
                cursor.execute("DELETE FROM payments WHERE invoice_id IN (SELECT id FROM invoices WHERE participant_id = ?)", (participant_id,))
                cursor.execute("DELETE FROM invoice_items WHERE invoice_id IN (SELECT id FROM invoices WHERE participant_id = ?)", (participant_id,))
                cursor.execute("DELETE FROM invoices WHERE participant_id = ?", (participant_id,))
                cursor.execute("DELETE FROM monthly_consumption WHERE participant_id = ?", (participant_id,))
            
            cursor.execute("DELETE FROM participants WHERE id = ?", (participant_id,))
            
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Participant non trouvé"
                )
        
        return DeletedResponse(
            message="Participant supprimé avec succès"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression du participant: {str(e)}"
        )

@router.get("/{participant_id}/statistics", response_model=APIResponse[ParticipantStatistics])
async def get_participant_statistics(
    participant_id: int,
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer les statistiques d'un participant
    """
    try:
        # Vérifier que le participant existe
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM participants WHERE id = ?", (participant_id,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Participant avec l'ID {participant_id} non trouvé"
                )
        
        # TODO: Implémenter le calcul des vraies statistiques
        statistics = ParticipantStatistics(
            total_consumption_kwh=0.0,
            total_autoconsumption_kwh=0.0,
            autoconsumption_rate=0.0,
            total_invoiced_amount=0.0,
            total_paid_amount=0.0,
            pending_amount=0.0,
            average_monthly_consumption=0.0,
            average_monthly_bill=0.0,
            payment_punctuality_score=0.0,
            last_12_months_consumption=[],
            last_12_months_bills=[]
        )
        
        return APIResponse(
            status="success",
            message="Statistiques du participant récupérées avec succès",
            data=statistics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul des statistiques: {str(e)}"
        )

@router.post("/{participant_id}/consumption", response_model=CreatedResponse)
async def add_monthly_consumption(
    participant_id: int,
    consumption: MonthlyConsumptionCreate,
    db: BillingDatabase = Depends(get_database)
):
    """
    Ajouter des données de consommation mensuelle pour un participant
    """
    try:
        # Vérifier que le participant existe
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM participants WHERE id = ?", (participant_id,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Participant avec l'ID {participant_id} non trouvé"
                )
        
        # Vérifier la cohérence des données
        consumption_data = consumption.dict()
        autoconsumption = consumption_data.get('autoconsumption_kwh', 0) or 0
        grid_consumption = consumption_data.get('grid_consumption_kwh', 0) or 0
        total_consumption = consumption_data['consumption_kwh']
        
        if autoconsumption + grid_consumption > total_consumption:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La somme de l'autoconsommation et de la consommation réseau ne peut pas dépasser la consommation totale"
            )
        
        # Enregistrer les données
        success = db.record_monthly_consumption(
            participant_id=participant_id,
            year=consumption.year,
            month=consumption.month,
            consumption_data=consumption_data
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de l'enregistrement des données de consommation"
            )
        
        return CreatedResponse(
            message="Données de consommation enregistrées avec succès",
            id=0  # L'ID n'est pas retourné par la méthode actuelle
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'enregistrement des données de consommation: {str(e)}"
        )

@router.get("/{participant_id}/consumption", response_model=APIResponse[List[MonthlyConsumptionResponse]])
async def get_participant_consumption(
    participant_id: int,
    year: Optional[int] = Query(None, description="Filtrer par année"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer les données de consommation d'un participant
    """
    try:
        # Vérifier que le participant existe
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM participants WHERE id = ?", (participant_id,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Participant avec l'ID {participant_id} non trouvé"
                )
        
        # Récupérer les données de consommation
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM monthly_consumption 
                WHERE participant_id = ?
            """
            params = [participant_id]
            
            if year:
                query += " AND year = ?"
                params.append(year)
            
            query += " ORDER BY year DESC, month DESC"
            
            cursor.execute(query, params)
            consumption_data = [dict(row) for row in cursor.fetchall()]
        
        # Convertir en modèles Pydantic avec calculs
        consumption_responses = []
        for data in consumption_data:
            # Calculer le taux d'autoconsommation
            total_consumption = data.get('consumption_kwh', 0)
            autoconsumption = data.get('autoconsumption_kwh', 0) or 0
            
            autoconsumption_rate = (autoconsumption / total_consumption * 100) if total_consumption > 0 else 0
            
            # TODO: Calculer les économies réelles
            savings_amount = autoconsumption * 0.15  # Prix exemple
            
            consumption_response = MonthlyConsumptionResponse(
                **data,
                autoconsumption_rate=autoconsumption_rate,
                savings_amount=savings_amount
            )
            consumption_responses.append(consumption_response)
        
        return APIResponse(
            status="success",
            message=f"{len(consumption_responses)} données de consommation récupérées",
            data=consumption_responses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des données de consommation: {str(e)}"
        )

@router.post("/bulk", response_model=BulkOperationResponse)
async def bulk_create_participants(
    bulk_data: BulkParticipantCreate,
    db: BillingDatabase = Depends(get_database)
):
    """
    Créer plusieurs participants en une seule opération
    """
    try:
        # Vérifier que le projet existe
        project = db.get_project(bulk_data.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Projet avec l'ID {bulk_data.project_id} non trouvé"
            )
        
        created_participants = []
        errors = []
        
        for i, participant in enumerate(bulk_data.participants):
            try:
                participant_data = participant.dict(exclude_unset=True)
                participant_data['project_id'] = bulk_data.project_id
                
                # Appliquer le tarif par défaut si spécifié
                if bulk_data.default_tariff_per_kwh and not participant_data.get('tariff_per_kwh'):
                    participant_data['tariff_per_kwh'] = bulk_data.default_tariff_per_kwh
                
                participant_id = db.create_participant(participant_data)
                created_participants.append(participant_id)
                
            except Exception as e:
                errors.append({
                    "index": i,
                    "participant_name": participant.name,
                    "error": str(e)
                })
        
        return BulkOperationResponse(
            message=f"Opération en lot terminée: {len(created_participants)} participants créés, {len(errors)} erreurs",
            total_processed=len(bulk_data.participants),
            successful=len(created_participants),
            failed=len(errors),
            errors=errors if errors else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création en lot des participants: {str(e)}"
        )