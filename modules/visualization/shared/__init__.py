"""
Module shared pour les utilitaires communs de visualisation
"""
from .chart_utilities import *
from .breakeven_analysis import create_breakeven_interactive_chart, display_breakeven_analysis_ui
from .export_utilities import (
    export_chart_to_png,
    export_chart_to_svg,
    export_data_to_excel,
    create_pdf_report,
    create_download_button,
    display_export_interface,
    cached_chart_generation,
    optimize_dataframe_display
)

__all__ = [
    # chart_utilities exports
    'PLOTLY_THEME',
    'COLORS',
    'format_number',
    'format_currency',
    'format_percentage',
    'validate_chart_data',
    'apply_theme',
    'add_value_annotations',
    'create_metric_card',
    'handle_chart_error',
    'prepare_chart_for_export',
    'compute_heavy_calculation',
    'create_grid_layout',
    'sync_y_axes',
    'get_user_friendly_message',
    'generate_test_data',
    # breakeven_analysis exports
    'create_breakeven_interactive_chart',
    'display_breakeven_analysis_ui',
    # export_utilities exports
    'export_chart_to_png',
    'export_chart_to_svg',
    'export_data_to_excel',
    'create_pdf_report',
    'create_download_button',
    'display_export_interface',
    'cached_chart_generation',
    'optimize_dataframe_display'
]