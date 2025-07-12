# tests/conftest.py
import pytest
import pandas as pd

@pytest.fixture(scope="session") # Scope "session" peut être plus efficace
def base_config():
    """Fournit une configuration minimale valide partagée pour les tests."""
    return {
        "duree_ppa": 240, "taux_inflation": 2.0, "taux_imposition": 25.0,
        "capex": 100000, "opex": 5000, "degradation_rate": 0.005,
        "puissance_kwc": 50, "cout_fonds_propres": 8.0, "with_loan": True,
        "debt_ratio": 0.7, "debt_term_years": 15, "taux_interet_dette": 4.0,
        "target_dscr": 1.2, "date_debut_ppa": "2024-01-01", "amortissement_duree": 20,
        "valeur_residuelle_pct": 10.0, "cout_demantelement_pct": 5.0,
        "prix_vente_initial": 0.15, "tarif_oa": 0.08, "tarif_edf_reference": 0.22,
        "tarif_oa_indexe_inflation": True, "taux_inflation_tarif_oa": 1.5,
        "source_prix_autoconso": "prix_initial",
        "subvention_rate_le3": 0, "subvention_rate_le9": 0, "subvention_rate_le36": 190, # Exemple subvention  <-- VIRGULE AJOUTÉE
        "subvention_rate_le100": 100, "subvention_rate_gt100": 0, # <-- VIRGULE AJOUTÉE ICI AUSSI
        # --- MODIFICATION : Ajout de clés potentiellement utilisées par l'optimiseur/random ---
        "constraint_min_irr_pct": 8.0,
        "constraint_max_payback": 20.0,
        "constraint_min_consumer_gain_pct": 5.0,
        "prix_min_revente": 0.05,
        "prix_max_revente": 0.21
        # --- FIN MODIFICATION ---
    }

# Vous pouvez ajouter d'autres fixtures partagées ici si nécessaire