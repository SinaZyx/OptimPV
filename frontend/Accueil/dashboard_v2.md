# Dashboard OptimPV V2 - Interface Principale avec NavBar

## Vue d'ensemble

Le Dashboard V2 est conçu comme un centre de commande unifié avec une navigation claire et une approche "parcours utilisateur" simplifiée. Il intègre une NavBar principale pour accéder rapidement à toutes les fonctionnalités.

## Structure de la NavBar Principale

### NavBar Complète
```typescript
interface MainNavBar {
 logo: {
 text: "OptimPV";
 icon: "";
 link: "/";
 };

 mainTabs: [
 {
 id: "accueil";
 label: "ACCUEIL";
 subItems: [
 { id: "dashboard", label: "Mon Dashboard", path: "/accueil/dashboard" },
 { id: "projets", label: "Projets Actifs", path: "/accueil/projets" },
 { id: "vue-ensemble", label: "Vue d'ensemble", path: "/accueil/overview" }
 ];
 },
 {
 id: "donnees";
 label: "DONNÉES";
 subItems: [
 { id: "import", label: "Importer", path: "/donnees/import" },
 { id: "config", label: "Configurer", path: "/donnees/configuration" },
 { id: "scenarios", label: "Scénarios", path: "/donnees/scenarios" },
 { id: "cles", label: "Clés Répartition", path: "/donnees/cles-repartition" }
 ];
 },
 {
 id: "analyse";
 label: "ANALYSE";
 subItems: [
 { id: "analyser", label: "Analyser", path: "/analyse/analyser" },
 { id: "optimiser", label: "Optimiser", path: "/analyse/optimiser" },
 { id: "visualiser", label: "Visualiser", path: "/analyse/visualisation" },
 { id: "rapports", label: "Rapports", path: "/analyse/rapports" }
 ];
 },
 {
 id: "commercial";
 label: "COMMERCIAL";
 subItems: [
 { id: "erp", label: "ERP Clients", path: "/commercial/erp-clients" },
 { id: "carte", label: "Carte Prospection", path: "/commercial/carte-prospection" },
 { id: "facturation", label: "Facturation PMO", path: "/commercial/facturation" }
 ];
 },
 {
 id: "outils";
 label: "OUTILS";
 subItems: [
 { id: "historique", label: "Historique", path: "/outils/historique" },
 { id: "serveur", label: "Serveur", path: "/outils/serveur" },
 { id: "securite", label: "Sécurité", path: "/outils/securite" }
 ];
 }
 ];
}
```

## Layout Principal du Dashboard

### Structure Complète
```typescript
interface DashboardLayout {
 navbar: MainNavBar;
 quickActionsBar: QuickActionsBar;
 mainContent: DashboardContent;
 contextualSidebar?: SidebarWidget;
}
```

### Zone Actions Rapides (sous NavBar)
```typescript
interface QuickActionsBar {
 search: {
 placeholder: "Recherche globale...";
 icon: "";
 suggestions: boolean;
 };

 shortcuts: [
 { label: "Favoris", action: "showFavorites" },
 { label: "Récents", action: "showRecent" },
 { label: "Mon Profil", action: "showProfile" }
 ];

 breadcrumb: {
 visible: boolean;
 path: string[]; // Ex: ["Accueil", "Commercial", "ERP Clients"]
 };
}
```

## Design Responsive

### Desktop (>1200px)
```

 OptimPV ACCUEIL DONNÉES ANALYSE COMMERCIAL OUTILS

 Recherche... Favoris Récents Profil

 CONTENU PRINCIPAL

```

### Tablet (768-1200px)
```

 OptimPV Recherche Profil

 ACCUEIL DONNÉES ANALYSE COMMERCIAL OUTILS

 CONTENU PRINCIPAL

```

### Mobile (<768px)
```

 OptimPV Recherche

 CONTENU PRINCIPAL

 [Menu hamburger caché]

```

## Contenu Principal Dashboard

### Zone d'Accueil Simplifiée
```typescript
interface WelcomeSection {
 greeting: {
 text: "Bonjour, que voulez-vous faire?";
 style: "centered";
 fontSize: "large";
 };

 mainActions: [
 {
 id: "new-project";
 icon: "";
 title: "COMMENCER UN NOUVEAU PROJET";
 subtitle: "→ Assistant étape par étape";
 color: "primary";
 size: "large";
 onClick: () => navigateTo("/projet/nouveau");
 },
 {
 id: "continue";
 icon: "";
 title: "CONTINUER UN PROJET EN COURS";
 subtitle: "→ Liste simple avec statuts";
 color: "secondary";
 size: "large";
 onClick: () => navigateTo("/projets/liste");
 },
 {
 id: "manage";
 icon: "";
 title: "GÉRER MON ACTIVITÉ";
 subtitle: "→ Clients, Factures, Analyses";
 color: "tertiary";
 size: "large";
 onClick: () => showManagementOptions();
 }
 ];
}
```

### Zone Projet Actuel (si un projet est sélectionné)
```typescript
interface CurrentProjectWidget {
 visible: boolean;
 project: {
 name: string;
 location: string;
 stage: string;
 progress: number;
 type: string;
 power: string;
 };

 display: {
 style: "card";
 position: "top";
 showProgress: true;
 showQuickStats: true;
 };
}
```

### Zone Métriques Clés
```typescript
interface KeyMetricsSection {
 title: "Mes Chiffres Clés";
 period: "Cette semaine";

 metrics: [
 { label: "nouveaux projets créés", value: 3 },
 { label: "clients ajoutés", value: 12 },
 { label: "de factures générées", value: "45k€" },
 { label: "zones prospectées", value: 2 }
 ];

 style: {
 layout: "horizontal";
 showTrend: true;
 animated: true;
 };
}
```

### Zone Workflow
```typescript
interface WorkflowSection {
 title: "MES ÉTAPES DE TRAVAIL";
 steps: [
 { number: "1", label: "PROSPECT", action: "Voir carte", path: "/commercial/carte-prospection" },
 { number: "2", label: "CLIENT", action: "Gérer base", path: "/commercial/erp-clients" },
 { number: "3", label: "PROJET", action: "Configurer", path: "/donnees/configuration" },
 { number: "4", label: "ANALYSE", action: "Optimiser", path: "/analyse/optimiser" },
 { number: "5", label: "FACTURE", action: "Encaisser", path: "/commercial/facturation" }
 ];

 display: {
 style: "pipeline";
 showProgress: true;
 highlightCurrent: true;
 };
}
```

### Zone Tâches du Jour
```typescript
interface TasksSection {
 title: "À FAIRE AUJOURD'HUI";
 tasks: Task[];

 display: {
 style: "checklist";
 showPriority: true;
 allowComplete: true;
 maxVisible: 5;
 };

 actions: {
 addTask: boolean;
 viewAll: boolean;
 };
}
```

## Navigation Contextuelle

### Dropdown Menu au Hover
```typescript
interface DropdownMenu {
 trigger: "hover" | "click";
 delay: 200; // ms
 animation: "fadeIn";

 structure: {
 showIcons: false;
 showDescriptions: true;
 groupByCategory: true;
 };
}
```

### Exemple Menu Commercial
```
GESTION COMMERCIALE
 ERP Clients
 Liste clients
 Nouveau client
 Tarification
 Dashboard commercial
 Carte de Prospection
 Recherche zone
 Analyse cadastrale
 Potentiel solaire
 Facturation PMO
 Projets
 Participants
 Factures
 Tableau de bord
```

## Comportements Intelligents

### Auto-adaptation selon contexte
```typescript
interface SmartBehaviors {
 roleBasedContent: {
 enabled: true;
 roles: ["developer", "commercial", "financial", "admin"];
 adaptContent: true;
 };

 projectContext: {
 showCurrentProject: true;
 quickAccessToLastUsed: true;
 suggestNextAction: true;
 };

 notifications: {
 position: "top-right";
 types: ["info", "warning", "error", "success"];
 autoHide: true;
 duration: 5000;
 };
}
```

## Modes d'Affichage

### Mode Focus (Un projet à la fois)
```typescript
interface FocusMode {
 enabled: boolean;
 hideNavigation: false; // NavBar toujours visible
 centerContent: true;
 showOnlyRelevant: true;

 layout: {
 type: "single-column";
 maxWidth: "800px";
 padding: "large";
 };
}
```

### Mode Multi-Projets
```typescript
interface MultiProjectMode {
 enabled: boolean;

 display: {
 layout: "grid" | "list";
 showComparison: true;
 quickSwitch: true;
 };

 features: {
 bulkActions: true;
 globalMetrics: true;
 crossProjectAnalysis: true;
 };
}
```

## Intégration avec Modules Existants

Le dashboard V2 s'intègre parfaitement avec:
- Module Storage: Sauvegarde des préférences utilisateur
- Module Security: Gestion des accès par rôle
- Module Engine: Récupération des KPIs en temps réel
- Module Visualization: Affichage des graphiques
- Module ERP/Facturation: Accès rapide aux données commerciales

## Notes d'Implémentation

1. Performance: Lazy loading des sous-modules
2. Cache: Mémorisation des derniers projets consultés
3. Personnalisation: Sauvegarde layout par utilisateur
4. Accessibilité: Navigation clavier complète
5. Animations: Transitions fluides mais désactivables