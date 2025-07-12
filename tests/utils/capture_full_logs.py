#!/usr/bin/env python3
"""
Script pour capturer tous les logs d'OptimPV pendant l'optimisation
"""

import logging
import sys
from datetime import datetime

def setup_complete_logging():
    """Configure un logging complet pour débugger l'optimisation"""
    
    # Créer un fichier de log complet
    log_file = f"debug_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Configuration du logging root pour capturer TOUT
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Logger spécifique pour les modules critiques
    critical_modules = [
        'modules.engine_module.core_analyzer',
        'modules.engine_module.financial_calculations',
        'modules.engine_module.equity_calculations',
        'modules.engine_module.treasury_placement'
    ]
    
    for module_name in critical_modules:
        logger = logging.getLogger(module_name)
        logger.setLevel(logging.DEBUG)
    
    print(f"🔍 LOGGING COMPLET ACTIVÉ")
    print(f"Fichier de log: {log_file}")
    print(f"Modules surveillés: {len(critical_modules)}")
    
    return log_file

def log_optimization_attempt():
    """Log d'une tentative d'optimisation"""
    
    logger = logging.getLogger(__name__)
    logger.info("=== DÉBUT TENTATIVE OPTIMISATION LCOE ===")
    logger.info("Configuration:")
    logger.info("- CAPEX divisé par 10")
    logger.info("- Placement trésorerie: DÉSACTIVÉ") 
    logger.info("- 4 petites maisons")
    logger.info("=====================================")

if __name__ == "__main__":
    
    print("🔧 SETUP DEBUG OPTIMISATION LCOE")
    print("=" * 40)
    
    log_file = setup_complete_logging()
    log_optimization_attempt()
    
    print(f"\n💡 INSTRUCTIONS:")
    print(f"1. Ce script a configuré un logging complet")
    print(f"2. Lancez OptimPV maintenant")
    print(f"3. Tentez l'optimisation LCOE")
    print(f"4. Consultez le fichier: {log_file}")
    print(f"5. Cherchez les mots-clés:")
    print(f"   - ERROR")
    print(f"   - SIMULATE_PRICE_DEBUG")
    print(f"   - calculate_financial_indicators")
    print(f"   - NPV = nan")
    print(f"   - RuntimeError")
    
    print(f"\n🚨 ATTENTION:")
    print(f"Ce logging peut générer BEAUCOUP de logs.")
    print(f"Désactivez-le après le test en redémarrant Python.")