"""
Module de gestion des workflows de facturation
Gère les états, transitions et validations automatiques
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Callable, Set
from enum import Enum
from dataclasses import dataclass, asdict
import json
from pathlib import Path

from .database import BillingDatabase

logger = logging.getLogger(__name__)

class WorkflowState(Enum):
    """États du workflow de facturation"""
    DRAFT = "draft"
    VALIDATION_PENDING = "validation_pending"
    VALIDATED = "validated"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"

class WorkflowAction(Enum):
    """Actions possibles dans le workflow"""
    SUBMIT_FOR_VALIDATION = "submit_for_validation"
    VALIDATE = "validate"
    REJECT = "reject"
    SEND = "send"
    MARK_PAID = "mark_paid"
    MARK_OVERDUE = "mark_overdue"
    CANCEL = "cancel"
    ARCHIVE = "archive"
    REOPEN = "reopen"

class ValidationLevel(Enum):
    """Niveaux de validation"""
    AUTOMATIC = "automatic"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    DIRECTOR = "director"

@dataclass
class WorkflowRule:
    """Règle de workflow"""
    id: Optional[int] = None
    name: str = ""
    from_state: WorkflowState = WorkflowState.DRAFT
    to_state: WorkflowState = WorkflowState.VALIDATED
    action: WorkflowAction = WorkflowAction.VALIDATE
    
    # Conditions
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    required_validation_level: ValidationLevel = ValidationLevel.AUTOMATIC
    require_approval: bool = False
    approval_roles: List[str] = None
    
    # Actions automatiques
    auto_execute: bool = False
    auto_conditions: Dict[str, Any] = None
    
    # Notifications
    notify_on_entry: bool = True
    notify_on_exit: bool = False
    notification_recipients: List[str] = None
    
    # Métadonnées
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.approval_roles is None:
            self.approval_roles = []
        if self.auto_conditions is None:
            self.auto_conditions = {}
        if self.notification_recipients is None:
            self.notification_recipients = []

@dataclass
class WorkflowTransition:
    """Transition de workflow"""
    id: Optional[int] = None
    invoice_id: int = 0
    from_state: WorkflowState = WorkflowState.DRAFT
    to_state: WorkflowState = WorkflowState.VALIDATED
    action: WorkflowAction = WorkflowAction.VALIDATE
    
    # Exécution
    executed_by: str = ""
    executed_at: datetime = None
    approval_required: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    # Données
    transition_data: Dict[str, Any] = None
    comments: str = ""
    
    def __post_init__(self):
        if self.transition_data is None:
            self.transition_data = {}
        if self.executed_at is None:
            self.executed_at = datetime.now()

class WorkflowManager:
    """
    Gestionnaire de workflows de facturation
    Gère les états, transitions et validations
    """
    
    def __init__(self, db: BillingDatabase):
        """
        Initialise le gestionnaire
        
        Args:
            db: Instance de base de données
        """
        self.db = db
        self._ensure_tables()
        
        # Cache des règles de workflow
        self._rules_cache: Dict[str, WorkflowRule] = {}
        self._load_workflow_rules()
        
        # Callbacks pour événements
        self.on_state_changed: Optional[Callable] = None
        self.on_validation_required: Optional[Callable] = None
        self.on_approval_required: Optional[Callable] = None
        self.on_transition_blocked: Optional[Callable] = None
        
        # Configuration des transitions valides
        self.valid_transitions = self._setup_valid_transitions()
        
        logger.info("WorkflowManager initialisé")
    
    def _ensure_tables(self):
        """Assure l'existence des tables requises"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Table des règles de workflow
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    from_state TEXT NOT NULL,
                    to_state TEXT NOT NULL,
                    action TEXT NOT NULL,
                    min_amount REAL,
                    max_amount REAL,
                    required_validation_level TEXT DEFAULT 'automatic',
                    require_approval BOOLEAN DEFAULT 0,
                    approval_roles TEXT, -- JSON array
                    auto_execute BOOLEAN DEFAULT 0,
                    auto_conditions TEXT, -- JSON object
                    notify_on_entry BOOLEAN DEFAULT 1,
                    notify_on_exit BOOLEAN DEFAULT 0,
                    notification_recipients TEXT, -- JSON array
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des transitions de workflow
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    from_state TEXT NOT NULL,
                    to_state TEXT NOT NULL,
                    action TEXT NOT NULL,
                    executed_by TEXT NOT NULL,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    approval_required BOOLEAN DEFAULT 0,
                    approved_by TEXT,
                    approved_at TIMESTAMP,
                    transition_data TEXT, -- JSON object
                    comments TEXT,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
                )
            """)
            
            # Table des approbations en attente
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    transition_id INTEGER NOT NULL,
                    required_role TEXT NOT NULL,
                    assigned_to TEXT,
                    status TEXT DEFAULT 'pending', -- pending, approved, rejected
                    approved_by TEXT,
                    approved_at TIMESTAMP,
                    rejection_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
                    FOREIGN KEY (transition_id) REFERENCES workflow_transitions(id)
                )
            """)
            
            # Table des hooks de workflow
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_hooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    event_type TEXT NOT NULL, -- on_enter, on_exit, on_transition
                    target_state TEXT,
                    hook_type TEXT NOT NULL, -- email, webhook, script
                    hook_config TEXT NOT NULL, -- JSON configuration
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index pour optimisation
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflow_transitions_invoice ON workflow_transitions(invoice_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflow_transitions_state ON workflow_transitions(to_state)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflow_approvals_status ON workflow_approvals(status)")
            
            # Insertion des règles par défaut
            self._insert_default_workflow_rules(cursor)
            
            conn.commit()
    
    def _insert_default_workflow_rules(self, cursor):
        """Insère les règles de workflow par défaut"""
        default_rules = [
            {
                'name': 'Auto validate small amounts',
                'from_state': 'draft',
                'to_state': 'validated',
                'action': 'validate',
                'max_amount': 1000.0,
                'auto_execute': True,
                'auto_conditions': '{"has_participant": true, "amount_positive": true}'
            },
            {
                'name': 'Supervisor validation medium amounts',
                'from_state': 'draft',
                'to_state': 'validation_pending',
                'action': 'submit_for_validation',
                'min_amount': 1000.01,
                'max_amount': 10000.0,
                'required_validation_level': 'supervisor',
                'require_approval': True,
                'approval_roles': '["supervisor", "manager"]'
            },
            {
                'name': 'Manager validation large amounts',
                'from_state': 'draft',
                'to_state': 'validation_pending',
                'action': 'submit_for_validation',
                'min_amount': 10000.01,
                'required_validation_level': 'manager',
                'require_approval': True,
                'approval_roles': '["manager", "director"]'
            },
            {
                'name': 'Auto send validated invoices',
                'from_state': 'validated',
                'to_state': 'sent',
                'action': 'send',
                'auto_execute': True,
                'auto_conditions': '{"has_email": true}'
            },
            {
                'name': 'Mark overdue after due date',
                'from_state': 'sent',
                'to_state': 'overdue',
                'action': 'mark_overdue',
                'auto_execute': True,
                'auto_conditions': '{"past_due_date": true}'
            }
        ]
        
        for rule in default_rules:
            cursor.execute("""
                INSERT OR IGNORE INTO workflow_rules (
                    name, from_state, to_state, action, min_amount, max_amount,
                    required_validation_level, require_approval, approval_roles,
                    auto_execute, auto_conditions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule['name'], rule['from_state'], rule['to_state'], rule['action'],
                rule.get('min_amount'), rule.get('max_amount'),
                rule.get('required_validation_level', 'automatic'),
                rule.get('require_approval', False),
                rule.get('approval_roles'),
                rule.get('auto_execute', False),
                rule.get('auto_conditions')
            ))
    
    def _setup_valid_transitions(self) -> Dict[WorkflowState, Set[WorkflowState]]:
        """Configure les transitions valides entre états"""
        return {
            WorkflowState.DRAFT: {
                WorkflowState.VALIDATION_PENDING,
                WorkflowState.VALIDATED,
                WorkflowState.CANCELLED
            },
            WorkflowState.VALIDATION_PENDING: {
                WorkflowState.VALIDATED,
                WorkflowState.DRAFT,
                WorkflowState.CANCELLED
            },
            WorkflowState.VALIDATED: {
                WorkflowState.SENT,
                WorkflowState.DRAFT,
                WorkflowState.CANCELLED
            },
            WorkflowState.SENT: {
                WorkflowState.PAID,
                WorkflowState.OVERDUE,
                WorkflowState.CANCELLED
            },
            WorkflowState.PAID: {
                WorkflowState.ARCHIVED
            },
            WorkflowState.OVERDUE: {
                WorkflowState.PAID,
                WorkflowState.CANCELLED
            },
            WorkflowState.CANCELLED: {
                WorkflowState.DRAFT,
                WorkflowState.ARCHIVED
            },
            WorkflowState.ARCHIVED: set()  # État final
        }
    
    def _load_workflow_rules(self):
        """Charge les règles de workflow en cache"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workflow_rules WHERE is_active = 1")
            
            for row in cursor.fetchall():
                rule = WorkflowRule(
                    id=row['id'],
                    name=row['name'],
                    from_state=WorkflowState(row['from_state']),
                    to_state=WorkflowState(row['to_state']),
                    action=WorkflowAction(row['action']),
                    min_amount=row['min_amount'],
                    max_amount=row['max_amount'],
                    required_validation_level=ValidationLevel(row['required_validation_level']),
                    require_approval=bool(row['require_approval']),
                    approval_roles=json.loads(row['approval_roles']) if row['approval_roles'] else [],
                    auto_execute=bool(row['auto_execute']),
                    auto_conditions=json.loads(row['auto_conditions']) if row['auto_conditions'] else {},
                    notify_on_entry=bool(row['notify_on_entry']),
                    notify_on_exit=bool(row['notify_on_exit']),
                    notification_recipients=json.loads(row['notification_recipients']) if row['notification_recipients'] else [],
                    is_active=bool(row['is_active']),
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
                )
                
                key = f"{rule.from_state.value}_{rule.action.value}"
                self._rules_cache[key] = rule
    
    def transition_invoice(self, invoice_id: int, action: str, 
                          executed_by: str = "system", comments: str = "",
                          transition_data: Dict[str, Any] = None,
                          **kwargs) -> Dict[str, Any]:
        """
        Exécute une transition de workflow pour une facture
        
        Args:
            invoice_id: ID de la facture
            action: Action à exécuter
            executed_by: Utilisateur exécutant la transition
            comments: Commentaires sur la transition
            transition_data: Données additionnelles
            **kwargs: Paramètres additionnels
            
        Returns:
            Dict: Résultat de la transition
        """
        try:
            # Récupération de la facture
            invoice = self.db.get_invoice(invoice_id)
            if not invoice:
                return {
                    'success': False,
                    'error': f'Facture {invoice_id} non trouvée'
                }
            
            current_state = WorkflowState(invoice['status'])
            action_enum = WorkflowAction(action)
            
            # Recherche de la règle applicable
            rule = self._find_applicable_rule(current_state, action_enum, invoice)
            if not rule:
                return {
                    'success': False,
                    'error': f'Aucune règle trouvée pour la transition {current_state.value} -> {action}'
                }
            
            # Vérification des conditions
            conditions_check = self._check_transition_conditions(invoice, rule, **kwargs)
            if not conditions_check['valid']:
                return {
                    'success': False,
                    'error': f'Conditions non remplies: {conditions_check["reason"]}'
                }
            
            # Vérification si la transition est valide
            if rule.to_state not in self.valid_transitions.get(current_state, set()):
                return {
                    'success': False,
                    'error': f'Transition invalide: {current_state.value} -> {rule.to_state.value}'
                }
            
            # Vérification des approbations requises
            if rule.require_approval and not kwargs.get('force_approval', False):
                approval_result = self._handle_approval_requirement(
                    invoice_id, rule, executed_by, comments, transition_data
                )
                return approval_result
            
            # Exécution de la transition
            transition_result = self._execute_transition(
                invoice_id, current_state, rule, executed_by, comments, transition_data
            )
            
            if transition_result['success']:
                # Exécution des hooks
                self._execute_hooks('on_transition', rule.to_state, invoice_id, transition_result)
                
                # Callback de changement d'état
                if self.on_state_changed:
                    self.on_state_changed({
                        'invoice_id': invoice_id,
                        'old_state': current_state.value,
                        'new_state': rule.to_state.value,
                        'action': action,
                        'executed_by': executed_by
                    })
                
                # Traitement des transitions automatiques suivantes
                self._process_auto_transitions(invoice_id, rule.to_state)
            
            return transition_result
            
        except Exception as e:
            logger.error(f"Erreur lors de la transition de la facture {invoice_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _find_applicable_rule(self, current_state: WorkflowState, 
                            action: WorkflowAction, invoice: Dict[str, Any]) -> Optional[WorkflowRule]:
        """Trouve la règle applicable pour une transition"""
        key = f"{current_state.value}_{action.value}"
        rule = self._rules_cache.get(key)
        
        if rule and self._rule_applies_to_invoice(rule, invoice):
            return rule
        
        # Recherche dans toutes les règles si pas de correspondance exacte
        for cached_rule in self._rules_cache.values():
            if (cached_rule.from_state == current_state and 
                cached_rule.action == action and
                self._rule_applies_to_invoice(cached_rule, invoice)):
                return cached_rule
        
        return None
    
    def _rule_applies_to_invoice(self, rule: WorkflowRule, invoice: Dict[str, Any]) -> bool:
        """Vérifie si une règle s'applique à une facture"""
        amount = invoice.get('total_amount', 0)
        
        # Vérification des montants
        if rule.min_amount is not None and amount < rule.min_amount:
            return False
        
        if rule.max_amount is not None and amount > rule.max_amount:
            return False
        
        return True
    
    def _check_transition_conditions(self, invoice: Dict[str, Any], 
                                   rule: WorkflowRule, **kwargs) -> Dict[str, bool]:
        """Vérifie les conditions pour une transition"""
        if not rule.auto_conditions:
            return {'valid': True}
        
        conditions = rule.auto_conditions
        
        # Vérification des conditions standard
        if conditions.get('has_participant') and not invoice.get('participant_id'):
            return {'valid': False, 'reason': 'Participant requis'}
        
        if conditions.get('amount_positive') and invoice.get('total_amount', 0) <= 0:
            return {'valid': False, 'reason': 'Montant doit être positif'}
        
        if conditions.get('has_email'):
            # Vérification que le participant a un email
            participant = self._get_participant(invoice.get('participant_id'))
            if not participant or not participant.get('contact_email'):
                return {'valid': False, 'reason': 'Email du participant requis'}
        
        if conditions.get('past_due_date'):
            # Vérification si la date d'échéance est dépassée
            due_date = datetime.strptime(invoice['due_date'], '%Y-%m-%d').date()
            if due_date >= date.today():
                return {'valid': False, 'reason': 'Date d\'échéance non dépassée'}
        
        # Conditions personnalisées via kwargs
        for condition, value in conditions.items():
            if condition.startswith('custom_') and condition in kwargs:
                if kwargs[condition] != value:
                    return {'valid': False, 'reason': f'Condition {condition} non remplie'}
        
        return {'valid': True}
    
    def _handle_approval_requirement(self, invoice_id: int, rule: WorkflowRule,
                                   executed_by: str, comments: str,
                                   transition_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gère les exigences d'approbation"""
        try:
            # Création de la transition en attente
            transition_id = self._create_pending_transition(
                invoice_id, rule, executed_by, comments, transition_data
            )
            
            # Création des approbations requises
            for role in rule.approval_roles:
                self._create_approval_request(invoice_id, transition_id, role)
            
            # Callback de validation requise
            if self.on_validation_required:
                self.on_validation_required({
                    'invoice_id': invoice_id,
                    'transition_id': transition_id,
                    'required_roles': rule.approval_roles,
                    'validation_level': rule.required_validation_level.value
                })
            
            return {
                'success': True,
                'approval_required': True,
                'transition_id': transition_id,
                'message': f'Approbation requise par: {", ".join(rule.approval_roles)}'
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la gestion de l'approbation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_transition(self, invoice_id: int, current_state: WorkflowState,
                          rule: WorkflowRule, executed_by: str, comments: str,
                          transition_data: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute une transition de workflow"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Mise à jour du statut de la facture
                cursor.execute("""
                    UPDATE invoices 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (rule.to_state.value, invoice_id))
                
                # Enregistrement de la transition
                cursor.execute("""
                    INSERT INTO workflow_transitions (
                        invoice_id, from_state, to_state, action,
                        executed_by, transition_data, comments
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    invoice_id, current_state.value, rule.to_state.value,
                    rule.action.value, executed_by,
                    json.dumps(transition_data) if transition_data else None,
                    comments
                ))
                
                transition_id = cursor.lastrowid
                
                # Actions spécifiques selon le type de transition
                self._execute_state_specific_actions(invoice_id, rule.to_state, transition_data)
                
                conn.commit()
                
                logger.info(f"Transition exécutée: facture {invoice_id} {current_state.value} -> {rule.to_state.value}")
                
                return {
                    'success': True,
                    'transition_id': transition_id,
                    'old_state': current_state.value,
                    'new_state': rule.to_state.value,
                    'message': f'Transition réussie vers {rule.to_state.value}'
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la transition: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_state_specific_actions(self, invoice_id: int, new_state: WorkflowState,
                                      transition_data: Dict[str, Any]):
        """Exécute des actions spécifiques selon l'état"""
        if new_state == WorkflowState.PAID:
            # Enregistrement automatique du paiement si données fournies
            if transition_data and 'payment_data' in transition_data:
                payment_data = transition_data['payment_data']
                payment_data['invoice_id'] = invoice_id
                self.db.record_payment(payment_data)
        
        elif new_state == WorkflowState.SENT:
            # Mise à jour de la date d'envoi
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE invoices 
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (invoice_id,))
        
        elif new_state == WorkflowState.OVERDUE:
            # Calcul et application éventuelle de pénalités
            self._apply_late_fees_if_configured(invoice_id)
    
    def _process_auto_transitions(self, invoice_id: int, current_state: WorkflowState):
        """Traite les transitions automatiques suivantes"""
        # Recherche des règles automatiques applicables
        for rule in self._rules_cache.values():
            if (rule.from_state == current_state and 
                rule.auto_execute and 
                rule.is_active):
                
                # Récupération de la facture mise à jour
                invoice = self.db.get_invoice(invoice_id)
                if invoice and self._rule_applies_to_invoice(rule, invoice):
                    
                    # Vérification des conditions auto
                    conditions_check = self._check_transition_conditions(invoice, rule)
                    if conditions_check['valid']:
                        # Exécution automatique
                        self.transition_invoice(
                            invoice_id, 
                            rule.action.value,
                            executed_by="system_auto",
                            comments="Transition automatique"
                        )
                        break  # Une seule transition auto par appel
    
    def approve_transition(self, transition_id: int, approved_by: str,
                          approval_comments: str = "") -> Dict[str, Any]:
        """
        Approuve une transition en attente
        
        Args:
            transition_id: ID de la transition
            approved_by: Utilisateur approuvant
            approval_comments: Commentaires d'approbation
            
        Returns:
            Dict: Résultat de l'approbation
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Récupération de la transition
                cursor.execute("""
                    SELECT * FROM workflow_transitions WHERE id = ?
                """, (transition_id,))
                transition_row = cursor.fetchone()
                
                if not transition_row:
                    return {
                        'success': False,
                        'error': 'Transition non trouvée'
                    }
                
                # Vérification des approbations en attente
                cursor.execute("""
                    SELECT * FROM workflow_approvals 
                    WHERE transition_id = ? AND status = 'pending'
                """, (transition_id,))
                pending_approvals = cursor.fetchall()
                
                if not pending_approvals:
                    return {
                        'success': False,
                        'error': 'Aucune approbation en attente'
                    }
                
                # Approbation de toutes les demandes en attente
                cursor.execute("""
                    UPDATE workflow_approvals 
                    SET status = 'approved', approved_by = ?, approved_at = CURRENT_TIMESTAMP
                    WHERE transition_id = ? AND status = 'pending'
                """, (approved_by, transition_id))
                
                # Mise à jour de la transition
                cursor.execute("""
                    UPDATE workflow_transitions 
                    SET approved_by = ?, approved_at = CURRENT_TIMESTAMP,
                        comments = COALESCE(comments, '') || ' | Approuvé: ' || ?
                    WHERE id = ?
                """, (approved_by, approval_comments, transition_id))
                
                # Exécution de la transition approuvée
                invoice_id = transition_row['invoice_id']
                to_state = WorkflowState(transition_row['to_state'])
                
                # Mise à jour du statut de la facture
                cursor.execute("""
                    UPDATE invoices 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (to_state.value, invoice_id))
                
                conn.commit()
                
                # Callback de changement d'état
                if self.on_state_changed:
                    self.on_state_changed({
                        'invoice_id': invoice_id,
                        'old_state': transition_row['from_state'],
                        'new_state': to_state.value,
                        'action': transition_row['action'],
                        'executed_by': approved_by,
                        'approved': True
                    })
                
                # Traitement des transitions automatiques suivantes
                self._process_auto_transitions(invoice_id, to_state)
                
                logger.info(f"Transition {transition_id} approuvée par {approved_by}")
                
                return {
                    'success': True,
                    'message': 'Transition approuvée et exécutée',
                    'invoice_id': invoice_id,
                    'new_state': to_state.value
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de l'approbation de la transition {transition_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def reject_transition(self, transition_id: int, rejected_by: str,
                         rejection_reason: str) -> Dict[str, Any]:
        """Rejette une transition en attente"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Mise à jour des approbations
                cursor.execute("""
                    UPDATE workflow_approvals 
                    SET status = 'rejected', approved_by = ?, 
                        rejection_reason = ?, approved_at = CURRENT_TIMESTAMP
                    WHERE transition_id = ? AND status = 'pending'
                """, (rejected_by, rejection_reason, transition_id))
                
                # Suppression de la transition en attente
                cursor.execute("""
                    DELETE FROM workflow_transitions WHERE id = ?
                """, (transition_id,))
                
                conn.commit()
                
                logger.info(f"Transition {transition_id} rejetée par {rejected_by}: {rejection_reason}")
                
                return {
                    'success': True,
                    'message': 'Transition rejetée'
                }
                
        except Exception as e:
            logger.error(f"Erreur lors du rejet de la transition {transition_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_pending_approvals(self, user_role: str = None) -> List[Dict[str, Any]]:
        """Récupère les approbations en attente"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    wa.*,
                    wt.invoice_id,
                    wt.from_state,
                    wt.to_state,
                    wt.action,
                    wt.executed_by,
                    wt.comments as transition_comments,
                    i.invoice_number,
                    i.total_amount,
                    p.name as participant_name
                FROM workflow_approvals wa
                JOIN workflow_transitions wt ON wa.transition_id = wt.id
                JOIN invoices i ON wt.invoice_id = i.id
                JOIN participants p ON i.participant_id = p.id
                WHERE wa.status = 'pending'
            """
            
            params = []
            if user_role:
                query += " AND wa.required_role = ?"
                params.append(user_role)
            
            query += " ORDER BY wa.created_at"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_invoice_workflow_history(self, invoice_id: int) -> List[Dict[str, Any]]:
        """Récupère l'historique de workflow d'une facture"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    wt.*,
                    wa.status as approval_status,
                    wa.approved_by as approver,
                    wa.approved_at as approval_date,
                    wa.rejection_reason
                FROM workflow_transitions wt
                LEFT JOIN workflow_approvals wa ON wt.id = wa.transition_id
                WHERE wt.invoice_id = ?
                ORDER BY wt.executed_at DESC
            """, (invoice_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def bulk_transition(self, invoice_ids: List[int], action: str,
                       executed_by: str = "system", **kwargs) -> Dict[str, Any]:
        """Exécute une transition en lot sur plusieurs factures"""
        results = {
            'success_count': 0,
            'failed_count': 0,
            'results': [],
            'errors': []
        }
        
        for invoice_id in invoice_ids:
            try:
                result = self.transition_invoice(
                    invoice_id, action, executed_by, **kwargs
                )
                
                results['results'].append({
                    'invoice_id': invoice_id,
                    'success': result['success'],
                    'message': result.get('message', result.get('error'))
                })
                
                if result['success']:
                    results['success_count'] += 1
                else:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'invoice_id': invoice_id,
                        'error': result.get('error')
                    })
                    
            except Exception as e:
                results['failed_count'] += 1
                results['errors'].append({
                    'invoice_id': invoice_id,
                    'error': str(e)
                })
        
        return results
    
    def _create_pending_transition(self, invoice_id: int, rule: WorkflowRule,
                                 executed_by: str, comments: str,
                                 transition_data: Dict[str, Any]) -> int:
        """Crée une transition en attente d'approbation"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO workflow_transitions (
                    invoice_id, from_state, to_state, action,
                    executed_by, approval_required, transition_data, comments
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_id, rule.from_state.value, rule.to_state.value,
                rule.action.value, executed_by, True,
                json.dumps(transition_data) if transition_data else None,
                comments
            ))
            
            return cursor.lastrowid
    
    def _create_approval_request(self, invoice_id: int, transition_id: int, role: str):
        """Crée une demande d'approbation"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO workflow_approvals (
                    invoice_id, transition_id, required_role
                ) VALUES (?, ?, ?)
            """, (invoice_id, transition_id, role))
    
    def _execute_hooks(self, event_type: str, state: WorkflowState, 
                      invoice_id: int, context: Dict[str, Any]):
        """Exécute les hooks de workflow"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM workflow_hooks 
                WHERE event_type = ? AND (target_state = ? OR target_state IS NULL)
                AND is_active = 1
            """, (event_type, state.value))
            
            for hook in cursor.fetchall():
                try:
                    self._execute_single_hook(hook, invoice_id, context)
                except Exception as e:
                    logger.error(f"Erreur lors de l'exécution du hook {hook['name']}: {e}")
    
    def _execute_single_hook(self, hook: Dict[str, Any], 
                           invoice_id: int, context: Dict[str, Any]):
        """Exécute un hook individuel"""
        hook_type = hook['hook_type']
        config = json.loads(hook['hook_config'])
        
        if hook_type == 'email':
            # Envoi d'email
            self._send_hook_email(config, invoice_id, context)
        elif hook_type == 'webhook':
            # Appel de webhook
            self._call_webhook(config, invoice_id, context)
        elif hook_type == 'script':
            # Exécution de script
            self._execute_script(config, invoice_id, context)
    
    def _send_hook_email(self, config: Dict[str, Any], 
                        invoice_id: int, context: Dict[str, Any]):
        """Envoie un email via hook"""
        # Implementation du hook email
        pass
    
    def _call_webhook(self, config: Dict[str, Any], 
                     invoice_id: int, context: Dict[str, Any]):
        """Appelle un webhook"""
        # Implementation du hook webhook
        pass
    
    def _execute_script(self, config: Dict[str, Any], 
                       invoice_id: int, context: Dict[str, Any]):
        """Exécute un script"""
        # Implementation du hook script
        pass
    
    def _get_participant(self, participant_id: int) -> Optional[Dict[str, Any]]:
        """Récupère les données d'un participant"""
        if not participant_id:
            return None
            
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM participants WHERE id = ?", (participant_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def _apply_late_fees_if_configured(self, invoice_id: int):
        """Applique les pénalités de retard si configuré"""
        # Vérification de la configuration des pénalités
        late_fee_rate = self.db.get_setting('late_fee_rate')
        if late_fee_rate:
            try:
                invoice = self.db.get_invoice(invoice_id)
                due_date = datetime.strptime(invoice['due_date'], '%Y-%m-%d').date()
                days_late = (date.today() - due_date).days
                
                if days_late > 0:
                    fee_amount = float(late_fee_rate) * days_late * invoice['total_amount'] / 100
                    
                    # Enregistrement de la pénalité
                    with self.db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO late_fees (
                                invoice_id, amount, days_late, applied_date
                            ) VALUES (?, ?, ?, ?)
                        """, (invoice_id, fee_amount, days_late, date.today().isoformat()))
                        
                    logger.info(f"Pénalité de {fee_amount}€ appliquée à la facture {invoice_id}")
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'application des pénalités: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du gestionnaire de workflow"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Statistiques des états
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM invoices 
                GROUP BY status
            """)
            state_counts = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Approbations en attente
            cursor.execute("""
                SELECT COUNT(*) FROM workflow_approvals WHERE status = 'pending'
            """)
            pending_approvals = cursor.fetchone()[0]
            
            # Transitions du jour
            cursor.execute("""
                SELECT COUNT(*) FROM workflow_transitions 
                WHERE date(executed_at) = date('now')
            """)
            daily_transitions = cursor.fetchone()[0]
            
            return {
                'rules_loaded': len(self._rules_cache),
                'state_counts': state_counts,
                'pending_approvals': pending_approvals,
                'daily_transitions': daily_transitions
            }