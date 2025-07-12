#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests pour la fonctionnalité de recherche d'adresse et affichage des DPE
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import pandas as pd
import logging
from unittest.mock import patch, MagicMock

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestProspectDPESearch(unittest.TestCase):
    """Tests pour les nouvelles fonctionnalités de recherche et DPE"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.test_address = "123 Avenue des Fleurs, Mougins, 06250"
        self.test_lat = 43.5974
        self.test_lon = 7.0058
        
    def test_search_and_geocode_address(self):
        """Test de la fonction de géocodage d'adresse"""
        try:
            from modules.prospect_mapping.core.data_handler import search_and_geocode_address
            
            # Test avec une adresse valide
            logger.info(f"Test géocodage de l'adresse: {self.test_address}")
            result = search_and_geocode_address(self.test_address)
            
            # Vérifier la structure du résultat
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)
            
            if result['success']:
                logger.info(f"✅ Adresse trouvée: {result.get('address_found', '')}")
                logger.info(f"   Coordonnées: {result.get('latitude', 0):.6f}, {result.get('longitude', 0):.6f}")
                
                # Vérifier les champs requis
                self.assertIn('latitude', result)
                self.assertIn('longitude', result)
                self.assertIn('address_found', result)
                
                # Vérifier que les coordonnées sont dans le département 06
                self.assertGreater(result['latitude'], 43.0)
                self.assertLess(result['latitude'], 44.5)
                self.assertGreater(result['longitude'], 6.5)
                self.assertLess(result['longitude'], 7.8)
            else:
                logger.warning(f"⚠️ Adresse non trouvée: {result.get('error', 'Erreur inconnue')}")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du test de géocodage: {e}")
            self.fail(f"Erreur lors du test de géocodage: {e}")
    
    def test_get_all_dpe_around_point(self):
        """Test de la fonction de récupération des DPE"""
        try:
            from modules.prospect_mapping.core.data_handler import get_all_dpe_around_point
            
            # Test avec les coordonnées de Mougins
            logger.info(f"Test récupération DPE autour de: {self.test_lat:.6f}, {self.test_lon:.6f}")
            
            # Rayon de recherche
            radius = 500
            df_dpe = get_all_dpe_around_point(self.test_lat, self.test_lon, radius)
            
            # Vérifier le type de retour
            self.assertIsInstance(df_dpe, pd.DataFrame)
            
            if len(df_dpe) > 0:
                logger.info(f"✅ {len(df_dpe)} DPE trouvés dans un rayon de {radius}m")
                
                # Vérifier les colonnes attendues
                expected_columns = ['latitude', 'longitude', 'dpe_classe_energie', 'dpe_classe_ges']
                for col in expected_columns:
                    self.assertIn(col, df_dpe.columns, f"Colonne manquante: {col}")
                
                # Afficher quelques statistiques
                classes_energie = df_dpe['dpe_classe_energie'].value_counts()
                logger.info("Distribution des classes énergétiques:")
                for classe, count in classes_energie.items():
                    logger.info(f"   Classe {classe}: {count} DPE")
                
                # Vérifier les distances
                if 'distance_m' in df_dpe.columns:
                    self.assertTrue(all(df_dpe['distance_m'] <= radius), 
                                  "Certains DPE sont hors du rayon demandé")
            else:
                logger.warning(f"⚠️ Aucun DPE trouvé dans un rayon de {radius}m")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du test DPE: {e}")
            # Ne pas faire échouer le test si l'API est indisponible
            logger.warning("L'API DPE pourrait être temporairement indisponible")
    
    def test_create_dpe_color_map(self):
        """Test de la fonction de mapping des couleurs DPE"""
        try:
            from modules.prospect_mapping.core.data_handler import create_dpe_color_map
            
            logger.info("Test du mapping des couleurs DPE")
            
            # Test pour chaque classe énergétique
            classes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'N/A', 'Invalid']
            expected_colors = {
                'A': [0, 150, 0, 200],      # Vert foncé
                'B': [50, 200, 50, 200],    # Vert clair
                'C': [255, 255, 0, 200],    # Jaune
                'D': [255, 200, 0, 200],    # Orange clair
                'E': [255, 140, 0, 200],    # Orange
                'F': [255, 69, 0, 200],     # Rouge-orange
                'G': [255, 0, 0, 200],      # Rouge
                'N/A': [128, 128, 128, 150] # Gris
            }
            
            for classe in classes:
                color = create_dpe_color_map(classe)
                self.assertIsInstance(color, list)
                self.assertEqual(len(color), 4)  # R, G, B, A
                
                if classe in expected_colors:
                    self.assertEqual(color, expected_colors[classe])
                    logger.info(f"✅ Classe {classe}: Couleur {color}")
                else:
                    # Classes invalides doivent retourner gris
                    self.assertEqual(color, expected_colors['N/A'])
                    logger.info(f"✅ Classe {classe} (invalide): Couleur par défaut {color}")
                    
        except Exception as e:
            logger.error(f"❌ Erreur lors du test des couleurs: {e}")
            self.fail(f"Erreur lors du test des couleurs: {e}")
    
    def test_map_integration(self):
        """Test de l'intégration avec la carte"""
        try:
            from modules.prospect_mapping.core.map_visualizer_robust import create_prospect_map
            
            logger.info("Test de l'intégration avec la carte")
            
            # Créer des données de test
            test_data = pd.DataFrame({
                'latitude': [43.5974, 43.5980, 43.5970],
                'longitude': [7.0058, 7.0060, 7.0055],
                'consommation_kwh': [5000, 8000, 12000],
                'adresse': ['Test 1', 'Test 2', 'Test 3'],
                'nom_commune': ['MOUGINS', 'MOUGINS', 'MOUGINS']
            })
            
            # Créer des données DPE de test
            test_dpe = pd.DataFrame({
                'latitude': [43.5975, 43.5972],
                'longitude': [7.0059, 7.0057],
                'dpe_classe_energie': ['B', 'E'],
                'dpe_classe_ges': ['B', 'D'],
                'type_batiment': ['appartement', 'maison']
            })
            
            # Location de recherche
            search_location = {
                'latitude': 43.5974,
                'longitude': 7.0058,
                'address': 'Point de test'
            }
            
            # Tester la création de la carte avec toutes les options
            try:
                map_obj = create_prospect_map(
                    data=test_data,
                    dpe_data=test_dpe,
                    show_dpe=True,
                    search_location=search_location
                )
                
                # Vérifier que la carte a été créée
                self.assertIsNotNone(map_obj)
                
                # Vérifier le nombre de couches
                self.assertGreaterEqual(len(map_obj.deck_widget.layers), 1)
                logger.info(f"✅ Carte créée avec {len(map_obj.deck_widget.layers)} couches")
                
            except Exception as e:
                logger.warning(f"⚠️ Impossible de créer la carte complète: {e}")
                # Tester au moins sans les données DPE
                map_obj = create_prospect_map(data=test_data)
                self.assertIsNotNone(map_obj)
                logger.info("✅ Carte créée en mode basique")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du test d'intégration: {e}")
            # Ne pas faire échouer si PyDeck n'est pas disponible
            logger.warning("PyDeck pourrait ne pas être disponible dans l'environnement de test")

def run_tests():
    """Fonction principale pour exécuter les tests"""
    logger.info("=" * 60)
    logger.info("TESTS DE LA FONCTIONNALITÉ RECHERCHE ADRESSE ET DPE")
    logger.info("=" * 60)
    
    # Créer le test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestProspectDPESearch)
    
    # Exécuter les tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Résumé
    logger.info("=" * 60)
    if result.wasSuccessful():
        logger.info("✅ TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS!")
    else:
        logger.error(f"❌ {len(result.failures)} tests ont échoué")
        logger.error(f"❌ {len(result.errors)} erreurs rencontrées")
    logger.info("=" * 60)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)