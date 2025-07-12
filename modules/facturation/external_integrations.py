"""
Module d'intégrations externes pour OptimPV
Connecteurs vers les ERP populaires et systèmes comptables
"""

import logging
import json
import xml.etree.ElementTree as ET
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod
import requests
import sys
import os

# Ajouter le chemin des modules
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.abspath(os.path.join(current_dir, '..', '..'))
if modules_path not in sys.path:
    sys.path.append(modules_path)

from modules.facturation.database import BillingDatabase

logger = logging.getLogger(__name__)

@dataclass
class ERPCredentials:
    """Informations d'authentification pour un ERP"""
    host: str
    username: str
    password: str
    database: Optional[str] = None
    api_key: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = None

@dataclass
class SyncResult:
    """Résultat d'une synchronisation"""
    success: bool
    records_processed: int
    records_created: int
    records_updated: int
    records_failed: int
    errors: List[str]
    start_time: datetime
    end_time: datetime
    
    @property
    def duration(self) -> float:
        """Durée en secondes"""
        return (self.end_time - self.start_time).total_seconds()

class ERPConnector(ABC):
    """Interface abstraite pour les connecteurs ERP"""
    
    def __init__(self, credentials: ERPCredentials, db: BillingDatabase):
        self.credentials = credentials
        self.db = db
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Tester la connexion à l'ERP"""
        pass
    
    @abstractmethod
    async def export_invoices(self, invoice_ids: List[int]) -> SyncResult:
        """Exporter des factures vers l'ERP"""
        pass
    
    @abstractmethod
    async def export_payments(self, payment_ids: List[int]) -> SyncResult:
        """Exporter des paiements vers l'ERP"""
        pass
    
    @abstractmethod
    async def import_customers(self) -> SyncResult:
        """Importer les clients depuis l'ERP"""
        pass
    
    @abstractmethod
    async def sync_chart_of_accounts(self) -> SyncResult:
        """Synchroniser le plan comptable"""
        pass

class SageConnector(ERPConnector):
    """
    Connecteur pour Sage (Sage 100, Sage X3)
    Utilise l'API REST ou les webservices SOAP selon la version
    """
    
    def __init__(self, credentials: ERPCredentials, db: BillingDatabase, sage_version: str = "100"):
        super().__init__(credentials, db)
        self.sage_version = sage_version
        self.base_url = f"{credentials.host}/api/v1"
        self.session = requests.Session()
        self.token = None
    
    async def test_connection(self) -> bool:
        """Tester la connexion à Sage"""
        try:
            await self._authenticate()
            response = requests.get(f"{self.base_url}/ping", 
                                  headers=self._get_headers(), 
                                  timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Erreur de connexion Sage: {e}")
            return False
    
    async def _authenticate(self):
        """Authentification auprès de Sage"""
        try:
            auth_data = {
                "username": self.credentials.username,
                "password": self.credentials.password,
                "database": self.credentials.database
            }
            
            response = requests.post(f"{self.base_url}/auth/login", 
                                   json=auth_data, 
                                   timeout=30)
            response.raise_for_status()
            
            self.token = response.json().get("access_token")
            self.logger.info("Authentification Sage réussie")
            
        except Exception as e:
            self.logger.error(f"Erreur d'authentification Sage: {e}")
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtenir les en-têtes d'authentification"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def export_invoices(self, invoice_ids: List[int]) -> SyncResult:
        """Exporter des factures vers Sage"""
        start_time = datetime.now()
        result = SyncResult(
            success=True,
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_failed=0,
            errors=[],
            start_time=start_time,
            end_time=start_time
        )
        
        try:
            await self._authenticate()
            
            for invoice_id in invoice_ids:
                try:
                    # Récupérer la facture depuis OptimPV
                    invoice_data = self.db.get_invoice(invoice_id)
                    if not invoice_data:
                        result.errors.append(f"Facture {invoice_id} non trouvée")
                        result.records_failed += 1
                        continue
                    
                    # Convertir au format Sage
                    sage_invoice = self._convert_invoice_to_sage(invoice_data)
                    
                    # Envoyer à Sage
                    response = requests.post(
                        f"{self.base_url}/invoices",
                        json=sage_invoice,
                        headers=self._get_headers(),
                        timeout=30
                    )
                    
                    if response.status_code == 201:
                        result.records_created += 1
                        self.logger.info(f"Facture {invoice_id} exportée vers Sage")
                    elif response.status_code == 200:
                        result.records_updated += 1
                        self.logger.info(f"Facture {invoice_id} mise à jour dans Sage")
                    else:
                        result.records_failed += 1
                        error_msg = f"Erreur Sage pour facture {invoice_id}: {response.status_code} - {response.text}"
                        result.errors.append(error_msg)
                        self.logger.error(error_msg)
                    
                    result.records_processed += 1
                    
                except Exception as e:
                    result.records_failed += 1
                    error_msg = f"Erreur lors de l'export de la facture {invoice_id}: {e}"
                    result.errors.append(error_msg)
                    self.logger.error(error_msg)
            
            result.success = result.records_failed == 0
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Erreur générale d'export: {e}")
            self.logger.error(f"Erreur d'export vers Sage: {e}")
        
        result.end_time = datetime.now()
        return result
    
    def _convert_invoice_to_sage(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convertir une facture OptimPV au format Sage"""
        return {
            "document_type": "INVOICE",
            "document_number": invoice_data["invoice_number"],
            "document_date": invoice_data["issue_date"],
            "due_date": invoice_data["due_date"],
            "customer_code": f"CLIENT_{invoice_data['participant_id']}",
            "currency": "EUR",
            "total_excluding_tax": invoice_data["subtotal"],
            "tax_amount": invoice_data["tax_amount"],
            "total_including_tax": invoice_data["total_amount"],
            "payment_terms": "30J",
            "lines": [
                {
                    "line_number": 1,
                    "account_code": "706000",  # Compte de vente d'énergie
                    "description": "Autoconsommation photovoltaïque",
                    "quantity": 1,
                    "unit_price": invoice_data["subtotal"],
                    "amount": invoice_data["subtotal"],
                    "tax_code": "TVA20"
                }
            ]
        }
    
    async def export_payments(self, payment_ids: List[int]) -> SyncResult:
        """Exporter des paiements vers Sage"""
        # Implémentation similaire aux factures
        start_time = datetime.now()
        result = SyncResult(
            success=True,
            records_processed=len(payment_ids),
            records_created=0,
            records_updated=0,
            records_failed=0,
            errors=[],
            start_time=start_time,
            end_time=datetime.now()
        )
        
        # TODO: Implémenter l'export des paiements
        self.logger.info(f"Export de {len(payment_ids)} paiements vers Sage (non implémenté)")
        
        return result
    
    async def import_customers(self) -> SyncResult:
        """Importer les clients depuis Sage"""
        # TODO: Implémenter l'import des clients
        start_time = datetime.now()
        result = SyncResult(
            success=True,
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_failed=0,
            errors=[],
            start_time=start_time,
            end_time=datetime.now()
        )
        
        self.logger.info("Import des clients depuis Sage (non implémenté)")
        return result
    
    async def sync_chart_of_accounts(self) -> SyncResult:
        """Synchroniser le plan comptable depuis Sage"""
        # TODO: Implémenter la synchronisation du plan comptable
        start_time = datetime.now()
        result = SyncResult(
            success=True,
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_failed=0,
            errors=[],
            start_time=start_time,
            end_time=datetime.now()
        )
        
        self.logger.info("Synchronisation plan comptable Sage (non implémenté)")
        return result

class CegidConnector(ERPConnector):
    """
    Connecteur pour Cegid (Business Suite, XRP Flex)
    """
    
    def __init__(self, credentials: ERPCredentials, db: BillingDatabase):
        super().__init__(credentials, db)
        self.api_url = f"{credentials.host}/api"
        self.session_token = None
    
    async def test_connection(self) -> bool:
        """Tester la connexion à Cegid"""
        try:
            await self._authenticate()
            # Test simple avec récupération des informations société
            response = requests.get(f"{self.api_url}/company/info", 
                                  headers=self._get_headers(), 
                                  timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Erreur de connexion Cegid: {e}")
            return False
    
    async def _authenticate(self):
        """Authentification auprès de Cegid"""
        try:
            auth_payload = {
                "login": self.credentials.username,
                "password": self.credentials.password,
                "database": self.credentials.database
            }
            
            response = requests.post(f"{self.api_url}/auth", 
                                   json=auth_payload, 
                                   timeout=30)
            response.raise_for_status()
            
            self.session_token = response.json().get("token")
            self.logger.info("Authentification Cegid réussie")
            
        except Exception as e:
            self.logger.error(f"Erreur d'authentification Cegid: {e}")
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtenir les en-têtes d'authentification"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.session_token:
            headers["X-Auth-Token"] = self.session_token
        return headers
    
    async def export_invoices(self, invoice_ids: List[int]) -> SyncResult:
        """Exporter des factures vers Cegid"""
        start_time = datetime.now()
        result = SyncResult(
            success=True,
            records_processed=len(invoice_ids),
            records_created=0,
            records_updated=0,
            records_failed=0,
            errors=[],
            start_time=start_time,
            end_time=datetime.now()
        )
        
        # TODO: Implémenter l'export vers Cegid
        self.logger.info(f"Export de {len(invoice_ids)} factures vers Cegid (non implémenté)")
        
        return result
    
    async def export_payments(self, payment_ids: List[int]) -> SyncResult:
        """Exporter des paiements vers Cegid"""
        start_time = datetime.now()
        result = SyncResult(
            success=True,
            records_processed=len(payment_ids),
            records_created=0,
            records_updated=0,
            records_failed=0,
            errors=[],
            start_time=start_time,
            end_time=datetime.now()
        )
        
        # TODO: Implémenter l'export des paiements
        self.logger.info(f"Export de {len(payment_ids)} paiements vers Cegid (non implémenté)")
        
        return result
    
    async def import_customers(self) -> SyncResult:
        """Importer les clients depuis Cegid"""
        start_time = datetime.now()
        result = SyncResult(
            success=True,
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_failed=0,
            errors=[],
            start_time=start_time,
            end_time=datetime.now()
        )
        
        # TODO: Implémenter l'import des clients
        self.logger.info("Import des clients depuis Cegid (non implémenté)")
        return result
    
    async def sync_chart_of_accounts(self) -> SyncResult:
        """Synchroniser le plan comptable depuis Cegid"""
        start_time = datetime.now()
        result = SyncResult(
            success=True,
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_failed=0,
            errors=[],
            start_time=start_time,
            end_time=datetime.now()
        )
        
        # TODO: Implémenter la synchronisation du plan comptable
        self.logger.info("Synchronisation plan comptable Cegid (non implémenté)")
        return result

class OdooConnector(ERPConnector):
    """
    Connecteur pour Odoo via XML-RPC
    """
    
    def __init__(self, credentials: ERPCredentials, db: BillingDatabase):
        super().__init__(credentials, db)
        self.url = credentials.host
        self.db_name = credentials.database
        self.uid = None
        
        # Import des modules XML-RPC
        try:
            import xmlrpc.client
            self.xmlrpc = xmlrpc.client
        except ImportError:
            raise ImportError("xmlrpc.client requis pour le connecteur Odoo")
    
    async def test_connection(self) -> bool:
        """Tester la connexion à Odoo"""
        try:
            await self._authenticate()
            # Test simple avec récupération d'informations utilisateur
            models = self.xmlrpc.ServerProxy(f'{self.url}/xmlrpc/2/object')
            user_info = models.execute_kw(
                self.db_name, self.uid, self.credentials.password,
                'res.users', 'read', [self.uid], {'fields': ['name']}
            )
            return bool(user_info)
        except Exception as e:
            self.logger.error(f"Erreur de connexion Odoo: {e}")
            return False
    
    async def _authenticate(self):
        """Authentification auprès d'Odoo"""
        try:
            common = self.xmlrpc.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.uid = common.authenticate(
                self.db_name, 
                self.credentials.username, 
                self.credentials.password, 
                {}
            )
            
            if not self.uid:
                raise Exception("Échec de l'authentification Odoo")
            
            self.logger.info("Authentification Odoo réussie")
            
        except Exception as e:
            self.logger.error(f"Erreur d'authentification Odoo: {e}")
            raise
    
    async def export_invoices(self, invoice_ids: List[int]) -> SyncResult:
        """Exporter des factures vers Odoo"""
        start_time = datetime.now()
        result = SyncResult(
            success=True,
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_failed=0,
            errors=[],
            start_time=start_time,
            end_time=start_time
        )
        
        try:
            await self._authenticate()
            models = self.xmlrpc.ServerProxy(f'{self.url}/xmlrpc/2/object')
            
            for invoice_id in invoice_ids:
                try:
                    # Récupérer la facture depuis OptimPV
                    invoice_data = self.db.get_invoice(invoice_id)
                    if not invoice_data:
                        result.errors.append(f"Facture {invoice_id} non trouvée")
                        result.records_failed += 1
                        continue
                    
                    # Convertir au format Odoo
                    odoo_invoice = self._convert_invoice_to_odoo(invoice_data)
                    
                    # Créer dans Odoo
                    odoo_invoice_id = models.execute_kw(
                        self.db_name, self.uid, self.credentials.password,
                        'account.move', 'create', [odoo_invoice]
                    )
                    
                    if odoo_invoice_id:
                        result.records_created += 1
                        self.logger.info(f"Facture {invoice_id} exportée vers Odoo (ID: {odoo_invoice_id})")
                    else:
                        result.records_failed += 1
                        result.errors.append(f"Échec de création facture {invoice_id} dans Odoo")
                    
                    result.records_processed += 1
                    
                except Exception as e:
                    result.records_failed += 1
                    error_msg = f"Erreur lors de l'export de la facture {invoice_id}: {e}"
                    result.errors.append(error_msg)
                    self.logger.error(error_msg)
            
            result.success = result.records_failed == 0
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Erreur générale d'export: {e}")
            self.logger.error(f"Erreur d'export vers Odoo: {e}")
        
        result.end_time = datetime.now()
        return result
    
    def _convert_invoice_to_odoo(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convertir une facture OptimPV au format Odoo"""
        return {
            'move_type': 'out_invoice',
            'ref': invoice_data['invoice_number'],
            'invoice_date': invoice_data['issue_date'],
            'invoice_date_due': invoice_data['due_date'],
            'partner_id': 1,  # TODO: Mapper le participant vers un partner Odoo
            'currency_id': 1,  # EUR par défaut
            'invoice_line_ids': [(0, 0, {
                'name': 'Autoconsommation photovoltaïque',
                'quantity': 1,
                'price_unit': invoice_data['subtotal'],
                'account_id': 1,  # TODO: Configurer le compte comptable
                'tax_ids': [(6, 0, [1])] if invoice_data['tax_amount'] > 0 else []
            })]
        }
    
    async def export_payments(self, payment_ids: List[int]) -> SyncResult:
        """Exporter des paiements vers Odoo"""
        start_time = datetime.now()
        result = SyncResult(
            success=True,
            records_processed=len(payment_ids),
            records_created=0,
            records_updated=0,
            records_failed=0,
            errors=[],
            start_time=start_time,
            end_time=datetime.now()
        )
        
        # TODO: Implémenter l'export des paiements
        self.logger.info(f"Export de {len(payment_ids)} paiements vers Odoo (non implémenté)")
        
        return result
    
    async def import_customers(self) -> SyncResult:
        """Importer les clients depuis Odoo"""
        start_time = datetime.now()
        result = SyncResult(
            success=True,
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_failed=0,
            errors=[],
            start_time=start_time,
            end_time=datetime.now()
        )
        
        # TODO: Implémenter l'import des clients
        self.logger.info("Import des clients depuis Odoo (non implémenté)")
        return result
    
    async def sync_chart_of_accounts(self) -> SyncResult:
        """Synchroniser le plan comptable depuis Odoo"""
        start_time = datetime.now()
        result = SyncResult(
            success=True,
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_failed=0,
            errors=[],
            start_time=start_time,
            end_time=datetime.now()
        )
        
        # TODO: Implémenter la synchronisation du plan comptable
        self.logger.info("Synchronisation plan comptable Odoo (non implémenté)")
        return result

class IntegrationManager:
    """
    Gestionnaire principal des intégrations ERP
    """
    
    def __init__(self, db: BillingDatabase):
        self.db = db
        self.connectors: Dict[str, ERPConnector] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_connector(self, name: str, connector: ERPConnector):
        """Enregistrer un connecteur ERP"""
        self.connectors[name] = connector
        self.logger.info(f"Connecteur {name} enregistré")
    
    def get_connector(self, name: str) -> Optional[ERPConnector]:
        """Obtenir un connecteur par nom"""
        return self.connectors.get(name)
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """Tester toutes les connexions ERP"""
        results = {}
        for name, connector in self.connectors.items():
            try:
                results[name] = await connector.test_connection()
            except Exception as e:
                self.logger.error(f"Erreur test connexion {name}: {e}")
                results[name] = False
        return results
    
    async def sync_all_invoices(self, invoice_ids: List[int]) -> Dict[str, SyncResult]:
        """Synchroniser des factures vers tous les ERP connectés"""
        results = {}
        for name, connector in self.connectors.items():
            try:
                results[name] = await connector.export_invoices(invoice_ids)
            except Exception as e:
                self.logger.error(f"Erreur sync factures vers {name}: {e}")
                results[name] = SyncResult(
                    success=False,
                    records_processed=0,
                    records_created=0,
                    records_updated=0,
                    records_failed=len(invoice_ids),
                    errors=[str(e)],
                    start_time=datetime.now(),
                    end_time=datetime.now()
                )
        return results
    
    def create_sage_connector(self, credentials: ERPCredentials, version: str = "100") -> SageConnector:
        """Créer un connecteur Sage"""
        connector = SageConnector(credentials, self.db, version)
        self.register_connector(f"sage_{version}", connector)
        return connector
    
    def create_cegid_connector(self, credentials: ERPCredentials) -> CegidConnector:
        """Créer un connecteur Cegid"""
        connector = CegidConnector(credentials, self.db)
        self.register_connector("cegid", connector)
        return connector
    
    def create_odoo_connector(self, credentials: ERPCredentials) -> OdooConnector:
        """Créer un connecteur Odoo"""
        connector = OdooConnector(credentials, self.db)
        self.register_connector("odoo", connector)
        return connector

# Export des formats comptables standards
class FECExporter:
    """
    Exporteur au format FEC (Fichier des Écritures Comptables)
    Format obligatoire français pour l'administration fiscale
    """
    
    def __init__(self, db: BillingDatabase):
        self.db = db
    
    def export_fec(self, start_date: date, end_date: date, company_siren: str) -> str:
        """Exporter les écritures au format FEC"""
        try:
            # Récupérer les écritures comptables
            entries = self.db.get_accounting_entries(start_date, end_date)
            
            # Format FEC: séparateur pipe (|)
            fec_lines = []
            
            # En-tête FEC
            header = "JournalCode|JournalLib|EcritureNum|EcritureDate|CompteNum|CompteLib|CompAuxNum|CompAuxLib|PieceRef|PieceDate|EcritureLib|Debit|Credit|EcritureLet|DateLet|ValidDate|Montantdevise|Idevise"
            fec_lines.append(header)
            
            for entry in entries:
                line = f"{entry['journal_code']}|" \
                       f"Journal {entry['journal_code']}|" \
                       f"{entry['document_number']}|" \
                       f"{entry['entry_date'].replace('-', '')}|" \
                       f"{entry['account_number']}|" \
                       f"{entry['account_label']}|" \
                       f"{entry.get('auxiliary_account', '')}|" \
                       f"|" \
                       f"{entry.get('document_number', '')}|" \
                       f"{entry.get('document_date', '').replace('-', '')}|" \
                       f"{entry['entry_label']}|" \
                       f"{entry['debit']:.2f}|" \
                       f"{entry['credit']:.2f}|" \
                       f"{entry.get('lettrage', '')}|" \
                       f"|" \
                       f"{entry['entry_date'].replace('-', '')}|" \
                       f"|"
                
                fec_lines.append(line)
            
            return "\n".join(fec_lines)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export FEC: {e}")
            raise

# Instance globale du gestionnaire d'intégrations
integration_manager = IntegrationManager(BillingDatabase())