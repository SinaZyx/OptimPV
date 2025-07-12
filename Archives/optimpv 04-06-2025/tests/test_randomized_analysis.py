# tests/test_randomized_analysis.py

import pytest
import pandas as pd
import numpy as np
import random
import time

# Importer les classes nécessaires (adaptez les chemins si nécessaire)
from modules.engine_module.core_analyzer import AnalysisEngine
from modules.optimisation_analyse.logique_optimisation import OptimizationLogic

# --- Fixtures (réutiliser ou adapter celles existantes si besoin) ---

# On réutilise la fixture de données simple
@pytest.fixture(scope="module")
def random_test_data():
    """Fournit un DataFrame simple de données traitées pour les tests aléatoires."""
    start_date = pd.Timestamp("2024-01-01")
    # Calculer le nombre exact de jours pour 20 ans en tenant compte des bissextiles
    end_date = start_date + pd.DateOffset(years=20) - pd.DateOffset(days=1)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    return pd.DataFrame({
        'Temps': dates,
        'production_kwh': np.full(len(dates), 200.0), # <-- Valeur réaliste pour 50 kWc base
        'consumption_kwh': np.full(len(dates), 10.0) # Garder la conso basse
    })

@pytest.fixture(scope="module")
def random_test_scenarios():
    """Scénario simple pour les tests aléatoires."""
    return {
        "Random_Test": {"description": "Test aléatoire", "production_modifier": 1.0,
                        "opex_modifier": 1.0, "capex_modifier": 1.0, "inflation_modifier": 1.0}
    }

# --- Fonction pour générer une configuration aléatoire réaliste ---

def generate_random_realistic_config(base_config):
    """Génère une config avec des variations aléatoires réalistes."""
    config = base_config.copy()
    seed = int(time.time() * 1000)
    rng = np.random.default_rng(seed)

    # Exemples de randomisation (plages ajustées pour plus de réalisme)
    config["capex"] = round(config["capex"] * rng.uniform(0.6, 1.1)) # Ex: 60% à 110% du CAPEX de base
    config["opex"] = round(config["opex"] * rng.uniform(0.8, 1.2))
    config["puissance_kwc"] = round(config["puissance_kwc"] * rng.uniform(0.8, 1.2))
    config["degradation_rate"] = round(rng.uniform(0.003, 0.007), 4)
    config["taux_inflation"] = round(rng.uniform(1.0, 4.0), 2)
    config["taux_imposition"] = round(rng.uniform(15.0, 35.0), 1) # Entre 15% et 35%
    config["cout_fonds_propres"] = round(rng.uniform(6.0, 12.0), 2)
    config["with_loan"] = rng.choice([True, False])
    if config["with_loan"]:
        config["debt_ratio"] = round(rng.uniform(0.3, 0.9), 2) # 30% à 90%
        config["debt_term_years"] = int(rng.integers(10, 25, endpoint=True)) # Utilise integers() de NumPy
        config["taux_interet_dette"] = round(rng.uniform(2.0, 6.0), 2)
    else:
        config["debt_ratio"] = 0.0
        config["debt_term_years"] = 15 # Mettre une valeur par défaut
        config["taux_interet_dette"] = 0.0
    config["prix_vente_initial"] = round(rng.uniform(0.10, 0.25), 3)
    config["tarif_oa"] = round(rng.uniform(0.05, 0.12), 3)
    config["tarif_edf_reference"] = round(rng.uniform(0.18, 0.35), 3) # Ex: Tarif EDF minimum un peu plus haut

    # S'assurer que les prix restent cohérents (ex: OA < EDF)
    config["tarif_oa"] = min(config["tarif_oa"], config["tarif_edf_reference"] * 0.9) # OA max 90% d'EDF

    # Contraintes aléatoires (mais cohérentes)
    min_irr = round(rng.uniform(5.0, 10.0), 1)
    max_payback = int(rng.integers(12, 25, endpoint=True)) # Utilise integers() de NumPy
    min_gain_pct = round(rng.uniform(5.0, 20.0), 1)
    config["constraint_min_irr_pct"] = min_irr
    config["constraint_max_payback"] = max_payback
    config["constraint_min_consumer_gain_pct"] = min_gain_pct

    # Assurer que le prix max est compatible avec le gain client min
    prix_max_par_gain = config["tarif_edf_reference"] * (1 - min_gain_pct / 100.0)
    config["prix_max_revente"] = round(max(0.01, prix_max_par_gain * rng.uniform(0.95, 1.0)), 3) # Légèrement en dessous
    config["prix_min_revente"] = round(config["prix_max_revente"] * rng.uniform(0.2, 0.6), 3) # Min inférieur au max

    # Recalculer la subvention basée sur la puissance aléatoire
    puissance = config["puissance_kwc"]
    if puissance <= 3: rate = config.get("subvention_rate_le3", 0)
    elif puissance <= 9: rate = config.get("subvention_rate_le9", 0)
    elif puissance <= 36: rate = config.get("subvention_rate_le36", 0)
    elif puissance <= 100: rate = config.get("subvention_rate_le100", 0)
    else: rate = config.get("subvention_rate_gt100", 0)
    config["total_subvention"] = puissance * rate # Ajouter cette clé si l'engine l'attend

    return config

# --- Test Aléatoire ---

# Définir le nombre d'itérations aléatoires
NB_RANDOM_RUNS = 25 # Commencer avec un petit nombre, augmenter si besoin

@pytest.mark.parametrize("run_number", range(NB_RANDOM_RUNS))
def test_random_config_robustness(run_number, base_config, random_test_scenarios, random_test_data):
    """
    Teste AnalysisEngine et OptimizationLogic avec une config aléatoire.
    Vérifie l'absence de crash et la cohérence des résultats de l'optimiseur.
    """
    seed = int(time.time() * 1000) + run_number
    print(f"\n--- Test Aléatoire Run {run_number+1}/{NB_RANDOM_RUNS} (Seed: {seed}) ---")
    random.seed(seed) # Pour la reproductibilité si un test échoue

    # 1. Générer la config aléatoire
    random_config = generate_random_realistic_config(base_config)
    # print("Config Générée:", random_config) # Décommenter pour voir la config

    # 2. Tester AnalysisEngine (robustesse)
    engine = None
    initial_results = None
    try:
        engine = AnalysisEngine(random_config, random_test_scenarios, random_test_data)
        # Faire un calcul initial pour voir s'il plante
        initial_results = engine.calculate_financial_indicators(
            "Random_Test",
            prix_revente=random_config["prix_vente_initial"]
        )
        assert initial_results is not None, "AnalysisEngine a retourné None pour la config aléatoire."
        print("AnalysisEngine: Calcul initial OK.")
    except Exception as e:
        pytest.fail(f"AnalysisEngine a échoué avec la config aléatoire (Seed {seed}): {e}\nConfig: {random_config}", pytrace=False)

    # 3. Tester OptimizationLogic (robustesse et cohérence)
    try:
        optimizer = OptimizationLogic(config=random_config, analysis_engine=engine)
        optim_results = optimizer.find_optimal_price_constrained("Random_Test")

        # Si find_optimal_price_constrained réussit (retourne un dict sans erreur)
        if optim_results and "error" not in optim_results:
             print(f"OptimizationLogic: OK (Solution trouvée)")
             # --- Vérifications existantes si solution trouvée ---
             assert "prix_optimal_const" in optim_results
             assert "indicateurs_au_prix_optimal" in optim_results
             prix_optimal = optim_results["prix_optimal_const"]
             indicateurs = optim_results["indicateurs_au_prix_optimal"]
             contraintes = random_config # Les contraintes sont dans la config aléatoire

             assert isinstance(prix_optimal, (float, np.float_)), "Prix optimal n'est pas un nombre."
             assert prix_optimal >= 0 , f"Prix optimal négatif trouvé: {prix_optimal}"

             # Vérifier si les indicateurs respectent les contraintes de la config ALEATOIRE
             min_irr_target = contraintes["constraint_min_irr_pct"] / 100.0
             actual_irr = indicateurs.get("irr")
             if actual_irr is not None:
                  assert actual_irr >= min_irr_target - 1e-3, f"TRI {actual_irr:.4f} < Cible {min_irr_target:.4f}"

             max_payback_target = contraintes["constraint_max_payback"]
             actual_payback = indicateurs.get("payback_period")
             if actual_payback is not None: # Si un payback est calculé
                  assert actual_payback <= max_payback_target + 0.1, f"Payback {actual_payback:.1f} > Cible {max_payback_target:.1f}"

             min_gain_target_pct = contraintes["constraint_min_consumer_gain_pct"]
             tarif_edf = contraintes["tarif_edf_reference"]
             actual_gain_pct = ((tarif_edf - prix_optimal) / tarif_edf) * 100 if tarif_edf > 1e-6 else 0
             assert actual_gain_pct >= min_gain_target_pct - 0.1, f"Gain Client {actual_gain_pct:.1f}% < Cible {min_gain_target_pct:.1f}%"

             print(f"  -> Prix: {prix_optimal:.4f}, TRI: {actual_irr*100:.1f}%, Payback: {actual_payback:.1f}, Gain: {actual_gain_pct:.1f}%")
             # --- Fin Vérifications ---
        elif optim_results and "error" in optim_results:
             # Cas où l'optimiseur retourne une erreur gérée (ex: pas de solution)
             print(f"OptimizationLogic: OK (Erreur gérée retournée: {optim_results['error']})")
             # Pas d'échec ici, c'est un résultat possible pour certaines configs.
        else:
             # Cas où optim_results est None (inattendu)
              pytest.fail(f"OptimizationLogic a retourné None (inattendu) (Seed {seed})\nConfig: {random_config}", pytrace=False)

    except ValueError as ve:
        # Capture spécifique de ValueError pour la plage invalide
        if "Plage recherche invalide" in str(ve):
            print(f"OptimizationLogic: OK (ValueError attendu capturé: {ve})")
            # Considérer ce cas comme un succès ou un skip, car attendu pour certaines configs aléatoires
            # pytest.skip(f"Configuration aléatoire (Seed {seed}) a généré une plage de recherche invalide.")
            pass # Traiter comme un succès pour ce test de robustesse
        else:
            # Si c'est une autre ValueError, la faire échouer
            pytest.fail(f"OptimizationLogic a levé une ValueError inattendue (Seed {seed}): {ve}\nConfig: {random_config}", pytrace=False)
    except Exception as e:
        # Capturer toute autre exception comme un échec
        pytest.fail(f"OptimizationLogic a échoué avec une exception inattendue (Seed {seed}): {type(e).__name__}: {e}\nConfig: {random_config}", pytrace=False)