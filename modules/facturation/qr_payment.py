"""
QR Code Payment Generator for OptimPV Billing Module
Generates EPC QR Codes compatible with European banking apps for SEPA payments
"""

import logging
from typing import Optional, Dict, Any, TYPE_CHECKING
from io import BytesIO
import re

if TYPE_CHECKING:
    from qrcode.image.pil import PilImage

try:
    import qrcode
    from qrcode.image.pil import PilImage
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    # Fallback type pour éviter les erreurs de type hints
    PilImage = Any

logger = logging.getLogger(__name__)


class QRPaymentGenerator:
    """Generator for EPC QR Codes for SEPA payments"""
    
    def __init__(self):
        if not QRCODE_AVAILABLE:
            logger.warning("qrcode library not available. QR code generation will be disabled.")
            logger.info("Install with: pip install qrcode[pil]")
    
    def generate_payment_qr(self, iban: str, amount: float, reference: str,
                          creditor_name: str, creditor_address: str = "",
                          bic: str = "", remittance_info: str = "",
                          debtor_name: str = "", debtor_address: str = "") -> Optional[bytes]:
        """
        Generate EPC QR Code for SEPA payment
        
        Args:
            iban: Creditor's IBAN
            amount: Payment amount in EUR (max 2 decimal places)
            reference: Payment reference/invoice number
            creditor_name: Name of the creditor (max 70 chars)
            creditor_address: Address of creditor (optional, max 70 chars)
            bic: BIC/SWIFT code (optional for domestic payments)
            remittance_info: Additional payment information (max 140 chars)
            debtor_name: Name of debtor (optional, max 70 chars)
            debtor_address: Address of debtor (optional, max 70 chars)
        
        Returns:
            QR code image as bytes, or None if generation fails
        """
        
        if not QRCODE_AVAILABLE:
            logger.error("Cannot generate QR code: qrcode library not installed")
            return None
        
        try:
            # Validate and format inputs
            formatted_iban = self._format_iban(iban)
            if not formatted_iban:
                logger.error(f"Invalid IBAN: {iban}")
                return None
            
            if not self._validate_amount(amount):
                logger.error(f"Invalid amount: {amount}")
                return None
            
            # Format amount to 2 decimal places
            amount_str = f"EUR{amount:.2f}"
            
            # Truncate text fields to maximum lengths
            creditor_name = self._truncate_text(creditor_name, 70)
            creditor_address = self._truncate_text(creditor_address, 70)
            reference = self._truncate_text(reference, 35)
            remittance_info = self._truncate_text(remittance_info, 140)
            debtor_name = self._truncate_text(debtor_name, 70)
            debtor_address = self._truncate_text(debtor_address, 70)
            
            # Build EPC QR Code data according to EPC069-12 standard
            epc_data = self._build_epc_data(
                service_tag="BCD",
                version="002",
                character_set="1",  # UTF-8
                identification="SCT",  # SEPA Credit Transfer
                bic=bic,
                creditor_name=creditor_name,
                creditor_iban=formatted_iban,
                amount=amount_str,
                purpose="",  # Not used for invoices
                structured_reference=reference,
                unstructured_remittance=remittance_info,
                beneficiary_to_originator_info=""
            )
            
            # Generate QR code
            qr_image = self._create_qr_code(epc_data)
            if not qr_image:
                return None
            
            # Convert to bytes
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')
            qr_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Generated EPC QR code for IBAN {formatted_iban}, amount {amount:.2f} EUR")
            return qr_bytes
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return None
    
    def _format_iban(self, iban: str) -> Optional[str]:
        """Format and validate IBAN"""
        if not iban:
            return None
        
        # Remove spaces and convert to uppercase
        iban = re.sub(r'\s+', '', iban.upper())
        
        # Basic IBAN validation (length and format)
        if not re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{4,30}$', iban):
            return None
        
        # Check length for common countries
        country_lengths = {
            'AD': 24, 'AE': 23, 'AL': 28, 'AT': 20, 'AZ': 28, 'BA': 20, 'BE': 16,
            'BG': 22, 'BH': 22, 'BR': 29, 'BY': 28, 'CH': 21, 'CR': 22, 'CY': 28,
            'CZ': 24, 'DE': 22, 'DK': 18, 'DO': 28, 'EE': 20, 'EG': 29, 'ES': 24,
            'FI': 18, 'FO': 18, 'FR': 27, 'GB': 22, 'GE': 22, 'GI': 23, 'GL': 18,
            'GR': 27, 'GT': 28, 'HR': 21, 'HU': 28, 'IE': 22, 'IL': 23, 'IS': 26,
            'IT': 27, 'JO': 30, 'KW': 30, 'KZ': 20, 'LB': 28, 'LC': 32, 'LI': 21,
            'LT': 20, 'LU': 20, 'LV': 21, 'MC': 27, 'MD': 24, 'ME': 22, 'MK': 19,
            'MR': 27, 'MT': 31, 'MU': 30, 'NL': 18, 'NO': 15, 'PK': 24, 'PL': 28,
            'PS': 29, 'PT': 25, 'QA': 29, 'RO': 24, 'RS': 22, 'SA': 24, 'SE': 24,
            'SI': 19, 'SK': 24, 'SM': 27, 'TN': 24, 'TR': 26, 'UA': 29, 'VG': 24,
            'XK': 20
        }
        
        country_code = iban[:2]
        expected_length = country_lengths.get(country_code)
        
        if expected_length and len(iban) != expected_length:
            logger.warning(f"IBAN length mismatch for {country_code}: expected {expected_length}, got {len(iban)}")
            return None
        
        return iban
    
    def _validate_amount(self, amount: float) -> bool:
        """Validate payment amount"""
        if amount <= 0:
            return False
        
        if amount > 999999999.99:  # EPC standard maximum
            return False
        
        # Check for more than 2 decimal places
        if round(amount, 2) != amount:
            return False
        
        return True
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to maximum length"""
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        logger.warning(f"Text truncated from {len(text)} to {max_length} characters")
        return text[:max_length]
    
    def _build_epc_data(self, service_tag: str, version: str, character_set: str,
                       identification: str, bic: str, creditor_name: str,
                       creditor_iban: str, amount: str, purpose: str,
                       structured_reference: str, unstructured_remittance: str,
                       beneficiary_to_originator_info: str) -> str:
        """
        Build EPC QR Code data string according to EPC069-12 standard
        
        Format:
        Line 1: Service Tag (BCD)
        Line 2: Version (002)
        Line 3: Character set (1 = UTF-8)
        Line 4: Identification (SCT)
        Line 5: BIC
        Line 6: Beneficiary Name
        Line 7: Beneficiary Account (IBAN)
        Line 8: Amount
        Line 9: Purpose (4 character purpose code)
        Line 10: Structured Reference (max 35 chars)
        Line 11: Unstructured Remittance Information (max 140 chars)
        Line 12: Beneficiary to originator information
        """
        
        epc_lines = [
            service_tag,
            version,
            character_set,
            identification,
            bic,
            creditor_name,
            creditor_iban,
            amount,
            purpose,
            structured_reference,
            unstructured_remittance,
            beneficiary_to_originator_info
        ]
        
        # Join with line feed characters
        epc_data = '\n'.join(epc_lines)
        
        # EPC standard limits total data to 331 characters
        if len(epc_data) > 331:
            logger.warning(f"EPC data exceeds 331 character limit: {len(epc_data)} characters")
            # Try to truncate unstructured remittance information
            excess = len(epc_data) - 331
            if len(unstructured_remittance) >= excess:
                unstructured_remittance = unstructured_remittance[:-excess]
                epc_lines[10] = unstructured_remittance
                epc_data = '\n'.join(epc_lines)
            else:
                logger.error("Cannot reduce EPC data to 331 characters")
        
        return epc_data
    
    def _create_qr_code(self, data: str) -> Optional["PilImage"]:
        """Create QR code image from data"""
        if not QRCODE_AVAILABLE:
            logger.warning("QR code generation disabled - qrcode library not available")
            return None
            
        try:
            qr = qrcode.QRCode(
                version=1,  # Start with smallest version
                error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction
                box_size=10,
                border=4,
            )
            
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            return img
            
        except Exception as e:
            logger.error(f"Error creating QR code image: {e}")
            return None
    
    def validate_epc_qr_data(self, data: str) -> Dict[str, Any]:
        """
        Validate EPC QR code data and extract information
        
        Returns:
            Dictionary with validation results and extracted data
        """
        result = {
            'valid': False,
            'errors': [],
            'data': {}
        }
        
        try:
            lines = data.split('\n')
            
            if len(lines) != 12:
                result['errors'].append(f"Expected 12 lines, got {len(lines)}")
                return result
            
            # Validate each field
            service_tag, version, charset, identification, bic, creditor_name, \
            creditor_iban, amount, purpose, structured_ref, unstructured_ref, \
            beneficiary_info = lines
            
            # Service tag must be "BCD"
            if service_tag != "BCD":
                result['errors'].append(f"Invalid service tag: {service_tag}")
            
            # Version must be "002"
            if version != "002":
                result['errors'].append(f"Invalid version: {version}")
            
            # Character set must be "1" (UTF-8)
            if charset != "1":
                result['errors'].append(f"Invalid character set: {charset}")
            
            # Identification must be "SCT"
            if identification != "SCT":
                result['errors'].append(f"Invalid identification: {identification}")
            
            # Validate IBAN
            if not self._format_iban(creditor_iban):
                result['errors'].append(f"Invalid IBAN: {creditor_iban}")
            
            # Validate amount format
            if amount.startswith("EUR"):
                try:
                    amount_value = float(amount[3:])
                    if not self._validate_amount(amount_value):
                        result['errors'].append(f"Invalid amount: {amount_value}")
                except ValueError:
                    result['errors'].append(f"Invalid amount format: {amount}")
            else:
                result['errors'].append(f"Amount must start with 'EUR': {amount}")
            
            # Extract data
            result['data'] = {
                'service_tag': service_tag,
                'version': version,
                'character_set': charset,
                'identification': identification,
                'bic': bic,
                'creditor_name': creditor_name,
                'creditor_iban': creditor_iban,
                'amount': amount,
                'purpose': purpose,
                'structured_reference': structured_ref,
                'unstructured_remittance': unstructured_ref,
                'beneficiary_info': beneficiary_info
            }
            
            # Check overall data length
            if len(data) > 331:
                result['errors'].append(f"Data exceeds 331 character limit: {len(data)}")
            
            result['valid'] = len(result['errors']) == 0
            
        except Exception as e:
            result['errors'].append(f"Error parsing EPC data: {e}")
        
        return result
    
    def generate_simple_qr(self, text: str, size: int = 10) -> Optional[bytes]:
        """
        Generate a simple QR code for any text
        
        Args:
            text: Text to encode
            size: Box size for QR code
            
        Returns:
            QR code image as bytes, or None if generation fails
        """
        
        if not QRCODE_AVAILABLE:
            logger.error("Cannot generate QR code: qrcode library not installed")
            return None
        
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=size,
                border=4,
            )
            
            qr.add_data(text)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_bytes = buffer.getvalue()
            buffer.close()
            
            return qr_bytes
            
        except Exception as e:
            logger.error(f"Error generating simple QR code: {e}")
            return None


def test_qr_generation():
    """Test function for QR code generation"""
    generator = QRPaymentGenerator()
    
    # Test data
    test_data = {
        'iban': 'FR14 2004 1010 0505 0001 3M02 606',
        'amount': 1250.50,
        'reference': 'FACT-2024-001',
        'creditor_name': 'OptimPV SAS',
        'creditor_address': '123 Rue de la Paix, 75001 Paris',
        'bic': 'BNPAFRPP',
        'remittance_info': 'Facture système photovoltaïque - Projet Solaire 2024'
    }
    
    qr_bytes = generator.generate_payment_qr(**test_data)
    
    if qr_bytes:
        print(f"Successfully generated QR code ({len(qr_bytes)} bytes)")
        
        # Save to file for testing
        with open('test_qr.png', 'wb') as f:
            f.write(qr_bytes)
        print("QR code saved as test_qr.png")
    else:
        print("Failed to generate QR code")


if __name__ == "__main__":
    test_qr_generation()