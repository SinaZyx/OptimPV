# Optimisation de Prix - Algorithme SLSQP

## Vue d'ensemble

L'optimisation de prix dans OptimPV utilise l'algorithme SLSQP (Sequential Least Squares Programming) avec stratégie multi-start pour trouver le prix de vente optimal sous contraintes financières.

## Implémentation SLSQP

### Configuration de l'Optimiseur
```python
class OptimizationLogic:
 def __init__(self, analysis_engine):
 self.analysis_engine = analysis_engine

 def optimize_price(self, constraints):
 """
 Optimise le prix de vente sous contraintes multiples

 Algorithme: SLSQP avec multi-start (3 points de départ)
 Objectif: Maximiser le prix tout en respectant les contraintes
 """

 # Points de départ pour multi-start
 starting_points = [
 self.prix_plancher * 1.05, # 5% au-dessus du plancher
 (self.prix_plancher + self.tarif_edf) / 2, # Milieu
 self.tarif_edf * 0.95 # 5% sous tarif EDF
 ]

 best_result = None
 best_price = 0

 for start_price in starting_points:
 result = scipy.optimize.minimize(
 fun=self._objective_function,
 x0=[start_price],
 method='SLSQP',
 bounds=[(self.prix_plancher, self.tarif_edf)],
 constraints=self._build_constraints(constraints),
 options={'ftol': 1e-9, 'disp': False}
 )

 if result.success and result.fun < 0: # Maximisation
 if -result.fun > best_price:
 best_price = -result.fun
 best_result = result

 return best_result
```

### Fonction Objectif
```python
def _objective_function(self, price):
 """
 Fonction objectif: maximiser le prix de vente
 (minimisation de -prix pour scipy.optimize)
 """
 return -price[0] # Négation pour maximisation

def _build_constraints(self, user_constraints):
 """
 Construction des contraintes d'optimisation
 """
 constraints = []

 # Contrainte TRI projet minimum
 if user_constraints.get('tri_projet_min'):
 constraints.append({
 'type': 'ineq',
 'fun': lambda p: self._calculate_tri_projet(p[0]) - user_constraints['tri_projet_min']
 })

 # Contrainte Payback maximum
 if user_constraints.get('payback_max'):
 constraints.append({
 'type': 'ineq',
 'fun': lambda p: user_constraints['payback_max'] - self._calculate_payback(p[0])
 })

 # Contrainte gain client minimum
 if user_constraints.get('gain_client_min'):
 constraints.append({
 'type': 'ineq',
 'fun': lambda p: self._calculate_gain_client(p[0]) - user_constraints['gain_client_min']
 })

 return constraints
```

## Calculs des Métriques

### TRI Projet (IRR)
```python
def _calculate_tri_projet(self, prix_vente):
 """
 Calcule le TRI projet avec le prix de vente donné
 """
 # Mise à jour des paramètres
 self.analysis_engine.update_selling_price(prix_vente)

 # Recalcul des cash flows
 results = self.analysis_engine.calculate_all_metrics()

 # Gestion cas financement 100% dette
 if self.analysis_engine.is_full_debt_financing():
 return results.get('irr_projet', 0)
 else:
 return results.get('irr_fonds_propres', 0)

def _calculate_payback(self, prix_vente):
 """
 Calcule le temps de retour avec le prix donné
 """
 self.analysis_engine.update_selling_price(prix_vente)
 results = self.analysis_engine.calculate_all_metrics()

 if self.analysis_engine.is_full_debt_financing():
 return results.get('payback_projet', float('inf'))
 else:
 return results.get('payback_equity', float('inf'))

def _calculate_gain_client(self, prix_vente):
 """
 Calcule le gain client annuel vs tarif EDF
 """
 # Économies annuelles client
 autoconso_kwh = self.analysis_engine.get_autoconsommation_annuelle()
 tarif_edf_ttc = self.analysis_engine.get_tarif_edf_reference()

 # Gain = (Tarif EDF - Prix de vente) × Autoconsommation
 gain_unitaire = tarif_edf_ttc - prix_vente * 1.20 # TVA 20%
 gain_total = gain_unitaire * autoconso_kwh

 return gain_total
```

## Interface Utilisateur

### Configuration des Contraintes
```python
# Dans ui_page.py
col1, col2, col3 = st.columns(3)

with col1:
 tri_min = st.number_input(
 "TRI Projet Minimum (%)",
 min_value=0.0,
 max_value=30.0,
 value=8.0,
 step=0.1,
 key="tri_min_constraint"
 )

with col2:
 payback_max = st.number_input(
 "Payback Maximum (ans)",
 min_value=1.0,
 max_value=30.0,
 value=18.0,
 step=0.5,
 key="payback_max_constraint"
 )

with col3:
 gain_client_min = st.slider(
 "Gain Client Minimum (%)",
 min_value=0,
 max_value=50,
 value=0,
 step=1,
 key="gain_client_min_constraint"
 )
```

### Lancement de l'Optimisation
```python
if st.button(" Lancer l'Optimisation", type="primary"):
 with st.spinner("Optimisation en cours..."):
 constraints = {
 'tri_projet_min': tri_min / 100,
 'payback_max': payback_max,
 'gain_client_min': gain_client_min / 100
 }

 try:
 result = optimizer.optimize_price(constraints)

 if result and result.success:
 prix_optimal = result.x[0]
 st.success(f" Prix optimal trouvé: {prix_optimal:.4f} €/kWh HT")

 # Mise à jour de l'état
 st.session_state.prix_optimal = prix_optimal
 st.session_state.optimization_success = True

 else:
 st.error(" Aucune solution trouvée respectant toutes les contraintes")

 except Exception as e:
 st.error(f" Erreur d'optimisation: {str(e)}")
```

## Gestion des Cas Particuliers

### Financement 100% Dette
```python
def handle_full_debt_financing(self):
 """
 Adaptation pour projets financés à 100% par dette
 - Masquage des indicateurs fonds propres
 - Utilisation TRI projet uniquement
 - Payback calculé sur cash flows projet
 """
 if self.analysis_engine.is_full_debt_financing():
 # Masquer les métriques equity
 self.show_equity_metrics = False

 # Adapter les contraintes
 self.use_project_metrics_only = True

 # Message d'information
 st.info(" Financement 100% dette détecté - Utilisation TRI projet uniquement")

def handle_minimal_equity(self):
 """
 Gestion des cas où les fonds propres sont très faibles
 """
 fonds_propres = self.analysis_engine.get_fonds_propres()

 if fonds_propres < 1000: # Seuil en euros
 st.warning(" Fonds propres très faibles - Métriques equity peu fiables")

 # Proposer alternative
 st.info(" Conseil: Privilégier l'analyse TRI projet")
```

## Résultats et Validation

### Affichage des Résultats
```python
def display_optimization_results(self, prix_optimal):
 """
 Affiche les résultats de l'optimisation
 """
 # Métriques au prix optimal
 metrics = self.analysis_engine.calculate_metrics_at_price(prix_optimal)

 col1, col2, col3 = st.columns(3)

 with col1:
 st.metric(
 "Prix Optimal (HT)",
 f"{prix_optimal:.4f} €/kWh",
 delta=f"+{((prix_optimal/self.prix_plancher-1)*100):.1f}% vs plancher"
 )

 with col2:
 tri_value = metrics.get('tri_projet', 0) * 100
 st.metric(
 "TRI Projet Résultant",
 f"{tri_value:.1f}%",
 delta="" if tri_value >= self.constraints['tri_min']*100 else ""
 )

 with col3:
 payback_value = metrics.get('payback', 0)
 st.metric(
 "Payback Résultant",
 f"{payback_value:.1f} ans",
 delta="" if payback_value <= self.constraints['payback_max'] else ""
 )

def validate_constraints(self, prix_optimal):
 """
 Valide que toutes les contraintes sont respectées
 """
 metrics = self.analysis_engine.calculate_metrics_at_price(prix_optimal)

 validation_results = {
 'tri_ok': metrics.get('tri_projet', 0) >= self.constraints['tri_min'],
 'payback_ok': metrics.get('payback', float('inf')) <= self.constraints['payback_max'],
 'gain_client_ok': self.calculate_gain_client(prix_optimal) >= self.constraints['gain_client_min']
 }

 all_valid = all(validation_results.values())

 if not all_valid:
 st.warning(" Certaines contraintes ne sont pas parfaitement respectées")

 for constraint, valid in validation_results.items():
 if not valid:
 st.error(f" Contrainte {constraint} non respectée")

 return all_valid
```

---

*L'optimisation SLSQP d'OptimPV offre une approche robuste et fiable pour trouver le prix de vente optimal tout en garantissant le respect des contraintes financières définies par l'utilisateur.*