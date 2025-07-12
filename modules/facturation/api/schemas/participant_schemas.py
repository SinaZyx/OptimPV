"""
Modèles Pydantic pour la validation des données de participants
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, validator, EmailStr
from enum import Enum

class ParticipantType(str, Enum):
    """Types de participants"""
    PRODUCER = "producer"
    CONSUMER = "consumer"

class ParticipantStatus(str, Enum):
    """Statuts des participants"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"

class ParticipantCreate(BaseModel):
    """Modèle pour créer un participant"""
    project_id: int = Field(..., description="ID du projet")
    name: str = Field(..., min_length=1, max_length=255, description="Nom du participant")
    type: ParticipantType = Field(..., description="Type de participant")
    address: Optional[str] = Field(None, max_length=500, description="Adresse du participant")
    contact_email: Optional[EmailStr] = Field(None, description="Email de contact")
    contact_phone: Optional[str] = Field(None, max_length=20, description="Téléphone de contact")
    consumption_profile_id: Optional[str] = Field(None, max_length=50, description="ID du profil de consommation")
    allocation_percentage: Optional[float] = Field(None, ge=0, le=100, description="Pourcentage d'allocation de la production")
    annual_consumption_kwh: Optional[float] = Field(None, ge=0, description="Consommation annuelle en kWh")
    contract_start_date: Optional[date] = Field(None, description="Date de début du contrat")
    contract_end_date: Optional[date] = Field(None, description="Date de fin du contrat")
    tariff_per_kwh: Optional[float] = Field(None, ge=0, description="Tarif par kWh en €")
    
    @validator('contact_phone')
    def validate_phone(cls, v):
        """Valider le format du téléphone"""
        if v:
            # Supprimer les espaces et caractères spéciaux
            clean_phone = ''.join(c for c in v if c.isdigit() or c in ['+', '-', '.', ' '])
            if len(clean_phone.replace(' ', '').replace('+', '').replace('-', '').replace('.', '')) < 8:
                raise ValueError('Le numéro de téléphone doit contenir au moins 8 chiffres')
        return v
    
    @validator('contract_end_date')
    def validate_contract_dates(cls, v, values):
        """Valider que la date de fin de contrat est postérieure à la date de début"""
        if v and 'contract_start_date' in values and values['contract_start_date']:
            if v <= values['contract_start_date']:
                raise ValueError('La date de fin de contrat doit être postérieure à la date de début')
        return v

class ParticipantUpdate(BaseModel):
    """Modèle pour mettre à jour un participant"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Nom du participant")
    type: Optional[ParticipantType] = Field(None, description="Type de participant")
    address: Optional[str] = Field(None, max_length=500, description="Adresse du participant")
    contact_email: Optional[EmailStr] = Field(None, description="Email de contact")
    contact_phone: Optional[str] = Field(None, max_length=20, description="Téléphone de contact")
    consumption_profile_id: Optional[str] = Field(None, max_length=50, description="ID du profil de consommation")
    allocation_percentage: Optional[float] = Field(None, ge=0, le=100, description="Pourcentage d'allocation de la production")
    annual_consumption_kwh: Optional[float] = Field(None, ge=0, description="Consommation annuelle en kWh")
    contract_start_date: Optional[date] = Field(None, description="Date de début du contrat")
    contract_end_date: Optional[date] = Field(None, description="Date de fin du contrat")
    tariff_per_kwh: Optional[float] = Field(None, ge=0, description="Tarif par kWh en €")
    status: Optional[ParticipantStatus] = Field(None, description="Statut du participant")

class ParticipantResponse(BaseModel):
    """Modèle de réponse pour un participant"""
    id: int = Field(..., description="ID unique du participant")
    project_id: int = Field(..., description="ID du projet")
    name: str = Field(..., description="Nom du participant")
    type: ParticipantType = Field(..., description="Type de participant")
    address: Optional[str] = Field(None, description="Adresse du participant")
    contact_email: Optional[str] = Field(None, description="Email de contact")
    contact_phone: Optional[str] = Field(None, description="Téléphone de contact")
    consumption_profile_id: Optional[str] = Field(None, description="ID du profil de consommation")
    allocation_percentage: Optional[float] = Field(None, description="Pourcentage d'allocation de la production")
    annual_consumption_kwh: Optional[float] = Field(None, description="Consommation annuelle en kWh")
    contract_start_date: Optional[date] = Field(None, description="Date de début du contrat")
    contract_end_date: Optional[date] = Field(None, description="Date de fin du contrat")
    tariff_per_kwh: Optional[float] = Field(None, description="Tarif par kWh en €")
    status: ParticipantStatus = Field(ParticipantStatus.ACTIVE, description="Statut du participant")
    created_at: datetime = Field(..., description="Date de création")
    
    # Champs calculés
    total_invoiced_amount: Optional[float] = Field(None, description="Montant total facturé")
    total_paid_amount: Optional[float] = Field(None, description="Montant total payé")
    pending_amount: Optional[float] = Field(None, description="Montant en attente")
    last_invoice_date: Optional[date] = Field(None, description="Date de dernière facture")
    last_payment_date: Optional[date] = Field(None, description="Date de dernier paiement")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class ParticipantSummary(BaseModel):
    """Modèle de résumé d'un participant"""
    id: int = Field(..., description="ID unique du participant")
    name: str = Field(..., description="Nom du participant")
    type: ParticipantType = Field(..., description="Type de participant")
    status: ParticipantStatus = Field(..., description="Statut du participant")
    project_name: str = Field(..., description="Nom du projet")
    allocation_percentage: Optional[float] = Field(None, description="Pourcentage d'allocation")
    total_invoiced: float = Field(0, description="Montant total facturé")
    pending_amount: float = Field(0, description="Montant en attente")
    last_activity: Optional[date] = Field(None, description="Date de dernière activité")

class ParticipantListFilters(BaseModel):
    """Filtres pour la liste des participants"""
    project_id: Optional[int] = Field(None, description="Filtrer par projet")
    type: Optional[ParticipantType] = Field(None, description="Filtrer par type")
    status: Optional[ParticipantStatus] = Field(None, description="Filtrer par statut")
    name: Optional[str] = Field(None, description="Recherche par nom (partielle)")
    has_pending_invoices: Optional[bool] = Field(None, description="Participants avec factures en attente")
    min_allocation: Optional[float] = Field(None, ge=0, le=100, description="Allocation minimale")
    max_allocation: Optional[float] = Field(None, ge=0, le=100, description="Allocation maximale")
    contract_active: Optional[bool] = Field(None, description="Contrat actif uniquement")

class ParticipantStatistics(BaseModel):
    """Statistiques d'un participant"""
    total_consumption_kwh: float = Field(..., description="Consommation totale en kWh")
    total_autoconsumption_kwh: float = Field(..., description="Autoconsommation totale en kWh")
    autoconsumption_rate: float = Field(..., description="Taux d'autoconsommation en %")
    total_invoiced_amount: float = Field(..., description="Montant total facturé")
    total_paid_amount: float = Field(..., description="Montant total payé")
    pending_amount: float = Field(..., description="Montant en attente")
    average_monthly_consumption: float = Field(..., description="Consommation mensuelle moyenne en kWh")
    average_monthly_bill: float = Field(..., description="Facture mensuelle moyenne en €")
    payment_punctuality_score: float = Field(..., description="Score de ponctualité de paiement")
    last_12_months_consumption: List[Dict[str, Any]] = Field(..., description="Consommation des 12 derniers mois")
    last_12_months_bills: List[Dict[str, Any]] = Field(..., description="Factures des 12 derniers mois")

class MonthlyConsumptionCreate(BaseModel):
    """Modèle pour créer des données de consommation mensuelle"""
    participant_id: int = Field(..., description="ID du participant")
    year: int = Field(..., ge=2020, le=2050, description="Année")
    month: int = Field(..., ge=1, le=12, description="Mois")
    consumption_kwh: float = Field(..., ge=0, description="Consommation totale en kWh")
    autoconsumption_kwh: Optional[float] = Field(None, ge=0, description="Autoconsommation en kWh")
    grid_consumption_kwh: Optional[float] = Field(None, ge=0, description="Consommation réseau en kWh")
    
    @validator('autoconsumption_kwh', 'grid_consumption_kwh')
    def validate_consumption_split(cls, v, values):
        """Valider que la somme autoconso + réseau = consommation totale"""
        if v is not None and 'consumption_kwh' in values:
            # Cette validation sera complétée côté serveur avec les deux valeurs
            pass
        return v

class MonthlyConsumptionResponse(BaseModel):
    """Modèle de réponse pour les données de consommation mensuelle"""
    id: int = Field(..., description="ID unique")
    participant_id: int = Field(..., description="ID du participant")
    year: int = Field(..., description="Année")
    month: int = Field(..., description="Mois")
    consumption_kwh: float = Field(..., description="Consommation totale en kWh")
    autoconsumption_kwh: Optional[float] = Field(None, description="Autoconsommation en kWh")
    grid_consumption_kwh: Optional[float] = Field(None, description="Consommation réseau en kWh")
    autoconsumption_rate: float = Field(..., description="Taux d'autoconsommation en %")
    savings_amount: Optional[float] = Field(None, description="Économies réalisées en €")
    created_at: datetime = Field(..., description="Date de création")
    
    class Config:
        from_attributes = True

class BulkParticipantCreate(BaseModel):
    """Modèle pour création en lot de participants"""
    project_id: int = Field(..., description="ID du projet")
    participants: List[ParticipantCreate] = Field(..., min_items=1, description="Liste des participants à créer")
    auto_calculate_allocation: bool = Field(False, description="Calculer automatiquement les allocations")
    default_tariff_per_kwh: Optional[float] = Field(None, ge=0, description="Tarif par défaut par kWh")

class BulkParticipantOperation(BaseModel):
    """Modèle pour opérations en lot sur les participants"""
    participant_ids: List[int] = Field(..., min_items=1, description="IDs des participants")
    operation: str = Field(..., description="Type d'opération (update_status, update_tariff, etc.)")
    parameters: Dict[str, Any] = Field(..., description="Paramètres de l'opération")

class ParticipantContract(BaseModel):
    """Modèle pour le contrat d'un participant"""
    participant_id: int = Field(..., description="ID du participant")
    contract_type: str = Field(..., description="Type de contrat")
    start_date: date = Field(..., description="Date de début")
    end_date: Optional[date] = Field(None, description="Date de fin")
    tariff_structure: Dict[str, Any] = Field(..., description="Structure tarifaire")
    terms_and_conditions: Optional[str] = Field(None, description="Conditions générales")
    auto_renewal: bool = Field(False, description="Renouvellement automatique")
    notice_period_days: int = Field(30, ge=0, description="Préavis en jours")

class ParticipantContractResponse(BaseModel):
    """Modèle de réponse pour un contrat de participant"""
    id: int = Field(..., description="ID unique du contrat")
    participant_id: int = Field(..., description="ID du participant")
    contract_number: str = Field(..., description="Numéro de contrat")
    contract_type: str = Field(..., description="Type de contrat")
    start_date: date = Field(..., description="Date de début")
    end_date: Optional[date] = Field(None, description="Date de fin")
    status: str = Field(..., description="Statut du contrat")
    tariff_structure: Dict[str, Any] = Field(..., description="Structure tarifaire")
    terms_and_conditions: Optional[str] = Field(None, description="Conditions générales")
    auto_renewal: bool = Field(..., description="Renouvellement automatique")
    notice_period_days: int = Field(..., description="Préavis en jours")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de modification")
    
    class Config:
        from_attributes = True