"""
Tests pour le système de gestion avancée des paiements OptimPV
Tests unitaires et d'intégration pour payment_manager, dunning et payment_dashboard
"""

import unittest
import sqlite3
import tempfile
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
import json

# Import des modules à tester
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules', 'facturation'))

try:
    from payment_manager import PaymentManager, PaymentMethod, PaymentStatus, BankTransaction, PaymentSchedule
    from dunning import DunningManager, DunningLevel, DunningAction
    from payment_dashboard import PaymentDashboard, DSO, AgingBucket, CollectionMetrics
    from database import BillingDatabase
    IMPORTS_OK = True
except ImportError as e:
    print(f"Erreur d'import: {e}")
    IMPORTS_OK = False

class TestPaymentManager(unittest.TestCase):
    """Tests pour PaymentManager"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        if not IMPORTS_OK:
            self.skipTest("Modules non importables")
        
        # Base de données temporaire
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Initialiser la base de données
        self.billing_db = BillingDatabase(self.db_path)
        self.payment_mgr = PaymentManager(self.db_path)
        
        # Créer des données de test
        self._create_test_data()
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        if hasattr(self, 'temp_db'):
            try:
                os.unlink(self.db_path)
            except:
                pass
    
    def _create_test_data(self):
        """Créer des données de test"""
        # Projet de test
        project_data = {
            'name': 'Projet Test Solar',
            'client_name': 'Client Test',
            'client_email': 'test@example.com',
            'total_capacity_kwc': 100.0,
            'annual_production_kwh': 120000.0
        }
        self.project_id = self.billing_db.create_project(project_data)
        
        # Participant de test
        participant_data = {
            'project_id': self.project_id,
            'name': 'Participant Test',
            'type': 'consumer',
            'contact_email': 'participant@example.com',
            'allocation_percentage': 50.0
        }
        self.participant_id = self.billing_db.create_participant(participant_data)
        
        # Période de facturation
        billing_data = {
            'project_id': self.project_id,
            'period_name': 'Q1 2024',
            'start_date': date(2024, 1, 1),
            'end_date': date(2024, 3, 31),
            'total_amount': 1500.0,
            'payment_due_date': date(2024, 4, 15)
        }
        self.billing_period_id = self.billing_db.create_billing_period(billing_data)
        
        # Facture de test
        invoice_data = {
            'billing_period_id': self.billing_period_id,
            'participant_id': self.participant_id,
            'invoice_number': 'INV-2024-001',
            'issue_date': date(2024, 3, 31),
            'due_date': date(2024, 4, 30),
            'subtotal': 1000.0,
            'tax_rate': 0.20,
            'tax_amount': 200.0,
            'total_amount': 1200.0,
            'status': 'sent'
        }
        self.invoice_id = self.billing_db.create_invoice(invoice_data)
    
    def test_import_ofx(self):
        """Test import OFX"""
        ofx_content = """<?xml version="1.0" encoding="UTF-8"?>
        <OFX>
            <BANKMSGSRSV1>
                <STMTTRNRS>
                    <STMTRS>
                        <BANKTRANLIST>
                            <STMTTRN>
                                <TRNTYPE>CREDIT</TRNTYPE>
                                <DTPOSTED>20241201</DTPOSTED>
                                <TRNAMT>1200.00</TRNAMT>
                                <FITID>TXN001</FITID>
                                <NAME>CLIENT TEST</NAME>
                                <MEMO>Paiement facture INV-2024-001</MEMO>
                            </STMTTRN>
                        </BANKTRANLIST>
                    </STMTRS>
                </STMTTRNRS>
            </BANKMSGSRSV1>
        </OFX>"""
        
        imported_count, errors = self.payment_mgr.import_ofx(ofx_content, "FR76123456789")
        
        self.assertEqual(imported_count, 1)
        self.assertEqual(len(errors), 0)
        
        # Vérifier que la transaction est bien importée
        transactions = self.payment_mgr.get_unmatched_transactions()
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]['amount'], 1200.0)
    
    def test_import_qif(self):
        """Test import QIF"""
        qif_content = """D12/01/2024
T1200.00
PCLIENT TEST
MPaiement facture INV-2024-001
^
D12/02/2024
T500.00
PAUTRE CLIENT
MPaiement partiel
^"""
        
        imported_count, errors = self.payment_mgr.import_qif(qif_content, "FR76123456789")
        
        self.assertEqual(imported_count, 2)
        self.assertEqual(len(errors), 0)
        
        transactions = self.payment_mgr.get_unmatched_transactions()
        self.assertEqual(len(transactions), 2)
    
    def test_automatic_matching(self):
        """Test rapprochement automatique"""
        # Importer une transaction qui correspond à notre facture
        ofx_content = """<?xml version="1.0" encoding="UTF-8"?>
        <OFX>
            <BANKMSGSRSV1>
                <STMTTRNRS>
                    <STMTRS>
                        <BANKTRANLIST>
                            <STMTTRN>
                                <TRNTYPE>CREDIT</TRNTYPE>
                                <DTPOSTED>20240430</DTPOSTED>
                                <TRNAMT>1200.00</TRNAMT>
                                <FITID>MATCH001</FITID>
                                <NAME>PARTICIPANT TEST</NAME>
                                <MEMO>Virement INV-2024-001</MEMO>
                            </STMTTRN>
                        </BANKTRANLIST>
                    </STMTRS>
                </STMTTRNRS>
            </BANKMSGSRSV1>
        </OFX>"""
        
        self.payment_mgr.import_ofx(ofx_content, "FR76123456789")
        
        # Lancer le rapprochement automatique
        results = self.payment_mgr.match_payments_to_invoices()
        
        # Devrait avoir au moins une suggestion ou un match automatique
        self.assertGreaterEqual(
            results['auto_matches_count'] + results['suggestions_count'], 
            1
        )
    
    def test_payment_processing(self):
        """Test traitement des paiements"""
        payment_id = self.payment_mgr.process_payment(
            invoice_id=self.invoice_id,
            amount=1200.0,
            payment_method=PaymentMethod.VIREMENT,
            payment_date=date.today(),
            transaction_id="VIR001",
            notes="Paiement test"
        )
        
        self.assertIsNotNone(payment_id)
        
        # Vérifier que la facture est marquée comme payée
        invoice = self.billing_db.get_invoice(self.invoice_id)
        self.assertEqual(invoice['status'], 'paid')
    
    def test_payment_schedule(self):
        """Test création d'échéancier"""
        schedule_ids = self.payment_mgr.create_payment_schedule(
            invoice_id=self.invoice_id,
            installments=3,
            start_date=date.today()
        )
        
        self.assertEqual(len(schedule_ids), 3)
        
        # Vérifier les montants des échéances
        with self.payment_mgr.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT amount FROM payment_schedules WHERE invoice_id = ?", (self.invoice_id,))
            amounts = [row[0] for row in cursor.fetchall()]
        
        # Chaque échéance devrait être de 400€ (1200/3)
        for amount in amounts:
            self.assertAlmostEqual(amount, 400.0, places=2)
    
    def test_late_fees_calculation(self):
        """Test calcul des pénalités de retard"""
        # Modifier la date d'échéance pour qu'elle soit dépassée
        with self.payment_mgr.get_connection() as conn:
            cursor = conn.cursor()
            old_due_date = date.today() - timedelta(days=30)
            cursor.execute("UPDATE invoices SET due_date = ? WHERE id = ?", 
                         (old_due_date.isoformat(), self.invoice_id))
        
        late_fee = self.payment_mgr.calculate_late_fees(self.invoice_id)
        
        self.assertIsNotNone(late_fee)
        self.assertEqual(late_fee.days_late, 30)
        self.assertGreater(late_fee.calculated_fee, 0)
        self.assertEqual(late_fee.legal_rate, 3.40)  # Taux légal français


class TestDunningManager(unittest.TestCase):
    """Tests pour DunningManager"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        if not IMPORTS_OK:
            self.skipTest("Modules non importables")
        
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        self.billing_db = BillingDatabase(self.db_path)
        self.dunning_mgr = DunningManager(self.db_path)
        
        self._create_test_data()
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        if hasattr(self, 'temp_db'):
            try:
                os.unlink(self.db_path)
            except:
                pass
    
    def _create_test_data(self):
        """Créer des données de test pour les relances"""
        # Même setup que PaymentManager
        project_data = {
            'name': 'Projet Dunning Test',
            'client_name': 'Client Dunning',
            'client_email': 'dunning@example.com'
        }
        self.project_id = self.billing_db.create_project(project_data)
        
        participant_data = {
            'project_id': self.project_id,
            'name': 'Participant Dunning',
            'type': 'consumer',
            'contact_email': 'participant.dunning@example.com'
        }
        self.participant_id = self.billing_db.create_participant(participant_data)
        
        billing_data = {
            'project_id': self.project_id,
            'period_name': 'Dunning Q1',
            'start_date': date(2024, 1, 1),
            'end_date': date(2024, 3, 31)
        }
        self.billing_period_id = self.billing_db.create_billing_period(billing_data)
        
        # Facture en retard
        overdue_date = date.today() - timedelta(days=15)
        invoice_data = {
            'billing_period_id': self.billing_period_id,
            'participant_id': self.participant_id,
            'invoice_number': 'DUN-2024-001',
            'issue_date': overdue_date - timedelta(days=30),
            'due_date': overdue_date,
            'subtotal': 800.0,
            'tax_amount': 160.0,
            'total_amount': 960.0,
            'status': 'overdue'
        }
        self.invoice_id = self.billing_db.create_invoice(invoice_data)
    
    def test_get_overdue_invoices(self):
        """Test récupération des factures en retard"""
        overdue_invoices = self.dunning_mgr.get_overdue_invoices()
        
        self.assertGreaterEqual(len(overdue_invoices), 1)
        
        # Vérifier qu'on trouve notre facture test
        found = False
        for invoice in overdue_invoices:
            if invoice['invoice_number'] == 'DUN-2024-001':
                found = True
                self.assertGreater(invoice['days_overdue'], 0)
        
        self.assertTrue(found, "Facture en retard non trouvée")
    
    def test_dunning_cycle_dry_run(self):
        """Test cycle de relance en mode simulation"""
        results = self.dunning_mgr.process_dunning_cycle(dry_run=True)
        
        self.assertGreaterEqual(results['processed_count'], 0)
        self.assertIsInstance(results['actions'], list)
        self.assertIsInstance(results['errors'], list)
    
    def test_manual_dunning(self):
        """Test relance manuelle"""
        success = self.dunning_mgr.send_manual_dunning(
            invoice_id=self.invoice_id,
            level=DunningLevel.FRIENDLY_REMINDER,
            custom_message="Test de relance manuelle"
        )
        
        # Devrait réussir même sans SMTP configuré (pas d'email envoyé)
        self.assertTrue(success)
        
        # Vérifier l'historique
        history = self.dunning_mgr.get_dunning_history(self.invoice_id)
        self.assertGreaterEqual(len(history), 1)
    
    def test_dunning_statistics(self):
        """Test statistiques des relances"""
        stats = self.dunning_mgr.get_dunning_statistics()
        
        self.assertIn('overdue_invoices_count', stats)
        self.assertIn('overdue_total_amount', stats)
        self.assertIn('dunning_actions_by_level', stats)
        self.assertIn('success_rate_percent', stats)


class TestPaymentDashboard(unittest.TestCase):
    """Tests pour PaymentDashboard"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        if not IMPORTS_OK:
            self.skipTest("Modules non importables")
        
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        self.billing_db = BillingDatabase(self.db_path)
        self.dashboard = PaymentDashboard(self.db_path)
        
        self._create_test_data()
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        if hasattr(self, 'temp_db'):
            try:
                os.unlink(self.db_path)
            except:
                pass
    
    def _create_test_data(self):
        """Créer des données de test pour le dashboard"""
        # Créer plusieurs factures avec différents statuts
        project_data = {
            'name': 'Projet Dashboard Test',
            'client_name': 'Client Dashboard'
        }
        project_id = self.billing_db.create_project(project_data)
        
        participant_data = {
            'project_id': project_id,
            'name': 'Participant Dashboard',
            'type': 'consumer'
        }
        participant_id = self.billing_db.create_participant(participant_data)
        
        billing_data = {
            'project_id': project_id,
            'period_name': 'Dashboard Q1',
            'start_date': date(2024, 1, 1),
            'end_date': date(2024, 3, 31)
        }
        billing_period_id = self.billing_db.create_billing_period(billing_data)
        
        # Factures de test avec différents âges
        test_invoices = [
            {
                'invoice_number': 'DASH-001',
                'due_date': date.today() - timedelta(days=15),  # 15 jours de retard
                'total_amount': 1000.0,
                'status': 'overdue'
            },
            {
                'invoice_number': 'DASH-002',
                'due_date': date.today() - timedelta(days=45),  # 45 jours de retard
                'total_amount': 1500.0,
                'status': 'overdue'
            },
            {
                'invoice_number': 'DASH-003',
                'due_date': date.today() + timedelta(days=15),  # Pas encore due
                'total_amount': 800.0,
                'status': 'sent'
            }
        ]
        
        for inv_data in test_invoices:
            invoice_data = {
                'billing_period_id': billing_period_id,
                'participant_id': participant_id,
                'invoice_number': inv_data['invoice_number'],
                'issue_date': inv_data['due_date'] - timedelta(days=30),
                'due_date': inv_data['due_date'],
                'subtotal': inv_data['total_amount'] * 0.8,
                'tax_amount': inv_data['total_amount'] * 0.2,
                'total_amount': inv_data['total_amount'],
                'status': inv_data['status']
            }
            self.billing_db.create_invoice(invoice_data)
    
    def test_dso_calculation(self):
        """Test calcul du DSO"""
        dso = self.dashboard.calculate_dso()
        
        self.assertIsInstance(dso, DSO)
        self.assertGreaterEqual(dso.dso_days, 0)
        self.assertGreaterEqual(dso.total_receivables, 0)
    
    def test_aging_buckets(self):
        """Test analyse de l'aging"""
        aging_buckets = self.dashboard.calculate_aging_buckets()
        
        self.assertIsInstance(aging_buckets, list)
        self.assertGreater(len(aging_buckets), 0)
        
        # Vérifier la structure des buckets
        for bucket in aging_buckets:
            self.assertIsInstance(bucket, AgingBucket)
            self.assertGreaterEqual(bucket.percentage, 0)
            self.assertLessEqual(bucket.percentage, 100)
    
    def test_collection_metrics(self):
        """Test métriques de collection"""
        metrics = self.dashboard.calculate_collection_rate()
        
        self.assertIsInstance(metrics, CollectionMetrics)
        self.assertGreaterEqual(metrics.collection_rate, 0)
        self.assertLessEqual(metrics.collection_rate, 100)
    
    def test_cash_flow_forecast(self):
        """Test prévisions de trésorerie"""
        forecast = self.dashboard.generate_cash_flow_forecast(30)
        
        self.assertIsInstance(forecast, list)
        # Peut être vide si pas de prévisions
        
        weekly_summary = self.dashboard.get_weekly_cash_flow_summary(4)
        self.assertIsInstance(weekly_summary, list)
        self.assertEqual(len(weekly_summary), 4)
    
    def test_payment_kpis(self):
        """Test KPIs globaux"""
        kpis = self.dashboard.get_payment_kpis()
        
        self.assertIn('dso_days', kpis)
        self.assertIn('current_receivables', kpis)
        self.assertIn('overdue_amount', kpis)
        self.assertIn('collection_rate', kpis)
        self.assertIn('aging_buckets', kpis)
    
    def test_export_functions(self):
        """Test fonctions d'export"""
        aging_report = self.dashboard.export_aging_report()
        
        self.assertIn('report_date', aging_report)
        self.assertIn('total_receivables', aging_report)
        self.assertIn('buckets', aging_report)
        
        dso_history = self.dashboard.export_dso_history(6)
        self.assertIsInstance(dso_history, list)


class TestIntegration(unittest.TestCase):
    """Tests d'intégration du système complet"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        if not IMPORTS_OK:
            self.skipTest("Modules non importables")
        
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        self.billing_db = BillingDatabase(self.db_path)
        self.payment_mgr = PaymentManager(self.db_path)
        self.dunning_mgr = DunningManager(self.db_path)
        self.dashboard = PaymentDashboard(self.db_path)
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        if hasattr(self, 'temp_db'):
            try:
                os.unlink(self.db_path)
            except:
                pass
    
    def test_full_payment_workflow(self):
        """Test workflow complet de paiement"""
        # 1. Créer les données de base
        project_data = {'name': 'Projet Intégration', 'client_name': 'Client Intégration'}
        project_id = self.billing_db.create_project(project_data)
        
        participant_data = {
            'project_id': project_id,
            'name': 'Participant Intégration',
            'type': 'consumer',
            'contact_email': 'integration@example.com'
        }
        participant_id = self.billing_db.create_participant(participant_data)
        
        billing_data = {
            'project_id': project_id,
            'period_name': 'Integration Q1',
            'start_date': date(2024, 1, 1),
            'end_date': date(2024, 3, 31)
        }
        billing_period_id = self.billing_db.create_billing_period(billing_data)
        
        # 2. Créer une facture
        invoice_data = {
            'billing_period_id': billing_period_id,
            'participant_id': participant_id,
            'invoice_number': 'INT-2024-001',
            'issue_date': date(2024, 3, 31),
            'due_date': date(2024, 4, 30),
            'subtotal': 1000.0,
            'tax_amount': 200.0,
            'total_amount': 1200.0,
            'status': 'sent'
        }
        invoice_id = self.billing_db.create_invoice(invoice_data)
        
        # 3. Importer une transaction bancaire
        ofx_content = """<?xml version="1.0" encoding="UTF-8"?>
        <OFX>
            <BANKMSGSRSV1>
                <STMTTRNRS>
                    <STMTRS>
                        <BANKTRANLIST>
                            <STMTTRN>
                                <TRNTYPE>CREDIT</TRNTYPE>
                                <DTPOSTED>20240430</DTPOSTED>
                                <TRNAMT>1200.00</TRNAMT>
                                <FITID>INT001</FITID>
                                <NAME>PARTICIPANT INTEGRATION</NAME>
                                <MEMO>Paiement INT-2024-001</MEMO>
                            </STMTTRN>
                        </BANKTRANLIST>
                    </STMTRS>
                </STMTTRNRS>
            </BANKMSGSRSV1>
        </OFX>"""
        
        imported_count, errors = self.payment_mgr.import_ofx(ofx_content)
        self.assertEqual(imported_count, 1)
        
        # 4. Rapprochement automatique
        results = self.payment_mgr.match_payments_to_invoices()
        
        # 5. Vérifier les KPIs
        kpis = self.dashboard.get_payment_kpis()
        self.assertIsInstance(kpis, dict)
        
        # 6. Test du système de relance (si la facture était impayée)
        stats = self.dunning_mgr.get_dunning_statistics()
        self.assertIsInstance(stats, dict)


def run_payment_tests():
    """Lancer tous les tests de paiement"""
    print("=== Tests du Système de Gestion Avancée des Paiements OptimPV ===\n")
    
    if not IMPORTS_OK:
        print("❌ ÉCHEC: Impossible d'importer les modules de paiement")
        print("Vérifiez que les fichiers suivants existent:")
        print("- modules/facturation/payment_manager.py")
        print("- modules/facturation/dunning.py") 
        print("- modules/facturation/payment_dashboard.py")
        return False
    
    # Créer la suite de tests
    suite = unittest.TestSuite()
    
    # Ajouter les tests
    suite.addTest(unittest.makeSuite(TestPaymentManager))
    suite.addTest(unittest.makeSuite(TestDunningManager))
    suite.addTest(unittest.makeSuite(TestPaymentDashboard))
    suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Lancer les tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Résumé
    print(f"\n=== RÉSUMÉ DES TESTS ===")
    print(f"Tests exécutés: {result.testsRun}")
    print(f"Échecs: {len(result.failures)}")
    print(f"Erreurs: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ ÉCHECS:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n❌ ERREURS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n✅ TOUS LES TESTS SONT PASSÉS!")
        print("Le système de gestion avancée des paiements fonctionne correctement.")
    else:
        print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("Des corrections sont nécessaires avant la mise en production.")
    
    return success


if __name__ == "__main__":
    run_payment_tests()