"""Connecteur pour l'intégration avec le module de facturation.

Ce module assure la synchronisation bidirectionnelle entre le module ERP
et le système de facturation existant d'OptimPV.
"""

import logging
import sqlite3
from typing import List, Dict, Optional, Any
from datetime import datetime, date
import json

from ..models.client import Client
from ..services.client_service import ClientService
from ..services.pricing_service import PricingService

logger = logging.getLogger(__name__)


class BillingConnector:
    """Connecteur pour l'intégration avec le module de facturation."""
    
    def __init__(self, billing_db_path: str, erp_client_service: ClientService = None, 
                 erp_pricing_service: PricingService = None):
        """Initialise le connecteur de facturation.
        
        Args:
            billing_db_path: Chemin vers la base billing.db
            erp_client_service: Service ERP clients
            erp_pricing_service: Service ERP prix
        """
        self.billing_db_path = billing_db_path
        self.client_service = erp_client_service or ClientService()
        self.pricing_service = erp_pricing_service or PricingService()
        
    def sync_client_to_billing(self, client: Client) -> bool:
        """Synchronise un client ERP vers le système de facturation.
        
        Args:
            client: Client à synchroniser
            
        Returns:
            True si synchronisation réussie
        """
        try:
            conn = sqlite3.connect(self.billing_db_path)
            cursor = conn.cursor()
            
            # Vérifier si le client existe déjà
            cursor.execute(
                "SELECT id FROM customers WHERE code = ?",
                (client.code_client,)
            )
            existing = cursor.fetchone()
            
            # Récupérer le prix actif
            prix = self.pricing_service.get_active_price(client.id)
            prix_kwh = prix.prix_kwh if prix else None
            
            if existing:
                # Mise à jour
                cursor.execute("""
                    UPDATE customers
                    SET name = ?, 
                        address = ?,
                        postal_code = ?,
                        city = ?,
                        phone = ?,
                        email = ?,
                        siret = ?,
                        active = ?,
                        price_kwh = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE code = ?
                """, (
                    client.nom,
                    client.adresse,
                    client.code_postal,
                    client.ville,
                    client.telephone,
                    client.email,
                    client.siret,
                    client.actif,
                    prix_kwh,
                    client.code_client
                ))
                
                logger.info(f"Client {client.code_client} mis à jour dans billing")
                
            else:
                # Création
                cursor.execute("""
                    INSERT INTO customers (
                        code, name, address, postal_code, city,
                        phone, email, siret, active, price_kwh,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    client.code_client,
                    client.nom,
                    client.adresse,
                    client.code_postal,
                    client.ville,
                    client.telephone,
                    client.email,
                    client.siret,
                    client.actif,
                    prix_kwh
                ))
                
                logger.info(f"Client {client.code_client} créé dans billing")
                
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erreur sync client vers billing: {e}")
            return False
            
    def sync_all_clients_to_billing(self) -> Dict[str, int]:
        """Synchronise tous les clients ERP vers la facturation.
        
        Returns:
            Statistiques de synchronisation
        """
        stats = {
            'total': 0,
            'created': 0,
            'updated': 0,
            'errors': 0
        }
        
        clients = self.client_service.get_all(include_inactive=True)
        stats['total'] = len(clients)
        
        for client in clients:
            try:
                # Vérifier si création ou mise à jour
                conn = sqlite3.connect(self.billing_db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM customers WHERE code = ?",
                    (client.code_client,)
                )
                is_update = cursor.fetchone() is not None
                conn.close()
                
                # Synchroniser
                if self.sync_client_to_billing(client):
                    if is_update:
                        stats['updated'] += 1
                    else:
                        stats['created'] += 1
                else:
                    stats['errors'] += 1
                    
            except Exception as e:
                logger.error(f"Erreur sync client {client.code_client}: {e}")
                stats['errors'] += 1
                
        logger.info(f"Synchronisation terminée: {stats}")
        return stats
        
    def import_clients_from_billing(self) -> Dict[str, int]:
        """Importe les clients depuis la facturation vers l'ERP.
        
        Returns:
            Statistiques d'import
        """
        stats = {
            'total': 0,
            'imported': 0,
            'updated': 0,
            'errors': 0
        }
        
        try:
            conn = sqlite3.connect(self.billing_db_path)
            cursor = conn.cursor()
            
            # Récupérer tous les clients de billing
            cursor.execute("""
                SELECT code, name, address, postal_code, city,
                       phone, email, siret, active, price_kwh
                FROM customers
            """)
            
            billing_clients = cursor.fetchall()
            stats['total'] = len(billing_clients)
            
            for row in billing_clients:
                try:
                    code_client = row[0]
                    
                    # Vérifier si le client existe dans l'ERP
                    existing = self.client_service.get_by_code(code_client)
                    
                    if existing:
                        # Mise à jour si nécessaire
                        needs_update = False
                        
                        if row[1] and existing.nom != row[1]:
                            existing.nom = row[1]
                            needs_update = True
                        if row[2] and existing.adresse != row[2]:
                            existing.adresse = row[2]
                            needs_update = True
                        if row[3] and existing.code_postal != row[3]:
                            existing.code_postal = row[3]
                            needs_update = True
                        if row[4] and existing.ville != row[4]:
                            existing.ville = row[4]
                            needs_update = True
                        if row[5] and existing.telephone != row[5]:
                            existing.telephone = row[5]
                            needs_update = True
                        if row[6] and existing.email != row[6]:
                            existing.email = row[6]
                            needs_update = True
                        if row[7] and existing.siret != row[7]:
                            existing.siret = row[7]
                            needs_update = True
                            
                        if needs_update:
                            self.client_service.update_client(existing)
                            stats['updated'] += 1
                            
                    else:
                        # Créer le client
                        new_client = Client(
                            code_client=code_client,
                            nom=row[1] or f"Client {code_client}",
                            type_client='consommateur',  # Par défaut
                            adresse=row[2],
                            code_postal=row[3],
                            ville=row[4],
                            telephone=row[5],
                            email=row[6],
                            siret=row[7],
                            actif=bool(row[8])
                        )
                        
                        created = self.client_service.create_client(new_client)
                        
                        # Créer le prix si défini
                        if row[9] and row[9] > 0:
                            from ..services.pricing_service import PrixClient
                            
                            prix = PrixClient(
                                id=None,
                                client_id=created.id,
                                prix_kwh=row[9],
                                date_debut=date.today(),
                                date_fin=None,
                                type_tarif='fixe',
                                reference_prix=None,
                                remise_pourcentage=0,
                                formule_calcul=None,
                                notes="Importé depuis facturation",
                                date_creation=None
                            )
                            
                            self.pricing_service.create_prix(prix)
                            
                        stats['imported'] += 1
                        
                except Exception as e:
                    logger.error(f"Erreur import client {code_client}: {e}")
                    stats['errors'] += 1
                    
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur import depuis billing: {e}")
            
        logger.info(f"Import terminé: {stats}")
        return stats
        
    def sync_prices_to_billing(self) -> Dict[str, int]:
        """Synchronise tous les prix ERP vers la facturation.
        
        Returns:
            Statistiques de synchronisation
        """
        stats = {
            'total': 0,
            'synced': 0,
            'errors': 0
        }
        
        clients = self.client_service.get_all()
        stats['total'] = len(clients)
        
        try:
            conn = sqlite3.connect(self.billing_db_path)
            cursor = conn.cursor()
            
            for client in clients:
                try:
                    # Prix actif du client
                    prix = self.pricing_service.get_active_price(client.id)
                    
                    if prix:
                        cursor.execute("""
                            UPDATE customers
                            SET price_kwh = ?,
                                price_type = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE code = ?
                        """, (
                            prix.prix_kwh,
                            prix.type_tarif,
                            client.code_client
                        ))
                        
                        if cursor.rowcount > 0:
                            stats['synced'] += 1
                            
                except Exception as e:
                    logger.error(f"Erreur sync prix client {client.code_client}: {e}")
                    stats['errors'] += 1
                    
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur sync prix vers billing: {e}")
            
        logger.info(f"Sync prix terminée: {stats}")
        return stats
        
    def get_billing_invoices_for_client(self, client_code: str) -> List[Dict[str, Any]]:
        """Récupère les factures d'un client depuis la facturation.
        
        Args:
            client_code: Code du client
            
        Returns:
            Liste des factures
        """
        invoices = []
        
        try:
            conn = sqlite3.connect(self.billing_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    invoice_number,
                    invoice_date,
                    due_date,
                    total_ht,
                    total_ttc,
                    status,
                    payment_date
                FROM invoices
                WHERE customer_code = ?
                ORDER BY invoice_date DESC
            """, (client_code,))
            
            for row in cursor.fetchall():
                invoices.append({
                    'number': row[0],
                    'date': row[1],
                    'due_date': row[2],
                    'total_ht': row[3],
                    'total_ttc': row[4],
                    'status': row[5],
                    'payment_date': row[6]
                })
                
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur récupération factures: {e}")
            
        return invoices
        
    def create_invoice_for_client(
        self, 
        client: Client,
        invoice_data: Dict[str, Any]
    ) -> Optional[str]:
        """Crée une facture pour un client dans le système de facturation.
        
        Args:
            client: Client ERP
            invoice_data: Données de la facture
            
        Returns:
            Numéro de facture créée ou None
        """
        try:
            # S'assurer que le client existe dans billing
            self.sync_client_to_billing(client)
            
            conn = sqlite3.connect(self.billing_db_path)
            cursor = conn.cursor()
            
            # Générer un numéro de facture
            cursor.execute("SELECT MAX(invoice_number) FROM invoices")
            last_number = cursor.fetchone()[0]
            
            if last_number:
                # Extraire le numéro et incrémenter
                last_num = int(last_number.split('-')[-1])
                new_number = f"F{datetime.now().strftime('%Y%m')}-{last_num + 1:04d}"
            else:
                new_number = f"F{datetime.now().strftime('%Y%m')}-0001"
                
            # Créer la facture
            cursor.execute("""
                INSERT INTO invoices (
                    invoice_number,
                    customer_code,
                    invoice_date,
                    due_date,
                    total_ht,
                    total_ttc,
                    status,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'draft', CURRENT_TIMESTAMP)
            """, (
                new_number,
                client.code_client,
                invoice_data.get('date', date.today()),
                invoice_data.get('due_date'),
                invoice_data.get('total_ht', 0),
                invoice_data.get('total_ttc', 0)
            ))
            
            # Ajouter les lignes de facture
            if 'lines' in invoice_data:
                for line in invoice_data['lines']:
                    cursor.execute("""
                        INSERT INTO invoice_lines (
                            invoice_number,
                            description,
                            quantity,
                            unit_price,
                            total_ht
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        new_number,
                        line.get('description'),
                        line.get('quantity', 1),
                        line.get('unit_price', 0),
                        line.get('total', 0)
                    ))
                    
            conn.commit()
            conn.close()
            
            logger.info(f"Facture {new_number} créée pour {client.code_client}")
            return new_number
            
        except Exception as e:
            logger.error(f"Erreur création facture: {e}")
            return None
            
    def get_billing_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques de facturation.
        
        Returns:
            Dictionnaire de statistiques
        """
        stats = {}
        
        try:
            conn = sqlite3.connect(self.billing_db_path)
            cursor = conn.cursor()
            
            # Nombre de clients dans billing
            cursor.execute("SELECT COUNT(*) FROM customers")
            stats['customers_count'] = cursor.fetchone()[0]
            
            # Nombre de factures
            cursor.execute("SELECT COUNT(*) FROM invoices")
            stats['invoices_count'] = cursor.fetchone()[0]
            
            # CA total
            cursor.execute("SELECT SUM(total_ttc) FROM invoices WHERE status = 'paid'")
            stats['total_revenue'] = cursor.fetchone()[0] or 0
            
            # Factures impayées
            cursor.execute("""
                SELECT COUNT(*), SUM(total_ttc)
                FROM invoices
                WHERE status IN ('sent', 'overdue')
            """)
            unpaid = cursor.fetchone()
            stats['unpaid_count'] = unpaid[0] or 0
            stats['unpaid_amount'] = unpaid[1] or 0
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur statistiques billing: {e}")
            
        return stats