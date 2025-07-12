"""
Serveur API FastAPI pour le module de facturation OptimPV
Fournit une API REST complète avec documentation automatique Swagger/OpenAPI
"""

import logging
from datetime import datetime
from typing import List, Dict, Any
import os
import sys

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
import uvicorn

# Ajouter le chemin des modules au path Python
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if modules_path not in sys.path:
    sys.path.append(modules_path)

# Import des middlewares
from .middleware.auth import JWTAuthMiddleware, verify_token
from .middleware.cors import setup_cors
from .middleware.logging import setup_logging, log_request
from .middleware.rate_limiting import RateLimitMiddleware

# Import des routes
from .routes.projects import router as projects_router
from .routes.participants import router as participants_router
from .routes.invoices import router as invoices_router
from .routes.payments import router as payments_router
from .routes.reports import router as reports_router
from .routes.webhooks import router as webhooks_router

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration de l'application
app = FastAPI(
    title="OptimPV API de Facturation",
    description="""
    API REST complète pour le système de facturation OptimPV.
    
    ## Fonctionnalités
    
    * **Gestion des projets** - CRUD complet pour les projets photovoltaïques
    * **Gestion des participants** - Producteurs et consommateurs d'énergie
    * **Facturation** - Création, modification et suivi des factures
    * **Paiements** - Enregistrement et suivi des paiements
    * **Rapports** - Export de rapports et analytics
    * **Webhooks** - Intégration avec des systèmes externes
    
    ## Authentification
    
    L'API utilise l'authentification JWT. Incluez le token dans l'en-tête Authorization:
    ```
    Authorization: Bearer <votre_token_jwt>
    ```
    
    ## Limitation de débit
    
    L'API est limitée à 100 requêtes par minute par client.
    
    ## Gestion d'erreurs
    
    L'API retourne des codes d'erreur HTTP standards avec des messages détaillés en JSON.
    """,
    version="1.0.0",
    contact={
        "name": "Support OptimPV",
        "email": "support@optimpv.com",
    },
    license_info={
        "name": "Propriétaire",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configuration des middlewares
setup_cors(app)
setup_logging(app)

# Middleware d'authentification JWT
app.add_middleware(JWTAuthMiddleware)

# Middleware de limitation de débit
app.add_middleware(RateLimitMiddleware, calls=100, period=60)

# Middleware de logging des requêtes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()
    
    log_request(
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time,
        client_ip=request.client.host if request.client else "unknown"
    )
    
    return response

# Gestionnaire d'erreurs global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erreur non gérée: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Erreur interne du serveur",
            "detail": "Une erreur inattendue s'est produite",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

# Routes de base
@app.get("/", tags=["Root"])
async def root():
    """Point d'entrée de l'API"""
    return {
        "message": "API de Facturation OptimPV",
        "version": "1.0.0",
        "documentation": "/docs",
        "timestamp": datetime.now().isoformat(),
        "status": "operational"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Vérification de l'état de santé de l'API"""
    try:
        # Vérifier la base de données
        from modules.facturation.database import BillingDatabase
        db = BillingDatabase()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Erreur lors du health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service indisponible - problème de base de données"
        )

@app.get("/version", tags=["Info"])
async def get_version():
    """Informations sur la version de l'API"""
    return {
        "api_version": "1.0.0",
        "openapi_version": "3.0.2",
        "build_date": "2025-01-11",
        "python_version": "3.8+",
        "dependencies": {
            "fastapi": ">=0.100.0",
            "pydantic": ">=2.0.0",
            "uvicorn": ">=0.20.0"
        }
    }

# Inclusion des routers
app.include_router(
    projects_router,
    prefix="/api/v1/projects",
    tags=["Projets"],
    dependencies=[Depends(verify_token)]
)

app.include_router(
    participants_router,
    prefix="/api/v1/participants",
    tags=["Participants"],
    dependencies=[Depends(verify_token)]
)

app.include_router(
    invoices_router,
    prefix="/api/v1/invoices",
    tags=["Factures"],
    dependencies=[Depends(verify_token)]
)

app.include_router(
    payments_router,
    prefix="/api/v1/payments",
    tags=["Paiements"],
    dependencies=[Depends(verify_token)]
)

app.include_router(
    reports_router,
    prefix="/api/v1/reports",
    tags=["Rapports"],
    dependencies=[Depends(verify_token)]
)

app.include_router(
    webhooks_router,
    prefix="/api/v1/webhooks",
    tags=["Webhooks"],
    dependencies=[Depends(verify_token)]
)

# Personnalisation de la documentation OpenAPI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        contact=app.contact,
        license_info=app.license_info,
    )
    
    # Ajouter des exemples et des descriptions personnalisées
    openapi_schema["info"]["x-logo"] = {
        "url": "https://optimpv.com/logo.png"
    }
    
    # Configuration de la sécurité JWT
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Token JWT pour l'authentification"
        }
    }
    
    # Appliquer la sécurité à toutes les routes
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method not in ["options"]:
                openapi_schema["paths"][path][method]["security"] = [
                    {"BearerAuth": []}
                ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Configuration pour le démarrage de l'application
def start_api_server(host: str = "0.0.0.0", port: int = 8001, debug: bool = False):
    """Démarre le serveur API FastAPI"""
    logger.info(f"Démarrage du serveur API OptimPV Facturation sur {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        debug=debug,
        log_level="info" if not debug else "debug",
        reload=debug,
        access_log=True
    )

if __name__ == "__main__":
    # Démarrage en mode développement
    import argparse
    
    parser = argparse.ArgumentParser(description="Serveur API REST OptimPV Facturation")
    parser.add_argument("--host", default="0.0.0.0", help="Adresse d'écoute")
    parser.add_argument("--port", type=int, default=8001, help="Port d'écoute")
    parser.add_argument("--debug", action="store_true", help="Mode debug")
    
    args = parser.parse_args()
    start_api_server(host=args.host, port=args.port, debug=args.debug)