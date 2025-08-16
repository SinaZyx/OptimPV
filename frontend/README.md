# Frontend OptimPV - Guide des Interfaces

Ce dossier contient les spécifications détaillées de chaque page et interface de l'application OptimPV, organisées par module.

## Structure

```
frontend/
 README.md # Ce fichier
 Accueil/ # Page d'accueil et tableau de bord principal
 dashboard.md # Dashboard principal

 Données & Configuration/ # Gestion des données et paramétrage
 configuration/ # Configuration système
 main.md # Page de configuration
 engine/ # Moteur de calcul
 parameters.md # Paramètres d'entrée
 results.md # Résultats calculs
 storage/ # Gestion du stockage
 project_manager.md # Gestionnaire projets
 comparison.md # Comparaison projets
 repartition_keys/ # Clés de répartition
 key_management.md # Gestion des clés

 Gestion Commerciale/ # Modules commerciaux
 erp_client/ # Module ERP Client
 dashboard_commercial.md # Dashboard commercial
 client_list.md # Liste des clients
 client_form.md # Formulaire client
 pricing.md # Tarification
 autoconso.md # Autoconsommation
 cartography.md # Cartographie
 facturation/ # Module Facturation
 dashboard.md # Tableau de bord
 projects.md # Gestion projets
 analytics.md # Analytics facturation
 participants.md # Gestion participants
 invoices.md # Génération factures
 payments.md # Gestion paiements
 config.md # Configuration
 prospect_mapping/ # Cartographie prospects
 main_map.md # Carte principale
 filters.md # Filtres et recherche
 results.md # Résultats et exports

 Analyse & Résultats/ # Analyses et rapports
 visualization/ # Visualisations
 analytics.md # Page Analytics avancée
 reports.md # Page Rapports
 classic.md # Vue classique
 table_finance/ # Tableaux financiers
 cash_flow.md # Flux de trésorerie
 summary.md # Résumés financiers
 reporting/ # Module Reporting
 templates.md # Templates rapports

 Outils & Admin/ # Outils et administration
 security/ # Sécurité
 config.md # Configuration sécurité
 shared/ # Composants partagés
 components.md # Composants réutilisables
 layouts.md # Layouts communs
```

## Objectif

Chaque fichier contient:
- Description de la page/interface
- Structure des composants
- Interactions utilisateur
- Exemples de code React/TypeScript
- États et données nécessaires
- API endpoints utilisés

## Navigation

Naviguez par thème:
- [Accueil](./Accueil/) - Page d'accueil et tableau de bord principal
- [Données & Configuration](./Données%20%26%20Configuration/) - Paramétrage et gestion des données
- [Gestion Commerciale](./Gestion%20Commerciale/) - Clients, facturation et prospection
- [Analyse & Résultats](./Analyse%20%26%20Résultats/) - Visualisations et rapports
- [Outils & Admin](./Outils%20%26%20Admin/) - Administration et composants partagés