"""Gestion des migrations de la base de données ERP.

Ce module gère les migrations de schéma pour permettre l'évolution
de la base de données tout en préservant les données existantes.
"""

import sqlite3
import logging
from typing import List, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class Migration:
    """Représente une migration de base de données."""
    
    def __init__(self, version: int, description: str, up_func: Callable, down_func: Callable = None):
        """Initialise une migration.
        
        Args:
            version: Numéro de version de la migration
            description: Description de la migration
            up_func: Fonction pour appliquer la migration
            down_func: Fonction pour annuler la migration (optionnel)
        """
        self.version = version
        self.description = description
        self.up = up_func
        self.down = down_func


class MigrationManager:
    """Gestionnaire des migrations de base de données."""
    
    def __init__(self, db_path: str):
        """Initialise le gestionnaire de migrations.
        
        Args:
            db_path: Chemin vers la base de données
        """
        self.db_path = db_path
        self.migrations = self._define_migrations()
        self._init_migrations_table()
        
    def _init_migrations_table(self):
        """Crée la table de suivi des migrations si elle n'existe pas."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
    def _define_migrations(self) -> List[Migration]:
        """Définit toutes les migrations disponibles.
        
        Returns:
            Liste des migrations ordonnées par version
        """
        migrations = []
        
        # Migration 1: Ajout de champs pour l'intégration facturation
        def migration_001_up(conn):
            cursor = conn.cursor()
            cursor.execute("""
                ALTER TABLE clients ADD COLUMN code_comptable VARCHAR(20)
            """)
            cursor.execute("""
                ALTER TABLE clients ADD COLUMN conditions_paiement VARCHAR(100) DEFAULT '30 jours'
            """)
            
        migrations.append(Migration(
            1, 
            "Ajout champs intégration facturation",
            migration_001_up
        ))
        
        # Migration 2: Table de liaison clients-documents
        def migration_002_up(conn):
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents_clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    type_document VARCHAR(50) NOT NULL,
                    nom_fichier VARCHAR(255) NOT NULL,
                    chemin_fichier TEXT NOT NULL,
                    taille_octets INTEGER,
                    hash_fichier VARCHAR(64),
                    date_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    uploaded_by VARCHAR(100),
                    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_client ON documents_clients(client_id)
            """)
            
        migrations.append(Migration(
            2,
            "Création table documents clients",
            migration_002_up
        ))
        
        # Migration 3: Table des zones géographiques
        def migration_003_up(conn):
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS zones_geographiques (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT,
                    polygone TEXT, -- GeoJSON ou WKT
                    couleur_carte VARCHAR(7) DEFAULT '#0000FF',
                    prix_defaut_kwh REAL,
                    actif BOOLEAN DEFAULT TRUE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS zones_codes_postaux (
                    zone_id INTEGER NOT NULL,
                    code_postal VARCHAR(10) NOT NULL,
                    PRIMARY KEY (zone_id, code_postal),
                    FOREIGN KEY (zone_id) REFERENCES zones_geographiques(id) ON DELETE CASCADE
                )
            """)
            
        migrations.append(Migration(
            3,
            "Création tables zones géographiques",
            migration_003_up
        ))
        
        # Migration 4: Table de suivi des consommations
        def migration_004_up(conn):
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS consommations_clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    date_periode DATE NOT NULL,
                    consommation_kwh REAL NOT NULL,
                    production_kwh REAL DEFAULT 0,
                    autoconso_kwh REAL DEFAULT 0,
                    injection_kwh REAL DEFAULT 0,
                    source_donnees VARCHAR(50), -- 'manuel', 'import', 'api'
                    date_import TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
                    UNIQUE(client_id, date_periode)
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conso_client_date ON consommations_clients(client_id, date_periode)
            """)
            
        migrations.append(Migration(
            4,
            "Création table consommations clients",
            migration_004_up
        ))
        
        # Migration 5: Ajout colonne actif à prix_clients
        def migration_005_up(conn):
            cursor = conn.cursor()
            
            # Vérifier si la colonne existe déjà
            cursor.execute("PRAGMA table_info(prix_clients)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'actif' not in columns:
                cursor.execute("""
                    ALTER TABLE prix_clients ADD COLUMN actif BOOLEAN DEFAULT TRUE
                """)
                # Mettre tous les prix existants comme actifs
                cursor.execute("""
                    UPDATE prix_clients SET actif = TRUE WHERE actif IS NULL
                """)
            
        migrations.append(Migration(
            5,
            "Ajout colonne actif à prix_clients",
            migration_005_up
        ))
        
        return sorted(migrations, key=lambda m: m.version)
        
    def get_current_version(self) -> int:
        """Retourne la version actuelle du schéma.
        
        Returns:
            Numéro de version actuel (0 si aucune migration appliquée)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(version) FROM schema_migrations")
        result = cursor.fetchone()
        
        conn.close()
        
        return result[0] if result[0] is not None else 0
        
    def get_pending_migrations(self) -> List[Migration]:
        """Retourne la liste des migrations en attente.
        
        Returns:
            Liste des migrations non encore appliquées
        """
        current_version = self.get_current_version()
        return [m for m in self.migrations if m.version > current_version]
        
    def migrate(self, target_version: int = None) -> int:
        """Applique les migrations jusqu'à la version cible.
        
        Args:
            target_version: Version cible (None = dernière version)
            
        Returns:
            Nombre de migrations appliquées
        """
        if target_version is None:
            target_version = max(m.version for m in self.migrations) if self.migrations else 0
            
        current_version = self.get_current_version()
        
        if current_version >= target_version:
            logger.info(f"Base de données déjà à jour (version {current_version})")
            return 0
            
        conn = sqlite3.connect(self.db_path)
        applied_count = 0
        
        try:
            for migration in self.migrations:
                if current_version < migration.version <= target_version:
                    logger.info(f"Application migration {migration.version}: {migration.description}")
                    
                    # Appliquer la migration
                    migration.up(conn)
                    
                    # Enregistrer la migration
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                        (migration.version, migration.description)
                    )
                    
                    conn.commit()
                    applied_count += 1
                    logger.info(f"Migration {migration.version} appliquée avec succès")
                    
        except Exception as e:
            conn.rollback()
            logger.error(f"Erreur lors de la migration: {e}")
            raise
        finally:
            conn.close()
            
        logger.info(f"{applied_count} migration(s) appliquée(s)")
        return applied_count
        
    def rollback(self, target_version: int) -> int:
        """Annule les migrations jusqu'à la version cible.
        
        Args:
            target_version: Version cible
            
        Returns:
            Nombre de migrations annulées
        """
        current_version = self.get_current_version()
        
        if current_version <= target_version:
            logger.info(f"Rien à annuler (version actuelle: {current_version})")
            return 0
            
        conn = sqlite3.connect(self.db_path)
        rolled_back = 0
        
        try:
            for migration in reversed(self.migrations):
                if target_version < migration.version <= current_version:
                    if migration.down is None:
                        raise ValueError(f"Migration {migration.version} ne peut pas être annulée")
                        
                    logger.info(f"Annulation migration {migration.version}: {migration.description}")
                    
                    # Annuler la migration
                    migration.down(conn)
                    
                    # Supprimer l'enregistrement
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM schema_migrations WHERE version = ?",
                        (migration.version,)
                    )
                    
                    conn.commit()
                    rolled_back += 1
                    logger.info(f"Migration {migration.version} annulée avec succès")
                    
        except Exception as e:
            conn.rollback()
            logger.error(f"Erreur lors du rollback: {e}")
            raise
        finally:
            conn.close()
            
        logger.info(f"{rolled_back} migration(s) annulée(s)")
        return rolled_back
        
    def get_migration_history(self) -> List[Dict]:
        """Retourne l'historique des migrations appliquées.
        
        Returns:
            Liste des migrations avec leur date d'application
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT version, description, applied_at 
            FROM schema_migrations 
            ORDER BY version
        """)
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'version': row[0],
                'description': row[1],
                'applied_at': row[2]
            })
            
        conn.close()
        return history