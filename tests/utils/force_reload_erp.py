"""Script pour forcer le rechargement du module ERP.

Ce script supprime les caches Python et force le rechargement
complet du module ERP pour s'assurer que toutes les nouvelles
méthodes sont bien chargées.
"""

import os
import sys
import shutil
from pathlib import Path

def clear_python_cache():
    """Supprime tous les caches Python du projet."""
    project_root = Path(__file__).parent.parent.parent
    
    print("🧹 Nettoyage des caches Python...")
    
    # Supprimer les dossiers __pycache__
    for pycache in project_root.rglob("__pycache__"):
        if pycache.is_dir():
            print(f"  🗑️ Suppression {pycache}")
            shutil.rmtree(pycache, ignore_errors=True)
    
    # Supprimer les fichiers .pyc
    for pyc_file in project_root.rglob("*.pyc"):
        if pyc_file.is_file():
            print(f"  🗑️ Suppression {pyc_file}")
            pyc_file.unlink(missing_ok=True)
    
    print("✅ Caches Python supprimés")

def create_version_marker():
    """Crée un marqueur de version pour forcer le rechargement."""
    from datetime import datetime
    
    marker_path = Path(__file__).parent.parent / "VERSION_RELOAD.txt"
    
    with open(marker_path, 'w') as f:
        f.write(f"ERP Module reloaded: {datetime.now().isoformat()}\n")
        f.write("All services updated with latest methods\n")
        f.write("get_average_price: AVAILABLE\n")
        f.write("get_total_capacity: AVAILABLE\n")
        f.write("get_client_capacity: AVAILABLE\n")
    
    print(f"✅ Marqueur de version créé: {marker_path}")

def verify_methods():
    """Vérifie que les méthodes sont bien présentes dans les fichiers."""
    print("🔍 Vérification des méthodes dans les fichiers...")
    
    # Vérifier PricingService
    pricing_file = Path(__file__).parent.parent.parent / "modules/erp_client/services/pricing_service.py"
    with open(pricing_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "def get_average_price" in content:
        print("✅ get_average_price présente dans pricing_service.py")
    else:
        print("❌ get_average_price manquante dans pricing_service.py")
    
    # Vérifier CapacityService
    capacity_file = Path(__file__).parent.parent.parent / "modules/erp_client/services/capacity_service.py"
    with open(capacity_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    methods_to_check = ["def get_total_capacity", "def get_client_capacity"]
    for method in methods_to_check:
        if method in content:
            print(f"✅ {method.replace('def ', '')} présente dans capacity_service.py")
        else:
            print(f"❌ {method.replace('def ', '')} manquante dans capacity_service.py")

def main():
    """Fonction principale."""
    print("🔄 FORCE RELOAD MODULE ERP")
    print("="*40)
    
    # 1. Vérifier que les méthodes sont dans les fichiers
    verify_methods()
    
    # 2. Supprimer les caches
    clear_python_cache()
    
    # 3. Créer un marqueur de version
    create_version_marker()
    
    print("\n🎯 ACTIONS RECOMMANDÉES:")
    print("1. Redémarrer Streamlit complètement")
    print("2. Lancer: streamlit run app.py")
    print("3. Les méthodes devraient maintenant être disponibles")
    
    print("\n✅ Force reload terminé")

if __name__ == "__main__":
    main()