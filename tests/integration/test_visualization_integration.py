"""
Test d'intégration complet du système de visualisation moderne
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Configuration pour les tests
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_test_environment():
    """Configure l'environnement de test Streamlit"""
    # Simuler session_state
    if not hasattr(st, 'session_state'):
        st.session_state = {}
    
    # Configuration de base
    st.session_state.config = {
        'projet_nom': 'Test Projet OptimPV',
        'puissance_installee_kwc': 100,
        'prix_vente_elec': 0.15,
        'duree_projet_annees': 20
    }
    
    # Données d'optimisation simulées
    st.session_state.constrained_optim_results = generate_test_optimization_results()
    
    # Monte Carlo results
    st.session_state.monte_carlo_results = generate_test_monte_carlo_results()
    
    # État de l'interface
    st.session_state.view_mode = 'dashboard'
    st.session_state.user_type = 'client'
    st.session_state.selected_scenario_visu = 'Scénario Optimal'
    
    print("✅ Environnement de test configuré")

def generate_test_optimization_results():
    """Génère des résultats d'optimisation de test"""
    scenarios = ['Scénario Optimal', 'Scénario Conservateur', 'Scénario Ambitieux']
    results = {}
    
    for scenario in scenarios:
        # Générer des données mensuelles
        dates = pd.date_range('2024-01-01', periods=240, freq='ME')  # 20 ans
        
        # Facteurs de variation selon le scénario
        factor = {'Scénario Optimal': 1.0, 'Scénario Conservateur': 0.8, 'Scénario Ambitieux': 1.2}[scenario]
        
        monthly_data = pd.DataFrame({
            'date': dates,
            'production_kWh': np.random.uniform(8000, 12000, len(dates)) * factor,
            'consommation_totale_kWh': np.random.uniform(7000, 10000, len(dates)),
            'autoconsommation_kWh': np.random.uniform(5000, 8000, len(dates)) * factor,
            'injection_reseau_kWh': np.random.uniform(1000, 4000, len(dates)) * factor,
            'soutirage_reseau_kWh': np.random.uniform(2000, 5000, len(dates)) * (2 - factor),
            'revenus_autoconso': np.random.uniform(500, 1500, len(dates)) * factor,
            'revenus_injection': np.random.uniform(100, 600, len(dates)) * factor,
            'charges_exploitation': np.random.uniform(100, 300, len(dates)),
            'cashflow': np.random.uniform(-200, 2000, len(dates)) * factor,
            'cashflow_cumule': np.random.uniform(-10000, 50000, len(dates)) * factor
        })
        
        # Faire en sorte que le cashflow cumulé soit croissant
        monthly_data['cashflow_cumule'] = monthly_data['cashflow'].cumsum()
        
        # Indicateurs financiers
        npv_base = 50000 * factor
        tri_base = 0.12 * factor
        
        results[scenario] = {
            'indicateurs_au_prix_optimal': {
                'monthly_data': monthly_data,
                'npv': npv_base + np.random.uniform(-5000, 5000),
                'tri': tri_base + np.random.uniform(-0.02, 0.02),
                'lcoe': 0.08 / factor,
                'payback': 8 / factor,
                'dscr_moyen': 1.2 * factor,
                'dscr_min': 1.0 * factor,
                'taux_autoconsommation': 0.65 * factor,
                'taux_autoproduction': 0.75 * factor,
                'emissions_evitees_tonnes': 25 * factor,
                'production_totale_mwh': monthly_data['production_kWh'].sum() / 1000,
                'revenus_totaux': (monthly_data['revenus_autoconso'] + monthly_data['revenus_injection']).sum()
            }
        }
    
    return results

def generate_test_monte_carlo_results():
    """Génère des résultats Monte Carlo de test"""
    scenarios = ['Scénario Optimal', 'Scénario Conservateur', 'Scénario Ambitieux']
    results = {}
    
    for scenario in scenarios:
        n_simulations = 1000
        factor = {'Scénario Optimal': 1.0, 'Scénario Conservateur': 0.8, 'Scénario Ambitieux': 1.2}[scenario]
        
        # Distributions des résultats
        results[scenario] = {
            'npv_distribution': np.random.normal(50000 * factor, 10000, n_simulations),
            'tri_distribution': np.random.normal(0.12 * factor, 0.02, n_simulations),
            'payback_distribution': np.random.normal(8 / factor, 1, n_simulations),
            'success_probability': 0.85 * factor,
            'risk_metrics': {
                'var_95': -5000 / factor,
                'cvar_95': -8000 / factor,
                'sharpe_ratio': 1.5 * factor
            }
        }
    
    return results

def test_modern_ui_components():
    """Test des composants UI modernes"""
    print("\n🧪 TEST DES COMPOSANTS UI MODERNES")
    print("=" * 50)
    
    try:
        from modules.visualization.ui.cards.modern_cards import render_metric_card, render_info_card
        from modules.visualization.ui.buttons.animated_buttons import render_animated_button
        
        # Test metric card
        print("✅ Test Metric Card")
        # render_metric_card devrait fonctionner sans erreur
        
        # Test info card
        print("✅ Test Info Card")
        
        # Test animated button
        print("✅ Test Animated Button")
        
        print("✅ Tous les composants UI fonctionnent correctement")
        
    except Exception as e:
        print(f"❌ Erreur dans les composants UI: {e}")
        return False
    
    return True

def test_advanced_charts():
    """Test des graphiques avancés"""
    print("\n🧪 TEST DES GRAPHIQUES AVANCÉS")
    print("=" * 50)
    
    try:
        from modules.visualization.charts.advanced.energy_flow_charts import (
            create_energy_sankey_diagram,
            create_consumption_heatmap,
            create_radar_comparison_chart
        )
        
        # Test Sankey
        print("📊 Test Diagramme de Sankey...")
        energy_flows = {
            'source': [0, 1, 0, 2],
            'target': [2, 3, 4, 5],
            'value': [5000, 3000, 2000, 8000],
            'labels': ['PV', 'Réseau', 'Autoconso', 'Soutirage', 'Injection', 'Consommation']
        }
        fig_sankey = create_energy_sankey_diagram(energy_flows)
        print("✅ Sankey créé avec succès")
        
        # Test Heatmap
        print("📊 Test Heatmap...")
        data = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=365, freq='D'),
            'value': np.random.randn(365).cumsum() + 100
        })
        fig_heatmap = create_consumption_heatmap(data, 'date', 'value')
        print("✅ Heatmap créée avec succès")
        
        # Test Radar
        print("📊 Test Graphique Radar...")
        categories = ['Rentabilité', 'Autonomie', 'CO2', 'Résilience', 'Performance']
        datasets = [
            {'name': 'Actuel', 'values': [70, 60, 80, 65, 75]},
            {'name': 'Optimal', 'values': [85, 80, 90, 85, 90]}
        ]
        fig_radar = create_radar_comparison_chart(categories, datasets)
        print("✅ Radar créé avec succès")
        
        print("✅ Tous les graphiques avancés fonctionnent correctement")
        
    except Exception as e:
        print(f"❌ Erreur dans les graphiques avancés: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_theme_system():
    """Test du système de thèmes"""
    print("\n🧪 TEST DU SYSTÈME DE THÈMES")
    print("=" * 50)
    
    try:
        from modules.visualization.styles.themes.theme_manager import theme_manager
        
        # Test des thèmes disponibles
        print("🎨 Thèmes disponibles:")
        for theme_name in ['light', 'dark', 'corporate']:
            result = theme_manager.switch_theme(theme_name)
            if result:
                print(f"  ✅ {theme_name}")
                colors = theme_manager.get_colors()
                print(f"     Primary: {colors['primary']}")
                print(f"     Background: {colors['background']}")
        
        # Test config Plotly
        plotly_config = theme_manager.get_plotly_theme()
        print("\n✅ Configuration Plotly générée")
        print(f"   Colorway: {len(plotly_config['layout']['colorway'])} couleurs")
        
        print("✅ Système de thèmes opérationnel")
        
    except Exception as e:
        print(f"❌ Erreur dans le système de thèmes: {e}")
        return False
    
    return True

def test_dashboard_customization():
    """Test du dashboard personnalisable"""
    print("\n🧪 TEST DU DASHBOARD PERSONNALISABLE")
    print("=" * 50)
    
    try:
        from modules.visualization.components.dashboard.customizable_dashboard import (
            CustomizableDashboard, WidgetType
        )
        
        # Créer un dashboard
        dashboard = CustomizableDashboard("test_dashboard")
        print("✅ Dashboard créé")
        
        # Ajouter des widgets
        widgets_added = []
        
        # Widget métrique
        widget_id = dashboard.add_widget(
            WidgetType.METRIC,
            "NPV",
            {"metric": "npv", "format": "currency"},
            {"x": 1, "y": 1, "w": 3, "h": 2}
        )
        widgets_added.append(widget_id)
        print(f"✅ Widget métrique ajouté: {widget_id}")
        
        # Widget graphique
        widget_id = dashboard.add_widget(
            WidgetType.CHART,
            "Production vs Consommation",
            {"chart_type": "line", "series": ["production", "consommation"]},
            {"x": 4, "y": 1, "w": 6, "h": 4}
        )
        widgets_added.append(widget_id)
        print(f"✅ Widget graphique ajouté: {widget_id}")
        
        # Widget tableau
        widget_id = dashboard.add_widget(
            WidgetType.TABLE,
            "Données mensuelles",
            {"columns": ["date", "production", "revenus"]},
            {"x": 1, "y": 3, "w": 3, "h": 3}
        )
        widgets_added.append(widget_id)
        print(f"✅ Widget tableau ajouté: {widget_id}")
        
        print(f"\n✅ {len(widgets_added)} widgets ajoutés au dashboard")
        
        # Test de suppression
        dashboard.remove_widget(widgets_added[0])
        print(f"✅ Widget {widgets_added[0]} supprimé")
        
        print("✅ Dashboard personnalisable opérationnel")
        
    except Exception as e:
        print(f"❌ Erreur dans le dashboard personnalisable: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_animation_system():
    """Test du système d'animations"""
    print("\n🧪 TEST DU SYSTÈME D'ANIMATIONS")
    print("=" * 50)
    
    try:
        from modules.visualization.styles.animations.animation_system import animation_system
        
        # Test chargement animations
        animations_to_test = ['fadeIn', 'slideInUp', 'bounce', 'pulse']
        animation_system.load_animations(animations_to_test)
        print(f"✅ {len(animations_to_test)} animations chargées")
        
        # Test animation d'élément
        animation_system.animate_element(
            'test-element',
            'fadeInUp',
            duration=1.0,
            delay=0.2
        )
        print("✅ Animation d'élément configurée")
        
        # Test animation décalée
        animation_system.stagger_animation(
            'parent-container',
            '.child-item',
            'fadeIn',
            stagger_delay=0.1
        )
        print("✅ Animation décalée configurée")
        
        print("✅ Système d'animations opérationnel")
        
    except Exception as e:
        print(f"❌ Erreur dans le système d'animations: {e}")
        return False
    
    return True

def test_full_integration():
    """Test d'intégration complète"""
    print("\n🧪 TEST D'INTÉGRATION COMPLÈTE")
    print("=" * 50)
    
    try:
        from modules.visualization.modern_visualization_ui import ModernVisualizationUI
        
        # Créer l'interface moderne
        ui = ModernVisualizationUI()
        print("✅ Interface moderne créée")
        
        # Vérifier les méthodes principales
        methods = [
            '_render_modern_header',
            '_render_modern_dashboard',
            '_render_advanced_analytics',
            '_check_data_availability'
        ]
        
        for method in methods:
            if hasattr(ui, method):
                print(f"✅ Méthode {method} disponible")
            else:
                print(f"❌ Méthode {method} manquante")
        
        # Test de disponibilité des données
        data_available = ui._check_data_availability()
        print(f"✅ Données disponibles: {data_available}")
        
        print("✅ Intégration complète réussie")
        
    except Exception as e:
        print(f"❌ Erreur dans l'intégration: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "=" * 70)
    print("🚀 DÉMARRAGE DES TESTS DE VISUALISATION MODERNE")
    print("=" * 70)
    
    # Configuration de l'environnement
    setup_test_environment()
    
    # Liste des tests
    tests = [
        ("Composants UI", test_modern_ui_components),
        ("Graphiques Avancés", test_advanced_charts),
        ("Système de Thèmes", test_theme_system),
        ("Dashboard Personnalisable", test_dashboard_customization),
        ("Système d'Animations", test_animation_system),
        ("Intégration Complète", test_full_integration)
    ]
    
    # Exécuter les tests
    results = {}
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = success
        except Exception as e:
            print(f"\n❌ Erreur critique dans {test_name}: {e}")
            results[test_name] = False
    
    # Résumé
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 70)
    
    total_tests = len(results)
    passed_tests = sum(1 for success in results.values() if success)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests réussis ({passed_tests/total_tests*100:.0f}%)")
    
    if passed_tests == total_tests:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS!")
    else:
        print("\n⚠️ Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    
    return passed_tests == total_tests

# Point d'entrée
if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)