# Cash Flow Mensuel - Analyse des Flux de Trésorerie

## Vue d'ensemble

Le module de cash flow mensuel d'OptimPV utilise `table_finance.monthly_cash_flow_display` pour afficher les flux de trésorerie détaillés avec configuration JSON et gestion avancée des phases projet.

## Affichage Principal

### Fonction Core
```python
# Fonction: display_cash_flow_statement_restructured()
# Fichier: modules/table_finance/monthly_cash_flow_display.py

def display_cash_flow_statement_restructured():
    """
    Affiche le tableau de flux de trésorerie mensuel restructuré
    avec configuration JSON et gestion des phases
    """
```

### Configuration via JSON
```python
# Fichier: config/monthly_cash_flow_structure.json
# Structure de configuration pour les catégories de flux

{
    "categories": {
        "revenus_exploitation": {
            "label": "Revenus d'Exploitation",
            "items": ["surplus_sales", "autoconso_valuation", "subsidies"]
        },
        "charges_exploitation": {
            "label": "Charges d'Exploitation", 
            "items": ["turpe", "maintenance", "insurance", "admin"]
        },
        "flux_financiers": {
            "label": "Flux Financiers",
            "items": ["interest_income", "interest_expense", "loan_repayment"]
        }
    }
}
```

## Structure des Flux

### Catégories de Flux
1. **Revenus d'Exploitation**
   - Ventes surplus (injection réseau)
   - Valorisation autoconsommation
   - Primes et subventions

2. **Charges d'Exploitation**
   - TURPE (tarif d'utilisation réseau)
   - Maintenance préventive/curative
   - Assurance installation
   - Frais administratifs
   - Provisions onduleurs

3. **Flux Financiers**
   - Produits de placement (si trésorerie activée)
   - Charges d'intérêts (emprunts)
   - Remboursement capital emprunts

4. **Flux d'Investissement**
   - CAPEX initial (phase construction)
   - Remplacement onduleurs
   - Améliorations installation

5. **Flux de Financement**
   - Apports en capital
   - Tirages emprunts
   - Dividendes (si applicables)

## Gestion des Phases

### Phase de Construction
```python
# Gestion spécifique phase construction
if is_construction_phase(month):
    # Affichage CAPEX et financement initial
    # Pas de revenus d'exploitation
    # Frais financiers intercalaires
```

### Phase d'Exploitation
```python
# Gestion phase opérationnelle
if is_operational_phase(month):
    # Revenus récurrents (production énergie)
    # Charges opérationnelles
    # Service de la dette
    # Gestion trésorerie
```

## Gestion de Trésorerie

### Placement Automatique
```python
# Si treasury_placement activé dans configuration
if config.get('treasury_placement', False):
    # Calcul réserve minimum
    # Placement excédents
    # Génération revenus financiers
    # Gestion des retraits
```

### Indicateurs de Santé Financière
- **Réserve minimum** : Seuil de sécurité trésorerie
- **Excédent disponible** : Montant placeable
- **Rendement placement** : Taux de rémunération
- **Alertes** : Niveau de trésorerie critique

## Calculs Automatiques

### Distinction Flux/Soldes
```python
# Fonction: calculate_annual_total_from_monthly()
# Fichier: modules/table_finance/financial_display_utils.py

def calculate_annual_total_from_monthly(monthly_values, item_name):
    """
    Calcul intelligent total annuel:
    - FLUX (revenus, charges) → Somme des 12 mois
    - SOLDES (trésorerie, dette) → Valeur en fin d'année
    """
    
    if is_balance_item(item_name):
        # Solde: prendre la dernière valeur non-nulle
        return get_last_non_null_value(monthly_values)
    else:
        # Flux: sommer toutes les valeurs
        return sum(monthly_values)
```

### Ratios Mensuels
- **DSCR mensuel** : Couverture service dette
- **Taux marge** : Par catégorie de revenus
- **Taux autoconsommation** : Énergie autoconsommée/produite
- **Taux autoproduction** : Production/consommation

## Interface et Affichage

### Navigation Mensuelle
```python
# Sélecteur de mois avec navigation
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if st.button("← Mois Précédent"):
        # Navigation backward
        
with col2:
    selected_month = st.selectbox("Mois", month_list)
    
with col3:
    if st.button("Mois Suivant →"):
        # Navigation forward
```

### Tableaux Formatés
```python
# CSS styling harmonisé
def get_table_css():
    """
    Retourne CSS pour tableaux financiers:
    - Headers avec couleur corporate
    - Bordures et espacements
    - Responsive design
    - Print-friendly
    """
```

### Alertes Automatiques
- Trésorerie saine : Réserve > minimum + marge
- Vigilance : Réserve proche du minimum
- Alerte : Réserve insuffisante ou DSCR < 1.2

## Export et Partage

### Export Excel
```python
if st.button("Export Cash Flow Excel"):
    # Génération fichier avec:
    # - Feuille flux mensuels
    # - Feuille résumé annuel  
    # - Feuille ratios et KPIs
    # - Graphiques intégrés
```

### Export CSV
```python
if st.button("Export CSV"):
    # Export données tabulaires
    # Format compatible tableurs
    # Headers explicites
```

## Fonctionnalités Avancées

### Drill-down par Catégorie
- **Clic sur catégorie** : Détail des composants
- **Historique** : Évolution sur plusieurs années
- **Comparaisons** : Budget vs réalisé (si données)

### Détection Anomalies
- **Valeurs aberrantes** : Détection automatique
- **Tendances** : Analyse des variations
- **Seuils** : Alertes personnalisables

---

*Le module de cash flow mensuel d'OptimPV offre une vision détaillée et professionnelle de la santé financière des projets photovoltaïques avec gestion avancée de la trésorerie.*