"""
Routes API pour la gestion des webhooks
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, status, BackgroundTasks
import sys
import os

# Ajouter le chemin des modules
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
if modules_path not in sys.path:
    sys.path.append(modules_path)

from ..schemas.response_schemas import (
    APIResponse, PaginatedResponse, CreatedResponse, UpdatedResponse,
    DeletedResponse, WebhookEventResponse
)

from modules.facturation.database import BillingDatabase

router = APIRouter()

def get_database():
    """Dependency pour obtenir une instance de la base de données"""
    return BillingDatabase()

# Modèles pour les webhooks
from pydantic import BaseModel, Field, HttpUrl

class WebhookEndpointCreate(BaseModel):
    """Modèle pour créer un endpoint webhook"""
    url: HttpUrl = Field(..., description="URL de l'endpoint webhook")
    events: List[str] = Field(..., description="Types d'événements à écouter")
    secret: Optional[str] = Field(None, description="Secret pour la signature")
    is_active: bool = Field(True, description="Endpoint actif")
    description: Optional[str] = Field(None, description="Description de l'endpoint")

class WebhookEndpointUpdate(BaseModel):
    """Modèle pour mettre à jour un endpoint webhook"""
    url: Optional[HttpUrl] = Field(None, description="URL de l'endpoint webhook")
    events: Optional[List[str]] = Field(None, description="Types d'événements à écouter")
    secret: Optional[str] = Field(None, description="Secret pour la signature")
    is_active: Optional[bool] = Field(None, description="Endpoint actif")
    description: Optional[str] = Field(None, description="Description de l'endpoint")

class WebhookEndpointResponse(BaseModel):
    """Modèle de réponse pour un endpoint webhook"""
    id: int = Field(..., description="ID unique de l'endpoint")
    url: str = Field(..., description="URL de l'endpoint webhook")
    events: List[str] = Field(..., description="Types d'événements à écouter")
    is_active: bool = Field(..., description="Endpoint actif")
    description: Optional[str] = Field(None, description="Description de l'endpoint")
    created_at: str = Field(..., description="Date de création")
    last_triggered: Optional[str] = Field(None, description="Dernier déclenchement")
    success_count: int = Field(0, description="Nombre de succès")
    failure_count: int = Field(0, description="Nombre d'échecs")

class WebhookEventCreate(BaseModel):
    """Modèle pour déclencher un événement webhook"""
    event_type: str = Field(..., description="Type d'événement")
    data: Dict[str, Any] = Field(..., description="Données de l'événement")
    entity_id: Optional[int] = Field(None, description="ID de l'entité concernée")

@router.get("/endpoints", response_model=PaginatedResponse[WebhookEndpointResponse])
async def get_webhook_endpoints(
    page: int = Query(1, ge=1, description="Numéro de page"),
    per_page: int = Query(20, ge=1, le=100, description="Éléments par page"),
    is_active: Optional[bool] = Query(None, description="Filtrer par statut actif"),
    event_type: Optional[str] = Query(None, description="Filtrer par type d'événement"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer la liste des endpoints webhook
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Créer la table des endpoints webhook si elle n'existe pas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS webhook_endpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    events TEXT NOT NULL, -- JSON array
                    secret TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_triggered TIMESTAMP,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0
                )
            """)
            
            # Construction de la requête avec filtres
            query = "SELECT * FROM webhook_endpoints WHERE 1=1"
            params = []
            
            if is_active is not None:
                query += " AND is_active = ?"
                params.append(is_active)
            
            if event_type:
                query += " AND events LIKE ?"
                params.append(f'%"{event_type}"%')
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            endpoints_data = [dict(row) for row in cursor.fetchall()]
        
        # Convertir en modèles de réponse
        endpoints = []
        for endpoint in endpoints_data:
            import json
            events = json.loads(endpoint.get('events', '[]'))
            
            endpoint_response = WebhookEndpointResponse(
                id=endpoint['id'],
                url=endpoint['url'],
                events=events,
                is_active=bool(endpoint['is_active']),
                description=endpoint.get('description'),
                created_at=endpoint['created_at'],
                last_triggered=endpoint.get('last_triggered'),
                success_count=endpoint.get('success_count', 0),
                failure_count=endpoint.get('failure_count', 0)
            )
            endpoints.append(endpoint_response)
        
        # Pagination
        total = len(endpoints)
        start = (page - 1) * per_page
        end = start + per_page
        endpoints_page = endpoints[start:end]
        
        return PaginatedResponse(
            status="success",
            message=f"{len(endpoints_page)} endpoints webhook récupérés",
            data=endpoints_page,
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
            detail=f"Erreur lors de la récupération des endpoints webhook: {str(e)}"
        )

@router.post("/endpoints", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook_endpoint(
    webhook: WebhookEndpointCreate,
    db: BillingDatabase = Depends(get_database)
):
    """
    Créer un nouvel endpoint webhook
    """
    try:
        import json
        
        # Valider les types d'événements
        valid_events = [
            'invoice.created', 'invoice.sent', 'invoice.paid', 'invoice.overdue',
            'payment.received', 'payment.failed',
            'project.created', 'project.updated',
            'participant.created', 'participant.updated'
        ]
        
        for event in webhook.events:
            if event not in valid_events:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Type d'événement invalide: {event}. Types valides: {', '.join(valid_events)}"
                )
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Créer la table si elle n'existe pas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS webhook_endpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    events TEXT NOT NULL,
                    secret TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_triggered TIMESTAMP,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0
                )
            """)
            
            # Insérer l'endpoint
            cursor.execute("""
                INSERT INTO webhook_endpoints (url, events, secret, is_active, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                str(webhook.url),
                json.dumps(webhook.events),
                webhook.secret,
                webhook.is_active,
                webhook.description
            ))
            
            endpoint_id = cursor.lastrowid
        
        return CreatedResponse(
            message="Endpoint webhook créé avec succès",
            id=endpoint_id,
            location=f"/api/v1/webhooks/endpoints/{endpoint_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de l'endpoint webhook: {str(e)}"
        )

@router.get("/endpoints/{endpoint_id}", response_model=APIResponse[WebhookEndpointResponse])
async def get_webhook_endpoint(
    endpoint_id: int,
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer un endpoint webhook spécifique
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM webhook_endpoints WHERE id = ?", (endpoint_id,))
            endpoint_data = cursor.fetchone()
            
            if not endpoint_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Endpoint webhook avec l'ID {endpoint_id} non trouvé"
                )
            
            endpoint_dict = dict(endpoint_data)
            
            import json
            events = json.loads(endpoint_dict.get('events', '[]'))
            
            endpoint = WebhookEndpointResponse(
                id=endpoint_dict['id'],
                url=endpoint_dict['url'],
                events=events,
                is_active=bool(endpoint_dict['is_active']),
                description=endpoint_dict.get('description'),
                created_at=endpoint_dict['created_at'],
                last_triggered=endpoint_dict.get('last_triggered'),
                success_count=endpoint_dict.get('success_count', 0),
                failure_count=endpoint_dict.get('failure_count', 0)
            )
        
        return APIResponse(
            status="success",
            message="Endpoint webhook récupéré avec succès",
            data=endpoint
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de l'endpoint webhook: {str(e)}"
        )

@router.put("/endpoints/{endpoint_id}", response_model=UpdatedResponse)
async def update_webhook_endpoint(
    endpoint_id: int,
    webhook: WebhookEndpointUpdate,
    db: BillingDatabase = Depends(get_database)
):
    """
    Mettre à jour un endpoint webhook
    """
    try:
        # Vérifier que l'endpoint existe
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM webhook_endpoints WHERE id = ?", (endpoint_id,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Endpoint webhook avec l'ID {endpoint_id} non trouvé"
                )
        
        # Préparer les données de mise à jour
        update_data = webhook.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucune donnée à mettre à jour"
            )
        
        # Valider les événements si fournis
        if 'events' in update_data:
            valid_events = [
                'invoice.created', 'invoice.sent', 'invoice.paid', 'invoice.overdue',
                'payment.received', 'payment.failed',
                'project.created', 'project.updated',
                'participant.created', 'participant.updated'
            ]
            
            for event in update_data['events']:
                if event not in valid_events:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Type d'événement invalide: {event}"
                    )
            
            import json
            update_data['events'] = json.dumps(update_data['events'])
        
        # Construire la requête SQL de mise à jour
        set_clauses = []
        values = []
        for key, value in update_data.items():
            set_clauses.append(f"{key} = ?")
            values.append(str(value) if key == 'url' else value)
        
        values.append(endpoint_id)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE webhook_endpoints 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """, values)
            
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Endpoint webhook non trouvé"
                )
        
        return UpdatedResponse(
            message="Endpoint webhook mis à jour avec succès",
            updated_fields=list(webhook.dict(exclude_unset=True).keys())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour de l'endpoint webhook: {str(e)}"
        )

@router.delete("/endpoints/{endpoint_id}", response_model=DeletedResponse)
async def delete_webhook_endpoint(
    endpoint_id: int,
    db: BillingDatabase = Depends(get_database)
):
    """
    Supprimer un endpoint webhook
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM webhook_endpoints WHERE id = ?", (endpoint_id,))
            
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Endpoint webhook avec l'ID {endpoint_id} non trouvé"
                )
        
        return DeletedResponse(
            message="Endpoint webhook supprimé avec succès"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression de l'endpoint webhook: {str(e)}"
        )

@router.post("/events", response_model=WebhookEventResponse)
async def trigger_webhook_event(
    event: WebhookEventCreate,
    background_tasks: BackgroundTasks,
    db: BillingDatabase = Depends(get_database)
):
    """
    Déclencher un événement webhook
    """
    try:
        import uuid
        from datetime import datetime
        
        # Générer un ID unique pour l'événement
        event_id = str(uuid.uuid4())
        
        # Récupérer les endpoints qui écoutent ce type d'événement
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM webhook_endpoints 
                WHERE is_active = 1 AND events LIKE ?
            """, (f'%"{event.event_type}"%',))
            
            endpoints = [dict(row) for row in cursor.fetchall()]
        
        if not endpoints:
            return WebhookEventResponse(
                event_id=event_id,
                event_type=event.event_type,
                status="no_endpoints",
                sent_at=datetime.now(),
                retry_count=0
            )
        
        # Envoyer les webhooks en arrière-plan
        for endpoint in endpoints:
            background_tasks.add_task(
                send_webhook_async,
                endpoint['url'],
                endpoint.get('secret'),
                event_id,
                event.event_type,
                event.data,
                db
            )
        
        return WebhookEventResponse(
            event_id=event_id,
            event_type=event.event_type,
            status="sent",
            sent_at=datetime.now(),
            retry_count=0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du déclenchement de l'événement webhook: {str(e)}"
        )

@router.get("/events", response_model=PaginatedResponse[Dict[str, Any]])
async def get_webhook_events(
    page: int = Query(1, ge=1, description="Numéro de page"),
    per_page: int = Query(20, ge=1, le=100, description="Éléments par page"),
    event_type: Optional[str] = Query(None, description="Filtrer par type d'événement"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    db: BillingDatabase = Depends(get_database)
):
    """
    Récupérer l'historique des événements webhook
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Créer la table des événements si elle n'existe pas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS webhook_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    endpoint_url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    response_code INTEGER,
                    response_body TEXT,
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP,
                    data TEXT -- JSON
                )
            """)
            
            # Construction de la requête avec filtres
            query = "SELECT * FROM webhook_events WHERE 1=1"
            params = []
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            events_data = [dict(row) for row in cursor.fetchall()]
        
        # Pagination
        total = len(events_data)
        start = (page - 1) * per_page
        end = start + per_page
        events_page = events_data[start:end]
        
        return PaginatedResponse(
            status="success",
            message=f"{len(events_page)} événements webhook récupérés",
            data=events_page,
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
            detail=f"Erreur lors de la récupération des événements webhook: {str(e)}"
        )

async def send_webhook_async(url: str, secret: Optional[str], event_id: str, 
                           event_type: str, data: Dict[str, Any], db: BillingDatabase):
    """
    Envoyer un webhook de manière asynchrone
    """
    import httpx
    import hashlib
    import hmac
    import json
    from datetime import datetime
    
    try:
        # Préparer le payload
        payload = {
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        payload_json = json.dumps(payload, default=str)
        
        # Calculer la signature si un secret est fourni
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "OptimPV-Webhooks/1.0"
        }
        
        if secret:
            signature = hmac.new(
                secret.encode('utf-8'),
                payload_json.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            headers["X-OptimPV-Signature"] = f"sha256={signature}"
        
        # Envoyer le webhook
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, content=payload_json, headers=headers)
            
            # Enregistrer le résultat
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Créer la table si elle n'existe pas
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS webhook_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        endpoint_url TEXT NOT NULL,
                        status TEXT NOT NULL,
                        response_code INTEGER,
                        response_body TEXT,
                        retry_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data TEXT
                    )
                """)
                
                cursor.execute("""
                    INSERT INTO webhook_events 
                    (event_id, event_type, endpoint_url, status, response_code, response_body, data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_id,
                    event_type,
                    url,
                    "success" if response.status_code < 400 else "failed",
                    response.status_code,
                    response.text[:1000],  # Limiter la taille
                    payload_json
                ))
                
                # Mettre à jour les statistiques de l'endpoint
                if response.status_code < 400:
                    cursor.execute("""
                        UPDATE webhook_endpoints 
                        SET success_count = success_count + 1, last_triggered = CURRENT_TIMESTAMP
                        WHERE url = ?
                    """, (url,))
                else:
                    cursor.execute("""
                        UPDATE webhook_endpoints 
                        SET failure_count = failure_count + 1
                        WHERE url = ?
                    """, (url,))
    
    except Exception as e:
        # Enregistrer l'erreur
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO webhook_events 
                (event_id, event_type, endpoint_url, status, response_body, data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                event_type,
                url,
                "error",
                str(e)[:1000],
                json.dumps(data, default=str)
            ))
            
            cursor.execute("""
                UPDATE webhook_endpoints 
                SET failure_count = failure_count + 1
                WHERE url = ?
            """, (url,))