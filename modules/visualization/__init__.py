"""
Module de visualisation moderne pour OptimPV
"""

# Import des composants principaux
try:
    # Interface principale moderne
    from .modern_visualization_ui import ModernVisualizationUI
    
    # Système de thèmes
    from .styles.themes.theme_manager import theme_manager, ThemeManager
    
    # Composants UI
    from .ui.cards.modern_cards import (
        render_metric_card,
        render_info_card,
        render_stat_cards_row,
        render_chart_card
    )
    
    from .ui.buttons.animated_buttons import (
        render_animated_button,
        render_button_group,
        render_floating_action_button
    )
    
    from .ui.theme_selector import (
        render_theme_selector,
        render_theme_toggle_mini
    )
    
    # Graphiques avancés
    from .charts.interactive.advanced_charts import (
        InteractiveChartManager,
        create_animated_time_series,
        create_realtime_chart_placeholder
    )
    
    from .charts.advanced.energy_flow_charts import (
        create_energy_sankey_diagram,
        create_consumption_heatmap,
        create_3d_surface_analysis,
        create_radar_comparison_chart,
        create_gantt_installation_chart,
        create_network_energy_flow
    )
    
    # Dashboard personnalisable
    from .components.dashboard.customizable_dashboard import (
        CustomizableDashboard,
        WidgetType,
        WidgetConfig
    )
    
    # Système d'animations
    from .styles.animations.animation_system import animation_system
    
    # Compatibilité avec l'ancienne interface
    from .main_visualization_ui import VisualizationModule
    
    # Flag pour indiquer que les imports modernes sont disponibles
    MODERN_UI_AVAILABLE = True
    
except ImportError as e:
    print(f"Avertissement: Certains composants de visualisation moderne ne sont pas disponibles: {e}")
    MODERN_UI_AVAILABLE = False
    
    # Fallback vers l'interface classique
    try:
        from .main_visualization_ui import VisualizationModule
    except ImportError:
        VisualizationModule = None

# Fonction helper pour créer l'interface appropriée
def create_visualization_interface(use_modern=True):
    """
    Crée l'interface de visualisation appropriée
    
    Args:
        use_modern: Si True, utilise l'interface moderne, sinon l'interface classique
        
    Returns:
        Instance de l'interface de visualisation
    """
    if use_modern and MODERN_UI_AVAILABLE:
        return ModernVisualizationUI()
    elif VisualizationModule:
        return VisualizationModule()
    else:
        raise ImportError("Aucune interface de visualisation disponible")

# Version du module
__version__ = "2.0.0"

# Exports publics
__all__ = [
    # Interfaces principales
    'ModernVisualizationUI',
    'VisualizationModule',
    'create_visualization_interface',
    
    # Thèmes
    'theme_manager',
    'ThemeManager',
    
    # Composants UI
    'render_metric_card',
    'render_info_card',
    'render_stat_cards_row',
    'render_chart_card',
    'render_animated_button',
    'render_button_group',
    'render_floating_action_button',
    'render_theme_selector',
    'render_theme_toggle_mini',
    
    # Graphiques
    'InteractiveChartManager',
    'create_animated_time_series',
    'create_realtime_chart_placeholder',
    'create_energy_sankey_diagram',
    'create_consumption_heatmap',
    'create_3d_surface_analysis',
    'create_radar_comparison_chart',
    'create_gantt_installation_chart',
    'create_network_energy_flow',
    
    # Dashboard
    'CustomizableDashboard',
    'WidgetType',
    'WidgetConfig',
    
    # Animations
    'animation_system',
    
    # Flags et version
    'MODERN_UI_AVAILABLE',
    '__version__'
]