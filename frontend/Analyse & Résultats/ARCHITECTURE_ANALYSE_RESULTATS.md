# Architecture Réelle du Module "Analyse & Résultats" - OptimPV

## Vue d'ensemble

Le module "Analyse & Résultats" d'OptimPV est composé de plusieurs sous-modules qui travaillent ensemble pour fournir une analyse financière complète des projets photovoltaïques. Contrairement aux spécifications théoriques, voici la **réalité du code implémenté**.

## Structure des Fichiers

### 1. Interface Utilisateur Principal
**Fichier:** `/modules/optimisation_analyse/ui_page.py`
- **Fonction principale:** `display_analysis_optimisation_section(scenario_name)`
- **Responsabilité:** Interface Streamlit complète avec onglets
- **Onglets disponibles:**
 - **Analyse & Visualisation**: Calculs, optimisation, graphiques
 - **Rapports Financiers Détaillés**: Tableaux de synthèse financière

### 2. Moteur d'Optimisation
**Fichier:** `/modules/optimisation_analyse/logique_optimisation.py`
- **Classe principale:** `OptimizationLogic`
- **Méthodes clés:**
 - `find_optimal_price_constrained()`: Optimisation avec contraintes
 - `run_monte_carlo_simulation()`: Simulation de robustesse

### 3. Visualisations
**Fichier:** `/modules/optimisation_analyse/visualisation_prix.py`
- **Fonctions principales:**
 - `create_price_benefit_figure()`: Graphique Prix HT vs Bénéfice Client
 - `create_autoconsommation_surplus_pie_chart()`: Camembert énergétique

### 4. Moteur d'Analyse Financière
**Fichier:** `/modules/engine_module/core_analyzer.py`
- **Classe principale:** `AnalysisEngine`
- **Responsabilité:** Calculs financiers détaillés (NPV, IRR, LCOE, etc.)

## Fonctionnalités Réelles Implémentées

### 1. Configuration & Calcul des Seuils

#### Prix Plancher (VAN=0)
```python
# Calcul du prix de vente HT qui annule la VAN du projet
floor_res = analysis_engine.simulate_selling_price(
 scenario_name,
 target_npv=0,
 override_source_prix_autoconso="prix_initial"
)
```

#### LCOE (Levelized Cost of Energy)
- **Calcul:** Coût actualisé de l'énergie en €/kWh HT
- **Usage:** Borne inférieure pour l'optimisation
- **Affichage:** Métrique dans l'interface utilisateur

#### Tarif EDF de Référence
- **Source:** Configuration globale `tarif_edf_reference`
- **Format:** Prix TTC pour comparaison client final
- **Usage:** Calcul du gain client et contraintes

### 2. Optimisation Sous Contraintes

#### Algorithme d'Optimisation
- **Méthode:** SLSQP (Sequential Least Squares Programming)
- **Multi-start:** 3 points de départ par défaut
- **Objectif:** Maximiser NPV Equity (ou NPV Projet si financement 100% dette)

#### Contraintes Appliquées
1. **TRI Projet Minimum:** Défini par `constraint_min_irr_pct`
2. **Payback Equity Maximum:** Défini par `constraint_max_payback`
3. **Gain Client Minimum:** Défini par `constraint_min_consumer_gain_pct`

#### Gestion Financement 100% Dette
```python
debt_ratio = float(config.get('debt_ratio', 0.8))
is_full_debt_financing = debt_ratio >= 0.99

if is_full_debt_financing:
 # Optimiser NPV Projet au lieu de NPV Equity
 # Masquer les indicateurs fonds propres
```

### 3. Indicateurs Financiers Calculés

#### Indicateurs Fonds Propres
- **VAN Fonds Propres:** Flux de trésorerie actualisés pour les actionnaires
- **TRI Fonds Propres:** Avec gestion des cas atypiques (MIRR si nécessaire)
- **Payback Fonds Propres:** Durée de récupération de l'investissement

#### Indicateurs Projet Global
- **VAN Projet:** Valeur actualisée nette du projet complet
- **TRI Projet:** Taux de rentabilité interne sur l'investissement total
- **Payback Projet:** Récupération via flux opérationnels après IS

#### Métriques Opérationnelles
- **LCOE:** Coût actualisé de l'énergie
- **DSCR Moyen:** Debt Service Coverage Ratio
- **Taux d'autoconsommation:** % de production autoconsommée
- **Taux d'autoproduction:** % de consommation couverte par production

### 4. Simulation Monte Carlo

#### Paramètres de Simulation
- **Itérations:** 50 à 1000 (configurable par slider)
- **Variabilité Production:** ±10% (écart-type par défaut)
- **Variabilité Consommation:** ±5% (écart-type par défaut)

#### Critères de Succès
- **TRI Projet ≥ seuil défini**
- **Payback Equity ≤ seuil défini**
- **DSCR Moyen ≥ 1.2**

#### Résultats Fournis
- **Probabilités de succès:** Par critère et globale
- **Statistiques:** Moyennes, écarts-types, percentiles
- **Nombre d'itérations valides:** Pour le calcul des probabilités

### 5. Visualisations Interactives

#### Graphique Prix/Bénéfice
```python
def create_price_benefit_figure(df_data, cout_prod_ht, prix_edf_ref_ttc,
 selected_price_ht, optimal_price_ht, taux_tva)
```
- **Axe X:** Prix de vente HT (€/kWh)
- **Axe Y:** Bénéfice client annuel TTC (€)
- **Marqueurs:** Prix sélectionné (étoile rouge), Prix optimal (diamant vert)
- **Lignes de référence:** LCOE HT (tirets), Bénéfice=0 (pointillés)

#### Camembert Énergétique
```python
def create_autoconsommation_surplus_pie_chart(total_autoconsommation, total_surplus)
```
- **Segments:** Autoconsommation (or), Surplus (bleu)
- **Style:** Donut avec détachement du surplus
- **Données:** Quantités en kWh et pourcentages

### 6. Rapports Financiers Détaillés

#### Synthèse Projet
- **Module:** `table_finance.annual_summary_display`
- **Fonction:** `display_project_summary()`
- **Contenu:** Métriques clés du projet

#### Tableau Annuel Détaillé
- **Module:** `table_finance.annual_summary_display`
- **Fonction:** `display_annual_detailed_summary()`
- **Contenu:** Évolution année par année des indicateurs

#### Flux de Trésorerie Mensuels
- **Module:** `table_finance.monthly_cash_flow_display`
- **Fonction:** `display_cash_flow_statement_restructured()`
- **Contenu:** Détail mensuel par année sélectionnée

## Flux de Données

### 1. Initialisation
```python
analysis_engine = AnalysisEngine(
 config=st.session_state.config,
 scenarios=st.session_state.scenarios,
 sites_data=st.session_state.sites_data
)
```

### 2. Calcul des Seuils
```python
floor_res = analysis_engine.simulate_selling_price(scenario_name, target_npv=0)
# → prix_plancher_ht, lcoe_ht, edf_ref_ttc
```

### 3. Optimisation
```python
optimizer = OptimizationLogic(config, analysis_engine)
optim_res = optimizer.find_optimal_price_constrained(
 scenario_name, tri_projet_min_pct_constraint, sites_config
)
# → prix_optimal_ht, indicateurs_au_prix_optimal
```

### 4. Monte Carlo
```python
mc_res = optimizer.run_monte_carlo_simulation(
 scenario_name, prix_optimal_ht, sites_config
)
# → probabilités, statistiques, résultats_détaillés
```

### 5. Visualisations
```python
# Génération des données pour le graphique
prix_ht_range = np.linspace(prix_min, prix_max, 100)
data_curve = []
for prix_ht in prix_ht_range:
 benefice_client = autoconso_annuel * (prix_edf_ttc - prix_ht * (1 + tva))
 data_curve.append({'PrixVenteHT': prix_ht, 'BeneficeClient': benefice_client})
```

## Gestion des États de Session

### Variables Clés
- `floor_price_results[scenario_name]`: Résultats du prix plancher
- `constrained_optim_results[scenario_name]`: Résultats de l'optimisation
- `monte_carlo_results[scenario_name]`: Résultats Monte Carlo
- `thresholds_calculated[scenario_name]`: Statut des seuils calculés

### Persistance des Résultats
Les résultats sont stockés dans `st.session_state` et persistent tant que la session reste active.

## Gestion des Erreurs

### Validation des Données
- **Vérification:** Présence des données de sites
- **Validation:** Paramètres financiers critiques
- **Fallbacks:** Valeurs par défaut si paramètres manquants

### Erreurs d'Optimisation
- **Convergence:** Gestion des échecs SLSQP
- **Contraintes:** Vérification du respect des seuils
- **Messages:** Erreurs détaillées pour debugging

### Erreurs Monte Carlo
- **Données:** Validation des données de simulation
- **Calculs:** Gestion des échecs d'itération
- **Résultats:** Statistiques même avec échecs partiels

## Intégration avec le Reste d'OptimPV

### Navigation
- **Page:** "Analyse & Optimisation" dans l'application principale
- **Prérequis:** Données importées (`data_imported = True`)
- **Sélection:** Scénario via selectbox

### Modules Utilisés
- **Configuration:** `modules.config`
- **Moteur:** `modules.engine_module`
- **Visualisation:** `modules.visualization`
- **Reporting:** `modules.reporting`
- **Stockage:** `modules.storage`

## Limitations et Améliorations Possibles

### Limitations Actuelles
1. **Pas de cache persistant**: Recalcul à chaque session
2. **Optimisation séquentielle**: Pas de parallélisation
3. **Visualisations limitées**: Seulement 2 graphiques principaux

### Améliorations Suggérées
1. **Cache Redis**: Stockage persistant des résultats
2. **Optimisation parallèle**: Multi-threading pour Monte Carlo
3. **Visualisations avancées**: Graphiques 3D, heatmaps
4. **Export des résultats**: PDF, Excel
5. **Historique des optimisations**: Comparaison des runs

## Conclusion

Le module "Analyse & Résultats" d'OptimPV est un système robuste et complet qui fournit:
- **Calculs financiers précis** avec gestion des cas edge
- **Optimisation sous contraintes** avec algorithme SLSQP
- **Simulation Monte Carlo** pour évaluation de robustesse
- **Visualisations interactives** pour aide à la décision
- **Rapports détaillés** pour présentation client

L'architecture modulaire permet une maintenance facile et des extensions futures.