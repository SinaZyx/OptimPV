"""
Module de numérotation séquentielle des factures
Garantit l'unicité et la séquentialité des numéros de facture
"""

import sqlite3
import logging
import threading
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """Types de documents numérotés"""
    INVOICE = "FACTURE"
    CREDIT_NOTE = "AVOIR"
    QUOTE = "DEVIS"
    ORDER = "COMMANDE"

@dataclass
class NumberingSequence:
    """Séquence de numérotation"""
    id: Optional[int] = None
    document_type: str = DocumentType.INVOICE.value
    prefix: str = "PMO"
    year: int = datetime.now().year
    last_number: int = 0
    format_pattern: str = "{prefix}-{year}-{number:05d}"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def get_next_formatted(self) -> str:
        """Retourne le prochain numéro formaté"""
        return self.format_pattern.format(
            prefix=self.prefix,
            year=self.year,
            number=self.last_number + 1
        )

@dataclass
class NumberingLog:
    """Journal d'attribution des numéros"""
    id: Optional[int] = None
    sequence_id: int = 0
    document_type: str = ""
    document_id: int = 0
    assigned_number: str = ""
    assigned_at: Optional[datetime] = None
    assigned_by: str = ""
    notes: str = ""

class InvoiceNumbering:
    """Gestionnaire de numérotation des factures avec verrouillage"""
    
    def __init__(self, db_path: str = "data/billing.db"):
        """Initialise le gestionnaire de numérotation"""
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_numbering_tables()
    
    def _init_numbering_tables(self):
        """Initialise les tables de numérotation"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
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
            
            # Table des avoirs (credit notes)
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
            
            # Table du journal de numérotation
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS numbering_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sequence_id INTEGER NOT NULL,
                    document_type TEXT NOT NULL,
                    document_id INTEGER NOT NULL,
                    assigned_number TEXT NOT NULL,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    assigned_by TEXT,
                    notes TEXT,
                    FOREIGN KEY (sequence_id) REFERENCES invoice_sequences(id),
                    UNIQUE(document_type, assigned_number)
                )
            """)
            
            # Index pour performances
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sequences_active 
                ON invoice_sequences(document_type, is_active)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_numbering_log_number 
                ON numbering_log(assigned_number)
            """)
            
            # Créer les séquences par défaut si elles n'existent pas
            current_year = datetime.now().year
            default_sequences = [
                (DocumentType.INVOICE.value, "PMO", current_year, "{prefix}-{year}-{number:05d}"),
                (DocumentType.CREDIT_NOTE.value, "AV", current_year, "{prefix}-{year}-{number:05d}"),
                (DocumentType.QUOTE.value, "DEV", current_year, "{prefix}-{year}-{number:05d}"),
            ]
            
            for doc_type, prefix, year, pattern in default_sequences:
                cursor.execute("""
                    INSERT OR IGNORE INTO invoice_sequences 
                    (document_type, prefix, year, format_pattern)
                    VALUES (?, ?, ?, ?)
                """, (doc_type, prefix, year, pattern))
            
            conn.commit()
            logger.info("Tables de numérotation initialisées")
    
    def get_next_number(self, document_type: str = DocumentType.INVOICE.value, 
                       prefix: Optional[str] = None,
                       year: Optional[int] = None,
                       user: str = "system") -> str:
        """
        Obtient le prochain numéro de document de manière thread-safe
        
        Args:
            document_type: Type de document
            prefix: Préfixe personnalisé (optionnel)
            year: Année (par défaut année courante)
            user: Utilisateur qui demande le numéro
            
        Returns:
            Numéro formaté unique
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("BEGIN EXCLUSIVE")
                    cursor = conn.cursor()
                    
                    # Année par défaut
                    if year is None:
                        year = datetime.now().year
                    
                    # Rechercher la séquence active
                    if prefix:
                        cursor.execute("""
                            SELECT * FROM invoice_sequences
                            WHERE document_type = ? AND prefix = ? AND year = ? AND is_active = 1
                            LIMIT 1
                        """, (document_type, prefix, year))
                    else:
                        cursor.execute("""
                            SELECT * FROM invoice_sequences
                            WHERE document_type = ? AND year = ? AND is_active = 1
                            ORDER BY created_at DESC
                            LIMIT 1
                        """, (document_type, year))
                    
                    row = cursor.fetchone()
                    
                    if not row:
                        # Créer une nouvelle séquence si elle n'existe pas
                        if not prefix:
                            prefix = self._get_default_prefix(document_type)
                        
                        pattern = self._get_default_pattern(document_type)
                        
                        cursor.execute("""
                            INSERT INTO invoice_sequences 
                            (document_type, prefix, year, last_number, format_pattern)
                            VALUES (?, ?, ?, 0, ?)
                        """, (document_type, prefix, year, pattern))
                        
                        sequence_id = cursor.lastrowid
                        last_number = 0
                        format_pattern = pattern
                    else:
                        sequence_id = row[0]
                        prefix = row[2]
                        last_number = row[4]
                        format_pattern = row[5]
                    
                    # Incrémenter le compteur
                    new_number = last_number + 1
                    
                    cursor.execute("""
                        UPDATE invoice_sequences 
                        SET last_number = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (new_number, sequence_id))
                    
                    # Formater le numéro
                    formatted_number = format_pattern.format(
                        prefix=prefix,
                        year=year,
                        number=new_number
                    )
                    
                    # Enregistrer dans le journal (sans document_id pour l'instant)
                    cursor.execute("""
                        INSERT INTO numbering_log 
                        (sequence_id, document_type, document_id, assigned_number, assigned_by)
                        VALUES (?, ?, 0, ?, ?)
                    """, (sequence_id, document_type, formatted_number, user))
                    
                    conn.commit()
                    
                    logger.info(f"Numéro attribué : {formatted_number}")
                    return formatted_number
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'attribution du numéro : {e}")
                raise
    
    def assign_number_to_document(self, document_type: str, document_id: int, 
                                 assigned_number: str) -> bool:
        """
        Associe un numéro déjà attribué à un document spécifique
        
        Args:
            document_type: Type de document
            document_id: ID du document
            assigned_number: Numéro attribué
            
        Returns:
            True si succès
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Mettre à jour le journal
                cursor.execute("""
                    UPDATE numbering_log 
                    SET document_id = ?
                    WHERE document_type = ? AND assigned_number = ? AND document_id = 0
                """, (document_id, document_type, assigned_number))
                
                if cursor.rowcount == 0:
                    # Si pas de ligne avec document_id = 0, vérifier si déjà assigné
                    cursor.execute("""
                        SELECT document_id FROM numbering_log
                        WHERE document_type = ? AND assigned_number = ?
                    """, (document_type, assigned_number))
                    
                    existing = cursor.fetchone()
                    if existing and existing[0] != document_id:
                        logger.error(f"Numéro {assigned_number} déjà assigné au document {existing[0]}")
                        return False
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de l'assignation du numéro : {e}")
            return False
    
    def get_sequence_info(self, document_type: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Obtient les informations de la séquence active
        
        Args:
            document_type: Type de document
            year: Année (par défaut année courante)
            
        Returns:
            Informations de la séquence ou None
        """
        if year is None:
            year = datetime.now().year
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM invoice_sequences
                WHERE document_type = ? AND year = ? AND is_active = 1
                ORDER BY created_at DESC
                LIMIT 1
            """, (document_type, year))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_numbering_history(self, document_type: Optional[str] = None, 
                            start_date: Optional[date] = None,
                            end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Récupère l'historique de numérotation
        
        Args:
            document_type: Filtrer par type (optionnel)
            start_date: Date de début (optionnel)
            end_date: Date de fin (optionnel)
            
        Returns:
            Liste des entrées du journal
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM numbering_log WHERE 1=1"
            params = []
            
            if document_type:
                query += " AND document_type = ?"
                params.append(document_type)
            
            if start_date:
                query += " AND DATE(assigned_at) >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND DATE(assigned_at) <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY assigned_at DESC"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def check_number_exists(self, number: str) -> bool:
        """
        Vérifie si un numéro existe déjà
        
        Args:
            number: Numéro à vérifier
            
        Returns:
            True si le numéro existe
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM numbering_log WHERE assigned_number = ?
            """, (number,))
            return cursor.fetchone()[0] > 0
    
    def reset_sequence(self, document_type: str, year: int, new_value: int = 0) -> bool:
        """
        Réinitialise une séquence (ATTENTION : utiliser avec précaution)
        
        Args:
            document_type: Type de document
            year: Année
            new_value: Nouvelle valeur du compteur
            
        Returns:
            True si succès
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        UPDATE invoice_sequences
                        SET last_number = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE document_type = ? AND year = ? AND is_active = 1
                    """, (new_value, document_type, year))
                    
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.warning(f"Séquence réinitialisée : {document_type} {year} -> {new_value}")
                        return True
                    
                    return False
                    
            except Exception as e:
                logger.error(f"Erreur lors de la réinitialisation : {e}")
                return False
    
    def create_custom_sequence(self, document_type: str, prefix: str, 
                             year: int, format_pattern: str) -> bool:
        """
        Crée une séquence personnalisée
        
        Args:
            document_type: Type de document
            prefix: Préfixe personnalisé
            year: Année
            format_pattern: Modèle de formatage
            
        Returns:
            True si succès
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Désactiver les anciennes séquences du même type/année
                cursor.execute("""
                    UPDATE invoice_sequences
                    SET is_active = 0
                    WHERE document_type = ? AND year = ?
                """, (document_type, year))
                
                # Créer la nouvelle séquence
                cursor.execute("""
                    INSERT INTO invoice_sequences
                    (document_type, prefix, year, format_pattern, is_active)
                    VALUES (?, ?, ?, ?, 1)
                """, (document_type, prefix, year, format_pattern))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Erreur création séquence : {e}")
            return False
    
    def _get_default_prefix(self, document_type: str) -> str:
        """Retourne le préfixe par défaut selon le type"""
        prefixes = {
            DocumentType.INVOICE.value: "PMO",
            DocumentType.CREDIT_NOTE.value: "AV",
            DocumentType.QUOTE.value: "DEV",
            DocumentType.ORDER.value: "CMD"
        }
        return prefixes.get(document_type, "DOC")
    
    def _get_default_pattern(self, document_type: str) -> str:
        """Retourne le pattern par défaut selon le type"""
        # Pattern standard : PREFIX-YYYY-NNNNN
        return "{prefix}-{year}-{number:05d}"
    
    def get_statistics(self, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtient les statistiques de numérotation
        
        Args:
            year: Année (par défaut année courante)
            
        Returns:
            Dictionnaire des statistiques
        """
        if year is None:
            year = datetime.now().year
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Statistiques par type de document
            cursor.execute("""
                SELECT 
                    document_type,
                    COUNT(*) as count,
                    MIN(assigned_at) as first_date,
                    MAX(assigned_at) as last_date
                FROM numbering_log
                WHERE strftime('%Y', assigned_at) = ?
                GROUP BY document_type
            """, (str(year),))
            
            stats = {
                'year': year,
                'by_type': {}
            }
            
            for row in cursor.fetchall():
                stats['by_type'][row[0]] = {
                    'count': row[1],
                    'first_date': row[2],
                    'last_date': row[3]
                }
            
            # Total général
            cursor.execute("""
                SELECT COUNT(*) FROM numbering_log
                WHERE strftime('%Y', assigned_at) = ?
            """, (str(year),))
            
            stats['total'] = cursor.fetchone()[0]
            
            return stats