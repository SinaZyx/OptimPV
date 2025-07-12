"""
Middleware de logging pour l'API REST
"""

import logging
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import os

# Configuration du logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # json ou text

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour logger toutes les requêtes HTTP
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("api.requests")
        
        # Chemins à exclure du logging détaillé
        self.exclude_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """
        Traiter la requête avec logging
        """
        # Générer un ID unique pour la requête
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Capturer le début de la requête
        start_time = time.time()
        
        # Récupérer les informations de la requête
        request_info = self._extract_request_info(request)
        
        # Logger le début de la requête (sauf pour les chemins exclus)
        if request.url.path not in self.exclude_paths:
            self.logger.info(
                "Request started",
                extra={
                    "request_id": request_id,
                    "event": "request_started",
                    **request_info
                }
            )
        
        # Traiter la requête
        try:
            response = await call_next(request)
            
            # Calculer le temps de traitement
            process_time = time.time() - start_time
            
            # Récupérer les informations de la réponse
            response_info = self._extract_response_info(response, process_time)
            
            # Logger la fin de la requête
            if request.url.path not in self.exclude_paths:
                log_level = logging.ERROR if response.status_code >= 400 else logging.INFO
                self.logger.log(
                    log_level,
                    "Request completed",
                    extra={
                        "request_id": request_id,
                        "event": "request_completed",
                        **request_info,
                        **response_info
                    }
                )
            
            # Ajouter l'ID de requête aux en-têtes de réponse
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Logger les erreurs
            process_time = time.time() - start_time
            
            self.logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "event": "request_failed",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "process_time": process_time,
                    **request_info
                },
                exc_info=True
            )
            
            raise
    
    def _extract_request_info(self, request: Request) -> Dict[str, Any]:
        """
        Extraire les informations pertinentes de la requête
        """
        # Récupérer l'IP du client
        client_ip = "unknown"
        if request.client:
            client_ip = request.client.host
        
        # Vérifier les en-têtes pour les proxies
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            client_ip = real_ip
        
        # Informations utilisateur (si disponible)
        user_info = {}
        if hasattr(request.state, "user"):
            user = request.state.user
            user_info = {
                "user_id": user.get("user_id"),
                "username": user.get("username"),
                "roles": user.get("roles", [])
            }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": client_ip,
            "user_agent": request.headers.get("User-Agent", ""),
            "referer": request.headers.get("Referer", ""),
            "content_type": request.headers.get("Content-Type", ""),
            "content_length": request.headers.get("Content-Length", ""),
            **user_info
        }
    
    def _extract_response_info(self, response: Response, process_time: float) -> Dict[str, Any]:
        """
        Extraire les informations pertinentes de la réponse
        """
        return {
            "status_code": response.status_code,
            "content_type": response.headers.get("Content-Type", ""),
            "content_length": response.headers.get("Content-Length", ""),
            "process_time": round(process_time, 4),
            "process_time_ms": round(process_time * 1000, 2)
        }

class JSONFormatter(logging.Formatter):
    """
    Formateur JSON pour les logs
    """
    
    def format(self, record):
        """
        Formater le log en JSON
        """
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Ajouter les données extra si disponibles
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                              'pathname', 'filename', 'module', 'lineno', 
                              'funcName', 'created', 'msecs', 'relativeCreated',
                              'thread', 'threadName', 'processName', 'process',
                              'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                    log_data[key] = value
        
        # Ajouter les informations d'exception si disponibles
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str, ensure_ascii=False)

def setup_logging(app: FastAPI) -> None:
    """
    Configurer le système de logging pour l'application
    """
    # Configuration du niveau de log
    log_level = getattr(logging, LOG_LEVEL, logging.INFO)
    
    # Configuration du formateur
    if LOG_FORMAT.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Configuration du handler pour les logs d'API
    api_handler = logging.StreamHandler()
    api_handler.setFormatter(formatter)
    api_handler.setLevel(log_level)
    
    # Configuration du logger principal de l'API
    api_logger = logging.getLogger("api")
    api_logger.setLevel(log_level)
    api_logger.addHandler(api_handler)
    
    # Configuration du logger pour les requêtes
    request_logger = logging.getLogger("api.requests")
    request_logger.setLevel(log_level)
    request_logger.addHandler(api_handler)
    
    # Configuration du logger pour la base de données
    db_logger = logging.getLogger("api.database")
    db_logger.setLevel(log_level)
    db_logger.addHandler(api_handler)
    
    # Ajouter le middleware de logging
    app.add_middleware(RequestLoggingMiddleware)
    
    # Logger de démarrage
    startup_logger = logging.getLogger("api.startup")
    startup_logger.info(
        "API logging configured",
        extra={
            "log_level": LOG_LEVEL,
            "log_format": LOG_FORMAT,
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    )

def log_request(method: str, url: str, status_code: int, process_time: float, 
               client_ip: str = "unknown", user_id: Optional[int] = None):
    """
    Fonction utilitaire pour logger une requête
    """
    logger = logging.getLogger("api.requests")
    
    log_data = {
        "method": method,
        "url": url,
        "status_code": status_code,
        "process_time": round(process_time, 4),
        "process_time_ms": round(process_time * 1000, 2),
        "client_ip": client_ip,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if user_id:
        log_data["user_id"] = user_id
    
    # Niveau de log basé sur le code de statut
    if status_code >= 500:
        log_level = logging.ERROR
    elif status_code >= 400:
        log_level = logging.WARNING
    else:
        log_level = logging.INFO
    
    logger.log(log_level, f"{method} {url} - {status_code}", extra=log_data)

def log_database_operation(operation: str, table: str, execution_time: float, 
                         affected_rows: int = 0, error: Optional[str] = None):
    """
    Logger une opération de base de données
    """
    logger = logging.getLogger("api.database")
    
    log_data = {
        "operation": operation,
        "table": table,
        "execution_time": round(execution_time, 4),
        "execution_time_ms": round(execution_time * 1000, 2),
        "affected_rows": affected_rows,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if error:
        log_data["error"] = error
        logger.error(f"Database operation failed: {operation} on {table}", extra=log_data)
    else:
        logger.info(f"Database operation: {operation} on {table}", extra=log_data)

def log_webhook_event(event_type: str, endpoint_url: str, status_code: Optional[int], 
                     response_time: float, error: Optional[str] = None):
    """
    Logger un événement webhook
    """
    logger = logging.getLogger("api.webhooks")
    
    log_data = {
        "event_type": event_type,
        "endpoint_url": endpoint_url,
        "response_time": round(response_time, 4),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if status_code is not None:
        log_data["status_code"] = status_code
    
    if error:
        log_data["error"] = error
        logger.error(f"Webhook failed: {event_type} to {endpoint_url}", extra=log_data)
    else:
        logger.info(f"Webhook sent: {event_type} to {endpoint_url}", extra=log_data)

# Configuration des logs pour les bibliothèques tierces
def configure_third_party_logging():
    """
    Configurer le logging pour les bibliothèques tierces
    """
    # Réduire le niveau de log pour certaines bibliothèques bruyantes
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    
    # Maintenir le niveau INFO pour les logs importantes
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

# Initialiser la configuration des logs tiers
configure_third_party_logging()