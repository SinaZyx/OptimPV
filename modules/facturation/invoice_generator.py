"""
Invoice generation module for PMO billing system
Handles PDF invoice creation and formatting with customizable templates
"""

import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from io import BytesIO
import os

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from .models import Invoice, InvoiceItem, Participant, Project, BillingCalculation
from .database import BillingDatabase
from .pdf_templates import PDFTemplateManager
from .pdf_config import get_pdf_config

logger = logging.getLogger(__name__)

class InvoiceGenerator:
    """Generates PDF invoices for PMO billing with template support"""
    
    def __init__(self, db: BillingDatabase):
        self.db = db
        
        if not REPORTLAB_AVAILABLE:
            logger.warning("ReportLab not available. PDF generation will be disabled.")
            logger.info("Install with: pip install reportlab")
        
        # Initialize template manager
        try:
            pdf_config = get_pdf_config()
            self.template_manager = PDFTemplateManager(pdf_config)
        except Exception as e:
            logger.error(f"Error initializing template manager: {e}")
            self.template_manager = None
    
    def generate_invoice_pdf(self, invoice: Invoice, participant: Participant, 
                           project: Project, output_path: Optional[str] = None,
                           template_name: str = 'modern', language: str = 'fr') -> Optional[bytes]:
        """Generate PDF invoice using customizable templates"""
        
        if not REPORTLAB_AVAILABLE:
            logger.error("Cannot generate PDF: ReportLab not installed")
            return None
        
        # Use new template system if available
        if self.template_manager:
            return self._generate_with_template(invoice, participant, project, 
                                              output_path, template_name, language)
        else:
            # Fallback to legacy method
            return self._generate_legacy_invoice(invoice, participant, project, output_path)
    
    def _generate_with_template(self, invoice: Invoice, participant: Participant,
                              project: Project, output_path: Optional[str] = None,
                              template_name: str = 'modern', language: str = 'fr') -> Optional[bytes]:
        """Generate invoice using the new template system"""
        try:
            # Prepare data for template
            data = {
                'invoice': invoice,
                'participant': participant,
                'project': project,
                'company': self._get_company_data(),
                'bank_details': self._get_bank_details()
            }
            
            # Generate PDF using template manager
            return self.template_manager.generate_document(
                template_type='invoice',
                data=data,
                template_name=template_name,
                language=language,
                output_path=output_path
            )
            
        except Exception as e:
            logger.error(f"Error generating invoice with template: {e}")
            return None
    
    def _generate_legacy_invoice(self, invoice: Invoice, participant: Participant, 
                               project: Project, output_path: Optional[str] = None) -> Optional[bytes]:
        """Legacy invoice generation method (fallback)"""
        # Create PDF in memory
        buffer = BytesIO()
        
        try:
            # Create document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                leftMargin=2*cm,
                rightMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # Build content
            story = []
            styles = getSampleStyleSheet()
            
            # Company header
            story.extend(self._build_header(styles))
            story.append(Spacer(1, 20))
            
            # Client information
            story.extend(self._build_client_info(participant, styles))
            story.append(Spacer(1, 20))
            
            # Invoice details
            story.extend(self._build_invoice_details(invoice, project, styles))
            story.append(Spacer(1, 20))
            
            # Invoice items table
            story.extend(self._build_items_table(invoice, styles))
            story.append(Spacer(1, 20))
            
            # Totals
            story.extend(self._build_totals(invoice, styles))
            story.append(Spacer(1, 20))
            
            # Footer
            story.extend(self._build_footer(styles))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            # Save to file if path provided
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
                logger.info(f"Invoice PDF saved to {output_path}")
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            buffer.close()
            return None
    
    def _get_company_data(self) -> Dict[str, str]:
        """Get company data from database settings"""
        return {
            'name': self.db.get_setting('company_name') or 'OptimPV',
            'address': self.db.get_setting('company_address') or '',
            'siret': self.db.get_setting('company_siret') or '',
            'phone': self.db.get_setting('company_phone') or '',
            'email': self.db.get_setting('company_email') or '',
            'payment_terms_days': self.db.get_setting('default_payment_terms_days') or '30'
        }
    
    def _get_bank_details(self) -> Dict[str, str]:
        """Get bank details for QR code generation"""
        return {
            'iban': self.db.get_setting('bank_iban') or '',
            'bic': self.db.get_setting('bank_bic') or '',
            'creditor_name': self.db.get_setting('company_name') or 'OptimPV',
            'creditor_address': self.db.get_setting('company_address') or ''
        }
    
    def _build_header(self, styles) -> List:
        """Build company header"""
        elements = []
        
        company_name = self.db.get_setting('company_name') or 'OptimPV'
        company_address = self.db.get_setting('company_address') or ''
        company_siret = self.db.get_setting('company_siret') or ''
        
        # Company name
        title_style = ParagraphStyle(
            'CompanyTitle',
            parent=styles['Heading1'],
            fontSize=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2E7D32')
        )
        elements.append(Paragraph(company_name, title_style))
        
        # Address and SIRET
        if company_address or company_siret:
            info_style = ParagraphStyle(
                'CompanyInfo',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=colors.grey
            )
            
            company_info = []
            if company_address:
                company_info.append(company_address)
            if company_siret:
                company_info.append(f"SIRET: {company_siret}")
            
            elements.append(Paragraph(" | ".join(company_info), info_style))
        
        return elements
    
    def _build_client_info(self, participant: Participant, styles) -> List:
        """Build client information section"""
        elements = []
        
        # Title
        elements.append(Paragraph("Facturé à:", styles['Heading2']))
        
        # Client details
        client_info = [
            participant.name,
            participant.address,
        ]
        
        if participant.contact_email:
            client_info.append(f"Email: {participant.contact_email}")
        if participant.contact_phone:
            client_info.append(f"Tél: {participant.contact_phone}")
        
        client_text = "<br/>".join(filter(None, client_info))
        elements.append(Paragraph(client_text, styles['Normal']))
        
        return elements
    
    def _build_invoice_details(self, invoice: Invoice, project: Project, styles) -> List:
        """Build invoice details section"""
        elements = []
        
        # Create table with invoice details
        data = [
            ['Facture N°:', invoice.invoice_number],
            ['Date d\'émission:', invoice.issue_date.strftime('%d/%m/%Y') if invoice.issue_date else ''],
            ['Date d\'échéance:', invoice.due_date.strftime('%d/%m/%Y') if invoice.due_date else ''],
            ['Projet:', project.name],
        ]
        
        table = Table(data, colWidths=[4*cm, 6*cm])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        return elements
    
    def _build_items_table(self, invoice: Invoice, styles) -> List:
        """Build invoice items table"""
        elements = []
        
        # Table header
        data = [['Description', 'Quantité', 'Prix unitaire', 'Total']]
        
        # Add items
        for item in invoice.items:
            data.append([
                item.description,
                f"{item.quantity:.2f}",
                f"{item.unit_price:.4f} €",
                f"{item.total_price:.2f} €"
            ])
        
        # Create table
        table = Table(data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8F5E8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F8F8')]),
            
            # Alignment
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2E7D32')),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        return elements
    
    def _build_totals(self, invoice: Invoice, styles) -> List:
        """Build totals section"""
        elements = []
        
        # Totals table
        data = [
            ['Sous-total HT:', f"{invoice.subtotal:.2f} €"],
        ]
        
        if invoice.tax_amount > 0:
            data.extend([
                [f'TVA ({invoice.tax_rate*100:.1f}%):', f"{invoice.tax_amount:.2f} €"],
                ['', ''],  # Separator line
            ])
        
        data.append(['Total TTC:', f"{invoice.total_amount:.2f} €"])
        
        # Create table with right alignment
        table = Table(data, colWidths=[4*cm, 3*cm], hAlign='RIGHT')
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -2), 'Helvetica'),
            ('FONTNAME', (1, 0), (1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -2), 10),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#2E7D32')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F5E8')),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(table)
        return elements
    
    def _build_footer(self, styles) -> List:
        """Build invoice footer"""
        elements = []
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        
        payment_terms_days = self.db.get_setting('default_payment_terms_days') or '30'
        
        footer_text = f"""
        <b>Conditions de paiement:</b> {payment_terms_days} jours net<br/>
        <b>Mode de paiement:</b> Virement bancaire<br/>
        En cas de retard de paiement, des pénalités de 3 fois le taux d'intérêt légal seront appliquées.<br/>
        <br/>
        Merci de votre confiance !
        """
        
        elements.append(Paragraph(footer_text, footer_style))
        
        return elements
    
    def generate_credit_note_pdf(self, invoice: Invoice, participant: Participant,
                               project: Project, output_path: Optional[str] = None,
                               template_name: str = 'modern', language: str = 'fr') -> Optional[bytes]:
        """Generate credit note PDF"""
        if self.template_manager:
            data = {
                'invoice': invoice,  # Credit note uses same structure as invoice
                'participant': participant,
                'project': project,
                'company': self._get_company_data(),
                'bank_details': self._get_bank_details()
            }
            
            return self.template_manager.generate_document(
                template_type='credit_note',
                data=data,
                template_name=template_name,
                language=language,
                output_path=output_path
            )
        else:
            # Fallback to legacy method with modified title
            return self._generate_legacy_invoice(invoice, participant, project, output_path)
    
    def generate_quote_pdf(self, quote_data: Dict[str, Any], client_data: Dict[str, str],
                         output_path: Optional[str] = None, template_name: str = 'modern',
                         language: str = 'fr') -> Optional[bytes]:
        """Generate quote/estimate PDF"""
        if self.template_manager:
            data = {
                'quote': quote_data,
                'client': client_data,
                'company': self._get_company_data()
            }
            
            return self.template_manager.generate_document(
                template_type='quote',
                data=data,
                template_name=template_name,
                language=language,
                output_path=output_path
            )
        else:
            logger.error("Quote generation requires template system")
            return None
    
    def list_available_templates(self) -> Dict[str, List[str]]:
        """List available templates by type"""
        if self.template_manager:
            return self.template_manager.list_templates()
        else:
            return {'invoice': ['legacy'], 'credit_note': ['legacy'], 'quote': []}
    
    def generate_billing_summary_pdf(self, project: Project, billing_calculations: List[BillingCalculation],
                                   period_name: str, output_path: Optional[str] = None) -> Optional[bytes]:
        """Generate PDF summary for billing period"""
        
        if not REPORTLAB_AVAILABLE:
            logger.error("Cannot generate PDF: ReportLab not installed")
            return None
        
        buffer = BytesIO()
        
        try:
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                leftMargin=2*cm,
                rightMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'SummaryTitle',
                parent=styles['Heading1'],
                fontSize=18,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#2E7D32')
            )
            story.append(Paragraph(f"Résumé de Facturation - {period_name}", title_style))
            story.append(Spacer(1, 20))
            
            # Project info
            story.append(Paragraph(f"<b>Projet:</b> {project.name}", styles['Normal']))
            story.append(Paragraph(f"<b>Client:</b> {project.client_name}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Summary table
            data = [['Participant', 'Autoconsommation (kWh)', 'Prix unitaire (€/kWh)', 'Sous-total HT (€)', 'Total TTC (€)']]
            
            total_kwh = 0
            total_amount = 0
            
            for calc in billing_calculations:
                data.append([
                    calc.participant_name,
                    f"{calc.autoconsumption_kwh:.2f}",
                    f"{calc.unit_price_eur_kwh:.4f}",
                    f"{calc.subtotal:.2f}",
                    f"{calc.total_amount:.2f}"
                ])
                total_kwh += calc.autoconsumption_kwh
                total_amount += calc.total_amount
            
            # Add totals row
            data.append(['TOTAL', f"{total_kwh:.2f}", '', '', f"{total_amount:.2f}"])
            
            table = Table(data, colWidths=[4*cm, 3*cm, 3*cm, 3*cm, 3*cm])
            table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8F5E8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                
                # Data
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F8F8F8')]),
                
                # Totals row
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F5E8')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#2E7D32')),
                
                # Alignment
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                
                # Borders
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
                
                # Padding
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(table)
            
            # Build PDF
            doc.build(story)
            
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
                logger.info(f"Billing summary PDF saved to {output_path}")
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating billing summary PDF: {e}")
            buffer.close()
            return None