"""
Module de gestion de la facturation récurrente
Gère les abonnements, templates et génération automatique
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, asdict
import json
import calendar
from decimal import Decimal, ROUND_HALF_UP

from .database import BillingDatabase

logger = logging.getLogger(__name__)

class RecurringFrequency(Enum):
    """Fréquences de facturation récurrente"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    CUSTOM = "custom"

class RecurringStatus(Enum):
    """États des abonnements récurrents"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

@dataclass
class RecurringTemplate:
    """Template pour facturation récurrente"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    frequency: RecurringFrequency = RecurringFrequency.MONTHLY
    amount: float = 0.0
    tax_rate: float = 0.20
    invoice_template: str = "standard"
    auto_validate: bool = False
    auto_send: bool = False
    payment_terms_days: int = 30
    
    # Conditions spéciales
    prorate_first_invoice: bool = True
    prorate_last_invoice: bool = True
    minimum_amount: float = 0.0
    maximum_amount: Optional[float] = None
    
    # Métadonnées
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class RecurringSubscription:
    """Abonnement récurrent"""
    id: Optional[int] = None
    participant_id: int = 0
    template_id: int = 0
    status: RecurringStatus = RecurringStatus.ACTIVE
    
    # Dates
    start_date: date = None
    end_date: Optional[date] = None
    next_billing_date: date = None
    last_billing_date: Optional[date] = None
    
    # Montants personnalisés
    custom_amount: Optional[float] = None
    custom_frequency: Optional[int] = None  # En jours pour fréquence custom
    
    # Historique
    total_invoices_generated: int = 0
    total_amount_billed: float = 0.0
    
    # Métadonnées
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class RecurringBillingManager:
    """
    Gestionnaire de facturation récurrente
    Gère les abonnements, templates et génération automatique
    """
    
    def __init__(self, db: BillingDatabase):
        """
        Initialise le gestionnaire
        
        Args:
            db: Instance de base de données
        """
        self.db = db
        self._ensure_tables()
        
        # Callbacks pour événements
        self.on_invoice_generated: Optional[Callable] = None
        self.on_generation_failed: Optional[Callable] = None
        self.on_subscription_created: Optional[Callable] = None
        self.on_subscription_cancelled: Optional[Callable] = None
        
        logger.info("RecurringBillingManager initialisé")
    
    def _ensure_tables(self):
        """Assure l'existence des tables requises"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Table des templates récurrents
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recurring_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    frequency TEXT NOT NULL,
                    amount REAL NOT NULL,
                    tax_rate REAL DEFAULT 0.20,
                    invoice_template TEXT DEFAULT 'standard',
                    auto_validate BOOLEAN DEFAULT 0,
                    auto_send BOOLEAN DEFAULT 0,
                    payment_terms_days INTEGER DEFAULT 30,
                    prorate_first_invoice BOOLEAN DEFAULT 1,
                    prorate_last_invoice BOOLEAN DEFAULT 1,
                    minimum_amount REAL DEFAULT 0.0,
                    maximum_amount REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des abonnements récurrents
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recurring_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    participant_id INTEGER NOT NULL,
                    template_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'active',
                    start_date DATE NOT NULL,
                    end_date DATE,
                    next_billing_date DATE NOT NULL,
                    last_billing_date DATE,
                    custom_amount REAL,
                    custom_frequency INTEGER,
                    total_invoices_generated INTEGER DEFAULT 0,
                    total_amount_billed REAL DEFAULT 0.0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (participant_id) REFERENCES participants(id),
                    FOREIGN KEY (template_id) REFERENCES recurring_templates(id)
                )
            """)
            
            # Table de l'historique des générations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recurring_generation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subscription_id INTEGER NOT NULL,
                    invoice_id INTEGER,
                    generation_date DATE NOT NULL,
                    billing_period_start DATE NOT NULL,
                    billing_period_end DATE NOT NULL,
                    amount REAL NOT NULL,
                    prorated BOOLEAN DEFAULT 0,
                    prorate_ratio REAL,
                    status TEXT DEFAULT 'success', -- success, failed, skipped
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subscription_id) REFERENCES recurring_subscriptions(id),
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
                )
            """)
            
            # Index pour optimisation
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_recurring_next_billing ON recurring_subscriptions(next_billing_date, status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_recurring_participant ON recurring_subscriptions(participant_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_generation_history_subscription ON recurring_generation_history(subscription_id)")
    
    def create_template(self, template_data: Dict[str, Any]) -> int:
        """
        Crée un nouveau template de facturation récurrente
        
        Args:
            template_data: Données du template
            
        Returns:
            int: ID du template créé
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO recurring_templates (
                    name, description, frequency, amount, tax_rate,
                    invoice_template, auto_validate, auto_send, payment_terms_days,
                    prorate_first_invoice, prorate_last_invoice, minimum_amount, maximum_amount
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                template_data['name'],
                template_data.get('description', ''),
                template_data['frequency'],
                template_data['amount'],
                template_data.get('tax_rate', 0.20),
                template_data.get('invoice_template', 'standard'),
                template_data.get('auto_validate', False),
                template_data.get('auto_send', False),
                template_data.get('payment_terms_days', 30),
                template_data.get('prorate_first_invoice', True),
                template_data.get('prorate_last_invoice', True),
                template_data.get('minimum_amount', 0.0),
                template_data.get('maximum_amount')
            ))
            
            template_id = cursor.lastrowid
            logger.info(f"Template récurrent créé: {template_id}")
            return template_id
    
    def get_template(self, template_id: int) -> Optional[RecurringTemplate]:
        """Récupère un template par ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recurring_templates WHERE id = ?", (template_id,))
            row = cursor.fetchone()
            
            if row:
                return RecurringTemplate(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    frequency=RecurringFrequency(row['frequency']),
                    amount=row['amount'],
                    tax_rate=row['tax_rate'],
                    invoice_template=row['invoice_template'],
                    auto_validate=bool(row['auto_validate']),
                    auto_send=bool(row['auto_send']),
                    payment_terms_days=row['payment_terms_days'],
                    prorate_first_invoice=bool(row['prorate_first_invoice']),
                    prorate_last_invoice=bool(row['prorate_last_invoice']),
                    minimum_amount=row['minimum_amount'],
                    maximum_amount=row['maximum_amount'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
                )
        
        return None
    
    def list_templates(self) -> List[RecurringTemplate]:
        """Liste tous les templates"""
        templates = []
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recurring_templates ORDER BY name")
            
            for row in cursor.fetchall():
                templates.append(RecurringTemplate(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    frequency=RecurringFrequency(row['frequency']),
                    amount=row['amount'],
                    tax_rate=row['tax_rate'],
                    invoice_template=row['invoice_template'],
                    auto_validate=bool(row['auto_validate']),
                    auto_send=bool(row['auto_send']),
                    payment_terms_days=row['payment_terms_days'],
                    prorate_first_invoice=bool(row['prorate_first_invoice']),
                    prorate_last_invoice=bool(row['prorate_last_invoice']),
                    minimum_amount=row['minimum_amount'],
                    maximum_amount=row['maximum_amount'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
                ))
        
        return templates
    
    def create_subscription(self, subscription_data: Dict[str, Any]) -> int:
        """
        Crée un nouvel abonnement récurrent
        
        Args:
            subscription_data: Données de l'abonnement
            
        Returns:
            int: ID de l'abonnement créé
        """
        start_date = subscription_data['start_date']
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        # Calcul de la prochaine date de facturation
        template = self.get_template(subscription_data['template_id'])
        if not template:
            raise ValueError(f"Template {subscription_data['template_id']} non trouvé")
        
        next_billing_date = self._calculate_next_billing_date(start_date, template.frequency)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO recurring_subscriptions (
                    participant_id, template_id, status, start_date, end_date,
                    next_billing_date, custom_amount, custom_frequency, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                subscription_data['participant_id'],
                subscription_data['template_id'],
                subscription_data.get('status', 'active'),
                start_date.isoformat(),
                subscription_data.get('end_date'),
                next_billing_date.isoformat(),
                subscription_data.get('custom_amount'),
                subscription_data.get('custom_frequency'),
                subscription_data.get('notes', '')
            ))
            
            subscription_id = cursor.lastrowid
            
            # Callback
            if self.on_subscription_created:
                self.on_subscription_created({
                    'subscription_id': subscription_id,
                    'participant_id': subscription_data['participant_id'],
                    'template_id': subscription_data['template_id']
                })
            
            logger.info(f"Abonnement récurrent créé: {subscription_id}")
            return subscription_id
    
    def get_subscription(self, subscription_id: int) -> Optional[RecurringSubscription]:
        """Récupère un abonnement par ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recurring_subscriptions WHERE id = ?", (subscription_id,))
            row = cursor.fetchone()
            
            if row:
                return RecurringSubscription(
                    id=row['id'],
                    participant_id=row['participant_id'],
                    template_id=row['template_id'],
                    status=RecurringStatus(row['status']),
                    start_date=datetime.strptime(row['start_date'], '%Y-%m-%d').date(),
                    end_date=datetime.strptime(row['end_date'], '%Y-%m-%d').date() if row['end_date'] else None,
                    next_billing_date=datetime.strptime(row['next_billing_date'], '%Y-%m-%d').date(),
                    last_billing_date=datetime.strptime(row['last_billing_date'], '%Y-%m-%d').date() if row['last_billing_date'] else None,
                    custom_amount=row['custom_amount'],
                    custom_frequency=row['custom_frequency'],
                    total_invoices_generated=row['total_invoices_generated'],
                    total_amount_billed=row['total_amount_billed'],
                    notes=row['notes'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
                )
        
        return None
    
    def list_subscriptions(self, participant_id: int = None, status: RecurringStatus = None) -> List[Dict[str, Any]]:
        """Liste les abonnements avec filtres optionnels"""
        conditions = []
        params = []
        
        if participant_id:
            conditions.append("rs.participant_id = ?")
            params.append(participant_id)
        
        if status:
            conditions.append("rs.status = ?")
            params.append(status.value)
        
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 
                    rs.*,
                    rt.name as template_name,
                    rt.frequency as template_frequency,
                    rt.amount as template_amount,
                    p.name as participant_name
                FROM recurring_subscriptions rs
                JOIN recurring_templates rt ON rs.template_id = rt.id
                JOIN participants p ON rs.participant_id = p.id
                {where_clause}
                ORDER BY rs.next_billing_date
            """, params)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def generate_due_invoices(self, target_date: date = None) -> Dict[str, Any]:
        """
        Génère toutes les factures dues
        
        Args:
            target_date: Date cible (par défaut aujourd'hui)
            
        Returns:
            Dict: Résultat de la génération
        """
        if target_date is None:
            target_date = date.today()
        
        result = {
            'success': True,
            'generated_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'invoices': [],
            'errors': []
        }
        
        try:
            # Récupération des abonnements dus
            due_subscriptions = self._get_due_subscriptions(target_date)
            
            logger.info(f"Traitement de {len(due_subscriptions)} abonnements dus")
            
            for subscription in due_subscriptions:
                try:
                    invoice_result = self._generate_subscription_invoice(subscription, target_date)
                    
                    if invoice_result['success']:
                        result['generated_count'] += 1
                        result['invoices'].append(invoice_result['invoice_id'])
                        
                        # Callback de succès
                        if self.on_invoice_generated:
                            self.on_invoice_generated({
                                'invoice_id': invoice_result['invoice_id'],
                                'subscription_id': subscription['id'],
                                'participant_id': subscription['participant_id']
                            })
                    else:
                        result['failed_count'] += 1
                        result['errors'].append({
                            'subscription_id': subscription['id'],
                            'error': invoice_result['error']
                        })
                        
                        # Callback d'échec
                        if self.on_generation_failed:
                            self.on_generation_failed({
                                'subscription_id': subscription['id'],
                                'error': invoice_result['error']
                            })
                
                except Exception as e:
                    logger.error(f"Erreur lors de la génération pour l'abonnement {subscription['id']}: {e}")
                    result['failed_count'] += 1
                    result['errors'].append({
                        'subscription_id': subscription['id'],
                        'error': str(e)
                    })
            
            if result['failed_count'] > 0:
                result['success'] = False
            
            logger.info(f"Génération terminée: {result['generated_count']} succès, {result['failed_count']} échecs")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des factures récurrentes: {e}")
            result['success'] = False
            result['error'] = str(e)
        
        return result
    
    def _get_due_subscriptions(self, target_date: date) -> List[Dict[str, Any]]:
        """Récupère les abonnements dus pour une date donnée"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    rs.*,
                    rt.name as template_name,
                    rt.frequency as template_frequency,
                    rt.amount as template_amount,
                    rt.tax_rate as template_tax_rate,
                    rt.auto_validate as template_auto_validate,
                    rt.auto_send as template_auto_send,
                    rt.payment_terms_days as template_payment_terms_days,
                    rt.prorate_first_invoice as template_prorate_first,
                    rt.prorate_last_invoice as template_prorate_last,
                    rt.minimum_amount as template_min_amount,
                    rt.maximum_amount as template_max_amount,
                    p.name as participant_name,
                    p.contact_email as participant_email
                FROM recurring_subscriptions rs
                JOIN recurring_templates rt ON rs.template_id = rt.id
                JOIN participants p ON rs.participant_id = p.id
                WHERE rs.status = 'active'
                AND rs.next_billing_date <= ?
                AND (rs.end_date IS NULL OR rs.end_date >= ?)
                ORDER BY rs.next_billing_date
            """, (target_date.isoformat(), target_date.isoformat()))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def _generate_subscription_invoice(self, subscription: Dict[str, Any], generation_date: date) -> Dict[str, Any]:
        """
        Génère une facture pour un abonnement
        
        Args:
            subscription: Données de l'abonnement
            generation_date: Date de génération
            
        Returns:
            Dict: Résultat de la génération
        """
        try:
            # Calcul de la période de facturation
            billing_start = datetime.strptime(subscription['next_billing_date'], '%Y-%m-%d').date()
            frequency = RecurringFrequency(subscription['template_frequency'])
            billing_end = self._calculate_billing_period_end(billing_start, frequency)
            
            # Calcul du montant
            base_amount = subscription['custom_amount'] or subscription['template_amount']
            
            # Vérification du prorate pour première facture
            prorate_ratio = 1.0
            is_prorated = False
            
            if subscription['total_invoices_generated'] == 0 and subscription['template_prorate_first']:
                prorate_ratio = self._calculate_prorate_ratio(
                    datetime.strptime(subscription['start_date'], '%Y-%m-%d').date(),
                    billing_start,
                    billing_end
                )
                is_prorated = True
            
            # Vérification du prorate pour dernière facture
            elif subscription['end_date'] and billing_end > datetime.strptime(subscription['end_date'], '%Y-%m-%d').date():
                if subscription['template_prorate_last']:
                    billing_end = datetime.strptime(subscription['end_date'], '%Y-%m-%d').date()
                    prorate_ratio = self._calculate_prorate_ratio(
                        billing_start,
                        billing_start,
                        billing_end
                    )
                    is_prorated = True
                else:
                    # Pas de facturation si dépassement et pas de prorate
                    return {
                        'success': False,
                        'error': 'Abonnement expiré sans prorate'
                    }
            
            # Application du prorate
            final_amount = base_amount * prorate_ratio
            
            # Vérification des limites
            if final_amount < subscription['template_min_amount']:
                final_amount = subscription['template_min_amount']
            
            if subscription['template_max_amount'] and final_amount > subscription['template_max_amount']:
                final_amount = subscription['template_max_amount']
            
            # Arrondi à 2 décimales
            final_amount = float(Decimal(str(final_amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            
            # Calcul de la TVA
            tax_rate = subscription['template_tax_rate']
            tax_amount = final_amount * tax_rate
            total_amount = final_amount + tax_amount
            
            # Calcul de la date d'échéance
            payment_terms = subscription['template_payment_terms_days']
            due_date = generation_date + timedelta(days=payment_terms)
            
            # Génération du numéro de facture
            invoice_number = self._generate_invoice_number()
            
            # Création de la période de facturation si nécessaire
            billing_period_id = self._get_or_create_billing_period(
                subscription, billing_start, billing_end
            )
            
            # Création de la facture
            invoice_data = {
                'billing_period_id': billing_period_id,
                'participant_id': subscription['participant_id'],
                'invoice_number': invoice_number,
                'issue_date': generation_date.isoformat(),
                'due_date': due_date.isoformat(),
                'subtotal': final_amount,
                'tax_rate': tax_rate,
                'tax_amount': tax_amount,
                'total_amount': total_amount,
                'status': 'validated' if subscription['template_auto_validate'] else 'draft'
            }
            
            invoice_id = self.db.create_invoice(invoice_data)
            
            # Création des lignes de facture
            self._create_invoice_items(invoice_id, subscription, billing_start, billing_end, final_amount, is_prorated, prorate_ratio)
            
            # Enregistrement dans l'historique
            self._record_generation_history(
                subscription['id'], invoice_id, generation_date,
                billing_start, billing_end, final_amount,
                is_prorated, prorate_ratio
            )
            
            # Mise à jour de l'abonnement
            self._update_subscription_after_generation(subscription, billing_end, final_amount)
            
            logger.info(f"Facture générée: {invoice_number} pour {final_amount}€")
            
            return {
                'success': True,
                'invoice_id': invoice_id,
                'invoice_number': invoice_number,
                'amount': total_amount,
                'prorated': is_prorated,
                'prorate_ratio': prorate_ratio
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de facture: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_billing_period_end(self, start_date: date, frequency: RecurringFrequency) -> date:
        """Calcule la fin de période de facturation"""
        if frequency == RecurringFrequency.MONTHLY:
            if start_date.month == 12:
                return date(start_date.year + 1, 1, start_date.day) - timedelta(days=1)
            else:
                next_month = start_date.month + 1
                # Gestion des fins de mois
                last_day = calendar.monthrange(start_date.year, next_month)[1]
                day = min(start_date.day, last_day)
                return date(start_date.year, next_month, day) - timedelta(days=1)
        
        elif frequency == RecurringFrequency.QUARTERLY:
            return start_date + timedelta(days=90) - timedelta(days=1)
        
        elif frequency == RecurringFrequency.SEMI_ANNUAL:
            return start_date + timedelta(days=180) - timedelta(days=1)
        
        elif frequency == RecurringFrequency.ANNUAL:
            return date(start_date.year + 1, start_date.month, start_date.day) - timedelta(days=1)
        
        else:
            # Pour custom, utiliser 30 jours par défaut
            return start_date + timedelta(days=30) - timedelta(days=1)
    
    def _calculate_next_billing_date(self, current_date: date, frequency: RecurringFrequency) -> date:
        """Calcule la prochaine date de facturation"""
        if frequency == RecurringFrequency.MONTHLY:
            if current_date.month == 12:
                return date(current_date.year + 1, 1, current_date.day)
            else:
                next_month = current_date.month + 1
                # Gestion des fins de mois
                last_day = calendar.monthrange(current_date.year, next_month)[1]
                day = min(current_date.day, last_day)
                return date(current_date.year, next_month, day)
        
        elif frequency == RecurringFrequency.QUARTERLY:
            return current_date + timedelta(days=91)
        
        elif frequency == RecurringFrequency.SEMI_ANNUAL:
            return current_date + timedelta(days=182)
        
        elif frequency == RecurringFrequency.ANNUAL:
            return date(current_date.year + 1, current_date.month, current_date.day)
        
        else:
            # Pour custom, utiliser 30 jours par défaut
            return current_date + timedelta(days=30)
    
    def _calculate_prorate_ratio(self, actual_start: date, period_start: date, period_end: date) -> float:
        """Calcule le ratio de prorate"""
        total_days = (period_end - period_start).days + 1
        
        if actual_start > period_start:
            # Début en cours de période
            actual_days = (period_end - actual_start).days + 1
        else:
            # Fin en cours de période
            actual_days = (actual_start - period_start).days + 1
        
        ratio = actual_days / total_days
        return max(0.0, min(1.0, ratio))  # Entre 0 et 1
    
    def _generate_invoice_number(self) -> str:
        """Génère un numéro de facture unique"""
        # Utilisation de la logique existante de numérotation
        from .invoice_numbering import InvoiceNumbering
        numbering = InvoiceNumbering(self.db)
        return numbering.generate_number("REC")
    
    def _get_or_create_billing_period(self, subscription: Dict[str, Any], start_date: date, end_date: date) -> int:
        """Récupère ou crée une période de facturation"""
        # Recherche d'une période existante
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Récupération du project_id via le participant
            cursor.execute("""
                SELECT project_id FROM participants WHERE id = ?
            """, (subscription['participant_id'],))
            project_row = cursor.fetchone()
            
            if not project_row:
                raise ValueError(f"Participant {subscription['participant_id']} non trouvé")
            
            project_id = project_row['project_id']
            
            # Recherche d'une période de facturation existante
            cursor.execute("""
                SELECT id FROM billing_periods
                WHERE project_id = ? AND start_date = ? AND end_date = ?
            """, (project_id, start_date.isoformat(), end_date.isoformat()))
            
            period_row = cursor.fetchone()
            
            if period_row:
                return period_row['id']
            
            # Création d'une nouvelle période
            period_name = f"Récurrent {start_date.strftime('%m/%Y')}"
            due_date = end_date + timedelta(days=30)
            
            cursor.execute("""
                INSERT INTO billing_periods (
                    project_id, period_name, start_date, end_date, payment_due_date
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                project_id, period_name, start_date.isoformat(),
                end_date.isoformat(), due_date.isoformat()
            ))
            
            return cursor.lastrowid
    
    def _create_invoice_items(self, invoice_id: int, subscription: Dict[str, Any], 
                            start_date: date, end_date: date, amount: float,
                            is_prorated: bool, prorate_ratio: float):
        """Crée les lignes de facture"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            description = f"Abonnement {subscription['template_name']}"
            if is_prorated:
                description += f" (prorata {prorate_ratio:.2%})"
            
            description += f" - Période {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}"
            
            cursor.execute("""
                INSERT INTO invoice_items (
                    invoice_id, description, quantity, unit_price, total_price, item_type
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                invoice_id, description, 1.0, amount, amount, 'subscription'
            ))
    
    def _record_generation_history(self, subscription_id: int, invoice_id: int, 
                                 generation_date: date, billing_start: date, 
                                 billing_end: date, amount: float,
                                 is_prorated: bool, prorate_ratio: float):
        """Enregistre l'historique de génération"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO recurring_generation_history (
                    subscription_id, invoice_id, generation_date,
                    billing_period_start, billing_period_end, amount,
                    prorated, prorate_ratio, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                subscription_id, invoice_id, generation_date.isoformat(),
                billing_start.isoformat(), billing_end.isoformat(), amount,
                is_prorated, prorate_ratio if is_prorated else None, 'success'
            ))
    
    def _update_subscription_after_generation(self, subscription: Dict[str, Any], 
                                            billing_end: date, amount: float):
        """Met à jour l'abonnement après génération"""
        frequency = RecurringFrequency(subscription['template_frequency'])
        next_billing_date = self._calculate_next_billing_date(billing_end + timedelta(days=1), frequency)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE recurring_subscriptions 
                SET 
                    next_billing_date = ?,
                    last_billing_date = ?,
                    total_invoices_generated = total_invoices_generated + 1,
                    total_amount_billed = total_amount_billed + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                next_billing_date.isoformat(),
                billing_end.isoformat(),
                amount,
                subscription['id']
            ))
    
    def cancel_subscription(self, subscription_id: int, reason: str = "") -> bool:
        """
        Annule un abonnement
        
        Args:
            subscription_id: ID de l'abonnement
            reason: Raison de l'annulation
            
        Returns:
            bool: True si annulé avec succès
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE recurring_subscriptions 
                    SET status = 'cancelled', 
                        notes = COALESCE(notes, '') || ? || ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    "\nAnnulé le " + date.today().isoformat() + ": " if reason else "",
                    reason,
                    subscription_id
                ))
                
                if cursor.rowcount > 0:
                    # Callback
                    if self.on_subscription_cancelled:
                        self.on_subscription_cancelled({
                            'subscription_id': subscription_id,
                            'reason': reason
                        })
                    
                    logger.info(f"Abonnement {subscription_id} annulé: {reason}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation de l'abonnement {subscription_id}: {e}")
            return False
    
    def suspend_subscription(self, subscription_id: int, until_date: date = None) -> bool:
        """Suspend un abonnement temporairement"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                notes_update = f"\nSuspendu le {date.today().isoformat()}"
                if until_date:
                    notes_update += f" jusqu'au {until_date.isoformat()}"
                
                cursor.execute("""
                    UPDATE recurring_subscriptions 
                    SET status = 'suspended',
                        notes = COALESCE(notes, '') || ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (notes_update, subscription_id))
                
                return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Erreur lors de la suspension de l'abonnement {subscription_id}: {e}")
            return False
    
    def resume_subscription(self, subscription_id: int) -> bool:
        """Reprend un abonnement suspendu"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE recurring_subscriptions 
                    SET status = 'active',
                        notes = COALESCE(notes, '') || ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND status = 'suspended'
                """, (f"\nReactivé le {date.today().isoformat()}", subscription_id))
                
                return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Erreur lors de la reprise de l'abonnement {subscription_id}: {e}")
            return False
    
    def get_subscription_history(self, subscription_id: int) -> List[Dict[str, Any]]:
        """Récupère l'historique d'un abonnement"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    rgh.*,
                    i.invoice_number,
                    i.status as invoice_status,
                    i.total_amount as invoice_total
                FROM recurring_generation_history rgh
                LEFT JOIN invoices i ON rgh.invoice_id = i.id
                WHERE rgh.subscription_id = ?
                ORDER BY rgh.generation_date DESC
            """, (subscription_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du gestionnaire"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Statistiques générales
            cursor.execute("SELECT COUNT(*) FROM recurring_templates")
            templates_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM recurring_subscriptions WHERE status = 'active'")
            active_subscriptions = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM recurring_subscriptions 
                WHERE status = 'active' AND next_billing_date <= date('now')
            """)
            due_subscriptions = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*), SUM(amount) FROM recurring_generation_history 
                WHERE generation_date >= date('now', 'start of month')
            """)
            monthly_stats = cursor.fetchone()
            
            return {
                'templates_count': templates_count,
                'active_subscriptions': active_subscriptions,
                'due_subscriptions': due_subscriptions,
                'monthly_invoices_generated': monthly_stats[0] or 0,
                'monthly_amount_generated': monthly_stats[1] or 0.0
            }