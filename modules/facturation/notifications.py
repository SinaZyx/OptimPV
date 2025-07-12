"""
Module de gestion des notifications pour le système de facturation
Gère les alertes multi-canaux (email, SMS, webhooks) et templates
"""

import logging
import smtplib
import requests
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import threading
import queue
import time
import re

from .database import BillingDatabase

logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    """Canaux de notification"""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    PUSH = "push"

class NotificationPriority(Enum):
    """Priorités de notification"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class NotificationStatus(Enum):
    """États des notifications"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"

@dataclass
class NotificationTemplate:
    """Template de notification"""
    id: Optional[int] = None
    name: str = ""
    channel: NotificationChannel = NotificationChannel.EMAIL
    subject: str = ""
    body: str = ""
    html_body: str = ""
    
    # Variables dynamiques supportées
    variables: List[str] = None
    
    # Configuration spécifique au canal
    channel_config: Dict[str, Any] = None
    
    # Métadonnées
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = []
        if self.channel_config is None:
            self.channel_config = {}

@dataclass
class NotificationConfig:
    """Configuration des notifications"""
    # Email
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    from_email: str = ""
    from_name: str = "OptimPV"
    
    # SMS
    sms_provider: str = ""  # twilio, ovh, etc.
    sms_api_key: str = ""
    sms_api_secret: str = ""
    sms_sender: str = ""
    
    # Webhooks
    webhook_timeout: int = 30
    webhook_retries: int = 3
    
    # Général
    max_retry_attempts: int = 3
    retry_delay_minutes: int = 5
    batch_size: int = 50
    rate_limit_per_minute: int = 100

@dataclass
class Notification:
    """Notification à envoyer"""
    id: Optional[str] = None
    channel: NotificationChannel = NotificationChannel.EMAIL
    priority: NotificationPriority = NotificationPriority.NORMAL
    
    # Destinataires
    recipients: List[str] = None
    cc_recipients: List[str] = None
    bcc_recipients: List[str] = None
    
    # Contenu
    subject: str = ""
    body: str = ""
    html_body: str = ""
    attachments: List[str] = None
    
    # Planification
    send_at: Optional[datetime] = None
    
    # État
    status: NotificationStatus = NotificationStatus.PENDING
    retry_count: int = 0
    last_error: Optional[str] = None
    sent_at: Optional[datetime] = None
    
    # Métadonnées
    template_id: Optional[int] = None
    context_data: Dict[str, Any] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.recipients is None:
            self.recipients = []
        if self.cc_recipients is None:
            self.cc_recipients = []
        if self.bcc_recipients is None:
            self.bcc_recipients = []
        if self.attachments is None:
            self.attachments = []
        if self.context_data is None:
            self.context_data = {}
        if self.tags is None:
            self.tags = []
        if self.id is None:
            import uuid
            self.id = str(uuid.uuid4())

class NotificationManager:
    """
    Gestionnaire de notifications multi-canaux
    Gère les alertes, templates et envois automatiques
    """
    
    def __init__(self, db: BillingDatabase):
        """
        Initialise le gestionnaire
        
        Args:
            db: Instance de base de données
        """
        self.db = db
        self._ensure_tables()
        
        # Configuration
        self.config = self._load_config()
        
        # État du gestionnaire
        self.is_running = False
        
        # Threads et queues
        self.sender_thread: Optional[threading.Thread] = None
        self.notification_queue = queue.PriorityQueue()
        self.stop_event = threading.Event()
        
        # Cache des templates
        self.templates_cache: Dict[str, NotificationTemplate] = {}
        self._load_templates()
        
        # Limiteur de débit
        self.rate_limiter = {
            'count': 0,
            'last_reset': datetime.now()
        }
        
        # Métriques
        self.metrics = {
            'notifications_sent': 0,
            'notifications_failed': 0,
            'emails_sent': 0,
            'sms_sent': 0,
            'webhooks_sent': 0,
            'total_processing_time': 0.0
        }
        
        logger.info("NotificationManager initialisé")
    
    def _ensure_tables(self):
        """Assure l'existence des tables requises"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Table des templates de notification
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notification_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    channel TEXT NOT NULL,
                    subject TEXT,
                    body TEXT NOT NULL,
                    html_body TEXT,
                    variables TEXT, -- JSON array
                    channel_config TEXT, -- JSON object
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table de l'historique des notifications
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notification_history (
                    id TEXT PRIMARY KEY,
                    channel TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    recipients TEXT NOT NULL, -- JSON array
                    subject TEXT,
                    body TEXT,
                    template_id INTEGER,
                    status TEXT NOT NULL,
                    retry_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    sent_at TIMESTAMP,
                    context_data TEXT, -- JSON object
                    tags TEXT, -- JSON array
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (template_id) REFERENCES notification_templates(id)
                )
            """)
            
            # Table des préférences de notification des utilisateurs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notification_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_email TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    frequency TEXT DEFAULT 'immediate', -- immediate, daily, weekly
                    quiet_hours_start TEXT, -- HH:MM
                    quiet_hours_end TEXT,   -- HH:MM
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_email, channel)
                )
            """)
            
            # Table des notifications en lot
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notification_batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    total_count INTEGER NOT NULL,
                    sent_count INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index pour optimisation
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notification_history_status ON notification_history(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notification_history_created ON notification_history(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notification_preferences_user ON notification_preferences(user_email)")
            
            # Insertion des templates par défaut
            self._insert_default_templates(cursor)
            
            conn.commit()
    
    def _insert_default_templates(self, cursor):
        """Insère les templates par défaut"""
        default_templates = [
            {
                'name': 'invoice_created',
                'channel': 'email',
                'subject': 'Nouvelle facture OptimPV - {{invoice_number}}',
                'body': '''Bonjour {{participant_name}},

Une nouvelle facture a été générée pour votre projet {{project_name}}.

Numéro de facture : {{invoice_number}}
Montant : {{total_amount}}€
Date d'échéance : {{due_date}}

Vous pouvez consulter et télécharger votre facture en vous connectant à votre espace client.

Cordialement,
L'équipe OptimPV''',
                'html_body': '''<p>Bonjour {{participant_name}},</p>
<p>Une nouvelle facture a été générée pour votre projet <strong>{{project_name}}</strong>.</p>
<ul>
<li>Numéro de facture : <strong>{{invoice_number}}</strong></li>
<li>Montant : <strong>{{total_amount}}€</strong></li>
<li>Date d'échéance : <strong>{{due_date}}</strong></li>
</ul>
<p>Vous pouvez consulter et télécharger votre facture en vous connectant à votre espace client.</p>
<p>Cordialement,<br>L'équipe OptimPV</p>''',
                'variables': '["participant_name", "project_name", "invoice_number", "total_amount", "due_date"]'
            },
            {
                'name': 'payment_reminder',
                'channel': 'email',
                'subject': 'Rappel de paiement - Facture {{invoice_number}}',
                'body': '''Bonjour {{participant_name}},

Nous vous rappelons que la facture {{invoice_number}} d'un montant de {{total_amount}}€ 
était échue le {{due_date}}.

Merci de procéder au règlement dans les plus brefs délais.

En cas de question, n'hésitez pas à nous contacter.

Cordialement,
L'équipe OptimPV''',
                'variables': '["participant_name", "invoice_number", "total_amount", "due_date"]'
            },
            {
                'name': 'payment_received',
                'channel': 'email',
                'subject': 'Confirmation de paiement - Facture {{invoice_number}}',
                'body': '''Bonjour {{participant_name}},

Nous vous confirmons la réception de votre paiement de {{payment_amount}}€ 
pour la facture {{invoice_number}}.

Date de paiement : {{payment_date}}

Merci pour votre confiance.

Cordialement,
L'équipe OptimPV''',
                'variables': '["participant_name", "invoice_number", "payment_amount", "payment_date"]'
            },
            {
                'name': 'recurring_generation_success',
                'channel': 'email',
                'subject': 'Génération automatique des factures - {{generation_date}}',
                'body': '''Bonjour,

La génération automatique des factures récurrentes s'est terminée avec succès.

- Factures générées : {{generated_count}}
- Date de génération : {{generation_date}}

Détails disponibles dans l'interface d'administration.

Cordialement,
Système OptimPV''',
                'variables': '["generated_count", "generation_date"]'
            }
        ]
        
        for template in default_templates:
            cursor.execute("""
                INSERT OR IGNORE INTO notification_templates (
                    name, channel, subject, body, html_body, variables
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                template['name'], template['channel'], template['subject'],
                template['body'], template.get('html_body'),
                template.get('variables')
            ))
    
    def start(self) -> bool:
        """
        Démarre le gestionnaire de notifications
        
        Returns:
            bool: True si démarré avec succès
        """
        try:
            if self.is_running:
                logger.warning("NotificationManager déjà en cours d'exécution")
                return True
            
            self.is_running = True
            self.stop_event.clear()
            
            # Démarrage du thread d'envoi
            self.sender_thread = threading.Thread(target=self._sender_loop, daemon=True)
            self.sender_thread.start()
            
            logger.info("NotificationManager démarré")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du NotificationManager: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Arrête le gestionnaire de notifications
        
        Returns:
            bool: True si arrêté avec succès
        """
        try:
            self.is_running = False
            self.stop_event.set()
            
            # Attente de l'arrêt du thread
            if self.sender_thread and self.sender_thread.is_alive():
                self.sender_thread.join(timeout=5)
            
            logger.info("NotificationManager arrêté")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt du NotificationManager: {e}")
            return False
    
    def send_notification(self, notification_data: Dict[str, Any]) -> bool:
        """
        Envoie une notification
        
        Args:
            notification_data: Données de la notification
            
        Returns:
            bool: True si mise en queue avec succès
        """
        try:
            # Création de l'objet notification
            notification = self._create_notification_from_data(notification_data)
            
            # Vérification des préférences utilisateur
            if not self._check_user_preferences(notification):
                logger.info(f"Notification {notification.id} ignorée selon les préférences utilisateur")
                return True
            
            # Mise en queue avec priorité
            priority = 5 - notification.priority.value  # Inversion pour PriorityQueue
            queue_item = (priority, datetime.now(), notification)
            self.notification_queue.put(queue_item)
            
            logger.debug(f"Notification {notification.id} mise en queue")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification: {e}")
            return False
    
    def send_notification_from_template(self, template_name: str, 
                                      recipients: List[str],
                                      context_data: Dict[str, Any],
                                      **kwargs) -> bool:
        """
        Envoie une notification basée sur un template
        
        Args:
            template_name: Nom du template
            recipients: Liste des destinataires
            context_data: Données pour remplir le template
            **kwargs: Arguments supplémentaires
            
        Returns:
            bool: True si envoyée avec succès
        """
        try:
            template = self._get_template(template_name)
            if not template:
                logger.error(f"Template {template_name} non trouvé")
                return False
            
            # Rendu du template
            subject = self._render_template(template.subject, context_data)
            body = self._render_template(template.body, context_data)
            html_body = self._render_template(template.html_body, context_data) if template.html_body else ""
            
            # Création de la notification
            notification_data = {
                'channel': template.channel.value,
                'recipients': recipients,
                'subject': subject,
                'body': body,
                'html_body': html_body,
                'template_id': template.id,
                'context_data': context_data,
                **kwargs
            }
            
            return self.send_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi depuis le template {template_name}: {e}")
            return False
    
    def send_invoice_email(self, invoice: Dict[str, Any], 
                          participant: Dict[str, Any],
                          attach_pdf: bool = True) -> bool:
        """Envoie un email de facture"""
        try:
            context_data = {
                'participant_name': participant['name'],
                'project_name': invoice.get('project_name', 'Projet'),
                'invoice_number': invoice['invoice_number'],
                'total_amount': f"{invoice['total_amount']:.2f}",
                'due_date': invoice['due_date']
            }
            
            notification_data = {
                'recipients': [participant['contact_email']],
                'attachments': [f"invoice_{invoice['invoice_number']}.pdf"] if attach_pdf else [],
                'tags': ['invoice', 'automatic']
            }
            
            return self.send_notification_from_template(
                'invoice_created', 
                notification_data['recipients'],
                context_data,
                **notification_data
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de facture: {e}")
            return False
    
    def send_dunning_email(self, invoice: Dict[str, Any], level: str) -> bool:
        """Envoie un email de relance"""
        try:
            # Récupération du participant
            participant = self._get_participant(invoice['participant_id'])
            if not participant or not participant.get('contact_email'):
                return False
            
            context_data = {
                'participant_name': participant['name'],
                'invoice_number': invoice['invoice_number'],
                'total_amount': f"{invoice['total_amount']:.2f}",
                'due_date': invoice['due_date']
            }
            
            # Template selon le niveau de relance
            template_name = 'payment_reminder'
            if level == 'final_notice':
                template_name = 'final_payment_notice'
            elif level == 'legal_action':
                template_name = 'legal_action_notice'
            
            return self.send_notification_from_template(
                template_name,
                [participant['contact_email']],
                context_data,
                tags=['dunning', level, 'automatic'],
                priority='high' if level in ['final_notice', 'legal_action'] else 'normal'
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la relance: {e}")
            return False
    
    def send_batch_notifications(self, batch_name: str, 
                               notifications: List[Dict[str, Any]]) -> int:
        """
        Envoie un lot de notifications
        
        Args:
            batch_name: Nom du lot
            notifications: Liste des notifications à envoyer
            
        Returns:
            int: ID du lot créé
        """
        try:
            # Création du lot en base
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO notification_batches (name, total_count)
                    VALUES (?, ?)
                """, (batch_name, len(notifications)))
                
                batch_id = cursor.lastrowid
            
            # Envoi des notifications
            for notification_data in notifications:
                notification_data['tags'] = notification_data.get('tags', []) + [f'batch_{batch_id}']
                self.send_notification(notification_data)
            
            logger.info(f"Lot de {len(notifications)} notifications créé (ID: {batch_id})")
            return batch_id
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du lot {batch_name}: {e}")
            return 0
    
    def _sender_loop(self):
        """Boucle principale d'envoi des notifications"""
        logger.info("Boucle d'envoi des notifications démarrée")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # Récupération d'une notification avec timeout
                try:
                    item = self.notification_queue.get(timeout=1)
                    priority, queued_at, notification = item
                except queue.Empty:
                    continue
                
                # Vérification du limiteur de débit
                if not self._check_rate_limit():
                    # Remettre en queue et attendre
                    self.notification_queue.put(item)
                    time.sleep(60)  # Attendre 1 minute
                    continue
                
                # Envoi de la notification
                success = self._send_notification(notification)
                
                # Marquer comme terminé dans la queue
                self.notification_queue.task_done()
                
                # Mise à jour des métriques
                if success:
                    self.metrics['notifications_sent'] += 1
                    self._update_channel_metrics(notification.channel)
                else:
                    self.metrics['notifications_failed'] += 1
                
            except Exception as e:
                logger.error(f"Erreur dans la boucle d'envoi: {e}")
                time.sleep(5)
        
        logger.info("Boucle d'envoi des notifications arrêtée")
    
    def _send_notification(self, notification: Notification) -> bool:
        """
        Envoie une notification selon son canal
        
        Args:
            notification: Notification à envoyer
            
        Returns:
            bool: True si envoyée avec succès
        """
        start_time = datetime.now()
        
        try:
            # Vérification de la planification
            if notification.send_at and notification.send_at > datetime.now():
                # Remettre en queue pour plus tard
                priority = 5 - notification.priority.value
                queue_item = (priority, notification.send_at, notification)
                self.notification_queue.put(queue_item)
                return True
            
            # Envoi selon le canal
            success = False
            
            if notification.channel == NotificationChannel.EMAIL:
                success = self._send_email(notification)
            elif notification.channel == NotificationChannel.SMS:
                success = self._send_sms(notification)
            elif notification.channel == NotificationChannel.WEBHOOK:
                success = self._send_webhook(notification)
            elif notification.channel == NotificationChannel.SLACK:
                success = self._send_slack(notification)
            elif notification.channel == NotificationChannel.TEAMS:
                success = self._send_teams(notification)
            else:
                logger.error(f"Canal non supporté: {notification.channel}")
                success = False
            
            # Mise à jour du statut
            if success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.now()
                notification.last_error = None
            else:
                notification.retry_count += 1
                if notification.retry_count < self.config.max_retry_attempts:
                    notification.status = NotificationStatus.PENDING
                    # Programmer un retry
                    retry_time = datetime.now() + timedelta(minutes=self.config.retry_delay_minutes)
                    notification.send_at = retry_time
                    
                    priority = 5 - notification.priority.value
                    queue_item = (priority, retry_time, notification)
                    self.notification_queue.put(queue_item)
                    
                    logger.info(f"Retry programmé pour la notification {notification.id}")
                else:
                    notification.status = NotificationStatus.FAILED
            
            # Sauvegarde en historique
            self._save_notification_history(notification)
            
            # Mise à jour des métriques de temps
            processing_time = (datetime.now() - start_time).total_seconds()
            self.metrics['total_processing_time'] += processing_time
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification {notification.id}: {e}")
            notification.status = NotificationStatus.FAILED
            notification.last_error = str(e)
            self._save_notification_history(notification)
            return False
    
    def _send_email(self, notification: Notification) -> bool:
        """Envoie un email"""
        try:
            # Configuration SMTP
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            
            if self.config.smtp_use_tls:
                server.starttls()
            
            if self.config.smtp_username and self.config.smtp_password:
                server.login(self.config.smtp_username, self.config.smtp_password)
            
            # Création du message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = ', '.join(notification.recipients)
            
            if notification.cc_recipients:
                msg['Cc'] = ', '.join(notification.cc_recipients)
            
            msg['Subject'] = notification.subject
            
            # Corps du message
            if notification.body:
                text_part = MIMEText(notification.body, 'plain', 'utf-8')
                msg.attach(text_part)
            
            if notification.html_body:
                html_part = MIMEText(notification.html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Pièces jointes
            for attachment_path in notification.attachments:
                if Path(attachment_path).exists():
                    with open(attachment_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {Path(attachment_path).name}'
                    )
                    msg.attach(part)
            
            # Envoi
            all_recipients = notification.recipients + notification.cc_recipients + notification.bcc_recipients
            server.send_message(msg, to_addrs=all_recipients)
            server.quit()
            
            logger.info(f"Email envoyé à {len(notification.recipients)} destinataires")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email: {e}")
            notification.last_error = str(e)
            return False
    
    def _send_sms(self, notification: Notification) -> bool:
        """Envoie un SMS"""
        try:
            if self.config.sms_provider == "twilio":
                return self._send_sms_twilio(notification)
            elif self.config.sms_provider == "ovh":
                return self._send_sms_ovh(notification)
            else:
                logger.error(f"Fournisseur SMS non supporté: {self.config.sms_provider}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du SMS: {e}")
            notification.last_error = str(e)
            return False
    
    def _send_sms_twilio(self, notification: Notification) -> bool:
        """Envoie un SMS via Twilio"""
        try:
            from twilio.rest import Client
            
            client = Client(self.config.sms_api_key, self.config.sms_api_secret)
            
            for recipient in notification.recipients:
                message = client.messages.create(
                    body=notification.body,
                    from_=self.config.sms_sender,
                    to=recipient
                )
                logger.debug(f"SMS Twilio envoyé: {message.sid}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur Twilio: {e}")
            return False
    
    def _send_sms_ovh(self, notification: Notification) -> bool:
        """Envoie un SMS via OVH"""
        try:
            import ovh
            
            client = ovh.Client(
                endpoint='ovh-eu',
                application_key=self.config.sms_api_key,
                application_secret=self.config.sms_api_secret
            )
            
            for recipient in notification.recipients:
                result = client.post('/sms/{}/jobs'.format(self.config.sms_sender), 
                    message=notification.body,
                    receivers=[recipient]
                )
                logger.debug(f"SMS OVH envoyé: {result}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur OVH: {e}")
            return False
    
    def _send_webhook(self, notification: Notification) -> bool:
        """Envoie un webhook"""
        try:
            # Les destinataires sont des URLs pour les webhooks
            for webhook_url in notification.recipients:
                payload = {
                    'notification_id': notification.id,
                    'subject': notification.subject,
                    'body': notification.body,
                    'context_data': notification.context_data,
                    'tags': notification.tags,
                    'timestamp': datetime.now().isoformat()
                }
                
                response = requests.post(
                    webhook_url,
                    json=payload,
                    timeout=self.config.webhook_timeout,
                    headers={'Content-Type': 'application/json'}
                )
                
                response.raise_for_status()
                logger.debug(f"Webhook envoyé à {webhook_url}: {response.status_code}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du webhook: {e}")
            notification.last_error = str(e)
            return False
    
    def _send_slack(self, notification: Notification) -> bool:
        """Envoie une notification Slack"""
        try:
            # Implementation pour Slack
            # TODO: Implémenter selon les besoins
            logger.warning("Envoi Slack non encore implémenté")
            return False
            
        except Exception as e:
            logger.error(f"Erreur Slack: {e}")
            return False
    
    def _send_teams(self, notification: Notification) -> bool:
        """Envoie une notification Microsoft Teams"""
        try:
            # Implementation pour Teams
            # TODO: Implémenter selon les besoins
            logger.warning("Envoi Teams non encore implémenté")
            return False
            
        except Exception as e:
            logger.error(f"Erreur Teams: {e}")
            return False
    
    def _create_notification_from_data(self, data: Dict[str, Any]) -> Notification:
        """Crée un objet Notification depuis des données"""
        notification = Notification()
        
        # Mapping des champs
        if 'channel' in data:
            notification.channel = NotificationChannel(data['channel'])
        
        if 'priority' in data:
            if isinstance(data['priority'], str):
                priority_map = {
                    'low': NotificationPriority.LOW,
                    'normal': NotificationPriority.NORMAL,
                    'high': NotificationPriority.HIGH,
                    'critical': NotificationPriority.CRITICAL
                }
                notification.priority = priority_map.get(data['priority'], NotificationPriority.NORMAL)
            else:
                notification.priority = NotificationPriority(data['priority'])
        
        # Champs directs
        for field in ['recipients', 'cc_recipients', 'bcc_recipients', 'subject', 
                     'body', 'html_body', 'attachments', 'template_id', 
                     'context_data', 'tags']:
            if field in data:
                setattr(notification, field, data[field])
        
        # Planification
        if 'send_at' in data:
            if isinstance(data['send_at'], str):
                notification.send_at = datetime.fromisoformat(data['send_at'])
            else:
                notification.send_at = data['send_at']
        
        return notification
    
    def _render_template(self, template_text: str, context: Dict[str, Any]) -> str:
        """Rend un template avec les données du contexte"""
        if not template_text:
            return ""
        
        rendered = template_text
        
        # Remplacement simple des variables {{variable}}
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, str(value))
        
        return rendered
    
    def _get_template(self, name: str) -> Optional[NotificationTemplate]:
        """Récupère un template par nom"""
        if name in self.templates_cache:
            return self.templates_cache[name]
        
        # Recherche en base
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM notification_templates 
                WHERE name = ? AND is_active = 1
            """, (name,))
            
            row = cursor.fetchone()
            if row:
                template = NotificationTemplate(
                    id=row['id'],
                    name=row['name'],
                    channel=NotificationChannel(row['channel']),
                    subject=row['subject'],
                    body=row['body'],
                    html_body=row['html_body'],
                    variables=json.loads(row['variables']) if row['variables'] else [],
                    channel_config=json.loads(row['channel_config']) if row['channel_config'] else {},
                    is_active=bool(row['is_active']),
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
                )
                
                self.templates_cache[name] = template
                return template
        
        return None
    
    def _load_templates(self):
        """Charge tous les templates en cache"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notification_templates WHERE is_active = 1")
            
            for row in cursor.fetchall():
                template = NotificationTemplate(
                    id=row['id'],
                    name=row['name'],
                    channel=NotificationChannel(row['channel']),
                    subject=row['subject'],
                    body=row['body'],
                    html_body=row['html_body'],
                    variables=json.loads(row['variables']) if row['variables'] else [],
                    channel_config=json.loads(row['channel_config']) if row['channel_config'] else {},
                    is_active=bool(row['is_active']),
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
                )
                
                self.templates_cache[template.name] = template
    
    def _check_user_preferences(self, notification: Notification) -> bool:
        """Vérifie les préférences utilisateur pour une notification"""
        # TODO: Implémenter la vérification des préférences
        # Pour l'instant, autoriser toutes les notifications
        return True
    
    def _check_rate_limit(self) -> bool:
        """Vérifie le limiteur de débit"""
        now = datetime.now()
        
        # Reset du compteur chaque minute
        if (now - self.rate_limiter['last_reset']).total_seconds() >= 60:
            self.rate_limiter['count'] = 0
            self.rate_limiter['last_reset'] = now
        
        # Vérification de la limite
        if self.rate_limiter['count'] >= self.config.rate_limit_per_minute:
            return False
        
        self.rate_limiter['count'] += 1
        return True
    
    def _update_channel_metrics(self, channel: NotificationChannel):
        """Met à jour les métriques par canal"""
        if channel == NotificationChannel.EMAIL:
            self.metrics['emails_sent'] += 1
        elif channel == NotificationChannel.SMS:
            self.metrics['sms_sent'] += 1
        elif channel == NotificationChannel.WEBHOOK:
            self.metrics['webhooks_sent'] += 1
    
    def _save_notification_history(self, notification: Notification):
        """Sauvegarde l'historique d'une notification"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO notification_history (
                        id, channel, priority, recipients, subject, body,
                        template_id, status, retry_count, last_error, sent_at,
                        context_data, tags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    notification.id, notification.channel.value, notification.priority.value,
                    json.dumps(notification.recipients), notification.subject, notification.body,
                    notification.template_id, notification.status.value, notification.retry_count,
                    notification.last_error, 
                    notification.sent_at.isoformat() if notification.sent_at else None,
                    json.dumps(notification.context_data), json.dumps(notification.tags)
                ))
                
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'historique: {e}")
    
    def _get_participant(self, participant_id: int) -> Optional[Dict[str, Any]]:
        """Récupère les données d'un participant"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM participants WHERE id = ?", (participant_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def _load_config(self) -> NotificationConfig:
        """Charge la configuration depuis la base de données"""
        config = NotificationConfig()
        
        # Chargement des paramètres depuis la table settings
        settings_map = {
            'smtp_server': 'smtp_server',
            'smtp_port': 'smtp_port',
            'smtp_username': 'smtp_username',
            'smtp_password': 'smtp_password',
            'smtp_use_tls': 'smtp_use_tls',
            'from_email': 'from_email',
            'from_name': 'from_name',
            'sms_provider': 'sms_provider',
            'sms_api_key': 'sms_api_key',
            'sms_api_secret': 'sms_api_secret',
            'sms_sender': 'sms_sender'
        }
        
        for setting_key, config_attr in settings_map.items():
            value = self.db.get_setting(setting_key)
            if value:
                # Conversion de type si nécessaire
                if config_attr in ['smtp_port', 'webhook_timeout', 'webhook_retries', 
                                 'max_retry_attempts', 'retry_delay_minutes', 
                                 'batch_size', 'rate_limit_per_minute']:
                    value = int(value)
                elif config_attr in ['smtp_use_tls']:
                    value = value.lower() in ['true', '1', 'yes']
                
                setattr(config, config_attr, value)
        
        return config
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Met à jour la configuration"""
        try:
            for key, value in new_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    # Sauvegarde en base
                    self.db.set_setting(key, str(value))
            
            logger.info("Configuration des notifications mise à jour")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la configuration: {e}")
            return False
    
    def get_notification_history(self, limit: int = 100, 
                               channel: str = None,
                               status: str = None) -> List[Dict[str, Any]]:
        """Récupère l'historique des notifications"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM notification_history WHERE 1=1"
            params = []
            
            if channel:
                query += " AND channel = ?"
                params.append(channel)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du gestionnaire"""
        return {
            'is_running': self.is_running,
            'queue_size': self.notification_queue.qsize(),
            'templates_loaded': len(self.templates_cache),
            'rate_limit_count': self.rate_limiter['count'],
            'rate_limit_reset': self.rate_limiter['last_reset'].isoformat(),
            'metrics': self.metrics.copy()
        }