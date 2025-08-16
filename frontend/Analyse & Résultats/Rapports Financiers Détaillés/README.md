# Rapports Financiers Détaillés - OptimPV

## Vue d'ensemble

Ce module fournit les tableaux financiers détaillés et les rapports professionnels pour l'analyse des projets photovoltaïques dans OptimPV. Il utilise le module `table_finance` pour afficher les données financières.

## Fonctionnalités réelles

### 1. Tableaux Financiers Streamlit
- **Résumé annuel détaillé**: Compte de résultat professionnel avec hiérarchie
- **Cash flow mensuel**: Flux de trésorerie détaillés par catégorie et par mois
- **Métriques de synthèse**: NPV, IRR, LCOE, Payback, DSCR

### 2. Génération de Rapports
- **Rapports commerciaux**: Documents Word personnalisables
- **Templates DOCX**: Modèles avec variables dynamiques
- **Export Excel/CSV**: Tableaux financiers exportables

## Structure des fichiers

```
Rapports Financiers Détaillés/
 README.md # Ce fichier
 tableaux_annuels.md # Résumés annuels et KPIs
 cash_flow_mensuel.md # Analyse des flux de trésorerie mensuels
 generation_rapports.md # Création de documents Word/PDF
```

## Architecture technique

- **Interface**: Streamlit avec onglets et navigation
- **Affichage**: Module `modules/table_finance/`
- **Export**: Fonctions Excel/CSV intégrées
- **Rapports**: Module `modules/reporting/` pour documents Word