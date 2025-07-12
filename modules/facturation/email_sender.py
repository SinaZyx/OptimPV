"""
Email sending module for PMO billing system
Handles email notifications and invoice delivery
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

from .models import Invoice, Participant, Project
from .database import BillingDatabase

logger = logging.getLogger(__name__)

class EmailSender:
    """Handles email sending for billing system"""
    
    def __init__(self, db: BillingDatabase):
        self.db = db
        self.smtp_configured = False
        self._check_smtp_config()
    
    def _check_smtp_config(self):
        """Check if SMTP is configured"""
        smtp_server = self.db.get_setting('smtp_server')
        smtp_port = self.db.get_setting('smtp_port')
        smtp_username = self.db.get_setting('smtp_username')
        smtp_password = self.db.get_setting('smtp_password')
        
        self.smtp_configured = all([smtp_server, smtp_port, smtp_username, smtp_password])
        
        if not self.smtp_configured:
            logger.warning("SMTP not configured. Email sending will be disabled.")
    
    def configure_smtp(self, server: str, port: int, username: str, password: str, 
                      use_tls: bool = True) -> bool:
        """Configure SMTP settings"""
        try:
            # Save settings to database
            self.db.set_setting('smtp_server', server)
            self.db.set_setting('smtp_port', str(port))
            self.db.set_setting('smtp_username', username)
            self.db.set_setting('smtp_password', password)
            self.db.set_setting('smtp_use_tls', str(use_tls))
            
            # Test connection
            if self._test_smtp_connection():
                self.smtp_configured = True
                logger.info("SMTP configuration successful")
                return True
            else:
                logger.error("SMTP test failed")
                return False
                
        except Exception as e:
            logger.error(f"Error configuring SMTP: {e}")
            return False
    
    def _test_smtp_connection(self) -> bool:
        """Test SMTP connection"""
        try:
            server = self.db.get_setting('smtp_server')
            port = int(self.db.get_setting('smtp_port') or '587')
            username = self.db.get_setting('smtp_username')
            password = self.db.get_setting('smtp_password')
            use_tls = self.db.get_setting('smtp_use_tls') == 'True'
            
            smtp = smtplib.SMTP(server, port)
            if use_tls:
                smtp.starttls()
            smtp.login(username, password)
            smtp.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False
    
    def send_invoice_email(self, invoice: Invoice, participant: Participant, 
                          project: Project, pdf_data: bytes, 
                          custom_message: Optional[str] = None) -> bool:
        """Send invoice by email"""
        
        if not self.smtp_configured:
            logger.error("Cannot send email: SMTP not configured")
            return False
        
        if not participant.contact_email:
            logger.error("Cannot send email: participant has no email address")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.db.get_setting('smtp_username')
            msg['To'] = participant.contact_email
            msg['Subject'] = f"Facture {invoice.invoice_number} - Projet {project.name}"
            
            # Email body
            body = self._create_invoice_email_body(invoice, participant, project, custom_message)
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # Attach PDF
            pdf_attachment = MIMEBase('application', 'octet-stream')
            pdf_attachment.set_payload(pdf_data)
            encoders.encode_base64(pdf_attachment)
            pdf_attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="Facture_{invoice.invoice_number}.pdf"'
            )
            msg.attach(pdf_attachment)
            
            # Send email
            self._send_email(msg)
            
            logger.info(f"Invoice {invoice.invoice_number} sent to {participant.contact_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending invoice email: {e}")
            return False
    
    def send_billing_summary_email(self, project: Project, period_name: str,
                                  summary_pdf: bytes, recipient_emails: List[str],
                                  custom_message: Optional[str] = None) -> bool:
        """Send billing summary to project managers"""
        
        if not self.smtp_configured:
            logger.error("Cannot send email: SMTP not configured")
            return False
        
        if not recipient_emails:
            logger.error("Cannot send email: no recipient emails provided")
            return False
        
        try:
            for email in recipient_emails:
                # Create message
                msg = MIMEMultipart()
                msg['From'] = self.db.get_setting('smtp_username')
                msg['To'] = email
                msg['Subject'] = f"Résumé de facturation - {period_name} - Projet {project.name}"
                
                # Email body
                body = self._create_summary_email_body(project, period_name, custom_message)
                msg.attach(MIMEText(body, 'html', 'utf-8'))
                
                # Attach PDF
                pdf_attachment = MIMEBase('application', 'octet-stream')
                pdf_attachment.set_payload(summary_pdf)
                encoders.encode_base64(pdf_attachment)
                pdf_attachment.add_header(
                    'Content-Disposition',
                    f'attachment; filename="Resume_Facturation_{period_name.replace(" ", "_")}.pdf"'
                )
                msg.attach(pdf_attachment)
                
                # Send email
                self._send_email(msg)
                
                logger.info(f"Billing summary sent to {email}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending billing summary email: {e}")
            return False
    
    def send_payment_reminder(self, invoice: Invoice, participant: Participant,
                            project: Project, days_overdue: int) -> bool:
        """Send payment reminder email"""
        
        if not self.smtp_configured:
            logger.error("Cannot send email: SMTP not configured")
            return False
        
        if not participant.contact_email:
            logger.error("Cannot send email: participant has no email address")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.db.get_setting('smtp_username')
            msg['To'] = participant.contact_email
            msg['Subject'] = f"Rappel de paiement - Facture {invoice.invoice_number}"
            
            # Email body
            body = self._create_reminder_email_body(invoice, participant, project, days_overdue)
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # Send email
            self._send_email(msg)
            
            logger.info(f"Payment reminder sent to {participant.contact_email} for invoice {invoice.invoice_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending payment reminder: {e}")
            return False
    
    def _send_email(self, msg: MIMEMultipart):
        """Internal method to send email via SMTP"""
        server = self.db.get_setting('smtp_server')
        port = int(self.db.get_setting('smtp_port') or '587')
        username = self.db.get_setting('smtp_username')
        password = self.db.get_setting('smtp_password')
        use_tls = self.db.get_setting('smtp_use_tls') == 'True'
        
        smtp = smtplib.SMTP(server, port)
        if use_tls:
            smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(msg)
        smtp.quit()
    
    def _create_invoice_email_body(self, invoice: Invoice, participant: Participant,
                                  project: Project, custom_message: Optional[str] = None) -> str:
        """Create HTML email body for invoice"""
        
        company_name = self.db.get_setting('company_name') or 'OptimPV'
        
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #2E7D32; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .invoice-details {{ background-color: #f5f5f5; padding: 15px; margin: 20px 0; }}
                .footer {{ background-color: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; }}
                .amount {{ font-size: 18px; font-weight: bold; color: #2E7D32; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{company_name}</h1>
                <h2>Facture d'Autoconsommation Collective</h2>
            </div>
            
            <div class="content">
                <p>Bonjour {participant.name},</p>
                
                <p>Veuillez trouver ci-joint votre facture pour l'autoconsommation collective 
                   du projet <strong>{project.name}</strong>.</p>
                
                <div class="invoice-details">
                    <h3>Détails de la facture:</h3>
                    <ul>
                        <li><strong>Numéro:</strong> {invoice.invoice_number}</li>
                        <li><strong>Date d'émission:</strong> {invoice.issue_date.strftime('%d/%m/%Y') if invoice.issue_date else ''}</li>
                        <li><strong>Date d'échéance:</strong> {invoice.due_date.strftime('%d/%m/%Y') if invoice.due_date else ''}</li>
                        <li><strong>Montant total:</strong> <span class="amount">{invoice.total_amount:.2f} €</span></li>
                    </ul>
                </div>
                
                {f'<div style="background-color: #e8f5e8; padding: 15px; margin: 20px 0; border-left: 4px solid #2E7D32;"><p>{custom_message}</p></div>' if custom_message else ''}
                
                <p>Cette facture correspond à votre consommation d'énergie solaire produite 
                   collectivement sur le projet. L'autoconsommation collective vous permet 
                   de bénéficier d'une énergie verte à prix préférentiel.</p>
                
                <p>Pour toute question concernant cette facture, n'hésitez pas à nous contacter.</p>
                
                <p>Cordialement,<br>
                L'équipe {company_name}</p>
            </div>
            
            <div class="footer">
                <p>Cet email a été généré automatiquement par le système de facturation {company_name}.</p>
            </div>
        </body>
        </html>
        """
        
        return body
    
    def _create_summary_email_body(self, project: Project, period_name: str,
                                  custom_message: Optional[str] = None) -> str:
        """Create HTML email body for billing summary"""
        
        company_name = self.db.get_setting('company_name') or 'OptimPV'
        
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #2E7D32; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .summary {{ background-color: #f5f5f5; padding: 15px; margin: 20px 0; }}
                .footer {{ background-color: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{company_name}</h1>
                <h2>Résumé de Facturation</h2>
            </div>
            
            <div class="content">
                <p>Bonjour,</p>
                
                <p>Veuillez trouver ci-joint le résumé de facturation pour la période 
                   <strong>{period_name}</strong> du projet <strong>{project.name}</strong>.</p>
                
                <div class="summary">
                    <h3>Informations du projet:</h3>
                    <ul>
                        <li><strong>Nom:</strong> {project.name}</li>
                        <li><strong>Client:</strong> {project.client_name}</li>
                        <li><strong>Période:</strong> {period_name}</li>
                        <li><strong>Date de génération:</strong> {datetime.now().strftime('%d/%m/%Y à %H:%M')}</li>
                    </ul>
                </div>
                
                {f'<div style="background-color: #e8f5e8; padding: 15px; margin: 20px 0; border-left: 4px solid #2E7D32;"><p>{custom_message}</p></div>' if custom_message else ''}
                
                <p>Ce résumé contient le détail de toutes les factures générées pour cette période, 
                   incluant les montants par participant et les totaux.</p>
                
                <p>Cordialement,<br>
                L'équipe {company_name}</p>
            </div>
            
            <div class="footer">
                <p>Cet email a été généré automatiquement par le système de facturation {company_name}.</p>
            </div>
        </body>
        </html>
        """
        
        return body
    
    def _create_reminder_email_body(self, invoice: Invoice, participant: Participant,
                                   project: Project, days_overdue: int) -> str:
        """Create HTML email body for payment reminder"""
        
        company_name = self.db.get_setting('company_name') or 'OptimPV'
        
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #FF6B35; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .alert {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0; }}
                .invoice-details {{ background-color: #f5f5f5; padding: 15px; margin: 20px 0; }}
                .footer {{ background-color: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; }}
                .amount {{ font-size: 18px; font-weight: bold; color: #FF6B35; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{company_name}</h1>
                <h2>Rappel de Paiement</h2>
            </div>
            
            <div class="content">
                <p>Bonjour {participant.name},</p>
                
                <div class="alert">
                    <h3>⚠️ Facture en retard de paiement</h3>
                    <p>Notre système indique que la facture ci-dessous est en retard de <strong>{days_overdue} jour(s)</strong>.</p>
                </div>
                
                <div class="invoice-details">
                    <h3>Détails de la facture en retard:</h3>
                    <ul>
                        <li><strong>Numéro:</strong> {invoice.invoice_number}</li>
                        <li><strong>Date d'émission:</strong> {invoice.issue_date.strftime('%d/%m/%Y') if invoice.issue_date else ''}</li>
                        <li><strong>Date d'échéance:</strong> {invoice.due_date.strftime('%d/%m/%Y') if invoice.due_date else ''}</li>
                        <li><strong>Montant à payer:</strong> <span class="amount">{invoice.total_amount:.2f} €</span></li>
                        <li><strong>Projet:</strong> {project.name}</li>
                    </ul>
                </div>
                
                <p>Nous vous remercions de bien vouloir régulariser cette situation dans les plus brefs délais.</p>
                
                <p>Si vous avez déjà effectué le paiement, merci de nous en informer en nous transmettant 
                   la preuve de virement.</p>
                
                <p>Pour toute question ou difficulté de paiement, n'hésitez pas à nous contacter 
                   afin que nous puissions trouver une solution ensemble.</p>
                
                <p>Cordialement,<br>
                L'équipe {company_name}</p>
            </div>
            
            <div class="footer">
                <p>Cet email a été généré automatiquement par le système de facturation {company_name}.</p>
            </div>
        </body>
        </html>
        """
        
        return body