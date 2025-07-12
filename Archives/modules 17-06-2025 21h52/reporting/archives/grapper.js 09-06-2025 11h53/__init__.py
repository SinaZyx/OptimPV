# Module de reporting modulaire - Structure optimisée
try:
    from .commercial_main import CommercialCustomerReportModule
    COMMERCIAL_MODULE_AVAILABLE = True
except ImportError:
    COMMERCIAL_MODULE_AVAILABLE = False

# Classe principale pour le reporting commercial
class ReportingModule:
    """
    Module de reporting OptimPV simplifié - Focus sur la proposition commerciale professionnelle.
    """
    
    def __init__(self):
        """Initialise le module de reporting commercial"""
        if COMMERCIAL_MODULE_AVAILABLE:
            self._commercial_module = CommercialCustomerReportModule()
        else:
            self._commercial_module = None
    
    def show_ui(self):
        """Interface utilisateur simplifiée - Direct vers rapport commercial"""
        import streamlit as st
        
        if COMMERCIAL_MODULE_AVAILABLE and self._commercial_module:
            # Interface directe vers le rapport commercial
            self._commercial_module.show_ui()
        else:
            st.error("❌ Module de rapport commercial non disponible")
            st.info("Veuillez vérifier l'installation du système de reporting.")
    
    # Méthodes de compatibilité pour l'ancien code (redirigent vers commercial)
    def generate_html_report(self, *args, **kwargs):
        """Génère un rapport HTML commercial"""
        if self._commercial_module:
            return self._commercial_module.generate_report(*args, **kwargs)
        return None
    
    def generate_pdf_report(self, *args, **kwargs):
        """Génère un rapport PDF commercial"""
        if self._commercial_module:
            return self._commercial_module._convert_to_pdf(self.generate_html_report(*args, **kwargs))
        return None
    
    def format_number(self, *args, **kwargs):
        """Formate un nombre"""
        if self._commercial_module:
            return self._commercial_module.format_number(*args, **kwargs)
        return str(args[0]) if args else ""
    
    def format_currency(self, *args, **kwargs):
        """Formate une devise"""
        if self._commercial_module:
            return self._commercial_module.format_currency(*args, **kwargs)
        return f"{args[0]:,.0f} €".replace(',', ' ') if args else "0 €"
    
    def format_percentage(self, *args, **kwargs):
        """Formate un pourcentage"""
        if self._commercial_module:
            return self._commercial_module.format_percentage(*args, **kwargs)
        return f"{args[0]:.1f}%" if args else "0%"

__all__ = ['CommercialCustomerReportModule', 'ReportingModule']