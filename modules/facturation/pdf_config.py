"""
PDF Configuration System for OptimPV Billing Module
Manages template configurations, colors, fonts, and multi-language support
"""

import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class TemplateConfig:
    """Configuration for a PDF template"""
    
    # Template identification
    name: str = "default"
    description: str = "Default template"
    
    # Colors (hex codes)
    colors: Dict[str, str] = None
    
    # Fonts
    fonts: Dict[str, Dict[str, Any]] = None
    
    # Layout and spacing
    margins: Dict[str, float] = None  # in mm
    
    # Logo configuration
    logo_path: str = ""
    logo_width: float = 30  # in mm
    logo_height: float = 15  # in mm
    
    # Table styling
    table_style: Dict[str, Any] = None
    
    # Multi-language texts
    texts: Dict[str, Dict[str, str]] = None
    
    def __post_init__(self):
        """Initialize default values"""
        if self.colors is None:
            self.colors = {
                'primary': '#2E7D32',      # Green primary
                'secondary': '#666666',     # Gray secondary
                'text': '#333333',         # Dark gray text
                'background': '#FFFFFF',    # White background
                'table_header': '#E8F5E8', # Light green header
                'table_alt': '#F8F8F8',    # Light gray alternating
                'border': '#CCCCCC',       # Light gray borders
                'accent': '#4CAF50'        # Bright green accent
            }
        
        if self.fonts is None:
            self.fonts = {
                'title': {'name': 'Helvetica-Bold', 'size': 20},
                'heading': {'name': 'Helvetica-Bold', 'size': 14},
                'body': {'name': 'Helvetica', 'size': 10},
                'footer': {'name': 'Helvetica', 'size': 9}
            }
        
        if self.margins is None:
            self.margins = {
                'top': 20,
                'bottom': 20,
                'left': 20,
                'right': 20
            }
        
        if self.table_style is None:
            self.table_style = {
                'header_height': 12,
                'row_height': 8,
                'border_width': 1,
                'grid_color': self.colors['border'] if self.colors else '#CCCCCC'
            }
        
        if self.texts is None:
            self._init_default_texts()
    
    def _init_default_texts(self):
        """Initialize default multi-language texts"""
        self.texts = {
            'fr': {
                # Document titles
                'invoice_title': 'FACTURE',
                'credit_note_title': 'AVOIR',
                'quote_title': 'DEVIS',
                
                # Labels
                'invoice_number': 'Facture N°',
                'credit_note_number': 'Avoir N°',
                'quote_number': 'Devis N°',
                'issue_date': 'Date d\'émission',
                'due_date': 'Date d\'échéance',
                'quote_date': 'Date du devis',
                'valid_until': 'Valable jusqu\'au',
                'project': 'Projet',
                'bill_to': 'Facturé à',
                'quote_for': 'Devis pour',
                
                # Table headers
                'description': 'Description',
                'quantity': 'Quantité',
                'unit_price': 'Prix unitaire',
                'total': 'Total',
                
                # Totals
                'subtotal': 'Sous-total HT',
                'vat': 'TVA',
                'total': 'Total TTC',
                
                # Payment
                'qr_payment': 'Paiement par QR Code',
                'qr_payment_desc': 'Scannez avec votre app bancaire',
                'payment_terms': 'Conditions de paiement',
                'days_net': 'jours net',
                'payment_method': 'Mode de paiement',
                'bank_transfer': 'Virement bancaire',
                'late_payment_penalty': 'En cas de retard de paiement, des pénalités de 3 fois le taux d\'intérêt légal seront appliquées.',
                'thank_you': 'Merci de votre confiance !',
                
                # Quote conditions
                'quote_conditions_title': 'Conditions générales',
                'quote_condition_1': 'Devis valable 30 jours à compter de la date d\'émission',
                'quote_condition_2': 'Prix fermes et définitifs, non révisables',
                'quote_condition_3': 'Règlement à 30 jours fin de mois',
                'quote_condition_4': 'Installation conforme aux normes en vigueur',
                
                # Watermarks
                'watermark_draft': 'BROUILLON',
                'watermark_paid': 'PAYÉ',
                'watermark_cancelled': 'ANNULÉ',
                'watermark_overdue': 'IMPAYÉ'
            },
            'en': {
                # Document titles
                'invoice_title': 'INVOICE',
                'credit_note_title': 'CREDIT NOTE',
                'quote_title': 'QUOTE',
                
                # Labels
                'invoice_number': 'Invoice No.',
                'credit_note_number': 'Credit Note No.',
                'quote_number': 'Quote No.',
                'issue_date': 'Issue Date',
                'due_date': 'Due Date',
                'quote_date': 'Quote Date',
                'valid_until': 'Valid Until',
                'project': 'Project',
                'bill_to': 'Bill To',
                'quote_for': 'Quote For',
                
                # Table headers
                'description': 'Description',
                'quantity': 'Quantity',
                'unit_price': 'Unit Price',
                'total': 'Total',
                
                # Totals
                'subtotal': 'Subtotal',
                'vat': 'VAT',
                'total': 'Total',
                
                # Payment
                'qr_payment': 'QR Code Payment',
                'qr_payment_desc': 'Scan with your banking app',
                'payment_terms': 'Payment Terms',
                'days_net': 'days net',
                'payment_method': 'Payment Method',
                'bank_transfer': 'Bank Transfer',
                'late_payment_penalty': 'Late payment penalties of 3 times the legal interest rate will apply.',
                'thank_you': 'Thank you for your trust!',
                
                # Quote conditions
                'quote_conditions_title': 'General Conditions',
                'quote_condition_1': 'Quote valid for 30 days from issue date',
                'quote_condition_2': 'Fixed and final prices, non-revisable',
                'quote_condition_3': 'Payment within 30 days end of month',
                'quote_condition_4': 'Installation compliant with current standards',
                
                # Watermarks
                'watermark_draft': 'DRAFT',
                'watermark_paid': 'PAID',
                'watermark_cancelled': 'CANCELLED',
                'watermark_overdue': 'OVERDUE'
            }
        }
    
    def get_text(self, key: str, language: str = 'fr') -> str:
        """Get localized text"""
        if language in self.texts and key in self.texts[language]:
            return self.texts[language][key]
        elif 'fr' in self.texts and key in self.texts['fr']:
            # Fallback to French
            return self.texts['fr'][key]
        else:
            # Fallback to key itself
            logger.warning(f"Missing text for key '{key}' in language '{language}'")
            return key
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateConfig':
        """Create from dictionary"""
        return cls(**data)


class PDFConfig:
    """Main configuration manager for PDF templates"""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = config_dir or self._get_default_config_dir()
        self.templates: Dict[str, TemplateConfig] = {}
        self._load_templates()
    
    def _get_default_config_dir(self) -> str:
        """Get default configuration directory"""
        current_dir = Path(__file__).parent
        config_dir = current_dir / "templates"
        config_dir.mkdir(exist_ok=True)
        return str(config_dir)
    
    def _load_templates(self):
        """Load template configurations"""
        # Load default templates
        self._load_default_templates()
        
        # Load custom templates from config directory
        self._load_custom_templates()
    
    def _load_default_templates(self):
        """Load built-in default templates"""
        
        # Modern OptimPV template
        modern_config = TemplateConfig(
            name="modern",
            description="Modern OptimPV template with clean design",
            colors={
                'primary': '#2E7D32',      # OptimPV Green
                'secondary': '#666666',
                'text': '#333333',
                'background': '#FFFFFF',
                'table_header': '#E8F5E8',
                'table_alt': '#F9F9F9',
                'border': '#DDDDDD',
                'accent': '#4CAF50'
            }
        )
        
        # Minimalist template
        minimal_config = TemplateConfig(
            name="minimal",
            description="Clean minimalist template",
            colors={
                'primary': '#000000',
                'secondary': '#777777',
                'text': '#333333',
                'background': '#FFFFFF',
                'table_header': '#F5F5F5',
                'table_alt': '#FAFAFA',
                'border': '#E0E0E0',
                'accent': '#333333'
            },
            fonts={
                'title': {'name': 'Helvetica-Bold', 'size': 18},
                'heading': {'name': 'Helvetica-Bold', 'size': 12},
                'body': {'name': 'Helvetica', 'size': 9},
                'footer': {'name': 'Helvetica', 'size': 8}
            }
        )
        
        # Corporate template
        corporate_config = TemplateConfig(
            name="corporate",
            description="Formal corporate template",
            colors={
                'primary': '#1B365D',      # Dark blue
                'secondary': '#4A6B8A',
                'text': '#2C3E50',
                'background': '#FFFFFF',
                'table_header': '#EBF2F7',
                'table_alt': '#F8F9FA',
                'border': '#BDC3C7',
                'accent': '#3498DB'
            },
            fonts={
                'title': {'name': 'Helvetica-Bold', 'size': 22},
                'heading': {'name': 'Helvetica-Bold', 'size': 14},
                'body': {'name': 'Helvetica', 'size': 10},
                'footer': {'name': 'Helvetica', 'size': 9}
            },
            margins={
                'top': 25,
                'bottom': 25,
                'left': 25,
                'right': 25
            }
        )
        
        self.templates.update({
            'default': modern_config,
            'modern': modern_config,
            'minimal': minimal_config,
            'corporate': corporate_config
        })
    
    def _load_custom_templates(self):
        """Load custom templates from config directory"""
        config_path = Path(self.config_dir)
        
        for json_file in config_path.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                template_config = TemplateConfig.from_dict(data)
                self.templates[template_config.name] = template_config
                
                logger.info(f"Loaded custom template: {template_config.name}")
                
            except Exception as e:
                logger.error(f"Error loading template from {json_file}: {e}")
    
    def get_template_config(self, name: str) -> Optional[TemplateConfig]:
        """Get template configuration by name"""
        return self.templates.get(name)
    
    def save_template(self, template_config: TemplateConfig):
        """Save template configuration to file"""
        config_path = Path(self.config_dir) / f"{template_config.name}.json"
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(template_config.to_dict(), f, indent=2, ensure_ascii=False)
            
            # Update in-memory templates
            self.templates[template_config.name] = template_config
            
            logger.info(f"Saved template configuration: {template_config.name}")
            
        except Exception as e:
            logger.error(f"Error saving template {template_config.name}: {e}")
            raise
    
    def delete_template(self, name: str) -> bool:
        """Delete a custom template"""
        if name in ['default', 'modern', 'minimal', 'corporate']:
            logger.error(f"Cannot delete built-in template: {name}")
            return False
        
        config_path = Path(self.config_dir) / f"{name}.json"
        
        try:
            if config_path.exists():
                config_path.unlink()
            
            if name in self.templates:
                del self.templates[name]
            
            logger.info(f"Deleted template: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting template {name}: {e}")
            return False
    
    def list_templates(self) -> Dict[str, str]:
        """List available templates with descriptions"""
        return {
            name: config.description
            for name, config in self.templates.items()
        }
    
    def create_custom_template(self, name: str, base_template: str = 'default',
                             modifications: Optional[Dict[str, Any]] = None) -> TemplateConfig:
        """Create a custom template based on an existing one"""
        base_config = self.get_template_config(base_template)
        if not base_config:
            raise ValueError(f"Base template '{base_template}' not found")
        
        # Create a copy of the base configuration
        new_config_data = base_config.to_dict()
        new_config_data['name'] = name
        new_config_data['description'] = f"Custom template based on {base_template}"
        
        # Apply modifications
        if modifications:
            for key, value in modifications.items():
                if key in new_config_data:
                    if isinstance(new_config_data[key], dict) and isinstance(value, dict):
                        new_config_data[key].update(value)
                    else:
                        new_config_data[key] = value
        
        new_config = TemplateConfig.from_dict(new_config_data)
        return new_config
    
    def set_logo(self, template_name: str, logo_path: str, 
                width: float = 30, height: float = 15):
        """Set logo for a template"""
        config = self.get_template_config(template_name)
        if not config:
            raise ValueError(f"Template '{template_name}' not found")
        
        if not os.path.exists(logo_path):
            raise FileNotFoundError(f"Logo file not found: {logo_path}")
        
        config.logo_path = logo_path
        config.logo_width = width
        config.logo_height = height
        
        # Save if it's a custom template
        if template_name not in ['default', 'modern', 'minimal', 'corporate']:
            self.save_template(config)
    
    def update_colors(self, template_name: str, colors: Dict[str, str]):
        """Update colors for a template"""
        config = self.get_template_config(template_name)
        if not config:
            raise ValueError(f"Template '{template_name}' not found")
        
        config.colors.update(colors)
        
        # Save if it's a custom template
        if template_name not in ['default', 'modern', 'minimal', 'corporate']:
            self.save_template(config)
    
    def update_texts(self, template_name: str, texts: Dict[str, Dict[str, str]]):
        """Update texts for a template"""
        config = self.get_template_config(template_name)
        if not config:
            raise ValueError(f"Template '{template_name}' not found")
        
        for language, language_texts in texts.items():
            if language not in config.texts:
                config.texts[language] = {}
            config.texts[language].update(language_texts)
        
        # Save if it's a custom template
        if template_name not in ['default', 'modern', 'minimal', 'corporate']:
            self.save_template(config)
    
    def export_template(self, template_name: str, export_path: str):
        """Export template configuration to a file"""
        config = self.get_template_config(template_name)
        if not config:
            raise ValueError(f"Template '{template_name}' not found")
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported template '{template_name}' to {export_path}")
    
    def import_template(self, import_path: str) -> str:
        """Import template configuration from a file"""
        with open(import_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        config = TemplateConfig.from_dict(data)
        self.save_template(config)
        
        logger.info(f"Imported template: {config.name}")
        return config.name


# Global configuration instance
_global_config = None

def get_pdf_config(config_dir: Optional[str] = None) -> PDFConfig:
    """Get global PDF configuration instance"""
    global _global_config
    
    if _global_config is None or config_dir is not None:
        _global_config = PDFConfig(config_dir)
    
    return _global_config


# Template validation functions
def validate_template_config(config: TemplateConfig) -> List[str]:
    """Validate template configuration and return list of errors"""
    errors = []
    
    # Check required fields
    if not config.name:
        errors.append("Template name is required")
    
    # Validate colors
    for color_name, color_value in config.colors.items():
        if not color_value.startswith('#') or len(color_value) != 7:
            errors.append(f"Invalid color format for '{color_name}': {color_value}")
    
    # Validate fonts
    valid_fonts = ['Helvetica', 'Helvetica-Bold', 'Times-Roman', 'Times-Bold']
    for font_type, font_config in config.fonts.items():
        if font_config['name'] not in valid_fonts:
            errors.append(f"Invalid font '{font_config['name']}' for {font_type}")
        
        if not isinstance(font_config['size'], (int, float)) or font_config['size'] <= 0:
            errors.append(f"Invalid font size for {font_type}: {font_config['size']}")
    
    # Validate margins
    for margin_name, margin_value in config.margins.items():
        if not isinstance(margin_value, (int, float)) or margin_value < 0:
            errors.append(f"Invalid margin value for '{margin_name}': {margin_value}")
    
    # Validate logo dimensions
    if config.logo_width <= 0 or config.logo_height <= 0:
        errors.append("Logo dimensions must be positive")
    
    return errors


def create_template_example():
    """Create an example template configuration file"""
    example_config = TemplateConfig(
        name="example",
        description="Example custom template",
        colors={
            'primary': '#FF5722',      # Orange
            'secondary': '#666666',
            'text': '#333333',
            'background': '#FFFFFF',
            'table_header': '#FFF3E0',
            'table_alt': '#F9F9F9',
            'border': '#DDDDDD',
            'accent': '#FF7043'
        }
    )
    
    return example_config