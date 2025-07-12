"""
Example usage of the Advanced Payment Management System for OptimPV
This file demonstrates how to use the payment management features
"""

from datetime import date, timedelta
from payment_manager import PaymentManager, PaymentMethod, PaymentStatus
from dunning import DunningManager, DunningLevel
from payment_dashboard import PaymentDashboard
import json

def demo_payment_management():
    """Demonstrate the payment management system"""
    
    # Initialize managers
    payment_mgr = PaymentManager()
    dunning_mgr = DunningManager()
    dashboard = PaymentDashboard()
    
    print("=== OptimPV Advanced Payment Management Demo ===\n")
    
    # 1. Import bank transactions
    print("1. Importing bank transactions...")
    
    # Example OFX content (simplified)
    ofx_content = """<?xml version="1.0" encoding="UTF-8"?>
    <OFX>
        <BANKMSGSRSV1>
            <STMTTRNRS>
                <STMTRS>
                    <BANKTRANLIST>
                        <STMTTRN>
                            <TRNTYPE>CREDIT</TRNTYPE>
                            <DTPOSTED>20241201</DTPOSTED>
                            <TRNAMT>1250.00</TRNAMT>
                            <FITID>TXN001</FITID>
                            <NAME>MARTIN DUPONT</NAME>
                            <MEMO>Virement OptimPV INV2024-001</MEMO>
                        </STMTTRN>
                        <STMTTRN>
                            <TRNTYPE>CREDIT</TRNTYPE>
                            <DTPOSTED>20241202</DTPOSTED>
                            <TRNAMT>750.50</TRNAMT>
                            <FITID>TXN002</FITID>
                            <NAME>SOCIETE ABC</NAME>
                            <MEMO>Paiement facture</MEMO>
                        </STMTTRN>
                    </BANKTRANLIST>
                </STMTRS>
            </STMTTRNRS>
        </BANKMSGSRSV1>
    </OFX>"""
    
    imported_count, errors = payment_mgr.import_ofx(ofx_content, "FR7612345678901234567890")
    print(f"   Imported {imported_count} transactions")
    if errors:
        print(f"   Errors: {errors}")
    
    # 2. Automatic payment matching
    print("\n2. Running automatic payment matching...")
    
    matching_results = payment_mgr.match_payments_to_invoices()
    print(f"   Processed {matching_results['total_transactions_processed']} transactions")
    print(f"   Auto-matched: {matching_results['auto_matches_count']} payments")
    print(f"   Suggestions: {matching_results['suggestions_count']} manual reviews needed")
    
    # Display auto-matches
    for match in matching_results['auto_matches']:
        print(f"   ✓ {match['transaction']['amount']}€ matched to invoice {match['invoice']['invoice_number']} "
              f"(confidence: {match['confidence']}%)")
    
    # 3. Process payment schedules
    print("\n3. Creating payment schedules...")
    
    # Example: Create 3-installment payment schedule for an invoice
    try:
        schedule_ids = payment_mgr.create_payment_schedule(
            invoice_id=1,  # Assuming invoice ID 1 exists
            installments=3,
            start_date=date.today()
        )
        print(f"   Created payment schedule with {len(schedule_ids)} installments")
    except Exception as e:
        print(f"   Could not create schedule: {e}")
    
    # 4. Calculate late fees
    print("\n4. Calculating late fees...")
    
    # Example late fee calculation
    try:
        late_fee = payment_mgr.calculate_late_fees(
            invoice_id=1,
            calculation_date=date.today()
        )
        if late_fee:
            print(f"   Invoice overdue by {late_fee.days_late} days")
            print(f"   Late fee: {late_fee.calculated_fee}€ (rate: {late_fee.legal_rate}%)")
        else:
            print("   No overdue invoices or late fees applicable")
    except Exception as e:
        print(f"   Could not calculate late fees: {e}")
    
    # 5. Dunning process
    print("\n5. Running dunning process...")
    
    # Configure SMTP for demo (use test settings)
    dunning_mgr.configure_smtp(
        smtp_host="smtp.example.com",
        smtp_port=587,
        username="noreply@optimpv.com",
        password="password",
        use_tls=True
    )
    
    # Run dunning cycle in dry-run mode
    dunning_results = dunning_mgr.process_dunning_cycle(dry_run=True)
    print(f"   Would process {dunning_results['processed_count']} dunning actions")
    
    for action in dunning_results['actions']:
        if action.get('dry_run'):
            print(f"   - Invoice {action['invoice_number']}: {action['action_level']} "
                  f"({action['days_overdue']} days overdue, {action['amount']}€)")
    
    # 6. Payment KPIs and Dashboard
    print("\n6. Payment KPIs and Analytics...")
    
    # Calculate DSO
    dso = dashboard.calculate_dso()
    print(f"   Days Sales Outstanding (DSO): {dso.dso_days} days")
    print(f"   Total receivables: {dso.total_receivables:,.2f}€")
    print(f"   Total sales (90 days): {dso.total_sales:,.2f}€")
    
    # Aging analysis
    aging_buckets = dashboard.calculate_aging_buckets()
    print("\n   Aging Analysis:")
    for bucket in aging_buckets:
        print(f"   - {bucket.bucket_name}: {bucket.total_amount:,.2f}€ "
              f"({bucket.percentage}%) - {bucket.count} invoices")
    
    # Collection metrics
    collection_metrics = dashboard.calculate_collection_rate()
    print(f"\n   Collection Performance:")
    print(f"   - Collection rate: {collection_metrics.collection_rate}%")
    print(f"   - Average collection period: {collection_metrics.average_collection_period} days")
    print(f"   - Bad debt rate: {collection_metrics.bad_debt_rate}%")
    
    # Payment method analytics
    payment_analytics = dashboard.get_payment_method_analytics()
    print(f"\n   Payment Methods Distribution:")
    for method, stats in payment_analytics['payment_method_distribution'].items():
        print(f"   - {method}: {stats['total_amount']:,.2f}€ "
              f"({stats['percentage']}%) - {stats['count']} payments")
    
    # 7. Cash flow forecast
    print("\n7. Cash Flow Forecast...")
    
    weekly_forecast = dashboard.get_weekly_cash_flow_summary(weeks=4)
    print("   Next 4 weeks expected receipts:")
    for week in weekly_forecast:
        print(f"   Week {week['week_number']}: {week['expected_receipts']:,.2f}€ expected, "
              f"{week['overdue_amount']:,.2f}€ overdue")
    
    # 8. Export reports
    print("\n8. Generating reports...")
    
    # Aging report
    aging_report = dashboard.export_aging_report()
    print(f"   Aging report generated: {aging_report['total_receivables']:,.2f}€ total receivables")
    
    # DSO trend
    dso_history = dashboard.export_dso_history(months=6)
    print(f"   DSO trend history: {len(dso_history)} months of data")
    
    print("\n=== Demo completed ===")
    
    return {
        'import_results': {'imported': imported_count, 'errors': errors},
        'matching_results': matching_results,
        'dso': dso,
        'aging_buckets': aging_buckets,
        'collection_metrics': collection_metrics,
        'payment_analytics': payment_analytics,
        'cash_flow_forecast': weekly_forecast
    }

def demo_manual_operations():
    """Demonstrate manual payment operations"""
    
    payment_mgr = PaymentManager()
    dunning_mgr = DunningManager()
    
    print("\n=== Manual Operations Demo ===\n")
    
    # 1. Manual payment processing
    print("1. Processing manual payment...")
    
    try:
        payment_id = payment_mgr.process_payment(
            invoice_id=1,
            amount=1250.00,
            payment_method=PaymentMethod.VIREMENT,
            payment_date=date.today(),
            transaction_id="VIR2024001",
            notes="Paiement manuel via interface"
        )
        print(f"   Payment processed with ID: {payment_id}")
    except Exception as e:
        print(f"   Could not process payment: {e}")
    
    # 2. Manual payment matching
    print("\n2. Manual payment matching...")
    
    unmatched = payment_mgr.get_unmatched_transactions(limit=5)
    print(f"   Found {len(unmatched)} unmatched transactions")
    
    for transaction in unmatched[:2]:  # Show first 2
        print(f"   - Transaction {transaction['id']}: {transaction['amount']}€ "
              f"from {transaction.get('beneficiary_name', 'Unknown')} "
              f"on {transaction['transaction_date']}")
    
    # 3. Manual dunning
    print("\n3. Sending manual dunning notice...")
    
    try:
        success = dunning_mgr.send_manual_dunning(
            invoice_id=1,
            level=DunningLevel.FRIENDLY_REMINDER,
            custom_message="Rappel personnalisé pour ce client",
            email_address="client@example.com"
        )
        print(f"   Manual dunning sent: {'Success' if success else 'Failed'}")
    except Exception as e:
        print(f"   Could not send dunning: {e}")
    
    # 4. Dunning history
    print("\n4. Dunning history...")
    
    history = dunning_mgr.get_dunning_history()
    print(f"   Found {len(history)} recent dunning actions")
    
    for action in history[:3]:  # Show first 3
        print(f"   - {action['action_date']}: {action['level']} for invoice "
              f"{action['invoice_number']} ({action['due_amount']}€)")
    
    # 5. Payment statistics
    print("\n5. Payment statistics...")
    
    method_stats = payment_mgr.get_payment_methods_stats()
    total_payments = sum(stats['count'] for stats in method_stats.values())
    total_amount = sum(stats['total_amount'] for stats in method_stats.values())
    
    print(f"   Total payments: {total_payments}")
    print(f"   Total amount: {total_amount:,.2f}€")
    
    for method, stats in method_stats.items():
        print(f"   - {method}: {stats['count']} payments, "
              f"{stats['total_amount']:,.2f}€ total")

if __name__ == "__main__":
    # Run the demos
    try:
        demo_results = demo_payment_management()
        demo_manual_operations()
        
        # Save demo results to file
        with open("payment_demo_results.json", "w", encoding='utf-8') as f:
            json.dump(demo_results, f, indent=2, default=str)
        
        print(f"\nDemo results saved to payment_demo_results.json")
        
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()