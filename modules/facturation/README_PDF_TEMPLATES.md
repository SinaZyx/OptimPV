# Système de Templates PDF OptimPV

## Vue d'ensemble

Ce système fournit une solution complète et personnalisable pour la génération de documents PDF dans le module de facturation OptimPV. Il supporte la génération de factures, avoirs, devis avec des templates personnalisables, du multilingue, et l'intégration de QR codes de paiement conformes aux standards européens.

## Fonctionnalités principales

### ✨ Templates personnalisables
- **3 templates intégrés** : Modern, Minimal, Corporate
- **Couleurs configurables** selon votre charte graphique
- **Polices et mise en page ajustables**
- **Support des logos** avec dimensionnement automatique
- **Création de templates personnalisés** basés sur les existants

### 🌍 Support multilingue
- **Français et anglais** intégrés
- **Système extensible** pour d'autres langues
- **Textes personnalisables** par template et langue

### 📱 QR Codes de paiement
- **Standard EPC QR Code** pour paiements SEPA
- **Compatible** avec toutes les apps bancaires européennes
- **Génération automatique** avec IBAN, montant et référence
- **Validation IBAN** intégrée

### 🎨 Watermarks automatiques
- **BROUILLON** pour les factures en draft
- **PAYÉ** pour les factures réglées
- **ANNULÉ** pour les factures annulées
- **IMPAYÉ** pour les factures en retard

## Architecture

```
modules/facturation/
├── pdf_templates.py          # Classes de templates et gestionnaire
├── pdf_config.py            # Configuration et gestion des templates
├── qr_payment.py            # Génération de QR codes EPC
├── templates/               # Templates JSON
│   ├── modern.json         # Template moderne OptimPV
│   ├── minimal.json        # Template minimaliste
│   ├── corporate.json      # Template corporate
│   └── README.md           # Documentation des templates
├── example_template_usage.py # Script de démonstration
└── README_PDF_TEMPLATES.md  # Cette documentation
```

### Classes principales

#### `PDFTemplateManager`
Gestionnaire principal pour la génération de documents PDF avec templates.

```python
from modules.facturation.pdf_templates import PDFTemplateManager
from modules.facturation.pdf_config import get_pdf_config

config = get_pdf_config()
manager = PDFTemplateManager(config)

# Générer une facture
pdf_bytes = manager.generate_document(
    template_type='invoice',
    data=invoice_data,
    template_name='modern',
    language='fr'
)
```

#### `BaseTemplate`
Classe de base pour tous les templates avec méthodes communes :
- Gestion des en-têtes et pieds de page
- Construction des tableaux
- Ajout de watermarks
- Support multilingue

#### Templates spécialisés
- **`InvoiceTemplate`** : Factures avec QR codes de paiement
- **`CreditNoteTemplate`** : Avoirs (hérite de InvoiceTemplate)
- **`QuoteTemplate`** : Devis avec conditions générales

#### `QRPaymentGenerator`
Générateur de QR codes conformes au standard EPC069-12 :
- Validation IBAN automatique
- Support BIC optionnel
- Limite de 331 caractères respectée
- Compatible apps bancaires européennes

## Installation et dépendances

### Dépendances requises

```bash
pip install reportlab  # Génération PDF
pip install qrcode[pil]  # Génération QR codes
```

### Dépendances optionnelles

```bash
pip install pillow  # Support images amélioré
```

## Utilisation

### 1. Génération de facture simple

```python
from modules.facturation.invoice_generator import InvoiceGenerator
from modules.facturation.database import BillingDatabase

# Initialiser le générateur
db = BillingDatabase()
generator = InvoiceGenerator(db)

# Générer une facture avec le template moderne
pdf_bytes = generator.generate_invoice_pdf(
    invoice=my_invoice,
    participant=my_participant,
    project=my_project,
    template_name='modern',
    language='fr',
    output_path='/path/to/facture.pdf'
)
```

### 2. Génération de devis

```python
quote_data = {
    'number': 'DEVIS-2024-001',
    'date': date.today(),
    'valid_until': date.today() + timedelta(days=30),
    'project_name': 'Installation Photovoltaïque',
    'items': [...],
    'subtotal': 12000.00
}

client_data = {
    'name': 'Client Name',
    'address': 'Client Address',
    'email': 'client@email.com'
}

pdf_bytes = generator.generate_quote_pdf(
    quote_data=quote_data,
    client_data=client_data,
    template_name='corporate',
    language='fr'
)
```

### 3. Création de template personnalisé

```python
from modules.facturation.pdf_config import get_pdf_config

config = get_pdf_config()

# Créer un template basé sur 'modern' avec des couleurs personnalisées
custom_template = config.create_custom_template(
    name="custom_blue",
    base_template="modern",
    modifications={
        'description': 'Template bleu personnalisé',
        'colors': {
            'primary': '#1565C0',
            'accent': '#2196F3',
            'table_header': '#E3F2FD'
        }
    }
)

# Sauvegarder le template
config.save_template(custom_template)
```

### 4. Gestion des logos

```python
# Ajouter un logo à un template
config.set_logo(
    template_name='modern',
    logo_path='/path/to/logo.png',
    width=40,  # mm
    height=20  # mm
)
```

### 5. Personnalisation des textes

```python
# Ajouter des textes personnalisés
custom_texts = {
    'fr': {
        'invoice_title': 'FACTURE SOLAIRE',
        'thank_you': 'Merci pour votre confiance en l\'énergie verte!'
    },
    'en': {
        'invoice_title': 'SOLAR INVOICE',
        'thank_you': 'Thank you for trusting green energy!'
    }
}

config.update_texts('modern', custom_texts)
```

## Configuration des templates

### Structure d'un template JSON

```json
{
  "name": "template_name",
  "description": "Description du template",
  "colors": {
    "primary": "#2E7D32",
    "secondary": "#666666",
    "text": "#333333",
    "background": "#FFFFFF",
    "table_header": "#E8F5E8",
    "table_alt": "#F9F9F9",
    "border": "#DDDDDD",
    "accent": "#4CAF50"
  },
  "fonts": {
    "title": {"name": "Helvetica-Bold", "size": 20},
    "heading": {"name": "Helvetica-Bold", "size": 14},
    "body": {"name": "Helvetica", "size": 10},
    "footer": {"name": "Helvetica", "size": 9}
  },
  "margins": {
    "top": 20,
    "bottom": 20,
    "left": 20,
    "right": 20
  },
  "logo_path": "/path/to/logo.png",
  "logo_width": 30,
  "logo_height": 15,
  "texts": {
    "fr": { /* textes français */ },
    "en": { /* textes anglais */ }
  }
}
```

### Couleurs disponibles

- **primary** : Couleur principale (titres, bordures importantes)
- **secondary** : Couleur secondaire (textes secondaires)
- **text** : Couleur du texte principal
- **background** : Couleur de fond
- **table_header** : Couleur de fond des en-têtes de tableau
- **table_alt** : Couleur de fond des lignes alternées
- **border** : Couleur des bordures
- **accent** : Couleur d'accent

### Polices supportées

- `Helvetica` / `Helvetica-Bold`
- `Times-Roman` / `Times-Bold`
- `Courier` / `Courier-Bold`

## QR Codes de paiement

### Standard EPC QR Code

Le système génère des QR codes conformes au standard EPC069-12 pour les paiements SEPA :

```python
from modules.facturation.qr_payment import QRPaymentGenerator

generator = QRPaymentGenerator()

qr_bytes = generator.generate_payment_qr(
    iban='FR14 2004 1010 0505 0001 3M02 606',
    amount=1234.56,
    reference='FACT-2024-001',
    creditor_name='OptimPV Solutions',
    bic='BNPAFRPP'  # Optionnel pour paiements domestiques
)
```

### Validation automatique

- **IBAN** : Validation format et longueur par pays
- **Montant** : Maximum 999,999,999.99€, 2 décimales max
- **Textes** : Troncature automatique selon limites EPC
- **Données** : Respect limite 331 caractères

## Gestion des erreurs et logs

### Logs détaillés

Le système utilise le module `logging` de Python pour tracer toutes les opérations :

```python
import logging

# Activer les logs détaillés
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('modules.facturation')
```

### Gestion des erreurs

- **Dépendances manquantes** : Détection automatique avec messages explicites
- **Templates invalides** : Validation avec liste d'erreurs détaillée
- **Données manquantes** : Valeurs par défaut et logs d'avertissement
- **Erreurs de génération** : Capture et logging avec stack trace

## Migration depuis l'ancien système

### Compatibilité descendante

L'`InvoiceGenerator` modifié reste compatible avec l'ancien code :

```python
# Ancien code (toujours fonctionnel)
pdf_bytes = generator.generate_invoice_pdf(invoice, participant, project)

# Nouveau code avec templates
pdf_bytes = generator.generate_invoice_pdf(
    invoice, participant, project,
    template_name='modern',
    language='fr'
)
```

### Migration progressive

1. **Installer les nouvelles dépendances**
2. **Tester avec les templates par défaut**
3. **Personnaliser les couleurs et logos**
4. **Créer des templates personnalisés**
5. **Migrer les anciens appels progressivement**

## Exemples et démonstration

### Script de démonstration

Exécutez le script d'exemple pour voir toutes les fonctionnalités :

```bash
cd modules/facturation
python example_template_usage.py
```

Ce script génère :
- Factures avec tous les templates et langues
- Devis avec templates sélectionnés
- QR codes de paiement
- Template personnalisé
- Démonstration des fonctionnalités de gestion

### Fichiers générés

Les PDFs de démonstration sont créés dans `modules/facturation/demo_output/` :

```
demo_output/
├── facture_modern_fr.pdf
├── facture_modern_en.pdf
├── facture_minimal_fr.pdf
├── facture_corporate_fr.pdf
├── devis_modern.pdf
├── devis_corporate.pdf
├── facture_custom_orange.pdf
└── qr_payment.png
```

## Personnalisation avancée

### Créer un nouveau type de template

```python
from modules.facturation.pdf_templates import BaseTemplate

class CustomTemplate(BaseTemplate):
    def generate(self, data, output_path=None):
        # Implémenter la génération personnalisée
        pass

# Enregistrer le nouveau type
manager.register_template('custom_type', CustomTemplate)
```

### Watermarks personnalisés

Les watermarks sont ajoutés automatiquement selon le statut :
- `InvoiceStatus.DRAFT` → "BROUILLON"
- `InvoiceStatus.PAID` → "PAYÉ"
- `InvoiceStatus.CANCELLED` → "ANNULÉ"
- `InvoiceStatus.OVERDUE` → "IMPAYÉ"

### Intégration avec d'autres modules

Le système est conçu pour s'intégrer facilement avec :
- **Module de stockage** : Sauvegarde automatique des PDFs
- **Module email** : Envoi automatique des factures
- **Module reporting** : Génération de rapports groupés
- **Interface Streamlit** : Prévisualisation et téléchargement

## Performance et limitations

### Performance

- **Génération rapide** : ~500ms par document PDF
- **Mémoire optimisée** : Utilisation de BytesIO pour éviter les fichiers temporaires
- **Cache des templates** : Chargement unique en mémoire

### Limitations

- **Polices** : Limitées aux polices ReportLab standard
- **Images** : Support PNG, JPEG pour logos
- **QR codes** : Standard EPC uniquement (pas de QR codes libres dans factures)
- **Langues** : Français et anglais par défaut (extensible)

## Support et contribution

### Signaler un problème

Pour signaler un bug ou demander une fonctionnalité :
1. Vérifiez les logs d'erreur
2. Testez avec le script de démonstration
3. Documentez les données d'entrée problématiques

### Contribuer

Pour ajouter un nouveau template ou fonctionnalité :
1. Créez un template JSON de test
2. Validez avec `validate_template_config()`
3. Testez avec différents types de données
4. Documentez les nouvelles options

## Changelog

### Version 1.0 (2024)
- ✅ Système de templates JSON configurables
- ✅ Support multilingue (FR/EN)
- ✅ QR codes EPC pour paiements SEPA
- ✅ 3 templates intégrés (Modern, Minimal, Corporate)
- ✅ Watermarks automatiques
- ✅ Compatibilité descendante
- ✅ Validation complète des données
- ✅ Documentation et exemples complets