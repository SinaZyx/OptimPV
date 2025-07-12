"""
Database module for PMO billing system
Handles SQLite database creation and management
"""

import sqlite3
import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import json
import os

logger = logging.getLogger(__name__)

class BillingDatabase:
    """Database manager for PMO billing system"""
    
    def __init__(self, db_path: str = "data/billing.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self._ensure_data_directory()
        self._init_database()
    
    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT,
                    client_name TEXT NOT NULL,
                    client_email TEXT,
                    client_phone TEXT,
                    start_date DATE,
                    end_date DATE,
                    status TEXT DEFAULT 'active',
                    total_capacity_kwc REAL,
                    total_investment REAL,
                    financing_percentage REAL,
                    annual_production_kwh REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Participants table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL, -- 'producer' or 'consumer'
                    address TEXT,
                    contact_email TEXT,
                    contact_phone TEXT,
                    consumption_profile_id TEXT,
                    allocation_percentage REAL,
                    annual_consumption_kwh REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)
            
            # Monthly production data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monthly_production (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    total_production_kwh REAL NOT NULL,
                    autoconsumption_kwh REAL,
                    injection_kwh REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    UNIQUE(project_id, year, month)
                )
            """)
            
            # Monthly consumption data per participant
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monthly_consumption (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    participant_id INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    consumption_kwh REAL NOT NULL,
                    autoconsumption_kwh REAL,
                    grid_consumption_kwh REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (participant_id) REFERENCES participants(id),
                    UNIQUE(participant_id, year, month)
                )
            """)
            
            # Billing periods
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS billing_periods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    period_name TEXT NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    status TEXT DEFAULT 'draft', -- draft, validated, sent, paid
                    total_amount REAL,
                    payment_due_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)
            
            # Individual invoices
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    billing_period_id INTEGER NOT NULL,
                    participant_id INTEGER NOT NULL,
                    invoice_number TEXT UNIQUE NOT NULL,
                    issue_date DATE NOT NULL,
                    due_date DATE NOT NULL,
                    subtotal REAL NOT NULL,
                    tax_rate REAL DEFAULT 0.0,
                    tax_amount REAL DEFAULT 0.0,
                    total_amount REAL NOT NULL,
                    status TEXT DEFAULT 'draft', -- draft, sent, paid, overdue
                    payment_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (billing_period_id) REFERENCES billing_periods(id),
                    FOREIGN KEY (participant_id) REFERENCES participants(id)
                )
            """)
            
            # Invoice line items
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoice_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    unit_price REAL NOT NULL,
                    total_price REAL NOT NULL,
                    item_type TEXT, -- autoconsumption, subscription, maintenance
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
                )
            """)
            
            # Payment records
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    payment_date DATE NOT NULL,
                    payment_method TEXT,
                    transaction_id TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
                )
            """)
            
            # System settings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default settings
            cursor.execute("""
                INSERT OR IGNORE INTO settings (key, value) VALUES 
                ('autoconsumption_price_eur_kwh', '0.15'),
                ('tax_rate', '0.20'),
                ('invoice_prefix', 'PMO'),
                ('company_name', 'OptimPV'),
                ('company_address', ''),
                ('company_siret', ''),
                ('default_payment_terms_days', '30')
            """)
            
            # ===== Nouvelles tables pour la comptabilité =====
            
            # Table des écritures comptables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounting_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    journal_code TEXT NOT NULL,
                    entry_date DATE NOT NULL,
                    document_date DATE,
                    document_number TEXT,
                    account_number TEXT NOT NULL,
                    account_label TEXT NOT NULL,
                    auxiliary_account TEXT,
                    entry_label TEXT NOT NULL,
                    debit REAL DEFAULT 0,
                    credit REAL DEFAULT 0,
                    lettrage TEXT,
                    invoice_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
                )
            """)
            
            # Table des séquences de numérotation
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoice_sequences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_type TEXT NOT NULL,
                    prefix TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    last_number INTEGER DEFAULT 0,
                    format_pattern TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(document_type, prefix, year)
                )
            """)
            
            # Table des avoirs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS credit_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    credit_note_number TEXT UNIQUE NOT NULL,
                    issue_date DATE NOT NULL,
                    reason TEXT NOT NULL,
                    subtotal REAL NOT NULL,
                    tax_rate REAL DEFAULT 0.0,
                    tax_amount REAL DEFAULT 0.0,
                    total_amount REAL NOT NULL,
                    status TEXT DEFAULT 'draft',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
                )
            """)
            
            # ===== Nouvelles tables pour la gestion avancée des paiements =====
            
            # Table des moyens de paiement
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payment_methods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    code TEXT NOT NULL UNIQUE,
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    requires_bank_details BOOLEAN DEFAULT 0,
                    processing_days INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des échéanciers de paiement
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payment_schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    installment_number INTEGER NOT NULL,
                    total_installments INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    due_date DATE NOT NULL,
                    status TEXT DEFAULT 'pending', -- pending, paid, overdue
                    payment_id INTEGER,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
                    FOREIGN KEY (payment_id) REFERENCES payments(id)
                )
            """)
            
            # Table de l'historique des relances
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dunning_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    level TEXT NOT NULL, -- friendly_reminder, first_notice, second_notice, final_notice, legal_action
                    action_date DATE NOT NULL,
                    due_amount REAL NOT NULL,
                    late_fees_amount REAL DEFAULT 0,
                    email_sent BOOLEAN DEFAULT 0,
                    email_address TEXT,
                    template_used TEXT,
                    notes TEXT,
                    next_action_date DATE,
                    next_action_level TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
                )
            """)
            
            # Table des rapprochements bancaires
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bank_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_date DATE NOT NULL,
                    value_date DATE,
                    amount REAL NOT NULL,
                    description TEXT,
                    reference TEXT,
                    account_number TEXT,
                    beneficiary_name TEXT,
                    debtor_name TEXT,
                    transaction_id TEXT UNIQUE,
                    import_batch_id TEXT,
                    status TEXT DEFAULT 'pending', -- pending, matched, partially_matched, unmatched, disputed
                    matched_invoice_id INTEGER,
                    confidence_score REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (matched_invoice_id) REFERENCES invoices(id)
                )
            """)
            
            # Table des pénalités de retard
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS late_fees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    legal_rate REAL DEFAULT 3.40, -- Taux légal français
                    days_late INTEGER NOT NULL,
                    reason TEXT,
                    applied_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
                )
            """)
            
            # Table des templates d'emails de relance
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    subject TEXT NOT NULL,
                    body TEXT NOT NULL,
                    template_type TEXT DEFAULT 'dunning', -- dunning, payment_confirmation, etc.
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des configurations de relance
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dunning_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL UNIQUE,
                    days_after_due INTEGER NOT NULL,
                    template_name TEXT NOT NULL,
                    include_late_fees BOOLEAN DEFAULT 0,
                    stop_services BOOLEAN DEFAULT 0,
                    escalate_to_legal BOOLEAN DEFAULT 0,
                    send_copy_to_manager BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des KPIs de paiement (pour cache)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payment_kpis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    calculation_date DATE NOT NULL,
                    dso_days REAL,
                    collection_rate REAL,
                    overdue_amount REAL,
                    total_receivables REAL,
                    bad_debt_rate REAL,
                    kpi_data TEXT, -- JSON data for detailed metrics
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index pour améliorer les performances
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_invoice_id ON payments(invoice_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_payment_date ON payments(payment_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bank_transactions_date ON bank_transactions(transaction_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bank_transactions_status ON bank_transactions(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dunning_actions_invoice ON dunning_actions(invoice_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dunning_actions_date ON dunning_actions(action_date)")
            
            # Insérer les moyens de paiement par défaut
            cursor.execute("""
                INSERT OR IGNORE INTO payment_methods (name, code, description, requires_bank_details, processing_days) VALUES 
                ('Virement bancaire', 'VIREMENT', 'Virement SEPA', 1, 1),
                ('Prélèvement SEPA', 'PRELEVEMENT', 'Prélèvement automatique SEPA', 1, 3),
                ('Carte bancaire', 'CB', 'Paiement par carte bancaire', 0, 0),
                ('Chèque', 'CHEQUE', 'Paiement par chèque', 0, 5),
                ('Espèces', 'ESPECES', 'Paiement en espèces', 0, 0),
                ('Autre', 'AUTRE', 'Autre moyen de paiement', 0, 0)
            """)
            
            # Insérer les règles de relance par défaut
            cursor.execute("""
                INSERT OR IGNORE INTO dunning_rules (level, days_after_due, template_name, include_late_fees, stop_services, escalate_to_legal, send_copy_to_manager) VALUES 
                ('friendly_reminder', 7, 'friendly_reminder', 0, 0, 0, 0),
                ('first_notice', 15, 'first_notice', 1, 0, 0, 0),
                ('second_notice', 30, 'second_notice', 1, 0, 0, 1),
                ('final_notice', 45, 'final_notice', 1, 1, 0, 1),
                ('legal_action', 60, 'legal_action', 1, 1, 1, 1)
            """)
            
            # ===== Tables pour l'automatisation et les workflows =====
            
            # Table des règles de workflow (déjà créée par WorkflowManager mais on s'assure)
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
            
            # Table de l'historique d'exécution des tâches
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
            
            # Table de l'historique des générations récurrentes
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
            
            # Index pour optimisation des nouvelles tables
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflow_transitions_invoice ON workflow_transitions(invoice_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflow_transitions_state ON workflow_transitions(to_state)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflow_approvals_status ON workflow_approvals(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_next_run ON scheduled_tasks(next_run)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_status ON scheduled_tasks(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_one_time_tasks_scheduled ON one_time_tasks(scheduled_for)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_history_task_id ON task_execution_history(task_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_recurring_next_billing ON recurring_subscriptions(next_billing_date, status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_recurring_participant ON recurring_subscriptions(participant_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_generation_history_subscription ON recurring_generation_history(subscription_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notification_history_status ON notification_history(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notification_history_created ON notification_history(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notification_preferences_user ON notification_preferences(user_email)")
            
            # Paramètres par défaut pour l'automatisation
            cursor.execute("""
                INSERT OR IGNORE INTO settings (key, value) VALUES 
                ('automation_enabled', 'true'),
                ('auto_generate_recurring', 'true'),
                ('auto_validate_invoices', 'false'),
                ('auto_send_notifications', 'true'),
                ('auto_dunning_enabled', 'true'),
                ('max_retry_attempts', '3'),
                ('backup_enabled', 'true'),
                ('backup_interval_hours', '24'),
                ('rate_limit_per_minute', '100'),
                ('notification_batch_size', '50'),
                ('smtp_server', ''),
                ('smtp_port', '587'),
                ('smtp_username', ''),
                ('smtp_password', ''),
                ('smtp_use_tls', 'true'),
                ('from_email', ''),
                ('from_name', 'OptimPV'),
                ('sms_provider', ''),
                ('sms_api_key', ''),
                ('sms_api_secret', ''),
                ('sms_sender', ''),
                ('webhook_timeout', '30'),
                ('webhook_retries', '3')
            """)

            conn.commit()
            logger.info("Database initialized successfully with automation and workflow tables")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def create_project(self, project_data: Dict[str, Any]) -> int:
        """Create a new project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects (
                    name, address, client_name, client_email, client_phone,
                    start_date, end_date, total_capacity_kwc, total_investment,
                    financing_percentage, annual_production_kwh
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_data['name'],
                project_data.get('address'),
                project_data['client_name'],
                project_data.get('client_email'),
                project_data.get('client_phone'),
                project_data.get('start_date'),
                project_data.get('end_date'),
                project_data.get('total_capacity_kwc'),
                project_data.get('total_investment'),
                project_data.get('financing_percentage'),
                project_data.get('annual_production_kwh')
            ))
            return cursor.lastrowid
    
    def create_participant(self, participant_data: Dict[str, Any]) -> int:
        """Create a new participant"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO participants (
                    project_id, name, type, address, contact_email,
                    contact_phone, consumption_profile_id, allocation_percentage,
                    annual_consumption_kwh
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                participant_data['project_id'],
                participant_data['name'],
                participant_data['type'],
                participant_data.get('address'),
                participant_data.get('contact_email'),
                participant_data.get('contact_phone'),
                participant_data.get('consumption_profile_id'),
                participant_data.get('allocation_percentage'),
                participant_data.get('annual_consumption_kwh')
            ))
            return cursor.lastrowid
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_participants(self, project_id: int) -> List[Dict[str, Any]]:
        """Get participants for a project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM participants 
                WHERE project_id = ? 
                ORDER BY type, name
            """, (project_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def record_monthly_production(self, project_id: int, year: int, month: int, 
                                 production_data: Dict[str, float]) -> bool:
        """Record monthly production data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO monthly_production (
                    project_id, year, month, total_production_kwh,
                    autoconsumption_kwh, injection_kwh
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                project_id, year, month,
                production_data['total_production_kwh'],
                production_data.get('autoconsumption_kwh'),
                production_data.get('injection_kwh')
            ))
            return True
    
    def record_monthly_consumption(self, participant_id: int, year: int, month: int,
                                  consumption_data: Dict[str, float]) -> bool:
        """Record monthly consumption data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO monthly_consumption (
                    participant_id, year, month, consumption_kwh,
                    autoconsumption_kwh, grid_consumption_kwh
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                participant_id, year, month,
                consumption_data['consumption_kwh'],
                consumption_data.get('autoconsumption_kwh'),
                consumption_data.get('grid_consumption_kwh')
            ))
            return True
    
    def create_billing_period(self, billing_data: Dict[str, Any]) -> int:
        """Create a new billing period"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO billing_periods (
                    project_id, period_name, start_date, end_date,
                    total_amount, payment_due_date
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                billing_data['project_id'],
                billing_data['period_name'],
                billing_data['start_date'],
                billing_data['end_date'],
                billing_data.get('total_amount'),
                billing_data.get('payment_due_date')
            ))
            return cursor.lastrowid
    
    def get_setting(self, key: str) -> Optional[str]:
        """Get a system setting"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row['value'] if row else None
    
    def set_setting(self, key: str, value: str) -> bool:
        """Set a system setting"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))
            return True
    
    def close(self):
        """Close database connection (if needed for cleanup)"""
        pass
    
    # ===== Nouvelles méthodes pour la comptabilité =====
    
    def create_invoice(self, invoice_data: Dict[str, Any]) -> int:
        """Create a new invoice"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO invoices (
                    billing_period_id, participant_id, invoice_number,
                    issue_date, due_date, subtotal, tax_rate, tax_amount,
                    total_amount, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_data['billing_period_id'],
                invoice_data['participant_id'],
                invoice_data['invoice_number'],
                invoice_data['issue_date'],
                invoice_data['due_date'],
                invoice_data['subtotal'],
                invoice_data.get('tax_rate', 0.0),
                invoice_data.get('tax_amount', 0.0),
                invoice_data['total_amount'],
                invoice_data.get('status', 'draft')
            ))
            return cursor.lastrowid
    
    def get_invoice(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific invoice"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_invoices_by_period(self, billing_period_id: int) -> List[Dict[str, Any]]:
        """Get all invoices for a billing period"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.*, p.name as participant_name
                FROM invoices i
                JOIN participants p ON i.participant_id = p.id
                WHERE i.billing_period_id = ?
                ORDER BY p.name
            """, (billing_period_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_invoice_status(self, invoice_id: int, status: str) -> bool:
        """Update invoice status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE invoices 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, invoice_id))
            return cursor.rowcount > 0
    
    def create_credit_note(self, credit_note_data: Dict[str, Any]) -> int:
        """Create a new credit note"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO credit_notes (
                    invoice_id, credit_note_number, issue_date, reason,
                    subtotal, tax_rate, tax_amount, total_amount, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                credit_note_data['invoice_id'],
                credit_note_data['credit_note_number'],
                credit_note_data['issue_date'],
                credit_note_data['reason'],
                credit_note_data['subtotal'],
                credit_note_data.get('tax_rate', 0.0),
                credit_note_data.get('tax_amount', 0.0),
                credit_note_data['total_amount'],
                credit_note_data.get('status', 'draft')
            ))
            return cursor.lastrowid
    
    def get_credit_notes_for_invoice(self, invoice_id: int) -> List[Dict[str, Any]]:
        """Get all credit notes for an invoice"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM credit_notes 
                WHERE invoice_id = ?
                ORDER BY issue_date DESC
            """, (invoice_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_accounting_entries(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get accounting entries for a period"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM accounting_entries
                WHERE entry_date >= ? AND entry_date <= ?
                ORDER BY entry_date, id
            """, (start_date.isoformat(), end_date.isoformat()))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_unpaid_invoices(self) -> List[Dict[str, Any]]:
        """Get all unpaid invoices"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.*, p.name as participant_name, pr.name as project_name
                FROM invoices i
                JOIN participants p ON i.participant_id = p.id
                JOIN billing_periods bp ON i.billing_period_id = bp.id
                JOIN projects pr ON bp.project_id = pr.id
                WHERE i.status IN ('sent', 'overdue')
                ORDER BY i.due_date
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def record_payment(self, payment_data: Dict[str, Any]) -> int:
        """Record a payment for an invoice"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert payment record
            cursor.execute("""
                INSERT INTO payments (
                    invoice_id, amount, payment_date, payment_method,
                    transaction_id, notes
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                payment_data['invoice_id'],
                payment_data['amount'],
                payment_data['payment_date'],
                payment_data.get('payment_method', ''),
                payment_data.get('transaction_id', ''),
                payment_data.get('notes', '')
            ))
            
            payment_id = cursor.lastrowid
            
            # Check if invoice is fully paid
            cursor.execute("""
                SELECT 
                    i.total_amount,
                    COALESCE(SUM(p.amount), 0) as total_paid
                FROM invoices i
                LEFT JOIN payments p ON i.id = p.invoice_id
                WHERE i.id = ?
                GROUP BY i.id
            """, (payment_data['invoice_id'],))
            
            row = cursor.fetchone()
            if row:
                total_amount = row[0]
                total_paid = row[1]
                
                if total_paid >= total_amount:
                    # Update invoice status to paid
                    cursor.execute("""
                        UPDATE invoices 
                        SET status = 'paid', payment_date = ?
                        WHERE id = ?
                    """, (payment_data['payment_date'], payment_data['invoice_id']))
            
            return payment_id
    
    def get_invoice_payments(self, invoice_id: int) -> List[Dict[str, Any]]:
        """Get all payments for an invoice"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM payments
                WHERE invoice_id = ?
                ORDER BY payment_date DESC
            """, (invoice_id,))
            return [dict(row) for row in cursor.fetchall()]