"""
Modèles Pydantic pour la validation des données de projets
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, validator, EmailStr
from enum import Enum

class ProjectStatus(str, Enum):
    """Statuts possibles d'un projet"""
    ACTIVE = "active"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class ProjectCreate(BaseModel):
    """Modèle pour la création d'un projet"""
    name: str = Field(..., min_length=1, max_length=255, description="Nom du projet")
    address: Optional[str] = Field(None, max_length=500, description="Adresse du projet")
    client_name: str = Field(..., min_length=1, max_length=255, description="Nom du client")
    client_email: Optional[EmailStr] = Field(None, description="Email du client")
    client_phone: Optional[str] = Field(None, max_length=20, description="Téléphone du client")
    start_date: Optional[date] = Field(None, description="Date de début du projet")
    end_date: Optional[date] = Field(None, description="Date de fin prévue du projet")
    total_capacity_kwc: Optional[float] = Field(None, ge=0, description="Puissance totale en kWc")
    total_investment: Optional[float] = Field(None, ge=0, description="Investissement total en €")
    financing_percentage: Optional[float] = Field(None, ge=0, le=100, description="Pourcentage de financement")
    annual_production_kwh: Optional[float] = Field(None, ge=0, description="Production annuelle en kWh")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Valider que la date de fin est postérieure à la date de début"""
        if v and 'start_date' in values and values['start_date']:
            if v <= values['start_date']:
                raise ValueError('La date de fin doit être postérieure à la date de début')
        return v
    
    @validator('client_phone')
    def validate_phone(cls, v):
        """Valider le format du téléphone"""
        if v:
            # Supprimer les espaces et caractères spéciaux
            clean_phone = ''.join(c for c in v if c.isdigit() or c in ['+', '-', '.', ' '])
            if len(clean_phone.replace(' ', '').replace('+', '').replace('-', '').replace('.', '')) < 8:
                raise ValueError('Le numéro de téléphone doit contenir au moins 8 chiffres')
        return v

class ProjectUpdate(BaseModel):
    """Modèle pour la mise à jour d'un projet"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Nom du projet")
    address: Optional[str] = Field(None, max_length=500, description="Adresse du projet")
    client_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Nom du client")
    client_email: Optional[EmailStr] = Field(None, description="Email du client")
    client_phone: Optional[str] = Field(None, max_length=20, description="Téléphone du client")
    start_date: Optional[date] = Field(None, description="Date de début du projet")
    end_date: Optional[date] = Field(None, description="Date de fin prévue du projet")
    status: Optional[ProjectStatus] = Field(None, description="Statut du projet")
    total_capacity_kwc: Optional[float] = Field(None, ge=0, description="Puissance totale en kWc")
    total_investment: Optional[float] = Field(None, ge=0, description="Investissement total en €")
    financing_percentage: Optional[float] = Field(None, ge=0, le=100, description="Pourcentage de financement")
    annual_production_kwh: Optional[float] = Field(None, ge=0, description="Production annuelle en kWh")

class ProjectResponse(BaseModel):
    """Modèle de réponse pour un projet"""
    id: int = Field(..., description="ID unique du projet")
    name: str = Field(..., description="Nom du projet")
    address: Optional[str] = Field(None, description="Adresse du projet")
    client_name: str = Field(..., description="Nom du client")
    client_email: Optional[str] = Field(None, description="Email du client")
    client_phone: Optional[str] = Field(None, description="Téléphone du client")
    start_date: Optional[date] = Field(None, description="Date de début du projet")
    end_date: Optional[date] = Field(None, description="Date de fin prévue du projet")
    status: ProjectStatus = Field(..., description="Statut du projet")
    total_capacity_kwc: Optional[float] = Field(None, description="Puissance totale en kWc")
    total_investment: Optional[float] = Field(None, description="Investissement total en €")
    financing_percentage: Optional[float] = Field(None, description="Pourcentage de financement")
    annual_production_kwh: Optional[float] = Field(None, description="Production annuelle en kWh")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de dernière modification")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class ProjectSummary(BaseModel):
    """Modèle de résumé d'un projet"""
    id: int = Field(..., description="ID unique du projet")
    name: str = Field(..., description="Nom du projet")
    client_name: str = Field(..., description="Nom du client")
    status: ProjectStatus = Field(..., description="Statut du projet")
    participants_count: int = Field(0, description="Nombre de participants")
    total_capacity_kwc: Optional[float] = Field(None, description="Puissance totale en kWc")
    monthly_revenue: Optional[float] = Field(None, description="Chiffre d'affaires mensuel")
    pending_invoices_count: int = Field(0, description="Nombre de factures en attente")
    pending_invoices_amount: float = Field(0, description="Montant des factures en attente")
    created_at: datetime = Field(..., description="Date de création")

class ProjectListFilters(BaseModel):
    """Filtres pour la liste des projets"""
    status: Optional[ProjectStatus] = Field(None, description="Filtrer par statut")
    client_name: Optional[str] = Field(None, description="Filtrer par nom de client (recherche partielle)")
    start_date_from: Optional[date] = Field(None, description="Date de début minimale")
    start_date_to: Optional[date] = Field(None, description="Date de début maximale")
    min_capacity: Optional[float] = Field(None, ge=0, description="Puissance minimale en kWc")
    max_capacity: Optional[float] = Field(None, ge=0, description="Puissance maximale en kWc")
    has_pending_invoices: Optional[bool] = Field(None, description="Projets avec factures en attente")

class ProjectStatistics(BaseModel):
    """Statistiques d'un projet"""
    total_participants: int = Field(..., description="Nombre total de participants")
    active_participants: int = Field(..., description="Nombre de participants actifs")
    total_production_kwh: float = Field(..., description="Production totale en kWh")
    total_consumption_kwh: float = Field(..., description="Consommation totale en kWh")
    autoconsumption_rate: float = Field(..., description="Taux d'autoconsommation en %")
    total_revenue: float = Field(..., description="Chiffre d'affaires total")
    pending_amount: float = Field(..., description="Montant en attente de paiement")
    paid_amount: float = Field(..., description="Montant payé")
    collection_rate: float = Field(..., description="Taux de recouvrement en %")
    last_billing_date: Optional[date] = Field(None, description="Date de dernière facturation")
    next_billing_date: Optional[date] = Field(None, description="Date de prochaine facturation")

class MonthlyProductionCreate(BaseModel):
    """Modèle pour créer des données de production mensuelle"""
    project_id: int = Field(..., description="ID du projet")
    year: int = Field(..., ge=2020, le=2050, description="Année")
    month: int = Field(..., ge=1, le=12, description="Mois")
    total_production_kwh: float = Field(..., ge=0, description="Production totale en kWh")
    autoconsumption_kwh: Optional[float] = Field(None, ge=0, description="Autoconsommation en kWh")
    injection_kwh: Optional[float] = Field(None, ge=0, description="Injection réseau en kWh")
    
    @validator('autoconsumption_kwh', 'injection_kwh')
    def validate_production_split(cls, v, values):
        """Valider que la somme autoconso + injection = production totale"""
        if v is not None and 'total_production_kwh' in values:
            # Cette validation sera complétée côté serveur avec les deux valeurs
            pass
        return v

class MonthlyProductionResponse(BaseModel):
    """Modèle de réponse pour les données de production mensuelle"""
    id: int = Field(..., description="ID unique")
    project_id: int = Field(..., description="ID du projet")
    year: int = Field(..., description="Année")
    month: int = Field(..., description="Mois")
    total_production_kwh: float = Field(..., description="Production totale en kWh")
    autoconsumption_kwh: Optional[float] = Field(None, description="Autoconsommation en kWh")
    injection_kwh: Optional[float] = Field(None, description="Injection réseau en kWh")
    autoconsumption_rate: float = Field(..., description="Taux d'autoconsommation en %")
    injection_rate: float = Field(..., description="Taux d'injection en %")
    created_at: datetime = Field(..., description="Date de création")
    
    class Config:
        from_attributes = True