"""Gestion de la base de données SQLite pour le module ERP.

Ce module gère toutes les interactions avec la base de données ERP,
incluant la création des tables, les migrations et les opérations CRUD.
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager
import json

logger = logging.getLogger(__name__)


class ERPDatabase:
    """Gestionnaire de base de données pour le module ERP."""
    
    def __init__(self, db_path: str = None):
        """Initialise la connexion à la base de données.
        
        Args:
            db_path: Chemin vers le fichier de base de données. 
                    Par défaut: data/erp_clients.db
        """
        if db_path is None:
            # Créer le répertoire data s'il n'existe pas
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "erp_clients.db")
            
        self.db_path = os.path.abspath(db_path)
        self._init_database()
        
    @contextmanager
    def get_connection(self):
        """Context manager pour gérer les connexions à la base de données."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Erreur base de données: {e}")
            raise
        finally:
            conn.close()
            
    def _init_database(self):
        """Initialise les tables de la base de données si elles n'existent pas."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Table Clients
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code_client VARCHAR(50) UNIQUE NOT NULL,
                    nom VARCHAR(200) NOT NULL,
                    type_client VARCHAR(50) CHECK(type_client IN ('producteur', 'consommateur', 'prosumer')),
                    adresse TEXT,
                    code_postal VARCHAR(10),
                    ville VARCHAR(100),
                    latitude REAL,
                    longitude REAL,
                    zone_geographique VARCHAR(100),
                    telephone VARCHAR(20),
                    email VARCHAR(200),
                    siret VARCHAR(20),
                    contact_principal VARCHAR(200),
                    notes TEXT,
                    metadata TEXT, -- JSON pour données additionnelles
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    actif BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Table Prix Clients
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prix_clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    prix_kwh REAL NOT NULL,
                    date_debut DATE NOT NULL,
                    date_fin DATE,
                    type_tarif VARCHAR(50) CHECK(type_tarif IN ('fixe', 'indexe', 'dynamique')),
                    reference_prix VARCHAR(100),
                    remise_pourcentage REAL DEFAULT 0,
                    formule_calcul TEXT, -- JSON pour formules complexes
                    notes TEXT,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
                )
            """)
            
            # Table Points Production (nouvelle version pour autoconso)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS points_production (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    nom VARCHAR(200) NOT NULL,
                    type_installation VARCHAR(50) DEFAULT 'Toiture',
                    capacite_kwc REAL NOT NULL,
                    capacite_disponible_kwc REAL,
                    date_mise_service DATE,
                    adresse TEXT,
                    latitude REAL,
                    longitude REAL,
                    actif BOOLEAN DEFAULT TRUE,
                    notes TEXT,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
                )
            """)
            
            # Table Points Consommation
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS points_consommation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    reference_interne VARCHAR(100) NOT NULL,
                    type_point VARCHAR(50) DEFAULT 'Principal',
                    consommation_annuelle_kwh REAL DEFAULT 0,
                    puissance_souscrite_kva INTEGER DEFAULT 36,
                    adresse TEXT,
                    latitude REAL,
                    longitude REAL,
                    actif BOOLEAN DEFAULT TRUE,
                    notes TEXT,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
                )
            """)
            
            # Table Autoconsommation Collective (nouvelle version)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS autoconso_collective (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    point_production_id INTEGER NOT NULL,
                    point_consommation_id INTEGER NOT NULL,
                    pourcentage_allocation REAL NOT NULL CHECK(pourcentage_allocation >= 0 AND pourcentage_allocation <= 100),
                    date_debut DATE NOT NULL,
                    date_fin DATE,
                    actif BOOLEAN DEFAULT TRUE,
                    notes TEXT,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (point_production_id) REFERENCES points_production(id) ON DELETE CASCADE,
                    FOREIGN KEY (point_consommation_id) REFERENCES points_consommation(id) ON DELETE CASCADE
                )
            """)
            
            # Table Historique Modifications
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historique_modifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name VARCHAR(50) NOT NULL,
                    record_id INTEGER NOT NULL,
                    action VARCHAR(20) NOT NULL CHECK(action IN ('INSERT', 'UPDATE', 'DELETE')),
                    old_values TEXT, -- JSON
                    new_values TEXT, -- JSON
                    user_id VARCHAR(100),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index pour les performances
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clients_code ON clients(code_client)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clients_zone ON clients(zone_geographique)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_prix_client_date ON prix_clients(client_id, date_debut, date_fin)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_autoconso_production ON autoconso_collective(point_production_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_autoconso_consommation ON autoconso_collective(point_consommation_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_points_production_client ON points_production(client_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_points_consommation_client ON points_consommation(client_id)")
            
            # Triggers pour la mise à jour automatique de date_modification
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_client_timestamp 
                AFTER UPDATE ON clients
                BEGIN
                    UPDATE clients SET date_modification = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            """)
            
            logger.info(f"Base de données ERP initialisée: {self.db_path}")
            
        # Appliquer les migrations automatiquement
        self._apply_migrations()
            
    def _apply_migrations(self):
        """Applique automatiquement les migrations en attente."""
        try:
            from .migrations import MigrationManager
            
            migration_manager = MigrationManager(self.db_path)
            applied = migration_manager.migrate()
            
            if applied > 0:
                logger.info(f"{applied} migration(s) appliquée(s) avec succès")
            else:
                logger.debug("Aucune migration en attente")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'application des migrations: {e}")
            # Ne pas faire échouer l'initialisation pour les erreurs de migration
            
    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict]:
        """Exécute une requête SELECT et retourne les résultats.
        
        Args:
            query: Requête SQL à exécuter
            params: Paramètres de la requête
            
        Returns:
            Liste de dictionnaires contenant les résultats
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
            
    def execute_command(self, command: str, params: Tuple = ()) -> int:
        """Exécute une commande INSERT/UPDATE/DELETE.
        
        Args:
            command: Commande SQL à exécuter
            params: Paramètres de la commande
            
        Returns:
            ID de la dernière ligne insérée ou nombre de lignes affectées
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(command, params)
            if command.strip().upper().startswith("INSERT"):
                return cursor.lastrowid
            else:
                return cursor.rowcount
                
    def migrate_from_billing_db(self, billing_db_path: str):
        """Migre les données clients depuis la base de facturation existante.
        
        Args:
            billing_db_path: Chemin vers la base billing.db
        """
        try:
            billing_conn = sqlite3.connect(billing_db_path)
            billing_conn.row_factory = sqlite3.Row
            
            # Récupérer les clients de la base facturation
            cursor = billing_conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"Tables trouvées dans billing.db: {tables}")
            
            # TODO: Adapter selon la structure réelle de billing.db
            # Cette partie sera complétée après analyse de la structure exacte
            
            billing_conn.close()
            logger.info("Migration depuis billing.db terminée")
            
        except Exception as e:
            logger.error(f"Erreur lors de la migration: {e}")
            raise
            
    def get_database_stats(self) -> Dict[str, int]:
        """Retourne des statistiques sur la base de données.
        
        Returns:
            Dictionnaire contenant le nombre d'enregistrements par table
        """
        stats = {}
        tables = ['clients', 'prix_clients', 'points_production', 'autoconso_collective']
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
                
        return stats
        
    def backup_database(self, backup_dir: str = None) -> str:
        """Crée une sauvegarde de la base de données.
        
        Args:
            backup_dir: Répertoire de sauvegarde (par défaut: data/backups)
            
        Returns:
            Chemin du fichier de sauvegarde
        """
        if backup_dir is None:
            backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")
            
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"erp_clients_backup_{timestamp}.db")
        
        with self.get_connection() as conn:
            backup_conn = sqlite3.connect(backup_path)
            conn.backup(backup_conn)
            backup_conn.close()
            
        logger.info(f"Sauvegarde créée: {backup_path}")
        return backup_path