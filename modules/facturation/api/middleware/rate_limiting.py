"""
Middleware de limitation de débit pour l'API REST
"""

import time
import json
import logging
from typing import Dict, Optional, Tuple
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from datetime import datetime, timedelta
import os
import sqlite3
import hashlib

logger = logging.getLogger(__name__)

class RateLimitStore:
    """
    Store pour gérer les compteurs de limitation de débit
    """
    
    def __init__(self, db_path: str = "data/rate_limits.db"):
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Créer le répertoire de la base de données si nécessaire"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _init_database(self):
        """Initialiser la base de données de limitation de débit"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id TEXT NOT NULL,
                    window_start INTEGER NOT NULL,
                    request_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(client_id, window_start)
                )
            """)
            
            # Index pour améliorer les performances
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rate_limits_client_window ON rate_limits(client_id, window_start)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rate_limits_window_start ON rate_limits(window_start)")
            
            conn.commit()
    
    def get_client_requests(self, client_id: str, window_start: int) -> int:
        """Récupérer le nombre de requêtes pour un client dans une fenêtre"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT request_count FROM rate_limits 
                WHERE client_id = ? AND window_start = ?
            """, (client_id, window_start))
            
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def increment_client_requests(self, client_id: str, window_start: int) -> int:
        """Incrémenter le compteur de requêtes pour un client"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tenter d'insérer ou mettre à jour
            cursor.execute("""
                INSERT OR REPLACE INTO rate_limits (client_id, window_start, request_count, updated_at)
                VALUES (?, ?, 
                    COALESCE((SELECT request_count FROM rate_limits WHERE client_id = ? AND window_start = ?), 0) + 1,
                    CURRENT_TIMESTAMP)
            """, (client_id, window_start, client_id, window_start))
            
            # Récupérer le nouveau compteur
            cursor.execute("""
                SELECT request_count FROM rate_limits 
                WHERE client_id = ? AND window_start = ?
            """, (client_id, window_start))
            
            result = cursor.fetchone()
            conn.commit()
            return result[0] if result else 1
    
    def cleanup_old_records(self, cutoff_time: int):
        """Nettoyer les anciens enregistrements"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM rate_limits WHERE window_start < ?", (cutoff_time,))
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                logger.debug(f"Cleaned up {deleted_count} old rate limit records")

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de limitation de débit basé sur l'IP client
    """
    
    def __init__(
        self, 
        app,
        calls: int = 100,
        period: int = 60,
        key_func: Optional[callable] = None,
        exempt_paths: Optional[list] = None,
        store: Optional[RateLimitStore] = None
    ):
        super().__init__(app)
        self.calls = calls  # Nombre de requêtes autorisées
        self.period = period  # Période en secondes
        self.key_func = key_func or self._default_key_func
        self.exempt_paths = exempt_paths or ["/health", "/docs", "/redoc", "/openapi.json"]
        self.store = store or RateLimitStore()
        
        # Démarrer le nettoyage périodique
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes
    
    async def dispatch(self, request: Request, call_next):
        """
        Traiter la requête avec limitation de débit
        """
        # Vérifier si le chemin est exempté
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Obtenir la clé du client
        client_key = self.key_func(request)
        
        # Calculer la fenêtre temporelle actuelle
        current_time = int(time.time())
        window_start = (current_time // self.period) * self.period
        
        # Effectuer le nettoyage périodique
        await self._periodic_cleanup(current_time)
        
        # Vérifier la limite
        try:
            current_count = self.store.increment_client_requests(client_key, window_start)
            
            # Calculer les en-têtes de réponse
            remaining = max(0, self.calls - current_count)
            reset_time = window_start + self.period
            
            if current_count > self.calls:
                # Limite dépassée
                retry_after = reset_time - current_time
                
                logger.warning(
                    f"Rate limit exceeded for {client_key}: {current_count}/{self.calls} requests",
                    extra={
                        "client_key": client_key,
                        "current_count": current_count,
                        "limit": self.calls,
                        "window_start": window_start,
                        "path": request.url.path,
                        "method": request.method
                    }
                )
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "detail": f"Too many requests. Limit: {self.calls} per {self.period} seconds",
                        "retry_after": retry_after,
                        "timestamp": datetime.now().isoformat()
                    },
                    headers={
                        "X-RateLimit-Limit": str(self.calls),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_time),
                        "Retry-After": str(retry_after)
                    }
                )
            
            # Traiter la requête
            response = await call_next(request)
            
            # Ajouter les en-têtes de limitation de débit
            response.headers["X-RateLimit-Limit"] = str(self.calls)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in rate limiting: {e}", exc_info=True)
            # En cas d'erreur, laisser passer la requête
            return await call_next(request)
    
    def _default_key_func(self, request: Request) -> str:
        """
        Fonction par défaut pour générer la clé du client
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
        
        # Ajouter l'utilisateur authentifié si disponible
        user_id = "anonymous"
        if hasattr(request.state, "user") and request.state.user:
            user_id = str(request.state.user.get("user_id", "anonymous"))
        
        # Combiner IP et utilisateur pour la clé
        key = f"{client_ip}:{user_id}"
        
        # Hasher la clé pour la sécurité et la cohérence
        return hashlib.sha256(key.encode()).hexdigest()[:16]
    
    async def _periodic_cleanup(self, current_time: int):
        """
        Effectuer un nettoyage périodique des anciens enregistrements
        """
        if current_time - self._last_cleanup > self._cleanup_interval:
            # Nettoyer les enregistrements plus anciens que 2 périodes
            cutoff_time = current_time - (2 * self.period)
            self.store.cleanup_old_records(cutoff_time)
            self._last_cleanup = current_time

class APIKeyRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de limitation de débit basé sur les clés API
    """
    
    def __init__(
        self,
        app,
        default_calls: int = 1000,
        default_period: int = 3600,  # 1 heure
        api_key_limits: Optional[Dict[str, Tuple[int, int]]] = None,
        store: Optional[RateLimitStore] = None
    ):
        super().__init__(app)
        self.default_calls = default_calls
        self.default_period = default_period
        self.api_key_limits = api_key_limits or {}
        self.store = store or RateLimitStore()
    
    async def dispatch(self, request: Request, call_next):
        """
        Traiter la requête avec limitation basée sur la clé API
        """
        # Récupérer la clé API depuis l'en-tête
        api_key = request.headers.get("X-API-Key")
        
        if not api_key:
            # Pas de clé API, utiliser les limites par défaut par IP
            return await call_next(request)
        
        # Obtenir les limites pour cette clé API
        calls, period = self.api_key_limits.get(api_key, (self.default_calls, self.default_period))
        
        # Calculer la fenêtre temporelle
        current_time = int(time.time())
        window_start = (current_time // period) * period
        
        # Clé pour cette API key
        client_key = f"apikey:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"
        
        try:
            current_count = self.store.increment_client_requests(client_key, window_start)
            
            if current_count > calls:
                # Limite dépassée
                retry_after = window_start + period - current_time
                
                logger.warning(
                    f"API key rate limit exceeded: {current_count}/{calls} requests",
                    extra={
                        "api_key_hash": client_key,
                        "current_count": current_count,
                        "limit": calls,
                        "period": period
                    }
                )
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "API rate limit exceeded",
                        "detail": f"API key limit: {calls} per {period} seconds",
                        "retry_after": retry_after
                    },
                    headers={
                        "X-RateLimit-Limit": str(calls),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(window_start + period),
                        "Retry-After": str(retry_after)
                    }
                )
            
            # Traiter la requête
            response = await call_next(request)
            
            # Ajouter les en-têtes
            remaining = max(0, calls - current_count)
            response.headers["X-RateLimit-Limit"] = str(calls)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(window_start + period)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in API key rate limiting: {e}", exc_info=True)
            return await call_next(request)

def create_user_rate_limit_key(request: Request) -> str:
    """
    Créer une clé de limitation basée sur l'utilisateur authentifié
    """
    if hasattr(request.state, "user") and request.state.user:
        user_id = request.state.user.get("user_id")
        if user_id:
            return f"user:{user_id}"
    
    # Fallback sur l'IP si pas d'utilisateur
    client_ip = "unknown"
    if request.client:
        client_ip = request.client.host
    
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    return f"ip:{client_ip}"

def create_endpoint_rate_limit_key(request: Request) -> str:
    """
    Créer une clé de limitation basée sur l'endpoint
    """
    base_key = create_user_rate_limit_key(request)
    endpoint = f"{request.method}:{request.url.path}"
    return f"{base_key}:{endpoint}"

# Configuration par défaut
DEFAULT_RATE_LIMITS = {
    "global": (100, 60),          # 100 requêtes par minute
    "auth": (10, 60),             # 10 tentatives de connexion par minute
    "heavy": (10, 300),           # 10 requêtes lourdes par 5 minutes
    "api_key": (1000, 3600),      # 1000 requêtes par heure avec clé API
}

def get_rate_limit_config() -> Dict[str, Tuple[int, int]]:
    """
    Récupérer la configuration de limitation de débit depuis l'environnement
    """
    config = DEFAULT_RATE_LIMITS.copy()
    
    # Permettre la configuration via variables d'environnement
    for key, (default_calls, default_period) in config.items():
        env_calls = os.getenv(f"RATE_LIMIT_{key.upper()}_CALLS", str(default_calls))
        env_period = os.getenv(f"RATE_LIMIT_{key.upper()}_PERIOD", str(default_period))
        
        try:
            config[key] = (int(env_calls), int(env_period))
        except ValueError:
            logger.warning(f"Invalid rate limit config for {key}, using defaults")
    
    return config