"""
PDF Templates System for OptimPV Billing Module
Provides customizable PDF templates with multi-language support, QR codes, and watermarks
"""

import logging
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from io import BytesIO
from abc import ABC, abstractmethod
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
    from reportlab.platypus.flowables import Flowable
    from reportlab.graphics.shapes import Drawing, String as GraphicsString
    from reportlab.graphics import renderPDF
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    # Fallback classes pour éviter les erreurs de définition
    class Flowable:
        def __init__(self, *args, **kwargs):
            pass
        def draw(self):
            pass
    
    class SimpleDocTemplate:
        def __init__(self, *args, **kwargs):
            pass
        def build(self, *args, **kwargs):
            pass
    
    class Paragraph:
        def __init__(self, *args, **kwargs):
            pass
    
    class ParagraphStyle:
        def __init__(self, *args, **kwargs):
            pass
    
    class Spacer:
        def __init__(self, *args, **kwargs):
            pass
    
    class Table:
        def __init__(self, *args, **kwargs):
            pass
    
    class TableStyle:
        def __init__(self, *args, **kwargs):
            pass
    
    class Image:
        def __init__(self, *args, **kwargs):
            pass
    
    class PageBreak:
        def __init__(self, *args, **kwargs):
            pass
    
    class Drawing:
        def __init__(self, *args, **kwargs):
            pass
    
    class ImageReader:
        def __init__(self, *args, **kwargs):
            pass
    
    def getSampleStyleSheet():
        return {}
    
    def renderPDF(*args, **kwargs):
        pass
    
    class canvas:
        def __init__(self, *args, **kwargs):
            pass
    
    # Mock pour colors et autres constantes
    class colors:
        black = 'black'
        white = 'white'
        red = 'red'
        blue = 'blue'
        green = 'green'
    
    # Mock pour enums
    TA_CENTER = 'center'
    TA_RIGHT = 'right'
    TA_LEFT = 'left'
    TA_JUSTIFY = 'justify'
    
    # Mock pour unités
    mm = 1
    cm = 10
    A4 = (210*mm, 297*mm)

from .models import Invoice, InvoiceItem, Participant, Project, InvoiceStatus
from .pdf_config import PDFConfig, TemplateConfig
from .qr_payment import QRPaymentGenerator

logger = logging.getLogger(__name__)


class WatermarkFlowable(Flowable):
    """Custom flowable for watermarks"""
    
    def __init__(self, text: str, config: TemplateConfig):
        Flowable.__init__(self)
        self.text = text
        self.config = config
        
    def draw(self):
        """Draw the watermark"""
        canvas = self.canv
        canvas.saveState()
        
        # Get page dimensions
        page_width, page_height = A4
        
        # Set watermark properties
        canvas.setFont("Helvetica-Bold", 60)
        canvas.setFillColor(colors.Color(0.9, 0.9, 0.9, alpha=0.3))
        
        # Calculate position for center rotation
        canvas.translate(page_width/2, page_height/2)
        canvas.rotate(45)
        
        # Draw text centered
        text_width = canvas.stringWidth(self.text, "Helvetica-Bold", 60)
        canvas.drawString(-text_width/2, -30, self.text)
        
        canvas.restoreState()


class BaseTemplate(ABC):
    """Base class for all PDF templates"""
    
    def __init__(self, config: TemplateConfig, language: str = 'fr'):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation")
            
        self.config = config
        self.language = language
        self.qr_generator = QRPaymentGenerator()
        
    @abstractmethod
    def generate(self, data: Dict[str, Any], output_path: Optional[str] = None) -> Optional[bytes]:
        """Generate PDF document"""
        pass
    
    def _create_document(self, buffer: BytesIO) -> SimpleDocTemplate:
        """Create base document with margins"""
        return SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=self.config.margins['left'] * mm,
            rightMargin=self.config.margins['right'] * mm,
            topMargin=self.config.margins['top'] * mm,
            bottomMargin=self.config.margins['bottom'] * mm
        )
    
    def _get_styles(self) -> Dict[str, ParagraphStyle]:
        """Get configured paragraph styles"""
        base_styles = getSampleStyleSheet()
        
        styles = {
            'title': ParagraphStyle(
                'CustomTitle',
                parent=base_styles['Heading1'],
                fontSize=self.config.fonts['title']['size'],
                fontName=self.config.fonts['title']['name'],
                alignment=TA_CENTER,
                textColor=colors.HexColor(self.config.colors['primary']),
                spaceBefore=0,
                spaceAfter=20
            ),
            'heading': ParagraphStyle(
                'CustomHeading',
                parent=base_styles['Heading2'],
                fontSize=self.config.fonts['heading']['size'],
                fontName=self.config.fonts['heading']['name'],
                textColor=colors.HexColor(self.config.colors['primary']),
                spaceBefore=15,
                spaceAfter=10
            ),
            'body': ParagraphStyle(
                'CustomBody',
                parent=base_styles['Normal'],
                fontSize=self.config.fonts['body']['size'],
                fontName=self.config.fonts['body']['name'],
                textColor=colors.HexColor(self.config.colors['text']),
                spaceBefore=3,
                spaceAfter=3
            ),
            'footer': ParagraphStyle(
                'CustomFooter',
                parent=base_styles['Normal'],
                fontSize=self.config.fonts['footer']['size'],
                fontName=self.config.fonts['footer']['name'],
                alignment=TA_CENTER,
                textColor=colors.HexColor(self.config.colors['secondary']),
                spaceBefore=10
            ),
            'address': ParagraphStyle(
                'CustomAddress',
                parent=base_styles['Normal'],
                fontSize=self.config.fonts['body']['size'],
                fontName=self.config.fonts['body']['name'],
                textColor=colors.HexColor(self.config.colors['text']),
                spaceBefore=2,
                spaceAfter=2
            )
        }
        
        return styles
    
    def _build_header(self, styles: Dict[str, ParagraphStyle], company_data: Dict[str, str]) -> List:
        """Build document header with logo and company info"""
        elements = []
        
        # Create header table with logo and company info
        header_data = []
        
        # Logo column
        logo_cell = ""
        if self.config.logo_path and os.path.exists(self.config.logo_path):
            try:
                logo_cell = Image(
                    self.config.logo_path,
                    width=self.config.logo_width * mm,
                    height=self.config.logo_height * mm
                )
            except Exception as e:
                logger.warning(f"Could not load logo: {e}")
                logo_cell = ""
        
        # Company info column
        company_info = []
        if company_data.get('name'):
            company_info.append(f"<b>{company_data['name']}</b>")
        if company_data.get('address'):
            company_info.append(company_data['address'])
        if company_data.get('siret'):
            company_info.append(f"SIRET: {company_data['siret']}")
        if company_data.get('phone'):
            company_info.append(f"Tél: {company_data['phone']}")
        if company_data.get('email'):
            company_info.append(f"Email: {company_data['email']}")
        
        company_paragraph = Paragraph("<br/>".join(company_info), styles['body'])
        
        # Create header table
        if logo_cell:
            header_data = [[logo_cell, company_paragraph]]
            col_widths = [4*cm, 12*cm]
        else:
            header_data = [[company_paragraph]]
            col_widths = [16*cm]
        
        header_table = Table(header_data, colWidths=col_widths)
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT') if logo_cell else ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(header_table)
        
        # Add separator line
        elements.append(Spacer(1, 5))
        separator_table = Table([['']], colWidths=[17*cm])
        separator_table.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 2, colors.HexColor(self.config.colors['primary'])),
        ]))
        elements.append(separator_table)
        elements.append(Spacer(1, 10))
        
        return elements
    
    def _build_client_section(self, styles: Dict[str, ParagraphStyle], 
                            client_data: Dict[str, str], title: str) -> List:
        """Build client information section"""
        elements = []
        
        # Section title
        elements.append(Paragraph(title, styles['heading']))
        
        # Client details
        client_info = []
        for field in ['name', 'address', 'email', 'phone']:
            if client_data.get(field):
                if field == 'email':
                    client_info.append(f"Email: {client_data[field]}")
                elif field == 'phone':
                    client_info.append(f"Tél: {client_data[field]}")
                else:
                    client_info.append(client_data[field])
        
        client_text = "<br/>".join(client_info)
        elements.append(Paragraph(client_text, styles['address']))
        
        return elements
    
    def _add_watermark(self, story: List, status: InvoiceStatus) -> List:
        """Add watermark based on invoice status"""
        watermark_text = ""
        
        if status == InvoiceStatus.DRAFT:
            watermark_text = self._get_text('watermark_draft')
        elif status == InvoiceStatus.PAID:
            watermark_text = self._get_text('watermark_paid')
        elif status == InvoiceStatus.CANCELLED:
            watermark_text = self._get_text('watermark_cancelled')
        elif status == InvoiceStatus.OVERDUE:
            watermark_text = self._get_text('watermark_overdue')
        
        if watermark_text:
            story.insert(0, WatermarkFlowable(watermark_text, self.config))
        
        return story
    
    def _get_text(self, key: str) -> str:
        """Get localized text"""
        return self.config.get_text(key, self.language)
    
    def _save_pdf(self, pdf_bytes: bytes, output_path: Optional[str]) -> bytes:
        """Save PDF to file if path provided"""
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
            logger.info(f"PDF saved to {output_path}")
        
        return pdf_bytes


class InvoiceTemplate(BaseTemplate):
    """Template for invoices"""
    
    def generate(self, data: Dict[str, Any], output_path: Optional[str] = None) -> Optional[bytes]:
        """Generate invoice PDF"""
        invoice: Invoice = data['invoice']
        participant: Participant = data['participant']
        project: Project = data['project']
        company_data: Dict[str, str] = data.get('company', {})
        bank_details: Dict[str, str] = data.get('bank_details', {})
        
        buffer = BytesIO()
        
        try:
            doc = self._create_document(buffer)
            story = []
            styles = self._get_styles()
            
            # Header
            story.extend(self._build_header(styles, company_data))
            story.append(Spacer(1, 20))
            
            # Document title
            story.append(Paragraph(self._get_text('invoice_title'), styles['title']))
            story.append(Spacer(1, 20))
            
            # Create two-column layout for invoice details and client info
            invoice_details = self._build_invoice_details(invoice, project, styles)
            client_info = self._build_client_section(
                styles, 
                {
                    'name': participant.name,
                    'address': participant.address,
                    'email': participant.contact_email,
                    'phone': participant.contact_phone
                },
                self._get_text('bill_to')
            )
            
            # Combine in table for side-by-side layout
            layout_data = [[invoice_details, client_info]]
            layout_table = Table(layout_data, colWidths=[8*cm, 8*cm])
            layout_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            story.append(layout_table)
            story.append(Spacer(1, 30))
            
            # Items table
            story.extend(self._build_items_table(invoice, styles))
            story.append(Spacer(1, 20))
            
            # Totals and QR code
            totals_qr = self._build_totals_with_qr(invoice, bank_details, styles)
            story.append(totals_qr)
            story.append(Spacer(1, 30))
            
            # Footer
            story.extend(self._build_footer(styles, company_data))
            
            # Add watermark based on status
            story = self._add_watermark(story, invoice.status)
            
            # Build PDF
            doc.build(story)
            
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            return self._save_pdf(pdf_bytes, output_path)
            
        except Exception as e:
            logger.error(f"Error generating invoice PDF: {e}")
            buffer.close()
            return None
    
    def _build_invoice_details(self, invoice: Invoice, project: Project, 
                             styles: Dict[str, ParagraphStyle]) -> List:
        """Build invoice details section"""
        elements = []
        
        # Invoice details
        details = [
            [f"<b>{self._get_text('invoice_number')}:</b>", invoice.invoice_number],
            [f"<b>{self._get_text('issue_date')}:</b>", 
             invoice.issue_date.strftime('%d/%m/%Y') if invoice.issue_date else ''],
            [f"<b>{self._get_text('due_date')}:</b>", 
             invoice.due_date.strftime('%d/%m/%Y') if invoice.due_date else ''],
            [f"<b>{self._get_text('project')}:</b>", project.name],
        ]
        
        for label, value in details:
            elements.append(Paragraph(f"{label} {value}", styles['body']))
        
        return elements
    
    def _build_items_table(self, invoice: Invoice, styles: Dict[str, ParagraphStyle]) -> List:
        """Build invoice items table"""
        elements = []
        
        # Table headers
        headers = [
            self._get_text('description'),
            self._get_text('quantity'), 
            self._get_text('unit_price'),
            self._get_text('total')
        ]
        
        data = [headers]
        
        # Add items
        for item in invoice.items:
            data.append([
                item.description,
                f"{item.quantity:.2f}",
                f"{item.unit_price:.4f} €",
                f"{item.total_price:.2f} €"
            ])
        
        # Create table
        table = Table(data, colWidths=[8*cm, 2.5*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.config.colors['table_header'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(self.config.colors['primary'])),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), 
             [colors.white, colors.HexColor(self.config.colors['table_alt'])]),
            
            # Alignment
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(self.config.colors['border'])),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor(self.config.colors['primary'])),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        return elements
    
    def _build_totals_with_qr(self, invoice: Invoice, bank_details: Dict[str, str], 
                            styles: Dict[str, ParagraphStyle]) -> Table:
        """Build totals section with QR code"""
        
        # Totals data
        totals_data = [
            [f"{self._get_text('subtotal')}:", f"{invoice.subtotal:.2f} €"],
        ]
        
        if invoice.tax_amount > 0:
            totals_data.append([
                f"{self._get_text('vat')} ({invoice.tax_rate*100:.1f}%):", 
                f"{invoice.tax_amount:.2f} €"
            ])
            totals_data.append(['', ''])  # Separator
        
        totals_data.append([
            f"<b>{self._get_text('total')}:</b>", 
            f"<b>{invoice.total_amount:.2f} €</b>"
        ])
        
        # Create totals table
        totals_table = Table(totals_data, colWidths=[4*cm, 3*cm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -2), 10),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor(self.config.colors['primary'])),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor(self.config.colors['table_header'])),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        # Generate QR code if bank details available
        qr_image = None
        if bank_details.get('iban') and invoice.total_amount > 0:
            try:
                qr_bytes = self.qr_generator.generate_payment_qr(
                    iban=bank_details['iban'],
                    bic=bank_details.get('bic', ''),
                    amount=invoice.total_amount,
                    reference=invoice.invoice_number,
                    creditor_name=bank_details.get('creditor_name', ''),
                    creditor_address=bank_details.get('creditor_address', '')
                )
                
                if qr_bytes:
                    qr_image = Image(BytesIO(qr_bytes), width=3*cm, height=3*cm)
            except Exception as e:
                logger.warning(f"Could not generate QR code: {e}")
        
        # Combine totals and QR code
        if qr_image:
            qr_label = Paragraph(
                f"<b>{self._get_text('qr_payment')}</b><br/>"
                f"<font size='8'>{self._get_text('qr_payment_desc')}</font>",
                styles['body']
            )
            
            combined_data = [[totals_table, qr_label], ['', qr_image]]
            combined_table = Table(combined_data, colWidths=[7*cm, 4*cm])
            combined_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            return combined_table
        else:
            # Just totals without QR code
            return totals_table
    
    def _build_footer(self, styles: Dict[str, ParagraphStyle], 
                     company_data: Dict[str, str]) -> List:
        """Build invoice footer"""
        elements = []
        
        payment_terms = company_data.get('payment_terms_days', '30')
        
        footer_text = f"""
        <b>{self._get_text('payment_terms')}:</b> {payment_terms} {self._get_text('days_net')}<br/>
        <b>{self._get_text('payment_method')}:</b> {self._get_text('bank_transfer')}<br/>
        {self._get_text('late_payment_penalty')}<br/>
        <br/>
        {self._get_text('thank_you')}
        """
        
        elements.append(Paragraph(footer_text, styles['footer']))
        
        return elements


class CreditNoteTemplate(InvoiceTemplate):
    """Template for credit notes (inherits from InvoiceTemplate with modifications)"""
    
    def generate(self, data: Dict[str, Any], output_path: Optional[str] = None) -> Optional[bytes]:
        """Generate credit note PDF"""
        # Modify data for credit note
        invoice = data['invoice']
        
        # Override title for credit note
        original_generate = super().generate
        
        # Temporarily modify texts for credit note
        data['_is_credit_note'] = True
        
        return original_generate(data, output_path)
    
    def _get_text(self, key: str) -> str:
        """Override text for credit note specific terms"""
        if key == 'invoice_title':
            return super()._get_text('credit_note_title')
        elif key == 'invoice_number':
            return super()._get_text('credit_note_number')
        return super()._get_text(key)


class QuoteTemplate(BaseTemplate):
    """Template for quotes/estimates"""
    
    def generate(self, data: Dict[str, Any], output_path: Optional[str] = None) -> Optional[bytes]:
        """Generate quote PDF"""
        quote_data = data['quote']
        client_data = data['client']
        company_data = data.get('company', {})
        
        buffer = BytesIO()
        
        try:
            doc = self._create_document(buffer)
            story = []
            styles = self._get_styles()
            
            # Header
            story.extend(self._build_header(styles, company_data))
            story.append(Spacer(1, 20))
            
            # Document title
            story.append(Paragraph(self._get_text('quote_title'), styles['title']))
            story.append(Spacer(1, 20))
            
            # Quote details and client info
            quote_details = self._build_quote_details(quote_data, styles)
            client_info = self._build_client_section(styles, client_data, self._get_text('quote_for'))
            
            layout_data = [[quote_details, client_info]]
            layout_table = Table(layout_data, colWidths=[8*cm, 8*cm])
            layout_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            story.append(layout_table)
            story.append(Spacer(1, 30))
            
            # Items table
            story.extend(self._build_quote_items_table(quote_data['items'], styles))
            story.append(Spacer(1, 20))
            
            # Totals
            story.extend(self._build_quote_totals(quote_data, styles))
            story.append(Spacer(1, 30))
            
            # Quote conditions
            story.extend(self._build_quote_conditions(styles, company_data))
            
            # Footer
            story.extend(self._build_footer(styles, company_data))
            
            # Build PDF
            doc.build(story)
            
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            return self._save_pdf(pdf_bytes, output_path)
            
        except Exception as e:
            logger.error(f"Error generating quote PDF: {e}")
            buffer.close()
            return None
    
    def _build_quote_details(self, quote_data: Dict[str, Any], 
                           styles: Dict[str, ParagraphStyle]) -> List:
        """Build quote details section"""
        elements = []
        
        details = [
            [f"<b>{self._get_text('quote_number')}:</b>", quote_data.get('number', '')],
            [f"<b>{self._get_text('quote_date')}:</b>", 
             quote_data.get('date', date.today()).strftime('%d/%m/%Y')],
            [f"<b>{self._get_text('valid_until')}:</b>", 
             quote_data.get('valid_until', '').strftime('%d/%m/%Y') if quote_data.get('valid_until') else ''],
            [f"<b>{self._get_text('project')}:</b>", quote_data.get('project_name', '')],
        ]
        
        for label, value in details:
            if value:
                elements.append(Paragraph(f"{label} {value}", styles['body']))
        
        return elements
    
    def _build_quote_items_table(self, items: List[Dict[str, Any]], 
                               styles: Dict[str, ParagraphStyle]) -> List:
        """Build quote items table"""
        elements = []
        
        headers = [
            self._get_text('description'),
            self._get_text('quantity'),
            self._get_text('unit_price'),
            self._get_text('total')
        ]
        
        data = [headers]
        
        for item in items:
            data.append([
                item.get('description', ''),
                f"{item.get('quantity', 0):.2f}",
                f"{item.get('unit_price', 0):.2f} €",
                f"{item.get('total', 0):.2f} €"
            ])
        
        table = Table(data, colWidths=[8*cm, 2.5*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.config.colors['table_header'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(self.config.colors['primary'])),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), 
             [colors.white, colors.HexColor(self.config.colors['table_alt'])]),
            
            # Alignment
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(self.config.colors['border'])),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor(self.config.colors['primary'])),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        return elements
    
    def _build_quote_totals(self, quote_data: Dict[str, Any], 
                          styles: Dict[str, ParagraphStyle]) -> List:
        """Build quote totals section"""
        elements = []
        
        subtotal = quote_data.get('subtotal', 0)
        tax_rate = quote_data.get('tax_rate', 0.20)
        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount
        
        data = [
            [f"{self._get_text('subtotal')}:", f"{subtotal:.2f} €"],
            [f"{self._get_text('vat')} ({tax_rate*100:.1f}%):", f"{tax_amount:.2f} €"],
            ['', ''],
            [f"<b>{self._get_text('total')}:</b>", f"<b>{total:.2f} €</b>"]
        ]
        
        table = Table(data, colWidths=[4*cm, 3*cm], hAlign='RIGHT')
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -2), 10),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor(self.config.colors['primary'])),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor(self.config.colors['table_header'])),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(table)
        return elements
    
    def _build_quote_conditions(self, styles: Dict[str, ParagraphStyle], 
                              company_data: Dict[str, str]) -> List:
        """Build quote conditions section"""
        elements = []
        
        elements.append(Paragraph(self._get_text('quote_conditions_title'), styles['heading']))
        
        conditions = [
            self._get_text('quote_condition_1'),
            self._get_text('quote_condition_2'),
            self._get_text('quote_condition_3'),
            self._get_text('quote_condition_4')
        ]
        
        for condition in conditions:
            elements.append(Paragraph(f"• {condition}", styles['body']))
            elements.append(Spacer(1, 3))
        
        return elements


class PDFTemplateManager:
    """Manager for PDF templates"""
    
    def __init__(self, config: PDFConfig):
        self.config = config
        self.templates = {
            'invoice': InvoiceTemplate,
            'credit_note': CreditNoteTemplate,
            'quote': QuoteTemplate
        }
    
    def get_template(self, template_type: str, template_name: str = 'default', 
                    language: str = 'fr') -> Optional[BaseTemplate]:
        """Get a template instance"""
        if template_type not in self.templates:
            logger.error(f"Unknown template type: {template_type}")
            return None
        
        template_config = self.config.get_template_config(template_name)
        if not template_config:
            logger.error(f"Unknown template: {template_name}")
            return None
        
        template_class = self.templates[template_type]
        return template_class(template_config, language)
    
    def generate_document(self, template_type: str, data: Dict[str, Any],
                         template_name: str = 'default', language: str = 'fr',
                         output_path: Optional[str] = None) -> Optional[bytes]:
        """Generate document using specified template"""
        template = self.get_template(template_type, template_name, language)
        if not template:
            return None
        
        return template.generate(data, output_path)
    
    def list_templates(self) -> Dict[str, List[str]]:
        """List available templates by type"""
        return {
            template_type: list(self.config.templates.keys())
            for template_type in self.templates.keys()
        }
    
    def register_template(self, template_type: str, template_class: type):
        """Register a new template type"""
        if not issubclass(template_class, BaseTemplate):
            raise ValueError("Template class must inherit from BaseTemplate")
        
        self.templates[template_type] = template_class
        logger.info(f"Registered template type: {template_type}")