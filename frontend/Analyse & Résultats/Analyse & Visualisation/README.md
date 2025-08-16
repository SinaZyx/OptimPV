# Analyse & Visualisation - OptimPV

## Vue d'ensemble

Ce module implémente les fonctionnalités d'analyse et de visualisation actuellement disponibles dans OptimPV, centrées sur l'optimisation de prix et la visualisation des résultats financiers.

## Fonctionnalités actuelles

### 1. Configuration & Calcul des Seuils
- **Prix plancher**: Calcul du prix minimum (VAN=0) via simulation
- **LCOE**: Coût de l'énergie produite (Levelized Cost of Energy)
- **Tarif de référence EDF**: Comparaison avec le tarif réglementé TTC

### 2. Optimisation sous Contraintes
- **Algorithme SLSQP** avec multi-start (3 points de départ)
- **Contraintes configurables**:
 - TRI Projet Minimum (%)
 - Payback Maximum (années)
 - Gain Client Minimum (%)

### 3. Visualisations Interactives
- **Courbe Prix/Bénéfice**: Prix de vente HT vs Bénéfice client annuel
- **Répartition énergétique**: Camembert autoconsommation/surplus
- **Contrôles interactifs**: Sliders pour ajustement prix en temps réel

## Structure des fichiers

```
Analyse & Visualisation/
 README.md # Ce fichier
 optimisation_prix.md # Algorithme d'optimisation SLSQP
 calculs_seuils.md # Prix plancher, LCOE et références
 visualisations_interactives.md # Graphiques Plotly existants
 simulation_monte_carlo.md # Analyse de risque par simulation
```

## Workflow actuel

1. **Calcul des seuils** → Prix plancher et LCOE
2. **Configuration contraintes** → TRI, Payback, Gain client
3. **Optimisation** → Recherche du prix optimal
4. **Visualisation** → Courbes et graphiques interactifs
5. **Simulation** → Monte Carlo pour analyse de risque

## Architecture technique

- **Interface**: `ui_page.py` avec onglets Streamlit
- **Optimisation**: `logique_optimisation.py` classe `OptimizationLogic`
- **Visualisation**: `visualisation_prix.py` fonctions Plotly
- **Calculs**: `core_analyzer.py` classe `AnalysisEngine`

## Cas d'usage typiques

1. **Définir le prix de vente optimal** selon contraintes financières
2. **Analyser l'impact prix** sur la rentabilité client/installateur
3. **Visualiser les équilibres** entre profitabilité et attractivité
4. **Évaluer les risques** via simulation Monte Carlo