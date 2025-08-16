# Génération de Rapports - Documents Word/PDF

## Vue d'ensemble

OptimPV utilise le module `modules/reporting/` pour générer des rapports professionnels en format Word (DOCX) avec templates personnalisables et variables dynamiques.

## Système de Rapports

### Module Principal
```python
# Fichier: modules/reporting/customer_report_commercial.py
# Génération rapports commerciaux avec templates Word

def generate_customer_report():
    """
    Génère un rapport commercial personnalisé
    avec données financières et techniques
    """
```

### Intégration DOCX
```python
# Fichier: modules/reporting/docx_integration.py
# Gestion des documents Word avec python-docx

from docx import Document
import modules.reporting.docx_system as docx_system

def create_docx_report(template_path, data_dict):
    """
    Crée rapport Word à partir template et données
    - Remplacement variables {{variable}}
    - Insertion tableaux financiers
    - Génération graphiques intégrés
    """
```

## Templates et Variables

### Interface de Gestion
```python
# Fichier: modules/reporting/template_interface.py
# Interface Streamlit pour gestion templates

def display_template_management():
    """
    Interface pour:
    - Sélection template existant
    - Upload nouveau template
    - Configuration variables
    - Aperçu avant génération
    """
```

### Variables Dynamiques
```python
# Variables disponibles dans templates:

project_variables = {
    # Données techniques
    "{{puissance_crete}}": f"{puissance_kwc:.1f} kWc",
    "{{production_annuelle}}": f"{production_kwh:.0f} kWh/an",
    "{{taux_autoconso}}": f"{autoconso_rate*100:.1f}%",
    
    # Données financières
    "{{investissement_total}}": f"{capex:.0f} €",
    "{{prix_vente_ht}}": f"{prix_ht:.4f} €/kWh",
    "{{van_projet}}": f"{npv:.0f} €",
    "{{tri_projet}}": f"{irr*100:.1f}%",
    "{{payback}}": f"{payback:.1f} ans",
    "{{lcoe}}": f"{lcoe:.4f} €/kWh",
    
    # Données économiques
    "{{economies_annuelles}}": f"{savings:.0f} €/an",
    "{{benefice_20ans}}": f"{total_benefit:.0f} €",
    "{{taux_rentabilite}}": f"{roe*100:.1f}%"
}
```

## Types de Rapports

### 1. Rapport Commercial Client
```python
def generate_commercial_report():
    """
    Rapport orienté client final:
    - Synthèse économique simple
    - Bénéfices et économies
    - Temps de retour
    - Impact environnemental
    """
```

**Sections typiques :**
- Page de garde avec logo
- Résumé exécutif (ROI, économies)
- Analyse technique (puissance, production)
- Analyse financière (investissement, bénéfices)
- Planning et démarches
- Conditions commerciales

### 2. Rapport Technique Détaillé
```python
def generate_technical_report():
    """
    Rapport technique approfondi:
    - Spécifications matériel
    - Études d'implantation
    - Performances détaillées
    - Maintenance et garanties
    """
```

### 3. Rapport Financier Investisseur
```python
def generate_investor_report():
    """
    Rapport pour investisseurs:
    - Analyse financière complète
    - Cash flows détaillés
    - Analyse de risque
    - Comparaisons marché
    """
```

## Système DOCX Avancé

### Génération de Graphiques
```python
# Module: modules/reporting/docx_system/
# Intégration graphiques dans documents Word

def insert_chart_in_docx(doc, chart_data, chart_type="line"):
    """
    Insère graphiques dans document Word:
    - Courbes de cash flow
    - Graphiques en barres (revenus/charges)
    - Camemberts (répartition énergie)
    - Graphiques de sensibilité
    """
```

### Templates Prédéfinis
- **Template Commercial** : `templates/rapport_commercial.docx`
- **Template Technique** : `templates/rapport_technique.docx`
- **Template Financier** : `templates/rapport_financier.docx`
- **Template Personnalisé** : Upload utilisateur

## Workflow de Génération

### 1. Sélection Template
```python
# Interface Streamlit
selected_template = st.selectbox(
    "Type de rapport",
    options=[
        "Commercial Client",
        "Technique Détaillé", 
        "Financier Investisseur",
        "Personnalisé"
    ]
)
```

### 2. Configuration Variables
```python
# Personnalisation variables
with st.expander("Personnaliser les variables"):
    client_name = st.text_input("Nom du client", value="")
    project_name = st.text_input("Nom du projet", value="")
    custom_logo = st.file_uploader("Logo personnalisé", type=['png', 'jpg'])
```

### 3. Génération et Export
```python
if st.button("Générer Rapport", type="primary"):
    with st.spinner("Génération en cours..."):
        # Collecte données projet
        report_data = collect_project_data()
        
        # Génération document
        doc_path = generate_docx_report(template, report_data)
        
        # Bouton téléchargement
        with open(doc_path, 'rb') as file:
            st.download_button(
                label="Télécharger Rapport",
                data=file.read(),
                file_name=f"rapport_{project_name}_{datetime.now().strftime('%Y%m%d')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
```

## Intégration Données Financières

### Tableaux dans Documents
```python
def insert_financial_table(doc, table_data):
    """
    Insère tableaux financiers formatés:
    - Cash flow mensuel/annuel
    - Résumé indicateurs (NPV, IRR, etc.)
    - Analyse de sensibilité
    - Comparaisons scénarios
    """
```

### Formatage Automatique
- **Devise** : Format € avec séparateurs milliers
- **Pourcentages** : Avec décimales appropriées
- **Dates** : Format local français
- **Unités** : kWh, kWc, €/kWh automatiques

## Historique et Versions

### Sauvegarde Rapports
```python
# Stockage rapports générés
report_history = {
    "timestamp": datetime.now(),
    "template_used": template_name,
    "client_name": client_name,
    "file_path": saved_report_path,
    "variables_used": report_variables
}
```

### Régénération
- **Même configuration** : Régénération identique
- **Mise à jour données** : Nouvelles données, même template
- **Modifications template** : Version modifiée

---

*Le système de génération de rapports d'OptimPV permet de créer des documents professionnels personnalisés pour chaque type d'audience, avec intégration automatique des données techniques et financières.*