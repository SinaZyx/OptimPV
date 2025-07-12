# Système DOCX OptimPV

Ce module fournit un système complet de génération de rapports DOCX professionnels pour l'application OptimPV.

## 🎯 Vue d'ensemble

Le système DOCX OptimPV permet de générer des rapports clients professionnels au format Microsoft Word (.docx) avec :
- Mise en forme professionnelle avec styles OptimPV
- Insertion automatique de données de projet
- Support des graphiques et tableaux
- Templates personnalisables
- Intégration complète avec l'interface utilisateur

## 📦 Installation

Pour utiliser le système DOCX, installez les dépendances requises :

```bash
pip install python-docx
pip install plotly pillow  # Pour les graphiques (optionnel)
```

## 🏗️ Architecture

Le système est composé de 4 modules principaux :

### 1. DocxGenerator (`docx_generator.py`)
Générateur principal qui coordonne la création des documents DOCX.

**Fonctionnalités principales :**
- Création de documents avec styles OptimPV
- Ajout de pages de garde professionnelles
- Gestion des en-têtes et pieds de page
- Assemblage final des rapports

### 2. TemplateManager (`template_manager.py`)
Gestionnaire de templates DOCX pour différents types de rapports.

**Fonctionnalités principales :**
- Création de templates par défaut
- Gestion de bibliothèque de templates
- Duplication et modification de templates
- Templates pour rapport client, technique et financier

### 3. DataMapper (`data_mapper.py`)
Système de mappage des données OptimPV vers les placeholders des templates.

**Fonctionnalités principales :**
- Mapping automatique des données de projet
- Support des placeholders `{{VARIABLE_NAME}}`
- Validation des mappings
- Formatage automatique des nombres et dates

### 4. ChartInserter (`chart_inserter.py`)
Insertion de graphiques Plotly dans les documents DOCX.

**Fonctionnalités principales :**
- Conversion de graphiques Plotly en images
- Insertion automatique dans les documents
- Support des graphiques OptimPV existants
- Gestion des graphiques personnalisés

## 🚀 Utilisation

### Utilisation basique

```python
from modules.reporting.docx_system import DocxGenerator

# Créer le générateur
generator = DocxGenerator()

# Préparer les données
project_config = {...}  # Configuration du projet
financial_data = {...}  # Données financières
energy_data = {...}     # Données énergétiques

# Générer le rapport
doc = generator.generate_customer_report(
    project_config=project_config,
    financial_data=financial_data,
    energy_data=energy_data,
    title="Votre Projet Solaire",
    client_name="Client ABC",
    project_name="Installation 25 kWc"
)

# Sauvegarder
filepath = generator.save_document(doc, "rapport_client.docx")
```

### Utilisation avec l'interface OptimPV

Le système est intégré dans le module `customer_report.py` :

1. Lancez l'application OptimPV
2. Allez dans l'onglet "Rapport Client"
3. Sélectionnez "DOCX professionnel" dans les options de format
4. Cliquez sur "Générer et Prévisualiser"
5. Téléchargez le fichier DOCX généré

## 📋 Templates

### Templates par défaut

Le système crée automatiquement 3 templates :

1. **customer_report.docx** - Rapport client avec focus économies
2. **technical_report.docx** - Rapport technique détaillé
3. **financial_summary.docx** - Résumé financier complet

### Placeholders supportés

Les templates utilisent des placeholders au format `{{VARIABLE_NAME}}` :

#### Informations générales
- `{{TITLE}}` - Titre du rapport
- `{{CLIENT_NAME}}` - Nom du client
- `{{PROJECT_NAME}}` - Nom du projet
- `{{REPORT_DATE}}` - Date de génération

#### Configuration technique
- `{{POWER_KWC}}` - Puissance installée (kWc)
- `{{PRODUCER_SITES}}` - Nombre de sites producteurs
- `{{CONSUMER_SITES}}` - Nombre de sites consommateurs
- `{{PROJECT_DURATION}}` - Durée du projet (années)

#### Données financières
- `{{TOTAL_SAVINGS}}` - Économies totales (€)
- `{{OPTIMAL_PRICE}}` - Prix optimal (€/kWh)
- `{{PROJECT_NPV}}` - VAN du projet (€)
- `{{PROJECT_IRR}}` - TRI du projet (%)
- `{{PAYBACK}}` - Période de retour (années)

#### Données énergétiques
- `{{ANNUAL_PRODUCTION}}` - Production annuelle (MWh)
- `{{ANNUAL_CONSUMPTION}}` - Consommation annuelle (MWh)
- `{{AUTOCONSUMPTION}}` - Autoconsommation (MWh)
- `{{AUTONOMY_RATE}}` - Taux d'autonomie (%)
- `{{AUTOCONSUMPTION_RATE}}` - Taux d'autoconsommation (%)

### Création de templates personnalisés

```python
from modules.reporting.docx_system import TemplateManager

manager = TemplateManager()

# Créer un nouveau template
doc = Document()
# ... personnaliser le document avec placeholders ...
manager.create_template_from_document(doc, "mon_template")

# Utiliser le template personnalisé
custom_template = manager.get_template("mon_template")
```

## 📊 Graphiques

### Graphiques automatiques

Le système insère automatiquement :
- Comparaison des prix d'électricité
- Distribution énergétique (camembert)
- Évolution des économies cumulées
- Indicateurs financiers clés

### Graphiques personnalisés

```python
from modules.reporting.docx_system import ChartInserter

inserter = ChartInserter()

# Créer un graphique simple
fig = inserter.create_simple_bar_chart(
    data={'A': 10, 'B': 20}, 
    title="Mon Graphique"
)

# Insérer dans un document
inserter.insert_custom_chart(doc, fig, "Titre", "Description")
```

## 🔧 Configuration

### Styles OptimPV

Le système utilise des styles prédéfinis :
- **OptimPV Title** - Titres principaux (vert OptimPV)
- **OptimPV Subtitle** - Sous-titres
- **OptimPV Section** - Titres de section
- **OptimPV Normal** - Texte normal
- **OptimPV Highlight** - Texte mis en valeur

### Personnalisation

Modifiez `DocxGenerator._add_custom_styles()` pour personnaliser :
- Couleurs (RGB)
- Polices
- Tailles
- Espacements

## 🧪 Tests

### Tests automatiques

```bash
# Tests complets (nécessite toutes les dépendances)
python tests/test_docx_system.py

# Tests de structure (sans dépendances)
python tests/test_docx_standalone.py
```

### Validation manuelle

1. Générez un rapport DOCX
2. Ouvrez dans Microsoft Word
3. Vérifiez :
   - Mise en forme correcte
   - Données correctement insérées
   - Graphiques présents
   - Pagination appropriée

## 🐛 Dépannage

### Erreurs communes

#### `ImportError: No module named 'docx'`
```bash
pip install python-docx
```

#### `Erreur lors de l'insertion de graphiques`
```bash
pip install plotly pillow
```

#### `Template non trouvé`
Le système crée automatiquement les templates au premier usage. Vérifiez que le dossier `modules/reporting/templates/` est accessible en écriture.

#### `Données manquantes dans le rapport`
Assurez-vous que :
- Les données ont été importées dans OptimPV
- Une optimisation a été lancée
- Les données sont disponibles dans `st.session_state`

### Mode debug

Activez les logs pour diagnostiquer :

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performances

### Recommandations

- **Taille des graphiques** : Limitez à 800x600 pixels
- **Nombre de graphiques** : Maximum 5-6 par rapport
- **Taille de fichier** : Typiquement 2-5 MB par rapport

### Optimisations

- Les graphiques sont automatiquement compressés
- Les fichiers temporaires sont nettoyés
- Le cache des templates optimise les performances

## 🔮 Évolutions futures

### Fonctionnalités prévues

- Support des graphiques vectoriels (SVG)
- Templates conditionnels
- Génération en lots
- Export PowerPoint (.pptx)
- Signatures électroniques

### Contributions

Pour contribuer au système DOCX :

1. Respectez l'architecture modulaire
2. Ajoutez des tests pour nouvelles fonctionnalités
3. Documentez les nouveaux placeholders
4. Maintenez la compatibilité descendante

## 📞 Support

Pour questions ou problèmes :
- Consultez les logs d'erreur
- Vérifiez les tests automatiques
- Référez-vous à cette documentation
- Contactez l'équipe OptimPV

---

*Système DOCX OptimPV - Version 1.0.0*
*Génération de rapports professionnels pour l'autoconsommation collective*