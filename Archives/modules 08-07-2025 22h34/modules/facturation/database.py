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
            
            conn.commit()
            logger.info("Database initialized successfully")
    
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