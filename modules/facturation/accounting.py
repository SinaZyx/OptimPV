"""
Module de comptabilité professionnelle pour OptimPV
Gestion des écritures comptables et export FEC
"""

import sqlite3
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
import csv
import io
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class JournalType(Enum):
    """Types de journaux comptables"""
    VENTES = "VTE"  # Journal des ventes
    ACHATS = "ACH"  # Journal des achats
    BANQUE = "BNQ"  # Journal de banque
    CAISSE = "CAI"  # Journal de caisse
    OD = "OD"       # Opérations diverses

class AccountType(Enum):
    """Types de comptes comptables"""
    CLIENT = "411"           # Clients
    FOURNISSEUR = "401"     # Fournisseurs
    TVA_COLLECTEE = "4457"  # TVA collectée
    TVA_DEDUCTIBLE = "4456" # TVA déductible
    VENTES = "706"          # Prestations de services
    BANQUE = "512"          # Banque
    CAISSE = "530"          # Caisse

@dataclass
class AccountingEntry:
    """Écriture comptable"""
    id: Optional[int] = None
    journal_code: str = ""
    entry_date: Optional[date] = None
    document_date: Optional[date] = None
    document_number: str = ""
    account_number: str = ""
    account_label: str = ""
    auxiliary_account: str = ""  # Compte auxiliaire (client/fournisseur)
    entry_label: str = ""
    debit: float = 0.0
    credit: float = 0.0
    lettrage: str = ""  # Code de lettrage pour rapprochement
    invoice_id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def validate(self) -> bool:
        """Valide l'écriture comptable"""
        if not self.journal_code or not self.entry_date:
            return False
        if not self.account_number or not self.entry_label:
            return False
        if self.debit < 0 or self.credit < 0:
            return False
        if self.debit > 0 and self.credit > 0:
            return False
        if self.debit == 0 and self.credit == 0:
            return False
        return True

@dataclass
class AccountingConfig:
    """Configuration des comptes comptables"""
    # Comptes de ventes
    account_sales: str = "706000"  # Prestations de services
    account_sales_label: str = "Prestations autoconsommation"
    
    # Comptes TVA
    account_vat_collected: str = "445710"  # TVA collectée 20%
    account_vat_collected_label: str = "TVA collectée 20%"
    
    # Comptes clients
    account_client_prefix: str = "411"  # Préfixe pour comptes clients
    use_auxiliary_accounts: bool = True  # Utiliser comptes auxiliaires
    
    # Journal par défaut
    default_journal_code: str = JournalType.VENTES.value
    
    # Options FEC
    fec_encoding: str = "utf-8"
    fec_delimiter: str = "|"

class AccountingManager:
    """Gestionnaire de comptabilité"""
    
    def __init__(self, db_path: str = "data/billing.db"):
        """Initialise le gestionnaire de comptabilité"""
        self.db_path = db_path
        self.config = AccountingConfig()
        self._init_accounting_tables()
    
    def _init_accounting_tables(self):
        """Initialise les tables comptables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
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
            
            # Index pour performances
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_entries_date 
                ON accounting_entries(entry_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_entries_account 
                ON accounting_entries(account_number)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_entries_invoice 
                ON accounting_entries(invoice_id)
            """)
            
            # Table de configuration comptable
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounting_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Configuration par défaut
            default_config = {
                'account_sales': ('706000', 'Compte de ventes par défaut'),
                'account_vat_collected': ('445710', 'Compte TVA collectée 20%'),
                'account_client_prefix': ('411', 'Préfixe comptes clients'),
                'default_journal_code': ('VTE', 'Code journal des ventes')
            }
            
            for key, (value, description) in default_config.items():
                cursor.execute("""
                    INSERT OR IGNORE INTO accounting_config (key, value, description)
                    VALUES (?, ?, ?)
                """, (key, value, description))
            
            conn.commit()
            logger.info("Tables comptables initialisées")
    
    def generate_accounting_entries(self, invoice_id: int) -> List[AccountingEntry]:
        """
        Génère les écritures comptables pour une facture
        
        Args:
            invoice_id: ID de la facture
            
        Returns:
            Liste des écritures comptables générées
        """
        entries = []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Récupérer la facture et ses détails
            cursor.execute("""
                SELECT i.*, p.name as participant_name, p.type as participant_type
                FROM invoices i
                JOIN participants p ON i.participant_id = p.id
                WHERE i.id = ?
            """, (invoice_id,))
            
            invoice = cursor.fetchone()
            if not invoice:
                logger.error(f"Facture {invoice_id} non trouvée")
                return entries
            
            # Date de l'écriture
            entry_date = date.fromisoformat(invoice['issue_date']) if invoice['issue_date'] else date.today()
            
            # Numéro de pièce
            document_number = invoice['invoice_number']
            
            # Compte client auxiliaire
            aux_account = ""
            if self.config.use_auxiliary_accounts:
                # Créer un compte auxiliaire basé sur l'ID participant
                aux_account = f"C{invoice['participant_id']:05d}"
            
            # Label de l'écriture
            entry_label = f"Fact. {document_number} - {invoice['participant_name']}"
            
            # 1. Écriture au débit : Client
            client_entry = AccountingEntry(
                journal_code=self.config.default_journal_code,
                entry_date=entry_date,
                document_date=entry_date,
                document_number=document_number,
                account_number=f"{self.config.account_client_prefix}000",
                account_label="Client",
                auxiliary_account=aux_account,
                entry_label=entry_label,
                debit=invoice['total_amount'],
                credit=0,
                invoice_id=invoice_id
            )
            entries.append(client_entry)
            
            # 2. Écriture au crédit : Ventes HT
            sales_entry = AccountingEntry(
                journal_code=self.config.default_journal_code,
                entry_date=entry_date,
                document_date=entry_date,
                document_number=document_number,
                account_number=self.config.account_sales,
                account_label=self.config.account_sales_label,
                entry_label=entry_label,
                debit=0,
                credit=invoice['subtotal'],
                invoice_id=invoice_id
            )
            entries.append(sales_entry)
            
            # 3. Écriture au crédit : TVA collectée (si applicable)
            if invoice['tax_amount'] > 0:
                vat_entry = AccountingEntry(
                    journal_code=self.config.default_journal_code,
                    entry_date=entry_date,
                    document_date=entry_date,
                    document_number=document_number,
                    account_number=self.config.account_vat_collected,
                    account_label=self.config.account_vat_collected_label,
                    entry_label=entry_label,
                    debit=0,
                    credit=invoice['tax_amount'],
                    invoice_id=invoice_id
                )
                entries.append(vat_entry)
            
            # Valider les écritures
            for entry in entries:
                if not entry.validate():
                    logger.error(f"Écriture invalide : {entry}")
                    return []
            
            # Vérifier l'équilibre
            total_debit = sum(e.debit for e in entries)
            total_credit = sum(e.credit for e in entries)
            
            if abs(total_debit - total_credit) > 0.01:
                logger.error(f"Écritures non équilibrées : débit={total_debit}, crédit={total_credit}")
                return []
            
            return entries
    
    def save_accounting_entries(self, entries: List[AccountingEntry]) -> bool:
        """
        Enregistre les écritures comptables
        
        Args:
            entries: Liste des écritures à enregistrer
            
        Returns:
            True si succès, False sinon
        """
        if not entries:
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for entry in entries:
                    cursor.execute("""
                        INSERT INTO accounting_entries (
                            journal_code, entry_date, document_date, document_number,
                            account_number, account_label, auxiliary_account,
                            entry_label, debit, credit, lettrage, invoice_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.journal_code,
                        entry.entry_date.isoformat() if entry.entry_date else None,
                        entry.document_date.isoformat() if entry.document_date else None,
                        entry.document_number,
                        entry.account_number,
                        entry.account_label,
                        entry.auxiliary_account,
                        entry.entry_label,
                        entry.debit,
                        entry.credit,
                        entry.lettrage,
                        entry.invoice_id
                    ))
                
                conn.commit()
                logger.info(f"{len(entries)} écritures comptables enregistrées")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement des écritures : {e}")
            return False
    
    def generate_fec(self, start_date: date, end_date: date, output_format: str = "csv") -> str:
        """
        Génère le Fichier des Écritures Comptables (FEC) conforme aux normes françaises
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            output_format: Format de sortie ('csv' ou 'txt')
            
        Returns:
            Contenu du fichier FEC
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Récupérer les écritures de la période
            cursor.execute("""
                SELECT * FROM accounting_entries
                WHERE entry_date >= ? AND entry_date <= ?
                ORDER BY entry_date, id
            """, (start_date.isoformat(), end_date.isoformat()))
            
            entries = cursor.fetchall()
            
            # Récupérer les informations de la société
            cursor.execute("SELECT value FROM settings WHERE key = 'company_siret'")
            siret_row = cursor.fetchone()
            siret = siret_row['value'] if siret_row else "00000000000000"
            
            # Créer le fichier FEC
            output = io.StringIO()
            delimiter = self.config.fec_delimiter
            
            # En-tête FEC obligatoire
            headers = [
                "JournalCode",      # Code journal
                "JournalLib",       # Libellé journal
                "EcritureNum",      # Numéro d'écriture
                "EcritureDate",     # Date de l'écriture
                "CompteNum",        # Numéro de compte
                "CompteLib",        # Libellé du compte
                "CompAuxNum",       # Compte auxiliaire
                "CompAuxLib",       # Libellé compte auxiliaire
                "PieceRef",         # Référence de la pièce
                "PieceDate",        # Date de la pièce
                "EcritureLib",      # Libellé de l'écriture
                "Debit",            # Montant au débit
                "Credit",           # Montant au crédit
                "EcritureLet",      # Lettrage
                "DateLet",          # Date de lettrage
                "ValidDate",        # Date de validation
                "Montantdevise",    # Montant en devise
                "Idevise"           # Identifiant devise
            ]
            
            writer = csv.writer(output, delimiter=delimiter)
            writer.writerow(headers)
            
            # Mapping des codes journaux vers libellés
            journal_labels = {
                "VTE": "Journal des ventes",
                "ACH": "Journal des achats",
                "BNQ": "Journal de banque",
                "CAI": "Journal de caisse",
                "OD": "Opérations diverses"
            }
            
            # Écrire les écritures
            for idx, entry in enumerate(entries, 1):
                row = [
                    entry['journal_code'],
                    journal_labels.get(entry['journal_code'], entry['journal_code']),
                    str(idx),  # Numéro séquentiel
                    entry['entry_date'],
                    entry['account_number'],
                    entry['account_label'],
                    entry['auxiliary_account'] or "",
                    "",  # Libellé compte auxiliaire (à implémenter si nécessaire)
                    entry['document_number'] or "",
                    entry['document_date'] or entry['entry_date'],
                    entry['entry_label'],
                    f"{entry['debit']:.2f}" if entry['debit'] > 0 else "0,00",
                    f"{entry['credit']:.2f}" if entry['credit'] > 0 else "0,00",
                    entry['lettrage'] or "",
                    "",  # Date de lettrage (à implémenter)
                    entry['entry_date'],  # Date de validation = date écriture
                    "",  # Montant devise
                    ""   # Code devise
                ]
                
                # Remplacer les points par des virgules pour les montants (norme française)
                row = [str(cell).replace('.', ',') if isinstance(cell, float) else cell for cell in row]
                
                writer.writerow(row)
            
            content = output.getvalue()
            output.close()
            
            # Ajouter l'identifiant du FEC en début de fichier
            fec_header = f"SIRET{siret}FEC{start_date.strftime('%Y%m%d')}\n"
            
            return fec_header + content
    
    def get_accounting_balance(self, start_date: date, end_date: date) -> Dict[str, Dict[str, float]]:
        """
        Calcule la balance comptable pour une période
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            Balance par compte {account_number: {'debit': x, 'credit': y, 'solde': z}}
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    account_number,
                    account_label,
                    SUM(debit) as total_debit,
                    SUM(credit) as total_credit
                FROM accounting_entries
                WHERE entry_date >= ? AND entry_date <= ?
                GROUP BY account_number, account_label
                ORDER BY account_number
            """, (start_date.isoformat(), end_date.isoformat()))
            
            balance = {}
            for row in cursor.fetchall():
                account = row[0]
                balance[account] = {
                    'label': row[1],
                    'debit': row[2] or 0,
                    'credit': row[3] or 0,
                    'solde': (row[2] or 0) - (row[3] or 0)
                }
            
            return balance
    
    def get_journal_entries(self, journal_code: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        Récupère les écritures d'un journal pour une période
        
        Args:
            journal_code: Code du journal
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            Liste des écritures
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM accounting_entries
                WHERE journal_code = ? 
                AND entry_date >= ? 
                AND entry_date <= ?
                ORDER BY entry_date, id
            """, (journal_code, start_date.isoformat(), end_date.isoformat()))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_config(self, key: str, value: str) -> bool:
        """
        Met à jour la configuration comptable
        
        Args:
            key: Clé de configuration
            value: Nouvelle valeur
            
        Returns:
            True si succès
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE accounting_config 
                    SET value = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE key = ?
                """, (value, key))
                
                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO accounting_config (key, value)
                        VALUES (?, ?)
                    """, (key, value))
                
                conn.commit()
                
                # Mettre à jour la configuration en mémoire
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                
                return True
                
        except Exception as e:
            logger.error(f"Erreur mise à jour config : {e}")
            return False
    
    def process_invoice_accounting(self, invoice_id: int) -> bool:
        """
        Traite la comptabilisation complète d'une facture
        
        Args:
            invoice_id: ID de la facture
            
        Returns:
            True si succès
        """
        try:
            # Générer les écritures
            entries = self.generate_accounting_entries(invoice_id)
            if not entries:
                return False
            
            # Enregistrer les écritures
            return self.save_accounting_entries(entries)
            
        except Exception as e:
            logger.error(f"Erreur comptabilisation facture {invoice_id}: {e}")
            return False