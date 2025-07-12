"""
Modèles Pydantic pour la validation des données de paiements
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
from enum import Enum

class PaymentMethod(str, Enum):
    """Méthodes de paiement disponibles"""
    BANK_TRANSFER = "bank_transfer"
    SEPA_DIRECT_DEBIT = "sepa_direct_debit"
    CREDIT_CARD = "credit_card"
    CHECK = "check"
    CASH = "cash"
    OTHER = "other"

class PaymentStatus(str, Enum):
    """Statuts des paiements"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class BankTransactionStatus(str, Enum):
    """Statuts des transactions bancaires"""
    PENDING = "pending"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    UNMATCHED = "unmatched"
    DISPUTED = "disputed"

class PaymentCreate(BaseModel):
    """Modèle pour créer un paiement"""
    invoice_id: int = Field(..., description="ID de la facture")
    amount: float = Field(..., gt=0, description="Montant du paiement en €")
    payment_date: date = Field(..., description="Date du paiement")
    payment_method: PaymentMethod = Field(..., description="Méthode de paiement")
    transaction_id: Optional[str] = Field(None, max_length=100, description="ID de transaction")
    reference: Optional[str] = Field(None, max_length=100, description="Référence du paiement")
    notes: Optional[str] = Field(None, max_length=1000, description="Notes sur le paiement")
    
    @validator('payment_date')
    def validate_payment_date(cls, v):
        """Valider que la date de paiement n'est pas dans le futur"""
        if v > date.today():
            raise ValueError('La date de paiement ne peut pas être dans le futur')
        return v

class PaymentUpdate(BaseModel):
    """Modèle pour mettre à jour un paiement"""
    amount: Optional[float] = Field(None, gt=0, description="Montant du paiement en €")
    payment_date: Optional[date] = Field(None, description="Date du paiement")
    payment_method: Optional[PaymentMethod] = Field(None, description="Méthode de paiement")
    transaction_id: Optional[str] = Field(None, max_length=100, description="ID de transaction")
    reference: Optional[str] = Field(None, max_length=100, description="Référence du paiement")
    notes: Optional[str] = Field(None, max_length=1000, description="Notes sur le paiement")
    status: Optional[PaymentStatus] = Field(None, description="Statut du paiement")

class PaymentResponse(BaseModel):
    """Modèle de réponse pour un paiement"""
    id: int = Field(..., description="ID unique du paiement")
    invoice_id: int = Field(..., description="ID de la facture")
    amount: float = Field(..., description="Montant du paiement en €")
    payment_date: date = Field(..., description="Date du paiement")
    payment_method: PaymentMethod = Field(..., description="Méthode de paiement")
    transaction_id: Optional[str] = Field(None, description="ID de transaction")
    reference: Optional[str] = Field(None, description="Référence du paiement")
    notes: Optional[str] = Field(None, description="Notes sur le paiement")
    status: PaymentStatus = Field(..., description="Statut du paiement")
    created_at: datetime = Field(..., description="Date de création")
    
    # Informations enrichies
    invoice_number: Optional[str] = Field(None, description="Numéro de facture")
    participant_name: Optional[str] = Field(None, description="Nom du participant")
    remaining_invoice_amount: Optional[float] = Field(None, description="Montant restant sur la facture")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class PaymentSummary(BaseModel):
    """Modèle de résumé d'un paiement"""
    id: int = Field(..., description="ID unique du paiement")
    invoice_number: str = Field(..., description="Numéro de facture")
    participant_name: str = Field(..., description="Nom du participant")
    amount: float = Field(..., description="Montant du paiement en €")
    payment_date: date = Field(..., description="Date du paiement")
    payment_method: PaymentMethod = Field(..., description="Méthode de paiement")
    status: PaymentStatus = Field(..., description="Statut du paiement")

class PaymentListFilters(BaseModel):
    """Filtres pour la liste des paiements"""
    invoice_id: Optional[int] = Field(None, description="Filtrer par facture")
    participant_id: Optional[int] = Field(None, description="Filtrer par participant")
    project_id: Optional[int] = Field(None, description="Filtrer par projet")
    payment_method: Optional[PaymentMethod] = Field(None, description="Filtrer par méthode de paiement")
    status: Optional[PaymentStatus] = Field(None, description="Filtrer par statut")
    payment_date_from: Optional[date] = Field(None, description="Date de paiement minimale")
    payment_date_to: Optional[date] = Field(None, description="Date de paiement maximale")
    min_amount: Optional[float] = Field(None, ge=0, description="Montant minimal")
    max_amount: Optional[float] = Field(None, ge=0, description="Montant maximal")
    search_term: Optional[str] = Field(None, description="Recherche dans référence ou transaction")

class PaymentStatistics(BaseModel):
    """Statistiques des paiements"""
    total_payments: int = Field(..., description="Nombre total de paiements")
    total_amount: float = Field(..., description="Montant total des paiements")
    average_payment_amount: float = Field(..., description="Montant moyen des paiements")
    payments_by_method: Dict[str, int] = Field(..., description="Répartition par méthode de paiement")
    payments_by_status: Dict[str, int] = Field(..., description="Répartition par statut")
    monthly_payments: List[Dict[str, Any]] = Field(..., description="Paiements par mois")
    collection_efficiency: float = Field(..., description="Efficacité de recouvrement en %")

class BankTransactionCreate(BaseModel):
    """Modèle pour créer une transaction bancaire"""
    transaction_date: date = Field(..., description="Date de transaction")
    value_date: Optional[date] = Field(None, description="Date de valeur")
    amount: float = Field(..., description="Montant en €")
    description: Optional[str] = Field(None, max_length=500, description="Description de la transaction")
    reference: Optional[str] = Field(None, max_length=100, description="Référence bancaire")
    account_number: Optional[str] = Field(None, max_length=50, description="Numéro de compte")
    beneficiary_name: Optional[str] = Field(None, max_length=255, description="Nom du bénéficiaire")
    debtor_name: Optional[str] = Field(None, max_length=255, description="Nom du débiteur")
    transaction_id: Optional[str] = Field(None, max_length=100, description="ID unique de transaction")
    import_batch_id: Optional[str] = Field(None, max_length=50, description="ID du lot d'import")

class BankTransactionResponse(BaseModel):
    """Modèle de réponse pour une transaction bancaire"""
    id: int = Field(..., description="ID unique de la transaction")
    transaction_date: date = Field(..., description="Date de transaction")
    value_date: Optional[date] = Field(None, description="Date de valeur")
    amount: float = Field(..., description="Montant en €")
    description: Optional[str] = Field(None, description="Description de la transaction")
    reference: Optional[str] = Field(None, description="Référence bancaire")
    account_number: Optional[str] = Field(None, description="Numéro de compte")
    beneficiary_name: Optional[str] = Field(None, description="Nom du bénéficiaire")
    debtor_name: Optional[str] = Field(None, description="Nom du débiteur")
    transaction_id: Optional[str] = Field(None, description="ID unique de transaction")
    import_batch_id: Optional[str] = Field(None, description="ID du lot d'import")
    status: BankTransactionStatus = Field(..., description="Statut de la transaction")
    matched_invoice_id: Optional[int] = Field(None, description="ID de la facture associée")
    confidence_score: float = Field(..., description="Score de confiance du rapprochement")
    created_at: datetime = Field(..., description="Date de création")
    
    class Config:
        from_attributes = True

class PaymentReconciliation(BaseModel):
    """Modèle pour le rapprochement de paiements"""
    bank_transaction_id: int = Field(..., description="ID de la transaction bancaire")
    invoice_id: int = Field(..., description="ID de la facture à associer")
    amount: Optional[float] = Field(None, gt=0, description="Montant à rapprocher (optionnel)")
    notes: Optional[str] = Field(None, max_length=500, description="Notes sur le rapprochement")

class PaymentScheduleCreate(BaseModel):
    """Modèle pour créer un échéancier de paiement"""
    invoice_id: int = Field(..., description="ID de la facture")
    total_installments: int = Field(..., ge=2, le=12, description="Nombre total d'échéances")
    first_due_date: date = Field(..., description="Date de première échéance")
    installment_frequency_days: int = Field(30, ge=1, le=365, description="Fréquence en jours entre échéances")
    
    @validator('first_due_date')
    def validate_first_due_date(cls, v):
        """Valider que la première échéance n'est pas dans le passé"""
        if v < date.today():
            raise ValueError('La première échéance ne peut pas être dans le passé')
        return v

class PaymentScheduleResponse(BaseModel):
    """Modèle de réponse pour un échéancier de paiement"""
    id: int = Field(..., description="ID unique de l'échéance")
    invoice_id: int = Field(..., description="ID de la facture")
    installment_number: int = Field(..., description="Numéro de l'échéance")
    total_installments: int = Field(..., description="Nombre total d'échéances")
    amount: float = Field(..., description="Montant de l'échéance")
    due_date: date = Field(..., description="Date d'échéance")
    status: str = Field(..., description="Statut (pending, paid, overdue)")
    payment_id: Optional[int] = Field(None, description="ID du paiement associé")
    notes: Optional[str] = Field(None, description="Notes")
    created_at: datetime = Field(..., description="Date de création")
    
    class Config:
        from_attributes = True

class BulkPaymentCreate(BaseModel):
    """Modèle pour création en lot de paiements"""
    payments: List[PaymentCreate] = Field(..., min_items=1, description="Liste des paiements à créer")
    validate_amounts: bool = Field(True, description="Valider que les montants correspondent aux factures")
    auto_update_invoice_status: bool = Field(True, description="Mettre à jour automatiquement le statut des factures")

class PaymentExport(BaseModel):
    """Modèle pour l'export de paiements"""
    format: str = Field(..., regex="^(csv|xlsx|pdf)$", description="Format d'export")
    filters: Optional[PaymentListFilters] = Field(None, description="Filtres à appliquer")
    include_invoice_details: bool = Field(False, description="Inclure les détails des factures")
    include_participant_details: bool = Field(False, description="Inclure les détails des participants")
    date_range_from: Optional[date] = Field(None, description="Début de période")
    date_range_to: Optional[date] = Field(None, description="Fin de période")