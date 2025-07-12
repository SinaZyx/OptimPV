# config/__init__.py
"""
Configuration module for OptimPV Control Panel

This package contains configuration management:
- System constants and defaults
- Secure configuration storage and retrieval
- Configuration import/export functionality
"""

from .constants import (
    SYSTEM_VERSION,
    SYSTEM_NAME,
    BASE_DIR,
    CONFIG_DIR,
    SECURE_CONFIG_DIR,
    LOGS_DIR,
    DEFAULT_BIND_ADDRESS,
    DEFAULT_PORT,
    CONTROL_PANEL_PORT,
    DEFAULT_CONFIG
)

from .settings import config_manager

__all__ = [
    'SYSTEM_VERSION',
    'SYSTEM_NAME',
    'BASE_DIR',
    'CONFIG_DIR',
    'SECURE_CONFIG_DIR',
    'LOGS_DIR',
    'DEFAULT_BIND_ADDRESS',
    'DEFAULT_PORT',
    'CONTROL_PANEL_PORT',
    'DEFAULT_CONFIG',
    'config_manager'
] 