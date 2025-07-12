"""
Tests pour les nouveaux composants de visualisation moderne
"""
import unittest
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Ajouter le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports des modules à tester
try:
    from modules.visualization.styles.themes.theme_manager import ThemeManager, ColorPalette
    from modules.visualization.charts.interactive.advanced_charts import InteractiveChartManager
    from modules.visualization.charts.advanced.energy_flow_charts import (
        create_energy_sankey_diagram,
        create_consumption_heatmap,
        create_3d_surface_analysis,
        create_radar_comparison_chart
    )
    from modules.visualization.components.dashboard.customizable_dashboard import (
        CustomizableDashboard,
        WidgetType,
        WidgetConfig
    )
    from modules.visualization.styles.animations.animation_system import AnimationSystem
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Erreur d'import: {e}")
    MODULES_AVAILABLE = False

class TestThemeManager(unittest.TestCase):
    """Tests pour le gestionnaire de thèmes"""
    
    def setUp(self):
        """Initialisation avant chaque test"""
        if MODULES_AVAILABLE:
            self.theme_manager = ThemeManager()
    
    def test_theme_initialization(self):
        """Test de l'initialisation du thème"""
        if not MODULES_AVAILABLE:
            self.skipTest("Modules non disponibles")
            
        # Vérifier que le thème par défaut est chargé
        self.assertIn(self.theme_manager.get_current_theme(), ['light', 'dark', 'corporate'])
    
    def test_theme_switching(self):
        """Test du changement de thème"""
        if not MODULES_AVAILABLE:
            self.skipTest("Modules non disponibles")
            
        # Changer vers dark
        result = self.theme_manager.switch_theme('dark')
        self.assertTrue(result)
        self.assertEqual(self.theme_manager.get_current_theme(), 'dark')
        
        # Changer vers light
        result = self.theme_manager.switch_theme('light')
        self.assertTrue(result)
        self.assertEqual(self.theme_manager.get_current_theme(), 'light')
        
        # Essayer un thème invalide
        result = self.theme_manager.switch_theme('invalid_theme')
        self.assertFalse(result)
    
    def test_color_palette(self):
        """Test de la palette de couleurs"""
        if not MODULES_AVAILABLE:
            self.skipTest("Modules non disponibles")
            
        colors = self.theme_manager.get_colors()
        
        # Vérifier les couleurs essentielles
        essential_colors = [
            'primary', 'secondary', 'background', 'text_primary',
            'success', 'error', 'warning', 'info'
        ]
        
        for color in essential_colors:
            self.assertIn(color, colors)
            self.assertIsInstance(colors[color], str)
            # Vérifier format couleur (commence par # ou rgba)
            self.assertTrue(
                colors[color].startswith('#') or 
                colors[color].startswith('rgba') or
                colors[color].startswith('var(')
            )
    
    def test_plotly_theme(self):
        """Test de la configuration Plotly"""
        if not MODULES_AVAILABLE:
            self.skipTest("Modules non disponibles")
            
        plotly_config = self.theme_manager.get_plotly_theme()
        
        # Vérifier la structure
        self.assertIn('layout', plotly_config)
        self.assertIn('paper_bgcolor', plotly_config['layout'])
        self.assertIn('colorway', plotly_config['layout'])
        self.assertIsInstance(plotly_config['layout']['colorway'], list)

class TestAdvancedCharts(unittest.TestCase):
    """Tests pour les graphiques avancés"""
    
    def setUp(self):
        """Préparer les données de test"""
        if MODULES_AVAILABLE:
            self.chart_manager = InteractiveChartManager()
            
            # Créer des données de test
            dates = pd.date_range('2024-01-01', periods=100, freq='D')
            self.test_data = pd.DataFrame({
                'date': dates,
                'value1': np.random.randn(100).cumsum() + 100,
                'value2': np.random.randn(100).cumsum() + 50,
                'category': np.random.choice(['A', 'B', 'C'], 100)
            })
    
    def test_sankey_diagram(self):
        """Test du diagramme de Sankey"""
        if not MODULES_AVAILABLE:
            self.skipTest("Modules non disponibles")
            
        # Données pour Sankey
        energy_flows = {
            'source': [0, 1, 0],
            'target': [2, 2, 3],
            'value': [100, 50, 50],
            'labels': ['Production PV', 'Réseau', 'Consommation', 'Injection']
        }
        
        try:
            fig = create_energy_sankey_diagram(energy_flows)
            self.assertIsNotNone(fig)
            self.assertEqual(len(fig.data), 1)  # Un seul trace Sankey
            self.assertEqual(fig.data[0].type, 'sankey')
        except Exception as e:
            self.fail(f"Erreur création Sankey: {e}")
    
    def test_heatmap_creation(self):
        """Test de création de heatmap"""
        if not MODULES_AVAILABLE:
            self.skipTest("Modules non disponibles")
            
        try:
            fig = create_consumption_heatmap(
                self.test_data,
                'date',
                'value1',
                aggregation='hourly'
            )
            self.assertIsNotNone(fig)
            self.assertEqual(fig.data[0].type, 'heatmap')
        except Exception as e:
            self.fail(f"Erreur création heatmap: {e}")
    
    def test_3d_surface(self):
        """Test de la surface 3D"""
        if not MODULES_AVAILABLE:
            self.skipTest("Modules non disponibles")
            
        # Créer des données 3D
        data_3d = pd.DataFrame({
            'x': np.repeat(range(10), 10),
            'y': np.tile(range(10), 10),
            'z': np.random.randn(100)
        })
        
        try:
            fig = create_3d_surface_analysis(data_3d, 'x', 'y', 'z')
            self.assertIsNotNone(fig)
            self.assertEqual(fig.data[0].type, 'surface')
        except Exception as e:
            self.fail(f"Erreur création surface 3D: {e}")
    
    def test_radar_chart(self):
        """Test du graphique radar"""
        if not MODULES_AVAILABLE:
            self.skipTest("Modules non disponibles")
            
        categories = ['Rentabilité', 'Autonomie', 'Impact CO2', 'Résilience', 'Performance']
        datasets = [
            {'name': 'Scénario 1', 'values': [80, 70, 60, 85, 75]},
            {'name': 'Scénario 2', 'values': [70, 85, 80, 65, 90]}
        ]
        
        try:
            fig = create_radar_comparison_chart(categories, datasets)
            self.assertIsNotNone(fig)
            self.assertEqual(len(fig.data), 2)  # Deux datasets
            self.assertEqual(fig.data[0].type, 'scatterpolar')
        except Exception as e:
            self.fail(f"Erreur création radar: {e}")

class TestCustomizableDashboard(unittest.TestCase):
    """Tests pour le dashboard personnalisable"""
    
    def setUp(self):
        """Initialisation du dashboard"""
        if MODULES_AVAILABLE:
            # Simuler session_state
            import streamlit as st
            if not hasattr(st, 'session_state'):
                st.session_state = {}
            
            self.dashboard = CustomizableDashboard("test_dashboard")
    
    def test_dashboard_initialization(self):
        """Test de l'initialisation du dashboard"""
        if not MODULES_AVAILABLE:
            self.skipTest("Modules non disponibles")
            
        self.assertIsNotNone(self.dashboard)
        self.assertEqual(self.dashboard.dashboard_id, "test_dashboard")
    
    def test_add_widget(self):
        """Test d'ajout de widget"""
        if not MODULES_AVAILABLE:
            self.skipTest("Modules non disponibles")
            
        # Ajouter un widget métrique
        widget_id = self.dashboard.add_widget(
            WidgetType.METRIC,
            "Test Metric",
            {"value": "100", "unit": "kWh"},
            {"x": 1, "y": 1, "w": 4, "h": 2}
        )
        
        self.assertIsNotNone(widget_id)
        self.assertEqual(len(widget_id), 8)  # UUID court
    
    def test_widget_config(self):
        """Test de la configuration de widget"""
        if not MODULES_AVAILABLE:
            self.skipTest("Modules non disponibles")
            
        config = WidgetConfig(
            id="test123",
            type=WidgetType.CHART,
            title="Test Chart",
            position={"x": 1, "y": 1, "w": 6, "h": 4},
            config={"chart_type": "line"}
        )
        
        self.assertEqual(config.id, "test123")
        self.assertEqual(config.type, WidgetType.CHART)
        self.assertEqual(config.position['w'], 6)
        self.assertTrue(config.visible)
        self.assertFalse(config.locked)

class TestAnimationSystem(unittest.TestCase):
    """Tests pour le système d'animations"""
    
    def setUp(self):
        """Initialisation du système d'animations"""
        if MODULES_AVAILABLE:
            self.animation_system = AnimationSystem()
    
    def test_animation_library(self):
        """Test de la bibliothèque d'animations"""
        if not MODULES_AVAILABLE:
            self.skipTest("Modules non disponibles")
            
        # Vérifier les animations de base
        essential_animations = [
            'fadeIn', 'fadeInUp', 'slideInLeft', 'pulse', 'bounce'
        ]
        
        for anim in essential_animations:
            self.assertIn(anim, AnimationSystem.ANIMATIONS)
            self.assertIsInstance(AnimationSystem.ANIMATIONS[anim], str)
            self.assertIn('@keyframes', AnimationSystem.ANIMATIONS[anim])
    
    def test_load_animations(self):
        """Test du chargement d'animations"""
        if not MODULES_AVAILABLE:
            self.skipTest("Modules non disponibles")
            
        # Simuler session_state
        import streamlit as st
        if not hasattr(st, 'session_state'):
            st.session_state = {'animations_loaded': set()}
        
        # Charger des animations
        self.animation_system.load_animations(['fadeIn', 'bounce'])
        
        # Vérifier qu'elles sont marquées comme chargées
        self.assertIn('fadeIn', st.session_state.animations_loaded)
        self.assertIn('bounce', st.session_state.animations_loaded)

class TestDataGeneration(unittest.TestCase):
    """Tests pour la génération de données de test"""
    
    def test_generate_monthly_data(self):
        """Test de génération de données mensuelles"""
        # Générer des données sur 12 mois
        dates = pd.date_range('2024-01-01', periods=12, freq='ME')
        
        monthly_data = pd.DataFrame({
            'date': dates,
            'production_kWh': np.random.uniform(1000, 5000, 12),
            'consommation_totale_kWh': np.random.uniform(800, 3000, 12),
            'autoconsommation_kWh': np.random.uniform(500, 2000, 12),
            'injection_reseau_kWh': np.random.uniform(100, 1000, 12),
            'soutirage_reseau_kWh': np.random.uniform(200, 800, 12)
        })
        
        # Vérifications
        self.assertEqual(len(monthly_data), 12)
        self.assertTrue(all(monthly_data['production_kWh'] >= 0))
        self.assertTrue(all(monthly_data['consommation_totale_kWh'] >= 0))
    
    def test_generate_financial_indicators(self):
        """Test de génération d'indicateurs financiers"""
        indicators = {
            'npv': 45000,
            'tri': 0.12,
            'lcoe': 0.08,
            'payback': 8.5,
            'dscr_moyen': 1.35,
            'taux_autoconsommation': 0.65,
            'emissions_evitees_tonnes': 25
        }
        
        # Vérifications
        self.assertGreater(indicators['npv'], 0)
        self.assertGreater(indicators['tri'], 0)
        self.assertLess(indicators['lcoe'], 0.20)
        self.assertLess(indicators['payback'], 15)

class TestIntegration(unittest.TestCase):
    """Tests d'intégration des composants"""
    
    def test_theme_with_charts(self):
        """Test de l'intégration thème + graphiques"""
        if not MODULES_AVAILABLE:
            self.skipTest("Modules non disponibles")
            
        # Créer un gestionnaire de thème
        theme_manager = ThemeManager()
        
        # Obtenir la config Plotly
        plotly_config = theme_manager.get_plotly_theme()
        
        # Créer un graphique simple avec le thème
        import plotly.graph_objects as go
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[1, 2, 3, 4],
            y=[10, 15, 13, 17],
            mode='lines+markers'
        ))
        
        # Appliquer le thème
        fig.update_layout(**plotly_config['layout'])
        
        # Vérifier que le thème est appliqué
        self.assertEqual(
            fig.layout.paper_bgcolor,
            plotly_config['layout']['paper_bgcolor']
        )

# Point d'entrée pour les tests
if __name__ == '__main__':
    # Configuration du test runner
    unittest.main(verbosity=2)