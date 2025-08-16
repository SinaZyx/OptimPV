# Calculs des Seuils - Prix Plancher et LCOE

## Vue d'ensemble

Le calcul des seuils dans OptimPV détermine les bornes financières fondamentales: le prix plancher (VAN=0) et le LCOE (coût de l'énergie), essentiels pour l'optimisation et la viabilité du projet.

## Prix Plancher (VAN = 0)

### Principe de Calcul
```python
def calculate_prix_plancher(self):
 """
 Calcule le prix plancher par simulation itérative
 Objectif: Trouver le prix où VAN = 0
 """
 def npv_at_price(price):
 """Fonction objectif: VAN à un prix donné"""
 self.analysis_engine.update_selling_price(price[0])
 results = self.analysis_engine.calculate_all_metrics()
 return abs(results.get('npv', 0)) # Valeur absolue pour minimisation

 # Estimation initiale basée sur LCOE
 lcoe = self.calculate_lcoe()
 initial_guess = lcoe * 1.1 # 10% au-dessus du LCOE

 # Optimisation par minimisation
 result = scipy.optimize.minimize(
 fun=npv_at_price,
 x0=[initial_guess],
 method='SLSQP',
 bounds=[(lcoe * 0.8, lcoe * 2.0)], # Bornes raisonnables
 options={'ftol': 1e-6}
 )

 if result.success:
 return result.x[0]
 else:
 # Fallback: recherche par dichotomie
 return self._binary_search_plancher(lcoe * 0.8, lcoe * 2.0)
```

### Recherche par Dichotomie (Fallback)
```python
def _binary_search_plancher(self, prix_min, prix_max, tolerance=1e-4):
 """
 Méthode de fallback si SLSQP échoue
 Recherche dichotomique du prix où VAN ≈ 0
 """
 max_iterations = 50
 iteration = 0

 while abs(prix_max - prix_min) > tolerance and iteration < max_iterations:
 prix_milieu = (prix_min + prix_max) / 2

 # Calcul VAN au prix milieu
 self.analysis_engine.update_selling_price(prix_milieu)
 results = self.analysis_engine.calculate_all_metrics()
 npv = results.get('npv', 0)

 if npv > 0:
 # VAN positive → prix trop haut → réduire borne haute
 prix_max = prix_milieu
 else:
 # VAN négative → prix trop bas → augmenter borne basse
 prix_min = prix_milieu

 iteration += 1

 return (prix_min + prix_max) / 2
```

### Validation du Prix Plancher
```python
def validate_prix_plancher(self, prix_plancher):
 """
 Valide que le prix plancher calculé est cohérent
 """
 # Test: VAN doit être proche de 0 (±1000€)
 self.analysis_engine.update_selling_price(prix_plancher)
 results = self.analysis_engine.calculate_all_metrics()
 npv = results.get('npv', 0)

 validation = {
 'npv_close_to_zero': abs(npv) < 1000, # €
 'price_reasonable': 0.05 <= prix_plancher <= 0.50, # €/kWh
 'price_above_lcoe': prix_plancher >= self.calculate_lcoe()
 }

 all_valid = all(validation.values())

 if not all_valid:
 st.warning(" Prix plancher calculé potentiellement incorrect")
 for check, valid in validation.items():
 if not valid:
 st.error(f" Validation {check} échouée")

 return all_valid, validation
```

## LCOE (Levelized Cost of Energy)

### Calcul Standard
```python
def calculate_lcoe(self):
 """
 Calcule le LCOE selon la méthodologie standard
 LCOE = Σ(CAPEX + OPEX)t / (1+r)^t / Σ(Production)t / (1+r)^t
 """
 project_data = self.analysis_engine.get_project_data()

 # Paramètres de base
 capex_initial = project_data['investment_total']
 annual_opex = project_data['opex_annual']
 annual_production = project_data['production_annuelle_kwh']
 discount_rate = project_data['wacc']
 project_lifetime = project_data['duree_vie_projet']

 # Calcul numérateur: coûts actualisés
 numerateur = capex_initial # Investissement initial (t=0)

 for year in range(1, project_lifetime + 1):
 # OPEX avec escalation (inflation)
 opex_year = annual_opex * (1 + project_data['inflation_rate']) ** year

 # Actualisation
 opex_actualisé = opex_year / (1 + discount_rate) ** year
 numerateur += opex_actualisé

 # Calcul dénominateur: production actualisée
 dénominateur = 0

 for year in range(1, project_lifetime + 1):
 # Production avec dégradation
 degradation_cumulative = (1 - project_data['degradation_rate']) ** year
 production_year = annual_production * degradation_cumulative

 # Actualisation
 production_actualisée = production_year / (1 + discount_rate) ** year
 dénominateur += production_actualisée

 # LCOE final
 lcoe = numerateur / dénominateur

 return lcoe
```

### Décomposition du LCOE
```python
def analyze_lcoe_components(self):
 """
 Décompose le LCOE par composants pour analyse
 """
 project_data = self.analysis_engine.get_project_data()

 components = {
 'capex_component': 0,
 'opex_maintenance': 0,
 'opex_insurance': 0,
 'opex_monitoring': 0,
 'financing_cost': 0
 }

 # Même calcul que LCOE mais par composant
 total_production_actualisée = self._calculate_total_discounted_production()

 # CAPEX component
 components['capex_component'] = project_data['investment_total'] / total_production_actualisée

 # OPEX components
 opex_breakdown = project_data.get('opex_breakdown', {})
 for category, annual_cost in opex_breakdown.items():
 discounted_cost = self._calculate_discounted_opex(annual_cost)
 components[f'opex_{category}'] = discounted_cost / total_production_actualisée

 # Validation
 total_lcoe = sum(components.values())
 calculated_lcoe = self.calculate_lcoe()

 if abs(total_lcoe - calculated_lcoe) > 0.001: # Tolérance 0.1 c€/kWh
 st.warning(" Incohérence dans la décomposition LCOE")

 return components

def _calculate_total_discounted_production(self):
 """Helper: calcule la production totale actualisée"""
 project_data = self.analysis_engine.get_project_data()

 total = 0
 for year in range(1, project_data['duree_vie_projet'] + 1):
 degradation = (1 - project_data['degradation_rate']) ** year
 production_year = project_data['production_annuelle_kwh'] * degradation
 production_actualisée = production_year / (1 + project_data['wacc']) ** year
 total += production_actualisée

 return total
```

## Tarif de Référence EDF

### Récupération du Tarif TTC
```python
def get_tarif_edf_reference(self):
 """
 Récupère le tarif EDF de référence TTC
 Utilisé comme borne haute pour l'optimisation
 """
 # Tarif réglementé en vigueur (mis à jour régulièrement)
 tarif_base_ht = 0.2134 # €/kWh base février 2024
 tva_rate = 0.20 # 20% TVA

 tarif_ttc = tarif_base_ht * (1 + tva_rate)

 # Validation cohérence
 if not (0.15 <= tarif_ttc <= 0.40): # Bornes de sanité
 st.warning(f" Tarif EDF hors bornes attendues: {tarif_ttc:.4f} €/kWh")

 return tarif_ttc

def compare_with_market_rates(self):
 """
 Compare avec autres tarifs du marché
 """
 tarif_edf = self.get_tarif_edf_reference()

 market_comparison = {
 'edf_tarif_bleu': tarif_edf,
 'heures_creuses_moyenne': tarif_edf * 0.85, # Estimation
 'fournisseurs_alternatifs': tarif_edf * 0.95, # Moyenne marché
 'entreprises_tarif_jaune': tarif_edf * 0.90 # Estimation pro
 }

 return market_comparison
```

## Interface Utilisateur

### Affichage des Seuils
```python
# Dans ui_page.py
def display_calculated_thresholds(self):
 """
 Affiche les seuils calculés dans l'interface
 """
 col1, col2, col3 = st.columns(3)

 with col1:
 st.metric(
 label="Prix Plancher Prod. (HT)",
 value=f"{self.prix_plancher:.4f} €/kWh",
 help="Prix minimum pour VAN = 0"
 )

 with col2:
 st.metric(
 label="LCOE (HT)",
 value=f"{self.lcoe:.4f} €/kWh",
 help="Coût de production de l'énergie"
 )

 with col3:
 st.metric(
 label="Tarif EDF Réf. (TTC)",
 value=f"{self.tarif_edf:.4f} €/kWh",
 help="Tarif réglementé de référence"
 )

 # Indicateur de marge
 marge_disponible = self.tarif_edf - self.prix_plancher * 1.20 # Avec TVA

 if marge_disponible > 0:
 st.success(f" Marge disponible: {marge_disponible:.4f} €/kWh")
 else:
 st.error(f" Projet non viable: déficit de {abs(marge_disponible):.4f} €/kWh")

def display_lcoe_breakdown(self):
 """
 Affiche la décomposition du LCOE
 """
 components = self.analyze_lcoe_components()

 st.subheader(" Décomposition LCOE")

 chart_data = pd.DataFrame([
 {"Composant": "CAPEX", "Coût": components['capex_component']},
 {"Composant": "Maintenance", "Coût": components['opex_maintenance']},
 {"Composant": "Assurance", "Coût": components['opex_insurance']},
 {"Composant": "Monitoring", "Coût": components['opex_monitoring']}
 ])

 fig = px.pie(
 chart_data,
 values='Coût',
 names='Composant',
 title="Répartition du LCOE par composant"
 )

 st.plotly_chart(fig, use_container_width=True)
```

## Mise à Jour Dynamique

### Recalcul Automatique
```python
def auto_update_thresholds(self):
 """
 Recalcule automatiquement les seuils si paramètres changent
 """
 # Détection changements dans session_state
 if self._has_parameters_changed():
 with st.spinner("Recalcul des seuils..."):
 try:
 # Recalcul LCOE
 self.lcoe = self.calculate_lcoe()

 # Recalcul prix plancher
 self.prix_plancher = self.calculate_prix_plancher()

 # Validation
 valid, checks = self.validate_prix_plancher(self.prix_plancher)

 if valid:
 st.success(" Seuils mis à jour")
 else:
 st.warning(" Seuils recalculés avec avertissements")

 # Sauvegarde dans session_state
 st.session_state.lcoe = self.lcoe
 st.session_state.prix_plancher = self.prix_plancher

 except Exception as e:
 st.error(f" Erreur recalcul seuils: {str(e)}")

def _has_parameters_changed(self):
 """
 Détecte si les paramètres ont changé depuis le dernier calcul
 """
 current_hash = self._hash_parameters()
 previous_hash = st.session_state.get('parameters_hash', None)

 if current_hash!= previous_hash:
 st.session_state.parameters_hash = current_hash
 return True

 return False

def _hash_parameters(self):
 """
 Calcule un hash des paramètres critiques
 """
 import hashlib

 critical_params = {
 'investment': self.analysis_engine.get_investment_total(),
 'production': self.analysis_engine.get_annual_production(),
 'wacc': self.analysis_engine.get_wacc(),
 'opex': self.analysis_engine.get_annual_opex()
 }

 params_str = str(sorted(critical_params.items()))
 return hashlib.md5(params_str.encode()).hexdigest()
```

---

*Le calcul des seuils d'OptimPV fournit les bornes financières essentielles pour l'optimisation, garantissant la viabilité économique et l'attractivité commerciale du projet.*