# Tableaux Annuels - Résumés Financiers

## Vue d'ensemble

Les tableaux annuels d'OptimPV affichent les résumés financiers détaillés via le module `table_finance.annual_summary_display`, avec navigation par année et export des données.

## Résumé Projet Global

### Affichage des KPIs Principaux
```python
# Fonction: display_project_summary()
# Fichier: modules/table_finance/annual_summary_display.py

def display_project_summary():
 """
 Affiche les indicateurs clés du projet
 - VAN Fonds Propres et Projet
 - TRI Fonds Propres et Projet
 - LCOE (coût de l'énergie)
 - Payback Equity et Projet
 - DSCR Moyen
 """
```

### Métriques Affichées
- **VAN Fonds Propres**: Valeur actualisée nette pour les actionnaires
- **VAN Projet**: Valeur actualisée nette globale du projet
- **TRI Fonds Propres**: Taux de rentabilité interne equity
- **TRI Projet**: Taux de rentabilité interne global
- **LCOE**: Coût actualisé de l'énergie (€/kWh)
- **Payback Equity**: Temps de retour sur fonds propres
- **Payback Projet**: Temps de retour global
- **DSCR Moyen**: Ratio de couverture du service de la dette

## Résumé Annuel Détaillé

### Interface de Navigation
```python
# Sélection d'année avec boutons et dropdown
col1, col2 = st.columns([3, 1])

with col1:
 # Boutons de navigation rapide
 years_buttons = st.columns(min(5, len(available_years)))

with col2:
 # Dropdown pour sélection précise
 selected_year = st.selectbox("Année", available_years)
```

### Structure du Compte de Résultat
```python
# Fonction: display_annual_detailed_summary()
# Structure hiérarchique professionnelle

def display_annual_detailed_summary():
 """
 Compte de résultat professionnel avec:

 REVENUS
 Ventes surplus (injection réseau)
 Valorisation autoconsommation
 Primes et subventions

 CHARGES D'EXPLOITATION
 TURPE (tarif réseau)
 Maintenance préventive/curative
 Assurance installation
 Frais administratifs
 Provisions onduleurs

 RESULTAT FINANCIER
 Produits financiers (placements)
 Charges financières (intérêts)

 RESULTAT APRES IMPOTS
 Résultat avant impôts
 Impôt sur les sociétés
 Résultat net
 """
```

### Calculs et Pourcentages
- **Revenus**: Montants et % du chiffre d'affaires
- **Charges**: Montants et % du chiffre d'affaires
- **Marges**: EBITDA, résultat opérationnel, résultat net
- **Ratios**: Taux de marge par niveau

## Gestion des Phases

### Phase de Construction
- **Investissement initial**: CAPEX total
- **Frais financiers**: Intérêts intercalaires
- **TVA**: Déductible selon statut fiscal

### Phase d'Exploitation
- **Revenus récurrents**: Production et vente d'énergie
- **Charges opérationnelles**: Maintenance, assurance, taxes
- **Amortissements**: Dépréciation des actifs

## Fonctionnalités Techniques

### Export des Données
```python
# Boutons d'export intégrés
col1, col2 = st.columns(2)

with col1:
 if st.button(" Export Excel"):
 # Génération fichier Excel avec tableaux

with col2:
 if st.button(" Export CSV"):
 # Export CSV des données tabulaires
```

### Gestion des Valeurs
```python
# Fonction: format_value() dans financial_display_utils.py

def format_value(value, format_type="currency"):
 """
 Formatage intelligent des valeurs:
 - Devise avec symbole €
 - Pourcentages avec décimales
 - Gestion NaN/Infini
 - Arrondis cohérents
 """
```

## Interface Utilisateur

### Cartes KPI
- **Codes couleur**: Vert/Rouge selon seuils
- **Delta**: Évolution vs objectifs
- **Tooltips**: Explications des métriques

### Tableaux Structurés
- **CSS harmonisé**: Style professionnel
- **Responsive**: Adaptation mobile
- **Tri et filtres**: Navigation facilitée

---

*Les tableaux annuels d'OptimPV fournissent une vision complète et professionnelle de la performance financière des projets photovoltaïques.*