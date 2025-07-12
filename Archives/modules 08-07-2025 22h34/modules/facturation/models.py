"""
Data models for PMO billing system
Defines data structures and business logic
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from enum import Enum

class ProjectStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class ParticipantType(Enum):
    PRODUCER = "producer"
    CONSUMER = "consumer"

class InvoiceStatus(Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class BillingPeriodStatus(Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    SENT = "sent"
    PAID = "paid"

@dataclass
class Project:
    """Project data model"""
    id: Optional[int] = None
    name: str = ""
    address: str = ""
    client_name: str = ""
    client_email: str = ""
    client_phone: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    total_capacity_kwc: float = 0.0
    total_investment: float = 0.0
    financing_percentage: float = 0.0
    annual_production_kwh: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'client_name': self.client_name,
            'client_email': self.client_email,
            'client_phone': self.client_phone,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status.value if isinstance(self.status, ProjectStatus) else self.status,
            'total_capacity_kwc': self.total_capacity_kwc,
            'total_investment': self.total_investment,
            'financing_percentage': self.financing_percentage,
            'annual_production_kwh': self.annual_production_kwh
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create from dictionary"""
        project = cls()
        for key, value in data.items():
            if hasattr(project, key):
                if key in ['start_date', 'end_date'] and value:
                    setattr(project, key, date.fromisoformat(value) if isinstance(value, str) else value)
                elif key == 'status':
                    setattr(project, key, ProjectStatus(value) if isinstance(value, str) else value)
                else:
                    setattr(project, key, value)
        return project

@dataclass
class Participant:
    """Participant data model"""
    id: Optional[int] = None
    project_id: int = 0
    name: str = ""
    type: ParticipantType = ParticipantType.CONSUMER
    address: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    consumption_profile_id: str = ""
    allocation_percentage: float = 0.0
    annual_consumption_kwh: float = 0.0
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'type': self.type.value if isinstance(self.type, ParticipantType) else self.type,
            'address': self.address,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'consumption_profile_id': self.consumption_profile_id,
            'allocation_percentage': self.allocation_percentage,
            'annual_consumption_kwh': self.annual_consumption_kwh
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Participant':
        """Create from dictionary"""
        participant = cls()
        for key, value in data.items():
            if hasattr(participant, key):
                if key == 'type':
                    setattr(participant, key, ParticipantType(value) if isinstance(value, str) else value)
                else:
                    setattr(participant, key, value)
        return participant

@dataclass
class MonthlyProduction:
    """Monthly production data model"""
    id: Optional[int] = None
    project_id: int = 0
    year: int = 0
    month: int = 0
    total_production_kwh: float = 0.0
    autoconsumption_kwh: float = 0.0
    injection_kwh: float = 0.0
    created_at: Optional[datetime] = None
    
    @property
    def autoconsumption_rate(self) -> float:
        """Calculate autoconsumption rate"""
        if self.total_production_kwh > 0:
            return (self.autoconsumption_kwh / self.total_production_kwh) * 100
        return 0.0
    
    @property
    def injection_rate(self) -> float:
        """Calculate injection rate"""
        if self.total_production_kwh > 0:
            return (self.injection_kwh / self.total_production_kwh) * 100
        return 0.0

@dataclass
class MonthlyConsumption:
    """Monthly consumption data model"""
    id: Optional[int] = None
    participant_id: int = 0
    year: int = 0
    month: int = 0
    consumption_kwh: float = 0.0
    autoconsumption_kwh: float = 0.0
    grid_consumption_kwh: float = 0.0
    created_at: Optional[datetime] = None
    
    @property
    def autoconsumption_rate(self) -> float:
        """Calculate autoconsumption rate for this participant"""
        if self.consumption_kwh > 0:
            return (self.autoconsumption_kwh / self.consumption_kwh) * 100
        return 0.0

@dataclass
class BillingPeriod:
    """Billing period data model"""
    id: Optional[int] = None
    project_id: int = 0
    period_name: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: BillingPeriodStatus = BillingPeriodStatus.DRAFT
    total_amount: float = 0.0
    payment_due_date: Optional[date] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'period_name': self.period_name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status.value if isinstance(self.status, BillingPeriodStatus) else self.status,
            'total_amount': self.total_amount,
            'payment_due_date': self.payment_due_date.isoformat() if self.payment_due_date else None
        }

@dataclass
class InvoiceItem:
    """Invoice line item data model"""
    id: Optional[int] = None
    invoice_id: int = 0
    description: str = ""
    quantity: float = 0.0
    unit_price: float = 0.0
    total_price: float = 0.0
    item_type: str = ""  # autoconsumption, subscription, maintenance
    created_at: Optional[datetime] = None
    
    def calculate_total(self):
        """Calculate total price"""
        self.total_price = self.quantity * self.unit_price

@dataclass
class Invoice:
    """Invoice data model"""
    id: Optional[int] = None
    billing_period_id: int = 0
    participant_id: int = 0
    invoice_number: str = ""
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    subtotal: float = 0.0
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    status: InvoiceStatus = InvoiceStatus.DRAFT
    payment_date: Optional[date] = None
    created_at: Optional[datetime] = None
    items: List[InvoiceItem] = field(default_factory=list)
    
    def calculate_totals(self):
        """Calculate invoice totals"""
        self.subtotal = sum(item.total_price for item in self.items)
        self.tax_amount = self.subtotal * self.tax_rate
        self.total_amount = self.subtotal + self.tax_amount
    
    def add_item(self, description: str, quantity: float, unit_price: float, item_type: str = ""):
        """Add an item to the invoice"""
        item = InvoiceItem(
            invoice_id=self.id or 0,
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            item_type=item_type
        )
        item.calculate_total()
        self.items.append(item)
        self.calculate_totals()
    
    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue"""
        if self.due_date and self.status != InvoiceStatus.PAID:
            return date.today() > self.due_date
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'id': self.id,
            'billing_period_id': self.billing_period_id,
            'participant_id': self.participant_id,
            'invoice_number': self.invoice_number,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'subtotal': self.subtotal,
            'tax_rate': self.tax_rate,
            'tax_amount': self.tax_amount,
            'total_amount': self.total_amount,
            'status': self.status.value if isinstance(self.status, InvoiceStatus) else self.status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None
        }

@dataclass
class Payment:
    """Payment record data model"""
    id: Optional[int] = None
    invoice_id: int = 0
    amount: float = 0.0
    payment_date: Optional[date] = None
    payment_method: str = ""
    transaction_id: str = ""
    notes: str = ""
    created_at: Optional[datetime] = None

@dataclass
class BillingCalculation:
    """Billing calculation result"""
    participant_id: int
    participant_name: str
    period_start: date
    period_end: date
    autoconsumption_kwh: float = 0.0
    unit_price_eur_kwh: float = 0.0
    subtotal: float = 0.0
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    
    def calculate(self, tax_rate: float = 0.20):
        """Calculate billing amounts"""
        self.subtotal = self.autoconsumption_kwh * self.unit_price_eur_kwh
        self.tax_rate = tax_rate
        self.tax_amount = self.subtotal * self.tax_rate
        self.total_amount = self.subtotal + self.tax_amount

@dataclass
class ProjectSummary:
    """Project summary for dashboard"""
    project: Project
    participants_count: int = 0
    total_monthly_production: float = 0.0
    total_monthly_consumption: float = 0.0
    autoconsumption_rate: float = 0.0
    monthly_revenue: float = 0.0
    pending_invoices_count: int = 0
    pending_invoices_amount: float = 0.0