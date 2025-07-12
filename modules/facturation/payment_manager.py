"""
Advanced Payment Management Module for OptimPV
Handles payment processing, bank reconciliation, and automated matching
"""

import sqlite3
import logging
import xml.etree.ElementTree as ET
import csv
import io
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from enum import Enum
import re
from difflib import SequenceMatcher
import json

logger = logging.getLogger(__name__)

class PaymentMethod(Enum):
    """Payment method types"""
    VIREMENT = "virement"
    PRELEVEMENT_SEPA = "prelevement_sepa"
    CARTE_BANCAIRE = "carte_bancaire"
    CHEQUE = "cheque"
    ESPECES = "especes"
    AUTRE = "autre"

class PaymentStatus(Enum):
    """Payment status"""
    PENDING = "pending"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    UNMATCHED = "unmatched"
    DISPUTED = "disputed"

@dataclass
class BankTransaction:
    """Bank transaction model"""
    id: Optional[int] = None
    transaction_date: Optional[date] = None
    value_date: Optional[date] = None
    amount: float = 0.0
    description: str = ""
    reference: str = ""
    account_number: str = ""
    beneficiary_name: str = ""
    debtor_name: str = ""
    transaction_id: str = ""
    import_batch_id: str = ""
    status: PaymentStatus = PaymentStatus.PENDING
    matched_invoice_id: Optional[int] = None
    confidence_score: float = 0.0
    created_at: Optional[datetime] = None

@dataclass
class PaymentSchedule:
    """Payment schedule model"""
    id: Optional[int] = None
    invoice_id: int = 0
    installment_number: int = 1
    total_installments: int = 1
    amount: float = 0.0
    due_date: Optional[date] = None
    status: str = "pending"  # pending, paid, overdue
    payment_id: Optional[int] = None
    created_at: Optional[datetime] = None

@dataclass
class LateFee:
    """Late fee calculation model"""
    invoice_id: int
    days_late: int
    base_amount: float
    legal_rate: float  # Taux légal français
    calculated_fee: float
    applied_date: date

class PaymentManager:
    """Advanced payment management with bank reconciliation and automated matching"""
    
    def __init__(self, db_path: str = "data/billing.db"):
        """Initialize payment manager"""
        self.db_path = db_path
        self.current_legal_rate = 3.40  # Taux légal français 2024 (à mettre à jour)
        
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ===== Bank Import Methods =====
    
    def import_ofx(self, file_content: str, account_number: str = "") -> Tuple[int, List[str]]:
        """
        Import OFX bank statements
        Returns: (number_imported, errors)
        """
        try:
            root = ET.fromstring(file_content)
            transactions = []
            errors = []
            batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Parse OFX structure
            for stmttrn in root.iter('STMTTRN'):
                try:
                    transaction = self._parse_ofx_transaction(stmttrn, account_number, batch_id)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    errors.append(f"Error parsing transaction: {str(e)}")
            
            # Save transactions to database
            imported_count = self._save_bank_transactions(transactions)
            
            logger.info(f"Imported {imported_count} transactions from OFX file")
            return imported_count, errors
            
        except ET.ParseError as e:
            logger.error(f"OFX parsing error: {str(e)}")
            return 0, [f"OFX parsing error: {str(e)}"]
        except Exception as e:
            logger.error(f"OFX import error: {str(e)}")
            return 0, [f"Import error: {str(e)}"]
    
    def import_qif(self, file_content: str, account_number: str = "") -> Tuple[int, List[str]]:
        """
        Import QIF bank statements
        Returns: (number_imported, errors)
        """
        try:
            transactions = []
            errors = []
            batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Parse QIF format
            lines = file_content.strip().split('\n')
            current_transaction = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line == '^':  # End of transaction
                    if current_transaction:
                        try:
                            transaction = self._parse_qif_transaction(
                                current_transaction, account_number, batch_id
                            )
                            if transaction:
                                transactions.append(transaction)
                        except Exception as e:
                            errors.append(f"Error parsing QIF transaction: {str(e)}")
                        current_transaction = {}
                else:
                    # Parse QIF field
                    if len(line) > 1:
                        field_type = line[0]
                        field_value = line[1:]
                        current_transaction[field_type] = field_value
            
            # Save transactions to database
            imported_count = self._save_bank_transactions(transactions)
            
            logger.info(f"Imported {imported_count} transactions from QIF file")
            return imported_count, errors
            
        except Exception as e:
            logger.error(f"QIF import error: {str(e)}")
            return 0, [f"Import error: {str(e)}"]
    
    def _parse_ofx_transaction(self, stmttrn_elem, account_number: str, batch_id: str) -> Optional[BankTransaction]:
        """Parse OFX transaction element"""
        try:
            # Extract fields from OFX
            trntype = stmttrn_elem.find('TRNTYPE')
            dtposted = stmttrn_elem.find('DTPOSTED')
            trnamt = stmttrn_elem.find('TRNAMT')
            fitid = stmttrn_elem.find('FITID')
            memo = stmttrn_elem.find('MEMO')
            name = stmttrn_elem.find('NAME')
            
            if not all([dtposted, trnamt]):
                return None
            
            # Parse date (YYYYMMDD format)
            date_str = dtposted.text[:8]
            transaction_date = datetime.strptime(date_str, '%Y%m%d').date()
            
            # Parse amount
            amount = float(trnamt.text)
            
            # Create transaction
            transaction = BankTransaction(
                transaction_date=transaction_date,
                value_date=transaction_date,
                amount=amount,
                description=memo.text if memo is not None else "",
                reference=fitid.text if fitid is not None else "",
                beneficiary_name=name.text if name is not None else "",
                account_number=account_number,
                transaction_id=fitid.text if fitid is not None else "",
                import_batch_id=batch_id,
                status=PaymentStatus.PENDING
            )
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error parsing OFX transaction: {str(e)}")
            return None
    
    def _parse_qif_transaction(self, qif_data: Dict[str, str], account_number: str, batch_id: str) -> Optional[BankTransaction]:
        """Parse QIF transaction data"""
        try:
            # QIF field mappings
            # D = Date, T = Amount, M = Memo, P = Payee, N = Number
            
            if 'D' not in qif_data or 'T' not in qif_data:
                return None
            
            # Parse date (various formats possible)
            date_str = qif_data['D']
            transaction_date = self._parse_qif_date(date_str)
            
            # Parse amount
            amount_str = qif_data['T'].replace(',', '')
            amount = float(amount_str)
            
            # Create transaction
            transaction = BankTransaction(
                transaction_date=transaction_date,
                value_date=transaction_date,
                amount=amount,
                description=qif_data.get('M', ''),
                beneficiary_name=qif_data.get('P', ''),
                reference=qif_data.get('N', ''),
                account_number=account_number,
                transaction_id=f"{batch_id}_{len(qif_data)}",
                import_batch_id=batch_id,
                status=PaymentStatus.PENDING
            )
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error parsing QIF transaction: {str(e)}")
            return None
    
    def _parse_qif_date(self, date_str: str) -> date:
        """Parse QIF date string (various formats)"""
        # Try common QIF date formats
        formats = ['%m/%d/%Y', '%d/%m/%Y', '%m/%d/%y', '%d/%m/%y', '%Y-%m-%d']
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        # Default to today if parsing fails
        logger.warning(f"Could not parse QIF date: {date_str}")
        return date.today()
    
    def _save_bank_transactions(self, transactions: List[BankTransaction]) -> int:
        """Save bank transactions to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            saved_count = 0
            
            for transaction in transactions:
                try:
                    cursor.execute("""
                        INSERT INTO bank_transactions (
                            transaction_date, value_date, amount, description,
                            reference, account_number, beneficiary_name, debtor_name,
                            transaction_id, import_batch_id, status, confidence_score
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        transaction.transaction_date.isoformat() if transaction.transaction_date else None,
                        transaction.value_date.isoformat() if transaction.value_date else None,
                        transaction.amount,
                        transaction.description,
                        transaction.reference,
                        transaction.account_number,
                        transaction.beneficiary_name,
                        transaction.debtor_name,
                        transaction.transaction_id,
                        transaction.import_batch_id,
                        transaction.status.value,
                        transaction.confidence_score
                    ))
                    saved_count += 1
                except sqlite3.IntegrityError as e:
                    logger.warning(f"Duplicate transaction skipped: {transaction.transaction_id}")
                except Exception as e:
                    logger.error(f"Error saving transaction: {str(e)}")
            
            return saved_count
    
    # ===== Automated Payment Matching =====
    
    def match_payments_to_invoices(self, date_tolerance_days: int = 7, amount_tolerance_percent: float = 2.0) -> Dict[str, Any]:
        """
        Automatically match bank transactions to invoices using fuzzy matching
        Returns matching statistics and suggestions
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get unmatched transactions (positive amounts = credits)
            cursor.execute("""
                SELECT * FROM bank_transactions 
                WHERE status = 'pending' AND amount > 0
                ORDER BY transaction_date DESC
            """)
            transactions = [dict(row) for row in cursor.fetchall()]
            
            # Get unpaid invoices
            cursor.execute("""
                SELECT i.*, p.name as participant_name, pr.name as project_name
                FROM invoices i
                JOIN participants p ON i.participant_id = p.id
                JOIN billing_periods bp ON i.billing_period_id = bp.id
                JOIN projects pr ON bp.project_id = pr.id
                WHERE i.status IN ('sent', 'overdue')
                ORDER BY i.due_date
            """)
            invoices = [dict(row) for row in cursor.fetchall()]
            
            matches = []
            auto_matches = []
            suggestions = []
            
            for transaction in transactions:
                best_matches = self._find_best_invoice_matches(
                    transaction, invoices, date_tolerance_days, amount_tolerance_percent
                )
                
                if best_matches:
                    # High confidence auto-match (>90%)
                    if best_matches[0]['confidence'] > 90:
                        match_result = self._apply_payment_match(
                            transaction['id'], best_matches[0]['invoice']['id'], 
                            transaction['amount'], best_matches[0]['confidence']
                        )
                        if match_result:
                            auto_matches.append({
                                'transaction': transaction,
                                'invoice': best_matches[0]['invoice'],
                                'confidence': best_matches[0]['confidence']
                            })
                            matches.append(match_result)
                    else:
                        # Lower confidence - add to suggestions
                        suggestions.append({
                            'transaction': transaction,
                            'possible_matches': best_matches[:3]  # Top 3 matches
                        })
            
            return {
                'total_transactions_processed': len(transactions),
                'auto_matches_count': len(auto_matches),
                'auto_matches': auto_matches,
                'suggestions_count': len(suggestions),
                'suggestions': suggestions,
                'matches_applied': matches
            }
    
    def _find_best_invoice_matches(self, transaction: Dict[str, Any], invoices: List[Dict[str, Any]], 
                                  date_tolerance_days: int, amount_tolerance_percent: float) -> List[Dict[str, Any]]:
        """Find best matching invoices for a transaction"""
        matches = []
        transaction_date = datetime.fromisoformat(transaction['transaction_date']).date()
        transaction_amount = abs(transaction['amount'])
        
        for invoice in invoices:
            confidence = 0.0
            reasons = []
            
            # Amount matching (40% weight)
            invoice_amount = invoice['total_amount']
            amount_diff_percent = abs(transaction_amount - invoice_amount) / invoice_amount * 100
            
            if amount_diff_percent <= amount_tolerance_percent:
                amount_score = max(0, 40 - (amount_diff_percent * 2))
                confidence += amount_score
                reasons.append(f"Amount match: {amount_score:.1f}%")
            
            # Date proximity (20% weight)
            invoice_due_date = datetime.fromisoformat(invoice['due_date']).date()
            date_diff = abs((transaction_date - invoice_due_date).days)
            
            if date_diff <= date_tolerance_days:
                date_score = max(0, 20 - (date_diff * 2))
                confidence += date_score
                reasons.append(f"Date proximity: {date_score:.1f}%")
            
            # Name/description matching (30% weight)
            name_score = self._calculate_name_similarity(transaction, invoice)
            confidence += name_score * 30
            if name_score > 0.3:
                reasons.append(f"Name similarity: {name_score*30:.1f}%")
            
            # Invoice number in transaction description (10% weight)
            if invoice['invoice_number'].lower() in transaction['description'].lower():
                confidence += 10
                reasons.append("Invoice number found: 10%")
            
            # Only consider matches with minimum confidence
            if confidence >= 30:
                matches.append({
                    'invoice': invoice,
                    'confidence': round(confidence, 1),
                    'reasons': reasons,
                    'amount_diff': round(abs(transaction_amount - invoice_amount), 2),
                    'date_diff': date_diff
                })
        
        # Sort by confidence descending
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        return matches
    
    def _calculate_name_similarity(self, transaction: Dict[str, Any], invoice: Dict[str, Any]) -> float:
        """Calculate name similarity between transaction and invoice"""
        # Extract names to compare
        transaction_names = [
            transaction.get('beneficiary_name', ''),
            transaction.get('debtor_name', ''),
            transaction.get('description', '')
        ]
        
        invoice_names = [
            invoice.get('participant_name', ''),
            invoice.get('project_name', '')
        ]
        
        max_similarity = 0.0
        
        for t_name in transaction_names:
            if not t_name:
                continue
            for i_name in invoice_names:
                if not i_name:
                    continue
                
                # Use SequenceMatcher for fuzzy string matching
                similarity = SequenceMatcher(None, t_name.lower(), i_name.lower()).ratio()
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def _apply_payment_match(self, transaction_id: int, invoice_id: int, amount: float, confidence: float) -> Dict[str, Any]:
        """Apply a payment match and update statuses"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Update transaction status
                cursor.execute("""
                    UPDATE bank_transactions 
                    SET status = 'matched', matched_invoice_id = ?, confidence_score = ?
                    WHERE id = ?
                """, (invoice_id, confidence, transaction_id))
                
                # Create payment record
                cursor.execute("""
                    INSERT INTO payments (
                        invoice_id, amount, payment_date, payment_method,
                        transaction_id, notes
                    ) VALUES (?, ?, date('now'), 'virement', ?, ?)
                """, (
                    invoice_id, 
                    amount, 
                    str(transaction_id),
                    f"Auto-matched with confidence {confidence}%"
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
                """, (invoice_id,))
                
                row = cursor.fetchone()
                if row:
                    total_amount = row[0]
                    total_paid = row[1]
                    
                    if total_paid >= total_amount:
                        cursor.execute("""
                            UPDATE invoices 
                            SET status = 'paid', payment_date = date('now')
                            WHERE id = ?
                        """, (invoice_id,))
                
                return {
                    'payment_id': payment_id,
                    'transaction_id': transaction_id,
                    'invoice_id': invoice_id,
                    'amount': amount,
                    'confidence': confidence
                }
                
            except Exception as e:
                logger.error(f"Error applying payment match: {str(e)}")
                conn.rollback()
                return None
    
    # ===== Payment Schedules Management =====
    
    def create_payment_schedule(self, invoice_id: int, installments: int, start_date: date = None) -> List[int]:
        """Create payment schedule for an invoice"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get invoice details
            cursor.execute("SELECT total_amount FROM invoices WHERE id = ?", (invoice_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Invoice {invoice_id} not found")
            
            total_amount = row[0]
            amount_per_installment = total_amount / installments
            
            if start_date is None:
                start_date = date.today()
            
            schedule_ids = []
            
            for i in range(installments):
                due_date = start_date + timedelta(days=30 * i)  # Monthly installments
                
                cursor.execute("""
                    INSERT INTO payment_schedules (
                        invoice_id, installment_number, total_installments,
                        amount, due_date, status
                    ) VALUES (?, ?, ?, ?, ?, 'pending')
                """, (invoice_id, i + 1, installments, amount_per_installment, due_date.isoformat()))
                
                schedule_ids.append(cursor.lastrowid)
            
            return schedule_ids
    
    def get_overdue_installments(self) -> List[Dict[str, Any]]:
        """Get overdue payment installments"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ps.*, i.invoice_number, p.name as participant_name
                FROM payment_schedules ps
                JOIN invoices i ON ps.invoice_id = i.id
                JOIN participants p ON i.participant_id = p.id
                WHERE ps.status = 'pending' AND ps.due_date < date('now')
                ORDER BY ps.due_date
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    # ===== Late Fees Calculation =====
    
    def calculate_late_fees(self, invoice_id: int, calculation_date: date = None) -> Optional[LateFee]:
        """Calculate late fees for an overdue invoice"""
        if calculation_date is None:
            calculation_date = date.today()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT due_date, total_amount, status 
                FROM invoices 
                WHERE id = ? AND status IN ('sent', 'overdue')
            """, (invoice_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            due_date = datetime.fromisoformat(row[0]).date()
            total_amount = row[1]
            
            if calculation_date <= due_date:
                return None  # Not overdue yet
            
            days_late = (calculation_date - due_date).days
            
            # French legal interest rate calculation
            # Intérêts = capital × taux × durée / 365
            daily_rate = self.current_legal_rate / 100 / 365
            calculated_fee = total_amount * daily_rate * days_late
            
            return LateFee(
                invoice_id=invoice_id,
                days_late=days_late,
                base_amount=total_amount,
                legal_rate=self.current_legal_rate,
                calculated_fee=round(calculated_fee, 2),
                applied_date=calculation_date
            )
    
    def apply_late_fee(self, invoice_id: int, fee_amount: float, reason: str = "") -> int:
        """Apply late fee to an invoice"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create late fee record
            cursor.execute("""
                INSERT INTO late_fees (
                    invoice_id, amount, reason, applied_date
                ) VALUES (?, ?, ?, date('now'))
            """, (invoice_id, fee_amount, reason))
            
            fee_id = cursor.lastrowid
            
            # Update invoice total
            cursor.execute("""
                UPDATE invoices 
                SET total_amount = total_amount + ?
                WHERE id = ?
            """, (fee_amount, invoice_id))
            
            return fee_id
    
    # ===== Multi-payment Methods Support =====
    
    def process_payment(self, invoice_id: int, amount: float, payment_method: PaymentMethod, 
                       payment_date: date = None, transaction_id: str = "", notes: str = "") -> int:
        """Process a payment with specified method"""
        if payment_date is None:
            payment_date = date.today()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create payment record
            cursor.execute("""
                INSERT INTO payments (
                    invoice_id, amount, payment_date, payment_method,
                    transaction_id, notes
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                invoice_id,
                amount,
                payment_date.isoformat(),
                payment_method.value,
                transaction_id,
                notes
            ))
            
            payment_id = cursor.lastrowid
            
            # Update invoice status if fully paid
            cursor.execute("""
                SELECT 
                    i.total_amount,
                    COALESCE(SUM(p.amount), 0) as total_paid
                FROM invoices i
                LEFT JOIN payments p ON i.id = p.invoice_id
                WHERE i.id = ?
                GROUP BY i.id
            """, (invoice_id,))
            
            row = cursor.fetchone()
            if row:
                total_amount = row[0]
                total_paid = row[1]
                
                if total_paid >= total_amount:
                    cursor.execute("""
                        UPDATE invoices 
                        SET status = 'paid', payment_date = ?
                        WHERE id = ?
                    """, (payment_date.isoformat(), invoice_id))
                elif total_paid > 0:
                    cursor.execute("""
                        UPDATE invoices 
                        SET status = 'partially_paid'
                        WHERE id = ?
                    """, (invoice_id,))
            
            return payment_id
    
    def get_payment_methods_stats(self) -> Dict[str, Any]:
        """Get payment methods usage statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    payment_method,
                    COUNT(*) as count,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount
                FROM payments
                WHERE payment_method IS NOT NULL
                GROUP BY payment_method
                ORDER BY total_amount DESC
            """)
            
            stats = {}
            for row in cursor.fetchall():
                stats[row[0]] = {
                    'count': row[1],
                    'total_amount': row[2],
                    'average_amount': round(row[3], 2)
                }
            
            return stats
    
    # ===== Utility Methods =====
    
    def get_unmatched_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get unmatched bank transactions"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM bank_transactions 
                WHERE status = 'pending'
                ORDER BY transaction_date DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def manual_match_payment(self, transaction_id: int, invoice_id: int) -> bool:
        """Manually match a transaction to an invoice"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get transaction details
            cursor.execute("""
                SELECT amount, transaction_date FROM bank_transactions 
                WHERE id = ?
            """, (transaction_id,))
            
            row = cursor.fetchone()
            if not row:
                return False
            
            amount = abs(row[0])
            payment_date = row[1]
            
            # Apply the match
            result = self._apply_payment_match(transaction_id, invoice_id, amount, 100.0)
            return result is not None
    
    def get_payment_history(self, invoice_id: int) -> List[Dict[str, Any]]:
        """Get payment history for an invoice"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM payments 
                WHERE invoice_id = ?
                ORDER BY payment_date DESC
            """, (invoice_id,))
            return [dict(row) for row in cursor.fetchall()]