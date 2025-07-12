"""
Middleware d'authentification JWT pour l'API REST
"""

import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import os

logger = logging.getLogger(__name__)

# Configuration JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "optimpv-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DELTA = timedelta(hours=24)

# Créer l'instance du schéma de sécurité
security = HTTPBearer()

class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware d'authentification JWT
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.exempt_paths = [
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/version",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """
        Traiter la requête avec vérification JWT
        """
        # Vérifier si le chemin est exempté
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Vérifier l'en-tête Authorization
        authorization: str = request.headers.get("Authorization")
        
        if not authorization:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Non autorisé",
                    "detail": "Token d'authentification requis",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        try:
            # Extraire le token
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise ValueError("Schéma d'authentification invalide")
            
            # Vérifier et décoder le token
            payload = verify_jwt_token(token)
            if not payload:
                raise ValueError("Token invalide")
            
            # Ajouter les informations utilisateur à la requête
            request.state.user = payload
            
        except Exception as e:
            logger.warning(f"Échec de l'authentification JWT: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Non autorisé",
                    "detail": "Token d'authentification invalide",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        return await call_next(request)

def create_jwt_token(user_data: Dict[str, Any]) -> str:
    """
    Créer un token JWT
    """
    try:
        # Préparer le payload
        payload = {
            "user_id": user_data.get("user_id"),
            "username": user_data.get("username"),
            "email": user_data.get("email"),
            "roles": user_data.get("roles", []),
            "exp": datetime.utcnow() + JWT_EXPIRATION_DELTA,
            "iat": datetime.utcnow(),
            "iss": "optimpv-api"
        }
        
        # Encoder le token
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token
        
    except Exception as e:
        logger.error(f"Erreur lors de la création du token JWT: {e}")
        raise

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Vérifier et décoder un token JWT
    """
    try:
        # Décoder le token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Vérifier l'expiration
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            return None
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token JWT expiré")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token JWT invalide: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du token JWT: {e}")
        return None

def refresh_jwt_token(token: str) -> Optional[str]:
    """
    Rafraîchir un token JWT
    """
    try:
        # Décoder le token sans vérifier l'expiration
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
        
        # Vérifier que le token n'est pas trop ancien (max 7 jours)
        iat = payload.get("iat")
        if iat and datetime.utcnow().timestamp() - iat > 7 * 24 * 3600:
            return None
        
        # Créer un nouveau token avec les mêmes données
        user_data = {
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
            "email": payload.get("email"),
            "roles": payload.get("roles", [])
        }
        
        return create_jwt_token(user_data)
        
    except Exception as e:
        logger.error(f"Erreur lors du rafraîchissement du token: {e}")
        return None

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency pour vérifier le token JWT dans les routes
    """
    try:
        payload = verify_jwt_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token d'authentification invalide"
            )
        return payload
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erreur d'authentification"
        )

async def verify_admin_token(current_user: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
    """
    Dependency pour vérifier que l'utilisateur est administrateur
    """
    user_roles = current_user.get("roles", [])
    if "admin" not in user_roles and "superuser" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès administrateur requis"
        )
    return current_user

def has_permission(permission: str, user_roles: list) -> bool:
    """
    Vérifier si l'utilisateur a une permission spécifique
    """
    # Mappage des permissions par rôle
    role_permissions = {
        "superuser": ["*"],  # Toutes les permissions
        "admin": [
            "projects.read", "projects.write", "projects.delete",
            "participants.read", "participants.write", "participants.delete",
            "invoices.read", "invoices.write", "invoices.delete",
            "payments.read", "payments.write", "payments.delete",
            "reports.read", "webhooks.read", "webhooks.write"
        ],
        "manager": [
            "projects.read", "projects.write",
            "participants.read", "participants.write",
            "invoices.read", "invoices.write",
            "payments.read", "payments.write",
            "reports.read"
        ],
        "operator": [
            "projects.read",
            "participants.read",
            "invoices.read", "invoices.write",
            "payments.read", "payments.write"
        ],
        "viewer": [
            "projects.read",
            "participants.read",
            "invoices.read",
            "payments.read",
            "reports.read"
        ]
    }
    
    # Vérifier si un des rôles a la permission
    for role in user_roles:
        permissions = role_permissions.get(role, [])
        if "*" in permissions or permission in permissions:
            return True
    
    return False

def require_permission(permission: str):
    """
    Decorator pour vérifier les permissions
    """
    def permission_dependency(current_user: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
        user_roles = current_user.get("roles", [])
        if not has_permission(permission, user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' requise"
            )
        return current_user
    
    return permission_dependency

# Classes pour les modèles d'authentification
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    """Modèle de requête de connexion"""
    username: str = Field(..., description="Nom d'utilisateur ou email")
    password: str = Field(..., description="Mot de passe")

class LoginResponse(BaseModel):
    """Modèle de réponse de connexion"""
    access_token: str = Field(..., description="Token d'accès JWT")
    token_type: str = Field("bearer", description="Type de token")
    expires_in: int = Field(..., description="Durée de validité en secondes")
    user: Dict[str, Any] = Field(..., description="Informations utilisateur")

class RefreshTokenRequest(BaseModel):
    """Modèle de requête de rafraîchissement de token"""
    refresh_token: str = Field(..., description="Token à rafraîchir")

class RefreshTokenResponse(BaseModel):
    """Modèle de réponse de rafraîchissement de token"""
    access_token: str = Field(..., description="Nouveau token d'accès JWT")
    token_type: str = Field("bearer", description="Type de token")
    expires_in: int = Field(..., description="Durée de validité en secondes")

# Fonction utilitaire pour l'authentification
def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authentifier un utilisateur (à implémenter selon votre système)
    """
    # TODO: Implémenter l'authentification réelle
    # Pour l'instant, un utilisateur de test
    if username == "admin" and password == "admin123":
        return {
            "user_id": 1,
            "username": "admin",
            "email": "admin@optimpv.com",
            "roles": ["admin"],
            "full_name": "Administrateur OptimPV"
        }
    
    # Vérifier avec le système de sécurité existant
    try:
        import sys
        import os
        
        # Ajouter le chemin des modules
        current_dir = os.path.dirname(os.path.abspath(__file__))
        modules_path = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
        if modules_path not in sys.path:
            sys.path.append(modules_path)
        
        from modules.security_config import get_default_password_hash
        import hashlib
        
        # Vérifier le mot de passe par défaut
        default_hash = get_default_password_hash()
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if input_hash == default_hash:
            return {
                "user_id": 2,
                "username": username,
                "email": f"{username}@optimpv.com",
                "roles": ["admin"],
                "full_name": f"Utilisateur {username}"
            }
    
    except Exception as e:
        logger.warning(f"Erreur lors de la vérification du mot de passe: {e}")
    
    return None