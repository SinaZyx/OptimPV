"""
Modèles Pydantic pour la validation des données de facturation
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum

class InvoiceStatus(str, Enum):
    """Statuts possibles d'une facture"""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    PARTIAL_PAID = "partial_paid"

class ItemType(str, Enum):
    """Types d'éléments de facture"""
    AUTOCONSUMPTION = "autoconsumption"
    SUBSCRIPTION = "subscription"
    MAINTENANCE = "maintenance"
    INSTALLATION = "installation"
    OTHER = "other"

class InvoiceItemCreate(BaseModel):
    """Modèle pour créer un élément de facture"""
    description: str = Field(..., min_length=1, max_length=500, description="Description de l'élément")
    quantity: float = Field(..., gt=0, description="Quantité")
    unit_price: float = Field(..., ge=0, description="Prix unitaire en €")
    item_type: ItemType = Field(ItemType.OTHER, description="Type d'élément")
    
    @property
    def total_price(self) -> float:
        """Calcul automatique du prix total"""
        return self.quantity * self.unit_price

class InvoiceItemUpdate(BaseModel):
    """Modèle pour mettre à jour un élément de facture"""
    description: Optional[str] = Field(None, min_length=1, max_length=500, description="Description de l'élément")
    quantity: Optional[float] = Field(None, gt=0, description="Quantité")
    unit_price: Optional[float] = Field(None, ge=0, description="Prix unitaire en €")
    item_type: Optional[ItemType] = Field(None, description="Type d'élément")

class InvoiceItemResponse(BaseModel):
    """Modèle de réponse pour un élément de facture"""
    id: int = Field(..., description="ID unique de l'élément")
    invoice_id: int = Field(..., description="ID de la facture")
    description: str = Field(..., description="Description de l'élément")
    quantity: float = Field(..., description="Quantité")
    unit_price: float = Field(..., description="Prix unitaire en €")
    total_price: float = Field(..., description="Prix total en €")
    item_type: ItemType = Field(..., description="Type d'élément")
    created_at: datetime = Field(..., description="Date de création")
    
    class Config:
        from_attributes = True

class InvoiceCreate(BaseModel):
    """Modèle pour créer une facture"""
    billing_period_id: int = Field(..., description="ID de la période de facturation")
    participant_id: int = Field(..., description="ID du participant")
    issue_date: date = Field(..., description="Date d'émission")
    due_date: date = Field(..., description="Date d'échéance")
    tax_rate: float = Field(0.20, ge=0, le=1, description="Taux de TVA (par défaut 20%)")
    items: List[InvoiceItemCreate] = Field(..., min_items=1, description="Éléments de la facture")
    
    @validator('due_date')
    def validate_due_date(cls, v, values):
        """Valider que la date d'échéance est postérieure à la date d'émission"""
        if 'issue_date' in values and v <= values['issue_date']:
            raise ValueError('La date d\'échéance doit être postérieure à la date d\'émission')
        return v
    
    @root_validator
    def validate_totals(cls, values):
        """Valider les totaux de la facture"""
        items = values.get('items', [])
        if items:
            subtotal = sum(item.total_price for item in items)
            if subtotal <= 0:
                raise ValueError('Le montant total de la facture doit être positif')
        return values

class InvoiceUpdate(BaseModel):
    """Modèle pour mettre à jour une facture"""
    issue_date: Optional[date] = Field(None, description="Date d'émission")
    due_date: Optional[date] = Field(None, description="Date d'échéance")
    tax_rate: Optional[float] = Field(None, ge=0, le=1, description="Taux de TVA")
    status: Optional[InvoiceStatus] = Field(None, description="Statut de la facture")
    
    @validator('due_date')
    def validate_due_date(cls, v, values):
        """Valider que la date d'échéance est postérieure à la date d'émission"""
        if v and 'issue_date' in values and values['issue_date']:
            if v <= values['issue_date']:
                raise ValueError('La date d\'échéance doit être postérieure à la date d\'émission')
        return v

class InvoiceResponse(BaseModel):
    """Modèle de réponse pour une facture"""
    id: int = Field(..., description="ID unique de la facture")
    billing_period_id: int = Field(..., description="ID de la période de facturation")
    participant_id: int = Field(..., description="ID du participant")
    invoice_number: str = Field(..., description="Numéro de facture")
    issue_date: date = Field(..., description="Date d'émission")
    due_date: date = Field(..., description="Date d'échéance")
    subtotal: float = Field(..., description="Sous-total HT en €")
    tax_rate: float = Field(..., description="Taux de TVA")
    tax_amount: float = Field(..., description="Montant de TVA en €")
    total_amount: float = Field(..., description="Montant total TTC en €")
    status: InvoiceStatus = Field(..., description="Statut de la facture")
    payment_date: Optional[date] = Field(None, description="Date de paiement")
    created_at: datetime = Field(..., description="Date de création")
    items: List[InvoiceItemResponse] = Field([], description="Éléments de la facture")
    
    # Champs calculés
    remaining_amount: float = Field(..., description="Montant restant à payer")
    days_overdue: int = Field(0, description="Nombre de jours de retard")
    is_overdue: bool = Field(..., description="Facture en retard")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class InvoiceSummary(BaseModel):
    """Modèle de résumé d'une facture"""
    id: int = Field(..., description="ID unique de la facture")
    invoice_number: str = Field(..., description="Numéro de facture")
    participant_name: str = Field(..., description="Nom du participant")
    issue_date: date = Field(..., description="Date d'émission")
    due_date: date = Field(..., description="Date d'échéance")
    total_amount: float = Field(..., description="Montant total TTC en €")
    status: InvoiceStatus = Field(..., description="Statut de la facture")
    days_overdue: int = Field(0, description="Nombre de jours de retard")

class InvoiceListFilters(BaseModel):
    """Filtres pour la liste des factures"""
    status: Optional[InvoiceStatus] = Field(None, description="Filtrer par statut")
    participant_id: Optional[int] = Field(None, description="Filtrer par participant")
    project_id: Optional[int] = Field(None, description="Filtrer par projet")
    issue_date_from: Optional[date] = Field(None, description="Date d'émission minimale")
    issue_date_to: Optional[date] = Field(None, description="Date d'émission maximale")
    due_date_from: Optional[date] = Field(None, description="Date d'échéance minimale")
    due_date_to: Optional[date] = Field(None, description="Date d'échéance maximale")
    min_amount: Optional[float] = Field(None, ge=0, description="Montant minimal")
    max_amount: Optional[float] = Field(None, ge=0, description="Montant maximal")
    overdue_only: Optional[bool] = Field(None, description="Factures en retard uniquement")
    search_term: Optional[str] = Field(None, description="Recherche dans numéro ou participant")

class InvoiceStatistics(BaseModel):
    """Statistiques des factures"""
    total_invoices: int = Field(..., description="Nombre total de factures")
    total_amount: float = Field(..., description="Montant total des factures")
    paid_invoices: int = Field(..., description="Nombre de factures payées")
    paid_amount: float = Field(..., description="Montant payé")
    pending_invoices: int = Field(..., description="Nombre de factures en attente")
    pending_amount: float = Field(..., description="Montant en attente")
    overdue_invoices: int = Field(..., description="Nombre de factures en retard")
    overdue_amount: float = Field(..., description="Montant en retard")
    collection_rate: float = Field(..., description="Taux de recouvrement en %")
    average_payment_delay: float = Field(..., description="Délai moyen de paiement en jours")

class BulkInvoiceCreate(BaseModel):
    """Modèle pour création en lot de factures"""
    billing_period_id: int = Field(..., description="ID de la période de facturation")
    participant_ids: List[int] = Field(..., min_items=1, description="IDs des participants")
    issue_date: date = Field(..., description="Date d'émission")
    payment_terms_days: int = Field(30, ge=1, le=365, description="Délai de paiement en jours")
    tax_rate: float = Field(0.20, ge=0, le=1, description="Taux de TVA")
    autoconsumption_price_per_kwh: float = Field(..., gt=0, description="Prix par kWh d'autoconsommation")
    
class BulkInvoiceOperation(BaseModel):
    """Modèle pour opérations en lot sur les factures"""
    invoice_ids: List[int] = Field(..., min_items=1, description="IDs des factures")
    operation: str = Field(..., description="Type d'opération (send, cancel, etc.)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Paramètres de l'opération")

class CreditNoteCreate(BaseModel):
    """Modèle pour créer un avoir"""
    invoice_id: int = Field(..., description="ID de la facture à créditer")
    reason: str = Field(..., min_length=1, max_length=500, description="Raison de l'avoir")
    amount: float = Field(..., gt=0, description="Montant de l'avoir")
    tax_rate: Optional[float] = Field(None, ge=0, le=1, description="Taux de TVA (hérite de la facture si non spécifié)")

class CreditNoteResponse(BaseModel):
    """Modèle de réponse pour un avoir"""
    id: int = Field(..., description="ID unique de l'avoir")
    invoice_id: int = Field(..., description="ID de la facture associée")
    credit_note_number: str = Field(..., description="Numéro de l'avoir")
    issue_date: date = Field(..., description="Date d'émission")
    reason: str = Field(..., description="Raison de l'avoir")
    subtotal: float = Field(..., description="Sous-total HT en €")
    tax_rate: float = Field(..., description="Taux de TVA")
    tax_amount: float = Field(..., description="Montant de TVA en €")
    total_amount: float = Field(..., description="Montant total TTC en €")
    status: str = Field(..., description="Statut de l'avoir")
    created_at: datetime = Field(..., description="Date de création")
    
    class Config:
        from_attributes = True