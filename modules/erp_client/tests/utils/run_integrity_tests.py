#!/usr/bin/env python3
"""
Script d'exécution des tests d'intégrité pour le module erp_client.
Fournit un rapport détaillé et des solutions pour corriger les problèmes d'imports.
"""

import sys
from pathlib import Path

# Ajouter le chemin racine du projet
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from modules.erp_client.tests.test_imports_integrity import run_manual_tests


def main():
    """Exécute les tests d'intégrité et affiche un rapport complet."""
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 16 + "RAPPORT D'INTÉGRITÉ ERP_CLIENT" + " " * 22 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # Exécuter les tests
    success = run_manual_tests()
    
    if not success:
        print("\n" + "═" * 70)
        print("🔧 ACTIONS RECOMMANDÉES POUR CORRIGER LES PROBLÈMES")
        print("═" * 70)
        
        print("\n1. PROBLÈME PRINCIPAL: Module models.pricing manquant")
        print("   Les fichiers suivants tentent d'importer PrixClient et TypeTarif:")
        print("   - ui/commercial_dashboard.py (ligne 22)")
        print("   - ui/commercial_dashboard_v2.py (ligne 27)")
        
        print("\n2. SOLUTIONS POSSIBLES:")
        print("   Option A - Créer le module manquant:")
        print("   └── Créer: modules/erp_client/models/pricing.py")
        print("   └── Déplacer PrixClient depuis services/pricing_service.py")
        print("   └── Créer la classe TypeTarif")
        
        print("\n   Option B - Corriger les imports:")
        print("   └── Changer: from ..models.pricing import PrixClient")
        print("   └── Vers: from ..services.pricing_service import PrixClient")
        print("   └── Créer TypeTarif dans services/pricing_service.py")
        
        print("\n3. DÉPENDANCES MANQUANTES:")
        print("   ⚠️  streamlit - Requis pour l'interface utilisateur")
        print("   Solution: pip install streamlit")
        
        print("\n4. VÉRIFICATION POST-CORRECTION:")
        print("   Après correction, relancer ce script pour vérifier.")
        
        print("\n" + "═" * 70)
        return 1
    else:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS !")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)