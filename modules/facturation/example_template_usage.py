#!/usr/bin/env python3
"""
Example usage of the PDF template system for OptimPV billing
Demonstrates how to use the new customizable PDF templates
"""

import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from modules.facturation.pdf_templates import PDFTemplateManager
from modules.facturation.pdf_config import get_pdf_config, TemplateConfig
from modules.facturation.qr_payment import QRPaymentGenerator
from modules.facturation.models import Invoice, InvoiceItem, Participant, Project, InvoiceStatus


def create_sample_data():
    """Create sample data for testing"""
    
    # Sample project
    project = Project(
        id=1,
        name="Installation Photovoltaïque Résidentielle",
        address="123 Rue de la Paix, 75001 Paris",
        client_name="SARL Énergie Verte",
        client_email="contact@energie-verte.fr",
        client_phone="01 23 45 67 89",
        start_date=date(2024, 1, 1),
        total_capacity_kwc=9.5,
        annual_production_kwh=12500
    )
    
    # Sample participant
    participant = Participant(
        id=1,
        project_id=1,
        name="Dupont Michel",
        address="456 Avenue des Fleurs<br/>92100 Boulogne-Billancourt",
        contact_email="michel.dupont@email.fr",
        contact_phone="01 98 76 54 32",
        allocation_percentage=25.0,
        annual_consumption_kwh=3500
    )
    
    # Sample invoice
    invoice = Invoice(
        id=1,
        participant_id=1,
        invoice_number="FACT-2024-001",
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        status=InvoiceStatus.SENT,
        tax_rate=0.20
    )
    
    # Add invoice items
    invoice.add_item(
        description="Autoconsommation électricité photovoltaïque - Janvier 2024",
        quantity=287.5,
        unit_price=0.1850,
        item_type="autoconsumption"
    )
    
    invoice.add_item(
        description="Frais de gestion mensuel",
        quantity=1.0,
        unit_price=15.00,
        item_type="subscription"
    )
    
    # Sample company data
    company_data = {
        'name': 'OptimPV Solutions',
        'address': '789 Boulevard Solaire<br/>69000 Lyon',
        'siret': '12345678901234',
        'phone': '04 12 34 56 78',
        'email': 'contact@optimpv-solutions.fr',
        'payment_terms_days': '30'
    }
    
    # Sample bank details
    bank_details = {
        'iban': 'FR14 2004 1010 0505 0001 3M02 606',
        'bic': 'BNPAFRPP',
        'creditor_name': 'OptimPV Solutions',
        'creditor_address': '789 Boulevard Solaire, 69000 Lyon'
    }
    
    # Sample quote data
    quote_data = {
        'number': 'DEVIS-2024-001',
        'date': date.today(),
        'valid_until': date.today() + timedelta(days=30),
        'project_name': 'Installation Photovoltaïque 9.5 kWc',
        'items': [
            {
                'description': 'Panneaux photovoltaïques 425W (22 unités)',
                'quantity': 22,
                'unit_price': 350.00,
                'total': 7700.00
            },
            {
                'description': 'Onduleur central 10kW',
                'quantity': 1,
                'unit_price': 1500.00,
                'total': 1500.00
            },
            {
                'description': 'Installation et mise en service',
                'quantity': 1,
                'unit_price': 2800.00,
                'total': 2800.00
            }
        ],
        'subtotal': 12000.00,
        'tax_rate': 0.20
    }
    
    client_data = {
        'name': 'Famille Martin',
        'address': '123 Rue des Cerisiers<br/>31000 Toulouse',
        'email': 'martin.famille@email.fr',
        'phone': '05 61 23 45 67'
    }
    
    return {
        'invoice': invoice,
        'participant': participant,
        'project': project,
        'company': company_data,
        'bank_details': bank_details,
        'quote': quote_data,
        'client': client_data
    }


def demo_invoice_generation():
    """Demonstrate invoice generation with different templates"""
    print("=== Démonstration de génération de factures ===")
    
    # Initialize template manager
    config = get_pdf_config()
    manager = PDFTemplateManager(config)
    
    # Get sample data
    data = create_sample_data()
    
    # Create output directory
    output_dir = Path(__file__).parent / "demo_output"
    output_dir.mkdir(exist_ok=True)
    
    # Generate invoices with different templates
    templates = ['modern', 'minimal', 'corporate']
    languages = ['fr', 'en']
    
    for template_name in templates:
        for language in languages:
            print(f"Génération facture - Template: {template_name}, Langue: {language}")
            
            invoice_data = {
                'invoice': data['invoice'],
                'participant': data['participant'],
                'project': data['project'],
                'company': data['company'],
                'bank_details': data['bank_details']
            }
            
            output_path = output_dir / f"facture_{template_name}_{language}.pdf"
            
            pdf_bytes = manager.generate_document(
                template_type='invoice',
                data=invoice_data,
                template_name=template_name,
                language=language,
                output_path=str(output_path)
            )
            
            if pdf_bytes:
                print(f"  ✓ Facture générée: {output_path}")
            else:
                print(f"  ✗ Erreur génération facture: {template_name} {language}")


def demo_quote_generation():
    """Demonstrate quote generation"""
    print("\n=== Démonstration de génération de devis ===")
    
    config = get_pdf_config()
    manager = PDFTemplateManager(config)
    data = create_sample_data()
    
    output_dir = Path(__file__).parent / "demo_output"
    output_dir.mkdir(exist_ok=True)
    
    # Generate quotes
    for template_name in ['modern', 'corporate']:
        print(f"Génération devis - Template: {template_name}")
        
        quote_data = {
            'quote': data['quote'],
            'client': data['client'],
            'company': data['company']
        }
        
        output_path = output_dir / f"devis_{template_name}.pdf"
        
        pdf_bytes = manager.generate_document(
            template_type='quote',
            data=quote_data,
            template_name=template_name,
            language='fr',
            output_path=str(output_path)
        )
        
        if pdf_bytes:
            print(f"  ✓ Devis généré: {output_path}")
        else:
            print(f"  ✗ Erreur génération devis: {template_name}")


def demo_qr_code_generation():
    """Demonstrate QR code generation"""
    print("\n=== Démonstration de génération QR Code ===")
    
    generator = QRPaymentGenerator()
    
    # Test EPC QR code generation
    qr_bytes = generator.generate_payment_qr(
        iban='FR14 2004 1010 0505 0001 3M02 606',
        amount=1234.56,
        reference='FACT-2024-001',
        creditor_name='OptimPV Solutions',
        creditor_address='789 Boulevard Solaire, 69000 Lyon',
        bic='BNPAFRPP',
        remittance_info='Facture système photovoltaïque - Janvier 2024'
    )
    
    if qr_bytes:
        output_path = Path(__file__).parent / "demo_output" / "qr_payment.png"
        with open(output_path, 'wb') as f:
            f.write(qr_bytes)
        print(f"  ✓ QR Code généré: {output_path}")
    else:
        print("  ✗ Erreur génération QR Code")


def demo_custom_template():
    """Demonstrate custom template creation"""
    print("\n=== Démonstration de template personnalisé ===")
    
    config = get_pdf_config()
    
    # Create a custom template based on modern
    custom_config = config.create_custom_template(
        name="custom_orange",
        base_template="modern",
        modifications={
            'description': 'Template personnalisé OptimPV avec couleurs orange',
            'colors': {
                'primary': '#FF5722',
                'accent': '#FF7043',
                'table_header': '#FFF3E0'
            }
        }
    )
    
    # Save the custom template
    config.save_template(custom_config)
    print(f"  ✓ Template personnalisé créé: {custom_config.name}")
    
    # Generate invoice with custom template
    manager = PDFTemplateManager(config)
    data = create_sample_data()
    
    invoice_data = {
        'invoice': data['invoice'],
        'participant': data['participant'],
        'project': data['project'],
        'company': data['company'],
        'bank_details': data['bank_details']
    }
    
    output_dir = Path(__file__).parent / "demo_output"
    output_path = output_dir / "facture_custom_orange.pdf"
    
    pdf_bytes = manager.generate_document(
        template_type='invoice',
        data=invoice_data,
        template_name='custom_orange',
        language='fr',
        output_path=str(output_path)
    )
    
    if pdf_bytes:
        print(f"  ✓ Facture avec template personnalisé: {output_path}")
    else:
        print("  ✗ Erreur génération facture personnalisée")


def demo_template_management():
    """Demonstrate template management features"""
    print("\n=== Démonstration de gestion des templates ===")
    
    config = get_pdf_config()
    
    # List available templates
    templates = config.list_templates()
    print("Templates disponibles:")
    for name, description in templates.items():
        print(f"  - {name}: {description}")
    
    # Template validation
    from modules.facturation.pdf_config import validate_template_config
    
    template_config = config.get_template_config('modern')
    errors = validate_template_config(template_config)
    
    if errors:
        print(f"\nErreurs de validation pour 'modern': {errors}")
    else:
        print("\n✓ Template 'modern' validé avec succès")


def main():
    """Main demonstration function"""
    print("Démonstration du système de templates PDF OptimPV")
    print("=" * 50)
    
    try:
        demo_template_management()
        demo_qr_code_generation()
        demo_invoice_generation()
        demo_quote_generation()
        demo_custom_template()
        
        print("\n" + "=" * 50)
        print("Démonstration terminée avec succès!")
        print("Consultez le dossier 'demo_output' pour voir les PDFs générés.")
        
    except Exception as e:
        print(f"\nErreur durant la démonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()