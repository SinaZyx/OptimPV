"""
Module d'automatisation pour le système de facturation OptimPV
Orchestre tous les processus automatiques et workflows
"""

import logging
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Callable
import json
from enum import Enum
from dataclasses import dataclass, asdict
import threading
import queue
import time
from pathlib import Path

from .database import BillingDatabase
from .recurring_billing import RecurringBillingManager
from .workflow import WorkflowManager
from .scheduler import TaskScheduler
from .notifications import NotificationManager

logger = logging.getLogger(__name__)

class AutomationStatus(Enum):
    """États de l'automatisation"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"

@dataclass
class AutomationConfig:
    """Configuration de l'automatisation"""
    auto_generate_recurring: bool = True
    auto_validate_invoices: bool = False
    auto_send_notifications: bool = True
    auto_dunning_enabled: bool = True
    max_retry_attempts: int = 3
    error_notification_recipients: List[str] = None
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    
    def __post_init__(self):
        if self.error_notification_recipients is None:
            self.error_notification_recipients = []

class AutomationEngine:
    """
    Moteur d'automatisation principal pour le système de facturation
    Orchestre tous les processus automatiques et workflows
    """
    
    def __init__(self, db: BillingDatabase, config: AutomationConfig = None):
        """
        Initialise le moteur d'automatisation
        
        Args:
            db: Instance de base de données
            config: Configuration de l'automatisation
        """
        self.db = db
        self.config = config or AutomationConfig()
        self.status = AutomationStatus.STOPPED
        
        # Initialisation des gestionnaires
        self.recurring_manager = RecurringBillingManager(db)
        self.workflow_manager = WorkflowManager(db)
        self.scheduler = TaskScheduler(db)
        self.notification_manager = NotificationManager(db)
        
        # File d'événements pour communication inter-modules
        self.event_queue = queue.Queue()
        self.worker_thread = None
        self.stop_event = threading.Event()
        
        # Métriques d'automatisation
        self.metrics = {
            'tasks_executed': 0,
            'tasks_failed': 0,
            'last_execution': None,
            'errors': []
        }
        
        # Enregistrement des handlers d'événements
        self._setup_event_handlers()
        
        logger.info("AutomationEngine initialisé")
    
    def _setup_event_handlers(self):
        """Configuration des gestionnaires d'événements"""
        # Événements de facturation récurrente
        self.recurring_manager.on_invoice_generated = self._on_invoice_generated
        self.recurring_manager.on_generation_failed = self._on_generation_failed
        
        # Événements de workflow
        self.workflow_manager.on_state_changed = self._on_workflow_state_changed
        self.workflow_manager.on_validation_required = self._on_validation_required
        
        # Événements de planificateur
        self.scheduler.on_task_completed = self._on_task_completed
        self.scheduler.on_task_failed = self._on_task_failed
    
    def start(self) -> bool:
        """
        Démarre le moteur d'automatisation
        
        Returns:
            bool: True si démarré avec succès
        """
        try:
            if self.status == AutomationStatus.RUNNING:
                logger.warning("AutomationEngine déjà en cours d'exécution")
                return True
            
            self.status = AutomationStatus.RUNNING
            self.stop_event.clear()
            
            # Démarrage du thread de traitement des événements
            self.worker_thread = threading.Thread(target=self._event_worker, daemon=True)
            self.worker_thread.start()
            
            # Démarrage des sous-modules
            self.scheduler.start()
            self.notification_manager.start()
            
            # Planification des tâches automatiques
            self._schedule_automated_tasks()
            
            logger.info("AutomationEngine démarré")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de l'AutomationEngine: {e}")
            self.status = AutomationStatus.ERROR
            return False
    
    def stop(self) -> bool:
        """
        Arrête le moteur d'automatisation
        
        Returns:
            bool: True si arrêté avec succès
        """
        try:
            self.status = AutomationStatus.STOPPED
            self.stop_event.set()
            
            # Arrêt des sous-modules
            self.scheduler.stop()
            self.notification_manager.stop()
            
            # Attente de l'arrêt du thread
            if self.worker_thread and self.worker_thread.is_alive():
                self.worker_thread.join(timeout=5)
            
            logger.info("AutomationEngine arrêté")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt de l'AutomationEngine: {e}")
            return False
    
    def pause(self) -> bool:
        """Met en pause l'automatisation"""
        if self.status == AutomationStatus.RUNNING:
            self.status = AutomationStatus.PAUSED
            self.scheduler.pause()
            logger.info("AutomationEngine mis en pause")
            return True
        return False
    
    def resume(self) -> bool:
        """Reprend l'automatisation"""
        if self.status == AutomationStatus.PAUSED:
            self.status = AutomationStatus.RUNNING
            self.scheduler.resume()
            logger.info("AutomationEngine repris")
            return True
        return False
    
    def _schedule_automated_tasks(self):
        """Planifie les tâches automatiques récurrentes"""
        
        # Génération de factures récurrentes (quotidien à 09:00)
        if self.config.auto_generate_recurring:
            self.scheduler.schedule_daily(
                "generate_recurring_invoices",
                hour=9,
                minute=0,
                callback=self._generate_recurring_invoices
            )
        
        # Traitement des relances (quotidien à 10:00)
        if self.config.auto_dunning_enabled:
            self.scheduler.schedule_daily(
                "process_dunning",
                hour=10,
                minute=0,
                callback=self._process_dunning
            )
        
        # Validation automatique des factures (toutes les heures)
        if self.config.auto_validate_invoices:
            self.scheduler.schedule_hourly(
                "auto_validate_invoices",
                minute=0,
                callback=self._auto_validate_invoices
            )
        
        # Nettoyage des données temporaires (hebdomadaire)
        self.scheduler.schedule_weekly(
            "cleanup_temp_data",
            day_of_week=0,  # Lundi
            hour=2,
            minute=0,
            callback=self._cleanup_temp_data
        )
        
        # Sauvegarde automatique
        if self.config.backup_enabled:
            self.scheduler.schedule_interval(
                "auto_backup",
                interval_hours=self.config.backup_interval_hours,
                callback=self._auto_backup
            )
    
    def _event_worker(self):
        """Thread de traitement des événements"""
        while not self.stop_event.is_set():
            try:
                if self.status != AutomationStatus.RUNNING:
                    time.sleep(1)
                    continue
                
                # Traitement des événements en attente
                try:
                    event = self.event_queue.get(timeout=1)
                    self._process_event(event)
                    self.event_queue.task_done()
                except queue.Empty:
                    continue
                    
            except Exception as e:
                logger.error(f"Erreur dans le worker d'événements: {e}")
                self._record_error(e)
    
    def _process_event(self, event: Dict[str, Any]):
        """
        Traite un événement
        
        Args:
            event: Dictionnaire contenant les détails de l'événement
        """
        event_type = event.get('type')
        data = event.get('data', {})
        
        logger.debug(f"Traitement de l'événement: {event_type}")
        
        try:
            if event_type == 'invoice_generated':
                self._handle_invoice_generated(data)
            elif event_type == 'invoice_validation_required':
                self._handle_validation_required(data)
            elif event_type == 'payment_received':
                self._handle_payment_received(data)
            elif event_type == 'workflow_state_changed':
                self._handle_workflow_state_changed(data)
            else:
                logger.warning(f"Type d'événement non reconnu: {event_type}")
            
            self.metrics['tasks_executed'] += 1
            self.metrics['last_execution'] = datetime.now()
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'événement {event_type}: {e}")
            self.metrics['tasks_failed'] += 1
            self._record_error(e)
    
    def _generate_recurring_invoices(self):
        """Génère les factures récurrentes"""
        try:
            logger.info("Génération des factures récurrentes")
            result = self.recurring_manager.generate_due_invoices()
            
            if result['success']:
                logger.info(f"Factures générées: {result['generated_count']}")
                
                # Notification du succès
                if self.config.auto_send_notifications:
                    self.notification_manager.send_notification({
                        'type': 'recurring_generation_success',
                        'title': 'Factures récurrentes générées',
                        'message': f"{result['generated_count']} factures ont été générées automatiquement",
                        'data': result
                    })
            else:
                logger.error(f"Échec de génération: {result.get('error', 'Erreur inconnue')}")
                self._send_error_notification("Échec de génération des factures récurrentes", result)
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération des factures récurrentes: {e}")
            self._record_error(e)
    
    def _process_dunning(self):
        """Traite les relances automatiques"""
        try:
            logger.info("Traitement des relances automatiques")
            
            # Récupération des factures en retard
            overdue_invoices = self._get_overdue_invoices()
            
            for invoice in overdue_invoices:
                self._process_invoice_dunning(invoice)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement des relances: {e}")
            self._record_error(e)
    
    def _auto_validate_invoices(self):
        """Validation automatique des factures selon critères"""
        try:
            logger.info("Validation automatique des factures")
            
            # Récupération des factures en brouillon
            draft_invoices = self._get_draft_invoices()
            
            for invoice in draft_invoices:
                if self._can_auto_validate(invoice):
                    self.workflow_manager.transition_invoice(
                        invoice['id'], 
                        'validate', 
                        auto_validated=True
                    )
                    
        except Exception as e:
            logger.error(f"Erreur lors de la validation automatique: {e}")
            self._record_error(e)
    
    def _cleanup_temp_data(self):
        """Nettoyage des données temporaires"""
        try:
            logger.info("Nettoyage des données temporaires")
            
            cutoff_date = datetime.now() - timedelta(days=30)
            
            # Suppression des logs anciens
            self._cleanup_old_logs(cutoff_date)
            
            # Nettoyage des fichiers temporaires
            self._cleanup_temp_files()
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {e}")
            self._record_error(e)
    
    def _auto_backup(self):
        """Sauvegarde automatique"""
        try:
            logger.info("Sauvegarde automatique")
            
            backup_path = self._create_backup()
            
            if backup_path:
                logger.info(f"Sauvegarde créée: {backup_path}")
                
                # Notification de succès
                self.notification_manager.send_notification({
                    'type': 'backup_success',
                    'title': 'Sauvegarde réussie',
                    'message': f"Sauvegarde créée: {backup_path}",
                    'data': {'backup_path': backup_path}
                })
            else:
                raise Exception("Échec de création de la sauvegarde")
                
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            self._send_error_notification("Échec de sauvegarde automatique", str(e))
            self._record_error(e)
    
    # Gestionnaires d'événements
    def _on_invoice_generated(self, invoice_data: Dict[str, Any]):
        """Gestionnaire pour facture générée"""
        self.event_queue.put({
            'type': 'invoice_generated',
            'data': invoice_data
        })
    
    def _on_generation_failed(self, error_data: Dict[str, Any]):
        """Gestionnaire pour échec de génération"""
        self.event_queue.put({
            'type': 'generation_failed',
            'data': error_data
        })
    
    def _on_workflow_state_changed(self, workflow_data: Dict[str, Any]):
        """Gestionnaire pour changement d'état de workflow"""
        self.event_queue.put({
            'type': 'workflow_state_changed',
            'data': workflow_data
        })
    
    def _on_validation_required(self, validation_data: Dict[str, Any]):
        """Gestionnaire pour validation requise"""
        self.event_queue.put({
            'type': 'invoice_validation_required',
            'data': validation_data
        })
    
    def _on_task_completed(self, task_name: str, result: Any):
        """Gestionnaire pour tâche terminée"""
        logger.debug(f"Tâche terminée: {task_name}")
    
    def _on_task_failed(self, task_name: str, error: Exception):
        """Gestionnaire pour tâche échouée"""
        logger.error(f"Tâche échouée: {task_name} - {error}")
        self._record_error(error)
    
    # Gestionnaires d'événements spécifiques
    def _handle_invoice_generated(self, data: Dict[str, Any]):
        """Gère la génération d'une facture"""
        invoice_id = data.get('invoice_id')
        
        if invoice_id and self.config.auto_validate_invoices:
            # Tentative de validation automatique
            invoice = self.db.get_invoice(invoice_id)
            if invoice and self._can_auto_validate(invoice):
                self.workflow_manager.transition_invoice(invoice_id, 'validate')
    
    def _handle_validation_required(self, data: Dict[str, Any]):
        """Gère une demande de validation"""
        invoice_id = data.get('invoice_id')
        
        # Notification aux gestionnaires
        if self.config.auto_send_notifications:
            self.notification_manager.send_notification({
                'type': 'validation_required',
                'title': 'Validation requise',
                'message': f"La facture {invoice_id} nécessite une validation manuelle",
                'data': data
            })
    
    def _handle_payment_received(self, data: Dict[str, Any]):
        """Gère la réception d'un paiement"""
        invoice_id = data.get('invoice_id')
        
        # Mise à jour automatique du statut
        if invoice_id:
            self.workflow_manager.transition_invoice(invoice_id, 'mark_paid')
    
    def _handle_workflow_state_changed(self, data: Dict[str, Any]):
        """Gère un changement d'état de workflow"""
        old_state = data.get('old_state')
        new_state = data.get('new_state')
        invoice_id = data.get('invoice_id')
        
        # Actions spécifiques selon la transition
        if new_state == 'validated' and self.config.auto_send_notifications:
            # Envoi automatique de la facture
            self._auto_send_invoice(invoice_id)
    
    # Méthodes utilitaires
    def _get_overdue_invoices(self) -> List[Dict[str, Any]]:
        """Récupère les factures en retard"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.*, p.name as participant_name, p.contact_email
                FROM invoices i
                JOIN participants p ON i.participant_id = p.id
                WHERE i.status = 'sent' 
                AND i.due_date < date('now')
                ORDER BY i.due_date
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def _get_draft_invoices(self) -> List[Dict[str, Any]]:
        """Récupère les factures en brouillon"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM invoices 
                WHERE status = 'draft'
                ORDER BY created_at
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def _can_auto_validate(self, invoice: Dict[str, Any]) -> bool:
        """
        Détermine si une facture peut être validée automatiquement
        
        Args:
            invoice: Données de la facture
            
        Returns:
            bool: True si validation automatique possible
        """
        # Critères de validation automatique
        return (
            invoice.get('total_amount', 0) > 0 and
            invoice.get('total_amount', 0) < 10000 and  # Limite de montant
            invoice.get('participant_id') is not None and
            invoice.get('billing_period_id') is not None
        )
    
    def _process_invoice_dunning(self, invoice: Dict[str, Any]):
        """Traite la relance d'une facture"""
        try:
            days_overdue = (datetime.now().date() - 
                          datetime.strptime(invoice['due_date'], '%Y-%m-%d').date()).days
            
            # Détermination du niveau de relance
            if days_overdue >= 60:
                level = 'legal_action'
            elif days_overdue >= 45:
                level = 'final_notice'
            elif days_overdue >= 30:
                level = 'second_notice'
            elif days_overdue >= 15:
                level = 'first_notice'
            elif days_overdue >= 7:
                level = 'friendly_reminder'
            else:
                return  # Pas encore temps pour relance
            
            # Vérification si cette relance a déjà été envoyée
            if not self._is_dunning_due(invoice['id'], level):
                return
            
            # Envoi de la relance
            self._send_dunning_notice(invoice, level)
            
        except Exception as e:
            logger.error(f"Erreur lors de la relance de la facture {invoice['id']}: {e}")
    
    def _is_dunning_due(self, invoice_id: int, level: str) -> bool:
        """Vérifie si une relance est due"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM dunning_actions 
                WHERE invoice_id = ? AND level = ?
            """, (invoice_id, level))
            return cursor.fetchone()[0] == 0
    
    def _send_dunning_notice(self, invoice: Dict[str, Any], level: str):
        """Envoie une relance"""
        try:
            # Enregistrement de l'action de relance
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO dunning_actions (
                        invoice_id, level, action_date, due_amount, 
                        email_address, template_used
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    invoice['id'], level, date.today().isoformat(),
                    invoice['total_amount'], invoice.get('contact_email'),
                    level
                ))
            
            # Envoi de la notification
            if invoice.get('contact_email') and self.config.auto_send_notifications:
                self.notification_manager.send_dunning_email(invoice, level)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la relance: {e}")
    
    def _auto_send_invoice(self, invoice_id: int):
        """Envoi automatique d'une facture"""
        try:
            invoice = self.db.get_invoice(invoice_id)
            if invoice and invoice.get('participant_id'):
                # Récupération des informations du participant
                participant = self._get_participant(invoice['participant_id'])
                
                if participant and participant.get('contact_email'):
                    # Envoi par email
                    self.notification_manager.send_invoice_email(invoice, participant)
                    
                    # Mise à jour du statut
                    self.db.update_invoice_status(invoice_id, 'sent')
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi automatique de la facture {invoice_id}: {e}")
    
    def _get_participant(self, participant_id: int) -> Optional[Dict[str, Any]]:
        """Récupère les données d'un participant"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM participants WHERE id = ?", (participant_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def _cleanup_old_logs(self, cutoff_date: datetime):
        """Supprime les anciens logs"""
        try:
            logs_dir = Path("logs")
            if logs_dir.exists():
                for log_file in logs_dir.glob("*.log"):
                    if log_file.stat().st_mtime < cutoff_date.timestamp():
                        log_file.unlink()
                        logger.debug(f"Log supprimé: {log_file}")
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des logs: {e}")
    
    def _cleanup_temp_files(self):
        """Supprime les fichiers temporaires"""
        try:
            temp_dirs = [Path("temp"), Path("tmp"), Path("cache")]
            
            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    for temp_file in temp_dir.glob("*"):
                        if temp_file.is_file():
                            temp_file.unlink()
                            logger.debug(f"Fichier temporaire supprimé: {temp_file}")
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des fichiers temporaires: {e}")
    
    def _create_backup(self) -> Optional[str]:
        """Crée une sauvegarde de la base de données"""
        try:
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"billing_backup_{timestamp}.db"
            
            # Copie de la base de données
            import shutil
            shutil.copy2(self.db.db_path, backup_path)
            
            # Compression optionnelle
            import gzip
            with open(backup_path, 'rb') as f_in:
                with gzip.open(f"{backup_path}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            backup_path.unlink()  # Suppression du fichier non compressé
            
            return str(f"{backup_path}.gz")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la sauvegarde: {e}")
            return None
    
    def _record_error(self, error: Exception):
        """Enregistre une erreur"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error': str(error),
            'type': type(error).__name__
        }
        
        self.metrics['errors'].append(error_info)
        
        # Limite le nombre d'erreurs stockées
        if len(self.metrics['errors']) > 100:
            self.metrics['errors'] = self.metrics['errors'][-50:]
    
    def _send_error_notification(self, title: str, details: Any):
        """Envoie une notification d'erreur"""
        if self.config.error_notification_recipients:
            self.notification_manager.send_notification({
                'type': 'error',
                'title': title,
                'message': f"Erreur dans l'automatisation: {details}",
                'recipients': self.config.error_notification_recipients,
                'priority': 'high'
            })
    
    # API publique pour contrôle externe
    def trigger_recurring_generation(self) -> Dict[str, Any]:
        """Déclenche manuellement la génération des factures récurrentes"""
        try:
            result = self.recurring_manager.generate_due_invoices()
            logger.info(f"Génération manuelle déclenchée: {result}")
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la génération manuelle: {e}")
            return {'success': False, 'error': str(e)}
    
    def trigger_dunning_process(self) -> Dict[str, Any]:
        """Déclenche manuellement le processus de relance"""
        try:
            self._process_dunning()
            return {'success': True, 'message': 'Processus de relance exécuté'}
        except Exception as e:
            logger.error(f"Erreur lors du processus de relance manuel: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_automation_status(self) -> Dict[str, Any]:
        """Retourne le statut de l'automatisation"""
        return {
            'status': self.status.value,
            'config': asdict(self.config),
            'metrics': self.metrics.copy(),
            'sub_modules': {
                'scheduler': self.scheduler.get_status(),
                'notifications': self.notification_manager.get_status(),
                'recurring': self.recurring_manager.get_status(),
                'workflow': self.workflow_manager.get_status()
            }
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Met à jour la configuration"""
        try:
            for key, value in new_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            # Sauvegarde de la configuration
            self._save_config()
            
            logger.info("Configuration de l'automatisation mise à jour")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la configuration: {e}")
            return False
    
    def _save_config(self):
        """Sauvegarde la configuration"""
        config_data = asdict(self.config)
        self.db.set_setting('automation_config', json.dumps(config_data))
    
    def _load_config(self) -> AutomationConfig:
        """Charge la configuration sauvegardée"""
        try:
            config_json = self.db.get_setting('automation_config')
            if config_json:
                config_data = json.loads(config_json)
                return AutomationConfig(**config_data)
        except Exception as e:
            logger.warning(f"Erreur lors du chargement de la configuration: {e}")
        
        return AutomationConfig()
    
    def __enter__(self):
        """Gestionnaire de contexte - entrée"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Gestionnaire de contexte - sortie"""
        self.stop()

# Fonctions utilitaires
def create_automation_engine(db_path: str = "data/billing.db", 
                           config: AutomationConfig = None) -> AutomationEngine:
    """
    Crée une instance d'AutomationEngine
    
    Args:
        db_path: Chemin vers la base de données
        config: Configuration de l'automatisation
        
    Returns:
        AutomationEngine: Instance configurée
    """
    db = BillingDatabase(db_path)
    return AutomationEngine(db, config)

def get_default_automation_config() -> AutomationConfig:
    """Retourne une configuration par défaut pour l'automatisation"""
    return AutomationConfig(
        auto_generate_recurring=True,
        auto_validate_invoices=False,
        auto_send_notifications=True,
        auto_dunning_enabled=True,
        max_retry_attempts=3,
        error_notification_recipients=['admin@optimpv.fr'],
        backup_enabled=True,
        backup_interval_hours=24
    )