# Templates PDF OptimPV

Ce répertoire contient les templates JSON pour la génération de documents PDF dans le module de facturation OptimPV.

## Templates disponibles

### 1. Modern (`modern.json`)
- **Description** : Template moderne avec design épuré et couleurs corporate OptimPV
- **Couleur principale** : Vert OptimPV (#2E7D32)
- **Style** : Moderne, professionnel, adapté à l'énergie solaire
- **Usage recommandé** : Documents standards, factures clients finaux

### 2. Minimal (`minimal.json`)
- **Description** : Template minimaliste avec design monochrome
- **Couleur principale** : Noir (#000000)
- **Style** : Épuré, simple, discret
- **Usage recommandé** : Documents internes, notes de crédit

### 3. Corporate (`corporate.json`)
- **Description** : Template corporate formel avec couleurs bleues
- **Couleur principale** : Bleu marine (#1B365D)
- **Style** : Formel, professionnel, institutionnel
- **Usage recommandé** : Devis officiels, documents contractuels

## Structure d'un template

Chaque template JSON contient les sections suivantes :

```json
{
  "name": "nom_du_template",
  "description": "Description du template",
  "colors": {
    "primary": "#couleur_principale",
    "secondary": "#couleur_secondaire",
    "text": "#couleur_texte",
    "background": "#couleur_fond",
    "table_header": "#couleur_entete_tableau",
    "table_alt": "#couleur_alternee_tableau",
    "border": "#couleur_bordures",
    "accent": "#couleur_accent"
  },
  "fonts": {
    "title": {"name": "police", "size": taille},
    "heading": {"name": "police", "size": taille},
    "body": {"name": "police", "size": taille},
    "footer": {"name": "police", "size": taille}
  },
  "margins": {
    "top": marge_haut,
    "bottom": marge_bas,
    "left": marge_gauche,
    "right": marge_droite
  },
  "logo_path": "chemin/vers/logo",
  "logo_width": largeur_mm,
  "logo_height": hauteur_mm,
  "table_style": {
    "header_height": hauteur_entete,
    "row_height": hauteur_ligne,
    "border_width": largeur_bordure,
    "grid_color": "#couleur_grille"
  },
  "texts": {
    "fr": { /* textes français */ },
    "en": { /* textes anglais */ }
  }
}
```

## Personnalisation

### Créer un nouveau template

1. Copiez un template existant
2. Modifiez le nom et la description
3. Personnalisez les couleurs selon votre charte graphique
4. Ajustez les polices et marges si nécessaire
5. Adaptez les textes dans les langues souhaitées

### Utiliser un logo personnalisé

1. Placez votre logo dans un dossier accessible
2. Mettez à jour le champ `logo_path` avec le chemin complet
3. Ajustez `logo_width` et `logo_height` selon les dimensions souhaitées (en mm)

### Couleurs personnalisées

Les couleurs doivent être au format hexadécimal (#RRGGBB) :
- `primary` : Couleur principale (titres, bordures importantes)
- `secondary` : Couleur secondaire (textes secondaires)
- `text` : Couleur du texte principal
- `background` : Couleur de fond (généralement blanc)
- `table_header` : Couleur de fond des en-têtes de tableau
- `table_alt` : Couleur de fond des lignes alternées
- `border` : Couleur des bordures
- `accent` : Couleur d'accent (boutons, éléments interactifs)

### Polices disponibles

Polices supportées par ReportLab :
- `Helvetica` : Police sans-serif standard
- `Helvetica-Bold` : Version grasse
- `Times-Roman` : Police serif classique
- `Times-Bold` : Version grasse
- `Courier` : Police monospace

### Textes multilingues

Chaque template supporte plusieurs langues. Pour ajouter une langue :

1. Ajoutez une section dans `texts` avec le code de langue (ex: `"es"` pour espagnol)
2. Copiez la structure des textes français
3. Traduisez tous les éléments

Clés de texte obligatoires :
- Titres de documents (`invoice_title`, `quote_title`, etc.)
- Labels de champs (`invoice_number`, `issue_date`, etc.)
- En-têtes de tableaux (`description`, `quantity`, etc.)
- Totaux (`subtotal`, `vat`, `total`)
- Conditions de paiement
- Watermarks pour les statuts

## Utilisation dans le code

```python
from modules.facturation.pdf_templates import PDFTemplateManager
from modules.facturation.pdf_config import get_pdf_config

# Initialiser le gestionnaire
config = get_pdf_config()
manager = PDFTemplateManager(config)

# Générer une facture avec le template moderne
pdf_bytes = manager.generate_document(
    template_type='invoice',
    data=invoice_data,
    template_name='modern',
    language='fr'
)

# Générer un devis avec le template corporate
pdf_bytes = manager.generate_document(
    template_type='quote',
    data=quote_data,
    template_name='corporate',
    language='en'
)
```

## Validation

Les templates sont automatiquement validés lors du chargement :
- Format des couleurs hexadécimales
- Polices supportées
- Valeurs numériques positives
- Présence des textes obligatoires

En cas d'erreur, consultez les logs pour plus de détails.