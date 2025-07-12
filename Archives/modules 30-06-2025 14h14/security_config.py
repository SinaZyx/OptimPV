"""
Module de configuration sécurisé pour OptimPV
Ce fichier sera protégé par PyArmor
"""

import hashlib

def get_default_password():
    """Retourne le mot de passe par défaut"""
    return "panel123"

def get_default_password_hash():
    """Retourne le hash du mot de passe par défaut"""
    password = get_default_password()
    return hashlib.sha256(password.encode()).hexdigest()

def get_security_config():
    """Retourne la configuration de sécurité"""
    return {
        "default_password": get_default_password(),
        "default_password_hash": get_default_password_hash(),
        "password_min_length": 6,
        "hash_algorithm": "sha256"
    }