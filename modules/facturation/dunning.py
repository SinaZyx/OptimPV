"""
Dunning Management Module for OptimPV
Handles automated dunning process (debt collection reminders)
"""

import sqlite3
import logging
import smtplib
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

logger = logging.getLogger(__name__)

class DunningLevel(Enum):
    """Dunning reminder levels"""
    FRIENDLY_REMINDER = "friendly_reminder"
    FIRST_NOTICE = "first_notice"
    SECOND_NOTICE = "second_notice"
    FINAL_NOTICE = "final_notice"
    LEGAL_ACTION = "legal_action"

@dataclass
class DunningRule:
    """Dunning rule configuration"""
    level: DunningLevel
    days_after_due: int
    template_name: str
    include_late_fees: bool = False
    stop_services: bool = False
    escalate_to_legal: bool = False
    send_copy_to_manager: bool = False

@dataclass
class DunningAction:
    """Dunning action record"""
    id: Optional[int] = None
    invoice_id: int = 0
    level: DunningLevel = DunningLevel.FRIENDLY_REMINDER
    action_date: Optional[date] = None
    due_amount: float = 0.0
    late_fees_amount: float = 0.0
    email_sent: bool = False
    email_address: str = ""
    template_used: str = ""
    notes: str = ""
    next_action_date: Optional[date] = None
    next_action_level: Optional[DunningLevel] = None
    created_at: Optional[datetime] = None

class DunningManager:
    """Automated dunning process management"""
    
    def __init__(self, db_path: str = "data/billing.db"):
        """Initialize dunning manager"""
        self.db_path = db_path
        self.smtp_config = {}
        
        # Default dunning rules (French business practice)
        self.default_rules = [
            DunningRule(
                level=DunningLevel.FRIENDLY_REMINDER,
                days_after_due=7,
                template_name="friendly_reminder",
                include_late_fees=False
            ),
            DunningRule(
                level=DunningLevel.FIRST_NOTICE,
                days_after_due=15,
                template_name="first_notice",
                include_late_fees=True
            ),
            DunningRule(
                level=DunningLevel.SECOND_NOTICE,
                days_after_due=30,
                template_name="second_notice",
                include_late_fees=True,
                send_copy_to_manager=True
            ),
            DunningRule(
                level=DunningLevel.FINAL_NOTICE,
                days_after_due=45,
                template_name="final_notice",
                include_late_fees=True,
                stop_services=True,
                send_copy_to_manager=True
            ),
            DunningRule(
                level=DunningLevel.LEGAL_ACTION,
                days_after_due=60,
                template_name="legal_action",
                include_late_fees=True,
                escalate_to_legal=True,
                stop_services=True,
                send_copy_to_manager=True
            )
        ]
        
        # Default email templates
        self.email_templates = {
            "friendly_reminder": {
                "subject": "Rappel amical - Facture {invoice_number} échue",
                "body": """
Madame, Monsieur,

Nous espérons que vous allez bien. Nous souhaitons simplement vous rappeler que la facture suivante est arrivée à échéance :

Facture : {invoice_number}
Date d'échéance : {due_date}
Montant : {amount} €
Projet : {project_name}

Si vous avez déjà effectué ce paiement, veuillez ignorer ce message. Dans le cas contraire, nous vous serions reconnaissants de bien vouloir procéder au règlement dans les meilleurs délais.

Pour toute question concernant cette facture, n'hésitez pas à nous contacter.

Cordialement,
L'équipe OptimPV
                """
            },
            "first_notice": {
                "subject": "RAPPEL - Facture {invoice_number} impayée - Pénalités applicables",
                "body": """
Madame, Monsieur,

Malgré notre rappel amical, nous constatons que la facture suivante demeure impayée :

Facture : {invoice_number}
Date d'échéance : {due_date}
Montant initial : {original_amount} €
Pénalités de retard : {late_fees} €
MONTANT TOTAL DÛ : {total_amount} €

Conformément à l'article L441-6 du Code de commerce, des pénalités de retard au taux légal de {legal_rate}% s'appliquent automatiquement.

Nous vous demandons de bien vouloir régulariser cette situation sous 8 jours à compter de la réception de ce courrier.

À défaut, nous nous réservons le droit d'engager toute action en recouvrement.

Cordialement,
Service Comptabilité OptimPV
                """
            },
            "second_notice": {
                "subject": "MISE EN DEMEURE - Facture {invoice_number} - Dernier rappel avant action",
                "body": """
Madame, Monsieur,

MISE EN DEMEURE DE PAYER

Malgré nos précédents courriers, la facture suivante demeure impayée :

Facture : {invoice_number}
Date d'émission : {issue_date}
Date d'échéance : {due_date}
Montant initial : {original_amount} €
Pénalités de retard : {late_fees} €
MONTANT TOTAL DÛ : {total_amount} €

Nous vous mettons en demeure de procéder au paiement de cette somme dans un délai de 8 jours à compter de la réception de cette mise en demeure.

À défaut de paiement dans ce délai, nous engagerons sans autre avis une procédure de recouvrement contentieux, ce qui entraînera des frais supplémentaires à votre charge.

Cette mise en demeure vaut dernier avertissement avant action judiciaire.

Service Contentieux OptimPV
                """
            },
            "final_notice": {
                "subject": "DERNIER AVIS - Transmission au service juridique - Facture {invoice_number}",
                "body": """
Madame, Monsieur,

DERNIER AVIS AVANT TRANSMISSION AU SERVICE JURIDIQUE

La facture suivante demeure impayée malgré nos relances successives :

Facture : {invoice_number}
Montant total dû : {total_amount} €
Nombre de jours de retard : {days_overdue}

Ce dossier sera transmis à notre service juridique sous 48 heures pour engagement d'une procédure de recouvrement contentieux si aucun règlement n'intervient.

Cette procédure entraînera des frais supplémentaires à votre charge conformément aux dispositions légales.

Service Contentieux OptimPV
Tél : [Numéro de téléphone]
                """
            },
            "legal_action": {
                "subject": "Transmission dossier contentieux - Facture {invoice_number}",
                "body": """
Madame, Monsieur,

Votre dossier a été transmis à notre service juridique pour recouvrement contentieux.

Vous recevrez prochainement une assignation en paiement de notre avocat.

Facture concernée : {invoice_number}
Montant : {total_amount} €

Il est encore possible d'éviter cette procédure en nous contactant immédiatement.

Service Juridique OptimPV
                """
            }
        }
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def configure_smtp(self, smtp_host: str, smtp_port: int, username: str, password: str, use_tls: bool = True):
        """Configure SMTP settings for email sending"""
        self.smtp_config = {
            'host': smtp_host,
            'port': smtp_port,
            'username': username,
            'password': password,
            'use_tls': use_tls
        }
    
    def get_overdue_invoices(self) -> List[Dict[str, Any]]:
        """Get all overdue invoices that need dunning action"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    i.*,
                    p.name as participant_name,
                    p.contact_email,
                    pr.name as project_name,
                    JULIANDAY('now') - JULIANDAY(i.due_date) as days_overdue,
                    COALESCE(SUM(pay.amount), 0) as total_paid,
                    COALESCE(MAX(da.action_date), '') as last_dunning_date,
                    COALESCE(MAX(da.level), '') as last_dunning_level
                FROM invoices i
                JOIN participants p ON i.participant_id = p.id
                JOIN billing_periods bp ON i.billing_period_id = bp.id
                JOIN projects pr ON bp.project_id = pr.id
                LEFT JOIN payments pay ON i.id = pay.invoice_id
                LEFT JOIN dunning_actions da ON i.id = da.invoice_id
                WHERE i.status IN ('sent', 'overdue') 
                AND i.due_date < date('now')
                GROUP BY i.id
                HAVING total_paid < i.total_amount
                ORDER BY days_overdue DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def process_dunning_cycle(self, dry_run: bool = False) -> Dict[str, Any]:
        """Process automatic dunning cycle for all overdue invoices"""
        overdue_invoices = self.get_overdue_invoices()
        processed_actions = []
        errors = []
        
        for invoice in overdue_invoices:
            try:
                action = self._determine_next_dunning_action(invoice)
                if action:
                    if not dry_run:
                        result = self._execute_dunning_action(invoice, action)
                        if result:
                            processed_actions.append(result)
                        else:
                            errors.append(f"Failed to execute action for invoice {invoice['invoice_number']}")
                    else:
                        processed_actions.append({
                            'invoice_id': invoice['id'],
                            'invoice_number': invoice['invoice_number'],
                            'action_level': action.level.value,
                            'days_overdue': int(invoice['days_overdue']),
                            'amount': invoice['total_amount'] - invoice['total_paid'],
                            'dry_run': True
                        })
            except Exception as e:
                logger.error(f"Error processing dunning for invoice {invoice.get('invoice_number', 'unknown')}: {str(e)}")
                errors.append(f"Error processing invoice {invoice.get('invoice_number', 'unknown')}: {str(e)}")
        
        return {
            'processed_count': len(processed_actions),
            'error_count': len(errors),
            'actions': processed_actions,
            'errors': errors
        }
    
    def _determine_next_dunning_action(self, invoice: Dict[str, Any]) -> Optional[DunningAction]:
        """Determine the next appropriate dunning action for an invoice"""
        days_overdue = int(invoice['days_overdue'])
        last_level = invoice.get('last_dunning_level', '')
        outstanding_amount = invoice['total_amount'] - invoice['total_paid']
        
        # Find the appropriate rule based on days overdue
        applicable_rule = None
        for rule in self.default_rules:
            if days_overdue >= rule.days_after_due:
                # Check if we haven't already sent this level
                if not last_level or self._is_escalation_needed(last_level, rule.level):
                    applicable_rule = rule
                    break
        
        if not applicable_rule:
            return None
        
        # Calculate late fees if applicable
        late_fees = 0.0
        if applicable_rule.include_late_fees:
            late_fees = self._calculate_late_fees(invoice, days_overdue)
        
        # Determine next action
        next_rule = self._get_next_rule(applicable_rule.level)
        next_action_date = None
        next_action_level = None
        
        if next_rule:
            next_action_date = date.today() + timedelta(days=next_rule.days_after_due - applicable_rule.days_after_due)
            next_action_level = next_rule.level
        
        return DunningAction(
            invoice_id=invoice['id'],
            level=applicable_rule.level,
            action_date=date.today(),
            due_amount=outstanding_amount,
            late_fees_amount=late_fees,
            email_address=invoice['contact_email'],
            template_used=applicable_rule.template_name,
            next_action_date=next_action_date,
            next_action_level=next_action_level
        )
    
    def _is_escalation_needed(self, last_level: str, new_level: DunningLevel) -> bool:
        """Check if escalation to new level is needed"""
        level_order = [level.value for level in DunningLevel]
        
        try:
            last_index = level_order.index(last_level)
            new_index = level_order.index(new_level.value)
            return new_index > last_index
        except ValueError:
            return True  # If level not found, proceed with action
    
    def _get_next_rule(self, current_level: DunningLevel) -> Optional[DunningRule]:
        """Get the next dunning rule after current level"""
        current_index = -1
        for i, rule in enumerate(self.default_rules):
            if rule.level == current_level:
                current_index = i
                break
        
        if current_index >= 0 and current_index < len(self.default_rules) - 1:
            return self.default_rules[current_index + 1]
        
        return None
    
    def _calculate_late_fees(self, invoice: Dict[str, Any], days_overdue: int) -> float:
        """Calculate late fees for overdue invoice"""
        base_amount = invoice['total_amount']
        legal_rate = 3.40  # French legal rate 2024
        daily_rate = legal_rate / 100 / 365
        return round(base_amount * daily_rate * days_overdue, 2)
    
    def _execute_dunning_action(self, invoice: Dict[str, Any], action: DunningAction) -> Optional[Dict[str, Any]]:
        """Execute a dunning action (send email, record action)"""
        try:
            # Record the action in database
            action_id = self._record_dunning_action(action)
            
            # Send email if email address is available
            email_sent = False
            if action.email_address and self.smtp_config:
                email_sent = self._send_dunning_email(invoice, action)
            
            # Apply late fees if applicable
            if action.late_fees_amount > 0:
                self._apply_late_fees(invoice['id'], action.late_fees_amount)
            
            # Update invoice status if needed
            if action.level in [DunningLevel.FINAL_NOTICE, DunningLevel.LEGAL_ACTION]:
                self._update_invoice_status(invoice['id'], 'overdue')
            
            # Schedule next action if applicable
            if action.next_action_date and action.next_action_level:
                self._schedule_next_action(action)
            
            return {
                'action_id': action_id,
                'invoice_id': invoice['id'],
                'invoice_number': invoice['invoice_number'],
                'level': action.level.value,
                'email_sent': email_sent,
                'late_fees_applied': action.late_fees_amount,
                'next_action_date': action.next_action_date.isoformat() if action.next_action_date else None
            }
            
        except Exception as e:
            logger.error(f"Error executing dunning action: {str(e)}")
            return None
    
    def _record_dunning_action(self, action: DunningAction) -> int:
        """Record dunning action in database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dunning_actions (
                    invoice_id, level, action_date, due_amount, late_fees_amount,
                    email_sent, email_address, template_used, notes,
                    next_action_date, next_action_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                action.invoice_id,
                action.level.value,
                action.action_date.isoformat(),
                action.due_amount,
                action.late_fees_amount,
                action.email_sent,
                action.email_address,
                action.template_used,
                action.notes,
                action.next_action_date.isoformat() if action.next_action_date else None,
                action.next_action_level.value if action.next_action_level else None
            ))
            return cursor.lastrowid
    
    def _send_dunning_email(self, invoice: Dict[str, Any], action: DunningAction) -> bool:
        """Send dunning email"""
        try:
            if action.template_used not in self.email_templates:
                logger.error(f"Email template '{action.template_used}' not found")
                return False
            
            template = self.email_templates[action.template_used]
            
            # Prepare email content
            subject = template['subject'].format(
                invoice_number=invoice['invoice_number']
            )
            
            body = template['body'].format(
                invoice_number=invoice['invoice_number'],
                due_date=invoice['due_date'],
                issue_date=invoice['issue_date'],
                amount=f"{action.due_amount:.2f}",
                original_amount=f"{invoice['total_amount']:.2f}",
                late_fees=f"{action.late_fees_amount:.2f}",
                total_amount=f"{action.due_amount + action.late_fees_amount:.2f}",
                project_name=invoice['project_name'],
                participant_name=invoice['participant_name'],
                days_overdue=int(invoice['days_overdue']),
                legal_rate="3.40"
            )
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['username']
            msg['To'] = action.email_address
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Send email
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                if self.smtp_config['use_tls']:
                    server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            logger.info(f"Dunning email sent for invoice {invoice['invoice_number']} to {action.email_address}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending dunning email: {str(e)}")
            return False
    
    def _apply_late_fees(self, invoice_id: int, fee_amount: float):
        """Apply late fees to invoice"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO late_fees (invoice_id, amount, reason, applied_date)
                VALUES (?, ?, 'Automatic dunning late fee', date('now'))
            """, (invoice_id, fee_amount))
            
            cursor.execute("""
                UPDATE invoices 
                SET total_amount = total_amount + ?
                WHERE id = ?
            """, (fee_amount, invoice_id))
    
    def _update_invoice_status(self, invoice_id: int, status: str):
        """Update invoice status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE invoices SET status = ? WHERE id = ?
            """, (status, invoice_id))
    
    def _schedule_next_action(self, action: DunningAction):
        """Schedule next dunning action"""
        # This could be implemented to integrate with a task scheduler
        # For now, we just record the next action date in the current action
        pass
    
    # ===== Manual Dunning Management =====
    
    def send_manual_dunning(self, invoice_id: int, level: DunningLevel, 
                           custom_message: str = None, email_address: str = None) -> bool:
        """Send manual dunning notice"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.*, p.name as participant_name, p.contact_email, pr.name as project_name
                FROM invoices i
                JOIN participants p ON i.participant_id = p.id
                JOIN billing_periods bp ON i.billing_period_id = bp.id
                JOIN projects pr ON bp.project_id = pr.id
                WHERE i.id = ?
            """, (invoice_id,))
            
            invoice = dict(cursor.fetchone()) if cursor.fetchone() else None
            if not invoice:
                return False
            
            # Calculate outstanding amount
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM payments WHERE invoice_id = ?
            """, (invoice_id,))
            total_paid = cursor.fetchone()[0]
            outstanding_amount = invoice['total_amount'] - total_paid
            
            # Create action
            action = DunningAction(
                invoice_id=invoice_id,
                level=level,
                action_date=date.today(),
                due_amount=outstanding_amount,
                email_address=email_address or invoice['contact_email'],
                template_used=level.value,
                notes=custom_message or ""
            )
            
            return self._execute_dunning_action(invoice, action) is not None
    
    def get_dunning_history(self, invoice_id: int = None) -> List[Dict[str, Any]]:
        """Get dunning history for an invoice or all invoices"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if invoice_id:
                cursor.execute("""
                    SELECT da.*, i.invoice_number, p.name as participant_name
                    FROM dunning_actions da
                    JOIN invoices i ON da.invoice_id = i.id
                    JOIN participants p ON i.participant_id = p.id
                    WHERE da.invoice_id = ?
                    ORDER BY da.action_date DESC
                """, (invoice_id,))
            else:
                cursor.execute("""
                    SELECT da.*, i.invoice_number, p.name as participant_name
                    FROM dunning_actions da
                    JOIN invoices i ON da.invoice_id = i.id
                    JOIN participants p ON i.participant_id = p.id
                    ORDER BY da.action_date DESC
                    LIMIT 100
                """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_dunning_statistics(self) -> Dict[str, Any]:
        """Get dunning process statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total overdue invoices
            cursor.execute("""
                SELECT COUNT(*), SUM(total_amount)
                FROM invoices
                WHERE status IN ('sent', 'overdue') AND due_date < date('now')
            """)
            overdue_stats = cursor.fetchone()
            
            # Dunning actions by level
            cursor.execute("""
                SELECT level, COUNT(*), SUM(due_amount)
                FROM dunning_actions
                WHERE action_date >= date('now', '-30 days')
                GROUP BY level
            """)
            level_stats = {row[0]: {'count': row[1], 'amount': row[2]} for row in cursor.fetchall()}
            
            # Success rate (invoices paid after dunning)
            cursor.execute("""
                SELECT COUNT(DISTINCT da.invoice_id)
                FROM dunning_actions da
                JOIN invoices i ON da.invoice_id = i.id
                WHERE da.action_date >= date('now', '-90 days')
                AND i.status = 'paid'
                AND i.payment_date > da.action_date
            """)
            paid_after_dunning = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(DISTINCT invoice_id)
                FROM dunning_actions
                WHERE action_date >= date('now', '-90 days')
            """)
            total_dunning_actions = cursor.fetchone()[0]
            
            success_rate = (paid_after_dunning / total_dunning_actions * 100) if total_dunning_actions > 0 else 0
            
            return {
                'overdue_invoices_count': overdue_stats[0] or 0,
                'overdue_total_amount': overdue_stats[1] or 0,
                'dunning_actions_by_level': level_stats,
                'success_rate_percent': round(success_rate, 2),
                'invoices_paid_after_dunning': paid_after_dunning
            }
    
    # ===== Template Management =====
    
    def update_email_template(self, template_name: str, subject: str, body: str):
        """Update email template"""
        if template_name in self.email_templates:
            self.email_templates[template_name] = {
                'subject': subject,
                'body': body
            }
            # Save to database or config file
            self._save_template_to_db(template_name, subject, body)
    
    def _save_template_to_db(self, template_name: str, subject: str, body: str):
        """Save email template to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO email_templates (name, subject, body, updated_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (template_name, subject, body))
    
    def load_templates_from_db(self):
        """Load email templates from database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, subject, body FROM email_templates")
                for row in cursor.fetchall():
                    self.email_templates[row[0]] = {
                        'subject': row[1],
                        'body': row[2]
                    }
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            pass