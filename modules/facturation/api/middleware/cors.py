"""
Configuration CORS pour l'API REST
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import List

def setup_cors(app: FastAPI) -> None:
    """
    Configurer le middleware CORS pour l'application FastAPI
    """
    
    # Configuration par défaut pour le développement
    default_origins = [
        "http://localhost:3000",  # React dev server
        "http://localhost:8000",  # FastAPI dev server
        "http://localhost:8001",  # API server alternative
        "http://localhost:8501",  # Streamlit app
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8501",
    ]
    
    # Récupérer les origines autorisées depuis les variables d'environnement
    allowed_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
    if allowed_origins_env:
        allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
    else:
        allowed_origins = default_origins
    
    # En production, être plus restrictif
    is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    if is_production:
        # En production, n'autoriser que les domaines spécifiés
        production_origins = os.getenv("PRODUCTION_ORIGINS", "").split(",")
        if production_origins and production_origins[0]:
            allowed_origins = [origin.strip() for origin in production_origins]
        else:
            # Si pas d'origines de production spécifiées, utiliser un domaine par défaut
            allowed_origins = ["https://optimpv.com", "https://api.optimpv.com"]
    
    # Configuration CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-CSRF-Token",
            "X-API-Key",
        ],
        expose_headers=[
            "X-Total-Count",
            "X-Page-Count",
            "X-Current-Page",
            "X-Per-Page",
            "Location",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
        max_age=3600,  # Cache preflight requests for 1 hour
    )

def get_cors_config() -> dict:
    """
    Retourner la configuration CORS actuelle
    """
    is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    allowed_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
    if allowed_origins_env:
        allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
    else:
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:8000",
            "http://localhost:8001",
            "http://localhost:8501",
        ]
    
    if is_production:
        production_origins = os.getenv("PRODUCTION_ORIGINS", "").split(",")
        if production_origins and production_origins[0]:
            allowed_origins = [origin.strip() for origin in production_origins]
        else:
            allowed_origins = ["https://optimpv.com", "https://api.optimpv.com"]
    
    return {
        "environment": "production" if is_production else "development",
        "allowed_origins": allowed_origins,
        "allow_credentials": True,
        "allowed_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "max_age": 3600,
    }

class CORSConfig:
    """
    Classe de configuration CORS avancée
    """
    
    def __init__(self):
        self.is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
        self.allowed_origins = self._get_allowed_origins()
        self.allowed_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
        self.allowed_headers = [
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-CSRF-Token",
            "X-API-Key",
        ]
        self.expose_headers = [
            "X-Total-Count",
            "X-Page-Count",
            "X-Current-Page",
            "X-Per-Page",
            "Location",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ]
    
    def _get_allowed_origins(self) -> List[str]:
        """
        Déterminer les origines autorisées
        """
        if self.is_production:
            # En production, utiliser les origines spécifiées dans l'environnement
            production_origins = os.getenv("PRODUCTION_ORIGINS", "")
            if production_origins:
                return [origin.strip() for origin in production_origins.split(",")]
            else:
                return ["https://optimpv.com", "https://api.optimpv.com"]
        else:
            # En développement, utiliser les origines par défaut
            dev_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
            if dev_origins:
                return [origin.strip() for origin in dev_origins.split(",")]
            else:
                return [
                    "http://localhost:3000",
                    "http://localhost:8000",
                    "http://localhost:8001",
                    "http://localhost:8501",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:8000",
                    "http://127.0.0.1:8001",
                    "http://127.0.0.1:8501",
                ]
    
    def is_origin_allowed(self, origin: str) -> bool:
        """
        Vérifier si une origine est autorisée
        """
        if not origin:
            return False
        
        # Permettre les origines explicitement listées
        if origin in self.allowed_origins:
            return True
        
        # En développement, permettre aussi les localhost avec différents ports
        if not self.is_production:
            if origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:"):
                return True
        
        return False
    
    def get_middleware_kwargs(self) -> dict:
        """
        Retourner les arguments pour le middleware CORS
        """
        return {
            "allow_origins": self.allowed_origins,
            "allow_credentials": True,
            "allow_methods": self.allowed_methods,
            "allow_headers": self.allowed_headers,
            "expose_headers": self.expose_headers,
            "max_age": 3600,
        }
    
    def add_security_headers(self, response_headers: dict) -> dict:
        """
        Ajouter des en-têtes de sécurité supplémentaires
        """
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
        
        if self.is_production:
            security_headers.update({
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Content-Security-Policy": "default-src 'self'",
            })
        
        return {**response_headers, **security_headers}

# Configuration globale
cors_config = CORSConfig()

def setup_advanced_cors(app: FastAPI) -> None:
    """
    Configurer CORS avec des options avancées
    """
    app.add_middleware(
        CORSMiddleware,
        **cors_config.get_middleware_kwargs()
    )