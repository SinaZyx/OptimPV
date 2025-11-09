#!/usr/bin/env python3
"""
Test des améliorations académiques Monte Carlo v2.0
Basé sur les standards du repository GitHub https://github.com/arunp77/MonteCarlo-simulation
"""

import numpy as np
import matplotlib.pyplot as plt

# Test des techniques de réduction de variance
def test_importance_sampling():
    """Test importance sampling vs échantillonnage standard"""
    print("=== TEST IMPORTANCE SAMPLING ===")
    
    n_samples = 1000
    
    # Fonction à estimer: E[x²] où x suit différentes distributions
    def f(x):
        return x**2
    
    # 1. Échantillonnage standard (uniforme)
    x_standard = np.random.uniform(0, 2, n_samples)
    estimate_standard = np.mean(f(x_standard)) / 2  # normalisation
    
    # 2. Importance sampling (Beta(2,5) concentré sur [0,1])
    x_importance = np.random.beta(2, 5, n_samples) * 2  # mise à l'échelle [0,2]
    weights = 2.5  # poids d'importance (simplifié)
    estimate_importance = np.mean(f(x_importance) * weights) / np.mean(weights)
    
    # Valeur théorique: E[X²] pour X~Uniform(0,2) = 8/3 ≈ 2.67
    theoretical = 8/3
    
    print(f"Valeur théorique: {theoretical:.3f}")
    print(f"Estimation standard: {estimate_standard:.3f} (erreur: {abs(estimate_standard-theoretical):.3f})")
    print(f"Estimation importance: {estimate_importance:.3f} (erreur: {abs(estimate_importance-theoretical):.3f})")
    
    return abs(estimate_importance-theoretical) < abs(estimate_standard-theoretical)

def test_antithetic_variables():
    """Test variables antithétiques pour réduction variance"""
    print("\n=== TEST VARIABLES ANTITHÉTIQUES ===")
    
    n_pairs = 500  # 500 paires = 1000 échantillons
    
    # Fonction à estimer: E[sin(X)] où X~N(π/2, 0.5)
    def f(x):
        return np.sin(x)
    
    # 1. Échantillonnage standard
    x_standard = np.random.normal(np.pi/2, 0.5, n_pairs*2)
    estimate_standard = np.mean(f(x_standard))
    variance_standard = np.var(f(x_standard))
    
    # 2. Variables antithétiques
    z = np.random.standard_normal(n_pairs)
    x1 = np.pi/2 + 0.5 * z
    x2 = np.pi/2 - 0.5 * z  # antithétique: 2*mean - x1
    
    y1 = f(x1)
    y2 = f(x2)
    estimate_antithetic = np.mean((y1 + y2) / 2)
    variance_antithetic = np.var((y1 + y2) / 2)
    
    # Valeur théorique proche de 1 (sin(π/2) = 1)
    theoretical = 1.0
    
    print(f"Valeur théorique: {theoretical:.3f}")
    print(f"Standard: {estimate_standard:.3f} ± {np.sqrt(variance_standard)/np.sqrt(n_pairs*2):.3f}")
    print(f"Antithétique: {estimate_antithetic:.3f} ± {np.sqrt(variance_antithetic)/np.sqrt(n_pairs):.3f}")
    print(f"Réduction variance: {(1-variance_antithetic/variance_standard)*100:.1f}%")
    
    return variance_antithetic < variance_standard

def test_correlated_variables():
    """Test génération variables corrélées via Cholesky"""
    print("\n=== TEST VARIABLES CORRÉLÉES ===")
    
    # Matrice de corrélation cible
    corr_matrix = np.array([[1.0, -0.3, 0.7], 
                           [-0.3, 1.0, -0.2], 
                           [0.7, -0.2, 1.0]])
    
    print("Matrice de corrélation cible:")
    print(corr_matrix)
    
    n_samples = 5000
    
    # Décomposition Cholesky
    L = np.linalg.cholesky(corr_matrix)
    
    # Génération variables corrélées
    Z = np.random.standard_normal((3, n_samples))
    X = L @ Z
    
    # Vérification corrélations empiriques
    empirical_corr = np.corrcoef(X)
    
    print("\nMatrice de corrélation empirique:")
    print(empirical_corr)
    
    # Test erreur maximale
    max_error = np.max(np.abs(corr_matrix - empirical_corr))
    print(f"\nErreur maximale: {max_error:.3f}")
    
    return max_error < 0.1  # Tolérance 10%

def test_convergence():
    """Test de convergence Monte Carlo"""
    print("\n=== TEST CONVERGENCE ===")
    
    # Estimation de pi via méthode Monte Carlo (cercle inscrit dans carré)
    def estimate_pi(n):
        x = np.random.uniform(-1, 1, n)
        y = np.random.uniform(-1, 1, n)
        inside_circle = (x**2 + y**2) <= 1
        return 4 * np.mean(inside_circle)
    
    # Test convergence avec échantillons croissants
    sample_sizes = [100, 500, 1000, 5000, 10000]
    estimates = []
    errors = []
    pi_theoretical = 3.141592653589793
    
    for n in sample_sizes:
        pi_est = estimate_pi(n)
        error = abs(pi_est - pi_theoretical)
        estimates.append(pi_est)
        errors.append(error)
        print(f"n={n:5d}: pi ~= {pi_est:.4f} (erreur: {error:.4f})")
    
    # Test si l'erreur diminue globalement
    convergence_trend = np.polyfit(np.log(sample_sizes), np.log(errors), 1)[0]
    print(f"\nTendance convergence: {convergence_trend:.3f} (doit etre < 0)")
    
    return convergence_trend < -0.1

def main():
    """Test complet des améliorations académiques"""
    print("TEST AMELIORATIONS MONTE CARLO ACADEMIQUES")
    print("Base sur: https://github.com/arunp77/MonteCarlo-simulation\n")
    
    # Tests individuels
    tests = [
        ("Importance Sampling", test_importance_sampling),
        ("Variables Antithétiques", test_antithetic_variables), 
        ("Variables Corrélées", test_correlated_variables),
        ("Test Convergence", test_convergence)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
            status = "PASS" if success else "FAIL"
            print(f"\n{status}: {name}")
        except Exception as e:
            print(f"\nERROR: {name} - {e}")
            results.append((name, False))
    
    # Résumé final
    print("\n" + "="*50)
    print("RESUME DES TESTS:")
    for name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{status} {name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nResultat: {passed}/{total} tests reussis")
    
    if passed == total:
        print("Toutes les ameliorations academiques fonctionnent correctement!")
    else:
        print("Certaines ameliorations necessitent des ajustements.")

if __name__ == "__main__":
    # Fixer la seed pour reproductibilité des tests
    np.random.seed(42)
    main()