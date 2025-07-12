"""
Module de planification de tâches pour le système de facturation
Planificateur CRON-like pour exécution de tâches en arrière-plan
"""

import logging
import threading
import time
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
from dataclasses import dataclass, asdict
import json
import re
from pathlib import Path
import queue
import uuid

from .database import BillingDatabase

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """États des tâches"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"

class TaskPriority(Enum):
    """Priorités des tâches"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class CronExpression:
    """Expression CRON pour planification"""
    minute: str = "*"  # 0-59
    hour: str = "*"    # 0-23
    day: str = "*"     # 1-31
    month: str = "*"   # 1-12
    weekday: str = "*" # 0-7 (0 et 7 = dimanche)
    
    def __str__(self):
        return f"{self.minute} {self.hour} {self.day} {self.month} {self.weekday}"
    
    @classmethod
    def from_string(cls, cron_string: str) -> 'CronExpression':
        """Crée une expression CRON depuis une chaîne"""
        parts = cron_string.strip().split()
        if len(parts) != 5:
            raise ValueError(f"Expression CRON invalide: {cron_string}")
        
        return cls(
            minute=parts[0],
            hour=parts[1], 
            day=parts[2],
            month=parts[3],
            weekday=parts[4]
        )

@dataclass
class ScheduledTask:
    """Tâche planifiée"""
    id: Optional[str] = None
    name: str = ""
    description: str = ""
    
    # Planification
    cron_expression: Optional[CronExpression] = None
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    
    # Exécution
    callback: Optional[Callable] = None
    callback_args: tuple = ()
    callback_kwargs: Dict[str, Any] = None
    
    # Configuration
    max_retries: int = 3
    retry_delay_seconds: int = 60
    timeout_seconds: int = 300
    priority: TaskPriority = TaskPriority.NORMAL
    
    # État
    status: TaskStatus = TaskStatus.SCHEDULED
    retry_count: int = 0
    last_error: Optional[str] = None
    execution_time: Optional[float] = None
    
    # Métadonnées
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_enabled: bool = True
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.callback_kwargs is None:
            self.callback_kwargs = {}
        if self.created_at is None:
            self.created_at = datetime.now()

class TaskScheduler:
    """
    Planificateur de tâches avec support CRON-like
    Gère l'exécution de tâches récurrentes et ponctuelles
    """
    
    def __init__(self, db: BillingDatabase):
        """
        Initialise le planificateur
        
        Args:
            db: Instance de base de données
        """
        self.db = db
        self._ensure_tables()
        
        # État du planificateur
        self.is_running = False
        self.is_paused = False
        
        # Threads et queues
        self.scheduler_thread: Optional[threading.Thread] = None
        self.worker_threads: List[threading.Thread] = []
        self.task_queue = queue.PriorityQueue()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        
        # Configuration
        self.max_workers = 5
        self.check_interval = 60  # secondes
        
        # Cache des tâches
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        
        # Callbacks
        self.on_task_completed: Optional[Callable] = None
        self.on_task_failed: Optional[Callable] = None
        self.on_task_started: Optional[Callable] = None
        
        # Métriques
        self.metrics = {
            'tasks_executed': 0,
            'tasks_failed': 0,
            'total_execution_time': 0.0,
            'average_execution_time': 0.0
        }
        
        # Chargement des tâches persistantes
        self._load_scheduled_tasks()
        
        logger.info("TaskScheduler initialisé")
    
    def _ensure_tables(self):
        """Assure l'existence des tables requises"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Table des tâches planifiées
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    cron_expression TEXT NOT NULL,
                    next_run TIMESTAMP,
                    last_run TIMESTAMP,
                    callback_name TEXT NOT NULL,
                    callback_args TEXT, -- JSON array
                    callback_kwargs TEXT, -- JSON object
                    max_retries INTEGER DEFAULT 3,
                    retry_delay_seconds INTEGER DEFAULT 60,
                    timeout_seconds INTEGER DEFAULT 300,
                    priority INTEGER DEFAULT 2,
                    status TEXT DEFAULT 'scheduled',
                    retry_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    execution_time REAL,
                    is_enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table de l'historique d'exécution
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_execution_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    execution_start TIMESTAMP NOT NULL,
                    execution_end TIMESTAMP,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    execution_time REAL,
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES scheduled_tasks(id)
                )
            """)
            
            # Table des tâches ponctuelles
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS one_time_tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    scheduled_for TIMESTAMP NOT NULL,
                    callback_name TEXT NOT NULL,
                    callback_args TEXT, -- JSON array
                    callback_kwargs TEXT, -- JSON object
                    priority INTEGER DEFAULT 2,
                    status TEXT DEFAULT 'pending',
                    last_error TEXT,
                    execution_time REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed_at TIMESTAMP
                )
            """)
            
            # Index pour optimisation
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_next_run ON scheduled_tasks(next_run)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_status ON scheduled_tasks(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_one_time_tasks_scheduled ON one_time_tasks(scheduled_for)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_history_task_id ON task_execution_history(task_id)")
    
    def start(self) -> bool:
        """
        Démarre le planificateur
        
        Returns:
            bool: True si démarré avec succès
        """
        try:
            if self.is_running:
                logger.warning("TaskScheduler déjà en cours d'exécution")
                return True
            
            self.is_running = True
            self.stop_event.clear()
            self.pause_event.clear()
            
            # Démarrage du thread principal du planificateur
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            
            # Démarrage des threads workers
            for i in range(self.max_workers):
                worker = threading.Thread(target=self._worker_loop, daemon=True, name=f"TaskWorker-{i}")
                worker.start()
                self.worker_threads.append(worker)
            
            logger.info(f"TaskScheduler démarré avec {self.max_workers} workers")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du TaskScheduler: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Arrête le planificateur
        
        Returns:
            bool: True si arrêté avec succès
        """
        try:
            self.is_running = False
            self.stop_event.set()
            
            # Attente de l'arrêt du scheduler principal
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            
            # Attente de l'arrêt des workers
            for worker in self.worker_threads:
                if worker.is_alive():
                    worker.join(timeout=2)
            
            self.worker_threads.clear()
            
            # Sauvegarde des tâches
            self._save_scheduled_tasks()
            
            logger.info("TaskScheduler arrêté")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt du TaskScheduler: {e}")
            return False
    
    def pause(self) -> bool:
        """Met en pause le planificateur"""
        if self.is_running:
            self.is_paused = True
            self.pause_event.set()
            logger.info("TaskScheduler mis en pause")
            return True
        return False
    
    def resume(self) -> bool:
        """Reprend le planificateur"""
        if self.is_running and self.is_paused:
            self.is_paused = False
            self.pause_event.clear()
            logger.info("TaskScheduler repris")
            return True
        return False
    
    def schedule_task(self, task: ScheduledTask) -> bool:
        """
        Planifie une tâche récurrente
        
        Args:
            task: Tâche à planifier
            
        Returns:
            bool: True si planifiée avec succès
        """
        try:
            # Calcul de la prochaine exécution
            if task.cron_expression:
                task.next_run = self._calculate_next_run(task.cron_expression)
            
            # Ajout au cache
            self.scheduled_tasks[task.id] = task
            
            # Persistance en base
            self._save_task_to_db(task)
            
            logger.info(f"Tâche planifiée: {task.name} (prochaine exécution: {task.next_run})")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la planification de la tâche {task.name}: {e}")
            return False
    
    def schedule_daily(self, name: str, hour: int = 0, minute: int = 0,
                      callback: Callable = None, **kwargs) -> str:
        """
        Planifie une tâche quotidienne
        
        Args:
            name: Nom de la tâche
            hour: Heure d'exécution (0-23)
            minute: Minute d'exécution (0-59)
            callback: Fonction à exécuter
            **kwargs: Arguments pour la fonction
            
        Returns:
            str: ID de la tâche créée
        """
        cron_expr = CronExpression(minute=str(minute), hour=str(hour))
        task = ScheduledTask(
            name=name,
            description=f"Tâche quotidienne à {hour:02d}:{minute:02d}",
            cron_expression=cron_expr,
            callback=callback,
            callback_kwargs=kwargs
        )
        
        if self.schedule_task(task):
            return task.id
        return None
    
    def schedule_weekly(self, name: str, day_of_week: int, hour: int = 0, minute: int = 0,
                       callback: Callable = None, **kwargs) -> str:
        """
        Planifie une tâche hebdomadaire
        
        Args:
            name: Nom de la tâche
            day_of_week: Jour de la semaine (0=dimanche, 1=lundi, ..., 6=samedi)
            hour: Heure d'exécution
            minute: Minute d'exécution
            callback: Fonction à exécuter
            **kwargs: Arguments pour la fonction
            
        Returns:
            str: ID de la tâche créée
        """
        cron_expr = CronExpression(
            minute=str(minute), 
            hour=str(hour), 
            weekday=str(day_of_week)
        )
        task = ScheduledTask(
            name=name,
            description=f"Tâche hebdomadaire le jour {day_of_week} à {hour:02d}:{minute:02d}",
            cron_expression=cron_expr,
            callback=callback,
            callback_kwargs=kwargs
        )
        
        if self.schedule_task(task):
            return task.id
        return None
    
    def schedule_monthly(self, name: str, day: int, hour: int = 0, minute: int = 0,
                        callback: Callable = None, **kwargs) -> str:
        """
        Planifie une tâche mensuelle
        
        Args:
            name: Nom de la tâche
            day: Jour du mois (1-31)
            hour: Heure d'exécution
            minute: Minute d'exécution
            callback: Fonction à exécuter
            **kwargs: Arguments pour la fonction
            
        Returns:
            str: ID de la tâche créée
        """
        cron_expr = CronExpression(
            minute=str(minute),
            hour=str(hour),
            day=str(day)
        )
        task = ScheduledTask(
            name=name,
            description=f"Tâche mensuelle le {day} à {hour:02d}:{minute:02d}",
            cron_expression=cron_expr,
            callback=callback,
            callback_kwargs=kwargs
        )
        
        if self.schedule_task(task):
            return task.id
        return None
    
    def schedule_hourly(self, name: str, minute: int = 0,
                       callback: Callable = None, **kwargs) -> str:
        """Planifie une tâche toutes les heures"""
        cron_expr = CronExpression(minute=str(minute))
        task = ScheduledTask(
            name=name,
            description=f"Tâche horaire à la minute {minute}",
            cron_expression=cron_expr,
            callback=callback,
            callback_kwargs=kwargs
        )
        
        if self.schedule_task(task):
            return task.id
        return None
    
    def schedule_interval(self, name: str, interval_hours: int,
                         callback: Callable = None, **kwargs) -> str:
        """Planifie une tâche à intervalle régulier (en heures)"""
        # Pour les intervalles, on utilise une approche différente
        # On calcule les heures d'exécution dans la journée
        hours = []
        for h in range(0, 24, interval_hours):
            hours.append(str(h))
        
        cron_expr = CronExpression(minute="0", hour=",".join(hours))
        task = ScheduledTask(
            name=name,
            description=f"Tâche toutes les {interval_hours}h",
            cron_expression=cron_expr,
            callback=callback,
            callback_kwargs=kwargs
        )
        
        if self.schedule_task(task):
            return task.id
        return None
    
    def schedule_cron(self, name: str, cron_expression: str,
                     callback: Callable = None, **kwargs) -> str:
        """
        Planifie une tâche avec expression CRON personnalisée
        
        Args:
            name: Nom de la tâche
            cron_expression: Expression CRON (format: minute hour day month weekday)
            callback: Fonction à exécuter
            **kwargs: Arguments pour la fonction
            
        Returns:
            str: ID de la tâche créée
        """
        try:
            cron_expr = CronExpression.from_string(cron_expression)
            task = ScheduledTask(
                name=name,
                description=f"Tâche CRON: {cron_expression}",
                cron_expression=cron_expr,
                callback=callback,
                callback_kwargs=kwargs
            )
            
            if self.schedule_task(task):
                return task.id
            return None
            
        except Exception as e:
            logger.error(f"Expression CRON invalide {cron_expression}: {e}")
            return None
    
    def schedule_once(self, name: str, run_at: datetime,
                     callback: Callable = None, priority: TaskPriority = TaskPriority.NORMAL,
                     **kwargs) -> str:
        """
        Planifie une tâche ponctuelle
        
        Args:
            name: Nom de la tâche
            run_at: Date et heure d'exécution
            callback: Fonction à exécuter
            priority: Priorité de la tâche
            **kwargs: Arguments pour la fonction
            
        Returns:
            str: ID de la tâche créée
        """
        try:
            task_id = str(uuid.uuid4())
            
            # Persistance en base
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO one_time_tasks (
                        id, name, description, scheduled_for, callback_name,
                        callback_args, callback_kwargs, priority
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_id, name, f"Tâche ponctuelle pour {run_at}",
                    run_at.isoformat(), callback.__name__ if callback else "",
                    json.dumps([]), json.dumps(kwargs), priority.value
                ))
            
            # Si la tâche doit s'exécuter maintenant ou bientôt, l'ajouter à la queue
            if run_at <= datetime.now() + timedelta(minutes=1):
                self._queue_task_for_execution(task_id, callback, priority, **kwargs)
            
            logger.info(f"Tâche ponctuelle planifiée: {name} pour {run_at}")
            return task_id
            
        except Exception as e:
            logger.error(f"Erreur lors de la planification de la tâche ponctuelle {name}: {e}")
            return None
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Annule une tâche planifiée
        
        Args:
            task_id: ID de la tâche à annuler
            
        Returns:
            bool: True si annulée avec succès
        """
        try:
            # Suppression du cache
            if task_id in self.scheduled_tasks:
                del self.scheduled_tasks[task_id]
            
            # Mise à jour en base
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Tâches récurrentes
                cursor.execute("""
                    UPDATE scheduled_tasks 
                    SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (task_id,))
                
                # Tâches ponctuelles
                cursor.execute("""
                    UPDATE one_time_tasks 
                    SET status = 'cancelled'
                    WHERE id = ?
                """, (task_id,))
            
            logger.info(f"Tâche {task_id} annulée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation de la tâche {task_id}: {e}")
            return False
    
    def enable_task(self, task_id: str) -> bool:
        """Active une tâche"""
        return self._toggle_task(task_id, True)
    
    def disable_task(self, task_id: str) -> bool:
        """Désactive une tâche"""
        return self._toggle_task(task_id, False)
    
    def _toggle_task(self, task_id: str, enabled: bool) -> bool:
        """Active/désactive une tâche"""
        try:
            # Mise à jour du cache
            if task_id in self.scheduled_tasks:
                self.scheduled_tasks[task_id].is_enabled = enabled
                if enabled:
                    # Recalcul de la prochaine exécution
                    task = self.scheduled_tasks[task_id]
                    task.next_run = self._calculate_next_run(task.cron_expression)
            
            # Mise à jour en base
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE scheduled_tasks 
                    SET is_enabled = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (enabled, task_id))
            
            action = "activée" if enabled else "désactivée"
            logger.info(f"Tâche {task_id} {action}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la modification de la tâche {task_id}: {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Récupère le statut d'une tâche"""
        # Recherche dans le cache
        if task_id in self.scheduled_tasks:
            task = self.scheduled_tasks[task_id]
            return {
                'id': task.id,
                'name': task.name,
                'status': task.status.value,
                'next_run': task.next_run.isoformat() if task.next_run else None,
                'last_run': task.last_run.isoformat() if task.last_run else None,
                'retry_count': task.retry_count,
                'last_error': task.last_error,
                'is_enabled': task.is_enabled
            }
        
        # Recherche en base
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tâches récurrentes
            cursor.execute("SELECT * FROM scheduled_tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row['id'],
                    'name': row['name'],
                    'status': row['status'],
                    'next_run': row['next_run'],
                    'last_run': row['last_run'],
                    'retry_count': row['retry_count'],
                    'last_error': row['last_error'],
                    'is_enabled': bool(row['is_enabled'])
                }
            
            # Tâches ponctuelles
            cursor.execute("SELECT * FROM one_time_tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row['id'],
                    'name': row['name'],
                    'status': row['status'],
                    'scheduled_for': row['scheduled_for'],
                    'executed_at': row['executed_at'],
                    'last_error': row['last_error']
                }
        
        return None
    
    def list_tasks(self, include_disabled: bool = True) -> List[Dict[str, Any]]:
        """Liste toutes les tâches planifiées"""
        tasks = []
        
        # Tâches du cache
        for task in self.scheduled_tasks.values():
            if include_disabled or task.is_enabled:
                tasks.append({
                    'id': task.id,
                    'name': task.name,
                    'description': task.description,
                    'type': 'recurring',
                    'cron_expression': str(task.cron_expression),
                    'next_run': task.next_run.isoformat() if task.next_run else None,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'status': task.status.value,
                    'is_enabled': task.is_enabled,
                    'retry_count': task.retry_count,
                    'last_error': task.last_error
                })
        
        # Tâches ponctuelles depuis la base
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM one_time_tasks 
                WHERE status != 'cancelled'
                ORDER BY scheduled_for
            """)
            
            for row in cursor.fetchall():
                tasks.append({
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'type': 'one_time',
                    'scheduled_for': row['scheduled_for'],
                    'status': row['status'],
                    'executed_at': row['executed_at'],
                    'last_error': row['last_error']
                })
        
        return tasks
    
    def get_task_history(self, task_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère l'historique d'exécution d'une tâche"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM task_execution_history
                WHERE task_id = ?
                ORDER BY execution_start DESC
                LIMIT ?
            """, (task_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def _scheduler_loop(self):
        """Boucle principale du planificateur"""
        logger.info("Boucle du planificateur démarrée")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # Pause si demandée
                if self.is_paused:
                    self.pause_event.wait()
                    continue
                
                current_time = datetime.now()
                
                # Vérification des tâches récurrentes
                self._check_scheduled_tasks(current_time)
                
                # Vérification des tâches ponctuelles
                self._check_one_time_tasks(current_time)
                
                # Attente avant la prochaine vérification
                self.stop_event.wait(self.check_interval)
                
            except Exception as e:
                logger.error(f"Erreur dans la boucle du planificateur: {e}")
                time.sleep(60)  # Attente plus longue en cas d'erreur
        
        logger.info("Boucle du planificateur arrêtée")
    
    def _check_scheduled_tasks(self, current_time: datetime):
        """Vérifie les tâches récurrentes à exécuter"""
        tasks_to_run = []
        
        for task in self.scheduled_tasks.values():
            if (task.is_enabled and 
                task.status in [TaskStatus.SCHEDULED, TaskStatus.FAILED] and
                task.next_run and 
                task.next_run <= current_time):
                tasks_to_run.append(task)
        
        for task in tasks_to_run:
            self._queue_task_for_execution(
                task.id, task.callback, task.priority,
                *task.callback_args, **task.callback_kwargs
            )
            
            # Calcul de la prochaine exécution
            task.next_run = self._calculate_next_run(task.cron_expression)
            task.status = TaskStatus.PENDING
            
            # Mise à jour en base
            self._update_task_in_db(task)
    
    def _check_one_time_tasks(self, current_time: datetime):
        """Vérifie les tâches ponctuelles à exécuter"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM one_time_tasks
                WHERE status = 'pending' AND scheduled_for <= ?
            """, (current_time.isoformat(),))
            
            for row in cursor.fetchall():
                # Mise à jour du statut
                cursor.execute("""
                    UPDATE one_time_tasks 
                    SET status = 'running'
                    WHERE id = ?
                """, (row['id'],))
                
                # Ajout à la queue d'exécution
                callback_kwargs = json.loads(row['callback_kwargs']) if row['callback_kwargs'] else {}
                priority = TaskPriority(row['priority'])
                
                self._queue_task_for_execution(
                    row['id'], None, priority, **callback_kwargs
                )
    
    def _queue_task_for_execution(self, task_id: str, callback: Callable,
                                priority: TaskPriority, *args, **kwargs):
        """Ajoute une tâche à la queue d'exécution"""
        try:
            # Priorité inversée pour queue.PriorityQueue (plus petit = plus prioritaire)
            queue_priority = 5 - priority.value
            
            task_item = (queue_priority, datetime.now(), task_id, callback, args, kwargs)
            self.task_queue.put(task_item)
            
            logger.debug(f"Tâche {task_id} ajoutée à la queue d'exécution")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de la tâche {task_id} à la queue: {e}")
    
    def _worker_loop(self):
        """Boucle des workers d'exécution"""
        thread_name = threading.current_thread().name
        logger.debug(f"Worker {thread_name} démarré")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # Récupération d'une tâche avec timeout
                try:
                    item = self.task_queue.get(timeout=1)
                    priority, queued_at, task_id, callback, args, kwargs = item
                except queue.Empty:
                    continue
                
                # Pause si demandée
                if self.is_paused:
                    # Remettre la tâche en queue
                    self.task_queue.put(item)
                    time.sleep(1)
                    continue
                
                # Exécution de la tâche
                self._execute_task(task_id, callback, args, kwargs)
                
                # Marquer la tâche comme terminée dans la queue
                self.task_queue.task_done()
                
            except Exception as e:
                logger.error(f"Erreur dans le worker {thread_name}: {e}")
        
        logger.debug(f"Worker {thread_name} arrêté")
    
    def _execute_task(self, task_id: str, callback: Callable, args: tuple, kwargs: Dict[str, Any]):
        """Exécute une tâche"""
        execution_start = datetime.now()
        execution_id = None
        
        try:
            # Enregistrement du début d'exécution
            execution_id = self._record_execution_start(task_id, execution_start)
            
            # Mise à jour du statut
            self._update_task_status(task_id, TaskStatus.RUNNING)
            
            # Callback de début
            if self.on_task_started:
                self.on_task_started(task_id, execution_start)
            
            logger.info(f"Exécution de la tâche {task_id}")
            
            # Exécution de la fonction callback
            if callback:
                result = callback(*args, **kwargs)
            else:
                # Pour les tâches ponctuelles sans callback défini
                result = None
            
            execution_end = datetime.now()
            execution_time = (execution_end - execution_start).total_seconds()
            
            # Enregistrement du succès
            self._record_execution_end(execution_id, execution_end, TaskStatus.COMPLETED, None, execution_time)
            
            # Mise à jour du statut de la tâche
            self._update_task_status(task_id, TaskStatus.COMPLETED, execution_time=execution_time)
            
            # Mise à jour des métriques
            self._update_metrics(execution_time, success=True)
            
            # Callback de succès
            if self.on_task_completed:
                self.on_task_completed(task_id, result)
            
            logger.info(f"Tâche {task_id} exécutée avec succès en {execution_time:.2f}s")
            
        except Exception as e:
            execution_end = datetime.now()
            execution_time = (execution_end - execution_start).total_seconds()
            error_message = str(e)
            
            logger.error(f"Erreur lors de l'exécution de la tâche {task_id}: {error_message}")
            
            # Enregistrement de l'échec
            if execution_id:
                self._record_execution_end(execution_id, execution_end, TaskStatus.FAILED, error_message, execution_time)
            
            # Gestion des retries
            retry_count = self._handle_task_retry(task_id, error_message)
            
            # Mise à jour des métriques
            self._update_metrics(execution_time, success=False)
            
            # Callback d'échec
            if self.on_task_failed:
                self.on_task_failed(task_id, e)
    
    def _calculate_next_run(self, cron_expr: CronExpression) -> datetime:
        """Calcule la prochaine exécution selon l'expression CRON"""
        now = datetime.now()
        
        # Commencer à la minute suivante
        next_run = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # Recherche de la prochaine date valide (max 4 ans dans le futur)
        for _ in range(366 * 4 * 24 * 60):  # Éviter les boucles infinies
            if self._matches_cron(next_run, cron_expr):
                return next_run
            next_run += timedelta(minutes=1)
        
        # Si aucune date trouvée, utiliser une date dans le futur
        return now + timedelta(days=365)
    
    def _matches_cron(self, dt: datetime, cron_expr: CronExpression) -> bool:
        """Vérifie si une date correspond à l'expression CRON"""
        # Vérification de la minute
        if not self._matches_cron_field(dt.minute, cron_expr.minute, 0, 59):
            return False
        
        # Vérification de l'heure
        if not self._matches_cron_field(dt.hour, cron_expr.hour, 0, 23):
            return False
        
        # Vérification du jour du mois
        if not self._matches_cron_field(dt.day, cron_expr.day, 1, 31):
            return False
        
        # Vérification du mois
        if not self._matches_cron_field(dt.month, cron_expr.month, 1, 12):
            return False
        
        # Vérification du jour de la semaine (0 et 7 = dimanche)
        weekday = dt.weekday() + 1  # Conversion: lundi=1, ..., dimanche=7
        if weekday == 7:
            weekday = 0  # Dimanche = 0
        
        return self._matches_cron_field(weekday, cron_expr.weekday, 0, 7)
    
    def _matches_cron_field(self, value: int, pattern: str, min_val: int, max_val: int) -> bool:
        """Vérifie si une valeur correspond à un champ CRON"""
        if pattern == "*":
            return True
        
        # Gestion des listes (ex: "1,3,5")
        if "," in pattern:
            return value in [int(x.strip()) for x in pattern.split(",")]
        
        # Gestion des plages (ex: "1-5")
        if "-" in pattern:
            start, end = map(int, pattern.split("-"))
            return start <= value <= end
        
        # Gestion des intervalles (ex: "*/5")
        if "/" in pattern:
            if pattern.startswith("*/"):
                step = int(pattern[2:])
                return value % step == 0
            else:
                # Format "1-10/2"
                range_part, step = pattern.split("/")
                step = int(step)
                if "-" in range_part:
                    start, end = map(int, range_part.split("-"))
                    return start <= value <= end and (value - start) % step == 0
                else:
                    start = int(range_part)
                    return value >= start and (value - start) % step == 0
        
        # Valeur exacte
        try:
            return value == int(pattern)
        except ValueError:
            return False
    
    def _record_execution_start(self, task_id: str, start_time: datetime) -> int:
        """Enregistre le début d'exécution"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO task_execution_history (
                    task_id, execution_start, status
                ) VALUES (?, ?, ?)
            """, (task_id, start_time.isoformat(), TaskStatus.RUNNING.value))
            
            return cursor.lastrowid
    
    def _record_execution_end(self, execution_id: int, end_time: datetime,
                            status: TaskStatus, error_message: str, execution_time: float):
        """Enregistre la fin d'exécution"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE task_execution_history 
                SET execution_end = ?, status = ?, error_message = ?, execution_time = ?
                WHERE id = ?
            """, (end_time.isoformat(), status.value, error_message, execution_time, execution_id))
    
    def _update_task_status(self, task_id: str, status: TaskStatus, 
                          error_message: str = None, execution_time: float = None):
        """Met à jour le statut d'une tâche"""
        # Mise à jour du cache
        if task_id in self.scheduled_tasks:
            task = self.scheduled_tasks[task_id]
            task.status = status
            task.last_run = datetime.now()
            if error_message:
                task.last_error = error_message
            if execution_time:
                task.execution_time = execution_time
        
        # Mise à jour en base
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tâches récurrentes
            cursor.execute("""
                UPDATE scheduled_tasks 
                SET status = ?, last_run = CURRENT_TIMESTAMP, last_error = ?, 
                    execution_time = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status.value, error_message, execution_time, task_id))
            
            # Tâches ponctuelles
            if status == TaskStatus.COMPLETED:
                cursor.execute("""
                    UPDATE one_time_tasks 
                    SET status = 'completed', executed_at = CURRENT_TIMESTAMP,
                        execution_time = ?
                    WHERE id = ?
                """, (execution_time, task_id))
            elif status == TaskStatus.FAILED:
                cursor.execute("""
                    UPDATE one_time_tasks 
                    SET status = 'failed', last_error = ?
                    WHERE id = ?
                """, (error_message, task_id))
    
    def _handle_task_retry(self, task_id: str, error_message: str) -> int:
        """Gère les tentatives de retry d'une tâche"""
        if task_id in self.scheduled_tasks:
            task = self.scheduled_tasks[task_id]
            task.retry_count += 1
            task.last_error = error_message
            
            if task.retry_count < task.max_retries:
                # Programmer un retry
                retry_time = datetime.now() + timedelta(seconds=task.retry_delay_seconds)
                task.next_run = retry_time
                task.status = TaskStatus.SCHEDULED
                
                logger.info(f"Retry programmé pour la tâche {task_id} ({task.retry_count}/{task.max_retries}) à {retry_time}")
            else:
                # Max retries atteint
                task.status = TaskStatus.FAILED
                logger.error(f"Tâche {task_id} échouée définitivement après {task.max_retries} tentatives")
            
            # Mise à jour en base
            self._update_task_in_db(task)
            
            return task.retry_count
        
        return 0
    
    def _update_metrics(self, execution_time: float, success: bool):
        """Met à jour les métriques"""
        if success:
            self.metrics['tasks_executed'] += 1
        else:
            self.metrics['tasks_failed'] += 1
        
        self.metrics['total_execution_time'] += execution_time
        
        total_tasks = self.metrics['tasks_executed'] + self.metrics['tasks_failed']
        if total_tasks > 0:
            self.metrics['average_execution_time'] = self.metrics['total_execution_time'] / total_tasks
    
    def _save_task_to_db(self, task: ScheduledTask):
        """Sauvegarde une tâche en base"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO scheduled_tasks (
                    id, name, description, cron_expression, next_run, last_run,
                    callback_name, callback_args, callback_kwargs, max_retries,
                    retry_delay_seconds, timeout_seconds, priority, status,
                    retry_count, last_error, execution_time, is_enabled
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id, task.name, task.description, str(task.cron_expression),
                task.next_run.isoformat() if task.next_run else None,
                task.last_run.isoformat() if task.last_run else None,
                task.callback.__name__ if task.callback else "",
                json.dumps(task.callback_args),
                json.dumps(task.callback_kwargs),
                task.max_retries, task.retry_delay_seconds, task.timeout_seconds,
                task.priority.value, task.status.value, task.retry_count,
                task.last_error, task.execution_time, task.is_enabled
            ))
    
    def _update_task_in_db(self, task: ScheduledTask):
        """Met à jour une tâche en base"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE scheduled_tasks 
                SET next_run = ?, last_run = ?, status = ?, retry_count = ?,
                    last_error = ?, execution_time = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                task.next_run.isoformat() if task.next_run else None,
                task.last_run.isoformat() if task.last_run else None,
                task.status.value, task.retry_count, task.last_error,
                task.execution_time, task.id
            ))
    
    def _load_scheduled_tasks(self):
        """Charge les tâches planifiées depuis la base"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM scheduled_tasks 
                WHERE status != 'cancelled' AND is_enabled = 1
            """)
            
            for row in cursor.fetchall():
                try:
                    task = ScheduledTask(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        cron_expression=CronExpression.from_string(row['cron_expression']),
                        next_run=datetime.fromisoformat(row['next_run']) if row['next_run'] else None,
                        last_run=datetime.fromisoformat(row['last_run']) if row['last_run'] else None,
                        callback_args=tuple(json.loads(row['callback_args'])) if row['callback_args'] else (),
                        callback_kwargs=json.loads(row['callback_kwargs']) if row['callback_kwargs'] else {},
                        max_retries=row['max_retries'],
                        retry_delay_seconds=row['retry_delay_seconds'],
                        timeout_seconds=row['timeout_seconds'],
                        priority=TaskPriority(row['priority']),
                        status=TaskStatus(row['status']),
                        retry_count=row['retry_count'],
                        last_error=row['last_error'],
                        execution_time=row['execution_time'],
                        is_enabled=bool(row['is_enabled']),
                        created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                        updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
                    )
                    
                    # Recalcul de next_run si nécessaire
                    if not task.next_run or task.next_run < datetime.now():
                        task.next_run = self._calculate_next_run(task.cron_expression)
                        task.status = TaskStatus.SCHEDULED
                    
                    self.scheduled_tasks[task.id] = task
                    
                except Exception as e:
                    logger.error(f"Erreur lors du chargement de la tâche {row['id']}: {e}")
    
    def _save_scheduled_tasks(self):
        """Sauvegarde toutes les tâches planifiées"""
        for task in self.scheduled_tasks.values():
            self._update_task_in_db(task)
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du planificateur"""
        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'scheduled_tasks_count': len(self.scheduled_tasks),
            'queue_size': self.task_queue.qsize(),
            'worker_threads_count': len(self.worker_threads),
            'metrics': self.metrics.copy()
        }