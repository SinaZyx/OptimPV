# 💰 Module de Facturation OptimPV

## Vue d'ensemble

Le module de facturation OptimPV est une solution professionnelle complète de gestion de la facturation pour l'autoconsommation collective photovoltaïque. Il offre toutes les fonctionnalités nécessaires pour gérer efficacement la facturation, les paiements, les analyses financières et les intégrations avec des systèmes externes.

## 🚀 Fonctionnalités principales

### ✅ Gestion complète des projets et participants
- Création et gestion de projets photovoltaïques
- Gestion des participants (producteurs/consommateurs)
- Répartition automatique des allocations d'énergie
- Import automatique depuis les clés de répartition OptimPV

### 💰 Facturation professionnelle
- Calcul automatique basé sur l'autoconsommation réelle
- Numérotation séquentielle sans trous
- Gestion des avoirs et factures rectificatives
- Facturation récurrente automatique
- Templates de facturation personnalisables

### 📄 Génération de documents PDF
- Templates PDF personnalisables (moderne, minimal, corporate)
- QR codes de paiement standard européen (EPC)
- Multi-langues (français/anglais)
- Watermarks automatiques selon le statut
- Export en masse et programmé

### 💳 Gestion avancée des paiements
- Support multi-moyens de paiement (virement, SEPA, CB, chèque)
- Import bancaire automatique (OFX/QIF)
- Rapprochement automatique des paiements
- Échéanciers personnalisés
- Calcul automatique des pénalités de retard

### 📊 Analytics et reporting
- 37+ KPIs financiers et opérationnels
- Dashboard exécutif avec métriques temps réel
- Prévisions de trésorerie avec machine learning
- Analyse prédictive des impayés
- Rapports automatiques multi-formats (PDF, Excel, CSV)

### 🤖 Automatisation intelligente
- Workflow de validation configurable
- Relances automatiques multi-niveaux
- Planificateur CRON pour tâches récurrentes
- Notifications multi-canaux (email, SMS, webhooks)
- Intégration avec systèmes externes

### 🔌 API REST complète
- Documentation Swagger automatique
- Authentification JWT sécurisée
- Webhooks pour événements temps réel
- Rate limiting et monitoring
- Intégrations ERP (Sage, Cegid, Odoo)

### 🎨 Interface utilisateur moderne
- Design responsive intégré avec OptimPV
- Navigation intuitive avec recherche avancée
- Actions en masse et auto-save
- Tour guidé pour nouveaux utilisateurs
- Thème unifié avec l'application principale

## 📁 Structure du module

```
modules/facturation/
├── 📄 README.md                          # Ce fichier
├── 📄 __init__.py                        # Point d'entrée du module
├── 📄 main.py                            # Interface Streamlit principale
├── 📄 models.py                          # Modèles de données
├── 📄 database.py                        # Gestionnaire de base de données SQLite
├── 📄 integration_helper.py              # Intégration avec OptimPV
│
├── 🧾 Génération de documents
│   ├── invoice_generator.py              # Générateur de factures PDF
│   ├── pdf_templates.py                  # Système de templates PDF
│   ├── pdf_config.py                     # Configuration des templates
│   ├── qr_payment.py                     # QR codes de paiement EPC
│   └── templates/                        # Templates JSON prédéfinis
│       ├── modern.json
│       ├── minimal.json
│       └── corporate.json
│
├── 💰 Gestion financière
│   ├── accounting.py                     # Gestionnaire comptable et export FEC
│   ├── invoice_numbering.py              # Numérotation séquentielle
│   ├── payment_manager.py                # Gestion des paiements
│   ├── dunning.py                        # Relances automatiques
│   └── payment_dashboard.py              # Tableau de bord paiements
│
├── 📊 Analytics et reporting
│   ├── analytics.py                      # Moteur d'analyse et KPIs
│   ├── reporting.py                      # Générateur de rapports
│   ├── dashboard_data.py                 # Données pour tableau de bord
│   ├── forecasting.py                    # Prévisions et ML
│   └── kpi_calculator.py                 # Calculateur de KPIs
│
├── 🤖 Automatisation
│   ├── automation.py                     # Moteur d'automatisation
│   ├── recurring_billing.py              # Facturation récurrente
│   ├── workflow.py                       # Gestion des workflows
│   ├── scheduler.py                      # Planificateur de tâches
│   └── notifications.py                  # Système de notifications
│
├── 📧 Communication
│   ├── email_sender.py                   # Envoi d'emails
│   ├── webhooks.py                       # Gestion des webhooks
│   └── external_integrations.py          # Intégrations ERP
│
├── 🔌 API REST
│   ├── api/
│   │   ├── api_server.py                 # Serveur FastAPI
│   │   ├── routes/                       # Endpoints par domaine
│   │   │   ├── projects.py
│   │   │   ├── participants.py
│   │   │   ├── invoices.py
│   │   │   ├── payments.py
│   │   │   ├── reports.py
│   │   │   └── webhooks.py
│   │   ├── middleware/                   # Authentification, CORS, logging
│   │   │   ├── auth.py
│   │   │   ├── cors.py
│   │   │   ├── logging.py
│   │   │   └── rate_limiting.py
│   │   └── schemas/                      # Modèles Pydantic
│   │       ├── project_schemas.py
│   │       ├── participant_schemas.py
│   │       ├── invoice_schemas.py
│   │       └── payment_schemas.py
│
├── 🎨 Interface utilisateur
│   ├── ui_components.py                  # Composants réutilisables
│   ├── export_manager.py                 # Gestionnaire d'exports
│   └── state_manager.py                  # Gestion d'état avancée
│
└── 📚 Configuration et dépendances
    ├── requirements_api.txt               # Dépendances pour l'API
    └── data/                             # Base de données SQLite
        └── billing.db
```

## 🛠️ Installation

### Prérequis
- Python 3.8+
- SQLite 3
- OptimPV installé

### Installation des dépendances

```bash
# Dépendances de base (incluses dans OptimPV)
pip install streamlit pandas numpy plotly

# Dépendances optionnelles pour fonctionnalités avancées
pip install reportlab           # Pour génération PDF
pip install openpyxl           # Pour exports Excel avancés
pip install scikit-learn       # Pour machine learning
pip install fastapi uvicorn    # Pour API REST
pip install python-jose       # Pour authentification JWT
pip install python-multipart  # Pour upload de fichiers
pip install ofxparse          # Pour import bancaire OFX
pip install qrcode[pil]       # Pour QR codes
```

## 🚀 Utilisation

### Démarrage depuis OptimPV

Le module de facturation est intégré dans l'application principale OptimPV. Pour y accéder :

1. Lancez OptimPV :
```bash
streamlit run app.py
```

2. Dans la barre latérale, sélectionnez "💰 Facturation PMO"

### Démarrage de l'API REST (optionnel)

Pour utiliser l'API REST indépendamment :

```bash
cd modules/facturation/api
python api_server.py --host 0.0.0.0 --port 8001
```

Documentation interactive disponible sur :
- Swagger UI : http://localhost:8001/docs
- ReDoc : http://localhost:8001/redoc

## 📋 Guide de démarrage rapide

### 1. Créer un premier projet

1. Allez dans l'onglet "🏗️ Gestion des Projets"
2. Cliquez sur "➕ Nouveau Projet"
3. Remplissez les informations du projet
4. Ou utilisez l'import automatique depuis OptimPV

### 2. Ajouter des participants

1. Sélectionnez votre projet
2. Allez dans "👥 Gestion des Participants"
3. Ajoutez les consommateurs et producteurs
4. Vérifiez que l'allocation totale = 100%

### 3. Importer les données de production/consommation

1. Allez dans "📈 Données de Production/Consommation"
2. Utilisez l'import automatique depuis OptimPV
3. Ou saisissez manuellement les données mensuelles

### 4. Générer vos premières factures

1. Allez dans "🧾 Génération de Factures"
2. Sélectionnez la période de facturation
3. Cliquez sur "🧮 Calculer les Factures"
4. Vérifiez les montants et générez les factures

### 5. Configurer l'envoi d'emails (optionnel)

1. Allez dans "⚙️ Configuration" > "📧 Email SMTP"
2. Configurez vos paramètres SMTP
3. Testez la configuration
4. Envoyez vos factures par email

## 🔧 Configuration

### Paramètres principaux

Le module utilise la base de données SQLite `data/billing.db` pour stocker :
- Projets et participants
- Factures et paiements
- Configuration système
- Historique des actions

### Paramètres configurables

| Paramètre | Description | Valeur par défaut |
|-----------|-------------|-------------------|
| `autoconsumption_price_eur_kwh` | Prix de l'autoconsommation | 0.15 €/kWh |
| `tax_rate` | Taux de TVA | 20% |
| `invoice_prefix` | Préfixe des factures | PMO |
| `default_payment_terms_days` | Délai de paiement | 30 jours |
| `company_name` | Nom de la société | OptimPV |

### Templates PDF

Trois templates sont inclus par défaut :
- **Modern** : Design OptimPV avec couleurs corporate
- **Minimal** : Design épuré monochrome
- **Corporate** : Design formel avec couleurs bleues

Personnalisez les templates en modifiant les fichiers JSON dans `templates/`.

## 📊 Tableau de bord et KPIs

### Métriques principales
- **Projets actifs** : Nombre de projets en cours
- **Participants** : Total des consommateurs et producteurs
- **CA mensuel** : Chiffre d'affaires avec évolution
- **Factures en attente** : Factures non payées
- **Taux de recouvrement** : Performance de collection
- **DSO** : Délai moyen de paiement

### Analytics avancés
- Prévisions de trésorerie 12 mois
- Analyse de risque client
- Segmentation par comportement de paiement
- Optimisation tarifaire automatique
- Détection d'anomalies

## 🔌 Intégrations

### OptimPV
- Import automatique des projets et participants
- Synchronisation des données de production
- Utilisation du prix optimal calculé
- Intégration avec les clés de répartition

### ERP compatibles
- **Sage** (100, X3) via API REST
- **Cegid** via webservices
- **Odoo** via XML-RPC
- Export FEC pour tous logiciels comptables français

### Moyens de paiement
- Virements bancaires
- Prélèvements SEPA
- Cartes bancaires
- Chèques
- Import automatique des relevés bancaires

## 🛡️ Sécurité

### Authentification
- Intégration avec le système d'authentification OptimPV
- Support JWT pour l'API REST
- Gestion des rôles et permissions

### Protection des données
- Chiffrement des données sensibles
- Backup automatique de la base de données
- Logs d'audit complets
- Conformité RGPD

### API sécurisée
- Authentification JWT obligatoire
- Rate limiting par utilisateur
- Validation stricte des entrées
- Signatures HMAC pour webhooks

## 🔍 Dépannage

### Problèmes courants

**1. Module non trouvé**
```bash
# Vérifiez que vous êtes dans le bon répertoire
cd /path/to/OptimPV
python -c "import modules.facturation; print('OK')"
```

**2. Erreur de base de données**
```bash
# Réinitialisez la base de données
rm data/billing.db
# Redémarrez l'application pour recréer la DB
```

**3. Problème de génération PDF**
```bash
# Installez ReportLab
pip install reportlab
```

**4. Import bancaire non fonctionnel**
```bash
# Installez les dépendances d'import
pip install ofxparse
```

### Logs

Les logs du module sont disponibles dans la console Python. Pour un debugging avancé :

```python
import logging
logging.getLogger('modules.facturation').setLevel(logging.DEBUG)
```

## 📈 Roadmap

### Version actuelle (1.0.0)
✅ Toutes les fonctionnalités de base et avancées implémentées

### Prochaines versions
- [ ] Intégration avec plus d'ERP
- [ ] Module mobile React Native
- [ ] Intelligence artificielle pour optimisation
- [ ] Blockchain pour traçabilité
- [ ] Conformité internationale (hors France)

## 🤝 Support

### Documentation
- README technique complet
- Documentation API Swagger
- Guides utilisateur intégrés
- Tour guidé dans l'interface

### Contact
- Issues GitHub pour bugs et suggestions
- Documentation OptimPV principale
- Support via l'équipe OptimPV

## 📄 Licence

Ce module fait partie d'OptimPV et suit la même licence que le projet principal.

---

## 🎯 En résumé

Le module de facturation OptimPV transforme la gestion complexe de la facturation d'autoconsommation collective en un processus simple, automatisé et professionnel. Avec ses nombreuses fonctionnalités avancées, il convient aussi bien aux petites installations qu'aux projets d'envergure.

**Prêt à révolutionner votre gestion de facturation photovoltaïque ! ⚡💰**