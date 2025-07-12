# tests/optimisation_analyse/test_logique_optimisation.py

import pytest
import pandas as pd
import numpy as np

# Importer les classes nécessaires (adaptez les chemins si nécessaire)
from modules.engine_module.core_analyzer import AnalysisEngine
from modules.optimisation_analyse.logique_optimisation import OptimizationLogic

# --- Fixtures pour les tests de l'optimiseur ---

@pytest.fixture(scope="module") # Scope "module" pour ne créer ces données qu'une fois
def optimizer_test_config():
    """Configuration spécifique pour tester l'optimiseur."""
    # Config simple mais avec des contraintes définies
    return {
        # --- Paramètres utilisés par AnalysisEngine ---
        "duree_ppa": 240, "taux_inflation": 1.0, "taux_imposition": 25.0,
        "capex": 5000, # Réduction drastique pour ce test spécifique
        "opex": 1000, "degradation_rate": 0.005,
        "puissance_kwc": 30, "cout_fonds_propres": 9.0, "with_loan": True,
        "debt_ratio": 0.6, "debt_term_years": 15, "taux_interet_dette": 3.5,
        "target_dscr": 1.15, "date_debut_ppa": "2024-01-01", "amortissement_duree": 15,
        "valeur_residuelle_pct": 5.0, "cout_demantelement_pct": 2.0,
        "prix_vente_initial": 0.12, # Prix initial potentiellement non optimal
        "tarif_oa": 0.07, "tarif_edf_reference": 0.20,
        "tarif_oa_indexe_inflation": False, # OA non indexé pour simplifier
        "taux_inflation_tarif_oa": 0.0,
        "source_prix_autoconso": "prix_initial",
        "subvention_rate_le3": 0, "subvention_rate_le9": 0,
        "subvention_rate_le36": 190, "subvention_rate_le100": 100, # P=30 -> 190 €/kWc
        "subvention_rate_gt100": 0,
        # --- Contraintes spécifiques pour l'optimiseur ---
        "constraint_min_irr_pct": 7.0,      # Exiger au moins 7% de TRI Equity
        "constraint_max_payback": 18.0,     # Payback Equity max 18 ans
        "constraint_min_consumer_gain_pct": 1.0, # Client doit gagner au moins 1% vs EDF (contrainte assouplie pour test)
        # --- Bornes de recherche (doivent être réalistes) ---
        "prix_min_revente": 0.05, # Plancher technique/LCOE estimé
        "prix_max_revente": 0.19  # Plafond (inférieur à EDF ref à cause du gain client)
    }

@pytest.fixture(scope="module")
def optimizer_test_scenarios():
    """Scénario simple pour le test de l'optimiseur."""
    return {
        "Optim_Test": {"description": "Scénario test optimisation",
                       "production_modifier": 1.0, "opex_modifier": 1.0,
                       "capex_modifier": 1.0, "inflation_modifier": 1.0}
    }

@pytest.fixture(scope="module")
def optimizer_test_data():
    """Données énergétiques simples pour le test."""
    start_date = pd.Timestamp("2024-01-01")
    end_date = start_date + pd.DateOffset(years=20) - pd.DateOffset(days=1) # 20 ans
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    # Production et conso qui permettent une rentabilité variable selon le prix
    return pd.DataFrame({
        'Temps': dates,
        'production_kwh': np.full(len(dates), 90.0), # Augmentation significative
        'consumption_kwh': np.full(len(dates), 8.0) # Consommation peut rester faible
    })

@pytest.fixture(scope="module")
def ready_analysis_engine(optimizer_test_config, optimizer_test_scenarios, optimizer_test_data):
    """Crée une instance fonctionnelle de AnalysisEngine."""
    # Note: Ce test suppose que AnalysisEngine fonctionne correctement (testé ailleurs)
    try:
        engine = AnalysisEngine(optimizer_test_config, optimizer_test_scenarios, optimizer_test_data)
        # Faire un calcul rapide pour vérifier que l'engine ne lève pas d'erreur majeure
        _ = engine.calculate_financial_indicators("Optim_Test", prix_revente=optimizer_test_config["prix_vente_initial"])
        return engine
    except Exception as e:
        pytest.fail(f"Échec de l'initialisation de AnalysisEngine pour le test d'optimisation: {e}")


# --- Tests pour OptimizationLogic ---

def test_find_optimal_price_constrained_basic(ready_analysis_engine, optimizer_test_config):
    """
    Teste la fonction find_optimal_price_constrained :
    - Vérifie qu'elle retourne un résultat sans erreur.
    - Vérifie que le prix trouvé est dans les bornes attendues.
    - Vérifie que les indicateurs au prix optimal respectent les contraintes.
    """
    optimizer = OptimizationLogic(config=optimizer_test_config, analysis_engine=ready_analysis_engine)
    scenario_name = "Optim_Test" # Le nom du scénario défini dans la fixture

    # Exécuter l'optimisation
    optim_results = optimizer.find_optimal_price_constrained(scenario_name)

    # 1. Vérifier la structure du résultat
    assert optim_results is not None, "L'optimisation n'a retourné aucun résultat."
    assert isinstance(optim_results, dict), "Le résultat de l'optimisation n'est pas un dictionnaire."
    assert "error" not in optim_results, f"L'optimisation a retourné une erreur: {optim_results.get('error')}"
    assert "prix_optimal_const" in optim_results, "Le prix optimal n'est pas dans les résultats."
    assert "indicateurs_au_prix_optimal" in optim_results, "Les indicateurs au prix optimal manquent."
    assert "contraintes_appliquees" in optim_results, "Les contraintes appliquées manquent."

    # 2. Vérifier la plausibilité du prix optimal
    prix_optimal = optim_results["prix_optimal_const"]
    assert isinstance(prix_optimal, (float, np.float_)), "Le prix optimal n'est pas un nombre."
    # Le prix doit être supérieur ou égal au prix plancher implicite (LCOE env.) et inférieur au tarif EDF moins le gain client
    lcoe_estime = optim_results.get("lcoe_estime", 0.05) # Prendre une valeur basse si LCOE non retourné
    gain_client_pct = optimizer_test_config["constraint_min_consumer_gain_pct"] / 100.0
    tarif_edf = optimizer_test_config["tarif_edf_reference"]
    prix_max_attendu = tarif_edf * (1 - gain_client_pct)
    assert prix_optimal >= lcoe_estime - 0.01, f"Prix optimal {prix_optimal:.4f} semble trop bas (LCOE estimé ~{lcoe_estime:.4f})."
    assert prix_optimal <= prix_max_attendu + 0.001, f"Prix optimal {prix_optimal:.4f} semble trop haut (max attendu ~{prix_max_attendu:.4f})."

    # 3. Vérifier que les indicateurs au prix optimal respectent les contraintes
    indicateurs = optim_results["indicateurs_au_prix_optimal"]
    contraintes = optim_results["contraintes_appliquees"]

    # Contrainte TRI Equity
    min_irr_target = contraintes["min_irr_pct"] / 100.0
    actual_irr = indicateurs.get("irr") # 'irr' est renommé pour TRI Equity
    assert actual_irr is not None, "TRI Equity non trouvé dans les indicateurs optimaux."
    # Ajouter une tolérance pour la convergence de l'optimiseur
    assert actual_irr >= min_irr_target - 1e-4, f"TRI Equity {actual_irr:.4f} est inférieur à la cible {min_irr_target:.4f} (avec tolérance)."

    # Contrainte Payback Equity
    max_payback_target = contraintes["max_payback"]
    actual_payback = indicateurs.get("payback_period") # 'payback_period' est renommé pour Payback Equity
    # Gérer le cas où le payback n'est pas atteint (None)
    if actual_payback is not None:
         # Ajouter une tolérance
         assert actual_payback <= max_payback_target + 0.1, f"Payback Equity {actual_payback:.2f} ans est supérieur à la cible {max_payback_target:.1f} ans (avec tolérance)."
    else:
        # Si le payback n'est pas atteint (None), mais que la contrainte était < infini, c'est un échec
        # Sauf si la durée de simu est elle-même inférieure au payback max visé (cas peu probable)
        assert max_payback_target == float('inf'), "Le payback n'a pas été atteint mais une cible finie était définie."


    # Contrainte Gain Client
    min_gain_target_pct = contraintes["min_consumer_gain_pct"]
    actual_gain_pct = ((tarif_edf - prix_optimal) / tarif_edf) * 100 if tarif_edf > 1e-6 else 0
    # Ajouter une tolérance
    assert actual_gain_pct >= min_gain_target_pct - 0.1, f"Gain client {actual_gain_pct:.1f}% est inférieur à la cible {min_gain_target_pct:.1f}% (avec tolérance)."

    print(f"\nOptimisation réussie. Prix trouvé: {prix_optimal:.4f}")
    print(f"  TRI obtenu: {actual_irr*100:.2f}% (cible >= {min_irr_target*100:.1f}%)")
    print(f"  Payback obtenu: {actual_payback:.2f} ans (cible <= {max_payback_target:.1f} ans)")
    print(f"  Gain client obtenu: {actual_gain_pct:.1f}% (cible >= {min_gain_target_pct:.1f}%)")

# --- Vous pouvez ajouter d'autres tests ici ---
# Par exemple:
# - tester avec des contraintes très strictes qui rendent l'optimisation impossible (vérifier qu'une erreur est gérée)
# - tester le cas où aucune contrainte n'est active (le prix optimal devrait maximiser la NPV)
# - tester la fonction run_monte_carlo_simulation (plus complexe)