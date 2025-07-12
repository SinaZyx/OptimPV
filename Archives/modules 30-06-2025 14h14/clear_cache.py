#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour nettoyer les caches et forcer le rechargement.
"""

import os
import shutil

def clear_streamlit_cache():
    """Nettoie le cache Streamlit."""
    print("=== NETTOYAGE DU CACHE ===")
    
    # Dossiers de cache potentiels
    cache_dirs = [
        '.streamlit',
        '__pycache__',
        'modules/__pycache__',
        'modules/prospect_mapping/__pycache__',
        'cache'
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                if os.path.isdir(cache_dir):
                    shutil.rmtree(cache_dir)
                    print(f"Supprime: {cache_dir}/")
                else:
                    os.remove(cache_dir)
                    print(f"Supprime: {cache_dir}")
            except Exception as e:
                print(f"Erreur suppression {cache_dir}: {e}")
        else:
            print(f"N'existe pas: {cache_dir}")
    
    print("\nCache nettoye - Redemarrez l'application pour voir les changements")

def main():
    """Fonction principale."""
    print("NETTOYAGE CACHE OPTIMPV")
    print("=" * 30)
    
    clear_streamlit_cache()
    
    print("\n" + "=" * 30)
    print("REDEMARRAGE REQUIS:")
    print("1. Fermez l'application OptimPV")
    print("2. Relancez: streamlit run app.py")
    print("3. Allez dans 'Carte de Prospection'")
    print("4. Testez avec les nouvelles communes")

if __name__ == "__main__":
    main()