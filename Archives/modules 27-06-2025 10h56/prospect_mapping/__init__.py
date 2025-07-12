# Module de cartographie de prospection OptimPV - VERSION FINALE

# Import conditionnel robuste
try:
    from .ui import show_prospect_map_ui as render_ui
    UI_AVAILABLE = True
except ImportError as e:
    print(f"Erreur import UI prospect_mapping: {e}")
    UI_AVAILABLE = False
    render_ui = None

def get_module_info():
    """Retourne les informations du module"""
    return {
        'version': '2.1',
        'enhanced': True,
        'features': ['proximite_mougins', 'enrichissement_a_la_demande', 'performance_optimisee']
    }

__all__ = ['render_ui', 'get_module_info'] if UI_AVAILABLE else ['get_module_info']
