"""
Système de génération de rapports DOCX pour OptimPV
Module complet avec templates Word modifiables et génération automatique
"""

# Imports des modules essentiels uniquement
try:
    from .template_based_generator import TemplateBasedGenerator as DocxTemplateGenerator
except ImportError:
    DocxTemplateGenerator = None

try:
    from .data_extractor import OptimPVDataExtractor
except ImportError:
    OptimPVDataExtractor = None

try:
    from .dependency_manager import DocxDependencyManager
except ImportError:
    DocxDependencyManager = None

try:
    from .premium_commercial_generator import PremiumCommercialGenerator
except ImportError:
    PremiumCommercialGenerator = None

__all__ = [
    'DocxTemplateGenerator',
    'OptimPVDataExtractor',
    'DocxDependencyManager',
    'PremiumCommercialGenerator'
]