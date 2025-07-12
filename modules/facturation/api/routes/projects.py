"""
Routes API pour la gestion des projets
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse
import sys
import os

# Ajouter le chemin des modules
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
if modules_path not in sys.path:
    sys.path.append(modules_path)

from ..schemas.project_schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectSummary,
    ProjectListFilters, ProjectStatistics, MonthlyProductionCreate,
    MonthlyProductionResponse
)
from ..schemas.response_schemas import (
    APIResponse, PaginatedResponse, CreatedResponse, UpdatedResponse,
    DeletedResponse, ErrorResponse
)

from modules.facturation.database import BillingDatabase
from modules.facturation.models import Project, ProjectStatus

router = APIRouter()

def get_database():
    """Dependency pour obtenir une instance de la base de données"""
    return BillingDatabase()

@router.get("/", response_model=PaginatedResponse[ProjectSummary])
async def get_projects(
    page: int = Query(1, ge=1, description="Numéro de page"),
    per_page: int = Query(20, ge=1, le=100, description="Éléments par page"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    client_name: Optional[str] = Query(None, description="Recherche par nom de client"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer la liste des projets avec pagination et filtres
    """
    try:
        # Construire les filtres
        filters = {}
        if status:
            filters['status'] = status
        if client_name:
            filters['client_name'] = f"%{client_name}%"
        
        # Récupérer les projets depuis la base de données
        projects = db.get_projects()
        
        # Appliquer les filtres
        if status:
            projects = [p for p in projects if p.get('status') == status]
        if client_name:
            projects = [p for p in projects if client_name.lower() in p.get('client_name', '').lower()]
        
        # Pagination
        total = len(projects)
        start = (page - 1) * per_page
        end = start + per_page
        projects_page = projects[start:end]
        
        # Enrichir avec des statistiques
        project_summaries = []
        for project in projects_page:
            # Récupérer les participants pour compter
            participants = db.get_participants(project['id'])
            
            # TODO: Calculer les statistiques réelles
            summary = ProjectSummary(
                id=project['id'],
                name=project['name'],
                client_name=project['client_name'],
                status=project['status'],
                participants_count=len(participants),
                total_capacity_kwc=project.get('total_capacity_kwc'),
                monthly_revenue=0.0,  # À calculer
                pending_invoices_count=0,  # À calculer
                pending_invoices_amount=0.0,  # À calculer
                created_at=project['created_at']
            )
            project_summaries.append(summary)
        
        return PaginatedResponse(
            status="success",
            message=f"{len(project_summaries)} projets récupérés",
            data=project_summaries,
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
            detail=f"Erreur lors de la récupération des projets: {str(e)}"
        )

@router.get("/{project_id}", response_model=APIResponse[ProjectResponse])
async def get_project(
    project_id: int,
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer un projet spécifique par son ID
    """
    try:
        project_data = db.get_project(project_id)
        if not project_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Projet avec l'ID {project_id} non trouvé"
            )
        
        # Convertir en modèle Pydantic
        project = ProjectResponse(**project_data)
        
        return APIResponse(
            status="success",
            message="Projet récupéré avec succès",
            data=project
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du projet: {str(e)}"
        )

@router.post("/", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: BillingDatabase = Depends(get_database)
):
    """
    Créer un nouveau projet
    """
    try:
        # Convertir le modèle Pydantic en dictionnaire
        project_data = project.dict(exclude_unset=True)
        
        # Créer le projet dans la base de données
        project_id = db.create_project(project_data)
        
        return CreatedResponse(
            message="Projet créé avec succès",
            id=project_id,
            location=f"/api/v1/projects/{project_id}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du projet: {str(e)}"
        )

@router.put("/{project_id}", response_model=UpdatedResponse)
async def update_project(
    project_id: int,
    project: ProjectUpdate,
    db: BillingDatabase = Depends(get_database)
):
    """
    Mettre à jour un projet existant
    """
    try:
        # Vérifier que le projet existe
        existing_project = db.get_project(project_id)
        if not existing_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Projet avec l'ID {project_id} non trouvé"
            )
        
        # Préparer les données de mise à jour
        update_data = project.dict(exclude_unset=True)
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
        
        values.append(project_id)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE projects 
                SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, values)
            
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Projet non trouvé"
                )
        
        return UpdatedResponse(
            message="Projet mis à jour avec succès",
            updated_fields=list(update_data.keys())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour du projet: {str(e)}"
        )

@router.delete("/{project_id}", response_model=DeletedResponse)
async def delete_project(
    project_id: int,
    force: bool = Query(False, description="Forcer la suppression même avec des dépendances"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Supprimer un projet
    """
    try:
        # Vérifier que le projet existe
        existing_project = db.get_project(project_id)
        if not existing_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Projet avec l'ID {project_id} non trouvé"
            )
        
        # Vérifier les dépendances si force=False
        if not force:
            participants = db.get_participants(project_id)
            if participants:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Impossible de supprimer le projet: il contient des participants. Utilisez force=true pour forcer la suppression."
                )
        
        # Supprimer le projet (et ses dépendances si force=True)
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            if force:
                # Supprimer les dépendances dans l'ordre
                cursor.execute("DELETE FROM monthly_consumption WHERE participant_id IN (SELECT id FROM participants WHERE project_id = ?)", (project_id,))
                cursor.execute("DELETE FROM participants WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM monthly_production WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM billing_periods WHERE project_id = ?", (project_id,))
            
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Projet non trouvé"
                )
        
        return DeletedResponse(
            message="Projet supprimé avec succès"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression du projet: {str(e)}"
        )

@router.get("/{project_id}/statistics", response_model=APIResponse[ProjectStatistics])
async def get_project_statistics(
    project_id: int,
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer les statistiques d'un projet
    """
    try:
        # Vérifier que le projet existe
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Projet avec l'ID {project_id} non trouvé"
            )
        
        # Calculer les statistiques
        participants = db.get_participants(project_id)
        
        # TODO: Implémenter le calcul des vraies statistiques
        statistics = ProjectStatistics(
            total_participants=len(participants),
            active_participants=len([p for p in participants if p.get('status', 'active') == 'active']),
            total_production_kwh=0.0,
            total_consumption_kwh=0.0,
            autoconsumption_rate=0.0,
            total_revenue=0.0,
            pending_amount=0.0,
            paid_amount=0.0,
            collection_rate=0.0,
            last_billing_date=None,
            next_billing_date=None
        )
        
        return APIResponse(
            status="success",
            message="Statistiques du projet récupérées avec succès",
            data=statistics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul des statistiques: {str(e)}"
        )

@router.post("/{project_id}/production", response_model=CreatedResponse)
async def add_monthly_production(
    project_id: int,
    production: MonthlyProductionCreate,
    db: BillingDatabase = Depends(get_database)
):
    """
    Ajouter des données de production mensuelle pour un projet
    """
    try:
        # Vérifier que le projet existe
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Projet avec l'ID {project_id} non trouvé"
            )
        
        # Vérifier la cohérence des données
        production_data = production.dict()
        if production_data.get('autoconsumption_kwh', 0) + production_data.get('injection_kwh', 0) > production_data['total_production_kwh']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La somme de l'autoconsommation et de l'injection ne peut pas dépasser la production totale"
            )
        
        # Enregistrer les données
        success = db.record_monthly_production(
            project_id=project_id,
            year=production.year,
            month=production.month,
            production_data=production_data
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de l'enregistrement des données de production"
            )
        
        return CreatedResponse(
            message="Données de production enregistrées avec succès",
            id=0  # L'ID n'est pas retourné par la méthode actuelle
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'enregistrement des données de production: {str(e)}"
        )

@router.get("/{project_id}/production", response_model=APIResponse[List[MonthlyProductionResponse]])
async def get_project_production(
    project_id: int,
    year: Optional[int] = Query(None, description="Filtrer par année"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer les données de production d'un projet
    """
    try:
        # Vérifier que le projet existe
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Projet avec l'ID {project_id} non trouvé"
            )
        
        # Récupérer les données de production
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM monthly_production 
                WHERE project_id = ?
            """
            params = [project_id]
            
            if year:
                query += " AND year = ?"
                params.append(year)
            
            query += " ORDER BY year DESC, month DESC"
            
            cursor.execute(query, params)
            production_data = [dict(row) for row in cursor.fetchall()]
        
        # Convertir en modèles Pydantic avec calculs
        production_responses = []
        for data in production_data:
            # Calculer les taux
            total_production = data.get('total_production_kwh', 0)
            autoconsumption = data.get('autoconsumption_kwh', 0) or 0
            injection = data.get('injection_kwh', 0) or 0
            
            autoconsumption_rate = (autoconsumption / total_production * 100) if total_production > 0 else 0
            injection_rate = (injection / total_production * 100) if total_production > 0 else 0
            
            production_response = MonthlyProductionResponse(
                **data,
                autoconsumption_rate=autoconsumption_rate,
                injection_rate=injection_rate
            )
            production_responses.append(production_response)
        
        return APIResponse(
            status="success",
            message=f"{len(production_responses)} données de production récupérées",
            data=production_responses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des données de production: {str(e)}"
        )