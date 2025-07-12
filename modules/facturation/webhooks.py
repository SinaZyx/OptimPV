"""
Gestionnaire de webhooks pour les événements de facturation OptimPV
Permet d'envoyer des notifications en temps réel aux systèmes externes
"""

import asyncio
import json
import logging
import hashlib
import hmac
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import httpx
import sys
import os

# Ajouter le chemin des modules
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.abspath(os.path.join(current_dir, '..', '..'))
if modules_path not in sys.path:
    sys.path.append(modules_path)

from modules.facturation.database import BillingDatabase

logger = logging.getLogger(__name__)

class WebhookEventType(str, Enum):
    """Types d'événements webhook disponibles"""
    # Événements de facture
    INVOICE_CREATED = "invoice.created"
    INVOICE_SENT = "invoice.sent"
    INVOICE_PAID = "invoice.paid"
    INVOICE_OVERDUE = "invoice.overdue"
    INVOICE_CANCELLED = "invoice.cancelled"
    INVOICE_UPDATED = "invoice.updated"
    
    # Événements de paiement
    PAYMENT_RECEIVED = "payment.received"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    
    # Événements de projet
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_COMPLETED = "project.completed"
    
    # Événements de participant
    PARTICIPANT_CREATED = "participant.created"
    PARTICIPANT_UPDATED = "participant.updated"
    PARTICIPANT_REMOVED = "participant.removed"
    
    # Événements de système
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"

class WebhookStatus(str, Enum):
    """Statuts d'envoi de webhook"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"
    ABANDONED = "abandoned"

@dataclass
class WebhookEvent:
    """Événement webhook"""
    id: str
    event_type: WebhookEventType
    data: Dict[str, Any]
    timestamp: datetime
    entity_id: Optional[int] = None
    entity_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class WebhookEndpoint:
    """Configuration d'un endpoint webhook"""
    id: int
    url: str
    events: List[WebhookEventType]
    secret: Optional[str] = None
    is_active: bool = True
    description: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 60

@dataclass
class WebhookDelivery:
    """Résultat de livraison d'un webhook"""
    event_id: str
    endpoint_id: int
    status: WebhookStatus
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    delivered_at: Optional[datetime] = None

class WebhookManager:
    """
    Gestionnaire principal des webhooks
    """
    
    def __init__(self, db: Optional[BillingDatabase] = None):
        self.db = db or BillingDatabase()
        self.endpoints: List[WebhookEndpoint] = []
        self.event_handlers: Dict[WebhookEventType, List[Callable]] = {}
        self._client: Optional[httpx.AsyncClient] = None
        self._retry_queue: List[WebhookDelivery] = []
        
        # Configuration
        self.max_concurrent_requests = 10
        self.default_timeout = 30
        self.max_retries = 3
        self.base_retry_delay = 60  # secondes
        
        # Charger les endpoints depuis la base de données
        self._load_endpoints()
    
    def _load_endpoints(self):
        """Charger les endpoints webhook depuis la base de données"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Vérifier si la table existe
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='webhook_endpoints'
                """)
                
                if not cursor.fetchone():
                    logger.info("Table webhook_endpoints n'existe pas encore")
                    return
                
                # Charger les endpoints actifs
                cursor.execute("""
                    SELECT id, url, events, secret, is_active, description
                    FROM webhook_endpoints 
                    WHERE is_active = 1
                """)
                
                for row in cursor.fetchall():
                    try:
                        events_json = json.loads(row[2])
                        events = [WebhookEventType(event) for event in events_json]
                        
                        endpoint = WebhookEndpoint(
                            id=row[0],
                            url=row[1],
                            events=events,
                            secret=row[3],
                            is_active=bool(row[4]),
                            description=row[5]
                        )
                        self.endpoints.append(endpoint)
                        
                    except Exception as e:
                        logger.error(f"Erreur lors du chargement de l'endpoint {row[0]}: {e}")
                
                logger.info(f"Chargé {len(self.endpoints)} endpoints webhook")
                
        except Exception as e:
            logger.error(f"Erreur lors du chargement des endpoints: {e}")
    
    async def __aenter__(self):
        """Initialisation asynchrone"""
        self._client = httpx.AsyncClient(
            timeout=self.default_timeout,
            limits=httpx.Limits(max_connections=self.max_concurrent_requests)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Nettoyage asynchrone"""
        if self._client:
            await self._client.aclose()
    
    def register_event_handler(self, event_type: WebhookEventType, handler: Callable):
        """Enregistrer un gestionnaire d'événement"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def emit_event(self, event_type: WebhookEventType, data: Dict[str, Any], 
                        entity_id: Optional[int] = None, entity_type: Optional[str] = None):
        """
        Émettre un événement webhook
        """
        try:
            # Créer l'événement
            event = WebhookEvent(
                id=str(uuid.uuid4()),
                event_type=event_type,
                data=data,
                timestamp=datetime.utcnow(),
                entity_id=entity_id,
                entity_type=entity_type
            )
            
            logger.info(f"Émission d'événement webhook: {event_type} ({event.id})")
            
            # Exécuter les gestionnaires locaux
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"Erreur dans le gestionnaire d'événement: {e}")
            
            # Envoyer aux endpoints externes
            await self._send_to_endpoints(event)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'émission d'événement: {e}")
    
    async def _send_to_endpoints(self, event: WebhookEvent):
        """Envoyer l'événement à tous les endpoints concernés"""
        if not self._client:
            logger.error("Client HTTP non initialisé")
            return
        
        # Filtrer les endpoints qui écoutent ce type d'événement
        relevant_endpoints = [
            endpoint for endpoint in self.endpoints
            if event.event_type in endpoint.events and endpoint.is_active
        ]
        
        if not relevant_endpoints:
            logger.debug(f"Aucun endpoint pour l'événement {event.event_type}")
            return
        
        # Envoyer en parallèle avec limite de concurrence
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        tasks = [
            self._send_to_endpoint(semaphore, event, endpoint)
            for endpoint in relevant_endpoints
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_to_endpoint(self, semaphore: asyncio.Semaphore, 
                               event: WebhookEvent, endpoint: WebhookEndpoint):
        """Envoyer l'événement à un endpoint spécifique"""
        async with semaphore:
            try:
                delivery = await self._attempt_delivery(event, endpoint)
                await self._record_delivery(delivery)
                
                # Programmer une nouvelle tentative si nécessaire
                if (delivery.status == WebhookStatus.FAILED and 
                    delivery.retry_count < endpoint.max_retries):
                    await self._schedule_retry(delivery, endpoint)
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi à {endpoint.url}: {e}")
    
    async def _attempt_delivery(self, event: WebhookEvent, 
                               endpoint: WebhookEndpoint) -> WebhookDelivery:
        """Tenter la livraison d'un événement"""
        delivery = WebhookDelivery(
            event_id=event.id,
            endpoint_id=endpoint.id,
            status=WebhookStatus.PENDING
        )
        
        try:
            # Préparer le payload
            payload = {
                "id": event.id,
                "event": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data
            }
            
            if event.entity_id:
                payload["entity_id"] = event.entity_id
            if event.entity_type:
                payload["entity_type"] = event.entity_type
            if event.metadata:
                payload["metadata"] = event.metadata
            
            payload_json = json.dumps(payload, default=str)
            
            # Préparer les en-têtes
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "OptimPV-Webhooks/1.0",
                "X-OptimPV-Event": event.event_type.value,
                "X-OptimPV-Event-ID": event.id,
                "X-OptimPV-Timestamp": event.timestamp.isoformat()
            }
            
            # Ajouter la signature si un secret est configuré
            if endpoint.secret:
                signature = self._generate_signature(payload_json, endpoint.secret)
                headers["X-OptimPV-Signature"] = signature
            
            # Ajouter les en-têtes personnalisés
            if endpoint.headers:
                headers.update(endpoint.headers)
            
            # Envoyer la requête
            start_time = datetime.utcnow()
            response = await self._client.post(
                endpoint.url,
                content=payload_json,
                headers=headers,
                timeout=endpoint.timeout
            )
            
            # Traiter la réponse
            delivery.response_code = response.status_code
            delivery.response_body = response.text[:1000]  # Limiter la taille
            delivery.delivered_at = datetime.utcnow()
            
            if 200 <= response.status_code < 300:
                delivery.status = WebhookStatus.SENT
                logger.info(f"Webhook livré avec succès à {endpoint.url}")
            else:
                delivery.status = WebhookStatus.FAILED
                delivery.error_message = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.warning(f"Webhook échoué à {endpoint.url}: {delivery.error_message}")
            
        except httpx.TimeoutException:
            delivery.status = WebhookStatus.FAILED
            delivery.error_message = "Timeout"
            logger.warning(f"Timeout webhook à {endpoint.url}")
            
        except httpx.ConnectError as e:
            delivery.status = WebhookStatus.FAILED
            delivery.error_message = f"Erreur de connexion: {str(e)}"
            logger.warning(f"Erreur de connexion webhook à {endpoint.url}: {e}")
            
        except Exception as e:
            delivery.status = WebhookStatus.FAILED
            delivery.error_message = str(e)
            logger.error(f"Erreur webhook à {endpoint.url}: {e}")
        
        return delivery
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """Générer une signature HMAC-SHA256 pour le payload"""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    async def _record_delivery(self, delivery: WebhookDelivery):
        """Enregistrer le résultat de livraison"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Créer la table si elle n'existe pas
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS webhook_deliveries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id TEXT NOT NULL,
                        endpoint_id INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        response_code INTEGER,
                        response_body TEXT,
                        error_message TEXT,
                        retry_count INTEGER DEFAULT 0,
                        delivered_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    INSERT INTO webhook_deliveries 
                    (event_id, endpoint_id, status, response_code, response_body, 
                     error_message, retry_count, delivered_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    delivery.event_id,
                    delivery.endpoint_id,
                    delivery.status.value,
                    delivery.response_code,
                    delivery.response_body,
                    delivery.error_message,
                    delivery.retry_count,
                    delivery.delivered_at.isoformat() if delivery.delivered_at else None
                ))
                
                # Mettre à jour les statistiques de l'endpoint
                if delivery.status == WebhookStatus.SENT:
                    cursor.execute("""
                        UPDATE webhook_endpoints 
                        SET success_count = success_count + 1, 
                            last_triggered = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (delivery.endpoint_id,))
                else:
                    cursor.execute("""
                        UPDATE webhook_endpoints 
                        SET failure_count = failure_count + 1
                        WHERE id = ?
                    """, (delivery.endpoint_id,))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de la livraison: {e}")
    
    async def _schedule_retry(self, delivery: WebhookDelivery, endpoint: WebhookEndpoint):
        """Programmer une nouvelle tentative"""
        try:
            retry_delay = self.base_retry_delay * (2 ** delivery.retry_count)  # Backoff exponentiel
            retry_time = datetime.utcnow() + timedelta(seconds=retry_delay)
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Créer la table des tentatives si nécessaire
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS webhook_retries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id TEXT NOT NULL,
                        endpoint_id INTEGER NOT NULL,
                        retry_count INTEGER NOT NULL,
                        scheduled_for TIMESTAMP NOT NULL,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    INSERT INTO webhook_retries (event_id, endpoint_id, retry_count, scheduled_for)
                    VALUES (?, ?, ?, ?)
                """, (
                    delivery.event_id,
                    delivery.endpoint_id,
                    delivery.retry_count + 1,
                    retry_time.isoformat()
                ))
                
                conn.commit()
                
            logger.info(f"Nouvelle tentative programmée pour {retry_time} (tentative {delivery.retry_count + 1})")
            
        except Exception as e:
            logger.error(f"Erreur lors de la programmation de nouvelle tentative: {e}")
    
    def add_endpoint(self, url: str, events: List[WebhookEventType], 
                    secret: Optional[str] = None, description: Optional[str] = None) -> int:
        """Ajouter un nouvel endpoint webhook"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO webhook_endpoints (url, events, secret, description)
                    VALUES (?, ?, ?, ?)
                """, (
                    url,
                    json.dumps([event.value for event in events]),
                    secret,
                    description
                ))
                
                endpoint_id = cursor.lastrowid
                conn.commit()
                
                # Ajouter à la liste en mémoire
                endpoint = WebhookEndpoint(
                    id=endpoint_id,
                    url=url,
                    events=events,
                    secret=secret,
                    description=description
                )
                self.endpoints.append(endpoint)
                
                logger.info(f"Endpoint webhook ajouté: {url}")
                return endpoint_id
                
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout d'endpoint: {e}")
            raise
    
    def remove_endpoint(self, endpoint_id: int):
        """Supprimer un endpoint webhook"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM webhook_endpoints WHERE id = ?", (endpoint_id,))
                conn.commit()
            
            # Supprimer de la liste en mémoire
            self.endpoints = [ep for ep in self.endpoints if ep.id != endpoint_id]
            
            logger.info(f"Endpoint webhook supprimé: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression d'endpoint: {e}")
            raise
    
    async def process_retries(self):
        """Traiter les tentatives programmées"""
        try:
            current_time = datetime.utcnow()
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Récupérer les tentatives à traiter
                cursor.execute("""
                    SELECT event_id, endpoint_id, retry_count
                    FROM webhook_retries
                    WHERE status = 'pending' AND scheduled_for <= ?
                    ORDER BY scheduled_for
                """, (current_time.isoformat(),))
                
                retries = cursor.fetchall()
            
            for retry in retries:
                await self._process_retry(retry[0], retry[1], retry[2])
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement des nouvelles tentatives: {e}")
    
    async def _process_retry(self, event_id: str, endpoint_id: int, retry_count: int):
        """Traiter une nouvelle tentative spécifique"""
        # TODO: Implémenter le traitement des nouvelles tentatives
        # Cela nécessiterait de stocker l'événement original pour le renvoyer
        pass

# Instance globale du gestionnaire de webhooks
webhook_manager = WebhookManager()

# Fonctions utilitaires pour émettre des événements spécifiques
async def emit_invoice_created(invoice_data: Dict[str, Any]):
    """Émettre un événement de création de facture"""
    await webhook_manager.emit_event(
        WebhookEventType.INVOICE_CREATED,
        invoice_data,
        entity_id=invoice_data.get('id'),
        entity_type='invoice'
    )

async def emit_invoice_paid(invoice_data: Dict[str, Any], payment_data: Dict[str, Any]):
    """Émettre un événement de paiement de facture"""
    await webhook_manager.emit_event(
        WebhookEventType.INVOICE_PAID,
        {
            'invoice': invoice_data,
            'payment': payment_data
        },
        entity_id=invoice_data.get('id'),
        entity_type='invoice'
    )

async def emit_payment_received(payment_data: Dict[str, Any]):
    """Émettre un événement de réception de paiement"""
    await webhook_manager.emit_event(
        WebhookEventType.PAYMENT_RECEIVED,
        payment_data,
        entity_id=payment_data.get('id'),
        entity_type='payment'
    )

async def emit_project_created(project_data: Dict[str, Any]):
    """Émettre un événement de création de projet"""
    await webhook_manager.emit_event(
        WebhookEventType.PROJECT_CREATED,
        project_data,
        entity_id=project_data.get('id'),
        entity_type='project'
    )

async def emit_participant_created(participant_data: Dict[str, Any]):
    """Émettre un événement de création de participant"""
    await webhook_manager.emit_event(
        WebhookEventType.PARTICIPANT_CREATED,
        participant_data,
        entity_id=participant_data.get('id'),
        entity_type='participant'
    )