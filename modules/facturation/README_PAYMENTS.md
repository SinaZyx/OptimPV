# Système de Gestion Avancée des Paiements - OptimPV

Ce module implémente un système complet de gestion des paiements pour OptimPV, incluant l'import bancaire, le rapprochement automatique, les relances automatisées et l'analyse des KPIs financiers.

## 🚀 Fonctionnalités Principales

### 1. Import Bancaire Automatisé
- **Support des formats OFX et QIF** pour l'import des relevés bancaires
- **Détection automatique des doublons** avec gestion des identifiants uniques
- **Validation et nettoyage des données** importées
- **Traçabilité des imports** avec batch IDs

### 2. Rapprochement Automatique des Paiements
- **Fuzzy matching** intelligent basé sur :
  - Montants (tolérance configurable)
  - Dates de transaction vs échéances
  - Noms des clients (similarité textuelle)
  - Références de factures dans les libellés
- **Score de confiance** pour chaque rapprochement
- **Suggestions manuelles** pour les cas ambigus

### 3. Gestion Multi-Moyens de Paiement
- Virement bancaire (SEPA)
- Prélèvement automatique SEPA
- Carte bancaire
- Chèque
- Espèces
- Autres moyens personnalisés

### 4. Échéanciers de Paiement
- **Paiements fractionnés** en plusieurs échéances
- **Suivi automatique** des échéances
- **Alertes d'impayés** par échéance
- **Calcul des pénalités** par échéance

### 5. Système de Relances Automatisées (Dunning)
- **5 niveaux de relance** configurables :
  1. Rappel amical (J+7)
  2. Première mise en demeure (J+15)
  3. Seconde mise en demeure (J+30)
  4. Dernier avis (J+45)
  5. Action juridique (J+60)
- **Templates d'emails personnalisables**
- **Calcul automatique des pénalités de retard** (taux légal français)
- **Planification automatique** des prochaines actions

### 6. Dashboard et KPIs Financiers
- **DSO (Days Sales Outstanding)** avec tendances
- **Analyse de l'aging** des créances (0-30j, 31-60j, 61-90j, 90j+)
- **Taux de recouvrement** et performance de collection
- **Prévisions de trésorerie** basées sur l'historique
- **Analyse par moyens de paiement**

## 📁 Structure des Fichiers

```
modules/facturation/
├── payment_manager.py     # Gestionnaire principal des paiements
├── dunning.py            # Système de relances automatisées
├── payment_dashboard.py  # KPIs et analytics
├── database.py          # Schema de base étendu
├── payment_example.py   # Exemples d'utilisation
└── README_PAYMENTS.md   # Cette documentation
```

## 🗄️ Nouvelles Tables de Base de Données

### Tables Principales
- **`payment_methods`** - Moyens de paiement disponibles
- **`payment_schedules`** - Échéanciers de paiement
- **`dunning_actions`** - Historique des relances
- **`bank_transactions`** - Transactions bancaires importées
- **`late_fees`** - Pénalités de retard appliquées
- **`email_templates`** - Templates d'emails de relance
- **`dunning_rules`** - Configuration des règles de relance
- **`payment_kpis`** - Cache des KPIs calculés

### Index de Performance
- Index sur les dates de paiement et d'échéance
- Index sur les statuts des factures et transactions
- Index sur les IDs de factures pour jointures rapides

## 🔧 Utilisation

### Import de Relevés Bancaires

```python
from payment_manager import PaymentManager

payment_mgr = PaymentManager()

# Import OFX
with open('releve.ofx', 'r') as f:
    ofx_content = f.read()

imported_count, errors = payment_mgr.import_ofx(
    ofx_content, 
    account_number="FR7612345678901234567890"
)

# Import QIF
with open('releve.qif', 'r') as f:
    qif_content = f.read()

imported_count, errors = payment_mgr.import_qif(
    qif_content,
    account_number="FR7612345678901234567890"
)
```

### Rapprochement Automatique

```python
# Lancement du rapprochement automatique
results = payment_mgr.match_payments_to_invoices(
    date_tolerance_days=7,
    amount_tolerance_percent=2.0
)

print(f"Auto-matched: {results['auto_matches_count']}")
print(f"Manual review needed: {results['suggestions_count']}")

# Rapprochement manuel
payment_mgr.manual_match_payment(
    transaction_id=123,
    invoice_id=456
)
```

### Gestion des Échéanciers

```python
# Créer un échéancier de 3 paiements
schedule_ids = payment_mgr.create_payment_schedule(
    invoice_id=1,
    installments=3,
    start_date=date.today()
)

# Vérifier les échéances en retard
overdue = payment_mgr.get_overdue_installments()
```

### Traitement des Paiements

```python
from payment_manager import PaymentMethod

# Enregistrer un paiement
payment_id = payment_mgr.process_payment(
    invoice_id=1,
    amount=1250.00,
    payment_method=PaymentMethod.VIREMENT,
    transaction_id="VIR2024001",
    notes="Paiement client"
)
```

### Système de Relances

```python
from dunning import DunningManager, DunningLevel

dunning_mgr = DunningManager()

# Configuration SMTP
dunning_mgr.configure_smtp(
    smtp_host="smtp.your-domain.com",
    smtp_port=587,
    username="billing@optimpv.com",
    password="your_password"
)

# Lancement automatique des relances
results = dunning_mgr.process_dunning_cycle()

# Relance manuelle
dunning_mgr.send_manual_dunning(
    invoice_id=1,
    level=DunningLevel.FIRST_NOTICE,
    email_address="client@example.com"
)
```

### Calcul des Pénalités

```python
# Calcul automatique selon le taux légal
late_fee = payment_mgr.calculate_late_fees(
    invoice_id=1,
    calculation_date=date.today()
)

if late_fee:
    print(f"Pénalité: {late_fee.calculated_fee}€ "
          f"({late_fee.days_late} jours de retard)")
    
    # Application de la pénalité
    payment_mgr.apply_late_fee(
        invoice_id=1,
        fee_amount=late_fee.calculated_fee,
        reason=f"Pénalité légale {late_fee.legal_rate}%"
    )
```

### Dashboard et KPIs

```python
from payment_dashboard import PaymentDashboard

dashboard = PaymentDashboard()

# Calcul du DSO
dso = dashboard.calculate_dso(period_days=90)
print(f"DSO: {dso.dso_days} jours")

# Analyse de l'aging
aging = dashboard.calculate_aging_buckets()
for bucket in aging:
    print(f"{bucket.bucket_name}: {bucket.total_amount}€")

# Métriques de collection
metrics = dashboard.calculate_collection_rate()
print(f"Taux de recouvrement: {metrics.collection_rate}%")

# Prévisions de trésorerie
forecast = dashboard.generate_cash_flow_forecast(90)
weekly_summary = dashboard.get_weekly_cash_flow_summary(12)

# KPIs complets
kpis = dashboard.get_payment_kpis()
```

## ⚙️ Configuration

### Templates d'Emails

Les templates d'emails sont personnalisables via la classe `DunningManager`. Variables disponibles :
- `{invoice_number}` - Numéro de facture
- `{due_date}` - Date d'échéance
- `{amount}` - Montant dû
- `{late_fees}` - Pénalités de retard
- `{participant_name}` - Nom du client
- `{project_name}` - Nom du projet
- `{days_overdue}` - Nombre de jours de retard

### Règles de Relance

Les règles de relance sont configurables dans la table `dunning_rules` :
- Délais après échéance
- Inclusion des pénalités
- Arrêt des services
- Escalade juridique
- Copie au manager

### Taux Légal

Le taux légal français est configuré dans `PaymentManager` (3.40% en 2024). À mettre à jour selon les évolutions légales.

## 🔍 Monitoring et Logs

Tous les modules utilisent le système de logging Python standard :
- Niveau INFO pour les opérations normales
- Niveau WARNING pour les erreurs récupérables
- Niveau ERROR pour les erreurs critiques

## 🚨 Gestion des Erreurs

- **Import bancaire** : Validation des formats, gestion des doublons
- **Rapprochement** : Tolérance configurable, suggestions manuelles
- **Emails** : Gestion des erreurs SMTP, retry automatique
- **Base de données** : Transactions atomiques, rollback en cas d'erreur

## 🔒 Sécurité

- **Validation des données** d'import
- **Chiffrement des mots de passe** SMTP (recommandé)
- **Logging des actions** pour audit
- **Contrôles d'intégrité** des montants

## 📊 Performance

- **Index optimisés** sur les colonnes de recherche fréquente
- **Cache des KPIs** pour éviter les recalculs
- **Pagination** des résultats pour les gros volumes
- **Traitement par batch** pour les imports volumineux

## 🔮 Évolutions Futures

- **API REST** pour intégration externe
- **Webhook** pour notifications temps réel
- **Machine Learning** pour améliorer le matching
- **Dashboard web** interactif
- **Export comptable** vers logiciels tiers