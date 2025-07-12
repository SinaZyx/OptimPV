"""
Modèles de réponse standardisés pour l'API REST de facturation OptimPV
"""

from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

T = TypeVar('T')

class ResponseStatus(str, Enum):
    """Statuts de réponse possibles"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class PaginationInfo(BaseModel):
    """Informations de pagination"""
    page: int = Field(..., description="Numéro de la page actuelle")
    per_page: int = Field(..., description="Nombre d'éléments par page")
    total: int = Field(..., description="Nombre total d'éléments")
    pages: int = Field(..., description="Nombre total de pages")
    has_next: bool = Field(..., description="Y a-t-il une page suivante")
    has_prev: bool = Field(..., description="Y a-t-il une page précédente")

class APIResponse(BaseModel, Generic[T]):
    """Réponse API standardisée"""
    status: ResponseStatus = Field(..., description="Statut de la réponse")
    message: str = Field(..., description="Message descriptif")
    data: Optional[T] = Field(None, description="Données de la réponse")
    timestamp: datetime = Field(default_factory=datetime.now, description="Horodatage de la réponse")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PaginatedResponse(BaseModel, Generic[T]):
    """Réponse paginée standardisée"""
    status: ResponseStatus = Field(..., description="Statut de la réponse")
    message: str = Field(..., description="Message descriptif")
    data: List[T] = Field(..., description="Liste des données")
    pagination: PaginationInfo = Field(..., description="Informations de pagination")
    timestamp: datetime = Field(default_factory=datetime.now, description="Horodatage de la réponse")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée"""
    status: ResponseStatus = ResponseStatus.ERROR
    error: str = Field(..., description="Type d'erreur")
    message: str = Field(..., description="Message d'erreur détaillé")
    code: Optional[str] = Field(None, description="Code d'erreur spécifique")
    details: Optional[Dict[str, Any]] = Field(None, description="Détails supplémentaires de l'erreur")
    timestamp: datetime = Field(default_factory=datetime.now, description="Horodatage de l'erreur")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ValidationErrorDetail(BaseModel):
    """Détail d'une erreur de validation"""
    field: str = Field(..., description="Champ en erreur")
    message: str = Field(..., description="Message d'erreur")
    value: Optional[Any] = Field(None, description="Valeur fournie")

class ValidationErrorResponse(BaseModel):
    """Réponse d'erreur de validation"""
    status: ResponseStatus = ResponseStatus.ERROR
    error: str = "validation_error"
    message: str = "Erreur de validation des données"
    errors: List[ValidationErrorDetail] = Field(..., description="Liste des erreurs de validation")
    timestamp: datetime = Field(default_factory=datetime.now, description="Horodatage de l'erreur")

class SuccessResponse(BaseModel):
    """Réponse de succès simple"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field(..., description="Message de succès")
    timestamp: datetime = Field(default_factory=datetime.now, description="Horodatage")

class CreatedResponse(BaseModel):
    """Réponse de création d'entité"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field(..., description="Message de succès")
    id: int = Field(..., description="ID de l'entité créée")
    location: Optional[str] = Field(None, description="URL de l'entité créée")
    timestamp: datetime = Field(default_factory=datetime.now, description="Horodatage")

class UpdatedResponse(BaseModel):
    """Réponse de mise à jour d'entité"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field(..., description="Message de succès")
    updated_fields: Optional[List[str]] = Field(None, description="Champs mis à jour")
    timestamp: datetime = Field(default_factory=datetime.now, description="Horodatage")

class DeletedResponse(BaseModel):
    """Réponse de suppression d'entité"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field(..., description="Message de succès")
    deleted_count: int = Field(1, description="Nombre d'entités supprimées")
    timestamp: datetime = Field(default_factory=datetime.now, description="Horodatage")

class HealthCheckResponse(BaseModel):
    """Réponse du health check"""
    status: str = Field(..., description="Statut du service")
    database: str = Field(..., description="Statut de la base de données")
    version: str = Field(..., description="Version de l'API")
    timestamp: datetime = Field(default_factory=datetime.now, description="Horodatage")
    uptime: Optional[str] = Field(None, description="Temps de fonctionnement")

class VersionResponse(BaseModel):
    """Réponse des informations de version"""
    api_version: str = Field(..., description="Version de l'API")
    openapi_version: str = Field(..., description="Version OpenAPI")
    build_date: str = Field(..., description="Date de build")
    python_version: str = Field(..., description="Version Python requise")
    dependencies: Dict[str, str] = Field(..., description="Dépendances principales")

class WebhookEventResponse(BaseModel):
    """Réponse d'événement webhook"""
    event_id: str = Field(..., description="ID unique de l'événement")
    event_type: str = Field(..., description="Type d'événement")
    status: str = Field(..., description="Statut d'envoi")
    sent_at: datetime = Field(..., description="Date d'envoi")
    retry_count: int = Field(0, description="Nombre de tentatives")
    
class BulkOperationResponse(BaseModel):
    """Réponse d'opération en lot"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field(..., description="Message de succès")
    total_processed: int = Field(..., description="Nombre total d'éléments traités")
    successful: int = Field(..., description="Nombre d'éléments traités avec succès")
    failed: int = Field(..., description="Nombre d'éléments en erreur")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Détails des erreurs")
    timestamp: datetime = Field(default_factory=datetime.now, description="Horodatage")

class ExportResponse(BaseModel):
    """Réponse d'export de données"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field(..., description="Message de succès")
    file_url: str = Field(..., description="URL de téléchargement du fichier")
    file_name: str = Field(..., description="Nom du fichier exporté")
    file_size: int = Field(..., description="Taille du fichier en octets")
    format: str = Field(..., description="Format du fichier (csv, xlsx, pdf)")
    expires_at: Optional[datetime] = Field(None, description="Date d'expiration du lien")
    timestamp: datetime = Field(default_factory=datetime.now, description="Horodatage")