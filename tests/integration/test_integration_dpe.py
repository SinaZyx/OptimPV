#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test d'intégration de la recherche DPE
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Coordonnées de test
LAT = 43.631241005708134
LON = 6.9373580224334495

print("TEST D'INTÉGRATION RECHERCHE DPE")
print("=" * 60)
print(f"Coordonnées GPS: {LAT}, {LON}")
print()

try:
    from modules.prospect_mapping.core.data_handler import get_all_dpe_around_point
    
    # Test avec différents rayons
    for radius in [500, 1000, 2000]:
        print(f"\nRecherche DPE dans un rayon de {radius}m:")
        print("-" * 40)
        
        df_dpe = get_all_dpe_around_point(LAT, LON, radius)
        
        if len(df_dpe) > 0:
            print(f"✅ {len(df_dpe)} DPE trouvés!")
            
            # Afficher les colonnes disponibles
            print(f"\nColonnes disponibles: {', '.join(df_dpe.columns)}")
            
            # Afficher les premiers résultats
            print(f"\nPremiers DPE (triés par distance):")
            for idx, row in df_dpe.head(5).iterrows():
                adresse = row.get('adresse', 'Adresse non disponible')
                classe = row.get('dpe_classe_energie', 'N/A')
                distance = row.get('distance_m', 0)
                print(f"  - {adresse}")
                print(f"    Classe: {classe}, Distance: {distance:.0f}m")
            
            # Statistiques par classe énergétique
            print(f"\nRépartition par classe énergétique:")
            if 'dpe_classe_energie' in df_dpe.columns:
                stats = df_dpe['dpe_classe_energie'].value_counts()
                for classe, count in stats.items():
                    print(f"  Classe {classe}: {count} DPE")
        else:
            print("❌ Aucun DPE trouvé")
            
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("RÉSUMÉ")
print("=" * 60)
print("La fonction get_all_dpe_around_point:")
print("1. Fait un reverse geocoding pour obtenir le code postal")
print("2. Recherche les DPE avec ce code postal")
print("3. Convertit les coordonnées Lambert 93 en WGS84")
print("4. Filtre par distance et retourne les résultats triés")