# Simulation Monte Carlo - Analyse de Risque

## Vue d'ensemble

La simulation Monte Carlo d'OptimPV évalue la robustesse des projets photovoltaïques en testant les performances financières sous différents scénarios de variabilité de production et de consommation.

## Principe de la Simulation

### Méthode Monte Carlo
```python
def run_monte_carlo_simulation(self, scenario_name, prix_vente_ht, sites_config):
 """
 Lance une simulation Monte Carlo pour évaluer la robustesse du projet

 Paramètres variables:
 - Production annuelle (±10% écart-type par défaut)
 - Consommation annuelle (±5% écart-type par défaut)
 """
 # Configuration de base
 num_iterations = sites_config.get('monte_carlo_iterations', 100)
 production_std = sites_config.get('production_variability_std', 0.10)
 consumption_std = sites_config.get('consumption_variability_std', 0.05)

 results = []
 valid_iterations = 0

 for i in range(num_iterations):
 try:
 # Génération des variations aléatoires
 production_factor = np.random.normal(1.0, production_std)
 consumption_factor = np.random.normal(1.0, consumption_std)

 # Application des variations
 varied_config = self._apply_variations(
 scenario_name,
 production_factor,
 consumption_factor
 )

 # Calcul des métriques avec données variées
 metrics = self.analysis_engine.calculate_all_metrics_with_config(
 varied_config,
 prix_vente_ht
 )

 results.append(metrics)
 valid_iterations += 1

 except Exception as e:
 # Gestion des itérations échouées
 continue

 return self._analyze_monte_carlo_results(results, valid_iterations)
```

### Application des Variations
```python
def _apply_variations(self, scenario_name, production_factor, consumption_factor):
 """
 Applique les facteurs de variation aux données du scénario
 """
 # Copie de la configuration de base
 varied_config = deepcopy(self.base_config)

 # Variation de la production
 for site_id, site_data in varied_config['sites'].items():
 original_production = site_data['production_annuelle_kwh']
 varied_production = original_production * production_factor

 # Contrainte physique: production ne peut pas être négative
 site_data['production_annuelle_kwh'] = max(0, varied_production)

 # Variation de la consommation
 scenario_data = varied_config['scenarios'][scenario_name]
 original_consumption = scenario_data['consommation_annuelle_kwh']
 varied_consumption = original_consumption * consumption_factor

 # Contrainte logique: consommation minimum
 scenario_data['consommation_annuelle_kwh'] = max(1000, varied_consumption)

 return varied_config
```

## Critères de Succès

### Définition des Seuils
```python
def _define_success_criteria(self, sites_config):
 """
 Définit les critères de succès pour la simulation
 """
 criteria = {
 'tri_projet_min': sites_config.get('constraint_min_irr_pct', 8.0) / 100,
 'payback_equity_max': sites_config.get('constraint_max_payback', 18.0),
 'dscr_moyen_min': sites_config.get('dscr_minimum', 1.2),
 'npv_positive': True # VAN positive requise
 }

 # Adaptation pour financement 100% dette
 debt_ratio = float(sites_config.get('debt_ratio', 0.8))
 if debt_ratio >= 0.99:
 # Utiliser TRI projet au lieu de critères equity
 criteria['use_project_metrics'] = True

 return criteria

def _evaluate_iteration_success(self, metrics, criteria):
 """
 Évalue si une itération respecte tous les critères
 """
 success_checks = {}

 # TRI Projet
 tri_projet = metrics.get('irr_projet', 0)
 success_checks['tri_ok'] = tri_projet >= criteria['tri_projet_min']

 # Payback (selon type de financement)
 if criteria.get('use_project_metrics', False):
 payback = metrics.get('payback_projet', float('inf'))
 else:
 payback = metrics.get('payback_equity', float('inf'))

 success_checks['payback_ok'] = payback <= criteria['payback_equity_max']

 # DSCR Moyen
 dscr_moyen = metrics.get('dscr_moyen', 0)
 success_checks['dscr_ok'] = dscr_moyen >= criteria['dscr_moyen_min']

 # VAN positive
 if criteria.get('use_project_metrics', False):
 npv = metrics.get('npv_projet', 0)
 else:
 npv = metrics.get('npv_equity', 0)

 success_checks['npv_ok'] = npv > 0

 # Succès global
 overall_success = all(success_checks.values())

 return overall_success, success_checks
```

## Analyse des Résultats

### Calcul des Statistiques
```python
def _analyze_monte_carlo_results(self, results, valid_iterations):
 """
 Analyse statistique des résultats de simulation
 """
 if not results:
 return {'error': 'Aucune itération valide'}

 # Extraction des métriques
 tri_values = [r.get('irr_projet', 0) * 100 for r in results]
 payback_values = [r.get('payback_equity', 0) for r in results if r.get('payback_equity', 0)!= float('inf')]
 npv_values = [r.get('npv_equity', 0) for r in results]
 dscr_values = [r.get('dscr_moyen', 0) for r in results]

 # Statistiques descriptives
 statistics = {
 'tri_projet': {
 'moyenne': np.mean(tri_values),
 'ecart_type': np.std(tri_values),
 'percentile_5': np.percentile(tri_values, 5),
 'percentile_95': np.percentile(tri_values, 95),
 'minimum': np.min(tri_values),
 'maximum': np.max(tri_values)
 },
 'payback_equity': {
 'moyenne': np.mean(payback_values) if payback_values else None,
 'ecart_type': np.std(payback_values) if payback_values else None,
 'percentile_5': np.percentile(payback_values, 5) if payback_values else None,
 'percentile_95': np.percentile(payback_values, 95) if payback_values else None
 },
 'npv_equity': {
 'moyenne': np.mean(npv_values),
 'ecart_type': np.std(npv_values),
 'percentile_5': np.percentile(npv_values, 5),
 'percentile_95': np.percentile(npv_values, 95)
 },
 'dscr_moyen': {
 'moyenne': np.mean(dscr_values),
 'ecart_type': np.std(dscr_values),
 'minimum': np.min(dscr_values)
 }
 }

 # Calcul des probabilités de succès
 success_probabilities = self._calculate_success_probabilities(results)

 return {
 'statistics': statistics,
 'probabilities': success_probabilities,
 'valid_iterations': valid_iterations,
 'total_iterations': len(results),
 'success_rate': success_probabilities.get('global_success', 0)
 }

def _calculate_success_probabilities(self, results):
 """
 Calcule les probabilités de succès par critère
 """
 criteria = self._define_success_criteria(self.sites_config)
 total_iterations = len(results)

 success_counts = {
 'tri_ok': 0,
 'payback_ok': 0,
 'dscr_ok': 0,
 'npv_ok': 0,
 'global_success': 0
 }

 for metrics in results:
 overall_success, checks = self._evaluate_iteration_success(metrics, criteria)

 # Comptage par critère
 for criterion, success in checks.items():
 if success:
 success_counts[criterion] += 1

 # Comptage succès global
 if overall_success:
 success_counts['global_success'] += 1

 # Conversion en probabilités (%)
 probabilities = {}
 for criterion, count in success_counts.items():
 probabilities[criterion] = (count / total_iterations) * 100

 return probabilities
```

## Interface Utilisateur

### Configuration de la Simulation
```python
def display_monte_carlo_configuration(self):
 """
 Interface de configuration pour la simulation Monte Carlo
 """
 st.subheader(" Configuration Simulation Monte Carlo")

 col1, col2, col3 = st.columns(3)

 with col1:
 num_iterations = st.slider(
 "Nombre d'itérations",
 min_value=50,
 max_value=1000,
 value=100,
 step=50,
 help="Plus d'itérations = résultats plus précis mais calcul plus long"
 )

 with col2:
 production_variability = st.slider(
 "Variabilité Production (%)",
 min_value=5,
 max_value=20,
 value=10,
 step=1,
 help="Écart-type de la variation de production (conditions météo)"
 )

 with col3:
 consumption_variability = st.slider(
 "Variabilité Consommation (%)",
 min_value=2,
 max_value=15,
 value=5,
 step=1,
 help="Écart-type de la variation de consommation (comportement)"
 )

 return {
 'monte_carlo_iterations': num_iterations,
 'production_variability_std': production_variability / 100,
 'consumption_variability_std': consumption_variability / 100
 }

def display_monte_carlo_launch(self, prix_optimal_ht, scenario_name):
 """
 Interface de lancement de la simulation
 """
 if st.button(" Lancer Simulation Monte Carlo", type="primary"):
 with st.spinner("Simulation en cours..."):
 # Configuration
 mc_config = self.display_monte_carlo_configuration()

 # Lancement
 results = self.optimizer.run_monte_carlo_simulation(
 scenario_name,
 prix_optimal_ht,
 mc_config
 )

 # Stockage des résultats
 st.session_state.monte_carlo_results[scenario_name] = results

 # Affichage immédiat
 self.display_monte_carlo_results(results)
```

### Affichage des Résultats
```python
def display_monte_carlo_results(self, results):
 """
 Affiche les résultats de la simulation Monte Carlo
 """
 if results.get('error'):
 st.error(f" Erreur simulation: {results['error']}")
 return

 # Métriques de synthèse
 st.subheader(" Résultats de Robustesse")

 col1, col2, col3, col4 = st.columns(4)

 with col1:
 success_rate = results['probabilities']['global_success']
 st.metric(
 "Taux de Succès Global",
 f"{success_rate:.1f}%",
 delta="Excellent" if success_rate >= 80 else "Attention" if success_rate >= 60 else "Risqué"
 )

 with col2:
 tri_prob = results['probabilities']['tri_ok']
 st.metric(
 "Prob. TRI Respecté",
 f"{tri_prob:.1f}%",
 delta=f"{tri_prob - 100:.1f}pp" if tri_prob < 100 else ""
 )

 with col3:
 payback_prob = results['probabilities']['payback_ok']
 st.metric(
 "Prob. Payback Respecté",
 f"{payback_prob:.1f}%",
 delta=f"{payback_prob - 100:.1f}pp" if payback_prob < 100 else ""
 )

 with col4:
 dscr_prob = results['probabilities']['dscr_ok']
 st.metric(
 "Prob. DSCR Respecté",
 f"{dscr_prob:.1f}%",
 delta=f"{dscr_prob - 100:.1f}pp" if dscr_prob < 100 else ""
 )

 # Statistiques détaillées
 self.display_monte_carlo_statistics(results['statistics'])

 # Recommandations
 self.display_monte_carlo_recommendations(results['probabilities'])

def display_monte_carlo_statistics(self, statistics):
 """
 Affiche les statistiques détaillées
 """
 st.subheader(" Statistiques Détaillées")

 # TRI Projet
 tri_stats = statistics['tri_projet']
 st.write("**TRI Projet:**")
 col1, col2, col3 = st.columns(3)

 with col1:
 st.metric("Moyenne", f"{tri_stats['moyenne']:.1f}%")
 st.metric("Écart-type", f"{tri_stats['ecart_type']:.1f}%")

 with col2:
 st.metric("Minimum", f"{tri_stats['minimum']:.1f}%")
 st.metric("Maximum", f"{tri_stats['maximum']:.1f}%")

 with col3:
 st.metric("P5", f"{tri_stats['percentile_5']:.1f}%")
 st.metric("P95", f"{tri_stats['percentile_95']:.1f}%")

 # VAN Equity
 npv_stats = statistics['npv_equity']
 st.write("**VAN Fonds Propres:**")
 col1, col2 = st.columns(2)

 with col1:
 st.metric("Moyenne", f"{npv_stats['moyenne']:.0f} €")
 st.metric("P5", f"{npv_stats['percentile_5']:.0f} €")

 with col2:
 st.metric("Écart-type", f"{npv_stats['ecart_type']:.0f} €")
 st.metric("P95", f"{npv_stats['percentile_95']:.0f} €")

def display_monte_carlo_recommendations(self, probabilities):
 """
 Affiche les recommandations basées sur les probabilités
 """
 st.subheader(" Recommandations")

 global_success = probabilities['global_success']

 if global_success >= 80:
 st.success(
 f" **Projet Robuste** ({global_success:.1f}% succès)\n\n"
 "Le projet présente une très bonne robustesse face aux variations. "
 "Les critères financiers sont respectés dans la majorité des scénarios."
 )

 elif global_success >= 60:
 st.warning(
 f" **Projet Modérément Robuste** ({global_success:.1f}% succès)\n\n"
 "Le projet est viable mais présente des risques. "
 "Considérer l'optimisation des paramètres ou l'ajout de garanties."
 )

 # Analyse détaillée des faiblesses
 if probabilities['tri_ok'] < 70:
 st.warning("- TRI insuffisant dans certains scénarios → Revoir le prix de vente")

 if probabilities['payback_ok'] < 70:
 st.warning("- Payback trop long dans certains cas → Optimiser l'investissement")

 if probabilities['dscr_ok'] < 70:
 st.warning("- DSCR faible → Revoir le financement ou la structure dette")

 else:
 st.error(
 f" **Projet à Risque** ({global_success:.1f}% succès)\n\n"
 "Le projet présente des risques élevés. "
 "Une révision majeure des paramètres est recommandée."
 )

 st.error("**Actions suggérées:**")
 st.error("- Augmenter le prix de vente si possible")
 st.error("- Réduire l'investissement initial")
 st.error("- Optimiser le profil de consommation")
 st.error("- Revoir la structure de financement")
```

## Graphiques de Distribution

### Histogramme des TRI
```python
def create_monte_carlo_distribution_chart(self, results):
 """
 Crée les graphiques de distribution des résultats Monte Carlo
 """
 import plotly.figure_factory as ff
 from plotly.subplots import make_subplots

 # Extraction des données
 tri_values = [r.get('irr_projet', 0) * 100 for r in results]
 npv_values = [r.get('npv_equity', 0) for r in results]

 # Création du subplot
 fig = make_subplots(
 rows=1, cols=2,
 subplot_titles=('Distribution TRI Projet (%)', 'Distribution VAN Equity (€)'),
 specs=[[{'secondary_y': False}, {'secondary_y': False}]]
 )

 # Histogramme TRI
 fig.add_trace(
 go.Histogram(
 x=tri_values,
 nbinsx=20,
 name='TRI Projet',
 marker_color='#2E86AB',
 opacity=0.7
 ),
 row=1, col=1
 )

 # Ligne de contrainte TRI
 tri_min = self.sites_config.get('constraint_min_irr_pct', 8.0)
 fig.add_vline(
 x=tri_min,
 line_dash="dash",
 line_color="red",
 annotation_text=f"TRI Min: {tri_min}%",
 row=1, col=1
 )

 # Histogramme VAN
 fig.add_trace(
 go.Histogram(
 x=npv_values,
 nbinsx=20,
 name='VAN Equity',
 marker_color='#F18F01',
 opacity=0.7
 ),
 row=1, col=2
 )

 # Ligne VAN = 0
 fig.add_vline(
 x=0,
 line_dash="dash",
 line_color="red",
 annotation_text="VAN = 0",
 row=1, col=2
 )

 # Layout
 fig.update_layout(
 title="Distribution des Résultats Monte Carlo",
 showlegend=False,
 height=400
 )

 return fig
```

---

*La simulation Monte Carlo d'OptimPV offre une évaluation quantitative de la robustesse des projets photovoltaïques, permettant une prise de décision éclairée sur les risques financiers.*